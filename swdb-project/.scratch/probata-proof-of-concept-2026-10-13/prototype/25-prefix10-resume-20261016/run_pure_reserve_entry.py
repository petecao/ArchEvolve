"""2026-10-16 ET. Bounded compiler-free tests at candidate→composition seam."""
import ast
import hashlib
import json
import runpy
import signal
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
MODULES = ['__init__.py', 'std_models.py', 'vector_reallocation_model.py',
           'vector_reallocation_composition.py']


def main():
    stage = sys.argv[1]
    assert stage in {'red', 'green', 'green-v2'}
    output = Path('/private/tmp/probata-resume-20261016-t25-reserve-entry-' + stage)
    output.mkdir(exist_ok=False)
    (output / 'swdb').mkdir()
    signal.alarm(60)
    rows = []
    for name in MODULES:
        data = (PROJECT / 'swdb' / name).read_bytes()
        tree = ast.parse(data)
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                   for alias in node.names}
        imports |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert not imports - {'hashlib', 're', 'pathlib', 'swdb'}
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
    data = (PROJECT / 'tests/test_vector_reallocation_reserve_application.py').read_bytes()
    test = output / 'test_reserve_application.py'
    test.write_bytes(data)
    rows.append({'path': test.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    assert sum(row['bytes'] for row in rows) < 1024 * 1024
    attempts = []

    def audit(event, arguments):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn',
                     'os.exec', 'os.fork', 'ctypes.dlopen'}:
            attempts.append(event)
            raise RuntimeError('external/native execution forbidden in pure composition tests')

    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(output))
    tests = runpy.run_path(str(test))
    outcomes = []
    for name, function in tests.items():
        if name.startswith('test_'):
            try:
                function()
                outcomes.append({'name': name, 'passed': True})
            except Exception as error:
                outcomes.append({'name': name, 'passed': False,
                                 'error': type(error).__name__ + ': ' + str(error),
                                 'traceback': traceback.format_exc()})
    signal.alarm(0)
    result = {'created': '2026-10-16 ET', 'stage': stage, 'source_files': rows,
              'seam': 'pure source-bound pending reserve_entry(candidate) row/receipt; no parser/runtime or proof claim',
              'outcomes': outcomes, 'passed': sum(row['passed'] for row in outcomes),
              'failed': sum(not row['passed'] for row in outcomes),
              'external_native_attempts': attempts, 'whole_alarm_seconds': 60,
              'source_byte_allowance': 1024 * 1024, 'project_import_overlay': False,
              'scope': 'Exact isolated source modules with literal-only type infrastructure; no live compiler/native or pytest conftest execution',
              'proof_acceptance': False, 'caller_acceptance': False}
    (output / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'result': str(output / 'result.json'),
                      'passed': result['passed'], 'failed': result['failed'],
                      'external_native_attempts': attempts}, indent=2))
    return 0 if result['failed'] == 0 and not attempts else 1


if __name__ == '__main__':
    raise SystemExit(main())
