"""2026-10-16 ET. Execute the actual policy-validator seam, no children."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure actual-validator seam refuses ' + event)


sys.addaudithook(deny)


def load(name): return json.loads((HERE / name).read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def validator(name):
    tree = ast.parse((HERE / name).read_bytes())
    assignments = {'PACKET', 'TEST_FUNCTION', 'CONSUMER_ROOTS', 'KERNEL_META_PIN_V2', 'CONTROL_NAMES_V2'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'validate_policy_v2'
             or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in assignments for target in node.targets)]
    context = {'Path': Path, 're': re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), name, 'exec'), context)
    return context['validate_policy_v2']


class NamespaceRegression(unittest.TestCase):
    def test_actual_old_validator_reproduces_pretool_refusal(self):
        old = validator('linux_trace_entry_v2.py')
        self.assertIsNotNone(old(load('linux_trace_policy_57c22ba6_v2.json')))
        with self.assertRaisesRegex(ValueError, '^fresh V2 memory-trace raw namespace differs$'):
            old(load('linux_trace_policy_04af74c1_v3.json'))

    def test_exact_final_policy_passes_real_successor_validator(self):
        policy = load('linux_trace_policy_04af74c1_v4.json')
        self.assertIs(validator('linux_trace_entry_v4.py')(policy), policy)

    def test_wrong_suffix_prefix_source_and_guard_still_refuse(self):
        validate = validator('linux_trace_entry_v4.py')
        original = load('linux_trace_policy_04af74c1_v4.json')
        for raw in (original['raw_name'].removesuffix('-v4') + '-v3',
                    original['raw_name'].removesuffix('-v4') + '-v2',
                    original['raw_name'].replace('04af74c1', '2baf722f')):
            policy = copy.deepcopy(original); policy['raw_name'] = raw
            with self.assertRaisesRegex(ValueError, 'raw namespace differs'): validate(policy)
        for changed in ({'source_commit': '0' * 40}, {'guard': {'workers': 2, 'rss_cap_bytes': 8589934592, 'timeout_seconds': 1200}},
                        {'junit': {'tests': 25, 'errors': 0, 'failures': 0, 'skipped': 1}}):
            policy = copy.deepcopy(original); policy.update(changed)
            with self.assertRaises(ValueError): validate(policy)

    def test_entry_policy_and_command_exact_namespace_inverse(self):
        old = (HERE / 'linux_trace_entry_v2.py').read_text()
        new = (HERE / 'linux_trace_entry_v4.py').read_text()
        inverse = new.replace("'probata-resume-20261016-t28-memory-trace-' + commit[:8] + '-v4'",
                              "'probata-resume-20261016-t28-memory-trace-' + commit[:8] + '-v2'", 1).replace(
                              "raise ValueError('fresh V4 memory-trace raw namespace differs')",
                              "raise ValueError('fresh V2 memory-trace raw namespace differs')", 1)
        self.assertEqual(inverse, old)
        policy_old = load('linux_trace_policy_04af74c1_v3.json')
        policy_new = load('linux_trace_policy_04af74c1_v4.json')
        inverse = copy.deepcopy(policy_new)
        for key in ('raw_name', 'status'): inverse[key] = policy_old[key]
        inverse['linux_launch_binding']['entry_sha256'] = policy_old['linux_launch_binding']['entry_sha256']
        self.assertEqual(inverse, policy_old)
        command_old = load('linux_trace_command_04af74c1_v3.json')
        command_new = load('linux_trace_command_04af74c1_v4.json')
        inverse = copy.deepcopy(command_new)
        for key in ('raw_root', 'status', 'argv', 'controller_inputs', 'control_total_bytes', 'root_places_exact_controller_metadata'):
            inverse[key] = command_old[key]
        self.assertEqual(inverse, command_old)

    def test_final_command_pins_exact_validated_policy_and_unchanged_controls(self):
        policy = load('linux_trace_policy_04af74c1_v4.json'); command = load('linux_trace_command_04af74c1_v4.json')
        raw = command['raw_root']; rows = command['controller_inputs']
        self.assertEqual(command['argv'][7:], [raw + '/control/linux_trace_entry_v4.py', command['source'], raw,
            raw + '/control/linux_trace_policy_04af74c1_v4.json', sha(HERE / 'linux_trace_policy_04af74c1_v4.json')])
        self.assertEqual(policy['raw_name'], Path(raw).name)
        self.assertEqual(policy['linux_launch_binding']['entry_sha256'], sha(HERE / 'linux_trace_entry_v4.py'))
        self.assertEqual(len(rows), 9)
        self.assertLessEqual(sum(row['bytes'] for row in rows), 1048576)
        self.assertEqual(rows[2:], load('linux_trace_command_04af74c1_v3.json')['controller_inputs'][2:])
        for row in rows:
            path = Path(row['path']); self.assertFalse(path.is_symlink())
            self.assertEqual(path.stat().st_size, row['bytes']); self.assertEqual(sha(path), row['sha256'])


if __name__ == '__main__': unittest.main(verbosity=2)
