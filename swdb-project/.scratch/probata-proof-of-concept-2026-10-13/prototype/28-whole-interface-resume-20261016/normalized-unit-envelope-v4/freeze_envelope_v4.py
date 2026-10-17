"""2026-10-16 ET. Freeze exact source controls; no runtime/consumer execution."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


basis = [WHOLE / 'normalized-unit-envelope-v3/source-packet-v3.json',
    WHOLE / 'normalized-unit-observation-v1/source-packet-v1.json',
    WHOLE / 'abi-role-transport-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2-independent-review/independent-abi-v2-source-review-20261016.json',
    WHOLE / 'root-launcher-loader-v11/source-packet-v11.json',
    WHOLE / 'root-launcher-loader-v11-independent-review/independent-source-review-v11.json',
    WHOLE / 'normalized-unit-envelope-v3-independent-review/independent-envelope-v3-spec-review-20261016.json']
closed = {}
for path in basis[:3]:
    value = json.loads(path.read_bytes())
    for row in value['files']:
        actual = Path(row['path'])
        if not actual.is_absolute(): actual = path.parent / actual
        checked = pin(actual)
        assert (checked['bytes'], checked['sha256']) == (row['bytes'], row['sha256'])
        closed[str(actual)] = checked
before = list(closed.values())

suite = unittest.TestSuite()
for name, cls in (('test_envelope_v4.py', 'Controls'), ('test_root_environment_v4.py', 'RootEnvironmentControls'),
                  ('test_abi_observer_v4.py', 'ABIObserverControls')):
    namespace = runpy.run_path(str(HERE / name), run_name='pure_' + cls)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[cls]))
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
(HERE / 'pure-controls-v4.log').write_text(output.getvalue())
assert result.testsRun == 23 and result.wasSuccessful() and not result.skipped
for row in before: assert pin(Path(row['path'])) == row
(HERE / 'pure-controls-v4.json').write_text(json.dumps({'date': '2026-10-16 ET', 'tests': 23, 'failures': 0,
    'errors': 0, 'skipped': 0, 'log': pin(HERE / 'pure-controls-v4.log'),
    'actual_retained_ABI_large_TU_observer_or_scientific_execution': False,
    'child_native_compiler_solver_shell_launcher_SSH_or_installed_project_import': False,
    'predecessor_physical_pin_rows_unchanged': len(before)}, sort_keys=True, indent=2) + '\n')
command = json.loads((HERE / 'command-v4.json').read_bytes())
envelope = json.loads((HERE / 'envelope-policy-v4.json').read_bytes())
observer = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
manifest = json.loads((HERE / 'observer/fixed-modules-v2.json').read_bytes())
assert len(command['stage_sources']) == 29 and len(observer['controls']) == 15 and len(manifest['modules']) == 13
assert command['root_controls_bytes_including_policy'] == 453830
assert command['root_controls_bytes_including_policy'] == sum(row['bytes'] for row in envelope['controls'].values()) + (HERE / 'envelope-policy-v4.json').stat().st_size
assert observer['capture']['prepared'] is None
for name, row in command['stage_sources'].items():
    assert pin(Path(row['path'])) == row
    assert name == Path(envelope['controls'][name]['path']).name
    assert (row['bytes'], row['sha256']) == (envelope['controls'][name]['bytes'], envelope['controls'][name]['sha256'])
(HERE / 'root-argv-v4.json').write_text(json.dumps(command['argv'], indent=2) + '\n')
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.name == 'source-packet-v4.json': continue
    if path.suffix == '.py': ast.parse(path.read_bytes())
    files.append(pin(path))
packet = {'schema': 'inert-linux-normalized-unit-ABI-observer-source-packet-4', 'date': '2026-10-16 ET',
    'files': files, 'basis': [pin(path) for path in basis], 'entry': pin(HERE / 'linux_observation_envelope_v4.py'),
    'policy': pin(HERE / 'envelope-policy-v4.json'), 'command': pin(HERE / 'command-v4.json'),
    'observer_entry': pin(HERE / 'observer/observe_entry_v2.py'), 'observer_inventory': pin(HERE / 'observer/fixed-modules-v2.json'),
    'tests': 23, 'observer_modules': 13, 'observer_controls': 15, 'root_controls': 29,
    'root_control_bytes_including_policy': 453830, 'entry_inverse': pin(HERE / 'exact-inverses-v4.json'),
    'ABI_helper': pin(HERE / 'observer/modules/abi_role_transport_v1.py'),
    'adapter': pin(HERE / 'observer/modules/normalized_compiler_adapter_v2.py'),
    'strict_token_grammar': pin(HERE / 'observer/modules/strict_minify_v2.py'),
    'legacy_compiler_consumer_sha256': '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c',
    'changed_previous_observer_module_count': 2, 'other_previous_module_bytes_exact': 9,
    'new_ingress_delta': 'Only the exact normalized adapter physical SHA; every ingress function unchanged.',
    'public_equality_and_private_prepared_unknown_boundary_preserved': True,
    'actual_physical_primitive_paths_independently_closed': True,
    'original_derived_ABI_receipt_identities_distinct': True,
    'root_preinterpreter_unset': ['LIBRARY_PATH', 'LD_LIBRARY_PATH'],
    'resource_runtime_source_guard_and_finalization_gates_unchanged': True,
    'actual_retained_ABI_replay_executed': False, 'actual_observer_executed': False,
    'root_independent_source_review_and_successful_ABI_replay_before_dispatch_required': True,
    'public_admission': False, 'owned_context_or_scientific_result_fabricated': False,
    'shared_or_frozen_predecessor_or_Git_mutated': False}
(HERE / 'source-packet-v4.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v4.json',
    'entry': 'linux_observation_envelope_v4.py', 'policy': 'envelope-policy-v4.json', 'command': 'command-v4.json',
    'observer': 'observer/observe_entry_v2.py', 'inventory': 'observer/fixed-modules-v2.json'}.items()}, sort_keys=True))
