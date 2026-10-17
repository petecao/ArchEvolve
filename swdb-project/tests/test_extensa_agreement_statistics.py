"""Public mathematical API fixtures; not application agreement. Created: 2026-10-06 ET.
Updated: 2026-10-09 ET (review F2/F3: D30 gate, top-3 cut, defined degenerate interval)."""
import pytest


def test_tau_b_uses_known_ties_and_refuses_degenerate_ranking():
    from swdb.extensa_agreement import kendall_tau_b
    assert kendall_tau_b([(1, 1), (2, 2), (3, 3)]) == 1.0
    assert kendall_tau_b([(1, 3), (2, 2), (3, 1)]) == -1.0
    # Worked tied-rank example retained in the SciPy primary documentation.
    assert kendall_tau_b(list(zip([12, 2, 1, 12, 2], [1, 4, 7, 1, 0]))) == pytest.approx(-0.47140452079103173)
    assert kendall_tau_b([(1, 1), (1, 2), (1, 3)]) is None


def test_shared_seed_connects_four_campaigns_and_refuses_an_independence_interval():
    from swdb.extensa_agreement import rank_statistics
    samples = [{'estimated_speedup': i + 1, 'timing_speedup': i + 1,
                'dependency_keys': ['generator_seed.27491095', 'fixture.campaign.' + str(i % 4)],
                'dependencies_complete': True} for i in range(20)]
    result = rank_statistics(samples)
    assert result['tau_b'] == 1.0
    assert result['dependency_component_count'] == 1
    assert result['interval_95'] is None and result['state'] == 'unsupported'
    assert result['reason'] == 'too_few_supported_dependency_components'


def test_independent_math_components_have_reproducible_percentiles_but_degeneracy_is_unsupported():
    from swdb.extensa_agreement import rank_statistics
    timing = [1, 2, 3, 4, 5, 10, 9, 8, 7, 6, 11, 12, 13, 14, 15, 20, 19, 18, 17, 16]
    samples = [{'estimated_speedup': i + 1, 'timing_speedup': timing[i],
                'dependency_keys': ['fixture.conditional_component.' + str(i // 5)],
                'dependencies_complete': True} for i in range(20)]
    result = rank_statistics(samples)
    assert result['state'] == 'supported'
    assert result['tau_b'] == pytest.approx(0.7894736842105263)
    assert result['dependency_component_count'] == 4
    assert result['defined_bootstrap_replicates'] == 10000
    assert -1 <= result['interval_95'][0] < result['interval_95'][1] <= 1
    assert rank_statistics(samples) == result
    # 2026-10-09 ET (review F3): perfect agreement has the defined interval [1, 1]; it was
    # previously refused as degenerate while weaker agreement was supported.
    perfect = [{**row, 'timing_speedup': row['estimated_speedup']} for row in samples]
    accepted = rank_statistics(perfect)
    assert accepted['state'] == 'supported' and accepted['reason'] is None
    assert accepted['tau_b'] == 1.0 and accepted['interval_95'] == [1.0, 1.0]


# 2026-10-09 ET (review F2): D30 applied literally. Hand-set fixture numbers, not evidence.

def _rank(tau, lower):
    return {'state': 'supported', 'tau_b': tau, 'interval_95': [lower, 0.95], 'reason': None}


def _stratum(cid, rank, total=5):
    return {'campaign': cid, 'class': 'kronecker', 'state': 'supported', 'in_top3': rank <= 3,
            'best_rank': rank, 'ranked_candidates': total}


@pytest.mark.parametrize('count, tau, lower, best_rank, state, failed', [
    (20, 0.6, 0.3, 3, 'met', []),
    (19, 0.6, 0.3, 3, 'not_met', ['minimum_unique_eligible_dx100_pairs']),
    (20, 0.5999999, 0.3, 3, 'not_met', ['minimum_tau']),
    (20, 0.6, 0.2999999, 3, 'not_met', ['minimum_95_interval_lower_bound']),
    (20, 0.6, 0.3, 4, 'not_met', ['gem5_best_in_estimate_top3_every_campaign']),
])
def test_d30_gate_uses_inclusive_thresholds_exactly_as_written(count, tau, lower, best_rank, state, failed):
    from swdb.extensa_agreement import d30_gate
    strata = [_stratum('extensa-gem5-bfs-20261004-a1', 1), _stratum('extensa-gem5-bfs-20261004-a2', best_rank)]
    gate = d30_gate(count, _rank(tau, lower), strata, set())
    assert gate['state'] == state and gate['failed'] == failed
    assert gate['D30']['minimum_unique_eligible_dx100_pairs'] == 20


def test_d30_gate_is_unsupported_without_a_supported_interval_or_a_planned_campaign():
    from swdb.extensa_agreement import d30_gate, rank_statistics
    strata = [_stratum('extensa-gem5-bfs-20261004-a1', 1)]
    assert d30_gate(25, rank_statistics([]), strata, set())['state'] == 'unsupported'
    missing = d30_gate(25, _rank(0.9, 0.7), strata, {'extensa-gem5-bfs-20261004-a2'})
    assert missing['state'] == 'unsupported' and missing['missing_campaigns'] == ['extensa-gem5-bfs-20261004-a2']
    unranked = d30_gate(25, _rank(0.9, 0.7), [{**strata[0], 'state': 'unsupported', 'in_top3': None}], set())
    assert unranked['state'] == 'unsupported'


def _row(name, estimate, eligible=True):
    return {'candidate': name, 'candidate_artifact_sha256': name[-1] * 64, 'estimated_speedup': estimate,
            'eligible': eligible}


def test_top3_cut_counts_rank_three_in_and_rank_four_out():
    from swdb.extensa_agreement import top3_stratum
    rows = [_row('cand-a', 2.0), _row('cand-b', 1.8), _row('cand-c', 1.5), _row('cand-d', 1.1)]
    third = top3_stratum(rows, 'cand-c')
    assert third['state'] == 'supported' and third['best_rank'] == 3 and third['in_top3'] is True
    fourth = top3_stratum(rows, 'cand-d')
    assert fourth['best_rank'] == 4 and fourth['in_top3'] is False and fourth['trivial_cut'] is False
    assert fourth['estimate_top3'] == ['a' * 64, 'b' * 64, 'c' * 64]


def test_top3_ties_at_the_cut_follow_the_frozen_hash_order_and_are_flagged():
    from swdb.extensa_agreement import top3_stratum
    rows = [_row('cand-a', 2.0), _row('cand-b', 1.8), _row('cand-d', 1.5), _row('cand-c', 1.5)]
    tied = top3_stratum(rows, 'cand-d')
    assert tied['tied_at_cut'] is True and tied['best_rank'] == 4 and tied['in_top3'] is False
    assert top3_stratum(rows, 'cand-c')['best_rank'] == 3


def test_top3_with_fewer_than_three_candidates_passes_trivially_and_says_so():
    from swdb.extensa_agreement import top3_stratum
    result = top3_stratum([_row('cand-a', 0.5), _row('cand-b', 1.5)], 'cand-a')
    assert result['state'] == 'supported' and result['in_top3'] is True and result['trivial_cut'] is True
    assert result['best_rank'] == 2 and result['ranked_candidates'] == 2


def test_top3_needs_a_complete_eligible_ranking_and_a_gem5_best():
    from swdb.extensa_agreement import top3_stratum
    rows = [_row('cand-a', 2.0), _row('cand-b', None, eligible=False)]
    assert top3_stratum(rows, 'cand-a')['reason'] == 'complete_finite_application_prediction_ranking_unavailable'
    assert top3_stratum(rows, None)['reason'] == 'no_gem5_best'
    assert top3_stratum(rows[:1], 'cand-z')['reason'] == 'gem5_best_has_no_base_source_pair'
