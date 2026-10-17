"""2026-10-16 ET. Freeze the scratch-only ABI/memory production proposal."""
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


paths = json.loads((HERE / 'production-paths-and-bases-v1.json').read_bytes())
before = paths['applied_V5_observed_rows']
for row in before: assert pin(Path(row['path'])) == row
namespace = runpy.run_path(str(HERE / 'test_integration_v1.py'), run_name='pure_ABI_memory_integration_controls')
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['IntegrationControls']))
(HERE / 'pure-controls-v1.log').write_text(output.getvalue())
assert result.testsRun == 8 and result.wasSuccessful() and not result.skipped
for row in before: assert pin(Path(row['path'])) == row
(HERE / 'pure-controls-v1.json').write_text(json.dumps({'date': '2026-10-16 ET', 'tests': 8,
    'failures': 0, 'errors': 0, 'skipped': 0, 'log': pin(HERE / 'pure-controls-v1.log'),
    'applied_V5_rows_physically_unchanged': 50,
    'installed_project_child_native_compiler_prover_SSH_or_scientific_execution': False}, sort_keys=True, indent=2) + '\n')
basis = [WHOLE / 'production-route-v5/source-packet-v5.json',
    WHOLE / 'memory-normalized-ingress-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2/source-packet-v2.json',
    WHOLE / 'abi-role-transport-v2-independent-review/independent-abi-v2-source-review-20261016.json',
    WHOLE / 'normalized-unit-envelope-v4/source-packet-v4.json',
    WHOLE / 'normalized-unit-envelope-v4-independent-review/independent-envelope-v4-spec-review-20261016.json']
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.name == 'source-packet-v1.json': continue
    if path.suffix == '.py': ast.parse(path.read_bytes())
    files.append(pin(path))
packet = {'schema': 'scratch-ABI-memory-production-integration-proposal-1', 'date': '2026-10-16 ET',
    'files': files, 'basis': [pin(path) for path in basis], 'tests': 8,
    'patch': pin(HERE / 'abi-memory-production-v1.patch'),
    'production_paths_and_bases': pin(HERE / 'production-paths-and-bases-v1.json'),
    'source_inverses': pin(HERE / 'exact-source-inverses-v1.json'),
    'producer_member_recipe': pin(HERE / 'producer-member-recipe-v1.json'),
    'production_paths': 10, 'modified_existing': 3, 'new_paths': 7,
    'base_state': 'Exact applied coherent V5 working-tree bytes; no Git/commit state queried.',
    'source_unit_member_recipe_before_final_finite_union': 61,
    'final_reviewed_finite_packet_or_regenerated_producer_basis': None,
    'all50_applied_V5_source_files_unchanged': True,
    'finite_four_hook_files_and_WP_Claude_work_untouched': True,
    'private_observer_helper_or_origin_metadata_promoted': False,
    'old54_member_basis_reused_as_new_identity': False,
    'prepared_memory_context_receiver_or_results_fabricated': False,
    'shared_Git_or_frozen_predecessor_written': False,
    'root_fresh_base_check_independent_review_apply_publish_regeneration_and_actual_admission_required': True,
    'actual_scientific_execution_or_public_admission': False}
(HERE / 'source-packet-v1.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v1.json',
    'patch': 'abi-memory-production-v1.patch', 'paths': 'production-paths-and-bases-v1.json',
    'recipe': 'producer-member-recipe-v1.json', 'source': 'proposed/swdb/dx100_checked_source.py'}.items()}, sort_keys=True))
