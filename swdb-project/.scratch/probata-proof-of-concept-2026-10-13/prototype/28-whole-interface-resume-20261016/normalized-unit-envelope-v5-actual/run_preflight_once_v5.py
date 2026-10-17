"""2026-10-16 ET. Root-authorized single bounded passive preflight only."""
import hashlib
import json
from pathlib import Path
import selectors
import subprocess
import time

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'normalized-unit-envelope-v5-dispatch/root-derived-scoped-preflight-v5.py'
SOURCE = SCRIPT.read_bytes()
EXPECTED = 'fb3aa731268eda7fad75a8b040079d1fb751182a70ace8288eaff99f58ac561c'
assert len(SOURCE) == 22205 and hashlib.sha256(SOURCE).hexdigest() == EXPECTED
ARGV = ['/usr/bin/ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'mbit10', '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '35s', '/usr/bin/python3', '-I', '-B', '-']
with (HERE / 'preflight-attempt-v5.json').open('x') as stream:
    json.dump(dict(date='2026-10-16 Eastern', purpose='exact root-authorized read-only preflight; no dispatch', argv=ARGV, stdin=dict(path=str(SCRIPT),bytes=len(SOURCE),sha256=EXPECTED), local_wall_cap_seconds=55, stdout_cap_bytes=131072, stderr_cap_bytes=16384), stream, sort_keys=True)
start = time.monotonic()
child = subprocess.Popen(ARGV, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
child.stdin.write(SOURCE)
child.stdin.close()
selector = selectors.DefaultSelector()
selector.register(child.stdout, selectors.EVENT_READ, ('stdout', 131072))
selector.register(child.stderr, selectors.EVENT_READ, ('stderr', 16384))
buffers = {'stdout': bytearray(), 'stderr': bytearray()}
failure = None
try:
    while selector.get_map():
        if time.monotonic() - start > 55:
            failure = 'local_wall_cap'
            break
        for key, _ in selector.select(timeout=0.2):
            name, cap = key.data
            chunk = key.fileobj.read1(4096)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            if len(buffers[name]) + len(chunk) > cap:
                failure = name + '_extent_cap'
                break
            buffers[name].extend(chunk)
        if failure:
            break
finally:
    if failure and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
    code = child.wait(timeout=5)
    selector.close()
paths = {}
for name, raw in buffers.items():
    path = HERE / ('preflight-' + name + '-v5.' + ('json' if name == 'stdout' else 'log'))
    with path.open('xb') as stream:
        stream.write(raw)
    paths[name] = dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
result = dict(date='2026-10-16 Eastern', argv=ARGV, actual_exit=code, actual_wall_seconds=time.monotonic()-start, local_refusal=failure, output=paths, exact_script_after=SCRIPT.read_bytes()==SOURCE, actual_launcher_or_lease_or_output_creation=False)
with (HERE / 'preflight-invocation-v5.json').open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(result,sort_keys=True))
raise SystemExit(code if not failure else 1)
