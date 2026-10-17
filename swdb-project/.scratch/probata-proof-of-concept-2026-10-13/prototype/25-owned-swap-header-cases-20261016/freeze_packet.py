"""2026-10-16 ET. Freeze exact public preparation bytes, never run formal tools."""
import hashlib
import json
from pathlib import Path
import signal
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
ISOLATED = Path('/private/tmp/probata-resume-20261016-t25-owned-swap-header-green-v3')


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(PROJECT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


attempts = []


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec',
                 'os.fork', 'ctypes.dlopen', 'socket.connect'}:
        attempts.append(event)
        raise RuntimeError('pure header preparation rejected '+event)


sys.addaudithook(audit)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ISOLATED))
signal.alarm(30)
names = ['std_models.py', 'c_lowering.py', 'vector_owned_transfer.py',
         'vector_owned_state.mlw', 'heap_reallocation.mlw', 'vector_owned_source_view.py',
         'vector_owned_effects.mlw', 'vector_owned_swap_parts.py', 'vector_owned_swap_header_cases.py']
inputs = []
for name in names:
    path = PROJECT/'swdb'/name
    assert path.read_bytes() == (ISOLATED/'swdb'/name).read_bytes()
    inputs.append(pin(path))
test = PROJECT/'tests/test_vector_owned_swap_header_cases.py'
assert test.read_bytes() == (ISOLATED/'test_swap_header_cases.py').read_bytes()
inputs.append(pin(test))
from swdb import vector_owned_swap_header_cases as packets

directory = HERE/'inert-all-types-v1'
plan = packets.prepare(directory, elements=('int', 'float', 'double', 'int *'))
assert packets.check(directory, elements=('int', 'float', 'double', 'int *')) == plan
outputs = [pin(path) for path in sorted(directory.rglob('*')) if path.is_file()]
assert len(outputs) == 45
stages = []
for stage in ('red-v1', 'green-v1', 'red-v2', 'green-v2', 'red-v3', 'green-v3'):
    path = HERE/'development'/(stage+'-result.json')
    result = json.loads(path.read_bytes())
    assert not result['external_native_attempts'] and result['actual_formal_run'] is False
    stages.append({'stage': stage, 'passed': result['passed'], 'failed': result['failed'], 'result': pin(path)})
receipt = {'date': '2026-10-16 ET', 'kind': 'inert-three-case-source-preparation',
           'inputs': inputs, 'outputs': outputs, 'stages': stages,
           'canonical_files': len(outputs), 'independent_case_targets': len(plan['obligations']),
           'checker': plan['checker'], 'logical_target': plan['logical_target'],
           'complete_source_antecedent': plan['complete_source_antecedent'],
           'original_statement': plan['original_statement'],
           'reconstruction': plan['reconstruction'],
           'unchanged_dependencies': plan['unchanged_dependencies'],
           'source_definition_bindings': plan['source_definition_bindings'],
           'formal_or_native_runs': 0, 'external_native_attempts': attempts,
           'science_admitted': False, 'source_heap_bridge_established': False,
           'source_typed_bridge_established': False, 'caller_acceptance': False,
           'default_method_adoption': False, 'public_record_admission': False}
with (HERE/'source-packet-v1.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True, indent=2)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'packet': pin(HERE/'source-packet-v1.json'), 'files': len(outputs), 'external_native_attempts': attempts}))
