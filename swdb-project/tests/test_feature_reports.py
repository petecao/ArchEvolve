"""Reported feature inputs through the public CLI. Created: 2026-10-06 ET."""
import json
import shutil

import pytest

from conftest import REPO, run_swdb

REPORTS = REPO.parent / 'examples' / 'received'
BASE = 'fixture.lanl.measured-v2.stream.t1'


def counted_store(records):
    # Copy canonical records, omitting unrelated large application counts/estimates.
    records.copy_repo(*(folder.name for folder in (REPO / 'records').iterdir()
                        if folder.is_dir() and folder.name not in {'workload_characterizations', 'estimates'}))
    target = records.path / 'workload_characterizations' / (BASE + '.yaml')
    target.parent.mkdir()
    shutil.copyfile(REPO / 'records' / 'workload_characterizations' / target.name, target)
    return target


@pytest.mark.parametrize('filename, expected_stride', [
    ('bfs-sparse.features.v1.2.yaml', 77118.0),
    ('bfs-fully-connected.features.v1.2.yaml', 4.00016),
])
def test_import_adds_reported_facts_without_changing_counted_work(records, filename, expected_stride):
    original_path = counted_store(records)
    original_bytes = original_path.read_bytes()
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', REPORTS / filename, '--characterization', BASE,
        '--id', 'fixture.peter', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    result = json.loads(imported.stdout)
    supplied = result['reported_inputs'][0]
    assert supplied['basis'] == 'reported'
    assert supplied['source_report']['filename_version'] == '1.2'
    assert supplied['source_report']['schema_version'] == '1.1'
    assert supplied['features']['schema_version'] == '1.1'
    stream = supplied['features']['indirect_access_distances'][-1 if 'fully-connected' in filename else 0]
    assert stream['statistics']['mean_byte_stride'] == expected_stride
    assert any(c['kind'] == 'version_mismatch' for c in supplied['conflicts'])
    assert 'hardware_performance_profile' not in supplied['features']
    measured = next(r for r in result['regions'] if r['id'] == 'fixture.stream')
    assert measured['operation_counts']['floating_point']['value'] == 34
    assert original_path.read_bytes() == original_bytes
    checked = records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_report_import_withholds_nested_timing_and_pmu_outcomes(records, tmp_path):
    import yaml
    counted_store(records)
    report = yaml.safe_load((REPORTS / 'bfs-sparse.features.v1.2.yaml').read_text())
    report['operations']['analysis'] = {
        'candidate_timings': {'median_seconds': 987.654},
        'instructions_per_cycle_ipc': 321.123,
        'cycles_frequency_ghz': 456.789,
        'detail': {'elapsed_ms': 654.321, 'mean_index_distance': 7.25},
        'note': 'observed speedup 9.87x from target timing',
    }
    supplied = tmp_path / 'nested.v1.2.yaml'
    supplied.write_text(yaml.safe_dump(report, sort_keys=False))
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', supplied, '--characterization', BASE,
        '--id', 'fixture.nested', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    data = json.loads(imported.stdout)['reported_inputs'][0]
    analysis = data['features']['operations']['analysis']
    assert analysis == {'detail': {'mean_index_distance': 7.25}}
    assert data['features']['operations']['rmw_operation']['conflict_frequency'] == 'high_to_extreme on hub nodes'
    removed = {item['path'] for item in data['redactions']}
    assert '/operations/analysis/candidate_timings' in removed
    assert '/operations/analysis/detail/elapsed_ms' in removed
    assert data['source_report']['sanitizer_version'] == 'swdb.feature-report-sanitizer.v1'
    assert all(secret not in imported.stdout for secret in ('987.654', '321.123', '456.789', '654.321', '9.87x'))


def test_report_import_lists_source_array_methodology_and_unit_conflicts(records):
    counted_store(records)
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', REPORTS / 'bfs-sparse.features.v1.2.yaml', '--characterization', BASE,
        '--methodology', REPORTS / 'peter-measurement-methods.v1.2.yaml',
        '--methodology-text', REPORTS / 'peter-measurement-methodology.v1.2.txt',
        '--manifest', REPORTS / 'manifest.json', '--array-alias', 'VertexOffsets=g.out_index_',
        '--id', 'fixture.conflicts', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    data = json.loads(imported.stdout)['reported_inputs'][0]
    kinds = {conflict['kind'] for conflict in data['conflicts']}
    assert {'version_mismatch', 'source_scope_mismatch', 'element_size_mismatch',
            'methodology_internal_conflict', 'unit_ambiguity', 'manifest_scope_conflict'} <= kinds
    width = next(c for c in data['conflicts'] if c['kind'] == 'element_size_mismatch')
    assert width['reported']['value'] == 4 and width['swdb']['value'] == 8
    assert width['reported']['basis'] == 'reported' and width['swdb']['basis'] == 'code_reading'
    assert width['comparison_scope'] == 'unresolved_source_and_access_binding'
    assert data['array_aliases'] == {'VertexOffsets': 'g.out_index_'}
    parent = next(c for c in data['conflicts'] if c['kind'] == 'unit_ambiguity'
                  and c['path'] == '/working_set/scale_examples/small_scale_g18/parent_footprint_mb')
    assert parent['expected_logical_capacity_bytes'] == 1048572
    assert parent['reported'] == {'value': 1.05, 'unit': 'MB', 'basis': 'reported'}
    assert parent['resolved_unit'] is None
    assert data['methodology']['features']['locality']['measures_same_address_block'] is False
    assert data['methodology']['features']['locality']['arrays']['VertexOffsets']['runtime_thread_interleaving_observed'] is False
    assert data['features']['data_structures'][1]['element_size_bytes'] == 4
    assert all(c['reason'] for c in data['conflicts'])


@pytest.mark.parametrize('field', ['timing_seconds', 'runtime_ms', 'cpi'])
def test_validate_refuses_reported_timing_reintroduced_with_recomputed_hashes(records, field):
    import hashlib
    import yaml
    counted_store(records)
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', REPORTS / 'bfs-sparse.features.v1.2.yaml', '--characterization', BASE,
        '--id', 'fixture.tampered', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    data = json.loads(imported.stdout)
    supplied = data['reported_inputs'][0]
    supplied['features']['nested'] = {field: 42.125}
    def sha(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                         allow_nan=False).encode()).hexdigest()
    supplied['source_report']['sanitized_sha256'] = sha(supplied['features'])
    data.pop('identity_sha256')
    data['identity_sha256'] = sha(data)
    records.write('workload_characterizations/fixture.tampered.yaml', data)
    checked = records.validate()
    assert checked.returncode != 0
    assert 'timing/PMU' in checked.stdout + checked.stderr


def test_validate_reports_nonfinite_reported_values_without_crashing(records):
    counted_store(records)
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', REPORTS / 'bfs-sparse.features.v1.2.yaml', '--characterization', BASE,
        '--id', 'fixture.nonfinite', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    data = json.loads(imported.stdout)
    data['reported_inputs'][0]['features']['unknown_metric'] = float('nan')
    records.write('workload_characterizations/fixture.nonfinite.yaml', data)
    checked = records.validate()
    assert checked.returncode == 1
    assert 'finite JSON' in checked.stdout + checked.stderr
    assert 'Traceback' not in checked.stderr


def test_malformed_report_is_refused_without_partial_records_or_traceback(records, tmp_path):
    import yaml
    counted_store(records)
    report = yaml.safe_load((REPORTS / 'bfs-sparse.features.v1.2.yaml').read_text())
    report['data_structures'] = ['not an array declaration']
    supplied = tmp_path / 'malformed.v1.2.yaml'
    supplied.write_text(yaml.safe_dump(report))
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', supplied, '--characterization', BASE,
        '--id', 'fixture.bad-report', '--format', 'json')
    assert imported.returncode == 1
    assert 'data_structures' in imported.stderr
    assert 'Traceback' not in imported.stderr
    assert not (records.path / 'workload_characterizations/fixture.bad-report.yaml').exists()


def test_ambiguous_sizes_and_unknown_values_remain_literal_without_alias_guesses(records, tmp_path):
    import yaml
    counted_store(records)
    report = yaml.safe_load((REPORTS / 'bfs-sparse.features.v1.2.yaml').read_text())
    report['data_structures'][1]['element_size_bytes'] = '4B'
    report['working_set']['scale_examples']['small_scale_g18']['parent_footprint_mb'] = None
    supplied = tmp_path / 'ambiguous.v1.2.yaml'
    supplied.write_text(yaml.safe_dump(report, sort_keys=False))
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', supplied, '--characterization', BASE,
        '--id', 'fixture.ambiguous', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    data = json.loads(imported.stdout)['reported_inputs'][0]
    assert data['array_aliases'] == {}
    assert data['features']['data_structures'][1]['element_size_bytes'] == '4B'
    assert data['features']['working_set']['scale_examples']['small_scale_g18']['parent_footprint_mb'] is None
    assert any(c['kind'] == 'non_numeric_reported_value' for c in data['conflicts'])
    offsets = next(c for c in data['conflicts'] if c['kind'] == 'unit_ambiguity'
                   and c['path'] == '/working_set/scale_examples/small_scale_g18/offsets_footprint_mb')
    assert offsets['expected_logical_capacity_bytes'] is None and offsets['resolved_unit'] is None
    assert not any(c['kind'] == 'element_size_mismatch' for c in data['conflicts'])


def test_malformed_methodology_is_refused_without_partial_records_or_traceback(records, tmp_path):
    import yaml
    counted_store(records)
    methodology = yaml.safe_load((REPORTS / 'peter-measurement-methods.v1.2.yaml').read_text())
    methodology['footprints'] = ['not a footprint object']
    supplied = tmp_path / 'malformed-methodology.yaml'
    supplied.write_text(yaml.safe_dump(methodology))
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', REPORTS / 'bfs-sparse.features.v1.2.yaml', '--characterization', BASE,
        '--methodology', supplied, '--id', 'fixture.bad-methodology', '--format', 'json')
    assert imported.returncode == 1
    assert 'footprints' in imported.stderr
    assert 'Traceback' not in imported.stderr
    assert not (records.path / 'workload_characterizations/fixture.bad-methodology.yaml').exists()


def test_duplicate_report_key_is_refused_without_partial_records_or_traceback(records, tmp_path):
    counted_store(records)
    supplied = tmp_path / 'duplicate.yaml'
    supplied.write_text('schema_version: "1.1"\nschema_version: "1.2"\nkernel: {}\n')
    imported = run_swdb('import-feature-report', '--records', records.path,
        '--report', supplied, '--characterization', BASE,
        '--id', 'fixture.duplicate-report', '--format', 'json')
    assert imported.returncode == 1
    assert 'duplicate key' in imported.stderr
    assert 'Traceback' not in imported.stderr
    assert not (records.path / 'workload_characterizations/fixture.duplicate-report.yaml').exists()
