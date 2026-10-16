"""2026-10-16 ET. INERT passive private-native86 cold auditor.

Root must review and admit reader/policy/runtime first. No project import,
compiler/native/solver/version/SSH/child execution or filesystem mutation.
Source/frozen/object/binary payloads are hashed locally on mbit10, never emitted.
Successful private observations establish neither public proof nor source-call,
hardware, current0.2, body-refinement, or whole-ticket acceptance.
"""
import ast
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import types

RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-whole-native86-2baf722f-v4'
COMMIT = '2baf722fdaa6cba24b859eae3172a6f597417d72'
ENTRY = ('linux_native86_entry_v4.py', '9f63dbe826ca70f2ceacd37b56753a5f212811a5a377c7baed59da4de60b7721')
RUN_POLICY = ('linux_native86_policy_v4.json', '14be0baf2dece709210abb6039b0ab7ede41c5e8d5d1dfbe08ed47b6f3ba9f5b')
COMMAND_SHA = 'fe518dfcdb0f5910f25d6678b5faa5500140d61a775b5c4873a10f8fc9324f70'
ROOT_RECEIPT_SHA = '67241250320da121d467688a89308db60831e6dea0c324329e7029a62373e26b'
GUARD_REVIEW_SHA = 'ad31177bce794e960107439ac2080f2f1af5eb71fa83007264edc6c1a4274682'
GUARDS = {'execute.py': '8442533f911e2ba7f10757a5b16ba451d4ece7d9d5dc292ce5b9d8c29eabdcbf',
          'watch.py': '49be8a36d6e04b50e1ab599dad8b00f78a1c639132c3079c523c2c0c9177c5f0',
          'run.sh': '901415b8bf07078acbaca6549e01a6836967524f1f06a36d57e80ac58e2b9603'}
RESULT = {'controls': 86, 'family_dtype_cases': 66, 'history_cases': 6,
          'subtract_fold_cases': 6, 'action_order_cases': 2, 'refusals': 6}
FLAGS = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-sanitize-recover=all']
INPUTS = ('whole_values_native_v1.c', 'whole_value_backend_v1.h', 'whole_adapters.h', 'whole_value_builders_v1.h', 'whole_closed_routes_v1.h')
HELPER_PINS = {'closed_python_surface.py': '748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af',
               'python_startup_roles_v2.py': '5e9d2e6dfa2aaa7999f4670a979d3cc32736b852a612f77d4e2f7c71bc229618'}
ADMISSION_ENV_KEYS = {'PYTHONPATH', 'PYTHONHOME', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX',
    'PYTHONNOUSERSITE', 'PYTHONSAFEPATH', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD', 'SETUPTOOLS_USE_DISTUTILS',
    'PROBATA_OUTPUT', 'SWDB_VERIFIER_LOCK', 'SWDB_VERIFIER_RSS_CAP_BYTES'}


def H(data): return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(rows):
        result = {}
        for name, value in rows:
            assert name not in result, 'duplicate JSON key'
            result[name] = value
        return result
    def bad(value): raise ValueError('nonfinite JSON constant: ' + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad)


def absolute(value):
    assert type(value) is str and value and Path(value).is_absolute() and str(Path(value)) == value
    assert '..' not in Path(value).parts
    return Path(value)


def relative(value):
    assert type(value) is str and value and not Path(value).is_absolute() and str(Path(value)) == value
    assert all(part not in ('.', '..') for part in Path(value).parts)
    return value


def stable(value):
    return tuple(getattr(value, key) for key in ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


class Physical:
    def __init__(self): self.rows = {}; self.checks = 0
    def pin(self, path, expected=None):
        path = absolute(str(path)); before = path.lstat()
        assert stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path, 'canonical regular input required'
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            assert stable(os.fstat(stream.fileno())) == stable(before)
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            assert stable(os.fstat(stream.fileno())) == stable(before)
        assert stable(path.lstat()) == stable(before), 'input changed during hashing'
        row = {'path': str(path), 'bytes': before.st_size, 'sha256': digest}
        if expected is not None:
            assert type(expected) is dict and set(expected) == {'path', 'bytes', 'sha256'}
            assert type(expected['bytes']) is int and expected['bytes'] >= 0
            assert row == expected, 'physical input pin differs: ' + str(path)
        value = (row, stable(before))
        if str(path) in self.rows: assert self.rows[str(path)] == value, 'physical input changed across reads'
        self.rows[str(path)] = value; self.checks += 1
        return row
    def read(self, row, maximum=2**20):
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        assert type(row['bytes']) is int and 0 <= row['bytes'] <= maximum
        assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256'])
        self.pin(row['path'], row); data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and H(data) == row['sha256'], 'captured bytes differ'
        return data
    def unchanged(self):
        for path, (row, attributes) in self.rows.items():
            assert stable(Path(path).lstat()) == attributes
            self.pin(path, row)


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.truncate', 'os.chmod', 'os.chown', 'os.utime'}:
        raise RuntimeError('passive native cold reader refuses ' + event)
    if event == 'open':
        _path, mode, flags = args
        if mode is not None and any(c in mode for c in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive native cold reader refuses filesystem writes')


def raw_snapshot(raw, expected, physical):
    assert str(raw) == RAW and raw.resolve(strict=True) == raw and not raw.is_symlink()
    assert type(expected) is dict and set(expected) == {'files', 'directories'}
    assert type(expected['files']) is list and type(expected['directories']) is list
    names = []
    for row in expected['files']:
        assert type(row) is dict and set(row) == {'relative', 'bytes', 'sha256'}
        names.append(relative(row['relative']))
        assert type(row['bytes']) is int and row['bytes'] >= 0
        assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256'])
    assert len(names) == len(set(names)) == 62
    assert all(relative(name) == name for name in expected['directories'])
    assert len(set(expected['directories'])) == len(expected['directories'])
    rows, directories = [], []
    for path in sorted(raw.rglob('*')):
        mode = path.lstat().st_mode; name = str(path.relative_to(raw))
        if stat.S_ISDIR(mode): directories.append(name)
        else:
            assert stat.S_ISREG(mode), 'raw link or special input'
            row = physical.pin(path); rows.append({'relative': name, 'bytes': row['bytes'], 'sha256': row['sha256']})
    assert rows == expected['files'] and directories == expected['directories'], 'complete raw census differs'
    assert len(rows) == 62 and sum(row['bytes'] for row in rows) == 9587978
    return {row['relative']: {'path': str(raw / row['relative']), 'bytes': row['bytes'], 'sha256': row['sha256']} for row in rows}


def load_helper(name, files, physical):
    row = files['control/' + name]; assert row['sha256'] == HELPER_PINS[name]
    source = physical.read(row); module = types.ModuleType('passive_native86_' + name[:-3])
    module.__file__ = row['path']; exec(compile(source, row['path'], 'exec'), module.__dict__)
    return module


def passive_entry(source, physical):
    wanted = {'pin', 'recheck', 'physical_runtime', 'make_dependencies', 'link_inputs'}
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert len(nodes) == len(wanted) and {node.name for node in nodes} == wanted
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for root in nodes for node in ast.walk(root))
    context = {'Path': Path, 'hashlib': hashlib, 'json': json, 'os': os, 'stat': stat}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-passive-native-functions>', 'exec'), context)
    context['pin'] = physical.pin
    return context


def result_census(value):
    assert type(value) is dict and set(value) == set(RESULT)
    assert all(type(value[name]) is int and value[name] == wanted for name, wanted in RESULT.items())
    return value


def resource_result(value):
    assert type(value['exit_code']) is int and value['exit_code'] == 0
    assert value['out_of_memory'] is False and value['timed_out'] is False
    assert type(value['peak_rss_bytes']) is int and 0 < value['peak_rss_bytes'] <= 4294967296
    for name in ('wall_seconds', 'cpu_seconds'):
        assert type(value[name]) in (int, float) and math.isfinite(value[name]) and value[name] >= 0
    assert 0 < value['wall_seconds'] <= 180


def recipe(policy, raw):
    compiler = policy['compiler']; command = compiler['command']; out = raw / 'component'; control = raw / 'control'
    rows = []
    for label, language, frozen_language, standard, suffix in (('c11', 'c', 'cpp-output', '-std=c11', '.i'),
            ('cpp17', 'c++', 'c++-cpp-output', '-std=c++17', '.ii')):
        frozen, dep, obj, binary = (out / (label + end) for end in (suffix, '.d', '.o', '.native'))
        rows += [(label + '-preprocess', [*command, '--no-default-config', '-x', language, standard, *FLAGS,
            '-E', '-MD', '-MF', str(dep), '-MT', label, str(control / INPUTS[0]), '-o', str(frozen)], 45),
            (label + '-compile', [*command, '--no-default-config', '-x', frozen_language, standard, *FLAGS, '-c', str(frozen), '-o', str(obj)], 60),
            (label + '-link', [*command, '--no-default-config', *FLAGS, '-fuse-ld=' + compiler['linker']['path'], '-Wl,-t', str(obj), '-o', str(binary)], 45),
            (label + '-run', [str(binary)], 20)]
    return rows


def check_commands(commands, policy, raw, files, physical):
    expected = recipe(policy, raw)
    assert len(commands) == len(expected) == 8
    for row, (name, argv, maximum) in zip(commands, expected):
        assert set(row) == {'name', 'argv', 'cwd', 'timeout_seconds', 'returncode', 'stdout', 'stderr'}
        assert row['name'] == name and row['argv'] == argv and row['cwd'] == str(raw / 'component')
        assert type(row['returncode']) is int and row['returncode'] == 0
        assert type(row['timeout_seconds']) in (int, float) and math.isfinite(row['timeout_seconds']) and 0 < row['timeout_seconds'] <= maximum
        for stream in ('stdout', 'stderr'):
            assert row[stream] == files['component/' + name + '.' + stream]
            assert row[stream]['bytes'] <= 134217728
        if name.endswith('-run'):
            assert row['stderr']['bytes'] == 0 and row['stdout']['bytes'] <= 65536
            result_census(strict_json(physical.read(row['stdout'], 65536)))
    return expected


def artifact_manifest(rows, files):
    expected = {name.removeprefix('component/'): row for name, row in files.items()
                if name.startswith('component/') and name != 'component/artifact-manifest.json'}
    assert len(rows) == len(expected) == 29
    seen = set()
    for row in rows:
        assert type(row) is dict and set(row) == {'relative', 'path', 'bytes', 'sha256'}
        assert type(row['bytes']) is int and row['bytes'] >= 0 and re.fullmatch('[0-9a-f]{64}', row['sha256'])
        name = relative(row['relative']); assert name not in seen; seen.add(name)
        assert {key: row[key] for key in ('path', 'bytes', 'sha256')} == expected[name]
    assert seen == set(expected)


def check_root(root, read, files, policy, command, raw, physical):
    assert root['kind'] == 'native86-v4' and root['raw_root'] == str(raw)
    assert root['raw_files'] == 62 and root['raw_bytes'] == 9587978 and root['manifest_rows_verified'] == 29
    for name, row in root['metadata_pins'].items():
        assert row == files[name] and strict_json(physical.read(row)) == root['actual'][name]
    assert root['artifact_manifest'] == files['component/artifact-manifest.json']
    launch = read('launch.json')
    assert launch['command'] == command['argv'] and launch['source_commit'] == policy['source_commit'] == COMMIT
    assert launch['source'] == str(Path(policy['source_project']).parent)
    assert launch['workers'] == 1 and launch['node'] == 0 and launch['rss_cap_bytes'] == 4294967296 and launch['timeout_seconds'] == 180
    assert launch['reviewed_wrapper_reuse'] == {name: GUARDS[name] for name in ('execute.py', 'watch.py')}
    assert launch['planned_raw_budget_bytes'] == 268435456
    reviewed = read('preflight.json')['reviewed_source_changes']['content']
    assert reviewed['additional_root_guard_review']['sha256'] == GUARD_REVIEW_SHA
    assert reviewed['source_commit'] == COMMIT and reviewed['raw_root'] == str(raw) and reviewed['rss_cap_bytes'] == 4294967296
    staged = reviewed['control_files']; assert len(staged) == len({row['name'] for row in staged}) == 11
    assert {row['name'] for row in staged} == {Path(name).name for name in files if name.startswith('control/')}
    for row in staged:
        assert {key: row[key] for key in ('bytes', 'sha256')} == {key: files['control/' + row['name']][key] for key in ('bytes', 'sha256')}
    for name, digest in GUARDS.items(): assert files[name]['sha256'] == digest
    adaptation = read('root-guard-adaptation.json')
    assert adaptation['rss_cap_bytes'] == 4294967296 and adaptation['timeout_seconds'] == 180
    assert adaptation['run_environment_unset'] == ['LIBRARY_PATH']
    for name, digest in GUARDS.items(): assert adaptation['files'][name]['actual_sha256'] == digest
    for name in ('resources.json', 'outer-resources.json'): resource_result(read(name))
    lane = read('lane.json')['socket_lane']; live = read('native86-linux-role.json')['live']
    assert lane['host'] == 'mbit10' and lane['exit_code'] == 0 and lane['node'] == 0
    assert lane['lease_name'] == live['lease'] == 'mbit10-evaluation-node0'
    assert type(lane['lease_generation']) is int and lane['lease_generation'] == live['generation'] == 612
    assert live['fd9_matches_lease'] is True and live['cpus'] == list(range(0, 64, 2))
    assert live['memory_policy'] == lane['numa_memory_policy'] == 'bind:0'
    assert lane['cpus_allowed_list'] == ','.join(str(value) for value in live['cpus'])
    assert lane['command'] == ['timeout', '--signal=TERM', '--kill-after=60', '300', 'bash', str(raw / 'run.sh')]
    role = read('native86-linux-role.json'); assert role['launch'] == files['launch.json'] and role['Mac_counted_claim'] is False
    marker = H(json.dumps({'launch': files['launch.json'], 'live': live}, sort_keys=True).encode())
    assert role['derived_marker'] == marker
    settlement = root['settlement']
    assert settlement['selected_live_processes'] == [] and type(settlement['proc_read_failures']) is int and settlement['proc_read_failures'] == 0
    leases = settlement['target_and_legacy_leases']; assert set(leases) == {'mbit10-evaluation-node0', 'mbit10-evaluation'}
    for lease in leases.values():
        assert lease['state'] == 'released' and lease['active_session'] is None and lease['attempt_pid'] is None and lease['session_state'] == 'none'
    assert leases['mbit10-evaluation-node0']['lease']['generation'] == 612
    ended = datetime.fromisoformat(lane['ended_utc'].replace('Z', '+00:00'))
    assert datetime.fromisoformat(root['created_utc']) >= ended
    return marker


def check_inputs(groups, observations, inputs, policy, raw, files, physical, helpers):
    assert len(groups) == len(observations) == 2
    source = [files['control/' + name] for name in INPUTS]
    assert inputs['source'] == source and inputs['compiler'] == policy['compiler']
    assert inputs['entry'] == files['control/' + ENTRY[0]] and inputs['policy'] == files['control/' + RUN_POLICY[0]]
    native = {row['path']: row for row in policy['native_runtime']['pins']}
    for name, digest in policy['runtime_files'].items():
        if name in native: assert native[name]['sha256'] == digest
    admitted = set(native) | set(policy['runtime_files'])
    for group, observation, label, suffix in zip(groups, observations, ('c11', 'cpp17'), ('.i', '.ii')):
        assert set(group) == {'dependencies', 'frozen', 'language', 'link_inputs', 'object', 'timing'}
        assert group['language'] == observation['language'] == label and observation['private_native_only'] is True
        result_census(observation['result'])
        for name, row in (('frozen', group['frozen']), ('object', group['object']), ('binary', observation['binary'])):
            end = {'frozen': suffix, 'object': '.o', 'binary': '.native'}[name]
            assert row == files['component/' + label + end]; physical.pin(row['path'], row)
        assert group['timing'] == 'first dependency hashes after original preprocessing; rechecked before and after frozen compilation'
        dependencies = group['dependencies']; assert len({row['path'] for row in dependencies}) == len(dependencies)
        used = helpers['make_dependencies'](physical.read(files['component/' + label + '.d']).decode(), label, raw / 'component')
        assert [row['path'] for row in dependencies] == used and {row['path'] for row in source} <= set(used)
        for row in dependencies: physical.pin(row['path'], row)
        linked = helpers['link_inputs'](physical.read(files['component/' + label + '-link.stdout']).decode(), raw / 'component')
        assert [row['path'] for row in group['link_inputs']] == linked
        assert group['object']['path'] in linked and set(linked) <= admitted | {group['object']['path']}
        for row in group['link_inputs']:
            physical.pin(row['path'], row)
            if row['path'] in native: assert row == native[row['path']]
            elif row['path'] in policy['runtime_files']: assert row['sha256'] == policy['runtime_files'][row['path']]
    return {'languages': 2, 'private_controls_per_language': 86,
            'used_headers': {group['language']: len(group['dependencies']) for group in groups},
            'header_timing': 'first full discovered dependency pins after preprocessing; cold hashes and recorded compile/runtime success do not remove that capture premise'}


def check_environment(inputs, policy, raw, marker):
    out = raw / 'component'
    expected = {'PATH': policy['path'], 'HOME': policy['home'], 'LANG': 'C', 'LC_ALL': 'C', 'TMPDIR': str(out / 'tmp'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': str(out / 'source-cache'),
        'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1:abort_on_error=0:symbolize=0:exitcode=86',
        'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=0', 'PROBATA_OUTPUT': str(raw),
        'SWDB_VERIFIER_LOCK': str(raw / 'verifier.lock'), 'SWDB_VERIFIER_RSS_CAP_BYTES': '4294967296',
        'SWDB_LINUX_REVIEWED_ADMISSION': marker, **policy['native_runtime']['loader_environment']}
    assert inputs['environment'] == expected
    assert not os.path.lexists(raw / 'entry-source-cache') and not os.path.lexists(out / 'source-cache')


def source_closure(policy, read, physical):
    project = absolute(policy['source_project']); root = project.parent
    source = read('source-manifest.json')
    assert len(source) == 220 and all(Path(name).parent == Path('swdb-project/swdb') and name.endswith('.py') for name in source)
    actual = {str(path.relative_to(root)) for path in (project / 'swdb').glob('*.py')}
    assert actual == set(source), 'root metadata source closure changed'
    for name, digest in source.items(): assert physical.pin(root / name)['sha256'] == digest
    assert read('source-after.json') == {'commit': COMMIT, 'source_unchanged': True, 'tracked_changes': ''}
    return {'root_manifest_python_files': 220, 'staged_compiled_sources': 5,
            'commit_boundary': 'Root pinned Git readback/unchanged observation; reader hashes the exact 220-file Python bootstrap closure and five staged compilation sources without executing Git or claiming a whole-repository Git implementation.'}


def audit(policy_path, policy_sha):
    assert __debug__ and not sys.flags.optimize and sys.flags.isolated and sys.dont_write_bytecode
    physical = Physical(); policy_path = absolute(str(policy_path))
    row = physical.pin(policy_path); assert row['sha256'] == policy_sha
    admission = strict_json(physical.read(row))
    assert admission['schema'] == 'native86-passive-cold-policy-1' and admission['admitted'] is True
    reader = admission['reader_admission']; assert reader['admitted'] is True
    assert set(reader['environment']) == ADMISSION_ENV_KEYS and reader['environment']['PYTHONDONTWRITEBYTECODE'] == '1'
    physical.pin(__file__, admission['reader'])
    assert sys.executable == reader['python'] and sys.prefix == reader['prefix'] and sys.base_prefix == reader['base_prefix']
    assert list(sys.path) == reader['initial_sys_path'] and sys.pycache_prefix == reader['pycache_prefix']
    assert all(os.environ.get(name) == value for name, value in reader['environment'].items())
    assert sys.flags.no_user_site == 1 and sys.flags.safe_path is True
    root_row = admission['root_receipt']; assert root_row['sha256'] == ROOT_RECEIPT_SHA
    root = strict_json(physical.read(root_row))
    review_row = admission['guard_review']; assert review_row['sha256'] == GUARD_REVIEW_SHA
    guard_review = strict_json(physical.read(review_row))
    assert guard_review['status'] == 'PASS_STATIC_V9_NARROW_SUCCESSOR'
    assert guard_review['findings'] == []
    assert guard_review['expected_4GiB_guard_files'] == {name: GUARDS[name] for name in ('execute.py', 'watch.py')}
    raw = absolute(admission['raw']); assert str(raw) == RAW
    files = raw_snapshot(raw, admission['raw_snapshot'], physical)
    def read(name): return strict_json(physical.read(files[name]))
    command_row = admission['command']; assert command_row['sha256'] == COMMAND_SHA
    command = strict_json(physical.read(command_row))
    policy = read('control/' + RUN_POLICY[0]); assert files['control/' + RUN_POLICY[0]]['sha256'] == RUN_POLICY[1]
    assert reader['python'] == policy['python']
    assert files['control/' + ENTRY[0]]['sha256'] == ENTRY[1]
    assert policy['entry_sha256'] == ENTRY[1] and policy['source_commit'] == COMMIT and policy['raw_name'] == raw.name
    assert policy['guard_files'] == {name: GUARDS[name] for name in ('execute.py', 'watch.py')}
    assert {Path(name).name for name in files if name.startswith('control/')} == {RUN_POLICY[0], *policy['controller_files']}
    for name, wanted in policy['controller_files'].items():
        assert {key: files['control/' + name][key] for key in ('bytes', 'sha256')} == wanted
    closed, roles = (load_helper(name, files, physical) for name in HELPER_PINS)
    helpers = passive_entry(physical.read(files['control/' + ENTRY[0]]), physical)
    current_runtime = helpers['physical_runtime'](policy, closed)
    assert current_runtime == read('native86-runtime-before.json') == read('native86-runtime-after.json')
    plan = policy['startup_roles']; assert reader['initial_sys_path'] == plan['package_sys_path']
    roles.validate_role_plan_v2(plan, metadata=policy['python_surface_binding'], source_project=Path(policy['source_project']),
        root_observer_bytes=physical.read(files['control/' + policy['root_observer_file']]), closed=closed)
    original_startup = read('native86-python-entry-role.json')
    request = roles.role_request_v2(plan, role='entry-isolated', environment=original_startup['startup_environment'], cache=raw / 'entry-source-cache')
    roles.check_role_observation_v2(request, original_startup)
    marker = check_root(root, read, files, policy, command, raw, physical)
    artifact_manifest(read('component/artifact-manifest.json'), files)
    check_commands(read('component/commands.json'), policy, raw, files, physical)
    inputs = read('component/inputs-before.json'); check_environment(inputs, policy, raw, marker)
    observed = check_inputs(read('component/used-inputs.json'), read('component/observations.json'), inputs, policy, raw, files, physical, helpers)
    result = read('component/result.json')
    assert result['accepted'] is True and result['error'] is None and result['after_input_errors'] == [] and result['bytecode_cache_present'] is False
    assert result['private_native_controls_only'] is True and result['public_proof'] is False and result['current_0_2'] is False and result['full_ticket28'] is False
    assert set(result['controls_by_language']) == {'c11', 'cpp17'}
    for value in result['controls_by_language'].values(): result_census(value)
    assert type(result['wall_seconds']) in (float, int) and math.isfinite(result['wall_seconds']) and 0 < result['wall_seconds'] <= 180
    source = source_closure(policy, read, physical)
    assert helpers['physical_runtime'](policy, closed) == current_runtime
    physical.unchanged(); assert raw_snapshot(raw, admission['raw_snapshot'], physical) == files
    return {'date': '2026-10-16 ET', 'classification': 'PASS_PRIVATE_NATIVE86_COLD_METADATA',
        'raw': str(raw), 'source_commit': COMMIT, 'source': source, 'observations': observed,
        'raw_files': len(files), 'raw_bytes': sum(row['bytes'] for row in files.values()), 'physical_checks': physical.checks,
        'root_receipt_sha256': ROOT_RECEIPT_SHA, 'reader_sha256': admission['reader']['sha256'],
        'cleanup': 'Root finite observation: target/legacy leases released, selected process scan empty and no scan read failures after this run. No continuing absence guarantee.',
        'guard_state': 'Retained successful resource results under exact reviewed guard bytes; no separate raw final-null watchdog field is inferred.',
        'runtime_boundary': 'Physical source/runtime identity and retained private ASan/UBSan behavior only; loader/dlopen and compiler capture timing remain explicit TCB.',
        'compiler_native_verifier_or_child_reexecuted': False, 'raw_payload_transferred': False,
        'public_proof': False, 'source_call_admission': False, 'source_body_proof': False, 'current_0_2': False, 'full_ticket28': False}


if __name__ == '__main__':
    sys.addaudithook(deny)
    if len(sys.argv) != 3: raise SystemExit('usage: admitted isolated Python -I -B READER POLICY SHA256')
    try: print(json.dumps(audit(sys.argv[1], sys.argv[2]), sort_keys=True, indent=2, allow_nan=False))
    except Exception as error:
        print(json.dumps({'classification': 'REFUSED', 'type': type(error).__name__, 'reason': str(error), 'scientific_acceptance': False}, sort_keys=True))
        raise SystemExit(1)
