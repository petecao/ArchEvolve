"""NOT RUN: copy two reviewed source blobs; never import or run either control.

Fixed Linux/account/native/root gates and an explicitly delivered primary commit
are required. Fresh literal output only; failure preserves any partial output.
Stdout is compact unsealed source-copy custody, never scientific admission.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import socket
import stat
import subprocess
import sys
import time

UID = 114316761
BASE = Path('/data1/yanruj')
PRIMARY = BASE / 'ArchEvolve'
DESTINATION = BASE / 'lanl14-completed-source-controls-20261008-a1'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
FORBIDDEN = (
    PRIMARY,
    BASE / 'ArchEvolve-lanl-cpu-model-validation-20261006-a1',
    BASE / 'ArchEvolve-lanl-generality-final-20261007-a1',
    BASE / 'ArchEvolve-lanl-generality-final-export-20261007-a1',
    Path('/data/yanruj/EvolveSWDB_runs/lanl-generality-final-20261007-a1'),
    Path('/data/yanruj/EvolveSWDB_runs/lanl14-export-reader-administration-20261007-a1'),
)
SOURCES = (
    {'target': 'export_invocation_r5.py', 'bytes': 35775,
     'sha256': '62808f732d3ca492c102bbeb0b0ccab5fcb6ed2c63efd088d8ccdac845d362b7',
     'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-exact-export-invocation-controls-20261008-a1/lanl14_invoke_reviewed_supervised_export_20261008_a1_r5.py'},
    {'target': 'completed_metadata_supplier_r1.py', 'bytes': 21759,
     'sha256': '0e8ad57fe58f631298502215732a3425ace0264e7348ecea51e6258ebf85f911',
     'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-completed-metadata-pin-supplier-controls-20261008-a1-r1/lanl14_read_completed_metadata_pins_20261008_a1_r1.py'},
)
NATIVE = {
    '/usr/bin/python3.12': (8020928, 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
    '/usr/bin/git': (4019024, '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
}
STABLE = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
          'st_size', 'st_mtime_ns', 'st_ctime_ns')
DIRECTORY_ID = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid')
DEADLINE_S = 90
MAX_FILE = 16 * 1024 * 1024
MAX_READ = 64 * 1024 * 1024
MAX_GIT_OUTPUT = 1024 * 1024
MAX_GIT_TOTAL = 8 * 1024 * 1024
MAX_STDOUT = 64 * 1024


class Refused(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(status, keys=STABLE):
    return {key: getattr(status, key) for key in keys}


def checked(path, owner=UID, directory=False):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(str(path)) <= 4096,
            'canonical_path')
    require(not any(p.is_symlink() for p in (path, *path.parents))
            and path.resolve(strict=True) == path, 'nonsymlink_components')
    status = path.lstat()
    require(status.st_uid == owner and
            (stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode)),
            'owner_type')
    if not directory:
        require(status.st_nlink == 1, 'single_link')
    return path, status


class Budget:
    def __init__(self):
        self.end = time.monotonic() + DEADLINE_S
        self.read = 0
        self.git_bytes = 0

    def remaining(self):
        left = self.end - time.monotonic()
        require(left > 0, 'source_copy_deadline')
        return left

    def consume(self, count):
        self.remaining()
        self.read += count
        require(self.read <= MAX_READ, 'source_read_budget')


def read_exact(path, budget, owner=UID, size=None, digest=None):
    path, before = checked(path, owner=owner)
    require(0 < before.st_size <= MAX_FILE and (size is None or before.st_size == size),
            'file_size')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd)) == stamp(before), 'opened_identity')
        blocks, total = [], 0
        while True:
            budget.remaining()
            block = os.read(fd, min(1024 * 1024, MAX_FILE - total + 1))
            if not block:
                break
            total += len(block)
            budget.consume(len(block))
            require(total <= MAX_FILE, 'returned_file_bound')
            blocks.append(block)
        raw = b''.join(blocks)
        require(total == before.st_size and
                stamp(os.fstat(fd)) == stamp(before) == stamp(path.lstat()), 'stable_file')
    finally:
        os.close(fd)
    require(digest is None or sha(raw) == digest, 'returned_file_sha256')
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw), 'stat': stamp(before)}, raw


def private_base():
    _, status = checked(BASE, directory=True)
    require(stat.S_IMODE(status.st_mode) == 0o700, 'literal_private_base')
    return stamp(status, DIRECTORY_ID)


def native_gate(budget):
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == UID and pwd.getpwuid(UID).pw_name == 'yanruj',
            'native_host_account')
    require(sys.flags.dont_write_bytecode == 1 and sys.flags.optimize == 0
            and Path(sys.executable).resolve(strict=True) == Path('/usr/bin/python3.12'),
            'native_python_B_not_optimized')
    result = {}
    for path, (size, digest) in NATIVE.items():
        pin, raw = read_exact(path, budget, owner=0, size=size, digest=digest)
        require(raw[:6] == b'\x7fELF\x02\x01' and int.from_bytes(raw[18:20], 'little') == 62
                and not pin['stat']['st_mode'] & 0o022 and pin['stat']['st_mode'] & 0o111,
                'root_owned_x86_64_native')
        result[path] = pin
    return result


def git(budget, *tail):
    budget.remaining()
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
           'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0',
           'GIT_PAGER': 'cat', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
    child = subprocess.run(['/usr/bin/git', '-c', 'protocol.allow=never',
                            '-c', 'core.fsmonitor=false', '-C', str(PRIMARY), *tail],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=min(15, budget.remaining()), env=env, check=False)
    require(child.returncode == 0 and not child.stderr
            and len(child.stdout) <= MAX_GIT_OUTPUT, 'readonly_git_refused')
    budget.git_bytes += len(child.stdout)
    require(budget.git_bytes <= MAX_GIT_TOTAL, 'git_metadata_budget')
    return child.stdout


def source_identity(budget, expected):
    base = private_base()
    _, primary_status = checked(PRIMARY, directory=True)
    # Historical literal primary02777 remains private beneath exact owned0700 BASE.
    require(stat.S_IMODE(primary_status.st_mode) in (0o700, 0o755, 0o2777),
            'literal_primary_mode')
    require(git(budget, 'rev-parse', '--show-toplevel').decode().strip() == str(PRIMARY)
            and git(budget, 'rev-parse', 'HEAD').decode().strip() == expected
            and git(budget, 'rev-parse', 'refs/remotes/origin/yanrujhou_main').decode().strip() == expected
            and git(budget, 'branch', '--show-current').decode().strip() == 'yanrujhou_main',
            'explicit_delivered_primary')
    require(not git(budget, 'diff', '--no-ext-diff', '--no-textconv', '--name-only')
            and not git(budget, 'diff', '--no-ext-diff', '--no-textconv', '--cached', '--name-only'), 'tracked_cached_clean')
    c = git(budget, 'ls-tree', '-r', '-z', C, '--', 'swdb-project/swdb')
    current = git(budget, 'ls-tree', '-r', '-z', expected, '--', 'swdb-project/swdb')
    require(current == c, 'frozen_C_source_Git_identity')
    rows = [r for r in c.split(b'\0') if r]
    require(len(rows) == 223 and sum(r.split(b'\t', 1)[1].endswith(b'.py') for r in rows) == 185,
            'frozen_C_source_counts')
    return {'expected_primary': expected, 'HEAD': expected, 'origin_yanrujhou_main': expected,
            'branch': 'yanrujhou_main', 'tracked_cached_clean': True,
            'base_identity': base, 'primary_identity': stamp(primary_status, DIRECTORY_ID),
            'C': C, 'C_source_Git_inventory_sha256': sha(c), 'source_entries': 223,
            'Python_modules': 185, 'F6_inherited_from_exact_C_Python_blobs': F6}


def original_source(budget, expected, spec):
    entry = git(budget, 'ls-tree', '-z', expected, '--', spec['path']).split(b'\0')
    require(len(entry) == 2 and not entry[1], 'single_committed_source')
    meta, name = entry[0].split(b'\t', 1)
    fields = meta.decode().split()
    require(fields[:2] == ['100644', 'blob'] and name.decode() == spec['path'],
            'source_Git_mode_path')
    raw = git(budget, 'cat-file', 'blob', expected + ':' + spec['path'])
    require(len(raw) == spec['bytes'] and sha(raw) == spec['sha256'], 'source_Git_byte_pin')
    require(git(budget, 'ls-files', '--stage', '--', spec['path']).decode().strip().split()
            == ['100644', fields[2], '0', spec['path']], 'source_index_blob')
    pin, physical = read_exact(PRIMARY / spec['path'], budget,
                               size=spec['bytes'], digest=spec['sha256'])
    require(physical == raw, 'source_worktree_equals_committed_blob')
    pin.update({'Git_mode': '100644', 'Git_blob': fields[2], 'Git_path': spec['path']})
    return pin, raw


def alarm(signum, frame):
    raise Refused('global_source_copy_deadline')


def run(args):
    require(re.fullmatch('[0-9a-f]{40}', args.expected_primary) is not None
            and re.fullmatch('[0-9a-f]{64}', args.producer_sha256) is not None,
            'explicit_revision_and_own_source_pin')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, DEADLINE_S)
    budget = Budget()
    native_before = native_gate(budget)
    own_before, own_raw = read_exact(Path(__file__), budget, digest=args.producer_sha256)
    identity_before = source_identity(budget, args.expected_primary)
    require(DESTINATION.parent == BASE and
            all(not DESTINATION.is_relative_to(root) for root in FORBIDDEN), 'fixed_output_exclusions')
    require(not os.path.lexists(DESTINATION), 'fresh_output_only')
    originals = [original_source(budget, args.expected_primary, spec) for spec in SOURCES]
    require(private_base() == identity_before['base_identity'], 'base_before_copy')
    directory_fd = None
    created = []
    previous_umask = os.umask(0o022)
    try:
        # No existing file or mode is changed, even after a partial failure.
        os.mkdir(DESTINATION, 0o700)
        _, ds = checked(DESTINATION, directory=True)
        require(stat.S_IMODE(ds.st_mode) == 0o700, 'fresh_output_0700')
        directory_id = stamp(ds, DIRECTORY_ID)
        directory_fd = os.open(DESTINATION, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        require(stamp(os.fstat(directory_fd), DIRECTORY_ID) == directory_id, 'output_directory_FD')
        for spec, (_, raw) in zip(SOURCES, originals):
            budget.remaining()
            require(stamp(DESTINATION.lstat(), DIRECTORY_ID) == directory_id
                    and private_base() == identity_before['base_identity'], 'directory_before_write')
            fd = os.open(spec['target'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o644, dir_fd=directory_fd)
            try:
                status = os.fstat(fd)
                require(stat.S_ISREG(status.st_mode) and status.st_uid == UID and status.st_nlink == 1
                        and stat.S_IMODE(status.st_mode) == 0o644, 'new_file_0644')
                remaining = memoryview(raw)
                while remaining:
                    budget.remaining()
                    count = os.write(fd, remaining)
                    require(count > 0, 'exclusive_write_progress')
                    remaining = remaining[count:]
                os.fsync(fd)
            finally:
                os.close(fd)
            created.append(spec['target'])
        os.fsync(directory_fd)
    finally:
        os.umask(previous_umask)
        if directory_fd is not None:
            os.close(directory_fd)
    require(set(os.listdir(DESTINATION)) == {s['target'] for s in SOURCES}, 'exact_two_outputs')
    copied = []
    for spec, (_, raw) in zip(SOURCES, originals):
        pin, body = read_exact(DESTINATION / spec['target'], budget,
                               size=spec['bytes'], digest=spec['sha256'])
        require(body == raw and stat.S_IMODE(pin['stat']['st_mode']) == 0o644, 'copied_source_exact')
        copied.append(pin)
    identity_after = source_identity(budget, args.expected_primary)
    require(identity_after == identity_before, 'source_identity_before_after')
    require(native_gate(budget) == native_before, 'native_before_after')
    for spec, (pin, raw), copied_pin in zip(SOURCES, originals, copied):
        require(original_source(budget, args.expected_primary, spec) == (pin, raw), 'original_before_after')
        current, body = read_exact(DESTINATION / spec['target'], budget,
                                   size=spec['bytes'], digest=spec['sha256'])
        require(current == copied_pin and body == raw, 'copied_stat_body_before_after')
    require(read_exact(Path(__file__), budget, digest=args.producer_sha256) == (own_before, own_raw),
            'own_source_before_after')
    require(private_base() == identity_before['base_identity']
            and stamp(checked(DESTINATION, directory=True)[1], DIRECTORY_ID) == directory_id
            and set(os.listdir(DESTINATION)) == {s['target'] for s in SOURCES}, 'final_private_exact_outputs')
    budget.remaining()
    return {'format': 'swdb.lanl14-completed-source-controls-copy.v1',
            'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'host': 'mbit10', 'uid': UID, 'user': 'yanruj', 'state': 'two_sources_copied',
            'original_receipt_policy': 'UNSEALED', 'source_identity_before': identity_before,
            'source_identity_after': identity_after, 'native_before_after': native_before,
            'producer_pin': own_before, 'destination': str(DESTINATION),
            'directory_identity': directory_id, 'original_source_pins': [p for p, _ in originals],
            'copied_source_before_after_pins': copied, 'copied_files': created,
            'copied_total_bytes': sum(s['bytes'] for s in SOURCES),
            'targets_imported_or_executed': False, 'scientific_admission': False,
            'existing_paths_permissions_repaired_or_overwritten': False,
            'partial_output_on_failure': 'Retained without retry, chmod, overwrite or cleanup.'}


def main():
    parser = argparse.ArgumentParser(description='Copy only two exact reviewed Git source blobs.')
    parser.add_argument('--expected-primary', required=True)
    parser.add_argument('--producer-sha256', required=True)
    args = parser.parse_args()
    try:
        row = run(args)
        code = 0
    except Exception as error:
        row = {'format': 'swdb.lanl14-completed-source-controls-copy.v1',
               'state': 'refused_or_partial_source_copy', 'exception_type': type(error).__name__,
               'original_receipt_policy': 'UNSEALED', 'partial_output_preserved': True,
               'targets_imported_or_executed': False, 'scientific_admission': False}
        code = 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    raw = json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False).encode() + b'\n'
    require(len(raw) <= MAX_STDOUT, 'compact_stdout_bound')
    sys.stdout.buffer.write(raw)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
