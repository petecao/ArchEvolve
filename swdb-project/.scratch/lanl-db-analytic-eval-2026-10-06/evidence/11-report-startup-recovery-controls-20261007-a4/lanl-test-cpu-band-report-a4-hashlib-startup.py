"""Bounded isolated startup regression; no Store, cleanup, native or provider."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--dispatcher', type=Path, required=True)
parser.add_argument('--original', type=Path)
args = parser.parse_args()
FIXTURES = {'cleanup': b'swdb.cpu-report.startup.fixture.cleanup.v1\n',
            'processes': b'swdb.cpu-report.startup.fixture.processes.v1\n'}

def decoded(path):
    outer = ast.parse(path.read_text())
    rows = [node for node in outer.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'RUNNER_TEMPLATE' for target in node.targets)]
    assert len(rows) == 1
    return ast.literal_eval(rows[0].value)

def run_case(path, fixture_root, *, tamper=None):
    actual = ast.parse(decoded(path))
    allowed = {'sys', 'pathlib', 'copy', 'datetime', 'hashlib', 'json', 'math', 'os',
               'shutil', 'signal', 'subprocess', 'time', 'ctypes', 'importlib.util'}
    imports = []
    hashes = []
    for node in actual.body:
        if isinstance(node, ast.Import) and all(alias.name in allowed for alias in node.names):
            imports.append(copy.deepcopy(node))
        elif isinstance(node, ast.ImportFrom) and node.module == 'pathlib':
            imports.append(copy.deepcopy(node))
        elif isinstance(node, ast.Assert) and 'hashlib.sha256' in ast.unparse(node):
            hashes.append(copy.deepcopy(node))
    assert len(hashes) == 2
    assert all(isinstance(node.test, ast.Compare) and len(node.test.comparators) == 1
               and isinstance(node.test.comparators[0], ast.Constant) for node in hashes)
    assert hashes[0].test.comparators[0].value == '31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
    assert hashes[1].test.comparators[0].value == 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
    for node, name in zip(hashes, ('cleanup', 'processes')):
        node.test.comparators[0] = ast.Constant(hashlib.sha256(FIXTURES[name]).hexdigest())
    scaffold = ast.parse('cleanup_path = Path(' + repr(str(fixture_root / 'cleanup.py')) + ')\nW = Path(' + repr(str(fixture_root)) + ')\n')
    code = ast.unparse(ast.fix_missing_locations(ast.Module(body=imports + scaffold.body + hashes, type_ignores=[])))
    (fixture_root / 'cleanup.py').write_bytes(FIXTURES['cleanup'])
    (fixture_root / 'swdb').mkdir(exist_ok=True)
    (fixture_root / 'swdb/processes.py').write_bytes(FIXTURES['processes'])
    if tamper:
        target = fixture_root / ('cleanup.py' if tamper == 'cleanup' else 'swdb/processes.py')
        target.write_bytes(target.read_bytes() + b'tampered\n')
    # This child has no parent globals/PYTHONPATH/site initialization. Only actual
    # runner standard imports execute; none of the fixture file bodies execute.
    child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code],
                           capture_output=True, text=True, timeout=10)
    error = ('NameError: name \'hashlib\' is not defined' if "NameError: name 'hashlib' is not defined" in child.stderr
             else 'AssertionError' if 'AssertionError' in child.stderr else None)
    return {'returncode': child.returncode, 'error': error,
            'actual_sha_assertions': 2, 'isolated_fresh_namespace': True,
            'executed_Store_cleanup_native_provider': False}

with tempfile.TemporaryDirectory(prefix='lanl-cpu-report-startup-a4-', dir='/private/tmp') as folder:
    root = Path(folder)
    cases = {'startup': run_case(args.dispatcher, root)}
    if args.original:
        cases['original_missing_import'] = run_case(args.original, root)
        cases['cleanup_hash_tamper'] = run_case(args.dispatcher, root, tamper='cleanup')
        cases['processes_hash_tamper'] = run_case(args.dispatcher, root, tamper='processes')
    passed = cases['startup']['returncode'] == 0
    if args.original:
        passed = passed and cases['original_missing_import']['error'] == "NameError: name 'hashlib' is not defined"
        passed = passed and all(cases[key]['error'] == 'AssertionError' and cases[key]['returncode'] != 0
                               for key in ('cleanup_hash_tamper', 'processes_hash_tamper'))
    result = {'format': 'swdb.cpu-report-startup-regression.v1',
              'dispatcher': str(args.dispatcher),
              'dispatcher_sha256': hashlib.sha256(args.dispatcher.read_bytes()).hexdigest(),
              'fixture_sha256': {key: hashlib.sha256(value).hexdigest() for key, value in FIXTURES.items()},
              'cases': cases, 'passed': passed}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed else 1)
