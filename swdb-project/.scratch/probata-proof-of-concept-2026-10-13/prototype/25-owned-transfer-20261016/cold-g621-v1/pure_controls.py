"""2026-10-16 ET. Child-free controls for the inert passive reader only."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
ATTEMPTS = []


def no_children(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'} or event.startswith('socket.'):
        ATTEMPTS.append(event)
        raise RuntimeError('child/native/network forbidden in pure controls')


sys.addaudithook(no_children)
semantic = types.ModuleType('pure_ownership_terms')
exec(compile((HERE / 'semantic_terms.py').read_text(), '<pure-term-controls>', 'exec'), semantic.__dict__)
observer = types.ModuleType('pure_observer')
observer.__dict__['__name__'] = 'pure_observer'
exec(compile((HERE / 'observer.py').read_text(), '<unexecuted-observer-definitions>', 'exec'), observer.__dict__)


class Controls(unittest.TestCase):
    def test_all_ten_independent_goal_transcriptions_parse(self):
        self.assertEqual(len(semantic.GOALS), 10)
        for ident in semantic.GOALS:
            term = semantic.source_goal(ident)
            self.assertEqual(term[0], 'not')
            self.assertEqual(term[1][0], 'forall')
            semantic.canon(term)

    def test_all_nine_source_definition_transcriptions_parse(self):
        self.assertEqual(len(semantic.DEFINITIONS), 9)
        for name in semantic.DEFINITIONS:
            semantic.canon(semantic.definition_expected(name))

    def test_smt_token_coverage_and_query_shape(self):
        for bad in ('(assert true', '(assert "unterminated)', '(assert |unterminated)', '(assert true))'):
            with self.assertRaises(ValueError):
                semantic.forms(bad)
        for query in ('(check-sat)(check-sat)', '(check-sat)(assert false)', '(push 1)(assert false)(check-sat)'):
            with self.assertRaises(ValueError):
                semantic.task_semantics(query, 'swap.self', {})

    def test_goal_not_replaced_by_desired_or_sibling_premise(self):
        for bad in ('(assert check_lemma_t25_owned_swap_self)', '(assert (wp_goal true))'):
            with self.assertRaises(ValueError):
                semantic.task_semantics(bad + '(assert (not true))(check-sat)', 'swap.self', {})

    def test_unknown_support_is_pending_not_standard(self):
        result = semantic.task_semantics('(assert false)(assert (not true))(check-sat)', 'swap.self', {})
        self.assertFalse(result['complete_semantic_match'])
        self.assertIn('support_assertion', [r['kind'] for r in result['unresolved']])

    def test_unknown_record_encoding_is_pending(self):
        result = semantic.task_semantics('(declare-datatype state ((mk_state (active (Array Int Bool)) (backing (Array Int Int))))) (assert (not true))(check-sat)', 'swap.self', {})
        self.assertIn('encoding_declaration', [r['kind'] for r in result['unresolved']])
        self.assertFalse(result['complete_semantic_match'])

    def test_antecedent_mutation_is_not_alpha_normalization(self):
        term = semantic.source_goal('move.transfer')
        changed = json.loads(json.dumps(term))
        changed[1][2][1].pop(4)
        self.assertNotEqual(semantic.canon(term), semantic.canon(changed))

    def test_move_store_order_is_material(self):
        term = semantic.definition_expected('move')
        changed = json.loads(json.dumps(term))
        stores = changed[2][2]
        stores[2] = 'destination'
        self.assertNotEqual(semantic.canon(term), semantic.canon(changed))

    def test_alpha_and_conjunction_order_are_the_only_permitted_changes(self):
        a = semantic.one('(forall ((r Int) (q Int)) (and (= r q) (< r 4)))')
        b = semantic.one('(forall ((x Int) (y Int)) (and (< x 4) (= y x)))')
        self.assertEqual(semantic.canon(a), semantic.canon(b))
        c = semantic.one('(exists ((x Int) (y Int)) (and (< x 4) (= y x)))')
        self.assertNotEqual(semantic.canon(a), semantic.canon(c))

    def test_let_bindings_are_simultaneous(self):
        actual = semantic.one('(let ((x y) (y x)) (= x y))')
        expected = semantic.one('(= y x)')
        self.assertEqual(semantic.canon(actual), semantic.canon(expected))

    def test_raw_symlink_special_and_outside_membership_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'file').write_bytes(b'x')
            self.assertEqual(len(observer.walk(root)), 1)
            (root / 'alias').symlink_to(root / 'file')
            with self.assertRaises(ValueError):
                observer.walk(root)
            with self.assertRaises(ValueError):
                observer.read_bytes(root / 'alias')

    def test_input_and_aggregate_bounds_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'file').write_bytes(b'12345')
            with self.assertRaises(ValueError):
                observer.read_bytes(root / 'file', 4)
            with self.assertRaises(ValueError):
                observer.walk(root, byte_cap=4)
            with self.assertRaises(ValueError):
                observer.walk(root, entry_cap=0)

    def test_duplicate_or_nonfinite_metadata_refuses(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / 'a.json'
            for payload in ('{"a":1,"a":2}', '{"a":NaN}'):
                path.write_text(payload)
                with self.assertRaises(ValueError):
                    observer.read(path)

    def test_observer_has_no_project_import_or_tool_version_probe(self):
        tree = ast.parse((HERE / 'observer.py').read_bytes())
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(getattr(n, 'module', '').startswith('swdb') for n in imports if isinstance(n, ast.ImportFrom)))
        self.assertNotIn('--version', (HERE / 'observer.py').read_text())
        self.assertNotIn('ctypes.CDLL', (HERE / 'observer.py').read_text())
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
