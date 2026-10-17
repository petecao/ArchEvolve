"""2026-10-16 ET. Frozen V1 actual-metadata projections with inert seams.

No audit, scientific record/output interpretation, project import, remote call,
compiler, native or solver. Runtime observations are compact retained JSON;
physical/process/import boundaries are explicit stand-ins, never observations.
"""
import ast
import builtins
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
V1 = TRACE / 'trace-cold-audit-v1'
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
LOCAL_PROJECT = TRACE.parents[3]
H = lambda value: hashlib.sha256(value).hexdigest()
READER_BYTES = (V1 / 'trace_cold_audit_v1.py').read_bytes()
assert H(READER_BYTES) == '3cefa1c4eb7c05371afcdaf8b43d6f46927dfe80aed0be90e652bac0cf0157ee'
CONTEXT_BYTES = (V1 / 'passive-trace-v4-context.json').read_bytes()
assert H(CONTEXT_BYTES) == '66c95b6c1a7eec239d95ca9fce7b9290381a54407472e572a4e5dcaa28732bf4'
CONTEXT = json.loads(CONTEXT_BYTES)
EXPECTED_BYTES = (TRACE / 'linux_trace_policy_04af74c1_v4.json').read_bytes()
assert H(EXPECTED_BYTES) == 'd61807f5595e77aabdbd054b6f00caff636775f07ab697f368af8f87864241de'
EXPECTED = json.loads(EXPECTED_BYTES)
METADATA_BYTES = (TRACE / 'python-physical-metadata-v2.json').read_bytes()
assert H(METADATA_BYTES) == EXPECTED['control_files']['python-physical-metadata-v2.json']
METADATA = json.loads(METADATA_BYTES)
ROOT_OBSERVER = (TRACE.parent.parent / 'evidence/resume-20261016-lane-coordination/t28-linux-runtime-observer-v2-actual-20261016.json').read_bytes()
assert H(ROOT_OBSERVER) == EXPECTED['python_startup_roles_v2']['root_observer_sha256']


def deny_child(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('metadata projection controls refuse ' + event)


sys.addaudithook(deny_child)


def load(path):
    namespace = {'__name__': 'metadata_controls_' + path.stem, '__file__': str(path)}
    exec(compile(path.read_bytes(), str(path), 'exec'), namespace)
    return namespace


READER = load(V1 / 'trace_cold_audit_v1.py')
COMMON_NS = load(V1 / 'reviewed_cold_primitives_v1.py')
COMMON = types.SimpleNamespace(**COMMON_NS)


def function(source, name, namespace):
    node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name)
    result = dict(namespace)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-frozen-metadata-function>', 'exec'), result)
    return result[name]


class SourcePath(type(Path())):
    """Map exact frozen project byte inputs to hash-checked local source data."""
    def read_bytes(self):
        name = str(self.relative_to(EXPECTED['source_root']))
        frozen = HERE / 'frozen-source' / name
        value = (frozen if frozen.is_file() else LOCAL_PROJECT / name).read_bytes()
        assert H(value) == EXPECTED['source_files'][name], 'local source differs from the exact published input: ' + name
        return value
    def read_text(self, encoding=None, errors=None):
        assert encoding in (None, 'utf-8') and errors in (None, 'strict')
        return self.read_bytes().decode().replace('\r\n', '\n').replace('\r', '\n')
    def open(self, mode='r', *args, **kwargs):
        assert mode == 'rb' and not args and not kwargs
        return io.BytesIO(self.read_bytes())


class MetadataPath(type(Path())):
    payload = CONTEXT['json']
    def read_bytes(self):
        name = str(self.relative_to(CONTEXT['raw']))
        if name == 'control/t28-linux-runtime-observer-v2-actual-20261016.json': return ROOT_OBSERVER
        if name.endswith('-startup-stderr.txt'): return b''
        if name.endswith('-startup-stdout.txt'):
            return json.dumps(self.payload[name.replace('-stdout.txt', '.json')]['observation']).encode()
        return json.dumps(self.payload[name]).encode()


def startup_projection(payload):
    raw = MetadataPath(CONTEXT['raw']); project = Path(EXPECTED['source_root'])
    roles = types.SimpleNamespace(**load(TRACE / 'python_startup_roles_v2.py'))
    provenance = CONTEXT['json']['entry-isolated-startup.json']['plan_provenance']
    def admitted_plan(plan, *, metadata, source_project, root_observer_bytes, closed):
        assert plan == EXPECTED['python_startup_roles_v2'] and metadata == METADATA
        assert source_project == project and root_observer_bytes == ROOT_OBSERVER
        return provenance
    roles.validate_role_plan_v2 = admitted_plan
    def absent(path):
        assert str(path) == str(raw / 'bootstrap-source-cache')
        return False
    run = function(READER_BYTES, 'startup_receipts', {**READER, 'os': types.SimpleNamespace(path=types.SimpleNamespace(lexists=absent))})
    old = MetadataPath.payload; MetadataPath.payload = payload
    try: return run(EXPECTED, METADATA, raw, project, roles, object(), COMMON)
    finally: MetadataPath.payload = old


class ActualShapeControls(unittest.TestCase):
    def test_runtime_policy_normalization_preserves_actual_closed_shapes(self):
        normalized = READER['normalized_runtime'](EXPECTED, METADATA)
        self.assertEqual(normalized['startup_roles'], EXPECTED['python_startup_roles_v2'])
        self.assertEqual(normalized['python_surface_binding'], METADATA)
        self.assertEqual(normalized['portable_import_surfaces'], {name: row['files'] for name, row in EXPECTED['portable_import_surfaces'].items()})
        self.assertEqual(len(normalized['runtime_files']), 2569)
        self.assertEqual(len(normalized['source_files']), 609)
        runtime = CONTEXT['json']['memory-trace-profile/runtime-provenance.json']
        self.assertNotIn('version', runtime['runtime'])
        self.assertEqual(set(runtime), {'date', 'source_commit', 'lowering', 'runtime', 'proof_setup', 'startup', 'scope'})
        for name, value in EXPECTED['linux_clang_components'].items(): self.assertEqual(runtime['runtime'][name], value)

    def test_exact_startup_function_consumes_actual_initial_post_import_and_identity_metadata(self):
        observed = startup_projection(copy.deepcopy(CONTEXT['json']))
        self.assertEqual(observed['runtime'], CONTEXT['json']['memory-trace-profile/runtime-provenance.json'])
        self.assertEqual(set(observed['roles']), {'entry-isolated', 'pytest-child'})
        self.assertEqual(observed['roles']['pytest-child']['post_package_sys_path'][0], EXPECTED['source_root'])
        self.assertEqual(observed['roles']['entry-isolated']['initial_sys_path'], EXPECTED['python_startup_roles_v2']['package_sys_path'])

    def test_startup_inverse_flags_components_and_missing_nested_context_are_rejected(self):
        mutations = [lambda data: data['memory-trace-profile/actual-pytest-child-startup.json']['flags'].update(isolated=1),
            lambda data: data['pytest-child-startup.json']['observation']['post_package_sys_path'].append('/unadmitted'),
            lambda data: data['memory-trace-profile/runtime-provenance.json']['runtime'].pop('parser'),
            lambda data: data['memory-trace-profile/runtime-provenance.json']['lowering'].pop('naming_rules'),
            lambda data: data['memory-trace-profile/launch-provenance.json']['cbmc_version'].update(exact_observed_version='6.11.1')]
        for index, change in enumerate(mutations):
            data = copy.deepcopy(CONTEXT['json']); change(data)
            with self.subTest(index=index), self.assertRaises((AssertionError, KeyError, ValueError)): startup_projection(data)

    def test_fixture_identity_projection_uses_actual_retained_runtime_and_exact_source_expressions(self):
        runtime = copy.deepcopy(CONTEXT['json']['memory-trace-profile/runtime-provenance.json'])
        identities = load(INIT / 'initialized_cold_identities_v2.py')
        self.assertEqual(H((INIT / 'initialized_cold_identities_v2.py').read_bytes()),
            '0c248fc3b50e69629fed8ab9a187dc5a947cc9aee3fb628aa8d604a6e79c5cc9')
        identities['Path'] = SourcePath
        module = types.SimpleNamespace(**identities)
        # Parser seam consumes the exact frozen public YAML bytes. The typed
        # stand-in tests transformation/data access, not actual method acceptance.
        base = {'c_lowering': {}, 'checks': {}, 'lineup': [{'tool': 'cbmc', 'flags': []}, {'tool': 'frama-c-wp', 'flags': []}]}
        captured = []
        def parser(_yaml, data):
            self.assertEqual(H(data), EXPECTED['source_files']['tests/fixtures/proof/methods/contract-fixture-1.yaml'])
            captured.append(True); return copy.deepcopy(base)
        common = types.SimpleNamespace(safe_yaml=parser)
        result = READER['fixture_identities'](SourcePath(EXPECTED['source_root']), runtime, module, object(), common)
        self.assertEqual(captured, [True])
        self.assertEqual(result['method']['checks'], runtime['proof_setup'])
        self.assertEqual(result['method']['c_lowering']['translators'][0], runtime['lowering']['c_lowering'])
        self.assertEqual(result['method']['c_lowering']['naming_rules'], runtime['lowering']['naming_rules'])
        self.assertEqual(result['translator']['id'], 'swdb-cbmc-translator-4')
        self.assertEqual(result['frozen'], ['--unwinding-assertions', '--pointer-overflow-check'])

    def test_copied_reader_admission_metadata_projection_uses_explicit_inert_import_boundary(self):
        expected = READER['normalized_runtime'](EXPECTED, METADATA)
        policy = json.loads((V1 / 'trace-cold-policy-template-04af74c1-v1.json').read_bytes())
        policy['reader_admission']['admitted'] = True
        admission = policy['reader_admission']; plan = expected['startup_roles']; pins = []
        environment = {key: value for key, value in admission['environment'].items() if value is not None}
        wanted = plan['module_origins']['yaml']
        fake_yaml = types.SimpleNamespace(__file__=wanted['path'], __spec__=types.SimpleNamespace(origin=wanted['spec_origin']))
        fake_site = types.SimpleNamespace(ENABLE_USER_SITE=False)
        def imported(name, *args, **kwargs):
            assert name in {'site', 'yaml'}
            return fake_site if name == 'site' else fake_yaml
        fake_builtins = dict(vars(builtins)); fake_builtins['__import__'] = imported
        sysmeta = types.SimpleNamespace(flags=types.SimpleNamespace(isolated=1, no_user_site=1, safe_path=True, optimize=0),
            dont_write_bytecode=True, executable=plan['executable'], path=plan['package_sys_path'],
            prefix=plan['prefix'], base_prefix=plan['base_prefix'], pycache_prefix=admission['pycache_prefix'])
        closed = types.SimpleNamespace(verify_python_metadata=lambda value: {'inert_metadata_match': value == METADATA},
            _resolution=lambda path, chain: Path(METADATA['interpreter']['resolved']))
        physical = types.SimpleNamespace(pinned=lambda row: pins.append(row), pin=lambda *args: pins.append(args))
        run = function((V1 / 'reviewed_cold_primitives_v1.py').read_bytes(), 'admit_reader', {
            '__builtins__': fake_builtins, 'sys': sysmeta, 'os': types.SimpleNamespace(environ=environment,
                path=types.SimpleNamespace(lexists=lambda path: False)), 'Path': Path, 'absolute': COMMON.absolute})
        result, receipt = run(policy, expected, closed, physical)
        self.assertIs(result, fake_yaml); self.assertEqual(receipt, {'inert_metadata_match': True})
        self.assertEqual(len(pins), 2)
        sysmeta.path = [*sysmeta.path, '/unlisted']
        with self.assertRaises(AssertionError): run(policy, expected, closed, physical)

    def test_actual_cbmc_descriptor_and_retained_raw_version_receipt(self):
        source = TRACE / 'cbmc_release_gate.py'
        self.assertEqual(H(source.read_bytes()), EXPECTED['control_files']['cbmc_release_gate.py'])
        gate = load(source)['check_cbmc_version']
        output = EXPECTED['cbmc_version_output']
        actual = gate(EXPECTED, 0, output['stdout'], output['stderr'])
        self.assertEqual(actual, CONTEXT['json']['memory-trace-profile/launch-provenance.json']['cbmc_version'])
        tool = EXPECTED['tools']['cbmc']
        self.assertEqual(tool['version'], '6.11.0')
        self.assertEqual(tool['accepted_release_family'], '6.11')
        self.assertTrue(Path(tool['path']).is_absolute())
        self.assertEqual(tool['sha256'], 'a62af25d27425610608221d79c202f993efe1d5a85cece186119bec196382995')
        for output in ('6.11.1 (cbmc-6.11.1)\n', '6.12.0\n', '6.110.0\n', 'unversioned'):
            with self.subTest(output=output), self.assertRaises((AssertionError, ValueError)):
                gate(EXPECTED, 0, output, '')


if __name__ == '__main__': unittest.main(verbosity=2)
