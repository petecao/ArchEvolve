"""2026-10-16 ET. Pure observer source/read/registration controls, no actual TU."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise AssertionError('pure observer controls forbid child/native/network')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('pure controls forbid project imports')


sys.addaudithook(deny)
ENTRY = runpy.run_path(str(HERE / 'observe_entry_v1.py'))


def function(path, name):
    text = path.read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)
    return ast.get_source_segment(text, node), node


class ObserverControls(unittest.TestCase):
    def test_entire_ingress_function_exact_inverse_and_public_unchanged(self):
        inverse = json.loads((HERE / 'observer-inverse-v1.json').read_bytes())
        old, _ = function(WHOLE / 'normalized-ingress-v2/proposed/normalized_capture_ingress_v2.py', 'complete_capture')
        new, _ = function(HERE / 'modules/normalized_unit_observation_v1.py', 'observe_capture')
        self.assertEqual(inverse['original_complete_capture'], old)
        self.assertEqual(inverse['observation_capture'], new)
        for edit in inverse['restoration_edits']:
            self.assertEqual(new.count(edit['old']), 1)
            new = new.replace(edit['old'], edit['new'], 1)
        self.assertEqual(new, old)
        self.assertIn("prepared==reads.document(selected['prepared'])", old)

    def test_exact_comparison_seam_red_green_no_fabricated_preparation(self):
        old, _ = function(WHOLE / 'normalized-ingress-v2/proposed/normalized_capture_ingress_v2.py', 'complete_capture')
        new, _ = function(HERE / 'modules/normalized_unit_observation_v1.py', 'observe_capture')
        def comparison(text):
            calls = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == 'need'
                     and node.args and isinstance(node.args[0], ast.BoolOp)
                     and "prepared['raw_full_tu_sha256']" in ast.unparse(node.args[0])]
            if not calls:
                calls = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Name) and node.func.id == 'need'
                         and node.args and isinstance(node.args[0], ast.Compare)
                         and "prepared['raw_full_tu_sha256']" in ast.unparse(node.args[0])]
            self.assertEqual(len(calls), 1)
            return compile(ast.Expression(calls[0]), 'exact-comparison-seam', 'eval')
        calls = []
        def absent(value):
            calls.append(value); raise ValueError('preparation artifact does not exist yet')
        ns = {'need': ENTRY['need'], 'reads': SimpleNamespace(document=absent), 'selected': {'prepared': None},
              'prepared': {'raw_full_tu_sha256': 'n' * 64}, 'NORMALIZED_SHA': 'n' * 64}
        with self.assertRaises(ValueError): eval(comparison(old), ns)
        self.assertEqual(calls, [None]); calls.clear()
        eval(comparison(new), ns); self.assertEqual(calls, [])
        ns['prepared']['raw_full_tu_sha256'] = 'changed'
        with self.assertRaises(ValueError): eval(comparison(new), ns)

    def test_fixed_modules_and_bridge_nodes_are_exact(self):
        raw = (HERE / 'fixed-modules-v1.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ENTRY['MANIFEST_SHA'])
        rows = json.loads(raw)['modules']
        self.assertEqual(tuple(row['module'] for row in rows), ENTRY['MODULE_NAMES'])
        self.assertEqual(len({row['file'] for row in rows}), len(rows))
        for row in rows:
            path = HERE / 'modules' / row['file']; data = path.read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (row['bytes'], row['sha256']))
            if 'exact_nodes' not in row and path.name != 'normalized_unit_observation_v1.py':
                self.assertEqual(data, Path(row['origin']).read_bytes())
        bridge = next(row for row in rows if 'exact_nodes' in row)
        for name in bridge['exact_nodes']:
            expected, _ = function(Path(bridge['origin']), name)
            actual, _ = function(HERE / 'modules' / bridge['file'], name)
            self.assertEqual(actual, expected)
        self.assertLess(sum(row['bytes'] for row in rows), ENTRY['MAX_CONTROL_BYTES'])

    def test_registration_uses_checked_bytes_and_never_searches_project_paths(self):
        # Only literal assignment bodies execute in isolated fake sys.modules.
        # No actual staged project module is imported by this control.
        ns = dict(ENTRY); fake_sys = SimpleNamespace(modules={}); ns['sys'] = fake_sys
        _text, node = function(HERE / 'observe_entry_v1.py', 'install_fixed')
        exec(compile(ast.Module([node], type_ignores=[]), 'fixed-loader-control', 'exec'), ns)
        rows = json.loads((HERE / 'fixed-modules-v1.json').read_bytes())['modules']
        values = {row['file']: ('ordinal=' + str(index)).encode() for index, row in enumerate(rows)}
        package, private = ns['install_fixed'](values, rows, Path('/fixed/control'), Path('/original/swdb-project'))
        self.assertEqual(package.__path__, []); self.assertEqual(private.__path__, [])
        self.assertEqual(package.paths.HOME, Path('/original/swdb-project'))
        for index, row in enumerate(rows):
            self.assertEqual(fake_sys.modules[row['module']].ordinal, index)
            self.assertEqual(fake_sys.modules[row['module']].__file__, '/fixed/control/' + row['file'])
        with self.assertRaises(ValueError):
            ns['install_fixed'](values, rows, Path('/fixed/control'), Path('/original/swdb-project'))

    def test_stable_metadata_ignores_atime_and_refuses_each_stable_change(self):
        first = {name: index for index, name in enumerate(ENTRY['STABLE'])}
        first['st_atime_ns'] = 1; second = {**first, 'st_atime_ns': 9}
        self.assertEqual(ENTRY['fingerprint'](SimpleNamespace(**first)), ENTRY['fingerprint'](SimpleNamespace(**second)))
        for name in ENTRY['STABLE']:
            changed = {**first, name: first[name] + 1}
            self.assertNotEqual(ENTRY['fingerprint'](SimpleNamespace(**first)), ENTRY['fingerprint'](SimpleNamespace(**changed)))

    def test_physical_reader_rejects_alias_change_and_extra_pin_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / 'input.json'; path.write_bytes(b'{}')
            pin = {'path': str(path), 'bytes': 2, 'sha256': hashlib.sha256(b'{}').hexdigest()}
            self.assertEqual(ENTRY['read_pin'](pin), b'{}')
            alias = root / 'alias'; alias.symlink_to(path)
            for changed in ({**pin, 'path': str(alias)}, {**pin, 'bytes': True}, {**pin, 'extra': True}):
                with self.assertRaises(ValueError): ENTRY['read_pin'](changed)
            path.write_bytes(b'[]')
            with self.assertRaises(ValueError): ENTRY['read_pin'](pin)

    def test_errors_are_bounded_frames_without_payload_or_locals(self):
        secret = 'scientific payload should not be copied'
        try: raise AssertionError(secret)
        except AssertionError as error: value = ENTRY['error_frames'](error)
        self.assertEqual(set(value), {'type', 'frames'})
        self.assertEqual(value['type'], 'AssertionError'); self.assertTrue(value['frames'])
        self.assertNotIn(secret, json.dumps(value))
        self.assertTrue(all(set(row) == {'filename', 'function', 'line'} for row in value['frames']))

    def test_strict_json_and_nonadmitting_output_source(self):
        for raw in (b'{"a":1,"a":2}', b'{"n":NaN}', b'{"n":Infinity}'):
            with self.assertRaises(ValueError): ENTRY['parse'](raw)
        text = (HERE / 'observe_entry_v1.py').read_text()
        self.assertIn("'public_admission': False", text)
        self.assertIn("'owned_context_emitted': False", text)
        self.assertNotIn('subprocess.run', text)
        self.assertIn("write_new(output / 'whole-unit-preparation.json'", text)
        self.assertIn("'observation_complete'] = False", text)


if __name__ == '__main__': unittest.main(verbosity=2)
