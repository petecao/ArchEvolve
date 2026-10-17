"""2026-10-16 ET. INERT initialized original-partial pair cold auditor.

Invocation only after independent root source/runtime/reader admission:
  SELECTED_PYTHON -I -B -X pycache_prefix=ABSENT initialized_cold_audit_v6.py POLICY POLICY_SHA256
Print output outside the immutable original raw tree. No child, project import,
compiler, verifier, runtime/config discovery or Git command is permitted.
PyYAML is imported only after the selected isolated reader and closed physical
Python surfaces are checked. Its exact package origin is then checked too.

Opaque Git blob hashes are recomputed from physical bytes against frozen root
consumer rows/OIDs. Root separately owns commit/Git readback and process/lease
settlement. This reader does not implement Git or infer universal process absence.
Success concerns one conditional original partial 711/1107 model observation;
source/model correspondence, portable MMIO, hardware/liveness/current0.2/full28
remain outside the result. New CSV/property classes fail closed.
"""
import ast
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import types
import xml.etree.ElementTree as ET

SOURCE_COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
RUNTIME_CONTROLLER_VERSION = 4
MODULE_PINS = {'closed_python_surface.py': '748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af', 'python_startup_roles_v2.py': '5e9d2e6dfa2aaa7999f4670a979d3cc32736b852a612f77d4e2f7c71bc229618', 'passive_initialized_certificate_rechecker_v2.py': 'd469b5168f4403c36d03fcacee6bce5eb4113ac55670c403b5c4a2a5682dad6e', 'initialized_cold_obligations_v2.py': 'dfc647552f4a1bbfd33cc4745289257a9aca4e8b587ce45ca9aa757066950dc9', 'initialized_cold_identities_v2.py': '0c248fc3b50e69629fed8ab9a187dc5a947cc9aee3fb628aa8d604a6e79c5cc9'}
SELECTION = [
    'tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[correct-initialized-result]',
    'tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[wrong-crossregister-result]',
]
REPORTS = {'c_lowering', 'anchors', 'wp_input', 'wp_log', 'wp_goals', 'wp_properties', 'wp_inventory', 'wp_normalized'}
KERNEL_META = {'path': '/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c/META', 'bytes': 2318,
               'sha256': '1d41605b5220bc71779ffac319ff9b06950245f5eab9f61894e865ddd9658002'}
H = lambda value: hashlib.sha256(value).hexdigest()


def strict_json(text):
    def pairs(rows):
        result = {}
        for name, value in rows:
            assert name not in result, 'duplicate JSON key'
            result[name] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant refused: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def safe_yaml(yaml, text):
    class UniqueSafeLoader(yaml.SafeLoader):
        pass
    def mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            assert key not in result, 'duplicate YAML key'
            result[key] = loader.construct_object(value_node, deep=deep)
        return result
    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    return yaml.load(text, Loader=UniqueSafeLoader)


def digest(value):
    return H(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def deny_children(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('passive initialized cold reader refuses ' + event)


def absolute(value):
    assert type(value) is str and value.startswith('/') and os.path.normpath(value) == value and '\0' not in value
    return Path(value)


def relative(value):
    assert type(value) is str and value and str(Path(value)) == value and not Path(value).is_absolute()
    assert all(part not in ('', '.', '..') for part in Path(value).parts)
    return value


def stable_stat(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class Physical:
    """Stream physical hashes; keep metadata, never whole catalog/file contents."""
    def __init__(self):
        self.files = {}
        self.checks = 0

    def pin(self, path, expected=None, size=None):
        path = Path(path)
        before = path.lstat()
        assert stat.S_ISREG(before.st_mode), 'regular physical input required: ' + str(path)
        result = hashlib.sha256()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            assert stable_stat(opened) == stable_stat(before), 'input changed while opening'
            for block in iter(lambda: stream.read(1048576), b''):
                result.update(block)
            after = os.fstat(stream.fileno())
        final = path.lstat()
        assert stable_stat(before) == stable_stat(after) == stable_stat(final), 'input changed while hashing'
        value = result.hexdigest()
        assert expected is None or value == expected, 'physical hash differs: ' + str(path)
        assert size is None or final.st_size == size, 'physical byte count differs: ' + str(path)
        row = {'sha256': value, 'bytes': final.st_size, 'stat': stable_stat(final)}
        if str(path) in self.files:
            assert self.files[str(path)] == row, 'input changed across passive reads'
        self.files[str(path)] = row
        self.checks += 1
        return value

    def pinned(self, row):
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        absolute(row['path'])
        assert type(row['bytes']) is int and row['bytes'] >= 0
        assert re.fullmatch('[a-f0-9]{64}', row['sha256'])
        return self.pin(row['path'], row['sha256'], row['bytes'])

    def read(self, row):
        self.pinned(row)
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and H(data) == row['sha256'], 'input changed while capturing selected small data'
        return data

    def unchanged(self):
        for name, row in self.files.items():
            assert stable_stat(Path(name).lstat()) == row['stat'], 'physical source/runtime/evidence metadata changed'


def raw_snapshot(raw, physical):
    files, links = {}, {}
    assert raw.is_dir() and not raw.is_symlink() and raw.resolve() == raw
    for path in sorted(raw.rglob('*')):
        name = str(path.relative_to(raw)); mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            # Alias links are inventoried literally; evidence inputs themselves
            # must be physical files and cannot silently follow these aliases.
            links[name] = {'target': os.readlink(path)}
        elif stat.S_ISREG(mode):
            files[name] = {'sha256': physical.pin(path), 'bytes': path.stat().st_size}
        else:
            assert stat.S_ISDIR(mode), 'special raw member'
    assert 1 <= len(files) <= 20000 and sum(row['bytes'] for row in files.values()) <= 8589934592
    return {'files': files, 'symlinks': links}


def load_reviewed_modules(policy, physical):
    assert set(policy['reader_files']) == set(MODULE_PINS)
    result = {}
    for name, expected in MODULE_PINS.items():
        row = policy['reader_files'][name]
        assert row['sha256'] == expected and Path(row['path']).name == name
        source = physical.read(row)
        module = types.ModuleType('closed_cold_' + name[:-3])
        module.__file__ = row['path']
        exec(compile(source, row['path'], 'exec'), module.__dict__)
        result[name] = module
    return result


def admit_reader(policy, expected, closed, physical):
    admission = policy['reader_admission']
    assert admission['admitted'] is True and admission['role'] == 'isolated-passive-cold-reader'
    assert sys.flags.isolated == sys.flags.no_user_site == 1 and sys.flags.safe_path is True
    assert not sys.flags.optimize and sys.dont_write_bytecode is True
    metadata = expected['python_surface_binding']
    receipt = closed.verify_python_metadata(metadata)
    interpreter = metadata['interpreter']
    assert sys.executable == interpreter['path'] == expected['linux_launch_binding']['python']
    physical.pinned(interpreter['target_pin'])
    assert closed._resolution(absolute(sys.executable), interpreter['chain']) == absolute(interpreter['resolved'])
    paths = expected['startup_roles']['package_sys_path']
    assert len(paths) == len(set(paths)) == 7 and list(sys.path) == paths == admission['sys_path']
    assert sys.prefix == expected['startup_roles']['prefix'] and sys.base_prefix == expected['startup_roles']['base_prefix']
    environment_names = {'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE',
                         'PYTHONSAFEPATH', 'SETUPTOOLS_USE_DISTUTILS'}
    assert set(admission['environment']) == environment_names
    for name in sorted(environment_names):
        assert os.environ.get(name) == admission['environment'][name]
    assert sys.pycache_prefix == admission['pycache_prefix']
    assert not os.path.lexists(absolute(admission['pycache_prefix']))
    assert not any(name.startswith('PYTHON') and name not in admission['environment'] for name in os.environ)
    # Only the explicitly selected YAML parser enters this passive reader.
    import site
    assert site.ENABLE_USER_SITE is False
    import yaml
    wanted = expected['startup_roles']['module_origins']['yaml']
    assert str(Path(yaml.__file__).resolve()) == wanted['path'] and yaml.__spec__.origin == wanted['spec_origin']
    physical.pin(wanted['path'], wanted['sha256'])
    assert list(sys.path) == paths and site.ENABLE_USER_SITE is False
    return yaml, receipt


def source_membership(project, expected):
    found = set()
    for name in expected['source_consumer_trees']:
        root = project / relative(name)
        for path in ([root] if root.is_file() else root.rglob('*')):
            mode = path.lstat().st_mode
            assert stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'consumer symlink/special member'
            if stat.S_ISREG(mode): found.add(str(path.relative_to(project)))
    return found


def complete_source(policy, expected, raw, project, physical):
    assert expected['source_commit'] == policy['source_commit'] == SOURCE_COMMIT
    assert len(expected['source_files']) == 496 and len(expected['source_consumer_trees']) == 11
    assert all(re.fullmatch('[a-f0-9]{40}', row['oid']) for row in expected['source_consumer_trees'].values())
    receipts = [strict_json((raw / name).read_text()) for name in (
        'initialized-source-consumer-closure-before.json', 'initialized-source-consumer-closure-after-bootstrap.json',
        'initialized-source-consumer-closure-after.json')]
    assert receipts[0] == receipts[1] == receipts[2]
    assert digest(receipts[0]) == policy['source_consumer_receipt_sha256']
    receipt = receipts[0]
    assert receipt['source_commit'] == SOURCE_COMMIT and receipt['trees'] == expected['source_consumer_trees']
    assert receipt['physical_git_blob_equality'] is True
    rows = receipt['files']; assert len(rows) == receipt['count'] == len({row['relative'] for row in rows})
    assert receipt['total_bytes'] == sum(row['bytes'] for row in rows)
    found = source_membership(project, expected)
    assert found == {row['relative'] for row in rows}, 'complete source consumer membership differs'
    source_stats = {}
    for row in rows:
        path = project / relative(row['relative'])
        assert str(path) == row['path']
        before = path.lstat(); assert stat.S_ISREG(before.st_mode)
        sha = hashlib.sha256(); blob = hashlib.sha1(('blob ' + str(before.st_size) + '\0').encode())
        with path.open('rb') as stream:
            assert stable_stat(os.fstat(stream.fileno())) == stable_stat(before)
            for block in iter(lambda: stream.read(1048576), b''):
                sha.update(block); blob.update(block)
        after = path.lstat(); assert stable_stat(before) == stable_stat(after)
        assert row['bytes'] == after.st_size and row['sha256'] == sha.hexdigest() and row['git_blob'] == blob.hexdigest()
        source_stats[str(path)] = stable_stat(after)
    for name, digest_value in expected['source_files'].items():
        # Already-hashed consumer rows bind selected files without a second
        # 1.3-GiB catalog content scan. Selected files outside them stream once.
        matches = [row for row in rows if row['relative'] == name]
        if matches: assert len(matches) == 1 and matches[0]['sha256'] == digest_value
        else: physical.pin(project / relative(name), digest_value)
    assert strict_json((raw / 'source-after.json').read_text()) == {
        'commit': SOURCE_COMMIT, 'source_unchanged': True, 'tracked_changes': ''}
    return {'receipt': receipt, 'source_stats': source_stats,
            'boundary': 'physical SHA256/opaque Git blob equality against root-pinned rows/OIDs; root separately owns actual commit/Git readback'}


def pure_runtime_helpers(entry_source, physical):
    """Compile exactly two reviewed pure AST functions; never execute entry main."""
    hashes = {'import_surface': '37332570894eae61fb41b21d7726f61c08f98f1ded38b85f2181eebb08e3c1c8',
              'header_surface_check_v4': 'a0c64a9458961cd997c8314a45f469e2e9eaa88cbeee8f7e75b634d6dd00c5aa'}
    selected = set(hashes)
    tree = ast.parse(entry_source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in selected]
    assert len(functions) == len(selected) and {node.name for node in functions} == selected
    for node in functions:
        assert H(ast.get_source_segment(entry_source, node).encode()) == hashes[node.name], 'unreviewed pure runtime helper'
    # The complete staged entry is independently pinned by original admission.
    namespace = dict(hashlib=hashlib, json=json, os=os, pathlib=__import__('pathlib'), Path=Path, stat=stat,
                     pin=lambda path: {'path': str(Path(path).resolve()), 'sha256': physical.pin(path)})
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<reviewed-pure-runtime-helpers>', 'exec'), namespace)
    return namespace


def runtime_closure(expected, closed, helpers, physical):
    for path, value in expected['runtime_files'].items(): physical.pin(path, value)
    assert expected['runtime_files'][KERNEL_META['path']] == KERNEL_META['sha256']
    physical.pinned(KERNEL_META)
    for row in expected['tools'].values():
        path = closed._resolution(absolute(row['path']), expected['python_surface_binding']['interpreter']['chain']) if row['path'] == expected['python_surface_binding']['interpreter']['path'] else closed._resolution(absolute(row['path']), [])
        physical.pin(path, row['sha256'])
    for path, value in expected['wp_artifacts'].items(): physical.pin(path, value)
    physical.pin(expected['config']['path'], expected['config']['sha256'])
    prefix = Path(expected['tools']['frama-c']['path']).parent.parent
    portable = {name: helpers['import_surface'](root, expected['portable_import_surfaces'][name]) for name, root in (
        ('why3_stdlib', prefix / 'share/why3/stdlib'), ('wp_why3_support', prefix / 'share/frama-c/share/wp/why3'),
        ('why3_drivers', prefix / 'share/why3/drivers'))}
    packages = {}
    for name, directory in expected['ocaml_packages'].items():
        root = Path(directory)
        wanted = [{'relative': str(Path(path).relative_to(root)), 'sha256': value}
                  for path, value in expected['runtime_files'].items() if Path(path).is_relative_to(root)]
        wanted.sort(key=lambda row: Path(row['relative']).parts)
        assert wanted
        packages[name] = helpers['import_surface'](root, wanted)
    headers = helpers['header_surface_check_v4'](expected['linux_header_surfaces'], expected['linux_clang_components']['headers'], closed)
    parser = expected['linux_clang_components']['parser']['sha256']
    paths = [path for path, value in expected['runtime_files'].items() if value == parser]
    assert len(paths) == 1 and Path(paths[0]).name == 'libclang.so.22.1.8'
    physical.pin(paths[0], parser)
    return {'portable': portable, 'packages': packages, 'headers': headers, 'parser': paths[0]}


def original_launch(policy, expected, raw, physical):
    entry, source_policy = policy['original_entry'], policy['source_policy']
    physical.pinned(entry); physical.pinned(source_policy)
    assert Path(entry['path']).parent == Path(source_policy['path']).parent == raw / 'control'
    launch = strict_json((raw / 'launch.json').read_text())
    wanted = [expected['tools']['opam']['path'], 'exec', '--switch=framac-33', '--',
              expected['linux_launch_binding']['python'], '-I', '-B', entry['path'], str(policy['project']),
              str(raw), source_policy['path'], source_policy['sha256']]
    assert launch['command'] == wanted and launch['source_commit'] == SOURCE_COMMIT
    assert Path(launch['source']) == Path(policy['project']).parent
    assert launch['node'] == expected['linux_launch_binding']['node'] and launch['workers'] == 1
    assert launch['rss_cap_bytes'] == 8589934592 and launch['timeout_seconds'] == 1200
    assert expected['linux_launch_binding']['entry_sha256'] == entry['sha256']
    names = set(expected['controller_files']) | {Path(entry['path']).name, Path(source_policy['path']).name}
    assert {path.name for path in (raw / 'control').iterdir()} == names
    for path in (raw / 'control').iterdir(): assert stat.S_ISREG(path.lstat().st_mode)
    for name, value in expected['controller_files'].items():
        assert set(value) == {'bytes', 'sha256'}
        physical.pin(raw / 'control' / name, value['sha256'], value['bytes'])
    for name, value in expected['linux_launch_binding']['wrappers'].items():
        assert launch['reviewed_wrapper_reuse'][name] == value
        physical.pin(raw / name, value)
    resources = {name: strict_json((raw / name).read_text()) for name in ('resources.json', 'outer-resources.json')}
    for name, row in resources.items():
        assert row['exit_code'] == 0 and row['out_of_memory'] is row['timed_out'] is False
        assert type(row['peak_rss_bytes']) is int and 0 < row['peak_rss_bytes'] < 8589934592
        assert type(row['wall_seconds']) in (int, float) and math.isfinite(row['wall_seconds'])
        assert 0 < row['wall_seconds'] < (1320 if name == 'outer-resources.json' else 1200)
    lane = strict_json((raw / 'lane.json').read_text())['socket_lane']
    assert lane == policy['settled_lane'] and lane['node'] == expected['linux_launch_binding']['node']
    validate_original_lane_v3(policy, expected, raw, physical, lane)
    return {'command': wanted, 'resources': resources, 'lane': lane,
            'settlement_boundary': 'root supplies independent finite process/lease settlement; no universal process-absence inference'}


def validate_original_lane_v3(policy, expected, raw, physical, lane):
    # Exact root-observed identity; a job label need not equal a raw basename.
    receipt_pin = policy['original_root_receipt']
    assert set(receipt_pin) == {'path', 'bytes', 'sha256'}
    assert receipt_pin['bytes'] == 5623
    assert receipt_pin['sha256'] == '832980ed68bdcd9654e82e9e6e33debdf8021054a7e7e03f8dfb794e86754665'
    root = strict_json(physical.read(receipt_pin))
    assert str(raw) == root['raw_root'] == '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5'
    assert expected['source_commit'] == SOURCE_COMMIT == '04af74c121a733589fbe1a2087ad602deaef598b'
    assert root['actual']['source-after.json'] == {'commit': SOURCE_COMMIT, 'source_unchanged': True, 'tracked_changes': ''}
    assert lane == root['actual']['lane.json']['socket_lane'] == policy['settled_lane']
    assert lane['exit_code'] == 0 and lane['node'] == expected['linux_launch_binding']['node'] == 0
    assert lane['job'] == 'probata-resume-20261016-04af74c1-t28-initialized-pair-v5'
    assert lane['lease_generation'] == 613


def startup_and_runtime_receipts(expected, raw, project, roles, closed, physical):
    plan = expected['startup_roles']
    observer_path = raw / 'control' / expected['root_observer_file']
    observer_bytes = observer_path.read_bytes()
    assert H(observer_bytes) == plan['root_observer_sha256']
    provenance = roles.validate_role_plan_v2(plan, metadata=expected['python_surface_binding'], source_project=project,
                                           root_observer_bytes=observer_bytes, closed=closed)
    assert strict_json((raw / 'initialized-python-role-plan.json').read_text()) == provenance
    role_receipts = {}
    for role in ('entry-isolated', 'pytest-child'):
        data = strict_json((raw / ('initialized-python-' + role + '.json')).read_text())
        assert data['role'] == role and data['exit_code'] == 0 and data['stderr'] == ''
        assert data['observer_source_sha256'] == expected['controller_files']['python_role_observer_v2.py']['sha256']
        cache = raw / ('bootstrap-source-cache' if role == 'entry-isolated' else 'initialized-profile/source-cache')
        env = data['request']['startup_environment']
        assert env['PYTHONPYCACHEPREFIX'] == str(cache) and env['PYTHONDONTWRITEBYTECODE'] == '1'
        if role == 'pytest-child':
            wanted = roles.startup_projection_v2(roles.child_environment_v2({}, project=project,
                                                 raw=raw / 'initialized-profile', cache=cache))
            assert env == wanted
        else:
            assert env['PROBATA_OUTPUT'] == str(raw) and env['SWDB_VERIFIER_LOCK'] == str(raw / 'verifier.lock')
            assert env['SWDB_VERIFIER_RSS_CAP_BYTES'] == '8589934592'
        request = roles.role_request_v2(plan, role=role, environment=env, cache=cache)
        assert request == data['request']
        flags = ['-I'] if role == 'entry-isolated' else []
        assert data['argv_prefix'] == [expected['linux_launch_binding']['python'], *flags,
                                      '-B', '-X', 'pycache_prefix=' + str(cache), '-c']
        observed = strict_json(data['stdout'])
        receipt = roles.check_role_observation_v2(request, observed)
        assert receipt == strict_json((raw / ('initialized-python-' + role + '-accepted.json')).read_text())
        role_receipts[role] = receipt
    before, startup, after = [strict_json((raw / ('initialized-runtime-' + label + '.json')).read_text())
                              for label in ('before', 'after-startup', 'after')]
    assert before == startup == after, 'complete original runtime receipts changed'
    assert before['runtime_files'] == expected['runtime_files']
    assert before['python']['policy_sha256'] == plan['physical_metadata_sha256']
    assert before['python']['before_after_equal'] is True
    for path in (raw / 'bootstrap-source-cache', raw / 'initialized-profile/source-cache'):
        assert not os.path.lexists(path)
    return {'plan': provenance, 'roles': role_receipts, 'original_runtime_before_after_equal': True}


def validate_compiler_descriptor_v4(name, row, expected):
    # Runtime identity has component bytes, not a version scalar. The two
    # retained producers expose their version through distinct exact metadata.
    assert set(row['runtime']) == {'check', 'command', 'command_executable', 'driver', 'frontend', 'headers', 'parser'}
    wanted = dict(expected['linux_clang_components'])
    assert row['lowering_identity']['clang'] == {'id': 'clang-22.1.8', 'sha256': wanted['command_executable']['sha256']}
    if name == 'runtime-provenance.json':
        assert set(row) == {'runtime', 'lowering_identity', 'tool'}
        assert row['tool'] == {'command': ['clang++'], 'version': '22.1.8', 'missing': ''}
        # The immutable bootstrap receipt predates the reviewed normalization.
        # Its physical wrapper/driver/parser/header pins must still match.
        wanted['command'] = ['clang++']
    else:
        assert name == 'initialized-project-runtime-provenance.json'
        assert set(row) == {'accepted_linux_components', 'admission_basis', 'cold_audit_requirement', 'cwd',
                            'lowering_identity', 'reporter', 'retained_basis', 'runtime', 'scope'}
        assert row['accepted_linux_components'] == wanted
    assert all(row['runtime'][key] == value for key, value in wanted.items())
    return wanted


def project_contexts(expected, raw, project, identities):
    contexts = {}
    for name in ('runtime-provenance.json', 'initialized-project-runtime-provenance.json'):
        row = strict_json((raw / name).read_text()); runtime = row['runtime']
        runtime_components = validate_compiler_descriptor_v4(name, row, expected)
        if name == 'initialized-project-runtime-provenance.json': assert row['cwd'] == str(project)
        derived = identities.source_identity(project, runtime)
        assert row['lowering_identity']['c_lowering']['sha256'] == derived['sha256']
        assert row['lowering_identity']['naming_rules'] == expected['naming']
        assert all(runtime[key] == value for key, value in runtime_components.items())
        contexts[name] = {'lowering': row['lowering_identity'], 'compiler': runtime,
                          'independent_lowerer_identity': derived}
    current = contexts['initialized-project-runtime-provenance.json']
    profile = strict_json((raw / 'initialized-profile/runtime-provenance.json').read_text())
    assert profile['compiler'] == current['compiler'] and profile['lowering'] == current['lowering']
    assert profile['checks'] == identities.checkers_identity(project)
    assert profile['actual_initialized_lineup'] == expected['actual_initialized_lineup'] == identities.LINEUP
    selected = strict_json((raw / 'selected-initialized-tool-metadata.json').read_text())
    assert selected['source_commit'] == SOURCE_COMMIT and selected['source_files'] == expected['source_files']
    assert selected['actual_initialized_lineup'] == identities.LINEUP and selected['ambient_wp_names'] == []
    assert selected['config'] == expected['config'] and selected['reporter'] == expected['reporter']
    assert set(selected['packages']) == set(expected['ocaml_packages'])
    for name, package in selected['packages'].items():
        assert package == {'path': expected['ocaml_packages'][name], 'accepted': True, 'exit_code': 0}
    for name, tool in expected['tools'].items():
        assert selected['tools'][name]['sha256'] == tool['sha256']
        assert Path(selected['tools'][name]['path']).resolve() == Path(tool['path']).resolve()
    return contexts


def workflow(expected, raw):
    profile = raw / 'initialized-profile'
    assert strict_json((raw / 'initialized-collection.json').read_text()) == {
        'cwd': expected['startup_roles']['source_project'], 'expected': SELECTION, 'selected': SELECTION, 'exit_code': 0}
    assert (raw / 'initialized-runner-exit-code.txt').read_text() == '0\n'
    assert (profile / 'selected-tests.txt').read_text().splitlines() == SELECTION
    assert (profile / 'profile.txt').read_text() == 'pair\n'
    assert (profile / 'exit-code.txt').read_text() == '0\n'
    assert (profile / 'source-commit.txt').read_text() == SOURCE_COMMIT + '\n'
    root = ET.parse(profile / 'junit.xml').getroot()
    suites, cases = list(root.iter('testsuite')), list(root.iter('testcase'))
    assert root.tag == 'testsuites' and len(list(root.iter('testsuites'))) == len(suites) == 1
    assert suites[0].get('tests') == '2' and len(cases) == 2
    assert all(suites[0].get(name) == '0' for name in ('errors', 'failures', 'skipped'))
    assert all(not list(root.iter(name)) for name in ('error', 'failure', 'skipped'))
    assert {case.get('name') for case in cases} == {name.split('::')[-1] for name in SELECTION}
    assert all(case in list(suites[0]) and case.get('classname') == 'tests.test_dx100_initialized_register_actual' for case in cases)
    assert strict_json((profile / 'junit-census.json').read_text())['accepted'] is True
    return {'tests': 2, 'errors': 0, 'failures': 0, 'skipped': 0,
            'scope': 'workflow only; complete native/source record audit is separate'}


def initialized_rules(semantics, record, sempin, lowerer, expected, project, certificates):
    tree = ast.parse((project / 'tests/testkit/dx100_trust.py').read_text())
    trust = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and
                 any(isinstance(target, ast.Name) and target.id == 'TRUST' for target in node.targets))
    assert len(trust) == 5
    required = dict(trust, register_scope=certificates.STATEMENT)
    rules = {row['id']: row for row in semantics['rules']}
    assert len(rules) == len(semantics['rules']) and set(rules) == set(required) | {'register_source'}
    wanted = []
    for name, sentence in required.items():
        assert rules[name] == {'id': name, 'statement': sentence, 'record_assumption': True,
                               'assumed': {'owner': 'Eric' if name == 'no_stale_cpu_copy' else certificates.OWNER}}
        wanted.append({'kind': 'proof_semantics', 'reference': {'id': sempin['id'] + '#' + name,
                       'sha256': sempin['sha256']}, 'sentence': sentence})
    assert rules['register_source'] == {'id': 'register_source',
        'statement': 'Typed CPU scalar writes are queued; dispatch updates RF before its response. A scalar read copies the selected RF bytes. IF stalls register writes only on matching explicit IDs.',
        'cites': {'gem5_commit': 'e4fc4afdf894f295442cef3604667a469fab8e62', 'path': 'src/mem/MAA/CpuSidePort.cc', 'lines': '112-150,317-332'}}
    wanted.append({'kind': 'proof_semantics', 'reference': sempin, 'sentence': certificates.STATEMENT})
    got = [row for row in record['assumptions'] if row['kind'] == 'proof_semantics']
    assert Counter(map(digest, got)) == Counter(map(digest, wanted))
    assert {row['kind'] for row in record['assumptions']} == {'trusted_tool', 'proof_semantics', 'assumed_clause'}
    trusted = [row for row in record['assumptions'] if row['kind'] == 'trusted_tool']
    wanted_tools = {lowerer['c_lowering']['id']: lowerer['c_lowering']['sha256'], lowerer['clang']['id']: lowerer['clang']['sha256']}
    for name, version in {'frama-c-wp': '33.0', 'z3': '5.1.0', 'cvc5': '1.2.1', 'alt-ergo': '2.6.4'}.items():
        wanted_tools[name + '-' + version] = expected['tools']['frama-c' if name == 'frama-c-wp' else name]['sha256']
    assert len(trusted) == len(wanted_tools)
    assert {row['reference']['id']: row['reference']['sha256'] for row in trusted} == wanted_tools
    return {'owned_rules': len(required), 'trusted_tools': len(trusted), 'source_model_agreement': 'owned unverified TCB duty'}


def semantic_model(semantics, library, project, certificates, physical):
    assert semantics['id'] == certificates.SEMANTICS_ID and semantics['version'] == '0.2'
    assert semantics['model']['layout'] == certificates.LAYOUT
    assert semantics['constants'] == {} and semantics['queries'] == [] and semantics['wp'] == {}
    manifest = strict_json((project / 'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json').read_text())
    assert semantics['declaration_inventory'] == {name: manifest[name] for name in ('sources', 'declarations')}
    assert semantics['inventory'] == {'sources': manifest['sources'], 'calls': sorted({row['name'] for row in manifest['declarations']})}
    calls = {row['call']: row for row in semantics['calls']}
    assert len(calls) == len(semantics['calls']) and set(calls) == set(semantics['inventory']['calls'])
    active = {name for name, row in calls.items() if row.get('supported') is not False}
    assert active == set(certificates.PROTOTYPES)
    for name, row in calls.items():
        assert row['rules'] == ['register_scope', 'register_source']
        if name not in active:
            assert row['supported'] is False and row['contract'] == r'requires \false; assigns \nothing;'
            continue
        if name == 'init_MAA': variants = [row]
        else:
            variants = row['instances']
            assert len(variants) == (2 if name == 'get_new_reg' else 1)
            if name == 'get_new_reg':
                assert variants[1] == {'arguments': ['unsigned int'], 'arity': 0, 'declaration': 'inline int get_new_reg()',
                    'prototype': 'int get_new_reg_unsigned_int_args0(void)', 'contract': r'requires \false; assigns \nothing;'}
            variants = variants[:1]
        variant = variants[0]
        assert variant['prototype'] == certificates.PROTOTYPES[name] and variant['contract'] == certificates.CONTRACTS[name]
        if name != 'init_MAA': assert variant['arguments'] == ['unsigned int'] and variant['arity'] == 1
        definition = variant['definition']
        assert definition['kind'] == certificates.KIND and definition['call'] == name and definition['entry'] == certificates.ENTRY
        assert {Path(pin['path']).name: pin['sha256'] for pin in definition['sources']} == certificates.SOURCE_PINS
    for group, name, wanted in [('model', 'state', certificates.STATE), ('model', 'c', certificates.MODEL),
                               ('model', 'logic', '/* No added axioms. */\n'),
                               ('ghost', 'acsl', '/* Ordinary register-word projection. */\n')]:
        row = semantics[group][name]
        assert row['root'] == 'library'
        path = library / relative(row['path']); physical.pin(path, row['sha256'])
        assert path.read_text() == wanted
    return {'active_calls': sorted(active), 'all_other_inventory_calls_refused': True,
            'model_bytes_exact': True, 'zero_queries': True, 'added_axioms': False}


def certificate_runtime_descriptor_v5(compiler, lowerer, physical):
    # A certificate's driver is the producer's _pin(command[0]), the selected
    # wrapper. stdlib runtime.driver independently names the underlying clang.
    assert set(compiler) == {'check', 'command', 'command_executable', 'driver', 'frontend', 'headers', 'parser'}
    selected = compiler['command_executable']
    assert compiler['command'] == [selected['path']] and Path(selected['path']).is_absolute()
    assert selected['sha256'] == '3c053dce26cf5ef22656f1ec9efe0cdf2911a37d5a910261895ac9c42e128fe4'
    assert lowerer['clang'] == {'id': 'clang-22.1.8', 'sha256': selected['sha256']}
    assert compiler['driver']['path'] != selected['path']
    driver = {'path': selected['path'], 'bytes': 145, 'sha256': selected['sha256']}
    physical.pinned(driver)
    return {'command': list(compiler['command']), 'version': lowerer['clang']['id'].removeprefix('clang-'), 'driver': driver}


def audit_record(row, *, expected, raw, project, compiler, lowerer, modules, yaml, physical, references):
    certs = modules['passive_initialized_certificate_rechecker_v2.py']
    obligations = modules['initialized_cold_obligations_v2.py']
    identities = modules['initialized_cold_identities_v2.py']
    assert set(row) == {'expected_result', 'record', 'id'} and type(row['expected_result']) is int
    number = row['expected_result']; assert number in (711, 1107)
    record_path = absolute(row['record']['path']); physical.pinned(row['record'])
    assert raw in record_path.parents and record_path.parent.name == 'proofs' and record_path.parent.parent.name == 'records'
    fixture = record_path.parent.parent.parent; library = fixture / 'library'
    assert [path for path in record_path.parent.iterdir() if path.is_file()] == [record_path]
    record = safe_yaml(yaml, record_path.read_text())
    assert record['id'] == row['id'] and record['kind'] == 'proof' and record['schema_version'] == '0.4'
    assert record['evidence_kind'] == 'contract_fixture' and record['bounds'] == {'threads': 1, 'input_size': 'unbounded'}
    assert record['verdict'] == ('proven' if number == 711 else 'not_proven')
    assert 'counterexample' not in record and 'unreplayed_counterexample' not in record
    settings, pins, setup = record['settings'], record['pins'], record['proof_setup_check']
    assert pins['summaries'] == [] and pins['build_constants'] == [] and pins['naming_rules'] == expected['naming']
    checker = identities.checkers_identity(project)
    assert setup['verdict'] == 'passed' and setup['check'] == checker['proof_setup_check']
    assert setup['method_version'] == pins['method_version']
    assert record['verdict_reading'] == {'check': checker['verdict_reading'], 'verdict': record['verdict']}
    assert settings['compiler_runtime'] == compiler and settings['verifier_launched'] is True
    assert settings['rss_cap_bytes'] == 8589934592 and settings['wp_seconds_per_solver'] == 30
    assert settings['session'] == 'fresh' and settings['hint_count'] == 0 and settings['warning_levels'] == 'default'
    assert settings['build_constants'] == []
    assert settings['machdep'] == 'x86_64' and settings['environment_removed'] == []
    methodfile = library / 'methods/dx100-initialized-register-partial-fixture-v1.yaml'
    method = safe_yaml(yaml, methodfile.read_text())
    assert pins['method_version'] == {'id': certs.PARTIAL_METHOD, 'sha256': physical.pin(methodfile)}
    assert method == identities.expected_fixture_method(project, checker, lowerer, expected['naming'])
    flags = next(tool['flags'] for tool in method['lineup'] if tool['tool'] == 'frama-c-wp')
    assert settings['flags'] == [*flags, '-machdep', 'x86_64', '-wp-timeout', '30', '-wp-par', '1', '-wp-smoke-tests']
    semfile = library / 'proof_semantics/dx100_trust_fixture.yaml'
    sempin = {'id': certs.SEMANTICS_ID, 'sha256': physical.pin(semfile)}
    assert pins['proof_semantics'] == sempin
    semantics = safe_yaml(yaml, semfile.read_text())
    model = semantic_model(semantics, library, project, certs, physical)
    definitions = settings['proof_semantics']['source_definitions']
    assert settings['proof_semantics']['calls'] == sorted(certs.PROTOTYPES)
    assert settings['proof_semantics']['probes'] == [] and 'entry_projection' not in settings['proof_semantics']
    assert settings['proof_semantics']['source_refinement'] == 'owned initialized source/model contract-body and disjoint-address TCB duties pending59; compiler observations not a theorem'
    reports = obligations.unique(record['evidence']['reports'], 'name')
    assert set(reports) == REPORTS | ({'handler'} if number == 1107 else set()), 'unexpected/missing evidence class requires source review'
    for evidence in [record['evidence']['adapter_log'], *reports.values()]:
        path = absolute(evidence['path']); assert raw in path.parents
        physical.pin(path, evidence['sha256'])
    wp = Path(reports['wp_input']['path']); text = wp.read_text()
    scratch = obligations.retained_wp_input_path(wp)
    assert not os.path.lexists(scratch.parent), 'completed original job scratch must remain removed'
    runtime = certificate_runtime_descriptor_v5(compiler, lowerer, physical)
    checked = certs.verify_initialized_record(record, project=project, expected_runtime=runtime,
                                              expected_result=number, wp_input_text=text)
    query = obligations.initialized_wp_source(text, number, references)
    canonical = '#include ' + json.dumps(str(project / 'apps/dx100/benchmarks/API/MAA_gem5.hpp')) + '\n' + certs.CALLER
    sources = {definition['source_path'] for definition in definitions}
    assert len(sources) == 1
    for definition in definitions:
        for pin in [*definition['sources'], *definition['compiler_inputs'], definition['runtime_identity']['driver']]:
            physical.pinned(pin)
    source = Path(next(iter(sources))); physical.pin(source)
    assert source.read_text() == canonical
    inventory = strict_json(Path(reports['wp_inventory']['path']).read_text())
    native = strict_json(Path(reports['wp_goals']['path']).read_text())
    csvrows = obligations.csv_properties(Path(reports['wp_properties']['path']).read_text())
    goals = obligations.current_goals(record, inventory, native, csvrows, scratch)
    goals['dependency_DAG'] = obligations.dependency_DAG(inventory)
    assert goals['healthy_negative'] is (number == 1107)
    if number == 1107:
        handler = strict_json(Path(reports['handler']['path']).read_text())
        vocabulary = safe_yaml(yaml, (project / 'vocab/proof_failure_classes.yaml').read_text())
        # The selected handler body and its exact vocabulary text are source
        # inputs. Native unknown/timeout remains nonproof, never a refutation.
        assert handler['failure_class'] == record['failure_class']
        assert handler['handler'] == next(value['handler'] for value in vocabulary['values'] if value['value'] == record['failure_class'])
        assert handler['for_hint_loop'] == goals['failed_ordinary']
        assert 'minimal_reproduction' not in handler and 'regression_corpus' not in handler
    rules = initialized_rules(semantics, record, sempin, lowerer, expected, project, certs)
    contractfile = library / 'rewrite_contracts/trust.yaml'; physical.pin(contractfile)
    contract = safe_yaml(yaml, contractfile.read_text()); unit = contract['proof_unit']
    assert contract['id'] == certs.PARTIAL_CONTRACT and contract['version'] == '0.1'
    assert pins['contract'] == pins['code'] == {'id': certs.PARTIAL_CONTRACT, 'sha256': digest(contract)}
    assert unit['correctness_policy'] == settings['proof_semantics']['unit_correctness_policy']
    assert unit['source'] == {'root': 'library', 'path': 'proof_units/trust.cc', 'sha256': H(canonical.encode())}
    assert unit['function'] == 'trust_fixture' and 'array_domains' not in unit and contract['concurrency_frame'] == []
    clauses = contract['clauses']; assert len(clauses) == 1
    assert clauses[0]['acsl']['text'] == r'assigns REG_count, SPD_count, region_count, __swdb_dx_reg_words[0..1]; ensures \result == ' + str(number) + ';'
    assert clauses[0]['acsl']['uses'] == [] and clauses[0]['proof_placement'] == {'once': 'self'}
    hashes = setup['hashes']; assert hashes['contract'] == pins['contract']['sha256']
    assert pins['c_lowering']['sha256'] == physical.pin(reports['c_lowering']['path']) == hashes['lowering']
    assert hashes['wp_input.c'] == physical.pin(wp) and hashes['compiler_runtime'] == digest(compiler)
    bindings = [receipt['retained_binding'] for receipt in checked['certificates']]
    assert hashes['dx100_initialized_register_source'] == digest(bindings)
    for name in ('dx100_register_source', 'dx100_allocation_source', 'dx100_stream_source', 'dx100_size_source',
                 'dx100_source_selector', 'summaries', 'summary_bindings'):
        assert hashes[name] == digest([])
    assert hashes['stdlib_provenance'] == digest({})
    assert len(setup['runs']) == 1
    run = setup['runs'][0]
    assert run['verdict'] == 'passed' and run['tool'] == 'wp'
    assert run['hashes'] == {name: value for name, value in hashes.items() if name not in {'contract', 'run_plan'}}
    log = Path(record['evidence']['adapter_log']['path']).read_text()
    commands = [shlex.split(line[len('command: '):]) for line in log.splitlines() if line.startswith('command: ')]
    assert len(commands) == 1 and '\ncwd: scratch\n' in log
    health = re.findall(r'^frama-c exit ([0-9]+), wall ([0-9.]+) s, peak rss ([0-9]+), out of memory (True|False), timed out (True|False)$', log, re.M)
    assert len(health) == 1 and health[0][0] == '0' and health[0][3:] == ('False', 'False')
    assert 0 <= float(health[0][1]) < 1200 and 0 < int(health[0][2]) < 8589934592
    command = commands[0]; assert command[0] == expected['tools']['frama-c']['path']
    context = obligations.ephemeral_wp_context(wp, command)
    exact_command = [expected['tools']['frama-c']['path'], '-machdep', 'x86_64', 'wp_input.c', '-print', '-ocode',
        'wp-normalized.c', '-then', *settings['flags'], '-wp-report-json', 'wp-goals.json', '-then', '-load-module',
        str(scratch.parent / 'proof_report.cmxs'), '-report', '-report-untried', '-report-csv', 'wp-properties.csv']
    assert command == exact_command
    assert run['run_plan_sha256'] == digest({'command': command, 'flags': settings['flags'], 'inputs': run['hashes'],
        'bounds': identities.fixture_job_bounds(project), 'method_version': pins['method_version']})
    return {'id': record['id'], 'expected_result': number, 'verdict': record['verdict'],
            'failure_class': record.get('failure_class'), 'source_certificates': checked,
            'complete_query': query, 'native_goal_property_CSV_audit': goals, 'rules': rules, 'model': model,
            'native_context': context, 'WP_input_sha256': physical.pin(wp),
            'structural_goals': [{name: goal[name] for name in ('goal', 'property', 'function', 'line', 'smoke', 'targets')}
                                 for goal in inventory['goals']],
            'source_sha256': H(canonical.encode()), 'correctness_policy': settings['proof_semantics']['unit_correctness_policy']}


def validate_record_selection(rows):
    assert type(rows) is list and len(rows) == 2
    assert [row['expected_result'] for row in rows] == [711, 1107]
    for row in rows:
        assert set(row) == {'expected_result', 'record', 'id'} and type(row['expected_result']) is int
        assert type(row['id']) is str and row['id']
        assert set(row['record']) == {'path', 'bytes', 'sha256'}
        absolute(row['record']['path'])
        assert type(row['record']['bytes']) is int and row['record']['bytes'] >= 0
        assert re.fullmatch('[a-f0-9]{64}', row['record']['sha256'])
    assert len({row['record']['path'] for row in rows}) == len({row['id'] for row in rows}) == 2
    return rows


def audit(policy_file, policy_sha256):
    assert __debug__ and not sys.flags.optimize
    assert isinstance(SOURCE_COMMIT, str) and re.fullmatch(r'[0-9a-f]{40}', SOURCE_COMMIT), 'V2 published source commit pending'
    assert type(RUNTIME_CONTROLLER_VERSION) is int and RUNTIME_CONTROLLER_VERSION == 4, 'V2 reviewed runtime controller version4 pending'
    physical = Physical(); pf = absolute(str(policy_file))
    physical.pin(pf, policy_sha256)
    policy = strict_json(pf.read_text())
    assert policy['schema'] == 'initialized-cold-audit-policy-1' and policy['admitted'] is True
    assert policy['source_commit'] == SOURCE_COMMIT
    raw, project = absolute(policy['raw']), absolute(policy['project'])
    assert raw.resolve() == raw and project.resolve() == project and not raw.is_relative_to(project.parent)
    assert not project.parent.is_relative_to(raw)
    physical.pin(__file__, policy['reader_sha256'])
    modules = load_reviewed_modules(policy, physical)
    closed = modules['closed_python_surface.py']; roles = modules['python_startup_roles_v2.py']
    source_bytes = physical.read(policy['source_policy']); expected = strict_json(source_bytes)
    assert expected['source_commit'] == SOURCE_COMMIT and raw.name == expected['raw_name']
    assert type(expected['runtime_controller_version']) is int and expected['runtime_controller_version'] == RUNTIME_CONTROLLER_VERSION
    yaml, python_before = admit_reader(policy, expected, closed, physical)
    raw_before = raw_snapshot(raw, physical)
    assert raw_before == policy['raw_manifest'], 'complete root-pinned immutable raw manifest differs'
    launch = original_launch(policy, expected, raw, physical)
    source = complete_source(policy, expected, raw, project, physical)
    helpers = pure_runtime_helpers(physical.read(policy['original_entry']).decode(), physical)
    runtime_before = runtime_closure(expected, closed, helpers, physical)
    startup = startup_and_runtime_receipts(expected, raw, project, roles, closed, physical)
    contexts = project_contexts(expected, raw, project, modules['initialized_cold_identities_v2.py'])
    work = workflow(expected, raw)
    validate_record_selection(policy['records'])
    references = absolute(policy['reference_directory'])
    for name, value in {'cold-reference-wp-correct.c': 'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',
                        'cold-reference-wp-wrong.c': '46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}.items():
        physical.pin(references / name, value)
    records = [audit_record(row, expected=expected, raw=raw, project=project,
        compiler=contexts['initialized-project-runtime-provenance.json']['compiler'],
        lowerer=contexts['initialized-project-runtime-provenance.json']['lowering'], modules=modules,
        yaml=yaml, physical=physical, references=references) for row in policy['records']]
    assert records[0]['source_sha256'] == records[1]['source_sha256']
    assert records[0]['structural_goals'] == records[1]['structural_goals']
    assert records[0]['correctness_policy'] == records[1]['correctness_policy']
    # Runtime and whole raw physical rehash after the audit; source consumer
    # members use stable ctime/mtime/inode/size after one complete content pass.
    assert runtime_closure(expected, closed, helpers, physical) == runtime_before
    assert closed.verify_python_metadata(expected['python_surface_binding']) == python_before
    for name, attributes in source['source_stats'].items():
        assert stable_stat(Path(name).lstat()) == attributes
    assert source_membership(project, expected) == {row['relative'] for row in source['receipt']['files']}
    for row in policy['reader_files'].values(): physical.pinned(row)
    physical.pin(__file__, policy['reader_sha256']); physical.pin(pf, policy_sha256)
    assert not os.path.lexists(policy['reader_admission']['pycache_prefix'])
    assert list(sys.path) == expected['startup_roles']['package_sys_path']
    physical.unchanged()
    assert raw_snapshot(raw, physical) == raw_before
    return {'classification': 'PASS_SCOPED_PARTIAL_INITIALIZED_U32_PAIR', 'source_commit': SOURCE_COMMIT,
            'reader_sha256': physical.pin(__file__), 'policy_sha256': policy_sha256,
            'physical_checks': physical.checks, 'indexed_physical_files': len(physical.files),
            'raw_files': len(raw_before['files']), 'raw_bytes': sum(row['bytes'] for row in raw_before['files'].values()),
            'source_consumer_count': source['receipt']['count'], 'source_boundary': source['boundary'],
            'launch': launch, 'runtime_contexts': contexts, 'startup': startup, 'workflow': work, 'records': records,
            'negative_refuted': False, 'source_event_refinement': False, 'model_contract_body_refinement': False,
            'hardware_or_liveness': False, 'current_0_2': False, 'full_ticket28': False,
            'root_owns_process_lease_settlement': True}


def refusal_frame_report_v6(error):
    """Bounded frame identity only; no exception text, source lines or locals."""
    frames, count = [], 0
    current = error.__traceback__
    while current is not None:
        code = current.tb_frame.f_code
        frames.append({'filename': code.co_filename, 'function': code.co_name, 'line': current.tb_lineno})
        if len(frames) > 16:
            frames.pop(0)
        count += 1
        current = current.tb_next
    return {'classification': 'REFUSED', 'error_type': type(error).__name__,
            'frames': frames, 'frames_omitted': max(0, count - len(frames)), 'scientific_acceptance': False}


if __name__ == '__main__':
    sys.addaudithook(deny_children)
    if len(sys.argv) != 3 or not __debug__:
        raise SystemExit('usage: pinned isolated Python -I -B READER POLICY POLICY_SHA256')
    try:
        print(json.dumps(audit(sys.argv[1], sys.argv[2]), indent=2, sort_keys=True, allow_nan=False))
    except Exception as error:
        print(json.dumps(refusal_frame_report_v6(error), sort_keys=True))
        raise SystemExit(1)
