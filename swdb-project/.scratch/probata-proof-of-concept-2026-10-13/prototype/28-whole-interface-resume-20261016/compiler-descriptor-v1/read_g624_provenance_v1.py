"""Once-admitted bounded passive read of one retained provenance document."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

PATH = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2/runtime-provenance.json')
EXPECTED_BYTES = 3368
EXPECTED_SHA = '88b89c657b024a9d2d22a7ebe2e18ee7cc9e0e23756952f3c672610bb6a4144c'


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('passive metadata only')
    if event == 'open':
        path, mode, flags = args
        if path != str(PATH) or not isinstance(mode, str) or mode != 'r' or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('only one selected regular metadata file may be read')
    if event in {'os.mkdir', 'os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.chmod', 'os.chown', 'os.link', 'os.symlink', 'os.truncate', 'os.utime', 'os.chdir', 'os.putenv', 'os.unsetenv'}:
        raise RuntimeError('passive metadata reader writes refused')


def stable(st):
    return tuple(getattr(st, name) for name in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


started = time.monotonic()
sys.addaudithook(audit)
for part in (PATH, *PATH.parents):
    before = part.lstat()
    assert not stat.S_ISLNK(before.st_mode)
assert PATH.resolve(strict=True) == PATH
before = PATH.lstat()
assert stat.S_ISREG(before.st_mode) and before.st_size == EXPECTED_BYTES
with PATH.open('rb') as source:
    payload = source.read(EXPECTED_BYTES + 1)
assert stable(PATH.lstat()) == stable(before)
assert len(payload) == EXPECTED_BYTES and hashlib.sha256(payload).hexdigest() == EXPECTED_SHA
value = json.loads(payload)
print(json.dumps({'schema': 'g624-one-provenance-passive-read-1', 'path': str(PATH), 'bytes': len(payload),
    'sha256': hashlib.sha256(payload).hexdigest(), 'document': value, 'stable_metadata': True,
    'compiler_native_solver_or_version_query': False, 'measurement_raw_unchanged': True,
    'wall_seconds': time.monotonic() - started}, sort_keys=True, separators=(',', ':')))
