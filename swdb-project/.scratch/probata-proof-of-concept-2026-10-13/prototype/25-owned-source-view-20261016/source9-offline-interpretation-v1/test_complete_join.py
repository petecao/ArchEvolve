"""2026-10-16 ET. Offline complete-support/definition/identity refusal controls."""
import copy
from pathlib import Path
import runpy
import unittest

J = runpy.run_path(str(Path(__file__).with_name('complete_join.py')))
D, S, H, O, _ = J['load']()
T = D['capture']['tasks'][0]
TREES = D['capture']['deduplicated_complete_math_commands']


def commands():
    return [copy.deepcopy(TREES[r['tree_ref']]) for r in T['commands'] if r['tree_ref']]


def interpret(rows):
    return J['interpret_commands'](rows, T['id'], D['context'], S, H, O,
        D['accepted_standard_basis']['source_interpretation']['support'], D['cold']['import_source_closure'])


def reconcile(capture):
    return J['reconcile'](D['cold'], capture, D['context'], S, H, O,
                          D['accepted_standard_basis'], D['own_join'])


class CompleteJoinControls(unittest.TestCase):
    def test_complete_all26_and_original_timeout(self):
        joined = reconcile(D['capture'])
        self.assertEqual(joined['unknown_items'], [])
        self.assertEqual(joined['counts']['standard_support_instances'], 784)
        self.assertEqual(joined['counts']['sum_map_support_instances'], 158)
        self.assertEqual(joined['outcomes'][-1]['normal_verdict'], 'not_proven')
        self.assertFalse(joined['source_C_Heap_Typed_lifetime_caller_default_admission'])

    def test_unknown_false_support_refused_without_hash_gate(self):
        rows = commands()
        rows.insert(-1, ['assert', 'false'])
        with self.assertRaises(ValueError):
            interpret(rows)

    def test_extra_definition_refused_without_hash_gate(self):
        rows = commands()
        rows.insert(-1, ['define-fun', 'hidden', [], 'Bool', 'false'])
        with self.assertRaises(ValueError):
            interpret(rows)

    def test_changed_abs_body_refused_without_hash_gate(self):
        rows = commands()
        next(r for r in rows if r[:2] == ['define-fun', 'abs1'])[4] = '0'
        with self.assertRaises(ValueError):
            interpret(rows)

    def test_extra_declaration_refused_without_hash_gate(self):
        rows = commands()
        rows.insert(-1, ['declare-fun', 'unknown', ['Int'], 'Bool'])
        with self.assertRaises(ValueError):
            interpret(rows)

    def test_missing_original_goal_premise_refused_without_hash_gate(self):
        rows = commands()
        goal = rows[-1][1][1][2]
        self.assertEqual(goal[0], '=>')
        rows[-1][1][1][2] = goal[2]
        with self.assertRaises(ValueError):
            interpret(rows)

    def test_support_family_change_refused(self):
        roots = copy.deepcopy(D['cold']['import_source_closure'])
        roots['int.Abs']['file']['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            J['interpret_commands'](commands(), T['id'], D['context'], S, H, O,
                D['accepted_standard_basis']['source_interpretation']['support'], roots)

    def test_complete_tree_content_hash_refused(self):
        capture = copy.deepcopy(D['capture'])
        capture['deduplicated_complete_math_commands'][next(iter(TREES))] = ['assert', 'false']
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_duplicate_task_owner_refused(self):
        capture = copy.deepcopy(D['capture'])
        capture['tasks'][1] = copy.deepcopy(capture['tasks'][0])
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_reordered_tasks_refused(self):
        capture = copy.deepcopy(D['capture'])
        capture['tasks'][0], capture['tasks'][1] = capture['tasks'][1], capture['tasks'][0]
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_unknown_command_reference_refused(self):
        capture = copy.deepcopy(D['capture'])
        row = next(r for r in capture['tasks'][0]['commands'] if r['tree_ref'])
        row['tree_ref'] = '0'*64
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_changed_command_order_refused(self):
        capture = copy.deepcopy(D['capture'])
        rows = capture['tasks'][0]['commands']
        rows[2], rows[3] = rows[3], rows[2]
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_original_swap_outcome_cannot_be_promoted(self):
        capture = copy.deepcopy(D['capture'])
        capture['retained_outcomes'][-1]['normal_verdict'] = 'proven'
        with self.assertRaises(ValueError):
            reconcile(capture)

    def test_no_external_attempts(self):
        self.assertEqual(J['ATTEMPTS'], [])


if __name__ == '__main__':
    unittest.main()
