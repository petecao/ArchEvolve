"""2026-10-16 ET. Two retained runtime JSON schemas/scalars only; read only."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5')
NAMES = ('runtime-provenance.json', 'initialized-project-runtime-provenance.json')


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.link', 'os.symlink', 'os.truncate'}:
        raise RuntimeError('retained runtime schema collector refuses ' + event)
    if event == 'open':
        _path, mode, flags = arguments
        if mode is not None and any(char in mode for char in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('retained runtime schema collector refuses writes')


sys.addaudithook(deny)


def shape(value):
    if isinstance(value, dict): return {key: shape(val) for key, val in value.items()}
    if isinstance(value, list): return {'kind': 'list', 'length': len(value), 'element_types': sorted({type(val).__name__ for val in value})}
    return type(value).__name__


def selected(value, path=''):
    result = {}
    if isinstance(value, dict):
        for key, val in value.items():
            name = path + '.' + key if path else key
            if key in {'version', 'cwd', 'source_commit'} and isinstance(val, (str, int, bool, type(None))): result[name] = val
            if key == 'command' and isinstance(val, list) and all(isinstance(item, str) for item in val): result[name] = val
            if key in {'c_lowering', 'naming_rules', 'check', 'command_executable', 'driver', 'headers', 'parser', 'clang'}:
                if isinstance(val, dict) and all(isinstance(item, (str, int, bool, type(None))) for item in val.values()): result[name] = val
            result.update(selected(val, name))
    return result


def main():
    result = {}
    for name in NAMES:
        path = RAW / name; assert path.resolve(strict=True) == path
        before = path.lstat(); assert stat.S_ISREG(before.st_mode)
        raw = path.read_bytes(); after = path.lstat()
        attributes = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        assert attributes(before) == attributes(after) and len(raw) == before.st_size
        value = json.loads(raw)
        result[name] = {'pin': {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
                        'schema': shape(value), 'selected_scalars': selected(value)}
        if 'tool' in value: result[name]['selected_tool_descriptor'] = value['tool']
        if 'accepted_linux_components' in value:
            result[name]['selected_accepted_linux_components'] = value['accepted_linux_components']
    return {'date': '2026-10-16 ET', 'captured_utc': datetime.now(timezone.utc).isoformat(), 'raw': str(RAW),
            'files': result, 'scope': 'Two retained runtime JSON schema/key/selected scalar observations only; no actual reader, records, project import or scientific/tool process'}


if __name__ == '__main__': print(json.dumps(main(), indent=2, sort_keys=True, allow_nan=False))
