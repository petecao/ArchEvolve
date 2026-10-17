"""2026-10-16 ET. Source-only semantic ABI observer successor; never execute it."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import shutil
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
OLD=WHOLE/'normalized-unit-envelope-v4'
DEPENDENTS=WHOLE/'abi-semantic-dependents-v1/proposed/swdb/_dx100_whole'
OUT=HERE/'observer'; MODULES=OUT/'modules'
MODULES.mkdir(parents=True,exist_ok=True)
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
inverses={}
def replace(text,old,new,rows,count=None):
    actual=text.count(old)
    assert actual>0 and (count is None or actual==count),old
    rows.append({'old':old,'new':new,'count':actual});return text.replace(old,new)
def source_edit(relative,basis,changes):
    text=basis.read_text();rows=[]
    for old,new in changes:text=replace(text,old,new,rows)
    target=HERE/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
    ast.parse(text)
    inverses[relative]={'basis':pin(basis),'replacements':rows}
    return text
assert pin(OLD/'source-packet-v4.json')['sha256']=='b74571794e41588c2110c9d0ccc9150c825c08a4ca83b78288db7fab21e06667'
manifest=json.loads((OLD/'observer/fixed-modules-v2.json').read_bytes())
rows=manifest['modules']
for row in rows:shutil.copyfile(OLD/'observer/modules'/row['file'],MODULES/row['file'])
# Both actual reader modules are present under their own real names.
reader=DEPENDENTS/'compiler_unit_adapter_v4.py'
assert pin(reader)['sha256']=='b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6'
shutil.copyfile(reader,MODULES/reader.name)
at=next(i for i,row in enumerate(rows) if row['module']=='swdb._dx100_whole.compiler_unit_adapter_v3')+1
rows.insert(at,{'module':'swdb._dx100_whole.compiler_unit_adapter_v4','file':reader.name,
    'origin':str(reader),'bytes':pin(reader)['bytes'],'sha256':pin(reader)['sha256']})
adapter=next(row for row in rows if row['module']=='swdb._dx100_whole.normalized_compiler_adapter_v1')
(MODULES/adapter['file']).unlink()
adapter['file']='normalized_compiler_adapter_v1.py'
shutil.copyfile(DEPENDENTS/adapter['file'],MODULES/adapter['file'])
adapter.update(origin=str(DEPENDENTS/adapter['file']),bytes=pin(MODULES/adapter['file'])['bytes'],sha256=pin(MODULES/adapter['file'])['sha256'])
source_edit('observer/modules/observation_source_bridge_v1.py',OLD/'observer/modules/observation_source_bridge_v1.py',[
    ('from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler',
     'from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler\nfrom swdb._dx100_whole import compiler_unit_adapter_v4 as semantic_compiler')])
old_adapter=pin(OLD/'observer/modules/normalized_compiler_adapter_v2.py')['sha256']
new_adapter=pin(DEPENDENTS/'normalized_compiler_adapter_v1.py')['sha256']
changes=[(old_adapter,new_adapter),('source.compiler','source.semantic_compiler'),
    ('normalized_compiler.LEGACY_SHA','normalized_compiler.CONSUMER_SHA'),
    ('normalized_compiler.legacy','normalized_compiler.consumer'),
    ('same unchanged legacy compiler module','same selected semantic compiler module')]
for name in ('normalized_capture_ingress_v2.py','normalized_unit_observation_v1.py'):
    selected=changes if name=='normalized_capture_ingress_v2.py' else changes[1:]
    source_edit('observer/modules/'+name,OLD/'observer/modules'/name,selected)
assert (MODULES/'normalized_capture_ingress_v2.py').read_bytes()==(DEPENDENTS/'normalized_capture_ingress_v2.py').read_bytes()
for row in rows:
    physical=pin(MODULES/row['file']);row.update(bytes=physical['bytes'],sha256=physical['sha256'])
    if row['module']=='swdb._dx100_whole.normalized_unit_observation_v1':
        row['origin']=str(OLD/'observer/modules/normalized_unit_observation_v1.py')
        row['lineage_note']='Exact predecessor wrapper plus declared semantic reader/adapter rebind; actual file pin is authoritative.'
manifest.update(schema='fixed-private-normalized-observer-module-inventory-3',
    predecessor=pin(OLD/'observer/fixed-modules-v2.json'),compatibility_module_alias={},
    semantic_reader=pin(reader),generic_v3_reader_preserved=True,actual_ABI_replay_or_observer_execution=False)
write(OUT/'fixed-modules-v3.json',manifest)
old_entry=OLD/'observer/observe_entry_v2.py'
text=old_entry.read_text();changes=[]
for key,new in (('MANIFEST_SHA',pin(OUT/'fixed-modules-v3.json')['sha256']),('MODULE_NAMES',tuple(row['module'] for row in rows))):
    assignment=next(node for node in ast.parse(text).body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id==key for target in node.targets))
    changes.append((ast.get_source_segment(text,assignment),key+' = '+repr(new)))
changes.append(('fixed-modules-v2.json','fixed-modules-v3.json'))
source_edit('observer/observe_entry_v3.py',old_entry,changes)
template=json.loads((OLD/'observer/observation-policy-template-v2.json').read_bytes())
raw='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v5'
template['controls']={}
for path in [*(MODULES/row['file'] for row in rows),OUT/'fixed-modules-v3.json',OUT/'observe_entry_v3.py']:
    template['controls'][path.name]={**pin(path),'path':raw+'/observer/control/'+path.name}
write(OUT/'observation-policy-template-v3.json',template)
text=(OLD/'linux_observation_envelope_v4.py').read_text()
changes=[('t28-unit-observation-2baf722f-v4','t28-unit-observation-2baf722f-v5'),
    ('control/linux_observation_envelope_v4.py','control/linux_observation_envelope_v5.py'),
    ('control/envelope-policy-v4.json','control/envelope-policy-v5.json'),
    ('observer/control/observe_entry_v2.py','observer/control/observe_entry_v3.py')]
for key,new in (('OBSERVER_SHA',pin(OUT/'observe_entry_v3.py')['sha256']),('OBSERVER_CONTROLS',tuple(sorted(template['controls'])))):
    assignment=next(node for node in ast.parse(text).body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id==key for target in node.targets))
    changes.append((ast.get_source_segment(text,assignment),key+' = '+repr(new)))
source_edit('linux_observation_envelope_v5.py',OLD/'linux_observation_envelope_v4.py',changes)
source_edit('prepare_envelope_v5.py',OLD/'prepare_envelope_v4.py',[
    ('t28-unit-observation-2baf722f-v4','t28-unit-observation-2baf722f-v5'),
    ('linux_observation_envelope_v4.py','linux_observation_envelope_v5.py'),
    ('envelope-policy-v4.json','envelope-policy-v5.json'),('envelope-policy-template-v4.json','envelope-policy-template-v5.json'),
    ('command-v4.json','command-v5.json'),('command-template-v4.json','command-template-v5.json'),
    ('observation-policy-template-v2.json','observation-policy-template-v3.json'),
    ("'observe_entry_v2.py'","'observe_entry_v3.py'")])
metadata=(OLD/'root-metadata-selection-v4.json').read_text().replace('t28-unit-observation-2baf722f-v4','t28-unit-observation-2baf722f-v5')
(HERE/'root-metadata-selection-v5.json').write_text(metadata)
shutil.copyfile(OLD/'root-metadata-provenance-v1.json',HERE/'root-metadata-provenance-v1.json')
write(HERE/'exact-inverses-v5.json',{'date':'2026-10-16 ET','files':inverses,
    'generic_v3_reader_preserved':True,'no_namespace_monkeypatch':True,'actual_reader_module_names_distinct':True,
    'semantic_reader':pin(reader),'first_adapter':pin(DEPENDENTS/'normalized_compiler_adapter_v1.py'),
    'root_launcher_and_runtime_science_profile_unchanged':True})
builder=runpy.run_path(str(HERE/'prepare_envelope_v5.py'),run_name='inert_semantic_ABI_observer_builder')
print(json.dumps(builder['build'](json.loads(metadata)),sort_keys=True))
