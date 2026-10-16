"""2026-10-16 ET. Pure Linux packet controls; no producer or child process runs."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import pathlib
import re
import shlex
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('pure packet control refuses ' + event)


sys.addaudithook(deny)
ROOT = Path(__file__).resolve().parent
TREE = ast.parse((ROOT / 'linux_trace_entry_v1.py').read_text())
ALLOWED = {'pin', 'compiler_preflight', 'normalize_compiler_selector', 'ambient_check', 'validate_policy', 'junit_census'}
NODES = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in ALLOWED
         or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'PACKET', 'TEST_FUNCTION', 'CONSUMER_ROOTS'} for target in node.targets)]
CONTEXT = dict(hashlib=hashlib, json=json, os=os, pathlib=pathlib, Path=Path, re=re, shlex=shlex, shutil=shutil, ET=ET)
exec(compile(ast.Module(body=NODES, type_ignores=[]), '<linux-packet-pure-ast>', 'exec'), CONTEXT)


def valid_policy():
    wanted = json.loads((ROOT / 'linux_trace_policy_template.json').read_bytes())
    wanted.update(admitted=True, source_commit='1' * 40, source_root='/admitted/checkout/swdb-project',
                  raw_name='probata-resume-20261016-t28-memory-trace-11111111-v1',
                  source_files={'swdb/bounded_initialization.py': '2' * 64},
                  runtime_files={'/admitted/python-loader.so': '3' * 64})
    wanted['source_consumer_trees'] = {root: {'oid': '9' * 40} for root in wanted['source_consumer_trees']}
    wanted['linux_clang_components'] = {'command': ['/admitted/clang++'],
        'command_executable': {'path': '/admitted/clang++', 'sha256': '4' * 64},
        'driver': {'path': '/admitted/clang-22', 'sha256': '5' * 64},
        'headers': {'files': 1, 'id': 'fixture-only', 'sha256': '6' * 64},
        'parser': {'id': 'fixture-only', 'sha256': '7' * 64}}
    wanted['tools'] = {name: {'path': '/admitted/' + name, 'sha256': '8' * 64}
                       for name in ('cbmc', 'frama-c', 'opam', 'python', 'ocamlfind', 'ocamlopt', 'why3', 'gcc', 'z3', 'cvc5', 'alt-ergo')}
    wanted['tools']['cbmc']['version'] = '6.11'
    wanted['tools']['frama-c']['version'] = '33.0'
    return wanted


class LinuxPacketControls(unittest.TestCase):
    def test_unbound_template_is_inert(self):
        policy = json.loads((ROOT / 'linux_trace_policy_template.json').read_text())
        with self.assertRaisesRegex(ValueError, 'fresh explicit'):
            CONTEXT['validate_policy'](policy)

    def test_policy_exact_shape_accepts_only_explicit_pins(self):
        self.assertEqual(CONTEXT['validate_policy'](valid_policy())['source_commit'], '1' * 40)
        original = valid_policy()
        mutations = [lambda p: p.update(source_commit=None), lambda p: p.update(raw_name='old'),
                     lambda p: p['guard'].update(workers=2), lambda p: p['guard'].update(timeout_seconds=1201),
                     lambda p: p['guard'].update(rss_cap_bytes=8589934593), lambda p: p.update(source_consumer_trees={}),
                     lambda p: p.update(source_files={}), lambda p: p.update(runtime_files={}),
                     lambda p: p.update(python_import_surfaces={}), lambda p: p['tools']['cbmc'].update(version='6.10'),
                     lambda p: p['junit'].update(skipped=1), lambda p: p['selection'].pop(),
                     lambda p: p['linux_clang_components'].update(command=['clang++']),
                     lambda p: p['linux_clang_components'].update(command=['/admitted/clang++', '-Doverride']),
                     lambda p: p['linux_clang_components']['command_executable'].update(path='/other/clang++')]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                policy = copy.deepcopy(original)
                mutate(policy)
                with self.assertRaises(ValueError):
                    CONTEXT['validate_policy'](policy)

    def test_absolute_pinned_compiler_preflight_preserves_all_existing_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            wrapper, driver = Path(folder) / 'clang++', Path(folder) / 'clang-22'
            wrapper.write_text('inert wrapper bytes')
            driver.write_text('inert driver bytes')
            wanted = {'command': [str(wrapper)], 'command_executable': CONTEXT['pin'](wrapper), 'driver': CONTEXT['pin'](driver)}
            with patch.object(shutil, 'which', return_value=str(wrapper)):
                self.assertEqual(CONTEXT['compiler_preflight']({'SWDB_CLANG': str(wrapper)}, wanted)['command'], [str(wrapper)])
                with self.assertRaisesRegex(ValueError, 'ambient Clang'):
                    CONTEXT['compiler_preflight']({'SWDB_CLANG': 'clang++'}, wanted)
                environment = {'SWDB_CLANG': 'clang++', 'PATH': '/reviewed/root/compiler-bin:/usr/bin'}
                normalized = CONTEXT['normalize_compiler_selector'](environment, wanted)
                self.assertTrue(normalized['reviewed_alias_used'])
                self.assertEqual(CONTEXT['compiler_preflight'](environment, wanted)['command'], [str(wrapper)])
                driver.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'driver bytes'):
                    CONTEXT['compiler_preflight']({}, wanted)

    def test_relative_command_refuses_before_discovery_or_execution(self):
        with patch.object(shutil, 'which', side_effect=AssertionError('must not discover')):
            with self.assertRaisesRegex(ValueError, 'command shape'):
                CONTEXT['compiler_preflight']({}, {'command': ['clang++']})

    def test_junit_exact25_and_each_failure_shape(self):
        policy = valid_policy()
        root = ET.Element('testsuites')
        suite = ET.SubElement(root, 'testsuite', tests='25', errors='0', failures='0', skipped='0')
        for node in policy['selection']:
            ET.SubElement(suite, 'testcase', classname=policy['junit_classname'], name=node.split('::')[-1])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'junit.xml'
            def check(tree):
                ET.ElementTree(tree).write(path)
                return CONTEXT['junit_census'](path, policy['selection'], policy['junit_classname'])
            self.assertTrue(check(root)['accepted'])
            mutations = [lambda tree: list(tree)[0].set('tests', '24'),
                         lambda tree: list(tree)[0].set('errors', '1'),
                         lambda tree: list(tree)[0].set('failures', '1'),
                         lambda tree: list(tree)[0].set('skipped', '1'),
                         lambda tree: list(list(tree)[0])[0].set('classname', 'other'),
                         lambda tree: list(list(tree)[0])[0].set('name', 'other'),
                         lambda tree: ET.SubElement(list(list(tree)[0])[0], 'skipped'),
                         lambda tree: ET.SubElement(tree, 'testsuite', tests='0', errors='0', failures='0', skipped='0')]
            for index, mutate in enumerate(mutations):
                with self.subTest(mutation=index):
                    tree = copy.deepcopy(root)
                    mutate(tree)
                    with self.assertRaises(ValueError):
                        check(tree)

    def test_reviewed_helpers_preserved_except_absolute_compiler_guard(self):
        basis = ROOT.parent / '28-initialized-u32-resume-20261016/linux_pair_entry_v1.py'
        original = ast.parse(basis.read_text())
        old = {node.name: node for node in original.body if isinstance(node, ast.FunctionDef)}
        new = {node.name: node for node in TREE.body if isinstance(node, ast.FunctionDef)}
        for name in ('consumer_closure', 'pin', 'ambient_check', 'validate_linux_launch', 'verified_linux_lane', 'import_surface', 'compiler_components'):
            self.assertEqual(ast.dump(old[name]), ast.dump(new[name]))
        reviewed = ast.parse((ROOT.parent / '28-initialized-u32-resume-20261016/linux_pair_selector_v3.py.inc').read_text())
        self.assertEqual(ast.dump(new['normalize_compiler_selector']), ast.dump(reviewed.body[0]))

    def test_entry_has_no_unguarded_top_level_runtime(self):
        for node in TREE.body:
            self.assertIsInstance(node, (ast.Expr, ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef, ast.If))
            if isinstance(node, ast.Expr):
                self.assertIsInstance(node.value, ast.Constant)
            if isinstance(node, ast.If):
                self.assertEqual(ast.unparse(node.test), "__name__ == '__main__'")
        main = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        assignments = {target.id: node.lineno for node in ast.walk(main) if isinstance(node, ast.Assign)
                       for target in node.targets if isinstance(target, ast.Name)}
        imports = [node.lineno for node in ast.walk(main) if isinstance(node, ast.ImportFrom) and node.module == 'swdb']
        self.assertLess(assignments['compiler_selector'], assignments['compiler'])
        self.assertLess(assignments['compiler'], min(imports))


if __name__ == '__main__':
    unittest.main(verbosity=2)
