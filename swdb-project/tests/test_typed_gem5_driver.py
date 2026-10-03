"""First-evaluation command admission and immutable request plans. 2026-10-03 ET.

These do not execute gem5 or produce target evidence. The driver's public
entry point has no fixture option and must refuse the local Mac before writes.
"""
import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from swdb import artifacts
from swdb.cli import Failure
from swdb.store import Store
from tools import typed_library_gem5_driver as driver


@pytest.fixture
def source_store(monkeypatch):
    store = Store(driver.PROJECT/'records')
    def representation(store, wid, application):
        definition = store.get(wid, 'workload')['definition']
        return {'representation': next(row for row in definition['representations'] if row['application'] == application)}
    monkeypatch.setattr(driver.bfs_protocol, 'workload_representation', representation)
    return store


def test_protocol_plan_keeps_t17_immutable_and_has_independent_read_only_grid(source_store):
    original = copy.deepcopy(source_store.get(driver.T17, 'protocol'))
    request = driver.protocol_request(source_store, 'first-evaluation-fixture', 'f'*64)
    assert request['version'] == 1 and request['supersedes'] is None
    assert request['id'] == 'first-evaluation-fixture.protocol'
    assert source_store.get(driver.T17, 'protocol') == original
    settings = request['settings']
    for key in ('targets', 'builds', 'simulation_identity', 'profitability', 'roi', 'threads'):
        assert settings[key] == original['settings'][key]
    assert settings['region_pairs'] == []
    assert settings['correctness']['required_accelerator_cases'] == {
        'baseline': [], 'candidate': ['read_only_executed', 'full_tiles', 'tail_tiles']}
    assert settings['correctness']['companion_cases'] == {
        'parent_gather_race': {'workload': driver.COVERAGE, 'source': 0}}
    assert len(settings['workloads']) == 2 and driver.COVERAGE not in settings['workloads']
    evidence = settings['sampling']['determinism']['evidence']
    assert artifacts.file_hash(driver.PROJECT/evidence['path']) == evidence['sha256']
    assert settings['route']['certified_tree_sha256'] == 'f'*64


def test_execution_plan_separates_primary_and_probe_binary_and_preserves_stage_budget(source_store):
    request = driver.protocol_request(source_store, 'first-evaluation-fixture', 'f'*64)
    protocol = {'id': 'frozen-fixture', **request}
    rows = {'protocol': protocol, 'baseline': {'id': 'baseline-fixture'}, 'candidate': {'id': 'candidate-fixture'}}
    for role in ('baseline.primary', 'candidate.primary', 'candidate.diagnostic'):
        rows[role] = {'id': role+'.build', 'build': {'binary': '/data1/builds/'+role, 'binary_sha256': 'a'*64}}
    args = SimpleNamespace(id='first-evaluation-fixture', memory_gib=48, storage_gib=8)
    primary = driver.execution_request(args, source_store, rows, 'candidate', driver.COVERAGE,
                                       'companion.timed', companion=True)
    diagnostic = driver.execution_request(args, source_store, rows, 'candidate', driver.COVERAGE,
                                          'companion.diagnostic', companion=True, diagnostic=True)
    assert primary['candidate_build'] != diagnostic['candidate_build']
    assert primary['protocol_companion'] == diagnostic['protocol_companion'] == 'parent_gather_race'
    assert primary['budget']['memory_gib'] == 48 and primary['budget']['storage_gib'] == 8
    assert primary['verification']['read_only'] is True and primary['verification']['coverage'] is True
    assert primary['verification']['trace_transport'] == 'gem5-gzip.v1'
    baseline = driver.execution_request(args, source_store, rows, 'baseline', request['settings']['workloads'][0], 'timed.baseline')
    assert 'protocol_companion' not in baseline
    assert baseline['verification']['read_only'] is False and baseline['verification']['coverage'] is False
    assert baseline['budget']['total_seconds'] == 9000
    with pytest.raises(Failure, match='timed sample'):
        driver.execution_request(args, source_store, rows, 'candidate', request['settings']['workloads'][0],
                                 'timed.diagnostic', diagnostic=True)


def test_public_driver_refuses_mac_before_creating_any_raw_output(tmp_path, monkeypatch):
    monkeypatch.setattr(driver.socket, 'gethostname', lambda: 'fixture-mac.local')
    runs = tmp_path/'no-output'
    with pytest.raises(Failure, match='requires mbit10'):
        driver.main(['--stage', 'prepare', '--id', 'first-evaluation-fixture', '--runs-dir', str(runs),
                     '--profile-package', 'package-fixture', '--approval-reference', 'fixture authorization'])
    assert not runs.exists()


def test_timed_stage_never_dispatches_after_inconclusive_l3(monkeypatch, tmp_path):
    monkeypatch.setattr(driver, 'prepared_records', lambda args: (None, {}))
    monkeypatch.setattr(driver, 'load_stage', lambda args, stage: {'l3_outcome': 'inconclusive', 'timed_admitted': False})
    called = []
    monkeypatch.setattr(driver, 'public', lambda *args, **kwargs: called.append(args))
    with pytest.raises(Failure, match='wait for an observed L3'):
        driver.timed_stage(SimpleNamespace(), tmp_path, 'fixture-lane', {})
    assert called == []


def test_prepare_budget_admits_serial_gcc_without_weakening_gem5_budget():
    args = SimpleNamespace(stage='prepare', memory_gib=48, storage_gib=8)
    assert driver.stage_budgets(args) == (4, 4)
    assert driver.PREPARE_MEMORY_GIB == 4
    args.stage = 'companion'
    assert driver.stage_budgets(args) == (48, 8)
    args.stage = 'timed'
    assert driver.stage_budgets(args) == (48, 8)
