"""ONE parent-owned passive deployment query. Updated 2026-10-08 ET; NOT RUN.

No hook imports, binding/request creation, fetch, Store or scientific execution.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import subprocess
import sys
import time

import yaml

BASE = Path('/data1/yanruj')
PRIMARY = BASE / 'ArchEvolve'
C = BASE / 'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
CORE = 'f893fed400347ed23d92e917d8bde21b75e5375d'
UID = 114316761
CREATOR_GID = 114316761
BASE_IDENTITY = {'dev': 2097, 'ino': 54132737, 'mode': stat.S_IFDIR | 0o700, 'uid': UID, 'gid': 0}
C_IDENTITY = {'dev': 2097, 'ino': 57973211, 'mode': stat.S_IFDIR | 0o775, 'uid': UID, 'gid': CREATOR_GID}
PRIMARY_IDENTITY = {'dev': 2097, 'ino': 54935911, 'mode': stat.S_IFDIR | 0o2777, 'uid': UID, 'gid': 0}
GIT = Path('/usr/bin/git')
PYTHON = Path('/usr/bin/python3.12')
NATIVES = {str(GIT): (4019024, '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
           str(PYTHON): (8020928, 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f')}
MANIFEST = 'd5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d'
BFS = '6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465'
RECORDS = {
    'candidate': 'swdb-project/records/candidates/typed-library-bfs-gem5-20261003-a2.baseline.yaml',
    'snapshot': 'swdb-project/records/source_snapshots/bfs-dx100-compile-20260925-a1.source.yaml',
    'implementation': 'swdb-project/records/implementations/dx100-bfs-scalar.yaml',
    'application': 'swdb-project/records/applications/dx100-gapbs.yaml',
}
TARGETS = (
    BASE / 'EvolveSWDB_sources/bfs-dx100-compile-20260925-a1.source/source',
    BASE / 'EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline/source',
)
END = time.monotonic() + 120
FIELDS = ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')


def require(value, code):
    if not value:
        raise ValueError(code)


def tick():
    require(time.monotonic() < END, 'query_deadline')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def values(s):
    return {key: getattr(s, 'st_' + key) for key in FIELDS}


def stamp(p):
    return values(p.lstat())


def identity(p):
    s = stamp(p)
    return {key: s[key] for key in ('dev', 'ino', 'mode', 'uid', 'gid')}


def canonical_path(p):
    require(p.is_absolute() and p.resolve(strict=True) == p
            and not any(x.is_symlink() for x in (p, *p.parents)), 'noncanonical_or_symlink')


def private_base():
    canonical_path(BASE)
    s = stamp(BASE)
    require(stat.S_ISDIR(s['mode']) and stat.S_IMODE(s['mode']) == 0o700
            and s['uid'] == UID and identity(BASE) == BASE_IDENTITY, 'private_base_identity')
    return s


def directory(p):
    canonical_path(p)
    require(p.is_relative_to(BASE), 'directory_outside_private_base')
    base = private_base()
    if p.is_relative_to(PRIMARY):
        require(identity(PRIMARY) == PRIMARY_IDENTITY, 'original_primary_private_route_identity')
    if p.is_relative_to(C):
        require(identity(C) == C_IDENTITY, 'original_C_private_route_identity')
    for part in reversed((p, *p.parents)):
        if not part.is_relative_to(BASE):
            continue
        s = stamp(part)
        # Ordinary owned routes may use the pinned BASE or actual creator group only.
        # Inherited directory SGID remains restricted to the private BASE group.
        require(stat.S_ISDIR(s['mode']) and s['uid'] == UID and s['gid'] in {base['gid'], CREATOR_GID}
                and s['dev'] == base['dev'] and not s['mode'] & 0o5000
                and (not s['mode'] & 0o2000 or s['gid'] == base['gid']), 'directory_owner_or_special_mode')
    return stamp(p)


def read(p, cap, owner):
    tick()
    canonical_path(p)
    before = stamp(p)
    require(stat.S_ISREG(before['mode']) and before['uid'] == owner and before['nlink'] == 1
            and not before['mode'] & 0o7000 and 0 <= before['size'] <= cap, 'file_type_owner_or_bound')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(values(os.fstat(fd)) == before, 'opened_file_changed')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(cap + 1)
        require(len(raw) == before['size'] and values(os.fstat(fd)) == before
                and stamp(p) == before, 'returned_file_changed')
    finally:
        os.close(fd)
    return raw, before


def git(repo, *args, absent_ok=False):
    tick()
    require(repo in (PRIMARY, C) and directory(repo) == ROOTS[repo], 'checkout_root_changed')
    result = subprocess.run([str(GIT), '--no-optional-locks', '--no-replace-objects', '-c',
                             'core.fsmonitor=false', '-C', str(repo), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=min(10, max(0.1, END - time.monotonic())))
    require(directory(repo) == ROOTS[repo], 'checkout_root_changed')
    require(len(result.stdout) <= 256 * 1024 and (result.returncode == 0 or
            absent_ok and result.returncode == 1 and not result.stdout), 'readonly_git_refused')
    return result.stdout


def unique_pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, 'duplicate_record_key')
        result[key] = value
    return result


class OriginalLoader(yaml.SafeLoader):
    pass


OriginalLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                               lambda loader, node: unique_pairs(loader.construct_pairs(node, deep=True)))


def records(repo, revision):
    result, pins = {}, {}
    for role, rel in RECORDS.items():
        size = int(git(repo, 'cat-file', '-s', revision + ':' + rel))
        require(0 < size <= 128 * 1024, 'original_record_bound')
        raw = git(repo, 'show', revision + ':' + rel)
        require(len(raw) == size, 'original_record_returned_size')
        result[role] = yaml.load(raw, Loader=OriginalLoader)
        row = git(repo, 'ls-tree', revision, '--', rel).decode().strip()
        require(row.startswith('100644 blob '), 'original_record_git_mode')
        pins[role] = {'path': rel, 'bytes': size, 'sha256': sha(raw), 'git_tree_entry': row}
    return result, pins


def target(p, expected):
    if not os.path.lexists(p):
        return {'path': str(p), 'observed_presence': False, 'original_manifest_verified': False}
    root_stat = directory(p)
    files, states, physical = [], {}, {}
    def fail(error):
        raise ValueError('incomplete_target_visibility') from error
    for current, dirs, names in os.walk(p, followlinks=False, onerror=fail):
        tick()
        require(len(states) <= 256, 'original_target_namespace_bound')
        for name in sorted(dirs + names):
            file = Path(current) / name
            rel = file.relative_to(p).as_posix()
            s = stamp(file)
            states[rel] = s
            require(not stat.S_ISLNK(s['mode']), 'target_symlink')
            if stat.S_ISDIR(s['mode']):
                directory(file)
            else:
                require(rel in expected, 'target_extra_file')
                require(s['gid'] in {BASE_IDENTITY['gid'], CREATOR_GID} and s['dev'] == BASE_IDENTITY['dev'], 'target_group_device')
                raw, opened = read(file, expected[rel]['bytes'], UID)
                row = {'path': rel, 'bytes': len(raw), 'sha256': sha(raw), 'executable': bool(opened['mode'] & 0o111)}
                require(row == expected[rel], 'target_original_file_mismatch')
                files.append(row)
                physical[rel] = {'bytes': len(raw), 'sha256': sha(raw), 'stat': opened}
    files.sort(key=lambda row: row['path'])
    require(len(files) == 53 and sha(canonical(files)) == MANIFEST, 'target_original_manifest_mismatch')
    require(stamp(p) == root_stat and all(stamp(p / rel) == s for rel, s in states.items()), 'target_postflight_changed')
    return {'path': str(p), 'observed_presence': True, 'original_manifest_verified': True,
            'artifact_sha256': MANIFEST, 'root_stat': root_stat, 'target_stats': states,
            'physical_files': physical, 'file_count': 53, 'logical_bytes': sum(row['bytes'] for row in files)}


def hooks():
    setting = git(PRIMARY, 'config', '--show-origin', '--null', '--get', 'core.hooksPath', absent_ok=True)
    route = git(PRIMARY, 'rev-parse', '--path-format=absolute', '--git-path', 'hooks').decode().strip()
    p = Path(route)
    result = {'core_hooksPath_origin_and_value': setting.decode().split('\0') if setting else [],
              'effective_primary_hooks_route': str(p), 'disposition': 'parent_decision_required_before_override',
              'source_or_export_worktree_relative_semantics_must_be_reviewed': True}
    if not os.path.lexists(p):
        result['observed_presence'] = False
        return result
    if not p.is_relative_to(BASE):
        result['contents_observed'] = False
        result['boundary'] = 'configured_hooks_outside_fixed_private_base_not_read'
        return result
    root_stat = directory(p)
    rows = []
    for file in sorted(p.iterdir()):
        require(len(rows) < 64, 'hooks_namespace_bound')
        s = stamp(file)
        require(stat.S_ISREG(s['mode']), 'hook_entry_not_regular')
        raw, s = read(file, 512 * 1024, UID)
        rows.append({'name': file.name, 'bytes': len(raw), 'sha256': sha(raw), 'stat': s,
                     'executable': bool(s['mode'] & 0o111), 'sample_filename': file.name.endswith('.sample')})
    require(stamp(p) == root_stat and all(stamp(p / row['name']) == row['stat'] for row in rows), 'hooks_changed')
    result.update(observed_presence=True, contents_observed=True, root_stat=root_stat, entries=rows)
    return result


def main():
    global ROOTS
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-primary40', required=True)
    parser.add_argument('--query-source-sha256', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}', args.expected_primary40)
            and re.fullmatch('[0-9a-f]{64}', args.query_source_sha256), 'explicit_pins_required')
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == UID and os.getgid() == os.getegid() == CREATOR_GID
            and pwd.getpwuid(UID).pw_name == 'yanruj'
            and Path(sys.executable) == PYTHON, 'exact_native_host_account')
    require(not any(os.environ.get(key) for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_NAMESPACE',
                'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES')), 'git_startup_redirection')
    base_stat = private_base()
    ROOTS = {p: directory(p) for p in (PRIMARY, C)}
    own = Path(__file__).absolute()
    require(own.is_relative_to(BASE) and not own.is_relative_to(PRIMARY) and not own.is_relative_to(C), 'query_source_scope')
    own_raw, own_stat = read(own, 64 * 1024, UID)
    require(sha(own_raw) == args.query_source_sha256 and not own_stat['mode'] & 0o022, 'query_source_pin')
    natives = {}
    for name, (size, digest) in NATIVES.items():
        raw, s = read(Path(name), size, 0)
        require(len(raw) == size and sha(raw) == digest and not s['mode'] & 0o022 and s['mode'] & 0o111, 'native_pin')
        natives[name] = {'path': name, 'bytes': size, 'sha256': digest, 'stat': s}
    retention = PRIMARY / 'swdb-project/records/.retention.lock'
    retention_original = read(retention, 0, UID)
    require(retention_original[0] == b'', 'retention_not_empty')
    primary_refs = {ref: git(PRIMARY, 'rev-parse', ref).decode().strip()
                    for ref in ('HEAD', 'origin/yanrujhou_main', 'origin/codex/lanl-analytic-eval')}
    require(primary_refs['HEAD'] == primary_refs['origin/yanrujhou_main'] == args.expected_primary40
            and git(PRIMARY, 'branch', '--show-current').strip() == b'yanrujhou_main'
            and git(PRIMARY, 'status', '--porcelain').strip() == b'?? swdb-project/records/.retention.lock'
            and git(C, 'rev-parse', 'HEAD').decode().strip() == CORE and not git(C, 'status', '--porcelain').strip(),
            'original_checkout_refs_or_status')
    git(PRIMARY, 'merge-base', '--is-ancestor', CORE, args.expected_primary40)
    core_tree = git(C, 'ls-tree', '-rz', CORE, '--', 'swdb-project/swdb')
    require(core_tree == git(PRIMARY, 'ls-tree', '-rz', args.expected_primary40, '--', 'swdb-project/swdb')
            and sum(row.split(b'\t', 1)[1].endswith(b'.py') for row in core_tree.split(b'\0') if row) == 185, 'core185_changed')
    original, c_pins = records(C, CORE)
    current, p_pins = records(PRIMARY, args.expected_primary40)
    require(original == current and c_pins == p_pins, 'original_catalog_records_changed')
    files = original['candidate']['artifact']['files']
    require(len(files) == 53 and files == original['snapshot']['artifact']['files']
            and sha(canonical(files)) == original['candidate']['artifact']['sha256']
            == original['snapshot']['artifact']['sha256'] == MANIFEST
            and original['application']['source']['local_path'] == 'apps/dx100'
            and next(row['sha256'] for row in files if row['path'] == 'benchmarks/gapbs/src/bfs.cc') == BFS,
            'original_manifest_or_application_mismatch')
    expected = {row['path']: row for row in files}
    targets = [target(p, expected) for p in TARGETS]
    hook_facts = hooks()
    require(directory(PRIMARY) == ROOTS[PRIMARY] and directory(C) == ROOTS[C] and private_base() == base_stat
            and read(retention, 0, UID) == retention_original and read(own, 64 * 1024, UID) == (own_raw, own_stat), 'query_postflight_changed')
    for name, (size, digest) in NATIVES.items():
        raw, s = read(Path(name), size, 0)
        require(sha(raw) == digest and s == natives[name]['stat'], 'native_postflight_changed')
    for ref, value in primary_refs.items():
        require(git(PRIMARY, 'rev-parse', ref).decode().strip() == value, 'ref_postflight_changed')
    require(git(C, 'rev-parse', 'HEAD').decode().strip() == CORE
            and not git(C, 'status', '--porcelain').strip()
            and git(PRIMARY, 'status', '--porcelain').strip() == b'?? swdb-project/records/.retention.lock', 'status_postflight_changed')
    value = {'format': 'swdb.lanl17-original-dx100-deployment-prerequisites-observed.v1', 'sealed': False,
             'checked_utc': datetime.now(timezone.utc).isoformat(), 'query_source_sha256': sha(own_raw),
             'primary_refs': primary_refs, 'original_C': CORE, 'core_module_count': 185,
             'unchanged_core_git_tree_sha256': sha(core_tree), 'private_base': {'path': str(BASE), 'identity': identity(BASE)},
             'checkout_root_stats': {str(p): s for p, s in ROOTS.items()}, 'native_pins': natives,
             'original_record_pins_C_and_PRIMARY': p_pins, 'original_artifact_sha256': MANIFEST,
             'original_bfs_source_sha256': BFS, 'targets': targets, 'effective_primary_hooks': hook_facts,
             'scope': 'Passive source/native/hooks facts only; no target selection, request, binding, source publication, cleanup, capacity or scientific admission.'}
    raw = canonical(value)
    require(len(raw) <= 256 * 1024, 'metadata_output_bound')
    print(raw.decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'format': 'swdb.lanl17-deployment-query-refusal.v1', 'sealed': False,
                          'error_class': type(error).__name__, 'error_sha256': sha(str(error).encode())}, sort_keys=True))
        sys.exit(1)
