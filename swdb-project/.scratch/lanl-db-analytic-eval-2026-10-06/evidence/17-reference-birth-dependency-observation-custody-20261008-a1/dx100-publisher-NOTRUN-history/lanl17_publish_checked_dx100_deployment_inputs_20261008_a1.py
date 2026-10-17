"""Fresh private hook/request publication only. Updated 2026-10-08 ET; SOURCE ONLY / NOT RUN.

No source worktree, original metadata-control/raw, hook invocation or scientific action.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import socket
import stat
import subprocess
import sys
import time

BASE = Path('/data1/yanruj')
PRIMARY = BASE / 'ArchEvolve'
C = BASE / 'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
RUNS = Path('/data/yanruj/EvolveSWDB_runs')
UID = CREATOR_GID = 114316761
CORE = 'f893fed400347ed23d92e917d8bde21b75e5375d'
CORE_TREE_SHA = '43864cde40d28f83331ebafdb247e2bf688e62a351e6b5619cd68bd098413c77'
HOOK_REL = 'swdb-project/scripts/deployment/dx100-binding/post-checkout'
HOOK_SHA = 'd340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527'
FACTS_SHA = '0252f42cde88946aadc6866af53b867b55b782bc9883eae3bb8b85a5ee56823e'
REVIEW_SHA = '5072c3025b0c372d6d4455d213d1e57d8ba6dda3f0b087883b447026828c4d07'
QUERY_SHA = '6d40fa3a6091abf01e88ee85c04636fed1ef051cc17729255a6485855596a4c1'
PACKAGE_QUERY_SHA = 'b9ac7235b76496925d7bca8609dfb03b94fc0f13f9015525816d6633ff33ef75'
MANIFEST = 'd5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d'
TARGET = BASE / 'EvolveSWDB_sources/bfs-dx100-compile-20260925-a1.source/source'
SECOND_TARGET = BASE / 'EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline/source'
GIT = Path('/usr/bin/git')
PYTHON = Path('/usr/bin/python3.12')
SYSTEM = Path('/usr/lib/python3/dist-packages')
FIELDS = ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')
IDENTITY_FIELDS = ('dev', 'ino', 'mode', 'uid', 'gid')
END = time.monotonic() + 180
STATE = {'state': 'preflight', 'created_paths': []}


def require(value, code):
    if not value:
        raise ValueError(code)


def tick():
    require(time.monotonic() < END, 'publication_deadline')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, 'nonfinite_json'))


def values(s):
    return {key: getattr(s, 'st_' + key) for key in FIELDS}


def stamp(p):
    return values(p.lstat())


def identity(p):
    s = stamp(p)
    return {key: s[key] for key in IDENTITY_FIELDS}


def canonical_path(p):
    require(p.is_absolute() and p.resolve(strict=True) == p
            and not any(x.is_symlink() for x in (p, *p.parents)), 'noncanonical_or_symlink')


def read(p, cap, owner):
    tick()
    canonical_path(p)
    before = stamp(p)
    require(stat.S_ISREG(before['mode']) and before['uid'] == owner and before['nlink'] == 1
            and not before['mode'] & 0o7000 and 0 <= before['size'] <= cap, 'file_owner_type_or_bound')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(values(os.fstat(fd)) == before, 'opened_file_changed')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(cap + 1)
        require(len(raw) == before['size'] and values(os.fstat(fd)) == before
                and stamp(p) == before, 'returned_bytes_or_stat_changed')
    finally:
        os.close(fd)
    return raw, before


def original_json(path, expected_sha, size=None):
    require(path.is_relative_to(BASE), 'original_metadata_outside_private_base')
    raw, s = read(path, 128 * 1024, UID)
    require(not s['mode'] & 0o022 and sha(raw) == expected_sha
            and (size is None or len(raw) == size), 'original_metadata_pin')
    return parse(raw), raw, s


def directory(p, base_pin):
    canonical_path(p)
    require(p.is_relative_to(BASE) and identity(BASE) == base_pin, 'private_root_changed_or_outside')
    for part in reversed((p, *p.parents)):
        if not part.is_relative_to(BASE):
            continue
        s = stamp(part)
        require(stat.S_ISDIR(s['mode']) and s['uid'] == UID and s['dev'] == base_pin['dev']
                and s['gid'] in {base_pin['gid'], CREATOR_GID} and not s['mode'] & 0o5000
                and (not s['mode'] & 0o2000 or s['gid'] == base_pin['gid']), 'directory_owner_group_or_mode')
    return stamp(p)


def absent(p, parent, prefix):
    canonical_path(parent)
    require(p.is_absolute() and p.parent == parent and str(p) == str(parent / p.name)
            and re.fullmatch(re.escape(prefix) + '[a-z0-9-]+', p.name)
            and not os.path.lexists(p), 'fresh_route_required')


def native(p, pin):
    raw, s = read(p, 64 * 1024 * 1024, 0)
    require(str(p) == pin['path'] and len(raw) == pin['bytes'] and sha(raw) == pin['sha256']
            and s == pin['stat'] and s['mode'] & 0o111 and not s['mode'] & 0o022, 'native_original_pin')
    return raw, s


def git(repo, *args, absent_ok=False):
    tick()
    require(directory(repo, FACTS['private_base']['identity']) == ROOTS[repo], 'checkout_root_changed')
    result = subprocess.run([str(GIT), '--no-optional-locks', '--no-replace-objects', '-c',
                             'core.fsmonitor=false', '-C', str(repo), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=min(10, max(0.1, END - time.monotonic())))
    require(directory(repo, FACTS['private_base']['identity']) == ROOTS[repo], 'checkout_root_changed')
    require(len(result.stdout) <= 2 * 1024 * 1024 and (result.returncode == 0 or
            absent_ok and result.returncode == 1 and not result.stdout), 'readonly_git_refused')
    return result.stdout


def verify_target(original):
    p = Path(original['path'])
    require(p in (TARGET, SECOND_TARGET) and original['file_count'] == 53
            and original['original_manifest_verified'] is True and original['artifact_sha256'] == MANIFEST,
            'original_target_identity')
    require(directory(p, FACTS['private_base']['identity']) == original['root_stat'], 'original_target_root_changed')
    physical, seen = {}, set()
    def fail(error):
        raise ValueError('incomplete_target_visibility') from error
    for current, dirs, names in os.walk(p, followlinks=False, onerror=fail):
        tick()
        for name in sorted(dirs + names):
            file = Path(current) / name
            rel = file.relative_to(p).as_posix()
            require(len(seen) < 256 and rel not in seen, 'target_namespace_bound_or_duplicate')
            seen.add(rel)
            s = stamp(file)
            require(s == original['target_stats'].get(rel), 'target_original_stat_changed')
            if stat.S_ISDIR(s['mode']):
                directory(file, FACTS['private_base']['identity'])
            else:
                require(rel in original['physical_files'] and s['gid'] in {0, CREATOR_GID}
                        and s['dev'] == FACTS['private_base']['identity']['dev'], 'target_original_file_group_or_device')
                expected = original['physical_files'][rel]
                raw, opened = read(file, 32 * 1024 * 1024, UID)
                require(opened == expected['stat'] and len(raw) == expected['bytes']
                        and sha(raw) == expected['sha256'], 'target_original_bytes_changed')
                physical[rel] = {'path': rel, 'bytes': len(raw), 'sha256': sha(raw),
                                 'executable': bool(opened['mode'] & 0o111)}
    require(seen == set(original['target_stats']) and len(physical) == 53
            and sha(canonical(sorted(physical.values(), key=lambda row: row['path']))) == MANIFEST,
            'complete_original_target_manifest')
    require(stamp(p) == original['root_stat']
            and all(stamp(p / rel) == s for rel, s in original['target_stats'].items()), 'target_postflight_changed')


def verify_hooks():
    original = FACTS['effective_primary_hooks']
    require(original['core_hooksPath_origin_and_value'] == [] and len(original['entries']) == 14
            and all(row['sample_filename'] is True and row['name'].endswith('.sample') for row in original['entries']),
            'reviewed_sample_hooks_disposition')
    require(git(PRIMARY, 'config', '--show-origin', '--null', '--get', 'core.hooksPath', absent_ok=True) == b'',
            'hooksPath_changed_since_parent_review')
    p = Path(original['effective_primary_hooks_route'])
    require(p == PRIMARY / '.git/hooks'
            and git(PRIMARY, 'rev-parse', '--path-format=absolute', '--git-path', 'hooks').decode().strip() == str(p),
            'original_hooks_route_changed')
    require(directory(p, FACTS['private_base']['identity']) == original['root_stat']
            and {x.name for x in p.iterdir()} == {row['name'] for row in original['entries']}, 'original_hooks_namespace_changed')
    for row in original['entries']:
        raw, s = read(p / row['name'], 512 * 1024, UID)
        require(s == row['stat'] and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'original_sample_hook_changed')
    require(stamp(p) == original['root_stat'], 'original_hooks_root_changed')


def package_pin(path, expected):
    p = Path(path)
    canonical_path(p)
    require(p.is_relative_to(SYSTEM), 'package_outside_fixed_system_route')
    for part in (p.parent, *p.parent.parents):
        if part.is_relative_to(Path('/usr/lib')):
            s = stamp(part)
            require(stat.S_ISDIR(s['mode']) and s['uid'] == 0 and not s['mode'] & 0o7022,
                    'package_directory_unsafe')
    raw, s = read(p, 128 * 1024 * 1024 if p.suffix == '.so' else 16 * 1024 * 1024, 0)
    require(s == expected['stat'] and len(raw) == expected['bytes'] and sha(raw) == expected['sha256']
            and not s['mode'] & 0o022, 'original_package_file_changed')


def verify_package(facts):
    require(facts['format'] == 'swdb.lanl17-native-system-pyyaml-package-facts-original.v1'
            and facts['sealed'] is False and facts['query_source']['sha256'] == PACKAGE_QUERY_SHA
            and isinstance(facts['yaml_version'], str) and len(facts['yaml_version']) <= 64,
            'reviewed_package_query_identity')
    require(facts['native_python'] == FACTS['native_pins'][str(PYTHON)], 'package_native_differs')
    initial = facts['yaml_init']
    spec = importlib.util.find_spec('yaml')
    require('yaml' not in sys.modules and spec is not None and spec.origin == initial['path'], 'installed_package_origin_changed')
    require(Path(initial['path']).name == '__init__.py' and Path(initial['path']).parent.name == 'yaml'
            and len(facts['imported_modules']) <= 32, 'package_origin_or_namespace')
    package_pin(initial['path'], initial)
    for row in facts['imported_modules'].values():
        package_pin(row['source']['path'], row['source'])
        if row['cached_observed'] is True:
            require(row['cached_origin'] == row['cached']['path'], 'cached_original_path')
            package_pin(row['cached']['path'], row['cached'])
        elif row['cached_origin'] is not None:
            require(not os.path.lexists(row['cached_origin']), 'original_absent_cache_changed')


def commands(prepare_path):
    require(os.environ.get('PATH') == prepare_path, 'explicit_prepare_PATH_mismatch')
    result = {}
    for name in ('git', 'python3', 'tmux', 'numactl', 'strace', 'timeout', 'bash', 'node'):
        route = shutil.which(name, path=prepare_path)
        require(route is not None, 'original_necessary_command_unavailable')
        p = Path(route).resolve(strict=True)
        raw, s = read(p, 64 * 1024 * 1024, 0)
        require(s['mode'] & 0o111 and not s['mode'] & 0o022, 'necessary_command_mode')
        result[name] = {'resolved_path': str(p), 'bytes': len(raw), 'sha256': sha(raw), 'stat': s}
    require(result['git']['resolved_path'] == str(GIT) and result['python3']['resolved_path'] == str(PYTHON),
            'PATH_git_or_python_differs_from_native')
    return result


def write_original(p, raw, mode):
    tick()
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, mode)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        s = values(os.fstat(fd))
        require(s == stamp(p) and s['uid'] == UID and s['nlink'] == 1 and stat.S_IMODE(s['mode']) == mode,
                'exclusive_publication_file_changed')
    finally:
        os.close(fd)
    require(read(p, len(raw), UID) == (raw, s), 'publication_returned_bytes_changed')
    return s


def main():
    global FACTS, ROOTS
    p = argparse.ArgumentParser()
    for key in ('final-source40', 'publisher-source-sha256', 'facts-file', 'facts-parent-review-file',
                'package-facts-file', 'package-facts-sha256', 'source', 'raw', 'original-metadata-control',
                'hooks-directory', 'deployment-control', 'prepare-path'):
        p.add_argument('--' + key, required=True)
    a = p.parse_args()
    require(re.fullmatch('[0-9a-f]{40}', a.final_source40)
            and re.fullmatch('[0-9a-f]{64}', a.publisher_source_sha256)
            and re.fullmatch('[0-9a-f]{64}', a.package_facts_sha256), 'explicit_actual_pins_required')
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == UID and os.getgid() == os.getegid() == CREATOR_GID
            and pwd.getpwuid(UID).pw_name == 'yanruj' and Path(sys.executable).resolve() == PYTHON
            and sys.flags.dont_write_bytecode and sys.flags.no_user_site, 'exact_native_host_account_startup')
    require(not any(os.environ.get(k) for k in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONINSPECT',
                                               'LD_PRELOAD', 'LD_LIBRARY_PATH'))
            and not any(k.startswith('GIT_') for k in os.environ), 'startup_overrides_not_cleared')
    os.umask(0o077)
    facts_file, review_file, package_file = map(Path, (a.facts_file, a.facts_parent_review_file, a.package_facts_file))
    FACTS, facts_raw, facts_stat = original_json(facts_file, FACTS_SHA, 60682)
    review, review_raw, review_stat = original_json(review_file, REVIEW_SHA, 1132)
    package, package_raw, package_stat = original_json(package_file, a.package_facts_sha256)
    require(FACTS['format'] == 'swdb.lanl17-original-dx100-deployment-prerequisites-observed.v1'
            and FACTS['sealed'] is False and FACTS['query_source_sha256'] == QUERY_SHA
            and FACTS['original_C'] == CORE and FACTS['core_module_count'] == 185
            and FACTS['unchanged_core_git_tree_sha256'] == CORE_TREE_SHA,
            'original_live_source_facts_identity')
    base_pin = FACTS['private_base']['identity']
    require(FACTS['private_base']['path'] == str(BASE)
            and base_pin == {'dev': 2097, 'ino': 54132737, 'mode': stat.S_IFDIR | 0o700, 'uid': UID, 'gid': 0},
            'original_private_base_identity')
    directory(BASE, base_pin)
    require(review['format'] == 'swdb.lanl17-dx100-live-source-facts-parent-review.v1'
            and review['sealed'] is False and review['selected_protected_target'] == str(TARGET)
            and review['original']['bytes'] == 60682 and review['original']['sha256'] == FACTS_SHA,
            'parent_reviewed_target_selection')
    ROOTS = {x: directory(x, base_pin) for x in (PRIMARY, C)}
    require(all(ROOTS[x] == FACTS['checkout_root_stats'][str(x)] for x in ROOTS), 'original_checkout_root_changed')
    own = Path(__file__).absolute()
    require(own.parent == BASE, 'private_publisher_source_required')
    own_raw, own_stat = read(own, 128 * 1024, UID)
    require(sha(own_raw) == a.publisher_source_sha256 and not own_stat['mode'] & 0o022, 'publisher_own_source_pin')
    native_originals = {x: native(x, FACTS['native_pins'][str(x)]) for x in (GIT, PYTHON)}
    runtime_commands = commands(a.prepare_path)
    verify_package(package)
    source, raw, metadata, hooks, control = map(Path, (a.source, a.raw, a.original_metadata_control,
                                                    a.hooks_directory, a.deployment_control))
    absent(source, BASE, 'ArchEvolve-lanl17-')
    absent(raw, RUNS, 'lanl17-')
    absent(metadata, RUNS, 'lanl17-metadata-')
    absent(hooks, BASE, 'lanl17-dx100-hooks-')
    absent(control, BASE, 'lanl17-dx100-deployment-')
    require(len({source, raw, metadata, hooks, control}) == 5, 'fresh_paths_overlap')
    refs = {ref: git(PRIMARY, 'rev-parse', ref).decode().strip()
            for ref in ('HEAD', 'origin/yanrujhou_main', 'origin/codex/lanl-analytic-eval')}
    require(refs['HEAD'] == refs['origin/yanrujhou_main'] == a.final_source40
            and git(PRIMARY, 'branch', '--show-current').strip() == b'yanrujhou_main'
            and git(PRIMARY, 'status', '--porcelain').strip() == b'?? swdb-project/records/.retention.lock'
            and git(C, 'rev-parse', 'HEAD').decode().strip() == CORE and not git(C, 'status', '--porcelain').strip(),
            'delivered_R_or_original_C_state')
    retention_path = PRIMARY / 'swdb-project/records/.retention.lock'
    retention = read(retention_path, 0, UID)
    git(PRIMARY, 'merge-base', '--is-ancestor', CORE, a.final_source40)
    tree = git(PRIMARY, 'ls-tree', '-rz', a.final_source40, '--', 'swdb-project/swdb')
    require(sha(tree) == CORE_TREE_SHA and tree == git(C, 'ls-tree', '-rz', CORE, '--', 'swdb-project/swdb')
            and sum(x.split(b'\t', 1)[1].endswith(b'.py') for x in tree.split(b'\0') if x) == 185, 'C185_or_namespace_changed')
    record_pins = {}
    for name, original in FACTS['original_record_pins_C_and_PRIMARY'].items():
        rel = original['path']
        require(git(PRIMARY, 'ls-tree', a.final_source40, '--', rel).decode().strip() == original['git_tree_entry']
                and int(git(PRIMARY, 'cat-file', '-s', a.final_source40 + ':' + rel)) == original['bytes'],
                'four_original_record_tree_or_size_changed')
        body = git(PRIMARY, 'show', a.final_source40 + ':' + rel)
        require(len(body) == original['bytes'] and sha(body) == original['sha256'], 'four_original_record_bytes_changed')
        record_pins[name] = {k: original[k] for k in ('path', 'bytes', 'sha256')}
    hook = git(PRIMARY, 'show', a.final_source40 + ':' + HOOK_REL)
    require(len(hook) == 17300 and sha(hook) == HOOK_SHA
            and git(PRIMARY, 'ls-tree', a.final_source40, '--', HOOK_REL).startswith(b'100755 blob '),
            'selected_hook_Git_bytes_or_mode_changed')
    require(b'/apps/dx100' in git(PRIMARY, 'show', a.final_source40 + ':swdb-project/.gitignore').splitlines(),
            'exact_runtime_alias_ignore_missing')
    originals = {Path(row['path']): row for row in FACTS['targets']}
    require(set(originals) == {TARGET, SECOND_TARGET}, 'both_original_targets_required')
    for original in originals.values():
        verify_target(original)
    verify_hooks()
    tick()
    STATE['state'] = 'private_publication_started'
    control.mkdir(mode=0o700)
    STATE['created_paths'].append(str(control))
    hooks.mkdir(mode=0o700)
    STATE['created_paths'].append(str(hooks))
    control_identity, hooks_identity = identity(control), identity(hooks)
    hook_path = hooks / 'post-checkout'
    hook_stat = write_original(hook_path, hook, 0o700)
    STATE['created_paths'].append(str(hook_path))
    selected = originals[TARGET]
    request = {'format': 'swdb.dx100-source-deployment-request.v1', 'uid': UID, 'creator_gid': CREATOR_GID,
               'source': str(source), 'expected_revision': a.final_source40,
               'private_base': {'path': str(BASE), 'identity': base_pin},
               'control_base': {'path': str(BASE), 'identity': base_pin},
               'control': {'path': str(control), 'identity': control_identity},
               'target': {'path': str(TARGET), 'stat': selected['root_stat']}, 'target_stats': selected['target_stats'],
               'records': record_pins, 'hook': {'path': str(hook_path), 'sha256': HOOK_SHA},
               'git': FACTS['native_pins'][str(GIT)], 'python': FACTS['native_pins'][str(PYTHON)],
               'pyyaml_parent_observed': {'version': package['yaml_version'], 'source': package['yaml_init'],
                                          'package_facts_file_sha256': a.package_facts_sha256}}
    request_raw = canonical(request) + b'\n'
    require(len(request_raw) <= 2 * 1024 * 1024, 'hook_request_original_bound')
    request_path = control / 'request.json'
    request_stat = write_original(request_path, request_raw, 0o600)
    STATE['created_paths'].append(str(request_path))
    for original in originals.values():
        verify_target(original)
    verify_hooks()
    verify_package(package)
    require(commands(a.prepare_path) == runtime_commands, 'runtime_command_postflight_changed')
    require(read(own, 128 * 1024, UID) == (own_raw, own_stat), 'publisher_source_changed')
    for path, raw_body, original_stat in ((facts_file, facts_raw, facts_stat), (review_file, review_raw, review_stat),
                                           (package_file, package_raw, package_stat)):
        require(read(path, 128 * 1024, UID) == (raw_body, original_stat), 'original_metadata_changed')
    require(all(native(x, FACTS['native_pins'][str(x)]) == original for x, original in native_originals.items())
            and read(retention_path, 0, UID) == retention, 'native_or_empty_retention_changed')
    require(all(git(PRIMARY, 'rev-parse', ref).decode().strip() == value for ref, value in refs.items())
            and git(C, 'rev-parse', 'HEAD').decode().strip() == CORE
            and not git(C, 'status', '--porcelain').strip()
            and git(PRIMARY, 'status', '--porcelain').strip() == b'?? swdb-project/records/.retention.lock',
            'refs_or_clean_sources_changed')
    require(directory(BASE, base_pin) and identity(control) == control_identity and identity(hooks) == hooks_identity
            and read(hook_path, 17300, UID) == (hook, hook_stat)
            and read(request_path, len(request_raw), UID) == (request_raw, request_stat), 'published_routes_changed')
    absent(source, BASE, 'ArchEvolve-lanl17-')
    absent(raw, RUNS, 'lanl17-')
    absent(metadata, RUNS, 'lanl17-metadata-')
    overrides = {'PATH': a.prepare_path, 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
                 'GIT_CONFIG_VALUE_0': str(hooks), 'SWDB_DX100_BINDING_REQUEST': str(request_path),
                 'SWDB_DX100_BINDING_REQUEST_SHA256': sha(request_raw),
                 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONSAFEPATH': '1'}
    receipt = {'format': 'swdb.lanl17-dx100-deployment-inputs-publication-original.v1', 'sealed': False,
               'checked_utc': datetime.now(timezone.utc).isoformat(), 'publisher_sha256': sha(own_raw),
               'final_source_commit': a.final_source40, 'core_C': CORE, 'core_module_count': 185,
               'unchanged_core_git_tree_sha256': CORE_TREE_SHA, 'original_facts_sha256': FACTS_SHA,
               'parent_facts_review_sha256': REVIEW_SHA, 'package_facts_sha256': a.package_facts_sha256,
               'hooks': {'path': str(hooks), 'identity': hooks_identity},
               'hook': {'path': str(hook_path), 'bytes': len(hook), 'sha256': HOOK_SHA, 'stat': hook_stat},
               'deployment_control': {'path': str(control), 'identity': control_identity},
               'request': {'path': str(request_path), 'bytes': len(request_raw), 'sha256': sha(request_raw), 'stat': request_stat},
               'future_hook_receipt': str(control / 'dx100-binding-original.json'),
               'source_raw_metadata_control_still_absent': [str(source), str(raw), str(metadata)],
               'selected_original_target': str(TARGET), 'target_original_root_stat': selected['root_stat'],
               'original_artifact_sha256': MANIFEST, 'runtime_commands': runtime_commands,
               'pyyaml_observed_version': package['yaml_version'], 'public_task_environment_overrides': overrides,
               'remove_only_for_this_future_child': ['PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONINSPECT',
                                                     'LD_PRELOAD', 'LD_LIBRARY_PATH', 'all original GIT_* overrides'],
               'HOME_and_CODEX_HOME_unchanged_no_auth_read': True, 'provider_calls': 0, 'application_outcomes': 0,
               'scope': 'Private hook/request publication only. No hook/source provisioning, prepare, campaign, capacity, cleanup or scientific admission.'}
    receipt_path = control / 'publication-original.json'
    receipt_raw = canonical(receipt) + b'\n'
    require(len(receipt_raw) <= 16384, 'bounded_original_publication_receipt')
    write_original(receipt_path, receipt_raw, 0o600)
    STATE['created_paths'].append(str(receipt_path))
    require(read(own, 128 * 1024, UID) == (own_raw, own_stat), 'own_source_changed_before_success')
    STATE['state'] = 'private_hook_and_request_published'
    result = {'format': 'swdb.lanl17-dx100-deployment-publication-status-original.v1', 'sealed': False,
              'state': STATE['state'], 'final_source_commit': a.final_source40,
              'receipt_path': str(receipt_path), 'receipt_bytes': len(receipt_raw), 'receipt_sha256': sha(receipt_raw),
              'request_path': str(request_path), 'request_sha256': sha(request_raw),
              'public_task_environment_overrides': overrides, 'hook_invoked': False,
              'source_worktree_created': False, 'provider_calls': 0, 'application_outcomes': 0}
    output = canonical(result)
    require(len(output) <= 16384, 'bounded_status')
    print(output.decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'format': 'swdb.lanl17-dx100-deployment-publication-refusal.v1', 'sealed': False,
                          **STATE, 'error_class': type(error).__name__, 'error_sha256': sha(str(error).encode()),
                          'partials_preserved': True, 'hook_invoked': False}, sort_keys=True))
        sys.exit(1)
