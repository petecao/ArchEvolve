"""Runtime input contracts using public external-compiler fixtures. Date: 2026-09-26 ET.

Artificial durations and explicitly synthetic historical records prove no gain,
calibration, OpenMP team size, worker placement, or cause of timing variability.
"""
import copy
import json
import shutil
from pathlib import Path

import pytest

from conftest import make_records
from testkit.proposals import build_proposal_setup
from testkit.bfs_native import build_evaluation_setup
from testkit.bfs_native import PROGRAM
from testkit.bfs_protocol import _command, _fixture_rebind, _payload, _settings, _workload_request
from swdb import artifacts, bfs_native, bfs_protocol
from swdb.cli import Failure


def policy(threads=1):
    return {'version': 1, 'environment': {**bfs_native.controlled_environment(threads),
            'OMP_THREAD_LIMIT': str(threads + 1), 'OMP_WAIT_POLICY': 'PASSIVE',
            'GOMP_SPINCOUNT': None, 'GOMP_CPU_AFFINITY': None}}


@pytest.mark.parametrize('key,value', [('OMP_THREAD_LIMIT', '0'), ('OMP_THREAD_LIMIT', '1'),
    ('OMP_THREAD_LIMIT', '-1'), ('OMP_THREAD_LIMIT', '2,4'), ('OMP_THREAD_LIMIT', 'two'),
    ('OMP_THREAD_LIMIT', str(2**32)), ('OMP_THREAD_LIMIT', '\u20032'), ('OMP_WAIT_POLICY', 'ACT\u0130VE'),
    ('OMP_WAIT_POLICY', 'sometimes'), ('OMP_WAIT_POLICY', ''), ('GOMP_SPINCOUNT', 0),
    ('GOMP_CPU_AFFINITY', '0\0'), ('OMP_NUM_THREADS', '1'), ('OMP_DYNAMIC', None)])
def test_malformed_or_ineffective_declared_inputs_are_rejected(key, value):
    requested = policy(2)
    requested['environment'][key] = value
    with pytest.raises(Failure, match='native_runtime'):
        bfs_native.validate_runtime_policy(requested, 2)


@pytest.mark.parametrize('fault', ['missing', 'extra', 'wrong-version', 'unknown-null'])
def test_runtime_policy_has_an_exact_versioned_map(fault):
    requested = policy()
    if fault == 'missing': requested['environment'].pop('GOMP_SPINCOUNT')
    elif fault == 'extra': requested['environment']['OTHER'] = None
    elif fault == 'wrong-version': requested['version'] = True
    else: requested = None
    with pytest.raises(Failure, match='native_runtime'):
        bfs_native.validate_runtime_policy(requested, 1)


def test_new_unfrozen_collection_captures_explicit_unsets_without_mutating_parent():
    inherited = {'OMP_THREAD_LIMIT': '2', 'OMP_WAIT_POLICY': 'passive', 'OMP_NUM_THREADS': '99', 'PATH': '/bin'}
    before = copy.deepcopy(inherited)
    environment, retained = bfs_native.runtime_environment(1, environ=inherited)
    assert inherited == before and environment['PATH'] == '/bin'
    assert retained['environment']['GOMP_SPINCOUNT'] is None
    assert retained['environment']['GOMP_CPU_AFFINITY'] is None
    assert environment['OMP_NUM_THREADS'] == '1'
    with pytest.raises(Failure, match='unknown'):
        bfs_native.runtime_environment(1, required=True, environ=inherited)


def test_valid_ascii_whitespace_and_case_preserve_exact_declared_spelling():
    requested = policy(2)
    requested['environment'].update(OMP_THREAD_LIMIT=' \t+4\n', OMP_WAIT_POLICY='\tPaSsIvE ')
    environment, retained = bfs_native.runtime_environment(2, requested, environ={})
    assert retained == requested and environment['OMP_WAIT_POLICY'] == '\tPaSsIvE '


@pytest.fixture(scope='module')
def runtime_seed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp('runtime-contract')
    records = make_records(tmp)
    setup = build_evaluation_setup(build_proposal_setup(records, tmp), tmp)
    _, runs, _, base = setup
    program = PROGRAM.replace('out.write_text(json.dumps(data))',
        "data['received_runtime'] = {key: os.environ.get(key) for key in "
        + repr(tuple(policy()['environment'])) + "}\nout.write_text(json.dumps(data))")
    compiler = Path(base['build']['compiler'])
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({program!r}); p.chmod(0o755)\n")
    workload = _command(records, 'register-workload', _payload(tmp, 'register',
                        _workload_request(records, tmp, base['workload']['graph'])))
    created = records.swdb('baseline-candidate', 'test-source', '--id', 'runtime-baseline', '--runs-dir', runs, '--format', 'json')
    assert created.returncode == 0, created.stderr
    baseline = json.loads(created.stdout)['id']
    ambient = {'OMP_NUM_THREADS': '99', 'OMP_DYNAMIC': 'TRUE', 'OMP_PROC_BIND': 'spread', 'OMP_PLACES': 'threads',
               'OMP_THREAD_LIMIT': '1', 'OMP_WAIT_POLICY': 'ACTIVE', 'GOMP_SPINCOUNT': '300000', 'GOMP_CPU_AFFINITY': '999'}
    cases = {}
    for mode in ('serial', 'paired'):
        settings = _settings(base, workload)
        settings['native_runtime'] = policy()
        if mode == 'paired':
            settings['sampling'].update(collection={'method': 'native_paired.v1', 'order_seed': 20260926},
                                        analysis='paired_repetition_block_bootstrap.v1')
            settings['profitability'].update(minimum_speedup=1.05, bootstrap_seed=20260925)
        frozen = _command(records, 'freeze-protocol', _payload(tmp, mode + '-freeze', {
            'message_version': '1.0', 'id': mode + '-runtime-policy', 'version': 1, 'settings': settings}))
        members = {role: {**copy.deepcopy(base), 'id': mode + '.' + role, 'candidate': baseline,
            'protocol': frozen['id'], 'protocol_role': role, 'workload': {'id': workload['id']},
            'sources': workload['definition']['sources'], 'repetitions': 5} for role in ('baseline', 'candidate')}
        if mode == 'paired':
            request = {'message_version': '1.0', 'id': 'runtime-aa', **members,
                       'collection': settings['sampling']['collection'], 'budget': {'total_seconds': 120}}
            result = records.swdb('evaluate-pair', _payload(tmp, 'pair', request), '--runs-dir', runs, '--format', 'json', env=ambient)
            assert result.returncode == 0, result.stdout + result.stderr
            assert json.loads(result.stdout)['outcome']['state'] == 'complete'
        else:
            for role, member in members.items():
                result = records.swdb('evaluate', _payload(tmp, role, member), '--runs-dir', runs, '--format', 'json', env=ambient)
                assert result.returncode == 0, result.stdout + result.stderr
        evaluations = {role: records.read('evaluations/' + member['id'] + '.yaml') for role, member in members.items()}
        comparison = {'message_version': '1.0', 'id': mode + '-comparison', 'protocol': frozen['id'],
                      'baseline_evaluation': members['baseline']['id'], 'candidate_evaluation': members['candidate']['id'],
                      'comparison_baseline': 'gapbs-bfs-do'}
        cases[mode] = (frozen, evaluations, comparison)
    return records, cases


@pytest.fixture
def runtime_setup(records, runtime_seed):
    original, cases = runtime_seed
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    return records, copy.deepcopy(cases)


@pytest.mark.parametrize('mode', ['serial', 'paired'])
def test_public_execution_replays_frozen_inputs_in_every_child(runtime_setup, tmp_path, mode):
    records, cases = runtime_setup
    frozen, evaluations, comparison = cases[mode]
    for evaluation in evaluations.values():
        assert evaluation['build']['native_runtime'] == frozen['settings']['native_runtime'] == policy()
        assert evaluation['build']['execution_environment'] == bfs_native.controlled_environment(1)
        assert len(evaluation['timing']) == 10
        assert all(json.loads(Path(row['output']).read_text())['received_runtime'] == policy()['environment']
                   for row in evaluation['timing'])
    if mode == 'paired':
        assert evaluations['candidate']['build']['binary'] == evaluations['baseline']['build']['binary']
        assert any(row['stage'] == 'build_reuse' for row in evaluations['candidate']['stages'])
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'compare', comparison))
    assert result['decision']['state'] == 'fixture_comparison' and result['gain_claim'] is False


@pytest.mark.parametrize('mode', ['serial', 'paired'])
@pytest.mark.parametrize('fault', ['missing', 'changed', 'unset-changed', 'controlled-changed', 'contradictory-controlled'])
def test_public_comparison_reopens_runtime_inputs(runtime_setup, tmp_path, mode, fault):
    records, cases = runtime_setup
    _, evaluations, comparison = cases[mode]
    candidate = evaluations['candidate']
    if fault == 'missing': candidate['build'].pop('native_runtime')
    elif fault == 'changed': candidate['build']['native_runtime']['environment']['OMP_WAIT_POLICY'] = 'ACTIVE'
    elif fault == 'unset-changed': candidate['build']['native_runtime']['environment']['GOMP_SPINCOUNT'] = '0'
    elif fault == 'controlled-changed': candidate['build']['native_runtime']['environment']['OMP_NUM_THREADS'] = '2'
    else: candidate['build']['execution_environment']['OMP_NUM_THREADS'] = '2'
    records.write('evaluations/' + candidate['id'] + '.yaml', candidate)
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'bad', comparison), succeeds=False)
    assert result['decision']['state'] == 'rejected' and not result['gain_claim']
    assert 'runtime' in str(result['decision']['reasons'])


def legacy_fixture(records, case):
    frozen, evaluations, comparison = copy.deepcopy(case)
    frozen['settings'].pop('native_runtime')
    frozen['requested_id'] = 'historical-runtime-fixture'
    frozen['identity_sha256'] = artifacts.digest(bfs_protocol._identity_payload(frozen))
    frozen['id'] = frozen['requested_id'] + '.' + frozen['identity_sha256'][:16]
    records.write('protocols/' + frozen['id'] + '.yaml', frozen)
    for role, original in evaluations.items():
        value = _fixture_rebind(original, frozen, role, 'historical.' + role)
        value['build'].pop('native_runtime')
        records.write('evaluations/' + value['id'] + '.yaml', value)
        evaluations[role] = value
        comparison[role + '_evaluation'] = value['id']
    comparison.update(id='historical-comparison', protocol=frozen['id'])
    return frozen, evaluations, comparison


def test_historical_records_remain_readable_and_fixture_comparison_stays_nonempirical(runtime_setup, tmp_path):
    records, cases = runtime_setup
    frozen, _, comparison = legacy_fixture(records, cases['serial'])
    result = records.swdb('get', frozen['id'], '--format', 'json')
    assert result.returncode == 0 and json.loads(result.stdout) == frozen
    compared = _command(records, 'compare-evaluations', _payload(tmp_path, 'legacy', comparison))
    assert compared['decision']['state'] == 'fixture_comparison' and not compared['gain_claim']


def test_relabeling_historical_fixtures_cannot_authorize_empirical_comparison(runtime_setup, tmp_path):
    records, cases = runtime_setup
    _, evaluations, comparison = legacy_fixture(records, cases['serial'])
    # Adversarial metadata only: this does not turn the fixture into execution.
    for evaluation in evaluations.values():
        evaluation['evidence_kind'] = 'execution'
        evaluation['request']['fixture'] = False
        records.write('evaluations/' + evaluation['id'] + '.yaml', evaluation)
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'no-promotion', comparison), succeeds=False)
    assert result['decision']['state'] == 'rejected' and not result['gain_claim']
    assert 'native_runtime' in str(result['decision']['reasons'])


@pytest.mark.parametrize('fixture', [True, False])
def test_historical_protocol_allows_only_explicit_fixture_dispatch(runtime_setup, tmp_path, fixture):
    records, cases = runtime_setup
    _, evaluations, _ = legacy_fixture(records, cases['serial'])
    request = evaluations['baseline']['request']
    request.update(id='legacy-dispatch', fixture=fixture)
    result = records.swdb('evaluate', _payload(tmp_path, 'legacy-dispatch', request), '--runs-dir', tmp_path / 'runs', '--format', 'json')
    assert result.returncode == (0 if fixture else 1), result.stderr
    evaluation = json.loads(result.stdout)
    assert not evaluation['gain_claim']
    if fixture:
        assert evaluation['evidence_kind'] == 'contract_fixture' and evaluation['outcome']['state'] == 'complete'
    else:
        assert 'native_runtime' in evaluation['outcome']['reason']
        assert not evaluation['timing'] and all(row['stage'] != 'build' for row in evaluation['stages'])


def test_new_native_freeze_cannot_copy_an_unknown_historical_environment(runtime_setup, tmp_path):
    records, cases = runtime_setup
    settings = copy.deepcopy(cases['serial'][0]['settings'])
    settings.pop('native_runtime')
    result = records.swdb('freeze-protocol', _payload(tmp_path, 'unknown', {
        'message_version': '1.0', 'id': 'unknown-runtime', 'version': 1, 'settings': settings}), '--format', 'json')
    assert result.returncode == 1 and 'native_runtime' in result.stderr
    assert not list((records.path / 'protocols').glob('unknown-runtime*'))


def test_campaign_rejects_unknown_runtime_before_public_retrieval_or_submission(runtime_setup):
    from scripts.bfs_native_campaign import validate_inputs
    records, cases = runtime_setup
    frozen, _, _ = legacy_fixture(records, cases['serial'])
    def forbidden(*_):
        pytest.fail('unsupported native protocol reached package retrieval')
    with pytest.raises(Failure, match='native_runtime'):
        validate_inputs([{'id': 'one'}, {'id': 'two'}], frozen, {}, forbidden, 'unused', 'unused')
