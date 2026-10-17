"""2026-10-16 ET. Inert diagnostic control gates; no method/tool imports."""
import ast
import copy
import json
import math
from pathlib import Path
import sys
import unittest


ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) \
            or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise RuntimeError('no external process/native/network in diagnostic controls')


sys.addaudithook(audit)
FILE = Path(__file__).with_name('public_move_diagnostic_v1.py')
TREE = ast.parse(FILE.read_text())
names = {'METHOD', 'CONTRACT', 'FUNCTION', 'WHOLE', 'BUDGET'}
selected = [node for node in TREE.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in names or isinstance(node, ast.FunctionDef)
            and node.name == 'completion_gate']
NS = {'math': math}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(FILE), 'exec'), NS)
GOOD = {'function': NS['FUNCTION'], 'contract': NS['CONTRACT'], 'method': NS['METHOD'],
        'record_subject': {'kind': 'library_summary', 'id': NS['CONTRACT']},
        'record_method': NS['METHOD'], 'verdict': 'not_proven', 'ordinary_goals': 1,
        'native_files_preserved': 1,
        'resources': {'exit_code': 0, 'out_of_memory': False, 'timed_out': False}}


def gate(row, elapsed=10, size=1024):
    return NS['completion_gate'](row, wall_seconds=elapsed, retained_bytes=size)


class Controls(unittest.TestCase):
    def test_full_normal_not_proven_is_complete_diagnostic(self):
        self.assertTrue(gate(GOOD))

    def test_full_native_proven_still_only_completed_diagnostic(self):
        row = copy.deepcopy(GOOD); row['verdict'] = 'proven'
        self.assertTrue(gate(row))

    def test_record_from_default_or_wrong_method_refuses(self):
        row = copy.deepcopy(GOOD); row['record_method'] = 'method.contract-fixture-1'
        self.assertFalse(gate(row))

    def test_wrong_record_subject_refuses(self):
        row = copy.deepcopy(GOOD); row['record_subject']['id'] = 'contract.other'
        self.assertFalse(gate(row))

    def test_no_real_ordinary_census_refuses(self):
        for value in (0, True, -1, None):
            row = copy.deepcopy(GOOD); row['ordinary_goals'] = value
            self.assertFalse(gate(row))

    def test_missing_native_materialization_refuses(self):
        row = copy.deepcopy(GOOD); row['native_files_preserved'] = 0
        self.assertFalse(gate(row))

    def test_resource_failure_or_boolean_exit_refuses(self):
        for value in (1, -9, False, None):
            row = copy.deepcopy(GOOD); row['resources']['exit_code'] = value
            self.assertFalse(gate(row))

    def test_oom_refuses(self):
        row = copy.deepcopy(GOOD); row['resources']['out_of_memory'] = True
        self.assertFalse(gate(row))

    def test_timeout_refuses(self):
        row = copy.deepcopy(GOOD); row['resources']['timed_out'] = True
        self.assertFalse(gate(row))

    def test_missing_explicit_resource_flags_refuses(self):
        for key in ('timed_out', 'out_of_memory'):
            row = copy.deepcopy(GOOD); del row['resources'][key]
            self.assertFalse(gate(row))

    def test_whole_budget_nan_inf_negative_or_bool_refuses(self):
        for value in (601, -1, True, float('nan'), float('inf')):
            self.assertFalse(gate(GOOD, elapsed=value))

    def test_retained_budget_bool_or_excess_refuses(self):
        for value in (NS['BUDGET']+1, -1, True, 1.5):
            self.assertFalse(gate(GOOD, size=value))

    def test_exact_budget_endpoints_are_allowed(self):
        self.assertTrue(gate(GOOD, elapsed=NS['WHOLE'], size=NS['BUDGET']))

    def test_wrong_original_contract_or_function_refuses(self):
        for key in ('function', 'contract', 'method'):
            row = copy.deepcopy(GOOD); row[key] += '_other'
            self.assertFalse(gate(row))

    def test_no_external_attempts(self):
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                      'external_attempts': ATTEMPTS, 'actual_diagnostic_execution': False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
