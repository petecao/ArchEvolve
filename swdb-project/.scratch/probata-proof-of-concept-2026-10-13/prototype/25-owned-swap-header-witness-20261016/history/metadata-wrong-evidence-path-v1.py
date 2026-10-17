"""2026-10-16 ET. Freeze exact Header3 witness source-preparation metadata."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
POC = HERE.parents[1]


def pin(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular physical source/evidence required: '+str(path))
    raw = path.read_bytes()
    return {'path': str(path.relative_to(PROJECT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, value):
    with path.open('x') as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def main():
    green = json.loads((HERE/'history/green-v4/result.json').read_bytes())
    if (green['passed'], green['failed'], green['external_native_attempts']) != (4, 0, []):
        raise ValueError('the exact four final public controls must pass without children')
    inputs = []
    for expected in green['source_pins']:
        row = pin(PROJECT/'swdb'/expected['path'])
        if (row['bytes'], row['sha256']) != (expected['bytes'], expected['sha256']):
            raise ValueError('final source differs from actual pure controls')
        inputs.append(row)
    public_test = pin(PROJECT/'tests/test_vector_owned_swap_header_witness.py')
    if public_test['sha256'] != green['test_sha256']:
        raise ValueError('final test differs from actual pure controls')
    canonical = json.loads((HERE/'canonical-files-v1.json').read_bytes())
    actual = []
    for path in sorted((HERE/'inert-all-types-v1').rglob('*')):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('canonical special entry refused')
        if path.is_file():
            row = pin(path); row['path'] = str(path.relative_to(HERE/'inert-all-types-v1'))
            actual.append(row)
    if actual != canonical['files'] or len(actual) != 48 or \
            sum(row['bytes'] for row in actual) != canonical['total_bytes']:
        raise ValueError('canonical full membership changed')
    stages = []
    for path in sorted((HERE/'history').glob('*/result.json')):
        data = json.loads(path.read_bytes())
        if data['external_native_attempts'] or data['actual_formal_run']:
            raise ValueError('pure history must contain no native attempts')
        stages.append({'stage': path.parent.name, 'passed': data['passed'],
                       'failed': data['failed'], 'result': pin(path)})
    historical = []
    for name, expected in (
        ('t25-owned-swap-header3-public-v1-producer-settlement-20261016.json',
         'bcb3c7c94e7f3e209787b26bca6d655515d6c7d8cd8c265c316744057335831b'),
        ('t25-owned-swap-header3-public-v1-native-diagnostics-001-stdout-20261016.json',
         '45b17f7a7485c0ad561e96fe75d086863e0178a250b3e35291fa880d30caa00c'),
        ('t25-owned-swap-header3-public-v1-complete-settlement-001-stdout-20261016.json',
         '43452f8b9465c900c9621f83fd61b6357fd4acaa8d95b651a9c9d3c4f458244a')):
        row = pin(POC/'evidence/resume-20261016-lane-coordination'/name)
        if row['sha256'] != expected:
            raise ValueError('original G644 retained evidence changed')
        historical.append(row)
    outputs = [pin(PROJECT/'swdb/vector_owned_swap_header_witness.py'), public_test]
    outputs += [pin(path) for path in sorted(HERE.rglob('*')) if path.is_file()]
    packet = {
        'date': '2026-10-16 ET', 'scope': 'inert stronger Header3 constructive witnesses',
        'observed_publication_baseline': '001df353dc4aa46ab43c395997b760fb2b203ab2',
        'source_inputs': inputs, 'outputs': outputs, 'tdd_stages': stages,
        'canonical_count': len(actual), 'canonical_total_bytes': canonical['total_bytes'],
        'targets': 3, 'unchanged_inherited_files': 41, 'original_cases_retained': 3,
        'physical_predecessor_containers': 7, 'kernel_definition_slices': 19,
        'original_g644_evidence': historical,
        'full_original_quantifiers_antecedent_guards_active_ready_preserved': True,
        'self_swap_guard_overlap_preserved': True,
        'capture_free_typed_existential_introduction': True,
        'complete_old_case_statement_inverse_checked': True,
        'stronger_goals_equivalent_to_original_claimed': False,
        'all_three_stronger_proofs_required': True,
        'added_caller_requires': [], 'sibling_theorem_premises': [],
        'new_axioms': [], 'bounds_increased': False,
        'original_g644_outcome': 'all three old cases unproved; Alt-Ergo Failed / CVC5 Unknown / Z3 Timeout per case',
        'original_alt_ergo_failure_cause_resolved': False,
        'actual_formal_run': False, 'mathematical_admission': False,
        'source_heap_typed_body_caller_default_public_record_admission': False,
        'launch': 'unconditionally refused after canonical public check',
        'review_state': 'pending parent independent Spec and root Standards',
        'authoring_history_note': 'The wrong-root author helper refused before module edits; green-v2 retained one failure on unchanged source. Corrected green-v2b passed. No result was relabeled.'}
    path = HERE/'source-packet-v1.json'; write(path, packet)
    preparation = {'date': '2026-10-16 ET', 'packet': pin(path),
        'module': outputs[0], 'test': public_test,
        'derivation': pin(HERE/'derivation-v1.json'),
        'pure_final_controls': pin(HERE/'history/green-v4/result.json'),
        'canonical': pin(HERE/'canonical-files-v1.json'),
        'state': 'frozen source preparation, awaiting independent reviews',
        'actual_formal_run': False, 'scientific_admission': False,
        'source_body_caller_admission': False, 'old_g644_raw_preserved': True,
        'shared_hooks_theories_trackers_git_index_unchanged': True}
    receipt = POC/'evidence/t25-owned-swap-header-witness-source-preparation-v1-20261016.json'
    write(receipt, preparation)
    print(json.dumps({'packet': pin(path), 'preparation': pin(receipt),
        'module': outputs[0], 'test': public_test, 'frozen_file_pins': len(inputs)+len(outputs)+len(historical)}))


if __name__ == '__main__':
    main()
