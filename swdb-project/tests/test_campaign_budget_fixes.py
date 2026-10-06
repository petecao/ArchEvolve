"""Ticket 80: Extensa campaign budgets (spec review C5, C6).

Created: 2026-10-05 ET. Every number comes from a contract fixture and is never evidence.
"""

import time
from argparse import Namespace
from pathlib import Path

import pytest

from swdb import campaign
from testkit.extensa import GEM5, campaign_file, fixture_file, provider, replay, rewrite, run

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
