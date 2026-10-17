"""2026-10-16 ET. Pure prospective initialized-pair native-health controls."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def no_children(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('pure outcome test refuses ' + event)


sys.addaudithook(no_children)
PROJECT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('initialized_outcomes', PROJECT / 'tests/testkit/dx100_initialized_register_outcomes.py')
outcomes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outcomes)


class NativeOutcomeTests(unittest.TestCase):
    def fixture(self, path, expected):
        positive = expected == 711
        status = 'valid' if positive else 'unknown'
        record = {'verdict': 'proven' if positive else 'not_proven', 'failure_class': None if positive else 'unknown',
                  'goals': [{'goal': 'typed_trust_fixture_requires', 'smoke': False, 'status': 'valid'},
                            {'goal': 'typed_trust_fixture_ensures', 'smoke': False, 'status': status},
                            {'goal': 'smoke_trust_fixture_entry', 'smoke': True, 'status': 'valid'}]}
        rows = [{'goal': 'typed_trust_fixture_requires', 'smoke': False, 'passed': True, 'results': ['valid']},
                {'goal': 'typed_trust_fixture_ensures', 'smoke': False, 'passed': positive, 'results': ['valid'] if positive else ['timeout', 'unknown', 'timeout']},
                {'goal': 'smoke_trust_fixture_entry', 'smoke': True, 'passed': True, 'results': ['unknown', 'timeout']}]
        return record, rows

    def observe(self, expected=1107, problem=None):
        with tempfile.TemporaryDirectory(prefix='probata-resume-20261016-t28-outcome-') as directory:
            path = Path(directory) / 'wp_inventory.json'
            record, rows = self.fixture(path, expected)
            complete = True
            if problem == 'native_failed': rows[1]['results'].append('failed')
            elif problem == 'unattempted': rows[1]['results'] = ['untried']
            elif problem == 'missing_smoke': record['goals'].pop(); rows.pop()
            elif problem == 'smoke_proved_false': rows[2]['results'] = ['valid']
            elif problem == 'smoke_unattempted': rows[2]['results'] = ['untried']
            elif problem == 'missing_goal': rows.pop(0)
            elif problem == 'extra_goal': rows.append(dict(rows[0], goal='unread'))
            elif problem == 'duplicate_goal': rows.append(copy.deepcopy(rows[0]))
            elif problem == 'changed_pass': rows[1]['passed'] = not rows[1]['passed']
            elif problem == 'extra_failed_requires': record['goals'][0]['status'] = 'unknown'; rows[0].update(passed=False, results=['unknown'])
            elif problem == 'solver_error': record['failure_class'] = 'solver_error'
            elif problem == 'incomplete': complete = False
            elif problem == 'no_direct_valid': rows[1]['results'] = []
            path.write_text(json.dumps({'version': '1', 'complete': complete, 'goals': rows}))
            record['evidence'] = {'reports': [{'name': 'wp_inventory', 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}
            if problem == 'changed_hash': record['evidence']['reports'][0]['sha256'] = '0' * 64
            return outcomes.assert_initialized_native_outcome(record, expected)

    def test_healthy_positive_reads_all_native_goals(self):
        self.assertEqual(self.observe(711), {'ordinary': 2, 'smoke': 1, 'failed_ordinary': 0})

    def test_healthy_wrong_postcondition_is_nonproof(self):
        self.assertEqual(self.observe(), {'ordinary': 2, 'smoke': 1, 'failed_ordinary': 1})

    def test_pass_flag_without_direct_valid_is_refused(self):
        with self.assertRaises(AssertionError): self.observe(711, 'no_direct_valid')

    def test_every_unhealthy_or_unread_native_case_refuses(self):
        for problem in ('native_failed', 'unattempted', 'missing_smoke', 'smoke_proved_false',
                        'smoke_unattempted', 'missing_goal', 'extra_goal', 'duplicate_goal',
                        'changed_pass', 'extra_failed_requires', 'solver_error', 'incomplete', 'changed_hash'):
            with self.subTest(problem=problem):
                with self.assertRaises(AssertionError): self.observe(problem=problem)


if __name__ == '__main__':
    unittest.main()
