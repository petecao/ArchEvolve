"""Paired calibration admission tests; durations are fixtures. Date: 2026-09-26 ET."""

import pytest

from scripts.bfs_freeze_pilot import summary
from scripts.bfs_paired_calibration import negative_control


POLICY = {'minimum_speedup': 1.05, 'confidence': .95, 'bootstrap_resamples': 2000,
          'bootstrap_seed': 20260925, 'maximum_relative_spread': .10}
SAMPLING = {'analysis': 'paired_repetition_block_bootstrap.v1'}


@pytest.mark.parametrize('factor', [.5, 1, 2])
def test_either_direction_of_unchanged_code_gain_vetoes_admission(factor):
    samples = {role: [summary(source, [scale * (1 + .001 * repeat) for repeat in range(10)])
                     for source in (0, 1234, 7777)]
               for role, scale in (('baseline', 1), ('candidate', factor))}
    result = negative_control(samples, POLICY, SAMPLING)
    assert result['gain_claim'] is False
    assert bool(result['unmet_gates']) == (factor != 1)
    assert {row['direction']: row['numerical_gain_leg'] for row in result['directions']} == {
        'baseline_over_candidate': factor < 1, 'candidate_over_baseline': factor > 1}
    assert all(row['statistics']['confidence_interval']['method'] == SAMPLING['analysis']
               for row in result['directions'])


def test_no_numerical_gain_does_not_excuse_high_spread():
    samples = {role: [summary(source, list(range(1, 11))) for source in (0, 1234, 7777)]
               for role in ('baseline', 'candidate')}
    result = negative_control(samples, POLICY, SAMPLING)
    assert not any(row['numerical_gain_leg'] for row in result['directions'])
    assert result['unmet_gates'] == ['paired source timing spread exceeds the prospective fixed ceiling']
    assert result['gain_claim'] is False


def test_shared_blocks_preserve_common_drift_across_roles():
    # Large shared drift cancels in both ratio directions, but still fails the
    # separately retained spread criterion. No fixture is empirical calibration.
    durations = [1, 2, 4, 8, 16, 1, 2, 4, 8, 16]
    samples = {role: [summary(source, durations) for source in (0, 1234, 7777)]
               for role in ('baseline', 'candidate')}
    result = negative_control(samples, POLICY, SAMPLING)
    for row in result['directions']:
        assert row['statistics']['confidence_interval']['lower'] == 1
        assert row['statistics']['confidence_interval']['upper'] == 1
    assert result['unmet_gates'] and not result['gain_claim']
