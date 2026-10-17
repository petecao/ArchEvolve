"""2026-10-16 ET. No-child source/metadata controls, no actual profile derivation."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent


def no_child(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'}:
        raise AssertionError('child/network event forbidden in pure controls: ' + event)
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('project import forbidden in pure controls')


sys.addaudithook(no_child)
M = SimpleNamespace(**runpy.run_path(str(HERE / 'profile_builder_v1.py')))
P = SimpleNamespace(**runpy.run_path(str(HERE / 'pair_plan_v1.py')))


def leaf(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError('missing exact source nodes')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class ProfileControls(unittest.TestCase):
    def test_exact_json_no_last_wins(self):
        self.assertEqual(M.parse(b'{"type":1}'), {'type': 1})
        for raw in (b'{"type":1,"type":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises((M.Refused, ValueError)):
                M.parse(raw)

    def test_actual_failed_v8_capture_refuses(self):
        path = POC / 'evidence/t28-capture-v8-root-observation-20261016t2130z.json'
        value = json.loads(path.read_bytes())['actual']['component/result.json']
        self.assertEqual(value['error']['message'], 'expanded compiler stream limit exceeded')
        with self.assertRaisesRegex(M.Refused, 'failed, partial'):
            M.require_capture(value)
        for change in ({'accepted': False}, {'error': {'type': 'Refused'}}, {'after_input_errors': ['changed']},
                       {'bytecode_cache_present': True}, {'finalization_refusal': 'changed'}):
            candidate = {'accepted': True, 'error': None, 'after_input_errors': [], 'bytecode_cache_present': False}
            candidate.update(change)
            with self.assertRaises(M.Refused):
                M.require_capture(candidate)

    def test_no_pending_transport_self_authorization(self):
        self.assertEqual(M.INGRESS, 'reviewed-production-route-v3-complete-capture')
        source = ast.parse((HERE / 'profile_builder_v1.py').read_text())
        derive = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == 'derive')
        self.assertIn('source.complete_capture', ast.unparse(derive))
        self.assertIn('source.CAPTURE_KIND == request[\'capture\'][\'kind\']', ast.unparse(derive))
        self.assertNotIn('filter(', ast.unparse(derive))
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and (node.module or '').startswith('swdb')
                             for node in source.body))

    def test_split_original_and_producer_project_roles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); original = root / 'immutable2baf'; producer = root / 'newproducer'
            original.mkdir(); producer.mkdir()
            dependencies = [{'path': str(original / 'apps/dx100/benchmarks/API' / name)}
                            for name in ('MAA.hpp', 'MAA_gem5.hpp')]
            observation = {'groups': [{'label': label, 'dependencies': dependencies} for label in ('caller', 'abi')]}
            with patch.dict(os.environ, {'SWDB_HOME': str(original)}):
                M.original_project_role(str(original), observation)
                with self.assertRaisesRegex(M.Refused, 'SWDB_HOME'):
                    M.original_project_role(str(producer), observation)
            with patch.dict(os.environ, {'SWDB_HOME': str(producer)}):
                with self.assertRaisesRegex(M.Refused, 'header paths'):
                    M.original_project_role(str(producer), observation)

    def test_complete_26_inventory_deletion_refuses(self):
        design = json.loads((WHOLE / 'new-0.2-contract-design-v1.json').read_bytes())
        declarations = [{'name': row['call']} for row in design['calls'] for _ in row['source_declarations']]
        M.source_inventory(design, declarations)
        self.assertEqual((len(design['calls']), len(declarations)), (26, 27))
        for index in range(26):
            candidate = copy.deepcopy(design); del candidate['calls'][index]
            with self.assertRaises(M.Refused):
                M.source_inventory(candidate, declarations)
        with self.assertRaises(M.Refused):
            M.source_inventory(design, declarations[:-1])

    def test_contract_hash_order_and_pair_model_identity(self):
        proof = {'root': 'library', 'path': 'proof_units/source.cpp', 'sha256': M.SOURCE_SHA}
        contracts = M.unit_contracts(proof); rows = M.contract_rows(contracts)
        self.assertEqual([row['expected_result'] for row in rows], [79, 80])
        self.assertNotEqual(rows[0]['sha256'], rows[1]['sha256'])
        for value in (79, 80):
            self.assertEqual(M.digest(contracts[value]), rows[value - 79]['sha256'])
            self.assertNotIn('semantics', M.canonical(contracts[value]).decode())
            self.assertEqual(contracts[value]['proof_unit'], {'source': proof, 'function': M.FUNCTION})
        a, b = (copy.deepcopy(contracts[value]) for value in (79, 80))
        for value in (a, b):
            del value['id']; del value['clauses']
        self.assertEqual(a, b)
        tree = ast.parse((HERE / 'profile_builder_v1.py').read_text())
        derive = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'derive')
        self.assertFalse(any(isinstance(node, ast.Constant) and type(node.value) is int and node.value in (79, 80)
                             for node in ast.walk(derive)))
        self.assertFalse(any(isinstance(node, ast.Name) and node.id in ('contracts', 'contract_rows', 'unit_contracts')
                             for node in ast.walk(derive)))
        # The fixed dependency order has no back-edge from contracts to semantics.
        edges = {'contracts': [], 'manifest': [], 'method': ['manifest'], 'source_policy': ['contracts', 'manifest'],
                 'semantics': ['source_policy'], 'context': [], 'globals': ['context'], 'receiver': ['globals', 'context']}
        done = set()
        while len(done) < len(edges):
            ready = {name for name, dependencies in edges.items() if set(dependencies) <= done} - done
            self.assertTrue(ready); done.update(ready)

    def test_six_distinct_owned_context_rules(self):
        namespace = runpy.run_path(str(WHOLE / 'receiver-state-draws-v2/receiver_state_draws_v2.py'))
        expected = namespace['PREMISES']; owner = 'Explicit root owner'
        rows = [{'rule': name, 'statement': text, 'owner': owner, 'record_assumption': True}
                for name, text in sorted(expected.items())]
        rules = M.context_rules(rows, owner, expected)
        self.assertEqual(len({row['id'] for row in rules}), 6)
        self.assertTrue(all(row['statement'].endswith(' Owner: ' + owner + '.') for row in rules))
        for mutation in ('owner', 'statement', 'record_assumption', 'delete'):
            candidate = copy.deepcopy(rows)
            if mutation == 'delete':
                candidate.pop()
            else:
                candidate[0][mutation] = False if mutation == 'record_assumption' else 'changed'
            with self.assertRaises(M.Refused):
                M.context_rules(candidate, owner, expected)

    def test_compiler_numeric_owner_not_filled_by_builder(self):
        request = {'owner': 'Root owner', 'design': {'sha256': 'd' * 64},
            'capture': {'observation': {'sha256': 'c' * 64}}, 'physical_inputs': {'closed': 'binding'}}
        expected = {'compiler_source_projection': 'compiler statement', 'numeric_runtime_profile': 'numeric statement'}
        rows = [{'id': name, 'statement': text, 'assumed': {'owner': 'Root owner'}, 'record_assumption': True}
                for name, text in expected.items()]
        receipt = {'schema': 'root-owned-checked-source-premises-1', 'owner': 'Root owner', 'design_sha256': 'd' * 64,
            'capture_observation_sha256': 'c' * 64, 'physical_inputs_sha256': M.digest(request['physical_inputs']), 'rules': rows}
        self.assertEqual(M.external_owned_rules(receipt, request, expected), rows)
        for key in ('owner', 'design_sha256', 'capture_observation_sha256', 'physical_inputs_sha256', 'rules'):
            changed = copy.deepcopy(receipt); changed[key] = [] if key == 'rules' else 'changed'
            with self.assertRaises(M.Refused):
                M.external_owned_rules(changed, request, expected)

    def test_exact_physical_pin_refuses_alias_and_content_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / 'input'; path.write_bytes(b'exact')
            row = M.pin(path, b'exact'); self.assertEqual(M.read(row), b'exact')
            alias = root / 'alias'; alias.symlink_to(path)
            with self.assertRaises(M.Refused):
                M.read({**row, 'path': str(alias)})
            path.write_bytes(b'other')
            with self.assertRaises(M.Refused):
                M.read(row)

    def test_no_overwrite_or_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            rows = M.write_new_files(root, {'proof_semantics/a.json': b'{}'})
            self.assertEqual(rows[0]['sha256'], M.sha(b'{}'))
            for name in ('proof_semantics/a.json', '../escape', '/absolute', 'a//b', 'a/./b'):
                with self.assertRaises(M.Refused):
                    M.write_new_files(root, {name: b'{}'})

    def test_real_default_root_pair_commands(self):
        contracts = M.contract_rows(M.unit_contracts({'root': 'library', 'path': 'proof_units/source.cpp', 'sha256': M.SOURCE_SHA}))
        profile = {'contracts': contracts, 'semantics_content_sha256': 's' * 64,
                   'method_content_sha256': 'm' * 64, 'producer_manifest_sha256': 'p' * 64}
        selection = {name: '/admitted/' + name for name in ('python', 'original_project', 'producer_project', 'records',
            'runs', 'verifier_lock', 'pycache', 'compiler_wrapper', 'cbmc')}
        selection.update(library_root='/admitted/library', root_admission_receipt={'path': '/root/receipt', 'bytes': 1, 'sha256': 'a' * 64})
        plan = P.plan(profile, selection)
        self.assertEqual([row['expected_result'] for row in plan['jobs']], [79, 80])
        self.assertEqual(plan['environment']['SWDB_HOME'], '/admitted/original_project')
        self.assertEqual(plan['environment']['PYTHONPATH'], '/admitted/producer_project')
        self.assertTrue(all(row['argv'][row['argv'].index('--bounds') + 1] == '{"threads":1}' for row in plan['jobs']))
        namespace = {'Path': Path, 'paths': SimpleNamespace(HOME=Path('/admitted/original_project'), RECORDS=Path('/admitted/original_project/records'))}
        leaf(WHOLE.parents[3] / 'swdb/library.py', {'default_root'}, namespace)
        self.assertEqual(namespace['default_root'](selection['records']), Path(selection['library_root']))
        with self.assertRaises(ValueError):
            P.plan(profile, {**selection, 'library_root': '/wrong/library'})

    def test_method_fixture_refused_and_manifest_changes_identity(self):
        identities = {'setup': {'proof_setup_check': {'version': '1', 'sha256': 's' * 64}},
            'lowering': {'naming_rules': {'id': 'names', 'sha256': 'n' * 64}, 'c_lowering': {'id': 'lower', 'sha256': 'l' * 64}},
            'translator': {'id': 'translate', 'sha256': 't' * 64}}
        base = {'kind': 'method_version', 'evidence_kind': 'execution', 'sequence': 7, 'checks': {}, 'c_lowering': {}}
        manifest = {'schema': 'swdb-dx100-whole-producers-1', 'files': {'one': {'sha256': '1' * 64}}}
        a = M.build_method(base, identities, manifest)
        b = M.build_method(base, identities, {**manifest, 'files': {'two': {'sha256': '2' * 64}}})
        self.assertNotEqual(M.digest(a), M.digest(b)); self.assertEqual(base['sequence'], 7)
        with self.assertRaises(M.Refused):
            M.build_method({**base, 'evidence_kind': 'contract_fixture'}, identities, manifest)

    def test_exact_lowering_identity_recipe_without_probe(self):
        original_path = WHOLE / 'production-route-v3/proposed/swdb/c_lowering.py'
        original = ast.parse(original_path.read_text())
        function = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == 'identity')
        names = {node.args[0].value for node in ast.walk(function) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == 'with_name'
            and len(node.args) == 1 and isinstance(node.args[0], ast.Constant)}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for name in names | {'c_lowering.py', 'terminal.py', 'effects.py', 'wrapper', 'driver'}:
                (root / name).write_bytes(b'selected ' + name.encode())
            (root / 'c_lowering.py').write_text(original_path.read_text())
            wrapper = M.pin(root / 'wrapper', (root / 'wrapper').read_bytes())
            driver = M.pin(root / 'driver', (root / 'driver').read_bytes())
            observed = {'schema': 'root-selected-compiler-observation-1', 'command': [wrapper['path']], 'version': '22.1.8',
                'wrapper': wrapper, 'driver': driver, 'runtime_identity': {'command': [wrapper['path']],
                    'driver': {key: driver[key] for key in ('path', 'sha256')}}}
            def forbidden(*args, **kwargs):
                raise AssertionError('compiler/runtime probe would execute')
            namespace = {'__file__': str(root / 'c_lowering.py'), 'Path': Path, 'hashlib': hashlib, 'json': json,
                'locate': forbidden, 'stdlib_provenance': SimpleNamespace(runtime_identity=forbidden),
                'terminal_release': SimpleNamespace(__file__=str(root / 'terminal.py')),
                'cpu_effects': SimpleNamespace(__file__=str(root / 'effects.py')),
                'bounded_initialization': SimpleNamespace(identity=lambda: {'sha256': 'bounded identity'}),
                'wp_pointer_bounds': SimpleNamespace(identity=lambda: {'sha256': 'pointer identity'}),
                'TOOL_ID': 'swdb-c-lowering', 'TOOL_VERSION': '1', 'naming_rules': lambda: {'id': 'names', 'sha256': 'n' * 64},
                '_binary': lambda text: Path(text), '_file_sha256': lambda path: M.sha(path.read_bytes())}
            module = SimpleNamespace(**namespace)
            actual = M.lowering_identity_without_probe(module, observed)
            expected_namespace = dict(namespace)
            expected_namespace.update(locate=lambda: SimpleNamespace(command=observed['command'], version='22.1.8', missing=False),
                stdlib_provenance=SimpleNamespace(runtime_identity=lambda tool: observed['runtime_identity']))
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(original_path), 'exec'), expected_namespace)
            self.assertEqual(actual, expected_namespace['identity']())
            for change in ({'command': ['clang++']}, {'command': [wrapper['path'], '-DUNREVIEWED']},
                           {'runtime_identity': {**observed['runtime_identity'], 'driver': {key: wrapper[key] for key in ('path', 'sha256')}}}):
                with self.assertRaises(M.Refused):
                    M.lowering_identity_without_probe(module, {**observed, **change})

    def test_exact_reviewed_producer_basis(self):
        raw = (HERE / 'normal-producer-basis-v1.json').read_bytes()
        self.assertEqual(M.sha(raw), M.BASIS_SHA)
        value = M.parse(raw); self.assertEqual(len(value['files']), 36)
        self.assertEqual(len({row['relative'] for row in value['files']}), 36)
        for row in value['files']:
            path = HERE / 'dx100_checked_native.proposed.py' if row['relative'] == 'swdb/dx100_checked_native.py' else WHOLE / 'production-route-v3/proposed' / row['relative']
            self.assertEqual(len(path.read_bytes()), row['bytes'])
            self.assertEqual(M.sha(path.read_bytes()), row['sha256'])

    def test_preparation_entry_never_launches_children(self):
        namespace = leaf(HERE / 'profile_prepare_v1.py', {'deny_child'}, {})
        for event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'):
            with self.assertRaises(RuntimeError):
                namespace['deny_child'](event, ())
        namespace['deny_child']('open', ())
        source = ast.parse((HERE / 'profile_prepare_v1.py').read_text())
        calls = [ast.unparse(node.func) for node in ast.walk(source) if isinstance(node, ast.Call)]
        self.assertFalse(any(name.startswith(('subprocess.', 'socket.', 'os.system', 'os.exec')) for name in calls))
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and (node.module or '').startswith('swdb')
                             for node in source.body))


class NativePhysicalRoleControls(unittest.TestCase):
    def native(self, root):
        raw = (WHOLE / 'runtime-projection-v2/runtime_projection_v2.py').read_bytes()
        path = root / 'newproducer/swdb/_dx100_whole/runtime_projection_v2.py'; path.parent.mkdir(parents=True); path.write_bytes(raw)
        class Unit:
            pass
        class Reads:
            def __init__(self, library): pass
            def absolute(self, row, **kwargs): return M.read(row, **kwargs)
            def recheck(self): pass
        receiver_namespace = {'dataclass': __import__('dataclasses').dataclass, 'Path': Path, 're': __import__('re'),
            'need': M.need, 'exact': M.exact, 'digest': lambda text: text if __import__('re').fullmatch('[0-9a-f]{64}', text) else M.need(False, 'digest')}
        leaf(WHOLE / 'receiver-state-draws-v2/receiver_state_draws_v2.py', {'Pin'}, receiver_namespace)
        source = SimpleNamespace(SourceUnit=Unit, need=M.need, Inputs=Reads, receiver=SimpleNamespace(Pin=receiver_namespace['Pin']),
            binder=SimpleNamespace(inventory=lambda project: []))
        projection = SimpleNamespace(__file__=str(path), projection=lambda *args, **kwargs:
            {'cxx_text': '#include "dws_original_runtime.hpp"', 'runtime_header': '', 'edit_manifest': {}, 'runtime_identity': {}})
        namespace = {'source': source, 'projection': projection, 'json': json, 'hashlib': hashlib, 'Path': Path,
            'PROJECTION_SHA': M.sha(raw), 'KIND': 'dx100-whole-source-preserving-cxx-v2'}
        leaf(HERE / 'dx100_checked_native.proposed.py', {'view'}, namespace)
        unit = Unit(); unit.selection = SimpleNamespace(library=object(), project=root / 'immutable2baf')
        unit.normalized_tu = {}; unit.abi = {}; unit.atlas = {}; unit.allocations = []
        unit.unit_preparation = {}; unit.statement_preparation = {'assertion_header_pin': {'selected': 'header'}}
        unit.receiver_preparation = SimpleNamespace(binding_json=b'{}', c_text='', draw_plan_json=b'{}', integration_plan_json=b'{}')
        unit.receiver_policy_pin_json = b'{}'; unit.certificate = {'captured_source_path': '/original/source.cpp'}
        policy = {'native_projection': {'kind': namespace['KIND'], 'producer': M.pin(path, raw), 'assertion_header': {'selected': 'header'}},
            'caller_mangled': '_Z30whole_interface_source_fixturev', 'thread': 0}
        return namespace['view'], unit, policy, path, raw

    def test_real_native_view_split_role_positive_and_refusals(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); view, unit, policy, path, raw = self.native(root)
            unit.policy_json = M.canonical(policy); self.assertIn('cxx_text', view(unit))
            wrong = root / 'wrong.py'; wrong.write_bytes(raw)
            alias = root / 'alias.py'; alias.symlink_to(path)
            candidates = [M.pin(wrong, raw), M.pin(alias, raw), {**M.pin(path, raw), 'sha256': '0' * 64},
                          {'root': 'project', 'path': str(path), 'sha256': M.sha(raw)}, {}]
            for selected in candidates:
                candidate = copy.deepcopy(policy); candidate['native_projection']['producer'] = selected
                unit.policy_json = M.canonical(candidate)
                with self.assertRaises((M.Refused, KeyError)):
                    view(unit)

    def test_narrow_native_inverse(self):
        base = (WHOLE / 'production-route-v3/proposed/swdb/dx100_checked_native.py').read_text()
        candidate = (HERE / 'dx100_checked_native.proposed.py').read_text()
        old = "raw = reads.portable(selected['producer'])\n    actual = Path(projection.__file__)\n    source.need(reads.path(selected['producer']) == actual and hashlib.sha256(raw).hexdigest() == PROJECTION_SHA,"
        new = "raw = reads.absolute(selected['producer'], limit=4 * 1024 * 1024)\n    actual = Path(projection.__file__)\n    source.need(source.receiver.Pin.parse(selected['producer']).path == str(actual)\n        and hashlib.sha256(raw).hexdigest() == PROJECTION_SHA,"
        self.assertEqual(candidate.replace(new, old), base)


if __name__ == '__main__':
    unittest.main(verbosity=2)
