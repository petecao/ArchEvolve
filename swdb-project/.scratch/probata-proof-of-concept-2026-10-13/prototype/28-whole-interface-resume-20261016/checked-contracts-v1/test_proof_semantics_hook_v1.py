"""2026-10-16 ET. No-child source inverse and new-form WP refusal controls."""
import ast
import builtins
from pathlib import Path
import types
import unittest

from test_checked_contracts_v1 import M, Controls as EntryControls, HERE

BASE = (HERE / 'proof_semantics.base.py').read_text()
PROPOSED = (HERE / 'proof_semantics.proposed.py').read_text()


class AdapterError(ValueError):
    pass


class Controls(unittest.TestCase):
    def test_complete_production_source_inverse_preserves_default_form(self):
        guard = '''def _require_summary_form(data):
    from swdb import dx100_whole_checked
    if dx100_whole_checked.checked(data):
        from swdb.proof import AdapterError
        raise AdapterError("whole-interface checked bodies have no WP/ACSL summary form")


'''
        branch = '''    from swdb import dx100_whole_checked
    if dx100_whole_checked.checked(data):
        return dx100_whole_checked.check(library, data, error)
'''
        self.assertEqual(PROPOSED.count(guard), 1)
        self.assertEqual(PROPOSED.count(branch), 1)
        self.assertEqual(PROPOSED.count('    _require_summary_form(data)\n'), 3)
        self.assertEqual(PROPOSED.replace(guard, '').replace(branch, '').replace('    _require_summary_form(data)\n', ''), BASE)
        before = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(BASE).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        after = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(PROPOSED).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(set(after) - set(before), {'_require_summary_form'})
        self.assertEqual({key for key in before if before[key] != after[key]}, {'check', 'acsl_source', 'wp_prelude', 'wp_locations'})

    def namespace(self):
        def imports(name, _globals=None, _locals=None, _fromlist=(), _level=0):
            if name == 'swdb':
                return types.SimpleNamespace(dx100_whole_checked=M)
            if name == 'swdb.proof':
                return types.SimpleNamespace(AdapterError=AdapterError)
            raise AssertionError('unexpected pure hook import: ' + name)
        namespace = {'__builtins__': dict(vars(builtins), __import__=imports)}
        tree = ast.parse(PROPOSED)
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in {'_require_summary_form', 'check', 'acsl_source', 'wp_prelude', 'wp_locations'}]
        exec(compile(ast.Module(body=selected, type_ignores=[]), 'inert-production-hooks', 'exec'), namespace)
        return namespace

    def test_all_acsl_wp_consumers_refuse_new_form_before_accessing_summary_fields(self):
        ns = self.namespace()
        data = {'contract_form': M.KIND}
        library = types.SimpleNamespace(get=lambda _: data)
        for name, args in (('acsl_source', (data, {})), ('wp_prelude', (library, 'new', [])),
            ('wp_locations', (library, 'new'))):
            with self.subTest(name=name), self.assertRaisesRegex(AdapterError, 'no WP/ACSL summary'):
                ns[name](*args)
        for data in ({}, {'contract_form': 'old'}, {'version': '0.1'}):
            self.assertIsNone(ns['_require_summary_form'](data))

    def test_early_public_validator_branch_consumes_full_contract_inventory(self):
        ns = self.namespace()
        fixture = EntryControls()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        errors = []
        self.assertEqual(ns['check'](fixture.library, 'new', fixture.entry, lambda *row: errors.append(row)), [])
        self.assertEqual(errors, [])
        fixture.entry['calls'].pop()
        self.assertEqual(ns['check'](fixture.library, 'new', fixture.entry, lambda *row: errors.append(row)), [])
        self.assertEqual(len(errors), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
