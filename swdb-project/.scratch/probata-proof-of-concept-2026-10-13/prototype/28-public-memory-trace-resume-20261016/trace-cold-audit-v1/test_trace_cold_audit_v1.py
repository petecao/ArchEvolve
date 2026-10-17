"""2026-10-16 ET. Tiny synthetic/AST controls only; no actual audit or child."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
PROJECT = TRACE.parents[3]
H = lambda value: hashlib.sha256(value).hexdigest()


def deny_child(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('pure controls refuse ' + event)


sys.addaudithook(deny_child)


def load_source(path, namespace=None):
    result = dict(__name__='pure_control_' + path.stem, __file__=str(path))
    result.update(namespace or {})
    exec(compile(path.read_bytes(), str(path), 'exec'), result)
    return types.SimpleNamespace(**result)


READER = load_source(HERE / 'trace_cold_audit_v1.py')
COMMON = load_source(HERE / 'reviewed_cold_primitives_v1.py')
CONSTANTS = READER.parse_literal_bindings((TRACE / 'trace_fixture.py').read_text(),
    {'ENTRY', 'POLICY_ID', 'QUERY_PROTOTYPES', 'SCOPE', 'TRUST', 'WP_REFUSAL'})
CASE_NS = dict(CONSTANTS)
tree = ast.parse((TRACE / 'trace_cases.py').read_bytes())
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'case', 'source'}]
nodes += [node for node in tree.body if isinstance(node, ast.Assign) and any(
    isinstance(target, ast.Name) and target.id in {'C', 'CASES'} for target in node.targets)]
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-case-source-data>', 'exec'), CASE_NS)
ASSERTIONS = load_source(HERE / 'public_assertions_v1.py', {**CASE_NS, 'Path': Path, 'hashlib': hashlib, 're': re}).audit_public_assertions_v1


def synthetic_record(folder, case):
    """Input stand-in for assertion controls, never a claimed real proof entry."""
    library = folder / 'library'
    semantics = library / 'proof_semantics/entry.yaml'
    semantics.parent.mkdir(parents=True); semantics.write_bytes(b'synthetic-metadata-only\n')
    units = library / 'proof_units'; units.mkdir()
    (units / 'trust.cc').write_text(CASE_NS['source'](case))
    semantic_pin = {'id': CONSTANTS['ENTRY'], 'sha256': H(semantics.read_bytes())}
    entry = {'description': CONSTANTS['SCOPE'], 'calls': [{'supported': False} for _ in range(26)],
             'queries': [{'query': key, 'prototype': value, 'contract': CONSTANTS['WP_REFUSAL']}
                         for key, value in CONSTANTS['QUERY_PROTOTYPES'].items()], 'wp': {}, 'model': {},
             'rules': [{'id': name, 'statement': name, 'record_assumption': True}
                       for name in ('synthetic_trace_scope', 'trace_domain', 'history_visibility')] +
                      [{'id': name, 'statement': 'Retained unused boundary entry: ' + sentence, 'record_assumption': True}
                       for name, sentence in CONSTANTS['TRUST'].items()]}
    report_dir = folder / 'reports'; report_dir.mkdir()
    input_path = report_dir / 'job.c'
    text = '  swdb_dx_init();\n  swdb_dx_check_exit();\n/* swdb-anchor trust_fixture.contract */\n'
    text += ''.join('  dx_tile_data[' + str(index) + '][0] = (int) swdb_next();\n' for index in range(4))
    input_path.write_text(text)
    outputs = {}
    for name in ('cbmc_output', 'differential_c_output', 'differential_cxx_output'):
        path = report_dir / name; path.write_text(' end=done\n'); outputs[name] = path
    def pin(path, name=None):
        return {'path': str(path), 'sha256': H(path.read_bytes()), **({'name': name} if name else {})}
    record = {'pins': {'proof_semantics': semantic_pin}, 'verdict': case['expected_verdict'],
        'proof_setup_check': {'verdict': 'passed'}, 'settings': {'verifier_launched': True,
            'bounded_initialization': {'verdict': 'passed', 'model_policy': {'id': CONSTANTS['POLICY_ID'],
                'calls': sorted(CONSTANTS['QUERY_PROTOTYPES'])}}, 'agreement': {'verdict': 'agree', 'runs': 1},
            'proof_semantics': {'scope': 'synthetic abstract scalar event trace only',
                'exit_check': 'no pending abstract command at unit exit',
                'native_address_abi': 'scalar abstract cell/region/tile IDs; no caller pointer mapping',
                'counterexample_scope': 'abstract-model trace only; no hardware counterexample or source refinement',
                'source_imports': [{'binding': {'name': 'swdb_t28_' + name}, 'reason': None}
                    for name in sorted({action[0] for action in case['actions']})]}},
        'evidence': {'adapter_log': pin(input_path), 'reports': [pin(input_path, 'cbmc_input')] +
            [pin(path, name) for name, path in outputs.items()]},
        'assumptions': [{'reference': {'id': semantic_pin['id'] + '#' + rule['id'], 'sha256': semantic_pin['sha256']},
            'sentence': rule['statement'], 'kind': 'proof_semantics'} for rule in entry['rules']],
        'goals': [{'status': 'failure', 'property': 'swdb_reach.end', 'goal': 'reach.assertion.1'}]}
    if case['expected_verdict'] == 'refuted':
        expected = (CONSTANTS['ENTRY'] + '#' + case['expected_property'] if case['expected_property'] != 'postcondition'
                    else 'contract.dx100_trust_fixture#result.ensures1')
        record['counterexample'] = {'property': expected, 'replay': {'replayed': True, 'sanitizer': None, 'failed': [expected]}}
    return record, entry, semantics


class TraceColdTests(unittest.TestCase):
    def test_exact_twelve_reviewed_nodes_and_complete_public_suffix(self):
        original = (INIT / 'initialized_cold_audit_v2.py').read_text()
        generated = (HERE / 'reviewed_cold_primitives_v1.py').read_text()
        provenance = json.loads((HERE / 'trace-cold-primitive-provenance-v1.json').read_bytes())
        for name, digest in provenance['copies'].items():
            for text in (original, generated):
                node = next(node for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)
                self.assertEqual(H(ast.get_source_segment(text, node).encode()), digest)
        public = (TRACE / 'test_public_actual.py').read_text()
        source = next(node for node in ast.parse(public).body if isinstance(node, ast.FunctionDef) and node.name == 'test_actual_public_abstract_memory_trace')
        target = ast.parse((HERE / 'public_assertions_v1.py').read_text()).body[1]
        self.assertEqual([ast.dump(node) for node in source.body[6:]], [ast.dump(node) for node in target.body])
        self.assertEqual(len(target.body), 45)

    def test_synthetic_proven_and_refuted_assertion_inputs(self):
        for index in (0, 1, 5):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as folder:
                record, entry, semantics = synthetic_record(Path(folder), CASE_NS['CASES'][index])
                ASSERTIONS(record, entry, CASE_NS['CASES'][index], semantics)

    def test_public_goal_reach_capacity_and_skip_criteria_remain_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            case = CASE_NS['CASES'][0]; record, entry, semantics = synthetic_record(Path(folder), case)
            mutations = [lambda row: row['goals'].clear(),
                lambda row: row['goals'][0].update(status='success'),
                lambda row: row['goals'].append({'status': 'unknown', 'goal': 'q', 'property': 'p'}),
                lambda row: row['goals'].append({'status': 'failure', 'goal': 'q', 'property': 'swdb.ghost_capacity'}),
                lambda row: row['goals'].append({'status': 'failure', 'goal': 'q.unwind.1', 'property': 'unwind'}),
                lambda row: row['settings']['agreement'].update(runs=0),
                lambda row: row['settings'].update(verifier_launched=False)]
            for index, change in enumerate(mutations):
                bad = copy.deepcopy(record); change(bad)
                with self.subTest(index=index), self.assertRaises(AssertionError): ASSERTIONS(bad, entry, case, semantics)

    def test_refutation_requires_exact_replayed_nonsanitizer_property(self):
        with tempfile.TemporaryDirectory() as folder:
            case = CASE_NS['CASES'][1]; record, entry, semantics = synthetic_record(Path(folder), case)
            for key, value in (('replayed', False), ('sanitizer', 'AddressSanitizer'), ('failed', ['unrelated'])):
                bad = copy.deepcopy(record); bad['counterexample']['replay'][key] = value
                with self.subTest(key=key), self.assertRaises(AssertionError): ASSERTIONS(bad, entry, case, semantics)
            bad = copy.deepcopy(record); bad['counterexample']['property'] = 'other'
            with self.assertRaises(AssertionError): ASSERTIONS(bad, entry, case, semantics)

    def test_model_scope_unsupported_calls_and_owned_assumptions_are_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            case = CASE_NS['CASES'][0]; record, entry, semantics = synthetic_record(Path(folder), case)
            changes = [lambda value: value['calls'][0].update(supported=True),
                       lambda value: value['queries'][0].update(contract=r'requires \true;'),
                       lambda value: value.update(description='hardware theorem'),
                       lambda value: value['model'].update(layout={})]
            for index, change in enumerate(changes):
                bad = copy.deepcopy(entry); change(bad)
                with self.subTest(index=index), self.assertRaises(AssertionError): ASSERTIONS(record, bad, case, semantics)
            for index in (0, 3):
                bad = copy.deepcopy(record); bad['assumptions'].pop(index)
                with self.subTest(index=index), self.assertRaises(AssertionError): ASSERTIONS(bad, entry, case, semantics)

    def test_source_bound_cbmc_reader_reconstructs_goals_and_refuses_unknown(self):
        read = READER.cbmc_outcome_primitive(PROJECT, COMMON)
        result = types.SimpleNamespace(out_of_memory=False, timed_out=False, exit_code=0)
        data = [{'result': [{'property': 'reach.assertion.1', 'description': 'swdb_reach.end', 'status': 'FAILURE'},
                            {'property': 'unit.assertion.1', 'description': 'postcondition', 'status': 'SUCCESS'}]}]
        self.assertEqual(read(result, json.dumps(data))['verdict'], 'proven')
        data[0]['result'][1]['status'] = 'UNKNOWN'
        self.assertEqual(read(result, json.dumps(data))['verdict'], 'not_proven')
        data[0]['result'][1].update(status='FAILURE', description='swdb.ghost_capacity')
        self.assertEqual(read(result, json.dumps(data))['failure_class'], 'ghost_capacity')
        data[0]['result'][1].update(description='swdb.dx100_memory_domain')
        self.assertEqual(read(result, json.dumps(data))['failure_class'], 'memory_domain')
        data[0]['result'][1].update(property='unit.unwind.1', description='loop')
        self.assertEqual(read(result, json.dumps(data))['failure_class'], 'unwinding_bound_too_small')

    def test_regular_physical_bootstrap_refuses_hash_change_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / 'file'; path.write_bytes(b'passive')
            row = {'path': str(path), 'bytes': 7, 'sha256': H(b'passive')}
            self.assertEqual(READER.bootstrap_bytes(row), b'passive')
            alias = path.with_name('alias'); alias.symlink_to(path)
            with self.assertRaises(AssertionError): READER.bootstrap_bytes({**row, 'path': str(alias)})
            path.write_bytes(b'changed')
            with self.assertRaises(AssertionError): READER.bootstrap_bytes(row)

    def test_policy_refuses_unadmitted_arbitrary_helpers_and_duplicate_selection(self):
        rows = [{'id': str(index), 'case': str(index), 'record': {'path': '/' + str(index)}} for index in range(25)]
        policy = {'schema': 'trace-cold-audit-policy-1', 'admitted': True, 'source_commit': READER.COMMIT,
            'raw': READER.RAW, 'records': rows, 'reader_files': {name: {'path': '/control/' + name, 'sha256': digest}
                for name, digest in READER.READER_PINS.items()}}
        self.assertIs(READER.validate_admission_policy(policy), policy)
        for key, value in (('admitted', False), ('source_commit', '0' * 40), ('raw', '/other')):
            bad = copy.deepcopy(policy); bad[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): READER.validate_admission_policy(bad)
        bad = copy.deepcopy(policy); bad['reader_files']['public_assertions_v1.py']['sha256'] = '0' * 64
        with self.assertRaises(AssertionError): READER.validate_admission_policy(bad)
        bad = copy.deepcopy(policy); bad['records'][1] = copy.deepcopy(bad['records'][0])
        with self.assertRaises(AssertionError): READER.validate_admission_policy(bad)

    def test_exact_twentyfive_junit_and_seventyfive_phase_receipts(self):
        cases = CASE_NS['CASES']
        wanted = [READER.PACKET + '/test_public_actual.py::test_actual_public_abstract_memory_trace[' + row['name'] + ']'
                  for row in cases]
        expected = {'selection': wanted, 'source_root': '/selected/source', 'junit_classname': 'exact.class'}
        with tempfile.TemporaryDirectory() as folder:
            raw = Path(folder).resolve(); profile = raw / 'memory-trace-profile'; profile.mkdir()
            def dump(name, value): (profile / name).write_text(json.dumps(value))
            dump('collection.json', {'exit_code': 0, 'selected': wanted, 'expected': wanted})
            (profile / 'exit-code.txt').write_text('0\n')
            dump('pytest-arguments.json', ['-q', '--tb=short', '--rootdir', '/selected/source', '-p', 'no:cacheprovider',
                '--basetemp', str(profile / 'pytest'), '--junitxml', str(profile / 'junit.xml'), *wanted])
            root = ET.Element('testsuites'); suite = ET.SubElement(root, 'testsuite', tests='25', errors='0', failures='0', skipped='0')
            for node in wanted: ET.SubElement(suite, 'testcase', name=node.split('::')[-1], classname='exact.class')
            ET.ElementTree(root).write(profile / 'junit.xml')
            progress = [{'event': 'runtest_report', 'nodeid': node, 'when': phase, 'outcome': 'passed',
                         'duration': 0.01, 'longrepr': None, 'at_utc': '2026-10-16T20:00:00Z'}
                        for node in wanted for phase in ('setup', 'call', 'teardown')]
            path = profile / 'case-reports.jsonl'; path.write_text(''.join(json.dumps(row) + '\n' for row in progress))
            dump('junit-census.json', {'accepted': True, 'cases': 25, 'skipped': 0,
                'scope': 'workflow census only; every abstract proof/refutation and cold audit remain separate'})
            self.assertEqual(READER.workflow(expected, raw, cases, COMMON)['complete_case_phase_reports'], 75)
            for rows in (progress[:-1], [*progress[:1], {**progress[1], 'outcome': 'skipped'}, *progress[2:]],
                         [{**progress[0], 'when': 'call'}, *progress[1:]]):
                path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
                with self.assertRaises(AssertionError): READER.workflow(expected, raw, cases, COMMON)
            path.write_text(''.join(json.dumps(row) + '\n' for row in progress))
            suite.set('skipped', '1'); ET.ElementTree(root).write(profile / 'junit.xml')
            with self.assertRaises(AssertionError): READER.workflow(expected, raw, cases, COMMON)

    def test_literal_pytest_current_alias_is_not_a_second_physical_record(self):
        with tempfile.TemporaryDirectory() as folder:
            raw = Path(folder).resolve(); base = raw / 'memory-trace-profile/pytest'; base.mkdir(parents=True)
            expected = set()
            for index in range(25):
                proof = base / ('fixture' + str(index)) / 'records/proofs'; proof.mkdir(parents=True)
                path = proof / 'proof.yaml'; path.write_text('id: synthetic\n'); expected.add(str(path))
            (base / 'fixturecurrent').symlink_to(base / 'fixture24')
            self.assertEqual(READER.physical_record_members(raw), expected)
            self.assertEqual(len(list(base.glob('*/records/proofs/*.yaml'))), 26)
            (base / 'unadmitted-physical-fixture').mkdir()
            with self.assertRaises(AssertionError): READER.physical_record_members(raw)

    def test_scalar_model_text_equals_exact_production_factory_with_inert_layout_seam(self):
        constants = READER.parse_literal_bindings((TRACE / 'trace_fixture.py').read_text(), {'CONSTANTS'})['CONSTANTS']
        entry = {'id': CONSTANTS['ENTRY'], 'version': '0.2', 'constants': constants,
            'ghost': {'acsl': {'name': 'ghost.acsl'}}, 'model': {'state': {'name': 'state.h'}, 'c': {'name': 'model.h'}},
            'calls': [], 'queries': []}
        source = (PROJECT / 'swdb/proof_semantics.py').read_text(); tree = ast.parse(source)
        names = {'ghost_declarations', '_bounded_state', 'model_for'}
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        nodes += [node for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                  isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'GHOST_LINE', 'DECL_NAME'}]
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder).resolve(); model = fixture / 'library/proof_semantics/synthetic-memory-trace'; model.mkdir(parents=True)
            for name in ('ghost.acsl', 'logic.acsl', 'model.h', 'state.h'):
                (model / name).write_bytes((TRACE / name).read_bytes())
            # Full entry shape is independently frozen by the reader. This
            # stand-in chooses its documented generic scalar bounded-state arm,
            # while the exact production model_for AST builds the oracle text.
            namespace = {'re': re, 'Model': lambda **values: types.SimpleNamespace(**values),
                '_constants': lambda data, defines: data['constants'],
                'artifacts': types.SimpleNamespace(file_hash=lambda path: H(path.read_bytes()))}
            exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-source-model-for>', 'exec'), namespace)
            namespace['_model_state'] = lambda data, text, constants: namespace['_bounded_state'](text, constants)
            class InertLibrary:
                files = {entry['id']: model / 'ghost.acsl'}
                def get(self, name): self.assert_name(name); return entry
                def assert_name(self, name): assert name == entry['id']
                def resolve(self, reference): return model / reference['name']
            expected = namespace['model_for'](InertLibrary(), entry['id'])
            actual, objects = READER.generated_model(entry, fixture, PROJECT)
            self.assertEqual(actual, expected.c_text)
            self.assertEqual(objects, [{'name': name, 'elements': size} for name, size in expected.tile_objects])

    def test_exact_retained_compact_launch_metadata_and_inverse_refusals(self):
        # Exercise only the metadata guard function with frozen compact inputs.
        # No actual record/goal audit, remote filesystem or child is accessed.
        context = json.loads((HERE / 'passive-trace-v4-context.json').read_bytes())
        policy = json.loads((HERE / 'trace-cold-policy-template-04af74c1-v1.json').read_bytes())
        expected_bytes = (TRACE / 'linux_trace_policy_04af74c1_v4.json').read_bytes()
        expected = json.loads(expected_bytes)
        root_bytes = (TRACE.parent.parent / 'evidence/t28-trace-v4-root-execution-20261016.json').read_bytes()
        self.assertEqual(H(root_bytes), READER.ROOT_RECEIPT_SHA)
        payload = copy.deepcopy(context['json'])
        raw = Path(READER.RAW)
        class MetadataPath(type(Path())):
            def read_bytes(self): return json.dumps(payload[str(self.relative_to(raw))]).encode()
        class MetadataPhysical:
            def read(self, row):
                if row == policy['source_policy']: return expected_bytes
                assert row == policy['root_execution_receipt']; return root_bytes
            def pin(self, path, wanted=None, size=None):
                value = context['raw_manifest']['files'][str(Path(path).relative_to(raw))]
                assert wanted is None or wanted == value['sha256']
                return value['sha256']
        def run():
            return READER.original_launch(policy, expected, MetadataPath(raw), MetadataPhysical(), COMMON)
        self.assertEqual(run()['lane']['lease_generation'], 635)
        mutations = [('resources.json', 'timed_out', True), ('outer-resources.json', 'out_of_memory', True),
                     ('resources.json', 'exit_code', 1), ('launch.json', 'workers', 2)]
        for name, key, value in mutations:
            old = payload[name][key]; payload[name][key] = value
            with self.subTest(name=name, key=key), self.assertRaises(AssertionError): run()
            payload[name][key] = old
        payload['memory-trace-linux-role-admission.json']['live_lane']['fd9_matches_lease'] = False
        with self.assertRaises(AssertionError): run()
        payload['memory-trace-linux-role-admission.json']['live_lane']['fd9_matches_lease'] = True
        payload['lane.json']['socket_lane']['lease_generation'] = 636
        policy['settled_lane']['lease_generation'] = 636
        with self.assertRaises(AssertionError): run()


if __name__ == '__main__':
    unittest.main(verbosity=2)
