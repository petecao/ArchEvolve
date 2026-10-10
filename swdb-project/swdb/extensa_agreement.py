"""Prospective Extensa agreement policy and retained report. Created: 2026-10-06 ET.

No application numeric adapter is registered by ticket16. Unknown and fixture
forecasts therefore cannot demonstrate D30, irrespective of campaign duration.
"""
import copy
import math
import random
from pathlib import Path

from swdb import artifacts, campaign, extensa_pairing, paths, workflow, writer, yamlio
from swdb.cli import Failure, _require_valid
from swdb.problems import Problem
from swdb.schemas import SchemaSet
from swdb.store import Record
from swdb.vocab import load_all

D30 = {'minimum_unique_eligible_dx100_pairs': 20, 'minimum_tau': 0.6,
       'minimum_95_interval_lower_bound': 0.3,
       'gem5_best_in_estimate_top3_every_campaign': True}
STATISTICS = {'rank_measure': 'kendall_tau_b', 'ratio': 'baseline_seconds/candidate_seconds',
    'interval': 'connected_dependency_cluster_percentile_bootstrap', 'bootstrap_samples': 10000,
    'bootstrap_seed': 20261006, 'confidence_level': 0.95, 'quantiles': [0.025, 0.975],
    'quantile_interpolation': 'linear', 'minimum_supported_independent_components': 4,
    'minimum_defined_bootstrap_replicates': 9500,
    'dependency_links': ['shared_generator_seed', 'candidate_artifact', 'provider_trajectory_or_parent_lineage',
                         'reused_baseline_outcome', 'campaign_trajectory'],
    'unresolved_dependency': 'unsupported_interval',
    'top3_scope': 'every_campaign_and_workload_class',
    'top3_order': 'estimated_speedup_descending_then_artifact_sha256',
    'top3_requires_complete_ranking': True,
    'interval_assumption': 'exchangeable_supported_dependency_components_only'}
POLICY_KEYS = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'frozen_at',
    'estimator_sha256', 'provider_config_sha256', 'population', 'statistics', 'D30', 'structural_missing')
REPORT_KEYS = ('format', 'mode', 'campaign', 'basis', 'estimator_variant', 'policy', 'policy_sha256',
    'policy_snapshot', 'reported_at', 'summaries', 'summary_identities', 'counts', 'pairs',
    'blind_order', 'rank', 'top3', 'gate', 'recommendation', 'selection_policy', 'evidence_kind')


def kendall_tau_b(pairs):
    """Tie-aware rank statistic for finite mathematical pairs; no evidence admission.

    Definition: SciPy primary documentation, scipy.stats.kendalltau (tau-b).
    Undefined/constant rankings return None, rather than an agreement value.
    """
    pairs = list(pairs)
    if any(len(row) != 2 or any(type(value) not in (int, float) or not math.isfinite(value)
                               for value in row) for row in pairs):
        raise ValueError('rank pairs must contain two finite mathematical numbers')
    concordant = discordant = tied_x = tied_y = 0
    for i, (x1, y1) in enumerate(pairs):
        for x2, y2 in pairs[i + 1:]:
            dx, dy = (x1 > x2) - (x1 < x2), (y1 > y2) - (y1 < y2)
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tied_x += 1
            elif dy == 0:
                tied_y += 1
            elif dx == dy:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + tied_x) *
                            (concordant + discordant + tied_y))
    return (concordant - discordant) / denominator if denominator else None


def rank_statistics(samples):
    """Conditional mathematical ranking; samples never acquire application eligibility.

    Dependency keys are explicit facts. A shared key unions its samples, including
    transitive candidate/seed/trajectory links. Unknown closure cannot support CI.
    """
    samples = list(samples)
    if len(samples) > 256:
        raise ValueError('bounded mathematical rank interface supports at most 256 samples')
    pairs = [(row['estimated_speedup'], row['timing_speedup']) for row in samples]
    result = {'state': 'unsupported', 'tau_b': kendall_tau_b(pairs), 'interval_95': None,
              'dependency_component_count': 0, 'defined_bootstrap_replicates': 0,
              'reason': 'zero_eligible_numeric_application_pairs'}
    if not samples:
        return result
    if any(not row.get('dependencies_complete') or not row.get('dependency_keys') or
           any(not isinstance(key, str) or not key for key in row['dependency_keys']) for row in samples):
        result.update(dependency_component_count=None, reason='unresolved_dependency_closure')
        return result
    parent, owner = list(range(len(samples))), {}
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, row in enumerate(samples):
        for key in row['dependency_keys']:
            if key in owner:
                parent[root(i)] = root(owner[key])
            else:
                owner[key] = i
    groups = {}
    for i, pair in enumerate(pairs):
        groups.setdefault(root(i), []).append(pair)
    result['dependency_component_count'] = len(groups)
    if len(groups) < STATISTICS['minimum_supported_independent_components']:
        result['reason'] = 'too_few_supported_dependency_components'
    elif result['tau_b'] is None:
        result['reason'] = 'degenerate_ranking'
    else:
        rng = random.Random(STATISTICS['bootstrap_seed'])
        blocks, draws = list(groups.values()), []
        for _ in range(STATISTICS['bootstrap_samples']):
            draw = [pair for block in rng.choices(blocks, k=len(blocks)) for pair in block]
            tau = kendall_tau_b(draw)
            if tau is not None:
                draws.append(tau)
        result['defined_bootstrap_replicates'] = len(draws)
        if len(draws) < STATISTICS['minimum_defined_bootstrap_replicates']:
            result['reason'] = 'too_few_defined_bootstrap_replicates'
            return result
        draws.sort()
        limits = []
        for quantile in STATISTICS['quantiles']:
            position = (len(draws) - 1) * quantile
            lo, hi = math.floor(position), math.ceil(position)
            limits.append(draws[lo] + (draws[hi] - draws[lo]) * (position - lo))
        if limits[0] == limits[1]:
            result['reason'] = 'degenerate_bootstrap_distribution'
        else:
            result.update(state='supported', interval_95=limits, reason=None)
    return result


def identity(data):
    keys = POLICY_KEYS if data['kind'] == 'agreement_policy' else REPORT_KEYS
    return artifacts.digest({key: data[key] for key in keys})


def _fail(condition, message):
    if not condition:
        raise Failure(message)


def _research():
    _fail(workflow.CREATION_TAGS.get('mode') == 'extensa',
          'ADR 0013: agreement commands require explicit Extensa research mode and campaign')


def _new(kind, fields):
    data = workflow.record(kind, workflow.CREATION_TAGS['campaign'] + '.agreement',
        mode='extensa', campaign=workflow.CREATION_TAGS['campaign'],
        basis='simulated' if kind == 'agreement_report' else 'code_reading',
        estimator_variant='research', **fields)
    data['identity_sha256'] = identity(data)
    data['id'] += '.' + data['identity_sha256'][:16]
    return data


def freeze(args):
    _research()
    store = _require_valid(args.records)
    population = []
    for file in args.campaign_file:
        configuration = yamlio.load(file)
        problems = campaign.campaign_problems(configuration)
        _fail(not problems, 'campaign configuration invalid: ' + '; '.join(map(str, problems)))
        _fail(configuration['target'] == 'dx100_gem5', 'D30 population requires DX100 gem5 campaigns')
        _fail(configuration.get('paired_estimates', {}).get('enabled', True), 'paired estimates cannot be disabled')
        workloads = []
        for row in configuration['workload_classes']:
            workload = store.get(row['workload'], 'workload')
            _fail(workload is not None, 'population workload is missing: ' + row['workload'])
            definition = workload['definition']
            workloads.append({'class': row['class'], 'id': workload['id'],
                'identity_sha256': workload['identity_sha256'], 'record_sha256': artifacts.digest(workload),
                'canonical_sha256': definition['canonical_sha256'], 'sources': list(definition['sources']),
                'generation': {'family': definition['family'],
                    'generator': copy.deepcopy(definition.get('generator'))}})
        baselines = []
        for row in configuration['baselines']:
            source = store.get(row['candidate'], 'candidate')
            _fail(source is not None, 'population baseline is missing: ' + row['candidate'])
            baselines.append({'role': row['role'], 'candidate': source['id'],
                              'record_sha256': artifacts.digest(source),
                              'artifact_sha256': source['artifact']['sha256']})
        population.append({'campaign': configuration['id'], 'campaign_file_sha256': artifacts.file_hash(file),
                           'configuration': configuration, 'workloads': workloads, 'baselines': baselines})
    _fail(len({row['campaign'] for row in population}) == len(population), 'population has duplicate campaigns')
    _fail(workflow.CREATION_TAGS['campaign'] in {row['campaign'] for row in population},
          'Extensa campaign tag must anchor a campaign in the frozen population')
    from swdb.estimate_protocol import estimator_identity
    data = _new('agreement_policy', {'format': 'swdb.extensa-agreement-policy.v1', 'frozen_at': writer.now(),
        'estimator_sha256': estimator_identity(), 'provider_config_sha256': artifacts.file_hash(args.provider_config),
        'population': population, 'statistics': copy.deepcopy(STATISTICS), 'D30': copy.deepcopy(D30),
        'structural_missing': ['no_verified_canonical_graph_complete_call_mmio_numeric_adapter']})
    ids = {row['campaign'] for row in population}
    overlapping = [row.data for row in store.of_kind('agreement_policy')
                   if ids & {p['campaign'] for p in row.data['population']}]
    if overlapping:
        comparison_keys = [key for key in POLICY_KEYS if key != 'frozen_at']
        _fail(len(overlapping) == 1 and all(overlapping[0][key] == data[key] for key in comparison_keys),
              'frozen population already exists with different source/configuration; use fresh campaign identities')
        return copy.deepcopy(overlapping[0])  # Query the original freeze; never replace its timestamp.
    for row in population:
        cid = row['campaign']
        events = Path(row['configuration']['runs_root']) / 'extensa' / cid / 'pairing' / 'outcome-accesses.jsonl'
        _fail(not any(r.data['campaign'] == cid for r in store.of_kind('campaign_summary')) and
              not (events.is_file() and events.stat().st_size),
              'population already has outcome access; freeze before fresh campaign execution')
    return workflow.persist(args.records, data, create=True)


def _summary_checked(summary):
    vocabs, problems = load_all(paths.VOCAB)
    _fail(not problems, 'vocabulary is invalid')
    schemas = SchemaSet(paths.SCHEMAS, vocabs)
    errors = list(schemas.for_kind('campaign_summary').iter_errors(summary))
    _fail(not errors, 'campaign summary schema differs: ' + '; '.join(e.message for e in errors))
    class Context:
        pass
    ctx = Context()
    ctx.vocabs = vocabs
    problems = list(extensa_pairing.validate_summary(Record('embedded_summary', summary), ctx))
    _fail(not problems, 'paired estimate receipt differs: ' + '; '.join(str(p) for p in problems))


def _forecasts(ledger, artifact, workload):
    return [row for row in ledger.get('records', [])
        if row['timing_context']['subject']['artifact_sha256'] == artifact
        and row['timing_context']['input']['id'] == workload
        and not extensa_pairing.artifact_only(row)
        and not row['timing_context']['execution'].get('protocol_companion')
        and row['timing_context']['execution'].get('protocol_role', 'candidate') == 'candidate']


def _analyse(policy, summaries):
    planned = {row['campaign']: row for row in policy['population']}
    pairs, strata, seen, blind_problems = [], [], set(), []
    for summary in summaries:
        _summary_checked(summary)
        cid = summary['campaign']
        _fail(cid in planned, 'summary campaign is outside the frozen population')
        plan = planned[cid]
        _fail(summary['campaign_file']['sha256'] == plan['campaign_file_sha256'],
              'summary campaign configuration differs from prospective freeze')
        _fail(summary['target'] == 'dx100_gem5', 'agreement summary target is not DX100')
        _fail({row['role']: row['candidate'] for row in summary['baselines']} ==
              {row['role']: row['candidate'] for row in plan['baselines']},
              'summary baseline population differs from prospective freeze')
        for row in plan['baselines']:
            _fail(all(receipt['timing_context']['subject']['artifact_sha256'] == row['artifact_sha256']
                      for receipt in (summary.get('paired_estimates') or {}).get('records', [])
                      if receipt['timing_context']['subject']['id'] == row['candidate']),
                  'baseline forecast source artifact differs from prospective freeze')
        classes = {row['class']: row['id'] for row in plan['workloads']}
        _fail({row['class']: row['workload'] for row in summary['workload_classes']} == classes,
              'summary workload population differs from prospective freeze')
        ledger = summary.get('paired_estimates') or {}
        if not ledger.get('records') or not ledger.get('outcome_accesses'):
            blind_problems.append({'campaign': cid, 'reason': 'missing_preceding_estimate_receipts'})
        for row in ledger.get('records', []):
            _fail(row['estimator_sha256'] == policy['estimator_sha256'], 'forecast model differs from frozen policy')
            _fail(extensa_pairing._time(policy['frozen_at']) < extensa_pairing._time(row['estimated_at']),
                  'agreement policy did not precede campaign forecast/outcome access')
        for event in ledger.get('outcome_accesses', []):
            _fail(event.get('timing_contexts'), 'fresh outcome access lacks exact timing request contexts')
        accessed_requests = {extensa_pairing.request_identity(context)
            for event in ledger.get('outcome_accesses', []) for context in event['timing_contexts']}
        for iteration in summary['iterations']:
            for candidate in iteration['candidates']:
                for comparison in candidate.get('comparisons', []):
                    if comparison['baseline_role'] != plan['configuration']['base_source']:
                        continue
                    forecasts = _forecasts(ledger, candidate['artifact_sha256'], classes[candidate['class']])
                    exclusions = []
                    if summary['evidence_kind'] == 'contract_fixture' or any(
                            row['evidence_kind'] == 'contract_fixture' for row in forecasts):
                        exclusions.append('contract_fixture')
                    if not forecasts:
                        exclusions.append('missing_preceding_estimate_receipts')
                    if not forecasts or any(extensa_pairing.request_identity(row['timing_context'])
                                             not in accessed_requests for row in forecasts):
                        exclusions.append('missing_matching_outcome_request')
                        blind_problems.append({'campaign': cid, 'candidate': candidate['id'],
                                               'reason': 'missing_matching_outcome_request'})
                    if any(row['seconds'] is None for row in forecasts):
                        exclusions.append('unknown_forecast')
                    # Ticket16 currently admits no application numeric forecast.
                    exclusions.extend(['no_verified_complete_call_numeric_adapter', 'unverified_unique_pair_content'])
                    key = artifacts.digest({'campaign_configuration': plan['configuration'],
                        'input': next(row for row in plan['workloads'] if row['class'] == candidate['class']),
                        'candidate_artifact_sha256': candidate['artifact_sha256'],
                        'baseline_role': comparison['baseline_role'],
                        'forecast_contexts': [extensa_pairing.request_identity(r['timing_context']) for r in forecasts]})
                    if key in seen:
                        exclusions.append('repeated_pair_content')
                    seen.add(key)
                    pairs.append({'campaign': cid, 'class': candidate['class'], 'candidate': candidate['id'],
                        'candidate_artifact_sha256': candidate['artifact_sha256'], 'comparison': comparison['comparison'],
                        'baseline_evaluation': comparison['baseline_evaluation'], 'pair_identity_sha256': None,
                        'request_digest_sha256': key,
                        'forecast_ids': [row['id'] for row in forecasts], 'timing_speedup': comparison['ratio'],
                        'timing_basis': summary['evidence_basis'], 'timing_evidence_kind': summary['evidence_kind'],
                        'structural_missing': sorted({reason for row in forecasts for reason in row['structural_missing']}),
                        'estimated_speedup': None, 'relative_error': None, 'eligible': False,
                        'exclusions': exclusions})
        for row in summary['per_class']:
            strata.append({'campaign': cid, 'class': row['class'], 'best': row['best'],
                           'state': 'unsupported', 'estimate_top3': None,
                           'reason': 'complete_finite_application_prediction_ranking_unavailable'})
    absent = sorted(set(planned) - {summary['campaign'] for summary in summaries})
    return {'evidence_kind': ('unavailable' if not summaries else 'mixed_sources' if
                             len({s['evidence_kind'] for s in summaries}) > 1 else summaries[0]['evidence_kind']),
        'counts': {'observed_candidate_rows': len(pairs), 'unique_observed_pair_contents': None, 'unique_retained_request_digests': len(seen),
            'unique_eligible_dx100_pairs': 0, 'excluded_candidate_rows': len(pairs),
            'planned_campaigns': len(planned), 'observed_campaigns': len(summaries)},
        'pairs': pairs,
        'blind_order': {'state': 'unverified' if blind_problems or absent else 'verified',
                        'problems': blind_problems, 'missing_campaigns': absent,
                        'scope': 'receipt_order_only; unknown forecasts never establish numeric agreement'},
        'rank': rank_statistics([]),
        'top3': {'state': 'unsupported', 'strata': strata},
        'gate': {'state': 'unsupported', 'D30': copy.deepcopy(D30),
                 'reason': 'minimum20_eligible_pairs_and_supported_rank_interval_top3_not_demonstrated'},
        'recommendation': 'do_not_switch_to_flow_b', 'selection_policy': 'unchanged_timing_only'}


def report(args):
    _research()
    store = _require_valid(args.records)
    policy = store.get(args.policy, 'agreement_policy')
    _fail(policy is not None, 'agreement policy does not exist')
    from swdb.estimate_protocol import estimator_identity
    _fail(policy['estimator_sha256'] == estimator_identity(), 'source/model implementation changed after policy freeze')
    summaries = []
    for folder in args.campaign_records:
        source = _require_valid(folder)
        summaries.extend(copy.deepcopy(row.data) for row in source.of_kind('campaign_summary')
                         if row.data['campaign'] in {p['campaign'] for p in policy['population']})
    _fail(len({s['campaign'] for s in summaries}) == len(summaries), 'duplicate campaign summaries supplied')
    data = _new('agreement_report', {'format': 'swdb.extensa-agreement-report.v1',
        'policy': policy['id'], 'policy_sha256': policy['identity_sha256'], 'policy_snapshot': copy.deepcopy(policy),
        'reported_at': writer.now(), 'summaries': summaries,
        'summary_identities': {s['id']: artifacts.digest(s) for s in summaries}, **_analyse(policy, summaries)})
    return workflow.persist(args.records, data, create=True)


def validate_record(record, ctx):
    data = record.data
    if identity(data) != data['identity_sha256'] or not data['id'].endswith('.' + identity(data)[:16]):
        yield Problem(record.rel, 'identity_sha256', 'agreement immutable payload/hash differs')
    if data['kind'] == 'agreement_policy':
        if data['D30'] != D30 or data['statistics'] != STATISTICS:
            yield Problem(record.rel, 'D30', 'prospective D30/statistical policy differs from version1 rule')
        own_campaigns = {row['campaign'] for row in data['population']}
        if len(own_campaigns) != len(data['population']) or data['campaign'] not in own_campaigns:
            yield Problem(record.rel, 'population', 'population campaign identities/anchor differ')
        for member in data['population']:
            configuration = member['configuration']
            problems = campaign.campaign_problems(configuration)
            if problems or configuration.get('id') != member['campaign'] or configuration.get('target') != 'dx100_gem5':
                yield Problem(record.rel, 'population', 'frozen campaign configuration differs or is invalid')
                continue  # Malformed embedded configurations are data errors, not Python exceptions.
            if ({row['role']: row['candidate'] for row in member['baselines']} !=
                    {row['role']: row['candidate'] for row in configuration['baselines']}):
                yield Problem(record.rel, 'population', 'frozen baseline configuration differs')
            for baseline in member['baselines']:
                source = ctx.passed(baseline['candidate'], 'candidate')
                if (source is None or artifacts.digest(source) != baseline['record_sha256'] or
                        source['artifact']['sha256'] != baseline['artifact_sha256']):
                    yield Problem(record.rel, 'population', 'frozen baseline artifact/metadata differs or is unavailable')
            for workload in member['workloads']:
                source = ctx.passed(workload['id'], 'workload')
                if source is None or artifacts.digest(source) != workload['record_sha256']:
                    yield Problem(record.rel, 'population', 'frozen workload metadata/hash differs or is unavailable')
                    continue
                definition = source['definition']
                if (workload['identity_sha256'] != source['identity_sha256'] or
                    workload['canonical_sha256'] != definition['canonical_sha256'] or
                    workload['sources'] != definition['sources'] or
                    workload['generation'] != {'family': definition['family'], 'generator': definition.get('generator')}):
                    yield Problem(record.rel, 'population', 'frozen graph/source/generator dependency differs')
        for other in ctx.store.of_kind('agreement_policy'):
            source = ctx.passed(other.id, 'agreement_policy')
            if source is not None and other.id != record.id and own_campaigns & {p['campaign'] for p in source['population']}:
                yield Problem(record.rel, 'population', 'campaign belongs to more than one immutable frozen population')
        try:
            extensa_pairing._time(data['frozen_at'])
        except (TypeError, ValueError):
            yield Problem(record.rel, 'frozen_at', 'policy timestamp must declare UTC')
        return
    policy = data['policy_snapshot']
    source_policy = ctx.passed(data['policy'], 'agreement_policy')
    if source_policy is None or source_policy['identity_sha256'] != data['policy_sha256']:
        yield Problem(record.rel, 'policy', 'frozen policy dependency differs or is unavailable')
    try:
        if extensa_pairing._time(data['reported_at']) <= extensa_pairing._time(policy['frozen_at']):
            yield Problem(record.rel, 'reported_at', 'report must follow its prospective policy freeze')
    except (TypeError, ValueError):
        yield Problem(record.rel, 'reported_at', 'report timestamp must declare UTC')
    if identity(policy) != data['policy_sha256'] or policy['id'] != data['policy']:
        yield Problem(record.rel, 'policy_sha256', 'frozen policy snapshot/hash differs')
        return
    if data['summary_identities'] != {s['id']: artifacts.digest(s) for s in data['summaries']}:
        yield Problem(record.rel, 'summary_identities', 'summary snapshot/hash differs')
    try:
        expected = _analyse(policy, data['summaries'])
        if any(data[key] != value for key, value in expected.items()):
            yield Problem(record.rel, 'gate', 'report differs from frozen admission and D30 rule')
    except (Failure, KeyError, TypeError, ValueError) as exc:
        yield Problem(record.rel, 'summaries', str(exc))


def register_cli(commands):
    for name, handler, help_text in (
        ('agreement-freeze', freeze, 'freeze the prospective Extensa population and D30 analysis policy'),
        ('agreement-report', report, 'report Extensa blind agreement, exclusions and the unchanged D30 gate')):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument('--records', type=Path, default=paths.RECORDS)
        sub.add_argument('--format', choices=['json', 'yaml'], default='yaml')
        if name == 'agreement-freeze':
            sub.add_argument('--campaign-file', type=Path, action='append', required=True)
            sub.add_argument('--provider-config', type=Path, required=True)
        else:
            sub.add_argument('--policy', required=True)
            sub.add_argument('--campaign-records', type=Path, action='append', required=True)
        sub.set_defaults(extensa_handler=handler)
