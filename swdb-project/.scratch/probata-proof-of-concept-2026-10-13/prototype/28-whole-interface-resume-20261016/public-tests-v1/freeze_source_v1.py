"""2026-10-16 ET. Freeze an unmaterialized public-test source proposal only.

This author parses source/JSON and pins local files. It never imports a proposed
test, swdb, pytest, or a tool; it never materializes fixtures or runs commands.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
WHOLE = ROOT.parent
PROJECT = WHOLE.parents[3]
DATE = '2026-10-16 ET'


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'ctypes.')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('source author forbids child/native/network execution')
    if event == 'import' and str(args[0]).split('.')[0] in ('swdb', 'pytest'):
        raise RuntimeError('source author forbids project/test imports')


sys.addaudithook(audit)


def dump(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def document(path):
    def pairs(rows):
        out = {}
        for key, value in rows:
            assert key not in out, 'duplicate author JSON key'
            out[key] = value
        return out
    return json.loads(path.read_bytes(), object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(AssertionError('nonfinite author JSON')))


def pin(path):
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def assignment(tree, name):
    return next(node.value for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))


def schema(properties, required=None):
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
        'additionalProperties': False, 'properties': properties,
        'required': list(properties) if required is None else required}


def schemas():
    absolute = {'type': 'string', 'pattern': '^/'}
    sha = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
    semantic = schema({'id': {'type': 'string', 'minLength': 1}, 'sha256': sha})
    physical = schema({'path': absolute, 'bytes': {'type': 'integer', 'minimum': 1, 'maximum': 8388608}, 'sha256': sha})
    candidate = schema({'schema': {'const': 'checked-whole-positive-candidate-profile-1'},
        'candidate': {'type': 'string', 'pattern': '^candidate\\.'}, 'contract': semantic,
        'prepared_unit': physical, 'entry': semantic, 'library': absolute, 'records': absolute, 'runs': absolute})
    candidate['description'] = DATE + '. One separately prepared positive SourceUnit candidate; no summary record attribution.'
    dump('candidate-profile.schema.json', candidate)
    environment = {'type': 'object', 'additionalProperties': {'type': 'string'}}
    common = {'python': absolute, 'producer_project': absolute, 'environment': environment,
        'required_skips': {'const': 0}, 'sequential_workers': {'const': 1}}
    argv = {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}}
    actual = schema({**common, 'required_count': {'const': 35},
        'per_case_timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 1800},
        'jobs': {'type': 'array', 'minItems': 35, 'maxItems': 35,
            'items': schema({'case_id': {'type': 'string'}, 'argv': argv, 'cwd': absolute})}})
    candidate_plan = schema({**common, 'required_count': {'const': 1},
        'timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 1800}, 'argv': argv, 'cwd': absolute})
    for name, value in [('actual-command-plan.schema.json', actual), ('candidate-command-plan.schema.json', candidate_plan)]:
        value['description'] = DATE + '. Root-selected exact normal CLI plan. Root guard/environment admission remains separate; ownership tokens are never serialized.'
        dump(name, value)


def inputs():
    value = document(ROOT / 'required-portable-input-map-v1.json')
    value['quiet_fixture']['required_project_configuration'] = [
        'byte-identical selected schemas/ tree, including schemas/library/library_entry.schema.json',
        'byte-identical selected vocab/ tree required by normal validate',
        'all project-root portable normative files referenced by the selected library closure']
    value['quiet_fixture']['normal_schema_consistency'] = 'The export must preserve selected schema/vocabulary bytes; in-process Library uses the installed schema, and the normal CLI validates the exported configuration.'
    value['actual35']['profile_schema'] = 'actual-profile.schema.json'
    value['actual35']['selection_schema'] = 'actual-selection.schema.json'
    value['actual35']['command_plan_schema'] = 'actual-command-plan.schema.json'
    value['positive_candidate1']['profile_schema'] = 'candidate-profile.schema.json'
    value['positive_candidate1']['selection_schema'] = 'actual-selection.schema.json'
    value['positive_candidate1']['command_plan_schema'] = 'candidate-command-plan.schema.json'
    value['positive_candidate1']['root_admission_pin'] = None
    value['positive_candidate1']['runtime_pin'] = None
    value['quiet_fixture']['required_origin_receipts'] = [
        'actual final producer union and selected method identities',
        'genuine complete source/ABI/body/call preparations from the final profile',
        'actual normal validate result for this exported entry closure']
    value['installation_gate'] = 'Do not copy the proposed tests to tests/ until the real fixture export and this exact final producer are prepared and reviewed; integration profiles require separate actual admission.'
    dump('required-portable-input-map-v1.json', value)


def verify():
    paths = sorted((ROOT / 'proposed').rglob('*.py'))
    trees = {path: ast.parse(path.read_bytes(), filename=str(path)) for path in paths}
    assert len(trees) == 4
    helper = trees[ROOT / 'proposed/tests/testkit/dx100_whole_interface_checked.py']
    calls = ast.literal_eval(assignment(helper, 'CALLS'))
    cases = ast.literal_eval(assignment(helper, 'CASES'))
    assert len(calls) == len(set(calls)) == 26
    assert len(cases) == len({row['case_id'] for row in cases}) == 35
    design = document(WHOLE / 'new-0.2-contract-design-v1.json')
    assert set(calls) == {row['call'] for row in design['calls']}
    assert sum(len(row['source_declarations']) for row in design['calls']) == 27
    assert sum(len(row['typed_arity_instances']) for row in design['calls']) == 132
    predictions = document(WHOLE / 'finite-trace-public-v4/predicted-public-corpus.json')
    predicted = {row['id']: 'proven' if row['prediction'] == 'predicted_valid' else 'refuted' for row in predictions['cases']}
    finite = {row['case_id'].removeprefix('finite-'): row['expected_verdict'] for row in cases if row['kind'] == 'TraceUnit'}
    assert len(predicted) == len(finite) == 30 and finite == predicted
    assert all(row['actual_verdict'] is None for row in predictions['cases'])
    registry = ast.parse((WHOLE / 'source-unit-registry-v2/unit_policy_registry_v2.py').read_bytes())
    names = {name: ast.literal_eval(assignment(registry, name)) for name in ('FIRST_SHA', 'MEMORY_SHA')}
    class Values(ast.NodeTransformer):
        def visit_Name(self, node):
            assert node.id in names
            return ast.copy_location(ast.Constant(names[node.id]), node)
    functions = ast.literal_eval(Values().visit(assignment(registry, 'FUNCTIONS')))
    registered = {(function, ident) for function, _, rows in functions for _, ident in rows}
    source = {(row['function'], row['contract_id']) for row in cases if row['kind'] == 'SourceUnit'}
    assert source == registered and len(source) == 5
    selected_cases = document(ROOT / 'required-cases-v1.json')
    assert selected_cases['cases'] == list(cases) and selected_cases['actual_outcomes'] is None
    documents = {path.name: document(path) for path in sorted(ROOT.glob('*.json')) if path.name not in ('source-packet-v1.json', 'source-verification-v1.json')}
    for name, value in documents.items():
        if name.endswith('.schema.json'):
            assert value['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
            assert value['additionalProperties'] is False and set(value['required']) <= set(value['properties'])
    metadata = documents['required-portable-input-map-v1.json']
    assert metadata['state'] == 'unmaterialized; source proposal only'
    for section, keys in [('quiet_fixture', ('manifest_sha256',)),
        ('actual35', ('profile_pin', 'command_plan_pin', 'root_admission_pin', 'runtime_pin')),
        ('positive_candidate1', ('profile_pin', 'command_plan_pin', 'root_admission_pin', 'runtime_pin'))]:
        assert all(metadata[section][key] is None for key in keys)
    forbidden = []
    for path, tree in trees.items():
        assert not path.name.startswith('test_') or path.name == 'test_dx100_whole_interface_checked.py'
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('skip', 'skipif', 'xfail', 'importorskip'):
                forbidden.append((str(path), node.lineno))
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or '').startswith(('_pytest', 'unittest.mock'))
    assert not forbidden
    quiet = trees[ROOT / 'proposed/tests/test_dx100_whole_interface_checked.py']
    assert len([node for node in quiet.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]) == 5
    assert not (ROOT / 'proposed/tests/fixtures').exists()
    assert not list(ROOT.rglob('manifest.json'))
    legacy = pin(PROJECT / 'library/proof_semantics/dx100_bfs_0_1.yaml')
    assert legacy['sha256'] == ast.literal_eval(assignment(helper, 'LEGACY_SHA'))
    return {'date': DATE, 'scope': 'source/AST/JSON consistency only',
        'checks': ['4 proposed Python modules parse without import', 'all JSON documents parse with unique keys',
            '26 names/27 declarations/132 instances match pinned design', '5 exact source contract/function tuples match actual closed registry',
            '30 finite predictions and 35 exact case tuples match frozen preparation', 'no skip/xfail/importorskip calls or mock imports',
            'unmaterialized input pins stay null and no fixture manifest exists', 'old0.1 physical SHA matches literal'],
        'static_test_census': {'quiet': 30, 'explicit_summary_profile': 35, 'separate_positive_candidate_profile': 1},
        'runtime_pytest_cases_executed': 0, 'project_or_pytest_imports': 0, 'compiler_native_verifier_SSH_CLI_execution': False,
        'fixture_or_profile_materialized': False, 'legacy_entry': legacy}


def freeze():
    schemas()
    inputs()
    verification = verify()
    dump('source-verification-v1.json', verification)
    own = sorted(path for path in ROOT.rglob('*') if path.is_file() and path.name != 'source-packet-v1.json')
    basis = [PROJECT / path for path in (
        'tests/conftest.py', 'swdb/library.py', 'swdb/proof_semantics.py', 'swdb/dx100_whole_checked.py',
        'swdb/proof.py', 'swdb/store.py', 'swdb/level_rule.py', 'swdb/handoff_level.py', 'swdb/wp_adapter.py',
        'swdb/cbmc_adapter.py', 'swdb/cbmc_translator.py', 'swdb/paths.py',
        'schemas/library/library_entry.schema.json', 'library/proof_semantics/dx100_bfs_0_1.yaml')]
    basis += [WHOLE / path for path in (
        'new-0.2-contract-design-v1.json', 'source-unit-registry-v2/unit_policy_registry_v2.py',
        'finite-trace-public-v4/source-packet-v4.json', 'finite-trace-public-v4/predicted-public-corpus.json',
        'finite-trace-public-v4/proposed/swdb/_dx100_finite/context_rule_scope_v1.py',
        'finite-trace-public-v4/proposed/swdb/_dx100_finite/finite_checks_v1.py',
        'finite-trace-public-v4/proposed/swdb/dx100_finite_trace_adapter.py')]
    packet = {'schema': 'checked-whole-public-tests-source-proposal-1', 'date': DATE,
        'status': 'frozen source proposal; real fixture and actual integration profiles unmaterialized',
        'files': [pin(path) for path in own], 'basis': [pin(path) for path in basis],
        'verification': verification, 'public_api_or_scientific_acceptance': False,
        'required_next_step': 'genuine final producer/profile preparation, fixture export, independent review and separate root actual admission'}
    dump('source-packet-v1.json', packet)
    print(json.dumps({'source_packet': pin(ROOT / 'source-packet-v1.json'), 'verification': pin(ROOT / 'source-verification-v1.json'),
        'static_test_census': verification['static_test_census'], 'actual_cases_executed': 0}, sort_keys=True))


if __name__ == '__main__':
    freeze()
