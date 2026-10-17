"""2026-10-16 ET. Tiny source/no-child controls; never invoke actual cold audit."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure cold composition controls refuse ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('cold_composition_source_only', HERE / 'initialized_cold_audit_v1.py')
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


def pin(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def record_rows():
    return [{'expected_result': value, 'record': {'path': '/synthetic/record-' + str(value) + '.yaml',
            'bytes': 0, 'sha256': '0' * 64}, 'id': 'synthetic-' + str(value)} for value in (711, 1107)]


class CompositionControls(unittest.TestCase):
    def test_strict_json_duplicate_and_nonfinite(self):
        self.assertEqual(reader.strict_json('{"value":1}'), {'value': 1})
        for text in ('{"value":1,"value":2}', '{"value":NaN}', '{"value":Infinity}'):
            with self.assertRaises((AssertionError, ValueError)): reader.strict_json(text)

    def test_stream_pin_stability_type_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / 'inert'
            path.write_bytes(b'inert source'); physical = reader.Physical()
            self.assertEqual(physical.pinned(pin(path)), pin(path)['sha256'])
            physical.unchanged()
            before = pin(path); path.write_bytes(b'changed')
            with self.assertRaises(AssertionError): physical.pinned(before)
            with self.assertRaises(AssertionError): physical.unchanged()
            path.unlink(); path.symlink_to('missing')
            with self.assertRaises(AssertionError): reader.Physical().pin(path)
            fake = dict(before, bytes=True)
            with self.assertRaises(AssertionError): reader.Physical().pinned(fake)

    def test_raw_complete_membership_and_literal_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / 'file'; path.write_bytes(b'inert')
            (root / 'alias').symlink_to('file')
            snapshot = reader.raw_snapshot(root, reader.Physical())
            self.assertEqual(snapshot['symlinks'], {'alias': {'target': 'file'}})
            self.assertEqual(set(snapshot['files']), {'file'})
            (root / 'added').write_bytes(b'new')
            self.assertNotEqual(reader.raw_snapshot(root, reader.Physical()), snapshot)
            os.mkfifo(root / 'special')
            with self.assertRaises(AssertionError): reader.raw_snapshot(root, reader.Physical())

    def test_explicit_711_1107_labels_no_verdict_inference(self):
        rows = record_rows(); self.assertEqual(reader.validate_record_selection(rows), rows)
        mutations = [lambda x: x.reverse(), lambda x: x[0].update(expected_result=True),
                     lambda x: x[1].update(expected_result=711), lambda x: x[1].update(id=x[0]['id']),
                     lambda x: x[1]['record'].update(path=x[0]['record']['path']),
                     lambda x: x[0]['record'].update(bytes=True)]
        for mutate in mutations:
            changed = copy.deepcopy(rows); mutate(changed)
            with self.assertRaises(AssertionError): reader.validate_record_selection(changed)

    def test_complete_consumer_membership_no_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); (root / 'source').mkdir(); (root / 'source/a').write_bytes(b'a')
            expected = {'source_consumer_trees': {'source': {'oid': '0' * 40}}}
            self.assertEqual(reader.source_membership(root, expected), {'source/a'})
            (root / 'source/b').write_bytes(b'b')
            self.assertEqual(reader.source_membership(root, expected), {'source/a', 'source/b'})
            (root / 'source/alias').symlink_to('a')
            with self.assertRaises(AssertionError): reader.source_membership(root, expected)

    def test_exact_pure_runtime_ast_no_entry_execution(self):
        source = (HERE / 'linux_pair_entry_v4.py').read_text()
        # The entry top-level would execute tools if imported. AST selection
        # returns only the exact two reviewed pure definitions.
        helpers = reader.pure_runtime_helpers(source + '\nraise RuntimeError("never execute entry")\n', reader.Physical())
        self.assertTrue(callable(helpers['import_surface']))
        changed = source.replace("def import_surface(root,wanted):", "def import_surface(root,wanted):\n raise RuntimeError('injected')")
        with self.assertRaises(AssertionError): reader.pure_runtime_helpers(changed, reader.Physical())

    def test_workflow_exact_two_no_skip_junit(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve(); profile = raw / 'initialized-profile'; profile.mkdir()
            expected = {'startup_roles': {'source_project': '/selected/source'}}
            (raw / 'initialized-collection.json').write_text(json.dumps({'cwd': '/selected/source', 'expected': reader.SELECTION,
                'selected': reader.SELECTION, 'exit_code': 0}))
            (raw / 'initialized-runner-exit-code.txt').write_text('0\n')
            for name, text in {'selected-tests.txt': '\n'.join(reader.SELECTION) + '\n', 'profile.txt': 'pair\n',
                'exit-code.txt': '0\n', 'source-commit.txt': reader.SOURCE_COMMIT + '\n', 'junit-census.json': '{"accepted":true}'}.items():
                (profile / name).write_text(text)
            cases = ''.join('<testcase classname="tests.test_dx100_initialized_register_actual" name="' + node.split('::')[-1] + '"/>' for node in reader.SELECTION)
            text = '<testsuites><testsuite tests="2" errors="0" failures="0" skipped="0">' + cases + '</testsuite></testsuites>'
            (profile / 'junit.xml').write_text(text)
            self.assertEqual(reader.workflow(expected, raw)['tests'], 2)
            for changed in (text.replace('skipped="0"', 'skipped="1"'), text.replace('/>', '><skipped/></testcase>', 1),
                            text.replace('tests="2"', 'tests="1"')):
                (profile / 'junit.xml').write_text(changed)
                with self.assertRaises(AssertionError): reader.workflow(expected, raw)

    def test_reviewed_module_hashes_and_no_project_or_yaml_top_import(self):
        trace = HERE.parent / '28-public-memory-trace-resume-20261016'
        for name, digest in reader.MODULE_PINS.items():
            path = HERE / name if (HERE / name).exists() else trace / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        tree = ast.parse((HERE / 'initialized_cold_audit_v1.py').read_text())
        for node in tree.body:
            if isinstance(node, ast.Import): self.assertFalse(any(alias.name == 'yaml' or alias.name.startswith('swdb') for alias in node.names))
            if isinstance(node, ast.ImportFrom): self.assertFalse((node.module or '').startswith(('yaml', 'swdb')))
        audit = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'audit')
        calls = [node.func.attr for node in ast.walk(audit) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertNotIn('run', calls); self.assertNotIn('check_output', calls)
        self.assertNotIn('popen', calls)
        self.assertIn('verify_python_metadata', calls)


if __name__ == '__main__': unittest.main(verbosity=2)
