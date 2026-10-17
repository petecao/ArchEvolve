"""2026-10-16 ET. Compiler-free real-source integration boundary controls.

Module locations and captures explicitly unavailable to this local review are
protocol fixtures. No installed project module or retained scientific payload
is imported/interpreted, and no source/native/proof program is executed.
"""
import ast
import builtins
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
PROPOSED = HERE / 'proposed'
SOURCE = PROPOSED / 'swdb/dx100_checked_source.py'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('integration controls forbid child/native/network')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise RuntimeError('integration controls forbid installed project imports')


sys.addaudithook(audit)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def need(value, message):
    if not value: raise ValueError(message)


def functions(path):
    text = path.read_text()
    return {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}


def leaves(path, selected, values=None):
    tree = ast.parse(path.read_bytes())
    nodes = [node for node in tree.body if isinstance(node, ast.Assign) or
        isinstance(node, ast.FunctionDef) and node.name in selected]
    result = {'Path': Path, 'hashlib': hashlib, 'json': json, 'need': need, **(values or {})}
    exec(compile(ast.Module(nodes, type_ignores=[]), str(path), 'exec'), result)
    return result


def producer_namespace(path):
    root = Path('/explicit-selected-producer-project')
    modules = {}
    namespace = {'__file__': str(root / 'swdb/dx100_checked_source.py'), 'Path': Path, 'need': need}
    tree = ast.parse(path.read_bytes())
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'swdb._dx100_whole':
            for row in node.names:
                module = modules.setdefault(row.name, SimpleNamespace(__file__=str(root / 'swdb/_dx100_whole' / (row.name + '.py'))))
                namespace[row.asname or row.name] = module
    namespace['contracts'] = SimpleNamespace(__file__=str(root / 'swdb/dx100_whole_checked.py'))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'swdb._dx100_whole':
            for row in node.names:
                modules.setdefault(row.name, SimpleNamespace(__file__=str(root / 'swdb/_dx100_whole' / (row.name + '.py'))))
    def imported(name, globals=None, locals=None, fromlist=(), level=0):
        if name != 'swdb._dx100_whole' or level != 0 or not set(fromlist) <= set(modules):
            raise AssertionError('unlisted producer-path protocol import')
        return SimpleNamespace(**modules)
    namespace['__builtins__'] = {**vars(builtins), '__import__': imported}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('producer_paths', 'producer_closure') or
        isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'ROUTE_PRODUCERS' for target in node.targets)]
    exec(compile(ast.Module(selected, type_ignores=[]), '<real-producer-path-contract>', 'exec'), namespace)
    return namespace, modules


class IntegrationControls(unittest.TestCase):
    def test_applied_V5_and_reviewed_proposal_physical_bytes(self):
        rows = json.loads((HERE / 'production-paths-and-bases-v1.json').read_bytes())
        self.assertEqual(len(rows['applied_V5_observed_rows']), 50)
        for row in rows['applied_V5_observed_rows']:
            raw = Path(row['path']).read_bytes()
            self.assertEqual((len(raw), sha(raw)), (row['bytes'], row['sha256']))
        self.assertEqual(len(rows['paths']), 10)
        self.assertEqual(sum(row['base'] is not None for row in rows['paths']), 3)
        for row in rows['paths']:
            raw = Path(row['proposal']['path']).read_bytes()
            self.assertEqual(raw, Path(row['reviewed_source']['path']).read_bytes())
            if row['base'] is None:
                self.assertFalse((PROJECT / row['relative']).exists())
            else:
                self.assertEqual((PROJECT / row['relative']).read_bytes(), (HERE / 'base-source' / row['relative']).read_bytes())

    def test_complete_three_existing_file_inverses_and_legacy_unchanged(self):
        inverse = json.loads((HERE / 'exact-source-inverses-v1.json').read_bytes())
        self.assertEqual(len(inverse['files']), 3)
        for relative, rows in inverse['files'].items():
            text = (PROPOSED / relative).read_text()
            for row in reversed(rows):
                self.assertEqual(text.count(row['new']), row.get('count', 1))
                text = text.replace(row['new'], row['old'])
            self.assertEqual(text, (HERE / 'base-source' / relative).read_text())
        old = HERE / 'base-source/swdb/_dx100_whole/normalized_capture_ingress_v2.py'
        self.assertEqual(functions(old), functions(PROPOSED / 'swdb/_dx100_whole/normalized_capture_ingress_v2.py'))
        self.assertEqual(sha((PROJECT / 'swdb/_dx100_whole/compiler_unit_adapter_v3.py').read_bytes()),
            '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        self.assertEqual(inverse['finite_hook_files_not_written'], ['cbmc_adapter.py', 'formal_frame.py', 'proof_semantics.py', 'proof_setup.py'])

    def test_real_producer_paths_close_all_seven_new_roles(self):
        new, modules = producer_namespace(SOURCE)
        old, _ = producer_namespace(HERE / 'base-source/swdb/dx100_checked_source.py')
        current = new['producer_paths'](); baseline = old['producer_paths']()
        self.assertEqual({key: current[key] for key in baseline}, baseline)
        self.assertEqual(set(current) - set(baseline), {'capture_family_dispatch_v1.py',
            'memory_normalized_capture_ingress_v1.py', 'memory_normalized_compiler_adapter_v1.py',
            'memory_source_preparation_v1.py', 'memory_capture_facts_v1.json',
            'abi_role_transport_v1.py', 'strict_minify_v2.py'})
        for path in current.values(): self.assertTrue(path.is_relative_to('/explicit-selected-producer-project/swdb'))
        modules['abi_role_transport_v1'].__file__ = modules['strict_minify_v2'].__file__
        with self.assertRaises(ValueError): new['producer_paths']()

    def test_real_producer_closure_rejects_deletion_extra_and_wrong_path(self):
        ns, _ = producer_namespace(SOURCE)
        paths = ns['producer_paths']()
        rows = {name: {'path': str(path), 'bytes': 1, 'sha256': 'a' * 64} for name, path in paths.items()}
        # Exact path/member checking executes here; physical contents are an
        # explicit unavailable-future-producer protocol double.
        manifest = {'schema': 'swdb-dx100-whole-producers-1', 'files': rows}
        calls = []
        reads = SimpleNamespace(document=lambda row: manifest, absolute=lambda row: calls.append(row))
        ns['producer_closure']({'producer_manifest': 'explicit-future-manifest'}, reads)
        self.assertEqual(len(calls), len(paths))
        for mutation in ('deleted', 'extra', 'wrong-path'):
            changed = copy.deepcopy(manifest)
            if mutation == 'deleted': changed['files'].pop('abi_role_transport_v1.py')
            elif mutation == 'extra': changed['files']['arbitrary.py'] = rows['abi_role_transport_v1.py']
            else: changed['files']['abi_role_transport_v1.py']['path'] = '/other/same-byte-helper.py'
            reads.document = lambda row, changed=changed: changed
            with self.assertRaises(ValueError): ns['producer_closure']({'producer_manifest': 'explicit-future-manifest'}, reads)

    def test_dispatch_preserves_actual_legacy_branch_and_unready_memory_refusal(self):
        root = PROPOSED / 'swdb/_dx100_whole'
        calls = []
        source = SimpleNamespace(need=need, CAPTURE_KIND='lossless-complete-original-tu-v1',
            complete_capture=lambda *args: calls.append(('legacy', args)) or 'legacy-result')
        first = leaves(root / 'normalized_capture_ingress_v2.py', {'complete_capture'}, {'source': source})
        memory = leaves(root / 'memory_normalized_capture_ingress_v1.py', {'complete_capture'}, {'source': source})
        memory['_derive'] = lambda *args: (_ for _ in ()).throw(AssertionError('unready memory reached scientific derivation'))
        ns = leaves(root / 'capture_family_dispatch_v1.py', {'complete_capture'},
            {'source': source, 'first': SimpleNamespace(**first), 'memory': SimpleNamespace(**memory)})
        selected = {'capture': {'kind': source.CAPTURE_KIND}}
        self.assertEqual(ns['complete_capture'](selected, None, '/original'), 'legacy-result')
        self.assertEqual(len(calls), 1)
        unready = {'capture': {'kind': memory['KIND'], 'prepared': None},
            'proof_source': {'sha256': memory['SOURCE_SHA']}}
        with self.assertRaises(ValueError): ns['complete_capture'](unready, None, '/original')
        for selected in ({'capture': {'kind': 'unsupported-unprepared-memory-profile-1'}},
            {'capture': {'kind': memory['KIND']}, 'proof_source': {'sha256': '0' * 64}}, {'capture': []}):
            with self.assertRaises(ValueError): ns['complete_capture'](selected, None, '/original')

    def test_actual_capture_metadata_projection_keeps_family_input_roles(self):
        dispatcher = SimpleNamespace(NORMALIZED_KINDS=('complete-original-tu-paired-type-gzip-2',
            'complete-memory-original-tu-paired-type-gzip-1'))
        def imported(name, globals=None, locals=None, fromlist=(), level=0):
            self.assertEqual((name, fromlist, level), ('swdb._dx100_whole', ('capture_family_dispatch_v1',), 0))
            return SimpleNamespace(capture_family_dispatch_v1=dispatcher)
        ns = {'need': need, 'CAPTURE_KIND': 'lossless-complete-original-tu-v1',
            '__builtins__': {**vars(builtins), '__import__': imported}}
        node = next(node for node in ast.parse(SOURCE.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == 'capture_inputs')
        exec(compile(ast.Module([node], type_ignores=[]), '<real-capture-input-metadata-frontdoor>', 'exec'), ns)
        for kind in dispatcher.NORMALIZED_KINDS:
            selected = {'kind': kind, 'transform': {'normalized_gzip': {'path': '/derived'}},
                'original': {'observation': {'path': '/original-observation'}, 'compressed_tu': {'path': '/wire'}}}
            self.assertEqual(ns['capture_inputs'](selected), ({'path': '/derived'}, {'path': '/original-observation'}))
        with self.assertRaises(ValueError): ns['capture_inputs']({'kind': 'unsupported-unprepared-memory-profile-1'})

    def test_both_new_physical_adapter_pins_match_and_old_pins_refuse(self):
        root = PROPOSED / 'swdb/_dx100_whole'
        for file, variable, expected_adapter, module_name, old_sha in (
            ('normalized_capture_ingress_v2.py', 'NORMALIZED_COMPILER_SHA', 'normalized_compiler_adapter_v1.py', 'normalized_compiler',
                '0bbf572196677dbc926bb5d331022c2766e44c287bd1ea3cce0ef077153a8a01'),
            ('memory_normalized_capture_ingress_v1.py', 'MEMORY_COMPILER_SHA', 'memory_normalized_compiler_adapter_v1.py', 'memory_compiler',
                '1315ebef75dc4219bcb012aa2a5f85cbcaeb82c54bb625fdad6f18ea397a6e62')):
            tree = ast.parse((root / file).read_bytes())
            loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
                and ast.unparse(node.target) == '(module, expected)')
            def absolute(row, **kwargs):
                data = Path(row['path']).read_bytes()
                need((len(data), sha(data)) == (row['bytes'], row['sha256']), 'exact physical primitive required')
            ns = {'Path': Path, 'hashlib': hashlib, 'need': need, 'reads': SimpleNamespace(absolute=absolute)}
            for name, basename in (('normalizer', 'role_normalized_gzip_v2.py'), ('codec', 'lossless_gzip_v2.py'), ('closed', 'closed_python_surface.py')):
                ns[name] = SimpleNamespace(__file__=str(PROJECT / 'swdb/_dx100_whole' / basename))
            ns[module_name] = SimpleNamespace(__file__=str(root / expected_adapter), LEGACY_SHA='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
            ns['source'] = SimpleNamespace(compiler=SimpleNamespace(__file__=str(PROJECT / 'swdb/_dx100_whole/compiler_unit_adapter_v3.py')))
            nodes = [node for node in tree.body if isinstance(node, ast.Assign)]
            exec(compile(ast.Module(nodes, type_ignores=[]), '<exact-adapter-constants>', 'exec'), ns)
            self.assertEqual(ns[variable], sha((root / expected_adapter).read_bytes()))
            code = compile(ast.Module([loop], type_ignores=[]), '<exact-adapter-physical-gate>', 'exec')
            exec(code, ns)
            ns[variable] = old_sha
            with self.assertRaises(ValueError): exec(code, ns)

    def test_prospective_recipe_has_no_stale_basis_or_context(self):
        recipe = json.loads((HERE / 'producer-member-recipe-v1.json').read_bytes())
        self.assertEqual(len(recipe['baseline_member_paths']), 54)
        self.assertEqual(len(recipe['ABI_memory_added_paths']), 7)
        self.assertEqual(recipe['source_unit_member_paths_before_final_finite_union'],
            sorted(set(recipe['baseline_member_paths']) | set(recipe['ABI_memory_added_paths'])))
        self.assertEqual(len(recipe['source_unit_member_paths_before_final_finite_union']), 61)
        self.assertIsNone(recipe['final_reviewed_finite_member_paths_and_packet'])
        self.assertIsNone(recipe['final_root_selected_source_commit'])
        self.assertIsNone(recipe['final_producer_basis'])
        self.assertIsNone(recipe['unready_memory_capture_prepared_mapping_receiver_and_context'])
        self.assertTrue(recipe['old_basis_hashes_are_not_new_basis_hashes'])
        self.assertEqual(EVENTS, [])
        self.assertNotIn('swdb', sys.modules)


if __name__ == '__main__': unittest.main(verbosity=2)
