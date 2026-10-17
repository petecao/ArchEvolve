"""2026-10-16 ET. Reconstruct inert readiness inputs without native execution."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
READY = HERE.parent
PACKET = READY / 'concrete-ready-v1/source-packet-v1.json'
DENIED = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        DENIED.append(event)
        raise AssertionError('readiness review permits no tools or native/network calls: ' + event)


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
sys.path.insert(0, str(READY))
import concrete_ready_v1 as producer
backend = (READY.parent / '28-whole-interface-resume-20261016/whole_value_backend_v1.h').read_bytes()
generated = producer.prepare(backend)
assert generated == json.loads((PACKET.parent / 'prepared.json').read_bytes())
for field, filename in [('concrete_c', 'concrete-ready.c'), ('wp_c', 'wp-ready.c'), ('wp_negative_c', 'wp-zero-read.c')]:
    assert generated[field].encode() == (PACKET.parent / filename).read_bytes()
assert producer.remove_loop_annotation(generated['wp_c']) == producer.wp_without_loop_annotation()
assert generated['concrete_c'].count(producer.CALLER) == 1
spec = importlib.util.spec_from_file_location('_independent_ready_controls', READY / 'test_concrete_ready_v1.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
(HERE / 'fresh-pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 5 and result.wasSuccessful() and not result.skipped
assert not DENIED and snapshot() == before
print(json.dumps(dict(date='2026-10-16 Eastern', packet=pin(PACKET), pins=len(before), generated_outputs_exact=True, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped), denied_attempts=DENIED, actual_compiler_native_solver_network_execution=False), sort_keys=True))
