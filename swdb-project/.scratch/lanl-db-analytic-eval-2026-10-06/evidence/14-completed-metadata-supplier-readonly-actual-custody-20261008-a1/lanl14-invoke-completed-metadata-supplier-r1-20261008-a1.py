"""Preparation only: parent selects ONE read-only invocation after real completion."""
import hashlib, json, os, re, socket, stat, sys
from pathlib import Path

SOURCE = Path('/data1/yanruj/lanl14-completed-source-controls-20261008-a1/completed_metadata_supplier_r1.py')
EXPECTED_SHA = '0e8ad57fe58f631298502215732a3425ace0264e7348ecea51e6258ebf85f911'
KEYS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')

def stamp(value):
    return {key: getattr(value, key) for key in KEYS}

def require(value):
    if not value:
        raise RuntimeError('completed_supplier_bootstrap_refused')

try:
    require(len(sys.argv) == 2 and re.fullmatch('[0-9a-f]{40}', sys.argv[1]))
    expected_primary = sys.argv[1]
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == 114316761 and sys.flags.dont_write_bytecode == 1
            and sys.flags.optimize == 0 and Path(sys.executable).resolve() == Path('/usr/bin/python3.12'))
    native = Path('/usr/bin/python3.12'); ns = native.lstat()
    require(stat.S_ISREG(ns.st_mode) and ns.st_uid == 0 and ns.st_nlink == 1
            and not ns.st_mode & 0o022 and ns.st_mode & 0o111 and ns.st_size == 8020928)
    nb = native.read_bytes()
    require(len(nb) == 8020928 and hashlib.sha256(nb).hexdigest() == 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
            and stamp(ns) == stamp(native.lstat()) and nb[:6] == b'\x7fELF\x02\x01'
            and int.from_bytes(nb[18:20], 'little') == 62)
    require(not any(p.is_symlink() for p in (SOURCE, *SOURCE.parents)) and SOURCE.resolve(strict=True) == SOURCE)
    for root in (Path('/data1/yanruj'), SOURCE.parent):
        value = root.lstat()
        require(stat.S_ISDIR(value.st_mode) and value.st_uid == 114316761 and stat.S_IMODE(value.st_mode) == 0o700)
    before = SOURCE.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == 114316761 and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o644 and before.st_size == 21759
            and before.st_dev == 2097 and before.st_ino == 55713065)
    fd = os.open(SOURCE, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd)) == stamp(before))
        body = os.read(fd, 21760)
        require(len(body) == 21759 and not os.read(fd, 1) and hashlib.sha256(body).hexdigest() == EXPECTED_SHA
                and stamp(os.fstat(fd)) == stamp(before) == stamp(SOURCE.lstat()))
    finally:
        os.close(fd)
    # Execute only the returned, hash-verified reviewed bytes; no reread for compilation.
    sys.argv = [str(SOURCE), '--deadline-s', '600', '--expected-primary', expected_primary]
    scope = {'__name__': '__main__', '__file__': str(SOURCE), '__package__': None}
    exec(compile(body, str(SOURCE), 'exec'), scope)
except Exception as failure:
    print(json.dumps({'format': 'swdb.lanl14-completed-metadata-supplier-bootstrap-refusal.v1',
                      'failure_type': type(failure).__name__, 'sealed': False,
                      'scientific_admission': False, 'permission_actions': 0}, sort_keys=True))
    raise SystemExit(2)
