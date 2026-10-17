"""Local selected-record admission after the actual parent model export succeeds.

No Store, writer, generated index, native command or provider is invoked. The
parent's receipt retains the full-catalog validation; this script independently
checks immutable bytes/pins and the four trial-composed forecasts.
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

sys.dont_write_bytecode = True
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
TARGET = 'mbit10.cpu.lanl20261006.t1.services.v1'
RECEIPT = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-cpu-model-mbit10-20261006-a3.json'
CHARS = {
    'bfs.kron-g16.t1.characterization.objects.a1': '535d43719d2e9269dc557e900886c625b80c5aa686e7682861a4f6d045e143bc',
    'bc.kron-g16.t1.characterization.objects.a1': '8561948088366aa18409da1db1f204ac2579cdb8ee90f1a2c76079a96e2eb4fd',
    'bfs.kron-g17.t1.characterization.objects.a1': '49b5c58f3551b065c91c49c1fb09f54de2d2d71f08b6a4e1eedf3aad5ec415c5',
    'bc.kron-g17.t1.characterization.objects.a1': '6b8d515b3f38a13bfd302993f8ac5e88bd77615da171c710b4ecd81d058c67db',
}
CALIBRATIONS = {'mbit10.cpu.lanl20261006.' + suffix for suffix in (
    'service.clock.a2', 'resource.allocator.a1', 'resource.allocator-extra.a1',
    'resource.memory.a1', 'resource.float-memory.a1', 'service.byte-read.a1',
    'resource.bulk-total.a1', 'resource.bulk-total.a2', 'service.openmp.a1')}
A1 = '8ddb9825fb7ccefff7088ea550af290379f8ea48744065b9d156196b7947db5a'
A2 = 'f12b499ff1a82dc31e5b03411ee90458ba12411c11dece9b066420be0b30f0a7'


def git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args], text=True, timeout=120).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--export-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace.resolve()
    assert git(root, 'rev-parse', 'HEAD') == args.export_commit
    assert not git(root, 'status', '--porcelain'), 'use the clean actual export checkout'
    sys.path.insert(0, str(root / 'swdb-project'))
    from swdb import access, artifacts, bfs_protocol, estimate_protocol
    from swdb.analytic_binding import counted_payload
    assert estimate_protocol.estimator_identity() == F6

    def sealed(data):
        assert data['identity_sha256'] == artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})
        return data

    receipt = sealed(access.read_record(root / RECEIPT))
    assert receipt['format'] == 'swdb.prospective-native-model-compact-receipt.v1'
    assert receipt['phase'] == 'model' and receipt['source_commit'] == C and receipt['source_clean'] is True
    assert receipt['raw_transferred'] is False and receipt['matched_native_observations'] == []
    lane = receipt['lane']
    assert lane['node'] == 0 and lane['exit_code'] == 0 and lane['ended_utc'] and lane['numa_memory_policy'] == 'bind:0'
    accepted = sealed(receipt['acceptance'])
    assert accepted['source_commit'] == C and accepted['source_clean'] is True and accepted['phase'] == 'model'
    assert accepted['estimator_sha256'] == F6 and accepted['ready_for_development'] is True
    assert accepted['application_performance_timings_collected'] is False and accepted['raw_transferred'] is False
    assert accepted['validation'].startswith('OK: ') and receipt['prior_records_preserved'] == accepted['prior_record_bytes_preserved'] == 665
    custody = sealed(receipt['failure_custody'])
    original = sealed(receipt['original_a1_failure_custody'])
    assert custody['identity_sha256'] == A2 and original['identity_sha256'] == A1
    for document in (custody, original):
        assert document['source_commit'] == C and document['phase'] == 'model'
        assert document['cause'] == 'metadata_processing_cap' and document['application_performance_timings_collected'] is False
    continuation = accepted['continuation']
    assert continuation['failure_custody_identity'] == A2 and continuation['original_a1_failure_custody_identity'] == A1
    assert continuation['scientific_recipe_changed'] is False and continuation['native_or_provider_commands'] == 0
    assert continuation['preserved_complete_record_files'] == custody['completed_record_files']
    assert len(custody['completed_record_files']) == 667
    assert all(custody['completed_record_files'].get(p) == h for p, h in original['completed_record_files'].items())
    assert continuation['metadata_invocations'] and continuation['metadata_invocations'][-1]['stage'] == 'validate'
    for invocation in continuation['metadata_invocations']:
        assert invocation['exit_code'] == 0 and invocation['argv'][:3] == ['python3', '-m', 'swdb']
        assert invocation['argv'][3] in {'freeze-protocol', 'estimate', 'validate'}

    pins = receipt['new_records']
    assert len(pins) == 7 and sorted(p['kind'] for p in pins) == ['estimate'] * 4 + ['protocol'] * 2 + ['target_description']
    expected_paths = {RECEIPT, *['swdb-project/records/' + p['path'] for p in pins]}
    changes = git(root, 'diff', '--name-status', C, args.export_commit).splitlines()
    assert len(changes) == 8 and all(line.startswith('A\t') for line in changes)
    assert {line.split('\t', 1)[1] for line in changes} == expected_paths, 'export must be strictly additive over C'
    records = root / 'swdb-project/records'
    for relative, expected in custody['completed_record_files'].items():
        assert access.record_hash(records / relative) == expected
    by_id = {}
    for path, relative in access.record_files(records):
        by_id.setdefault(path.stem, []).append(path)
    pin_by_id = {p['id']: p for p in pins}

    def read(rid, expected=None):
        paths = by_id[rid]
        assert len(paths) == 1, 'ambiguous canonical filename: ' + rid
        path = paths[0]
        if rid in pin_by_id:
            pin = pin_by_id[rid]
            assert path.relative_to(records).as_posix() == pin['path']
            assert path.stat().st_size == pin['bytes'] and access.record_hash(path) == pin['file_sha256']
            expected = pin['sha256'] if expected is None else expected
        data = access.read_record(path)
        assert data['id'] == rid
        if expected is not None:
            assert artifacts.digest(data) == expected, 'canonical pin mismatch: ' + rid
        return data

    target = read(TARGET, accepted['target_sha256'])
    assert target['threads'] == 1
    binding = target['extensions']['cpu_services_binding']
    assert binding['calibrations'] == accepted['calibrations'] and binding['characterization_allowlist'] == accepted['characterizations']
    assert {p['id'] for p in binding['calibrations']} == CALIBRATIONS and len(binding['calibrations']) == 9
    assert {p['id']: p['sha256'] for p in binding['characterization_allowlist']} == CHARS
    assert all(not row['missing'] and all(not s['missing'] for s in row.get('scopes', [])) for row in binding['compatibility'])
    assert binding['transfer_basis'] == 'inferred' and binding['timings_rerun'] is False
    assert binding['memory_selection']['footprint_bytes'] == 8388608
    assert binding['memory_selection']['cas_policy'] == 'max_constructed_success_failure_median'
    assert binding['bulk_selection']['profile_policy'] == 'max_constructed_profiles_median'
    assert binding['allocator_resource_selection'] == {'recipe': 'gross_allocator_loop_resource_v1', 'composition': 'max_with_counted_compute_resource', 'paired_rates_used': False}
    for pin in binding['calibrations']:
        read(pin['id'], pin['sha256'])
    base = binding['base']
    read(base['id'], base['sha256'])
    chars = {rid: read(rid, digest) for rid, digest in CHARS.items()}
    for char in chars.values():
        assert char['evidence_kind'] == 'execution' and char['binding']['state'] == 'verified' and char['binding']['threads'] == 1
        assert char['binding']['execution_receipt']['counted_payload_sha256'] == artifacts.digest(counted_payload(char))
    assert set(accepted['protocols']) == {'bfs', 'bc'}
    protocols = {}
    dependencies = {}
    for kernel, pin in accepted['protocols'].items():
        p = read(pin['id'], pin['sha256'])
        bfs_protocol.verify_immutable(p)
        assert p['kind'] == 'protocol' and p['state'] == 'frozen' and p['requested_id'] == 'lanl.cpu.' + kernel + '.t1.native-model.v1'
        settings = p['settings']
        assert settings['threads'] == 1 and settings['mode'] == 'estimated' and settings['estimator_sha256'] == F6
        assert settings['target_description'] == {'id': TARGET, 'sha256': artifacts.digest(target), 'snapshot': target}
        assert 'cpu_error_band' not in settings
        selected = [chars[kernel + '.kron-g' + str(g) + '.t1.characterization.objects.a1'] for g in (16, 17)]
        assert set(settings['inputs']) == {c['input'] for c in selected}
        assert settings['input_run_arguments'] == {c['input']: c['source']['run_arguments'] for c in selected}
        assert settings['sources'] == [selected[0]['subject']['id']] and selected[0]['subject'] == selected[1]['subject']
        assert settings['roi'] == 'gapbs.trial_lambda.v1' and all(c['binding']['roi'] == settings['roi'] for c in selected)
        assert set(p['input_identities']) == set(settings['inputs']) and set(p['source_identities']) == set(settings['sources'])
        for rid, digest in {**p['input_identities'], **p['source_identities']}.items():
            read(rid, digest)
        assert all(p['input_identities'][c['input']] == c['binding']['input_record_sha256'] for c in selected)
        for rid, digest in settings['dependency_identities'].items():
            if rid in dependencies:
                assert dependencies[rid] == digest
            else:
                read(rid, digest)
                dependencies[rid] = digest
        protocols[kernel] = p
    assert protocols['bfs']['id'] != protocols['bc']['id']
    assert protocols['bfs']['settings']['dependency_identities'] == protocols['bc']['settings']['dependency_identities']
    assert protocols['bfs']['id'] == 'lanl.cpu.bfs.t1.native-model.v1.c74c7a1046e0e5f1'
    assert access.record_hash(by_id[protocols['bfs']['id']][0]) == 'ff538076ca2048c03672e7dcd1a7046895bed05b41be05979ec3e7493f8f4d5b'

    forecasts = []
    expected_estimates = {'lanl.cpu.' + k + '.g' + str(g) + '.t1.estimate.v1' for k in ('bfs', 'bc') for g in (16, 17)}
    assert len(accepted['estimates']) == 4 and {r['id'] for r in accepted['estimates']} == expected_estimates
    for row in accepted['estimates']:
        e = read(row['id'], row['sha256'])
        kernel = e['id'].split('.')[2]
        scale = int(e['id'].split('.')[3][1:])
        char = chars[kernel + '.kron-g' + str(scale) + '.t1.characterization.objects.a1']
        p = protocols[kernel]
        assert e['protocol'] == p['id'] and e['protocol_sha256'] == p['identity_sha256']
        assert e['estimator_sha256'] == F6 and e['threads'] == 1 and e['evidence_kind'] == 'execution'
        assert e['characterization'] == char['id'] and e['characterization_sha256'] == CHARS[char['id']]
        assert e['subject'] == char['subject'] and e['input'] == char['input'] and e['binding'] == char['binding']
        assert e['target_description_snapshot'] == target and e['target_description_sha256'] == accepted['target_sha256']
        assert e['seconds'] == row['seconds'] and type(e['seconds']) in (int, float) and math.isfinite(e['seconds']) and e['seconds'] > 0
        assert e['error_band'] is None and e['baseline'] is None and e['ratio'] is None
        trials = e['trials']
        assert len(trials) == 5 and [t['position'] for t in trials] == list(range(5))
        for trial, observed in zip(trials, char['trials']):
            assert trial['sources'] == observed['sources']
            assert type(trial['seconds']) in (int, float) and math.isfinite(trial['seconds']) and trial['seconds'] > 0
            for region in trial['regions']:
                assert region['state'] == 'known' and math.isfinite(region['seconds']) and region['seconds'] >= 0
                for component in region['bounds'] + region['overheads']:
                    assert component['state'] == 'known' and not component['missing'] and math.isfinite(component['seconds']) and component['seconds'] >= 0
                composed = max((b['seconds'] for b in region['bounds']), default=0.0) + sum(b['seconds'] for b in region['overheads'])
                assert math.isclose(region['seconds'], composed, rel_tol=1e-12, abs_tol=1e-15)
            assert math.isclose(trial['seconds'], sum(r['seconds'] for r in trial['regions']), rel_tol=1e-12, abs_tol=1e-15)
        assert e['seconds'] == statistics.median(t['seconds'] for t in trials)
        scopes = e['extensions']['legacy_trial_scope_reconciliations']
        assert len(scopes) == 5 and [r['position'] for r in scopes] == list(range(5))
        execution = char['binding']['execution_receipt']
        assert all(s['basis'] == 'inferred' and s['characterization_sha256'] == CHARS[char['id']] and s['counted_payload_sha256'] == execution['counted_payload_sha256'] and s['runtime_source_sha256'] == execution['runtime_source_sha256'] for s in scopes)
        forecasts.append({'kernel': kernel, 'scale': scale, 'threads': 1, 'predicted_seconds': e['seconds'], 'trial_predicted_seconds': [t['seconds'] for t in trials], 'estimate': e['id'], 'sha256': row['sha256'], 'model_admission': 'supported_conditional_constructed_resources', 'native_seconds': None, 'error_band': None})

    proof = {'format': 'swdb.cpu-model-local-readonly-admission.v1', 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_commit': C, 'export_commit': args.export_commit, 'estimator_sha256': F6, 'actual_compact_receipt_identity': receipt['identity_sha256'], 'actual_acceptance_identity': accepted['identity_sha256'], 'target_sha256': accepted['target_sha256'], 'protocols': accepted['protocols'], 'new_record_pins': pins, 'recursive_protocol_dependencies_checked': len(dependencies), 'prior_record_bytes_preserved': 665, 'a2_complete_records_preserved': 667, 'full_catalog_validation': {'kind': 'parent_actual_receipt', 'result': accepted['validation']}, 'local_scope': 'Selected canonical records, dependency pins, immutable prior bytes, scope proofs and trial composition only; no full Store/validation or execution.', 'application_performance_timings_collected': False, 'forecasts': sorted(forecasts, key=lambda r: (r['kernel'], r['scale'])), 'admitted_for_parent_development': True, 'scope': 'Exact four original-driver T1 BF/BC scopes. Constructed gross resources and compatibility transfers remain inferred. No physical latency, residency, upper-bound, accuracy or validated-band claim.'}
    proof['identity_sha256'] = artifacts.digest(proof)
    assert not args.output.exists(), 'preserve every prior admission attempt'
    args.output.write_text(json.dumps(proof, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'proof': str(args.output), 'identity_sha256': proof['identity_sha256'], 'forecasts': proof['forecasts']}, indent=2))


if __name__ == '__main__':
    main()
