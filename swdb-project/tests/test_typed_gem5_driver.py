"""First-evaluation command admission and immutable request plans. 2026-10-03 ET.
Updated 2026-10-05 ET (code review P15: the shared operator frame and budgets).

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


@pytest.mark.parametrize('name', ['typed', 'bc'])
def test_gem5_drivers_refuse_raw_output_inside_the_checkout_before_creating_it(tmp_path, monkeypatch, name):
    """P15 (2026-10-05 ET): the BC driver had lost this refusal; both drivers now share run_driver.

    Every earlier check is satisfied by fixtures (host name, lane, record root, an approved run root
    that is the checkout itself), so only the checkout refusal can stop the run."""
    from tools import bc_gem5_driver
    module = driver if name == 'typed' else bc_gem5_driver
    monkeypatch.setattr(module.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(driver.provider_guard, 'verified_lane', lambda: 'mbit10-evaluation-node0 (fixture)')
    monkeypatch.setattr(driver, 'RECORDS_ROOT', tmp_path)
    monkeypatch.setattr(driver.dispatch_preflight, 'PRIMARY', driver.PROJECT)
    runs = driver.PROJECT/'raw-output-inside-checkout-fixture'
    argv = ['--stage', 'prepare', '--id', 'checkout-guard-fixture', '--runs-dir', str(runs),
            '--records', str(tmp_path/'records'), '--approval-reference', 'fixture authorization']
    if name == 'typed':
        argv += ['--profile-package', 'package-fixture']
    with pytest.raises(Failure, match='raw output cannot be inside the checkout'):
        module.main(argv)
    assert not runs.exists()


def test_gem5_driver_budgets_are_the_named_constants():
    """P15 (2026-10-05 ET): the BC and typed drivers request the same named build/simulator budgets."""
    assert driver.COMPILE_BUDGET == {'total_seconds': 600, 'build_seconds': 300, 'memory_gib': 4, 'storage_gib': 1}
    assert driver.TIMED_SECONDS == {'total_seconds': 9000, 'checkpoint_seconds': 1800, 'run_seconds': 7140}
    assert driver.COMPANION_SECONDS == {'total_seconds': 3600, 'checkpoint_seconds': 600, 'run_seconds': 2940}
    assert driver.COMMAND_GRACE_SECONDS == 60


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


def test_prepare_ignores_a_newer_receipt_without_current_dependencies(monkeypatch):
    """Test-only shared state; no review or dispatch is recorded."""
    from swdb.library import Library
    from swdb.store import Record
    store = Store(driver.PROJECT / 'records')
    lib = Library(driver.PROJECT / 'library')
    receipts = [row for row in store.of_kind('certification')
                if row.data.get('entry', {}).get('id') == driver.CONTRACT
                and row.data.get('candidate') and lib.current_certification(row.data)]
    assert receipts, 'requires the durable dependency-bound candidate receipt'
    original = sorted(receipts, key=lambda row: (row.data.get('created_at', ''), row.id))[-1]
    stale = copy.deepcopy(original.data)
    stale.update(id='certification.newer-unbound-selection-fixture', created_at='9999-01-01T00:00:00Z')
    stale.pop('dependencies')
    rows = [*store.records, Record('fixture-newer-unbound.yaml', stale)]
    isolated = Store(store.dir, indexed_records=rows)
    monkeypatch.setattr(Library, 'state', lambda self, entry_id: {'tier': 'shared', 'status': 'certified'})
    _, selected = driver.current_library(isolated)
    assert selected['id'] == original.id


@pytest.fixture
def published_first_attempt(source_store):
    """Immutable public plans; no remote build, simulation or performance claim."""
    run = 'typed-library-bfs-gem5-20261003-a1'
    rows = {
        'protocol': source_store.get(run + '.protocol.8de9b516796360dc', 'protocol'),
        'baseline': source_store.get(run + '.baseline', 'candidate'),
        'candidate': source_store.get(run + '.proposal.candidate-1', 'candidate')}
    for role in ('baseline.primary', 'candidate.primary', 'candidate.diagnostic'):
        rows[role] = source_store.get(run + '.' + role + '.build', 'evaluation')
    assert all(rows.values())
    return SimpleNamespace(id=run, memory_gib=36, storage_gib=8), rows


def test_post_roi_budget_covers_retained_scale18_completion_for_every_role(source_store, published_first_attempt):
    """Catch a short planner cap before spending another real simulator run."""
    from swdb.dx100_witness import validate_record_witness
    args, rows = published_first_attempt
    historical = []
    for role in ('baseline', 'candidate'):
        for workload in ('uniform18', 'kronecker18'):
            for mode in ('primary', 'diagnostic'):
                rid = f'bfs-t17-routes-20260928-a3.{role}.{workload}.s0.r0.{mode}.evaluation'
                record = source_store.get(rid, 'evaluation')
                assert record['outcome']['state'] == 'complete'
                assert record['build']['adapter'] == 'dx100.complete_call.v2'
                validate_record_witness(record, source_store)
                historical.append(record)
    ceiling = {record['request']['verification']['max_ticks'] for record in historical}
    assert ceiling == {10**14}
    observed = max(record['correctness']['checks'][0]['continuation']['simulated_ticks']
                   for record in historical)
    assert observed == 86 * 10**9
    # Baseline receipts alone already require 57/84 billion ticks; selecting
    # the established common ceiling does not depend on candidate gain.
    assert max(record['correctness']['checks'][0]['continuation']['simulated_ticks']
               for record in historical if '.baseline.' in record['id']) == 84 * 10**9
    plans = [driver.execution_request(args, source_store, rows, role, wid,
                                      f'timed.w{index}.{role}')
             for index, wid in enumerate(rows['protocol']['settings']['workloads'])
             for role in ('baseline', 'candidate')]
    plans += [driver.execution_request(args, source_store, rows, 'candidate', driver.COVERAGE,
                                       'companion.' + role, companion=True, diagnostic=role == 'diagnostic')
              for role in ('timed', 'diagnostic')]
    assert len(plans) == 6
    for request in plans:
        assert request['verification']['max_ticks'] == next(iter(ceiling)) > observed
        assert 'post_roi_cpu' not in request['verification']
        assert request['verification']['checker'] == 'dx100.bfs.verifier.v2'
        assert request['budget'] == {
            'total_seconds': 3600 if 'protocol_companion' in request else 9000,
            'checkpoint_seconds': 600 if 'protocol_companion' in request else 1800,
            'run_seconds': 2940 if 'protocol_companion' in request else 7140,
            'memory_gib': 36, 'storage_gib': 8}


@pytest.mark.parametrize('label', ['timed.w0.baseline', 'companion.timed', 'companion.diagnostic'])
def test_post_roi_budget_fix_preserves_every_other_actual_request_field(source_store, published_first_attempt, label):
    args, rows = published_first_attempt
    companion = label.startswith('companion.')
    role = 'candidate' if companion else 'baseline'
    wid = driver.COVERAGE if companion else rows['protocol']['settings']['workloads'][0]
    planned = driver.execution_request(args, source_store, rows, role, wid, label,
                                        companion=companion, diagnostic=label == 'companion.diagnostic')
    original = copy.deepcopy(source_store.get(args.id + '.' + label + '.evaluation', 'evaluation')['request'])
    assert planned['verification'].pop('max_ticks') == 10**14
    assert original['verification'].pop('max_ticks') == 10**10
    assert planned == original


def test_timed_postprocessing_has_a_separate_bound_for_real_trace_revalidation(
        source_store, published_first_attempt, tmp_path, monkeypatch):
    """Reach the observed candidate-aggregate timeout without replaying 177M lines."""
    import json
    args, rows = published_first_attempt
    args.records, args.runs_dir = source_store.dir, tmp_path
    lane = 'mbit10-evaluation-node0 fixture'
    companions = {name: driver.reference(source_store.get(
        args.id + '.companion.' + name + '.evaluation', 'evaluation'))
        for name in ('timed', 'diagnostic')}
    acceptance = {'outcome': 'observed'}
    monkeypatch.setattr(driver, 'prepared_records', lambda args: (source_store, rows))
    monkeypatch.setattr(driver, 'load_stage', lambda args, stage: {
        'l3_outcome': 'observed', 'timed_admitted': True,
        'companion_evaluations': companions, 'acceptance': acceptance})
    monkeypatch.setattr(driver.read_only_checks, 'companion_acceptance', lambda *args: acceptance)
    monkeypatch.setattr(driver.provider_guard, 'verified_lane', lambda: lane)
    monkeypatch.setattr(driver, 'lease_snapshot', lambda lane: [])
    monkeypatch.setattr(driver, '_require_valid', lambda path: source_store)
    monkeypatch.setattr(driver.library.Library, 'state', lambda *args: {'tier': 'shared', 'status': 'certified'})
    calls = []
    def command(argv, folder, stage, *, timeout, environment=None):
        request = json.loads(Path(next(value for value in argv if str(value).endswith('.request.json'))).read_text())
        calls.append((argv[3], stage, timeout))
        if stage == 'timed.w0.candidate-aggregate' and timeout < 1082:
            raise Failure(f'{stage} exceeded {timeout} seconds')
        if argv[3] == 'dx100-execute':
            return {'id': request['id'], 'outcome': {'state': 'complete'},
                    'correctness': {'state': 'passed', 'checks': [{'coverage': {
                        key: {'state': 'observed'} for key in ('read_only_executed', 'full_tiles', 'tail_tiles')}}]}}
        if argv[3] == 'aggregate-evaluations':
            return {'id': request['id'], 'outcome': {'state': 'complete'}}
        return {'id': request['id'], 'decision': {'state': 'accepted'}, 'metrics': {'roi_speedup': 1.0}}
    monkeypatch.setattr(driver, 'checked_command', command)
    result = driver.timed_stage(args, tmp_path, lane, {})
    assert len(result['workloads']) == 2
    assert [timeout for command, _, timeout in calls if command == 'dx100-execute'] == [9060] * 4
    assert [timeout for command, _, timeout in calls if command in {'aggregate-evaluations', 'compare-evaluations'}] == [3600] * 6
