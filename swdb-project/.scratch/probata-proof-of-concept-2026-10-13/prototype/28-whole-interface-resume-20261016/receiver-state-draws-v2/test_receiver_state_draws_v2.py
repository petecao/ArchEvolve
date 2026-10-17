"""2026-10-16 ET. Synthetic metadata/refusal controls; no scientific execution."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


def deny(event, _args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('receiver controls refuse ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
name = 'owned_inert_receiver_preparation_v2'
module = types.ModuleType(name)
sys.modules[name] = module
exec(compile(ast.parse((HERE / 'receiver_state_draws_v2.py').read_bytes()), str(HERE / 'receiver_state_draws_v2.py'), 'exec'), module.__dict__)
M = module


def pin(path):
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-controls-', dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.owner = 'synthetic-no-admission-test-owner'
        self.physical = {}
        for role in sorted(M.PHYSICAL_ROLES):
            path = self.root / role
            path.write_bytes(('synthetic physical input: ' + role).encode())
            self.physical[role] = pin(path)
        self.frozen = {name: pin(PROJECT / 'swdb/cbmc_translator.py' if name == 'harness/cbmc_translator.py' else WHOLE / name) for name in M.FROZEN}
        self.inputs = {'source': pin(WHOLE / 'source_call_fixture_v2.cpp')}
        for key in ('abi_observation', 'capture_receipt', 'assertion_header'):
            self.inputs[key] = self.put(key, {'synthetic_protocol_only': key})
        tu = {'kind': 'TranslationUnitDecl', 'synthetic_protocol_only': True}
        self.tu_sha = M.object_sha(tu)
        self.inputs['full_tu'] = self.put('full_tu', tu)
        numeric = {name: {'value': 0, 'policy': policy} for name, policy in M.FLAGS.items()}
        self.runtime = {'schema': 'whole-interface-runtime-selection-1',
            'evidence_kind': 'selected-configuration-and-owned-numeric-policies', 'owner': self.owner,
            'physical_inputs_sha256': M.object_sha(self.physical), 'numeric_flags': numeric}
        self.inputs['runtime_receipt'] = self.put('runtime_receipt', self.runtime)
        self.allocations = []
        objects = []
        source = (WHOLE / 'source_call_fixture_v2.cpp').read_text()
        for index, (local, dtype, physical) in enumerate((('data', 0, 4096), ('limits', 1, 8192))):
            declaration = source.index(local + '[2]')
            declaration_sha = hashlib.sha256(('synthetic declaration ' + local).encode()).hexdigest()
            allocation = {'object_index': index, 'object_id': local, 'caller': 'whole_interface_source_fixture',
                'local_id': 'synthetic-' + local, 'declaration_sha256': declaration_sha,
                'declaration_range': [declaration, source.index(';', declaration)], 'scope_end_offset': len(source) - 2,
                'allocation_thread': 0, 'allocation_origin': 'checked-original-automatic-declaration'}
            self.allocations.append(allocation)
            objects.append({'object_id': local, 'guest_base': physical, 'physical_base': physical,
                'extent': 2, 'dtype': dtype,
                'source_pin': M.object_sha({'source_sha256': M.SOURCE_SHA, 'caller': allocation['caller'],
                    'local_id': allocation['local_id'], 'declaration_sha256': declaration_sha}),
                'base_cell': index * 2, 'cell_ids': [index * 2, index * 2 + 1]})
        self.atlas = {'schema': 'source-ordinary-cell-atlas-1', 'objects': objects,
            'cells': [{'cell': obj['base_cell'] + lane, 'physical_begin': obj['physical_base'] + lane * 4,
                'physical_end': obj['physical_base'] + (lane + 1) * 4, 'dtype': obj['dtype']}
                for obj in objects for lane in range(obj['extent'])],
            'mmio_excluded_span': [17179869184, 17179869184 + 8 * 32 * 16384 + 4 * 32 + 4 * 32 + 24],
            'initialization_granted': False, 'history_events_added': 0,
            'owned_premises': ['source object identity/lifetime', 'guest→physical projection', 'complete CPU-access instrumentation'],
            'public_admission': False}
        self.inputs['source_atlas'] = self.put('source_atlas', self.atlas)
        self.budget = 128
        code = M.choice_hook_prefix(self.budget) + '\n' + '\n'.join((WHOLE / name).read_text() for name in M.FROZEN if name.endswith('.h'))
        self.assembly = {'entry': {'kind': 'proof_semantics', 'target': 'dx100-mmio', 'contract_form': M.MODEL_KIND,
            'public_admission': False, 'source_preconditions_assumed': False,
            'model': {'sha256': hashlib.sha256(code.encode()).hexdigest(), 'source_atlas_sha256': M.object_sha(self.atlas),
                'source_inputs': list(self.frozen.values())},
            'harness_draws': {'object': 'dws_choice_table', 'scalar_type': 'uint32_t', 'count': self.budget,
                'independent': True, 'draw_before_source_unit': True}},
            'c_text': code, 'instances': [], 'atlas': self.atlas}
        self.inputs['model_assembly'] = self.put('model_assembly', self.assembly)
        text = 'uint32_t dws_source_program(unsigned owned_thread) { /* synthetic shape only */ return 0; }\n'
        self.statements = {'schema': 'whole-interface-source-statements-1', 'text': text,
            'generated_c_sha256': hashlib.sha256(text.encode()).hexdigest(), 'original_full_tu_sha256': self.tu_sha,
            'original_source_sha256': M.SOURCE_SHA, 'assertion_header_pin': self.inputs['assertion_header']}
        self.inputs['statement_preparation'] = self.put('statement_preparation', self.statements)
        self.context = {'schema': 'whole-interface-program-context-1', 'owner': self.owner,
            'source_kind': M.SOURCE_KIND, 'model_kind': M.MODEL_KIND, 'profile': M.PROFILE,
            'execution_mode': 'fresh-cxx-program-globals', 'bindings': {},
            'physical_inputs_sha256': M.object_sha(self.physical), 'modeled_threads': 2,
            'numeric_flags': {name: dict(row, runtime_receipt_sha256=self.inputs['runtime_receipt']['sha256'])
                for name, row in numeric.items()},
            'premises': [{'rule': rule, 'statement': M.PREMISES[rule], 'owner': self.owner, 'record_assumption': True}
                for rule in sorted(M.PREMISES)], 'ordinary_allocations': self.allocations}
        self.observation = self.global_observation()
        self.policy = {'schema': 'whole-interface-receiver-selection-1', 'selection_owner': self.owner,
            'source_kind': M.SOURCE_KIND, 'model_kind': M.MODEL_KIND, 'profile': M.PROFILE,
            'inputs': self.inputs, 'context_receipt': {}, 'physical_inputs': self.physical,
            'frozen_inputs': self.frozen, 'choice_budget': self.budget, 'modeled_threads': 2,
            'full_tu_canonical_sha256': self.tu_sha}

    def put(self, name, value):
        path = self.root / (name + '.json')
        path.write_bytes(M.canonical(value))
        return pin(path)

    def global_observation(self):
        rows = []
        for index, (name, (header, typ, _receiver)) in enumerate(sorted(M.GLOBALS.items())):
            path = PROJECT / 'apps/dx100/benchmarks/API' / header
            rows.append({'name': name, 'declaration_id': 'synthetic-' + name,
                'actual_type': {'qualType': typ}, 'source_type': typ, 'source_range': [index, index + 1],
                'header_path': str(path), 'header_sha256': pin(path)['sha256'],
                'declaration_sha256': hashlib.sha256(('synthetic global ' + name).encode()).hexdigest(),
                'CXX_static_initialization': 'null pointer' if '*' in typ else 'zero scalar',
                'source_initial_value': None if '*' in typ else 0, 'model_host_receiver_relation': M.global_relation(name)})
        out = {'schema': 'whole-interface-source-program-globals-1', 'execution_mode': 'fresh-cxx-program-globals',
            'program_context_receipt_sha256': '', 'globals': rows, 'full_tu_sha256': self.tu_sha}
        for name in ('fresh_program_interpretation_requires_root_admission', 'pointer_null_is_source_semantic_value_not_raw_bit_claim',
                     'model_host_mapping_requires_derived_setup_state', 'instruction_pointer_offsets_apply_only_after_alloc_not_to_null_initial_values'):
            out[name] = True
        for name in ('model_reset_called', 'alloc_MAA_called', 'init_MAA_called', 'device_payload_initializedness_granted',
                     'device_ownership_granted', 'preexisting_command_history_cleared', 'device_receiver_state_bound', 'public_admission'):
            out[name] = False
        return out

    def selection(self):
        # The context precedes its observation; no self-referential receipt hash.
        self.context['bindings'] = {name: row['sha256'] for name, row in self.inputs.items() if name != 'source_globals'}
        self.policy['context_receipt'] = self.put('context', self.context)
        self.observation['program_context_receipt_sha256'] = self.policy['context_receipt']['sha256']
        self.inputs['source_globals'] = self.put('source_globals', self.observation)
        return M.OwnedSelection(M.Pin.parse(self.put('selected_policy', self.policy)))

    def run_prepare(self):
        return M.prepare(self.selection())

    def test_01_synthetic_preparation_binds_all_twelve_without_claiming_observation(self):
        output = self.run_prepare()
        binding = json.loads(output.binding_json)
        self.assertEqual(len(binding['host_globals']), 12)
        self.assertEqual(binding['initial_receiver']['tile_register_owner'], -1)
        self.assertEqual(binding['initial_receiver']['ordinary_initialized'], 0)
        self.assertEqual(len(binding['record_assumptions']), 6)
        self.assertIn('not a hardware refinement theorem', binding['scope'])
        self.assertEqual(output, self.run_prepare())

    def test_02_missing_or_self_authorized_context_refuses(self):
        for field, value in (('profile', 'fresh-cxx-program-globals'), ('execution_mode', 'reused-state'),
                             ('owner', 'another-owner'), ('premises', [])):
            saved = copy.deepcopy(self.context)
            self.context[field] = value
            with self.assertRaises(M.Refused):
                self.run_prepare()
            self.context = saved
        self.context['admitted'] = True
        with self.assertRaises(M.Refused):
            self.run_prepare()
        with self.assertRaises(M.Refused):
            M.prepare(True)

    def test_03_each_owned_premise_is_exact_and_recorded(self):
        for index in range(len(self.context['premises'])):
            saved = copy.deepcopy(self.context['premises'][index])
            for field, value in (('record_assumption', False), ('owner', 'different'), ('statement', 'static globals prove an empty device')):
                self.context['premises'][index] = dict(saved, **{field: value})
                with self.assertRaises(M.Refused):
                    self.run_prepare()
            self.context['premises'][index] = saved

    def test_04_globals_offsets_census_and_device_non_grants_are_closed(self):
        base = copy.deepcopy(self.observation)
        for mutate in (lambda x: x['globals'].pop(), lambda x: x['globals'].reverse(),
            lambda x: x['globals'][0].update(source_initial_value=8),
            lambda x: x['globals'][0].update(model_host_receiver_relation={'kind': 'source host field', 'model_field': 'dxs_mmio[5]+8'}),
            lambda x: x.update(device_payload_initializedness_granted=True),
            lambda x: x.update(preexisting_command_history_cleared=True)):
            self.observation = copy.deepcopy(base)
            mutate(self.observation)
            with self.assertRaises(M.Refused):
                self.run_prepare()

    def test_05_no_resets_payload_writes_or_assumptions_emitted(self):
        text = self.run_prepare().c_text
        self.assertNotRegex(text, r'\b(?:dxc_reset|dxm_reset|dxs_alloc|dxs_init|alloc_MAA|init_MAA|__CPROVER_assume)\s*\(')
        self.assertNotRegex(text, r'\b(?:dxm_memory|dxm_events|dxm_nodes|dxp_image)\s*\[')
        self.assertNotRegex(text, r'\b(?:dxm_count|dxm_event_count|dxc_count|dxc_constructing|dxa_count|dxp_count|dws_choice_used)\s*=[^=]')
        self.assertIn('dxm_initialized[i]==0', text)
        self.assertIn('dxg_image[i].initialized==0', text)
        self.assertIn('dxz_sizes[i]=UINT_MAX', text)
        self.assertIn('dxm_tile_owner[i]=-1', text)
        self.assertIn('dxg_owner[i]=-1', text)

    def test_06_ordinary_origin_does_not_forbid_another_admitted_thread(self):
        text = self.run_prepare().c_text
        require = text.split('static void dws_local_require_v1', 1)[1].split('\n}', 1)[0]
        self.assertIn('accessing_thread<2u', require)
        self.assertIn('dws_local_live_v1[object]==1', require)
        self.assertIn('dws_local_origin_v1[object]>=0', require)
        self.assertNotRegex(require, r'origin_v1\[object\]\s*==\s*\(?int\)?\s*accessing_thread')
        self.assertNotIn('==accessing_thread', require)
        self.assertIn('dws_source_object_leave(0u)', text)
        plan = json.loads(self.run_prepare().integration_plan_json)
        self.assertIn('every original CPU access', plan['ordinary_access'])
        self.assertIn('no origin-thread equality', plan['ordinary_access'])

    def test_07_allocation_alias_reuse_bad_origin_and_false_registration_refuse(self):
        original = copy.deepcopy(self.context['ordinary_allocations'])
        for field, value in (('allocation_origin', 'source-registration'), ('local_id', 'wrong-local'),
                             ('object_index', 99), ('allocation_thread', 2), ('declaration_range', [5, 2])):
            self.context['ordinary_allocations'] = copy.deepcopy(original)
            self.context['ordinary_allocations'][0][field] = value
            with self.assertRaises(M.Refused):
                self.run_prepare()
        self.context['ordinary_allocations'] = original
        atlas = copy.deepcopy(self.atlas)
        atlas['objects'][1]['physical_base'] = atlas['objects'][0]['physical_base']
        with self.assertRaises(M.Refused):
            M.check_allocations(original, atlas, M.SOURCE_SHA, 2)

    def test_08_numeric_flags_require_exact_runtime_policy_and_physical_pin(self):
        flag = next(iter(M.FLAGS))
        original = copy.deepcopy(self.context['numeric_flags'][flag])
        for field, value in (('value', True), ('value', 2), ('policy', 'inferred from operands'), ('runtime_receipt_sha256', '0' * 64)):
            self.context['numeric_flags'][flag] = dict(original, **{field: value})
            with self.assertRaises(M.Refused):
                self.run_prepare()
        self.context['numeric_flags'][flag] = original
        path = Path(self.physical['numeric_runtime']['path'])
        path.write_bytes(b'changed selected numeric input')
        with self.assertRaises(M.Refused):
            self.run_prepare()

    def test_09_full_uint32_draws_precede_source_and_keep_budget_guards(self):
        output = self.run_prepare()
        plan = json.loads(output.draw_plan_json)
        self.assertEqual(plan['domain'], [0, 2**32 - 1])
        self.assertEqual(plan['independent_calls'], 128)
        self.assertEqual(plan['order'][-1], 'original source function')
        self.assertIn('for(unsigned i=0;i<128u;++i) dws_choice_table[i]=(uint32_t)swdb_next();', output.c_text)
        self.assertEqual(len(plan['producer_plan_rows']), 128)
        self.assertEqual(plan['draw_symbol'], 'swdb_next')
        self.assertIn('swdb.oracle_capacity', plan['producer_capacity'])
        self.assertNotRegex(output.c_text, r'\bnondet\w*\s*\([^)]*\)\s*\{')
        self.assertNotIn('%', output.c_text)
        # Execute only the exact frozen pure hook renderer, never its module.
        tree = ast.parse((WHOLE / 'model-entry-v3/whole_model_v3.py').read_bytes())
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'hook_text')
        ns = {'need': M.need}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-frozen-hook-leaf>', 'exec'), ns)
        for budget in (1, 128, 256):
            self.assertEqual(M.choice_hook_prefix(budget), ns['hook_text'](budget))
        hook = M.choice_hook_prefix(128)
        self.assertIn('alternatives>0', hook)
        self.assertIn('dws_choice_used<128u', hook)
        self.assertIn('dws_choice_table[dws_choice_used++] % alternatives', hook)
        self.assertNotIn('alternatives<=', hook)
        self.assertEqual({x % 16385 for x in range(16385)}, set(range(16385)))

    def test_10_bad_budget_choice_hooks_model_and_statement_linkage_refuse(self):
        for budget in (0, 257, True):
            self.policy['choice_budget'] = budget
            with self.assertRaises(M.Refused):
                self.run_prepare()
        self.policy['choice_budget'] = 128
        old = copy.deepcopy(self.assembly)
        for mutate in (lambda a: a.update(c_text=a['c_text'].replace('alternatives>0', 'alternatives<=256', 1)),
                       lambda a: a['entry'].update(public_admission=True),
                       lambda a: a['entry']['harness_draws'].update(independent=False),
                       lambda a: a['entry']['model'].update(source_atlas_sha256='0' * 64)):
            self.assembly = copy.deepcopy(old)
            mutate(self.assembly)
            self.assembly['entry']['model']['sha256'] = hashlib.sha256(self.assembly['c_text'].encode()).hexdigest()
            self.inputs['model_assembly'] = self.put('model_assembly', self.assembly)
            with self.assertRaises(M.Refused):
                self.run_prepare()

    def test_11_physical_symlink_missing_or_changed_selected_input_refuses(self):
        selection = self.selection()
        policy_path = Path(selection.policy.path)
        alias = self.root / 'policy-link.json'
        alias.symlink_to(policy_path)
        bad = M.Pin(str(alias), selection.policy.bytes, selection.policy.sha256)
        with self.assertRaises(M.Refused):
            M.prepare(M.OwnedSelection(bad))
        policy_path.write_bytes(policy_path.read_bytes() + b' ')
        with self.assertRaises(M.Refused):
            M.prepare(selection)

    def test_12_no_arbitrary_renderer_callback_or_extra_input_and_malformed_refuse(self):
        self.policy['renderer'] = 'choose-any-C'
        with self.assertRaises(M.Refused):
            self.run_prepare()
        del self.policy['renderer']
        self.inputs['extra'] = self.inputs['source']
        with self.assertRaises(M.Refused):
            self.run_prepare()
        del self.inputs['extra']
        self.context['ordinary_allocations'][0]['scope_end_offset'] = None
        with self.assertRaises(M.Refused):
            self.run_prepare()
        with self.assertRaises(M.Refused):
            M.Pin('/tmp/example', True, '0' * 64)

    def test_13_frozen_globals_mapping_and_scope_basis_match_source(self):
        tree = ast.parse((WHOLE / 'source_program_globals_v1.py').read_bytes())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'GLOBALS' for target in node.targets))
        self.assertEqual(M.GLOBALS, ast.literal_eval(assignment.value))
        for name, expected in M.FROZEN.items():
            self.assertEqual(pin(PROJECT / 'swdb/cbmc_translator.py' if name == 'harness/cbmc_translator.py' else WHOLE / name)['sha256'], expected)
        self.assertEqual(pin(WHOLE / 'source_call_fixture_v2.cpp')['sha256'], M.SOURCE_SHA)

    def test_14_fixed_integer_oracle_recipe_retains_full_domain_and_checked_capacity(self):
        tree = ast.parse((PROJECT / 'swdb/cbmc_translator.py').read_bytes())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'PRELUDE' for target in node.targets))
        prelude = ast.literal_eval(assignment.value)
        self.assertIn('static long long swdb_next(void)', prelude)
        self.assertIn('SWDB_CHECK(swdb_oracle_next < swdb_oracle_n, "@CAPACITY@")', prelude)
        self.assertIn('return swdb_oracle[swdb_oracle_next++];', prelude)
        for value in (0, 1, 2**31, 2**32 - 1):
            # All these signed-64 oracle values exist, and C unsigned conversion
            # covers every uint32 value without a desired-output restriction.
            self.assertTrue(-(2**63) <= value < 2**63)
            self.assertEqual(value % 2**32, value)
        plan = json.loads(self.run_prepare().draw_plan_json)
        self.assertEqual(len({row['name'] for row in plan['producer_plan_rows']}), 128)
        self.assertEqual({row['ctype'] for row in plan['producer_plan_rows']}, {'uint32_t'})

    def test_15_physical_postclosure_catches_change_after_initial_hash(self):
        selection = self.selection()
        old = M.document
        victim = Path(self.physical['numeric_runtime']['path'])
        def changing_document(selected):
            value = old(selected)
            if selected.sha256 == self.inputs['statement_preparation']['sha256']:
                victim.write_bytes(b'changed after initial physical check')
            return value
        M.document = changing_document
        try:
            with self.assertRaises(M.Refused):
                M.prepare(selection)
        finally:
            M.document = old

    def test_16_atlas_cannot_grant_values_or_ownership_or_hide_cells(self):
        for mutate in (lambda a: a.update(initialization_granted=True), lambda a: a.update(history_events_added=1),
                       lambda a: a.update(public_admission=True), lambda a: a.update(source_registration_grants_ownership=True),
                       lambda a: a['cells'].pop(), lambda a: a['cells'][0].update(cell=False),
                       lambda a: a['objects'][0].update(guest_base=17179869184)):
            atlas = copy.deepcopy(self.atlas)
            mutate(atlas)
            with self.assertRaises(M.Refused):
                M.check_allocations(self.context['ordinary_allocations'], atlas, M.SOURCE_SHA, 2)
        saved = self.inputs['statement_preparation']
        wrong = dict(self.statements, original_full_tu_sha256='0' * 64)
        self.inputs['statement_preparation'] = self.put('wrong_statements', wrong)
        with self.assertRaises(M.Refused):
            self.run_prepare()
        self.inputs['statement_preparation'] = saved

    def test_17_emitted_hook_declarations_precede_lowered_source_uses(self):
        output = self.run_prepare()
        self.assertLess(output.c_text.index('static void dws_source_object_leave(unsigned object);'),
                        output.c_text.index('dws_source_object_leave(0u);'))
        self.assertIn('DXM_CELLS==64', output.c_text)
        self.assertIn('DXP_TILE_WORDS==16384', output.c_text)
        plan = json.loads(output.integration_plan_json)
        self.assertTrue(plan['original_source_text_unchanged'])
        self.assertEqual(plan['translation_unit_order'][2], 'fixed receiver/lifetime hooks with forward declaration')

    def controlled_read(self, *, changed=None, atime_only=False, old=False, canonical=True, regular=True, wrong_hash=False, wrong_size=False):
        payload = b'exact controlled input bytes'
        typed_pin = M.Pin('/synthetic/receiver-stable-input', len(payload) + (1 if wrong_size else 0),
            '0' * 64 if wrong_hash else hashlib.sha256(payload).hexdigest())
        fields = {'st_dev': 3, 'st_ino': 41, 'st_mode': (0o100644 if regular else 0o040755),
            'st_nlink': 1, 'st_uid': 501, 'st_gid': 20, 'st_size': len(payload), 'st_mtime_ns': 1001, 'st_ctime_ns': 1002}
        before = types.SimpleNamespace(**fields, st_atime_ns=10)
        after = types.SimpleNamespace(**fields, st_atime_ns=11 if atime_only else 10)
        if changed:
            setattr(after, changed, getattr(after, changed) + 1)
        class InMemoryPhysicalFile:
            def __init__(self): self.calls = 0
            def lstat(self):
                self.calls += 1
                return before if self.calls == 1 else after
            def resolve(self, strict=True): return self if canonical else object()
            def open(self, mode):
                assert mode == 'rb'
                return io.BytesIO(payload)
        path = InMemoryPhysicalFile()
        if old:
            text = (WHOLE / 'receiver-state-draws-v1/receiver_state_draws_v1.py').read_text()
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), '07b8f687987a90423179e13b42fa312e4678fe5d929e932c9ac0374f0ca54e7b')
            node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'check_file')
            namespace = {'Pin': M.Pin, 'Path': lambda _value: path, 'stat': M.stat, 'need': M.need, 'hashlib': hashlib}
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-v1-file-check>', 'exec'), namespace)
            return namespace['check_file'](typed_pin, retain=True)
        saved = M.Path
        M.Path = lambda _value: path
        try:
            return M.check_file(typed_pin, retain=True)
        finally:
            M.Path = saved

    def test_18_atime_only_change_is_old_red_new_green_at_actual_read_seam(self):
        with self.assertRaises(M.Refused):
            self.controlled_read(atime_only=True, old=True)
        self.assertEqual(self.controlled_read(atime_only=True), b'exact controlled input bytes')

    def test_19_every_one_of_nine_stable_field_mutations_refuses(self):
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        for field in fields:
            with self.subTest(field=field), self.assertRaises(M.Refused):
                self.controlled_read(changed=field, atime_only=True)

    def test_20_stable_metadata_copy_source_and_two_consumer_inverse_are_exact(self):
        before = (WHOLE / 'receiver-state-draws-v1/receiver_state_draws_v1.py').read_text()
        after = (HERE / 'receiver_state_draws_v2.py').read_text()
        origin = (WHOLE / 'model-entry-v3/whole_model_v3.py').read_text()
        helper_node = next(node for node in ast.parse(after).body if isinstance(node, ast.FunctionDef) and node.name == 'stable_metadata')
        origin_node = next(node for node in ast.parse(origin).body if isinstance(node, ast.FunctionDef) and node.name == 'stable_metadata')
        helper = ast.get_source_segment(after, helper_node)
        self.assertEqual(helper, ast.get_source_segment(origin, origin_node))
        inverse = after.replace(helper + '\n\n\n', '', 1).replace(
            'stable_metadata(path.lstat()) == stable_metadata(before) and hasher.hexdigest() == pin.sha256',
            'path.lstat() == before and hasher.hexdigest() == pin.sha256', 1)
        changes = {'model-entry-v2/whole_model_v2.py': 'model-entry-v3/whole_model_v3.py',
            '7ddff742ec78573dec9ee53c071f57d88ed8fd4d4f819a05118456f72acafe61': '2de83f722c439c5a834f9b17549b979e24b3716d79170377bf8cbeafd7b07b50',
            'source_statements_v1.py': 'source_statements_v2.py',
            '333148951b8e1c634600a7a0deb2abf312c4d708b1ca69fdd04429959518c0d1': '49832255fef43afa51078479770d62f01e7e539e4f71f4034e3f2648cb867738'}
        for old, new in changes.items(): inverse = inverse.replace(new, old, 1)
        self.assertEqual(inverse, before)
        old_template = json.loads((WHOLE / 'receiver-state-draws-v1/selection-policy-template-v1.json').read_bytes())
        new_template = json.loads((HERE / 'selection-policy-template-v2.json').read_bytes())
        for old, new in [('model-entry-v2/whole_model_v2.py', 'model-entry-v3/whole_model_v3.py'),
                         ('source_statements_v1.py', 'source_statements_v2.py')]:
            new_template['frozen_inputs'].pop(new)
            new_template['frozen_inputs'][old] = old_template['frozen_inputs'][old]
        self.assertEqual(new_template, old_template)
        for name in ('context-receipt-template', 'runtime-selection-template'):
            self.assertEqual((HERE / (name + '-v2.json')).read_bytes(), (WHOLE / 'receiver-state-draws-v1' / (name + '-v1.json')).read_bytes())

    def test_21_atime_tolerance_keeps_canonical_regular_size_and_hash_gates(self):
        for options in ({'canonical': False}, {'regular': False}, {'wrong_hash': True}, {'wrong_size': True}):
            with self.subTest(options=options), self.assertRaises(M.Refused):
                self.controlled_read(atime_only=True, **options)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date': '2026-10-16 ET', 'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped), 'synthetic_protocol_only': True,
        'compiler_native_project_child_or_scientific_execution': False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
