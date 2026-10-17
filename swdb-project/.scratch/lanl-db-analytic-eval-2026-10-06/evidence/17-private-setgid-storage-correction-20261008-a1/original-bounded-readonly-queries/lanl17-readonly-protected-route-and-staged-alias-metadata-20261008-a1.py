#!/usr/bin/env python3
"""One fixed read-only query; original UNSEALED output, no clearance or admission.

Parent must review this exact source and run it only after the observer window.
No selected control is imported, no command is executed, and nothing is written.
Explicit application file reads are confined to the 15 fixed staged aliases.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import signal
import socket
import stat
import sys
import time

BASE = Path('/data1/yanruj')
RAW = Path('/data/yanruj/EvolveSWDB_runs')
UID = 114316761
SECONDS = 120
TOTAL_READ = 2 * 1024 * 1024
FILE_READ = 256 * 1024
MAP_PIN = {'bytes': 17357, 'sha256': '3580d732064ef55e2f75589f8c9e3d4ca0c70ccddb7d450565b93c4c13b8cb7f'}
ALIASES = (
    ('/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py', 38195, '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),
    ('/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py', 8014, 'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'),
    ('/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py', 14577, '9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),
    ('/data1/yanruj/lanl17-custody-source-20261007-a2r1/collector.py', 24818, 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'),
    ('/data1/yanruj/lanl17-custody-source-20261007-a3/auditor.py', 115130, '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'),
    ('/data1/yanruj/lanl17-custody-source-20261007-a3/capture-producer.py', 46165, '32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'),
    ('/data1/yanruj/lanl17-index-source-20261007-a1/writer.py', 33445, '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'),
    ('/data1/yanruj/lanl17-input-author-source-20261007-a1/index_request_author.py', 38266, 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'),
    ('/data1/yanruj/lanl17-input-author-source-20261007-a1/passive_inventory.py', 29653, '76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176'),
    ('/data1/yanruj/lanl17-input-author-source-20261007-a1/publication_author.py', 28419, '791f95b5f53c23740ce8b2bdd72fc8dcd625494a60f5399f30b5ed704347fb1a'),
    ('/data1/yanruj/lanl17-index-privacy-source-20261007-a1/envelope.py', 38790, '1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc'),
    ('/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/outer_capture.py', 34658, '59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544'),
    ('/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/bootstrap.sh', 6549, '0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217'),
    ('/data1/yanruj/lanl17-custody-source-20261007-a3/assembler.py', 33584, 'de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a'),
    ('/data1/yanruj/lanl17-custody-source-20261007-a3/spec-writer.py', 11868, '339ea0dc1abb6778f0f016e9c03f2b29c5f1916154b668f5416747b2768a9231'),
)
PROTECTED = (
    BASE / 'Memacc-repro-20260925',
    BASE / '.codex',
    BASE / '.npm-global',
    BASE / 'DX100-bfs-e4fc4af',
    BASE / 'EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline/source',
    RAW / 'lanl17-prospective-inputs-20261006-a2',
    RAW / 'bfs-dx100-coverage-20260926-a2/bfs-dx100-coverage-20260926-a2/graph/coverage.sg',
)
PROSPECTIVE = tuple(BASE / ('ArchEvolve-lanl17-' + name + '-20261007-a4')
                    for name in ('source', 'freeze-evidence', 'actual-report-evidence')) + tuple(
    RAW / ('lanl17-' + name + '-20261007-a4')
    for name in ('actual-campaigns', 'metadata-prepare', 'metadata-finalize'))
OVERRIDE_NAMES = (
    'SWDB_HOME', 'LACT_LEASE_ROOT', 'PYTHONHOME', 'PYTHONPATH', 'GIT_DIR',
    'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
    'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_INDEX_FILE', 'LD_PRELOAD',
    'LD_LIBRARY_PATH', 'SWDB_CERTIFY_CXX',
)
PATH_PROGRAMS = ('python3', 'git', 'timeout', 'bash', 'tmux', 'numactl',
                 'strace', 'g++-13', 'g++', 'codex')


class Limit(Exception):
    pass


class Refused(Exception):
    pass


class Budget:
    def __init__(self):
        self.start = time.monotonic()
        self.read_bytes = 0

    def check(self):
        if time.monotonic() - self.start >= SECONDS:
            raise Limit('elapsed_limit')

    def debit(self, size):
        self.check()
        self.read_bytes += size
        if self.read_bytes > TOTAL_READ:
            raise Limit('total_read_limit')


def stamp(value):
    return {'device': value.st_dev, 'inode': value.st_ino,
            'mode': oct(stat.S_IMODE(value.st_mode)), 'type_bits': stat.S_IFMT(value.st_mode),
            'uid': value.st_uid, 'gid': value.st_gid, 'links': value.st_nlink,
            'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns}


def problem(error):
    result = {'error_type': type(error).__name__}
    if isinstance(error, OSError):
        result['errno'] = error.errno
    elif isinstance(error, (Limit, Refused)):
        result['reason'] = str(error)
    return result


def component_metadata(path, budget):
    """Bounded lexical component lstat only, including redirect/absence facts."""
    path = Path(os.path.abspath(os.fspath(path)))
    if len(os.fspath(path).encode()) > 4096 or len(path.parts) > 64:
        raise Refused('route_shape_limit')
    rows = []
    current = Path('/')
    for part in path.parts:
        budget.check()
        if part != '/':
            current = current / part
        row = {'path': os.fspath(current)}
        try:
            value = current.lstat()
            row['stat'] = stamp(value)
            row['symlink'] = stat.S_ISLNK(value.st_mode)
        except OSError as error:
            row.update(problem(error))
            row['absent'] = isinstance(error, FileNotFoundError)
            rows.append(row)
            break
        rows.append(row)
        if row['symlink']:
            # Do not lstat deeper lexical components through a redirect.
            break
    return rows


def route_metadata(path, budget, resolve):
    """Resolution is metadata-only; never open a protected route's contents."""
    result = {'path': os.fspath(path), 'components': component_metadata(path, budget)}
    budget.check()
    try:
        result['lexists'] = True
        result['lstat'] = stamp(Path(path).lstat())
    except OSError as error:
        result['lexists'] = False if isinstance(error, FileNotFoundError) else None
        result.update(problem(error))
    if resolve:
        try:
            budget.check()
            physical = Path(path).resolve(strict=True)
            result['physical_resolved_path'] = os.fspath(physical)
            result['physical_stat'] = stamp(physical.stat())
            result['redirected'] = os.fspath(physical) != os.fspath(path)
        except (OSError, RuntimeError) as error:
            result['resolution'] = problem(error)
    return result


def hash_alias(path, expected_size, expected_sha, budget):
    """Pin each ancestor FD and final file FD, refusing symlink traversal."""
    result = {'path': path, 'expected_bytes': expected_size, 'expected_sha256': expected_sha}
    result['route'] = route_metadata(Path(path), budget, True)
    descriptors = []
    ancestor_rows = []
    file_fd = None
    try:
        budget.check()
        p = Path(path)
        if not p.is_absolute() or len(p.parts) > 64 or expected_size > FILE_READ:
            raise Refused('alias_shape_limit')
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        root_fd = os.open('/', flags)
        descriptors.append(root_fd)
        current = Path('/')
        root_before = stamp(os.fstat(root_fd))
        if root_before != stamp(current.lstat()):
            raise Refused('root_identity_changed')
        ancestor_rows.append((current, root_fd, root_before))
        for part in p.parts[1:-1]:
            budget.check()
            current = current / part
            before = current.lstat()
            if not stat.S_ISDIR(before.st_mode):
                raise Refused('ancestor_not_nonsymlink_directory')
            fd = os.open(part, flags, dir_fd=descriptors[-1])
            descriptors.append(fd)
            identity = stamp(os.fstat(fd))
            if identity != stamp(before):
                raise Refused('ancestor_identity_changed')
            ancestor_rows.append((current, fd, identity))
        before = os.stat(p.name, dir_fd=descriptors[-1], follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_uid != UID:
            raise Refused('alias_not_owned_regular_file')
        if before.st_size > FILE_READ:
            raise Refused('alias_file_read_limit')
        file_fd = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                          dir_fd=descriptors[-1])
        identity = stamp(os.fstat(file_fd))
        if identity != stamp(before):
            raise Refused('alias_open_identity_changed')
        result['stat_before'] = identity
        digest = hashlib.sha256()
        size = 0
        # Read exactly the bounded initial size; stat+FD anchors catch changes.
        while size < before.st_size:
            budget.check()
            data = os.read(file_fd, min(65536, before.st_size - size, TOTAL_READ - budget.read_bytes))
            if not data:
                raise Refused('alias_truncated_or_total_read_limit')
            budget.debit(len(data))
            size += len(data)
            digest.update(data)
        after = stamp(os.fstat(file_fd))
        path_after = stamp(os.stat(p.name, dir_fd=descriptors[-1], follow_symlinks=False))
        if after != identity or path_after != identity:
            raise Refused('alias_final_identity_changed')
        for ancestor, fd, prior in ancestor_rows:
            budget.check()
            if stamp(os.fstat(fd)) != prior or stamp(ancestor.lstat()) != prior:
                raise Refused('alias_ancestor_final_identity_changed')
        result.update({'bytes': size, 'sha256': digest.hexdigest(), 'stat_after': after,
                       'matches_original_pin': size == expected_size and digest.hexdigest() == expected_sha,
                       'physical_resolved_path': path, 'read_route_nonsymlink_stable': True})
    except Limit:
        raise
    except (OSError, Refused, RuntimeError) as error:
        result['hash_observation'] = problem(error)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for fd in reversed(descriptors):
            os.close(fd)
    return result


def environment_metadata(budget):
    result = {'override_name_presence': {name: name in os.environ for name in OVERRIDE_NAMES}}
    budget.check()
    try:
        # Public account lookup; neither home value is serialized.
        result['HOME_equals_pwd_home'] = os.environ.get('HOME') == pwd.getpwuid(UID).pw_dir
    except (KeyError, OSError) as error:
        result['home_comparison'] = problem(error)
    result['CODEX_HOME_present'] = 'CODEX_HOME' in os.environ
    result['CODEX_HOME_equals_BASE_dot_codex'] = os.environ.get('CODEX_HOME') == os.fspath(BASE / '.codex')
    result['CODEX_HOME_comparison_policy'] = 'exact_string_equality_only'
    # auth.json existence only; refuse a redirected parent rather than probing it.
    parents = component_metadata(BASE / '.codex', budget)
    if all('stat' in row and not row['symlink'] for row in parents):
        try:
            budget.check()
            (BASE / '.codex/auth.json').lstat()
            result['fixed_BASE_dot_codex_auth_json_lexists'] = True
        except FileNotFoundError:
            result['fixed_BASE_dot_codex_auth_json_lexists'] = False
        except OSError as error:
            result['auth_existence'] = problem(error)
    else:
        result['auth_existence'] = {'reason': 'fixed_parent_absent_redirected_or_inaccessible'}
    return result


def path_routes(budget):
    # Inspect selected program routes without printing PATH or executing anything.
    raw = os.environ.get('PATH', os.defpath)
    result = {'PATH_present': 'PATH' in os.environ, 'program_routes': []}
    if len(raw.encode()) > 16384 or len(raw.split(os.pathsep)) > 64:
        result['PATH_route_observation'] = {'reason': 'PATH_shape_limit'}
        return result
    components = raw.split(os.pathsep)
    result['component_count'] = len(components)
    result['empty_component_present'] = '' in components
    for program in PATH_PROGRAMS:
        budget.check()
        row = {'program': program, 'selected_path': None}
        for directory in components:
            budget.check()
            candidate = Path(directory or '.') / program
            try:
                value = candidate.stat()
                if stat.S_ISREG(value.st_mode) and os.access(candidate, os.X_OK):
                    selected = Path(os.path.abspath(os.fspath(candidate)))
                    row['selected_path'] = os.fspath(selected)
                    row['route'] = route_metadata(selected, budget, True)
                    break
            except OSError:
                continue
        result['program_routes'].append(row)
    return result


def mount_metadata(path, budget):
    result = {'path': path}
    try:
        budget.check()
        before = stamp(Path(path).lstat())
        values = os.statvfs(path)
        budget.check()
        after = stamp(Path(path).lstat())
        result.update({'stat_before': before, 'stat_after': after, 'stat_stable': before == after,
                       'fragment_bytes': values.f_frsize, 'block_bytes': values.f_bsize,
                       'total_bytes': values.f_blocks * values.f_frsize,
                       'free_bytes': values.f_bfree * values.f_frsize,
                       'available_bytes': values.f_bavail * values.f_frsize,
                       'total_inodes': values.f_files, 'free_inodes': values.f_ffree,
                       'available_inodes': values.f_favail, 'filesystem_flags': values.f_flag})
    except OSError as error:
        result.update(problem(error))
    return result


def main():
    budget = Budget()
    result = {'format': 'swdb.lanl17-readonly-protected-route-and-staged-alias-metadata.v1',
              'sealed': False, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'purpose': 'Original passive physical metadata, not source selection, capacity clearance or scientific admission.',
              'alias_map_original_pin': MAP_PIN, 'alias_expected_count': len(ALIASES),
              'alias_expected_total_bytes': sum(row[1] for row in ALIASES),
              'limits': {'elapsed_seconds': SECONDS, 'explicit_file_read_bytes': TOTAL_READ,
                         'per_alias_file_bytes': FILE_READ}, 'aliases': [], 'protected_routes': [],
              'prospective_lexical_routes': [], 'mounts': []}
    def deadline(signum, frame):
        raise Limit('elapsed_alarm')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.alarm(SECONDS)
    try:
        host = socket.gethostname().split('.')[0]
        result['native_account'] = {'platform': sys.platform, 'hostname_short': host,
                                    'uid': os.getuid(), 'effective_uid': os.geteuid(),
                                    'machine': os.uname().machine}
        if sys.platform != 'linux' or host != 'mbit10' or os.getuid() != UID or os.geteuid() != UID or UID == 0:
            raise Refused('native_linux_mbit10_own_nonroot_account_required')
        for path, size, sha in ALIASES:
            result['aliases'].append(hash_alias(path, size, sha, budget))
        for path in PROTECTED:
            result['protected_routes'].append(route_metadata(path, budget, True))
        for path in PROSPECTIVE:
            result['prospective_lexical_routes'].append(route_metadata(path, budget, False))
        result['environment'] = environment_metadata(budget)
        result['PATH_route_metadata'] = path_routes(budget)
        for mount in ('/data1', '/data'):
            result['mounts'].append(mount_metadata(mount, budget))
    except (Limit, Refused, OSError, RuntimeError) as error:
        result['query_interruption_or_refusal'] = problem(error)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        result['explicit_alias_file_bytes_read'] = budget.read_bytes
        result['elapsed_seconds'] = time.monotonic() - budget.start
        result['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sys.stdout.write(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n')
    return 1 if 'query_interruption_or_refusal' in result else 0


if __name__ == '__main__':
    raise SystemExit(main())
