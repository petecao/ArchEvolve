"""Blind campaign pairing through public fixture campaigns; all fixture numbers are synthetic."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
import yaml

from swdb.store import Store
from conftest import run_swdb
from testkit.extensa import campaign_file, campaign_store, fixture_file, provider, records_of, run


def test_fixture_freezes_each_artifact_input_before_pilot_and_comparison(campaign_team):
    summary = run(campaign_team, campaign_file(campaign_team), fixture_file(campaign_team),
                  provider(campaign_team, {}))
    pairing = summary["paired_estimates"]
    records = records_of(campaign_store(campaign_team), "paired_estimates")
    assert records and pairing["records"] and pairing["outcome_accesses"]
    by_id = {r["id"]: r for r in records}
    assert all(r["mode"] == "extensa" and r["campaign"] == summary["campaign"] for r in records)
    assert any("pilot" in e["stage"] for e in pairing["outcome_accesses"])
    assert any("comparison" in e["stage"] for e in pairing["outcome_accesses"])
    for event in pairing["outcome_accesses"]:
        for rid in event["paired_estimates"]:
            assert by_id[rid]["estimated_at"] < event["outcome_access_started_at"]
            assert not by_id[rid]["eligible_for_agreement"]
    result = run_swdb("validate", "--records", campaign_store(campaign_team))
    assert result.returncode == 0, result.stderr

# The real campaign loop and adapters run; only the evaluator/host are contract
# fixtures at the established evaluator seam. No application performance evidence.
from testkit.extensa import knob_rows
from testkit.extensa_targets import FakeHost, FakeRunner, common, gem5_campaign, inside_patch, run as run_target, write_campaign


class AuditedRunner(FakeRunner):
    def __init__(self, team, cid, ratios):
        super().__init__(ratios)
        self.folder = team['root'] / 'runs' / 'extensa' / cid
        self.boundaries = []

    def __call__(self, command, request=None, *, stage, **kwargs):
        if command in {'evaluate-pair', 'dx100-execute'}:
            path = self.folder / 'pairing/outcome-accesses.jsonl'
            assert path.is_file(), 'the evaluator opened before its pairing boundary was persisted'
            event = json.loads(path.read_text().splitlines()[-1])
            assert event['stage'] == stage
            records = Store(self.folder / 'records')
            now = datetime.now(timezone.utc)
            for rid in event['paired_estimates']:
                receipt = records.get(rid, 'paired_estimate')
                assert receipt is not None
                assert datetime.fromisoformat(receipt['estimated_at']) < now
            self.boundaries.append({'stage': stage, 'command': command, 'request': request,
                                    'started': now.isoformat(), 'event': event})
        return super().__call__(command, request, stage=stage, **kwargs)


def native_pairing_file(team):
    data = common(team, 'extensa-native-bfs-20261004-f1', 'native_cpu')
    data.update(baselines=[{'role': 'fork_scalar_tdstep', 'candidate': 'bfs-native-pilot-20260925-dx10018-a1.baseline'},
                           {'role': 'upstream_do_bfs', 'candidate': 'bfs-native-pilot-20260925-upstream18-a2.baseline'}],
                protocol={'roi': 'bfs.complete_call.v1', 'threads': 1, 'repetitions': 10,
                          'sources': [0, 1234, 7777], 'region_pairs': False, 'differences': 'Pairing contract fixture.'},
                workload_classes=[{'class': 'kronecker', 'workload': 'bfs-20260925-kronecker18.48de8267ac2098d5'},
                                  {'class': 'uniform_random', 'workload': 'bfs-20260925-uniform18.cd2169a5c421baf7'}],
                library={'allowed_tiers': ['shared', 'experimental'], 'contracts': []})
    data['budgets']['max_iterations'] = 1
    return write_campaign(team, data)


@pytest.mark.parametrize('target', ['native_cpu', 'dx100_gem5'])
def test_real_adapters_persist_estimates_before_every_evaluator_entry(repo_team, base_source, target):
    import yaml
    path = native_pairing_file(repo_team) if target == 'native_cpu' else gem5_campaign(repo_team, max_iterations=1)
    cid = yaml.safe_load(path.read_text())['id']
    patch = base_source + '// fixture pairing edit\n' if target == 'native_cpu' else None
    if target == 'native_cpu':
        from testkit.extensa_targets import diff
        patch = diff(base_source, patch)
    else:
        patch = inside_patch(base_source)
    config = provider(repo_team, {'rewriting': [{'patch': patch, 'contracts': [] if target == 'native_cpu' else ['contract.bfs_read_offload'],
                                              'knobs': knob_rows({}), 'unresolved': []}]})
    runner = AuditedRunner(repo_team, cid, {'pilot': 1.0, 'fork_scalar_tdstep': 1.3, 'upstream_do_bfs': 0.8,
                                           'kronecker': 1.4, 'uniform_random': 1.02})
    loop, summary = run_target(repo_team, path, config, runner, FakeHost())
    assert summary['stop_reason'] == 'max_iterations'
    assert runner.boundaries
    rows = summary['paired_estimates']['records']
    assert rows and all(r['seconds'] is None and not r['eligible_for_agreement'] for r in rows)
    # A new candidate record ID cannot make identical artifact content blind again.
    catalog = Store(loop.store_dir)
    for boundary in runner.boundaries:
        subjects = ([boundary['request'][side]['candidate'] for side in ('baseline', 'candidate')]
                    if target == 'native_cpu' else [boundary['request']['candidate']])
        for subject in subjects:
            sha = catalog.get(subject)['artifact']['sha256']
            assert all(r['estimated_at'] < boundary['started'] for r in rows
                       if r['timing_context']['subject']['artifact_sha256'] == sha)
    assert all(boundary['event']['timing_contexts'] for boundary in runner.boundaries)
    if target == 'native_cpu':
        assert sum('.pilot.' in row['stage'] for row in runner.boundaries) == 4
        assert all(len(row['event']['paired_estimates']) == 2 for row in runner.boundaries)
    else:
        assert sum('.companion.' in row['stage'] for row in runner.boundaries) == 4
        assert sum('.baseline.' in row['stage'] for row in runner.boundaries) == 2
        # Every class context for an artifact predates ANY companion timing for it.
        for boundary in runner.boundaries:
            candidate = boundary['request']['candidate']
            if '.companion.' in boundary['stage']:
                assert all(r['estimated_at'] < boundary['started'] for r in rows
                           if r['timing_context']['subject']['id'] == candidate)
        assert all('functional_trial_lambda_to_mmio_complete_call_bridge' in r['structural_missing'] for r in rows)


@pytest.mark.parametrize('damage', ['missing_events', 'policy_changed'])
def test_resume_refuses_lost_or_changed_prior_baseline_estimate_before_provider(campaign_team, damage):
    from testkit.extensa import GEM5
    import yaml
    path = campaign_file(campaign_team, cid=GEM5, target='dx100_gem5')
    fixture, config = fixture_file(campaign_team), provider(campaign_team, {})
    prepared = run(campaign_team, path, fixture, config, '--baselines-only')
    assert prepared['baselines'] and prepared['paired_estimates']['records']
    folder = campaign_team['root'] / 'runs/extensa' / GEM5
    if damage == 'missing_events':
        (folder / 'pairing/outcome-accesses.jsonl').unlink()
    else:
        policy = json.loads((folder / 'pairing/policy.json').read_text())
        policy['estimator_sha256'] = '0' * 64
        (folder / 'pairing/policy.json').write_text(json.dumps(policy))
    result = run_swdb('campaign', path, '--records', campaign_team['records'], '--fixture', fixture,
                      '--provider-config', config, '--resume', '--format', 'json')
    assert result.returncode == 1, result.stderr + result.stdout[:500]
    assert 'paired estimate' in result.stderr
    assert not (campaign_team['root'] / 'provider-log.jsonl').exists()


@pytest.mark.parametrize('damage', ['chronology', 'artifact', 'backend', 'input'])
def test_team_summary_validates_embedded_pairing_hashes_and_chronology(campaign_team, damage):
    import yaml
    summary = run(campaign_team, campaign_file(campaign_team), fixture_file(campaign_team), provider(campaign_team, {}))
    path = campaign_team['records'] / 'campaign_summaries' / (summary['id'] + '.yaml')
    data = yaml.safe_load(path.read_text())
    event = data['paired_estimates']['outcome_accesses'][0]
    if damage == 'chronology':
        event['outcome_access_started_at'] = '1900-01-01T00:00:00+00:00'
    elif damage == 'artifact':
        event['timing_contexts'][0]['subject']['artifact_sha256'] = '0' * 64
    elif damage == 'input':
        event['timing_contexts'][0]['input']['identity_sha256'] = '0' * 64
    else:
        event['timing_contexts'][0]['execution']['backend'] = 'spoofed_mmio_backend'
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', campaign_team['records'])
    assert result.returncode == 1, result.stderr + result.stdout[:500]
    assert 'paired_estimates' in result.stderr and 'preced' in result.stderr


def test_synthetic_estimates_do_not_change_timing_selection_or_plateau(campaign_team):
    fixture = fixture_file(campaign_team, estimate_fixture={
        'work_units': {'baseline': 10, 'candidate': 1000}, 'units_per_second': 100})
    config = provider(campaign_team, {})
    enabled = run(campaign_team, campaign_file(campaign_team), fixture, config)
    disabled = run(campaign_team, campaign_file(campaign_team, cid='extensa-native-bfs-20261004-a2',
                   paired_estimates={'enabled': False}), fixture, config)
    rows = enabled['paired_estimates']['records']
    assert {r['seconds'] for r in rows} == {0.1, 10}
    assert all(r['evidence_kind'] == 'contract_fixture' and not r['eligible_for_agreement'] for r in rows)
    assert not disabled['paired_estimates']['records']
    def selected(summary):
        return [(c['class'], c['level'], c['selection'], c['artifact_sha256'])
                for iteration in summary['iterations'] for c in iteration['candidates']]
    assert selected(enabled) == selected(disabled)
    assert enabled['stop_reason'] == disabled['stop_reason'] == 'max_iterations'
    assert enabled['budgets']['used']['iterations'] == disabled['budgets']['used']['iterations']
    assert all(c['selection']['verdict'] == 'gain' for it in enabled['iterations'] for c in it['candidates'])


def test_team_protocol_recursively_refuses_paired_receipt_but_extensa_keeps_dispatch(campaign_team):
    summary = run(campaign_team, campaign_file(campaign_team), fixture_file(campaign_team), provider(campaign_team, {}))
    records = campaign_store(campaign_team)
    paired = summary['paired_estimates']['records'][0]['id']
    catalog = Store(records)
    relay = copy.deepcopy(catalog.get(campaign_team['machine']))
    relay['id'] = 'native-pairing-relay'
    relay.setdefault('notes', []).append(paired)
    relay_file = campaign_team['root'] / 'relay.yaml'
    relay_file.write_text(yaml.safe_dump(relay, sort_keys=False))
    added = run_swdb('add', relay_file, '--records', records, '--mode', 'extensa',
                     '--campaign', summary['campaign'])
    assert added.returncode == 0, added.stderr + added.stdout[:500]
    settings = copy.deepcopy(catalog.get(campaign_team['protocol'])['settings'])
    settings['differences']['software'].append(relay['id'])
    request = campaign_team['root'] / 'freeze-paired.yaml'
    request.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.paired.boundary',
                                     'version': 1, 'settings': settings}, sort_keys=False))
    refused = run_swdb('freeze-protocol', request, '--records', records, '--mode', 'archevolve')
    assert refused.returncode == 1 and all(term in refused.stderr for term in ('ADR 0013', paired, relay['id']))
    accepted = run_swdb('freeze-protocol', request, '--records', records, '--mode', 'extensa',
                        '--campaign', summary['campaign'], '--format', 'json')
    assert accepted.returncode == 0, accepted.stderr + accepted.stdout[:500]
    frozen = json.loads(accepted.stdout)
    assert frozen['mode'] == 'extensa' and frozen['campaign'] == summary['campaign']
    checked = run_swdb('validate', '--records', records)
    assert checked.returncode == 0, checked.stderr + checked.stdout[:500]
