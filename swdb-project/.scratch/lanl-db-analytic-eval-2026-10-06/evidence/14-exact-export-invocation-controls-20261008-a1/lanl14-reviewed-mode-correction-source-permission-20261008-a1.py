import datetime, hashlib, json, os, pathlib, stat, subprocess, sys

PRIMARY = pathlib.Path('/data1/yanruj/ArchEvolve')
REV = '742aa576f69df2d2c70047a7acf49fafbe8a9abf'
REL = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-completed-report-transfer-mode-controls-20261008-a1/lanl14_correct_completed_report_transfer_modes_20261008_a1.py'
EXPECTED = 'ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7'
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
    assert stat.S_ISREG(before.st_mode) and before.st_uid == 114316761 and before.st_nlink == 1 and before.st_size == 29985
    assert stat.S_IMODE(before.st_mode) in (0o644, 0o664, 0o666)
    raw = os.read(fd, 29986)
    assert len(raw) == 29985 and hashlib.sha256(raw).hexdigest() == EXPECTED
    assert stable(os.fstat(fd)) == stable(before) and stable(p.lstat()) == stable(before)
    if stat.S_IMODE(before.st_mode) != 0o644:
        os.fchmod(fd, 0o644)
    after = os.fstat(fd)
    assert (after.st_dev, after.st_ino, after.st_uid, after.st_gid, after.st_size, after.st_mtime_ns, after.st_nlink) == (before.st_dev, before.st_ino, before.st_uid, before.st_gid, before.st_size, before.st_mtime_ns, before.st_nlink)
    assert stat.S_IMODE(after.st_mode) == 0o644 and stable(p.lstat()) == stable(after)
    os.lseek(fd, 0, os.SEEK_SET)
    assert hashlib.sha256(os.read(fd, 29986)).hexdigest() == EXPECTED
finally:
    os.close(fd)
assert git('rev-parse', 'HEAD').decode().strip() == REV
assert not git('status', '--porcelain', '--untracked-files=no')
print(json.dumps({'format': 'swdb.lanl14-selected-mode-correction-source-permission-facts.v1', 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(p), 'primary_revision': REV, 'uid': before.st_uid, 'device': before.st_dev, 'inode': before.st_ino, 'bytes': before.st_size, 'sha256': EXPECTED, 'before_mode': oct(stat.S_IMODE(before.st_mode)), 'after_mode': oct(stat.S_IMODE(after.st_mode)), 'source_bytes_and_Git_mode_unchanged': True, 'scientific_main_or_active_R14_change': False}))
