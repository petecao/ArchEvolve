"""2026-10-16 ET. Pure Linux bootstrap environment seam; no project/tool imports."""
import ast
from pathlib import Path
import sys
import unittest


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('pure environment control refuses ' + event)


sys.addaudithook(deny)
ENTRY = Path(__file__).with_name('linux_pair_entry_v1.py')
tree = ast.parse(ENTRY.read_bytes())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'ambient_check')
context = {'pathlib': __import__('pathlib')}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(ENTRY), 'exec'), context)
check = context['ambient_check']
CONFIG = '/data1/yanruj/probata-verifiers/home/.why3.conf'
SOURCE = '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project'


def observe(environment):
    return check(environment, CONFIG, SOURCE)


class LinuxEnvironmentTests(unittest.TestCase):
    def test_empty_environment_admits_no_override(self):
        self.assertEqual(observe({}), [])

    def test_exact_admitted_why3_path_is_accepted(self):
        self.assertEqual(observe({'WHY3CONFIG': CONFIG, 'SWDB_WHY3_CONFIG': CONFIG}), [])

    def test_wrong_why3_path_refuses(self):
        with self.assertRaises(ValueError): observe({'WHY3CONFIG': '/tmp/other.conf'})

    def test_exact_selected_source_pythonpath_is_accepted(self):
        self.assertEqual(observe({'PYTHONPATH': SOURCE}), [])

    def test_other_or_extra_pythonpath_refuses(self):
        for value in ('/tmp/unbound', SOURCE + ':/tmp/unbound'):
            with self.subTest(value=value), self.assertRaises(ValueError): observe({'PYTHONPATH': value})

    def test_python_assertion_and_import_overrides_refuse_before_child(self):
        for name in ('PYTHONOPTIMIZE', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE'):
            with self.subTest(name=name), self.assertRaises(ValueError): observe({name: '1'})

    def test_compiler_pytest_and_ocaml_overrides_refuse(self):
        for name in ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'OBJC_INCLUDE_PATH', 'INCLUDE',
                     'SDKROOT', 'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'OCAMLPATH'):
            with self.subTest(name=name), self.assertRaises(ValueError): observe({name: 'override'})

    def test_wp_overrides_keep_refusing(self):
        for name in ('FRAMAC_WP_PROVER', 'WP_HOME', 'SWDB_PROOF_REPORT_OUT'):
            with self.subTest(name=name), self.assertRaises(ValueError): observe({name: 'override'})


if __name__ == '__main__':
    unittest.main()
