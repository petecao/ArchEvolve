"""The WP phase after an Extensa campaign stops: the unbounded rung on its `gain` candidate artifacts.

Created: 2026-10-14 ET (Probata proof of concept, ticket 16). Seam 3 of the formal-verification map's spec
(`swdb campaign --fixture`, a contract-fixture campaign with the scripted verifier adapter), seam 1 (`swdb
prove`'s records) and seam 4 (`swdb validate`, `swdb build`). Every certification, comparison and proof record
here is a contract fixture, never evidence; no real verifier or provider runs. The fixture and its library
(ticket 11's `contract_fixture` method version: 10 hint rounds, 60 minutes of loop wall time) come from ticket
14's bounded-gate tests. A fixture class row's `proof.wp` scripts the WP job of that class's candidate artifact:
`proven_at` names the stage that proves it unbounded (`wp`: WP alone; `seeds`: with the contract seeds; a
number: that proof-hint round; absent: never), and `unit_postcondition: false` says its proof unit has none.
"""

import datetime
import json
from zoneinfo import ZoneInfo

import yaml

from conftest import run_swdb
from test_bounded_gate_campaign import (MIN_ONE, READ, entries, gate_campaign, gate_fixture, gate_seed,  # noqa: F401
                                        level, records_of, team)
from test_two_winners_campaign import PATCHES, THREADS_1, THREADS_K, per_class, row, winners
from testkit.extensa import campaign_file, fixture_file, provider, rewrite
from testkit.extensa import run as run_fixture

UNBOUNDED, CERTIFIED = "proven_unbounded", "certified"
HINT_ROUNDS = 10            # the contract_fixture method version's budgets.hint_rounds
ALL_ROUNDS = list(range(1, HINT_ROUNDS + 1))


def wp_campaign(team, rows, *, contract_proofs=None, fixture=None, **budgets):
    """A gated fixture campaign of len(rows) iterations; the rewrite call of iteration i returns PATCHES[i]."""
    fixture = gate_fixture(team, iterations=rows, contract_proofs=contract_proofs, **(fixture or {}))
    plan = {"rewriting": [rewrite(contracts=[READ], patch=PATCHES[i]) for i in range(len(rows))]}
    return gate_campaign(team, plan, fixture=fixture, **{"max_iterations": len(rows), **budgets})


def wp_class(summary, cls):
    return next(c for c in summary["wp_phase"]["classes"] if c["class"] == cls)


def ids(summary, cls):
    return [entries(summary, i)[cls][0]["id"] for i in range(len(summary["iterations"]))]


def wp_records(store, candidate):
    """The candidate artifact's WP proof records: those with no bounds-minimum pin and no skip of the gate."""
    gate = {j["record"] for e in all_entries(store) for j in (e.get("bounded_gate") or {}).get("jobs", [])}
    return [r for r in records_of(store, "proofs") if (r.get("subject") or {}).get("candidate") == candidate
            and r["id"] not in gate]


def state_of(store):
    return json.loads((store.parent / "state.json").read_text())


def all_entries(store):
    return [c for it in state_of(store)["iterations"] for c in it["candidates"]]


def when(text):
    return datetime.datetime.fromisoformat(text)


def assert_no_overlap(store):
    """No two recorded intervals (proof jobs, timing steps, gem5 simulations) overlap."""
    rows = sorted(state_of(store)["timeline"], key=lambda r: when(r["started"]))
    for earlier, later in zip(rows, rows[1:]):
        assert when(earlier["ended"]) <= when(later["started"]), (earlier, later)
    return rows


# --- the tracer: order and stop per class; one record per job; the summary rewritten once -------------------

def test_each_class_tries_its_gain_candidates_fastest_first_until_one_is_proven_unbounded(team):
    rows = [{"kronecker": row(1.5, wp={}), "uniform_random": row(1.1, wp={"proven_at": "wp"})},
            {"kronecker": row(1.3, wp={"proven_at": 2}), "uniform_random": row(1.4, wp={})},
            {"kronecker": row(1.2, wp={"proven_at": "wp"}), "uniform_random": row(0.9, wp={"proven_at": "wp"})}]
    summary, store = wp_campaign(team, rows)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    k1, k2, k3 = ids(summary, "kronecker")
    u1, u2, u3 = ids(summary, "uniform_random")
    wp = summary["wp_phase"]
    assert wp["state"] == "ended" and wp["end_reason"] == "classes_done", wp
    # Kronecker, fastest first: the fastest spends its hint budget, the second is proven unbounded, the third
    # never runs.
    kron = wp_class(summary, "kronecker")
    assert kron["order"] == [k1, k2, k3] and kron["proven"] == k2 and kron["state"] == UNBOUNDED
    first, second = kron["jobs"]
    assert first["candidate"] == k1 and second["candidate"] == k2
    assert first["verdict"] == "not_proven" and first["failure_class"] == "hint_budget_spent"
    assert first["stages"] == ["wp", "seeds", *ALL_ROUNDS] and first["hint_calls"] == HINT_ROUNDS
    assert second["verdict"] == "proven" and second["stages"] == ["wp", "seeds", 1, 2] and second["hint_calls"] == 2
    # One `swdb prove` job, one proof record per WP run, contract-fixture evidence; levels read from the records.
    for job in kron["jobs"]:
        (record,) = wp_records(store, job["candidate"])
        assert record["id"] == job["record"] and record["verdict"] == job["verdict"]
        assert record["evidence_kind"] == "contract_fixture" and record["pins"]["method_version"]["id"] == \
            "method.contract-fixture-1" and record["job"]["adapter"] == "scripted"
    assert wp_records(store, k3) == []
    assert [level(store, c)["level"] for c in (k1, k2, k3)] == [THREADS_K, UNBOUNDED, THREADS_K]
    # The second class runs its own order; a candidate artifact without a gain is never scheduled.
    uniform = wp_class(summary, "uniform_random")
    assert uniform["order"] == [u2, u1] and [j["candidate"] for j in uniform["jobs"]] == [u2, u1]
    assert uniform["proven"] == u1 and wp_records(store, u3) == []
    # Starts after the stop summary; the summary is rewritten exactly once, at the phase end.
    writes = state_of(store)["summary_writes"]
    assert [w["when"] for w in writes] == ["stop", "wp_phase_end"]
    assert when(writes[0]["at"]) <= when(wp["started"]) <= when(wp["ended"]) <= when(writes[1]["at"])
    timeline = assert_no_overlap(store)
    assert all(when(r["ended"]) <= when(wp["started"]) for r in timeline if r["kind"] != "proof_job")
    # The rewritten summary: best-proven winner recomputed (proven unbounded beats threads <= k), the fastest stays;
    # snapshots dated at the phase end, with the level-rule version; no level reads as pending.
    assert winners(per_class(summary, "kronecker")["winners"]) == {"fastest": k1, "best_proven": k2}
    assert winners(per_class(summary, "uniform_random")["winners"]) == {"fastest": u2, "best_proven": u1}
    started_et = when(wp["started"]).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M ET")
    for cls in ("kronecker", "uniform_random"):
        for winner in per_class(summary, cls)["winners"]:
            snapshot = winner["level_snapshot"]
            assert snapshot["at"] >= started_et and snapshot["level_rule"] == "level-rule.2"
            assert snapshot["level"] == level(store, winner["candidate"])["level"]
    assert "pending" not in json.dumps(summary)
    # Budget lines: proof-hint calls on their own line, never in the rewriting total.
    used, limits = summary["budgets"]["used"], summary["budgets"]["limits"]
    loop_calls = summary["setup"]["provider_calls"] + [c for it in summary["iterations"] for c in it["provider_calls"]]
    assert used["provider_calls_counted"] == sum(1 for c in loop_calls if c["counted"]) == 4
    assert used["provider_calls_proof"] == len(wp["provider_calls"]) == HINT_ROUNDS + 2 + HINT_ROUNDS
    assert {c["role"] for c in wp["provider_calls"]} == {"proof_hint"}
    assert used["certification_repair_calls"] == used["counterexample_repair_calls"] == 0
    assert limits["provider_calls_proof"] == 30 and 0 < used["proof_lane_hours"] <= used["lane_hours"]
    # The team store's summary is the rewritten one; both stores validate and build.
    (team_copy,) = (team["records"] / "campaign_summaries").glob("*.yaml")
    assert yaml.safe_load(team_copy.read_text())["wp_phase"]["state"] == "ended"
    for records in (team["records"], store):
        for command in ("validate", "build"):
            result = run_swdb(command, "--records", records)
            assert result.returncode == 0, (records, command, result.stdout + result.stderr)
    # A campaign whose WP phase has ended is refused on resume, as a stopped campaign is.
    again = run_swdb("campaign", team["root"] / "campaigns" / "extensa" / f"{summary['campaign']}.yaml",
                     "--records", team["records"], "--provider-config", team["root"] / "provider.yaml",
                     "--fixture", team["root"] / "fixture.yaml", "--library", team["library"], "--resume")
    assert again.returncode != 0 and "already stopped" in again.stderr + again.stdout


# --- what may run (S6, O7) ---------------------------------------------------------------------------------------

def test_without_a_contract_proof_route_1_wp_runs_when_the_unit_has_a_postcondition_else_it_is_skipped(team):
    rows = [{"kronecker": row(1.5, wp={"unit_postcondition": False, "proven_at": "wp"}),
             "uniform_random": row(1.5, wp={"proven_at": "wp"}, cpp_subset=False)},
            {"kronecker": row(1.3, wp={"proven_at": 1}), "uniform_random": row(1.3, wp={"proven_at": "wp"})}]
    summary, store = wp_campaign(team, rows, contract_proofs={})
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    k1, k2 = ids(summary, "kronecker")
    u1, u2 = ids(summary, "uniform_random")
    kron, uniform = wp_class(summary, "kronecker"), wp_class(summary, "uniform_random")
    # No contract proof and no unit postcondition: a skip record with that reason; the next one is tried.
    skipped, ran = kron["jobs"]
    (record,) = wp_records(store, k1)
    assert skipped["skip_reason"] == record["skip_reason"] == "no_contract_proof" and "verdict" not in record
    # No contract proof, with a unit postcondition: route-1 WP runs without seeds and writes its record.
    assert ran["candidate"] == k2 and ran["stages"] == ["wp", 1] and ran["verdict"] == "proven"
    # Outside the C++ subset: skipped with that reason, no hint loop.
    outside, proven = uniform["jobs"]
    (record,) = wp_records(store, u1)
    assert outside["candidate"] == u1 and outside["skip_reason"] == record["skip_reason"] == "outside_cpp_subset"
    assert "stages" not in outside and proven["candidate"] == u2 and proven["stages"] == ["wp"]
    # A skipped candidate artifact keeps its level.
    assert [level(store, c)["level"] for c in (k1, k2, u1, u2)] == [CERTIFIED, UNBOUNDED, CERTIFIED, UNBOUNDED]
    assert summary["budgets"]["used"]["provider_calls_proof"] == 1


def test_a_timed_out_bounded_job_or_missing_minimum_bounds_still_schedules_and_a_spent_hint_cap_leaves_wp_and_seeds(team):
    """Also the second budget control: once provider_calls_proof is spent, WP and the seeds still run."""
    rows = [{"kronecker": row(1.5, wp={}, threads_1=["timeout"]), "uniform_random": row(1.5, wp={"proven_at": "seeds"})},
            {"kronecker": row(1.3, wp={"proven_at": 1}), "uniform_random": row(1.2, wp={"proven_at": "wp"})}]
    no_threads_k_minimum = {READ: {"minimum_bounds": {"threads_1": MIN_ONE}}}
    summary, store = wp_campaign(team, rows, contract_proofs=no_threads_k_minimum, provider_calls_proof=3)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    k1, k2 = ids(summary, "kronecker")
    u1, u2 = ids(summary, "uniform_random")
    gate = {j["rung"]: j for j in entries(summary, 0)["kronecker"][0]["bounded_gate"]["jobs"]}
    assert gate["threads_1"]["failure_class"] == "timeout" and gate["threads_k"]["skip_reason"] == "no_minimum_bounds"
    kron = wp_class(summary, "kronecker")
    assert kron["order"] == [k1, k2] and kron["state"] == "order_spent" and kron["proven"] is None
    first, second = kron["jobs"]
    assert first["stages"] == ["wp", "seeds", 1, 2, 3] and first["hint_calls"] == 3
    # The cap is spent: the next WP run uses WP alone and the seeds, then ends not proven, hint budget spent.
    assert second["stages"] == ["wp", "seeds"] and second["hint_calls"] == 0
    assert first["failure_class"] == second["failure_class"] == "hint_budget_spent"
    for cid, job in ((k1, first), (k2, second)):
        (record,) = wp_records(store, cid)
        assert record["verdict"] == "not_proven" and record["failure_class"] == "hint_budget_spent"
    assert [level(store, c)["level"] for c in (k1, k2)] == [CERTIFIED, THREADS_1]       # each keeps its level
    # Seeds alone still prove a unit after the cap is spent.
    uniform = wp_class(summary, "uniform_random")
    assert [j["candidate"] for j in uniform["jobs"]] == [u1] and uniform["jobs"][0]["stages"] == ["wp", "seeds"]
    assert level(store, u1)["level"] == UNBOUNDED and wp_records(store, u2) == []
    assert summary["budgets"]["used"]["provider_calls_proof"] == 3


# --- the two call budgets stay apart --------------------------------------------------------------------------

def test_a_campaign_stopped_on_its_rewriting_total_still_runs_its_wp_phase_hint_calls(team):
    """Every attempt of iteration 1 spends a counted rewrite call; Kronecker's certification fails and its repair
    call pauses on a usage limit, until the rewriting total (2 x 2) refuses the repair call (iteration 1 then
    completes, Kronecker rejected) and then iteration 2's rewrite call: the campaign stops on provider_calls."""
    rows = [{"kronecker": {**row(1.5, wp={"proven_at": "wp"}), "certification": ["failed"]},
             "uniform_random": row(1.3, wp={"proven_at": 2})}]
    path = campaign_file(team, library={"contracts": [READ]},
                         budgets={"max_iterations": 2, "provider_calls_per_iteration": 2, "provider_calls_setup": 0})
    fixture = gate_fixture(team, iterations=rows)
    config = provider(team, {"rewriting": [rewrite(contracts=[READ], patch=PATCHES[0])], "repair": ["usage_limit"]})
    result = run_fixture(team, path, fixture, config, "--library", team["library"])
    for _ in range(6):
        if result.get("state") != "paused":
            break
        result = run_fixture(team, path, fixture, config, "--library", team["library"], "--resume")
    assert result["stop_reason"] == "provider_calls", result.get("stop_detail")
    used = result["budgets"]["used"]
    assert used["provider_calls_counted"] == 4 and used["iterations"] == 1
    kron, uniform = (entries(result, 0)[cls][0] for cls in ("kronecker", "uniform_random"))
    assert kron["level"] == "rejected" and wp_class(result, "kronecker")["order"] == []
    # The spent rewriting total takes nothing from the WP phase: its two hint calls run.
    (job,) = wp_class(result, "uniform_random")["jobs"]
    assert job["candidate"] == uniform["id"] and job["stages"] == ["wp", "seeds", 1, 2] and job["verdict"] == "proven"
    assert used["provider_calls_proof"] == 2 and used["provider_calls_counted"] == 4


# --- lane-hours shared, reported apart; never overlapping a timing step ---------------------------------------

def test_proof_jobs_share_the_lane_hours_report_them_apart_end_the_phase_and_wait_for_an_open_timing_step(team):
    rows = [{cls: row(1.5 if cls == "kronecker" else 1.4, wp={}) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.3, wp={}) for cls in ("kronecker", "uniform_random")}]
    fixture = {"step_hours": {"proof": 0.6}, "open_timing_step": {"seconds": 2}}
    summary, store = wp_campaign(team, rows, fixture=fixture, lane_hours=3.5)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    used, wp = summary["budgets"]["used"], summary["wp_phase"]
    # Four gate runs in the loop (2.4 lane-hours); the first WP job leaves 0.5, less than the next job's 60 minutes.
    assert wp["end_reason"] == "lane_hours" and wp["state"] == "ended"
    jobs = [j for c in wp["classes"] for j in c["jobs"]]
    assert len(jobs) == 1 and jobs[0]["candidate"] == ids(summary, "kronecker")[0]
    assert {c["class"]: c["state"] for c in wp["classes"]} == {"kronecker": "unfinished", "uniform_random": "unfinished"}
    # Every other step is charged its measured wall time here (seconds), so lane-hours are the proof jobs' and a little.
    assert used["proof_lane_hours"] == 3.0 and 3.0 <= used["lane_hours"] < 3.05
    assert summary["bounded_gate"]["proof_job_hours"] >= 0
    # The scripted timing step was open when the phase started: the WP job waited until it closed.
    (wait,) = wp["waits"]
    assert wait["for"] == ["scripted timing step"] and wait["seconds"] >= 1.5
    assert when(jobs[0]["started"]) >= when(wait["until"])
    timeline = assert_no_overlap(store)
    kinds = [r["kind"] for r in timeline]
    assert kinds.count("proof_job") == 5 and "timing_step" in kinds
    # Raising lane-hours still needs the approval entry (the existing check).
    path = campaign_file(team, cid="extensa-native-bfs-20261004-a2", budgets={"lane_hours": 25})
    result = run_swdb("validate", "--records", team["records"])
    assert result.returncode != 0 and "budgets.lane_hours" in result.stdout + result.stderr
    path.unlink()


# --- provider_calls_proof in budget validation -------------------------------------------------------------------

def test_provider_calls_proof_validates_up_to_30_and_above_only_with_an_approval_entry_naming_it(team):
    path = campaign_file(team, budgets={"provider_calls_proof": 30})
    assert run_swdb("validate", "--records", team["records"]).returncode == 0
    campaign_file(team, budgets={"provider_calls_proof": 31})
    refused = run_swdb("validate", "--records", team["records"])
    assert refused.returncode != 0 and "budgets.provider_calls_proof" in refused.stdout + refused.stderr
    campaign_file(team, budgets={"provider_calls_proof": 31},
                  approval={"by": "Yan-Ru Jhou", "date": "2026-10-14", "scope": "contract-fixture test",
                            "raised_budgets": ["provider_calls_proof"]})
    accepted = run_swdb("validate", "--records", team["records"])
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    # Omitted: a campaign whose library holds a method version (so it has a WP phase) is refused at start.
    data = yaml.safe_load(path.read_text())
    data["budgets"].pop("provider_calls_proof")
    data.pop("approval")
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    fixture = fixture_file(team, base_snapshot="test-source")
    config = provider(team, {"rewriting": [rewrite(contracts=[READ], patch=PATCHES[0])]})
    started = run_swdb("campaign", path, "--records", team["records"], "--provider-config", config, "--fixture",
                       fixture, "--library", team["library"])
    assert started.returncode != 0 and "budgets.provider_calls_proof" in started.stdout + started.stderr
    assert not (team["root"] / "runs" / "extensa" / data["id"] / "state.json").exists()
