"""2026-10-09: exact disposable-output cleanup; never an index/recovery guard.

Preflight writes hashes and metadata on the output disk. Apply requires that
receipt, rehashes everything, and checks current targeted process observations.
Unreadable unrelated process metadata is reported as a limitation. This does
not assert whole-host quiescence or supply scientific/recovery clearance.
"""
import argparse
import datetime
import hashlib
import json
import os
import stat
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path('/data1/yanruj/EvolveSWDB_runs')
RAW = Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
TREES = [ROOT / n / 'tests' for n in ('provider-linux-20260930-a12', 'provider-linux-20260929-a6')]
CACHES = [RAW / 'campaign-runs/extensa' / f'extensa-gem5-bfs-20261006-p{i}' / 'site-finder.sqlite' for i in range(1, 5)]
TARGETS = TREES + CACHES
RECORD = Path('/data/yanruj/EvolveSWDB_runs/disposable-cleanup-20261009-a1')
UID = os.getuid()
FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
RECORD_FD = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode() + b'\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def stable_read(path, capture=False):
    fd = os.open(path, FLAGS)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode) and before.st_uid == UID and before.st_nlink == 1
        assert not capture or before.st_size <= 1000000
        sha = hashlib.sha256()
        chunks = []
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            sha.update(block)
            if capture:
                chunks.append(block)
        assert pin(before) == pin(os.fstat(fd)) == pin(os.lstat(path))
        result = {'stat': pin(before), 'bytes': before.st_size, 'allocated': before.st_blocks * 512,
                  'sha256': sha.hexdigest()}
        return (result, b''.join(chunks)) if capture else result
    finally:
        os.close(fd)


def ancestry(path):
    # Selected paths must have their literal, owned, non-symlink parents.
    for p in [path.parent, *path.parents[:-1]]:
        s = os.lstat(p)
        assert stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode)
    assert path.parent.resolve() == path.parent


def parent_pins(path):
    return {str(p): pin(os.lstat(p)) for p in [Path('/'), *reversed(path.parent.parents[:-1]), path.parent]}


def anchored_parent(path, pins, full_parent=True):
    fd = os.open('/', FLAGS | os.O_DIRECTORY)
    try:
        assert pin(os.fstat(fd))[:5] == pins['/'][:5]
        current = Path('/')
        for part in path.parent.parts[1:]:
            current /= part
            nxt = os.open(part, FLAGS | os.O_DIRECTORY, dir_fd=fd)
            try:
                assert pin(os.fstat(nxt))[:5] == pins[str(current)][:5]
            except BaseException:
                os.close(nxt)
                raise
            os.close(fd); fd = nxt
        assert pin(os.fstat(fd))[:(9 if full_parent else 5)] == pins[str(path.parent)][: (9 if full_parent else 5)]
        return fd
    except BaseException:
        os.close(fd)
        raise


def inventory(path):
    ancestry(path)
    if path in CACHES:
        # A sidecar or unfinished builder needs separate interpretation.
        assert sorted(n for n in os.listdir(path.parent) if n.startswith(('site-finder.sqlite', '.site-finder.sqlite.'))) == ['site-finder.sqlite']
    rows = []
    def visit(p):
        assert len(rows) < 120000
        st = os.lstat(p)
        assert st.st_uid == UID and st.st_dev == os.lstat(path).st_dev
        row = {'relative': str(p.relative_to(path)) if p != path else '.', 'stat': pin(st),
               'allocated': st.st_blocks * 512}
        if stat.S_ISREG(st.st_mode):
            row.update(stable_read(p)); row['kind'] = 'file'
        elif stat.S_ISLNK(st.st_mode):
            row['kind'] = 'symlink'; row['link'] = os.readlink(p)
            assert pin(st) == pin(os.lstat(p))
        else:
            assert stat.S_ISDIR(st.st_mode)
            row['kind'] = 'directory'
        rows.append(row)
        if row['kind'] == 'directory':
            names = sorted(os.listdir(p))
            assert '.git' not in names
            for name in names:
                visit(p / name)
            assert names == sorted(os.listdir(p)) and pin(st) == pin(os.lstat(p))
    visit(path)
    return rows


def producer(path):
    parent = path.parent
    keep = {}
    bodies = {}
    for name in ('ended.txt', 'exit.txt', 'pytest.xml', 'pytest.log', 'driver.log', 'checkout.txt', 'retained-reaudit.json'):
        if name in ('ended.txt', 'exit.txt', 'pytest.xml'):
            keep[name], bodies[name] = stable_read(parent / name, capture=True)
        else:
            keep[name] = stable_read(parent / name)
    suites = list(ET.fromstring(bodies['pytest.xml']).iter('testsuite'))
    assert suites and all(n.attrib.get('failures') == '0' and n.attrib.get('errors') == '0' for n in suites)
    assert bodies['ended.txt'].strip() and keep['ended.txt']['stat'][7] / 1e9 < time.time() - 7 * 86400
    assert bodies['exit.txt'].decode().startswith('tests=0 ')
    return {'preserved': keep, 'tests': sum(int(n.attrib['tests']) for n in suites),
            'test_failures': 0, 'test_errors': 0,
            'exit_text': bodies['exit.txt'].decode().strip()}


def targeted_scan(rows_by_path):
    scan_paths = TREES + [p.parent for p in CACHES]
    needles = [os.fsencode(str(p)) for p in scan_paths]
    identities = {(r['stat'][0], r['stat'][1]) for rows in rows_by_path.values() for r in rows}
    matches = []
    limitations = []
    owned = 0
    identities_observed = {}
    def process_identity(p):
        a = os.lstat(p)
        data = (p / 'stat').read_bytes()
        tail = data[data.rindex(b')') + 2:].split()
        assert a.st_uid == UID and int(data.split(b' ', 1)[0]) == int(p.name)
        start = int(tail[19]); assert start > 0
        return [a.st_dev, a.st_ino, a.st_uid, start, tail[0].decode('ascii')]
    # Only the actual current SSH/timeout transport ancestry is excluded. These
    # identities come from the running process, not a user PID/name allowlist.
    transport = {}
    ancestor = os.getpid()
    for _ in range(16):
        p = Path('/proc') / str(ancestor)
        if os.lstat(p).st_uid != UID:
            break
        ident = process_identity(p)
        data = (p / 'stat').read_bytes()
        tail = data[data.rindex(b')') + 2:].split()
        parent = int(tail[1])
        assert ident == process_identity(p) and parent > 0 and parent != ancestor
        transport[str(ancestor)] = ident
        ancestor = parent
    else:
        raise RuntimeError('transport ancestry exceeded bound')
    for name in sorted(os.listdir('/proc')):
        if not name.isdecimal():
            continue
        if name in transport:
            continue
        p = Path('/proc') / name
        try:
            if os.lstat(p).st_uid != UID:
                continue
        except FileNotFoundError:
            continue
        before = process_identity(p)
        identities_observed[name] = before
        owned += 1
        for leaf in ('cmdline', 'maps'):
            try:
                with open(p / leaf, 'rb') as f:
                    data = f.read(8 * 1024 * 1024 + 1)
                if len(data) > 8 * 1024 * 1024:
                    raise RuntimeError('process metadata exceeded bound')
                if any(n in data for n in needles):
                    matches.append({'pid': name, 'route': leaf})
            except OSError as e:
                limitations.append({'pid': name, 'leaf': leaf, 'errno': e.errno})
        for leaf in ('cwd', 'root', 'exe', 'fd'):
            routes = [p / leaf]
            if leaf == 'fd':
                try:
                    routes = [p / leaf / n for n in os.listdir(p / leaf)]
                except OSError as e:
                    limitations.append({'pid': name, 'leaf': leaf, 'errno': e.errno})
                    continue
            for route in routes:
                try:
                    link = os.readlink(route)
                    st = os.stat(route)
                    if any(str(t) == link or link.startswith(str(t) + '/') for t in scan_paths) or (st.st_dev, st.st_ino) in identities:
                        matches.append({'pid': name, 'route': str(route.relative_to(p))})
                except OSError as e:
                    limitations.append({'pid': name, 'leaf': str(route.relative_to(p)), 'errno': e.errno})
        assert before == process_identity(p)
    return {'checked_utc': now(), 'owned_processes_observed': owned, 'matches': matches,
            'limitations': limitations, 'identities': identities_observed, 'whole_host_no_use_proven': False,
            'excluded_current_transport_identities': transport,
            'scope': 'completed disposable test fixtures and rebuildable caches only'}


def save_new(name, data):
    assert '/' not in name and RECORD_FD is not None
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=RECORD_FD)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
    finally:
        os.close(fd)


def brief(manifest, phase):
    return {'format': 'swdb.disposable-cleanup.v1', 'phase': phase, 'checked_utc': now(),
            'record_directory': str(RECORD), 'targets': [
                {'path': p, 'entries': len(rows), 'regular_bytes': sum(r.get('bytes', 0) for r in rows),
                 'allocated_bytes': sum(r['allocated'] for r in rows), 'inventory_sha256': digest(packed(rows)),
                 **({'sha256': rows[0]['sha256']} if len(rows) == 1 else {})}
                for p, rows in manifest['rows'].items()], 'producer_results': manifest['producers'],
            'scans': manifest['scans'], 'immutable_index_and_recovery_guards_changed': False}


def unlink_anchored(path, rows, pins):
    expected = {r['relative']: r for r in rows}
    parent_fd = anchored_parent(path, pins)
    try:
        def remove_at(fd, name, relative):
            row = expected[relative]
            st = os.stat(name, dir_fd=fd, follow_symlinks=False)
            assert pin(st) == row['stat']
            if row['kind'] != 'directory':
                os.unlink(name, dir_fd=fd)
                return
            child = os.open(name, FLAGS | os.O_DIRECTORY, dir_fd=fd)
            try:
                assert pin(os.fstat(child)) == row['stat']
                names = sorted(os.listdir(child))
                prefix = '' if relative == '.' else relative + '/'
                expected_names = sorted(k[len(prefix):] for k in expected if k.startswith(prefix) and k != relative and '/' not in k[len(prefix):] and k != '.')
                assert names == expected_names
                for n in names:
                    remove_at(child, n, prefix + n)
                assert not os.listdir(child)
            finally:
                os.close(child)
            # Our own child deletions change directory timestamps and nlink.
            end = os.stat(name, dir_fd=fd, follow_symlinks=False)
            assert (end.st_dev, end.st_ino, end.st_mode, end.st_uid, end.st_gid) == tuple(row['stat'][:5])
            os.rmdir(name, dir_fd=fd)
        remove_at(parent_fd, path.name, '.')
    finally:
        os.close(parent_fd)


def main():
    global RECORD_FD
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--observe', action='store_true')
    parser.add_argument('--expected-manifest-sha256')
    parser.add_argument('--expected-limitations-sha256')
    args = parser.parse_args()
    assert not (args.apply and args.observe)
    assert UID == 114316761
    free_before = {p: os.statvfs(p).f_bavail * os.statvfs(p).f_frsize for p in ('/data1', '/data')}
    if not args.apply and not args.observe:
        RECORD.mkdir(mode=0o700)
    ancestry(RECORD / 'manifest.json')
    RECORD_FD = anchored_parent(RECORD / 'manifest.json', parent_pins(RECORD / 'manifest.json'))
    assert os.fstat(RECORD_FD).st_uid == UID and stat.S_IMODE(os.fstat(RECORD_FD).st_mode) == 0o700
    if not args.apply and not args.observe:
        rows = {str(p): inventory(p) for p in TARGETS}
        scans = [targeted_scan(rows), targeted_scan(rows)]
        manifest = {'created_utc': now(), 'created_unix': time.time(), 'rows': rows,
                    'parents': {str(p): parent_pins(p) for p in TARGETS},
                    'producers': {str(p): producer(p) for p in TREES}, 'scans': scans}
        assert not any(s['matches'] for s in scans)
        data = packed(manifest); save_new('manifest.json', data)
        receipt = brief(manifest, 'prepared_not_removed')
        receipt.update({'manifest_bytes': len(data), 'manifest_sha256': digest(data), 'free_bytes': free_before})
        limits = [{'limitations': s['limitations'], 'identities': {p: s['identities'][p] for p in sorted({x['pid'] for x in s['limitations']})}} for s in scans]
        assert limits[0] == limits[1]
        receipt['limitations_review_sha256'] = digest(packed(limits[0]))
        save_new('preflight.json', packed(receipt)); print(packed(receipt).decode(), end='')
        return
    assert args.expected_manifest_sha256
    assert args.observe or args.expected_limitations_sha256
    fd = os.open('manifest.json', FLAGS, dir_fd=RECORD_FD)
    try:
        with os.fdopen(fd, 'rb', closefd=False) as f:
            data = f.read(32000000 + 1)
        assert len(data) <= 32000000
    finally:
        os.close(fd)
    assert digest(data) == args.expected_manifest_sha256
    manifest = json.loads(data)
    assert time.time() - manifest['created_unix'] < 600
    assert {str(p) for p in TARGETS} == set(manifest['rows'])
    if args.observe:
        scans = [targeted_scan(manifest['rows']), targeted_scan(manifest['rows'])]
        assert not any(s['matches'] for s in scans)
        limits = [{'limitations': s['limitations'], 'identities': {p: s['identities'][p] for p in sorted({x['pid'] for x in s['limitations']})}} for s in scans]
        assert limits[0] == limits[1]
        print(packed({'phase': 'fresh_targeted_observation_no_removal', 'manifest_sha256': digest(data),
                      'limitations_review_sha256': digest(packed(limits[0])), 'scans': scans}).decode(), end='')
        return
    fresh = {str(p): inventory(p) for p in TARGETS}
    assert fresh == manifest['rows']
    assert {str(p): producer(p) for p in TREES} == manifest['producers']
    scans = [targeted_scan(fresh), targeted_scan(fresh)]
    assert not any(s['matches'] for s in scans)
    for s in scans:
        limits = {'limitations': s['limitations'], 'identities': {p: s['identities'][p] for p in sorted({x['pid'] for x in s['limitations']})}}
        assert digest(packed(limits)) == args.expected_limitations_sha256
    start = {'checked_utc': now(), 'manifest_sha256': digest(data), 'fresh_scans': scans,
             'authorized_scope': 'user requested disk reclamation of completed disposable output', 'free_bytes_before': free_before}
    save_new('removal-start.json', packed(start))
    removed = []
    for p in TARGETS:
        unlink_anchored(p, fresh[str(p)], manifest['parents'][str(p)])
        assert not os.path.lexists(p)
        removed.append(str(p))
        save_new(f'removed-{len(removed)}.json', packed({'checked_utc': now(), 'removed': str(p),
                 'inventory_sha256': digest(packed(fresh[str(p)]))}))
    assert {str(p): producer(p) for p in TREES} == manifest['producers']
    receipt = brief(manifest, 'removed')
    receipt.update({'removed': removed, 'apply_scans': scans, 'manifest_sha256': digest(data),
                    'free_bytes_before': free_before,
                    'free_bytes_after': {p: os.statvfs(p).f_bavail * os.statvfs(p).f_frsize for p in ('/data1', '/data')},
                    'preserved_producer_receipts_match': True})
    save_new('completion.json', packed(receipt)); print(packed(receipt).decode(), end='')


if __name__ == '__main__':
    main()
