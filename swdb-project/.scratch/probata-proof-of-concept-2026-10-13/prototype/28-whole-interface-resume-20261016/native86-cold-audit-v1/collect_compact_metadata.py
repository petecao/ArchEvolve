"""2026-10-16 ET. Authorized passive metadata/census collection only.

No actual cold-reader admission, compiler/native/version/solver/project process.
Source, frozen source, objects and binaries are streamed into SHA-256 only;
their payloads are never included in output. No remote filesystem writes.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-whole-native86-2baf722f-v4')
NAMES = {'launch.json', 'component/used-inputs.json', 'component/inputs-before.json',
         'component/artifact-manifest.json', 'native86-runtime-before.json',
         'native86-runtime-after.json', 'source-before.json', 'source-after.json',
         'final.json', 'watch-state.json', 'state.json', 'resources.json',
         'outer-resources.json', 'lane.json', 'root-guard-adaptation.json'}


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.truncate'}:
        raise RuntimeError('passive metadata collection refuses ' + event)
    if event == 'open':
        _path, mode, flags = arguments
        if mode is not None and any(c in mode for c in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive metadata collection refuses filesystem writes')


sys.addaudithook(deny)


def fields(value):
    return tuple(getattr(value, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def main():
    assert RAW.resolve(strict=True) == RAW and RAW.is_dir() and not RAW.is_symlink()
    rows, data, directories = [], {}, []
    for path in sorted(RAW.rglob('*')):
        relative = str(path.relative_to(RAW)); before = path.lstat()
        if stat.S_ISDIR(before.st_mode): directories.append(relative); continue
        if stat.S_ISLNK(before.st_mode): raise ValueError('unreviewed raw symlink')
        if not stat.S_ISREG(before.st_mode): raise ValueError('unreviewed raw special input')
        with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert fields(before) == fields(path.stat())
        rows.append({'relative': relative, 'bytes': before.st_size, 'sha256': digest})
        if relative in NAMES:
            assert before.st_size <= 2**20
            raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == digest
            data[relative] = json.loads(raw)
    assert len(rows) <= 100 and sum(row['bytes'] for row in rows) <= 16 * 2**20
    final = {str(path.relative_to(RAW)) for path in RAW.rglob('*') if path.is_file()}
    assert final == {row['relative'] for row in rows}
    return {'date': '2026-10-16 ET', 'captured_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Read-only compact JSON metadata and complete streamed raw-file hashes; no raw source/frozen/object/binary payload transfer, no actual cold reader or scientific reexecution',
        'raw_root': str(RAW), 'files': rows, 'directories': directories, 'json': data,
        'file_count': len(rows), 'total_bytes': sum(row['bytes'] for row in rows),
        'native_compiler_version_solver_project_child_launched': False}


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
