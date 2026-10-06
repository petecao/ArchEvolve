"""Frozen description -> generic source/count observation contract.
Created: 2026-10-06 ET. No hardware names, execution results or address traces.
"""
import re
from pathlib import Path
from swdb import artifacts,paths
from swdb.cli import Failure

FIELDS=('channel','rank','bank_group','bank','row')


def payload_problems(target):
    observation=target.get('functional_observation')
    if observation is None:return []
    problems=[]
    request=observation['request_policy']['transaction_bytes']
    if request is not None and (type(request) is not int or request<1 or request&(request-1)):
        problems.append('transaction_bytes must be a positive power of two or null')
    layout=target.get('dram_address_layout')
    if layout is not None:
        occupied=set()
        for name in FIELDS:
            if name not in layout:problems.append('dram_address_layout missing '+name);continue
            for field in layout[name]:
                lo,width=field['lsb'],field['bits']
                if type(lo) is not int or type(width) is not int or lo<0 or width<1 or lo+width>64:
                    problems.append('invalid address bit field '+name);continue
                bits=set(range(lo,lo+width))
                if bits&occupied:problems.append('overlapping address bit field '+name)
                if request is not None and bits&set(range(request.bit_length()-1)):
                    problems.append('address field overlaps transaction offset '+name)
                occupied|=bits
    return problems


def prepare(store,target,source,*,fixture=False):
    observation=target.get('functional_observation')
    if not observation:raise Failure('live target counting requires functional_observation')
    problems=payload_problems(target)
    if problems:raise Failure('functional observation: '+'; '.join(problems))
    if not fixture:
        # A fabricated debug filename cannot redirect a binding into shipped code.
        # Registered artifact/source protection supplies the enclosing source proof.
        if re.search(r'^\s*#\s*(?:line\b|[0-9]+)',source.read_text(),re.M):
            raise Failure('functional source binding refuses explicit debug #line overrides')
        for command in observation['commands']:
            intrinsic=store.get(command['intrinsic'],'intrinsic')
            if not intrinsic or not set(command['hardware_operations'])<=set(intrinsic.get('hardware_operations',[])):
                raise Failure('functional command lacks its resolvable normative intrinsic/operation binding: '+command['intrinsic'])
            for operation in command['hardware_operations']:
                if store.get(operation,'hardware_operation') is None:
                    raise Failure('functional hardware operation is unavailable: '+operation)
            for alias in command['aliases']+command['target_access_sources']+command['bookkeeping_access_sources']:
                reference=alias.get('source')
                if not reference:raise Failure('functional aliases require pinned shipped source references')
                root={'library':paths.LIBRARY,'repository':paths.ROOT}.get(reference['root'])
                if root is None:raise Failure('functional alias source root unsupported')
                file=(root/reference['path']).resolve()
                if not file.is_relative_to(root.resolve()) or not file.is_file() or artifacts.file_hash(file)!=alias['source_sha256'] or reference['sha256']!=alias['source_sha256']:
                    raise Failure('functional alias shipped source hash differs: '+reference['path'])
                if re.search(r'^\s*#\s*(?:line\b|[0-9]+)',file.read_text(),re.M):
                    raise Failure('functional alias source refuses explicit debug #line overrides')
    env={}
    request=observation['request_policy']
    env['SWDB_LOGICAL_TRANSACTION_BYTES']=str(request['transaction_bytes'] or 0)
    env['SWDB_LOGICAL_COALESCING']=request['read_coalescing']
    env['SWDB_LOGICAL_WINDOW_REQUESTS']=str(observation['window']['requests'] or 0)
    env['SWDB_LOGICAL_PLACEMENT_KNOWN']='1' if observation['placement']['policy']=='isolated_row_aligned_allocations' else '0'
    layout=target.get('dram_address_layout')
    env['SWDB_LOGICAL_LAYOUT_KNOWN']='1' if layout is not None else '0'
    for name in FIELDS:
        env['SWDB_LOGICAL_FIELD_'+name.upper()]=','.join(str(field['lsb'])+':'+str(field['bits']) for field in (layout or {}).get(name,[]))
    return {'target_description_sha256':artifacts.digest(target),
        'functional_observation':observation,'dram_address_layout':layout,
        'layout_sha256':artifacts.digest(layout),
        'request_policy_sha256':artifacts.digest(request),
        'placement_assumption_sha256':artifacts.digest(observation['placement']),
        'window_policy_sha256':artifacts.digest(observation['window']), 'environment':env}


def merge(regions,static,counts,contract,scope):
    if not contract:return
    command_specs=contract['functional_observation']['commands']
    dynamic=counts.get('semantic_commands',{})
    global_missing=list(counts.get('semantic_missing',[]))
    if {site['descriptor'] for site in static.get('semantic_sites',[])}!=set(range(len(command_specs))):global_missing.append('semantic_command_binding')
    fact=lambda v,basis='measured':{'value':v,'basis':'unknown' if v is None else basis,'scope':scope}
    def key(site):return str(site['site'])+':'+str(site['region_index'])
    by_region={region['id']:region for region in regions}
    for site in static.get('semantic_sites',[]):
        region=by_region[site['region']]
        observed=dynamic.get(key(site),{})
        command=command_specs[site['descriptor']]
        value=observed.get('executions',0)
        region['accelerator_calls'].append({'site':site['site'],'event':command['event'],
            'intrinsic':command['intrinsic'],'hardware_operations':command['hardware_operations'],
            'execution_count':fact(value),'active_elements':fact(None if observed.get('active_unknown') else observed.get('active_elements',0)),
            'useful_accesses':fact(None if observed.get('unknown_target') else observed.get('useful_accesses',0)),
            'useful_bytes':fact(None if observed.get('unknown_target') else observed.get('useful_bytes',0)),
            'accounting_domain':'offload','observation_method':'pre_inline_guarded_source_access',
            'missing':observed.get('missing',[])})
    target_hash=contract['target_description_sha256']
    for region in regions:
        sites=[dynamic.get(key(site),{}) for site in static.get('semantic_sites',[]) if site['region']==region['id']]
        missing=sorted(set(global_missing)|{item for site in sites for item in site.get('missing',[])})
        def total(name):
            return None if any(site.get(name,0) is None for site in sites) else sum(site.get(name,0) for site in sites)
        request_count=total('line_requests');groups=total('row_groups')
        if global_missing:request_count=None;groups=None
        staged=None if global_missing or any(site.get('unknown_target') for site in sites) else total('useful_bytes')
        region['address_stream_counts'][target_hash]={'format':'swdb.logical-address-counts.v1',
            'target_description_sha256':target_hash,'level':'derived_logical_transactions',
            **{key:contract[key] for key in ('layout_sha256','request_policy_sha256','placement_assumption_sha256','window_policy_sha256')},
            'state':'incomplete' if missing else 'complete','scope':scope,
            'line_requests':fact(request_count,'inferred'),'row_groups':fact(groups,'inferred'),
            'grouped_row_hits':fact(request_count-groups if request_count is not None and groups is not None else None,'inferred'),
            'grouped_row_hit_fraction':fact((request_count-groups)/request_count if request_count and groups is not None else None,'inferred'),
            'windows':fact(total('windows'),'inferred'),'staged_bytes':fact(staged),
            'missing':missing,'notes':['Allocation-lifetime-relative isolated placement and fixed logical windows are inferred; no physical DRAM placement, hardware request, row state or schedule is observed.']}


def count_problems(data):
    """Same integer/hash/algebra checks for aggregate and trial observations."""
    contract=data.get('observation_contract',{})
    observation=contract.get('functional_observation')
    expected={}
    if observation:
        for problem in payload_problems({'functional_observation':observation,'dram_address_layout':contract.get('dram_address_layout')}):yield 'observation_contract',problem
        expected={'layout_sha256':artifacts.digest(contract.get('dram_address_layout')),
            'request_policy_sha256':artifacts.digest(observation['request_policy']),
            'placement_assumption_sha256':artifacts.digest(observation['placement']),
            'window_policy_sha256':artifacts.digest(observation['window'])}
    groups=[('regions',data['regions'])]+[(f'trials[{i}].regions',trial['regions']) for i,trial in enumerate(data.get('trials',[]))]
    for group,regions in groups:
        for i,region in enumerate(regions):
            location=f'{group}[{i}].address_stream_counts'
            for key,row in region.get('address_stream_counts',{}).items():
                if row.get('format')!='swdb.logical-address-counts.v1':continue
                if observation:
                    if key!=contract.get('requested_target_description_sha256') or row['target_description_sha256']!=key:
                        yield location,'logical counts differ from requested target-description hash'
                    for field,value in expected.items():
                        if row[field]!=value:yield location,'logical counts differ from sealed '+field
                request,groups_count,hits=(row[name]['value'] for name in ('line_requests','row_groups','grouped_row_hits'))
                if request is not None and groups_count is not None:
                    if groups_count>request or (request and groups_count==0):yield location,'row groups must cover the nonzero requests without exceeding them'
                    if hits!=request-groups_count:yield location,'grouped row hits differ from requests minus groups'
                    fraction=row['grouped_row_hit_fraction']['value']
                    if (request==0 and fraction is not None) or (request and fraction!=(request-groups_count)/request):
                        yield location,'grouped row-hit fraction differs from supported counts'
                elif hits is not None or row['grouped_row_hit_fraction']['value'] is not None:
                    yield location,'unknown request/group work cannot establish grouped hits'
                for name in ('line_requests','row_groups','grouped_row_hits','grouped_row_hit_fraction','windows','staged_bytes'):
                    fact=row[name]
                    if fact['value'] is None and fact['basis']!='unknown':yield location,'null logical fact must retain unknown basis'
                if row['state']=='complete' and row['missing']:yield location,'complete logical counts cannot have missing scope'
