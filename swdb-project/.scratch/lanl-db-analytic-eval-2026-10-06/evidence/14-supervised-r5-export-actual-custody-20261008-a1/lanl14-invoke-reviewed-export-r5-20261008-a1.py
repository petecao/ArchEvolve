"""Parent selects one reviewed R5 supervised export invocation."""
import hashlib, json, os, socket, stat, sys
from pathlib import Path

SOURCE = Path('/data1/yanruj/lanl14-completed-source-controls-20261008-a1/export_invocation_r5.py')
SHA = '62808f732d3ca492c102bbeb0b0ccab5fcb6ed2c63efd088d8ccdac845d362b7'
KEYS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
def stamp(value): return {key: getattr(value, key) for key in KEYS}
def require(value):
    if not value: raise RuntimeError('reviewed_export_invocation_bootstrap_refused')
try:
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == 114316761 and sys.flags.dont_write_bytecode == 1
            and sys.flags.optimize == 0 and Path(sys.executable).resolve() == Path('/usr/bin/python3.12'))
    for name, size, digest in (
        ('/usr/bin/python3.12', 8020928, 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
        ('/usr/bin/timeout', 39880, '12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52')):
        path = Path(name); before = path.lstat(); body = path.read_bytes()
        require(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and before.st_nlink == 1
                and not before.st_mode & 0o022 and before.st_mode & 0o111
                and len(body) == before.st_size == size and hashlib.sha256(body).hexdigest() == digest
                and stamp(before) == stamp(path.lstat()) and body[:6] == b'\x7fELF\x02\x01'
                and int.from_bytes(body[18:20], 'little') == 62)
    require(not any(p.is_symlink() for p in (SOURCE, *SOURCE.parents)) and SOURCE.resolve(strict=True) == SOURCE)
    root = Path('/data1/yanruj').lstat()
    require(stat.S_ISDIR(root.st_mode) and root.st_uid == 114316761 and stat.S_IMODE(root.st_mode) == 0o700)
    before = SOURCE.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid == 114316761 and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o644 and before.st_size == 35775
            and before.st_dev == 2097 and before.st_ino == 55713064)
    fd = os.open(SOURCE, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd)) == stamp(before))
        body = os.read(fd, 35776)
        require(len(body) == 35775 and not os.read(fd, 1) and hashlib.sha256(body).hexdigest() == SHA
                and stamp(os.fstat(fd)) == stamp(before) == stamp(SOURCE.lstat()))
    finally: os.close(fd)
    sys.argv = [str(SOURCE), *sys.argv[1:]]
    exec(compile(body, str(SOURCE), 'exec'), {'__name__': '__main__', '__file__': str(SOURCE), '__package__': None})
except Exception as exc:
    print(json.dumps({'format': 'swdb.lanl14-reviewed-export-invocation-bootstrap-refusal.v1',
                      'failure_type': type(exc).__name__, 'sealed': False, 'scientific_admission': False}))
    raise SystemExit(2)
