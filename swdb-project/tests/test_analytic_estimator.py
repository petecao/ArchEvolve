"""Public estimator and validation seams. Fixture numbers are not research evidence.
Updated: 2026-10-06 ET.
"""
import json
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import REPO, run_swdb


@pytest.fixture
def copied_records(tmp_path):
    target = tmp_path / 'records'
    shutil.copytree(REPO / 'records', target)
    return target


def test_estimated_fact_validates_without_changing_existing_records(copied_records):
    path = copied_records / 'inputs' / 'kron-g16-k16.yaml'
    original = path.read_bytes()
    data = yaml.safe_load(original)
    # Existing application inputs are frozen by real count/protocol receipts.
    # Test fact-basis admission on a new unbound input without weakening those pins.
    data['id'] = 'fixture.estimated-input'
    data['properties']['num_nodes']['basis'] = 'estimated'
    (copied_records / 'inputs/fixture.estimated-input.yaml').write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', copied_records)
    assert result.returncode == 0, result.stderr + result.stdout
    assert path.read_bytes() == original


@pytest.fixture
def llvm22():
    import os
    import subprocess
    candidate = Path(os.environ.get('SWDB_LLVM_BIN', '/opt/homebrew/opt/llvm/bin'))
    if not all((candidate / tool).is_file() for tool in ('llvm-config', 'clang++', 'opt')):
        pytest.skip('LLVM 22 llvm-config/clang++/opt required')
    version = subprocess.run([candidate / 'llvm-config', '--version'], capture_output=True, text=True)
    if version.returncode or not version.stdout.startswith('22.'):
        pytest.skip('LLVM 22 required')
    return candidate


def characterization(copied_records, tmp_path, llvm22, n=8):
    fixture = REPO / 'tests' / 'fixtures' / 'analytic'
    result = run_swdb('characterize', '--records', copied_records,
        '--source', fixture / 'stream.cpp', '--implementation', 'gapbs-bfs-do',
        '--input', 'kron-g16-k16', '--region-map', fixture / 'regions.json',
        '--function', 'stream', '--roi', 'fixture.stream.v1', '--run-arg', str(n), '--id', 'fixture.characterization',
        '--llvm-bin', llvm22, '--output', tmp_path / 'counted', '--fixture', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def test_characterize_counts_source_elements_across_vector_tail(copied_records, tmp_path, llvm22):
    result = characterization(copied_records, tmp_path, llvm22, n=17)
    region = next(r for r in result['regions'] if r['id'] == 'fixture.stream')
    assert region['dynamic_counts']['loop_iterations']['value'] == 17
    assert region['operation_counts']['floating_point']['value'] == 34
    reads = [a for a in region['access_patterns'] if a['update_kind'] == 'read']
    writes = [a for a in region['access_patterns'] if a['update_kind'] == 'write']
    assert [a['element_count']['value'] for a in reads] == [17]
    assert [a['element_count']['value'] for a in writes] == [17]
    assert all(a['address_shape']['value'] == 'stream' for a in reads + writes)
    assert result['host']['machine'] and result['host']['architecture']
    assert result['counting']['level'] == 'source_normalized_ir'
    assert result['static_analysis']['optimized_ir_sha256']
    checked = run_swdb('validate', '--records', copied_records)
    assert checked.returncode == 0, checked.stdout + checked.stderr


def target_description(tmp_path, bandwidth=32.0):
    params = {name + '_ops_per_s': {'value': (16.0 if name == 'floating_point' else 1e9),
        'basis': 'reported', 'source': 'Hand-computed test fixture; not mbit10 measurement.', 'unit': 'operations/s'}
        for name in ('integer', 'floating_point', 'branch', 'atomic')}
    target = {'kind': 'target_description', 'schema_version': '0.4', 'id': 'fixture.target',
        'status': 'draft', 'created': '2026-10-06', 'updated': '2026-10-06',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Hand-computed test fixture.', 'uri': None}],
        'format': 'swdb.target-description.v1', 'version': '1', 'target': 'mbit10', 'threads': 1,
        'estimator_variant': 'team', 'calibration_sources': [], 'dram_address_layout': None,
        'mechanisms': [{'model': 'compute_throughput', 'parameters': params},
            {'model': 'streaming_bandwidth', 'parameters': {'bytes_per_s': {'value': bandwidth,
                'basis': 'unknown' if bandwidth is None else 'reported',
                'source': 'Hand-computed test fixture; not mbit10 measurement.', 'unit': 'bytes/s'}}}]}
    path = tmp_path / 'target.yaml'
    path.write_text(yaml.safe_dump(target, sort_keys=False))
    return path


def freeze_protocol(records, tmp_path):
    file = tmp_path / 'freeze.yaml'
    file.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.estimate.protocol', 'version': 1,
        'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1',
            'target_description': str(tmp_path / 'target.yaml'), 'inputs': ['kron-g16-k16'],
            'roi': 'fixture.stream.v1', 'threads': 1}}, sort_keys=False))
    result = run_swdb('freeze-protocol', file, '--records', records, '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)['id']


def test_estimate_reports_hand_computed_bounds(copied_records, tmp_path, llvm22):
    characterization(copied_records, tmp_path, llvm22)
    result = run_swdb('estimate', '--records', copied_records,
        '--characterization', 'fixture.characterization', '--target-description', target_description(tmp_path),
        '--protocol', freeze_protocol(copied_records, tmp_path), '--id', 'fixture.estimate', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    estimate = json.loads(result.stdout)
    region = next(r for r in estimate['regions'] if r['id'] == 'fixture.stream')
    assert [(b['model'], b['seconds']) for b in region['bounds']] == [('compute_throughput', 1.0), ('streaming_bandwidth', 2.0)]
    assert region['limiting_bound'] == 'streaming_bandwidth'
    assert estimate['seconds'] == pytest.approx(2.0, abs=5e-9)
    assert estimate['basis'] == 'estimated'
    assert estimate['verdict'] == 'within_error'
    checked = run_swdb('validate', '--records', copied_records)
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_unknown_bandwidth_preserves_known_compute_bound_and_null_total(copied_records, tmp_path, llvm22):
    characterization(copied_records, tmp_path, llvm22)
    result = run_swdb('estimate', '--records', copied_records,
        '--characterization', 'fixture.characterization', '--target-description', target_description(tmp_path, bandwidth=None),
        '--protocol', freeze_protocol(copied_records, tmp_path), '--id', 'fixture.unknown', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    estimate = json.loads(result.stdout)
    region = next(r for r in estimate['regions'] if r['id'] == 'fixture.stream')
    assert region['bounds'][0]['seconds'] == 1.0
    assert region['bounds'][1]['seconds'] is None
    assert region['bounds'][1]['missing'] == ['bytes_per_s']
    assert region['seconds'] is None and estimate['seconds'] is None and estimate['ratio'] is None


def test_validate_rejects_characterization_counts_changed_after_receipt(copied_records, tmp_path, llvm22):
    characterization(copied_records, tmp_path, llvm22)
    path = copied_records / 'workload_characterizations' / 'fixture.characterization.yaml'
    data = yaml.safe_load(path.read_text())
    region = next(r for r in data['regions'] if r['id'] == 'fixture.stream')
    region['operation_counts']['floating_point']['value'] = 12345
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', copied_records)
    assert result.returncode == 1
    assert 'identity_sha256' in result.stdout + result.stderr


def test_characterize_zero_trip_loop_does_not_count_a_phantom_iteration(copied_records, tmp_path, llvm22):
    result = characterization(copied_records, tmp_path, llvm22, n=0)
    region = next(r for r in result['regions'] if r['id'] == 'fixture.stream')
    assert region['dynamic_counts']['loop_iterations']['value'] == 0
    assert region['operation_counts']['floating_point']['value'] == 0
    assert [a['element_count']['value'] for a in region['access_patterns']] == [0, 0]


def test_characterize_retains_executed_unmodeled_calls(copied_records, tmp_path, llvm22):
    result = run_swdb('characterize', '--records', copied_records,
        '--source', REPO / 'tests/fixtures/analytic/calls.cpp', '--implementation', 'gapbs-bfs-do',
        '--input', 'kron-g16-k16', '--function', 'call_scope', '--roi', 'fixture.stream.v1', '--id', 'fixture.calls',
        '--llvm-bin', llvm22, '--output', tmp_path / 'counted', '--fixture', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    char = json.loads(result.stdout)
    assert [(c['name'], c['execution_count']['value']) for c in char['unmodeled_calls']] == [('bump', 4)]
    assert char['coverage']['missing_costs'] == ['bump']
    assert char['unmapped_loops']
    estimate = run_swdb('estimate', '--records', copied_records,
        '--characterization', 'fixture.calls', '--target-description', target_description(tmp_path),
        '--protocol', freeze_protocol(copied_records, tmp_path), '--id', 'fixture.calls.estimate', '--format', 'json')
    assert estimate.returncode == 0, estimate.stderr + estimate.stdout
    assert json.loads(estimate.stdout)['seconds'] is None


def test_characterize_missing_llvm_fails_cleanly(copied_records, tmp_path):
    result = run_swdb('characterize', '--records', copied_records,
        '--source', REPO / 'tests/fixtures/analytic/stream.cpp', '--implementation', 'gapbs-bfs-do',
        '--input', 'kron-g16-k16', '--id', 'fixture.missing', '--llvm-bin', tmp_path / 'missing')
    assert result.returncode == 1
    assert 'LLVM 22 is required' in result.stderr
    assert 'Traceback' not in result.stderr


def test_static_llvm_distribution_loads_pass_via_host_symbols(copied_records, tmp_path, llvm22):
    import sys
    # External toolchain boundary: emulate the official Linux distribution's missing
    # libLLVM shared object while retaining real LLVM analysis/instrumentation.
    proxy = tmp_path / 'llvm-static-bin'
    proxy.mkdir()
    for name in ('opt', 'clang++', 'llvm-ar', 'llvm-nm'):
        (proxy / name).symlink_to(llvm22 / name)
    config = proxy / 'llvm-config'
    config.write_text(f'#!{sys.executable}\n' +
        'import subprocess, sys\n' +
        "if '--link-shared' in sys.argv:\n    print('error: libLLVM-22.so is missing', file=sys.stderr)\n    sys.exit(1)\n" +
        'sys.exit(subprocess.call([' + repr(str(llvm22 / 'llvm-config')) + ', *sys.argv[1:]]))\n')
    config.chmod(0o755)
    result = characterization(copied_records, tmp_path, proxy)
    assert result['toolchain']['plugin_linkage'] == 'host_symbols'
    region = next(r for r in result['regions'] if r['id'] == 'fixture.stream')
    assert region['operation_counts']['floating_point']['value'] == 16
