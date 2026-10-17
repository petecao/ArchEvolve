"""2026-10-16 ET. Inert G642 observer with explicitly selected semantic reader."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'memory-normalized-ingress-v2';DEPENDENTS=WHOLE/'abi-semantic-dependents-v1/proposed/swdb/_dx100_whole'
OUT=HERE/'observer';MODULES=OUT/'modules';MODULES.mkdir(parents=True,exist_ok=True)
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
assert pin(OLD/'source-packet-v2.json')['sha256']=='9904def8876809e84e737355c93f6a1c87bfb4751bf1c901a05a3b6629915df9'
inverses={}
def transform(relative,changes):
    source=OLD/relative;text=source.read_text();edits=[]
    for old,new in changes:
        count=text.count(old);assert count>0,old;edits.append({'old':old,'new':new,'count':count});text=text.replace(old,new)
    path=HERE/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);ast.parse(text)
    inverses[relative]={'basis':pin(source),'replacements':edits}
for source in (OLD/'observer').iterdir():
    if source.is_file() and source.name not in {'observation-policy-template-v1.json','fixed-memory-modules-v1.json','observe_memory_entry_v1.py'}:shutil.copyfile(source,OUT/source.name)
for source in (OLD/'observer/modules').iterdir():
    if source.is_file():shutil.copyfile(source,MODULES/source.name)
for name in ('memory_normalized_compiler_adapter_v1.py','memory_normalized_capture_ingress_v1.py','compiler_unit_adapter_v4.py'):
    shutil.copyfile(DEPENDENTS/name,MODULES/name)
transform('observer/modules/observation_source_bridge_v1.py',[
    ('from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler',
     'from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler\nfrom swdb._dx100_whole import compiler_unit_adapter_v4 as semantic_compiler')])
manifest=json.loads((OLD/'observer/fixed-memory-modules-v1.json').read_bytes());rows=manifest['modules']
at=next(i for i,row in enumerate(rows) if row['module']=='swdb._dx100_whole.compiler_unit_adapter_v3')+1
rows.insert(at,{'module':'swdb._dx100_whole.compiler_unit_adapter_v4','file':'compiler_unit_adapter_v4.py','origin':str(DEPENDENTS/'compiler_unit_adapter_v4.py')})
for row in rows:
    actual=pin(MODULES/row['file']);row.update(bytes=actual['bytes'],sha256=actual['sha256'])
    if row['file'] in {'memory_normalized_compiler_adapter_v1.py','memory_normalized_capture_ingress_v1.py'}:row['origin']=str(DEPENDENTS/row['file'])
manifest.update(schema='fixed-private-memory-normalized-module-inventory-2',predecessor=pin(OLD/'observer/fixed-memory-modules-v1.json'),
    semantic_reader=pin(DEPENDENTS/'compiler_unit_adapter_v4.py'),actual_v3_reader_preserved=True,actual_observer_execution=False)
write(OUT/'fixed-memory-modules-v2.json',manifest)
text=(OLD/'observer/observe_memory_entry_v1.py').read_text();changes=[]
for key,value in [('MANIFEST_SHA',pin(OUT/'fixed-memory-modules-v2.json')['sha256']),('MODULE_NAMES',tuple(row['module'] for row in rows))]:
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets))
    changes.append((ast.get_source_segment(text,node),key+' = '+repr(value)))
changes.append(('fixed-memory-modules-v1.json','fixed-memory-modules-v2.json'))
# Same relative path intentionally retains the entry API; the new directory,
# exact manifest and output packet make this a distinct frozen observer version.
transform('observer/observe_memory_entry_v1.py',changes)
old_raw='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-unit-observation-2baf722f-v2'
raw='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-unit-observation-2baf722f-v3'
policy=json.loads((OLD/'observer/observation-policy-template-v1.json').read_bytes());policy=json.loads(json.dumps(policy).replace(old_raw,raw))
policy['controls']={}
for path in [*(MODULES/row['file'] for row in rows),MODULES/'memory_capture_facts_v1.json',OUT/'fixed-memory-modules-v2.json',OUT/'observe_memory_entry_v1.py']:
    policy['controls'][path.name]={**pin(path),'path':raw+'/observer/control/'+path.name}
write(OUT/'observation-policy-template-v2.json',policy)
write(HERE/'exact-inverses-v3.json',{'date':'2026-10-16 ET','files':inverses,
    'explicit_reader_and_adapter_module_pins':{name:pin(MODULES/name) for name in ('compiler_unit_adapter_v3.py','compiler_unit_adapter_v4.py','memory_normalized_compiler_adapter_v1.py','memory_normalized_capture_ingress_v1.py')},
    'all_other_module_bytes_exact':True,'actual_preparation_receiver_context_and_public_admission':False})
plan=json.loads((OLD/'observer-staging-plan-v2.json').read_bytes());plan=json.loads(json.dumps(plan).replace(old_raw,raw))
plan['modules']=[pin(MODULES/row['file']) for row in rows]
plan['selected_semantic_reader']=pin(MODULES/'compiler_unit_adapter_v4.py')
plan['root_lane_and_guard_selected_for_memory']=False
write(HERE/'observer-staging-plan-v3.json',plan)
print(json.dumps({'modules':len(rows),'observer_controls':len(policy['controls']),'controlled_bytes':sum(row['bytes'] for row in policy['controls'].values()),
    'prepared':policy['capture']['prepared'],'runtime_admission':False}))
