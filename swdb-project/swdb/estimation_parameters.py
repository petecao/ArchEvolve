"""Immutable parameter-fill versions through the shared guarded provider launcher.
Created: 2026-10-06 ET. The provider receives allowlisted facts, never raw records.
"""
import copy
import fcntl
import json
import math
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from swdb import artifacts, provider_roles, rewrite, writer
from swdb.cli import Failure
from swdb.estimation_contract import INPUT_SCHEMAS, OUTPUT_SCHEMA, LOGICAL_NAMES
from swdb.store import Store

# Generic formula contracts, not target/kernel IDs. Unknown model metadata is
# refused rather than treating an arbitrary numeric field as a physics parameter.
PARAMETER_UNITS={
    'compute_throughput':{name+'_ops_per_s':'operations/s' for name in ('integer','floating_point','branch','atomic')},
    'streaming_bandwidth':{'bytes_per_s':'bytes/s'},
    'requests_in_flight_latency':{'dependent_latency_s':'seconds/load','effective_requests_per_thread':'requests/thread'},
    'cache_fit':{'capacity_bytes':'bytes','bytes_per_s':'bytes/s','cold_bytes_per_s':'bytes/s'},
    'offload_setup':{'seconds_per_event':'seconds/event'},
    'reorder_window_rows':{'row_miss_service_s':'seconds/request','row_hit_service_s':'seconds/request','effective_memory_parallelism':'requests'},
    'fetch_queue':{'queue_entries':'entries','fetch_latency_s':'seconds/request','admission_requests_per_s':'requests/s'},
    'tile_staging':{'staging_bytes_per_s':'bytes/s'}}
PROMPT='''Fill only the named unknown analytic parameters using the supplied structural facts and physics.\nReturn a value with basis estimated and a specific reason, or null with basis unknown and explain why.\nPreserve units and parameter identities. Never fill missing observations, layout, runtime coverage or composition policies.\nThese files omit timings, PMU ratios, evaluator code, candidate code and prior provider history.\nDo not seek other information or run collectors. These values are frozen once; do not tune them to performance outcomes.'''


def domain(unit,model,name):
    from swdb.analytic_count_reuse import RATES
    if name not in RATES.get(model,{}):return 'unsupported'
    return 'positive_integer' if unit in {'bytes','entries'} else 'positive'


def require_service_compatibility(target):
    binding=target.get('extensions',{}).get('cpu_services_binding')
    if binding is None:return
    if not isinstance(binding,dict) or binding.get('format')!='swdb.cpu-services-binding.v1':
        raise Failure('invalid structural service compatibility binding')
    rows=binding.get('compatibility')
    if not isinstance(rows,list):raise Failure('invalid structural service compatibility rows')
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('missing'),list):
            raise Failure('invalid structural service compatibility premises')
        scopes=row.get('scopes',[])
        if not isinstance(scopes,list) or any(not isinstance(scope,dict) or
                not isinstance(scope.get('missing'),list) for scope in scopes):
            raise Failure('invalid structural service compatibility scopes')
        if row['missing'] or any(scope['missing'] for scope in scopes):
            # Binding incompatibility withholds a value; it does not establish
            # an unknown numerical rate which an estimator may replace.
            raise Failure('structural service compatibility gap: '+str(row.get('parameter','unknown')))


def parameters(target):
    require_service_compatibility(target)
    known=[];unknown=[]
    for i,mechanism in enumerate(target['mechanisms']):
        model=mechanism['model']
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,79}',model):raise Failure('unsupported mechanism identity')
        for name,fact in sorted(mechanism['parameters'].items()):
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,79}',name):raise Failure('unsupported parameter identity')
            if not re.fullmatch(r'[a-zA-Z0-9_ /.-]{1,80}',fact['unit']):raise Failure('unsupported parameter unit')
            if PARAMETER_UNITS.get(model,{}).get(name)!=fact['unit']:
                raise Failure('unsupported parameter contract: '+model+'.'+name+' / '+fact['unit'])
            row={'parameter':f'mechanisms[{i}].parameters.{name}','model':model,'unit':fact['unit']}
            if fact['value'] is None:unknown.append({**row,'domain':domain(fact['unit'],model,name)})
            else:known.append({**row,'value':fact['value'],'basis':fact['basis']})
    return {'format':'swdb.estimation-parameters.v1','target_sha256':artifacts.digest(target),
        'threads':target['threads'],'known':known,'unknown':unknown}


def count(value):
    value=value.get('value') if isinstance(value,dict) else value
    return value if type(value) is int and value>=0 else None


def regions(rows):
    result=[]
    for region in rows:
        groups={}
        for access in region['access_patterns']:
            shape=access['address_shape']['value'];update=access['update_kind']
            if update not in ('read','write','compare-and-swap','add-update','min-max-update'):update='unknown'
            key=(shape,update,count(access['element_bytes']))
            group=groups.setdefault(key,{'shape':shape,'update':update,'element_bytes':key[2],
                'elements':0,'useful_bytes':0})
            for field,source in [('elements','element_count'),('useful_bytes','bytes_accessed')]:
                value=count(access[source]);group[field]=None if value is None or group[field] is None else group[field]+value
        logical=[]
        for description,facts in sorted(region.get('address_stream_counts',{}).items()):
            logical.append({'description_sha256':artifacts.digest(description),**{name:count(facts.get(name)) for name in LOGICAL_NAMES}})
        result.append({'region_sha256':artifacts.digest(region['id']),
            'operations':[{'category':name,'count':count(region['operation_counts'][name])}
                for name in ('integer','floating_point','branch','atomic')],
            'footprint_bytes':count(region['footprint_bytes']),'active_workers':count(region.get('active_workers')),
            'access_groups':list(groups.values()),'logical_counts':logical})
    return result


def characterization_view(characterization):
    binding=characterization.get('binding',{})
    trials=characterization.get('trials') or [{'position':0,'regions':characterization['regions']}]
    return {'format':'swdb.estimation-characterization.v1','record_sha256':artifacts.digest(characterization),
        'input_sha256':binding.get('input_record_sha256') or artifacts.digest(characterization['input']),
        'roi_sha256':artifacts.digest(binding.get('roi')),
        'source_ir_sha256':characterization['static_analysis']['source_ir_sha256'],
        'trials':[{'position':t['position'],'regions':regions(t['regions'])} for t in trials]}



def profile_view(profile):
    return {'format':'swdb.estimation-profile.v1','record_sha256':artifacts.digest(profile),
        'regions':[{'region_sha256':artifacts.digest(row.get('id')),
            'kind':row.get('kind') if row.get('kind') in ('loop','function','statement') else 'unknown'}
            for row in profile.get('regions',[]) if isinstance(row,dict)]}

def project(characterization,profile,target):
    char=characterization_view(characterization)
    prof=profile_view(profile)
    objects={'characterization.json':char,'profile.json':prof,'parameters.json':parameters(target)}
    files={}
    for name,data in objects.items():
        problems=list(Draft202012Validator(INPUT_SCHEMAS[name]).iter_errors(data))
        if problems:raise Failure('invalid estimation projection '+name+': '+problems[0].message)
        files[name]=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)
    checked_input_files(files)
    provider_roles.checked_inputs(files)
    return files,objects




def checked_input_files(files):
    if set(files)!=set(INPUT_SCHEMAS):raise Failure('invalid estimation input: exact three-file contract required')
    for name,text in files.items():
        try:
            data=json.loads(text)
            json.dumps(data,allow_nan=False)
        except (ValueError,TypeError,RecursionError):
            raise Failure('invalid estimation input: finite JSON required') from None
        errors=list(Draft202012Validator(INPUT_SCHEMAS[name]).iter_errors(data))
        if errors:raise Failure('invalid estimation input '+name+': '+errors[0].message)
        if name=='parameters.json':
            seen=set()
            for category in ('known','unknown'):
                for row in data[category]:
                    match=re.fullmatch(r'mechanisms\[([0-9]+)\]\.parameters\.([a-z][a-z0-9_]{0,79})',row['parameter'])
                    if not match or row['parameter'] in seen or PARAMETER_UNITS.get(row['model'],{}).get(match[2])!=row['unit']:
                        raise Failure('invalid estimation input: unsupported or duplicate parameter contract')
                    seen.add(row['parameter'])
                    if category=='unknown' and row['domain']!=domain(row['unit'],row['model'],match[2]):
                        raise Failure('invalid estimation input: parameter domain differs')
                    if category=='known' and (not finite_number(row['value']) or row['value']<=0):
                        raise Failure('invalid estimation input: invalid known numeric parameter')
    return files


def reason_source(row,output):
    return row['reason']+' [Frozen estimation output '+artifacts.digest(output)+', '+row['parameter']+']'

def finite_number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)):return False
    try:return math.isfinite(value)
    except OverflowError:return False

def checked_output(output,parameter_input):
    errors=list(Draft202012Validator(OUTPUT_SCHEMA).iter_errors(output))
    if errors:raise Failure('invalid estimation output: '+errors[0].message)
    unknown={row['parameter']:row for row in parameter_input['unknown']};seen=set()
    for row in output['parameters']:
        path=row['parameter']
        if path not in unknown:raise Failure('parameter is already known or not a declared unknown: '+path)
        if path in seen:raise Failure('duplicate parameter: '+path)
        seen.add(path);expected=unknown[path];value=row['value']
        if row['unit']!=expected['unit']:raise Failure('parameter unit differs: '+path)
        if value is None:
            if row['basis']!='unknown':raise Failure('null parameter requires basis unknown')
        elif (row['basis']!='estimated' or not finite_number(value) or value<=0 or expected['domain']=='unsupported'
              or expected['domain']=='positive_integer' and not float(value).is_integer()):
            raise Failure('parameter value is outside its declared domain: '+path)
    if seen!=set(unknown):raise Failure('output must answer every declared unknown, using null for unresolved values')
    return output


def fill(args):
    from swdb.analytic import _load
    target=_load(Store(args.records),args.target_description,'target_description')
    # One successful fill per target ID/version, including concurrent launchers.
    with (Path(args.records)/('.estimation-'+artifacts.digest([target['id'],target['version']])+'.lock')).open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        try:return _fill(args)
        finally:fcntl.flock(handle,fcntl.LOCK_UN)


def _fill(args):
    from swdb.analytic import _load
    store=Store(args.records)
    target=_load(store,args.target_description,'target_description')
    if store.get(args.id) is not None:raise Failure('output record ID already exists')
    characterization=_load(store,args.characterization,'workload_characterization')
    profile=store.get(args.profile)
    if profile is None:
        from swdb import access
        try:profile=access.read_record(Path(args.profile))
        except (OSError,ValueError) as exc:raise Failure('profile is not a readable record: '+str(exc)) from None
    if not isinstance(profile,dict):raise Failure('expected a profile mapping')
    if profile.get('kind') not in ('profile','profile_package','region_profile'):raise Failure('expected a profile record')
    profile=_load(store,args.profile,profile['kind'])
    from swdb.archevolve import require_team_safe
    require_team_safe(store,target,characterization,profile,command='fill-target-parameters')
    subject=characterization['subject']
    registered=store.get(subject['id'],subject['kind']) or {}
    implementation=subject['id'] if subject['kind']=='implementation' else registered.get('implementation')
    if profile.get('implementation')!=implementation or profile.get('candidate') not in (None,subject['id']):
        raise Failure('profile and characterization subjects differ')
    source_identity=characterization.get('binding',{}).get('subject_source_identity',{})
    snapshot=source_identity.get('source_snapshot')
    if snapshot and profile.get('source_snapshot')!=snapshot:
        raise Failure('profile and characterization registered source snapshots differ')
    if target['threads']!=characterization['binding']['threads']:
        raise Failure('target and characterization thread identities differ')
    if 'parameter_estimation' in target:raise Failure('target version already contains frozen estimation output')
    base_sha=artifacts.digest(target)
    if any((r.data.get('parameter_estimation',{}).get('base_snapshot',{}).get('id'),
            r.data.get('parameter_estimation',{}).get('base_snapshot',{}).get('version'))==(target['id'],target['version'])
            for r in store.of_kind('target_description')):
        raise Failure('target version already has frozen estimation output')
    from swdb import analytic_binding
    if characterization.get('binding',{}).get('state')=='verified':
        problems=analytic_binding.verify_binding(characterization,store)
        if problems:raise Failure('registered characterization binding: '+problems[0])
    from swdb.analytic_count_reuse import resolve
    resolve(characterization,target)
    try:files,objects=project(characterization,profile,target)
    except (ValueError,TypeError,RecursionError) as exc:
        raise Failure('input records must contain finite acyclic JSON facts: '+str(exc)) from None
    if not objects['parameters.json']['unknown']:raise Failure('target version has no unknown numeric parameters')
    if args.prepare_only:
        folder=Path(args.output);folder.mkdir(parents=True,exist_ok=False)
        inputs=folder/'inputs';inputs.mkdir()
        for name,text in files.items():(inputs/name).write_text(text)
        plan={'format':'swdb.estimation-preparation.v1','state':'prepared','provider_launched':False,
            'total_input_bytes':sum(len(text.encode()) for text in files.values()),
            'base_sha256':base_sha,'input_sha256s':{name:artifacts.digest(data) for name,data in objects.items()},
            'unknown_parameters':objects['parameters.json']['unknown'],
            'projection':projection(files,objects,characterization,profile,target)}
        (folder/'plan.json').write_text(json.dumps(plan,indent=2,allow_nan=False))
        return plan
    config=rewrite.configuration(args.provider_config)
    if config['kind']!='external_fixture' and characterization.get('binding',{}).get('state')!='verified':
        raise Failure('real estimation requires verified registered characterization')
    output,metadata=provider_roles.run('estimation',files,PROMPT,config,args.output)
    checked_output(output,objects['parameters.json'])
    updated=copy.deepcopy(target);updated['id']=args.id
    updated['version']=str(target['version'])+'.estimated.'+artifacts.digest(output)[:16]
    updated['status']='draft';updated['created']=updated['updated']=writer.today()
    for row in output['parameters']:
        match=re.fullmatch(r'mechanisms\[([0-9]+)\]\.parameters\.(.+)',row['parameter'])
        fact=updated['mechanisms'][int(match[1])]['parameters'][match[2]]
        if row['value'] is not None:fact.update(value=row['value'],basis='estimated',source=reason_source(row,output))
    updated['parameter_estimation']={'format':'swdb.parameter-estimation.v1','base_sha256':base_sha,
        'base_snapshot':target,'input_sha256s':{name:artifacts.digest(data) for name,data in objects.items()},
        'input_record_sha256s':{'characterization':artifacts.digest(characterization),'profile':artifacts.digest(profile)},
        'input_snapshots':objects,
        'output':output,'output_sha256':artifacts.digest(output),'provider':{
            'kind':config['kind'],'classification':metadata['classification'],
            'model':metadata.get('model'),'effort':metadata.get('effort'),
            'cli_version':metadata.get('cli_version'),'executable_sha256':metadata.get('executable_sha256'),
            'prompt_sha256':metadata['prompt_sha256'],'output_schema_sha256':artifacts.digest(OUTPUT_SCHEMA),
            'receipt_sha256':artifacts.file_hash(Path(args.output)/'provider.json'),
            'workspace_manifest_sha256':artifacts.digest(metadata['workspace_manifest']),
            'audit_sha256':artifacts.digest(metadata['audit']),'audit_passed':metadata['audit']['passed'],
            'guard_enforced':(metadata.get('guard_policy') or {}).get('enforced',False),
            'guard_passed':(metadata.get('guard_result') or {}).get('passed'),
            'guard_policy_sha256':artifacts.digest(metadata.get('guard_policy')),
            'guard_result_sha256':artifacts.digest(metadata.get('guard_result')),
            'lane_sha256':artifacts.digest(metadata.get('lane')),
            'login_copy_deleted':metadata['workspace_manifest']['login_copy_deleted']}}
    resolve(characterization,updated)
    updated['parameter_estimation']['projection']=projection(files,objects,characterization,profile,target)
    updated['parameter_estimation']['input_records']=[
        {'kind':raw['kind'],'id':raw['id'],'sha256':artifacts.digest(raw),
         'stored':store.get(raw['id'],raw['kind'])==raw}
        for raw in (target,characterization,profile)]
    updated['parameter_estimation']['identity_sha256']=artifacts.digest(updated['parameter_estimation'])
    require_team_safe(store,updated,command='fill-target-parameters')
    writer.commit(args.records,new=[updated])
    return updated



def projection(files,objects,characterization,profile,target):
    return {
        'format':'swdb.estimation-projection.v1',
        'policy':'typed_native_counts_and_profile_structure_only',
        'source_sha256s':{'builder':artifacts.file_hash(Path(__file__)),
            'contract':artifacts.file_hash(Path(__file__).with_name('estimation_contract.py'))},
        'files':[{'name':name,'bytes':len(text.encode()),'sha256':artifacts.digest(objects[name])} for name,text in files.items()],
        'omitted_raw_fields':[{'input':name,'field':key,'sha256':artifacts.digest(value)}
            for name,raw in [('characterization',characterization),('profile',profile),('target',target)]
            for key,value in sorted(raw.items())]}

def register_cli(commands):
    from swdb import paths
    sub=commands.add_parser('fill-target-parameters',help='freeze estimated unknown values in a new target-description version')
    sub.add_argument('--records',type=Path,default=paths.RECORDS)
    for name in ('characterization','profile','target-description','id'):sub.add_argument('--'+name,required=True)
    sub.add_argument('--provider-config',type=Path,help='required for execution; omitted for preparation only')
    sub.add_argument('--prepare-only',action='store_true',help='export sanitized inputs and hashes without credentials or provider execution')
    sub.add_argument('--output',type=Path,required=True,help='new isolated provider workspace and audit directory')
    sub.add_argument('--format',choices=['yaml','json'],default='yaml')
    sub.set_defaults(analytic_handler=fill)


def payload_problems(target):
    receipt=target.get('parameter_estimation')
    if receipt is None:return
    try:artifacts.digest(receipt)
    except (ValueError,TypeError,RecursionError):
        yield 'parameter_estimation','receipt requires finite acyclic JSON facts';return
    base=receipt['base_snapshot']
    if 'parameter_estimation' in base:
        yield 'parameter_estimation','base version already has frozen estimation output';return
    if artifacts.digest(base)!=receipt['base_sha256']:
        yield 'parameter_estimation','base snapshot differs from its content hash'
    if artifacts.digest({key:value for key,value in receipt.items() if key!='identity_sha256'})!=receipt['identity_sha256']:
        yield 'parameter_estimation','receipt differs from its sealed identity'
    try:base_parameters=parameters(base)
    except Failure as exc:
        yield 'parameter_estimation',str(exc);return
    snapshots=receipt['input_snapshots']
    for name,snapshot in snapshots.items():
        if artifacts.digest(snapshot)!=receipt['input_sha256s'][name]:
            yield 'parameter_estimation','sanitized input snapshot differs from its recorded hash: '+name
    if snapshots['parameters.json']!=base_parameters:
        yield 'parameter_estimation','parameter input differs from frozen base facts'
    for kind,name in [('characterization','characterization.json'),('profile','profile.json')]:
        if snapshots[name]['record_sha256']!=receipt['input_record_sha256s'][kind]:
            yield 'parameter_estimation','projection full-record hash differs: '+kind
    files=receipt['projection']['files']
    if len({row['name'] for row in files})!=3:
        yield 'parameter_estimation','duplicate projected file identity'
    for row in files:
        snapshot=snapshots[row['name']]
        raw=json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if row['sha256']!=artifacts.digest(snapshot) or row['bytes']!=len(raw):
            yield 'parameter_estimation','projected file hash or byte size differs'
    if sum(row['bytes'] for row in files)>rewrite.JSON_OUTPUT_LIMIT:
        yield 'parameter_estimation','complete role inputs exceed 10 MiB'
    output=receipt['output']
    if artifacts.digest(output)!=receipt['output_sha256']:
        yield 'parameter_estimation','provider output differs from its content hash'
    try:checked_output(output,base_parameters)
    except Failure as exc:
        yield 'parameter_estimation',str(exc);return
    expected=copy.deepcopy(base)
    for row in output['parameters']:
        match=re.fullmatch(r'mechanisms\[([0-9]+)\]\.parameters\.(.+)',row['parameter'])
        if row['value'] is not None:
            expected['mechanisms'][int(match[1])]['parameters'][match[2]].update(
                value=row['value'],basis='estimated',source=reason_source(row,output))
    expected['version']=str(base['version'])+'.estimated.'+artifacts.digest(output)[:16]
    ignored={'id','status','created','updated','parameter_estimation'}
    if {k:v for k,v in expected.items() if k not in ignored}!={k:v for k,v in target.items() if k not in ignored}:
        yield 'parameter_estimation','frozen values or known target facts differ from the original plus provider output'
    provider=receipt['provider']
    from swdb.provider_adapters import PINS
    if provider['kind'] in PINS:
        if not provider['guard_enforced'] or provider['guard_passed'] is not True:
            yield 'parameter_estimation','actual estimation requires a passing enforced provider guard'
        if provider['classification']!='rewrite_provider' or any(provider[k]!=v for k,v in PINS[provider['kind']].items()):
            yield 'parameter_estimation','actual provider pins or classification differ'
    elif provider['classification']!='contract_fixture':
        yield 'parameter_estimation','fixture provider cannot establish actual evidence'
    if provider['login_copy_deleted'] is not True:
        yield 'parameter_estimation','provider login copy was not cleaned up'
    if provider['output_schema_sha256']!=artifacts.digest(OUTPUT_SCHEMA):
        yield 'parameter_estimation','output wire contract differs'


def binding_problems(target,store):
    receipt=target.get('parameter_estimation')
    if receipt is None:return
    base=receipt['base_snapshot'];key=(base['id'],base['version'])
    siblings=[row for row in store.of_kind('target_description')
        if (row.data.get('parameter_estimation',{}).get('base_snapshot',{}).get('id'),
            row.data.get('parameter_estimation',{}).get('base_snapshot',{}).get('version'))==key]
    if len(siblings)>1:yield 'multiple frozen outputs for the same base target ID/version'
    for row in receipt['input_records']:
        current=store.get(row['id'],row['kind'])
        if row['stored'] and (current is None or artifacts.digest(current)!=row['sha256']):
            yield 'frozen parameter input differs: '+row['kind']+'/'+row['id']
    for row in receipt['input_records']:
        if row['kind']=='workload_characterization' and row['stored']:
            current=store.get(row['id'],row['kind'])
            if current and characterization_view(current)!=receipt['input_snapshots']['characterization.json']:
                yield 'projection differs from canonical characterization'
        elif row['kind'] in ('profile','profile_package','region_profile') and row['stored']:
            current=store.get(row['id'],row['kind'])
            if current:
                if profile_view(current)!=receipt['input_snapshots']['profile.json']:
                    yield 'projection differs from canonical profile'
