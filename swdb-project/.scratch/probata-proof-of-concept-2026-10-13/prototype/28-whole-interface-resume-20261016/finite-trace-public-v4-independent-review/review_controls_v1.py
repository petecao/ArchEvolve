"""2026-10-16 ET. Independent local source checks; no project tools or children."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / 'finite-trace-public-v4/source-packet-v4.json'
ROOT = PACKET.parent
DENIED = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        DENIED.append(event)
        raise AssertionError('source-only independent control: ' + event)


sys.addaudithook(audit)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def pinned_rows(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value):
            yield value
        for item in value.values():
            yield from pinned_rows(item)
    elif isinstance(value, list):
        for item in value:
            yield from pinned_rows(item)


def snapshot():
    rows = list(pinned_rows(json.loads(PACKET.read_bytes())))
    for row in rows:
        assert pin(Path(row['path'])) == {key: row[key] for key in ('path', 'bytes', 'sha256')}, row['path']
    return rows


def definitions(raw):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


before = snapshot()
inverse = json.loads((ROOT / 'attribution-inverse-v4.json').read_bytes())
for name, row in inverse['files'].items():
    old = Path(row['predecessor']['path']).read_text()
    new = Path(row['successor']['path']).read_text()
    reconstructed = new
    for edit in reversed(row['edits']):
        assert reconstructed[edit['new_start']:edit['new_end']] == edit['after'], name
        reconstructed = reconstructed[:edit['new_start']] + edit['before'] + reconstructed[edit['new_end']:]
    assert reconstructed == old, name
    old_defs, new_defs = definitions(old), definitions(new)
    assert {name for name in old_defs if old_defs[name] == new_defs.get(name)} == set(row['unchanged_definition_ASTs'])
    assert {name for name in set(old_defs) | set(new_defs) if old_defs.get(name) != new_defs.get(name)} == set(row['changed_definition_ASTs'])

suite = unittest.TestSuite()
for index, filename in enumerate(('test_finite_public.py', 'test_rule_scope_v1.py', 'test_summary_attribution_v1.py')):
    spec = importlib.util.spec_from_file_location('_independent_finite_v4_' + str(index), ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
(HERE / 'fresh-pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 26 and result.wasSuccessful() and not result.skipped
assert not DENIED
after = snapshot()
assert before == after
print(json.dumps({'date': '2026-10-16 Eastern', 'packet': pin(PACKET), 'pin_occurrences': len(before), 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped), 'denied_attempts': DENIED, 'all_declared_source_bytes_unchanged': before == after, 'complete_attribution_inverses': True, 'actual_project_compiler_native_verifier_network_execution': False}, sort_keys=True))
