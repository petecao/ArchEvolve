"""2026-10-16 ET. Pure metadata/physical seams, no actual TU preparation.

Physical pin readers, closed registry functions, source selection, the formal
metadata front door and harness/obligation gates are real extracted source.
Library construction/checked-body normalization and native projection emission
are explicit protocol doubles. No project package, compiler or native imports.
"""
import ast
import builtins
import copy
from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import re
import runpy
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OUT = HERE / 'proposed/swdb'
BASE = runpy.run_path(str(WHOLE / 'public-profile-builder-v2/test_contract_formatter_v2.py'), run_name='metadata_support')
REG = SimpleNamespace(**runpy.run_path(str(WHOLE / 'source-unit-registry-v2/unit_policy_registry_v2.py')))
RECEIVER = SimpleNamespace(**runpy.run_path(str(WHOLE / 'receiver-state-draws-v2/receiver_state_draws_v2.py')))
BUILDER = BASE['NEW']


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise AssertionError('pure controls forbid child/native/network')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('pure controls forbid project imports')


sys.addaudithook(deny)
extract = BASE['extract']
protocol = BASE['import_protocol']


def replace_policy_rows(policies, refs, contracts):
    documents = {}
    for index, definition in enumerate(REG.FUNCTIONS):
        function, source_sha, expected = definition
        policy = policies[index]
        policy['unit_contracts'] = [{'id': name, 'sha256': REG.digest(json.loads(contracts[name])), 'expected_result': value}
                                   for value, name in expected]
        raw = (json.dumps(policy, indent=2) + '\n').encode() if index == 0 else REG.canonical(policy)
        refs[index]['sha256'] = REG.sha(raw); documents[REG.sha(raw)] = raw
    return documents


class Seam:
    def __init__(self, root):
        self.root = root
        self.values, self.contracts, self.policies, self.references = {}, {}, [], []
        for index, (function, source_sha, expected) in enumerate(REG.FUNCTIONS):
            source = {'root': 'library', 'path': 'proof_units/' + ('first.cpp' if index == 0 else 'memory.cpp'), 'sha256': source_sha}
            for value, name in expected:
                contract = copy.deepcopy(BUILDER.unit_contracts(source)[80])
                contract['id'] = name; contract['proof_unit']['function'] = function
                contract['clauses'][1]['statement'] = 'Original scalar result equals ' + str(value) + '.'
                contract['clauses'][1]['acsl']['text'] = r'ensures \result == ' + str(value) + ';'
                self.values[name] = contract; self.contracts[name] = REG.canonical(contract)
            self.policies.append({'kind': REG.KIND,
                'schema': 'dx100-whole-fixed-source-policy-1' if index == 0 else 'dx100-whole-exact-memory-source-policy-1',
                'function': function, 'caller_mangled': '_Z' + str(len(function)) + function + 'v',
                'defines': ['NUM_CORES=4', 'TILE_SIZE=16384'], 'choice_budget': 256, 'thread': 0,
                'buffer_projection': 'fixed-fixture-identical-buffer-with-captured-diagnostic-origin-v1' if index == 0 else
                    'exact-three-root-cxx-view-with-captured-origin-v1',
                'proof_source': source, 'capture': {'synthetic': 'NOT an accepted capture'},
                'receiver_selection': {'root': 'library', 'path': 'receivers/' + str(index) + '.json', 'sha256': 'a' * 64},
                'expected': {'synthetic': 'NOT a source certificate'},
                'producer_manifest': {'root': 'library', 'path': 'producers/' + str(index) + '.json', 'sha256': 'b' * 64},
                'native_projection': {'synthetic': 'NOT a native certificate'}, 'frame': r'assigns \everything;',
                'unit_contracts': [], 'source_loop_bound': 1, 'helper_loop_bound': 513})
            self.references.append({'root': 'library', 'path': 'policies/' + str(index) + '.json', 'sha256': '0' * 64})
        policy_docs = replace_policy_rows(self.policies, self.references, self.contracts)
        self.output = REG.assemble(self.references, policy_docs, self.contracts)
        self.reference = {'root': 'library', 'path': 'registry.json', 'sha256': self.output['registry_sha256']}
        self.write('registry.json', self.output['registry_bytes'])
        for ref in self.references:
            self.write(ref['path'], policy_docs[ref['sha256']])
        for name, raw in self.contracts.items():
            self.write('rewrite_contracts/' + name + '.yaml', raw)
        self.write('proof_units/first.cpp', (WHOLE / 'source_call_fixture_v2.cpp').read_bytes())
        self.write('proof_units/memory.cpp', (WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp').read_bytes())
        self.entry = {'id': 'semantics.dx100_bfs_0_2', 'kind': 'proof_semantics', 'target': 'dx100-mmio', 'sequence': 2,
                      'contract_form': 'synthetic NORMALIZATION PROTOCOL ONLY'}
        # Exact real portable resolver/pin/content methods; JSON construction is
        # a disclosed stand-in for normal Library's YAML loading constructor.
        library_ns = {'Path': Path, 're': re, 'paths': SimpleNamespace(HOME=root),
                      'artifacts': SimpleNamespace(digest=REG.digest,
                          file_hash=lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest())}
        original = next(node for node in ast.parse((WHOLE / 'public-profile-builder-v2/base-source/library.py').read_text()).body
                        if isinstance(node, ast.ClassDef) and node.name == 'Library')
        names = {'get', 'content_sha256', 'resolve', '_pin'}
        methods = [node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in names]
        cls = ast.ClassDef(name='Library', bases=[], keywords=[], body=methods, decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module([cls], type_ignores=[])), 'real-library-methods', 'exec'), library_ns)
        Library = library_ns['Library']; outer = self
        def initialize(library, path):
            library.root = Path(path); library.problems = []; library.files = {}; library.entries = {}
            for file in sorted((library.root / 'rewrite_contracts').glob('*.yaml')):
                value = json.loads(file.read_bytes()); library.entries[value['id']] = value; library.files[value['id']] = file
            library.entries[outer.entry['id']] = outer.entry
        Library.__init__ = initialize
        self.Library = Library; self.library = Library(root)
        checked = {'Path': Path, 'stat': stat, 'hashlib': hashlib, 'json': json, 're': re,
                   'paths': SimpleNamespace(HOME=root)}
        extract(WHOLE / 'checked-contracts-v2/dx100_whole_checked_v2.py',
                {'Refused', 'need', 'stable_metadata', 'pinned', 'document'}, checked)
        checked['policy'] = lambda library, entry: {'source_policy': self.reference, 'choice_budget': 256,
                                                  'components': [], 'design': {}}
        checked['checked'] = lambda data: data == self.entry
        contracts = SimpleNamespace(**checked)
        source = SimpleNamespace()
        imports = {('swdb', ('dx100_checked_source',)): SimpleNamespace(dx100_checked_source=source),
                   ('swdb.library', ('Library',)): SimpleNamespace(Library=Library),
                   ('swdb', ('paths',)): SimpleNamespace(paths=SimpleNamespace(HOME=root))}
        src = {'dataclass': dataclass, 'json': json, 'Path': Path, 'stat': stat, 'hashlib': hashlib, 're': re,
               'contracts': contracts, 'receiver': RECEIVER, 'unit_registry': REG,
               'FUNCTION': REG.FUNCTIONS[0][0], 'UNIT_FUNCTIONS': tuple(row[0] for row in REG.FUNCTIONS),
               'METHOD': 'method.dx100-whole-checked-source-v1', '__builtins__': protocol(imports)}
        extract(OUT / 'dx100_checked_source.py', {'Refused', 'need', 'sha', 'canonical', 'digest',
            'SourceSelection', 'SourceUnit', 'Inputs', 'source_policy', 'select_baseline',
            'checked_unit_format', 'unit_contract', 'harness_profile'}, src)
        source.__dict__.update(src)
        consumer = {'json': json, 'Path': Path, 'registry': REG, '__builtins__': protocol(imports)}
        extract(OUT / 'dx100_checked_registry.py', {'load', 'baseline', 'contract', 'harness_clauses'}, consumer)
        self.consumer = consumer; src['registry_consumer'] = SimpleNamespace(**consumer)
        source.registry_consumer = src['registry_consumer']
        self.src, self.source = src, source
        self.translator = BASE['MetadataSeam'](root, {79: self.values[REG.FUNCTIONS[0][2][0][1]],
                                                   80: self.values[REG.FUNCTIONS[0][2][1][1]]}).translator

    def write(self, relative, raw):
        path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)

    def selection(self, index):
        policy = self.policies[index]
        unit = {'source': policy['proof_source'], 'function': policy['function']}
        return self.src['SourceSelection'](self.library, self.entry['id'], self.root, self.src['METHOD'], REG.canonical(unit))

    def unit(self, index):
        policy = self.policies[index]
        fields = {name: None for name in inspect.signature(self.src['SourceUnit']).parameters}
        fields.update(function=policy['function'], returns='uint32_t', policy_json=REG.canonical(policy),
                      selection=self.selection(index), certificate_json=REG.canonical({'unit_registry': self.reference}),
                      draw_rows_json=REG.canonical([{'name': 'whole_choice_' + str(i), 'role': 'whole-model-choice',
                          'ctype': 'uint32_t', 'c_lvalue': 'dws_choice_table[' + str(i) + ']'} for i in range(256)]))
        return self.src['SourceUnit'](**fields)


class CompositionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.seam = Seam(self.root)

    def test_actual_read_set_loads_all_four_policies_five_physical_contracts(self):
        reads = self.seam.src['Inputs'](self.seam.library)
        checked = self.seam.consumer['load'](self.seam.library, reads, self.seam.reference)
        self.assertEqual(len(reads.pins), 10)
        self.assertEqual((len(checked.policy_byte_identities), len(checked.contract_content_identities)), (4, 5))
        self.assertFalse(REG.baseline_policy(checked, {'source': self.seam.policies[0]['proof_source'],
            'function': self.seam.policies[0]['function']})['contract_or_source_admission_granted'])

    def test_all_structural_selections_recheck_exact_registry(self):
        for index, policy in enumerate(self.seam.policies):
            proof = {'source': policy['proof_source'], 'function': policy['function']}
            selected = self.seam.src['select_baseline'](self.seam.library, proof)
            self.assertEqual(selected.proof_unit_json, REG.canonical(proof))
            _entry, binding, actual = self.seam.src['source_policy'](selected, self.seam.src['Inputs'](self.seam.library))
            self.assertEqual(actual, policy); self.assertEqual(binding['source_policy'], self.seam.references[index])
            self.assertEqual(binding['unit_registry'], self.seam.reference)
        self.assertIsNone(self.seam.src['select_baseline'](self.seam.library, {'function': 'unregistered'}))

    def test_actual_contract_tuple_and_real_parsed_obligations(self):
        for index, (_function, _sha, expected) in enumerate(REG.FUNCTIONS):
            unit = self.seam.unit(index)
            for _value, name in expected:
                value = self.seam.values[name]; rows = self.seam.translator['clauses'](name, value['clauses'])
                self.seam.src['unit_contract'](self.seam.library, unit, name, REG.digest(value), rows)
                for changed_id, changed_hash in ((name, '0' * 64), ('contract.unregistered', REG.digest(value))):
                    with self.assertRaises((REG.Refused, self.seam.src['Refused'])):
                        self.seam.src['unit_contract'](self.seam.library, unit, changed_id, changed_hash, rows)
                wrong = list(rows); wrong[1] = self.seam.translator['Clause']('ensures', r'\result == 100', name + '#result')
                with self.assertRaises(self.seam.src['Refused']):
                    self.seam.src['unit_contract'](self.seam.library, unit, name, REG.digest(value), wrong)

    def test_read_set_refuses_symlink_missing_deleted_and_changed_contract(self):
        row = self.seam.policies[0]['unit_contracts'][0]; path = self.seam.library.files[row['id']]
        original = path.read_bytes(); target = self.root / 'identical'; target.write_bytes(original)
        path.unlink(); path.symlink_to(target)
        with self.assertRaises((ValueError, OSError)):
            self.seam.consumer['load'](self.seam.library, self.seam.src['Inputs'](self.seam.library), self.seam.reference)
        path.unlink(); path.write_bytes(original + b' ')
        with self.assertRaises(ValueError):
            self.seam.consumer['load'](self.seam.library, self.seam.src['Inputs'](self.seam.library), self.seam.reference)
        path.unlink()
        with self.assertRaises((ValueError, OSError)):
            self.seam.consumer['load'](self.seam.library, self.seam.src['Inputs'](self.seam.library), self.seam.reference)

    def test_real_harness_slots_are_full_u32_and_property_independent(self):
        profiles = []
        for index, (_function, _sha, expected) in enumerate(REG.FUNCTIONS):
            unit = self.seam.unit(index)
            interface = SimpleNamespace(function=unit.function, returns=unit.returns, parameters=(), globals=())
            for _value, name in expected:
                rows = self.seam.translator['clauses'](name, self.seam.values[name]['clauses'])
                profile = self.seam.src['harness_profile'](unit, interface, rows, {}, {}, (), (), (), {})
                self.assertEqual(profile['setup'], ('dws_prepare_receiver_v1();',))
                self.assertEqual(len(profile['draws']), 256)
                self.assertTrue(all(row['ctype'] == 'uint32_t' for row in profile['draws']))
                profiles.append(profile['draws'])
        self.assertTrue(all(rows == profiles[0] for rows in profiles))

    def test_wrong_direct_first_source_hash_refuses_before_capture(self):
        policy = copy.deepcopy(self.seam.policies[0]); policy['proof_source']['sha256'] = '0' * 64
        raw = REG.canonical(policy); self.seam.write('bad-policy.json', raw)
        self.seam.reference = {'root': 'library', 'path': 'bad-policy.json', 'sha256': REG.sha(raw)}
        selection = self.seam.src['SourceSelection'](self.seam.library, self.seam.entry['id'], self.root, self.seam.src['METHOD'])
        with self.assertRaisesRegex(self.seam.src['Refused'], 'exact registered source'):
            self.seam.src['source_policy'](selection, self.seam.src['Inputs'](self.seam.library))

    def test_all_five_contracts_pass_real_formal_metadata_frontdoor(self):
        contracts = {79: self.seam.values[REG.FUNCTIONS[0][2][0][1]], 80: self.seam.values[REG.FUNCTIONS[0][2][1][1]]}
        seam = BASE['MetadataSeam'](self.root, contracts)
        seam.library.entries = self.seam.values
        seam.library.files = self.seam.library.files
        seam.policy = {'unit_contracts': [row for policy in self.seam.policies for row in policy['unit_contracts']]}
        seam.source['UNIT_FUNCTIONS'] = self.seam.src['UNIT_FUNCTIONS']
        extract(OUT / 'dx100_checked_source.py', {'checked_unit_format'}, seam.source)
        seam.frame['__builtins__'] = protocol({('swdb', ('dx100_checked_source',)):
                                              SimpleNamespace(dx100_checked_source=SimpleNamespace(**seam.source))})
        extract(OUT / 'formal_frame.py', {'_entry'}, seam.frame)
        self.assertEqual(seam.problems(), [])
        self.assertEqual(len(seam.pending), 5)

    def test_legacy_capture_and_root_wp_hooks_remain_exact(self):
        name = 'complete_capture'
        old = (WHOLE / 'production-route-v3/proposed/swdb/dx100_checked_source.py').read_text()
        new = (OUT / 'dx100_checked_source.py').read_text()
        def node(text):
            value = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
            return ast.get_source_segment(text, value)
        self.assertEqual(node(old), node(new))
        inverse = json.loads((HERE / 'reviewed-hooks-rebased-inverse-v4.json').read_bytes())
        for filename, edits in inverse.items():
            # Before later integration, only the adapter retains one additional
            # explicit selection-coordinate forwarding change.
            text = (OUT / filename).read_text()
            if filename == 'cbmc_adapter.py':
                checked = json.loads((HERE / 'checked-unwind-inverse-v4.json').read_bytes())
                self.assertEqual(text.count(checked['after']), 1)
                text = text.replace(checked['after'], checked['before'], 1)
            if filename == 'dx100_checked_adapter.py':
                continue
            for edit in reversed(edits):
                self.assertEqual(text.count(edit['new']), edit['count'])
                text = text.replace(edit['new'], edit['old'], edit['count'])
            self.assertEqual(text.encode(), (HERE / 'base-source' / filename).read_bytes())
        setup = (OUT / 'proof_setup.py').read_text()
        self.assertIn('"standard_vector_member_view.py"', setup)
        self.assertIn('vector_qualified=vector_qualified', setup)

    def test_new_call_sites_bind_real_reviewed_signatures(self):
        selector = runpy.run_path(str(WHOLE / 'source-memory-selection-v1/source_memory_selection_v1.py'))
        runtime = runpy.run_path(str(WHOLE / 'runtime-projection-v4/runtime_projection_v4.py'))
        tree = ast.parse((OUT / 'dx100_checked_source.py').read_text())
        targets = {'memory_selection.selected_root': selector['selected_root'],
                   'memory_runtime.memory_object': runtime['memory_object']}
        seen = {name: 0 for name in targets}
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call): continue
            name = ast.unparse(call.func)
            if name not in targets: continue
            inspect.signature(targets[name]).bind(*[object() for _ in call.args],
                **{arg.arg: object() for arg in call.keywords})
            seen[name] += 1
        self.assertEqual(seen, {'memory_selection.selected_root': 2, 'memory_runtime.memory_object': 1})

    def test_native_roles_select_only_the_exact_physical_imported_producer(self):
        events = []
        def emission(role):
            def emitted(*args, **kwargs):
                events.append((role, args, kwargs))
                return {'cxx_text': '#include "dws_original_runtime.hpp"\n', 'runtime_header': 'protocol only',
                        'edit_manifest': {}, 'runtime_identity': {}}
            return emitted
        first = SimpleNamespace(__file__=str(OUT / '_dx100_whole/runtime_projection_v3.py'), projection=emission('first'))
        memory = SimpleNamespace(__file__=str(OUT / '_dx100_whole/runtime_projection_v4.py'), memory_projection=emission('memory'))
        self.seam.source.binder = SimpleNamespace(inventory=lambda _: ['explicit inventory protocol'])
        ns = {'source': self.seam.source, 'first': first, 'memory': memory, 'hashlib': hashlib, 'json': json, 'Path': Path}
        BASE['assignments'](OUT / 'dx100_checked_native.py', {'FIRST_SHA', 'MEMORY_SHA', 'FIRST_KIND', 'MEMORY_KIND'}, ns)
        extract(OUT / 'dx100_checked_native.py', {'view'}, ns)
        for index in range(4):
            unit = self.seam.unit(index); policy = copy.deepcopy(self.seam.policies[index])
            imported = first if index == 0 else memory
            path = Path(imported.__file__); raw = path.read_bytes()
            selected = {'kind': ns['FIRST_KIND'] if index == 0 else ns['MEMORY_KIND'],
                'producer': {'path': str(path), 'bytes': len(raw), 'sha256': REG.sha(raw)},
                'assertion_header': {'path': '/synthetic/assert.h', 'bytes': 1, 'sha256': 'a' * 64}}
            policy['native_projection'] = selected
            unit = type(unit)(**{**vars(unit), 'policy_json': REG.canonical(policy),
                'statement_preparation': {'assertion_header_pin': selected['assertion_header']},
                'receiver_preparation': SimpleNamespace(binding_json=b'{}', c_text='protocol only',
                    draw_plan_json=b'{}', integration_plan_json=b'{}'),
                'receiver_policy_pin_json': b'{}',
                'certificate_json': REG.canonical({'captured_source_path': str(self.root / 'original.cpp')}),
                'allocations': (), 'normalized_tu': {'synthetic': True}})
            ns['view'](unit)
            role, args, kwargs = events[-1]
            self.assertEqual(role, 'first' if index == 0 else 'memory')
            self.assertEqual(kwargs.get('function'), None if index == 0 else unit.function)
            self.assertEqual(args, (path.parent, self.root))
            self.assertEqual(kwargs['source_path'], self.root / 'original.cpp')
            for mutation in ('kind', 'alias', 'sha', 'missing', 'extra'):
                changed = copy.deepcopy(policy)
                if mutation == 'kind': changed['native_projection']['kind'] = 'unreviewed'
                elif mutation == 'sha': changed['native_projection']['producer']['sha256'] = '0' * 64
                elif mutation == 'missing': changed['native_projection'].pop('producer')
                elif mutation == 'extra': changed['native_projection']['renderer'] = 'unreviewed'
                else:
                    alias = self.root / ('same-bytes-' + str(index)); alias.write_bytes(raw)
                    changed['native_projection']['producer']['path'] = str(alias)
                bad = type(unit)(**{**vars(unit), 'policy_json': REG.canonical(changed)})
                count = len(events)
                with self.assertRaises((ValueError, KeyError)):
                    ns['view'](bad)
                self.assertEqual(len(events), count)

    def test_all_promoted_python_consumers_are_in_fixed_producer_closure(self):
        names = {'compiler': 'compiler_unit_adapter_v3.py', 'codec': 'lossless_gzip_v1.py',
                 'model': 'model_primitives.py', 'receiver': 'receiver_state_draws_v2.py',
                 'memory_receiver': 'receiver_memory_v1.py', 'staging': 'source_argument_staging_v2.py',
                 'dispatch': 'source_dispatch_v3.py', 'globals_observer': 'source_program_globals_v1.py',
                 'statements': 'source_statements_v2.py', 'binder': 'whole_interface_v4.py',
                 'unit_registry': 'unit_policy_registry_v2.py', 'memory_selection': 'source_memory_selection_v1.py',
                 'memory_runtime': 'runtime_projection_v4.py', 'resources': 'resource_profile_v2.py'}
        ns = {'Path': Path, '__file__': str(OUT / 'dx100_checked_source.py'), 'need': self.seam.src['need'],
              'contracts': SimpleNamespace(__file__=str(OUT / 'dx100_whole_checked.py'))}
        ns.update({name: SimpleNamespace(__file__=str(OUT / '_dx100_whole' / file)) for name, file in names.items()})
        imported = {name: SimpleNamespace(__file__=str(OUT / '_dx100_whole' / (name + '.py'))) for name in
                    ('normalized_capture_ingress_v2', 'closed_python_surface', 'role_normalized_gzip_v2',
                     'lossless_gzip_v2', 'runtime_projection_v3', 'normalized_compiler_adapter_v1')}
        ns['__builtins__'] = protocol({('swdb._dx100_whole', ('normalized_capture_ingress_v2',)):
            SimpleNamespace(normalized_capture_ingress_v2=imported['normalized_capture_ingress_v2']),
            ('swdb._dx100_whole', ('closed_python_surface', 'role_normalized_gzip_v2', 'lossless_gzip_v2')):
                SimpleNamespace(**{key: imported[key] for key in ('closed_python_surface', 'role_normalized_gzip_v2', 'lossless_gzip_v2')}),
            ('swdb._dx100_whole', ('runtime_projection_v3', 'normalized_compiler_adapter_v1')): SimpleNamespace(runtime_projection_v3=imported['runtime_projection_v3'], normalized_compiler_adapter_v1=imported['normalized_compiler_adapter_v1'])})
        BASE['assignments'](OUT / 'dx100_checked_source.py', {'ROUTE_PRODUCERS'}, ns)
        extract(OUT / 'dx100_checked_source.py', {'producer_paths'}, ns)
        paths = ns['producer_paths']()
        actual = {path for path in OUT.rglob('*.py')}
        self.assertLessEqual(actual, set(paths.values()))
        self.assertIn(OUT / '__init__.py', paths.values())
        self.assertIn(OUT / '_dx100_whole/__init__.py', paths.values())
        self.assertEqual(len(paths), len(set(paths.values())))

    def builder(self):
        return SimpleNamespace(**runpy.run_path(str(HERE / 'profile/profile_builder_v3.py')))

    def resource_source(self):
        resources = SimpleNamespace(**runpy.run_path(str(OUT / '_dx100_whole/resource_profile_v2.py')))
        class Unit:
            pass
        namespace = {'SourceUnit': Unit, 'resources': resources, 'need': self.seam.src['need'],
            'contracts': SimpleNamespace(COMPONENTS=resources.COMPONENTS), 'unit_registry': REG,
            'SOURCE_SHA': resources.SOURCE_SHA, 'FUNCTION': resources.FUNCTION,
            'UNIT_FUNCTIONS': tuple(row[0] for row in REG.FUNCTIONS)}
        extract(OUT / 'dx100_checked_source.py', {'resource_selection', 'unit_resource_profile'}, namespace)
        unit = Unit(); unit.function = resources.FUNCTION
        unit.certificate = {'source_sha256': resources.SOURCE_SHA, 'resource_profile': resources.select(
            resources.SOURCE_SHA, resources.FUNCTION, dict(resources.COMPONENTS))}
        return namespace, unit

    def test_real_checked_cbmc_flag_branch_uses_exact_owner_bounds_and_old_path_unchanged(self):
        source, unit = self.resource_source(); helpers = ('dxm_cover', 'dxp_find', 'dxm_cpu_write', 'dxm_device_write')
        source['model_fields'] = lambda _unit: {'functions': helpers}
        adapter_ns = {'source': SimpleNamespace(**source)}
        extract(OUT / 'dx100_checked_adapter.py', {'helper_loop_bounds'}, adapter_ns)
        tree = ast.parse((OUT / 'cbmc_adapter.py').read_text())
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == '_cbmc')
        branch = next(node for node in method.body if isinstance(node, ast.If) and ast.unparse(node.test) == 'code.model is not None')
        def run(whole, actual):
            module = SimpleNamespace(model_loops=lambda *_args: list(actual), helper_loop_bounds=adapter_ns['helper_loop_bounds'])
            namespace = {'self': SimpleNamespace(_model_loops=lambda *_args: ['old_helper.0']), 'tools': {}, 'scratch': None,
                'context': {'settings': {}}, 'code': SimpleNamespace(model=SimpleNamespace(unwind=7),
                    lowering=SimpleNamespace(whole_source=whole)), 'flags': ['--unwinding-assertions']}
            namespace['__builtins__'] = protocol({('swdb', ('dx100_checked_adapter',)): SimpleNamespace(dx100_checked_adapter=module)})
            exec(compile(ast.Module(body=[branch], type_ignores=[]), '<real-checked-cbmc-loop-flag-branch>', 'exec'), namespace)
            return namespace
        checked = run(unit, ['dxm_cover.8', 'dxp_find.1', 'dxm_cpu_write.0', 'dxm_device_write.1'])
        self.assertEqual(checked['flags'], ['--unwinding-assertions', '--unwindset', 'dxm_cover.8:20481,dxp_find.1:513,dxm_cpu_write.0:1025,dxm_device_write.1:1025'])
        self.assertEqual([row['unwind'] for row in checked['context']['settings']['whole_source_actual_helper_loop_bounds']], [20481, 513, 1025, 1025])
        self.assertEqual(run(None, [])['flags'], ['--unwinding-assertions', '--unwindset', 'old_helper.0:7'])
        with self.assertRaises(ValueError): run(unit, ['unknown.0'])
        with self.assertRaises(ValueError): run(unit, ['dxm_cover.0', 'dxm_cover.0'])
        with self.assertRaises(ValueError): run(unit, ['dxm_cover.0', 'dxp_find.0'])

    def test_real_loop_observer_keeps_same_job_role_full_inventory_and_refuses_empty_or_unknown(self):
        helpers = ('dxm_cover', 'dxm_cpu_write', 'dxm_device_write', 'dxp_find')
        expected_command = []; launches = []; result = SimpleNamespace(returncode=0, stdout='', stderr='')
        def run(argv, **kwargs): expected_command.append((argv, kwargs)); return result
        def launch(_adapter, _job, _context, roles): launches.append(roles)
        source = SimpleNamespace(need=self.seam.src['need'], model_fields=lambda _unit: {'functions': helpers})
        namespace = {'source': source, 'Path': Path, 're': re, 'check_launch': launch, 'subprocess': SimpleNamespace(run=run),
            '__builtins__': protocol({('swdb', ('cbmc_adapter',)): SimpleNamespace(cbmc_adapter=SimpleNamespace(FROZEN=['--unwinding-assertions']))})}
        extract(OUT / 'dx100_checked_adapter.py', {'model_loops'}, namespace)
        tools = {'command': ['/pinned/cbmc'], 'flags': ['--unwinding-assertions']}
        unit = SimpleNamespace(function=REG.FUNCTIONS[0][0]); context = {'job': object(), 'out': self.root, 'reports': [], 'settings': {}}
        result.stdout = 'Loop dxm_cover.8:\nLoop dxm_cpu_write.0:\nLoop dxm_device_write.1:\nLoop swdb_run.0:\n'
        rows = namespace['model_loops'](object(), tools, self.root, unit, context)
        self.assertEqual(rows, ['dxm_cover.8', 'dxm_cpu_write.0', 'dxm_device_write.1'])
        self.assertEqual(context['settings']['whole_source_actual_loop_ids'], [*rows, 'swdb_run.0'])
        self.assertEqual(launches, [[('c', self.root / 'job.c')], [('c', self.root / 'job.c')]])
        self.assertEqual(expected_command[0][0], ['/pinned/cbmc', 'job.c', '-DSWDB_CBMC', '--unwinding-assertions', '--show-loops'])
        self.assertEqual(expected_command[0][1]['cwd'], self.root)
        for stdout in ('', 'Loop unknown.0:\n', 'Loop dxm_cover.0:\nLoop dxm_cover.0:\n', 'Loop swdb_run.0:\n'):
            result.stdout = stdout
            with self.assertRaises(ValueError): namespace['model_loops'](object(), tools, self.root, unit, context)

    def test_same_resource_profile_reaches_assembly_composition_and_method_identity(self):
        namespace, unit = self.resource_source(); profile = namespace['unit_resource_profile'](unit)
        self.assertEqual(profile['structural_node_budget'], 828)
        compose = next(node for node in ast.parse((OUT / 'dx100_checked_source.py').read_text()).body
                       if isinstance(node, ast.FunctionDef) and node.name == 'compose')
        builder = next(node for node in ast.parse((HERE / 'profile/profile_builder_v3.py').read_text()).body
                       if isinstance(node, ast.FunctionDef) and node.name == 'derive')
        for node in (compose, builder):
            prefix = [call for call in ast.walk(node) if isinstance(call, ast.Call) and ast.unparse(call.func).endswith('resources.prefix')]
            self.assertEqual(len(prefix), 1)
            self.assertEqual(ast.unparse(prefix[0].args[0]), 'resource_profile')
        text = (OUT / 'dx100_checked_source.py').read_text()
        self.assertIn("assembly['entry']['model'].get('resource_profile') == resource_profile", text)
        self.assertIn("'resource_profile': resource_profile", text)
        for value in (79, 80):
            # The expected postcondition is never an input to resource selection.
            unit.expected_result = value
            self.assertEqual(namespace['unit_resource_profile'](unit), profile)
        bad = copy.copy(unit); bad.certificate = {**unit.certificate, 'resource_profile': None}
        with self.assertRaises(ValueError): namespace['unit_resource_profile'](bad)

    def test_real_refusal_handler_no_longer_reads_removed_native_projection_alias(self):
        class Refused(ValueError): pass
        source = SimpleNamespace(need=lambda value, message: None if value else (_ for _ in ()).throw(Refused(message)),
            Refused=Refused, DEFINES=('NUM_CORES=4', 'TILE_SIZE=16384'))
        module = SimpleNamespace()
        namespace = {'source': source, 'native': module,
            'subprocess': SimpleNamespace(TimeoutExpired=type('TimeoutExpired', (Exception,), {})),
            'c_lowering': SimpleNamespace(LoweringError=type('LoweringError', (ValueError,), {})),
            'tr': SimpleNamespace(Untranslatable=type('Untranslatable', (ValueError,), {}))}
        namespace['__builtins__'] = protocol({('swdb', ('cbmc_adapter',)): SimpleNamespace(cbmc_adapter=SimpleNamespace())})
        adapter = SimpleNamespace(defines=source.DEFINES, _not_proven=lambda *args: args)
        job = SimpleNamespace(bounds={'threads': 2})
        extract(WHOLE / 'production-route-v3/proposed/swdb/dx100_checked_adapter.py', {'run'}, namespace)
        with self.assertRaises(AttributeError): namespace['run'](adapter, job, {}, {'settings': {}}, None, None)
        extract(OUT / 'dx100_checked_adapter.py', {'run'}, namespace)
        result = namespace['run'](adapter, job, {}, {'settings': {}}, None, None)
        self.assertEqual(result[0], 'unsupported_construct')

    def test_real_registry_attachment_keeps_ready_bytes_and_unprepared_memory_refuses_before_reads(self):
        builder = self.builder(); policy = copy.deepcopy(self.seam.policies[0])
        completed = {'files': {'proof_semantics/dx100_whole/source-policy.json': REG.canonical(policy),
            'proof_semantics/dx100_bfs_0_2.yaml': REG.canonical({'kind': 'proof_semantics', 'checked_body': {}, 'rules': []}),
            'proof_semantics/dx100_whole/assembly.json': b'{"synthetic":"not an actual model"}'}}
        for row in policy['unit_contracts']:
            completed['files']['rewrite_contracts/' + row['id'] + '.yaml'] = self.seam.contracts[row['id']]
        memory = self.root / 'proof_units/same_thread_memory_v1.cpp'
        memory.write_bytes((WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp').read_bytes())
        attachment = dict(builder.attach_registry.__globals__)
        attachment['__builtins__'] = protocol({('swdb._dx100_whole', ('unit_policy_registry_v2',)):
            SimpleNamespace(unit_policy_registry_v2=REG)})
        extract(HERE / 'profile/profile_builder_v3.py', {'attach_registry'}, attachment)
        attached = attachment['attach_registry'](completed, self.root)
        for name, raw in completed['files'].items():
            if not name.endswith('dx100_bfs_0_2.yaml'): self.assertEqual(attached['files'][name], raw)
        for name, raw in attached['files'].items(): self.seam.write(name, raw)
        self.seam.reference = attached['unit_registry']; self.seam.library = self.seam.Library(self.root)
        reads = self.seam.src['Inputs'](self.seam.library)
        loaded = self.seam.consumer['load'](self.seam.library, reads, self.seam.reference)
        self.assertEqual((len(loaded.policy_documents), len(loaded.contract_documents)), (4, 5))
        selected = self.seam.src['source_policy'](self.seam.selection(0), self.seam.src['Inputs'](self.seam.library))
        self.assertEqual(selected[2], policy)
        self.assertNotIn('prepared', next(json.loads(raw)['capture'] for _sha, raw in loaded.policy_documents
                                         if json.loads(raw)['function'] != REG.FUNCTIONS[0][0]))
        source = SimpleNamespace(CAPTURE_KIND='lossless-complete-original-tu-v1', need=self.seam.src['need'])
        namespace = {'source': source, 'KIND': 'complete-original-tu-paired-type-gzip-2'}
        extract(OUT / '_dx100_whole/normalized_capture_ingress_v2.py', {'need', 'exact', 'complete_capture'}, namespace)
        class NoScientificReads:
            def __getattr__(self, name): raise AssertionError('unready profile attempted scientific read: ' + name)
        unready = []
        for _sha, raw in loaded.policy_documents:
            value = json.loads(raw)
            if value['function'] == REG.FUNCTIONS[0][0]: continue
            self.assertEqual(value['capture']['kind'], 'unsupported-unprepared-memory-profile-1')
            self.assertEqual(json.loads(attached['files'][value['receiver_selection']['path']])['schema'], 'unprepared-memory-source-profile-1')
            with self.assertRaises(ValueError): namespace['complete_capture'](value, NoScientificReads(), self.root)
            unready.append(value['capture'])
        self.assertEqual(len(unready), 3); self.assertTrue(all(row == unready[0] for row in unready))
        memory.write_bytes(b'changed')
        with self.assertRaises(ValueError): attachment['attach_registry'](completed, self.root)

    def normalized_capture(self):
        schema = json.loads((WHOLE / 'normalized-ingress-v1/capture-schema-v1.json').read_bytes())
        pin = lambda name: {'path': str(self.root / name), 'bytes': 1, 'sha256': hashlib.sha256(name.encode()).hexdigest()}
        return {'kind': schema['kind'], 'original': {name: pin('original-' + name) for name in schema['original_keys']},
                'transform': {name: pin('transform-' + name) for name in schema['transform_keys']},
                'prepared': pin('prepared')}

    def test_profile_capture_roles_preserve_original_and_derived_identities(self):
        builder = self.builder(); capture = self.normalized_capture()
        roles = builder.capture_roles(capture)
        self.assertEqual(roles['storage'], capture['transform']['normalized_gzip'])
        self.assertEqual(roles['observation'], capture['original']['observation'])
        self.assertEqual(roles['raw_abi'], capture['original']['abi'])
        self.assertNotEqual(roles['storage'], capture['original']['compressed_tu'])
        for name in ('kind', 'original', 'transform', 'prepared'):
            altered = copy.deepcopy(capture); altered.pop(name)
            with self.assertRaises((builder.Refused, KeyError)):
                builder.capture_roles(altered)
        for changes in ({'kind': 'unknown'}, {'extra': True}):
            with self.assertRaises(builder.Refused):
                builder.capture_roles({**capture, **changes})

    def test_profile_raw_abi_comparison_red_derived_observation_green(self):
        builder = self.builder()
        original = b'exact source bytes'; source_path = self.root / 'captured.cpp'; source_path.write_bytes(original)
        raw_abi = self.root / 'raw-abi.json'; raw_abi.write_bytes(b'{"Clang":"raw AST"}')
        observation = {'schema': 'derived ABI observation protocol', 'abi': {'word': 32}}
        observed = self.root / 'derived-abi.json'; observed.write_bytes(builder.canonical(observation))
        raw_pin = builder.pin(raw_abi, raw_abi.read_bytes()); derived_pin = builder.pin(observed, observed.read_bytes())
        compiler_observation = {'path': '/synthetic/original-observation', 'bytes': 1, 'sha256': 'c' * 64}
        storage = {'path': '/synthetic/original-gzip', 'bytes': 1, 'sha256': 'd' * 64}
        header = {'path': '/synthetic/assert.h', 'bytes': 1, 'sha256': 'a' * 64}
        capture = {'kind': 'lossless-complete-original-tu-v1', 'compressed_tu': storage,
                   'abi': raw_pin, 'observation': compiler_observation, 'result': {}}
        receiver = {'inputs': {'source': builder.pin(source_path, original), 'full_tu': storage,
            'capture_receipt': compiler_observation, 'assertion_header': header, 'abi_observation': derived_pin}}
        # Execute the actual old producer's exact need-expression at the seam.
        old_path = WHOLE / 'public-profile-builder-v2/profile_builder_v2.py'
        old = next(node for node in ast.parse(old_path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'assemble')
        call = next(node for node in ast.walk(old) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'need' and node.args and isinstance(node.args[-1], ast.Constant)
                    and node.args[-1].value == 'receiver source/storage/ABI/capture/assertion selection differs')
        ns = {'need': builder.need, 'pin': builder.pin, 'selected_receiver': receiver, 'captured_path': source_path,
              'original': original, 'request': {'capture': capture, 'assertion_header': header}}
        with self.assertRaises(builder.Refused):
            eval(compile(ast.Expression(call), str(old_path), 'eval'), ns)
        builder.check_receiver_compiler_projection(receiver, capture, {'abi_observation': observation}, source_path, original, header)
        substituted = copy.deepcopy(receiver); substituted['inputs']['abi_observation'] = raw_pin
        with self.assertRaises(builder.Refused):
            builder.check_receiver_compiler_projection(substituted, capture, {'abi_observation': observation}, source_path, original, header)
        normalized = self.normalized_capture(); normalized['original']['observation'] = compiler_observation
        normalized['original']['abi'] = raw_pin; normalized['transform']['normalized_gzip'] = {**storage, 'path': '/synthetic/normalized-gzip'}
        receiver['inputs']['full_tu'] = normalized['transform']['normalized_gzip']
        builder.check_receiver_compiler_projection(receiver, normalized, {'abi_observation': observation}, source_path, original, header)

    def test_profile_capture_metadata_supports_closed_physical_or_portable_pins(self):
        builder = self.builder(); raw = b'{"metadata":true}'
        file = self.root / 'physical.json'; file.write_bytes(raw)
        library = builder.LibraryRoot(self.root, self.root)
        self.assertEqual(builder.selected(library, builder.pin(file, raw)), raw)
        self.assertEqual(builder.selected(library, {'root': 'library', 'path': file.name, 'sha256': builder.sha(raw)}), raw)
        for row in ({'path': str(file)}, {'root': 'other', 'path': file.name, 'sha256': builder.sha(raw)}):
            with self.assertRaises(builder.Refused): builder.selected(library, row)

    def test_profile_formatter_and_planner_are_the_reviewed_exact_functions(self):
        current = (HERE / 'profile/profile_builder_v3.py').read_text()
        prior = (WHOLE / 'public-profile-builder-v2/profile_builder_v2.py').read_text()
        def node(text, name):
            value = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
            return ast.get_source_segment(text, value)
        self.assertEqual(node(current, 'unit_contracts'), node(prior, 'unit_contracts'))
        self.assertEqual((HERE / 'profile/pair_plan_v2.py').read_bytes(),
                         (WHOLE / 'public-profile-planner-v2/pair_plan_v2.py').read_bytes())
        builder = self.builder(); rows = builder.contract_rows(builder.unit_contracts(self.seam.policies[0]['proof_source']))
        planner = runpy.run_path(str(HERE / 'profile/pair_plan_v2.py'))
        selection = {name: '/admitted/' + name for name in ('python', 'original_project', 'producer_project', 'records',
            'runs', 'verifier_lock', 'pycache', 'compiler_wrapper', 'cbmc')}
        selection['library_root'] = '/admitted/library'
        selection['root_admission_receipt'] = {'path': '/admitted/root.json', 'bytes': 1, 'sha256': 'a' * 64}
        profile = {'contracts': rows, 'semantics_content_sha256': 's' * 64,
                   'method_content_sha256': 'm' * 64, 'producer_manifest_sha256': 'p' * 64}
        result = planner['plan'](profile, selection)
        self.assertEqual(len(result['jobs']), 2)
        for job in result['jobs']:
            self.assertIn('--method-version', job['argv'])
            self.assertEqual(job['argv'].count('--define'), 2)
            self.assertIn('NUM_CORES=4', job['argv']); self.assertIn('TILE_SIZE=16384', job['argv'])
        self.assertEqual(result['environment']['SWDB_HOME'], '/admitted/original_project')
        self.assertEqual(result['environment']['PYTHONPATH'], '/admitted/producer_project')

    def test_profile_basis_is_complete_acyclic_and_builder_pin_is_exact(self):
        builder = self.builder(); root = HERE / 'profile'
        raw = (root / 'normal-producer-basis-v4.json').read_bytes()
        self.assertEqual(builder.sha(raw), builder.BASIS_SHA)
        rows = json.loads(raw)['files']
        by_name = {row['relative']: row for row in rows}
        for path in OUT.rglob('*'):
            if not path.is_file(): continue
            name = 'swdb/' + path.relative_to(OUT).as_posix(); row = by_name[name]
            self.assertEqual((row['bytes'], row['sha256']), (path.stat().st_size, builder.sha(path.read_bytes())))
        self.assertFalse(any('profile_builder' in row['relative'] for row in rows))
        prepare = ast.parse((root / 'profile_prepare_v3.py').read_text())
        pinned = next(ast.literal_eval(node.value) for node in prepare.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == 'BUILDER_SHA' for target in node.targets))
        self.assertEqual(pinned, builder.sha((root / 'profile_builder_v3.py').read_bytes()))
        self.assertIn("'abi-observation.json': builder.canonical(derived['prepared']['abi_observation'])",
                      (root / 'profile_prepare_v3.py').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
