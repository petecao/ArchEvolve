"""Prospective agreement through public freeze/report commands. Created: 2026-10-06 ET.

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
    assert report['basis'] == 'simulated'
    assert report['evidence_kind'] == 'contract_fixture'
    assert all(row['timing_basis'] == 'simulated' and row['structural_missing'] for row in report['pairs'])
    assert report['counts']['observed_candidate_rows'] > 0
    assert report['counts']['unique_eligible_dx100_pairs'] == 0
    assert report['counts']['unique_observed_pair_contents'] is None
    assert all(row['pair_identity_sha256'] is None and row['request_digest_sha256'] for row in report['pairs'])
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


def test_public_validate_refuses_malformed_frozen_population_without_crashing(repo_team):
    import yaml
    file = gem5_campaign(repo_team, max_iterations=1)
    config = provider(repo_team, {})
    cid = yaml.safe_load(file.read_text())['id']
    result = run_swdb('agreement-freeze', '--campaign-file', file, '--provider-config', config,
                     '--records', repo_team['records'], '--mode', 'extensa', '--campaign', cid, '--format', 'json')
    assert result.returncode == 0, result.stderr
    policy = json.loads(result.stdout)
    path = repo_team['records'] / 'agreement_policies' / (policy['id'] + '.yaml')
    damaged = yaml.safe_load(path.read_text())
    damaged['population'] = [{}]
    path.write_text(yaml.safe_dump(damaged, sort_keys=False))
    result = run_swdb('validate', '--records', repo_team['records'])
    assert result.returncode == 1 and 'population' in result.stderr
    assert 'Traceback' not in result.stderr
    damaged = policy
    damaged['population'][0]['configuration'] = {}
    path.write_text(yaml.safe_dump(damaged, sort_keys=False))
    result = run_swdb('validate', '--records', repo_team['records'])
    assert result.returncode == 1 and 'population' in result.stderr
    assert 'Traceback' not in result.stderr


def test_public_report_does_not_claim_pair_blindness_from_baseline_events_alone(campaign_team):
    import yaml
    file = campaign_file(campaign_team, cid=GEM5, target='dx100_gem5')
    config = provider(campaign_team, {})
    frozen = run_swdb('agreement-freeze', '--campaign-file', file, '--provider-config', config,
                     '--records', campaign_team['records'], '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert frozen.returncode == 0, frozen.stderr
    policy = json.loads(frozen.stdout)
    summary = run(campaign_team, file, fixture_file(campaign_team), config)
    source = campaign_store(campaign_team, GEM5)
    summary['paired_estimates']['outcome_accesses'] = [row for row in summary['paired_estimates']['outcome_accesses']
                                                     if not row['stage'].startswith('comparison.')]
    assert summary['paired_estimates']['outcome_accesses']
    path = source / 'campaign_summaries' / (summary['id'] + '.yaml')
    path.write_text(yaml.safe_dump(summary, sort_keys=False))
    result = run_swdb('agreement-report', '--policy', policy['id'], '--campaign-records', source,
                     '--records', campaign_team['records'], '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['blind_order']['state'] == 'unverified'
    assert all('missing_matching_outcome_request' in row['exclusions'] for row in report['pairs'])
    assert report['gate']['state'] == 'unsupported' and report['counts']['unique_eligible_dx100_pairs'] == 0


def test_public_freeze_pins_baseline_artifact_and_metadata(repo_team):
    import yaml
    from swdb import artifacts
    from swdb.store import Store
    file = gem5_campaign(repo_team, max_iterations=1)
    config = provider(repo_team, {})
    cid = yaml.safe_load(file.read_text())['id']
    frozen = run_swdb('agreement-freeze', '--campaign-file', file, '--provider-config', config,
                     '--records', repo_team['records'], '--mode', 'extensa', '--campaign', cid, '--format', 'json')
    assert frozen.returncode == 0, frozen.stderr
    policy = json.loads(frozen.stdout)
    expected = []
    catalog = Store(repo_team['records'])
    for row in yaml.safe_load(file.read_text())['baselines']:
        source = catalog.get(row['candidate'], 'candidate')
        expected.append({'role': row['role'], 'candidate': source['id'],
                         'record_sha256': artifacts.digest(source),
                         'artifact_sha256': source['artifact']['sha256']})
    assert policy['population'][0]['baselines'] == expected


def test_public_team_recursively_refuses_policy_and_report_but_extensa_accepts(campaign_team):
    import copy
    import yaml
    from swdb.store import Store
    file = campaign_file(campaign_team, cid=GEM5, target='dx100_gem5')
    config = provider(campaign_team, {})
    args = ('agreement-freeze', '--campaign-file', file, '--provider-config', config,
            '--records', campaign_team['records'])
    denied = run_swdb(*args)
    assert denied.returncode == 1 and 'ADR 0013' in denied.stderr
    frozen = run_swdb(*args, '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert frozen.returncode == 0, frozen.stderr
    policy = json.loads(frozen.stdout)
    run(campaign_team, file, fixture_file(campaign_team), config)
    result = run_swdb('agreement-report', '--policy', policy['id'], '--campaign-records',
                     campaign_store(campaign_team, GEM5), '--records', campaign_team['records'],
                     '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    catalog = Store(campaign_team['records'])
    for index, rid in enumerate([policy['id'], report['id']]):
        relay = copy.deepcopy(catalog.get(campaign_team['machine']))
        relay['id'] = f'native-agreement-relay-{index}'
        relay.setdefault('notes', []).append(rid)
        relay_file = campaign_team['root'] / f'relay-{index}.yaml'
        relay_file.write_text(yaml.safe_dump(relay, sort_keys=False))
        added = run_swdb('add', relay_file, '--records', campaign_team['records'],
                        '--mode', 'extensa', '--campaign', GEM5)
        assert added.returncode == 0, added.stderr
        settings = copy.deepcopy(catalog.get(campaign_team['protocol'])['settings'])
        settings['differences']['software'].append(relay['id'])
        request = campaign_team['root'] / f'freeze-agreement-{index}.yaml'
        request.write_text(yaml.safe_dump({'message_version': '1.0', 'id': f'fixture.agreement.boundary.{index}',
                                          'version': 1, 'settings': settings}, sort_keys=False))
        denied = run_swdb('freeze-protocol', request, '--records', campaign_team['records'], '--mode', 'archevolve')
        assert denied.returncode == 1 and all(term in denied.stderr for term in ('ADR 0013', rid, relay['id']))
        accepted = run_swdb('freeze-protocol', request, '--records', campaign_team['records'],
                          '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
        assert accepted.returncode == 0, accepted.stderr
    checked = run_swdb('validate', '--records', campaign_team['records'])
    assert checked.returncode == 0, checked.stderr


def test_public_validate_refuses_rehashed_relaxed_d30_and_report_result(campaign_team):
    import yaml
    from swdb.extensa_agreement import identity
    file = campaign_file(campaign_team, cid=GEM5, target='dx100_gem5')
    config = provider(campaign_team, {})
    frozen = run_swdb('agreement-freeze', '--campaign-file', file, '--provider-config', config,
                     '--records', campaign_team['records'], '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert frozen.returncode == 0, frozen.stderr
    policy = json.loads(frozen.stdout)
    run(campaign_team, file, fixture_file(campaign_team), config)
    result = run_swdb('agreement-report', '--policy', policy['id'], '--campaign-records',
                     campaign_store(campaign_team, GEM5), '--records', campaign_team['records'],
                     '--mode', 'extensa', '--campaign', GEM5, '--format', 'json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    for data, folder, field, value, expected in [
        (policy, 'agreement_policies', 'D30', {**policy['D30'], 'minimum_tau': 0.0}, 'D30'),
        (report, 'agreement_reports', 'counts', {**report['counts'], 'unique_eligible_dx100_pairs': 20}, 'gate'),
        (report, 'agreement_reports', 'evidence_kind', 'execution', 'gate')]:
        path = campaign_team['records'] / folder / (data['id'] + '.yaml')
        raw = path.read_bytes()
        mutated = yaml.safe_load(raw)
        mutated[field] = value
        mutated['identity_sha256'] = identity(mutated)
        mutated['id'] = mutated['id'].rsplit('.', 1)[0] + '.' + mutated['identity_sha256'][:16]
        changed_path = path.with_name(mutated['id'] + '.yaml')
        path.unlink()
        changed_path.write_text(yaml.safe_dump(mutated, sort_keys=False))
        checked = run_swdb('validate', '--records', campaign_team['records'])
        assert checked.returncode == 1 and expected in checked.stderr
        assert 'Traceback' not in checked.stderr
        changed_path.unlink()
        path.write_bytes(raw)
    checked = run_swdb('validate', '--records', campaign_team['records'])
    assert checked.returncode == 0, checked.stderr
