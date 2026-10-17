"""2026-10-16 ET. Pure AST/JSON plan controls; never execute observer main."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent
POC = PUBLIC.parents[2]
CANDIDATE = Path(sys.argv.pop(1))
EVENTS = []


def no_child(event, values):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in ('os.system', 'ctypes.dlopen'):
        EVENTS.append(event)
        raise RuntimeError('plan controls forbid child/native/network')


sys.addaudithook(no_child)
SOURCE = CANDIDATE.read_bytes()
TREE = ast.parse(SOURCE)
EXPECTED = json.loads((PUBLIC/'expected.json').read_bytes())
PRIMARY = POC/'evidence/t25-public-v4-complete-record-probe-v2-actual-stdout-20261016.json'
EXECUTION = json.loads((POC/'evidence/t25-public-v4-complete-record-probe-v2-execution-20261016.json').read_bytes())
assert hashlib.sha256(PRIMARY.read_bytes()).hexdigest() == EXECUTION['stdout']['sha256']
ACTUAL = json.loads(PRIMARY.read_bytes())
NS = {'json': json, 'hashlib': hashlib}
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'CONTRACT' for target in node.targets):
        exec(compile(ast.Module([node], type_ignores=[]), '<inert-contract-literal>', 'exec'), NS)
    elif isinstance(node, ast.FunctionDef) and node.name in {'H', 'digest', 'expected_contract_entry'}:
        exec(compile(ast.Module([node], type_ignores=[]), '<inert-plan-definition>', 'exec'), NS)
FUNCTION = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'record_check')
PLAN = next(node for node in FUNCTION.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'plan' for target in node.targets))


def construct_plan(control):
    contract = NS['expected_contract_entry'](EXPECTED, control)
    namespace = dict(NS, record={'pins': {'contract': {'sha256': NS['digest'](contract)}}})
    exec(compile(ast.Module([PLAN], type_ignores=[]), '<inert-full-plan-assignment>', 'exec'), namespace)
    return namespace['plan']


class Controls(unittest.TestCase):
    def test_all_five_complete_plan_hashes_match_actual_source_materialization(self):
        self.assertEqual(EXECUTION['exit_code'], 0)
        self.assertTrue(ACTUAL['all_five_record_checks_complete'])
        self.assertEqual(len(ACTUAL['cases']), 5)
        for row in ACTUAL['cases']:
            with self.subTest(case=row['case']):
                plan = construct_plan(row['case'])
                self.assertEqual(NS['digest'](plan), row['exact_plan_matrix']['actual_plan_sha256'])
                self.assertIs(type(plan['budget_seconds']), float)
                self.assertIsNone(plan['bounds'])
                self.assertTrue(row['exact_plan_matrix']['contract_materialization_matches'])

    def test_type_and_null_contract_mutations_remain_distinct(self):
        plan = construct_plan('safe')
        wanted = ACTUAL['cases'][0]['exact_plan_matrix']['source_float_plan_sha256']
        for key, value in [('budget_seconds', 300), ('budget_seconds', True), ('bounds', {}), ('bounds', False), ('contract_sha256', '0'*64)]:
            with self.subTest(key=key, value=value):
                mutated = dict(plan, **{key: value})
                self.assertNotEqual(NS['digest'](mutated), wanted)
        self.assertNotEqual(NS['digest'](construct_plan('wrong_result')), wanted)
        self.assertEqual(len({NS['digest'](value) for value in [True, 1, 1.0, False, 0, 0.0, None]}), 7)

    def test_v4_inverse_is_exact_and_all_other_functions_and_embeds_unchanged(self):
        old = (PUBLIC/'full-observer-v3/observer-v3.py').read_bytes()
        new = (HERE/'observer-v4.py').read_bytes()
        before, after = b"'budget_seconds':300,", b"'budget_seconds':300.0,"
        self.assertEqual(old.count(before), 1)
        self.assertEqual(new.count(after), 1)
        self.assertEqual(new.replace(after, before, 1), old)
        old_tree, new_tree = ast.parse(old), ast.parse(new)
        differences = [a for a, b in zip(old_tree.body, new_tree.body) if ast.dump(a, include_attributes=False) != ast.dump(b, include_attributes=False)]
        self.assertEqual([node.name for node in differences], ['record_check'])
        delta = json.loads((HERE/'source-delta-v4.json').read_bytes())
        self.assertTrue(delta['all_other_source_bytes_identical'])
        self.assertEqual(delta['successor']['sha256'], hashlib.sha256(new).hexdigest())
        self.assertEqual(EVENTS, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped), 'child_events': EVENTS,
                      'candidate': str(CANDIDATE), 'candidate_sha256': hashlib.sha256(SOURCE).hexdigest(), 'observer_main_or_project_import_or_actual_metadata_run': False}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful() or bool(EVENTS))
