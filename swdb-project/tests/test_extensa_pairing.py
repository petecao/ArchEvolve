"""Blind campaign pairing through public fixture campaigns; all fixture numbers are synthetic."""
import json

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
from datetime import datetime, timezone
from pathlib import Path

import pytest
from swdb.store import Store
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
