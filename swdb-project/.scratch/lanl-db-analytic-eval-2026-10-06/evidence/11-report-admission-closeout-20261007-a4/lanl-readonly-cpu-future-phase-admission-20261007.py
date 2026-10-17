"""Selected-record-only admission after parent supplies an accepted actual export.

Prepared 2026-10-07 ET. No Store, writer, index, test, native or provider call.
Parent's complete-export/cleanup handoff is a prerequisite. This local reader
checks compact receipts, exact bytes, scoped native samples and unchanged bands;
it does not inspect current remote host/process/lease/capacity state.
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
E = '887d9bfd319a08df20d6f6cf3571bde8db71406c'
MODEL_IDENTITY = 'ea12a575bf4c70cf77dbc436f1f1df17b54b03cfc944f11627424b1c45521fec'
MODEL_ADMISSION = 'fe2890f8e7d8c95d6841ddd78b61762667e07c02688567676aca5d8fc4f4e3bd'
TARGET = 'mbit10.cpu.lanl20261006.t1.services.v1'
TARGET_SHA = '9fec46b1ab4c8ac2e8e501e61cf137c075ec40b6eef128a247cf28dd54fca76b'
EVIDENCE = Path('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
CHARS = {
    'bfs.kron-g16.t1.characterization.objects.a1': '535d43719d2e9269dc557e900886c625b80c5aa686e7682861a4f6d045e143bc',
    'bc.kron-g16.t1.characterization.objects.a1': '8561948088366aa18409da1db1f204ac2579cdb8ee90f1a2c76079a96e2eb4fd',
    'bfs.kron-g17.t1.characterization.objects.a1': '49b5c58f3551b065c91c49c1fb09f54de2d2d71f08b6a4e1eedf3aad5ec415c5',
    'bc.kron-g17.t1.characterization.objects.a1': '6b8d515b3f38a13bfd302993f8ac5e88bd77615da171c710b4ecd81d058c67db',
}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, timeout=120).strip()


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def timestamp_ns(text):
    value = datetime.datetime.fromisoformat(text.replace('Z', '+00:00'))
    assert value.tzinfo is not None
    return int(value.timestamp() * 1_000_000_000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--phase', required=True, choices=('development', 'holdout', 'report'))
    parser.add_argument('--export-commit', required=True)
    parser.add_argument('--receipt-identity', required=True, help='actual sealed identity supplied by parent')
    parser.add_argument('--model-receipt', type=Path)
    parser.add_argument('--model-admission', type=Path, default=Path('/private/tmp/lanl-cpu-model-a3-local-admission-20261007.json'))
    parser.add_argument('--development-receipt', type=Path)
    parser.add_argument('--holdout-receipt', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.workspace.resolve()
    assert re.fullmatch('[0-9a-f]{40}', args.export_commit)
    assert re.fullmatch('[0-9a-f]{64}', args.receipt_identity)
    assert not args.output.exists(), 'preserve previous attempts'
    assert not git(root, 'status', '--porcelain'), 'clean accepted export or integration checkout required'
    assert git(root, 'merge-base', args.export_commit, 'HEAD') == args.export_commit
    assert git(root, 'rev-parse', args.export_commit + ':swdb-project/swdb') == git(root, 'rev-parse', C + ':swdb-project/swdb')
    assert git(root, 'diff', '--name-only', C, 'HEAD', '--', 'swdb-project/swdb') == ''
    sys.path.insert(0, str(root / 'swdb-project'))
    from swdb import access, artifacts, estimate_protocol
    from swdb import cpu_error_band, cpu_native_validation
    assert estimate_protocol.estimator_identity() == F6

    def sealed(value):
        assert value['identity_sha256'] == artifacts.digest({k: v for k, v in value.items() if k != 'identity_sha256'}), 'seal differs'
        return value

    model_path = args.model_receipt or root / EVIDENCE / '11-cpu-model-mbit10-20261006-a3.json'
    model_receipt = sealed(access.read_record(model_path))
    assert model_receipt['identity_sha256'] == MODEL_IDENTITY
    model = sealed(model_receipt['acceptance'])
    local = sealed(access.read_record(args.model_admission))
    assert local['identity_sha256'] == MODEL_ADMISSION and local['export_commit'] == E
    assert local['actual_acceptance_identity'] == model['identity_sha256']
    assert local['admitted_for_parent_development'] is True
    assert model['phase'] == 'model' and model['source_commit'] == C and model['estimator_sha256'] == F6
    assert model['application_performance_timings_collected'] is False and model['ready_for_development'] is True
    assert model['target_sha256'] == TARGET_SHA
    assert {x['id']: x['sha256'] for x in model['characterizations']} == CHARS
    expected_model_ids = {'lanl.cpu.' + k + '.g' + str(g) + '.t1.estimate.v1' for k in ('bfs', 'bc') for g in (16, 17)}
    assert len(model['estimates']) == 4 and {x['id'] for x in model['estimates']} == expected_model_ids
    assert all(finite_positive(x['seconds']) and x['evidence_kind'] == 'execution' and x['estimator_sha256'] == F6 for x in model['estimates'])

    records = root / 'swdb-project/records'
    by_id = {}
    for path, _ in access.record_files(records):
        by_id.setdefault(path.stem, []).append(path)
    known_pins = {p['id']: p for p in model_receipt['new_records']}
    # Recheck model canonical bytes from original admission, without reparsing all
    # four large estimates or revalidating the full catalog.
    for p in model_receipt['new_records']:
        path = records / p['path']
        assert path.stat().st_size == p['bytes'] and access.record_hash(path) == p['file_sha256']
    cache = {}
    checked = {}

    def read(rid, expected=None, *, retain=True):
        paths = by_id.get(rid, [])
        assert len(paths) == 1, 'missing or ambiguous selected ID: ' + rid
        path = paths[0]
        pin = known_pins.get(rid)
        if pin is not None:
            assert path.relative_to(records).as_posix() == pin['path']
            assert path.stat().st_size == pin['bytes'] and access.record_hash(path) == pin['file_sha256']
            expected = pin['sha256'] if expected is None else expected
        value = cache.get(rid)
        if value is None:
            value = access.read_record(path)
            assert value['id'] == rid
            if retain:
                cache[rid] = value
        actual = artifacts.digest(value)
        if expected is not None:
            assert actual == expected, 'selected canonical identity differs: ' + rid
        checked[rid] = actual
        return value

    def receipt(path, phase):
        wrapper = sealed(access.read_record(path))
        assert wrapper['source_commit'] == C and wrapper['source_clean'] is True and wrapper['raw_transferred'] is False
        lane = wrapper['lane']
        assert lane['node'] == 0 and lane['exit_code'] == 0 and lane['ended_utc'] and lane['numa_memory_policy'] == 'bind:0'
        accepted = sealed(wrapper['acceptance'])
        expected_phase = 'band_report' if phase == 'report' else phase
        assert accepted['phase'] == expected_phase and accepted['source_commit'] == C and accepted['source_clean'] is True
        assert accepted['raw_transferred'] is False and accepted['validation'].startswith('OK: ')
        assert accepted['application_performance_timings_collected'] is (phase != 'report')
        assert accepted['frozen_model_acceptance']['identity_sha256'] == model['identity_sha256']
        if phase != 'report':
            assert wrapper['phase'] == phase and accepted['protocols'] == model['protocols']
            assert wrapper['format'] == 'swdb.prospective-native-model-compact-receipt.v1'
            assert wrapper['prior_records_preserved'] == accepted['prior_record_bytes_preserved']
            for p in wrapper['new_records']:
                if p['id'] in known_pins:
                    assert known_pins[p['id']] == p
                known_pins[p['id']] = p
        else:
            assert wrapper['format'] == 'swdb.cpu-band-report-compact-receipt.v1'
            assert wrapper['application_performance_timings_collected'] is False
            assert wrapper['prior_heldout_records_preserved'] == accepted['prior_record_bytes_preserved']
            for p in wrapper['new_phase_records']:
                known_pins[p['id']] = p
        return wrapper, accepted

    stem = 'band-report' if args.phase == 'report' else args.phase
    selected_path = root / EVIDENCE / ('11-cpu-' + stem + '-mbit10-20261006-a3.json')
    selected, accepted = receipt(selected_path, args.phase)
    assert selected['identity_sha256'] == args.receipt_identity
    development = None
    holdout = None
    if args.phase in ('holdout', 'report'):
        assert args.development_receipt is not None
        _, development = receipt(args.development_receipt, 'development')
    if args.phase == 'report':
        assert args.holdout_receipt is not None
        _, holdout = receipt(args.holdout_receipt, 'holdout')
        assert accepted['heldout_acceptance']['identity_sha256'] == holdout['identity_sha256']

    target = read(TARGET, TARGET_SHA)
    binding = target['extensions']['cpu_services_binding']
    assert binding['calibrations'] == model['calibrations'] and binding['characterization_allowlist'] == model['characterizations']
    assert not [p for p in binding['compatibility'] if p['missing'] or any(s['missing'] for s in p.get('scopes', []))]
    # Old dependency bytes are protected by strict additive export over C; all
    # model new-record bytes above are independently matched to actual E.
    char_cache = {}
    protocols = {}
    for kernel, pin in model['protocols'].items():
        p = read(pin['id'], pin['sha256'])
        assert p['settings']['estimator_sha256'] == F6 and p['settings']['threads'] == 1
        assert p['settings']['target_description'] == {'id': TARGET, 'sha256': TARGET_SHA, 'snapshot': target}
        assert 'cpu_error_band' not in p['settings']
        protocols[kernel] = p

    class Context:
        def passed(self, rid, kind):
            value = read(rid)
            assert value['kind'] == kind
            return value

    def native_band(kernel, scale, band_pin):
        char_id = kernel + '.kron-g' + str(scale) + '.t1.characterization.objects.a1'
        char = char_cache.setdefault(char_id, read(char_id, CHARS[char_id]))
        original_id = 'lanl.cpu.' + kernel + '.g' + str(scale) + '.t1.estimate.v1'
        original_pin = next(p for p in model['estimates'] if p['id'] == original_id)
        validation_id = 'lanl.cpu.' + kernel + '.g' + str(scale) + '.t1.validation.v1'
        v = sealed(read(validation_id))
        assert v['kind'] == 'cpu_native_validation' and v['evidence_kind'] == 'native' and v['backend'] == 'native'
        errors = list(cpu_native_validation.validate_record(SimpleNamespace(data=v, rel=validation_id), Context()))
        assert not errors, [str(p) for p in errors]
        assert v['target'] == 'mbit10' and v['context']['commit'] == C and v['context']['dirty'] is False
        assert v['context']['timing_started_ns'] > timestamp_ns(model['completed_utc'])
        assert timestamp_ns(protocols[kernel]['frozen_at']) < v['context']['timing_started_ns']
        assert v['scope']['roi'] == 'gapbs.trial_lambda.v1' and v['scope']['trial_count'] == 5
        assert v['context']['cpus'] == [0], 'exact node0 physical T1 core required'
        values = [t['printed_duration_s'] for t in v['trials']]
        assert all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in values)
        assert v['summary']['median_whole_call_s'] == statistics.median(values)
        assert v['summary']['rounding_half_width_s'] == .000005
        native = v['summary']['median_whole_call_s']
        e = read(original_id, original_pin['sha256'], retain=False)
        assert e['seconds'] == original_pin['seconds'] and e['error_band'] is None
        assert e['target'] == v['target'] and e['input'] == v['input'] and e['subject']['id'] == v['implementation']
        assert e['characterization'] == v['characterization'] and e['characterization_sha256'] == v['characterization_sha256']
        assert v['estimate_protocol'] == {'id': protocols[kernel]['id'], 'sha256': artifacts.digest(protocols[kernel]), 'estimator_sha256': F6, 'target_description_sha256': TARGET_SHA}
        b = sealed(read(band_pin['id'], band_pin['sha256']))
        assert b['kind'] == 'cpu_error_band' and b['evidence_kind'] == 'native' and b['backend'] == 'native'
        assert b['threads'] == 1 and b['target_description_sha256'] == TARGET_SHA and b['estimator_sha256'] == F6
        assert b['state'] == band_pin['state'] and b['width_log'] == band_pin['width_log'] and b['admission'] == band_pin['admission']
        assert len(b['pairs']) == 1 and b['frozen_ns'] >= v['context']['finished_ns']
        pair = b['pairs'][0]
        assert pair['estimate'] == original_id and pair['estimate_sha256'] == original_pin['sha256']
        assert pair['validation'] == validation_id and pair['validation_sha256'] == artifacts.digest(v)
        assert pair['characterization'] == char_id and pair['characterization_sha256'] == CHARS[char_id]
        assert pair['input'] == char['input'] and pair['scope'] == cpu_error_band._source_scope(char)
        assert pair['regions'] == e['regions'] and pair['predicted_seconds'] == e['seconds'] and pair['native_seconds'] == native
        initial_missing = ['positive_resolved_native_time'] if native <= 0 else ['printed_time_resolution'] if native <= .000005 else []
        error = None if initial_missing else math.log(e['seconds']) - math.log(native)
        worst = None if initial_missing else max(abs(math.log(e['seconds']) - math.log(native-.000005)), abs(math.log(e['seconds']) - math.log(native+.000005)))
        assert pair['log_error'] == error and pair['rounding_aware_absolute_log_error'] == worst
        assert b['admission']['missing'] == sorted(set(pair['missing']))
        if scale == 16:
            assert b['id'] == 'lanl.cpu.' + kernel + '.t1.development-band.v1'
            assert b['state'] == ('failed' if initial_missing else 'development') and b['development_band'] is None
            assert b['width_log'] == worst and pair['missing'] == initial_missing and b['admission']['validated'] is False
            assert v['development_band'] is None
        else:
            assert development is not None
            dev = sealed(read(development['bands'][kernel]['id'], development['bands'][kernel]['sha256']))
            assert b['id'] == 'lanl.cpu.' + kernel + '.t1.heldout-band.v1'
            assert b['development_band'] == v['development_band'] == dev['id']
            assert b['width_log'] == dev['width_log'] and pair['scope'] == dev['pairs'][0]['scope']
            assert dev['state'] == 'development' and type(dev['width_log']) in (int, float) and math.isfinite(dev['width_log']) and dev['width_log'] >= 0
            assert v['input'] != dev['pairs'][0]['input']
            # Both per-kernel development widths must freeze before either g17.
            assert v['context']['timing_started_ns'] > max(read(p['id'], p['sha256'])['frozen_ns'] for p in development['bands'].values())
            expected_missing = initial_missing + (['empirical_holdout_outside_frozen_width'] if worst is not None and worst > dev['width_log'] else [])
            assert pair['missing'] == expected_missing
            passed = not expected_missing
            assert b['state'] == ('validated' if passed else 'failed') and b['admission']['validated'] is passed and b['admission']['holdout_passed'] is passed
        result = {'kernel': kernel, 'scale': scale, 'validation': validation_id, 'validation_sha256': artifacts.digest(v), 'predicted_seconds': e['seconds'], 'native_median_seconds': native, 'native_trial_seconds': values, 'printed_half_width_s': .000005, 'log_error': error, 'rounding_aware_absolute_log_error': worst, 'band': b['id'], 'band_sha256': artifacts.digest(b), 'width_log': b['width_log'], 'state': b['state'], 'validated': b['admission']['validated'], 'missing': pair['missing'], 'timing_started_ns': v['context']['timing_started_ns'], 'timing_finished_ns': v['context']['finished_ns'], 'band_frozen_ns': b['frozen_ns'], 'estimate_regions_sha256': artifacts.digest(e['regions'])}
        del e
        return result

    outcomes = []
    if args.phase != 'report':
        scale = 16 if args.phase == 'development' else 17
        assert set(accepted['bands']) == {'bfs', 'bc'}
        expected_phase = {'lanl.cpu.' + k + '.g' + str(scale) + '.t1.validation.v1' for k in ('bfs', 'bc')} | {accepted['bands'][k]['id'] for k in ('bfs', 'bc')}
        pins = selected['new_records']
        assert len(pins) == 4 and {p['id'] for p in pins} == expected_phase
        assert sorted(p['kind'] for p in pins) == ['cpu_error_band'] * 2 + ['cpu_native_validation'] * 2
        for kernel in ('bfs', 'bc'):
            outcomes.append(native_band(kernel, scale, accepted['bands'][kernel]))
        if args.phase == 'development':
            assert accepted['ready_for_holdout'] is all(x['state'] == 'development' and x['width_log'] is not None for x in outcomes)
    else:
        assert holdout is not None and development is not None
        assert accepted['target_sha256'] == TARGET_SHA and accepted['calibrations'] == model['calibrations'] and accepted['characterizations'] == model['characterizations']
        assert accepted['original_estimates'] == model['estimates'] and accepted['new_phase_records'] == 4
        assert len(accepted['reports']) == 2 and set(accepted['protocols']) == {'bfs', 'bc'}
        pins = selected['new_phase_records']
        assert len(pins) == 4 and sorted(p['kind'] for p in pins) == ['estimate', 'estimate', 'protocol', 'protocol']
        assert {p['id'] for p in pins} == {r['id'] for r in accepted['reports']} | {p['id'] for p in accepted['protocols'].values()}
        for kernel in ('bfs', 'bc'):
            outcome = native_band(kernel, 17, holdout['bands'][kernel])
            band = read(outcome['band'], outcome['band_sha256'])
            assert accepted['bands'][kernel] == {k: v for k, v in {'id': band['id'], 'sha256': artifacts.digest(band), 'state': band['state'], 'width_log': band['width_log'], 'validated': band['admission']['validated']}.items()}
            dev_pin = development['bands'][kernel]
            assert accepted['development_bands'][kernel] == {'id': dev_pin['id'], 'sha256': dev_pin['sha256'], 'width_log': dev_pin['width_log']}
            p = read(accepted['protocols'][kernel]['id'], accepted['protocols'][kernel]['sha256'])
            old_p = protocols[kernel]
            assert p['state'] == 'frozen' and p['requested_id'] == 'lanl.cpu.' + kernel + '.t1.report-model.v1'
            for field in ('estimator_sha256', 'target_description', 'inputs', 'input_run_arguments', 'sources', 'roi', 'threads'):
                assert p['settings'][field] == old_p['settings'][field]
            assert p['settings']['cpu_error_band'] == {'id': band['id'], 'sha256': artifacts.digest(band), 'snapshot': band}
            for rid, expected in p['settings']['cpu_error_band_dependencies'].items():
                read(rid, expected, retain=False)
            row = next(x for x in accepted['reports'] if x['id'] == 'lanl.cpu.' + kernel + '.g17.t1.report.v1')
            old = read(row['original_estimate'], row['original_estimate_sha256'], retain=False)
            report = read(row['id'], row['sha256'], retain=False)
            assert row['original_estimate'] == 'lanl.cpu.' + kernel + '.g17.t1.estimate.v1'
            for field in ('seconds', 'regions', 'subject', 'input', 'threads', 'target', 'evidence_kind', 'characterization', 'characterization_sha256', 'target_description_sha256', 'estimator_sha256'):
                assert report[field] == old[field], 'report changed scientific field: ' + field
            assert report['protocol'] == p['id'] and report['protocol_sha256'] == p['identity_sha256']
            assert row['seconds_unchanged'] is True and row['per_region_costs_unchanged'] is True
            assert row['per_region_costs_sha256'] == artifacts.digest(report['regions'])
            error_band = report['error_band']
            assert error_band == row['error_band']
            assert error_band['id'] == band['id'] and error_band['sha256'] == artifacts.digest(band)
            assert error_band['state'] == band['state'] and error_band['width_log'] == band['width_log']
            assert error_band['validated'] is (band['state'] == 'validated' and band['admission']['validated'] is True)
            assert error_band['missing'] == band['admission']['missing']
            assert report['verdict'] == row['verdict'] == 'within_error'
            outcome.update(report=row['id'], report_sha256=row['sha256'], seconds_unchanged=True, regions_unchanged=True, reported_validated=error_band['validated'])
            outcomes.append(outcome)
            del old, report

    # Parent exports include previous canonical additions but only the current
    # compact phase receipt; C's authoritative records must never be modified.
    expected_paths = {'swdb-project/records/' + p['path'] for p in model_receipt['new_records']}
    if development is not None:
        for kernel in ('bfs', 'bc'):
            for rid in ('lanl.cpu.' + kernel + '.g16.t1.validation.v1', development['bands'][kernel]['id']):
                expected_paths.add('swdb-project/records/' + by_id[rid][0].relative_to(records).as_posix())
    if holdout is not None:
        for kernel in ('bfs', 'bc'):
            for rid in ('lanl.cpu.' + kernel + '.g17.t1.validation.v1', holdout['bands'][kernel]['id']):
                expected_paths.add('swdb-project/records/' + by_id[rid][0].relative_to(records).as_posix())
    expected_paths |= {'swdb-project/records/' + p['path'] for p in pins}
    expected_paths.add(selected_path.relative_to(root).as_posix())
    changes = git(root, 'diff', '--name-status', C, args.export_commit).splitlines()
    assert all(line.startswith('A\t') for line in changes)
    assert {line.split('\t', 1)[1] for line in changes} == expected_paths, 'strict additive export contains unexpected changes'
    # Current integration can contain unrelated later additions; selected export
    # bytes must nevertheless remain exact, including its compact receipt.
    for path in expected_paths:
        expected_blob = git(root, 'rev-parse', args.export_commit + ':' + path)
        assert git(root, 'hash-object', root / path) == expected_blob
    assert not git(root, 'status', '--porcelain')
    result = {'format': 'swdb.cpu-future-phase-local-readonly-admission.v1', 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': args.phase, 'source_commit': C, 'estimator_sha256': F6, 'export_commit': args.export_commit, 'workspace_head': git(root, 'rev-parse', 'HEAD'), 'actual_compact_receipt_identity': selected['identity_sha256'], 'actual_acceptance_identity': accepted['identity_sha256'], 'frozen_model_acceptance_identity': model['identity_sha256'], 'prior_model_local_admission_identity': MODEL_ADMISSION, 'selected_records_checked': checked, 'strict_additive_export_paths': sorted(expected_paths), 'full_validation': {'scope': 'parent actual public receipt, not repeated locally', 'result': accepted['validation']}, 'outcomes': outcomes, 'native_or_provider_or_remote_invocations': 0, 'store_or_writer_or_index_invocations': 0, 'application_timing_read_scope': 'Only accepted compact canonical five-trial native validation records; no raw logs, binaries or measured region timing', 'scope': 'Two separate exact T1 original-driver per-kernel workload bands only; no unseen scope or protected-driver transfer. Failed heldout band remains failed with original width.', 'admitted': True}
    result['identity_sha256'] = artifacts.digest(result)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'identity_sha256': result['identity_sha256'], 'outcomes': outcomes}, indent=2))


if __name__ == '__main__':
    main()
