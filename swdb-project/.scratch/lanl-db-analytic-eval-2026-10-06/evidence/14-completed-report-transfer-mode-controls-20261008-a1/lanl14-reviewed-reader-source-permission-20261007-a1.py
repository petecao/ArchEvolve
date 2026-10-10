import datetime, hashlib, json, os, pathlib, stat, subprocess, sys

PRIMARY = pathlib.Path('/data1/yanruj/ArchEvolve')
REV = 'c97d03175fd70e28397e7aa7ba43c5a9969ca7f4'
REL = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-lossless-report-export-controls-20261007-a1/lanl14_readonly_nine_export_admission_lossless_gzip_20261007_a1.py'
EXPECTED = '6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570'
assert os.getuid() == os.geteuid() == 114316761
assert sys.platform == 'linux' and os.uname().nodename.split('.')[0] == 'mbit10'
assert pathlib.Path(sys.executable).resolve() == pathlib.Path('/usr/bin/python3.12')
assert hashlib.sha256(pathlib.Path('/usr/bin/python3.12').read_bytes()).hexdigest() == 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'

def git(*args):
    r = subprocess.run(['/usr/bin/git', '-C', str(PRIMARY), *args], capture_output=True, check=True, timeout=25)
    assert not r.stderr and len(r.stdout) <= 65536
    return r.stdout

def stable(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_size, s.st_nlink, s.st_mtime_ns, s.st_ctime_ns)

assert git('rev-parse', 'HEAD').decode().strip() == REV
assert not git('status', '--porcelain', '--untracked-files=no')
assert git('ls-tree', REV, '--', REL).startswith(b'100644 blob ')
assert hashlib.sha256(git('show', REV + ':' + REL)).hexdigest() == EXPECTED
p = PRIMARY / REL
assert p.resolve(strict=True) == p and all(not x.is_symlink() for x in p.parents)
fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
try:
    before = os.fstat(fd)
    assert stat.S_ISREG(before.st_mode) and before.st_uid == 114316761 and before.st_nlink == 1 and before.st_size == 37647
    assert stat.S_IMODE(before.st_mode) in (0o644, 0o664, 0o666)
    raw = os.read(fd, 37648)
    assert len(raw) == 37647 and hashlib.sha256(raw).hexdigest() == EXPECTED
    assert stable(os.fstat(fd)) == stable(before) and stable(p.lstat()) == stable(before)
    if stat.S_IMODE(before.st_mode) != 0o644:
        os.fchmod(fd, 0o644)
    after = os.fstat(fd)
    assert (after.st_dev, after.st_ino, after.st_uid, after.st_gid, after.st_size, after.st_mtime_ns, after.st_nlink) == (before.st_dev, before.st_ino, before.st_uid, before.st_gid, before.st_size, before.st_mtime_ns, before.st_nlink)
    assert stat.S_IMODE(after.st_mode) == 0o644 and stable(p.lstat()) == stable(after)
    os.lseek(fd, 0, os.SEEK_SET)
    assert hashlib.sha256(os.read(fd, 37648)).hexdigest() == EXPECTED
finally:
    os.close(fd)
assert git('rev-parse', 'HEAD').decode().strip() == REV
assert not git('status', '--porcelain', '--untracked-files=no')
print(json.dumps({'format': 'swdb.lanl14-selected-reader-source-permission-facts.v1', 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(p), 'primary_revision': REV, 'uid': before.st_uid, 'device': before.st_dev, 'inode': before.st_ino, 'bytes': before.st_size, 'sha256': EXPECTED, 'before_mode': oct(stat.S_IMODE(before.st_mode)), 'after_mode': oct(stat.S_IMODE(after.st_mode)), 'source_bytes_and_Git_mode_unchanged': True, 'scientific_main_or_active_R14_change': False}))
