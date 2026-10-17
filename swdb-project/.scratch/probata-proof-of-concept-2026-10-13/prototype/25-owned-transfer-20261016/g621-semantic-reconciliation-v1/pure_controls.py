"""2026-10-16 ET. Offline interpretation join mutation controls, no children."""
import copy
import json
import runpy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
ATTEMPTS = []


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen', 'socket.connect'}:
        ATTEMPTS.append(event)
        raise RuntimeError('pure interpretation controls forbid '+event)


sys.addaudithook(audit)
ns = runpy.run_path(str(HERE/'reconcile.py'), run_name='_pure_reconciliation')
old = json.loads((POC/'evidence/t25-owned-transfer10-cold-v3-root-stdout-20261016.json').read_bytes())
actual = json.loads((POC/'evidence/t25-owned-transfer10-encoding-v3-actual-stdout-20261016.json').read_bytes())
v3 = HERE.parent/'cold-g621-encoding-v3'
context = json.loads((v3/'context.json').read_bytes())
semantic = {'__name__': '_pure_terms'}
for name in ('semantic_terms.py', 'encoding_probe.py'):
    exec(compile((v3/name).read_bytes(), str(v3/name), 'exec'), semantic)


class Controls(unittest.TestCase):
    def test_complete_actual_join_accounts_every_goal_declaration_definition_and_support(self):
        result = ns['reconcile'](old, actual, context, semantic)
        self.assertEqual(len(result['tasks']), 20)
        self.assertEqual(len(result['goals']), 10)
        self.assertEqual(len(result['declaration_signatures']), 5)
        self.assertEqual(sum(row['instances'] for row in result['support'].values()), 684)
        self.assertEqual(result['unknown_items_after_explicit_interpretation'], [])
        self.assertTrue(result['independent_root_scientific_acceptance_required'])

    def test_missing_or_false_source_goal_and_duplicate_task_are_refused(self):
        for mutation in ('missing', 'duplicate', 'goal'):
            value = copy.deepcopy(actual)
            if mutation == 'missing':
                value['tasks'].pop()
            elif mutation == 'duplicate':
                value['tasks'][1] = value['tasks'][0]
            else:
                value['tasks'][0]['goal_equivalent_after_local_schema_check'] = False
            with self.assertRaises(ValueError):
                ns['reconcile'](old, value, context, semantic)

    def test_declared_product_or_function_type_change_cannot_hide_behind_its_name(self):
        value = copy.deepcopy(actual)
        value['tasks'][0]['declaration_census'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'typed declaration'):
            ns['reconcile'](old, value, context, semantic)

    def test_empty_needs_both_complete_maps_and_exact_definition(self):
        for mutation in ('map', 'body', 'signature'):
            value = copy.deepcopy(actual)
            task = value['tasks'][0]
            if mutation == 'map':
                task['constant_maps'][0]['full_quantified_formula_matches'] = False
            elif mutation == 'body':
                task['empty']['form_sha256'] = '0'*64
            else:
                task['empty']['integer_dummy_signature_matches_source'] = False
            with self.assertRaises(ValueError):
                ns['reconcile'](old, value, context, semantic)

    def test_unknown_support_or_definition_remains_refused(self):
        for mutation in ('support', 'definition'):
            value = copy.deepcopy(actual)
            if mutation == 'support':
                value['tasks'][2]['support_assertions'][0]['sha256'] = '0'*64
            else:
                value['tasks'][2]['definitions'][0]['equivalent_after_local_schema_check'] = False
            with self.assertRaises(ValueError):
                ns['reconcile'](old, value, context, semantic)

    def test_source_or_physical_identity_change_prevents_reconciliation(self):
        for key in ('source_commit', 'source_theory_sha256', 'all22_selected_inputs_pre_post_equal'):
            value = copy.deepcopy(actual)
            value[key] = False if key.endswith('equal') else '0'*64
            with self.assertRaises(ValueError):
                ns['reconcile'](old, value, context, semantic)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'child_native_network_attempts': ATTEMPTS, 'controls': result.testsRun,
                      'failures': len(result.failures), 'errors': len(result.errors)}))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
