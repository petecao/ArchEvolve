"""Exact pinned postprocessing recovery admission. Updated: 2026-10-03 ET.

Test receipts are recreated in a temporary folder from published metadata.
No raw artifact is copied, verified, simulated or represented as new execution.
"""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from swdb import artifacts
from swdb.cli import Failure
from swdb.store import Store, Record
from tools import typed_library_gem5_driver as driver

TRACKER = driver.PROJECT/'.scratch/typed-library-dx100-bfs-2026-10-03'


@pytest.fixture
def recovery_case(tmp_path, monkeypatch):
    store = Store(driver.PROJECT/'records')
    manifest = json.loads((TRACKER/'evaluation/a2-aggregation-failure-summary.json').read_text())
    run = manifest['id']
    args = SimpleNamespace(id=run, recovery_id='r1', recovery_manifest=tmp_path/'manifest.json',
                           records=store.dir, runs_dir=tmp_path, memory_gib=36, storage_gib=8)
    rows = {'protocol': store.get(run+'.protocol.84229924369fc6b0', 'protocol'),
            'candidate': store.get(run+'.proposal.candidate-1', 'candidate'),
            'baseline': store.get(run+'.baseline', 'candidate')}
    for role in ('baseline.primary', 'candidate.primary', 'candidate.diagnostic'):
        rows[role] = store.get(run+'.'+role+'.build', 'evaluation')
    def representation(store, wid, application):
        return {'representation': next(row for row in store.get(wid, 'workload')['definition']['representations']
                                      if row['application'] == application)}
    monkeypatch.setattr(driver.bfs_protocol, 'workload_representation', representation)
    original = tmp_path/(run+'.driver-timed'); original.mkdir()
    fresh = tmp_path/(run+'.driver-timed-r1'); fresh.mkdir()
    def pin(path):
        return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': artifacts.file_hash(path)}
    def write(path, content):
        path.write_text(json.dumps(content, indent=2)+'\n')
        return pin(path)
    manifest['timed_driver']['artifact'] = write(original/'driver.json', manifest['timed_driver']['content'])
    for entry in [*manifest['completed_uniform_commands'], manifest['failed_aggregation_command']]:
        stage = entry['content']['stage']
        cli = 'aggregate-evaluations' if stage.endswith('-aggregate') else 'dx100-execute'
        request_path = original/(stage+'.request.json')
        entry['request']['artifact'] = write(request_path, entry['request']['content'])
        entry['content']['command'] = driver._cli(args, cli)+[str(request_path)]
        if cli == 'dx100-execute':
            entry['content']['command'] += ['--runs-dir', str(tmp_path), '--lane', '0']
        output_path = original/(stage+'.json')
        if entry['content']['state'] == 'complete':
            entry['output'] = write(output_path, store.get(entry['record']['id'], 'evaluation'))
            entry['content']['output'] = {k:entry['output'][k] for k in ('path', 'sha256')}
        else:
            output_path.write_text(''); entry['output'] = pin(output_path)
        stderr_path = original/(stage+'.stderr.txt'); stderr_path.write_text('')
        entry['stderr'] = pin(stderr_path)
        if entry['content']['state'] == 'complete':
            entry['content']['stderr'] = {k:entry['stderr'][k] for k in ('path', 'sha256')}
        entry['artifact'] = write(original/(stage+'.command.json'), entry['content'])
    def seal():
        write(args.recovery_manifest, manifest)
        args.recovery_sha256 = artifacts.file_hash(args.recovery_manifest)
    seal()
    acceptance = {'outcome': 'observed'}
    companions = {name: driver.reference(store.get(run+'.companion.'+name+'.evaluation', 'evaluation'))
                  for name in ('timed', 'diagnostic')}
    monkeypatch.setattr(driver, 'prepared_records', lambda args: (store, rows))
    monkeypatch.setattr(driver, 'load_stage', lambda args, stage: {
        'l3_outcome': 'observed', 'timed_admitted': True,
        'companion_evaluations': companions, 'acceptance': acceptance})
    monkeypatch.setattr(driver.read_only_checks, 'companion_acceptance', lambda *args: acceptance)
    monkeypatch.setattr(driver, '_require_valid', lambda path: store)
    monkeypatch.setattr(driver.library.Library, 'state', lambda *args: {'tier': 'shared', 'status': 'certified'})
    return SimpleNamespace(args=args, rows=rows, store=store, manifest=manifest, original=original,
                           fresh=fresh, seal=seal, write=write, pin=pin, acceptance=acceptance)


def public_calls(monkeypatch, case, *, reject=False, timeout=False):
    calls = []
    def public(args, folder, command, stage, request, **kwargs):
        calls.append((command, stage, copy.deepcopy(request), kwargs))
        if timeout and command == 'aggregate-evaluations':
            raise Failure('bounded postprocessing timed out')
        if command == 'dx100-execute':
            return {'id': request['id'], 'outcome': {'state': 'complete'}, 'correctness': {
                'state': 'passed', 'checks': [{'coverage': {key: {'state': 'observed'}
                    for key in ('read_only_executed', 'full_tiles', 'tail_tiles')}}]}}
        if command == 'aggregate-evaluations':
            return {'id': request['id'], 'outcome': {'state': 'complete'}}
        return {'id': request['id'], 'decision': {'state': 'rejected' if reject else 'no_gain'},
                'metrics': {'roi_speedup': 1.0}}
    monkeypatch.setattr(driver, 'public', public)
    return calls


def test_recovery_reuses_exact_uniform_pair_and_qualifies_it_before_two_missing_samples(recovery_case, monkeypatch):
    case = recovery_case
    calls = public_calls(monkeypatch, case)
    result = driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert [command for command, *_ in calls] == [
        'aggregate-evaluations', 'compare-evaluations', 'dx100-execute', 'aggregate-evaluations',
        'dx100-execute', 'aggregate-evaluations', 'compare-evaluations']
    physical = [request for command, _, request, _ in calls if command == 'dx100-execute']
    assert len(physical) == 2
    assert {request['workload']['id'] for request in physical} == {case.rows['protocol']['settings']['workloads'][1]}
    assert {request['protocol_role'] for request in physical} == {'baseline', 'candidate'}
    assert all('.recovery.r1.timed.w1.' in request['id'] for request in physical)
    for request in physical:
        role = request['protocol_role']
        old_plan = driver.execution_request(case.args, case.store, case.rows, role,
            request['workload']['id'], 'timed.w1.'+role)
        old_plan['id'] = request['id']
        assert request == old_plan  # Only namespace changes, never binary, policy or budget.
    assert all(kwargs['timeout'] == (9060 if command == 'dx100-execute' else 3600)
               for command, _, _, kwargs in calls)
    first = result['workloads'][0]
    assert first['executions'] == case.manifest['completed_uniform_samples']
    assert first['aggregates']['baseline'] == case.manifest['completed_baseline_aggregate']
    assert '.recovery.r1.' in first['aggregates']['candidate']['id']
    assert '.recovery.r1.' in first['comparison']['id']
    assert result['recovery']['original_runtime_commit'] == case.manifest['runtime_commit']
    assert json.loads((case.original/'driver.json').read_text())['state'] == 'failed'


@pytest.mark.parametrize('failure', ['rejected', 'timeout'])
def test_recovery_does_not_run_second_graph_after_public_requalification_failure(recovery_case, monkeypatch, failure):
    case = recovery_case
    calls = public_calls(monkeypatch, case, reject=failure == 'rejected', timeout=failure == 'timeout')
    with pytest.raises(Failure, match='comparison rejected|postprocessing timed out'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert not any(command == 'dx100-execute' for command, *_ in calls)
    assert not (case.fresh/'first-result.md').exists()


@pytest.mark.parametrize('drift', ['manifest', 'output', 'command', 'request', 'store', 'failed-output'])
def test_recovery_refuses_drift_before_public_calls(recovery_case, monkeypatch, drift):
    case = recovery_case
    calls = public_calls(monkeypatch, case)
    entry = case.manifest['completed_uniform_commands'][1]
    if drift == 'manifest':
        case.args.recovery_sha256 = '0'*64
    elif drift == 'output':
        Path(entry['output']['path']).write_text('{}')
    elif drift == 'command':
        Path(entry['artifact']['path']).write_text('{}')
    elif drift == 'request':
        Path(entry['request']['artifact']['path']).write_text('{}')
    elif drift == 'store':
        value = copy.deepcopy(case.store.get(entry['record']['id']))
        value['correctness']['state'] = 'unverified'
        case.store.replace(case.store.path_of(value['id']), value)
    else:
        Path(case.manifest['failed_aggregation_command']['output']['path']).write_text('later output')
    with pytest.raises(Failure, match='recovery artifact|recovery evidence'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


@pytest.mark.parametrize('field,value', [
    ('candidate_build', 'wrong-build'), ('binary', {'path': '/wrong/bfs', 'sha256': '0'*64}),
    ('protocol', 'another-freeze'), ('protocol_role', 'baseline'),
    ('protocol_trial', {'source_position': 0, 'repetition': 1}),
    ('protocol_trial', {'source_position': False, 'repetition': 0}),
    ('protocol_trial', {'source_position': 0, 'repetition': 0.0})])
def test_recovery_rejects_consistently_resealed_wrong_planned_cell(recovery_case, monkeypatch, field, value):
    case = recovery_case
    entry = case.manifest['completed_uniform_commands'][1]
    entry['request']['content'][field] = value
    path = Path(entry['request']['artifact']['path'])
    entry['request']['artifact'] = case.write(path, entry['request']['content'])
    record = copy.deepcopy(case.store.get(entry['record']['id']))
    record['request'][field] = value
    case.store.replace(case.store.path_of(record['id']), record)
    entry['record'] = driver.reference(record)
    entry['output'] = case.write(Path(entry['output']['path']), record)
    entry['content']['output'] = {k:entry['output'][k] for k in ('path', 'sha256')}
    entry['artifact'] = case.write(Path(entry['artifact']['path']), entry['content'])
    case.seal()
    calls = public_calls(monkeypatch, case)
    with pytest.raises(Failure, match='recovery evidence'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


@pytest.mark.parametrize('trial', [{'source_position': False, 'repetition': 0},
                                 {'source_position': 0, 'repetition': 0.0}])
def test_recovery_rejects_record_only_resealed_json_type_drift(recovery_case, monkeypatch, trial):
    case = recovery_case
    entry = case.manifest['completed_uniform_commands'][1]
    record = copy.deepcopy(case.store.get(entry['record']['id']))
    record['request']['protocol_trial'] = trial
    case.store.replace(case.store.path_of(record['id']), record)
    entry['record'] = driver.reference(record)
    entry['output'] = case.write(Path(entry['output']['path']), record)
    entry['content']['output'] = {k:entry['output'][k] for k in ('path', 'sha256')}
    entry['artifact'] = case.write(Path(entry['artifact']['path']), entry['content'])
    case.seal()  # Original request file remains correct; only the record contradicts it.
    calls = public_calls(monkeypatch, case)
    with pytest.raises(Failure, match='recovery evidence'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


@pytest.mark.parametrize('state', ['failed', 'fixture', 'nested'])
def test_recovery_never_reuses_failed_fixture_or_nested_execution(recovery_case, monkeypatch, state):
    case = recovery_case
    entry = case.manifest['completed_uniform_commands'][1]
    record = copy.deepcopy(case.store.get(entry['record']['id']))
    if state == 'failed':
        record['outcome']['state'] = 'failed'
    elif state == 'fixture':
        record['evidence_kind'] = 'contract_fixture'
    else:
        record['component_evaluations'] = [{'evaluation': 'other', 'sha256': '0'*64}]
    case.store.replace(case.store.path_of(record['id']), record)
    entry['record'] = driver.reference(record)
    entry['output'] = case.write(Path(entry['output']['path']), record)
    entry['content']['output'] = {k:entry['output'][k] for k in ('path', 'sha256')}
    entry['artifact'] = case.write(Path(entry['artifact']['path']), entry['content'])
    case.seal()
    calls = public_calls(monkeypatch, case)
    with pytest.raises(Failure, match='recovery evidence'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


def test_recovery_refuses_any_additional_timed_history_including_another_recovery(recovery_case, monkeypatch):
    case = recovery_case
    other = copy.deepcopy(case.store.get(case.manifest['completed_uniform_samples']['candidate']['id']))
    other['id'] = case.args.id+'.recovery.r1.timed.w1.candidate.evaluation'
    other['request']['id'] = other['id']
    other['request']['workload']['id'] = case.rows['protocol']['settings']['workloads'][1]
    case.store.add(Record('additional-history-fixture.yaml', other))
    case.args.recovery_id = 'r2'
    calls = public_calls(monkeypatch, case)
    with pytest.raises(Failure, match='additional timed sample history'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


def test_recovery_refuses_existing_new_namespace_or_a_timedout_aggregate_record(recovery_case, monkeypatch):
    case = recovery_case
    calls = public_calls(monkeypatch, case)
    for rid in [case.args.id+'.recovery.r1.w0.comparison', case.args.id+'.timed.w0.candidate.aggregate']:
        case.store.add(Record('collision-'+rid+'.yaml', {'kind': 'evaluation', 'id': rid}))
        with pytest.raises(Failure, match='namespace already exists|timed-out aggregate has a public record'):
            driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []


def test_recovery_still_refuses_companion_acceptance_drift(recovery_case, monkeypatch):
    case = recovery_case
    calls = public_calls(monkeypatch, case)
    monkeypatch.setattr(driver.read_only_checks, 'companion_acceptance', lambda *args: {'outcome': 'inconclusive'})
    with pytest.raises(Failure, match='companion acceptance changed'):
        driver.timed_stage(case.args, case.fresh, 'fixture-lane', {})
    assert calls == []
