"""2026-10-16 ET. Pure absolute-command admission controls; no compiler."""
import ast
import copy
import hashlib
import pathlib
import shlex
import sys
import tempfile
import types
import unittest


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('child execution prohibited')

sys.addaudithook(deny)
HERE = pathlib.Path(__file__).resolve().parent
TREE = ast.parse((HERE / 'linux_pair_entry_v2.py').read_text())
NODES = [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name in {'pin', 'compiler_preflight'}]


class CompilerCommand(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='t28-compiler-metadata-only-')
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name).resolve()
        self.wrapper = self.root / 'wrapper'
        self.driver = self.root / 'driver'
        self.wrapper.write_text('inert wrapper bytes; never execute')
        self.driver.write_text('inert driver bytes; never execute')
        self.namespace = {'pathlib': pathlib, 'hashlib': hashlib, 'shlex': shlex,
                          'shutil': types.SimpleNamespace(which=lambda command: str(self.wrapper))}
        exec(compile(ast.Module(body=NODES, type_ignores=[]), '<compiler-preflight-ast>', 'exec'), self.namespace)
        pin = self.namespace['pin']
        self.wanted = {'command': [str(self.wrapper)], 'command_executable': pin(self.wrapper), 'driver': pin(self.driver)}
        self.check = self.namespace['compiler_preflight']

    def test_absolute_command(self):
        observed = self.check({}, self.wanted)
        self.assertEqual(observed['command'], [str(self.wrapper)])
        self.assertEqual(self.check({'SWDB_CLANG': shlex.join([str(self.wrapper)])}, self.wanted), observed)

    def test_relative_and_multiple_tokens(self):
        for command in [['clang++'], [str(self.wrapper), '-fno-exceptions'], [], [3]]:
            changed = copy.deepcopy(self.wanted); changed['command'] = command
            with self.subTest(command=command):
                with self.assertRaises(ValueError): self.check({}, changed)

    def test_ambient_and_physical_changes(self):
        for ambient in ['clang++', str(self.driver), str(self.wrapper) + ' -bad', "'unterminated"]:
            with self.subTest(ambient=ambient):
                with self.assertRaises(ValueError): self.check({'SWDB_CLANG': ambient}, self.wanted)
        self.wrapper.write_text('changed wrapper bytes')
        with self.assertRaises(ValueError): self.check({}, self.wanted)


if __name__ == '__main__': unittest.main()
