"""2026-10-16 ET. Real binding functions on synthetic diagnostic TU metadata.

Pinned original source/header text supplies spans; no actual compiler TU,
source-program execution, C++ compilation, native run or project import occurs.
"""
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
V2 = WHOLE / 'runtime-projection-v2'
SOURCE_PATH = WHOLE / 'source_call_fixture_v2.cpp'


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise AssertionError('child/native/network event forbidden: ' + event)
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('project imports forbidden')


sys.addaudithook(no_child)


def selected_source(path, names):
    source = path.read_text(); tree = ast.parse(source)
    chosen = [node for node in tree.body if
        isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names or
        isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in names for target in node.targets)]
    namespace = {'__name__': 'pure_source_nodes', '__file__': str(path), 'Path': Path,
        'hashlib': hashlib, 'json': json, 're': re}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


API = selected_source(WHOLE / 'whole_interface_v4.py', {'Refused', 'digest', '_need', '_parameters', '_packet',
    'inventory', 'validate_abi', '_type_tokens', 'signature', '_span', 'bind_call', 'recheck_binding',
    'HEADER_PINS', 'TYPE_KEYS', 'PACKET_SLOTS', 'OPCODES', 'MEMORY'})
DECLARATIONS = API['inventory'](PROJECT)
ABI = {'byte_order': 'little', 'int_bits': 32, 'pointer_bits': 64,
    'canonical_types': dict(zip(API['TYPE_KEYS'], ('unsigned int', 'int', 'float', 'unsigned long', 'long', 'double'))),
    'alignments': [4, 4, 4, 8, 8, 8], 'sizes': [4, 4, 4, 8, 8, 8]}
SOURCE = SOURCE_PATH.read_text()
CALLER_NAME = 'whole_interface_source_fixture'
CALLER = '_Z' + str(len(CALLER_NAME)) + CALLER_NAME + 'v'


def direct_range(begin, end):
    return {'begin': {'offset': begin}, 'end': {'offset': end - 1, 'tokLen': 1}}


def fixture():
    """Synthetic nodes, explicitly not the retained compiler observation."""
    definitions = {}
    calls = []
    for index, match in enumerate(re.finditer(r'(get_(?:noncacheable|cacheable)_tile_pointer)<(std::(?:u?int32_t))>\((\w+)\)', SOURCE)):
        name, spelling = match[1], match[2]
        canonical = 'unsigned int' if spelling == 'std::uint32_t' else 'int'
        record = next(row for row in DECLARATIONS if row['name'] == name)
        identity = 'synthetic-declaration-' + name + '-' + canonical
        definitions[identity] = {'id': identity, 'kind': 'FunctionDecl', 'name': name,
            'loc': {'_file': record['header_path'], 'line': record['line']},
            'range': direct_range(*record['source_range']), 'type': {'qualType': API['signature'](record, canonical)},
            'inner': [{'kind': 'TemplateArgument', 'type': {'qualType': canonical}},
                {'kind': 'ParmVarDecl', 'name': 'SPD_id', 'type': {'qualType': 'int'}},
                {'kind': 'CompoundStmt', 'inner': []}]}
        calls.append({'id': 'synthetic-call-' + str(index), 'kind': 'CallExpr',
            'range': direct_range(match.start(), match.end()),
            'inner': [{'kind': 'DeclRefExpr', 'referencedDecl': {'id': identity, 'name': name}},
                {'kind': 'DeclRefExpr', 'referencedDecl': {'id': 'synthetic-local-' + match[3], 'name': match[3]},
                 'type': {'qualType': 'int'}}]})
    if len(calls) != 6:
        raise AssertionError('exact six fixed-fixture pointer getter sites required')
    owner = {'id': 'synthetic-source-definition', 'kind': 'FunctionDecl', 'name': CALLER_NAME,
        'mangledName': CALLER, 'loc': {'_file': str(SOURCE_PATH.resolve())},
        'inner': [{'kind': 'CompoundStmt', 'inner': calls}]}
    tu = {'kind': 'TranslationUnitDecl', 'id': 'synthetic-TU-for-signature-control-only',
          'inner': [*definitions.values(), owner]}
    records = [API['bind_call'](tu, caller=CALLER, call_range=API['_span'](call), source_path=SOURCE_PATH,
        source_text=SOURCE, declarations=DECLARATIONS, abi=ABI) for call in calls]
    return tu, records


def projection_recheck(path):
    tree = ast.parse(path.read_text())
    projection = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_projection')
    rows = [node.value for node in ast.walk(projection) if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'fresh' for target in node.targets)
        and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == "api['recheck_binding']"]
    if len(rows) != 1:
        raise AssertionError('one exact projection recheck callsite required')
    return rows[0]


def apply_recheck(path, record, tu, *, caller=CALLER):
    return eval(compile(ast.Expression(body=projection_recheck(path)), '<exact-projection-recheck-callsite>', 'eval'),
        {'api': API, 'record': record, 'normalized_tu': tu, 'caller': caller, 'source_path': SOURCE_PATH,
         'source': SOURCE, 'declarations': DECLARATIONS, 'abi': ABI})


class RecheckControls(unittest.TestCase):
    def test_real_keyword_only_signature(self):
        signature = inspect.signature(API['bind_call'])
        for name in ('caller', 'call_range'):
            self.assertEqual(signature.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIs(signature.parameters[name].default, inspect.Parameter.empty)
        old = projection_recheck(V2 / 'runtime_projection_v2.py')
        new = projection_recheck(HERE / 'runtime_projection_v3.py')
        self.assertEqual([row.arg for row in new.keywords], ['caller', 'call_range'] + [row.arg for row in old.keywords])

    def test_v2_red_every_pointer_getter(self):
        tu, records = fixture()
        self.assertEqual(len(records), 6)
        for row in records:
            with self.subTest(name=row['name'], dtype=row['dtype']):
                with self.assertRaisesRegex(TypeError, "required keyword-only arguments: 'caller' and 'call_range'"):
                    apply_recheck(V2 / 'runtime_projection_v2.py', row, tu)

    def test_v3_green_every_pointer_getter(self):
        tu, records = fixture()
        self.assertEqual({row['name'] for row in records}, {'get_cacheable_tile_pointer', 'get_noncacheable_tile_pointer'})
        self.assertEqual({row['dtype'] for row in records}, {0, 1})
        for row in records:
            self.assertEqual(apply_recheck(HERE / 'runtime_projection_v3.py', row, tu), row)

    def test_wrong_caller_refuses(self):
        tu, records = fixture()
        with self.assertRaisesRegex(API['Refused'], 'actual TU/caller'):
            apply_recheck(HERE / 'runtime_projection_v3.py', records[0], tu, caller='_Z5wrongv')
        changed = copy.deepcopy(records[0]); changed['caller_mangled'] = '_Z5wrongv'
        with self.assertRaisesRegex(API['Refused'], 'binding changed'):
            apply_recheck(HERE / 'runtime_projection_v3.py', changed, tu)

    def test_wrong_call_range_refuses(self):
        tu, records = fixture()
        for selected in ([records[0]['call_range'][0] + 1, records[0]['call_range'][1]],
                         records[3]['call_range'], [-1, 1], [True, 2], 'range'):
            with self.subTest(range=selected):
                changed = copy.deepcopy(records[0]); changed['call_range'] = selected
                with self.assertRaises(API['Refused']):
                    apply_recheck(HERE / 'runtime_projection_v3.py', changed, tu)

    def test_exact_one_callsite_inverse_all_other_functions_and_literals(self):
        inverse = json.loads((HERE / 'runtime-projection-v3-inverse.json').read_text())
        text = (HERE / 'runtime_projection_v3.py').read_text()
        for row in reversed(inverse['edits']):
            self.assertEqual(text.count(row['new']), 1)
            text = text.replace(row['new'], row['old'], 1)
        self.assertEqual(text, (V2 / 'runtime_projection_v2.py').read_text())
        old_tree = ast.parse((V2 / 'runtime_projection_v2.py').read_text())
        new_tree = ast.parse((HERE / 'runtime_projection_v3.py').read_text())
        old = {node.name: node for node in old_tree.body if isinstance(node, ast.FunctionDef)}
        new = {node.name: node for node in new_tree.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(old), set(new))
        for name in set(old) - {'_projection'}:
            self.assertEqual(ast.dump(old[name], include_attributes=False), ast.dump(new[name], include_attributes=False))

    def test_all_v2_packet_and_input_pins_unchanged(self):
        path = V2 / 'runtime-projection-source-packet-v2.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), 'b52aee9f472356519cc3edb1fe23bc8e5c1e333dcbb969ebdb23c4d9c51c0c49')
        value = json.loads(path.read_bytes())
        for row in value['files'] + value['inputs']:
            raw = Path(row['path']).read_bytes()
            self.assertEqual(len(raw), row['bytes']); self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(), '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd')


if __name__ == '__main__':
    unittest.main(verbosity=2)
