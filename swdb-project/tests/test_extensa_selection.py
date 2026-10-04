"""Extensa campaigns on contract fixtures: protocol, speed rule, selection and knobs (ticket 53).

Created: 2026-10-03 ET. Shares the fixtures of test_extensa_campaign.py; every number is
a contract fixture, never evidence.
"""


import pytest

from test_extensa_campaign import (CID, GEM5, GIB, campaign_file, campaign_store, comparison, fixture_file, log,  # noqa: F401
                                   provider, records_of, rewrite, run, team, team_seed)
from test_bfs_protocol import protocol_seed  # noqa: F401


# --- ticket 53: protocol, speed rule, selection, knobs -----------------------------------

def test_one_protocol_is_frozen_per_campaign_from_the_campaign_file(team):
    path = campaign_file(team)
    summary = run(team, path, fixture_file(team), provider(team, {}))
    (protocol,) = [p for p in records_of(campaign_store(team), "protocols") if p.get("campaign") == CID]
    settings = protocol["settings"]
    assert protocol["id"] == summary["protocol"]["id"] and settings["sampling"]["repetitions"] == 10
    assert settings["roi"] == "bfs.complete_call.v1" and settings["region_pairs"] == [] and settings["threads"] == 1
    assert "Extensa campaign fixture: rewrites of TDStep." in settings["differences"]["software"]
    assert settings["profitability"]["minimum_speedup"] == 1.05
    assert settings["profitability"]["maximum_relative_spread"] == 0.1
    assert summary["protocol"]["settings"]["sources"] == [0, 1234, 7777]
    comparisons = records_of(campaign_store(team), "comparison_results")
    assert comparisons and all(c["protocol"] == protocol["id"] for c in comparisons if c.get("campaign") == CID)


def test_gem5_measures_the_scalar_baseline_once_per_class_and_native_pairs_each_candidate(team):
    path = campaign_file(team, cid=GEM5, target="dx100_gem5", budgets={"max_iterations": 2})
    row = {cls: {"comparisons": {"fork_scalar_tdstep": {"ratio": 1.3}}} for cls in ("kronecker", "uniform_random")}
    summary = run(team, path, fixture_file(team, iterations=[row, row]), provider(team, {}))
    comps = [c for it in summary["iterations"] for cand in it["candidates"] for c in cand["comparisons"]]
    assert len(comps) == 4
    by_class = {}
    for it in summary["iterations"]:
        for cand in it["candidates"]:
            by_class.setdefault(cand["class"], set()).update(c["baseline_evaluation"] for c in cand["comparisons"])
    assert all(len(ids) == 1 for ids in by_class.values())
    assert summary["baselines"][0]["evaluation_ids_by_class"].keys() == {"kronecker", "uniform_random"}
    assert all(c["lower"] == c["ratio"] and c["spread"] == 0.0 for c in comps)   # point ratios
    native = run(team, campaign_file(team, cid="extensa-native-bfs-20261004-b1"), fixture_file(team),
                 provider(team, {}))
    native_comps = [c for it in native["iterations"] for cand in it["candidates"] for c in cand["comparisons"]]
    assert len({c["baseline_evaluation"] for c in native_comps}) == len(native_comps) == 4


@pytest.mark.parametrize("numbers, target, expected", [
    ({"ratio": 1.06, "lower": 1.05, "spreads": [0.05]}, "native_cpu", "no_gain"),
    ({"ratio": 1.06, "lower": 1.0501, "spreads": [0.05]}, "native_cpu", "gain"),
    ({"ratio": 1.3, "lower": 1.2, "spreads": [0.05, 0.11]}, "native_cpu", "inconclusive"),
    ({"ratio": 1.3, "lower": 1.2, "spreads": [0.1]}, "native_cpu", "gain"),
    ({"ratio": 1.05, "lower": 1.05, "spreads": [0.0]}, "dx100_gem5", "no_gain"),
    ({"ratio": 1.051, "lower": 1.051, "spreads": [0.0]}, "dx100_gem5", "gain"),
])
def test_speed_rule_is_strict_above_1_05_with_spread_at_most_0_1(numbers, target, expected):
    from swdb.campaign import speed_verdict
    assert speed_verdict(numbers, target) == expected


def test_native_pilot_with_unstable_baseline_stops_before_any_provider_call(team):
    # Ticket 64 (2026-10-04 ET) made the A/A gate per class: the campaign stops only when
    # every class is unstable (updated 2026-10-04 ET by the final code review).
    path = campaign_file(team)
    fx = fixture_file(team, pilot={"kronecker": {"fork_scalar_tdstep": 0.04, "upstream_do_bfs": 0.12},
                                   "uniform_random": {"fork_scalar_tdstep": 0.11, "upstream_do_bfs": 0.05}})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["stop_reason"] == "baseline_unstable" and summary["pilot"]["passed"] is False
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0 and summary["iterations"] == []
    assert log(team) == []


def test_native_pilot_unstable_class_is_never_timed_while_the_stable_class_runs(team):
    path = campaign_file(team)
    fx = fixture_file(team, pilot={"kronecker": {"fork_scalar_tdstep": 0.04, "upstream_do_bfs": 0.12},
                                   "uniform_random": {"fork_scalar_tdstep": 0.04, "upstream_do_bfs": 0.05}})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["pilot"]["passed"] is False and summary["pilot"]["unstable_classes"] == ["kronecker"]
    assert all(c["class"] == "uniform_random" for it in summary["iterations"] for c in it["candidates"])
    verdicts = {row["class"]: row["verdict"] for row in summary["per_class"]}
    assert verdicts["kronecker"] == "baseline_unstable" and verdicts["uniform_random"] != "baseline_unstable"


def test_selection_ranks_certification_first_and_lists_faster_uncertified(team):
    path = campaign_file(team, budgets={"max_iterations": 3, "provider_calls_setup": 0})
    certified = {cls: {"comparisons": {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)}}
                 for cls in ("kronecker", "uniform_random")}
    faster = {cls: {"comparisons": {"fork_scalar_tdstep": comparison(1.6), "upstream_do_bfs": comparison(1.1)}}
              for cls in ("kronecker", "uniform_random")}
    failing = {"kronecker": {"certification": ["failed", "failed", "failed"], "failed_checks": ["frontier_size"],
                             "comparisons": faster["kronecker"]["comparisons"]},
               "uniform_random": {"comparisons": {"fork_scalar_tdstep": comparison(1.0),
                                                  "upstream_do_bfs": comparison(0.8)}}}
    plan = {"rewriting": [rewrite(), rewrite(contracts=()), rewrite()],
            "repair": [rewrite(), rewrite()]}
    summary = run(team, path, fixture_file(team, iterations=[certified, faster, failing]), provider(team, plan))
    per = {row["class"]: row for row in summary["per_class"]}
    first = {c["class"]: c["id"] for c in summary["iterations"][0]["candidates"]}
    second = {c["class"]: c["id"] for c in summary["iterations"][1]["candidates"]}
    assert per["kronecker"]["best"] == first["kronecker"] and per["kronecker"]["best_level"] == "certified"
    assert per["kronecker"]["faster_uncertified"] == [second["kronecker"]]
    assert per["kronecker"]["best_selection_baseline"] == "fork_scalar_tdstep"
    assert per["kronecker"]["best_other_baseline"]["role"] == "upstream_do_bfs"
    assert all(c["level"] == "uncertified" and c["certification"] is None
               for c in summary["iterations"][1]["candidates"])
    third = {c["class"]: c for c in summary["iterations"][2]["candidates"]}
    assert third["kronecker"]["level"] == "rejected" and third["kronecker"]["comparisons"] == []
    assert [c["role"] for c in summary["iterations"][2]["provider_calls"]] == ["rewriting", "repair", "repair"]
    assert all(row["label"] == "single graph per class" for row in summary["per_class"])


def test_class_where_nothing_passes_has_no_best(team):
    path = campaign_file(team)
    row = {cls: {"comparisons": {"fork_scalar_tdstep": comparison(1.02), "upstream_do_bfs": comparison(0.9)}}
           for cls in ("kronecker", "uniform_random")}
    summary = run(team, path, fixture_file(team, iterations=[row]), provider(team, {}))
    assert all(r["verdict"] == "no_gain" and r["best"] is None and r["best_level"] is None
               for r in summary["per_class"])


def test_knob_outside_its_range_rejects_that_class_without_a_provider_call(team):
    path = campaign_file(team)
    plan = {"rewriting": [rewrite(knobs={"kronecker": {"frontier_threshold": 0},
                                         "uniform_random": {"frontier_threshold": 128}})]}
    summary = run(team, path, fixture_file(team), provider(team, plan))
    (it,) = summary["iterations"]
    by = {c["class"]: c for c in it["candidates"]}
    assert by["kronecker"]["level"] == "rejected" and by["kronecker"]["certification"] is None
    assert by["uniform_random"]["level"] == "certified"
    assert "knob_out_of_range" in it["feedback_reasons"]
    assert [c["role"] for c in it["provider_calls"]] == ["rewriting", "independent_test_generation"]


