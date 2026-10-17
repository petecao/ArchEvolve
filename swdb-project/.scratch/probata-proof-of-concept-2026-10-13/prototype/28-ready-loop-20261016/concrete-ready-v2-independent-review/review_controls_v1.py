"""2026-10-16 ET. Native protocol source delta only; no native calls."""
import ast
import difflib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PACKET = ROOT / 'concrete-ready-v2/source-packet-v2.json'
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise AssertionError('source-only readiness protocol controls: ' + event)


sys.addaudithook(audit)


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def snapshot():
    rows = json.loads(PACKET.read_bytes())['files']
    for row in rows:
        assert pin(Path(row['path'])) == row
    return rows


before = snapshot()
sys.path.insert(0, str(ROOT))
import concrete_ready_v1 as old
import concrete_ready_v2 as new
for name in ('BACKEND_SHA', 'CALLER', 'ZERO_CALLER', 'LOOP', 'WP_PREFIX', 'CONCRETE_PREFIX', 'CONCRETE_SUFFIX'):
    assert getattr(new, name) == getattr(old, name), name
assert new.CONCRETE_MAIN.split('#else\n', 1)[0] == old.CONCRETE_MAIN.split('#else\n', 1)[0]
for name in ('function_body', 'need', 'wp_without_loop_annotation', 'remove_loop_annotation'):
    def definition(path):
        return ast.dump(next(node for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == name), include_attributes=False)
    assert definition(ROOT / 'concrete_ready_v1.py') == definition(ROOT / 'concrete_ready_v2.py'), name
delta = ''.join(difflib.unified_diff((ROOT / 'concrete_ready_v1.py').read_text().splitlines(True), (ROOT / 'concrete_ready_v2.py').read_text().splitlines(True), fromfile='v1', tofile='v2'))
assert delta.encode() == (PACKET.parent / 'native-protocol-delta.patch').read_bytes()
backend = (ROOT.parent / '28-whole-interface-resume-20261016/whole_value_backend_v1.h').read_bytes()
previous, generated = old.prepare(backend), new.prepare(backend)
assert generated == json.loads((PACKET.parent / 'prepared.json').read_bytes())
for key in previous:
    if key not in {'schema', 'concrete_c', 'concrete_c_sha256'}:
        assert previous[key] == generated[key], key
for field, filename in [('concrete_c', 'concrete-ready.c'), ('wp_c', 'wp-ready.c'), ('wp_negative_c', 'wp-zero-read.c')]:
    assert generated[field].encode() == (PACKET.parent / filename).read_bytes()
assert len(generated['native_control_plan']) == 47
assert all(row['actual_execution'] is False for row in generated['native_control_plan'])
spec = importlib.util.spec_from_file_location('_independent_ready_v2', ROOT / 'test_concrete_ready_v2.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
(HERE / 'fresh-pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 6 and result.wasSuccessful() and not result.skipped
assert not ATTEMPTS and snapshot() == before
print(json.dumps(dict(date='2026-10-16 Eastern', packet=pin(PACKET), pins=12, generated_outputs_exact=True, complete_symbolic_backend_and_WP_unchanged=True, native_controls_prospective_only=47, tests=6, failures=0, errors=0, skips=0, external_attempts=ATTEMPTS, actual_native_or_proof_execution=False), sort_keys=True))
