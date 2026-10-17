"""2026-10-16 ET. Freeze the source-only memory ABI inlet; no actual replay."""
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


basis = [WHOLE / 'memory-normalized-ingress-v1/source-packet-v1.json',
    WHOLE / 'abi-role-transport-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2-independent-review/independent-abi-v2-source-review-20261016.json',
    WHOLE / 'production-route-v5/source-packet-v5.json',
    WHOLE / 'normalized-unit-envelope-v4/source-packet-v4.json']
before = []
for packet in basis[:2]:
    for row in json.loads(packet.read_bytes())['files']:
        assert pin(Path(row['path'])) == row
        before.append(row)
namespace = runpy.run_path(str(HERE / 'test_memory_family_v2.py'), run_name='pure_memory_ABI_successor_controls')
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE / 'pure-controls-v2.log').write_text(output.getvalue())
assert result.testsRun == 18 and result.wasSuccessful() and not result.skipped
for row in before: assert pin(Path(row['path'])) == row
(HERE / 'pure-controls-v2.json').write_text(json.dumps({'date': '2026-10-16 ET', 'tests': 18, 'failures': 0,
    'errors': 0, 'skipped': 0, 'log': pin(HERE / 'pure-controls-v2.log'),
    'actual_retained_ABI_TU_body_or_source_program_interpreted': False,
    'compiler_native_verifier_SSH_child_network_or_installed_project_import': False,
    'explicit_tiny_TU_and_ABI_protocol_fixtures_only': True,
    'predecessor_and_ABI_source_pin_rows_unchanged': len(before)}, sort_keys=True, indent=2) + '\n')
policy = json.loads((HERE / 'observer/observation-policy-template-v1.json').read_bytes())
staging = json.loads((HERE / 'observer-staging-plan-v2.json').read_bytes())
manifest = json.loads((HERE / 'observer/fixed-memory-modules-v1.json').read_bytes())
assert len(manifest['modules']) == 14 and len(policy['controls']) == 17
assert sum(row['bytes'] for row in policy['controls'].values()) == 256522
assert policy['capture']['prepared'] is None and policy['root_admission_receipt'] is None
for row in staging['controls'].values(): assert pin(Path(row['path'])) == row
missing = {'actual_retained_G642_ABI_replay': {
    'state': 'required before dispatch; exact 29-root/four-role eligibility is prospective until genuine artifact passes',
    'original': namespace['FACTS']['original']['abi'],
    'source_helper_reviewed': True, 'actual_call_eligibility_inferred': False},
    'actual_memory_observer': {'root_admission_receipt': None, 'outer_runtime_envelope': None,
        'new_compiler_or_byte_transform_required': False},
    'body_and_public': {'mapping_receipts': {name: None for name in (
        'whole_same_thread_read_during_store', 'whole_same_thread_write_during_gather', 'whole_same_thread_read_during_gather')},
        'alignment_or_ownership_inferred': False, 'owned_runtime_context_receiver_fresh_library_and_method': None}}
(HERE / 'missing-inputs-v2.json').write_text(json.dumps(missing, sort_keys=True, indent=2) + '\n')
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.name == 'source-packet-v2.json': continue
    if path.suffix == '.py': ast.parse(path.read_bytes())
    files.append(pin(path))
packet = {'schema': 'prospective-memory-normalized-ABI-source-family-packet-2', 'date': '2026-10-16 ET',
    'files': files, 'basis': [pin(path) for path in basis],
    'proposed': {path.name: pin(path) for path in sorted((HERE / 'proposed').iterdir()) if path.is_file()},
    'source_route_hook_patch': pin(HERE / 'source-family-hook-proposal-v2.patch'),
    'source_route_base': 'Exact inherited SourceUnit V4/V5 proposal; no shared application.',
    'observer_entry': pin(HERE / 'observer/observe_memory_entry_v1.py'),
    'observer_policy': pin(HERE / 'observer/observation-policy-template-v1.json'),
    'observer_modules': 14, 'observer_controls': 17, 'observer_control_bytes': 256522,
    'root_original_project': '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
    'actual_public_runtime_cwd': '/data1/yanruj/probata-resume-20261016-2baf722f',
    'tests': 18, 'source_inverse': pin(HERE / 'successor-inverse-v2.json'),
    'ABI_helper_reviewed_source': pin(WHOLE / 'abi-role-transport-v2/abi_role_transport_v1.py'),
    'original_G642_ABI_and_derived_input_identities_distinct': True,
    'all_ingress_functions_selection_and_body_consumers_unchanged': True,
    'first_source_transport_or_ABI_family_not_admitted_by_memory_adapter': True,
    'shared_frozen_or_Git_mutated': False, 'scientific_execution': False,
    'actual_retained_ABI_eligibility_and_observer_dispatch_pending': True,
    'mapping_context_receiver_prepared_or_results_fabricated': False,
    'public_admission': False, 'whole_ticket28_acceptance': False}
(HERE / 'source-packet-v2.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v2.json',
    'adapter': 'proposed/memory_normalized_compiler_adapter_v1.py',
    'ingress': 'proposed/memory_normalized_capture_ingress_v1.py',
    'observer': 'observer/observe_memory_entry_v1.py', 'policy': 'observer/observation-policy-template-v1.json'}.items()}, sort_keys=True))
