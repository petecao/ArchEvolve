"""Pilot admission and review boundaries; all durations are fixtures. Date: 2026-09-25."""
import copy
import json
import runpy
import subprocess
import sys

import pytest

from conftest import REPO


@pytest.fixture
def pilot():
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    sources = [0, 1234, 7777]
    value = {'context': {'sources': sources, 'repetitions': 5, 'roi': 'bfs.complete_call.v1'},
             'build': {'binary_sha256': 'a' * 64}, 'timing': []}
    for position, source in enumerate(sources):
        for repetition in range(5):
            value['timing'].append({'source': source, 'source_position': position, 'repetition': repetition,
                'duration_s': 0.1 + repetition * 0.001, 'binary_sha256': 'a' * 64, 'roi': 'bfs.complete_call.v1',
                'basis': 'measured', 'quantity': 'native_roi_wall_seconds', 'verified': True,
                'evidence_kind': 'execution', 'output': f'/fixture/{position}/{repetition}'})
    return module, value, sources


def test_pilot_reports_actual_repeated_source_samples_separately(pilot):
    module, value, sources = pilot
    result = module['sample_grid'](value, sources, 5)
    assert len(result) == 3 and all(len(row['samples_seconds']) == 5 for row in result)
    assert result[0]['median_seconds'] == pytest.approx(0.102)
    assert result[0]['relative_spread'] == pytest.approx(0.004 / 0.102)


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'reused-output', 'boolean-source',
                                  'wrong-source', 'wrong-binary', 'wrong-roi', 'simulated', 'unverified', 'fixture'])
def test_calibration_cannot_invent_or_relabel_trial_cells(pilot, fault):
    module, value, sources = pilot
    row = value['timing'][-1]
    if fault == 'missing': value['timing'].pop()
    elif fault == 'duplicate': value['timing'].append(copy.deepcopy(row))
    elif fault == 'reused-output': row['output'] = value['timing'][0]['output']
    elif fault == 'boolean-source': value['context']['sources'] = [False, 1234, 7777]
    elif fault == 'wrong-source': row['source'] = 1234
    elif fault == 'wrong-binary': row['binary_sha256'] = 'b' * 64
    elif fault == 'wrong-roi': row['roi'] = 'bfs.dx100.traversal.v1'
    elif fault == 'simulated': row['basis'] = 'simulated'
    elif fault == 'unverified': row['verified'] = False
    else: row['evidence_kind'] = 'contract_fixture'
    with pytest.raises(ValueError):
        module['sample_grid'](value, sources, 5)


def test_missing_accelerator_size_evidence_does_not_make_native_freeze_publishable():
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    reasons = []
    result = module['accelerator_gate'](None, [], [], {}, reasons, 0.10)
    assert reasons and result == {'executions': [], 'repeatability': []}


@pytest.mark.parametrize('fault', [None, 'bare-lane', 'wrong-bind', 'wrong-config', 'wrong-host', 'missing-node'])
def test_recorded_native_lane_receipt_preserves_verified_identity(fault):
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    # Shape emitted by profile._verified_lane, not a claim of a live held lease.
    context = {'target': 'mbit10', 'host': 'mbit10',
               'lane': 'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 375)',
               'backend_configuration': {'lane': 'mbit10-evaluation-node1'}}
    machine = {'id': 'mbit10', 'hostname': 'mbit10', 'numa_nodes': [{'node': 0}, {'node': 1}]}
    if fault == 'bare-lane': context['lane'] = 'mbit10-evaluation-node1'
    elif fault == 'wrong-bind': context['lane'] = context['lane'].replace('bind:1', 'bind:0')
    elif fault == 'wrong-config': context['backend_configuration']['lane'] = 'mbit10-evaluation-node0'
    elif fault == 'wrong-host': context['host'] = 'different-host'
    elif fault == 'missing-node': machine['numa_nodes'] = [{'node': 0}]
    if fault:
        with pytest.raises(ValueError, match='native pilot'):
            module['native_lane'](context, machine)
    else:
        assert module['native_lane'](context, machine) == 'mbit10-evaluation-node1'
        assert context['lane'].endswith('generation 375)')


def test_public_native_metadata_query_preserves_the_verifiable_lane_shape(records):
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    rid = 'bfs-native-smoke-20260925-a1.evaluation'
    # Query a copy of retained metadata only; its old changed candidate is never
    # admitted as a baseline pilot or reclassified into empirical freeze evidence.
    records.copy_repo()
    result = records.swdb('get', rid, '--format', 'json')
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)['context']
    context['backend_configuration'] = {'lane': context['lane'].split(' ', 1)[0]}
    machine = records.read('machines/mbit10.yaml')
    assert module['native_lane'](context, machine) == context['backend_configuration']['lane']
    context['backend_configuration']['lane'] = 'mbit10-evaluation-node0' if 'node1' in context['lane'] else 'mbit10-evaluation-node1'
    with pytest.raises(ValueError, match='requested configuration'):
        module['native_lane'](context, machine)


def test_public_prepare_without_completed_pilots_does_not_create_a_freeze(records, tmp_path):
    request = tmp_path / 'selection.json'
    request.write_text(json.dumps({'id': 'unobserved', 'mode': 'native', 'packages': [],
        'maximum_relative_spread': 0.1, 'spread_justification': 'fixture only; not empirical',
        'size_selection': {'scale': 18, 'justification': 'fixture'}}))
    output = tmp_path / 'not-published'
    result = subprocess.run([sys.executable, str(REPO / 'scripts/bfs_freeze_pilot.py'), 'prepare', str(request),
                            '--records', str(records.path), '--output', str(output)], cwd=REPO,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and 'one distinct native package per graph family' in result.stderr
    assert not output.exists() and not (records.path / 'protocols').exists()
