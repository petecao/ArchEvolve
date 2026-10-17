"""Second-block admission and cleanup, without lab dispatch. Created: 2026-09-26 ET."""
import copy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts import bfs_native_repeatability as repeat
from scripts.bfs_process import run_stage
from swdb import artifacts, yamlio


@pytest.fixture
def evidence():
    plan = yamlio.load(repeat.PLAN)
    cell = copy.deepcopy(plan['cells'][0])
    first = yamlio.load(repeat.ROOT / 'records/evaluations' / (cell['first_evaluation'] + '.yaml'))
    machine = yamlio.load(repeat.ROOT / 'records/machines/mbit10.yaml')
    return plan, cell, first, machine


def test_actual_retained_requests_admit_only_four_fixed_unchanged_cells(evidence):
    plan, _, _, machine = evidence
    repeat.validate_plan(plan)
    for cell in plan['cells']:
        first = yamlio.load(repeat.ROOT / 'records/evaluations' / (cell['first_evaluation'] + '.yaml'))
        request = repeat.first_request(first, cell, machine)
        assert request['id'] == cell['id']
        assert request['candidate'] == first['candidate']
        assert request['workload'] == first['request']['workload']
        assert request['build'] == {k: first['build'][k] for k in ('compiler', 'flags')}
        assert request['budget']['total_seconds'] == 1200
        assert first['request'].get('build') is None


@pytest.mark.parametrize('fault', ['id', 'lane', 'count', 'order', 'retry', 'warmup-bool', 'source-bool'])
def test_plan_cannot_expand_or_silently_change_the_finite_measurement(evidence, fault):
    plan = evidence[0]
    if fault == 'id': plan['id'] = '../../escape'
    elif fault == 'lane': plan['lane'] = 'mbit10-evaluation-node0'
    elif fault == 'count': plan['cells'].append(copy.deepcopy(plan['cells'][0]))
    elif fault == 'order': plan['cells'].reverse()
    elif fault == 'retry': plan['bounds']['retries'] = 1
    elif fault == 'warmup-bool': plan['bounds']['warmups'] = False
    else: plan['sources'][0] = False
    with pytest.raises(ValueError):
        repeat.validate_plan(plan)


@pytest.mark.parametrize('fault', ['record', 'source', 'compiler', 'fixture', 'missing-trial',
                                  'wrong-env', 'protocol', 'wrong-graph', 'wrong-machine'])
def test_first_block_changes_fail_before_dispatch(evidence, fault):
    _, cell, first, machine = evidence
    if fault == 'record': first['updated'] = '2026-09-26'
    elif fault == 'source': cell['source_sha256'] = 'b' * 64
    elif fault == 'compiler': cell['compiler'] = '/usr/bin/clang++'
    elif fault == 'fixture': first['request']['fixture'] = True
    elif fault == 'missing-trial': first['timing'].pop()
    elif fault == 'wrong-env': first['build']['execution_environment']['OMP_NUM_THREADS'] = '8'
    elif fault == 'protocol': first['context']['protocol'] = 'unexpected.freeze'
    elif fault == 'wrong-graph': first['request']['workload']['id'] = 'other'
    else: machine['hostname'] = 'different-host'
    # Exercise semantic admission independently of the content seal where relevant.
    if fault not in ('record', 'source', 'compiler'):
        cell['first_evaluation_sha256'] = artifacts.digest(first)
    with pytest.raises(ValueError):
        repeat.first_request(first, cell, machine)


def second_fixture(evidence):
    _, cell, first, machine = evidence
    request = repeat.first_request(first, cell, machine)
    second = copy.deepcopy(first)
    second.update(id=request['id'], request=request)
    for row in second['timing']:
        row['output'] = '/fixture/second/' + Path(row['output']).name
    return first, second, machine, request


def test_second_block_keeps_five_values_per_source_and_never_creates_a_gain(evidence):
    first, second, machine, request = second_fixture(evidence)
    result = repeat.repeat_result(first, second, machine, request)
    assert [row['source'] for row in result] == [0, 1234, 7777]
    assert all(len(row['samples_seconds']) == 5 for row in result)
    assert all('gain' not in row and 'speedup' not in row for row in result)


@pytest.mark.parametrize('fault', ['binary', 'driver', 'wrapper', 'compiler', 'environment',
                                  'source', 'graph', 'unverified', 'reused-output', 'trial-order', 'request'])
def test_second_block_cannot_hide_changed_conditions_or_unchecked_samples(evidence, fault):
    first, second, machine, request = second_fixture(evidence)
    if fault in ('binary', 'driver', 'wrapper'):
        field = {'binary': 'binary_sha256', 'driver': 'template_sha256', 'wrapper': 'wrapper_sha256'}[fault]
        second['build'][field] = 'f' * 64
    elif fault == 'compiler': second['build']['compiler_version'][0] = 'other GCC'
    elif fault == 'environment': second['build']['execution_environment']['OMP_PROC_BIND'] = 'spread'
    elif fault == 'source': second['context']['candidate_sha256'] = 'f' * 64
    elif fault == 'graph': second['context']['workload']['canonical_sha256'] = 'f' * 64
    elif fault == 'unverified': second['correctness']['checks'].pop()
    elif fault == 'reused-output': second['timing'][0]['output'] = first['timing'][0]['output']
    elif fault == 'trial-order': second['timing'].reverse()
    else:
        second['request'] = copy.deepcopy(request)
        second['request']['budget']['total_seconds'] = 1800
    with pytest.raises(ValueError):
        repeat.repeat_result(first, second, machine, request)


@pytest.mark.parametrize('path', ['/tmp/bfs', '/data/yanruj/other/bfs',
                                  '/data/yanruj/EvolveSWDB_runs/../../escape',
                                  '/data/yanruj/EvolveSWDB_runs'])
def test_raw_path_is_rejected_before_creation(path):
    with pytest.raises(ValueError):
        repeat.raw_root(path)


def test_owned_timeout_retains_streamed_output_and_terminal_receipt(tmp_path):
    receipt = {'stages': []}
    child = [sys.executable, '-c', 'import time; print("retained-before-timeout", flush=True); time.sleep(30)']
    with pytest.raises(subprocess.TimeoutExpired):
        run_stage(receipt, tmp_path, child, timeout=0.3,
                  deadline=time.monotonic() + 5, cwd=tmp_path)
    saved = json.loads((tmp_path / 'driver.json').read_text())['stages'][0]
    assert saved['state'] == 'interrupted_or_timeout'
    assert saved['returncode'] is not None
    assert Path(saved['output']).read_text() == 'retained-before-timeout\n'
    assert artifacts.file_hash(saved['output']) == saved['stdout_sha256']


def test_dedicated_directory_rejects_even_small_unrelated_existing_content(tmp_path):
    repeat.empty_run_directory(tmp_path)
    (tmp_path / 'unrelated').mkdir()
    with pytest.raises(ValueError, match='must be empty'):
        repeat.empty_run_directory(tmp_path)


def test_pilot_deadline_cannot_be_reset_by_a_generous_budget_attestation():
    assert repeat.pilot_budget(6000, repeat.PILOT_DEADLINE - timedelta(seconds=5500)) == 5500
    with pytest.raises(ValueError, match='original pilot deadline'):
        repeat.pilot_budget(43200, repeat.PILOT_DEADLINE - timedelta(seconds=5399))
    with pytest.raises(ValueError, match='original pilot deadline'):
        repeat.pilot_budget(5399, repeat.PILOT_DEADLINE - timedelta(seconds=10000))


def test_batch_storage_counts_nested_files_and_preserves_the_over_limit_evidence(tmp_path):
    folder = tmp_path / 'evaluation'
    folder.mkdir()
    output = folder / 'parent.json'
    output.write_bytes(b'x' * 30)
    assert repeat.batch_storage(tmp_path, 30) == 30
    with pytest.raises(ValueError, match='ceiling exceeded'):
        repeat.batch_storage(tmp_path, 29)
    assert output.read_bytes() == b'x' * 30


def test_live_storage_monitor_stops_owned_child_and_retains_failure(tmp_path):
    receipt = {'stages': []}
    oversized = tmp_path / 'raw-over-budget'
    oversized.write_bytes(b'x' * 100)
    command = [sys.executable, '-c', 'import time; time.sleep(30)']
    with pytest.raises(ValueError, match='ceiling exceeded'):
        run_stage(receipt, tmp_path, command, timeout=10, deadline=time.monotonic() + 10,
                  cwd=tmp_path, monitor=lambda: repeat.batch_storage(tmp_path, 50))
    saved = json.loads((tmp_path / 'driver.json').read_text())['stages'][0]
    assert saved['state'] == 'failed' and saved['returncode'] is not None
    assert oversized.read_bytes() == b'x' * 100
