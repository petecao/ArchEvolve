"""2026-10-16 ET. Authorized passive trace-V4 metadata; no actual cold audit.

Only stream hashes, compact JSON context and YAML key/scalar metadata leave the
raw root. Scientific source, record, trace, native and binary payloads stay there.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v4')
JSON = {'lane.json', 'launch.json', 'source-after.json', 'resources.json', 'outer-resources.json',
        'memory-trace-linux-role-admission.json', 'entry-isolated-startup.json', 'pytest-child-startup.json',
        'memory-trace-profile/junit-census.json', 'memory-trace-profile/collection.json',
        'memory-trace-profile/pytest-arguments.json', 'memory-trace-profile/launch-provenance.json',
        'memory-trace-profile/runtime-provenance.json', 'memory-trace-profile/actual-pytest-child-startup.json'}
FINAL = 'memory-trace-final-physical-check.json'


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.link', 'os.symlink', 'os.truncate'}:
        raise RuntimeError('passive trace metadata refuses ' + event)
    if event == 'open':
        _path, mode, flags = args
        if mode is not None and any(char in mode for char in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive trace metadata refuses mutation')


sys.addaudithook(deny)


def attributes(value):
    return tuple(getattr(value, name) for name in ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def compact_consumer(value):
    return {**{key: value[key] for key in ('source_commit', 'trees', 'count', 'total_bytes', 'physical_git_blob_equality')},
            'canonical_sha256': hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()}


def main():
    assert RAW.resolve(strict=True) == RAW and RAW.is_dir() and not RAW.is_symlink()
    files, links, directories, data, records = {}, {}, [], {}, {}
    for path in sorted(RAW.rglob('*')):
        name = str(path.relative_to(RAW)); before = path.lstat()
        if stat.S_ISDIR(before.st_mode): directories.append(name); continue
        if stat.S_ISLNK(before.st_mode): links[name] = {'target': os.readlink(path)}; continue
        assert stat.S_ISREG(before.st_mode)
        with path.open('rb') as stream: value = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert attributes(before) == attributes(path.lstat())
        files[name] = {'bytes': before.st_size, 'sha256': value}
        if name in JSON or name == FINAL:
            assert before.st_size <= 8 * 2**20
            raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == value
            parsed = json.loads(raw)
            if name == FINAL:
                parsed = {**parsed, 'source_before': compact_consumer(parsed['source_before']),
                          'source_after': compact_consumer(parsed['source_after'])}
            data[name] = parsed
        elif '/records/proofs/' in name and path.suffix == '.yaml':
            # Lexical metadata only; no YAML interpretation or record acceptance.
            raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == value
            text = raw.decode('utf-8')
            keys = sorted(set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', text, re.M)))
            scalars = {key: val for key, val in re.findall(r'^(id|kind|verdict|failure_class): ([^\n]+)$', text, re.M)}
            records[name] = {'top_keys': keys, 'top_scalars': scalars}
    assert len(files) <= 20000 and sum(row['bytes'] for row in files.values()) <= 8589934592
    return {'date': '2026-10-16 ET', 'captured_utc': datetime.now(timezone.utc).isoformat(), 'raw': str(RAW),
            'raw_manifest': {'files': files, 'symlinks': links}, 'directories': directories, 'json': data,
            'record_lexical_metadata': records, 'file_count': len(files),
            'total_bytes': sum(row['bytes'] for row in files.values()),
            'scope': 'Passive JSON/lexical metadata and streaming hashes only; no scientific payload transfer, actual reader, project import or tool execution'}


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
