"""Existing candidate reuse through fresh public queries. Updated: 2026-09-26 ET.

Fixture timings and provider metadata below are contract evidence only.
"""
import copy
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from conftest import records as records_fixture
from scripts import bfs_native_campaign as campaign
from swdb import artifacts
from swdb.cli import Failure
from test_proposals import proposal_setup
from test_bfs_native import evaluation_setup


@pytest.fixture(scope='module')
def reuse_seed(tmp_path_factory):
    folder = tmp_path_factory.mktemp('campaign-reuse-contract')
    records = records_fixture.__wrapped__(folder)
    return evaluation_setup.__wrapped__(proposal_setup.__wrapped__(records, folder), folder)


@pytest.fixture
def reuse_case(reuse_seed, tmp_path, monkeypatch):
    seed, _, _, base = reuse_seed
    records = records_fixture.__wrapped__(tmp_path)
    shutil.copytree(seed.path, records.path, dirs_exist_ok=True)
    runs = tmp_path / 'campaign-runs'; runs.mkdir()
    args = SimpleNamespace(id='reuse-contract', protocol='fixture-policy', lane='fixture-lane',
        total_seconds=120, runs_dir=runs, source_runs_dir=tmp_path / 'sources', records=records.path,
        provider_config=None, repair_config=None, existing_candidate=base['candidate'])
    args.source_runs_dir.mkdir()
    # Only driver host/resource preconditions are replaced. Every SWDB command
    # remains an actual subprocess, and evaluation uses its explicit fixture flag.
    monkeypatch.setattr(campaign.profile, '_verified_lane', lambda *_: 'fixture-lane')
    monkeypatch.setattr(campaign.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=100 * 1024**3, f_frsize=1))
    worker = campaign.Driver(args)
    proposal = records.read('proposals/test-proposal.yaml')
    candidate = records.read('candidates/' + proposal['candidate'] + '.yaml')
    source = records.read('source_snapshots/test-source.yaml')
    package = records.read('profile_packages/test-package.yaml')
    return SimpleNamespace(worker=worker, records=records, proposal=proposal, candidate=candidate,
        source=source, package=package, request=copy.deepcopy(proposal['request']), base=copy.deepcopy(base))


def test_fresh_submit_route_still_creates_candidate_through_public_submit(reuse_case):
    case = reuse_case
    case.worker.args.existing_candidate = None
    case.request['id'] = 'fresh-campaign-request'
    result = case.worker.acquire_candidate(case.request)
    assert result['outcome']['state'] == 'candidate_created'
    assert result['candidate'] == 'fresh-campaign-request.candidate-1'
    assert [row['command'][3] for row in case.worker.receipt['stages']] == ['submit']
    assert 'candidate_acquisition' not in case.worker.receipt
    later = case.records.swdb('get', result['candidate'], '--chain', '--format', 'json')
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout)['records'][result['candidate']]['proposal'] == case.request['id']


def test_exact_reuse_never_resubmits_and_can_continue_public_fixture_evaluation(reuse_case):
    case = reuse_case
    before = artifacts.digest(case.proposal)
    result = case.worker.acquire_candidate(case.request)
    assert artifacts.digest(result) == before
    assert [row['command'][3] for row in case.worker.receipt['stages'] if row['command'][1:3] == ['-m', 'swdb']] == ['get'] * 5
    assert case.worker.receipt['candidate_acquisition']['patch_binding']['candidate_sha256'] == case.candidate['artifact']['sha256']
    assert list(case.worker.args.source_runs_dir.iterdir()) == []
    assert case.worker.receipt['candidate_acquisition']['candidate'] == case.candidate['id']
    assert case.worker.receipt['candidate_acquisition']['gain_claim'] is False
    result = case.worker.request('evaluate', {**case.base, 'id': 'reuse-evaluation'},
                                 '--runs-dir', case.worker.args.runs_dir, timeout=60)
    assert result['outcome']['state'] == 'complete'
    assert result['evidence_kind'] == 'contract_fixture' and result['gain_claim'] is False
    later = case.worker.call('get', result['id'], '--chain')
    chain = later['records']
    assert artifacts.digest(chain[case.proposal['id']]) == before
    assert chain[result['id']]['proposal'] == case.proposal['id']
    assert chain[result['id']]['candidate'] == case.candidate['id']
    assert chain[case.package['id']]['completeness'] == 'fixture'
    for stage in case.worker.receipt['stages']:
        assert artifacts.file_hash(stage['stdout']) == stage['stdout_sha256']
    assert not any(row['command'][3] in ('submit', 'repair') for row in case.worker.receipt['stages'])


@pytest.mark.parametrize('fault', ['request', 'numeric-request', 'candidate', 'profile', 'source',
                                  'parent', 'repair-attempt', 'repair-budget', 'diff', 'artifact', 'rehashed-artifact'])
def test_reuse_mismatches_fail_before_submit_provider_or_evaluation(reuse_case, tmp_path, fault):
    case = reuse_case
    if fault == 'request': case.request['intent'] += ' changed'
    elif fault == 'numeric-request':
        case.request['parameters'] = {'same_python_value': True}
        case.proposal['request']['parameters'] = {'same_python_value': 1}
        case.records.write('proposals/test-proposal.yaml', case.proposal)
    elif fault == 'candidate': case.worker.args.existing_candidate = 'missing-candidate'
    elif fault == 'profile':
        case.proposal['profile_package'] = 'missing-package'
        case.records.write('proposals/test-proposal.yaml', case.proposal)
    elif fault == 'source':
        case.candidate['source_snapshot'] = 'missing-source'
        case.records.write('candidates/' + case.candidate['id'] + '.yaml', case.candidate)
    elif fault == 'parent':
        case.candidate['parent_candidate'] = case.candidate['id']
        case.records.write('candidates/' + case.candidate['id'] + '.yaml', case.candidate)
    elif fault == 'repair-attempt':
        case.proposal['attempts'].append({'number': 2, 'stage': 'repair', 'state': 'completed', 'candidate': case.candidate['id']})
        case.records.write('proposals/test-proposal.yaml', case.proposal)
    elif fault == 'repair-budget':
        case.proposal['repair_budget'] = {'max_repairs': 1, 'total_seconds': 60, 'used_seconds': 1.0, 'repairs': 1}
        case.records.write('proposals/test-proposal.yaml', case.proposal)
    elif fault == 'diff':
        diff = tmp_path / 'changed.diff'; diff.write_text(case.request['payload']['content'] + '\n')
        case.candidate.update(diff=str(diff), diff_sha256=artifacts.file_hash(diff))
        case.records.write('candidates/' + case.candidate['id'] + '.yaml', case.candidate)
    else:
        changed = tmp_path / 'changed-source'; shutil.copytree(case.candidate['artifact']['path'], changed)
        target = changed / 'src/bfs.cc'
        target.write_text(target.read_text().replace('int alpha = 14', 'int alpha = 999'))
        case.candidate['artifact']['path'] = str(changed)
        if fault == 'rehashed-artifact': case.candidate['artifact'] = artifacts.identify(changed)
        case.records.write('candidates/' + case.candidate['id'] + '.yaml', case.candidate)
    with pytest.raises((ValueError, RuntimeError, Failure), match='bytes differ from replaying' if fault == 'rehashed-artifact' else None):
        case.worker.acquire_candidate(case.request)
    assert all(row['command'][3] == 'get' for row in case.worker.receipt['stages'] if row['command'][1:3] == ['-m', 'swdb'])
    assert list(case.worker.args.source_runs_dir.iterdir()) == []
    assert not case.worker.receipt['candidate_rounds']


def test_provider_option_is_rejected_on_reuse_without_starting_a_public_command(reuse_case):
    case = reuse_case
    case.worker.args.provider_config = Path('/fixture/never-opened-provider-config')
    with pytest.raises(ValueError, match='never invokes a provider'):
        case.worker.acquire_candidate(case.request)
    assert case.worker.receipt['stages'] == []


def test_patch_replay_cannot_start_after_the_campaign_deadline_and_cleans_temp_tree(reuse_case):
    case = reuse_case
    case.worker.started -= 200
    with pytest.raises(TimeoutError, match='total wall budget'):
        case.worker.replay_candidate(case.request, case.source, case.candidate, case.request['payload']['content'])
    assert case.worker.receipt['stages'] == []
    assert list(case.worker.args.source_runs_dir.iterdir()) == []


def test_patch_replay_failure_retains_process_result_and_cleans_temp_tree(reuse_case):
    case = reuse_case
    with pytest.raises(RuntimeError, match='candidate-binding failed'):
        case.worker.replay_candidate(case.request, case.source, case.candidate, 'invalid fixture patch')
    assert list(case.worker.args.source_runs_dir.iterdir()) == []
    stage = case.worker.receipt['stages'][-1]
    assert stage['state'] == 'failed' and stage['returncode'] != 0
    assert artifacts.file_hash(stage['stderr']) == stage['stderr_sha256']


def interpreted_fixture(case):
    """Synthetic retained provider metadata, without invoking any provider."""
    request = copy.deepcopy(case.request)
    patch = request['payload']['content']
    request['payload'] = {'kind': 'structured_instructions', 'content': {'alpha': 14}}
    submitted = copy.deepcopy(case.proposal)
    submitted.update(request=copy.deepcopy(request), payload_sha256=artifacts.digest(request['payload']),
                     interpretation={'interpretation': 'Fixture metadata: alpha 14.', 'patch': patch, 'unresolved': []},
                     provider={'kind': 'claude', 'max_repairs': 1, 'total_seconds': 60, 'timeout_s': 30},
                     repair_budget={'max_repairs': 1, 'total_seconds': 60, 'used_seconds': 2.0, 'repairs': 0})
    submitted['attempts'][0]['provider'] = {'classification': 'rewrite_provider', 'state': 'completed',
        'returncode': 0, 'host_wall_s': 2.0, 'provider': copy.deepcopy(submitted['provider'])}
    return request, submitted


@pytest.mark.parametrize('kind', ['claude', 'codex'])
def test_interpreted_reuse_preserves_original_provider_time_and_repair_budget(reuse_case, kind):
    case = reuse_case
    request, submitted = interpreted_fixture(case)
    submitted['provider']['kind'] = kind
    submitted['attempts'][0]['provider']['provider']['kind'] = kind
    if kind == 'codex':
        pins = {'resolved_kind':'codex','model':'gpt-5.6-sol','effort':'xhigh'}
        submitted['provider'].update(pins)
        submitted['attempts'][0]['provider']['provider'].update(pins)
    result = campaign.validate_existing_candidate(request, submitted, case.candidate, case.source, case.package, case.worker.replay_candidate)
    assert result['repair_budget'] == {'max_repairs': 1, 'total_seconds': 60, 'used_seconds': 2.0, 'repairs': 0}
    assert result['gain_claim'] is False


@pytest.mark.parametrize('fault', ['missing-budget', 'changed-used', 'nonfinite', 'used-bool', 'reset-total',
                                  'fixture-kind', 'fixture-class', 'provider-binding'])
def test_interpreted_reuse_cannot_promote_fixture_provider_or_reset_consumed_time(reuse_case, fault):
    case = reuse_case
    request, submitted = interpreted_fixture(case)
    if fault == 'missing-budget': submitted.pop('repair_budget')
    elif fault == 'changed-used': submitted['repair_budget']['used_seconds'] = 0
    elif fault == 'nonfinite': submitted['repair_budget']['used_seconds'] = float('nan')
    elif fault == 'used-bool': submitted['repair_budget']['used_seconds'] = True
    elif fault == 'reset-total': submitted['repair_budget']['total_seconds'] = 120
    elif fault == 'fixture-kind': submitted['provider']['kind'] = 'external_fixture'
    elif fault == 'fixture-class': submitted['attempts'][0]['provider']['classification'] = 'contract_fixture'
    else: submitted['attempts'][0]['provider']['provider']['total_seconds'] = 120
    with pytest.raises(ValueError):
        campaign.validate_existing_candidate(request, submitted, case.candidate, case.source, case.package, case.worker.replay_candidate)
