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
    for command in observation['commands']:
        none=command.get('memory_effect','read')=='none'
        if none:
            if command['target_access_sources'] or any(alias['memory_base_argument'] is not None for alias in command['aliases']):
                problems.append('no-memory command requires no target source or memory operand')
            if command.get('active_elements_policy')!='not_applicable':problems.append('no-memory active-element scope must be not_applicable')
        elif not command['target_access_sources'] or any(alias['memory_base_argument'] is None for alias in command['aliases']):
            problems.append('read command requires target access source and memory operand')
        if command.get('active_elements_policy')=='observed_target_reads' and not command.get('target_reads_per_active_element'):
            problems.append('observed-target active elements require explicit reads-per-element relation')
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


def prepare(store,target,source,*,fixture=False,compile_flags=()):
    observation=target.get('functional_observation')
    if not observation:raise Failure('live target counting requires functional_observation')
    problems=payload_problems(target)
    if problems:raise Failure('functional observation: '+'; '.join(problems))
    bindings={'format':'swdb.functional-source-bindings.v1','records':{},'library_entries':{},'compiled_views':[]}
    if not fixture:
        from swdb.intrinsic_source_views import require_compiled_view,source_file
        from swdb.library import Library
        library=Library(paths.HOME/'library',store)
        # A fabricated debug filename cannot redirect a binding into shipped code.
        # Registered artifact/source protection supplies the enclosing source proof.
        if re.search(r'^\s*#\s*(?:line\b|[0-9]+)',source.read_text(),re.M):
            raise Failure('functional source binding refuses explicit debug #line overrides')
        for command in observation['commands']:
            intrinsic=store.get(command['intrinsic'],'intrinsic')
            if not intrinsic or not set(command['hardware_operations'])<=set(intrinsic.get('hardware_operations',[])):
                raise Failure('functional command lacks its resolvable normative intrinsic/operation binding: '+command['intrinsic'])
            if (command.get('memory_effect','read')=='none')!=(intrinsic.get('memory_kind')=='none'):
                raise Failure('functional command memory effect differs from normative intrinsic')
            proof=require_compiled_view(intrinsic,compile_flags)
            bindings['compiled_views'].append(proof)
            bindings['records'][intrinsic['id']]=artifacts.digest(intrinsic)
            for operation in command['hardware_operations']:
                record=store.get(operation,'operation')
                if record is None:raise Failure('functional hardware operation is unavailable: '+operation)
                bindings['records'][operation]=artifacts.digest(record)
            view=intrinsic['source_view']
            if not any(alias['role']=='command' and alias.get('source')==view['source']
                and alias.get('debug_name','').split('<')[0]==intrinsic['name'] for alias in command['aliases']):
                raise Failure('functional command primary alias differs from exact intrinsic source_view')
            for alias in command['aliases']+command['target_access_sources']+command['bookkeeping_access_sources']:
                reference=alias.get('source')
                if not reference:raise Failure('functional aliases require pinned shipped source references')
                file=source_file(reference)
                if reference['sha256']!=alias['source_sha256']:
                    raise Failure('functional alias shipped source hash differs: '+reference['path'])
                if re.search(r'^\s*#\s*(?:line\b|[0-9]+)',file.read_text(),re.M):
                    raise Failure('functional alias source refuses explicit debug #line overrides')
            entry=intrinsic.get('library_entry',{})
            item=library.get(entry.get('id'))
            if item is None or item.get('intrinsic_record')!=intrinsic['id'] or item.get('hardware_operations')!=intrinsic['hardware_operations'] or library.content_sha256(entry['id'])!=entry.get('content_sha256'):
                raise Failure('functional source_view requires its exact normative library entry')
            file=library.files[entry['id']]
            if file.resolve()!=(paths.HOME/artifacts.relative_path(entry.get('path',''))).resolve():
                raise Failure('functional source_view library entry path differs')
            bindings['library_entries'][entry['id']]=entry['content_sha256']
            for pin in library.dependency_pins(entry['id']):bindings['library_entries'][pin['id']]=pin['content_sha256']
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
        'window_policy_sha256':artifacts.digest(observation['window']), 'environment':env,
        'normative_bindings':None if fixture else bindings}


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
        active=None if observed.get('active_unknown') else observed.get('active_elements',0)
        if command.get('active_elements_policy')=='observed_target_reads':
            reads=observed.get('useful_accesses',0);relation=command['target_reads_per_active_element']
            active=None if observed.get('unknown_target') or reads%relation else reads//relation
        region['accelerator_calls'].append({'site':site['site'],'event':command['event'],
            'intrinsic':command['intrinsic'],'hardware_operations':command['hardware_operations'],
            'execution_count':fact(value),'active_elements':fact(active),
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


def binding_problems(data,store):
    """Verify outcome-free normative identities independently of a counted payload label."""
    contract=data.get('observation_contract',{})
    pins=contract.get('normative_bindings')
    if pins is None:return []  # Historical/fixture receipts keep their original contract.
    from swdb.intrinsic_source_views import require_compiled_view
    from swdb.library import Library
    library=Library(paths.HOME/'library',store);issues=[]
    commands=contract.get('functional_observation',{}).get('commands',[])
    required={c['intrinsic'] for c in commands}|{op for c in commands for op in c['hardware_operations']}
    if set(pins['records'])!=required:issues.append('functional normative record pin coverage differs')
    for rid,digest in pins['records'].items():
        record=store.get(rid)
        if record is None or artifacts.digest(record)!=digest:issues.append('functional normative record changed: '+rid)
    for rid,digest in pins['library_entries'].items():
        if library.get(rid) is None or library.content_sha256(rid)!=digest:issues.append('functional normative library entry changed: '+rid)
    flags=data['source']['build_flags']+data['toolchain'].get('compiler_flags',[])
    if len(pins['compiled_views'])!=len(commands):issues.append('functional compiled view coverage differs')
    for proof in pins['compiled_views']:
        intrinsic=store.get(proof.get('intrinsic'),'intrinsic')
        if intrinsic is None:continue
        try:
            if proof!=require_compiled_view(intrinsic,flags):issues.append('functional compiled source_view differs: '+intrinsic['id'])
        except Failure as exc:issues.append(str(exc))
    return issues
