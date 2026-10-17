"""2026-10-16 ET. Scratch-only integration from applied V5; no Git/import/run."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
REPOSITORY = PROJECT.parent
OLD = WHOLE / 'production-route-v4'
MEMORY = WHOLE / 'memory-normalized-ingress-v2'
ABI = WHOLE / 'abi-role-transport-v2'
OBSERVER = WHOLE / 'normalized-unit-envelope-v4'
OUT = HERE / 'proposed'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


assert PROJECT.name == 'swdb-project'
expected = json.loads((OLD / 'production-paths-and-bases-v4.json').read_bytes())['paths']
applied = []
for row in expected:
    path = REPOSITORY / row['path']
    actual = pin(path)
    assert (actual['bytes'], actual['sha256']) == (row['proposal']['bytes'], row['proposal']['sha256']), row['path']
    applied.append(actual)
assert len(applied) == 50

origins = {
    'swdb/dx100_checked_source.py': MEMORY / 'integration-source/dx100_checked_source.py',
    'swdb/_dx100_whole/normalized_compiler_adapter_v1.py': ABI / 'normalized_compiler_adapter_v2.py',
    'swdb/_dx100_whole/normalized_capture_ingress_v2.py': OBSERVER / 'observer/modules/normalized_capture_ingress_v2.py',
}
for name in ('abi_role_transport_v1.py', 'strict_minify_v2.py', 'capture_family_dispatch_v1.py',
             'memory_normalized_compiler_adapter_v1.py', 'memory_normalized_capture_ingress_v1.py',
             'memory_source_preparation_v1.py', 'memory_capture_facts_v1.json'):
    origins['swdb/_dx100_whole/' + name] = MEMORY / 'proposed' / name

rows = []
patch = []
for relative, source in sorted(origins.items()):
    target = PROJECT / relative
    old = b''
    base = None
    if target.exists() or target.is_symlink():
        assert not target.is_symlink() and target.resolve(strict=True) == target and stat.S_ISREG(target.lstat().st_mode)
        old = target.read_bytes()
        base = pin(target)
        path = HERE / 'base-source' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(old)
    else:
        assert relative not in {row['path'].removeprefix('swdb-project/') for row in expected}
    new = source.read_bytes()
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(new)
    if path.suffix == '.py': ast.parse(new)
    label = 'swdb-project/' + relative
    patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
        fromfile='a/' + label if base else '/dev/null', tofile='b/' + label))
    rows.append({'relative': relative, 'base': base, 'proposal': pin(path), 'reviewed_source': pin(source),
        'shared_written': False})
assert sum(row['base'] is not None for row in rows) == 3 and len(rows) == 10
(HERE / 'abi-memory-production-v1.patch').write_text(''.join(patch))
write_json(HERE / 'production-paths-and-bases-v1.json', {'schema': 'scratch-ABI-memory-production-paths-1',
    'date': '2026-10-16 ET', 'paths': rows, 'applied_V5_observed_rows': applied,
    'shared_fresh_overlap_check_before_apply_required': True,
    'published_source_commit_or_final_producer_basis_inferred': False})

inverses = {
    'swdb/dx100_checked_source.py': json.loads((MEMORY / 'source-family-hook-inverse-v2.json').read_bytes())['replacements'],
    'swdb/_dx100_whole/normalized_compiler_adapter_v1.py': json.loads((ABI / 'adapter-inverse-v1.json').read_bytes())['replacements'],
    'swdb/_dx100_whole/normalized_capture_ingress_v2.py': json.loads((OBSERVER / 'exact-inverses-v4.json').read_bytes())['files']['observer/modules/normalized_capture_ingress_v2.py']['replacements'],
}
for relative, edits in inverses.items():
    text = (OUT / relative).read_text()
    for edit in reversed(edits):
        assert text.count(edit['new']) == edit.get('count', 1)
        text = text.replace(edit['new'], edit['old'])
    assert text.encode() == (HERE / 'base-source' / relative).read_bytes(), relative
write_json(HERE / 'exact-source-inverses-v1.json', {'schema': 'ABI-memory-integration-source-inverses-1',
    'files': inverses, 'generic_compiler_and_every_nonselected_path_unchanged': True,
    'finite_hook_files_not_written': ['cbmc_adapter.py', 'formal_frame.py', 'proof_semantics.py', 'proof_setup.py']})

# This is a member/path recipe, deliberately not a basis with stale final hashes.
# The final root-selected finite successor may add members or change existing
# hooks. Its exact reviewed list must be unioned before any byte basis is emitted.
old_basis = json.loads((OLD / 'profile/normal-producer-basis-v4.json').read_bytes())
baseline = sorted(row['relative'] for row in old_basis['files'])
added = sorted(row['relative'] for row in rows if row['base'] is None)
members = sorted(set(baseline) | set(added))
assert len(baseline) == 54 and len(added) == 7 and len(members) == 61
recipe = {'schema': 'prospective-ABI-memory-producer-member-recipe-1', 'date': '2026-10-16 ET',
    'old_basis_is_only_a_member_source': pin(OLD / 'profile/normal-producer-basis-v4.json'),
    'old_basis_hashes_are_not_new_basis_hashes': True, 'baseline_member_paths': baseline,
    'ABI_memory_added_paths': added, 'source_unit_member_paths_before_final_finite_union': members,
    'source_unit_member_count_before_final_finite_union': 61,
    'modified_existing_members': sorted(row['relative'] for row in rows if row['base'] is not None),
    'final_reviewed_finite_member_paths_and_packet': None,
    'final_root_selected_source_commit': None, 'final_producer_basis': None,
    'steps': [
        'Root chooses and applies independently reviewed ABI/memory and finite successors after a fresh physical overlap check.',
        'Take the unique sorted union of these61 members and every exact selected finite producer/read/exec member; no glob-based omission or callback.',
        'Validate the actual source.producer_paths and finite producer/read/exec maps against that selected physical root; include package aliases and fixed basis reads.',
        'Hash the final selected physical bytes only after every hook has settled, using canonical regular/no-link shape and stable before/after metadata.',
        'Emit a separately versioned basis and builder BASIS_SHA; rebuild the normal source snapshot, library producer_manifest, method and all physical entry/context bindings.',
        'Keep the full swdb/vocab census gate and actual method recomputation; refuse any subsequent source or member mismatch before launch.'
    ],
    'no_basis_regenerated_or_old_digest_reused': True,
    'unready_memory_capture_prepared_mapping_receiver_and_context': None}
write_json(HERE / 'producer-member-recipe-v1.json', recipe)
for row in applied: assert pin(Path(row['path'])) == row
print(json.dumps({'production_paths': len(rows), 'modified': 3, 'new': 7,
    'all_applied_V5_rows_unchanged': 50, 'source_member_recipe_before_finite_union': 61,
    'final_producer_basis': None, 'shared_written': False}, sort_keys=True))
