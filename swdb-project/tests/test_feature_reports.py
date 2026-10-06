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
