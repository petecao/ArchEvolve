"""2026-10-16 ET. Source and stdlib controls only; no actual observer run."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
basis=[WHOLE/'memory-normalized-ingress-v2/source-packet-v2.json',WHOLE/'abi-enum-repair-v1/source-packet-v1.json',
    WHOLE/'production-union-v1/source-packet-v1.json',WHOLE/'normalized-unit-envelope-v5/source-packet-v5.json']
ns=runpy.run_path(str(HERE/'test_memory_semantic_v3.py'),run_name='no_child_memory_semantic_controls')
log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['Controls']))
(HERE/'pure-controls-fixed-v3.log').write_text(log.getvalue())
assert result.testsRun==5 and result.wasSuccessful() and not result.skipped
write(HERE/'pure-controls-v3.json',{'date':'2026-10-16 ET','tests':5,'failures':0,'errors':0,'skips':0,
    'actual_large_TU_body_scientific_or_remote_execution':False,'log':pin(HERE/'pure-controls-fixed-v3.log')})
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_dir() or path.name=='source-packet-v3.json':continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.suffix=='.py':ast.parse(path.read_bytes())
    files.append(pin(path))
policy=json.loads((HERE/'observer/observation-policy-template-v2.json').read_bytes())
assert policy['capture']['prepared'] is None and len(policy['controls'])==18
packet={'schema':'explicit-semantic-ABI-memory-observer-source-packet-3','date':'2026-10-16 ET','files':files,
    'basis':[pin(path) for path in basis],'tests':5,'observer_modules':15,'observer_controls':18,
    'controlled_observer_bytes':sum(row['bytes'] for row in policy['controls'].values()),
    'observer_entry':pin(HERE/'observer/observe_memory_entry_v1.py'),
    'observation_policy':pin(HERE/'observer/observation-policy-template-v2.json'),
    'observer_inventory':pin(HERE/'observer/fixed-memory-modules-v2.json'),
    'actual_genuine_G642_transport_and_source_identity_preserved':True,
    'actual_generic_v3_and_separate_semantic_v4_both_physical':True,
    'complete_TU_40_calls_three_roots_body_CPU_lifetime_gates_retained':True,
    'prepared_mapping_receiver_owned_context_or_public_admission':False,
    'root_lane_guard_outer_admission_and_actual_observation_pending':True,
    'shared_Git_compiler_native_solver_project_import_or_remote_execution':False}
write(HERE/'source-packet-v3.json',packet)
print(json.dumps(pin(HERE/'source-packet-v3.json')))
