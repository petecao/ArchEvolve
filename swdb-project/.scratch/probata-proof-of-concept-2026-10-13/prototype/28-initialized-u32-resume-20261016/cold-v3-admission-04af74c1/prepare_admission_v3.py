"""2026-10-16 ET. Source-only V3 lane identity successor and admission builder.

This does not invoke the reader, import project modules, or execute children.
V1/V2 remain unchanged. Root separately reviews and stages the output.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INITIALIZED = HERE.parent
POC = INITIALIZED.parent.parent
TRACE = INITIALIZED.parent / '28-public-memory-trace-resume-20261016'
COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
BASE_SHA = '11b4e94d269f153d91ecd016dceee6deb65beb6cd6ee7a554ec9df78f37a65d3'
RECEIPT_SHA = '832980ed68bdcd9654e82e9e6e33debdf8021054a7e7e03f8dfb794e86754665'
CONTEXT_SHA = 'ce5f39fac13f9e5bb1b4feadb518245d5975f577048e0306b1e7cd2fe2324aa7'
PAIR_POLICY_SHA = 'bae7dc4c11e44bfd763ece9178dcc99f1aaffac3e492efdd3477137fae846637'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v3'
CONTROL = COLD + '/control'
PROJECT = '/data1/yanruj/probata-resume-20261016-04af74c1/swdb-project'
HELPER = '''def validate_original_lane_v3(policy, expected, raw, physical, lane):
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


'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, wanted):
    data = path.read_bytes()
    assert sha(data) == wanted, str(path)
    return data


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def pin(path, remote=None):
    data = path.read_bytes()
    return {'path': remote or str(path), 'bytes': len(data), 'sha256': sha(data)}


def build_source():
    before = checked(INITIALIZED / 'initialized_cold_audit_v2.py', BASE_SHA).decode()
    old = "    assert lane['exit_code'] == 0 and lane['job'] == raw.name and lane['node'] in (0, 1)\n"
    assert before.count(old) == 1
    after = before.replace('  SELECTED_PYTHON -I -B initialized_cold_audit_v2.py POLICY POLICY_SHA256',
                           '  SELECTED_PYTHON -I -B -X pycache_prefix=ABSENT initialized_cold_audit_v3.py POLICY POLICY_SHA256')
    after = after.replace(old, '    validate_original_lane_v3(policy, expected, raw, physical, lane)\n')
    after = after.replace('def startup_and_runtime_receipts(', HELPER + 'def startup_and_runtime_receipts(', 1)
    # The complete AST inverse is mechanically exact. No scientific function changes.
    old_ast = ast.parse(before)
    new_ast = ast.parse(after)
    new_ast.body[0] = old_ast.body[0]
    new_ast.body = [node for node in new_ast.body if not isinstance(node, ast.FunctionDef) or node.name != 'validate_original_lane_v3']
    old_launch = next(node for node in old_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'original_launch')
    new_launch = next(node for node in new_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'original_launch')
    new_launch.body[-2] = old_launch.body[-2]
    assert ast.dump(new_ast, include_attributes=False) == ast.dump(old_ast, include_attributes=False)
    target = HERE / 'initialized_cold_audit_v3.py'
    target.write_text(after)
    return target


def build():
    source = build_source()
    receipt_path = POC / 'evidence/t28-initialized-v5-root-execution-20261016.json'
    context_path = INITIALIZED / 'cold-v2-admission-04af74c1/passive-initialized-v5-context.json'
    pair_path = INITIALIZED / 'linux_pair_policy_04af74c1_v5.json'
    receipt = json.loads(checked(receipt_path, RECEIPT_SHA))
    context = json.loads(checked(context_path, CONTEXT_SHA))
    pair = json.loads(checked(pair_path, PAIR_POLICY_SHA))
    assert receipt['raw_root'] == context['raw'] == RAW
    assert context['file_count'] == receipt['raw_files'] == 184
    assert context['total_bytes'] == receipt['raw_bytes'] == 62761931
    consumers = list(context['consumers'].values())
    assert len(consumers) == 3 and all(row == consumers[0] for row in consumers)
    assert consumers[0]['source_commit'] == COMMIT
    assert context['json']['lane.json'] == receipt['actual']['lane.json']
    assert pair['source_commit'] == COMMIT and pair['runtime_controller_version'] == 4
    rows = []
    for index, expected in enumerate((711, 1107)):
        observation = receipt['records'][index]
        record = observation['pin']
        assert '/test_actual_initialized_u32_or' + str(index) + '/records/proofs/' in record['path']
        raw_row = context['raw_manifest']['files'][str(Path(record['path']).relative_to(RAW))]
        assert raw_row == {key: record[key] for key in ('bytes', 'sha256')}
        rows.append({'expected_result': expected, 'id': observation['id'], 'record': record})
    modules = {
        name: INITIALIZED / name for name in ('passive_initialized_certificate_rechecker_v2.py',
            'initialized_cold_obligations_v2.py', 'initialized_cold_identities_v2.py')}
    modules.update({name: TRACE / name for name in ('closed_python_surface.py', 'python_startup_roles_v2.py')})
    references = [INITIALIZED / name for name in ('cold-reference-wp-correct.c', 'cold-reference-wp-wrong.c')]
    policy = {
        'schema': 'initialized-cold-audit-policy-1', 'date': '2026-10-16 ET',
        'admitted': True, 'source_commit': COMMIT, 'project': PROJECT, 'raw': RAW,
        'original_entry': pin(INITIALIZED / 'linux_pair_entry_v4.py', RAW + '/control/linux_pair_entry_v4.py'),
        'source_policy': pin(pair_path, RAW + '/control/' + pair_path.name),
        'original_root_receipt': pin(receipt_path, CONTROL + '/' + receipt_path.name),
        'raw_manifest': context['raw_manifest'],
        'settled_lane': receipt['actual']['lane.json']['socket_lane'],
        'source_consumer_receipt_sha256': consumers[0]['canonical_sha256'],
        'reader_sha256': sha(source.read_bytes()),
        'reader_files': {name: pin(path, CONTROL + '/' + name) for name, path in modules.items()},
        'reader_admission': {'admitted': True, 'role': 'isolated-passive-cold-reader',
            'sys_path': pair['startup_roles']['package_sys_path'],
            'pycache_prefix': COLD + '/reader-source-cache',
            'environment': {'PYTHONPATH': PROJECT, 'PYTHONPYCACHEPREFIX': COLD + '/cache',
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': None,
                'PYTHONSAFEPATH': None, 'SETUPTOOLS_USE_DISTUTILS': None}},
        'records': rows, 'reference_directory': CONTROL,
        'root_duties': ['Independently review and admit this exact policy and V3 source before executing',
            'Verify staged physical reader/policy/reference/receipt bytes and selected Python runtime and exact environment',
            'Reconfirm immutable published source commit/Git readback and finite original process/lease settlement',
            'Capture the isolated passive reader result outside the original immutable raw tree'],
        'scope': 'Prepared concrete admission request; not executed or independently approved by its author. '
            'Original conditional partial initialized uint32 711/1107 pair only. The 1107 result is not_proven '
            'with one normal ensures timeout, never refuted. No source/body/hardware/current0.2/full28.',
        'provenance': {'root_execution_receipt': pin(receipt_path), 'passive_context': pin(context_path),
            'record_label_source': 'Fixed public param order [711,1107] and fixture directory indexes [0,1]; never selected by verdict',
            'reader_base': pin(INITIALIZED / 'initialized_cold_audit_v2.py'),
            'prior_independent_review': pin(INITIALIZED / 'independent-initialized-cold-v2-source-review-20261016.json')},
    }
    policy_path = HERE / 'initialized-cold-policy-04af74c1-v3.json'
    dump(policy_path, policy)
    controls = {source.name: pin(source, CONTROL + '/' + source.name)}
    controls.update({name: pin(path, CONTROL + '/' + name) for name, path in modules.items()})
    controls.update({path.name: pin(path, CONTROL + '/' + path.name) for path in references})
    controls[receipt_path.name] = pin(receipt_path, CONTROL + '/' + receipt_path.name)
    controls[policy_path.name] = pin(policy_path, CONTROL + '/' + policy_path.name)
    command = [pair['linux_launch_binding']['python'], '-I', '-B', '-X',
        'pycache_prefix=' + COLD + '/reader-source-cache', CONTROL + '/' + source.name,
        CONTROL + '/' + policy_path.name, sha(policy_path.read_bytes())]
    dump(HERE / 'initialized-cold-command-04af74c1-v3.json', {
        'date': '2026-10-16 ET', 'status': 'PREPARED_AWAITING_INDEPENDENT_REVIEW_AND_ROOT_ADMISSION',
        'scientific_execution': False, 'raw': COLD, 'source_commit': COMMIT, 'command': command,
        'environment': policy['reader_admission']['environment'], 'control_files': controls,
        'control_total_bytes': sum(row['bytes'] for row in controls.values()),
        'conditions': ['No extra PYTHON* environment variables; unset the three explicit null-valued selectors',
            'Create outer cache if needed, but reader-source-cache must remain absent before and after',
            'No writes inside original initialized pair raw; stdout/stderr captured only under this fresh cold raw',
            'Root supplies exact guarded launch and confirms finite process/lease settlement independently'],
    })
    dump(HERE / 'initialized-cold-v3-inverse.json', {
        'date': '2026-10-16 ET', 'base': pin(INITIALIZED / 'initialized_cold_audit_v2.py'),
        'successor': pin(source), 'unchanged_scientific_functions': True,
        'allowed_delta': ['module invocation example', 'one original_launch lane predicate replaced by validate_original_lane_v3',
            'new exact root receipt / raw / source / full lane / literal job / generation validator'],
        'inverse': 'Remove new validator; restore original_launch penultimate statement and module docstring; complete AST equality required',
        'original_v2_refusal_preserved': 'Actual job and raw basename differ in name ordering; V2 is retained unchanged',
    })


if __name__ == '__main__':
    build()
