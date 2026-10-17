"""2026-10-16 ET. Root-admitted exact V11 metadata-observer dispatch, once."""
import hashlib
import json
from pathlib import Path
import selectors
import subprocess
import time

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
ANCILLARY = HERE.parent / 'normalized-unit-envelope-v5-dispatch/root-ancillary-packet-v5.json'
ADMISSION = POC / 'evidence/t28-semantic-observer-v5-root-once-admission-20261016.json'
assert hashlib.sha256(ANCILLARY.read_bytes()).hexdigest() == '4358a403da63e98e40dec6bc1aaf04171388a6b0af5c2b83e98649984557e632'
assert hashlib.sha256(ADMISSION.read_bytes()).hexdigest() == '99a7c8cd7b81a6fe1e5b44c974f91f5a9aca0e38a10de16e7e065a6d768e2a4d'
selected = json.loads(ANCILLARY.read_bytes())
for key in ('launcher', 'source_review', 'bare_argv', 'envelope_command', 'source_packet'):
    row = selected[key]
    raw = Path(row['path']).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
ARGV = selected['exact_local_launcher_argv']
with (HERE / 'dispatch-attempt-v5.json').open('x') as stream:
    json.dump(dict(date='2026-10-16 Eastern', argv=ARGV, root_admission_sha256='99a7c8cd7b81a6fe1e5b44c974f91f5a9aca0e38a10de16e7e065a6d768e2a4d', once_only=True, local_wall_cap_seconds=180, stdout_cap_bytes=131072, stderr_cap_bytes=131072), stream, sort_keys=True)
started = time.monotonic()
child = subprocess.Popen(ARGV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
selector = selectors.DefaultSelector()
selector.register(child.stdout, selectors.EVENT_READ, ('stdout', 131072))
selector.register(child.stderr, selectors.EVENT_READ, ('stderr', 131072))
buffers = {'stdout': bytearray(), 'stderr': bytearray()}
failure = None
try:
    while selector.get_map():
        if time.monotonic() - started > 180:
            failure = 'local_dispatch_wall_cap'
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
outputs = {}
for name, raw in buffers.items():
    path = HERE / ('dispatch-' + name + '-v5.' + ('json' if name == 'stdout' else 'log'))
    with path.open('xb') as stream:
        stream.write(raw)
    outputs[name] = dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
result = dict(date='2026-10-16 Eastern', argv=ARGV, actual_exit=code, wall_seconds=time.monotonic()-started, local_failure=failure, outputs=outputs, launched_once=True, actual_observer_result_not_inferred=True)
with (HERE / 'dispatch-invocation-v5.json').open('x') as stream:
    json.dump(result,stream,indent=2,sort_keys=True)
    stream.write('\n')
print(json.dumps(result,sort_keys=True))
raise SystemExit(code if not failure else 1)
