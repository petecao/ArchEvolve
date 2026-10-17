"""2026-10-16 ET. INERT exact completed1433 source retirement controller.

Root must review/admit this exact stdin before execution. Only ordinary Git
worktree removal and a recoverable ref are mutable. All raw stays untouched.
No compiler, verifier, native helper, project import, hook or forced removal.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import time

PRIMARY = Path('/data1/yanruj/ArchEvolve')
SOURCE = Path('/data1/yanruj/probata-resume-20261016-1433b8f5')
COMMIT = '1433b8f58baa63538d1e8aa8a33d9ce566826407'
TREE = 'caebea95343008d22c4cb5ef5df7afdaab069865'
RECOVERY = 'refs/probata/recovery/20261016/source-1433b8f5'
RAW_PARENT = Path('/data/yanruj/EvolveSWDB_runs')
MIN_RAWS = ('probata-resume-20261016-1433b8f5-t25-closed-source-public-v3',
            'probata-resume-20261016-1433b8f5-t25-closed-source-public-v4')
PROTECTED = tuple(Path('/data1/yanruj/probata-resume-20261016-'+name)
                  for name in ('2baf722f', 'd7f685c6', '36266e10', '032e1851'))
LINKS = {
    'swdb-project/weeklogs/2026-09-24/.build/node_modules':
        '/Users/yanrujhou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',
    'swdb-project/weeklogs/2026-09-30/.build/node_modules':
        '../../2026-09-24/.build/node_modules',
}
EXPECTED_FILES = 12016
EXPECTED_BYTES = 1680110251
ENTRY_CAP = 50000
GIT_CAP = 16 * 1024**2
FILE_CAP = 256 * 1024**2
RAW_BYTES_CAP = 2 * 1024**3
SSH_BINARY_SHA = '95b291d957f87dd200796c4986c97b6f4d970e26ad620ec9174e69c13ec5c137'
SSH_BINARY_BYTES = 925512
SETTLED_PINS = {
    'lane.json': (842, '53104a2029fdbd5b1c8b4d9a21443ec4c69910feca470d2bbcd011349b01d0d4'),
    'resources.json': (167, 'd6462ea32fa50df36e1196ab86b12e0d939b6d085fd86669f2785c816fbb4a8c'),
    'outer-resources.json': (167, '1710a0ecafd4a0e2ea03bbe036c691b0a2e64a70439760e1d781fb18086b5a2b'),
    'closed-record-census.json': (1285, '41588fa2fdef5392b5d9b229f1d4bb8cf81aa7b4a4a4eda71d31777aa42b9870'),
    'closed-transient-lock-races.json': (178, 'deb98b7496a160224675021ae2c31b41785fd86b861df88f516131fadd223a62'),
}
STARTED = None
PHASE = 'inert'

WANTED_PAM=[{'cgroup': '0::/user.slice/user-114316761.slice/user@114316761.service/init.scope', 'cmdline': ['(sd-pam)'], 'comm': '(sd-pam)', 'exe_permission_protected': True, 'pid': 3261267, 'start_ticks': '645211088', 'status': ['Name:\t(sd-pam)', 'State:\tS (sleeping)', 'PPid:\t3261266', 'TracerPid:\t0', 'Uid:\t114316761\t114316761\t114316761\t114316761', 'Gid:\t114316761\t114316761\t114316761\t114316761', 'NSpid:\t3261267']}, {'cgroup': '0::/user.slice/user-114316761.slice/user@114316761.service/init.scope', 'cmdline': ['/usr/lib/systemd/systemd', '--user', '--deserialize=24'], 'comm': 'systemd', 'exe': {'bytes': 100816, 'gid': 0, 'literal': '/usr/lib/systemd/systemd', 'mode': 33261, 'physical': '/usr/lib/systemd/systemd', 'sha256': '9a813714ffd4dadb692afe44384c9c5b334fa323a4ec1dd5157aebdcbbb0667a', 'uid': 0}, 'pid': 3261266, 'start_ticks': '645211085', 'status': ['Name:\tsystemd', 'State:\tS (sleeping)', 'PPid:\t1', 'TracerPid:\t0', 'Uid:\t114316761\t114316761\t114316761\t114316761', 'Gid:\t114316761\t114316761\t114316761\t114316761', 'NSpid:\t3261266']}]


def pam_identity():
 rows=[]
 for template in WANTED_PAM:
  pid=template['pid'];root=Path('/proc')/str(pid);status=(root/'status').read_text();tail=(root/'stat').read_text().rsplit(')',1)[1].split()
  row={'pid':pid,'comm':(root/'comm').read_text().strip(),'start_ticks':tail[19],'cmdline':(root/'cmdline').read_bytes().decode().split(chr(0))[:-1],'status':[l for l in status.splitlines()if l.startswith(('Name:','State:','PPid:','TracerPid:','Uid:','Gid:','NSpid:'))],'cgroup':(root/'cgroup').read_text().strip()}
  try:
   exe=os.readlink(root/'exe');path=Path(exe);s=path.stat();row['exe']={'literal':exe,'physical':str(path.resolve()),'bytes':s.st_size,'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  except PermissionError:row['exe_permission_protected']=True
  rows.append(row)
 if rows!=WANTED_PAM:raise ValueError('exact admitted PAM/parent identity changed')
 return {'pid':3261267,'parent':3261266,'identity_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'permission_protected_exe_cwd_fds_inherited_OS_PAM_TCB':True}



def need(condition, message):
    if not condition:
        raise ValueError(message)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(compact(value)).hexdigest()


def stable(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid,
            st.st_gid, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def physical_dir(path):
    need(path.is_absolute() and path.resolve(strict=True) == path
         and stat.S_ISDIR(path.lstat().st_mode), 'physical directory required')


def file_pin(path, cap=FILE_CAP, *, blob=False):
    """No-follow streaming physical bytes and stable identity, never source text."""
    physical_dir(path.parent)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= cap,
         'bounded regular physical file required')
    h = hashlib.sha256()
    g = hashlib.sha1(b'blob '+str(before.st_size).encode()+b'\0') if blob else None
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    size = 0
    try:
        need(stable(os.fstat(fd)) == stable(before), 'physical open identity changed')
        while True:
            block = os.read(fd, 1024**2)
            if not block:
                break
            size += len(block)
            need(size <= cap, 'file grew beyond bound')
            h.update(block)
            if g is not None:
                g.update(block)
        need(stable(os.fstat(fd)) == stable(before) and size == before.st_size,
             'file changed during hashing')
    finally:
        os.close(fd)
    need(stable(path.lstat()) == stable(before), 'file replaced after hashing')
    row = {'path': str(path), 'bytes': size, 'sha256': h.hexdigest(), 'identity': list(stable(before))}
    if g is not None:
        row['git_blob'] = g.hexdigest()
    return row


def git(root, *arguments, timeout=30):
    command = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
               '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
               '-c', 'core.preloadIndex=false', '-c', 'index.threads=1',
               '-c', 'core.untrackedCache=false', '-c', 'core.fileMode=true',
               '-c', 'core.ignoreStat=false', '-C', str(root), *arguments]
    env = {'HOME': '/nonexistent', 'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0'}
    done = subprocess.run(command, env=env, capture_output=True, timeout=timeout)
    need(len(done.stdout) <= GIT_CAP and len(done.stderr) <= 65536, 'Git metadata output cap')
    need(done.returncode == 0, 'exact Git operation refused: '+arguments[0])
    return done.stdout


def clean_source():
    physical_dir(SOURCE)
    need(git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == COMMIT and
         git(SOURCE, 'rev-parse', 'HEAD^{tree}').decode().strip() == TREE and
         git(SOURCE, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip() == 'HEAD',
         'exact detached source/commit/tree required')
    need(not git(SOURCE, 'status', '--porcelain', '--untracked-files=all', '--ignored')
         and not git(SOURCE, 'submodule', 'status'), 'modified/untracked/ignored/submodule state refuses')
    need(Path(git(SOURCE, 'rev-parse', '--git-common-dir').decode().strip()).resolve(strict=True)
         == PRIMARY/'.git', 'source must be this primary managed worktree')
    return file_pin(SOURCE/'.git', 4096)


def parse_tracked(data):
    rows = []
    for part in data.split(b'\0'):
        if not part:
            continue
        meta, raw = part.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        name = raw.decode()
        p = Path(name)
        need(mode in ('100644', '100755', '120000') and kind == 'blob' and
             not p.is_absolute() and '..' not in p.parts and
             not any(ord(c) < 32 for c in name), 'unexpected tracked Git entry')
        rows.append({'relative': name, 'mode': mode, 'oid': oid})
    need(len(rows) == EXPECTED_FILES and len({r['relative'] for r in rows}) == len(rows),
         'exact tracked source membership required')
    need({r['relative'] for r in rows if r['mode'] == '120000'} == set(LINKS),
         'exact two unlink-only tracked aliases required')
    return rows


def source_manifest():
    rows = parse_tracked(git(SOURCE, 'ls-tree', '-r', '-z', COMMIT))
    expected_names = {r['relative'] for r in rows} | {'.git'}
    allowed_dirs = {str(p) for r in rows for p in Path(r['relative']).parents if str(p) != '.'}
    actual = set()
    pending = [SOURCE]
    directories = 0
    while pending:
        root = pending.pop()
        physical_dir(root)
        with os.scandir(root) as stream:
            children = list(stream)
        for item in children:
            p = Path(item.path); rel = str(p.relative_to(SOURCE)); st = p.lstat()
            if stat.S_ISDIR(st.st_mode):
                need(rel in allowed_dirs, 'untracked physical directory refuses')
                directories += 1; pending.append(p)
            else:
                need(rel in expected_names and rel not in actual, 'untracked physical source entry refuses')
                actual.add(rel)
            need(len(actual)+directories <= ENTRY_CAP, 'finite source entry census cap')
    need(actual == expected_names, 'complete physical tracked membership required')
    manifest = hashlib.sha256(); total = 0; aliases = []
    for row in rows:
        p = SOURCE/row['relative']
        if row['mode'] == '120000':
            st = p.lstat()
            need(stat.S_ISLNK(st.st_mode) and os.readlink(p) == LINKS[row['relative']],
                 'unlink-only alias literal differs')
            payload = os.readlink(p).encode()
            oid = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
            item = {**row, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                    'literal_target': os.readlink(p), 'target_traversed': False,
                    'operation': 'ordinary Git unlinks this entry only'}
            aliases.append(item)
        else:
            result = file_pin(p, blob=True)
            need(bool(p.lstat().st_mode & 0o111) == (row['mode'] == '100755'),
                 'tracked executable mode differs')
            oid = result['git_blob']
            item = {**row, 'bytes': result['bytes'], 'sha256': result['sha256']}
        need(oid == row['oid'], 'physical content differs from exact Git blob')
        total += item['bytes']; manifest.update(compact(item)+b'\n')
    need(total == EXPECTED_BYTES, 'exact tracked physical byte extent differs')
    return {'files': len(rows), 'directories': directories, 'bytes': total,
            'physical_manifest_sha256': manifest.hexdigest(), 'unlink_only_aliases': aliases,
            'external_alias_targets_read_or_followed': False}


def retained_raws():
    physical_dir(RAW_PARENT)
    roots = []
    for p in RAW_PARENT.iterdir():
        if '1433b8f5' in p.name:
            physical_dir(p); roots.append(p)
    need(set(MIN_RAWS) <= {p.name for p in roots} and len(roots) <= 8,
         'all known original1433 raw roots must be retained')
    return sorted(roots)


def original_settlement():
    root = RAW_PARENT/MIN_RAWS[1]
    metadata = {}
    for name, (size, wanted) in SETTLED_PINS.items():
        path = root/name; before = file_pin(path, 65536)
        need(before['bytes'] == size and before['sha256'] == wanted, 'original G619 metadata pin changed')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            need(list(stable(os.fstat(fd))) == before['identity'], 'settled metadata open changed')
            raw = os.read(fd, 65537)
            need(len(raw) == size and hashlib.sha256(raw).hexdigest() == wanted and
                 list(stable(os.fstat(fd))) == before['identity'], 'settled metadata bytes changed')
        finally:
            os.close(fd)
        need(file_pin(path, 65536) == before, 'settled metadata identity changed after read')
        metadata[name] = json.loads(raw)
    lane = metadata['lane.json']['socket_lane']
    need(lane['lease_generation'] == 619 and lane['node'] == 0 and lane['exit_code'] == 0 and
         lane['ended_utc'] == '2026-10-16T21:28:57Z', 'exact settled G619 required')
    for name in ('resources.json', 'outer-resources.json'):
        r = metadata[name]
        need(r['exit_code'] == 0 and not r['timed_out'] and not r['out_of_memory'],
             'original source workflow whole guards not complete')
    return {'generation': 619, 'ended_utc': lane['ended_utc'], 'exact_metadata_pins': SETTLED_PINS}


def worktree_registration():
    rows = {}
    for record in git(PRIMARY, 'worktree', 'list', '--porcelain', '-z').split(b'\0\0'):
        values = [value.decode() for value in record.split(b'\0') if value]
        if not values:
            continue
        need(values[0].startswith('worktree '), 'unexpected worktree metadata')
        path = values[0][9:]
        need(path not in rows, 'duplicate worktree registration')
        rows[path] = values[1:]
    need(len(rows) <= 64, 'finite worktree registration census')
    return rows


def raw_manifest(roots):
    result = []
    for selected in roots:
        physical_dir(selected)
        pending = [selected]; rows = []; total = 0
        while pending:
            root = pending.pop(); physical_dir(root)
            with os.scandir(root) as stream:
                children = list(stream)
            for item in children:
                p = Path(item.path); st = p.lstat(); rel = str(p.relative_to(selected))
                if stat.S_ISDIR(st.st_mode):
                    pending.append(p); row = {'relative': rel, 'kind': 'directory', 'identity': list(stable(st))}
                elif stat.S_ISREG(st.st_mode):
                    row = {'relative': rel, 'kind': 'regular', **file_pin(p)}; total += st.st_size
                else:
                    need(stat.S_ISLNK(st.st_mode), 'raw special entries refuse retirement')
                    row = {'relative': rel, 'kind': 'symlink', 'literal_target': os.readlink(p),
                           'identity': list(stable(st)), 'target_traversed': False}
                rows.append(row)
                need(len(rows) <= ENTRY_CAP and total <= RAW_BYTES_CAP, 'bounded raw retention census')
        rows.sort(key=lambda r: Path(r['relative']).parts)
        result.append({'root': str(selected), 'entries': len(rows), 'bytes': total,
                       'manifest_sha256': digest(rows)})
    return result


def proc_bytes(path, cap=1024**2):
    with path.open('rb') as stream:
        value = stream.read(cap+1)
    need(len(value) <= cap, 'bounded process metadata required')
    return value


def transport_identity():
    rows = []; current = os.getpid()
    for _ in range(6):
        p = Path('/proc')/str(current)
        fields = dict(line.split(':', 1) for line in proc_bytes(p/'status').decode().splitlines() if ':' in line)
        tail = proc_bytes(p/'stat').decode().rsplit(')', 1)[1].split()
        row = {'pid': current, 'parent': int(fields['PPid']), 'comm': proc_bytes(p/'comm').decode().strip(),
               'start_ticks': tail[19], 'uids': fields['Uid'].split(),
               'argv': proc_bytes(p/'cmdline').decode().split(chr(0))[:-1]}
        rows.append(row)
        if row['parent'] == 0:
            break
        current = row['parent']
    validate_transport_rows(rows, os.getuid())
    binary = file_pin(Path('/usr/sbin/sshd'), 2*1024**2)
    need(binary['sha256'] == SSH_BINARY_SHA and binary['bytes'] == SSH_BINARY_BYTES and
         binary['identity'][4] == 0, 'exact root SSH daemon bytes required')
    return {'chain': rows, 'daemon_binary': binary,
            'allowed_unreadable_current_transport_pid': rows[2]['pid']}


def validate_transport_rows(rows, uid):
    need(len(rows) == 6 and len({r['pid'] for r in rows}) == 6,
         'complete current SSH ancestry required')
    need(all(rows[i]['parent'] == rows[i+1]['pid'] and
             int(rows[i]['start_ticks']) >= int(rows[i+1]['start_ticks']) for i in range(5)),
         'current SSH parent/birth chain differs')
    need(rows[0]['comm'] == 'python3' and rows[0]['argv'] ==
         ['/usr/bin/python3', '-I', '-B', '-', '--retire-reviewed-1433'], 'exact retirement interpreter required')
    need(rows[1]['comm'] == 'timeout' and rows[1]['argv'] ==
         ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '300s',
          '/usr/bin/python3', '-I', '-B', '-', '--retire-reviewed-1433'], 'exact outer300second guard required')
    need(rows[2]['comm'] == 'sshd' and rows[2]['argv'] == ['sshd: yanruj@notty', '', ''] and
         all(r['uids'] == [str(uid)]*4 for r in rows[:3]), 'exact current own-UID SSH ancestry required')
    need(rows[3]['comm'] == 'sshd' and rows[3]['argv'] == ['sshd: yanruj [priv]', ''] and
         rows[3]['uids'] == ['0']*4 and rows[4]['uids'] == ['0']*4 and
         rows[4]['comm'] == 'sshd' and len(rows[4]['argv']) == 1 and
         rows[4]['argv'][0].startswith('sshd: /usr/sbin/sshd -D [listener] '), 'exact root SSH parent/listener required')
    need(rows[5]['pid'] == 1 and rows[5]['parent'] == 0 and rows[5]['comm'] == 'systemd' and
         rows[5]['uids'] == ['0']*4 and rows[5]['argv'][0] == '/usr/lib/systemd/systemd',
         'root init ancestry required')


def reference_matches(command, environment, links, needles):
    # Only match metadata is exported; environ/command payloads never leave host.
    return sorted({n for n in needles if n.encode() in command or n.encode() in environment
                   or any(n in value for value in links)})


def reader_scan(needles, transport):
    rounds = []
    for _ in range(3):
        matches = []; unreadable = []; vanished = 0; checked = 0; descriptors = 0; helpers = []
        for p in sorted(Path('/proc').iterdir(), key=lambda p: p.name):
            if not p.name.isdecimal() or int(p.name) == os.getpid():
                continue
            try:
                if p.stat().st_uid != os.getuid():
                    continue
                checked += 1; need(checked <= 4096, 'finite own-UID process cap')
                before = proc_bytes(p/'stat').decode().rsplit(')', 1)[1].split()[19]
                command = proc_bytes(p/'cmdline'); environment = proc_bytes(p/'environ')
                links = [os.readlink(p/name) for name in ('cwd', 'exe')]
                fds = list((p/'fd').iterdir()); need(len(fds) <= 2048, 'per-process descriptor cap')
                for fd in fds:
                    descriptors += 1; need(descriptors <= 32768, 'aggregate descriptor cap')
                    links.append(os.readlink(fd))
                need(proc_bytes(p/'stat').decode().rsplit(')', 1)[1].split()[19] == before,
                     'process identity changed during reader scan')
                found = reference_matches(command, environment, links, needles)
                if found:
                    matches.append({'pid': int(p.name), 'selected_root_matches': found})
            except FileNotFoundError:
                vanished += 1
            except PermissionError:
                if p.name == '3261267':
                    helpers.append(pam_identity())
                elif int(p.name) == transport['allowed_unreadable_current_transport_pid']:
                    current = transport_identity()
                    need(current == transport, 'current SSH ancestry/birth identity changed')
                    helpers.append({'current_query_SSH_identity_sha256': digest(current)})
                else:
                    unreadable.append(int(p.name))
        snapshot = {'own_processes': checked, 'descriptor_links': descriptors, 'vanished': vanished,
                    'selected_readers': matches, 'unreadable_own_processes': unreadable,
                    'exact_OS_PAM_and_current_SSH_exceptions': helpers}
        rounds.append(snapshot)
        if not vanished:
            break
    if snapshot['selected_readers'] or snapshot['unreadable_own_processes'] or snapshot['vanished']:
        raise ValueError('active/unreadable readers or unresolved races: '+compact({
            'selected_readers': snapshot['selected_readers'][:8],
            'unreadable_own_processes': snapshot['unreadable_own_processes'][:16],
            'vanished': snapshot['vanished']}).decode())
    return rounds


def protected_snapshot():
    result = []
    for root in (PRIMARY, *PROTECTED):
        physical_dir(root)
        result.append({'root': str(root), 'physical_root_identity': list(stable(root.lstat())),
                       'HEAD': git(root, 'rev-parse', 'HEAD').decode().strip(),
                       'branch': git(root, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip(),
                       'status_sha256': hashlib.sha256(git(root, 'status', '--porcelain', '--untracked-files=all', '--ignored')).hexdigest()})
    return result


def main():
    global STARTED, PHASE
    need(sys.argv[1:] == ['--retire-reviewed-1433'], 'root-admitted explicit retirement mode required')
    need(sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,
         'isolated nonoptimized no-bytecode metadata interpreter required')
    STARTED = time.monotonic(); signal.alarm(290); PHASE = 'read_only_preflight'
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    physical_dir(PRIMARY)
    need(git(PRIMARY, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip() == 'yanrujhou_main',
         'primary must remain on the approved main branch')
    selected_git = clean_source()
    git(PRIMARY, 'merge-base', '--is-ancestor', COMMIT, 'origin/yanrujhou_main')
    origin = git(PRIMARY, 'rev-parse', 'origin/yanrujhou_main').decode().strip()
    disk = os.statvfs('/data1'); disk_before = disk.f_bavail*disk.f_frsize
    before_protected = protected_snapshot(); registrations = worktree_registration()
    need(str(SOURCE) in registrations and 'HEAD '+COMMIT in registrations[str(SOURCE)] and
         'detached' in registrations[str(SOURCE)], 'selected registered detached worktree required')
    lock = PRIMARY/'swdb-project/records/.retention.lock'; lock_before = file_pin(lock, 1024**2)
    roots = retained_raws(); settled = original_settlement(); transport = transport_identity()
    needles = tuple(str(p) for p in (SOURCE, *roots))
    scans_before = reader_scan(needles, transport)
    raw_before = raw_manifest(roots)
    source = source_manifest()
    clean_source(); scans_final = reader_scan(needles, transport)
    need(protected_snapshot() == before_protected and file_pin(lock, 1024**2) == lock_before,
         'protected sources or primary retention lock changed before retirement')
    need(time.monotonic()-STARTED < 220, 'at least70seconds of whole guard must remain before mutation')
    # Create exactly one durable recovery ref with absent-ref CAS; an existing
    # exact recovery is reusable. No remote ref, branch or source is changed.
    PHASE = 'durable_recovery_ref'
    found = git(PRIMARY, 'for-each-ref', '--format=%(refname)%00%(objectname)', RECOVERY).decode().splitlines()
    need(found in ([], [RECOVERY+'\0'+COMMIT]), 'recovery ref or matching descendant already differs')
    if not found:
        git(PRIMARY, 'update-ref', RECOVERY, COMMIT, '0'*40)
    need(git(PRIMARY, 'rev-parse', RECOVERY).decode().strip() == COMMIT, 'durable recovery ref required')
    # Only Git removes its clean registered detached checkout, never force,
    # shutil.rmtree, external target traversal or raw evidence mutation.
    PHASE = 'ordinary_worktree_remove_requested'
    git(PRIMARY, 'worktree', 'remove', str(SOURCE), timeout=60)
    need(not os.path.lexists(SOURCE), 'source worktree did not retire')
    PHASE = 'source_removed_postflight'
    need(worktree_registration() == {p: row for p, row in registrations.items() if p != str(SOURCE)},
         'only selected worktree registration may change')
    need(retained_raws() == roots and raw_manifest(roots) == raw_before,
         'all original raw physical contents and membership must remain exact')
    need(file_pin(lock, 1024**2) == lock_before and protected_snapshot() == before_protected,
         'primary retention lock and required sources must remain exact')
    need(git(PRIMARY, 'rev-parse', RECOVERY).decode().strip() == COMMIT,
         'recovery ref changed after retirement')
    need(git(PRIMARY, 'rev-parse', 'origin/yanrujhou_main').decode().strip() == origin,
         'retained remote main changed during retirement')
    disk = os.statvfs('/data1'); disk_after = disk.f_bavail*disk.f_frsize
    result = {'date': '2026-10-16 ET', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'classification': 'EXACT_CLEAN_DETACHED1433_SOURCE_RETIRED_ALL_RAW_RETAINED',
              'retired_source': str(SOURCE), 'commit': COMMIT, 'tree': TREE,
              'source_manifest': source, 'original_git_registration': selected_git,
              'completed_original_workflow': settled,
              'recovery_ref': RECOVERY, 'recovery_commit': COMMIT,
              'retained_remote_main': origin, 'disk_before_bytes': disk_before, 'disk_after_bytes': disk_after,
              'restore_argv': ['/usr/bin/git', '-C', str(PRIMARY), 'worktree', 'add', '--detach', str(SOURCE), RECOVERY],
              'raw_retention': raw_before, 'raw_pre_post_equal': True,
              'protected_sources': before_protected, 'primary_retention_lock': lock_before,
              'process_scans_before': scans_before, 'process_scans_immediately_before_removal': scans_final,
              'current_SSH_transport_identity': transport, 'elapsed_seconds': time.monotonic()-STARTED,
              'scope': 'Recovery ref and ordinary nonforced source worktree removal only. Two tracked aliases unlinked by Git; their external targets never read, followed or removed. Original raw and other sources preserved. Exact OS/PAM/current SSH exceptions, own-UID cmdline/environment/cwd/exe/fd scan only; no universal kernel/helper visibility or atomic future-reader exclusion claim.',
              'compiler_native_verifier_solver_project_execution': False}
    encoded = compact(result)+b'\n'; need(len(encoded) <= 65536, 'bounded retirement receipt')
    sys.stdout.buffer.write(encoded)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        sys.stdout.buffer.write(compact({'classification': 'REFUSED_EXACT1433_RETIREMENT',
            'error_type': type(error).__name__, 'reason': str(error)[:2048],
            'phase': PHASE,
            'recovery_ref_if_created': RECOVERY, 'commit': COMMIT,
            'raw_evidence_never_mutated_by_controller': True})+b'\n')
        raise SystemExit(1)
