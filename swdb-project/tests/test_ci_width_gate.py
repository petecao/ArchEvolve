"""CI-width speed rule (ticket 66, decided by Yan-Ru 2026-10-04). Created 2026-10-04 ET.

The circular block bootstrap over repetitions, the relative CI-width gate for the A/A pilot and
for candidate blocks, and the old range rule kept for every protocol without the gate. The
two-regime data are synthetic, never evidence.
"""

import math
import random

import pytest

from swdb import bfs_protocol as protocol
from swdb.bfs_protocol import ANALYSIS_CIRCULAR_BLOCK, circular_block_indices, decide
from swdb.campaign import (CI_WIDTH_RULE, RANGE_RULE, campaign_problems, pilot_passes, protocol_settings,
                           relative_ci_width, speed_verdict)
from test_extensa_campaign import (CID, campaign_file, campaign_store, fixture_file, log, provider,  # noqa: F401
                                   records_of, run, team, team_seed)
from test_bfs_protocol import protocol_seed  # noqa: F401

POLICY = {"bootstrap_seed": 20260925, "bootstrap_resamples": 2000}
OLD = {"analysis": "paired_repetition_block_bootstrap.v1"}
NEW = {"analysis": ANALYSIS_CIRCULAR_BLOCK, "block_length": 4}
BASE = {0: 0.70, 1: 0.74, 2: 1.10}          # seconds per source position (fork-like)


def _noise(rng, sigma):
    return math.exp(rng.gauss(0.0, sigma))


def _blocks(baseline_regime, candidate_regime, *, repetitions=20, sigma=0.006, seed=7):
    """{position: [times]} for both sides; regimes are multiplicative factors per repetition."""
    rng = random.Random(seed)
    baseline, candidate = {}, {}
    for position, base in BASE.items():
        baseline[position] = [base * baseline_regime(r) * _noise(rng, sigma) for r in range(repetitions)]
        candidate[position] = [base * candidate_regime(r) * _noise(rng, sigma) for r in range(repetitions)]
    return baseline, candidate


def _width(metrics):
    interval = metrics["confidence_interval"]
    return (interval["upper"] - interval["lower"]) / metrics["roi_speedup"]


# --- the resampling ----------------------------------------------------------------------------

def test_circular_blocks_are_consecutive_wrapping_runs_of_the_block_length():
    rng = random.Random(1)
    for count, length in ((20, 4), (10, 3), (7, 2)):
        for _ in range(200):
            indices = circular_block_indices(rng, count, length)
            assert len(indices) == count and all(0 <= i < count for i in indices)
            for start in range(0, count, length):
                run_ = indices[start:start + length]
                assert all((b - a) % count == 1 for a, b in zip(run_, run_[1:]))


def test_old_analysis_output_is_unchanged_and_the_new_one_adds_its_width():
    baseline, candidate = _blocks(lambda r: 1.0, lambda r: 1.0, repetitions=10)
    old = protocol._statistics(baseline, candidate, POLICY, OLD)
    assert old["confidence_interval"]["method"] == "paired_repetition_block_bootstrap.v1"
    assert set(old["confidence_interval"]) == {"confidence", "lower", "upper", "method", "resamples"}
    new = protocol._statistics(baseline, candidate, POLICY, {**NEW, "block_length": 2})
    assert new["roi_speedup"] == old["roi_speedup"]           # same point estimate (the spec's statistic)
    assert new["confidence_interval"]["method"] == ANALYSIS_CIRCULAR_BLOCK
    assert new["confidence_interval"]["block_length"] == 2
    assert new["confidence_interval"]["relative_width"] == pytest.approx(_width(new), rel=1e-15)
    again = protocol._statistics(baseline, candidate, POLICY, {**NEW, "block_length": 2})
    assert again == new                                       # fixed seed: reproducible


# --- synthetic two-regime data -------------------------------------------------------------------

def test_a_regime_common_to_both_sides_cancels_in_the_paired_ratio():
    """A/A: both sides switch together (15% slow for the first 8 repetitions). The range rule
    calls this unstable; the paired CI stays narrow and inside (1/1.05, 1.05)."""
    regime = lambda r: 1.15 if r < 8 else 1.0                 # noqa: E731
    baseline, candidate = _blocks(regime, regime)
    metrics = protocol._statistics(baseline, candidate, POLICY, NEW)
    assert max(v for rows in metrics["relative_spread"].values() for v in rows.values()) > 0.1
    block = {"ratio": metrics["roi_speedup"], "lower": metrics["confidence_interval"]["lower"],
             "upper": metrics["confidence_interval"]["upper"], "spread": 0.15}
    assert _width(metrics) < 0.05 and pilot_passes(block, CI_WIDTH_RULE)
    assert not pilot_passes(block, RANGE_RULE)


def test_a_persistent_regime_on_one_side_widens_the_block_interval_and_fails_the_gate():
    """The candidate side switches once to a 13% faster regime halfway through the block (as
    upstream DO-BFS does). Repetitions are then dependent: the circular block interval is wider
    than the single-repetition one, and the gate calls the comparison inconclusive."""
    baseline, candidate = _blocks(lambda r: 1.0, lambda r: 1.0 if r < 10 else 0.87)
    iid = protocol._statistics(baseline, candidate, POLICY, OLD)
    blocks = protocol._statistics(baseline, candidate, POLICY, NEW)
    assert _width(blocks) > _width(iid)
    assert _width(blocks) > 0.05
    gate = {"minimum_speedup": 1.05, "gate": {"statistic": "relative_ci_width.v1", "maximum": 0.05}}
    assert decide(blocks, gate)[0] == "inconclusive"


def test_independent_noise_without_regimes_passes_and_resolves_a_real_effect():
    baseline, candidate = _blocks(lambda r: 1.0, lambda r: 1 / 1.28, sigma=0.02)
    metrics = protocol._statistics(baseline, candidate, POLICY, NEW)
    gate = {"minimum_speedup": 1.05, "gate": {"statistic": "relative_ci_width.v1", "maximum": 0.05}}
    state, noisy, gain = decide(metrics, gate)
    assert _width(metrics) < 0.05 and state == "gain" and gain and not noisy
    assert 1.2 < metrics["confidence_interval"]["lower"] < 1.28 < metrics["confidence_interval"]["upper"]


# --- decisions -------------------------------------------------------------------------------------

def _metrics(lower, upper, ratio, spread=0.2):
    return {"roi_speedup": ratio, "relative_spread": {"baseline": {"0": spread}, "candidate": {"0": 0.0}},
            "confidence_interval": {"lower": lower, "upper": upper, "relative_width": (upper - lower) / ratio}}


@pytest.mark.parametrize("lower, upper, ratio, expected", [
    (1.05, 1.08, 1.065, "no_gain"),          # exactly 1.05: no gain
    (1.0501, 1.08, 1.065, "gain"),
    (1.10, 1.20, 1.15, "inconclusive"),      # width 0.087 > 0.05, even with lower > 1.05
    (0.90, 0.94, 0.92, "regression"),
    (0.98, 1.02, 1.0, "no_gain"),
])
def test_ci_width_gate_decides_from_the_same_interval(lower, upper, ratio, expected):
    gate = {"minimum_speedup": 1.05, "gate": {"statistic": "relative_ci_width.v1", "maximum": 0.05}}
    assert decide(_metrics(lower, upper, ratio), gate)[0] == expected
    numbers = {"ratio": ratio, "lower": lower, "upper": upper, "spreads": [0.2]}
    campaign = speed_verdict(numbers, "native_cpu", CI_WIDTH_RULE)
    assert campaign == ("no_gain" if expected == "regression" else expected)


def test_range_rule_is_unchanged_for_protocols_without_a_gate():
    policy = {"minimum_speedup": 1.05, "maximum_relative_spread": 0.1}
    assert decide(_metrics(1.2, 1.25, 1.22, spread=0.11), policy)[0] == "inconclusive"
    assert decide(_metrics(1.2, 1.25, 1.22, spread=0.1), policy)[0] == "gain"
    assert decide(_metrics(1.10, 1.50, 1.3, spread=0.05), policy)[0] == "gain"     # width is not a range-rule gate
    numbers = {"ratio": 1.3, "lower": 1.2, "upper": 1.4, "spreads": [0.11]}
    assert speed_verdict(numbers, "native_cpu") == speed_verdict(numbers, "native_cpu", RANGE_RULE) == "inconclusive"


@pytest.mark.parametrize("block, passed", [
    ({"ratio": 1.0, "lower": 0.985, "upper": 1.016, "spread": 0.13}, True),
    ({"ratio": 1.0, "lower": 0.97, "upper": 1.03, "spread": 0.01}, False),      # width 0.06
    ({"ratio": 1.04, "lower": 1.03, "upper": 1.051, "spread": 0.01}, False),    # leaves (1/1.05, 1.05)
    ({"ratio": 0.96, "lower": 0.9520, "upper": 0.97, "spread": 0.01}, False),   # 0.9520 < 1/1.05
    ({"ratio": 0.96, "lower": 0.9525, "upper": 0.97, "spread": 0.01}, True),
])
def test_aa_pilot_gate_needs_a_narrow_interval_inside_the_equivalence_band(block, passed):
    assert pilot_passes(block, CI_WIDTH_RULE) is passed
    assert relative_ci_width(block) == (block["upper"] - block["lower"]) / block["ratio"]


# --- campaign files and the campaign loop ----------------------------------------------------------

def _campaign(**protocol_changes):
    data = {"format": "swdb.extensa-campaign.v1", "id": "extensa-native-bfs-20261004-z1", "created": "2026-10-04",
            "mode": "extensa", "kernel": "gapbs-bfs", "target": "native_cpu", "machine": "mbit10",
            "base_source": "fork_scalar_tdstep",
            "baselines": [{"role": "fork_scalar_tdstep", "candidate": "a"}, {"role": "upstream_do_bfs", "candidate": "b"}],
            "protocol": {"roi": "bfs.complete_call.v1", "threads": 1, "repetitions": 20, "sources": [0, 1234, 7777],
                         "region_pairs": False, "differences": "x", "speed_rule": CI_WIDTH_RULE,
                         **protocol_changes},
            "workload_classes": [{"class": "kronecker", "workload": "w"}], "label": "single graph per class",
            "library": {"allowed_tiers": ["shared"], "contracts": []}, "regions": ["r"],
            "provider": {"name": "codex", "model": "m", "effort": "xhigh"},
            "budgets": {"max_iterations": 8, "plateau_iterations": 4, "lane_hours": 24,
                        "provider_calls_per_iteration": 3, "provider_calls_setup": 1, "disk_gb": 20, "lanes": 1},
            "runs_root": "/tmp/x"}
    return data


def test_campaign_files_admit_the_ci_width_rule_for_native_only_with_enough_repetitions():
    assert campaign_problems(_campaign()) == []
    assert any("at least 8 repetitions" in p for p in campaign_problems(_campaign(repetitions=6)))
    gem5 = _campaign(repetitions=1, sources=[0])
    gem5.update(target="dx100_gem5", id="extensa-gem5-bfs-20261004-z1", baselines=gem5["baselines"][:1])
    assert any("native only" in p for p in campaign_problems(gem5))
    assert any("speed_rule" in p for p in campaign_problems(_campaign(speed_rule="swdb.speed_rule.other.v9")))
    settings = protocol_settings(_campaign())["profitability"]
    assert settings["gate"] == {"statistic": "relative_ci_width.v1", "maximum": 0.05}
    assert settings["block_length"] == 4 and "maximum_relative_spread" not in settings
    old = _campaign()
    old["protocol"].pop("speed_rule")
    assert protocol_settings(old)["profitability"]["maximum_relative_spread"] == 0.1


def _aa(width, center=1.0, spread=0.15):
    return {"ratio": center, "lower": center - width / 2, "upper": center + width / 2, "spread": spread}


def test_ci_width_pilot_gates_per_class_and_freezes_the_gate_into_the_protocol(team):
    path = campaign_file(team, protocol={"repetitions": 20, "speed_rule": CI_WIDTH_RULE})
    fx = fixture_file(team, pilot={"kronecker": {"fork_scalar_tdstep": _aa(0.06, spread=0.02),
                                                 "upstream_do_bfs": _aa(0.002)},
                                   "uniform_random": {"fork_scalar_tdstep": _aa(0.03),
                                                      "upstream_do_bfs": _aa(0.002)}})
    summary = run(team, path, fx, provider(team, {}))
    pilot = summary["pilot"]
    # Kronecker fails on width although its spread is 0.02; uniform passes although its spread is 0.15.
    assert pilot["unstable_classes"] == ["kronecker"] and pilot["speed_rule"] == CI_WIDTH_RULE
    assert pilot["ci_by_class_and_role"]["kronecker"]["fork_scalar_tdstep"]["passed"] is False
    assert pilot["ci_by_class_and_role"]["uniform_random"]["fork_scalar_tdstep"]["relative_width"] == pytest.approx(0.03)
    verdicts = {row["class"]: row["verdict"] for row in summary["per_class"]}
    assert verdicts["kronecker"] == "baseline_unstable" and verdicts["uniform_random"] == "gain"
    comps = [c for it in summary["iterations"] for cand in it["candidates"] for c in cand["comparisons"]]
    assert comps and all("relative_ci_width" in c and c["upper"] > c["lower"] for c in comps)
    (frozen,) = [p for p in records_of(campaign_store(team), "protocols") if p.get("campaign") == CID]
    settings = frozen["settings"]
    assert settings["sampling"]["analysis"] == ANALYSIS_CIRCULAR_BLOCK and settings["sampling"]["block_length"] == 4
    assert settings["profitability"]["gate"] == {"statistic": "relative_ci_width.v1", "maximum": 0.05}
    assert "maximum_relative_spread" not in settings["profitability"]


def test_ci_width_pilot_failing_every_class_stops_before_any_provider_call(team):
    path = campaign_file(team, protocol={"repetitions": 20, "speed_rule": CI_WIDTH_RULE})
    shifted = {"ratio": 1.04, "lower": 1.03, "upper": 1.052, "spread": 0.01}       # biased A/A
    fx = fixture_file(team, pilot={cls: {"fork_scalar_tdstep": shifted, "upstream_do_bfs": _aa(0.002)}
                                   for cls in ("kronecker", "uniform_random")})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["stop_reason"] == "baseline_unstable" and summary["iterations"] == [], summary.get("stop_detail")
    assert summary["stop_detail"] == "baseline A/A CI-width gate failed in every class"
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0 and log(team) == []


def test_ci_width_candidate_block_wider_than_the_gate_is_inconclusive(team):
    path = campaign_file(team, protocol={"repetitions": 20, "speed_rule": CI_WIDTH_RULE})
    wide = {"ratio": 1.3, "lower": 1.2, "upper": 1.4, "spread": 0.01}
    row = {cls: {"comparisons": {"fork_scalar_tdstep": wide, "upstream_do_bfs": wide}}
           for cls in ("kronecker", "uniform_random")}
    fx = fixture_file(team, iterations=[row],
                      pilot={cls: {"fork_scalar_tdstep": _aa(0.02), "upstream_do_bfs": _aa(0.002)}
                             for cls in ("kronecker", "uniform_random")})
    summary = run(team, path, fx, provider(team, {}))
    assert {row["verdict"] for row in summary["per_class"]} == {"inconclusive"}
    assert all(row["best"] is None for row in summary["per_class"])


# --- ticket 72: speed rule ci_width.v2 (the pilot gates on the selection baseline only) -------------

def test_level_mix_splits_two_level_trials_and_leaves_one_level_alone():
    from swdb.campaign import level_mix, level_mix_of
    two = level_mix([0.135, 0.1586, 0.1352, 0.1588, 0.1351, 0.159, 0.1349, 0.1353])
    assert two["levels"] == 2 and two["slow_trials"] == 3 and two["slow_share"] == pytest.approx(3 / 8)
    assert two["level_ratio"] == pytest.approx(0.1588 / 0.1351, rel=1e-3)
    one = level_mix([1.00, 1.02, 0.99, 1.05, 1.01])
    assert one["levels"] == 1 and one["slow_trials"] == 0 and one["largest_adjacent_ratio"] < 1.08
    evaluation = {"timing": [{"source_position": p, "duration_s": d}
                             for p, ds in ((0, [0.124, 0.143, 0.124, 0.143]), (1, [0.10, 0.101, 0.10, 0.102]))
                             for d in ds]}
    mix = level_mix_of(evaluation)
    assert mix["by_source_position"]["0"]["slow_trials"] == 2 and mix["by_source_position"]["1"]["levels"] == 1
    assert mix["slow_share"] == pytest.approx(2 / 8)


def test_v2_campaign_files_are_admitted_like_v1():
    from swdb.campaign import CI_WIDTH_RULE_V2, pilot_gating_roles
    assert campaign_problems(_campaign(speed_rule=CI_WIDTH_RULE_V2)) == []
    assert any("at least 8 repetitions" in p
               for p in campaign_problems(_campaign(speed_rule=CI_WIDTH_RULE_V2, repetitions=6)))
    v2 = _campaign(speed_rule=CI_WIDTH_RULE_V2)
    assert protocol_settings(v2)["profitability"]["gate"] == protocol_settings(_campaign())["profitability"]["gate"]
    roles = ["fork_scalar_tdstep", "upstream_do_bfs"]
    assert pilot_gating_roles(CI_WIDTH_RULE_V2, roles, "fork_scalar_tdstep") == ["fork_scalar_tdstep"]
    assert pilot_gating_roles(CI_WIDTH_RULE, roles, "fork_scalar_tdstep") == roles
    assert pilot_gating_roles(RANGE_RULE, roles, "fork_scalar_tdstep") == roles


def test_v2_pilot_gates_on_the_selection_baseline_and_reports_upstream(team):
    from swdb.campaign import CI_WIDTH_RULE_V2
    path = campaign_file(team, protocol={"repetitions": 20, "speed_rule": CI_WIDTH_RULE_V2})
    wide_upstream = _aa(0.12)                                   # a6-like upstream A/A: fails the block test
    fx = fixture_file(team, pilot={"kronecker": {"fork_scalar_tdstep": _aa(0.06), "upstream_do_bfs": wide_upstream},
                                   "uniform_random": {"fork_scalar_tdstep": _aa(0.02),
                                                      "upstream_do_bfs": wide_upstream}})
    summary = run(team, path, fx, provider(team, {}))
    pilot = summary["pilot"]
    assert pilot["speed_rule"] == CI_WIDTH_RULE_V2 and pilot["gating_roles"] == ["fork_scalar_tdstep"]
    assert pilot["unstable_classes"] == ["kronecker"]           # its fork block fails; upstream never gates
    up = pilot["ci_by_class_and_role"]["uniform_random"]["upstream_do_bfs"]
    assert up["passed"] is False and up["gates"] is False
    verdicts = {row["class"]: row["verdict"] for row in summary["per_class"]}
    assert verdicts == {"kronecker": "baseline_unstable", "uniform_random": "gain"}
    comps = [c for it in summary["iterations"] for cand in it["candidates"] for c in cand["comparisons"]]
    assert {c["baseline_role"] for c in comps} == {"fork_scalar_tdstep", "upstream_do_bfs"}


def test_v1_pilot_still_gates_on_every_role(team):
    path = campaign_file(team, protocol={"repetitions": 20, "speed_rule": CI_WIDTH_RULE})
    fx = fixture_file(team, pilot={cls: {"fork_scalar_tdstep": _aa(0.02), "upstream_do_bfs": _aa(0.12)}
                                   for cls in ("kronecker", "uniform_random")})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["stop_reason"] == "baseline_unstable" and summary["iterations"] == []
