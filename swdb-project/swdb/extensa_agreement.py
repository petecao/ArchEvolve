"""Prospective Extensa agreement policy and retained report. Created: 2026-10-06 ET.

No application numeric adapter is registered by ticket16. Unknown and fixture
forecasts therefore cannot demonstrate D30, irrespective of campaign duration.

Updated: 2026-10-09 23:15 ET (ticket 16/17 review F2/F3/F6/F8): report v2 matches
baseline and candidate forecasts, derives the estimated speedup, sends eligible
pairs to the rank statistics and applies D30 literally (`>=` on every threshold,
top 3 per campaign stratum). Version 1 reports keep their original analysis.
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
REPORT_V1 = 'swdb.extensa-agreement-report.v1'
REPORT_V2 = 'swdb.extensa-agreement-report.v2'
NO_SWITCH = 'do_not_switch_to_flow_b'
# D30 met is a reading for Yan-Ru, never an automatic switch (story 71).
D30_MET = 'd30_met_human_decides'
#: D29: a forecast carrying this label never enters agreement statistics.
BEYOND = 'beyond_paired_range'


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
        # 2026-10-09 ET (review F3): a defined tau whose replicates all agree has the
        # interval [v, v]; refusing it reported perfect agreement as unsupported.
        result.update(state='supported', interval_95=limits, reason=None)
    return result


def top3_stratum(rows, best):
    """D30's top-3 condition for one campaign/workload-class stratum.

    `rows` are the stratum's timed candidate pairs; `best` is gem5's selected best
    candidate ID (the summary's per-class best). The frozen v1 policy orders by
    estimated speedup descending, then artifact SHA-256, and needs a complete
    ranking: every ranked artifact must be an eligible numeric pair. Three or fewer
    ranked artifacts pass trivially; `trivial_cut` says so. `tied_at_cut` says the
    hash order decided a tie between ranks 3 and 4.
    """
    ranked = {}
    for row in rows:
        ranked.setdefault(row['candidate_artifact_sha256'], row)
    result = {'best': best, 'state': 'unsupported', 'estimate_top3': None, 'best_rank': None,
              'in_top3': None, 'ranked_candidates': len(ranked), 'trivial_cut': None,
              'tied_at_cut': None, 'reason': None}
    best_row = next((row for row in rows if row['candidate'] == best), None) if best else None
    if best is None:
        result['reason'] = 'no_gem5_best'
    elif best_row is None:
        result['reason'] = 'gem5_best_has_no_base_source_pair'
    elif any(not row['eligible'] or row['estimated_speedup'] is None for row in ranked.values()):
        result['reason'] = 'complete_finite_application_prediction_ranking_unavailable'
    else:
        order = sorted(ranked.values(), key=lambda row: (-row['estimated_speedup'],
                                                         row['candidate_artifact_sha256']))
        shas = [row['candidate_artifact_sha256'] for row in order]
        rank = shas.index(best_row['candidate_artifact_sha256']) + 1
        result.update(state='supported', estimate_top3=shas[:3], best_rank=rank, in_top3=rank <= 3,
                      trivial_cut=len(order) <= 3,
                      tied_at_cut=len(order) > 3 and order[2]['estimated_speedup'] == order[3]['estimated_speedup'])
    return result


def d30_gate(unique_eligible_pairs, rank, strata, missing_campaigns):
    """Apply D30 as written: every threshold is `>=`; nothing is relaxed or rounded.

    `met` needs all four conditions. `not_met` means every statistic was computed
    and a threshold failed. `unsupported` means a required statistic, stratum or
    planned campaign is unavailable, so the rule cannot be met.
    """
    observed = {row['campaign'] for row in strata}
    supported = (rank.get('state') == 'supported' and rank.get('tau_b') is not None
                 and rank.get('interval_95') is not None and bool(strata) and not missing_campaigns
                 and all(row['state'] == 'supported' for row in strata))
    checks = {
        'minimum_unique_eligible_dx100_pairs': unique_eligible_pairs >= D30['minimum_unique_eligible_dx100_pairs'],
        'minimum_tau': supported and rank['tau_b'] >= D30['minimum_tau'],
        'minimum_95_interval_lower_bound': supported and rank['interval_95'][0] >= D30['minimum_95_interval_lower_bound'],
        'gem5_best_in_estimate_top3_every_campaign': supported and bool(observed) and all(
            row['in_top3'] for row in strata)}
    failed = [name for name, passed in checks.items() if not passed]
    state = 'met' if not failed else 'not_met' if supported else 'unsupported'
    return {'state': state, 'D30': copy.deepcopy(D30), 'checks': checks, 'failed': failed,
            'missing_campaigns': sorted(missing_campaigns),
            'reason': None if state == 'met' else 'unchanged_D30_not_met: ' + ', '.join(failed)}


def evaluate_d30(pairs, bests, planned):
    """Rank statistics, top-3 strata and the D30 gate from report pair rows.

    `bests` maps (campaign, class) to gem5's selected best candidate ID (or None);
    `planned` is the frozen population's campaign IDs. Only rows marked eligible
    enter the statistics; their D29 and blindness exclusions were applied earlier.
    """
    eligible = [row for row in pairs if row['eligible']]
    unique = len({row['pair_identity_sha256'] for row in eligible})
    samples = [{'estimated_speedup': row['estimated_speedup'], 'timing_speedup': row['timing_speedup'],
                'dependency_keys': row['dependency_keys'], 'dependencies_complete': row['dependencies_complete']}
               for row in eligible]
    if len(samples) > 256:
        rank = rank_statistics([])
        rank.update(reason='sample_count_exceeds_bounded_interface', dependency_component_count=None)
    else:
        rank = rank_statistics(samples)
    strata = []
    for (cid, cls), best in sorted(bests.items()):
        rows = [row for row in pairs if row['campaign'] == cid and row['class'] == cls]
        strata.append({'campaign': cid, 'class': cls, **top3_stratum(rows, best)})
    missing = set(planned) - {cid for cid, _ in bests}
    gate = d30_gate(unique, rank, strata, missing)
    return {'unique_eligible_dx100_pairs': unique, 'rank': rank,
            'top3': {'state': 'supported' if strata and all(r['state'] == 'supported' for r in strata)
                     else 'unsupported', 'strata': strata},
            'gate': gate, 'recommendation': D30_MET if gate['state'] == 'met' else NO_SWITCH}


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


def _side(ledger, artifact, workload, role):
    """Exact timed forecasts for one artifact/input/protocol side; artifact-only and
    companion receipts never count. A context without a protocol role (the fixture
    adapter) matches either side."""
    return [row for row in ledger.get('records', [])
        if row['timing_context']['subject']['artifact_sha256'] == artifact
        and row['timing_context']['input']['id'] == workload
        and not extensa_pairing.artifact_only(row)
        and not row['timing_context']['execution'].get('protocol_companion')
        and row['timing_context']['execution'].get('protocol_role', role) == role]


def _seconds(rows, prefix, accessed, exclusions):
    """One side's forecast seconds, or None with the reason appended."""
    if not rows:
        exclusions.append(prefix + 'missing_preceding_estimate_receipts')
    if not rows or any(extensa_pairing.request_identity(row['timing_context']) not in accessed for row in rows):
        exclusions.append(prefix + 'missing_matching_outcome_request')
    if any(row['seconds'] is None for row in rows):
        exclusions.append(prefix + 'unknown_forecast')
    values = {row['seconds'] for row in rows if row['seconds'] is not None}
    if len(values) > 1:
        exclusions.append(prefix + 'ambiguous_forecast')
    if any(row['timing_context'].get('prior_outcome_exposure') for row in rows):
        exclusions.append(prefix + 'prior_outcome_exposure')
    if any(row.get('paired_range') == BEYOND for row in rows) and BEYOND not in exclusions:
        exclusions.append(BEYOND)    # D29: never counted in agreement statistics
    if not rows or any(row['seconds'] is None for row in rows) or len(values) != 1:
        return None
    value = values.pop()
    if not value > 0:
        exclusions.append(prefix + 'nonpositive_forecast')
        return None
    return value


def _analyse_v2(policy, summaries):
    """Report v2 (2026-10-09 ET): numeric matching, eligibility and the literal D30 gate."""
    planned = {row['campaign']: row for row in policy['population']}
    pairs, bests, seen, contents, blind_problems = [], {}, set(), set(), []
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
        baselines = {row['role']: row for row in plan['baselines']}
        ledger = summary.get('paired_estimates') or {}
        if not ledger.get('records') or not ledger.get('outcome_accesses'):
            blind_problems.append({'campaign': cid, 'reason': 'missing_preceding_estimate_receipts'})
        for row in ledger.get('records', []):
            _fail(row['estimator_sha256'] == policy['estimator_sha256'], 'forecast model differs from frozen policy')
            _fail(extensa_pairing._time(policy['frozen_at']) < extensa_pairing._time(row['estimated_at']),
                  'agreement policy did not precede campaign forecast/outcome access')
        for event in ledger.get('outcome_accesses', []):
            _fail(event.get('timing_contexts'), 'fresh outcome access lacks exact timing request contexts')
        accessed = {extensa_pairing.request_identity(context)
                    for event in ledger.get('outcome_accesses', []) for context in event['timing_contexts']}
        checked = 0
        for iteration in summary['iterations']:
            for candidate in iteration['candidates']:
                for comparison in candidate.get('comparisons', []):
                    if comparison['baseline_role'] != plan['configuration']['base_source']:
                        continue
                    checked += 1
                    workload = next(row for row in plan['workloads'] if row['class'] == candidate['class'])
                    baseline = baselines[comparison['baseline_role']]
                    forecasts = _side(ledger, candidate['artifact_sha256'], workload['id'], 'candidate')
                    reference = _side(ledger, baseline['artifact_sha256'], workload['id'], 'baseline')
                    exclusions = []
                    if summary['evidence_kind'] == 'contract_fixture' or any(
                            row['evidence_kind'] == 'contract_fixture' for row in forecasts + reference):
                        exclusions.append('contract_fixture')
                    candidate_seconds = _seconds(forecasts, '', accessed, exclusions)
                    baseline_seconds = _seconds(reference, 'baseline_', accessed, exclusions)
                    for reason in ('missing_matching_outcome_request', 'baseline_missing_matching_outcome_request'):
                        if reason in exclusions:
                            blind_problems.append({'campaign': cid, 'candidate': candidate['id'], 'reason': reason})
                    if any(row['eligible_for_agreement'] is not True for row in forecasts + reference):
                        exclusions.append('no_verified_complete_call_numeric_adapter')
                    timing = comparison['ratio']
                    if type(timing) not in (int, float) or not math.isfinite(timing) or timing <= 0:
                        exclusions.append('missing_timing_ratio')
                        timing = None
                    key = artifacts.digest({'campaign_configuration': plan['configuration'], 'input': workload,
                        'candidate_artifact_sha256': candidate['artifact_sha256'],
                        'baseline_role': comparison['baseline_role'],
                        'forecast_contexts': [extensa_pairing.request_identity(r['timing_context']) for r in forecasts]})
                    # Campaign-independent content: the same artifact pair on the same graph counts once.
                    identity = artifacts.digest({'input_identity_sha256': workload['identity_sha256'],
                        'input_canonical_sha256': workload['canonical_sha256'],
                        'candidate_artifact_sha256': candidate['artifact_sha256'],
                        'baseline_artifact_sha256': baseline['artifact_sha256'],
                        'baseline_role': comparison['baseline_role']})
                    if identity in contents:
                        exclusions.append('repeated_pair_content')
                    seen.add(key)
                    contents.add(identity)
                    estimated = (baseline_seconds / candidate_seconds
                                 if baseline_seconds is not None and candidate_seconds is not None else None)
                    # Dependency facts come from the frozen population only. A generator without a
                    # recorded seed parameter (a handwritten graph) has no seed link.
                    generator = workload['generation']['generator']
                    seed = ((generator.get('parameters') or {}).get('seed', generator.get('seed'))
                            if isinstance(generator, dict) else None)
                    keys = ['campaign_trajectory.' + cid, 'provider_trajectory.' + cid,
                            'candidate_artifact.' + candidate['artifact_sha256']]
                    if isinstance(comparison.get('baseline_evaluation'), str):
                        keys.append('reused_baseline_outcome.' + comparison['baseline_evaluation'])
                    if seed is not None:
                        keys.append('generator_seed.' + str(seed))
                    pairs.append({'campaign': cid, 'class': candidate['class'], 'candidate': candidate['id'],
                        'candidate_artifact_sha256': candidate['artifact_sha256'], 'comparison': comparison['comparison'],
                        'baseline_evaluation': comparison['baseline_evaluation'], 'pair_identity_sha256': identity,
                        'request_digest_sha256': key, 'forecast_ids': [row['id'] for row in forecasts],
                        'baseline_forecast_ids': [row['id'] for row in reference],
                        'estimated_candidate_seconds': candidate_seconds, 'estimated_baseline_seconds': baseline_seconds,
                        'timing_speedup': timing, 'timing_basis': summary['evidence_basis'],
                        'timing_evidence_kind': summary['evidence_kind'],
                        'structural_missing': sorted({reason for row in forecasts + reference
                                                      for reason in row['structural_missing']}),
                        'estimated_speedup': estimated,
                        'relative_error': estimated / timing - 1 if estimated is not None and timing else None,
                        'dependency_keys': keys,
                        'dependencies_complete': generator is None or isinstance(generator, dict),
                        'eligible': not exclusions, 'exclusions': exclusions})
        if not checked:
            # Review F8: zero checked comparisons is no evidence of blind order.
            blind_problems.append({'campaign': cid, 'reason': 'no_timed_candidate_comparisons'})
        for row in summary['per_class']:
            bests[(cid, row['class'])] = row['best']
    absent = sorted(set(planned) - {summary['campaign'] for summary in summaries})
    result = evaluate_d30(pairs, bests, planned)
    eligible = sum(1 for row in pairs if row['eligible'])
    return {'evidence_kind': ('unavailable' if not summaries else 'mixed_sources' if
                             len({s['evidence_kind'] for s in summaries}) > 1 else summaries[0]['evidence_kind']),
        'counts': {'observed_candidate_rows': len(pairs), 'unique_observed_pair_contents': len(contents),
            'unique_retained_request_digests': len(seen),
            'unique_eligible_dx100_pairs': result['unique_eligible_dx100_pairs'],
            'excluded_candidate_rows': len(pairs) - eligible,
            'planned_campaigns': len(planned), 'observed_campaigns': len(summaries)},
        'pairs': pairs,
        'blind_order': {'state': 'unverified' if blind_problems or absent else 'verified',
                        'problems': blind_problems, 'missing_campaigns': absent,
                        'scope': 'receipt_order_only; unknown forecasts never establish numeric agreement'},
        'rank': result['rank'], 'top3': result['top3'], 'gate': result['gate'],
        'recommendation': result['recommendation'], 'selection_policy': 'unchanged_timing_only'}


ANALYSES = {REPORT_V1: _analyse, REPORT_V2: _analyse_v2}


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
    data = _new('agreement_report', {'format': REPORT_V2,
        'policy': policy['id'], 'policy_sha256': policy['identity_sha256'], 'policy_snapshot': copy.deepcopy(policy),
        'reported_at': writer.now(), 'summaries': summaries,
        'summary_identities': {s['id']: artifacts.digest(s) for s in summaries}, **_analyse_v2(policy, summaries)})
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
        # Each report is checked by the analysis of its own format; v1 stays unchanged.
        analyse = ANALYSES.get(data['format'])
        _fail(analyse is not None, 'unknown agreement report format')
        expected = analyse(policy, data['summaries'])
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
