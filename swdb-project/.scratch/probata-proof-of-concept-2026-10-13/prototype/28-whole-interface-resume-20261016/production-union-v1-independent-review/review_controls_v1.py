"""2026-10-16 ET. Independent frozen union review; no project imports or tools."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'production-union-v1'
PACKET = ROOT / 'source-packet-v1.json'
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'} or (event == 'import' and str(args[0]).split('.')[0] == 'swdb'):
        ATTEMPTS.append(event)
        raise AssertionError('union source review blocks project/native/external execution: ' + event)


sys.addaudithook(audit)


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def rows(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value):
            yield value
        for item in value.values():
            yield from rows(item)
    elif isinstance(value, list):
        for item in value:
            yield from rows(item)


def snapshot():
    result = list(rows(json.loads(PACKET.read_bytes())))
    for row in result:
        assert pin(Path(row['path'])) == {key: row[key] for key in ('path', 'bytes', 'sha256')}
    table = json.loads((ROOT / 'production-paths-and-bases-v1.json').read_bytes())
    for row in rows(table):
        assert pin(Path(row['path'])) == {key: row[key] for key in ('path', 'bytes', 'sha256')}
    return result


before = snapshot()
for path in (ROOT / 'proposed').rglob('*.py'):
    ast.parse(path.read_bytes(), filename=str(path))
spec = importlib.util.spec_from_file_location('_independent_union_controls', ROOT / 'test_union_v1.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
(HERE / 'fresh-pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 8 and result.wasSuccessful() and not result.skipped
assert not ATTEMPTS and snapshot() == before
print(json.dumps(dict(date='2026-10-16 Eastern', packet=pin(PACKET), packet_pin_occurrences=len(before), selected_paths=69, SourceUnit_roles=47, TraceUnit_roles=70, prospective_basis_members=79, tests=8, failures=0, errors=0, skips=0, external_attempts=ATTEMPTS, complete_patch_and_role_inverses=True, shared_apply_or_Git_or_actual_runtime=False), sort_keys=True))
