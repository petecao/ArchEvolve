"""2026-10-16 ET. Synthetic same-TU root-cut controls; no observed AST claim."""
import ast
import copy
import inspect
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def forbid(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'}:
        raise AssertionError('no child/network in source-root controls')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('no project import in source-root controls')


sys.addaudithook(forbid)
M = runpy.run_path(str(HERE / 'source_memory_selection_v1.py'))
SOURCE = WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp'
RAW = SOURCE.read_bytes()
TEXT = RAW.decode()
BINDER = WHOLE / 'whole_interface_v4.py'
BTREE = ast.parse(BINDER.read_bytes())


def fixture(function):
    roots, calls = [], []
    for index, (name, _, _, _) in enumerate(M['CASES']):
        start, end = M['spelling_span'](TEXT, name)
        local_id = '0x' + str(100 + index)
        local = {'kind': 'VarDecl', 'id': local_id, 'name': 'data',
            'loc': {'_file': str(SOURCE)}, 'inner': []}
        call_start = TEXT.index('alloc_MAA()', start)
        call_range = [call_start, call_start + len('alloc_MAA()')]
        call = {'kind': 'CallExpr', 'range': {'begin': {'offset': call_range[0]},
            'end': {'offset': call_range[1] - 1, 'tokLen': 1}}, 'inner': []}
        ref = {'kind': 'DeclRefExpr', 'referencedDecl': {'kind': 'VarDecl', 'id': local_id}, 'inner': []}
        roots.append({'kind': 'FunctionDecl', 'name': name, 'mangledName': '_Z' + str(len(name)) + name + 'v',
            'id': '0x' + str(200 + index), 'loc': {'_file': str(SOURCE)},
            'range': {'begin': {'offset': start}, 'end': {'offset': end - 1, 'tokLen': 1}},
            'type': {'qualType': 'std::uint32_t ()'},
            'inner': [{'kind': 'CompoundStmt', 'inner': [local, call, ref]}]})
        calls.append({'name': 'alloc_MAA', 'caller_mangled': roots[-1]['mangledName'], 'call_range': call_range})
    tu = {'kind': 'TranslationUnitDecl', 'inner': roots}
    preparation = {'schema': 'whole-interface-original-tu-preparation-1',
        'one_full_tu_for_all_declaration_ids': True, 'normalized_full_tu_sha256': M['digest'](tu),
        'original_source_sha256': M['SOURCE_SHA'], 'calls': calls}
    # Real binder keyword-only signature, real recheck wrapper and real direct
    # range parser. The source-body binder's semantics are deliberately not
    # substituted or claimed here: only the invocation/identity seam is tested.
    functions = {node.name: node for node in BTREE.body if isinstance(node, ast.FunctionDef)}
    signature = copy.deepcopy(functions['bind_call'])
    signature.body = [ast.Pass()]
    namespace = {'_need': M['need']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[signature], type_ignores=[])), str(BINDER), 'exec'), namespace)
    sig = inspect.signature(namespace['bind_call'])
    def known_binding(*args, **kwargs):
        sig.bind(*args, **kwargs)
        selected = [row for row in calls if row['caller_mangled'] == kwargs['caller']
                    and row['call_range'] == list(kwargs['call_range'])]
        M['need'](len(selected) == 1, 'wrong same-TU caller or call range')
        return selected[0]
    namespace.update(bind_call=known_binding)
    nodes = [functions[name] for name in ('_span', 'recheck_binding')]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(BINDER), 'exec'), namespace)
    api = {'__file__': str(BINDER), 'validate_abi': lambda abi: M['need'](abi == {'fixture': 'ABI'}, 'wrong ABI'),
        '_span': namespace['_span'], 'recheck_binding': namespace['recheck_binding']}
    declarations = [{'name': 'alloc_MAA'}] + [{'name': 'fixture_api_' + str(n)} for n in range(25)] + [{'name': 'fixture_api_0'}]
    kwargs = {'normalized_tu': tu, 'source_path': SOURCE, 'preparation': preparation,
        'function': function, 'declarations': declarations, 'abi': {'fixture': 'ABI'}}
    return api, kwargs


def refresh(kwargs):
    kwargs['preparation']['normalized_full_tu_sha256'] = M['digest'](kwargs['normalized_tu'])


class Controls(unittest.TestCase):
    def test_all_three_roots_preserve_selected_tokens_and_coordinates(self):
        for name, result, verdict, failure in M['CASES']:
            api, kwargs = fixture(name)
            before = copy.deepcopy(kwargs['normalized_tu'])
            value = M['selected_root'](api, **kwargs)
            self.assertEqual(kwargs['normalized_tu'], before)
            self.assertEqual(value['profile']['contract']['expected_result'], result)
            self.assertEqual((value['profile']['predicted_verdict'], value['profile']['predicted_failure_rule']), (verdict, failure))
            self.assertEqual(len(value['omitted_unreferenced_definitions']), 2)
            text = value['counterpart_root_source']
            begin, end = value['selected_source_range']
            self.assertEqual(TEXT[begin:end], text[begin:end])
            self.assertEqual([i for i,c in enumerate(TEXT) if c == '\n'], [i for i,c in enumerate(text) if c == '\n'])
            self.assertIn('#include "MAA_gem5.hpp"', text)
            for omitted in value['omitted_unreferenced_definitions']:
                left,right = omitted['range']
                self.assertTrue(all(char in ' \r\n' for char in text[left:right]))
            self.assertFalse(value['actual_source_ABI_native_public_or_new02_acceptance'])

    def test_old_first_source_and_unknown_function_refuse(self):
        for name in ('whole_interface_source_fixture', 'unlisted', '', None):
            with self.assertRaises(M['Refused']):
                M['profile'](name)

    def test_complete_source_identity_and_unfiltered_graph_required(self):
        api, kwargs = fixture(M['CASES'][0][0])
        for key, value in (('normalized_full_tu_sha256', '0' * 64), ('original_source_sha256', '0' * 64),
                           ('one_full_tu_for_all_declaration_ids', False)):
            candidate = copy.deepcopy(kwargs); candidate['preparation'][key] = value
            with self.assertRaises(M['Refused']): M['selected_root'](api, **candidate)
        candidate = copy.deepcopy(kwargs); candidate['normalized_tu']['inner'].pop(); refresh(candidate)
        with self.assertRaises(M['Refused']): M['selected_root'](api, **candidate)

    def test_wrong_root_type_identity_span_or_parameter_refuses(self):
        for field, value in (('type', {'qualType': 'int ()'}), ('mangledName', '_Zwrongv'),
                             ('id', 'invented'), ('storageClass', 'static')):
            api, kwargs = fixture(M['CASES'][0][0]); kwargs['normalized_tu']['inner'][0][field] = value; refresh(kwargs)
            with self.assertRaises(M['Refused']): M['selected_root'](api, **kwargs)
        api, kwargs = fixture(M['CASES'][0][0]); kwargs['normalized_tu']['inner'][0]['range']['begin']['offset'] += 1; refresh(kwargs)
        with self.assertRaises(M['Refused']): M['selected_root'](api, **kwargs)
        api, kwargs = fixture(M['CASES'][0][0]); kwargs['normalized_tu']['inner'][0]['inner'].append({'kind': 'ParmVarDecl'}); refresh(kwargs)
        with self.assertRaises(M['Refused']): M['selected_root'](api, **kwargs)

    def test_nonlocal_variable_or_omitted_function_dependency_refuses(self):
        for ref in ({'kind': 'VarDecl', 'id': '0xglobal'}, {'kind': 'FunctionDecl', 'id': '0x201'},
                    {'kind': 'VarDecl', 'id': '0x101'}):
            api, kwargs = fixture(M['CASES'][0][0]); kwargs['normalized_tu']['inner'][0]['inner'][0]['inner'][-1]['referencedDecl'] = ref; refresh(kwargs)
            with self.assertRaises(M['Refused']): M['selected_root'](api, **kwargs)
        api, kwargs = fixture(M['CASES'][0][0]); kwargs['normalized_tu']['inner'].append({'kind': 'VarDecl', 'id': '0xglobal', 'loc': {'_file': str(SOURCE)}}); refresh(kwargs)
        with self.assertRaises(M['Refused']): M['selected_root'](api, **kwargs)

    def test_complete_actual_call_census_and_real_required_keyword_seam(self):
        api, kwargs = fixture(M['CASES'][0][0]); M['selected_root'](api, **kwargs)
        for mutation in ('delete', 'duplicate', 'wrong-caller', 'wrong-range', 'wrong-name'):
            api, candidate = fixture(M['CASES'][0][0]); calls = candidate['preparation']['calls']
            if mutation == 'delete': calls.pop(0)
            if mutation == 'duplicate': calls.append(copy.deepcopy(calls[0]))
            if mutation == 'wrong-caller': calls[0]['caller_mangled'] = '_Zwrongv'
            if mutation == 'wrong-range': calls[0]['call_range'][1] += 1
            if mutation == 'wrong-name': calls[0]['name'] = 'unadmitted'
            with self.assertRaises(M['Refused']): M['selected_root'](api, **candidate)
        # These required arguments are bound by the real original signature;
        # no permissive **kwargs-only fake can hide this integration edge.
        with self.assertRaises(TypeError): api['recheck_binding']({}, candidate['normalized_tu'], source_path=SOURCE,
            source_text=TEXT, declarations=candidate['declarations'], abi=candidate['abi'])

    def test_mapping_and_predicted_outcome_metadata_never_grants_acceptance(self):
        for name, _, _, _ in M['CASES']:
            selected = M['profile'](name)
            self.assertEqual(selected['objects'][0]['requires_owned_physical_alignment'], 64)
            self.assertFalse(selected['objects'][0]['alignment_inferred_from_source'])
        tree = ast.parse((HERE / 'source_memory_selection_v1.py').read_bytes())
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and (n.module or '').startswith('swdb') for n in ast.walk(tree)))
        self.assertNotIn('subprocess', ast.unparse(tree))


if __name__ == '__main__':
    unittest.main(verbosity=2)
