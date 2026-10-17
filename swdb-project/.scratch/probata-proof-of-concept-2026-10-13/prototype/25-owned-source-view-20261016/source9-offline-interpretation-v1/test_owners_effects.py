"""2026-10-16 ET. Complete retained-task and hostile-mutation controls; no tools."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import unittest


ATTEMPTS = []


def no_children(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn',
                 'ctypes.dlopen', 'socket.__new__'} or event.startswith('os.exec'):
        ATTEMPTS.append(event)
        raise RuntimeError('external execution forbidden: '+event)


sys.dont_write_bytecode = True
sys.addaudithook(no_children)
HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
SEMANTIC = runpy.run_path(str(POC/'prototype/25-owned-transfer-20261016/cold-g621-encoding-v3/semantic_terms.py'))
HEAP = runpy.run_path(str(HERE/'heap_reader_v2.py'))
OWN = runpy.run_path(str(HERE/'owners_effects_reader.py'))
DATA = json.loads((POC/'evidence/t25-owned-source9-math-ast-v3-actual-stdout-20261016.json').read_text())
TREES = DATA['deduplicated_complete_math_commands']


def commands(task):
    return [copy.deepcopy(TREES[row['tree_ref']]) for row in task['commands'] if row['tree_ref']]


def check(task, altered=None):
    rows = commands(task) if altered is None else altered
    context = HEAP['task_context'](rows, SEMANTIC['one'], SEMANTIC['canon'])
    return OWN['reconcile_task'](rows, task['id'], context, SEMANTIC['one'],
                                 SEMANTIC['canon'], HEAP['normalize_source_primitives'])


class OwnersEffectsControls(unittest.TestCase):
    def test_complete_all26_tasks(self):
        result = [check(task) for task in DATA['tasks']]
        self.assertEqual(len(result), 26)
        self.assertTrue(all(row['source_goal_equivalent'] for row in result))
        self.assertTrue(all(row['all_observed_own_definitions_equivalent'] for row in result))
        self.assertTrue(all(not row['source_Heap_Typed_caller_admission'] for row in result))
        self.assertTrue(all(not row['complete_support_or_scientific_acceptance'] for row in result))

    def test_complete_source_declaration_consistency(self):
        self.assertEqual(set(OWN['CONCLUSIONS']), {row['id'] for row in DATA['tasks']})
        self.assertEqual(len(OWN['OWNERS_EFFECTS_DEFINITIONS']), 24)
        for key, (parameters, result, body) in OWN['OWNERS_EFFECTS_DEFINITIONS'].items():
            self.assertTrue(SEMANTIC['one']('('+parameters+')'), key)
            self.assertTrue(SEMANTIC['one'](result), key)
            self.assertTrue(SEMANTIC['one'](body), key)

    def test_reject_dropped_original_premise(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        goal = rows[-1][1]
        body = goal[1][2]
        self.assertEqual(body[0], '=>')
        goal[1][2] = body[2]
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_changed_original_post(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        rows[-1][1][1][2] = ['=>', 'false', 'true']
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_duplicate_outer_binder(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        binders = rows[-1][1][1][1]
        binders[1][0] = binders[0][0]
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_changed_outer_sort(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        rows[-1][1][1][1][0][1] = 'Real'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_definition_parameter_permutation(self):
        task = next(t for t in DATA['tasks'] if t['id'] == 'move.destination_header')
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'copy_header'])
        row[2][1], row[2][2] = row[2][2], row[2][1]
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_changed_owner_update(self):
        task = next(t for t in DATA['tasks'] if t['id'] == 'move.owner_correspondence')
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'move'] and r[3] == 'state')
        row[4][-1][-1] = '1'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_changed_cell_projection(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'target'])
        row[4][-1] = '1'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_changed_overload_sort(self):
        task = next(t for t in DATA['tasks'] if t['id'] == 'move.owner_correspondence')
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'move'] and r[3] == 'state')
        row[3] = 'heap'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_complete_position_preserving_parameter_alpha(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'copy_header'])
        # Rename a bound argument in both its declaration and complete body.
        old = row[2][1][0]
        row[2][1][0] = 'renamed_destination'
        def replace(tree):
            if isinstance(tree, str):
                return 'renamed_destination' if tree == old else tree
            return [replace(item) for item in tree]
        row[4] = replace(row[4])
        self.assertTrue(check(task, rows)['source_goal_equivalent'])

    def test_reject_private_interpretation_vocabulary(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        rows[-1][1][1][1][0][0] = '$source9_argument0'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_scope_safe_global_alias(self):
        tree = SEMANTIC['one']('(forall ((target Int)) (= target (target h r)))')
        # The same atom can denote a bound symbol in an invalid higher-order
        # call. Renaming must preserve that scope, never bless the alias.
        result = OWN['rename_globals'](tree, {'target': 'E_target'})
        self.assertEqual(result, tree)

    def test_reject_undeclared_source_role_in_actual_goal(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        def inject(tree):
            if isinstance(tree, str):
                return 'E_header' if tree == 'header' else tree
            return [inject(item) for item in tree]
        rows[-1] = inject(rows[-1])
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_captured_parameter_renaming(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        row = next(r for r in rows if r[:2] == ['define-fun', 'world'])
        # The old source state argument must not become captured by the inner
        # receiver quantifier when an otherwise permitted argument is renamed.
        row[2][1][0] = 'r'
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_reject_extra_original_premise(self):
        task = DATA['tasks'][0]
        rows = commands(task)
        original = rows[-1][1][1][2]
        rows[-1][1][1][2] = ['=>', 'false', original]
        with self.assertRaises(ValueError):
            check(task, rows)

    def test_no_child_attempts(self):
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    unittest.main()
