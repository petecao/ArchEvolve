"""2026-10-16 ET. Complete retained-task context and interpretation mutations.

No compiler, solver, remote reader or project module executes. The actual task
trees remain unchanged; mutations exercise the closed checker on private copies.
"""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
HEAP = runpy.run_path(str(HERE/'heap_reader.py'))
SYNTAX = runpy.run_path(str(HERE.parent/'source9-cold/semantic_terms.py'))
RAW = (POC/'evidence/t25-owned-source9-math-ast-v3-actual-stdout-20261016.json').read_bytes()
assert hashlib.sha256(RAW).hexdigest() == '9924e02166c0613047bf750b31a06508b67d5eb8853fec79a59c8f1d926b5a72'
CAPTURE = json.loads(RAW)
TREES = CAPTURE['deduplicated_complete_math_commands']
COMMANDS = [[TREES[r['tree_ref']] for r in t['commands'] if r['tree_ref'] is not None]
            for t in CAPTURE['tasks']]
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise AssertionError('no child/native/network during interpretation controls')


sys.addaudithook(audit)


def context(commands):
    return HEAP['task_context'](commands, SYNTAX['one'], SYNTAX['canon'])


def check(commands):
    result = context(commands)
    return result, HEAP['reconcile_heap_definitions'](commands, result, SYNTAX['one'], SYNTAX['canon'])


class Controls(unittest.TestCase):
    def test_all26_retained_contexts_and462_complete_typed_Heap_definitions(self):
        results = [check(commands) for commands in COMMANDS]
        self.assertEqual(len(results), 26)
        self.assertEqual(sum(r[0]['mode'] == 'closed_axiomatized_polymorphic_sum' for r in results), 18)
        self.assertEqual(sum(r[0]['mode'] == 'native_algebraic_sum' for r in results), 8)
        self.assertEqual(sum(len(r[1]) for r in results), 462)
        self.assertTrue(all(r[0]['definition_goal_or_scientific_acceptance'] is False for r in results))

    def test_same_sort_record_field_reordering_is_not_alpha_renaming(self):
        commands = copy.deepcopy(COMMANDS[0])
        record = next(r for r in commands if r[0] == 'declare-datatypes' and r[1] == [['heap', '0']])
        fields = record[2][0][0]
        fields[2], fields[3] = fields[3], fields[2]
        with self.assertRaisesRegex(ValueError, 'ordered record'): context(commands)

    def test_record_field_sort_or_extra_field_refuses(self):
        for mutation in ('sort', 'extra'):
            commands = copy.deepcopy(COMMANDS[0])
            record = next(r for r in commands if r[0] == 'declare-datatypes' and r[1] == [['heap', '0']])
            if mutation == 'sort': record[2][0][0][1][1] = 'Real'
            else: record[2][0][0].append(['hidden', 'Int'])
            with self.assertRaises(ValueError): context(commands)

    def test_extra_function_declaration_refuses_even_if_unused(self):
        commands = copy.deepcopy(COMMANDS[0])
        commands.insert(0, ['declare-fun', 'hidden', [], 'Bool'])
        with self.assertRaisesRegex(ValueError, 'extra sort'): context(commands)

    def test_each_of_eight_sum_laws_is_required(self):
        original = COMMANDS[0]
        selected = context(original)['sum_and_map_support']
        self.assertEqual(len(selected), 8)
        for law in selected:
            commands = copy.deepcopy(original); commands.remove(law)
            with self.assertRaisesRegex(ValueError, 'sum encoding law'): context(commands)

    def test_polymorphic_match_result_and_constructor_tag_changes_refuse(self):
        for marker in ('match', 'tag'):
            commands = copy.deepcopy(COMMANDS[0])
            if marker == 'match':
                row = next(r for r in commands if r[0] == 'declare-fun' and r[1] == 'match_cell')
                row[2][-1] = 'Int'
            else:
                law = next(r for r in commands if r[0] == 'assert' and 'index_cell' in json.dumps(r) and 'Integer' in json.dumps(r))
                law[1][2][1][2] = '1'  # retained annotated Integer tag0 becomes tag1
            with self.assertRaises(ValueError): context(commands)

    def test_native_sum_constructor_width_change_refuses(self):
        original = next(c for c in COMMANDS if context(c)['mode'] == 'native_algebraic_sum')
        commands = copy.deepcopy(original)
        cell = next(r for r in commands if r[0] == 'declare-datatypes' and r[1] == [['cell', '0']])
        cell[2][0][1].pop()
        with self.assertRaisesRegex(ValueError, 'native Integer/Pointer'): context(commands)

    def test_false_map_requires_the_exact_type_and_false_equation(self):
        original = next(c for c in COMMANDS if ['declare-fun', 'fc', [], ['Array', 'Int', 'Bool']] in c)
        for mutation in ('type', 'value'):
            commands = copy.deepcopy(original)
            if mutation == 'type':
                next(r for r in commands if r[:2] == ['declare-fun', 'fc'])[3][-1] = 'Int'
            else:
                row = next(r for r in commands if r[0] == 'assert' and 'fc' in json.dumps(r))
                row[1][2][2] = 'true'
            with self.assertRaises(ValueError): context(commands)

    def test_full_Heap_body_store_value_change_refuses(self):
        commands = copy.deepcopy(COMMANDS[0])
        row = next(r for r in commands if r[:2] == ['define-fun', 'put_integer'])
        row[4][-2][-1][-1][-1] = '1'
        with self.assertRaisesRegex(ValueError, 'Heap definition mismatch'): check(commands)

    def test_definition_result_sort_change_refuses(self):
        commands = copy.deepcopy(COMMANDS[0])
        next(r for r in commands if r[:2] == ['define-fun', 'contents'])[3] = 'Int'
        with self.assertRaisesRegex(ValueError, 'parameter/result'): check(commands)

    def test_match_projection_requires_the_whole_selected_argument_and_zero_case(self):
        commands = copy.deepcopy(COMMANDS[0])
        row = next(r for r in commands if r[:2] == ['define-fun', 'load_int'])
        row[4][-1] = '1'
        with self.assertRaisesRegex(ValueError, 'complete cell projection'): check(commands)

    def test_goal_cannot_supply_a_missing_constant_map_support_law(self):
        original = next(c for c in COMMANDS if ['declare-fun', 'fc', [], ['Array', 'Int', 'Bool']] in c)
        commands = copy.deepcopy(original)
        law = next(r for r in commands if r[0] == 'assert' and 'fc' in json.dumps(r))
        commands.remove(law); commands.pop(); commands.append(law)
        with self.assertRaisesRegex(ValueError, 'false-map'): context(commands)

    def test_private_normalization_vocabulary_cannot_be_inserted_in_actual_input(self):
        commands = copy.deepcopy(COMMANDS[0]); commands.insert(0, ['define-fun', '_source9_integer_or_zero', [], 'Int', '0'])
        with self.assertRaisesRegex(ValueError, 'private interpretation vocabulary'): context(commands)

    def test_unclassified_added_false_assertion_is_not_consumed_or_adopted(self):
        commands = copy.deepcopy(COMMANDS[0]); commands.insert(-1, ['assert', 'false'])
        result = context(commands)
        self.assertNotIn(['assert', 'false'], result['sum_and_map_support'])
        self.assertFalse(result['definition_goal_or_scientific_acceptance'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                      'external_attempts': ATTEMPTS, 'actual_solver_or_scientific_adoption': False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
