"""Independent allocator cells through public commands. Created: 2026-10-06 ET."""
import json

from conftest import run_swdb


def test_allocator_runner_retains_split_exact_size_costs_and_bounded_payload(records, tmp_path):
    output = tmp_path / 'allocator'
    result = run_swdb('cpu-service-calibrate', '--records', records.path,
        '--service-group', 'allocator', '--size', '8', '--size', '65536',
        '--output', output, '--fixture', '--repetitions', '3',
        '--min-trial-s', '.002', '--max-wall-s', '120')
    assert result.returncode == 0, result.stdout + result.stderr
    raw = json.loads((output / 'receipt.json').read_text())
    assert raw['evidence_kind'] == 'fixture'
    assert len(raw['services']) == 8
    assert {s['scope']['size_bytes'] for s in raw['services']} == {8, 65536}
    assert {s['scope']['operation'] for s in raw['services']} == {
        'new_array', 'delete_array', 'new_scalar', 'delete_scalar'}
    assert raw['settings']['live_payload_cap_bytes'] == 64 * 1024**2
    assert raw['settings']['count_build_cap_bytes'] == 64 * 1024**2
    assert raw['settings']['timed_data_cap_bytes'] == 25 * 1024**2
    for service in raw['services']:
        assert service['scope']['transfer_basis'] == 'inferred'
        assert service['scope']['allocator_regime'] == 'fresh_process_repeated_allocate_free_batches'
        assert len(service['trials']) == 3
        assert all(t['events'] == t['batch_events'] * t['batches'] and
            t['gross_seconds'] > 0 and t['driver_seconds'] > 0 and
            t['batch_events'] * service['scope']['size_bytes'] <= 64 * 1024**2
            for t in service['trials'])
    imported = run_swdb('import-cpu-service-calibration', '--records', records.path,
        '--receipt', output / 'receipt.json', '--id', 'fixture.allocator.costs',
        '--fixture', '--format', 'json')
    assert imported.returncode == 0, imported.stdout + imported.stderr
    checked = run_swdb('validate', '--records', records.path)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    refused = run_swdb('cpu-service-calibrate', '--records', records.path,
        '--service-group', 'allocator', '--size', '536870912',
        '--output', tmp_path / 'excessive', '--fixture')
    assert refused.returncode != 0 and not (tmp_path / 'excessive').exists()


def test_allocator_count_only_binds_exact_abis_and_never_collects_elapsed(records, tmp_path, llvm22):
    records.copy_repo('applications', 'kernels', 'implementations', 'inputs', 'machines',
        'profiles', 'hardware_configs', 'strategies')
    output = tmp_path / 'allocator-counts'
    result = run_swdb('cpu-service-calibrate', '--records', records.path,
        '--service-group', 'allocator', '--size', '8', '--output', output,
        '--fixture', '--llvm-bin', llvm22, '--count-only', '--max-wall-s', '180')
    assert result.returncode == 0, result.stdout + result.stderr
    raw = json.loads((output / 'count-proof.json').read_text())
    assert raw['timings_collected'] is False
    assert not (output / 'receipt.json').exists() and not (output / 'partial-trials.json').exists()
    assert raw['context']['optimized_event_proof']['retained_event_abis'] == [
        '_Znam', '_ZdaPv', '_Znwm', '_ZdlPv']
    points = raw['count_proof']['points']
    assert len(points) == 16
    assert {(p['events'], p['opaque_events']) for p in points if p['invoke']} == {(3, 3), (5, 5)}
    assert {(p['events'], p['opaque_events']) for p in points if not p['invoke']} == {(3, 0), (5, 0)}
    assert {p['event_abi'] for p in points} == {'_Znam', '_ZdaPv', '_Znwm', '_ZdlPv'}
    assert all(p['event_size_bins'] == [{'bytes':8, 'events':p['events']}] for p in points if p['invoke'])
    assert all(p['event_size_bins'] == [] for p in points if not p['invoke'])



def test_count_build_budget_fails_closed_preserves_sealed_points_and_never_raises_timed_cap(records, tmp_path, llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines',
        'profiles','hardware_configs','strategies')
    output=tmp_path/'small-build-budget'
    result=run_swdb('cpu-service-calibrate','--records',records.path,'--service-group','allocator',
        '--size','8','--fixture','--llvm-bin',llvm22,'--count-only',
        '--count-build-cap-mib','1','--max-wall-s','120','--output',output)
    assert result.returncode!=0 and 'count-build artifacts exceed' in result.stderr
    assert list((output/'count-records/workload_characterizations').glob('*.yaml'))
    assert not (output/'count-proof.json').exists() and not (output/'receipt.json').exists()
    refused=run_swdb('cpu-service-calibrate','--records',records.path,'--service-group','allocator',
        '--fixture','--count-build-cap-mib','65','--output',tmp_path/'too-large-build-budget')
    assert refused.returncode!=0 and not (tmp_path/'too-large-build-budget').exists()


def test_allocator_v2_runner_measures_only_requested_cells_and_binds_beside_v1(records, tmp_path):
    """2026-10-12 ET, cpu-description ticket 04: exact malloc and 16 MiB new[]/delete[] cells only."""
    from testkit.cpu_service import allocator_v2_estimate
    output = tmp_path / 'allocator-v2'
    cells = ['malloc:64', 'new_array:16777216', 'delete_array:16777216']
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--service-group', 'allocator',
        *[a for cell in cells for a in ('--cell', cell)], '--machine', 'testhost',
        '--output', output, '--fixture', '--repetitions', '3', '--min-trial-s', '.05', '--max-wall-s', '300')
    assert result.returncode == 0, result.stdout + result.stderr
    raw = json.loads((output / 'receipt.json').read_text())
    assert raw['settings']['group'] == 'allocator_v2'
    assert raw['settings']['cells'] == [{'operation': 'new_array', 'size_bytes': 16777216},
        {'operation': 'delete_array', 'size_bytes': 16777216}, {'operation': 'malloc', 'size_bytes': 64}]
    assert {(s['scope']['event_abi'], s['scope']['size_bytes']) for s in raw['services']} == {
        ('_Znam', 16777216), ('_ZdaPv', 16777216), ('malloc', 64)}
    _, resource = allocator_v2_estimate(records, tmp_path, [(64, 2)], receipt=output / 'receipt.json')
    assert resource['seconds'] is not None and resource['seconds'] > 0
    assert sorted(c['site'] for c in resource['inputs']['covered_calls']) == [29, 30, 31]
    assert records.validate().returncode == 0


def test_allocator_v2_count_proof_covers_exactly_the_requested_operations(records, tmp_path, llvm22):
    records.copy_repo('applications', 'kernels', 'implementations', 'inputs', 'machines',
        'profiles', 'hardware_configs', 'strategies')
    output = tmp_path / 'allocator-v2-counts'
    result = run_swdb('cpu-service-calibrate', '--records', records.path, '--service-group', 'allocator',
        '--cell', 'malloc:64', '--cell', 'delete_array:16777216', '--output', output,
        '--fixture', '--llvm-bin', llvm22, '--count-only', '--max-wall-s', '300')
    assert result.returncode == 0, result.stdout + result.stderr
    raw = json.loads((output / 'count-proof.json').read_text())
    assert raw['context']['optimized_event_proof']['retained_event_abis'] == ['_ZdaPv', 'malloc']
    points = raw['count_proof']['points']
    assert {(p['event_abi'], p['size_bytes']) for p in points} == {
        ('_ZdaPv', 64), ('_ZdaPv', 16777216), ('malloc', 64), ('malloc', 16777216)}
    assert all(p['event_size_bins'] == [{'bytes': p['size_bytes'], 'events': p['events']}] for p in points if p['invoke'])
    assert all(p['opaque_events'] == (p['events'] if p['invoke'] else 0) for p in points)


def test_allocator_cells_refuse_unknown_operations_sizes_above_32_mib_and_mixing_with_size(records, tmp_path):
    cases = (['--cell', 'calloc:64'], ['--cell', 'malloc:33554433'], ['--cell', 'malloc:64', '--size', '64'],
             ['--cell', 'malloc:64', '--cell', 'malloc:64'])
    for index, argv in enumerate(cases):
        out = tmp_path / f'refused-{index}'
        refused = run_swdb('cpu-service-calibrate', '--records', records.path, '--service-group', 'allocator',
            *argv, '--output', out, '--fixture')
        assert refused.returncode != 0 and not out.exists(), argv
