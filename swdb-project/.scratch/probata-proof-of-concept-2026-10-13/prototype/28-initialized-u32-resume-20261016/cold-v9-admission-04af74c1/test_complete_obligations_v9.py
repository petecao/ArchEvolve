"""Pinned full 711/1107 goal/CSV seam controls, no full audit or children."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest


def deny(event, _args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('complete obligation controls refuse ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'cold-v8-admission-04af74c1'
raw = (BASE / 'complete-obligation-input-metadata-20261016.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'f4a36928d25f0cd2252e418131da5aa7947cb712fc4e6842e3e9746b1440d0b5'
DATA = json.loads(raw)


def load(path):
    module = types.ModuleType('inert_complete_obligations')
    exec(compile(ast.parse(path.read_bytes()), str(path), 'exec'), module.__dict__)
    return module


NEW = load(HERE / 'initialized_cold_obligations_v4.py')
OLD = load(BASE / 'initialized_cold_obligations_v3.py')


def run(module, row):
    result = module.current_goals(row['record_projection'], row['inventory'], row['native'],
        row['csvrows'], Path(row['expected_wp_input']), validated_query=row['validated_query'])
    result['dependency_DAG'] = module.dependency_DAG(row['inventory'])
    return result


class Controls(unittest.TestCase):
    def test_both_complete_actual_pipelines_are_old_red_new_green(self):
        results = []
        for row in DATA['records']:
            with self.subTest(expected_result=row['expected_result']):
                with self.assertRaises(AssertionError):
                    run(OLD, row)
                checked = run(NEW, row)
                self.assertEqual((checked['properties'], checked['goals'], checked['ordinary'], checked['smoke']), (41, 33, 23, 10))
                self.assertEqual(checked['CSV_crosswalk']['CSV_rows'], 26)
                self.assertEqual(checked['CSV_crosswalk']['source_initialization_reads']['ordinary_direct_valid'], 2)
                self.assertFalse(checked['CSV_crosswalk']['unproved_init_termination']['termination_proven'])
                self.assertEqual(checked['healthy_negative'], row['expected_result'] == 1107)
                self.assertFalse(checked['refuted'])
                results.append({'expected_result': row['expected_result'], 'decision': checked})
        self.assertEqual([row['expected_result'] for row in DATA['records']], [711, 1107])
        self.results = results

    def test_every_rte_source_predicate_site_and_dependency_remains_exact(self):
        first = 'trust_fixture_assert_rte_initialization'
        for base in DATA['records']:
            for index, prop in enumerate([p for p in base['inventory']['properties'] if p['emitter'] == 'rte']):
                for key, value in (('description', r'assert rte: initialization: \initialized(&other);'),
                    ('property', first + '_3'), ('line', 48), ('function', 'other'), ('extern', True),
                    ('property_variant', 'IPOther'), ('origin', first), ('dependencies', [] if index else [first]),
                    ('source_file', '/other/wp_input.c'), ('call_context', {}), ('status_registered', False)):
                    row = copy.deepcopy(base)
                    target = next(p for p in row['inventory']['properties'] if p['property'] == prop['property'])
                    target[key] = value
                    with self.subTest(result=base['expected_result'], property=prop['property'], key=key), self.assertRaises((AssertionError, KeyError)):
                        run(NEW, row)

    def test_each_initialization_native_inventory_and_saved_goal_is_mandatory(self):
        for base in DATA['records']:
            names = [g['goal'] for g in base['inventory']['goals'] if 'assert_rte_initialization' in g['goal']]
            self.assertEqual(len(names), 2)
            for name in names:
                for collection in ('native', 'inventory', 'record'):
                    row = copy.deepcopy(base)
                    values = row['native'] if collection == 'native' else row['inventory']['goals'] if collection == 'inventory' else row['record_projection']['goals']
                    values[:] = [value for value in values if value['goal'] != name]
                    with self.subTest(result=base['expected_result'], goal=name, collection=collection), self.assertRaises(AssertionError):
                        run(NEW, row)
                row = copy.deepcopy(base)
                goal = next(g for g in row['inventory']['goals'] if g['goal'] == name)
                goal.update(passed=False, results=['unknown'])
                with self.assertRaises(AssertionError):
                    run(NEW, row)

    def test_csv_cannot_drop_or_relabel_an_initialization(self):
        for base in DATA['records']:
            for local in ('first', 'second'):
                for mutation in ('drop', 'status', 'predicate', 'kind'):
                    row = copy.deepcopy(base)
                    target = next(item for item in row['csvrows'] if item['property'] == r'\initialized(&' + local + ')')
                    if mutation == 'drop':
                        row['csvrows'].remove(target)
                    else:
                        target[{'status': 'status', 'predicate': 'property', 'kind': 'property kind'}[mutation]] = {'status': 'Unknown', 'predicate': '1', 'kind': 'postcondition'}[mutation]
                    with self.subTest(result=base['expected_result'], local=local, mutation=mutation), self.assertRaises(AssertionError):
                        run(NEW, row)

    def test_ordinary_wrong_ensures_stays_nonproof_and_smoke_health_remains_mandatory(self):
        for base in DATA['records']:
            row = copy.deepcopy(base)
            smoke = next(g for g in row['native'] if g['smoke'])
            smoke['passed'] = False
            with self.assertRaises(AssertionError):
                run(NEW, row)
        wrong = copy.deepcopy(DATA['records'][1])
        wrong['record_projection']['verdict'] = 'refuted'
        with self.assertRaises(AssertionError):
            run(NEW, wrong)
        correct = copy.deepcopy(DATA['records'][0])
        correct['record_projection']['verdict'] = 'not_proven'
        with self.assertRaises((AssertionError, KeyError)):
            run(NEW, correct)

    def test_only_csv_name_census_wrapper_and_new_exact_rte_validator_change(self):
        before = (BASE / 'initialized_cold_obligations_v3.py').read_text()
        after = (HERE / 'initialized_cold_obligations_v4.py').read_text()
        old_tree = ast.parse(before)
        new_tree = ast.parse(after)
        old_functions = {n.name: ast.dump(n, include_attributes=False) for n in old_tree.body if isinstance(n, ast.FunctionDef)}
        new_functions = {n.name: ast.dump(n, include_attributes=False) for n in new_tree.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(set(new_functions) - set(old_functions), {'initialized_reads_v4', 'init_termination_v4'})
        self.assertEqual({name for name in old_functions if old_functions[name] != new_functions[name]}, {'current_csv_active_v2', 'current_csv'})
        self.assertEqual(OLD.HELPERS, NEW.HELPERS)
        self.assertEqual(len(NEW.HELPERS), 3)

    def test_unproved_init_termination_cannot_become_proof_or_an_active_premise(self):
        name = 'init_MAA_terminates'
        for base in DATA['records']:
            for mutation in ('status', 'predicate', 'goal', 'active-dependency', 'Extern', 'source-site'):
                row = copy.deepcopy(base)
                prop = next(p for p in row['inventory']['properties'] if p['property'] == name)
                csv = next(p for p in row['csvrows'] if p['function'] == 'init_MAA' and p['property kind'] == 'termination clause')
                if mutation == 'status':
                    csv['status'] = 'Valid'
                elif mutation == 'predicate':
                    prop['description'] = r'terminates \false'
                elif mutation == 'goal':
                    row['inventory']['goals'][0]['targets'] = [name]
                elif mutation == 'active-dependency':
                    row['inventory']['properties'][0]['dependencies'].append(name)
                elif mutation == 'Extern':
                    prop['extern'] = True
                else:
                    prop['line'] = 25
                with self.subTest(result=base['expected_result'], mutation=mutation), self.assertRaises(AssertionError):
                    run(NEW, row)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'complete_actual_metadata_pipelines': [711, 1107],
        'record_audit_or_scientific_execution': False}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
