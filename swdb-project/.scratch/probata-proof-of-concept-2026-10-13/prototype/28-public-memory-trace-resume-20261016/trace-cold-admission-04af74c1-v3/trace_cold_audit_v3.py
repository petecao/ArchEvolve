"""2026-10-16 ET. INERT passive auditor of one original abstract trace25 run.

Root must independently admit exact source, policy, selected Python/environment
and runtime before invocation. No child, project import or scientific rerun.
PyYAML enters only after closed isolated Python admission. Original raw is read
only. Print compact metadata outside it. No hardware/source/current0.2 claim.
"""
import ast
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

COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
PACKET = '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-public-memory-trace-resume-20261016'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v4'
ENTRY_SHA = '5f17d3f730253265393575aa9557b7bfcc567ee83bdf231b2b828e8412e1c986'
POLICY_SHA = 'd61807f5595e77aabdbd054b6f00caff636775f07ab697f368af8f87864241de'
PUBLIC_SHA = 'e5acab8650b8b56b78df1cb7c1cfc22ba34e16c4039e1faf51417f3917a7a63f'
ROOT_RECEIPT_SHA = 'c94420bdb85074be52aa2044158c9ee77cace37f4dbb0fac2274e64973a5e7ff'
READER_PINS = {
    'reviewed_cold_primitives_v1.py': '4b5ccd919ab71e54c70038a456c68c06b6f9e84af5ca6e690258094d79f428c4',
    'public_assertions_v1.py': '7fb5964e54a7a862e807b7154de43a46cd7ac34f22483d7858113cf37da13acd',
    'closed_python_surface.py': '748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af',
    'python_startup_roles_v2.py': '5e9d2e6dfa2aaa7999f4670a979d3cc32736b852a612f77d4e2f7c71bc229618',
    'initialized_cold_identities_v2.py': '0c248fc3b50e69629fed8ab9a187dc5a947cc9aee3fb628aa8d604a6e79c5cc9',
}
H = lambda value: hashlib.sha256(value).hexdigest()


def deny_passive(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir',
            'os.link', 'os.symlink', 'os.truncate', 'os.chmod', 'os.chown'}:
        raise RuntimeError('passive trace reader refuses ' + event)
    if event == 'open':
        _path, mode, flags = arguments
        if mode is not None and any(char in mode for char in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive trace reader refuses write access')


def bootstrap_bytes(row):
    assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
    path = Path(row['path'])
    assert path.is_absolute() and path.resolve(strict=True) == path
    before = path.lstat(); assert stat.S_ISREG(before.st_mode)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno()); data = stream.read()
        after = os.fstat(stream.fileno())
    def state(value):
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    assert state(before) == state(opened) == state(after) == state(path.lstat())
    assert type(row['bytes']) is int and len(data) == row['bytes'] and H(data) == row['sha256']
    return data


def module_from_bytes(name, data, *, namespace=None):
    module = types.ModuleType('passive_' + name.replace('.', '_'))
    module.__file__ = name
    if namespace: module.__dict__.update(namespace)
    exec(compile(data, name, 'exec'), module.__dict__)
    return module


def validate_admission_policy(policy):
    assert policy['schema'] == 'trace-cold-audit-policy-1' and policy['admitted'] is True
    assert policy['source_commit'] == COMMIT and policy['raw'] == RAW
    assert set(policy['reader_files']) == set(READER_PINS)
    for name, digest in READER_PINS.items():
        assert Path(policy['reader_files'][name]['path']).name == name
        assert policy['reader_files'][name]['sha256'] == digest
    assert len(policy['records']) == 25
    assert len({row['id'] for row in policy['records']}) == 25
    assert len({row['record']['path'] for row in policy['records']}) == 25
    assert len({row['case'] for row in policy['records']}) == 25
    return policy


def parse_literal_bindings(text, names):
    result = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in names:
                assert name not in result
                result[name] = ast.literal_eval(node.value)
    assert set(result) == set(names)
    return result


def source_case_primitives(project, physical):
    folder = project / PACKET
    public = (folder / 'test_public_actual.py').read_bytes()
    assert H(public) == PUBLIC_SHA
    constants = parse_literal_bindings((folder / 'trace_fixture.py').read_text(),
        {'ENTRY', 'POLICY_ID', 'QUERY_PROTOTYPES', 'SCOPE', 'TRUST', 'WP_REFUSAL'})
    text = (folder / 'trace_cases.py').read_text(); tree = ast.parse(text)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'case', 'source'}]
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in {'C', 'CASES'} for target in node.targets)]
    assert len(functions) == len(assignments) == 2
    # The source file is a source-consumer member of the exact commit. This
    # selected AST has no import, filesystem, project or child expression.
    namespace = dict(constants)
    exec(compile(ast.Module(body=functions + assignments, type_ignores=[]), '<source-bound-case-data>', 'exec'), namespace)
    cases = namespace['CASES']
    assert type(cases) is list and len(cases) == len({row['name'] for row in cases}) == 25
    assert all(row['expected_verdict'] in ('proven', 'refuted') for row in cases)
    for row in cases:
        text = namespace['source'](row)
        assert physical.pin(folder / 'cases' / (row['name'] + '.cc')) == H(text.encode())
    return namespace, public


def normalized_runtime(expected, metadata):
    # Explicit schema projection; it does not add paths, tools or allowances.
    assert set(expected['portable_import_surfaces']) == {'why3_stdlib', 'wp_why3_support', 'why3_drivers'}
    result = dict(expected)
    result['python_surface_binding'] = metadata
    result['startup_roles'] = expected['python_startup_roles_v2']
    result['portable_import_surfaces'] = {name: row['files'] for name, row in expected['portable_import_surfaces'].items()}
    return result


def source_closure(policy, expected, final, project, physical, common):
    assert expected['source_commit'] == policy['source_commit'] == COMMIT
    assert len(expected['source_files']) == 609 and len(expected['source_consumer_trees']) == 11
    receipt = final['source_before']
    assert receipt == final['source_after'] and final['unchanged'] is True
    assert common.digest(receipt) == policy['source_consumer_receipt_sha256']
    assert receipt['source_commit'] == COMMIT and receipt['trees'] == expected['source_consumer_trees']
    assert receipt['physical_git_blob_equality'] is True
    rows = receipt['files']; assert len(rows) == receipt['count'] == len({row['relative'] for row in rows}) == 1678
    assert receipt['total_bytes'] == sum(row['bytes'] for row in rows)
    assert common.source_membership(project, expected) == {row['relative'] for row in rows}
    stats = {}
    for row in rows:
        path = project / common.relative(row['relative'])
        assert str(path) == row['path']
        before = path.lstat(); assert stat.S_ISREG(before.st_mode)
        content = hashlib.sha256(); blob = hashlib.sha1(('blob ' + str(before.st_size) + '\0').encode())
        with path.open('rb') as stream:
            assert common.stable_stat(os.fstat(stream.fileno())) == common.stable_stat(before)
            for block in iter(lambda: stream.read(1048576), b''): content.update(block); blob.update(block)
        after = path.lstat(); assert common.stable_stat(before) == common.stable_stat(after)
        assert row['bytes'] == after.st_size and row['sha256'] == content.hexdigest() and row['git_blob'] == blob.hexdigest()
        stats[str(path)] = common.stable_stat(after)
    indexed = {row['relative']: row for row in rows}
    for name, digest in expected['source_files'].items():
        if name in indexed: assert indexed[name]['sha256'] == digest
        else: physical.pin(project / common.relative(name), digest)
    return {'stats': stats, 'count': len(rows), 'boundary': 'physical SHA256 and opaque Git blob equality; root separately owns commit/Git readback'}


def original_launch(policy, expected, raw, physical, common):
    source = physical.read(policy['source_policy']); assert H(source) == POLICY_SHA
    assert physical.pin(policy['original_entry']['path'], ENTRY_SHA) == expected['linux_launch_binding']['entry_sha256']
    launch = common.strict_json((raw / 'launch.json').read_bytes())
    argv = [expected['tools']['opam']['path'], 'exec', '--switch=framac-33', '--',
        expected['tools']['python']['path'], '-I', '-B', policy['original_entry']['path'], expected['source_root'],
        str(raw), policy['source_policy']['path'], policy['source_policy']['sha256']]
    assert launch['command'] == argv and launch['source_commit'] == COMMIT
    assert launch['workers'] == 1 and launch['rss_cap_bytes'] == 8589934592 and launch['timeout_seconds'] == 1200
    assert launch['node'] == 1 and launch['source'] == str(Path(expected['source_root']).parent)
    for name, digest in expected['linux_launch_binding']['wrappers'].items():
        assert launch['reviewed_wrapper_reuse'][name] == digest
        physical.pin(raw / name, digest)
    resources = {name: common.strict_json((raw / name).read_bytes()) for name in ('resources.json', 'outer-resources.json')}
    for name, value in resources.items():
        assert value['exit_code'] == 0 and value['out_of_memory'] is value['timed_out'] is False
        assert type(value['peak_rss_bytes']) is int and 0 < value['peak_rss_bytes'] < 8589934592
        assert type(value['wall_seconds']) in (int, float) and math.isfinite(value['wall_seconds'])
        assert 0 < value['wall_seconds'] < (1320 if name == 'outer-resources.json' else 1200)
    lane = common.strict_json((raw / 'lane.json').read_bytes())['socket_lane']
    assert lane == policy['settled_lane']
    assert lane['node'] == 1 and lane['lease_generation'] == 635 and lane['exit_code'] == 0
    assert lane['host'] == 'mbit10' and lane['lease_name'] == 'mbit10-evaluation-node1'
    assert lane['cpus_allowed_list'] == ','.join(map(str, range(1, 64, 2)))
    assert lane['numa_memory_policy'] == 'bind:1' and lane['numactl'] == '--cpunodebind=1 --membind=1'
    assert lane['command'] == ['timeout', '--signal=TERM', '--kill-after=60', '1320', 'bash', str(raw / 'run.sh')]
    role = common.strict_json((raw / 'memory-trace-linux-role-admission.json').read_bytes())
    assert role['launch'] == {'path': str(raw / 'launch.json'), 'sha256': physical.pin(raw / 'launch.json')}
    assert role['source_commit'] == COMMIT and role['node'] == 1 and role['workers'] == 1
    assert role['rss_cap_bytes'] == 8589934592 and role['whole_seconds'] == 1200
    live = role['live_lane']
    assert live['lease'] == lane['lease_name'] and live['generation'] == lane['lease_generation']
    assert live['memory_policy'] == 'bind:1' and live['cpus'] == list(range(1, 64, 2)) and live['fd9_matches_lease'] is True
    assert type(live['ancestor_pid']) is int and live['ancestor_pid'] > 0
    assert type(live['ancestor_chain']) is list and live['ancestor_chain'] and len(set(live['ancestor_chain'])) == len(live['ancestor_chain'])
    assert all(type(pid) is int and pid > 0 for pid in live['ancestor_chain'])
    assert policy['root_execution_receipt']['bytes'] == 26667
    assert policy['root_execution_receipt']['sha256'] == ROOT_RECEIPT_SHA
    root = common.strict_json(physical.read(policy['root_execution_receipt']))
    assert root['raw_root'] == str(raw) and root['actual']['lane.json']['socket_lane'] == lane
    for name in resources: assert root['actual'][name] == resources[name]
    assert common.strict_json((raw / 'source-after.json').read_bytes()) == {
        'commit': COMMIT, 'source_unchanged': True, 'tracked_changes': ''}
    return {'resources': resources, 'lane': lane,
            'settlement_boundary': 'finite process/lease settlement is separately root supplied; no invented final-null or continuing absence'}


def original_controls(expected, raw, policy, physical):
    names = set(expected['control_files']) | {Path(policy['original_entry']['path']).name, Path(policy['source_policy']['path']).name}
    control = raw / 'control'
    assert control.resolve(strict=True) == control and not control.is_symlink()
    assert {path.name for path in control.iterdir()} == names
    for path in control.iterdir(): assert stat.S_ISREG(path.lstat().st_mode)
    for name, digest in expected['control_files'].items(): physical.pin(control / name, digest)
    physical.pinned(policy['original_entry']); physical.pinned(policy['source_policy'])
    return sorted(names)


def startup_receipts(expected, metadata, raw, project, roles, closed, common):
    plan = expected['python_startup_roles_v2']; cache = raw / 'bootstrap-source-cache'
    observer = (raw / 'control/t28-linux-runtime-observer-v2-actual-20261016.json').read_bytes()
    provenance = roles.validate_role_plan_v2(plan, metadata=metadata, source_project=project,
        root_observer_bytes=observer, closed=closed)
    environment = roles.child_environment_v2({}, project=project, raw=raw, cache=cache)
    receipts = {}
    for role in ('entry-isolated', 'pytest-child'):
        value = common.strict_json((raw / (role + '-startup.json')).read_bytes())
        request = roles.role_request_v2(plan, role=role, environment=environment, cache=cache)
        assert value['plan_provenance'] == provenance
        assert roles.check_role_observation_v2(request, value['observation']) == value['receipt']
        assert (raw / (role + '-startup-stderr.txt')).read_bytes() == b''
        assert common.strict_json((raw / (role + '-startup-stdout.txt')).read_bytes()) == value['observation']
        receipts[role] = value['receipt']
    actual = common.strict_json((raw / 'memory-trace-profile/actual-pytest-child-startup.json').read_bytes())
    request = roles.role_request_v2(plan, role='pytest-child', environment=environment, cache=cache)
    roles.check_role_observation_v2(request, actual)
    runtime = common.strict_json((raw / 'memory-trace-profile/runtime-provenance.json').read_bytes())
    assert runtime['startup'] == actual and runtime['source_commit'] == COMMIT
    assert all(runtime['runtime'][name] == row for name, row in expected['linux_clang_components'].items())
    assert runtime['lowering']['naming_rules'] == expected['naming']
    provenance_row = common.strict_json((raw / 'memory-trace-profile/launch-provenance.json').read_bytes())
    assert provenance_row['plan'] == provenance
    cbmc = provenance_row['cbmc_version']
    assert cbmc['returncode'] == 0 and cbmc['accepted_cbmc_release_family'] == '6.11' and cbmc['exact_observed_version'] == '6.11.0'
    assert cbmc['stdout_sha256'] == H(expected['cbmc_version_output']['stdout'].encode())
    assert cbmc['stderr_sha256'] == H(expected['cbmc_version_output']['stderr'].encode())
    assert provenance_row['compiler_preflight']['command'] == expected['linux_clang_components']['command']
    normalized = provenance_row['compiler_selector_normalization']
    assert normalized['input_tokens'] == ['clang++'] and normalized['reviewed_alias_used'] is True
    assert normalized['selected_absolute_tokens'] == expected['linux_clang_components']['command']
    assert not os.path.lexists(cache)
    return {'plan': provenance, 'roles': receipts, 'runtime': runtime}


def workflow(expected, raw, cases, common):
    wanted = [PACKET + '/test_public_actual.py::test_actual_public_abstract_memory_trace[' + row['name'] + ']' for row in cases]
    assert wanted == expected['selection'] and len(wanted) == len(set(wanted)) == 25
    profile = raw / 'memory-trace-profile'
    collection = common.strict_json((profile / 'collection.json').read_bytes())
    assert collection == {'exit_code': 0, 'selected': wanted, 'expected': wanted}
    assert (profile / 'exit-code.txt').read_bytes() == b'0\n'
    arguments = ['-q', '--tb=short', '--rootdir', expected['source_root'], '-p', 'no:cacheprovider',
                 '--basetemp', str(profile / 'pytest'), '--junitxml', str(profile / 'junit.xml'), *wanted]
    assert common.strict_json((profile / 'pytest-arguments.json').read_bytes()) == arguments
    root = ET.parse(profile / 'junit.xml').getroot()
    suites, tests = list(root.iter('testsuite')), list(root.iter('testcase'))
    assert root.tag == 'testsuites' and len(list(root.iter('testsuites'))) == len(suites) == 1
    assert suites[0].get('tests') == '25' and len(tests) == 25
    assert all(suites[0].get(name) == '0' for name in ('failures', 'errors', 'skipped'))
    assert all(not list(root.iter(name)) for name in ('failure', 'error', 'skipped'))
    assert [case.get('name') for case in tests] == [node.split('::')[-1] for node in wanted]
    assert all(case in list(suites[0]) and case.get('classname') == expected['junit_classname'] for case in tests)
    progress = [common.strict_json(line) for line in (profile / 'case-reports.jsonl').read_bytes().splitlines()]
    assert len(progress) == 75
    for index, row in enumerate(progress):
        assert row['event'] == 'runtest_report' and row['nodeid'] == wanted[index // 3]
        assert row['when'] == ('setup', 'call', 'teardown')[index % 3] and row['outcome'] == 'passed'
        assert row['longrepr'] is None and type(row['duration']) in (int, float) and math.isfinite(row['duration']) and row['duration'] >= 0
        assert type(row['at_utc']) is str and row['at_utc']
    assert common.strict_json((profile / 'junit-census.json').read_bytes()) == {
        'accepted': True, 'cases': 25, 'skipped': 0,
        'scope': 'workflow census only; every abstract proof/refutation and cold audit remain separate'}
    return {'tests': 25, 'errors': 0, 'failures': 0, 'skipped': 0, 'complete_case_phase_reports': 75}


def cbmc_outcome_primitive(project, common):
    text = (project / 'swdb/cbmc_adapter.py').read_text()
    constants = parse_literal_bindings(text, {'UNCLASSIFIED'})
    names = {'read_outcome', '_unproven', '_oracle'}
    functions = [node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(functions) == len(names)
    translator = parse_literal_bindings((project / 'swdb/cbmc_translator.py').read_text(), {'REACH_END', 'REACH_SUMMARY', 'ORACLE_CAPACITY'})
    semantics = parse_literal_bindings((project / 'swdb/proof_semantics.py').read_text(), {'CAPACITY', 'MEMORY_DOMAIN'})
    namespace = dict(json=json, re=re, tr=types.SimpleNamespace(**translator),
                     proof_semantics=types.SimpleNamespace(**semantics), **constants)
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<source-bound-passive-cbmc-reading>', 'exec'), namespace)
    return namespace['read_outcome']


def physical_record_members(raw):
    # Pytest's literal current symlink is part of the root-pinned raw manifest,
    # never a second physical fixture or alternate evidence input.
    fixtures = [path for path in (raw / 'memory-trace-profile/pytest').iterdir()
                if stat.S_ISDIR(path.lstat().st_mode)]
    assert len(fixtures) == 25
    members = {str(path) for fixture in fixtures for path in (fixture / 'records/proofs').glob('*.yaml')}
    assert len(members) == 25
    return members


def fixture_identities(project, runtime, identities, yaml, common):
    assert identities.source_identity(project, runtime['runtime'])['sha256'] == runtime['lowering']['c_lowering']['sha256']
    assert identities.checkers_identity(project) == runtime['proof_setup']
    text = (project / 'swdb/cbmc_translator.py').read_text()
    values = parse_literal_bindings(text, {'TOOL_ID', 'TOOL_VERSION'})
    translator = {'id': values['TOOL_ID'] + '-' + values['TOOL_VERSION'],
        'sha256': H((project / 'swdb/cbmc_translator.py').read_bytes() + (project / 'swdb/bounded_entry_windows.py').read_bytes())}
    method = common.safe_yaml(yaml, (project / 'tests/fixtures/proof/methods/contract-fixture-1.yaml').read_bytes())
    method['c_lowering']['translators'] = [runtime['lowering']['c_lowering'], translator]
    frozen = parse_literal_bindings((project / 'swdb/cbmc_adapter.py').read_text(), {'FROZEN'})['FROZEN']
    next(row for row in method['lineup'] if row['tool'] == 'cbmc')['flags'] = list(frozen)
    next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')['flags'] += [
        '-rte-initialized', '@all', '-wp-no-filter-init', '-machdep', 'x86_64', '-wp-prover', 'z3,cvc5,alt-ergo']
    method.update(id='method.dx100-selector-fixture-0-2', sequence=2)
    method['checks'].update(runtime['proof_setup'])
    method['c_lowering']['naming_rules'] = runtime['lowering']['naming_rules']
    return {'method': method, 'translator': translator, 'frozen': list(frozen)}


def owned_assumptions(record, entry, expected, runtime, identities, project):
    text = (project / 'swdb/cbmc_adapter.py').read_text()
    sentences = parse_literal_bindings(text, {'SENTENCES'})['SENTENCES']
    version = parse_literal_bindings((project / 'swdb/c_lowering.py').read_text(), {'TOOL_VERSION'})['TOOL_VERSION']
    cbmc = expected['tools']['cbmc']
    tools = [
        ('c_lowering', runtime['lowering']['c_lowering'], version),
        ('clang', runtime['lowering']['clang'], '22.1.8'),
        ('translator', identities['translator'], identities['translator']['id']),
        ('cbmc', {'id': 'cbmc-6.11.0', 'sha256': cbmc['sha256']}, '6.11.0'),
        ('solver', {'id': 'minisat2-in-cbmc-6.11.0', 'sha256': cbmc['sha256']}, 'minisat2 (bundled with CBMC 6.11.0)'),
    ]
    wanted = [{'kind': 'trusted_tool', 'reference': pin, 'sentence': sentences[name].format(version=ver)}
              for name, pin, ver in tools]
    semantic = record['pins']['proof_semantics']
    wanted += [{'kind': 'proof_semantics', 'reference': {'id': semantic['id'] + '#' + rule['id'], 'sha256': semantic['sha256']},
                'sentence': rule['statement']} for rule in entry['rules'] if rule.get('record_assumption') is True]
    wanted.append({'kind': 'proof_semantics', 'reference': semantic,
        'sentence': 'This is a synthetic abstract scalar trace. Deferred history, ownership, '
                    'region and pair checks describe its exact pinned model only; there is no '
                    'real-header, CPU-access, typed-value, physical-address or hardware refinement '
                    'certificate and no at-issue reduction claim.'})
    assert record['assumptions'] == wanted and record['tools'] == [pin['id'] for _name, pin, _ver in tools]


def generated_model(entry, fixture, project):
    text = (project / 'swdb/proof_semantics.py').read_text()
    tree = ast.parse(text)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'ghost_declarations', '_bounded_state'}]
    expressions = [node for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                   isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'GHOST_LINE', 'DECL_NAME'}]
    assert len(functions) == len(expressions) == 2
    namespace = {'re': re}
    exec(compile(ast.Module(body=expressions + functions, type_ignores=[]), '<source-bound-scalar-model-text>', 'exec'), namespace)
    model = fixture / 'library/proof_semantics/synthetic-memory-trace'
    ghost = namespace['ghost_declarations']((model / 'ghost.acsl').read_text())
    assert ghost == [('swdb_t28_marker', 'int swdb_t28_marker[1]')]
    state, objects = namespace['_bounded_state']((model / 'state.h').read_text(), entry['constants'])
    parts = [f"/* Generated by swdb.proof_semantics: the C model of {entry['id']} (version {entry['version']}). */"]
    parts += [f'#define {name} {value}' for name, value in entry['constants'].items()]
    parts.append('#define DX_RULE(r) "' + entry['id'] + '#" r')
    parts.append('/* ghost state, generated from ghost.acsl (declared once there) */')
    parts += [decl + ';' for _name, decl in ghost]
    parts += [state, (model / 'model.h').read_text()]
    return '\n'.join(parts) + '\n', [{'name': name, 'elements': extent} for name, extent in objects]


def audit_record(row, case, *, raw, project, expected, physical, common, yaml, assertions, source, runtime, read_outcome, identities):
    record_path = common.absolute(row['record']['path'])
    assert raw in record_path.parents and record_path.parent.name == 'proofs' and record_path.parent.parent.name == 'records'
    fixture = record_path.parent.parent.parent
    records = list((fixture / 'records/proofs').glob('*.yaml')); assert records == [record_path]
    assert not os.path.lexists(fixture / 'must-not-launch-solver')
    record = common.safe_yaml(yaml, physical.read(row['record']))
    assert record['id'] == row['id'] and record['kind'] == 'proof' and record['evidence_kind'] == 'contract_fixture'
    assert record['subject'] == {'kind': 'library_summary', 'id': 'contract.dx100_trust_fixture'}
    assert record['bounds'] == {'threads': 1}
    assert record['verdict'] == case['expected_verdict'] and record.get('failure_class') is None
    assert 'unreplayed_counterexample' not in record and not record.get('unproven_properties')
    semantics = fixture / 'library/proof_semantics/dx100_trust_fixture.yaml'
    entry = common.safe_yaml(yaml, semantics.read_bytes())
    shape = parse_literal_bindings((project / 'swdb/bounded_initialization.py').read_text(),
        {'DX100_TRACE_SHAPE_SHA256', 'DX100_TRACE_COMPONENTS'})
    assert common.digest(entry) == shape['DX100_TRACE_SHAPE_SHA256'] == '8c1d71f33cfd1ee2d596a63bf7efec9d5bf75b9bb7830cf933a456c4fb46bdf0'
    for name in ('ghost.acsl', 'logic.acsl', 'state.h', 'model.h'):
        assert (fixture / 'library/proof_semantics/synthetic-memory-trace' / name).read_bytes() == (project / PACKET / name).read_bytes()
    assert (fixture / 'library/proof_units/trust.cc').read_text() == source(case)
    method_path = fixture / 'library/methods/dx100-selector-fixture-0-2.yaml'
    method = common.safe_yaml(yaml, method_path.read_bytes())
    assert method == identities['method']
    assert method['id'] == 'method.dx100-selector-fixture-0-2' and method['sequence'] == 2
    assert record['pins']['method_version'] == {'id': method['id'], 'sha256': H(method_path.read_bytes())}
    assert method['checks']['proof_setup_check'] == runtime['proof_setup']['proof_setup_check']
    assert method['checks']['verdict_reading'] == runtime['proof_setup']['verdict_reading']
    assert method['c_lowering']['naming_rules'] == runtime['lowering']['naming_rules']
    settings = record['settings']
    model = settings['bounded_initialization']['model_policy']
    assert model['entry_sha256'] == record['pins']['proof_semantics']['sha256'] == H(semantics.read_bytes())
    assert model['components'] == shape['DX100_TRACE_COMPONENTS']
    generated_text, objects = generated_model(entry, fixture, project)
    assert model['generated_sha256'] == H(generated_text.encode()) and model['tile_objects'] == objects
    assert model['scope'] == entry['description']
    assert settings['compiler_runtime'] == runtime['runtime'] and settings['rss_cap_bytes'] == 8589934592
    assert settings['wall_budget_seconds'] == 900 and settings['verifier_launched'] is True
    setup = record['proof_setup_check']
    assert setup['verdict'] == 'passed' and setup['check'] == runtime['proof_setup']['proof_setup_check']
    assert setup['method_version'] == record['pins']['method_version']
    assert len(setup['runs']) == 1 and setup['runs'][0]['verdict'] == 'passed' and setup['runs'][0]['tool'] == 'cbmc'
    assert record['pins']['translator'] == identities['translator']
    contract = common.safe_yaml(yaml, (fixture / 'library/rewrite_contracts/trust.yaml').read_bytes())
    assert contract['id'] == 'contract.dx100_trust_fixture'
    assert contract['proof_unit'] == {'source': {'root': 'library', 'path': 'proof_units/trust.cc',
        'sha256': H(source(case).encode())}, 'function': 'trust_fixture'}
    assert contract['concurrency_frame'] == [] and len(contract['clauses']) == 1
    assert contract['clauses'][0]['acsl'] == {'text': r'assigns \nothing; ensures \result == 1;', 'uses': []}
    reports = {}
    for evidence in record['evidence']['reports']:
        name = evidence['name']; assert name not in reports
        path = common.absolute(evidence['path']); assert fixture / 'runs' in path.parents
        physical.pin(path, evidence['sha256']); reports[name] = path
    names = {'cbmc_input', 'cbmc_output', 'differential_c', 'differential_cxx', 'differential_c_output', 'differential_cxx_output'}
    assert set(reports) == names | ({'replay_cxx'} if case['expected_verdict'] == 'refuted' else set())
    for name in ('cbmc_input', 'differential_c', 'differential_cxx', *(['replay_cxx'] if case['expected_verdict'] == 'refuted' else [])):
        assert reports[name].read_text().count(generated_text) == 1
    log_pin = record['evidence']['adapter_log']; log = Path(log_pin['path'])
    assert fixture / 'runs' in log.parents; physical.pin(log, log_pin['sha256'])
    text = log.read_text()
    flags = ['-DSWDB_CBMC', '--unwind', '1', *identities['frozen']]
    assert settings['flags'] == flags and settings['unwind'] == 1 and settings['array_length'] == 0
    commands = [shlex.split(value) for value in re.findall(r'^command: (.+)$', text, re.M)]
    command = [runtime['_cbmc_tool_path'], 'job.c', *flags, '--json-ui']
    assert commands == [command]
    generated = setup['runs'][0]
    assert generated['hashes']['job.c'] == physical.pin(reports['cbmc_input'])
    assert generated['hashes']['compiler_runtime'] == common.digest(runtime['runtime'])
    assert generated['run_plan_sha256'] == common.digest({'command': command, 'flags': flags,
        'inputs': generated['hashes'], 'bounds': {'threads': 1}, 'method_version': record['pins']['method_version']})
    executions = re.findall(r'^cbmc exit (-?\d+), wall ([0-9.]+) s, peak rss (\d+), out of memory (True|False), timed out (True|False)$', text, re.M)
    assert len(executions) == 1
    code, seconds, rss, oom, timeout = executions[0]
    assert int(code) in (0, 10) and math.isfinite(float(seconds)) and 0 <= float(seconds) < 900
    assert 0 < int(rss) < 8589934592 and oom == timeout == 'False'
    outcome = read_outcome(types.SimpleNamespace(out_of_memory=False, timed_out=False, exit_code=int(code)), reports['cbmc_output'].read_text())
    assert outcome['failure_class'] is None and outcome['goals'] == record['goals']
    assert outcome['verdict'] == ('proven' if case['expected_verdict'] == 'proven' else 'failed')
    agreement = settings['agreement']
    outputs = [reports['differential_' + side + '_output'].read_bytes() for side in ('c', 'cxx')]
    assert outputs[0] == outputs[1] and H(outputs[0]) == agreement['c_output_sha256'] == agreement['cxx_output_sha256']
    assert len(outputs[0].splitlines()) == agreement['runs'] and agreement['runs'] > 0
    assert not agreement.get('undefined_behavior_runs', 0)
    assert b'AddressSanitizer' not in outputs[0] and b'runtime error' not in outputs[0]
    if case['expected_verdict'] == 'refuted':
        witness = record['counterexample']
        assert any(all(witness[key] == failure[key] for key in ('check', 'property', 'function', 'oracle')) for failure in outcome['failures'])
        assert witness['replay']['replayed'] is True and witness['replay']['sanitizer'] is None
        assert witness['replay']['form'] == 'cxx' and witness['replay']['sanitizer_matches_check'] is None
        assert 'replayed; native ' in text and 'did not replay' not in text
    owned_assumptions(record, entry, expected, runtime, identities, project)
    assertions(record, entry, case, assertions.__globals__['Path'](semantics))
    return {'case': case['name'], 'record_id': record['id'], 'verdict': record['verdict'],
            'goals': len(record['goals']), 'native_agreement_runs': agreement['runs'],
            'replayed_abstract_refutation': case['expected_verdict'] == 'refuted'}


def audit(policy_file, policy_sha256):
    assert __debug__ and not sys.flags.optimize
    pf = Path(policy_file)
    policy_data = bootstrap_bytes({'path': str(pf), 'bytes': pf.stat().st_size, 'sha256': policy_sha256})
    policy = validate_admission_policy(json.loads(policy_data))
    common = module_from_bytes('reviewed_cold_primitives_v1.py', bootstrap_bytes(policy['reader_files']['reviewed_cold_primitives_v1.py']))
    assert policy_data == bootstrap_bytes({'path': str(pf), 'bytes': len(policy_data), 'sha256': policy_sha256})
    physical = common.Physical()
    physical.pin(pf, policy_sha256); physical.pin(__file__, policy['reader_sha256'])
    modules = {}
    for name in ('closed_python_surface.py', 'python_startup_roles_v2.py'):
        modules[name] = module_from_bytes(name, physical.read(policy['reader_files'][name]))
    closed, roles = modules['closed_python_surface.py'], modules['python_startup_roles_v2.py']
    raw, project = common.absolute(policy['raw']), common.absolute(policy['project'])
    assert raw.resolve(strict=True) == raw and project.resolve(strict=True) == project
    assert not raw.is_relative_to(project.parent) and not project.parent.is_relative_to(raw)
    expected = common.strict_json(physical.read(policy['source_policy']))
    assert H(physical.read(policy['source_policy'])) == POLICY_SHA and expected['raw_name'] == raw.name
    metadata = common.strict_json((raw / 'control/python-physical-metadata-v2.json').read_bytes())
    assert H((raw / 'control/python-physical-metadata-v2.json').read_bytes()) == expected['control_files']['python-physical-metadata-v2.json']
    normalized = normalized_runtime(expected, metadata)
    yaml, python_before = common.admit_reader(policy, normalized, closed, physical)
    before = common.raw_snapshot(raw, physical)
    assert before == policy['raw_manifest'] and len(before['files']) == 1409
    original_controls(expected, raw, policy, physical)
    launch = original_launch(policy, expected, raw, physical, common)
    final = common.strict_json((raw / 'memory-trace-final-physical-check.json').read_bytes())
    source = source_closure(policy, expected, final, project, physical, common)
    pure = common.pure_runtime_helpers(physical.read(policy['original_entry']).decode(), physical)
    runtime_before = common.runtime_closure(normalized, closed, pure, physical)
    assert final['python_physical'] == python_before
    startup = startup_receipts(expected, metadata, raw, project, roles, closed, common)
    identities_module = module_from_bytes('initialized_cold_identities_v2.py',
        physical.read(policy['reader_files']['initialized_cold_identities_v2.py']))
    identities = fixture_identities(project, startup['runtime'], identities_module, yaml, common)
    startup['runtime']['_cbmc_tool_path'] = expected['tools']['cbmc']['path']
    namespace, _public = source_case_primitives(project, physical)
    # Every Path access in the exact public assertion suffix is restricted to
    # previously root-pinned raw members. File bytes are verified before use.
    base_path = type(Path())
    class PinnedPath(base_path):
        def read_bytes(self):
            key = str(self.relative_to(raw)); row = before['files'][key]
            return physical.read({'path': str(self), **row})
        def read_text(self, encoding=None, errors=None):
            assert encoding in (None, 'utf-8') and errors in (None, 'strict')
            return self.read_bytes().decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    namespace.update(Path=PinnedPath, hashlib=hashlib, re=re, source=namespace['source'])
    assertions = module_from_bytes('public_assertions_v1.py', physical.read(policy['reader_files']['public_assertions_v1.py']), namespace=namespace).audit_public_assertions_v1
    cases = namespace['CASES']; work = workflow(expected, raw, cases, common)
    assert len(policy['records']) == 25 and len({row['id'] for row in policy['records']}) == 25
    assert [row['case'] for row in policy['records']] == [case['name'] for case in cases]
    record_members = physical_record_members(raw)
    assert record_members == {row['record']['path'] for row in policy['records']}
    read_outcome = cbmc_outcome_primitive(project, common)
    results = [audit_record(row, case, raw=raw, project=project, expected=expected, physical=physical, common=common,
        yaml=yaml, assertions=assertions, source=namespace['source'], runtime=startup['runtime'], read_outcome=read_outcome, identities=identities)
        for row, case in zip(policy['records'], cases)]
    assert common.runtime_closure(normalized, closed, pure, physical) == runtime_before
    assert closed.verify_python_metadata(metadata) == python_before
    assert common.source_membership(project, expected) == {str(Path(name).relative_to(project)) for name in source['stats']}
    for name, value in source['stats'].items(): assert common.stable_stat(Path(name).lstat()) == value
    original_controls(expected, raw, policy, physical)
    for row in policy['reader_files'].values(): physical.pinned(row)
    physical.pin(__file__, policy['reader_sha256']); physical.pin(pf, policy_sha256)
    assert common.raw_snapshot(raw, physical) == before
    assert not os.path.lexists(policy['reader_admission']['pycache_prefix'])
    assert list(sys.path) == expected['python_startup_roles_v2']['package_sys_path']
    physical.unchanged()
    return {'classification': 'PASS_SCOPED_ORIGINAL_ABSTRACT_TRACE25', 'source_commit': COMMIT,
        'records': results, 'workflow': work, 'launch': launch, 'source': {'count': source['count'], 'boundary': source['boundary']},
        'physical_checks': physical.checks, 'raw_files': len(before['files']),
        'raw_bytes': sum(row['bytes'] for row in before['files'].values()),
        'scope': 'exact original scalar abstract traces and their persisted native agreement/replay only',
        'hardware_counterexamples': False, 'source_call_refinement': False, 'whole_interface': False,
        'current_0_2': False, 'full_ticket28': False, 'root_owns_finite_process_lease_settlement': True}


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
    sys.addaudithook(deny_passive)
    if len(sys.argv) != 3 or not __debug__:
        raise SystemExit('usage: admitted Python -I -B -X pycache_prefix=ABSENT READER POLICY POLICY_SHA256')
    try:
        print(json.dumps(audit(sys.argv[1], sys.argv[2]), indent=2, sort_keys=True, allow_nan=False))
    except Exception as error:
        print(json.dumps(refusal_frame_report_v6(error), sort_keys=True))
        raise SystemExit(1)
