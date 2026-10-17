"""2026-10-16 ET. Independent source/stdlib controls; no retained ABI replay.

The 29-root ABI stream below is deliberately synthetic. It checks the real
transport and unchanged literal-value reader without claiming captured-source
eligibility or joining its declaration IDs to a source translation unit.
"""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V1 = WHOLE / 'abi-role-transport-v1'
V2 = WHOLE / 'abi-role-transport-v2'
NORMAL = WHOLE / 'role-normalized-gzip-v2/role_normalized_gzip_v2.py'
TOKEN = WHOLE / 'streaming-minify-v1/strict_minify_v2.py'
LEGACY = WHOLE / 'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py'
PROBE = WHOLE / 'compiler_abi_probe_v1.cpp'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('independent ABI controls forbid child/native/network')


sys.addaudithook(audit)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(path):
    result = types.ModuleType('independent_pinned_primitive')
    result.__dict__.update(runpy.run_path(str(path), run_name='independent_pinned_primitive'))
    return result


def isolated_source(path, **injected):
    """Execute exact source nodes, excluding only project imports."""
    tree = ast.parse(path.read_bytes(), filename=str(path))
    tree.body = [node for node in tree.body if not
        (isinstance(node, ast.ImportFrom) and (node.module or '').startswith('swdb'))]
    namespace = {'__name__': 'independent_closed_source', '__file__': str(path), **injected}
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace


def helper(version=V2, normal=NORMAL, token=TOKEN):
    return isolated_source(version / 'abi_role_transport_v1.py', normalizer=module(normal), tokens=module(token))


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def inverse(text, rows):
    for row in reversed(rows):
        if text.count(row['new']) != 1:
            raise AssertionError('inverse replacement not unique')
        text = text.replace(row['new'], row['old'], 1)
    return text


def paired(index, kind='UsingType'):
    decl = 'UsingShadowDecl' if kind == 'UsingType' else 'TypedefDecl'
    return ('{"id":"0x%x","kind":"%s","type":{"qualType":"std::uint32_t"},'
        '"decl":{"id":"0x%x","kind":"%s","name":"uint32_t"},'
        '"type":{"qualType":"unsigned int"},"inner":[]}') % (index + 1, kind, index + 33, decl)


def synthetic_abi(probe):
    legacy = runpy.run_path(str(LEGACY), run_name='independent_literal_ABI_reader')
    names = legacy['TYPE_KEYS']
    values = ('unsigned int', 'int', 'float', 'unsigned long', 'long', 'double')
    roots = []
    for index, (name, value) in enumerate(zip(names, values)):
        root = {'id': '0x1', 'kind': 'TypeAliasDecl', 'name': 'dws_probe_' + name,
            'loc': {'file': str(probe), 'offset': index}, 'type': {'qualType': value},
            'note': 'whitespace, escaped quote: " and unicode spelling retained'}
        prefix = json.dumps(root, separators=(',', ':'), ensure_ascii=True)[:-1]
        roots.append(prefix + (',"inner":[' + paired(index, 'UsingType' if index % 2 else 'TypedefType') + ']}'
            if index < 4 else '}'))
    numbers = dict(char_bit=8, int_bits=32, pointer_bits=64, little_endian=1,
        float_radix=2, float_mantissa=24, double_mantissa=53,
        source_cores=4, source_tiles=32, source_registers=32, source_tile_words=16384)
    for name, size in zip(names, (4, 4, 4, 8, 8, 8)):
        numbers['size_' + name] = numbers['align_' + name] = size
    for index, name in enumerate(legacy['ABI_INTS']):
        roots.append(json.dumps({'id': '0x1', 'kind': 'EnumConstantDecl', 'name': 'dws_probe_' + name,
            'loc': {'file': str(probe), 'offset': index + 10},
            'inner': [{'kind': 'ConstantExpr', 'value': str(numbers[name])}]}, separators=(',', ':')))
    return (' \r\n' + '\n \t'.join(roots) + '\t\n').encode('ascii')


def select_synthetic(namespace, raw):
    # This is an explicit test-local replacement; the selected source files and
    # their two immutable actual artifact selectors remain untouched.
    namespace['FAMILIES'] = {'independent-synthetic-control': (len(raw), sha(raw))}


class IndependentABIControls(unittest.TestCase):
    def test_frozen_packet_and_predecessor_pins(self):
        checked = []
        def walk(item):
            if isinstance(item, dict):
                if {'path', 'bytes', 'sha256'} <= set(item):
                    self.assertEqual(pin(Path(item['path'])), {key: item[key] for key in ('path', 'bytes', 'sha256')})
                    checked.append(item['path'])
                for value in item.values(): walk(value)
            elif isinstance(item, list):
                for value in item: walk(value)
        self.assertEqual(sha((V2 / 'source-packet-v2.json').read_bytes()), 'dc34b92c47111545777e7268df1f2f471889678b298fe1705d1308dc3f170b15')
        for path in (V2 / 'source-packet-v2.json', V1 / 'source-packet-v1.json', V2 / 'adapter-inverse-v1.json'):
            walk(json.loads(path.read_bytes()))
        self.assertGreaterEqual(len(checked), 20)

    def test_exact_helper_and_adapter_inverses(self):
        original = (V1 / 'abi_role_transport_v1.py').read_text()
        current = (V2 / 'abi_role_transport_v1.py').read_text()
        rows = json.loads((V2 / 'helper-inverse-v2.json').read_bytes())['replacements']
        self.assertEqual(len(rows), 2)
        self.assertEqual(inverse(current, rows), original)
        inv = json.loads((V2 / 'adapter-inverse-v1.json').read_bytes())
        self.assertEqual(len(inv['replacements']), 4)
        self.assertEqual(inverse((V2 / 'normalized_compiler_adapter_v2.py').read_text(), inv['replacements']), Path(inv['basis']['path']).read_text())
        self.assertEqual((V2 / 'normalized_compiler_adapter_v2.py').read_bytes(), (V1 / 'normalized_compiler_adapter_v2.py').read_bytes())
        self.assertEqual(sha(LEGACY.read_bytes()), '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')

    def test_two_real_physical_locations_red_v1_green_v2(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temporary:
            root = Path(temporary).resolve()
            locations = []
            for label in ('observer-control', 'normal-producer'):
                location = root / label
                location.mkdir()
                for source in (NORMAL, TOKEN): (location / source.name).write_bytes(source.read_bytes())
                locations.append(location)
            raw = synthetic_abi(PROBE.resolve())
            old, new = [], []
            for location in locations:
                for version, results in ((V1, old), (V2, new)):
                    ns = helper(version, location / NORMAL.name, location / TOKEN.name)
                    select_synthetic(ns, raw)
                    results.append(ns['normalize_abi'](raw))
            self.assertEqual(old[0][0], old[1][0])
            self.assertNotEqual(old[0][1], old[1][1])
            stripped = copy.deepcopy([row[1] for row in old])
            for receipt in stripped:
                for item in receipt['primitive_sources']: item.pop('path')
            self.assertEqual(*stripped)
            self.assertEqual(*new)
            self.assertEqual([item['role'] for item in new[0][1]['primitive_sources']], ['paired-type-normalizer', 'strict-token-grammar'])
            self.assertEqual([pin(location / NORMAL.name)['sha256'] for location in locations], [new[0][1]['primitive_sources'][0]['sha256']] * 2)

    def test_real_transport_to_unchanged_ABI_value_domain(self):
        ns = helper()
        raw = synthetic_abi(PROBE.resolve())
        select_synthetic(ns, raw)
        derived, receipt = ns['normalize_abi'](raw)
        legacy = runpy.run_path(str(LEGACY), run_name='independent_real_ABI_reader')
        binder = runpy.run_path(str(WHOLE / 'whole_interface_v4.py'), run_name='independent_literal_ABI_domain')
        with self.assertRaises(legacy['Refused']): legacy['parse_json_roots'](raw)
        observed = legacy['observed_abi'](derived, probe_path=PROBE.resolve(), api=binder)
        self.assertEqual(observed['root_count'], 29)
        self.assertEqual(observed['raw_probe_sha256'], receipt['derived_strict_sha256'])
        self.assertNotEqual(receipt['original_sha256'], observed['raw_probe_sha256'])
        self.assertEqual(receipt['original_sha256'], sha(raw))
        self.assertEqual(receipt['normalization']['original_minified_token_sha256'], receipt['inverse']['original_minified_token_sha256'])
        self.assertEqual(receipt['role_renames'], 4)
        before = [json.loads(row, object_pairs_hook=ns['Pairs']) for row in ns['roots'](raw, strict=False)]
        after = legacy['parse_json_roots'](derived)
        self.assertEqual([dict(row)['name'] for row in before], [row['name'] for row in after])
        self.assertEqual([row['id'] for row in after], ['0x1'] * 29)
        self.assertFalse(receipt['source_call_IDs_joined'])
        self.assertFalse(receipt['source_ABI_or_public_admission'])
        self.assertFalse(observed['public_admission'])
        bad = derived.replace(b'"value":"16384"', b'"value":"16383"')
        with self.assertRaises(legacy['Refused']): legacy['observed_abi'](bad, probe_path=PROBE.resolve(), api=binder)

    def test_ordered_tokens_and_unknown_roles_refuse(self):
        ns = helper()
        selected = paired(0)
        invalid = [selected.replace('UsingType', 'UnknownType'), selected.replace('UsingShadowDecl', 'TypedefDecl'),
            selected.replace('"id":"0x1","kind"', '"name":"x","kind"'),
            selected.replace('"type":{"qualType":"unsigned int"}', '"type":{"qualType":"unsigned int"},"extra":true'),
            selected.replace('"inner":[]', '"inner":[],"swdbClangDesugaredType":{}'),
            selected.replace('"type":{"qualType":"unsigned int"}', '"type":{}'),
            '{"x":0,"x":1}', '{"x":NaN}', '{"x":Infinity}', '{"x":1,}', '{"x":"unterminated}']
        for row in invalid:
            with self.subTest(digest=sha(row.encode())), self.assertRaises(ValueError):
                ns['_transport'](row.encode(), expected_roots=1, expected_renames=1)
        for args in ((2, 1), (1, 0), (1, 2)):
            with self.assertRaises(ValueError): ns['_transport'](selected.encode(), expected_roots=args[0], expected_renames=args[1])
        for value in (b'[]', b'{} ' * 30, b'{"x":"\xff"}', b'', b'{}\0'):
            with self.assertRaises(ValueError): ns['_transport'](value, expected_roots=1, expected_renames=0)

    def test_selected_artifacts_remain_closed_and_pre_hash_bounded(self):
        ns = helper()
        self.assertEqual(ns['FAMILIES'], {'first-source-v10': (127394, '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'),
            'three-memory-g642': (127541, '493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c')})
        calls = []
        original_sha = ns['sha']
        def counted(raw): calls.append(len(raw)); return original_sha(raw)
        ns['sha'] = counted
        for value in (None, 'str', bytearray(b'x'), b'', b'x' * (ns['LIMIT'] + 1)):
            with self.assertRaises(ns['Refused']): ns['normalize_abi'](value)
            self.assertEqual(calls, [])
        with self.assertRaises(ns['Refused']): ns['normalize_abi'](b'explicit bounded unknown ABI')
        self.assertEqual(calls, [len(b'explicit bounded unknown ABI')])

    def test_actual_primitive_regular_canonical_source_is_still_required(self):
        ns = helper()
        with tempfile.TemporaryDirectory(dir=HERE) as temporary:
            root = Path(temporary).resolve()
            physical = root / 'normal.py'
            physical.write_bytes(NORMAL.read_bytes())
            selected = module(physical)
            self.assertEqual(ns['primitive'](selected, ns['NORMALIZER_SHA'])['path'], str(physical))
            link = root / 'link.py'
            link.symlink_to(physical)
            with self.assertRaises(ns['Refused']): ns['primitive'](types.SimpleNamespace(__file__=str(link)), ns['NORMALIZER_SHA'])
            physical.write_bytes(physical.read_bytes() + b'\n')
            with self.assertRaises(ns['Refused']): ns['primitive'](selected, ns['NORMALIZER_SHA'])

    def test_real_adapter_first_family_and_actual_derived_inlet(self):
        full = b'explicit unavailable actual full-TU control object'
        original, derived = b'original ABI control', b'derived ABI control'
        called = []
        receipt = {'selected_family': 'first-source-v10', 'original_sha256': sha(original), 'derived_strict_sha256': sha(derived)}
        actual_probe_digest = [sha(derived)]
        def prepare(api, **args):
            called.append(args)
            return {'schema': 'whole-interface-original-tu-preparation-1', 'raw_full_tu_sha256': ns['EXPANDED_SHA'],
                'public_admission': False, 'abi_observation': {'raw_probe_sha256': actual_probe_digest[0]}}
        ns = isolated_source(V2 / 'normalized_compiler_adapter_v2.py',
            legacy=types.SimpleNamespace(__file__=str(LEGACY), prepare_unit=prepare),
            abi_transport=types.SimpleNamespace(normalize_abi=lambda raw: (derived, receipt)))
        real_len = len
        ns['len'] = lambda raw: ns['EXPANDED_BYTES'] if raw is full else real_len(raw)
        ns['hashlib'] = types.SimpleNamespace(sha256=lambda raw: types.SimpleNamespace(hexdigest=lambda: ns['EXPANDED_SHA']) if raw is full else hashlib.sha256(raw))
        request = dict(transport_kind=ns['KIND'], full_tu_raw=full, abi_raw=original,
            source_path=Path('/explicit-unavailable-source'), source_bytes=b'source',
            probe_path=Path('/explicit-unavailable-probe'), probe_bytes=b'probe', declarations=[],
            compiler_capture_pin='a' * 64, full_tu_compressed_bytes=ns['COMPRESSED_BYTES'],
            full_tu_expanded_limit=ns['EFFECTIVE_LIMIT'])
        result = ns['prepare_unit']({}, **request)
        self.assertEqual(len(called), 1)
        self.assertIs(called[0]['full_tu_raw'], full)
        self.assertIs(called[0]['abi_raw'], derived)
        self.assertEqual(called[0]['full_tu_expanded_limit'], ns['LEGACY_CEILING'])
        self.assertEqual(result['abi_observation']['raw_probe_sha256'], sha(derived))
        self.assertEqual(result['abi_observation']['original_raw_probe_sha256'], sha(original))
        self.assertEqual(result['abi_observation']['paired_type_role_transport'], receipt)
        receipt['selected_family'] = 'three-memory-g642'
        with self.assertRaises(ValueError): ns['prepare_unit']({}, **request)
        self.assertEqual(len(called), 1)
        receipt['selected_family'] = 'first-source-v10'
        actual_probe_digest[0] = sha(original)
        with self.assertRaises(ValueError): ns['prepare_unit']({}, **request)

    def test_no_child_native_network_or_project_imports(self):
        self.assertEqual(EVENTS, [])
        self.assertNotIn('swdb', sys.modules)


if __name__ == '__main__':
    unittest.main(verbosity=2)
