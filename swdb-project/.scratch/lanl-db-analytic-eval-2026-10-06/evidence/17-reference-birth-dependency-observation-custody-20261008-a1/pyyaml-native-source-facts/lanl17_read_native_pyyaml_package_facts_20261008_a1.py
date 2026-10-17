"""Installed system PyYAML facts only. Updated 2026-10-08 ET; SOURCE ONLY / NOT RUN."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import sys
import time

UID = 114316761
BASE = Path('/data1/yanruj')
SYSTEM = Path('/usr/lib/python3/dist-packages')
PYTHON = Path('/usr/bin/python3.12')
PYTHON_SHA = 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
END = time.monotonic() + 30
FIELDS = ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')


def require(value, code):
    if not value:
        raise ValueError(code)


def tick():
    require(time.monotonic() < END, 'package_query_deadline')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def values(s):
    return {key: getattr(s, 'st_' + key) for key in FIELDS}


def stamp(p):
    return values(p.lstat())


def canonical_path(p):
    require(p.is_absolute() and p.resolve(strict=True) == p
            and not any(x.is_symlink() for x in (p, *p.parents)), 'noncanonical_or_symlink')


def read(p, cap, owner):
    tick()
    canonical_path(p)
    before = stamp(p)
    require(stat.S_ISREG(before['mode']) and before['uid'] == owner and before['nlink'] == 1
            and not before['mode'] & 0o7022 and 0 <= before['size'] <= cap, 'system_file_owner_mode_or_bound')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(values(os.fstat(fd)) == before, 'opened_file_changed')
        digest = hashlib.sha256()
        read_bytes = 0
        while True:
            tick()
            block = os.read(fd, min(1024 * 1024, cap + 1 - read_bytes))
            if not block:
                break
            read_bytes += len(block)
            require(read_bytes <= cap, 'read_bound')
            digest.update(block)
        require(read_bytes == before['size'] and values(os.fstat(fd)) == before
                and stamp(p) == before, 'returned_file_changed')
    finally:
        os.close(fd)
    return {'path': str(p), 'bytes': read_bytes, 'sha256': digest.hexdigest(), 'stat': before}


def system_route(p):
    canonical_path(p)
    require(p.is_relative_to(SYSTEM), 'outside_fixed_system_package')
    for part in (p.parent, *p.parent.parents):
        if not part.is_relative_to(Path('/usr/lib')):
            continue
        s = stamp(part)
        require(stat.S_ISDIR(s['mode']) and s['uid'] == 0 and not s['mode'] & 0o7022,
                'unsafe_system_package_directory')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query-source-sha256', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{64}', args.query_source_sha256), 'explicit_own_source_pin')
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == UID and pwd.getpwuid(UID).pw_name == 'yanruj'
            and Path(sys.executable).resolve() == PYTHON and sys.flags.dont_write_bytecode,
            'native_host_account_startup')
    require(not any(os.environ.get(k) for k in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONINSPECT',
                                               'LD_PRELOAD', 'LD_LIBRARY_PATH'))
            and sys.flags.no_user_site and os.environ.get('PATH') == '/usr/bin:/bin', 'startup_overrides')
    own = Path(__file__).absolute()
    require(own.is_relative_to(BASE) and own.parent == BASE, 'private_query_source_scope')
    canonical_path(BASE)
    b = stamp(BASE)
    require(stat.S_ISDIR(b['mode']) and stat.S_IMODE(b['mode']) == 0o700 and b['uid'] == UID
            and b['gid'] == 0 and b['dev'] == 2097 and b['ino'] == 54132737, 'private_base_identity')
    own_pin = read(own, 64 * 1024, UID)
    require(own_pin['sha256'] == args.query_source_sha256, 'own_source_pin')
    native = read(PYTHON, 16 * 1024 * 1024, 0)
    require(native['bytes'] == 8020928 and native['sha256'] == PYTHON_SHA
            and native['stat']['mode'] & 0o111, 'native_python_pin')
    require('yaml' not in sys.modules, 'yaml_already_loaded')
    spec = importlib.util.find_spec('yaml')
    require(spec is not None and isinstance(spec.origin, str), 'system_yaml_unavailable')
    initial = Path(spec.origin)
    system_route(initial)
    require(initial.name == '__init__.py' and initial.parent.name == 'yaml', 'system_yaml_package_route')
    package = initial.parent
    before = {}
    def fail(error):
        raise ValueError('incomplete_package_visibility') from error
    for current, dirs, names in os.walk(package, followlinks=False, onerror=fail):
        tick()
        for name in sorted(dirs + names):
            p = Path(current) / name
            require(len(before) < 128, 'package_namespace_bound')
            s = stamp(p)
            require(not stat.S_ISLNK(s['mode']), 'package_symlink')
            if stat.S_ISDIR(s['mode']):
                require(s['uid'] == 0 and not s['mode'] & 0o7022, 'package_directory_mode')
            elif p.suffix in {'.py', '.pyc', '.so'}:
                system_route(p)
                before[str(p)] = read(p, 128 * 1024 * 1024 if p.suffix == '.so' else 16 * 1024 * 1024, 0)
    require(str(initial) in before, 'initial_module_not_pinned')
    yaml = importlib.import_module('yaml')
    require(Path(yaml.__file__) == initial and isinstance(yaml.__version__, str)
            and len(yaml.__version__) <= 64, 'loaded_yaml_origin_or_version')
    modules = {}
    for name, module in sorted(sys.modules.items()):
        if name != 'yaml' and not name.startswith('yaml.') and name != '_yaml':
            continue
        source = getattr(module, '__file__', None)
        require(isinstance(source, str) and len(modules) < 32, 'module_origin_or_namespace')
        p = Path(source)
        system_route(p)
        require(str(p) in before, 'imported_origin_not_pre_pinned')
        source_pin = read(p, 128 * 1024 * 1024 if p.suffix == '.so' else 16 * 1024 * 1024, 0)
        require(source_pin == before[str(p)], 'imported_source_changed')
        cached = getattr(module, '__cached__', None)
        row = {'source': source_pin, 'cached_origin': cached, 'cached_observed': False}
        if cached is not None:
            require(isinstance(cached, str), 'cached_origin_type')
            q = Path(cached)
            if os.path.lexists(q):
                system_route(q)
                require(str(q) in before, 'cached_origin_not_pre_pinned')
                cached_pin = read(q, 16 * 1024 * 1024, 0)
                require(cached_pin == before[str(q)], 'cached_source_changed')
                row.update(cached_observed=True, cached=cached_pin)
        modules[name] = row
    for path, original in before.items():
        p = Path(path)
        require(read(p, 128 * 1024 * 1024 if p.suffix == '.so' else 16 * 1024 * 1024, 0) == original,
                'system_package_postflight_changed')
    require(read(own, 64 * 1024, UID) == own_pin and read(PYTHON, 16 * 1024 * 1024, 0) == native,
            'own_or_native_changed')
    require({k: stamp(BASE)[k] for k in ('dev', 'ino', 'mode', 'uid', 'gid')}
            == {k: b[k] for k in ('dev', 'ino', 'mode', 'uid', 'gid')}, 'private_base_changed')
    result = {'format': 'swdb.lanl17-native-system-pyyaml-package-facts-original.v1', 'sealed': False,
              'checked_utc': datetime.now(timezone.utc).isoformat(), 'query_source': own_pin,
              'native_python': native, 'yaml_version': yaml.__version__, 'package': str(package),
              'yaml_init': before[str(initial)], 'imported_modules': modules,
              'preimport_and_postimport_existing_package_file_count': len(before),
              'package_file_hash_scope': 'All existing .py/.pyc/.so within the fixed system yaml package; imported origins must have been pinned before import.',
              'scope': 'Installed dependency observations only; no SWDB/control/main/request/binding/provider/campaign/cleanup or scientific admission.'}
    raw = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(len(raw) <= 32768, 'compact_metadata_output_bound')
    print(raw.decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'format': 'swdb.lanl17-package-facts-query-refusal.v1', 'sealed': False,
                          'error_class': type(error).__name__, 'error_sha256': sha(str(error).encode())}, sort_keys=True))
        sys.exit(1)
