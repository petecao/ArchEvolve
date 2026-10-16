"""2026-10-16 ET. No-child V4 composition and exact inherited-export controls."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pathlib
import shlex
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure V4 packet control refuses ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
TRACE = HERE.parent / '28-public-memory-trace-resume-20261016'
OLD = ast.parse((HERE / 'linux_pair_entry_v3.py').read_text())
NEW = ast.parse((HERE / 'linux_pair_entry_v4.py').read_text())
POLICY = json.loads((HERE / 'linux_pair_policy_2baf722f_v4.json').read_text())
COMMAND = json.loads((HERE / 'linux_pair_command_2baf722f_v4.json').read_text())
ROOT_EXPORTS = json.loads((HERE / 'linux_pair_root_exports_v3.json').read_text())
spec = importlib.util.spec_from_file_location('t28_pure_roles', TRACE / 'python_startup_roles_v2.py')
ROLES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ROLES)


class LinuxRuntimeV4Controls(unittest.TestCase):
    def test_original_functions_and_scientific_inputs_unchanged(self):
        functions = {node.name: node for node in NEW.body if isinstance(node, ast.FunctionDef)}
        for node in OLD.body:
            if isinstance(node, ast.FunctionDef):
                with self.subTest(function=node.name):
                    self.assertEqual(ast.dump(node, include_attributes=False), ast.dump(functions[node.name], include_attributes=False))
        old_policy = json.loads((HERE / 'linux_pair_policy_2baf722f_v3.json').read_text())
        for name in ('source_commit', 'source_files', 'source_consumer_trees', 'actual_initialized_lineup',
                     'naming', 'linux_clang_components', 'wp_artifacts', 'config', 'portable_import_surfaces'):
            self.assertEqual(old_policy[name], POLICY[name], name)
        pins = {
            'run_initialized_register_acceptance.sh': '982cf10fa9cdbd54e6bd3f7e55f90470778e1816c47bad99ffcef80a1f100895',
        }
        for name, digest in pins.items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), digest)

    def test_root_exact_export_alias_normalizes_before_absolute_preflight_and_final_child_environment(self):
        wanted = POLICY['linux_clang_components']
        environment = {'PATH': '/usr/bin:/bin', 'PROBATA_OUTPUT': COMMAND['raw_root']}
        for line in sorted(ROOT_EXPORTS['exports'], key=int):
            for name, value in ROOT_EXPORTS['exports'][line].items():
                environment[name] = value.replace('$PATH', environment['PATH']).replace('$PROBATA_OUTPUT', environment['PROBATA_OUTPUT'])
        self.assertEqual(environment['SWDB_CLANG'], 'clang++')
        self.assertEqual(environment['PYTHONPATH'], COMMAND['source'])
        selected = {node.name: node for node in NEW.body if isinstance(node, ast.FunctionDef)}
        context = dict(pathlib=pathlib, Path=Path, shlex=shlex, shutil=shutil, sys=sys)
        context['pin'] = lambda path: {'path': path, 'sha256': wanted[
            'driver' if str(path) == wanted['driver']['path'] else 'command_executable']['sha256']}
        exec(compile(ast.Module(body=[selected[name] for name in ('normalize_compiler_selector', 'compiler_preflight',
            'runner_child_environment_v4')], type_ignores=[]), '<exact-root-export-v4-control>', 'exec'), context)
        with patch.object(shutil, 'which', return_value=wanted['command'][0]), patch.object(Path, 'is_file', return_value=True):
            normalization = context['normalize_compiler_selector'](environment, wanted)
            self.assertEqual(normalization['input_tokens'], ['clang++'])
            self.assertEqual(context['compiler_preflight'](environment, wanted)['command'], wanted['command'])
        child = context['runner_child_environment_v4'](environment, Path(COMMAND['source']), Path(COMMAND['raw_root']), ROLES)
        profile = Path(COMMAND['raw_root']) / 'initialized-profile'
        self.assertEqual(shlex.split(child['SWDB_CLANG']), wanted['command'])
        self.assertEqual(child['PYTHONPATH'], COMMAND['source'])
        for name in ('PYTHONNOUSERSITE', 'PYTHONSAFEPATH', 'PYTHONDONTWRITEBYTECODE', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD'):
            self.assertEqual(child[name], '1')
        for name, value in {'PROBATA_OUTPUT': profile, 'SWDB_VERIFIER_LOCK': profile / 'verifier.lock',
                            'PYTHONPYCACHEPREFIX': profile / 'source-cache', 'TMPDIR': profile / 'tmp',
                            'XDG_CACHE_HOME': profile / 'cache'}.items():
            self.assertEqual(child[name], str(value))
        self.assertEqual(child['SWDB_VERIFIER_RSS_CAP_BYTES'], '8589934592')

    def test_actual_role_and_physical_checks_precede_compiler_and_project_imports(self):
        source = (HERE / 'linux_pair_entry_v4.py').read_text()
        start = source.index("closed_v4,_closed_source_v4=load_controller_module_v4")
        first_compiler = source.index('compiler_selector=normalize_compiler_selector')
        first_project = source.index('from swdb import c_lowering,stdlib_provenance')
        for text in ("runtime_surface_check_v4('before')", "observe_startup_role_v4(role_plan_v4,'entry-isolated'",
                     "observe_startup_role_v4(role_plan_v4,'pytest-child'", "runtime_surface_check_v4('after-startup')"):
            index = source.index(text, start)
            self.assertLess(index, first_compiler)
            self.assertLess(index, first_project)
        self.assertNotIn('os.chdir(project);sys.path.insert', source)
        self.assertNotIn('os.execv(', source)
        final = [node for node in NEW.body if isinstance(node, ast.Try)][-1]
        final_text = ast.unparse(ast.Module(body=final.finalbody, type_ignores=[]))
        self.assertIn('source_check()', final_text)
        self.assertIn('consumer_closure(project, repo, EXPECTED)', final_text)
        self.assertIn("runtime_surface_check_v4('after')", final_text)

    def test_controller_and_raw_names_are_exact_and_under_one_mib(self):
        total = 0
        for row in COMMAND['controller_inputs']:
            path = Path(row['path'])
            data = path.read_bytes()
            self.assertEqual(len(data), row['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            total += len(data)
        self.assertLessEqual(total, 1048576)
        self.assertTrue(COMMAND['raw_root'].endswith('-v4'))
        self.assertEqual(POLICY['raw_name'], Path(COMMAND['raw_root']).name)
        self.assertEqual(COMMAND['argv'][-1], hashlib.sha256(Path(COMMAND['controller_inputs'][1]['path']).read_bytes()).hexdigest())
        self.assertEqual(len(POLICY['runtime_files']), 2569)
        meta = POLICY['framac_kernel_meta_origin']['pin']
        self.assertEqual(POLICY['runtime_files'][meta['path']], meta['sha256'])
        self.assertEqual(meta['bytes'], 2318)
        self.assertEqual(len(POLICY['startup_roles']['package_sys_path']), 7)
        self.assertEqual(len(POLICY['python_surface_binding']['surfaces']), 4)

    def test_compact_header_census_rejects_content_membership_and_link_changes(self):
        context = dict(Path=Path, hashlib=hashlib, json=json, stat=__import__('stat'))
        function = next(node for node in NEW.body if isinstance(node, ast.FunctionDef) and node.name == 'header_surface_check_v4')
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<passive-header-census-control>', 'exec'), context)
        closed_spec = importlib.util.spec_from_file_location('t28_pure_closed', TRACE / 'closed_python_surface.py')
        closed = importlib.util.module_from_spec(closed_spec)
        closed_spec.loader.exec_module(closed)
        with tempfile.TemporaryDirectory(prefix='t28-v4-inert-headers-') as temporary:
            base = Path(temporary).resolve()
            expected, aggregate, count = {}, hashlib.sha256(), 0
            for label in ('libc++', 'clang-resource'):
                root = base / label
                root.mkdir()
                (root / 'inert.h').write_text('inert header data, never compiled\n')
                rows = [{'relative': 'inert.h', 'bytes': (root / 'inert.h').stat().st_size,
                         'sha256': hashlib.sha256((root / 'inert.h').read_bytes()).hexdigest()}]
                digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                expected[label] = {'path': str(root), 'count': 1, 'inventory_sha256': digest}
                aggregate.update(label.encode() + b'\0' + b'inert.h\0' + bytes.fromhex(rows[0]['sha256']))
                count += 1
            wanted = {'id': 'llvm-standard-resource-headers', 'sha256': aggregate.hexdigest(), 'files': count}
            self.assertEqual(context['header_surface_check_v4'](expected, wanted, closed)['aggregate'], wanted)
            file = base / 'libc++/inert.h'
            original = file.read_bytes()
            file.write_bytes(original + b'changed')
            with self.assertRaises(ValueError): context['header_surface_check_v4'](expected, wanted, closed)
            file.write_bytes(original)
            extra = file.parent / 'extra.h'
            extra.write_text('new inert header')
            with self.assertRaises(ValueError): context['header_surface_check_v4'](expected, wanted, closed)
            extra.unlink()
            extra.symlink_to('inert.h')
            with self.assertRaisesRegex(ValueError, 'symlink/special'): context['header_surface_check_v4'](expected, wanted, closed)
        common = ast.unparse(next(node for node in NEW.body if isinstance(node, ast.FunctionDef) and node.name == 'runtime_surface_check_v4'))
        for name in ('why3_stdlib', 'wp_why3_support', 'why3_drivers', 'header_surface_check_v4'):
            self.assertIn(name, common)


if __name__ == '__main__':
    unittest.main(verbosity=2)
