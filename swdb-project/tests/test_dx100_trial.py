"""Actual unfrozen simulator cell identity through the public API. Updated: 2026-09-26 ET."""
import json
from pathlib import Path

import pytest
import yaml

from test_bfs_protocol import _workload_request
from test_dx100 import case
from test_dx100_v2 import v2_request


def registered_trial(case, records):
    data = v2_request(case, 'witness')
    _, _, folder = case
    repo = Path(__file__).resolve().parents[1]
    records.copy_repo('applications')
    kernel = yaml.safe_load((repo / 'records/kernels/gapbs-bfs.yaml').read_text())
    kernel['baseline_implementation'] = 'dx100-bfs-scalar'
    records.write('kernels/gapbs-bfs.yaml', kernel)
    records.write('implementations/dx100-bfs-scalar.yaml', yaml.safe_load(
        (repo / 'records/implementations/dx100-bfs-scalar.yaml').read_text()))
    payload = _workload_request(records, folder,
        {'num_vertices': 3, 'directed': True, 'edges': [[0, 1], [1, 2]]})
    payload['sources'] = [2, 0, 1]
    path = folder / 'workload-registration.yaml'
    path.write_text(yaml.safe_dump(payload))
    result = records.swdb('register-workload', path, '--format', 'json')
    assert result.returncode == 0, result.stderr
    workload = json.loads(result.stdout)
    representation = next(row for row in workload['definition']['representations']
                          if row['application'] == 'dx100-gapbs')
    data['workload'] = {'id': workload['id'], 'source': 1,
                        'representation': {key: representation[key] for key in ('path', 'sha256')}}
    data['protocol_trial'] = {'source_position': 2, 'repetition': 1}
    return data


def test_public_unfrozen_trial_retains_registered_global_position_and_actual_repetition(case, records):
    data = registered_trial(case, records)
    _, invoke, _ = case
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'complete', result['outcome']
    assert 'protocol' not in result['request']
    assert result['context']['protocol_trial'] == data['protocol_trial']
    assert result['context']['workload']['sources'] == [2, 0, 1]
    assert result['context']['sources'] == [1]
    for row in (*result['timing'], *result['correctness']['checks']):
        assert (row['source'], row['source_position'], row['repetition']) == (1, 2, 1)


@pytest.mark.parametrize('trial', [
    {'source_position': 0, 'repetition': 1},
    {'source_position': 3, 'repetition': 1},
    {'source_position': True, 'repetition': 1},
    {'source_position': 2, 'repetition': 1.0},
    {'source_position': 2, 'repetition': -1},
    {'source_position': 2, 'repetition': 1, 'source': 1},
    {'repetition': 1},
])
def test_public_unfrozen_trial_rejects_invalid_or_mislabeled_cell_before_execution(case, records, trial):
    data = registered_trial(case, records)
    _, invoke, _ = case
    data['protocol_trial'] = trial
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'protocol_trial' in result['outcome']['reason']
    assert not any(row['stage'] in {'checkpoint', 'checkpoint_resolution', 'simulation'}
                   for row in result['stages'])


def test_public_explicit_trial_requires_registered_source_order(case):
    data = v2_request(case, 'witness')
    _, invoke, _ = case
    data['protocol_trial'] = {'source_position': 0, 'repetition': 0}
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'registered ordered workload' in result['outcome']['reason']
    assert not any(row['stage'] in {'checkpoint', 'checkpoint_resolution', 'simulation'}
                   for row in result['stages'])
