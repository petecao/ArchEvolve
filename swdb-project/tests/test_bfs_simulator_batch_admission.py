"""Simulator batch result admission, 2026-09-26 ET.

All records below are synthetic contract data in memory. The public aggregation
function and its semantic readback run; no evaluator, simulator, provider, raw
measurement, or empirical claim is produced. Model/source prerequisite checks
and package assembly are isolated because they have separate public tests.
"""
import copy
from types import SimpleNamespace

import pytest

from scripts import bfs_simulator_batch as batch
from swdb import artifacts, bfs_protocol
from swdb.cli import Failure
from test_bfs_simulator_batch import admission, complete_child, fixture_package, plan


class MemoryStore:
    def __init__(self, values):
        self.values = {value['id']: value for value in values}

    def get(self, identity, kind=None):
        value = self.values.get(identity)
        return value if value and (kind is None or value['kind'] == kind) else None


def immutable(kind, name, **fields):
    value = {'kind': kind, 'requested_id': name, 'version': 1, 'supersedes': None,
             'invalidated_comparisons': [], **fields}
    value['identity_sha256'] = artifacts.digest(bfs_protocol._identity_payload(value))
    value['id'] = name + '.' + value['identity_sha256'][:16]
    return value


@pytest.fixture
def completed(monkeypatch):
    policy = plan('t16'); row = policy['series'][0]; approved = admission(policy)
    workload = immutable('workload', 'synthetic-workload', definition={
        'sources': row['sources'], 'canonical_sha256': 'a'*64})
    row['workload'] = workload['id']
    build = {'compiler': 'synthetic-c++', 'compiler_version': ['synthetic'], 'flags': ['-O2'],
             'adapter': 'synthetic.simulator', 'binary': '/synthetic/bfs', 'binary_sha256': 'b'*64}
    settings = {'mode': 'controlled_simulator', 'kernel': 'synthetic.bfs',
        'threads': policy['threads'], 'roi': policy['roi'], 'sampling': {'repetitions': 2, 'warmups': 0},
        'targets': {role: {'id': policy['target'], 'configuration': row['configuration']}
                    for role in ('baseline', 'candidate')},
        'builds': {role: build for role in ('baseline', 'candidate')},
        'instrumentation': {role: {} for role in ('baseline', 'candidate')},
        'correctness': {'verifier': 'synthetic.verifier', 'required_cases': []},
        'simulation_identity': {'simulator': {'path': '/synthetic/gem5', 'sha256': 'c'*64}}}
    frozen = immutable('protocol', 'synthetic-protocol', settings=settings, state='frozen',
        frozen_at='2026-09-26T09:00:00-04:00', workload_identities={workload['id']: workload['identity_sha256']})
    approved['protocols'][row['protocol_key']] = {'id': frozen['id'], 'sha256': artifacts.digest(frozen)}
    child = complete_child(policy, row, approved, 59)
    candidate = {'kind': 'candidate', 'id': row['candidate'], 'implementation': 'synthetic.impl',
                 'artifact': {'sha256': 'd'*64}}
    implementation = {'kind': 'implementation', 'id': candidate['implementation'], 'kernel': settings['kernel']}
    primaries = []
    for sample in child['samples']:
        trial = {key: sample[key] for key in ('source_position', 'repetition')}
        binding = {'protocol': frozen['id'], 'frozen_sha256': frozen['identity_sha256'],
            'settings_sha256': artifacts.digest(settings), 'role': row['protocol_role'],
            'workload_id': workload['id'], 'workload_sha256': workload['identity_sha256'],
            'bound_at': '2026-09-26T10:00:00-04:00'}
        primary = {'kind': 'evaluation', 'id': sample['evaluation'], 'candidate': candidate['id'],
            'implementation': implementation['id'], 'evidence_kind': 'execution', 'gain_claim': False,
            'build': copy.deepcopy(build), 'outcome': {'state': 'complete'},
            'request': {'protocol': frozen['id'], 'protocol_role': row['protocol_role'], 'protocol_trial': trial},
            'context': {'protocol': frozen['id'], 'protocol_binding': binding, 'protocol_trial': trial,
                'workload': {'id': workload['id'], 'sources': [sample['source']], 'canonical_sha256': 'a'*64},
                'sources': [sample['source']], 'repetitions': 1, 'threads': policy['threads'], 'roi': policy['roi'],
                'candidate_sha256': candidate['artifact']['sha256'], 'basis': 'simulated',
                'target': policy['target'], 'backend_configuration': row['configuration'],
                'instrumentation': {}, 'adapter': build['adapter'], 'verifier': 'synthetic.verifier',
                'correctness_cases': [], 'execution_binding': {'simulator': settings['simulation_identity']['simulator'],
                    'binary': {'path': build['binary'], 'sha256': build['binary_sha256']}}},
            'timing': [{**trial, 'source': sample['source'], 'binary_sha256': 'b'*64, 'output_sha256': 'e'*64,
                'verified': True, 'roi': policy['roi'], 'basis': 'simulated', 'quantity': 'simulated_roi_seconds',
                'evidence_kind': 'execution', 'duration_s': 1.0}],
            'correctness': {'state': 'passed', 'checks': [{**trial, 'source': sample['source'],
                'binary_sha256': 'b'*64, 'graph_sha256': 'a'*64, 'output_sha256': 'e'*64,
                'passed': True, 'verifier': 'synthetic.verifier'}]},
            'stages': [{'stage': 'synthetic', 'state': 'complete', 'started': '2026-09-26T10:00:00-04:00'}]}
        primaries.append(primary)
    store = MemoryStore([workload, frozen, candidate, implementation, *primaries])
    request = {'message_version': '1.0', 'id': row['id']+'.aggregate', 'protocol': frozen['id'],
               'protocol_role': row['protocol_role'], 'evaluations': [value['id'] for value in primaries]}
    monkeypatch.setattr(bfs_protocol, '_validate_settings', lambda *_: None)
    monkeypatch.setattr(bfs_protocol, '_simulation_build', lambda *_: None)
    monkeypatch.setattr(bfs_protocol, 'validate_baseline_source', lambda *_: None)
    monkeypatch.setattr(bfs_protocol, '_request', lambda _: copy.deepcopy(request))
    monkeypatch.setattr(bfs_protocol, '_require_valid', lambda _: store)
    monkeypatch.setattr(bfs_protocol.workflow, 'persist', lambda _, value, *args, **kwargs: value)
    aggregate = bfs_protocol.aggregate_evaluations(SimpleNamespace(records=None))
    assert aggregate['outcome']['state'] == 'complete', aggregate['outcome']
    store.values[aggregate['id']] = aggregate
    child['aggregate'] = aggregate['id']
    monkeypatch.setattr(batch, 'package_binding', lambda _, package, requested, evaluation, *_rest:
        fixture_package(policy, row, store.get(evaluation)['context']['sources'][0]))
    return SimpleNamespace(policy=policy, row=row, approved=approved, child=child, store=store,
                           aggregate=aggregate, primaries=primaries, frozen=frozen)


def admit(value):
    batch.validate_series_result(value.policy, value.row, value.approved, value.child, 21600, 59, value.store)


def reseal(value):
    """Consistently rehash synthetic components to exercise semantic readback."""
    aggregate = value.aggregate
    aggregate['component_evaluations'] = [{'evaluation': item['id'], 'sha256': artifacts.digest(item)}
                                        for item in value.primaries]
    aggregate['context']['component_contexts'] = {item['id']: copy.deepcopy(item['context']) for item in value.primaries}
    aggregate['context']['component_bindings'] = {item['id']: copy.deepcopy(item['context']['execution_binding'])
                                                for item in value.primaries}
    aggregate['timing'] = [copy.deepcopy(t) for item in value.primaries for t in item['timing']]
    aggregate['correctness']['checks'] = [copy.deepcopy(t) for item in value.primaries for t in item['correctness']['checks']]
    aggregate['stages'] = [{**copy.deepcopy(t), 'component_evaluation': item['id']}
                           for item in value.primaries for t in item['stages']]


def test_public_aggregate_function_result_reopens_complete_ordered_grid(completed):
    admit(completed)
    assert [item['evaluation'] for item in completed.aggregate['component_evaluations']] == [
        sample['evaluation'] for sample in completed.child['samples']]
    assert completed.aggregate['gain_claim'] is False


@pytest.mark.parametrize('fault', ['missing', 'wrong-id', 'unavailable', 'wrong-request-role', 'wrong-request-order',
    'wrong-component-order', 'component-hash', 'current-protocol', 'incomplete', 'candidate', 'gain'])
def test_aggregate_declaration_and_current_public_record_cannot_diverge(completed, fault):
    value = completed
    if fault == 'missing': value.child.pop('aggregate')
    elif fault == 'wrong-id': value.child['aggregate'] = 'another-protocol.aggregate'
    elif fault == 'unavailable': value.store.values.pop(value.aggregate['id'])
    elif fault == 'wrong-request-role': value.aggregate['request']['protocol_role'] = 'candidate'
    elif fault == 'wrong-request-order': value.aggregate['request']['evaluations'].reverse()
    elif fault == 'wrong-component-order': value.aggregate['component_evaluations'].reverse()
    elif fault == 'component-hash': value.aggregate['component_evaluations'][0]['sha256'] = 'f'*64
    elif fault == 'current-protocol': value.approved['protocols'][value.row['protocol_key']]['sha256'] = 'f'*64
    elif fault == 'incomplete': value.aggregate['outcome']['state'] = 'incompatible'
    elif fault == 'candidate': value.aggregate['candidate'] = 'another-candidate'
    else: value.aggregate['gain_claim'] = True
    with pytest.raises((ValueError, Failure)): admit(value)


@pytest.mark.parametrize('fault', ['request-role', 'request-protocol', 'trial', 'bool-trial', 'source',
    'binding-role', 'binding-protocol', 'settings-hash', 'duration', 'duplicate-timing', 'configuration',
    'correctness', 'classification', 'promoted-fixture'])
def test_consistently_rehashed_components_still_require_frozen_semantics(completed, fault):
    value = completed; primary = value.primaries[-1]
    if fault == 'request-role': primary['request']['protocol_role'] = 'candidate'
    elif fault == 'request-protocol': primary['request']['protocol'] = 'another.protocol'
    elif fault == 'trial': primary['context']['protocol_trial']['repetition'] = 0
    elif fault == 'bool-trial': primary['context']['protocol_trial']['repetition'] = True
    elif fault == 'source': primary['context']['workload']['sources'] = [0]
    elif fault == 'binding-role': primary['context']['protocol_binding']['role'] = 'candidate'
    elif fault == 'binding-protocol': primary['context']['protocol_binding']['protocol'] = 'another.protocol'
    elif fault == 'settings-hash': primary['context']['protocol_binding']['settings_sha256'] = 'f'*64
    elif fault == 'duration': primary['timing'][0]['duration_s'] = 0
    elif fault == 'duplicate-timing': primary['timing'][0]['repetition'] = 0
    elif fault == 'configuration': primary['context']['backend_configuration'] = {'wrong': True}
    elif fault == 'correctness': primary['correctness']['checks'][0]['passed'] = False
    elif fault == 'promoted-fixture': primary['request']['fixture'] = True
    else: primary['evidence_kind'] = 'contract_fixture'
    reseal(value)
    with pytest.raises((ValueError, Failure)): admit(value)


def test_fixture_cannot_be_promoted_to_actual_series_completion(completed):
    value = completed
    for primary in value.primaries:
        primary['evidence_kind'] = 'contract_fixture'
        primary['timing'][0]['evidence_kind'] = 'contract_fixture'
        primary['request']['fixture'] = True
    value.aggregate['evidence_kind'] = 'contract_fixture'
    reseal(value)
    with pytest.raises(ValueError, match='primary protocol role or ordered trial binding'): admit(value)


def test_t15_keeps_no_freeze_or_aggregate_semantics(monkeypatch):
    value = plan('t15'); row = value['series'][0]; approved = admission(value)
    child = complete_child(value, row, approved, 39)
    monkeypatch.setattr(batch, 'package_binding', lambda _, package, requested, *_rest:
        fixture_package(value, row, row['sources'][int(requested[len(row['id'])+2:].split('.')[0])]))
    batch.validate_series_result(value, row, approved, child, 21600, 39, None)
    child['aggregate'] = 'unplanned.aggregate'
    with pytest.raises(ValueError, match='unfrozen calibration'):
        batch.validate_series_result(value, row, approved, child, 21600, 39, None)


@pytest.fixture
def terminal_files(tmp_path):
    from scripts import bfs_simulator_batch_terminal as terminal
    start = '2026-09-26T10:00:00-04:00'; end = '2026-09-26T22:00:00-04:00'
    creator = {'pid': 100, 'start_ticks': 200}
    ledger = {'format': terminal.FORMAT, 'budget_seconds': 30, 'absolute_end': end,
        'monotonic_end': 100000, 'created': '2026-09-26T10:00:02-04:00', 'creator': creator,
        'spent_seconds': .3, 'reservations': {}, 'events': [
            {'pid': 100, 'seconds': 5, 'started': '2026-09-26T10:00:05-04:00',
             'purpose': 'cleanup_or_finalization', 'elapsed_seconds': .1,
             'finished': '2026-09-26T10:00:05.05-04:00', 'exceeded_grant': False},
            {'pid': 101, 'seconds': 5, 'started': '2026-09-26T10:00:09-04:00',
             'purpose': 'cleanup_or_finalization', 'elapsed_seconds': .2,
             'finished': '2026-09-26T10:00:09.1-04:00', 'exceeded_grant': False}]}
    ledger_path = tmp_path/'cleanup-ledger.json'; driver_path = tmp_path/'driver.json'
    driver = {'id': 'synthetic.batch', 'state': 'complete', 'outer_started': start, 'outer_deadline': end,
        'started': '2026-09-26T10:00:01-04:00', 'finished': '2026-09-26T10:00:09-04:00',
        'process_observations': {'driver_identity': creator},
        'cleanup_budget': {'path': str(ledger_path), 'binding': terminal.SharedCleanup.binding_of(ledger),
                           'budget_seconds': 30},
        'cleanup': {'state': 'all_owned_descendants_absent', 'subreaper': True, 'direct_reaped': True,
                    'checked_at': '2026-09-26T10:00:08-04:00', 'shared_budget': str(ledger_path), 'errors': []},
        # Legitimately captured before later shared reservations settle.
        'cleanup_accounting': {'spent_seconds': .1, 'reservations': {'still-running-parent': {'seconds': 5}}}}
    def write():
        import json
        driver_path.write_text(json.dumps(driver))
        ledger_path.write_text(json.dumps(ledger))
        return ({'path': str(driver_path), 'sha256': artifacts.file_hash(driver_path)},
                {'path': str(ledger_path), 'sha256': artifacts.file_hash(ledger_path)})
    def validate(refs=None):
        return terminal.validate_cleanup_ledger(*(refs or write()), expected_run_id=driver['id'],
            expected_outer_start=start, expected_deadline=end, current='2026-09-26T10:00:10-04:00')
    return SimpleNamespace(terminal=terminal, driver=driver, ledger=ledger, write=write, validate=validate,
                           driver_path=driver_path, ledger_path=ledger_path)


@pytest.mark.parametrize('state', ['complete', 'failed'])
def test_final_ledger_is_distinct_from_nonfinal_embedded_snapshots(terminal_files, state):
    fixture = terminal_files; fixture.driver['state'] = state
    result = fixture.validate()
    assert result['spent_seconds'] == .3 and result['settled_events'] == 2
    assert result['embedded_cleanup_snapshots'] == 'nonfinal'
    assert result['driver_outcome'] == state
    assert result['process_absence_verified'] is result['empirical_qualification'] is False


@pytest.mark.parametrize('fault', ['missing', 'changed-bytes', 'path', 'binding', 'creator-start', 'creator-bool',
    'reserve', 'deadline', 'outstanding', 'overspent', 'unsettled-sum', 'nan', 'bool-charge', 'overgrant',
    'exceeded', 'prefreeze-event', 'late-event', 'order', 'empty-events', 'still-running', 'cleanup-failed',
    'driver-clock'])
def test_final_ledger_requires_exact_settled_original_budget(terminal_files, fault):
    value = terminal_files
    refs = None
    if fault == 'missing':
        refs = value.write(); value.ledger_path.unlink()
    elif fault == 'changed-bytes':
        refs = value.write(); value.ledger_path.write_text('{}')
    elif fault == 'path': value.driver['cleanup_budget']['path'] += '.other'
    elif fault == 'binding': value.driver['cleanup_budget']['binding'] = 'f'*64
    elif fault == 'creator-start': value.driver['process_observations']['driver_identity'] = {'pid': 100, 'start_ticks': 201}
    elif fault == 'creator-bool': value.ledger['creator'] = {'pid': True, 'start_ticks': 200}
    elif fault == 'reserve': value.ledger['budget_seconds'] = 31
    elif fault == 'deadline': value.ledger['absolute_end'] = '2026-09-27T22:00:00-04:00'
    elif fault == 'outstanding': value.ledger['reservations'] = {'dead-child': {'seconds': 1}}
    elif fault == 'overspent': value.ledger['spent_seconds'] = 31
    elif fault == 'unsettled-sum': value.ledger['spent_seconds'] = .1
    elif fault == 'nan': value.ledger['spent_seconds'] = float('nan')
    elif fault == 'bool-charge': value.ledger['events'][0]['elapsed_seconds'] = True
    elif fault == 'overgrant': value.ledger['events'][0]['seconds'] = .05
    elif fault == 'exceeded': value.ledger['events'][0]['exceeded_grant'] = True
    elif fault == 'prefreeze-event': value.ledger['events'][0]['started'] = '2026-09-26T09:00:00-04:00'
    elif fault == 'late-event': value.ledger['events'][1]['finished'] = '2026-09-26T22:00:01-04:00'
    elif fault == 'order': value.ledger['events'].reverse()
    elif fault == 'empty-events': value.ledger['events'] = []
    elif fault == 'still-running': value.driver['state'] = 'running'
    elif fault == 'cleanup-failed': value.driver['cleanup']['errors'] = ['PermissionError']
    else: value.driver['outer_started'] = '2026-09-26T10:00:01-04:00'
    # Reseal mutated header cases to reach semantic checks, rather than rely on
    # a stale digest alone. The explicit caller clock/driver identity stay fixed.
    if fault in {'creator-bool', 'reserve', 'deadline'}:
        value.driver['cleanup_budget']['binding'] = value.terminal.SharedCleanup.binding_of(value.ledger)
    with pytest.raises((ValueError, KeyError)):
        value.validate(refs)


def test_final_ledger_reopens_bytes_again_to_detect_concurrent_settlement(terminal_files, monkeypatch):
    value = terminal_files; refs = value.write(); read = value.terminal.read_reference
    calls = 0
    def changed(ref, maximum):
        nonlocal calls
        result = read(ref, maximum)
        if ref == refs[1]:
            calls += 1
            if calls == 1:
                value.ledger_path.write_text('{}')
        return result
    monkeypatch.setattr(value.terminal, 'read_reference', changed)
    with pytest.raises(ValueError, match='changed'):
        value.validate(refs)


def test_final_ledger_refuses_ambiguous_duplicate_json_fields(terminal_files):
    value = terminal_files; driver_ref, ledger_ref = value.write()
    value.ledger_path.write_text(value.ledger_path.read_text()[:-1] + ', "spent_seconds": 0}')
    ledger_ref['sha256'] = artifacts.file_hash(value.ledger_path)
    with pytest.raises(ValueError, match='duplicate'):
        value.validate((driver_ref, ledger_ref))
