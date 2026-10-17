"""2026-10-16 ET. Source-only freeze of an explicitly unready memory envelope."""
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


basis = [WHOLE / 'normalized-unit-envelope-v4/source-packet-v4.json',
    WHOLE / 'normalized-unit-envelope-v4-independent-review/independent-envelope-v4-spec-review-20261016.json',
    WHOLE / 'memory-normalized-ingress-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2-independent-review/independent-abi-v2-source-review-20261016.json',
    WHOLE / 'root-launcher-loader-v11/source-packet-v11.json',
    WHOLE / 'root-launcher-loader-v11-independent-review/independent-source-review-v11.json',
    WHOLE / 'abi-memory-production-v1/source-packet-v1.json']
before = []
for packet in (basis[0], basis[2], basis[3]):
    for row in json.loads(packet.read_bytes())['files']:
        assert pin(Path(row['path'])) == row
        before.append(row)
suite = unittest.TestSuite()
for name, cls in (('test_envelope_v1.py', 'Controls'), ('test_root_environment_v1.py', 'RootEnvironmentControls'),
                  ('test_memory_bindings_v1.py', 'MemoryBindingControls')):
    namespace = runpy.run_path(str(HERE / name), run_name='pure_memory_' + cls)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[cls]))
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
(HERE / 'pure-controls-v1.log').write_text(output.getvalue())
assert result.testsRun == 22 and result.wasSuccessful() and not result.skipped
for row in before: assert pin(Path(row['path'])) == row
(HERE / 'pure-controls-v1.json').write_text(json.dumps({'date': '2026-10-16 ET', 'tests': 22,
    'failures': 0, 'errors': 0, 'skipped': 0, 'log': pin(HERE / 'pure-controls-v1.log'),
    'actual_child_native_compiler_solver_SSH_ABI_TU_or_observer_execution': False,
    'frozen_predecessor_rows_unchanged': len(before)}, sort_keys=True, indent=2) + '\n')
command = json.loads((HERE / 'command-v1.json').read_bytes())
outer = json.loads((HERE / 'envelope-policy-v1.json').read_bytes())
observer = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
assert outer['node'] is None and outer['guard_files'] is None and command['root_metadata_complete'] is False
assert len(outer['controls']) == 35 and len(observer['controls']) == 17 and observer['capture']['prepared'] is None
total = sum(row['bytes'] for row in outer['controls'].values()) + (HERE / 'envelope-policy-v1.json').stat().st_size
assert total == command['root_controls_bytes_including_policy'] == 718864
for name, row in command['stage_sources'].items():
    assert pin(Path(row['path'])) == row
    assert (row['bytes'], row['sha256']) == (outer['controls'][name]['bytes'], outer['controls'][name]['sha256'])
(HERE / 'root-argv-inert-v1.json').write_text(json.dumps(command['argv'], indent=2) + '\n')
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.name == 'source-packet-v1.json': continue
    if path.suffix == '.py': ast.parse(path.read_bytes())
    files.append(pin(path))
packet = {'schema': 'inert-memory-source-observer-envelope-source-packet-1', 'date': '2026-10-16 ET',
    'files': files, 'basis': [pin(path) for path in basis], 'tests': 22,
    'entry': pin(HERE / 'linux_memory_observation_envelope_v1.py'),
    'policy': pin(HERE / 'envelope-policy-v1.json'), 'command': pin(HERE / 'command-v1.json'),
    'observer_policy': pin(HERE / 'observation-policy-v1.json'),
    'exact_outer_inverse': pin(HERE / 'exact-envelope-inverse-v1.json'),
    'root_controls': 35, 'observer_controls': 17, 'observer_modules': 14,
    'root_control_bytes_including_policy': total,
    'actual_node_guard_role_selection_or_dispatch': False,
    'pending_root_fields': ['node', 'guard_files'],
    'root_source_proposal_provenance_is_review_or_authority': False,
    'all_outer_logic_resource_startup_source_runtime_and_finalization_checks_preserved': True,
    'memory_scientific_consumer_modified': False,
    'prepared_mapping_receiver_or_owned_context_fabricated': False,
    'actual_ABI_TU_source_native_proof_or_public_admission': False,
    'shared_Git_or_frozen_predecessor_mutated': False,
    'independent_review_exact_filled_policy_root_preflight_ABI_replay_and_admission_required': True}
(HERE / 'source-packet-v1.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v1.json',
    'entry': 'linux_memory_observation_envelope_v1.py', 'policy': 'envelope-policy-v1.json',
    'command': 'command-v1.json', 'observer_policy': 'observation-policy-v1.json'}.items()}, sort_keys=True))
