"""No-child actual-metadata and physical-reader/API regression controls.

The retained Clang descriptor is historical shape evidence, not a new runtime or
owned-context observation. Upstream capture/library selection and physical Linux
payload streams use explicit protocol doubles when those paths are unavailable.
"""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
from types import SimpleNamespace
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'production-route-v4'
TRACE = WHOLE.parent / '28-public-memory-trace-resume-20261016'
PRIOR = runpy.run_path(str(OLD / 'test_composition_v4.py'), run_name='frozen_v4_control_support')
NEW = runpy.run_path(str(HERE / 'profile/profile_builder_v4.py'), run_name='profile_v5_no_project_import')
PREVIOUS = runpy.run_path(str(OLD / 'profile/profile_builder_v3.py'), run_name='profile_v4_no_project_import')
COMPILER = json.loads((WHOLE / 'compiler-capture-v10/linux_compiler_capture_policy_v10.json').read_bytes())['compiler']
CONTEXT = json.loads((WHOLE / 'compiler-descriptor-v1/passive-read-stdout-v1.json').read_bytes())
RUNTIME = CONTEXT['document']['runtime']


def identity_source():
    text = (OLD / 'base-source/c_lowering.py').read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'identity')
    return ast.get_source_segment(text, node)


def descriptor():
    path = WHOLE / 'compiler-descriptor-v1/expected-absolute-compiler-descriptor-v1.json'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '7ef1f44848dd60dae9a9732ce49752209197e80e1afcd3720649d173e386aba3'
    return json.loads(raw)


def inventory():
    small = {'path': '/explicit-root-selected-data-standin', 'bytes': 1, 'sha256': 'a' * 64}
    return {'compiler_driver': copy.deepcopy(COMPILER['driver']), 'compiler_wrapper': copy.deepcopy(COMPILER['wrapper']),
        'device_configuration': dict(small), 'address_projection': dict(small), 'numeric_runtime': dict(small)}


def extracted(name, overrides=None, previous=False):
    ns = dict(PREVIOUS if previous else NEW)
    if overrides: ns.update(overrides)
    text = (OLD / 'profile/profile_builder_v3.py' if previous else HERE / 'profile/profile_builder_v4.py').read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<real-profile-' + name + '>', 'exec'), ns)
    return ns[name]


class StreamControls(unittest.TestCase):
    def test_exact_root_candidate_descriptor_is_only_expected_command_projection(self):
        expected = copy.deepcopy(RUNTIME); expected['command'] = COMPILER['command']
        selected = descriptor()
        self.assertEqual(selected, {'schema': 'root-selected-compiler-observation-1', 'command': COMPILER['command'],
            'version': COMPILER['version'], 'wrapper': COMPILER['wrapper'], 'driver': COMPILER['driver'], 'runtime_identity': expected})
        self.assertEqual(RUNTIME['command'], ['clang++'])
        provenance = WHOLE / 'compiler-descriptor-v1/descriptor-provenance-v1.json'
        self.assertEqual(hashlib.sha256(provenance.read_bytes()).hexdigest(),
            '6379822389f62aea0289da83d16a45a7484ea5c78b86889a6c397751679b4948')

    def test_exact_builder_preparer_inverse_and_frozen_production_basis(self):
        new = (HERE / 'profile/profile_builder_v4.py').read_text()
        inverse = json.loads((HERE / 'builder-inverse-v5.json').read_bytes())
        for row in reversed(inverse['replacements']):
            self.assertEqual(new.count(row['new']), 1); new = new.replace(row['new'], row['old'], 1)
        self.assertEqual(new, (OLD / 'profile/profile_builder_v3.py').read_text())
        for name in ('normal-producer-basis-v4.json', 'pair_plan_v2.py', 'pair-selection-template-v4.json'):
            self.assertEqual((HERE / 'profile' / name).read_bytes(), (OLD / 'profile' / name).read_bytes())
        before = (OLD / 'profile/profile_prepare_v3.py').read_text()
        after = (HERE / 'profile/profile_prepare_v4.py').read_text()
        for new_name, old_name in inverse['preparer_inverse_names'].items(): after = after.replace(new_name, old_name)
        after = after.replace(hashlib.sha256((HERE / 'profile/profile_builder_v4.py').read_bytes()).hexdigest(),
            hashlib.sha256((OLD / 'profile/profile_builder_v3.py').read_bytes()).hexdigest())
        self.assertEqual(before, after)
        self.assertEqual(hashlib.sha256((OLD / 'production-route-v4.patch').read_bytes()).hexdigest(),
            'c7650b15a840c037be56fc477a5f033d455db6e2f391f5a4cdc7e49214836cd5')

    def test_actual_driver_extent_old_red_new_inventory_green(self):
        selected = inventory(); calls = []
        self.assertEqual(selected['compiler_driver']['bytes'], 271520144)
        self.assertGreater(selected['compiler_driver']['bytes'], 256 * 1024 * 1024)
        with self.assertRaisesRegex(PREVIOUS['Refused'], 'bounded physical pin'):
            PREVIOUS['read'](selected['compiler_driver'], limit=256 * 1024 * 1024)
        checker = extracted('check_physical_inventory', {'stream_pin': lambda row, *, limit: calls.append((row, limit))})
        self.assertEqual(checker(selected), selected)
        self.assertEqual(len(calls), 5)
        self.assertEqual(next(limit for row, limit in calls if row == selected['compiler_driver']), 271520144)
        for row, limit in calls:
            if row != selected['compiler_driver']: self.assertEqual(limit, 256 * 1024 * 1024)
        for change in (lambda v: v['compiler_driver'].update(bytes=271520145), lambda v: v.pop('numeric_runtime'),
                       lambda v: v.update(extra_role=selected['compiler_driver'])):
            bad = copy.deepcopy(selected); change(bad)
            with self.assertRaises(NEW['Refused']): checker(bad)

    def test_real_validate_request_uses_selected_inventory_at_actual_shape_seam(self):
        source = json.loads((HERE / 'profile/selection-template-v5.json').read_bytes())
        source.update(owner='explicit-control-owner', library_root=None, physical_inputs=inventory())
        # Only upstream library/capture gates are protocol doubles. The real
        # validate_request body and exact physical-inventory call are executed.
        with tempfile.TemporaryDirectory() as directory:
            source['library_root'] = str(Path(directory).resolve()); events = []
            capture = source['capture']; original = capture['original']; transform = capture['transform']
            ingress = SimpleNamespace(ORIGINAL_POLICY_SHA=original['policy']['sha256'], ORIGINAL_RESULT_SHA=original['result']['sha256'],
                TRANSFORM_RESULT_SHA=transform['result']['sha256'], ROOT_EXECUTION_SHA=transform['execution']['sha256'],
                fixed_pin=lambda *a: None, original_refusal=lambda *a: None, transform_gate=lambda *a: None, execution_gate=lambda *a: None)
            def import_protocol(name, globals=None, locals=None, fromlist=(), level=0):
                if name == 'swdb._dx100_whole': return SimpleNamespace(normalized_capture_ingress_v2=ingress)
                raise AssertionError('unexpected import in extracted validate_request')
            import builtins
            hooks = {'selected_modules': lambda request: None, 'selected': lambda *a: b'{}',
                'original_project_role': lambda *a: None, '__builtins__': {**vars(builtins), '__import__': import_protocol},
                'check_physical_inventory': lambda values: events.append(values)}
            extracted('validate_request', hooks)(source)
            self.assertEqual(events, [source['physical_inputs']])
            with self.assertRaises(PREVIOUS['Refused']): extracted('validate_request', hooks, previous=True)(source)

    def test_real_identity_signature_actual_runtime_roles_and_inventory_binding(self):
        observed = descriptor(); selected = inventory(); calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / 'identity_recipe.py'; path.write_text(identity_source())
            # Execute the real production recipe over inert producer file data.
            # No actual method hash or compiler observation is claimed.
            for node in ast.walk(ast.parse(identity_source())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'with_name' and node.args and isinstance(node.args[0], ast.Constant):
                    (root / node.args[0].value).write_bytes(b'explicit-inert-producer-file')
            aux = root / 'aux.py'; aux.write_bytes(b'explicit-inert-auxiliary-source')
            module = SimpleNamespace(__file__=str(path))
            module.__dict__.update(Path=Path, hashlib=hashlib, json=json, terminal_release=SimpleNamespace(__file__=str(aux)),
                cpu_effects=SimpleNamespace(__file__=str(aux)), bounded_initialization=SimpleNamespace(identity=lambda: {'sha256':'a'*64}),
                wp_pointer_bounds=SimpleNamespace(identity=lambda: {'sha256':'b'*64}), TOOL_ID='control-only', TOOL_VERSION='1',
                naming_rules=lambda: {'control': 'not-an-actual-naming-identity'},
                _file_sha256=lambda path: observed['wrapper']['sha256'], _binary=lambda value: value)
            function = extracted('lowering_identity_without_probe', {'stream_pin': lambda row, *, limit: calls.append((row, limit))})
            result = function(module, observed, physical_inventory=selected)
            self.assertEqual(result['clang']['id'], 'clang-22.1.8')
            self.assertEqual([row for row, _ in calls], [observed['wrapper'], observed['driver']])
            selected_runtime = copy.deepcopy(RUNTIME); selected_runtime['command'] = COMPILER['command']
            self.assertEqual(observed['runtime_identity'], selected_runtime)
            self.assertEqual(RUNTIME['command'], ['clang++'])
            self.assertEqual(CONTEXT['document']['tool']['command'], ['clang++'])
            self.assertEqual({k:v for k,v in selected_runtime.items() if k != 'command'},
                {k:v for k,v in RUNTIME.items() if k != 'command'})
            for mutation in ('driver', 'wrapper', 'command', 'runtime-driver', 'runtime-wrapper', 'missing-runtime-role', 'original-alias-runtime'):
                bad = copy.deepcopy(observed)
                if mutation in ('driver', 'wrapper'): bad[mutation]['path'] += '.unadmitted'
                elif mutation == 'command': bad['command'] = ['clang++']
                elif mutation == 'runtime-driver': bad['runtime_identity']['driver']['path'] = observed['wrapper']['path']
                elif mutation == 'runtime-wrapper': bad['runtime_identity']['command_executable']['path'] = observed['driver']['path']
                elif mutation == 'missing-runtime-role': bad['runtime_identity'].pop('headers')
                else: bad['runtime_identity'] = copy.deepcopy(RUNTIME)
                with self.subTest(mutation=mutation), self.assertRaises(NEW['Refused']): function(module, bad, physical_inventory=selected)

    def test_streamed_small_physical_pin_canonical_hash_extent_and_atime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / 'small'; path.write_bytes(b'streamed physical bytes')
            row = NEW['pin'](path, path.read_bytes())
            self.assertEqual(NEW['stream_pin'](row, limit=len(path.read_bytes())), row)
            link = root / 'link'; link.symlink_to(path)
            for bad in ({**row, 'path': str(link)}, {**row, 'sha256': '0'*64}, {**row, 'bytes': row['bytes']+1}):
                with self.assertRaises(NEW['Refused']): NEW['stream_pin'](bad, limit=row['bytes']+1)
            with self.assertRaises(NEW['Refused']): NEW['stream_pin'](row, limit=row['bytes']-1)

    def test_stream_read_is_bounded_and_all_nine_stable_fields_are_checked(self):
        payload = b'bounded stream'; row = {'path':'/explicit-inert-stream', 'bytes':len(payload), 'sha256':hashlib.sha256(payload).hexdigest()}
        fields = ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
        baseline = dict.fromkeys(fields, 1); baseline.update(st_mode=stat.S_IFREG | 0o644, st_size=len(payload), st_atime_ns=1)
        for field in ('st_atime_ns', *fields):
            before = SimpleNamespace(**baseline); after = SimpleNamespace(**{**baseline, field:baseline.get(field,1)+1}); reads = []
            class Stream(io.BytesIO):
                def read(self, size=-1):
                    self.assertion = size
                    if size < 0 or size > 1024*1024: raise AssertionError('unbounded read')
                    reads.append(size); return super().read(size)
            class PhysicalPath:
                def __init__(self, value): self.calls = 0
                def is_absolute(self): return True
                def lstat(self): self.calls += 1; return before if self.calls == 1 else after
                def resolve(self, strict): return self
                def open(self, mode): return Stream(payload)
            function = extracted('stream_pin', {'Path':PhysicalPath})
            if field == 'st_atime_ns': self.assertEqual(function(row, limit=len(payload)), row)
            else:
                with self.subTest(field=field), self.assertRaises(NEW['Refused']): function(row, limit=len(payload))
            self.assertTrue(reads)

    def test_preparer_callsite_and_template_keep_raw_and_runtime_roles_distinct(self):
        text = (HERE / 'profile/profile_builder_v4.py').read_text()
        tree = ast.parse(text)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == 'lowering_identity_without_probe']
        self.assertEqual(len(calls), 1)
        self.assertEqual({k.arg:ast.unparse(k.value) for k in calls[0].keywords}, {'physical_inventory':"request['physical_inputs']"})
        template = json.loads((HERE / 'profile/selection-template-v5.json').read_bytes())
        self.assertIsNone(template['compiler_observation'])
        self.assertNotIn('runtime_identity', template['capture']['original'])
        self.assertIsNone(template['capture']['prepared'])
        before = json.loads((OLD / 'profile/selection-template-v4.json').read_bytes())
        before['compiler_observation'] = None
        self.assertEqual(template, before)


if __name__ == '__main__': unittest.main(verbosity=2)
