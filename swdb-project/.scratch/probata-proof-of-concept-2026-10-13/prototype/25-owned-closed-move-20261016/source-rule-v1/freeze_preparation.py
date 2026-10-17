"""2026-10-16 ET. Freeze reviewed source inputs and pure preparation metadata."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
POC = HERE.parents[2]


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, sort_keys=True)+'\n').encode())


def main():
    root = Path('/private/tmp/probata-t25-owned-move-source-green-v9')
    result = json.loads((root/'result.json').read_bytes())
    assert result['passed'] == 6 and result['failed'] == 0 and not result['child_native_network_attempts']
    for row in result['source_pins']:
        assert pin(PROJECT/'swdb'/row['path'])['sha256'] == row['sha256']
    source_paths = [PROJECT/name for name in ('swdb/vector_owned_move_source.py',
        'tests/test_vector_owned_move_source.py', 'tests/testkit/vector_owned_move.py',
        'tests/fixtures/proof/lowering/vector_owned_transfer.cc')]
    assert (root/'test_owned_move.py').read_bytes() == source_paths[1].read_bytes()
    assert (root/'testkit/vector_owned_move.py').read_bytes() == source_paths[2].read_bytes()
    assert pin(source_paths[-1])['sha256'] == 'a0dc043284f96a5b7c052963b51188318ae4abc6a85ee347fea78b6ab392d3a2'
    for path in source_paths[:3]+[HERE/'run_pure.py', HERE/'freeze_preparation.py']:
        compile(ast.parse(path.read_bytes()), str(path), 'exec')
    canonical = root/'test_closed_move_derives_source_local_transfer_scalar_and_reverse_cleanup/packet'
    data = (canonical/'sources/original-caller.c').read_bytes()
    assert len(data) == 5642 and hashlib.sha256(data).hexdigest() == '5c33a1a1843045d0b9d2ba43eb8d590c9e6106c794982286b28505c64e896e34'
    manifest = json.loads((canonical/'manifest.json').read_bytes())
    assert manifest['source_admission'] is False and manifest['source_typed_bridge_established'] is False
    target = HERE/'inert-v1'
    shutil.copytree(canonical, target)
    history = HERE/'history'; history.mkdir()
    observations = []
    for stage in ('red-v1', 'green-v1', 'red-v2', 'green-v2', 'red-v3', 'green-v3',
                  'green-v4', 'red-v4', 'green-v5', 'green-v6', 'green-v7', 'green-v8', 'red-v5', 'green-v9'):
        old = Path('/private/tmp/probata-t25-owned-move-source-'+stage)
        observed = json.loads((old/'result.json').read_bytes())
        directory = history/stage; directory.mkdir()
        for name, original in [('result.json', old/'result.json'), ('public-test.py', old/'test_owned_move.py'),
                               ('source-module.py', old/'swdb/vector_owned_move_source.py')]:
            if original.exists():
                shutil.copyfile(original, directory/name)
        observations.append({'stage': stage, 'passed': observed['passed'], 'failed': observed['failed'],
                             'child_native_network_attempts': observed['child_native_network_attempts'],
                             'result': pin(directory/'result.json')})
    original_evidence = POC/'evidence/t25-owned-move-compiler-v1-actual-decision-20261016.json'
    census_evidence = POC/'evidence/t25-owned-move-compiler-v1-source-event-census-20261016.json'
    census = json.loads(census_evidence.read_bytes())
    assert [row['normalized_sha256'] for row in census['C_event_inventory']] == [
        row['normalized_sha256'] for row in manifest['source_events']['lowered']]
    assert len(manifest['cfg']['original_anchors']) == 17
    canonical_rows = [pin(path) for path in sorted(target.rglob('*')) if path.is_file()]
    packet = {'date': '2026-10-16 ET', 'classification': 'FROZEN_CLOSED_MOVE_SOURCE_RULE_PREPARATION',
        'public_inputs': [pin(path) for path in source_paths],
        'preparation_sources': [pin(HERE/name) for name in ('run_pure.py', 'freeze_preparation.py', 'README.md')],
        'actual_compiler_metadata_inputs': [pin(original_evidence), pin(census_evidence)],
        'canonical': canonical_rows,
        'canonical_files': len(canonical_rows), 'canonical_bytes': sum(row['bytes'] for row in canonical_rows),
        'public_functional_case_results': observations,
        'complete_original_C_reconstruction': {'bytes': 5642, 'sha256': hashlib.sha256(data).hexdigest(),
            'equals_retained_G641_original_C': True, 'actual_raw_transfer': False,
            'seventeen_anchors': True, 'normalized_statement_hashes': 12,
            'actual_full_Lowering_metadata_or_provenance_replay': False},
        'compiler_boundary': 'Real immutable Lowering dataclass and pure original model renderer; reconstructed byte-identical C with explicitly synthetic library provenance. Normal public builder still uses the real selected lowerer.',
        'dependency_targets': {name: len(value['targets']) for name, value in manifest['scientific_dependencies'].items()},
        'source_Heap_Typed_caller_or_default_admission': False,
        'scientific_execution_or_acceptance': False, 'public_proof_record_created': False,
        'new_production_edits': [str(path) for path in source_paths[:3]],
        'required_existing_untracked_fixture_for_parent_publication': pin(source_paths[3]),
        'scope': 'Checked exact conditional source/effect/scalar/cleanup derivation. Complete scientific context and source/Heap composition remain required; public launch always refuses.'}
    write(HERE/'source-packet.json', packet)
    receipt = {'date': '2026-10-16 ET', 'classification': 'PREPARATION_COMPLETE; INDEPENDENT_STANDARDS_AND_SPEC_REQUIRED',
        'packet': pin(HERE/'source-packet.json'), 'public_sources': packet['public_inputs'],
        'final_pure_result': pin(history/'green-v9/result.json'), 'final_log': pin(HERE/'green-v9.log'),
        'passed': 6, 'failed': 0, 'child_native_network_attempts': [],
        'syntax_checked': [str(path) for path in source_paths[:3]],
        'actual_compiler_metadata_inputs': packet['actual_compiler_metadata_inputs'],
        'complete_C_reconstruction': packet['complete_original_C_reconstruction'],
        'canonical_files': len(canonical_rows), 'canonical_bytes': packet['canonical_bytes'],
        'canonical_manifest': pin(target/'manifest.json'),
        'dependency_targets': packet['dependency_targets'], 'TDD_history': observations,
        'author_harness_history': [
            {'kind': 'pre-harness interpreter closure failure', 'log': pin(HERE/'red-v1.log'), 'scope': 'Default Python lacked pytest before any harness output or test; genuine public missing-module RED is separately retained.'},
            {'kind': 'input-shape counterexample and repair', 'stage': 'red-v4', 'scope': 'Initial synthetic source omitted real printer anchors between fallback calls. Complete token-offset CFG edits replaced the whitespace-only locator. Full seventeen-anchor/byte-identical C was then reconstructed.'},
            {'kind': 'test change-detector issue', 'stage': 'green-v7', 'scope': 'Dataclass equality equated false and zero before the negative API call; canonical JSON now preserves exact input type. Production signature validation already preserved the Boolean.'},
            {'kind': 'parent semantic review finding and genuine public regression', 'stage': 'red-v5', 'scope': 'Inserted same-line ACSL assume false kept executable tokens and anchors but was accepted. Exact whole original C pin now rejects every added annotation; final GREEN9 passes.'}],
        'fixture_a0dc_required_for_publication': True,
        'no_Git_SSH_compiler_native_verifier_solver_or_scientific_execution': True,
        'all_source_Heap_Typed_caller_admission_false': True}
    path = POC/'evidence/t25-owned-move-source-rule-preparation-v1-20261016.json'
    write(path, receipt)
    print(json.dumps({'preparation': pin(path), 'packet': pin(HERE/'source-packet.json'),
                      'sources': packet['public_inputs'], 'canonical': {'files': len(canonical_rows), 'bytes': packet['canonical_bytes']}}, indent=2))


if __name__ == '__main__':
    main()
