"""Freeze the coherent source-only patch. No Git, child or project import."""
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
PROJECT = WHOLE.parents[3]


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


runpy.run_path(str(HERE / 'build_patch_v4.py'), run_name='source_only_exact_patch')
namespace = runpy.run_path(str(HERE / 'test_composition_v4.py'), run_name='source_only_composition_controls')
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['CompositionControls']))
(HERE / 'pure-controls-v4.log').write_text(stream.getvalue())
assert result.testsRun == 21 and result.wasSuccessful() and not result.skipped
(HERE / 'pure-controls-v4.json').write_text(json.dumps({'tests': 21, 'failures': 0, 'errors': 0, 'skipped': 0,
    'no_child_project_import_compiler_native_solver_SSH_Git_or_actual_TU_preparation': True,
    'protocol_doubles': ['Library constructor and checked-body normalization', 'native projection text emission',
        'actual tool stdout and subprocess protocol in extracted orchestration'],
    'log': pin(HERE / 'pure-controls-v4.log')}, sort_keys=True, indent=2) + '\n')
origins = json.loads((HERE / 'draft-component-origins-v4.json').read_bytes())
for row in origins['files']:
    destination, original = HERE / row['path'], WHOLE / row['origin']
    assert destination.read_bytes() == original.read_bytes()
    assert pin(destination)['sha256'] == row['sha256']
published = json.loads((HERE / 'published-hook-bases-v4.json').read_bytes())
for row in published['files']:
    path = PROJECT / row['path']
    assert (pin(path)['bytes'], pin(path)['sha256']) == (row['bytes'], row['sha256'])
api = {}
for name in ('dx100_checked_source.py', 'dx100_checked_adapter.py', 'dx100_checked_native.py'):
    text = (HERE / 'proposed/swdb' / name).read_text()
    api[name] = {node.name: ast.unparse(node.args) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
(HERE / 'api-v4.json').write_text(json.dumps({'schema': 'checked-source-proposal-api-4', 'functions': api,
    'source_unit_is_not_finite_model_trace': True,
    'finite_next_seam': 'separately discriminated immutable TraceUnit/event-Plan with its own exact selection, receiver, model and native claim',
    'no_source_cpp_projection_for_generated_model_trace': True}, sort_keys=True, indent=2) + '\n')
basis_names = [
    'production-route-v3/source-packet-v3.json',
    'checked-contracts-v2/checked-contracts-source-packet-v2.json',
    'source-unit-registry-v2/source-packet-v2.json',
    'runtime-projection-v3/runtime-projection-source-packet-v3.json',
    'runtime-projection-v4/runtime-projection-source-packet-v4.json',
    'normalized-ingress-v2/source-packet-v2.json',
    'first-source-resources-v2/source-packet-v2.json',
    'public-profile-builder-v2/source-packet-v2.json',
    'public-profile-planner-v2/source-packet-v2.json',
    'source-memory-selection-v1/source-packet-v1.json',
    'receiver-memory-v1/source-packet-v1.json',
    'runtime-projection-v4/independent-runtime-projection-v4-review-20261016.json',
    'public-profile-builder-v2/independent-contract-formatter-v2-review-20261016.json',
    'normalized-ingress-v2/independent-ingress-v2-source-review-20261016.json',
    'first-source-resources-v2-independent-review/independent-source-review-v2.json',
    'production-route-v3-independent-review/independent-review-v3.json']
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path == HERE / 'source-packet-v4.json': continue
    files.append(pin(path))
paths = json.loads((HERE / 'production-paths-and-bases-v4.json').read_bytes())
assert len(paths['paths']) == 50
packet = {'schema': 'coherent-checked-source-production-proposal-4', 'date': '2026-10-16 ET',
    'source_base_commit': published['source_commit'], 'files': files,
    'basis': [pin(WHOLE / name) for name in basis_names],
    'patch': pin(HERE / 'production-route-v4.patch'),
    'production_paths_and_exact_bases': pin(HERE / 'production-paths-and-bases-v4.json'),
    'six_hook_bases': published['files'], 'proposed_paths': 50,
    'normal_producer_basis': pin(HERE / 'profile/normal-producer-basis-v4.json'),
    'normal_producer_count': 54,
    'profile_builder': pin(HERE / 'profile/profile_builder_v3.py'),
    'profile_prepare': pin(HERE / 'profile/profile_prepare_v3.py'),
    'pair_plan': pin(HERE / 'profile/pair_plan_v2.py'),
    'tests': 21, 'shared_production_written': False, 'Git_mutated': False,
    'compiler_native_solver_or_actual_source_preparation_executed': False,
    'public_admission': False, 'root_fresh_overlap_check_apply_publish_and_actual_admission_required': True,
    'first79_80_scientific_gates_pending': ['actual complete source/ABI/call observation',
        'owned receiver/runtime/context', 'normal source publication and method identity',
        'both actual public proofs and persisted cold criteria'],
    'memory_registry_rows': 'closed explicit unsupported capture; no prepared or owned receiver receipt',
    'whole_ticket28_acceptance': False}
(HERE / 'source-packet-v4.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v4.json',
    'patch': 'production-route-v4.patch', 'paths': 'production-paths-and-bases-v4.json',
    'source': 'proposed/swdb/dx100_checked_source.py', 'adapter': 'proposed/swdb/dx100_checked_adapter.py',
    'builder': 'profile/profile_builder_v3.py'}.items()}, sort_keys=True))
