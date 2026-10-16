"""2026-10-16 ET. Passive initialized-V5 metadata/hash context only.

Never run the cold reader, import a project/YAML parser, or launch tools. Hash
full raw files remotely; transfer only pins and selected compact JSON context.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5')
CONSUMERS = {'initialized-source-consumer-closure-before.json', 'initialized-source-consumer-closure-after-bootstrap.json',
             'initialized-source-consumer-closure-after.json'}
JSON = {'lane.json', 'launch.json', 'source-after.json', 'resources.json', 'outer-resources.json',
        'initialized-profile/run-plan.json', 'initialized-profile/junit-census.json',
        'initialized-collection.json', 'initialized-linux-role.json'}


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.link', 'os.symlink', 'os.truncate'}:
        raise RuntimeError('passive initialized metadata refuses ' + event)
    if event == 'open':
        _path, mode, flags = args
        if mode is not None and any(char in mode for char in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive initialized metadata refuses mutation')


sys.addaudithook(deny)


def attributes(value):
    return tuple(getattr(value, name) for name in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def main():
    assert RAW.resolve(strict=True) == RAW and RAW.is_dir() and not RAW.is_symlink()
    files, links, directories, data, consumers = {}, {}, [], {}, {}
    for path in sorted(RAW.rglob('*')):
        name = str(path.relative_to(RAW)); before = path.lstat()
        if stat.S_ISDIR(before.st_mode): directories.append(name); continue
        if stat.S_ISLNK(before.st_mode): links[name] = {'target': os.readlink(path)}; continue
        assert stat.S_ISREG(before.st_mode)
        with path.open('rb') as stream: value = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert attributes(before) == attributes(path.lstat())
        files[name] = {'bytes': before.st_size, 'sha256': value}
        if name in JSON or name in CONSUMERS:
            assert before.st_size <= 8 * 2**20
            raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == value
            parsed = json.loads(raw)
            if name in CONSUMERS:
                consumers[name] = {'canonical_sha256': hashlib.sha256(json.dumps(parsed, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                    'count': parsed['count'], 'total_bytes': parsed['total_bytes'], 'source_commit': parsed['source_commit'],
                    'trees': parsed['trees'], 'physical_git_blob_equality': parsed['physical_git_blob_equality']}
            else: data[name] = parsed
    assert len(files) <= 20000 and sum(row['bytes'] for row in files.values()) <= 8589934592
    return {'date': '2026-10-16 ET', 'captured_utc': datetime.now(timezone.utc).isoformat(), 'raw': str(RAW),
        'raw_manifest': {'files': files, 'symlinks': links}, 'directories': directories, 'json': data,
        'consumers': consumers, 'file_count': len(files), 'total_bytes': sum(row['bytes'] for row in files.values()),
        'scope': 'Passive metadata and streaming hashes only; no raw record/source/compiler/native payload transfer; no actual cold reader/project/YAML/tool execution'}


if __name__ == '__main__': print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
