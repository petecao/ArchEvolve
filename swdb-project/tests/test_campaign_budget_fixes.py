"""Ticket 80: Extensa campaign budgets and pruning (spec review C5, C6, C8).

Created: 2026-10-05 ET. Every number comes from a contract fixture or a fixture runner and is never evidence.
"""

import time
from argparse import Namespace
from pathlib import Path

import pytest

from swdb import campaign
from testkit.extensa import (GEM5, campaign_file, campaign_store, fixture_file, knob_rows, provider, records_of,
                             replay, rewrite, run)
from testkit.extensa_targets import CONTRACT as READ, FakeHost, FakeRunner, gem5_campaign, inside_patch
from testkit.extensa_targets import run as run_target

FIXTURES = Path(__file__).parent / "fixtures" / "provider_capacity"
CAPACITY = replay(stdout=FIXTURES / "a7-call4.stdout.txt")
TINY = 1e-9           # a fixture step charged this many hours (non-zero, so no wall time is measured)


# --- C5: the in-iteration gem5 baseline is charged ---------------------------------------------

def test_gem5_in_iteration_baseline_evaluation_is_charged_to_the_lane_hour_cap(campaign_team):
    path = campaign_file(campaign_team, cid=GEM5, target="dx100_gem5", budgets={"provider_calls_setup": 0})
    fx = fixture_file(campaign_team, step_hours={"evaluation": 0.25, "provider": TINY, "certification": TINY})
    summary = run(campaign_team, path, fx, provider(campaign_team, {}))
    assert summary["stop_reason"] == "max_iterations"
    assert len(summary["baselines"][0]["evaluation_ids_by_class"]) == 2
    # two class baselines and two comparisons, 0.25 h each (before ticket 80 only the comparisons counted)
    assert summary["budgets"]["used"]["lane_hours"] == pytest.approx(1.0, abs=1e-6)


def test_gem5_in_iteration_baseline_respects_the_lane_hour_cap(campaign_team):
    path = campaign_file(campaign_team, cid=GEM5, target="dx100_gem5",
                         budgets={"provider_calls_setup": 0, "lane_hours": 0.6})
    hours = {"evaluation": 0.25, "provider": TINY, "certification": TINY}
    summary = run(campaign_team, path, fixture_file(campaign_team, step_hours=hours, step_budget_hours=hours),
                  provider(campaign_team, {}))
    # kronecker: baseline 0.25 + comparison 0.25; uniform's baseline would pass 0.6 h
    assert summary["stop_reason"] == "lane_hours" and summary["budgets"]["used"]["lane_hours"] <= 0.6


# --- C6: provider waits are lane time ------------------------------------------------------------

def test_capacity_backoff_is_charged_to_lane_hours(campaign_team):
    config = provider(campaign_team, {"rewriting": [CAPACITY, rewrite()]})
    path = campaign_file(campaign_team, budgets={"max_iterations": 1})
    summary = run(campaign_team, path, fixture_file(campaign_team), config, env={"SWDB_CAPACITY_BACKOFF_S": "0.3"})
    used = summary["budgets"]["used"]
    assert used["provider_calls_uncounted"] == 1 and summary["stop_reason"] == "max_iterations"
    assert used["provider_wait_hours"] >= 0.3 / 3600
    assert used["lane_hours"] >= used["provider_wait_hours"]


def test_a_backoff_past_the_lane_hour_cap_stops_without_waiting(campaign_team):
    config = provider(campaign_team, {"rewriting": [CAPACITY]})
    path = campaign_file(campaign_team, budgets={"max_iterations": 1, "lane_hours": 0.001, "provider_calls_setup": 0})
    fx = fixture_file(campaign_team, step_hours={"provider": TINY, "evaluation": TINY, "certification": TINY})
    started = time.monotonic()
    summary = run(campaign_team, path, fx, config, env={"SWDB_CAPACITY_BACKOFF_S": "600"})
    assert summary["stop_reason"] == "lane_hours" and "capacity backoff of 600 s" in summary["stop_detail"]
    assert time.monotonic() - started < 300                 # the 600 s wait never started
    (call,) = [c for c in summary["interrupted_iteration"]["provider_calls"] if c["role"] == "rewriting"]
    assert call["outcome"] == "provider_capacity" and call["counted"] is False


def test_a_guard_retry_wait_is_charged_too(campaign_team):
    path = campaign_file(campaign_team, budgets={"max_iterations": 1, "lane_hours": 0.001, "provider_calls_setup": 0})
    loop = campaign.Campaign(Namespace(file=path, records=campaign_team["records"], library=None,
                                       provider_config=provider(campaign_team, {}), runs_root=None,
                                       fixture=fixture_file(campaign_team), resume=False))
    loop.state = {"lane_hours": 0.0}
    loop._wait(0.2, "guard retry wait")
    assert loop.state["lane_hours"] >= 0.2 / 3600 and loop.state["provider_wait_hours"] == loop.state["lane_hours"]
    with pytest.raises(campaign.Stop) as stopped:
        loop._wait(30, "guard retry wait")
    assert stopped.value.reason.value == "lane_hours"


# --- C8: companion runs and class baselines are pruned -------------------------------------------

def test_gem5_class_baselines_are_pruned_at_stop_unless_a_team_claim_cites_them(campaign_team):
    path = campaign_file(campaign_team, cid=GEM5, target="dx100_gem5", budgets={"provider_calls_setup": 0})
    fx = fixture_file(campaign_team, claim_runs=[f"{GEM5}.baseline.uniform_random"])
    summary = run(campaign_team, path, fx, provider(campaign_team, {}))
    store = campaign_store(campaign_team, GEM5)
    runs = store.parent / "runs"
    kron = runs / f"{GEM5}.baseline.kronecker.fork_scalar_tdstep"
    uniform = runs / f"{GEM5}.baseline.uniform_random.fork_scalar_tdstep"
    assert not (kron / "debug.trace.gz").exists() and not (kron / "cpt.1" / "payload.bin").exists()
    assert (kron / "correctness.json").exists()                       # compact evidence stays
    assert (uniform / "debug.trace.gz").exists()                      # cited by a team claim
    prunes = [r for r in records_of(store, "retentions") if r["event"] == "prune"]
    assert kron.name in {r["evaluation"] for r in prunes} and uniform.name not in {r["evaluation"] for r in prunes}
    assert all(r["mode"] == "extensa" and r["campaign"] == GEM5 for r in prunes)
    assert sorted(summary["retentions"]) == sorted(r["id"] for r in prunes)
    assert uniform.name in summary["baselines"][0]["evaluation_ids_by_class"].values()


def test_gem5_companion_runs_are_pruned_right_after_their_comparison(repo_team, base_source, monkeypatch):
    pruned = []
    original = campaign.Campaign._prune

    def recording(self, ids):
        pruned.append(list(ids))
        return original(self, ids)
    monkeypatch.setattr(campaign.Campaign, "_prune", recording)
    # a Kronecker-only knob makes the two classes' trees differ, so each class has its own companions
    config = provider(repo_team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [READ],
                                                 "knobs": knob_rows({"kronecker": {"frontier_threshold": 32}}),
                                                 "unresolved": []}]})
    runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02})
    _, summary = run_target(repo_team, gem5_campaign(repo_team, max_iterations=1), config, runner, FakeHost())
    rows = summary["iterations"][0]["candidates"]
    assert [r["level"] for r in rows] == ["certified", "certified"] and rows[0]["id"] != rows[1]["id"]
    for row in rows:
        companions = [f"{row['id']}.companion.{name}.evaluation" for name in ("diagnostic", "timed")]
        (call,) = [ids for ids in pruned if companions[0] in ids]
        assert call == [f"{row['id']}.evaluation", *companions]       # the observed run, then its companions
    # the class baselines serve every comparison, so they are pruned once, at stop
    assert pruned[-1] == sorted(f"extensa-gem5-bfs-20261004-f1.baseline.{cls}.aggregate"
                                for cls in ("kronecker", "uniform_random"))
