"""Extensa campaigns on contract fixtures: budgets, pauses and pruning (ticket 54).

Created: 2026-10-03 ET. Shares the fixtures of test_extensa_campaign.py; every number is
a contract fixture, never evidence.
"""

import json


from test_extensa_campaign import (CID, GEM5, GIB, campaign_file, campaign_store, comparison, fixture_file, log,  # noqa: F401
                                   provider, records_of, rewrite, run, team, team_seed)
from test_bfs_protocol import protocol_seed  # noqa: F401


# --- ticket 54: budgets, pauses, pruning --------------------------------------------------

def test_plateau_stops_after_non_improving_iterations(team):
    path = campaign_file(team, budgets={"max_iterations": 8, "plateau_iterations": 2, "provider_calls_setup": 0})
    flat = {cls: {"comparisons": {"fork_scalar_tdstep": comparison(1.01), "upstream_do_bfs": comparison(0.9)}}
            for cls in ("kronecker", "uniform_random")}
    summary = run(team, path, fixture_file(team, iterations=[flat]), provider(team, {}))
    assert summary["stop_reason"] == "plateau" and summary["budgets"]["used"]["iterations"] == 2


def test_lane_hour_cap_refuses_a_step_that_would_exceed_it(team):
    path = campaign_file(team, budgets={"max_iterations": 5, "lane_hours": 3, "provider_calls_setup": 0})
    fx = fixture_file(team, step_hours={"provider": 0.2, "certification": 0.3, "evaluation": 0.25},
                      step_budget_hours={"provider": 0.5, "certification": 0.5, "evaluation": 0.5})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["stop_reason"] == "lane_hours"
    assert summary["budgets"]["used"]["lane_hours"] <= 3


def test_disk_cap_and_dispatch_preflight_stop_the_campaign(team):
    path = campaign_file(team, budgets={"disk_gb": 0.00005, "provider_calls_setup": 0})
    summary = run(team, path, fixture_file(team, run_bytes=30000), provider(team, {}))
    assert summary["stop_reason"] == "disk"
    other = campaign_file(team, cid="extensa-native-bfs-20261004-c1", budgets={"provider_calls_setup": 0})
    low = fixture_file(team, preflight={"disk": "/data1", "free_bytes": GIB, "free_memory_bytes": 64 * GIB})
    summary = run(team, other, low, provider(team, {}))
    assert summary["stop_reason"] == "disk" and "preflight" in summary["stop_detail"]


def test_native_timed_blocks_refuse_while_a_gem5_extensa_job_holds_the_other_socket(team):
    path = campaign_file(team, budgets={"provider_calls_setup": 0})
    fx = fixture_file(team, other_socket_lease={"mode": "extensa", "target": "dx100_gem5", "campaign": GEM5})
    summary = run(team, path, fx, provider(team, {}))
    assert summary["stop_reason"] == "infrastructure_failure" and GEM5 in summary["stop_detail"]


def test_usage_limit_pauses_uncounted_releases_the_lane_and_resumes_the_iteration(team):
    path = campaign_file(team, budgets={"max_iterations": 1, "provider_calls_setup": 0})
    config = provider(team, {"rewriting": ["usage_limit", rewrite()]})
    paused = run(team, path, fixture_file(team), config)
    assert paused["state"] == "paused" and paused["reason"] == "usage_limit"
    state = json.loads((campaign_store(team).parent / "state.json").read_text())
    assert state["ledger"]["iterations_completed"] == 0
    summary = run(team, path, fixture_file(team), config, "--resume")
    assert summary["stop_reason"] == "max_iterations" and summary["budgets"]["used"]["iterations"] == 1
    assert summary["budgets"]["used"]["provider_calls_uncounted"] == 1
    (pause,) = summary["pauses"]
    assert pause["reason"] == "usage_limit" and pause["resumed_at"]
    assert pause["provider_calls"][0]["counted"] is False


def test_login_failure_also_pauses_uncounted(team):
    path = campaign_file(team, budgets={"provider_calls_setup": 0})
    paused = run(team, path, fixture_file(team), provider(team, {"rewriting": ["login", rewrite()]}))
    assert paused["state"] == "paused" and paused["reason"] == "login"


def test_total_provider_call_budget_stops_with_provider_calls(team):
    path = campaign_file(team, budgets={"max_iterations": 2, "provider_calls_per_iteration": 2,
                                        "provider_calls_setup": 0})
    # Each attempt: the rewrite call is counted, the test-generation call hits the usage
    # limit (uncounted) and pauses. Counted calls of paused attempts stay counted, so the
    # campaign-wide total (2 x 2) eventually refuses the next rewrite call.
    config = provider(team, {"rewriting": [rewrite()], "testgen": ["usage_limit"]})
    fx = fixture_file(team)
    result = run(team, path, fx, config)
    for _ in range(6):
        if result.get("state") != "paused":
            break
        result = run(team, path, fx, config, "--resume")
    assert result["stop_reason"] == "provider_calls"
    assert result["budgets"]["used"]["provider_calls_counted"] == 4
    assert result["budgets"]["used"]["provider_calls_uncounted"] == 3 and len(result["pauses"]) == 3


def test_stopped_by_yanru(team):
    path = campaign_file(team, budgets={"max_iterations": 3, "provider_calls_setup": 0})
    folder = team["root"] / "runs" / "extensa" / CID
    folder.mkdir(parents=True)
    (folder / "STOP").write_text("Yan-Ru Jhou 2026-10-04\n")
    summary = run(team, path, fixture_file(team), provider(team, {}))
    assert summary["stop_reason"] == "stopped_by_yanru" and summary["iterations"] == []


def test_bulky_output_is_pruned_after_each_comparison_unless_a_team_claim_cites_it(team):
    path = campaign_file(team, budgets={"provider_calls_setup": 0})
    summary = run(team, path, fixture_file(team, claim_runs=["it1.kronecker.a0.fork_scalar_tdstep.candidate-eval"]),
                  provider(team, {}))
    store = campaign_store(team)
    retentions = [r for r in records_of(store, "retentions") if r["event"] == "prune"]
    assert retentions and all(r["mode"] == "extensa" and r["campaign"] == CID for r in retentions)
    assert sorted(summary["retentions"]) == sorted(r["id"] for r in retentions)
    runs = store.parent / "runs"
    claimed = runs / f"{CID}.it1.kronecker.a0.fork_scalar_tdstep.candidate-eval"
    assert (claimed / "debug.trace.gz").exists() and (claimed / "cpt.1" / "payload.bin").exists()
    others = [p for p in runs.iterdir() if p != claimed]
    assert others and all(not (p / "debug.trace.gz").exists() and (p / "correctness.json").exists() for p in others)
    assert {r["evaluation"] for r in retentions}.isdisjoint({claimed.name})
    # campaign records are never pruned
    assert all(p.exists() for p in store.rglob("*.yaml"))
