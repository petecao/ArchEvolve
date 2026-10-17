"""2026-10-16 ET. Replay retained parser output to test public packet orchestration.

This runs no compiler and proves no source/runtime or parser correspondence.
The ordinary pytest seam separately invokes the real lowerer when admitted.
"""
import ast
import copy
import hashlib
import json
import runpy
import signal
import sys
import traceback
import types
from pathlib import Path

import pytest
from author import blob

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
RETAINED = Path('/private/tmp/probata-t25-caller104-compiler-controls-v1-20261016/pytest/test_whole_clauses_may_share_o0/whole')
MODULES = ['__init__.py', 'std_models.py', 'heap_model_vcs.py',
           'vector_reallocation_model.py', 'vector_reallocation_inventory.py',
           'vector_reallocation_vcs.py', 'vector_reallocation_composition.py',
           'vector_reallocation_caller_packets.py', 'vector_reallocation_calls.py',
           'vector_reallocation_caller_vcs.py', 'vector_reallocation_lifetime.py',
           'vector_reallocation_capacity.py', 'heap_reallocation.mlw']


def main():
    stage = sys.argv[1]
    assert stage in {'red', 'green', 'red-v2', 'green-v2', 'green-v3', 'green-v4'}
    output = Path('/private/tmp/probata-resume-20261016-t25-caller-reserve-' + stage)
    output.mkdir(exist_ok=False)
    (output / 'swdb').mkdir()
    signal.alarm(60)
    rows = []
    for name in MODULES:
        data = (PROJECT / 'swdb' / name).read_bytes()
        if stage == 'red-v2' and name == 'vector_reallocation_caller_packets.py':
            data = blob('swdb/' + name)
        if name.endswith('.py'):
            imports = {alias.name for node in ast.walk(ast.parse(data))
                       if isinstance(node, ast.Import) for alias in node.names}
            imports |= {node.module for node in ast.walk(ast.parse(data))
                        if isinstance(node, ast.ImportFrom)}
            assert not imports - {'hashlib', 'json', 're', 'pathlib', 'ast', 'swdb',
                                  'swdb.heap_model_vcs', 'swdb.vector_reallocation_inventory',
                                  'swdb.vector_reallocation_composition'}
        (output / 'swdb' / name).write_bytes(data)
        rows.append({'path': 'swdb/' + name, 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    lowerer = (PROJECT / 'swdb/c_lowering.py').read_bytes()
    stub = types.ModuleType('swdb.c_lowering')
    nodes = [node for node in ast.parse(lowerer).body if isinstance(node, ast.Assign)
             and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
             and node.targets[0].id in {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}]
    assert len(nodes) == 3
    for node in nodes:
        setattr(stub, node.targets[0].id, ast.literal_eval(node.value))
    sys.modules['swdb.c_lowering'] = stub
    retained = json.loads((RETAINED / 'manifest.json').read_bytes())
    source = (PROJECT / 'tests/fixtures/proof/vector_reallocation_v3.cc').read_bytes()
    assert source == (RETAINED / 'original.cc').read_bytes()
    assert hashlib.sha256(source).hexdigest() == retained['source']['sha256']
    lowered = (RETAINED / 'lowering.c').read_bytes()
    assert hashlib.sha256(lowered).hexdigest() == retained['lowering']['sha256']
    assert retained['candidate']['source_sha256'] == retained['source']['sha256']
    assert retained['candidate']['lowered_sha256'] == retained['lowering']['sha256']
    fixture = output / 'fixtures/proof/vector_reallocation_v3.cc'
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(source)
    conftest = types.ModuleType('conftest')
    conftest.FIXTURES = output / 'fixtures'
    sys.modules['conftest'] = conftest
    replay_calls = []

    def replay(path, function):
        assert Path(path).read_bytes() == source and function == 'vector_realloc_v3_safe'
        replay_calls.append({'source_sha256': retained['source']['sha256'], 'function': function})
        return types.SimpleNamespace(
            text=lowered.decode(), sha256=retained['lowering']['sha256'],
            vector_reallocation_candidate=copy.deepcopy(retained['candidate']),
            anchors_json=(RETAINED / 'anchors.json').read_text(), tool=retained['lowering']['tool'])

    stub.lower = replay
    data = (PROJECT / 'tests/test_vector_reallocation_caller_packets.py').read_bytes()
    test = output / 'test_caller_packets.py'
    test.write_bytes(data)
    attempts = []

    def audit(event, arguments):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn',
                     'os.exec', 'os.fork', 'ctypes.dlopen'}:
            attempts.append(event)
            raise RuntimeError('external/native execution forbidden in packet replay')

    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(output))
    from swdb import std_models
    stub.model_text = std_models.model_text
    tests = runpy.run_path(str(test))
    outcomes = []
    selected = ['test_reserve_entry_application_is_canonical_and_never_grants_a_poststate',
                'test_canonical_caller_preparation_binds_existing_contract_without_enabling_proof']
    for index, name in enumerate(selected):
        path = output / ('case' + str(index))
        path.mkdir()
        try:
            tests[name](path)
            outcomes.append({'name': name, 'passed': True})
        except Exception as error:
            outcomes.append({'name': name, 'passed': False,
                             'error': type(error).__name__ + ': ' + str(error),
                             'traceback': traceback.format_exc()})
    if stage in {'green-v3', 'green-v4'}:
        prepared = output / 'case1/caller'
        for mutation in ['reserve_application', 'reserve_receipt']:
            path = output / mutation
            path.mkdir()
            name = 'canonical_reserve_tamper_refusal:' + mutation
            try:
                tests['test_caller_packet_check_reconstructs_source_and_contract_after_self_consistent_tampering'](
                    path, prepared, mutation)
                outcomes.append({'name': name, 'passed': True})
            except Exception as error:
                outcomes.append({'name': name, 'passed': False,
                                 'error': type(error).__name__ + ': ' + str(error),
                                 'traceback': traceback.format_exc()})
    if stage == 'green-v4':
        name = 'current_caller_count_literal_control'
        try:
            controls = runpy.run_path(str(PROJECT / 'tests/test_vector_reallocation_copy_prefix_cases.py'))
            controls['test_caller_count_literals_follow_current_body_packets_without_running_caller_lowering']()
            outcomes.append({'name': name, 'passed': True})
        except Exception as error:
            outcomes.append({'name': name, 'passed': False,
                             'error': type(error).__name__ + ': ' + str(error),
                             'traceback': traceback.format_exc()})
    raw_bytes = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    assert raw_bytes < 16 * 1024 * 1024
    signal.alarm(0)
    result = {'created': '2026-10-16 ET', 'stage': stage, 'source_files': rows,
              'seam': 'public caller_packets.prepare/check orchestration with retained real lowerer-output replay',
              'retained_manifest': {'path': str(RETAINED / 'manifest.json'),
                  'sha256': hashlib.sha256((RETAINED / 'manifest.json').read_bytes()).hexdigest()},
              'parser_replay_calls': replay_calls, 'outcomes': outcomes,
              'passed': sum(row['passed'] for row in outcomes),
              'failed': sum(not row['passed'] for row in outcomes),
              'external_native_attempts': attempts, 'whole_alarm_seconds': 60,
              'raw_bytes': raw_bytes, 'raw_budget_bytes': 16 * 1024 * 1024,
              'actual_parser_or_source_runtime_acceptance': False,
              'proof_acceptance': False, 'caller_acceptance': False}
    (output / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'result': str(output / 'result.json'),
                      'passed': result['passed'], 'failed': result['failed'],
                      'external_native_attempts': attempts}, indent=2))
    return 0 if result['failed'] == 0 and not attempts else 1


if __name__ == '__main__':
    raise SystemExit(main())
