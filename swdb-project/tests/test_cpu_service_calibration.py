"""Native service calibration through public commands. Created: 2026-10-06 ET."""
import hashlib
import json

import pytest

from conftest import run_swdb


def save_receipt(tmp_path, data):
    data['identity_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    path = tmp_path / 'service-receipt.json'
    path.write_text(json.dumps(data))
    return path


def fixture_receipt():
    return {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'fixture',
        'machine': 'mbit10', 'threads': 1,
        'context': {'compiler_version': 'hand fixture', 'architecture': 'fixture'},
        'settings': {'repetitions': 3},
        'services': [{'id': 'clock.now', 'unit': 'seconds/call',
            'event_definition': 'One system_clock::now call; hand fixture only.',
            'scope': {'worker_scope': 'serial', 'cache_state': 'warm'},
            'denominator': {'level': 'source_normalized_work', 'basis': 'reported',
                'proof': 'Hand-computed fixture, not native count evidence.'},
            'trials': [{'events': 10, 'gross_seconds': seconds, 'driver_seconds': 1.0,
                'order': order} for seconds, order in [(2.0, 'service_first'),
                    (2.2, 'driver_first'), (1.8, 'service_first')]]}]}


def test_import_service_fixture_retains_paired_trials_and_reported_cost(records, tmp_path):
    result = run_swdb('import-cpu-service-calibration', '--records', records.path,
        '--receipt', save_receipt(tmp_path, fixture_receipt()), '--id', 'fixture.clock.cost',
        '--fixture', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data['kind'] == 'cpu_service_calibration' and data['evidence_kind'] == 'fixture'
    service = data['services'][0]
    assert service['parameter'] == {'value': .1, 'basis': 'reported',
        'source': 'Service calibration fixture.clock.cost; clock.now; paired elapsed/work trials.',
        'unit': 'seconds/call'}
    assert service['seconds_per_event']['spread'] == pytest.approx(.04)
    assert service['seconds_per_event']['repetitions'] == 3
    assert [t['driver_seconds'] for t in service['trials']] == [1.0, 1.0, 1.0]
    checked = run_swdb('validate', '--records', records.path)
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_unresolved_paired_subtraction_keeps_unknown_cost_without_clamping(records, tmp_path):
    data = fixture_receipt()
    for trial, gross in zip(data['services'][0]['trials'], [.9, 1.2, 1.0]):
        trial['gross_seconds'] = gross
    result = run_swdb('import-cpu-service-calibration', '--records', records.path,
        '--receipt', save_receipt(tmp_path, data), '--id', 'fixture.unresolved.cost',
        '--fixture', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    service = json.loads(result.stdout)['services'][0]
    assert service['parameter']['value'] is None and service['parameter']['basis'] == 'unknown'
    assert service['seconds_per_event']['min'] == pytest.approx(-.01)
    assert 'subtraction' in service['missing'][0]


def test_portable_service_runner_is_bounded_and_imports_only_as_fixture(records, tmp_path):
    output = tmp_path / 'services'
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--output', output,
        '--fixture', '--repetitions', '3', '--min-trial-s', '.002', '--max-wall-s', '60')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'receipt.json').read_text())
    assert data['evidence_kind'] == 'fixture' and data['threads'] == 1
    assert data['services'][0]['id'] == 'clock.now'
    assert len(data['services'][0]['trials']) == 3
    assert all(t['events'] > 0 and t['gross_seconds'] > 0 and t['driver_seconds'] > 0
               for t in data['services'][0]['trials'])
    imported = run_swdb('import-cpu-service-calibration', '--records', records.path,
        '--receipt', output / 'receipt.json', '--id', 'fixture.runner.service', '--fixture', '--format', 'json')
    assert imported.returncode == 0, imported.stdout + imported.stderr
    parameter = json.loads(imported.stdout)['services'][0]['parameter']
    assert parameter['basis'] in {'reported', 'unknown'}
    excessive = run_swdb('cpu-service-calibrate', '--records', records.path,
        '--output', tmp_path / 'unbounded', '--fixture', '--max-wall-s', '901')
    assert excessive.returncode != 0 and not (tmp_path / 'unbounded').exists()


def test_portable_clock_receipt_binds_separate_source_normalized_call_counts(records, tmp_path, llvm22):
    records.copy_repo()
    output = tmp_path / 'counted-service'
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--output', output,
        '--fixture', '--llvm-bin', llvm22, '--repetitions', '3', '--min-trial-s', '.002',
        '--max-wall-s', '120')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'receipt.json').read_text())
    proof = data['services'][0]['denominator']['proof']
    assert proof['pipeline']['version'] == 'source-normalized-v2'
    assert proof['service_validation_points'] == [[32, 32], [64, 64], [96, 96]]
    assert proof['driver_validation_points'] == [[32, 0], [64, 0], [96, 0]]
    assert proof['source_sha256'] == data['context']['source_sha256']['CpuServiceWork.h']
    assert len(proof['characterization_sha256']) == 6
    assert data['context']['instrumented_timer'] is False
    assert data['evidence_kind'] == 'fixture'


def test_service_runner_records_explicit_fixture_target_and_rejects_native_on_wrong_host(records, tmp_path):
    output = tmp_path / 'fixture-target'
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--output', output,
        '--machine', 'fixture.target', '--fixture', '--repetitions', '3', '--min-trial-s', '.002', '--max-wall-s', '60')
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads((output / 'receipt.json').read_text())
    assert receipt['machine'] == 'fixture.target' and receipt['evidence_kind'] == 'fixture'
    refused = run_swdb('cpu-service-calibrate', '--records', records.path,
        '--output', tmp_path / 'native-refused', '--machine', 'fixture.target', '--lane', '0')
    assert refused.returncode != 0 and not (tmp_path / 'native-refused').exists()


def test_count_only_service_receipt_contains_no_elapsed_calibration(records, tmp_path, llvm22):
    records.copy_repo()
    output = tmp_path / 'count-only'
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--output', output,
        '--fixture', '--llvm-bin', llvm22, '--count-only', '--max-wall-s', '120')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'count-proof.json').read_text())
    assert data['format'] == 'swdb.cpu-service-count-only.v1'
    assert data['timings_collected'] is False and 'services' not in data
    assert data['count_proof']['service_validation_points'] == [[32,32], [64,64], [96,96]]
    assert not (output / 'receipt.json').exists() and not (output / 'partial-trials.json').exists()
    refused = run_swdb('import-cpu-service-calibration', '--records', records.path,
        '--receipt', output / 'count-proof.json', '--id', 'fixture.counts.never.rate', '--fixture')
    assert refused.returncode != 0
