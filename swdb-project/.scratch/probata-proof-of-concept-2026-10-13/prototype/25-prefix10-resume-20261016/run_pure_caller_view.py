"""2026-10-16 ET. Bounded source-view controls with retained real parser output."""
import ast
import copy
import hashlib
import inspect
import json
import runpy
import signal
import sys
import traceback
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
RETAINED = Path('/private/tmp/probata-t25-caller104-compiler-controls-v1-20261016/pytest/test_public_alias_controls_kee1')
MODULES = ['__init__.py', 'std_models.py', 'heap_model_vcs.py',
           'vector_reallocation_model.py', 'vector_reallocation_inventory.py',
           'vector_reallocation_vcs.py', 'vector_reallocation_composition.py',
           'vector_reallocation_caller_packets.py', 'vector_reallocation_calls.py',
           'vector_reallocation_caller_vcs.py', 'vector_reallocation_lifetime.py',
           'vector_reallocation_capacity.py', 'heap_reallocation.mlw']


def main():
    stage = sys.argv[1]
    assert stage in {'red', 'green', 'red-v2', 'green-v2', 'red-v3', 'green-v3', 'green-v4'}
    output = Path('/private/tmp/probata-resume-20261016-t25-caller-view-' + stage)
    output.mkdir(exist_ok=False)
    (output / 'swdb').mkdir()
    signal.alarm(60)
    rows = []
    modules = MODULES + (['vector_reallocation_caller_view.py'] if stage != 'red' else [])
    for name in modules:
        data = (PROJECT / 'swdb' / name).read_bytes()
        if name.endswith('.py'):
            imports = {alias.name for node in ast.walk(ast.parse(data))
                       if isinstance(node, ast.Import) for alias in node.names}
            imports |= {node.module for node in ast.walk(ast.parse(data)) if isinstance(node, ast.ImportFrom)}
            assert not imports - {'hashlib', 'json', 're', 'pathlib', 'ast', 'dataclasses', 'swdb',
                                  'swdb.heap_model_vcs', 'swdb.vector_reallocation_inventory',
                                  'swdb.vector_reallocation_composition', 'swdb.vector_reallocation_caller_packets'}
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
    anchor_path = RETAINED / 'vector_realloc_v3_no_growth.anchors.json'
    anchors = json.loads(anchor_path.read_bytes())
    lowered = (RETAINED / 'vector_realloc_v3_no_growth.c').read_bytes()
    candidate = anchors['vector_reallocation_candidate']
    assert hashlib.sha256(lowered).hexdigest() == candidate['lowered_sha256'] == anchors['c_lowering_sha256']
    source = PROJECT / 'tests/fixtures/proof/vector_reallocation_v3.cc'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == candidate['source_sha256']
    lowering = types.SimpleNamespace(text=lowered.decode(), sha256=candidate['lowered_sha256'],
        vector_reallocation_candidate=copy.deepcopy(candidate), function=anchors['function'],
        models=anchors['models'], source_sha256=candidate['source_sha256'])
    test = output / 'test_caller_view.py'
    test.write_bytes((PROJECT / 'tests/test_vector_reallocation_caller_view.py').read_bytes())
    attempts = []

    def audit(event, arguments):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn',
                     'os.exec', 'os.fork', 'ctypes.dlopen'}:
            attempts.append(event)
            raise RuntimeError('external/native execution forbidden in source-view controls')

    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(output))
    tests = runpy.run_path(str(test))
    outcomes = []
    for name, function in tests.items():
        if not name.startswith('test_'):
            continue
        path = output / name
        path.mkdir()
        arguments = [(source, copy.deepcopy(lowering))]
        if 'tmp_path' in inspect.signature(function).parameters:
            arguments.append(path)
        patch = pytest.MonkeyPatch()
        if 'monkeypatch' in inspect.signature(function).parameters:
            arguments.append(patch)
        try:
            function(*arguments)
            outcomes.append({'name': name, 'passed': True})
        except (Exception, pytest.fail.Exception) as error:
            outcomes.append({'name': name, 'passed': False,
                             'error': type(error).__name__ + ': ' + str(error),
                             'traceback': traceback.format_exc()})
        finally:
            patch.undo()
    signal.alarm(0)
    raw_bytes = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    assert raw_bytes < 4 * 1024 * 1024
    result = {'created': '2026-10-16 ET', 'stage': stage, 'source_files': rows,
              'seam': 'source-derived prepare/check/check_launch view; retained genuine no-growth parser output replay',
              'retained_anchors': {'path': str(anchor_path), 'sha256': hashlib.sha256(anchor_path.read_bytes()).hexdigest()},
              'source_sha256': candidate['source_sha256'], 'lowered_sha256': candidate['lowered_sha256'],
              'outcomes': outcomes, 'passed': sum(row['passed'] for row in outcomes),
              'failed': sum(not row['passed'] for row in outcomes),
              'external_native_attempts': attempts, 'whole_alarm_seconds': 60,
              'raw_bytes': raw_bytes, 'raw_budget_bytes': 4 * 1024 * 1024,
              'actual_parser_or_source_runtime_acceptance': False,
              'proof_acceptance': False, 'caller_acceptance': False}
    (output / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'result': str(output / 'result.json'), 'passed': result['passed'],
                      'failed': result['failed'], 'external_native_attempts': attempts}, indent=2))
    return 0 if result['failed'] == 0 and not attempts else 1


if __name__ == '__main__':
    raise SystemExit(main())
