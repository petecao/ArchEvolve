"""Freeze a source proposal with an explicit, unadmitted ABI seam."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent


def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


namespace=runpy.run_path(str(HERE/'test_memory_family_v1.py'),run_name='pure_memory_family_controls')
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE/'pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun==13 and result.wasSuccessful() and not result.skipped
(HERE/'pure-controls-v1.json').write_text(json.dumps({'tests':13,'failures':0,'errors':0,'skipped':0,
    'log':pin(HERE/'pure-controls-v1.log'),'large_TU_original_ABI_body_or_program_executed':False,
    'compiler_native_solver_SSH_child_or_project_import':False,
    'literal_TU_and_ABI_semantics_are_explicit_protocol_doubles':True},sort_keys=True,indent=2)+'\n')
for path in HERE.rglob('*.py'):ast.parse(path.read_bytes())
proposed={p.name:pin(p)for p in sorted((HERE/'proposed').iterdir())if p.is_file()}
observer=json.loads((HERE/'observer-staging-plan-v1.json').read_bytes())
old=WHOLE/'production-route-v5/source-packet-v5.json'
assert pin(old)['sha256']=='60d69b94c7dddc9040adee699cfdda17503aff66f295b90565401f90ddbc119b'
for row in json.loads(old.read_bytes())['files']:assert pin(Path(row['path']))==row
missing={'ABI_transport':{'state':'required before dispatch; generic strict ABI decoder currently refuses duplicate keys',
    'original_genuine_ABI':namespace['FACTS']['original']['abi'],
    'owned_by':'parent /root/ticket28; separately reviewed exact-source ABI helper',
    'duplicate_count_or_eligibility_inferred':False},
    'actual_memory_observer':{'root_admission_receipt':None,'runtime_envelope':None,'new_compiler_or_byte_transform_required':False},
    'body_and_public':{'mapping_receipts':{name:None for name in ('whole_same_thread_read_during_store',
           'whole_same_thread_write_during_gather','whole_same_thread_read_during_gather')},
        'physical_mapping_alignment_inferred_from_source':False,
        'runtime_context_receiver_and_fresh_normal_library_method':None}}
(HERE/'missing-inputs-v1.json').write_text(json.dumps(missing,sort_keys=True,indent=2)+'\n')
basis=[old,WHOLE/'normalized-ingress-v2/source-packet-v2.json',
    WHOLE/'source-memory-selection-v1/source-packet-v1.json',
    WHOLE/'runtime-projection-v4/runtime-projection-source-packet-v4.json',
    WHOLE/'receiver-memory-v1/source-packet-v1.json',
    WHOLE/'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json',
    WHOLE/'memory-role-gzip-v1-actual/actual-reconciliation-v1.json',
    WHOLE.parents[1]/'evidence/t28-memory-role-gzip-v1-root-scoped-acceptance-20261016.json']
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_dir():continue
    assert stat.S_ISREG(path.lstat().st_mode)and not path.is_symlink()
    if path.name=='source-packet-v1.json':continue
    files.append(pin(path))
value={'schema':'prospective-memory-normalized-source-family-packet-1','date':'2026-10-16 ET','files':files,
    'basis':[pin(path)for path in basis],'proposed':proposed,
    'source_route_hook_patch':pin(HERE/'source-family-hook-proposal-v1.patch'),
    'source_route_base':'frozen coherent SourceUnit V4 eaf7b660; V5 production bytes unchanged',
    'observer_entry':pin(HERE/'observer/observe_memory_entry_v1.py'),
    'observer_policy':pin(HERE/'observer/observation-policy-template-v1.json'),
    'observer_modules':12,'observer_controls':15,'observer_control_bytes':239545,
    'root_original_project':'/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
    'actual_public_runtime_cwd':'/data1/yanruj/probata-resume-20261016-2baf722f',
    'tests':13,'shared_frozen_or_Git_mutated':False,'scientific_execution':False,
    'ABI_helper_pending_and_actual_observer_dispatch_prohibited':True,
    'prepared_context_mapping_receiver_receipts_or_public_results_fabricated':False,
    'public_admission':False,'whole_ticket28_acceptance':False}
(HERE/'source-packet-v1.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps({name:pin(HERE/path)for name,path in {'packet':'source-packet-v1.json',
    'ingress':'proposed/memory_normalized_capture_ingress_v1.py',
    'adapter':'proposed/memory_normalized_compiler_adapter_v1.py',
    'preparation':'proposed/memory_source_preparation_v1.py',
    'observer':'observer/observe_memory_entry_v1.py'}.items()},sort_keys=True))
