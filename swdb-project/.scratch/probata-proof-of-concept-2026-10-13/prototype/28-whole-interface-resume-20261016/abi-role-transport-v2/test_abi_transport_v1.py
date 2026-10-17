"""No-child transport controls; synthetic roots grant no actual ABI result."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('no child/native/network in ABI controls')


sys.addaudithook(audit)


def module(path):
    namespace = runpy.run_path(str(path), run_name='fixed_ABI_primitive_control')
    result = types.ModuleType(path.stem)
    result.__dict__.update(namespace)
    return result


normalizer = module(WHOLE / 'role-normalized-gzip-v2/role_normalized_gzip_v2.py')
tokens = module(WHOLE / 'streaming-minify-v1/strict_minify_v2.py')
package = types.ModuleType('swdb._dx100_whole')
package.__path__ = []
package.role_normalized_gzip_v2 = normalizer
package.strict_minify_v2 = tokens
parent = types.ModuleType('swdb')
parent.__path__ = []
parent._dx100_whole = package
sys.modules['swdb'] = parent
sys.modules['swdb._dx100_whole'] = package
ABI = runpy.run_path(str(HERE / 'abi_role_transport_v1.py'), run_name='fixed_ABI_transport_control')


def root(index):
    return ('{"kind":"TypeAliasDecl","name":"dws_probe_control_%d","type":{"qualType":"unsigned int"},'
        '"inner":[{"id":"0x%x","kind":"UsingType","type":{"qualType":"std::uint32_t"},'
        '"decl":{"id":"0x%x","kind":"UsingShadowDecl","name":"uint32_t"},'
        '"type":{"qualType":"unsigned int"},"inner":[]}]}') % (index, index + 1, index + 17)


def source():
    return (' \n' + root(0) + '\n\t' + root(1) + '\n').encode()


class TransportControls(unittest.TestCase):
    def test_exact_adapter_inverse_leaves_every_legacy_function_unchanged(self):
        inverse = json.loads((HERE / 'adapter-inverse-v1.json').read_bytes())
        source = (HERE / 'normalized_compiler_adapter_v2.py').read_text()
        for row in reversed(inverse['replacements']):
            self.assertEqual(source.count(row['new']), 1)
            source = source.replace(row['new'], row['old'], 1)
        self.assertEqual(source, Path(inverse['basis']['path']).read_text())

    def test_real_adapter_inlet_preserves_full_tu_and_names_both_abi_identities(self):
        # Only unavailable actual TU payload and the downstream preparation are
        # protocol doubles. Execute the real adapter body and its new ABI inlet.
        full = b'explicit unavailable full-TU protocol stand-in'
        original = b'explicit original ABI protocol stand-in'
        derived = b'explicit derived ABI protocol stand-in'
        receipt = {'selected_family': 'first-source-v10', 'original_sha256': hashlib.sha256(original).hexdigest(),
                   'derived_strict_sha256': hashlib.sha256(derived).hexdigest()}
        calls = []
        def prepare(api, **kwargs):
            calls.append(kwargs)
            self.assertIs(kwargs['full_tu_raw'], full)
            self.assertIs(kwargs['abi_raw'], derived)
            return {'schema': 'whole-interface-original-tu-preparation-1',
                'raw_full_tu_sha256': '1f0616302273d146fc88e1c676d25c41230432ee8ec259a92ae65f8fbb5755a3',
                'public_admission': False, 'abi_observation': {'raw_probe_sha256': receipt['derived_strict_sha256']}}
        legacy_path = WHOLE / 'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py'
        legacy = types.SimpleNamespace(__file__=str(legacy_path), prepare_unit=prepare)
        sys.modules['swdb'] = parent
        sys.modules['swdb._dx100_whole'] = package
        package.compiler_unit_adapter_v3 = legacy
        package.abi_role_transport_v1 = types.SimpleNamespace(normalize_abi=lambda raw: (derived, receipt))
        namespace = runpy.run_path(str(HERE / 'normalized_compiler_adapter_v2.py'), run_name='real_ABI_inlet_protocol_control')
        function = next(node for node in ast.parse((HERE / 'normalized_compiler_adapter_v2.py').read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'prepare_unit')
        def selected_hash(raw):
            if raw is full:
                return types.SimpleNamespace(hexdigest=lambda: namespace['EXPANDED_SHA'])
            return hashlib.sha256(raw)
        namespace.update(hashlib=types.SimpleNamespace(sha256=selected_hash),
            len=lambda value: namespace['EXPANDED_BYTES'] if value is full else len(value))
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<exact-adapter-ABI-inlet>', 'exec'), namespace)
        result = namespace['prepare_unit']({}, transport_kind=namespace['KIND'], full_tu_raw=full,
            abi_raw=original, source_path=Path('/explicit/source-standin'), source_bytes=b'source',
            probe_path=Path('/explicit/probe-standin'), probe_bytes=b'probe', declarations=[],
            compiler_capture_pin='a'*64, full_tu_compressed_bytes=namespace['COMPRESSED_BYTES'],
            full_tu_expanded_limit=namespace['EFFECTIVE_LIMIT'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['abi_observation']['original_raw_probe_sha256'], receipt['original_sha256'])
        self.assertEqual(result['abi_observation']['raw_probe_sha256'], receipt['derived_strict_sha256'])
        self.assertEqual(result['abi_observation']['paired_type_role_transport'], receipt)

    def test_exact_primitive_lineage_and_unchanged_generic_decoder(self):
        self.assertEqual(ABI['primitive'](normalizer, ABI['NORMALIZER_SHA'])['sha256'], ABI['NORMALIZER_SHA'])
        self.assertEqual(ABI['primitive'](tokens, ABI['TOKENS_SHA'])['sha256'], ABI['TOKENS_SHA'])
        legacy = WHOLE / 'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py'
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(),
            '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        ns = runpy.run_path(str(legacy), run_name='unchanged_generic_decoder_control')
        with self.assertRaisesRegex(ns['Refused'], 'malformed compiler JSON'):
            ns['parse_json_roots'](source())

    def test_complete_transport_inverse_and_artificial_wrapper_removal(self):
        derived, receipt = ABI['_transport'](source(), expected_roots=2, expected_renames=2)
        self.assertEqual(len(ABI['roots'](derived, strict=True)), 2)
        self.assertEqual(receipt['root_count'], 2)
        self.assertEqual(receipt['role_renames'], 2)
        self.assertEqual(receipt['original_sha256'], hashlib.sha256(source()).hexdigest())
        self.assertFalse(receipt['synthetic_container_is_original_TU'])
        self.assertFalse(receipt['source_call_IDs_joined'])
        self.assertFalse(receipt['source_ABI_or_public_admission'])
        for line in derived.splitlines():
            value = json.loads(line)
            self.assertEqual(value['kind'], 'TypeAliasDecl')
            nested = value['inner'][0]
            self.assertEqual(nested['type'], {'qualType': 'std::uint32_t'})
            self.assertEqual(nested['swdbClangDesugaredType'], {'qualType': 'unsigned int'})
        self.assertEqual(receipt['normalization']['original_minified_token_sha256'],
            receipt['inverse']['original_minified_token_sha256'])

    def test_whitespace_only_identity_preserves_string_and_escape_tokens(self):
        raw = b' { "x" : "a b\\\" c", "y" : "\\u0041", "z" : [ 1, -2 ] } '
        self.assertEqual(ABI['minified_tokens'](raw), b'{"x":"a b\\\" c","y":"\\u0041","z":[1,-2]}')

    def test_unknown_duplicate_kind_order_collision_and_shape_refuse(self):
        selected = root(0)
        mutations = [selected.replace('UsingType', 'UnknownType'),
            selected.replace('"id":"0x1","kind":"UsingType"', '"kind":"UsingType","id":"0x1"'),
            selected.replace('"inner":[]', '"inner":[],"swdbClangDesugaredType":{}'),
            selected.replace('"type":{"qualType":"unsigned int"},"inner":[]', '"type":{},"inner":[]'),
            selected.replace('"decl":', '"unexpected":')]
        for raw in mutations:
            with self.subTest(raw_hash=hashlib.sha256(raw.encode()).hexdigest()), self.assertRaises(ValueError):
                ABI['_transport'](raw.encode(), expected_roots=1, expected_renames=1)
        for raw in (b'{"x":1,"x":2}', b'{"kind":"TypeAliasDecl","x":NaN}', b'{"kind":'):
            with self.assertRaises(ValueError): ABI['_transport'](raw, expected_roots=1, expected_renames=0)

    def test_count_mismatch_and_unknown_original_selection_refuse(self):
        for roots, renames in ((1, 2), (2, 1), (2, 3)):
            with self.assertRaises(ValueError): ABI['_transport'](source(), expected_roots=roots, expected_renames=renames)
        with self.assertRaisesRegex(ABI['Refused'], 'exact retained'):
            ABI['normalize_abi'](source())
        self.assertEqual(ABI['FAMILIES']['first-source-v10'],
            (127394, '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'))
        self.assertEqual(ABI['FAMILIES']['three-memory-g642'],
            (127541, '493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c'))
        self.assertEqual(EVENTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
