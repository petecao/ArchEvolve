"""Prospective agreement through public freeze/report commands. Created2026-10-06 ET.

Contract fixture numbers never become application agreement evidence.
"""
import json

from conftest import run_swdb
from testkit.extensa import GEM5, campaign_file, campaign_store, fixture_file, provider, run


def test_public_report_keeps_fixture_forecasts_ineligible_and_d30_unsupported(campaign_team):
    file = campaign_file(campaign_team, cid=GEM5, target='dx100_gem5')
    config = provider(campaign_team, {})
    frozen = run_swdb('agreement-freeze', '--campaign-file', file, '--provider-config', config,
                      '--records', campaign_team['records'], '--mode', 'extensa',
                      '--campaign', GEM5, '--format', 'json')
    assert frozen.returncode == 0, frozen.stderr
    policy = json.loads(frozen.stdout)
    assert policy['D30'] == {'minimum_unique_eligible_dx100_pairs': 20, 'minimum_tau': 0.6,
                            'minimum_95_interval_lower_bound': 0.3,
                            'gem5_best_in_estimate_top3_every_campaign': True}
    summary = run(campaign_team, file, fixture_file(campaign_team,
        estimate_fixture={'work_units': {'baseline': 10, 'candidate': 1000}, 'units_per_second': 100}), config)
    result = run_swdb('agreement-report', '--policy', policy['id'], '--campaign-records',
                     campaign_store(campaign_team, GEM5), '--records', campaign_team['records'],
                     '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['counts']['observed_candidate_rows'] > 0
    assert report['counts']['unique_eligible_dx100_pairs'] == 0
    assert report['gate']['state'] == 'unsupported'
    assert report['rank']['tau_b'] is None and report['rank']['interval_95'] is None
    assert report['top3']['state'] == 'unsupported'
    assert report['recommendation'] == 'do_not_switch_to_flow_b'
    assert any('contract_fixture' in row['exclusions'] for row in report['pairs'])
    assert report['blind_order']['state'] == 'verified'
    assert report['selection_policy'] == 'unchanged_timing_only'
    assert all(row['best'] == next(r['best'] for r in summary['per_class'] if r['class'] == row['class'])
               for row in report['top3']['strata'])
    checked = run_swdb('validate', '--records', campaign_team['records'])
    assert checked.returncode == 0, checked.stderr

from testkit.extensa_targets import gem5_campaign


def test_public_freeze_is_immutable_for_the_same_prospective_campaign_population(repo_team):
    file = gem5_campaign(repo_team, max_iterations=1)
    config = provider(repo_team, {})
    import yaml
    cid = yaml.safe_load(file.read_text())['id']
    args = ('agreement-freeze', '--campaign-file', file, '--provider-config', config,
            '--records', repo_team['records'], '--mode', 'extensa', '--campaign', cid, '--format', 'json')
    first = run_swdb(*args)
    assert first.returncode == 0, first.stderr
    first = json.loads(first.stdout)
    again = run_swdb(*args)
    assert again.returncode == 0, again.stderr
    again = json.loads(again.stdout)
    assert again['id'] == first['id'] and again['frozen_at'] == first['frozen_at']
    changed = yaml.safe_load(file.read_text())
    changed['budgets']['max_iterations'] = 2
    file.write_text(yaml.safe_dump(changed, sort_keys=False))
    refused = run_swdb(*args)
    assert refused.returncode == 1
    assert 'frozen population' in refused.stderr
