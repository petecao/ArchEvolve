"""Public mathematical API fixtures; not application agreement. Created: 2026-10-06 ET."""
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
    perfect = [{**row, 'timing_speedup': row['estimated_speedup']} for row in samples]
    refused = rank_statistics(perfect)
    assert refused['interval_95'] is None and refused['state'] == 'unsupported'
    assert refused['reason'] == 'degenerate_bootstrap_distribution'
