"""2026-10-16 ET. Independent compiler-free native86 admission controls.

Only actual source function AST slices run, against small local filesystem
fixtures. No controller main, compiler, linker, native program, SSH, or version
probe runs. The source payload's separate semantics review remains separate.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
EVENTS = []


def deny_children(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        EVENTS.append(event)
        raise RuntimeError('independent no-child native86 control refuses ' + event)


sys.addaudithook(deny_children)


def tree(version):
    return ast.parse((WHOLE / ('linux_native86_entry_' + version + '.py')).read_bytes())


def function(source_tree, name, **values):
    nodes = [node for node in ast.walk(source_tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(nodes) == 1
    context = {'Path': Path, 'hashlib': hashlib, 'json': json, 'os': os, 'stat': stat, **values}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<native86-' + name + '>', 'exec'), context)
    return context[name]


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Native86AdmissionGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = tree('v1')
        cls.new = tree('v2')

    def test_policy_symlink_red_old_green_successor_and_fifo_refused(self):
        def check(source_tree, directory):
            control = directory / 'control'; control.mkdir(exist_ok=True)
            entry = control / 'entry.py'; entry.write_bytes(b'inert source bytes\n')
            (control / 'fixture.h').write_bytes(b'inert header\n')
            policy_path = control / 'policy.json'; policy_bytes = b'{"inert":true}\n'
            policy_path.write_bytes(policy_bytes)
            pin = function(source_tree, 'pin')
            controls = {p.name: {key: value for key, value in pin(p).items() if key != 'path'} for p in (entry, control / 'fixture.h')}
            return control, policy_path, policy_bytes, function(source_tree, 'control_check',
                control=control, policy_path=policy_path, controls=controls,
                policy={'entry_sha256': digest(entry.read_bytes())}, __file__=str(entry),
                argv=['inert', '', '', '', digest(policy_bytes)], pin=pin)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            old_control, old_path, old_bytes, old_check = check(self.old, root)
            old_check(); outside = root / 'outside.json'; outside.write_bytes(old_bytes)
            old_path.unlink(); old_path.symlink_to(outside)
            self.assertIsNone(old_check())  # Exact bytes alone miss topology change.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            control, policy_path, policy_bytes, revised_check = check(self.new, root)
            self.assertIsNone(revised_check())
            outside = root / 'outside.json'; outside.write_bytes(policy_bytes)
            policy_path.unlink(); policy_path.symlink_to(outside)
            with self.assertRaises(ValueError): revised_check()
            policy_path.unlink(); os.mkfifo(policy_path)
            with self.assertRaises(ValueError): revised_check()

    def test_control_bytes_and_membership_refuse_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            control = Path(temporary).resolve()
            entry = control / 'entry.py'; entry.write_bytes(b'inert entry\n')
            policy_path = control / 'policy.json'; policy_path.write_bytes(b'{}\n')
            pin = function(self.new, 'pin')
            controls = {entry.name: {'bytes': entry.stat().st_size, 'sha256': digest(entry.read_bytes())}}
            check = function(self.new, 'control_check', control=control, policy_path=policy_path,
                controls=controls, policy={'entry_sha256': digest(entry.read_bytes())},
                __file__=str(entry), argv=['inert', '', '', '', digest(policy_path.read_bytes())], pin=pin)
            check(); extra = control / 'extra'; extra.write_bytes(b'')
            with self.assertRaises(ValueError): check()
            extra.unlink(); entry.write_bytes(b'changed')
            with self.assertRaises(ValueError): check()

    def test_complete_runtime_trees_aliases_absences_and_headers_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); headers = root / 'headers'; headers.mkdir()
            native = root / 'native'; native.mkdir(); physical = native / 'lib'; physical.write_bytes(b'fixed runtime')
            outside = root / 'other'; outside.write_bytes(b'fixed runtime')
            alias = root / 'alias'; alias.symlink_to(physical)
            pin = function(self.new, 'pin'); recheck = function(self.new, 'recheck', pin=pin)
            runtime = function(self.new, 'physical_runtime', pin=pin, recheck=recheck)
            policy = {'python_surface_binding': {}, 'runtime_files': {},
                'linux_header_surfaces': {name: {'path': str(headers), 'count': 0, 'inventory_sha256': digest(b'[]')}
                    for name in ('libc++', 'clang-resource')},
                'native_runtime': {'admitted': True, 'pins': [pin(physical)],
                    'aliases': [{'path': str(alias), 'target': str(physical), 'resolved': str(physical)}],
                    'absence': [str(root / 'absent')],
                    'trees': [{'path': str(native), 'files': [{'relative': 'lib', 'bytes': physical.stat().st_size,
                                                              'sha256': digest(physical.read_bytes())}]}]}}
            closed = SimpleNamespace(verify_python_metadata=lambda metadata: {'inert': True}, _resolution=lambda path, links: path)
            self.assertEqual(runtime(policy, closed)['native_roots'], 1)
            for mutation in ('unknown_file', 'file_bytes', 'retarget_alias', 'new_absent', 'unknown_header', 'unknown_link'):
                with self.subTest(mutation=mutation):
                    if mutation == 'unknown_file': (native / 'extra').write_bytes(b'')
                    elif mutation == 'file_bytes': physical.write_bytes(b'changed')
                    elif mutation == 'retarget_alias': alias.unlink(); alias.symlink_to(outside)
                    elif mutation == 'new_absent': (root / 'absent').write_bytes(b'')
                    elif mutation == 'unknown_header': (headers / 'extra.h').write_bytes(b'')
                    else: (native / 'extra-link').symlink_to(outside)
                    with self.assertRaises(ValueError): runtime(policy, closed)
                    if mutation == 'unknown_file': (native / 'extra').unlink()
                    elif mutation == 'file_bytes': physical.write_bytes(b'fixed runtime')
                    elif mutation == 'retarget_alias': alias.unlink(); alias.symlink_to(physical)
                    elif mutation == 'new_absent': (root / 'absent').unlink()
                    elif mutation == 'unknown_header': (headers / 'extra.h').unlink()
                    else: (native / 'extra-link').unlink()

    def test_policy_runtime_inventory_exact_consistency_and_stage_budget(self):
        policy = json.loads((WHOLE / 'linux_native86_policy_v2.json').read_text())
        inventory = json.loads((WHOLE / 'native86-linux-runtime-passive-v5.json').read_text())
        for key in ('pins', 'aliases', 'trees', 'absence', 'loader_environment'):
            self.assertEqual(policy['native_runtime'][key], inventory[key])
        self.assertFalse(inventory['admitted']); self.assertTrue(inventory['passive_only'])
        self.assertEqual(inventory['unresolved'], []); self.assertEqual(inventory['prior_pin_differences'], [])
        pins = {row['path']: row['sha256'] for row in inventory['pins']}
        self.assertEqual(len(pins), 608)
        for path, sha in pins.items():
            if path in policy['runtime_files']: self.assertEqual(sha, policy['runtime_files'][path])
        self.assertEqual(len(inventory['aliases']), 158); self.assertEqual(len(inventory['trees']), 4)
        self.assertLess(sum(row['bytes'] for row in policy['controller_files'].values()) + (WHOLE / 'linux_native86_policy_v2.json').stat().st_size, 2**20)
        self.assertEqual(policy['budgets'], {'whole_seconds': 180, 'entry_seconds': 165, 'rss_bytes': 4294967296,
            'stage_bytes': 134217728, 'total_bytes': 268435456})
        self.assertEqual(policy['compiler']['linker']['path'], '/usr/bin/x86_64-linux-gnu-ld.bfd')

    def test_used_inputs_are_rechecked_and_scope_remains_private(self):
        main = next(node for node in self.new.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        source = ast.unparse(main)
        self.assertIn('finally:', source)
        for required in ('physical_runtime(policy, closed)', 'control_check()', "recheck(source_pins)", "len(commands) == 8", "len(observations) == 2"):
            self.assertIn(required, source)
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'stage']
        self.assertEqual(len(calls), 4)
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(main)))
        self.assertEqual(EVENTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
