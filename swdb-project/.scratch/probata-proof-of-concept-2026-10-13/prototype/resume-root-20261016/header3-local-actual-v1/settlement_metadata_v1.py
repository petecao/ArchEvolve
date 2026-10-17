"""2026-10-16 ET. Finite passive Header3 G644 producer settlement, no proof interpretation.

Only stdlib/Git and physical metadata are used. Raw C/AST/SMT/binaries remain
remote; the output contains identities, status fields and bounded log notices.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess

resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
signal.alarm(120)
RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-abb598a4-t25-owned-swap-header3-public-v1')
PROFILE = RAW / 'owned-swap-header3-public-v1-profile'
SOURCE = Path('/data1/yanruj/probata-resume-20261016-abb598a4')
PRIMARY = Path('/data1/yanruj/ArchEvolve')
SHA = 'abb598a485cca67c77798e690382b44beb48c9e3'
EXPECTED_SHA = 'c63ed3337e81d121669b6e8735743dc1cb9dfff7e6e8470a25dfa40df6fd69cc'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def pin(path, cap=256 * 1024**2):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= cap
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    assert identity(before) == identity(path.lstat())
    return {'bytes': before.st_size, 'sha256': h.hexdigest()}


def read_json(path, cap=2 * 1024**2):
    before = pin(path, cap)
    value = json.loads(path.read_bytes())
    assert before == pin(path, cap)
    return value


def walk(root):
    rows = []
    pending = [root]
    while pending:
        parent = pending.pop()
        assert parent.resolve(strict=True) == parent and stat.S_ISDIR(parent.lstat().st_mode)
        with os.scandir(parent) as stream:
            entries = list(stream)
        for item in entries:
            path = Path(item.path)
            s = path.lstat()
            row = {'relative': str(path.relative_to(root))}
            if stat.S_ISDIR(s.st_mode):
                row['kind'] = 'directory'
                pending.append(path)
            elif stat.S_ISREG(s.st_mode):
                row.update(kind='file', **pin(path))
            elif stat.S_ISLNK(s.st_mode):
                row.update(kind='symlink', target=os.readlink(path))
            else:
                row.update(kind='special', mode=s.st_mode, bytes=s.st_size)
            rows.append(row)
            assert len(rows) <= 20000
    rows.sort(key=lambda row: Path(row['relative']).parts)
    assert sum(row.get('bytes', 0) for row in rows) <= 2 * 1024**3
    return rows


ENV = {'HOME': '/nonexistent', 'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
       'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0'}


def command(args, input=None):
    return subprocess.check_output(args, input=input, timeout=30, env=ENV)


def git(root, *args, input=None):
    return command(['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                    '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                    '-c', 'core.preloadIndex=false', '-c', 'index.threads=1', '-C', str(root), *args], input)


def primary_snapshot():
    common = PRIMARY / '.git'
    configs = {}
    for p in [common / 'config', common / 'config.worktree', *sorted((common / 'worktrees').glob('*/config.worktree'))]:
        configs[str(p)] = {'absent': True} if not os.path.lexists(p) else {**pin(p, 1024**2), 'identity': list(identity(p.lstat()))}
    lock = PRIMARY / 'swdb-project/records/.retention.lock'
    return {'configs': configs, 'retention_lock': {**pin(lock, 1024**2), 'identity': list(identity(lock.lstat()))},
            'worktree_registration_sha256': hashlib.sha256(git(PRIMARY, 'worktree', 'list', '--porcelain', '-z')).hexdigest()}


def status_fields(goal):
    keys = ('goal', 'property', 'function', 'line', 'smoke', 'passed', 'results', 'provers', 'verdict', 'failure_class')
    return {key: goal[key] for key in keys if key in goal}


before = walk(RAW)
expected_path = PROFILE / 'expected.json'
assert pin(expected_path)['sha256'] == EXPECTED_SHA
expected = read_json(expected_path)
result = read_json(PROFILE / 'result.json')
assert result['producer_complete'] is True and result['unexecuted'] == []
assert [row['id'] for row in result['runs']] == expected['target_ids']
preflight = read_json(RAW / 'preflight.json')
lane = read_json(RAW / 'lane.json')['socket_lane']
assert lane['node'] == 1 and lane['lease_generation'] == 644 and lane['ended_utc'] and lane['exit_code'] == 0
report = {'created': '2026-10-16 ET', 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'raw_root': str(RAW), 'scope': 'Finite producer settlement and byte retention only; complete mathematical term/hypothesis interpretation remains independent.',
          'uptime': command(['/usr/bin/uptime']).decode().strip(),
          'disks': command(['/usr/bin/df', '-B1', '/data1', '/data']).decode().strip(),
          'lane': lane, 'inner_resources': read_json(RAW / 'resources.json'),
          'outer_resources': read_json(RAW / 'outer-resources.json'),
          'source_after': read_json(RAW / 'source-after.json'), 'leases': {},
          'raw_file_manifest': before, 'raw_manifest_sha256': digest(before),
          'raw_files': sum(row['kind'] == 'file' for row in before),
          'raw_directories': sum(row['kind'] == 'directory' for row in before),
          'raw_bytes': sum(row.get('bytes', 0) for row in before),
          'raw_links_or_specials': [row for row in before if row['kind'] not in ('file', 'directory')],
          'producer_complete': result['producer_complete'],
          'all_three_producer_proven': result['all_three_producer_proven'],
          'result_pin': pin(PROFILE / 'result.json'), 'canonical': {}, 'leaves': []}
for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
    value = read_json(Path('/data1/yanruj/lact-host-lease') / (name + '.meta.json'))
    report['leases'][name] = {key: value.get(key) for key in ('state', 'lease')}
canonical = walk(PROFILE / 'canonical-inputs')
physical = [{'path': row['relative'], 'bytes': row['bytes'], 'sha256': row['sha256']} for row in canonical if row['kind'] == 'file']
assert physical == expected['canonical_files'] and all(row['kind'] in ('file', 'directory') for row in canonical)
report['canonical'] = {'files': len(physical), 'manifest_sha256': digest(physical), 'all_exact': True}
for row in result['runs']:
    directory = PROFILE / ('leaf-' + row['id'])
    inventory = read_json(directory / 'wp-inventory.json')
    goals = read_json(directory / 'wp-goals.json')
    census = read_json(directory / 'task-census.json')
    outcome = read_json(directory / 'outcome.json')
    properties = inventory['properties']
    by_property = {p['property'] for p in properties}
    dangling = sorted({d for p in properties for d in p['dependencies'] if d not in by_property})
    leaf = {'id': row['id'], 'outcome': {key: outcome.get(key) for key in ('verdict', 'failure_class', 'reason')},
            'resources': read_json(directory / 'resources.json'),
            'native_complete': inventory.get('complete'), 'native_goals': [status_fields(g) for g in inventory['goals']],
            'standard_goals': [status_fields(g) for g in goals], 'native_properties': len(properties),
            'dangling_dependencies': dangling, 'property_kinds': {},
            'census': {key: census[key] for key in ('native_goal_count', 'native_property_count', 'ordinary_count', 'smoke_count',
                                                 'internal_qed_inventory_only', 'missing_noninternal_tasks', 'extern_properties')},
            'common_exports': [{key: export[key] for key in ('export_id', 'goal', 'begin_byte', 'end_byte', 'sha256')} for export in census['common_exports']],
            'metadata_pins': {name: pin(directory / name) for name in ('command.json', 'resources.json', 'outcome.json',
                               'task-census.json', 'wp-goals.json', 'wp-inventory.json', 'wp-properties.csv', 'frama-c.log')}}
    for prop in properties:
        key = str(prop.get('kind'))
        leaf['property_kinds'][key] = leaf['property_kinds'].get(key, 0) + 1
    if outcome['verdict'] != 'proven':
        notices = []
        with (directory / 'frama-c.log').open('rb') as stream:
            for number, line in enumerate(stream, 1):
                if re.match(rb'^\[(?:wp|wp:[^\]]+|kernel|why3)[^\]]*\]', line) and re.search(rb'(?i)timeout|failed|unknown|warning|error|out of memory|killed|valid|goal', line):
                    text = line.decode(errors='replace').strip()[:512]
                    notices.append({'line': number, 'text': text, 'sha256': hashlib.sha256(line).hexdigest()})
                    if len(notices) == 40:
                        break
        leaf['bounded_failure_notices'] = notices
    report['leaves'].append(leaf)
roots = list(expected['source_consumer_trees'])
data = git(SOURCE, 'ls-tree', '-rlz', SHA, '--', *['swdb-project/' + root for root in roots])
source_rows = []
for part in data.split(b'\0'):
    if not part:
        continue
    meta, name = part.split(b'\t', 1)
    mode, kind, oid, size = meta.decode().split()
    assert kind == 'blob' and mode in ('100644', '100755')
    source_rows.append({'path': name.decode(), 'mode': mode, 'oid': oid, 'bytes': int(size)})
checkout = preflight['source_checkout']
assert len(source_rows) == checkout['files'] == 426 and digest(source_rows) == checkout['inventory_sha256']
source_found = walk(SOURCE / 'swdb-project')
source_physical = {'swdb-project/' + row['relative'] for row in source_found if row['kind'] == 'file'}
assert source_physical == {row['path'] for row in source_rows}
assert all(row['kind'] in ('file', 'directory') for row in source_found)
physical_oids = git(SOURCE, 'hash-object', '--no-filters', '--stdin-paths',
                    input=''.join(str(SOURCE / row['path']) + '\n' for row in source_rows).encode()).decode().splitlines()
assert physical_oids == [row['oid'] for row in source_rows]
assert git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == SHA
assert git(SOURCE, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip() == 'HEAD'
assert not git(SOURCE, 'status', '--porcelain', '--untracked-files=all', '--ignored')
assert primary_snapshot() == checkout['primary_before_after']
assert SOURCE.resolve(strict=True) == SOURCE and (SOURCE / '.git').is_dir()
assert (SOURCE / '.git/objects/info/alternates').read_text() == str(PRIMARY / '.git/objects') + '\n'
assert pin(SOURCE / '.git/config') == {key: checkout['private_git_config'][key] for key in ('bytes', 'sha256')}
assert (SOURCE / '.git/info/sparse-checkout').read_text() == checkout['private_sparse_patterns']
report['source'] = {'commit': SHA, 'detached': True, 'clean': True, 'physical_files': len(source_rows),
                    'physical_bytes': sum(row['bytes'] for row in source_rows),
                    'inventory_sha256': digest(source_rows), 'all_git_blobs_exact': True,
                    'primary_configs_registrations_retention_lock_equal': True,
                    'private_config_and_sparse_patterns_equal': True,
                    'retained_1433_source_exists': Path('/data1/yanruj/probata-resume-20261016-1433b8f5').is_dir()}
runtime = []
for path, expected_sha in expected['runtime_files'].items():
    actual = pin(Path(path))
    assert actual['sha256'] == expected_sha
    runtime.append({'path': path, **actual})
aliases = []
for row in expected['why3_elf_candidate_aliases']:
    path = Path(row['path'])
    assert stat.S_ISLNK(path.lstat().st_mode) and os.readlink(path) == row['target'] and str(path.resolve(strict=True)) == row['resolved']
    aliases.append(row)
report['runtime'] = {'files': len(runtime), 'files_sha256': digest(runtime), 'all_current_declared_pins_exact': True,
                     'aliases': aliases, 'producer_runtime_receipt_pin': pin(PROFILE / 'runtime.json'),
                     'compiler_runtime_receipt_pin': pin(PROFILE / 'compiler-runtime.json'),
                     'scope': 'Current declared physical pins plus original producer point checks. Loader/dlopen, source-to-binary and between-check identity remain TCB; no retroactive full historical dynamic closure.'}
report['method_pin'] = pin(PROFILE / 'method.json')
report['foundation_pin'] = pin(PROFILE / 'foundation.json')
report['source_consumer_receipts'] = [{'relative': str(path.relative_to(PROFILE)), **pin(path)} for path in sorted(PROFILE.glob('source-consumers-*.json'))]
report['public_record_files'] = [row['relative'] for row in before if '/records/proofs/' in row['relative'] and row['kind'] == 'file']
after = walk(RAW)
assert before == after
report['raw_before_after_equal'] = True
report['admission'] = {key: False for key in ('mathematical_cold_semantics', 'source_body', 'heap_typed_bridge',
                                            'caller', 'default_method', 'public_record', 'ticket_complete')}
payload = json.dumps(report, sort_keys=True, allow_nan=False)
assert len(payload.encode()) <= 1024**2
print(payload)
