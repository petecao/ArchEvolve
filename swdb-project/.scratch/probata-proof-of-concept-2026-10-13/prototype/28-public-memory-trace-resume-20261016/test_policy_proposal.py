"""2026-10-16 ET. Pure proposal controls with explicit library/model doubles.

Only the proposed Python hash-gate AST is executed. No production module,
compiler, CLI, native binary, solver, SSH or process API is imported/launched.
"""
import ast
import copy
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import trace_fixture as fixture


@dataclass(frozen=True)
class ModelDouble:
    entry: str
    sha256: str
    c_text: str
    queries: tuple
    calls: tuple
    functions: tuple
    tile_objects: tuple


def proposal_namespace():
    source = Path(__file__).with_name('bounded_initialization.py.proposed').read_text()
    tree = ast.parse(source)
    nodes = [node for node in tree.body if
             isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith('DX100_TRACE_') for t in node.targets)
             or isinstance(node, ast.FunctionDef) and node.name in {'_hash', '_dx100_trace_policy'}]
    namespace = {'hashlib': hashlib, 'json': json}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<reviewed-proposal-ast>', 'exec'), namespace)
    return namespace


def frozen_base(name):
    """Old means the exact verified preintegration snapshot, never live code."""
    folder = Path(__file__).parent
    expected = json.loads((folder / 'integration-base.json').read_text())['base_sha256'][name]
    data = (folder / 'base-source' / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise AssertionError('preintegration base bytes changed: ' + name)
    return data.decode()


class ProposalControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='trace-policy-double-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.entry = {}
        (self.root / 'proof_semantics').mkdir()
        fixture.transform(self.entry, self.root)
        self.entry_path = self.root / 'entry.json'
        self.entry_path.write_text(json.dumps(self.entry, sort_keys=True))
        self.model = ModelDouble(fixture.ENTRY, fixture.digest(self.entry_path.read_bytes()), fixture.model_text(),
            tuple(fixture.QUERY_PROTOTYPES), tuple(row['call'] for row in self.entry['calls']),
            tuple(fixture.QUERY_PROTOTYPES), tuple((f'swdb_dx_tile_row_{i}', 1) for i in range(4)))
        self.fresh = self.model
        outer = self
        class LibraryDouble:
            files = {fixture.ENTRY: outer.entry_path}
            def get(self, entry):
                return outer.entry
            def resolve(self, reference):
                return outer.root / reference['path']
            def _pin(self, reference):
                if reference['root'] != 'library' or fixture.digest(self.resolve(reference).read_bytes()) != reference['sha256']:
                    raise ValueError('double pin mismatch')
        self.library = LibraryDouble()
        self.namespace = proposal_namespace()
        fake = types.ModuleType('swdb')
        fake.artifacts = types.SimpleNamespace(file_hash=lambda path: fixture.digest(Path(path).read_bytes()))
        def constants(entry, defines):
            found = dict(entry['constants'])
            for define in defines:
                key, _, value = define.partition('=')
                if key in found:
                    found[key] = int(value or 1)
            return found
        fake.proof_semantics = types.SimpleNamespace(_constants=constants,
            model_for=lambda library, entry, defines: self.fresh)
        self.modules = patch.dict(sys.modules, {'swdb': fake})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def policy(self, model=None, defines=()):
        return self.namespace['_dx100_trace_policy'](self.library, model or self.model, defines)

    def test_exact_four_component_policy_admits_only_ten_scalar_queries(self):
        policy = self.policy()
        self.assertIsNotNone(policy)
        self.assertEqual(policy['id'], fixture.POLICY_ID)
        self.assertEqual(policy['calls'], sorted(fixture.QUERY_PROTOTYPES))
        self.assertEqual(policy['components'], fixture.policy_document()['components'])
        self.assertTrue(set(policy['calls']).isdisjoint(self.model.calls))

    def test_all_top_level_mutations_or_new_keys_refuse(self):
        original = copy.deepcopy(self.entry)
        for key in list(original) + ['source_definitions', 'unit_correctness_policy']:
            with self.subTest(key=key):
                self.entry = copy.deepcopy(original)
                self.entry[key] = 'changed'
                self.assertIsNone(self.policy())
        self.entry = original

    def test_hidden_hardware_support_or_query_prototype_or_contract_refuses(self):
        original = copy.deepcopy(self.entry)
        mutations = [lambda e: e['calls'][0].update(supported=True),
                     lambda e: e['queries'][0].update(prototype='int swdb_t28_claim(int *p)'),
                     lambda e: e['queries'][0].update(contract=r'assigns \nothing;'),
                     lambda e: e['calls'][0].update(instances=[]),
                     lambda e: e['model'].update(layout='new-layout'),
                     lambda e: e['ghost'].update(extra=True)]
        for mutate in mutations:
            self.entry = copy.deepcopy(original)
            mutate(self.entry)
            self.assertIsNone(self.policy())
        self.entry = original

    def test_every_recorded_scope_premise_is_immutable(self):
        original = copy.deepcopy(self.entry)
        for row_index, row in enumerate(original['rules']):
            if row.get('record_assumption'):
                for key in ('statement', 'assumed', 'record_assumption'):
                    with self.subTest(rule=row['id'], key=key):
                        self.entry = copy.deepcopy(original)
                        self.entry['rules'][row_index][key] = None
                        self.assertIsNone(self.policy())
        self.entry = original

    def test_each_physical_component_change_refuses_even_with_unmodified_entry(self):
        references = {'ghost': self.entry['ghost']['acsl'], **self.entry['model']}
        for component, reference in references.items():
            with self.subTest(component=component):
                path = self.library.resolve(reference)
                original = path.read_bytes()
                path.write_bytes(original + b'\n/* changed */\n')
                self.assertIsNone(self.policy())
                path.write_bytes(original)

    def test_model_and_entry_freshness_remain_mandatory(self):
        self.entry_path.write_text('changed entry bytes')
        self.assertIsNone(self.policy())
        self.entry_path.write_text(json.dumps(self.entry, sort_keys=True))
        self.assertIsNone(self.policy(replace(self.model, c_text=self.model.c_text + '\n')))
        self.assertIsNone(self.policy(replace(self.model, queries=self.model.queries[:-1])))
        self.assertIsNone(self.policy(replace(self.model, functions=self.model.functions + (self.model.calls[0],))))

    def test_changed_geometry_defines_and_malformed_ghost_model_refuse(self):
        self.assertIsNone(self.policy(defines=('DX_NT=8',)))
        original = copy.deepcopy(self.entry)
        for key in ('model', 'ghost'):
            self.entry = copy.deepcopy(original)
            self.entry[key] = []
            self.assertIsNone(self.policy())
        self.entry = original

    def test_legacy_dx100_content_constant_and_array_domains_are_unmodified(self):
        output = Path(__file__).parent
        proposed = (output / 'bounded_initialization.py.proposed').read_text()
        current = frozen_base('bounded_initialization.py')
        def content(text):
            return next(ast.literal_eval(node.value) for node in ast.parse(text).body
                        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DX100_CONTENT' for t in node.targets))
        self.assertEqual(content(proposed), content(current))
        patch_text = (output / 'integration.patch').read_text()
        self.assertNotIn('+++ b/swdb-project/swdb/dx_array_domains.py', patch_text)
        self.assertNotIn('+++ b/swdb-project/swdb/c_lowering.py', patch_text)

    def test_legacy_policy_and_verdict_fallback_ast_are_unchanged(self):
        output = Path(__file__).parent
        def named(tree, name):
            return next(n for n in ast.walk(ast.parse(tree)) if isinstance(n, ast.FunctionDef) and n.name == name)
        current = frozen_base('bounded_initialization.py')
        proposed = (output / 'bounded_initialization.py.proposed').read_text()
        old_function, new_function = named(current, '_dx100_policy'), named(proposed, '_dx100_policy')
        class UndoExactFallback(ast.NodeTransformer):
            def visit_Return(self, node):
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == '_dx100_trace_policy':
                    return ast.Return(value=ast.Constant(value=None))
                return node
        self.assertEqual(ast.dump(old_function), ast.dump(UndoExactFallback().visit(new_function)))
        old_adapter = frozen_base('cbmc_adapter.py')
        new_adapter = (output / 'cbmc_adapter.py.proposed').read_text()
        def model_branch(text):
            verdict = named(text, '_verdict')
            return next(n for n in verdict.body if isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                        and isinstance(n.test.left, ast.Name) and n.test.left.id == 'model')
        old_body, new_body = model_branch(old_adapter).body, model_branch(new_adapter).body
        exact_branch = next(n for n in new_body if isinstance(n, ast.If))
        self.assertEqual(ast.dump(ast.Module(body=old_body[1:], type_ignores=[])),
                         ast.dump(ast.Module(body=exact_branch.orelse, type_ignores=[])))

    def test_proposed_import_guard_uses_real_lowering_metadata_and_rechecks_source(self):
        output = Path(__file__).parent
        source = (output / 'cbmc_adapter.py.proposed').read_text()
        self.assertNotIn('lowering.pointer_calls', source)
        self.assertIn("import_report = wp_pointer_bounds.check(lowering)", source)
        self.assertIn("imports = [row for row in import_report['sites']", source)
        self.assertIn("context['synthetic_trace_source_plan']", source)
        self.assertIn("wp_pointer_bounds.recheck_source(context['lowering'], trace_plan)", source)
        actual = (output / 'test_public_actual.py').read_text()
        ast.parse(actual)
        self.assertNotIn('skipif', actual)
        self.assertNotIn('pytest.skip', actual)


if __name__ == '__main__':
    unittest.main(verbosity=2)
