"""Separate matched CPU collector through public commands. Created: 2026-10-06 ET."""
import json
import yaml

from conftest import run_swdb


def test_original_driver_fixture_retains_five_trials_separate_verification_and_rounding(records, tmp_path, llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines',
        'profiles','hardware_targets','strategies','operations','intrinsics')
    data = records.read('inputs/kron-g16-k16.yaml')
    data.update(id='fixture.kron.g4', name='Small collector contract fixture')
    data['generator']['arguments'] = '-g 4 -k 2'; data['properties'] = {}
    records.write('inputs/fixture.kron.g4.yaml', data)
    counted = run_swdb('characterize', '--records', records.path, '--adapter', 'registered-gapbs',
        '--implementation', 'gapbs-bfs-do', '--input', 'fixture.kron.g4', '--threads', '1', '--trials', '5',
        '--id', 'fixture.native.counts', '--llvm-bin', llvm22, '--run-library-path', llvm22.parent / 'lib',
        '--output', tmp_path / 'counted', '--format', 'json',
        env={'GLIBC_TUNABLES':'glibc.malloc.tcache_count=7','MALLOC_ARENA_MAX':'3'})
    assert counted.returncode == 0, counted.stdout + counted.stderr
    result = run_swdb('collect-cpu-native-validation', '--records', records.path,
        '--characterization', 'fixture.native.counts', '--llvm-bin', llvm22,
        '--run-library-path', llvm22.parent / 'lib', '--fixture', '--id', 'fixture.native.validation',
        '--output', tmp_path / 'validation', '--max-wall-s', '120', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data['kind'] == 'cpu_native_validation' and data['evidence_kind'] == 'fixture'
    assert len(data['trials']) == 5
    assert data['summary']['basis'] == 'reported'
    assert data['summary']['rounding_half_width_s'] == .000005
    assert data['correctness']['state'] == 'passed'
    assert data['correctness']['separate_process'] is True
    assert '-v' not in data['timing_arguments'] and '-v' in data['correctness']['arguments']
    assert data['scope']['process_policy'] == 'five original GAPBS calls in one fresh process; no verification between timed calls'
    assert data['context']['instrumented_timer'] is False
    assert data['context']['native_runtime']['GLIBC_TUNABLES']=='glibc.malloc.tcache_count=7'
    assert data['context']['native_runtime']['MALLOC_ARENA_MAX']=='3'
    assert data['context']['native_runtime']['LD_AUDIT'] is None
    checked = records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
