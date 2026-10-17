"""2026-10-16 ET. Exact root-export snapshot -> normalization -> preflight.

Remote paths/bytes are explicit test doubles, never a live runtime observation.
No shell, compiler, CLI, process, native binary or SSH is run.
"""
import ast
import copy
import hashlib
import json
import pathlib
import shlex
import sys
import types
import unittest
from unittest.mock import patch


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure normalization control prohibits child execution')


sys.addaudithook(deny)
HERE = pathlib.Path(__file__).resolve().parent
TREE = ast.parse((HERE / 'linux_pair_entry_v3.py').read_text())
NODES = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in
         {'normalize_compiler_selector', 'compiler_preflight'}]
SNAPSHOT = json.loads((HERE / 'linux_pair_root_exports_v3.json').read_text())
POLICY = json.loads((HERE / 'linux_pair_policy_2baf722f_v3.json').read_text())


def root_environment():
    environment = {'PATH': '/usr/bin:/bin', 'PROBATA_OUTPUT': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-2baf722f-v3'}
    for line in ('5', '6', '13'):
        for name, value in SNAPSHOT['exports'][line].items():
            environment[name] = value.replace('$PATH', environment['PATH']).replace('$PROBATA_OUTPUT', environment['PROBATA_OUTPUT'])
    return environment


class RootCompilerExportControls(unittest.TestCase):
    def setUp(self):
        self.wanted = copy.deepcopy(POLICY['linux_clang_components'])
        self.wrapper = self.wanted['command_executable']['path']
        self.driver = self.wanted['driver']['path']
        self.alias_path = self.wrapper
        self.pins = {self.wrapper: self.wanted['command_executable']['sha256'], self.driver: self.wanted['driver']['sha256']}
        self.discoveries = []
        def which(command, path=None):
            self.discoveries.append((command, path))
            return self.alias_path if command == 'clang++' else command if command == self.wrapper else None
        def pin(path):
            name = str(pathlib.Path(path).resolve())
            return {'path': name, 'sha256': self.pins[name]}
        self.namespace = {'pathlib': pathlib, 'shlex': shlex, 'shutil': types.SimpleNamespace(which=which), 'pin': pin}
        exec(compile(ast.Module(body=NODES, type_ignores=[]), '<normalization-preflight-exact-export-ast>', 'exec'), self.namespace)
        self.normalize = self.namespace['normalize_compiler_selector']
        self.preflight = self.namespace['compiler_preflight']
        self.files = patch.object(pathlib.Path, 'is_file', side_effect=lambda: True)
        self.files.start()
        self.addCleanup(self.files.stop)

    def together(self, environment):
        receipt = self.normalize(environment, self.wanted)
        preflight = self.preflight(environment, self.wanted)
        return receipt, preflight

    def test_exact_root_export_snapshot_becomes_exact_absolute_public_tokens(self):
        self.assertEqual(SNAPSHOT['root_run_sh'], {'bytes': 1115, 'sha256': '3ebfee9c5295f4e21b35e301003341eff5cc2824f8b5269a67747a5c6bd4cc1e'})
        environment = root_environment()
        original = dict(environment)
        self.assertEqual(environment['SWDB_CLANG'], 'clang++')
        self.assertTrue(environment['PATH'].startswith(str(pathlib.Path(self.wrapper).parent) + ':'))
        receipt, preflight = self.together(environment)
        self.assertEqual(self.discoveries[0], ('clang++', original['PATH']))
        self.assertEqual(receipt['input_tokens'], ['clang++'])
        self.assertTrue(receipt['reviewed_alias_used'])
        self.assertEqual(receipt['resolved_alias_wrapper']['sha256'], self.pins[self.wrapper])
        self.assertEqual(shlex.split(environment['SWDB_CLANG']), self.wanted['command'])
        self.assertEqual(preflight['command'], self.wanted['command'])
        self.assertTrue(pathlib.Path(preflight['command'][0]).is_absolute())
        self.assertEqual({k: v for k, v in environment.items() if k != 'SWDB_CLANG'},
                         {k: v for k, v in original.items() if k != 'SWDB_CLANG'})
        self.assertEqual(environment['PYTHONPATH'], '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project')
        self.assertEqual(environment['SWDB_VERIFIER_LOCK'], environment['PROBATA_OUTPUT'] + '/verifier.lock')
        self.assertEqual(environment['SWDB_VERIFIER_RSS_CAP_BYTES'], '8589934592')

    def test_final_absolute_public_tokens_pass_together_without_alias_admission(self):
        environment = root_environment()
        environment['SWDB_CLANG'] = shlex.join(self.wanted['command'])
        receipt, preflight = self.together(environment)
        self.assertFalse(receipt['reviewed_alias_used'])
        self.assertIsNone(receipt['resolved_alias_wrapper'])
        self.assertEqual(receipt['selected_absolute_tokens'], preflight['command'])

    def test_unknown_selectors_refuse_before_discovery_and_never_normalize(self):
        for selector in ['clang', './clang++', '/other/clang++', 'clang++ -bad', self.wrapper + ' -bad', "'unterminated"]:
            with self.subTest(selector=selector):
                environment = root_environment()
                environment['SWDB_CLANG'] = selector
                before = dict(environment)
                self.discoveries.clear()
                with self.assertRaises(ValueError):
                    self.together(environment)
                self.assertEqual(environment, before)
                self.assertEqual(self.discoveries, [])

    def test_known_alias_wrong_resolution_or_bytes_refuses_without_normalization(self):
        for path in (None, '/other/clang++'):
            self.alias_path = path
            environment = root_environment()
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'another physical'):
                self.together(environment)
            self.assertEqual(environment['SWDB_CLANG'], 'clang++')
        self.alias_path = self.wrapper
        self.pins[self.wrapper] = '0' * 64
        environment = root_environment()
        with self.assertRaisesRegex(ValueError, 'wrapper bytes differ'):
            self.together(environment)
        self.assertEqual(environment['SWDB_CLANG'], 'clang++')

    def test_preflight_keeps_underlying_driver_check_after_alias_normalization(self):
        self.pins[self.driver] = '0' * 64
        environment = root_environment()
        with self.assertRaisesRegex(ValueError, 'driver bytes differ'):
            self.together(environment)
        self.assertEqual(shlex.split(environment['SWDB_CLANG']), self.wanted['command'])

    def test_v3_inverse_ast_equals_v2_and_preflight_guard_is_unchanged(self):
        old = ast.parse((HERE / 'linux_pair_entry_v2.py').read_text())
        new = copy.deepcopy(TREE)
        class UndoNormalization(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                return None if node.name == 'normalize_compiler_selector' else self.generic_visit(node)
            def visit_Assign(self, node):
                return None if any(isinstance(t, ast.Name) and t.id == 'compiler_selector' for t in node.targets) else node
            def visit_Dict(self, node):
                remove = [i for i, key in enumerate(node.keys) if isinstance(key, ast.Constant) and key.value == 'compiler_selector_normalization']
                node.keys = [key for i, key in enumerate(node.keys) if i not in remove]
                node.values = [value for i, value in enumerate(node.values) if i not in remove]
                return self.generic_visit(node)
        self.assertEqual(ast.dump(old), ast.dump(UndoNormalization().visit(new)))
        top = TREE.body
        normalizer = next(i for i, node in enumerate(top) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'compiler_selector' for t in node.targets))
        preflight = next(i for i, node in enumerate(top) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'compiler_binding' for t in node.targets))
        first_project_import = next(i for i, node in enumerate(top) if isinstance(node, ast.ImportFrom) and node.module == 'swdb')
        self.assertLess(normalizer, preflight)
        self.assertLess(preflight, first_project_import)

    def test_policy_inverse_preserves_every_existing_source_runtime_guard_pin(self):
        old = json.loads((HERE / 'linux_pair_policy_2baf722f_v2.json').read_text())
        new = copy.deepcopy(POLICY)
        new.pop('compiler_selector_normalization')
        new['linux_launch_binding']['entry_sha256'] = old['linux_launch_binding']['entry_sha256']
        self.assertEqual(new, old)
        command = json.loads((HERE / 'linux_pair_command_2baf722f_v3.json').read_text())
        self.assertTrue(command['raw_root'].endswith('-v3'))
        self.assertEqual(command['argv'][-1], hashlib.sha256((HERE / 'linux_pair_policy_2baf722f_v3.json').read_bytes()).hexdigest())
        self.assertEqual(POLICY['linux_launch_binding']['entry_sha256'], hashlib.sha256((HERE / 'linux_pair_entry_v3.py').read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)
