"""2026-10-16 ET. Source/pure-control freeze only; no observer entry execution."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;POC=WHOLE.parent.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
basis=[WHOLE/'normalized-unit-envelope-v4/source-packet-v4.json',WHOLE/'abi-enum-repair-v1/source-packet-v1.json',
    WHOLE/'abi-enum-repair-v1-independent-review/independent-ABI-enum-reader-v1-spec-review-20261016.json',
    POC/'evidence/t28-ABI-enum-repair-root-standards-review-v1-20261016.json',
    WHOLE/'root-launcher-loader-v11/source-packet-v11.json',
    WHOLE/'normalized-unit-envelope-v4-independent-review/independent-envelope-v4-spec-review-20261016.json']
assert pin(basis[2])['sha256']=='33dc1ac17ed70297a319ae1a587063d913e1253b7a285221dfba30beaef01bf3'
assert pin(basis[3])['sha256']=='8e78b0cd1a0414848e8bd9a37929fc34d4178d7fab5707a573f5d76c79b6a309'
retained={}
for path in basis[:2]:
    for row in json.loads(path.read_bytes())['files']:
        selected=row.get('pin',row);actual=pin(Path(selected['path']))
        assert actual==selected
        retained[actual['path']]=actual
suite=unittest.TestSuite()
for name,cls in [('test_envelope_v5.py','Controls'),('test_root_environment_v5.py','RootEnvironmentControls'),
                 ('test_semantic_observer_v5.py','SemanticObserverControls')]:
    ns=runpy.run_path(str(HERE/name),run_name='no_child_'+cls)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ns[cls]))
log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(HERE/'pure-controls-v5.log').write_text(log.getvalue())
assert result.testsRun==23 and result.wasSuccessful() and not result.skipped
for row in retained.values():assert pin(Path(row['path']))==row
write(HERE/'pure-controls-v5.json',{'date':'2026-10-16 ET','tests':23,'failures':0,'errors':0,'skips':0,
    'log':pin(HERE/'pure-controls-v5.log'),'predecessor_and_reader_basis_files_unchanged':len(retained),
    'actual_large_TU_observer_or_source_program_or_scientific_execution':False,
    'no_child_native_compiler_verifier_shell_launcher_SSH_or_installed_project_import':True})
command=json.loads((HERE/'command-v5.json').read_bytes());envelope=json.loads((HERE/'envelope-policy-v5.json').read_bytes())
observer=json.loads((HERE/'observation-policy-v1.json').read_bytes());manifest=json.loads((HERE/'observer/fixed-modules-v3.json').read_bytes())
assert (len(command['stage_sources']),len(observer['controls']),len(manifest['modules']))==(30,16,14)
assert command['root_controls_bytes_including_policy']==479538
assert observer['capture']['prepared'] is None and manifest['compatibility_module_alias']=={}
for name,row in command['stage_sources'].items():
    assert pin(Path(row['path']))==row
    assert {k:v for k,v in row.items() if k!='path'}=={k:v for k,v in envelope['controls'][name].items() if k!='path'}
write(HERE/'root-argv-v5.json',command['argv'])
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_dir() or path.name=='source-packet-v5.json':continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.suffix=='.py':ast.parse(path.read_bytes())
    files.append(pin(path))
packet={'schema':'explicit-semantic-ABI-first-source-observer-packet-5','date':'2026-10-16 ET','files':files,
    'basis':[pin(path) for path in basis],
    'entry':pin(HERE/'linux_observation_envelope_v5.py'),'policy':pin(HERE/'envelope-policy-v5.json'),
    'command':pin(HERE/'command-v5.json'),'observer_entry':pin(HERE/'observer/observe_entry_v3.py'),
    'observer_inventory':pin(HERE/'observer/fixed-modules-v3.json'),
    'entry_and_observer_inverses':pin(HERE/'exact-inverses-v5.json'),
    'semantic_reader':pin(HERE/'observer/modules/compiler_unit_adapter_v4.py'),
    'actual_v3_reader':pin(HERE/'observer/modules/compiler_unit_adapter_v3.py'),
    'adapter':pin(HERE/'observer/modules/normalized_compiler_adapter_v1.py'),
    'tests':23,'observer_modules':14,'observer_controls':16,'root_controls':30,
    'root_control_bytes_including_policy':479538,'no_compatibility_alias_or_module_monkeypatch':True,
    'legacy_direct_route_keeps_actual_v3':True,'original_role_derived_and_interpreted_ABI_identities_distinct':True,
    'public_equality_and_private_prepared_unknown_preserved':True,
    'runtime_resource_source_guard_and_settled_finalization_gates_unchanged':True,
    'actual_observer_or_scientific_execution':False,'root_review_and_actual_admission_pending':True,
    'shared_production_Git_or_frozen_predecessor_mutation':False,'public_admission':False}
write(HERE/'source-packet-v5.json',packet)
print(json.dumps({name:pin(HERE/path) for name,path in {'packet':'source-packet-v5.json','entry':'linux_observation_envelope_v5.py',
    'policy':'envelope-policy-v5.json','command':'command-v5.json','observer':'observer/observe_entry_v3.py'}.items()},sort_keys=True))
