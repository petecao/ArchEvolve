"""2026-10-16 ET. Real read-only Git metadata from the nested project cwd."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
API = runpy.run_path(str(HERE / 'materialize.py'))
ORIGINAL_GIT = subprocess.check_output
CALLS = []


def git_metadata(argv, **kwargs):
    if not (isinstance(argv, list) and argv[0] == 'git' and '-C' in argv):
        raise AssertionError('only exact read-only Git metadata commands are permitted')
    index = argv.index('-C') + 2
    command = argv[index:]
    if not (command == ['rev-parse', 'HEAD'] or command[0] == 'ls-tree'
            or (command[0] == 'show' and len(command) == 2 and ':swdb-project/' in command[1])):
        raise AssertionError('unexpected Git metadata operation')
    CALLS.append(list(argv))
    return ORIGINAL_GIT(argv, **kwargs)


class MaterializerGitControl(unittest.TestCase):
    def test_nested_selection_equals_the_root_tree_and_materializes_all_declared_consumers(self):
        commit = git_metadata(['git', '-C', str(PROJECT), 'rev-parse', 'HEAD']).decode().strip()
        roots = ['swdb-project/' + name for name in ('swdb', 'schemas', 'vocab')]
        explicit = ['tests/testkit/standard_library.py', 'tests/conftest.py',
            'tests/fixtures/proof/lowering/vector_owned_transfer.cc',
            'tests/fixtures/proof/methods/contract-fixture-1.yaml', 'library/methods/probata-draft-1.yaml']
        expected = git_metadata(['git', '-C', str(PROJECT.parent), 'ls-tree', '-r', '-z', '--name-only',
            commit, '--', *roots, *['swdb-project/' + name for name in explicit]]).decode().split('\0')
        expected = sorted(name.removeprefix('swdb-project/') for name in expected if name)
        self.assertGreater(len(expected), 100)
        with tempfile.TemporaryDirectory(prefix='probata-move-git-selection-', dir='/private/tmp') as raw:
            temporary = Path(raw)
            for name in ('entry-template.py', 'test_controls.py', 'README.md'):
                (temporary / name).write_bytes((HERE / name).read_bytes())
            output = temporary / 'fresh-observation-output'
            with patch.dict(API['main'].__globals__, {'HERE': temporary}), \
                    patch.object(subprocess, 'check_output', side_effect=git_metadata), \
                    patch.object(sys, 'argv', ['materialize.py', '--source-commit', commit,
                                              '--output', str(output)]), redirect_stdout(io.StringIO()):
                API['main']()
            packet = json.loads((temporary / ('source-packet-' + commit[:8] + '.json')).read_bytes())
            rows = packet['source_pins']
            self.assertEqual([row['relative'] for row in rows], expected)
            self.assertTrue(set(explicit) <= {row['relative'] for row in rows})
            for row in rows:
                raw = (PROJECT / row['relative']).read_bytes()
                self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row['bytes'], row['sha256']))
            self.assertFalse(output.exists())
            self.assertTrue(packet['full_template_inverse_exact'])
            self.assertFalse(packet['actual_execution'])
            nested = [argv for argv in CALLS if argv[argv.index('-C') + 1] == str(PROJECT)
                      and argv[argv.index('-C') + 2] == 'ls-tree']
            self.assertEqual(len(nested), 1)
            self.assertIn('--full-tree', nested[0])


if __name__ == '__main__':
    unittest.main()
