"""Build source/policy for a guarded memory observation, never execute it."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
OLD=WHOLE/'normalized-unit-observation-v1'
OUT=HERE/'observer'
MODULES=OUT/'modules'
MODULES.mkdir(parents=True,exist_ok=True)


def pin(path, remote=None):
    raw=path.read_bytes()
    return {'path':str(path) if remote is None else remote,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


rows=[]
def module(name,path,basename=None):
    raw=path.read_bytes();file=basename or path.name
    (MODULES/file).write_bytes(raw)
    rows.append({'module':name,'file':file,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})


old_manifest=json.loads((OLD/'fixed-modules-v1.json').read_bytes())
for row in old_manifest['modules'][:8]:
    module(row['module'],OLD/'modules'/row['file'])
for name in ('memory_normalized_compiler_adapter_v1','memory_normalized_capture_ingress_v1'):
    module('swdb._dx100_whole.'+name,HERE/'proposed'/str(name+'.py'))
module('swdb._dx100_whole.source_memory_selection_v1',WHOLE/'source-memory-selection-v1/source_memory_selection_v1.py')
module('swdb._dx100_whole.memory_source_preparation_v1',HERE/'proposed/memory_source_preparation_v1.py')
manifest={'schema':'fixed-private-memory-observer-modules-1','modules':rows,
    'private_staged_observer_not_installed_public_producer':True,'actual_execution':False}
manifest_raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
(OUT/'fixed-memory-modules-v1.json').write_bytes(manifest_raw)
(MODULES/'memory_capture_facts_v1.json').write_bytes((HERE/'proposed/memory_capture_facts_v1.json').read_bytes())
source=(OLD/'observe_entry_v1.py').read_text();edits=[]
def replace(old,new):
    global source
    assert source.count(old)==1,old[:70]
    source=source.replace(old,new,1);edits.append({'old':old,'new':new})
replace("MANIFEST_SHA = 'c03688336db98b8008f557e16fdf6adf589505b5aef2c795bc3c2a63021e3c36'",
    "MANIFEST_SHA = '"+hashlib.sha256(manifest_raw).hexdigest()+"'")
node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='MODULE_NAMES'for t in n.targets))
replace(ast.get_source_segment(source,node),'MODULE_NAMES = '+repr(tuple(row['module']for row in rows)))
replace("hashlib.sha256(values['fixed-modules-v1.json'])","hashlib.sha256(values['fixed-memory-modules-v1.json'])")
replace("parse(values['fixed-modules-v1.json'])","parse(values['fixed-memory-modules-v1.json'])")
replace("'3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'",
    "'55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'")
replace("'only the exact first-source observation is supported'","'only the exact three-memory source observation is supported'")
replace("result = private.normalized_unit_observation_v1.observe_capture(policy, reads, project)",
    "result = private.memory_normalized_capture_ingress_v1.observe_capture(policy, reads, project)")
replace("'whole-interface-normalized-original-tu-preparation-1', 'observation must retain its non-admitting schema')",
    "'whole-interface-original-tu-preparation-1' and prepared['normalized_transport']['kind'] == private.memory_normalized_capture_ingress_v1.KIND, 'observation must retain its distinct memory transport and non-admitting schema')")
replace("        preparation = canonical(prepared); inputs = canonical([row.row() for row in reads.pins.values()])",
    "        units = private.memory_source_preparation_v1.prepare_roots(normalized_tu=_tu,\n"
    "            source_path=path, preparation=prepared, declarations=declarations, abi=prepared['abi_observation']['abi'])\n"
    "        preparation = canonical(prepared); inputs = canonical([row.row() for row in reads.pins.values()])")
replace("        inputs_pin = write_new(output / 'observed-input-pins.json', inputs)",
    "        inputs_pin = write_new(output / 'observed-input-pins.json', inputs)\n"
    "        units_pin = write_new(output / 'memory-source-units.json', canonical(units))")
replace("'preparation': prepared_pin, 'input_pins': inputs_pin, 'source_sha256': hashlib.sha256(original).hexdigest(),",
    "'preparation': prepared_pin, 'input_pins': inputs_pin, 'source_sha256': hashlib.sha256(original).hexdigest(),\n"
    "            'source_units': units_pin, 'source_unit_count': 3, 'per_unit_body_CPU_lifetime_mapping_receiver_checks_required': True,")
source=source.replace('private-normalized-unit-observation-result-1','private-normalized-memory-unit-observation-result-1')
ast.parse(source)
(OUT/'observe_memory_entry_v1.py').write_text(source)
(HERE/'observer-entry-inverse-v1.json').write_text(json.dumps({'predecessor':pin(OLD/'observe_entry_v1.py'),
    'replacements':edits,'result_schema_inverse':{'private-normalized-memory-unit-observation-result-1':'private-normalized-unit-observation-result-1'},
    'scientific_consumer_is_new_closed_memory_family':True},sort_keys=True,indent=2)+'\n')
root='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-unit-observation-2baf722f-v1'
control=root+'/observer/control'
external_control=root+'/control'
f=json.loads((HERE/'proposed/memory_capture_facts_v1.json').read_bytes())
original={**f['original'],'execution':pin(WHOLE/'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json',external_control+'/memory-capture-execution.json')}
runtime=json.loads((WHOLE/'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json').read_bytes())
zlib=runtime['zlib_binding']
zlib_data={'schema':'selected-stdlib-zlib-runtime-1','origin':zlib['spec_origin'],'version':zlib['ZLIB_RUNTIME_VERSION'],
    'physical_inputs':[zlib['physical_interpreter'],*zlib['mapped_compression_objects']]}
(OUT/'selected-memory-zlib-runtime.json').write_bytes(json.dumps(zlib_data,sort_keys=True,separators=(',',':')).encode())
original['zlib_runtime']=pin(OUT/'selected-memory-zlib-runtime.json',external_control+'/selected-memory-zlib-runtime.json')
remote={'controller':'control/controller.py','policy':'control/policy.json','result':'result.json','transport':'component/transport.json',
    'inverse':'component/inverse.json','manifest':'component/rename-manifest.jsonl','normalized_gzip':'component/caller.normalized.json.gz',
    'census':'component/census.json','runtime_before':'component/runtime-before.json','runtime_after':'component/runtime-after.json'}
transform={role:f['transform_outputs'][name]for role,name in remote.items()}
mirrors={role:Path(f[role]['path'])for role in ('command','bootstrap','root_adoption','reconciliation','postflight','invocation','stdout','stderr')}
mirrors['memory-capture-execution']=WHOLE/'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json'
for role,path in mirrors.items():
    name='memory-'+role.replace('_','-')+('.log'if role=='stderr'else'.json'if path.suffix=='.json'else'.py')
    if role=='memory-capture-execution':name='memory-capture-execution.json'
    (OUT/name).write_bytes(path.read_bytes())
    if role!='memory-capture-execution':transform[role]=pin(OUT/name,external_control+'/'+name)
controls={}
for path in [*(MODULES/row['file']for row in rows),MODULES/'memory_capture_facts_v1.json',OUT/'fixed-memory-modules-v1.json',OUT/'observe_memory_entry_v1.py']:
    controls[path.name]=pin(path,control+'/'+path.name)
selected={'schema':'root-selected-normalized-unit-observation-1','original_project':runtime['source_project'],
    'library_root':root+'/library_fixture','output_root':root+'/observer',
    'proof_source':{'root':'library','path':'proof_units/same_thread_memory_v1.cpp','sha256':f['original']['source']['sha256']},
    'capture':{'kind':f['kind'],'original':original,'transform':transform,'prepared':None},
    'controls':controls,'root_admission_receipt':None}
(OUT/'observation-policy-template-v1.json').write_text(json.dumps(selected,sort_keys=True,indent=2)+'\n')
(HERE/'observer-staging-plan-v1.json').write_text(json.dumps({'schema':'prospective-memory-observer-staging-plan-1','raw':root,
    'controls':{name:pin((MODULES/name)if(MODULES/name).exists()else OUT/name)for name in controls},
    'external_provenance_mirrors':{path.name:pin(path)for path in OUT.iterdir()if path.is_file()and(path.name.startswith('memory-')or path.name=='selected-memory-zlib-runtime.json')},
    'policy':pin(OUT/'observation-policy-template-v1.json'),'owned_mapping_runtime_context_or_receiver_not_created':True,
    'scientific_outputs':['whole-unit-preparation.json','observed-input-pins.json','memory-source-units.json','unit-observation-result.json'],
    'runtime_envelope_and_root_admission_required':True,'actual_executed':False},sort_keys=True,indent=2)+'\n')
print(json.dumps({'modules':len(rows),'controls':len(controls),'controls_bytes':sum(row['bytes']for row in controls.values()),'public_admission':False}))
