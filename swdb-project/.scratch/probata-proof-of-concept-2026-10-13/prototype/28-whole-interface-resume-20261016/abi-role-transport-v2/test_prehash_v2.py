"""No-child standalone resource controls for the ABI helper successor."""
import ast
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent
PRIOR = runpy.run_path(str(HERE / 'test_abi_transport_v1.py'), run_name='v2_source_control_support')
ABI = PRIOR['ABI']


class PrehashControls(unittest.TestCase):
    def function(self, calls):
        def hashed(raw):
            calls.append(len(raw))
            return 'not-a-selected-digest'
        namespace = {**ABI, 'sha': hashed}
        tree = ast.parse((HERE / 'abi_role_transport_v1.py').read_bytes())
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'normalize_abi')
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-normalize-prehash-bound>', 'exec'), namespace)
        return namespace['normalize_abi']

    def test_empty_oversize_and_wrong_type_refuse_before_hash(self):
        for value in (b'', b'x' * (ABI['LIMIT'] + 1), bytearray(b'x'), 'text'):
            calls = []
            with self.assertRaises(ValueError): self.function(calls)(value)
            self.assertEqual(calls, [])

    def test_allowed_extent_hashes_once_before_unknown_family_refusal(self):
        calls = []
        with self.assertRaises(ValueError): self.function(calls)(b'bounded unselected ABI')
        self.assertEqual(calls, [len(b'bounded unselected ABI')])

    def test_complete_two_edit_inverse_and_other_functions_exact(self):
        before = HERE.parent / 'abi-role-transport-v1/abi_role_transport_v1.py'
        after = HERE / 'abi_role_transport_v1.py'
        inverse = json.loads((HERE / 'helper-inverse-v2.json').read_bytes())['replacements']
        text = after.read_text()
        for row in reversed(inverse):
            self.assertEqual(text.count(row['new']), 1)
            text = text.replace(row['new'], row['old'], 1)
        self.assertEqual(text, before.read_text())
        def functions(path):
            return {node.name: ast.dump(node) for node in ast.parse(path.read_bytes()).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        old, new = functions(before), functions(after)
        self.assertEqual({key:value for key,value in old.items() if key != 'normalize_abi'},
                         {key:value for key,value in new.items() if key != 'normalize_abi'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
