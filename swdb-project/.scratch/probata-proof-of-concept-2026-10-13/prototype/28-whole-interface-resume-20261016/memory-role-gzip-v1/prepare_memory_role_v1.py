"""2026-10-16 ET. Source-only memory role-transport assembly, no target imports."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import shlex

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
OLD=WHOLE/'role-normalization-controller-v2'
ACTUAL=WHOLE/'compiler-memory-capture-v1-actual'
RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1'
OUT='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-role-gzip-2baf722f-v1'
def pin(path,expected=None):
    data=path.read_bytes();row={'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if expected is not None:assert row['sha256']==expected
    return row
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def write(name,value):
    (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
closure_path=ACTUAL/'closure-stdout-v1.json'
pin(closure_path,'6e2c6f561885625904cd525ea481244c929539fe1e9855a94a091f4cb243efa2')
reconciliation_path=ACTUAL/'actual-observation-reconciliation-v2.json'
pin(reconciliation_path,'d2a30efc347b0a84174fe641e2436b308e33f896e269d6136fdda0cd4190a8b4')
closure=json.loads(closure_path.read_bytes());metadata=closure['metadata'];observation=metadata['component/compiler-observation.json']
original_policy_path=WHOLE/'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json'
pin(original_policy_path,'d1bfb65ad9bf85aab9cd7dce14ef3b5002134878d86dbaae432814b3082c7cf6')
original_policy=json.loads(original_policy_path.read_bytes())
known={}
def add(row):
    row={key:row[key] for key in ('path','bytes','sha256')}
    assert Path(row['path']).is_absolute()
    assert row['path'] not in known or known[row['path']]=={key:row[key] for key in ('bytes','sha256')}
    known[row['path']]={key:row[key] for key in ('bytes','sha256')}
for row in closure['rows']:add(row)
for row in observation['inputs']:add(row)
for group in observation['groups']:
    for row in group['dependencies']:add(row)
for row in [original_policy['zlib_binding']['physical_interpreter'],*original_policy['zlib_binding']['mapped_compression_objects']]:add(row)
normalizer_path=WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py'
normalizer=pin(normalizer_path,'6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941')
base_path=WHOLE/'streaming-minify-v1/strict_minify_v2.py'
base=pin(base_path,'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897')
old_policy=json.loads((OLD/'source_policy_v2.json').read_bytes())
policy={'date':'2026-10-16 ET','schema':'memory-original-tu-role-gzip-policy-1','original_raw':RAW,'output_root':OUT,
    'physical_inputs':known,'normalizer':normalizer,'strict_base':base,'original_commands':observation['commands'],
    'original_result_scope':metadata['component/result.json']['scope'],'original_observation_profile':'root-observed-four-phase-memory-capture-v1',
    'original_source_fixture':{'bytes':3258,'sha256':'55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'},
    'limits':old_policy['limits'],'expected_duplicate_count':None,'expected_normalized_output_identities':None,
    'scope':'Prospective passive one-pass complete role census/normalization plus full inverse; compiler observation remains observation-only',
    'actual_normalized_writes_admitted':False,'compiler_or_proof_or_public_admission':False}
write('source_policy_v1.json',policy)
template_path=OLD/'controller_template.py';template=template_path.read_text();edits=[]
def replace(old,new):
    global template
    assert template.count(old)==1,old[:100]
    at=template.index(old);template=template[:at]+new+template[at+len(old):];edits.append({'offset':at,'old':old,'new':new})
replace("CENSUS_B64='__CENSUS_B64__'","BASE_B64='__BASE_B64__'")
replace("RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10')",'RAW=Path('+repr(RAW)+')')
replace("OUT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2')",'OUT=Path('+repr(OUT)+')')
replace("'control/controller.py','control/normalizer.py','control/census.json','control/policy.json',",
    "'control/controller.py','control/normalizer.py','control/strict_minify_v2.py','control/policy.json',\n    'component/census.json','component/runtime-before.json','component/runtime-after.json',")
helper='''def check_original_observation(result,observation,commands,policy,original_policy):
    need(original_policy.get('schema')=='t28-three-memory-TU-compiler-observation-1' and original_policy.get('observation_only') is True
        and original_policy.get('source_commit')=='2baf722fdaa6cba24b859eae3172a6f597417d72',
        'exact original memory observation policy profile required')
    need(result.get('accepted') is True and result.get('error') is None and result.get('after_input_errors')==[]
        and result.get('bytecode_cache_present') is False and 'finalization_refusal' not in result
        and result.get('compiler_observation_complete') is True and result.get('source_call_admitted') is False
        and result.get('source_names')==[] and result.get('source_call_count')==0 and result.get('ABI_interpreted') is False
        and result.get('strict_complete_TU_consumer_passed') is False and result.get('native_or_solver_executed') is False
        and result.get('public_proof') is False and result.get('current_0_2') is False and result.get('full_ticket28') is False
        and result.get('scope')==policy['original_result_scope'],'exact successful observation-only memory capture required')
    need(commands==policy['original_commands']==observation.get('commands') and len(commands)==4
        and [row['phase'] for row in commands]==['caller-preprocess','caller-ast','abi-preprocess','abi-ast']
        and all(type(row['returncode']) is int and row['returncode']==0 for row in commands)
        and observation.get('source_commit')=='2baf722fdaa6cba24b859eae3172a6f597417d72'
        and observation.get('original_source_coordinates') is True,'exact four complete memory compiler observations required')

def check_derived_transport(transport,wire):
    value=transport['normalization']
    need(all(type(value[key]) is int and value[key]>=0 for key in ('raw_bytes','duplicate_events','prospective_role_renames',
        'inverse_manifest_rows','unknown_or_mismatched_duplicate_events','normalized_bytes'))
        and (value['raw_bytes'],value['raw_sha256'])==(wire['expanded_bytes'],wire['expanded_sha256'])
        and value['unknown_or_mismatched_duplicate_events']==0 and value['duplicate_events']<=100000
        and value['duplicate_events']==value['prospective_role_renames']==value['inverse_manifest_rows']
        and value['role_normalization_and_expanded_cap_eligible'] is True and value['expanded_role_transport_refused'] is False
        and value['normalized_AST_admitted'] is False and value['normalized_uncompressed_file_written'] is False
        and 0<value['normalized_bytes']<=201326592,'complete derived census/role/extent identity required')
    return value

def check_dependencies(observation,original_policy,helpers):
    need([group['label'] for group in observation['groups']]==['caller','abi'],'complete original group census required')
    for index,group in enumerate(observation['groups']):
        label=group['label'];names=[row['path'] for row in group['dependencies']]
        source='same_thread_memory_v1.cpp' if label=='caller' else 'compiler_abi_probe_v1.cpp'
        required={str(RAW/'control'/source),str(RAW/'control/include/gem5/m5ops.h'),
            original_policy['source_project']+'/apps/dx100/benchmarks/API/MAA.hpp',original_policy['source_project']+'/apps/dx100/benchmarks/API/MAA_gem5.hpp'}
        need(len(names)==len(set(names)) and required<=set(names),'complete source/probe/two-header/stub dependencies required')
        for role,target in (('preprocess_dependency',label),('ast_dependency',label+'-ast')):
            need(helpers['make_dependencies'](Path(group[role]['path']).read_text(),target,RAW/'component')==names,
                'retained AST/preprocessing dependency memberships differ')
        need(group['ast']==observation['commands'][index*2+1]['stdout'],'same original AST/compiler stdout differs')

'''
replace('def main():',helper+'def main():')
replace("normalizer_raw=base64.b64decode(NORMALIZER_B64,validate=True);census_raw=base64.b64decode(CENSUS_B64,validate=True)",
    "normalizer_raw=base64.b64decode(NORMALIZER_B64,validate=True);base_raw=base64.b64decode(BASE_B64,validate=True)")
replace("(len(census_raw),sha(census_raw))==(policy['census']['bytes'],policy['census']['sha256'])","(len(base_raw),sha(base_raw))==(policy['strict_base']['bytes'],policy['strict_base']['sha256'])")
start=template.index('    before=input_check(policy);census=document(census_raw);old_result=')
end=template.index('    for directory in (OUT,OUT/\'control\',OUT/\'component\'):directory.mkdir()',start)
replace(template[start:end],'''    before=input_check(policy)
    old_result=document(read_input(RAW/'component/result.json',policy))
    observation=document(read_input(RAW/'component/compiler-observation.json',policy))
    commands=document(read_input(RAW/'component/commands.json',policy))
    original_policy=document(read_input(RAW/'control/linux_memory_capture_policy_v1.json',policy))
    check_original_observation(old_result,observation,commands,policy,original_policy)
''')
replace("stage('control/controller.py',SOURCE_BYTES);stage('control/normalizer.py',normalizer_raw);stage('control/census.json',census_raw);stage('control/policy.json',policy_raw)",
    "stage('control/controller.py',SOURCE_BYTES);stage('control/normalizer.py',normalizer_raw);stage('control/strict_minify_v2.py',base_raw);stage('control/policy.json',policy_raw)")
replace("entry_path=RAW/'control/linux_compiler_capture_v10.py'","entry_path=RAW/'control/linux_memory_capture_v1.py'")
replace("original_policy=document(read_input(RAW/'control/linux_compiler_capture_policy_v10.json',policy));zlib,zbefore=entry['bind_zlib'](original_policy)",
    "original_policy=document(read_input(RAW/'control/linux_memory_capture_policy_v1.json',policy));zlib,zbefore=entry['bind_zlib'](original_policy)\n"
    "    helpers=entry['original_helpers'](RAW/'control/linux_native86_entry_v4.py')\n"
    "    closed_path=RAW/'control/closed_python_surface.py';closed_ns=load(read_input(closed_path,policy),str(closed_path),policy['physical_inputs'][str(closed_path)])\n"
    "    import types\n    closed=types.SimpleNamespace(**closed_ns)\n"
    "    runtime_before=helpers['physical_runtime'](original_policy,closed)\n"
    "    need(runtime_before==document(read_input(RAW/'capture-runtime-before.json',policy)),'current full physical runtime differs from original observation')\n"
    "    check_dependencies(observation,original_policy,helpers);save('component/runtime-before.json',runtime_before)")
replace("base_path=RAW/'control/strict_minify_v2.py';codec_path=RAW/'control/lossless_gzip_v2.py'\n    base=load(read_input(base_path,policy),str(base_path),policy['physical_inputs'][str(base_path)])",
    "base_path=OUT/'control/strict_minify_v2.py';codec_path=RAW/'control/lossless_gzip_v2.py'\n    base=load(base_raw,str(base_path),policy['strict_base'])")
start=template.index("    transformed=transport['normalization'];observed=census['census']")
end=template.index("    with (OUT/'component/caller.normalized.json.gz').open('rb') as source:",start)
replace(template[start:end],"    transformed=check_derived_transport(transport,gzip_receipt)\n")
replace("    after=input_check(policy);need(after==before,'selected original/source/runtime inputs changed')",
    "    runtime_after=helpers['physical_runtime'](original_policy,closed)\n"
    "    need(runtime_after==runtime_before,'full physical runtime membership changed')\n"
    "    check_dependencies(observation,original_policy,helpers);save('component/runtime-after.json',runtime_after)\n"
    "    after=input_check(policy);need(after==before,'selected original/source/runtime inputs changed')")
replace("pin(OUT/'control/census.json')['sha256']==policy['census']['sha256']","pin(OUT/'control/strict_minify_v2.py')['sha256']==policy['strict_base']['sha256']")
replace("save('component/transport.json',transport);save('component/inverse.json',inverse);save('component/inputs-after.json',after)",
    "save('component/census.json',transformed);save('component/transport.json',transport);save('component/inverse.json',inverse);save('component/inputs-after.json',after)")
replace("'schema':'passive-paired-type-gzip-transform-result-2'","'schema':'passive-memory-paired-type-gzip-transform-result-1'")
replace("'original_capture_accepted':False,\n        'original_capture_refusal':old_result['error'],",
    "'original_compiler_observation_accepted':True,'original_AST_ABI_source_call_admitted':False,\n        'source_fixture_sha256':policy['original_source_fixture']['sha256'],'original_observation':pin(RAW/'component/compiler-observation.json'),")
replace("'original_capture_accepted':False,'source_call_ABI_public_or_full28_admission':False,'wall_seconds':time.monotonic()-START}",
    "'original_compiler_observation_accepted':True,'source_call_ABI_public_or_full28_admission':False,'wall_seconds':time.monotonic()-START}")
(HERE/'controller_template_v1.py').write_text(template)
rendered=template.replace('__POLICY_B64__',base64.b64encode((HERE/'source_policy_v1.json').read_bytes()).decode()).replace('__NORMALIZER_B64__',
    base64.b64encode(normalizer_path.read_bytes()).decode()).replace('__BASE_B64__',base64.b64encode(base_path.read_bytes()).decode())
entry_path=HERE/'memory_role_controller_v1.py';entry_path.write_text(rendered);ast.parse(rendered)
bootstrap=(OLD/'bootstrap_v2.py').read_text().replace(str(old_policy['output_root']),OUT)
old_files=ast.literal_eval(next(node for node in ast.parse(bootstrap).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OUTPUT_PATHS' for t in node.targets)).value)
files=ast.literal_eval(next(node for node in ast.parse(template).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in node.targets)).value)
bootstrap=bootstrap.replace(repr(old_files),repr(tuple(OUT+'/'+name for name in sorted(files))))
old_entry=pin(OLD/'normalization_controller_v2.py');entry=pin(entry_path)
bootstrap=bootstrap.replace(str(old_entry['bytes']+1),str(entry['bytes']+1)).replace('len(payload)!='+str(old_entry['bytes']),'len(payload)!='+str(entry['bytes'])).replace(old_entry['sha256'],entry['sha256'])
(HERE/'bootstrap_v1.py').write_text(bootstrap);ast.parse(bootstrap)
command=json.loads((OLD/'command_v2.json').read_bytes())
command['stdin']=entry;command['source_policy']=pin(HERE/'source_policy_v1.json');command['bootstrap']=pin(HERE/'bootstrap_v1.py')
command['python_argv']=[original_policy['python'],'-I','-B','-c',bootstrap,OUT]
command['remote_argv']=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','960s','/usr/bin/env','-i',
    *[key+'='+value for key,value in command['closed_environment'].items()],*command['python_argv']]
command['remote_shell_command']=shlex.join(command['remote_argv'])
command['scope']='INERT memory observation-only source55b9 byte transport; independent review and new root once-only admission required'
command['prior_once_only_census_admission_reused']=False
write('command_v1.json',command)
restored=template
for row in reversed(edits):
    at=row['offset'];assert restored[at:at+len(row['new'])]==row['new'];restored=restored[:at]+row['old']+restored[at+len(row['new']):]
assert restored.encode()==template_path.read_bytes()
write('controller-inverse-v1.json',{'date':'2026-10-16 ET','predecessor_template':pin(template_path),
    'successor_template':pin(HERE/'controller_template_v1.py'),'edits':edits,'exact_predecessor_reconstructed':True,
    'normalizer_bytes_unchanged':normalizer,'strict_base_new_staged_input':base,
    'actual_memory_source_observation':pin(reconciliation_path),'actual_metadata':pin(closure_path),
    'expected_derived_hashes_and_duplicate_count':None,'actual_transform':False})
print(json.dumps({'entry':entry,'policy':command['source_policy'],'command':pin(HERE/'command_v1.json'),
    'known_physical_inputs':len(known),'fixed_outputs':len(files)},sort_keys=True))
