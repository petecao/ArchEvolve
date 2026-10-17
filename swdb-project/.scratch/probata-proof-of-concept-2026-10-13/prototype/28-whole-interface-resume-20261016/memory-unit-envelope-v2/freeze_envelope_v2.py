"""2026-10-16 ET. Pure source/metadata freeze only, no envelope execution."""
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
basis=[WHOLE/'normalized-unit-envelope-v5/source-packet-v5.json',WHOLE/'memory-normalized-ingress-v3/source-packet-v3.json',
    WHOLE/'memory-unit-envelope-v1/source-packet-v1.json',WHOLE/'production-union-v1/source-packet-v1.json']
suite=unittest.TestSuite()
for filename,cls in [('test_envelope_v2.py','Controls'),('test_root_environment_v2.py','RootEnvironmentControls'),('test_real_memory_stage_v2.py','Controls')]:
    ns=runpy.run_path(str(HERE/filename),run_name='pure_memory_envelope_'+filename)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ns[cls]))
log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(HERE/'pure-controls-final-v2.log').write_text(log.getvalue());assert result.testsRun==20 and result.wasSuccessful() and not result.skipped
write(HERE/'pure-controls-v2.json',{'date':'2026-10-16 ET','tests':20,'failures':0,'errors':0,'skips':0,
    'log':pin(HERE/'pure-controls-final-v2.log'),'actual_observer_compiler_native_solver_project_import_or_remote_execution':False})
command=json.loads((HERE/'command-v2.json').read_bytes());policy=json.loads((HERE/'envelope-policy-v2.json').read_bytes())
assert command['root_metadata_complete'] is False and policy['node'] is None and policy['guard_files'] is None
assert len(command['stage_sources'])==36 and command['root_controls_bytes_including_policy']==736053
write(HERE/'root-argv-inert-v2.json',command['argv'])
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_dir() or path.name=='source-packet-v2.json':continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.suffix=='.py':ast.parse(path.read_bytes())
    files.append(pin(path))
packet={'schema':'inert-memory-observer-semantic-reader-envelope-2','date':'2026-10-16 ET','files':files,
    'basis':[pin(path) for path in basis],'tests':20,'entry':pin(HERE/'linux_memory_observation_envelope_v2.py'),
    'policy':pin(HERE/'envelope-policy-v2.json'),'command_template':pin(HERE/'command-v2.json'),
    'payload_controls':36,'flat_controls_including_policy':37,'flat_control_bytes_including_policy':736053,
    'observer_modules':15,'observer_controls':18,'root_lane_and_guard_selection':None,
    'actual_admitted_command':False,'source_complete_TU_CPU_lifetime_gates_retained':True,
    'actual_compiler_native_solver_SSH_project_import_or_scientific_execution':False,
    'owned_context_mapping_receiver_preparation_or_public_acceptance':False,
    'frozen_predecessors_shared_source_and_Git_unchanged':True}
write(HERE/'source-packet-v2.json',packet)
print(json.dumps({name:pin(HERE/path) for name,path in {'packet':'source-packet-v2.json','entry':'linux_memory_observation_envelope_v2.py',
    'policy':'envelope-policy-v2.json','command':'command-v2.json'}.items()},sort_keys=True))
