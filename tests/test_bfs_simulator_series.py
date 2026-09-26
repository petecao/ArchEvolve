"""Simulator orchestration selection guards; no simulator evidence. Updated: 2026-09-26."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from conftest import REPO
from swdb import artifacts, bfs_protocol
from swdb.cli import Failure


@pytest.fixture
def selection(tmp_path, monkeypatch):
    # This client imports the sibling bounded-build helper when run as a script.
    monkeypatch.syspath_prepend(str(REPO / 'scripts'))
    spec = importlib.util.spec_from_file_location('simulator_series', REPO / 'scripts/bfs_simulator_series.py')
    client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client)
    pinned = tmp_path / 'pinned'; pinned.mkdir()
    (pinned / 'bfs.cc').write_text('int fixture_bfs(){return 0;}\n')
    expected = artifacts.identify(pinned)
    implementation = {'id': 'dx100-bfs-scalar', 'function': 'DOBFS'}
    source = {'id': 'snapshot', 'implementation': implementation['id'],
              'context': {'function': 'DOBFS'}, 'artifact': copy.deepcopy(expected)}
    candidate = {'id': 'baseline', 'implementation': implementation['id'],
                 'source_snapshot': source['id'], 'context': {'function': 'DOBFS'},
                 'artifact_role': 'source_baseline', 'artifact': copy.deepcopy(expected)}
    workload = {'kind': 'workload', 'requested_id': 'graph.v1', 'version': 1, 'supersedes': None,
                'invalidated_comparisons': [], 'definition': {'sources': [0, 4], 'family': 'contract_fixture'}}
    seal(workload)
    return client, candidate, source, implementation, workload, expected


def seal(record):
    fingerprint = artifacts.digest(bfs_protocol._identity_payload(record))
    record.update(identity_sha256=fingerprint, id=record['requested_id'] + '.' + fingerprint[:16])
    return record


def protocol(workload, mode='controlled_simulator'):
    return seal({'kind': 'protocol', 'requested_id': 'policy.v1', 'version': 1, 'supersedes': None,
                 'invalidated_comparisons': [], 'frozen_at': '2026-09-25T20:00:00-04:00', 'state': 'frozen',
                 'settings': {'mode': mode}, 'workload_identities': {workload['id']: workload['identity_sha256']}})


def check(selection, frozen=None, role=None, author=False):
    client, candidate, source, implementation, workload, expected = selection
    client.validate_selection(candidate, source, implementation, workload, frozen, role, author, expected)


@pytest.mark.parametrize('implementation_id,function,author', [
    ('dx100-bfs-scalar', 'DOBFS', False), ('gapbs-bfs-do', 'DOBFS', False),
    ('dx100-bfs-maa-reference', 'DOBFSMAA', True)])
def test_unchanged_identified_source_can_calibrate(selection, implementation_id, function, author):
    _, candidate, source, implementation, _, _ = selection
    implementation.update(id=implementation_id, function=function)
    for value in (candidate, source):
        value['implementation'] = implementation_id
        value['context']['function'] = function
    check(selection, author=author)


def test_repackaged_rewrite_is_not_an_unchanged_pilot(selection, tmp_path):
    _, candidate, source, _, _, _ = selection
    changed = tmp_path / 'changed'; changed.mkdir()
    (changed / 'bfs.cc').write_text('int fixture_bfs(){return 1;}\n')
    # Public baseline-candidate also accepts a newly profiled source snapshot.
    # Equality to that snapshot alone cannot establish pinned-source identity.
    candidate['artifact'] = source['artifact'] = artifacts.identify(changed)
    with pytest.raises(ValueError, match='pinned application source'):
        check(selection)


@pytest.mark.parametrize('fault', ['candidate-implementation', 'source-implementation',
                                  'source-reference', 'candidate-function', 'source-function', 'proposal'])
def test_mixed_identity_or_rewrite_history_cannot_calibrate(selection, fault):
    _, candidate, source, _, _, _ = selection
    if fault == 'candidate-implementation': candidate['implementation'] = 'gapbs-bfs-do'
    elif fault == 'source-implementation': source['implementation'] = 'gapbs-bfs-do'
    elif fault == 'source-reference': candidate['source_snapshot'] = 'different-snapshot'
    elif fault == 'candidate-function': candidate['context']['function'] = 'DOBFSMAA'
    elif fault == 'source-function': source['context']['function'] = 'DOBFSMAA'
    else: candidate['proposal'] = 'actual-rewrite-proposal'
    with pytest.raises(ValueError, match='identity|pilot'):
        check(selection)


def test_frozen_candidate_may_change_source_but_baseline_may_not(selection):
    _, candidate, _, _, workload, _ = selection
    frozen = protocol(workload)
    candidate.update(artifact_role='rewrite', proposal='selected-proposal')
    candidate['artifact']['sha256'] = 'f' * 64
    check(selection, frozen, 'candidate')
    with pytest.raises(ValueError, match='pinned application source'):
        check(selection, frozen, 'baseline')
    with pytest.raises(ValueError, match='pinned application source'):
        check(selection, frozen, 'candidate', author=True)


@pytest.mark.parametrize('fault', ['native-policy', 'changed-policy', 'changed-workload',
                                  'missing-workload', 'wrong-workload-fingerprint', 'role'])
def test_frozen_selection_requires_exact_simulator_policy(selection, fault):
    workload = selection[4]
    frozen = protocol(workload)
    role = 'candidate'
    if fault == 'native-policy': frozen = protocol(workload, 'native')
    elif fault == 'changed-policy': frozen['settings']['mode'] = 'artifact_reference'
    elif fault == 'changed-workload': workload['definition']['sources'].reverse()
    elif fault == 'missing-workload': frozen['workload_identities'] = {}; seal(frozen)
    elif fault == 'wrong-workload-fingerprint':
        frozen['workload_identities'][workload['id']] = 'a' * 64; seal(frozen)
    else: role = 'exploratory'
    with pytest.raises((Failure, ValueError)):
        check(selection, frozen, role)


def test_author_binary_cannot_be_labeled_as_upstream_source(selection):
    _, candidate, source, implementation, _, _ = selection
    implementation['id'] = candidate['implementation'] = source['implementation'] = 'gapbs-bfs-do'
    with pytest.raises(ValueError, match='author binaries'):
        check(selection, author=True)


def test_accelerated_author_reference_is_not_the_scalar_comparator(selection):
    _, candidate, source, implementation, workload, _ = selection
    implementation.update(id='dx100-bfs-maa-reference', function='DOBFSMAA')
    for value in (candidate, source):
        value.update(implementation=implementation['id'])
        value['context']['function'] = implementation['function']
    frozen = protocol(workload, 'artifact_reference')
    check(selection, frozen, 'candidate', author=True)
    with pytest.raises(ValueError, match='unaccelerated starting source'):
        check(selection, frozen, 'baseline', author=True)


@pytest.mark.parametrize('root', ['/data/yanruj/EvolveSWDB_runs', '/data1/yanruj/EvolveSWDB_runs',
                                 '/data/yanruj/EvolveSWDB_runs/existing-batch'])
def test_batch_budget_never_counts_a_shared_or_nonempty_output_root(selection, tmp_path, monkeypatch, capsys, root):
    client = selection[0]
    monkeypatch.setattr(client.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(sys, 'argv', ['bfs_simulator_series.py', '--id', 'guard-case', '--candidate', 'baseline',
        '--workload', 'graph', '--build-evaluation', 'build', '--configuration', str(tmp_path / 'unused.json'),
        '--runs-dir', root, '--lane', '0'])
    (tmp_path / 'unrelated-job.log').write_text('already owned output')
    calls = []
    def external_directory(path):
        calls.append(str(path))
        return tmp_path
    monkeypatch.setattr(client.artifacts, 'external_directory', external_directory)
    with pytest.raises(SystemExit) as stopped:
        client.main()
    assert stopped.value.code == 2
    if root.endswith('existing-batch'):
        assert calls == [root] and 'directory must be empty' in capsys.readouterr().err
    else:
        assert not calls and 'dedicated child' in capsys.readouterr().err


def test_reused_diagnostic_must_match_source_and_frozen_collector(selection):
    client, candidate, _, implementation, workload, _ = selection
    model = {'id': 'model', 'context': {'model_root': '/fixture/model', 'target': 'target'}}
    collector = {'backend': 'libclang-cindex', 'collector': 'dx100.m5_rpns.source_scopes.v1',
                 'library_sha256': 'a'*64, 'pass_sha256': 'b'*64, 'runtime_sha256': 'c'*64}
    diagnostic = {'id': 'diagnostic', 'candidate': candidate['id'], 'evidence_kind': 'execution',
        'outcome': {'state': 'complete', 'stage': 'candidate_build'},
        'request': {'diagnostic_regions': True}, 'context': {
            'candidate_sha256': candidate['artifact']['sha256'], 'function': implementation['function'],
            'model_build': model['id'], 'model_root': '/fixture/model', 'target': 'target',
            'roi': 'bfs.complete_call.v1', 'accelerated_requested': False,
            'diagnostic': {'regions': [{'id': 'selected'}],
                'discovery': {key: value for key, value in collector.items() if key != 'runtime_sha256'},
                'runtime': {'sha256': collector['runtime_sha256']}}}}
    frozen = protocol(workload)
    frozen['settings']['region_pairs'] = [{'evidence': 'simulated_diagnostic_profile',
        'baseline': 'selected', 'candidate': 'selected', 'collector': collector}]
    def check(build):
        client.validate_diagnostic_build(build, candidate, implementation, model,
                                         'bfs.complete_call.v1', False, frozen, 'baseline')
    check(diagnostic)
    for location, key, value in [
        ('context', 'candidate_sha256', 'd'*64), ('context', 'function', 'AnotherEntry'),
        ('context', 'model_build', 'other-model'), ('context', 'target', 'other-target'),
        ('context', 'roi', 'bfs.dx100.traversal.v1'), ('context', 'accelerated_requested', True),
        ('request', 'diagnostic_regions', False), ('request', 'fixture', True),
        ('outcome', 'state', 'failed')]:
        changed = copy.deepcopy(diagnostic); changed[location][key] = value
        with pytest.raises(ValueError, match='exact source/model/ROI/treatment'):
            check(changed)
    changed = copy.deepcopy(diagnostic)
    changed['context']['diagnostic']['discovery']['pass_sha256'] = 'd'*64
    with pytest.raises(ValueError, match='frozen region correspondence/collector'):
        check(changed)
    changed = copy.deepcopy(diagnostic)
    changed['context']['diagnostic']['regions'][0]['id'] = 'new-selected'
    with pytest.raises(ValueError, match='frozen region correspondence/collector'):
        check(changed)


def test_checker_selection_never_silently_promotes_legacy_evidence(selection):
    client = selection[0]
    v1, v2 = 'dx100.bfs.verifier.v1', 'dx100.bfs.verifier.v2'
    assert client.select_verifier(None, None) == v1
    assert client.select_verifier(v2, None) == v2
    for checker in (v1, v2):
        frozen = {'settings': {'correctness': {'verifier': checker}}}
        assert client.select_verifier(None, frozen) == checker
        assert client.select_verifier(checker, frozen) == checker
        with pytest.raises(ValueError, match='differs from frozen'):
            client.select_verifier(v1 if checker == v2 else v2, frozen)
    with pytest.raises(ValueError, match='supported DX100'):
        client.select_verifier(None, {'settings': {'correctness': {'verifier': 'unknown'}}})


@pytest.mark.parametrize('frozen_series', [False, True])
def test_client_emits_actual_trial_for_every_primary_and_diagnostic_request(selection, tmp_path, monkeypatch, frozen_series):
    """Exercise the client/public-command boundary without running a simulator."""
    client, candidate, source, implementation, workload, expected = selection
    source['application'] = 'dx100-gapbs'
    frozen = protocol(workload)
    frozen['settings'].update(sampling={'repetitions': 2}, correctness={'verifier': 'dx100.bfs.verifier.v1'})
    seal(frozen)
    model = {'id': 'model', 'outcome': {'state': 'complete', 'stage': 'build'}, 'evidence_kind': 'execution',
        'context': {'model_root': '/fixture/model', 'target': 'dx100-e4fc4af-4c'},
        'build': {'details': {'binaries': [{'path': '/fixture/gem5.opt', 'sha256': 'a' * 64}]}}}
    catalog = {row['id']: row for row in (candidate, source, implementation, workload, model, frozen)}
    execution_requests = []

    def stage(receipt, folder, argv, *, output, **kwargs):
        command, argument = argv[3:5]
        if command == 'get':
            result = catalog[argument]
        else:
            payload = json.loads(Path(argument).read_text())
            result = {'id': payload['id']}
            if command == 'dx100-compile':
                result.update(candidate=candidate['id'], evidence_kind='execution', request=payload,
                    outcome={'state': 'complete', 'stage': 'candidate_build'},
                    build={'binary': '/fixture/' + result['id'], 'binary_sha256': 'b' * 64},
                    context={'candidate_sha256': expected['sha256'], 'function': implementation['function'],
                        'model_build': model['id'], 'model_root': '/fixture/model', 'target': model['context']['target'],
                        'roi': 'bfs.complete_call.v1', 'accelerated_requested': False,
                        'diagnostic': {'regions': [], 'discovery': {}, 'runtime': {}}})
            elif command == 'dx100-execute':
                execution_requests.append(payload)
                result.update(outcome={'state': 'complete'}, correctness={'state': 'passed', 'checks': [{}]},
                    context={'checkpoint_manifest': '/fixture/checkpoint', 'workload': {'canonical_sha256': 'c' * 64},
                        'sources': [payload['workload']['source']], 'target': model['context']['target'],
                        'backend_configuration': payload['configuration'], 'threads': 4, 'roi': 'bfs.complete_call.v1'},
                    timing=[{'duration_s': 0.01}])
            elif command == 'profile-package':
                result['completeness'] = 'complete'
            elif command == 'aggregate-evaluations':
                result['outcome'] = {'state': 'complete'}
            elif command != 'dx100-profile':
                raise AssertionError(command)
            catalog[result['id']] = result
        output.write_text(json.dumps(result))
        receipt['stages'].append({'command': command})

    runs = tmp_path / 'runs'; runs.mkdir()
    config = tmp_path / 'configuration.json'
    config.write_text(json.dumps({'mode': 'BASE', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384}))
    monkeypatch.setattr(client.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(client, 'Store', lambda _: SimpleNamespace(get=lambda ident, kind=None: catalog.get(ident, {})))
    monkeypatch.setattr(client.profile, '_verified_lane', lambda *args: None)
    monkeypatch.setattr(client.artifacts, 'external_directory', lambda _: runs)
    monkeypatch.setattr(client.artifacts, 'source_root', lambda *args: tmp_path / 'pinned')
    monkeypatch.setattr(client.bfs_protocol, 'workload_representation',
                        lambda *args: {'representation': {'path': '/fixture/graph.sg', 'sha256': 'c' * 64}})
    monkeypatch.setattr(client.subprocess, 'check_output', lambda *args, **kwargs: 'fixture-commit\n')
    monkeypatch.setattr(client.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=100 * 1024**3, f_frsize=1))
    monkeypatch.setattr(client, 'disk_usage_kib', lambda _: (1, []))
    monkeypatch.setattr(client, 'run_stage', stage)
    argv = ['bfs_simulator_series.py', '--id', 'series-fixture', '--candidate', candidate['id'],
        '--workload', workload['id'], '--build-evaluation', model['id'], '--configuration', str(config),
        '--runs-dir', '/data/yanruj/EvolveSWDB_runs/series-fixture', '--records', str(tmp_path / 'records'), '--lane', '1']
    if frozen_series:
        argv += ['--protocol', frozen['id'], '--protocol-role', 'baseline']
    monkeypatch.setattr(sys, 'argv', argv)
    client.main()
    expected_cells = [(position, vertex, repetition) for position, vertex in enumerate(workload['definition']['sources'])
                      for repetition in range(2) for _ in ('primary', 'diagnostic')]
    assert [(row['protocol_trial']['source_position'], row['workload']['source'], row['protocol_trial']['repetition'])
            for row in execution_requests] == expected_cells
    assert all(set(row['protocol_trial']) == {'source_position', 'repetition'} for row in execution_requests)
    assert all(('protocol' in row) == (frozen_series and '.primary.' in row['id']) for row in execution_requests)
