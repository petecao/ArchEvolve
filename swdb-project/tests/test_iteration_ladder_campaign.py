"""The iteration ladder in Extensa campaigns: where `LADDER.json` appears, what it holds, resume and version.

Created: 2026-10-14 ET (Probata proof of concept, ticket 17). Seam 3 of the formal-verification map's spec
(`swdb campaign --fixture`, a contract-fixture campaign with the scripted verifier adapter) and seam 4
(`swdb validate`). Every certification, comparison and proof record here is a contract fixture, never
evidence; no real verifier or provider runs. The renderer's own tests are in test_iteration_ladder.py.
"""

import hashlib
import json

import yaml

from conftest import run_swdb
from swdb import iteration_ladder
from test_bounded_gate_campaign import (READ, cex_repair, edit, gate_campaign, gate_fixture,  # noqa: F401
                                        gate_seed, team)       # gate_seed, team: fixtures
from test_two_winners_campaign import THREADS_1, row
from testkit.extensa import CID, campaign_file, fixture_file, log, provider, rewrite, run

P1, P3, P4 = (edit("int alpha = 15", f"int alpha = {n}") for n in (14, 13, 12))
CERT_REPAIR = rewrite(contracts=[READ], patch=edit("int alpha = 15", "int alpha = 11"))
BETA = ("int beta = 18", "int beta = 17")
#: A rewrite answer outside the role's output schema: the call returns nothing usable.
NOTHING = {"bogus": True}


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def folder_of(team, cid=CID):
    return team["root"] / "runs" / "extensa" / cid


def state_of(team, cid=CID):
    return json.loads((folder_of(team, cid) / "state.json").read_text())


def ladder_rows(text):
    return json.loads(text)["rows"]


def by_role(calls, role):
    return [c for c in calls if c["role"] == role]


# --- the tracer: a gated campaign with a rejected, a repaired and an empty iteration --------------------------

def test_every_workspace_from_iteration_2_shows_the_ladder_rebuilt_from_state(team):
    rows = [{"kronecker": row(1.2), "uniform_random": row(1.3, THREADS_1)},       # uniform: a threads_k timeout
            {"kronecker": row(1.1), "uniform_random": row(1.1)},                    # unused: the call returns nothing
            {"kronecker": row(1.5, threads_1=["refuted", "proven"]),               # refuted, then repaired
             "uniform_random": {**row(1.4), "certification": ["failed"],
                                "failed_checks": ["verifier", "control:fixture_control"]}},
            {"kronecker": row(1.1, "certified"), "uniform_random": row(1.1, "certified")}]
    plan = {"rewriting": [rewrite(contracts=[READ], patch=P1), NOTHING, rewrite(contracts=[READ], patch=P3),
                          rewrite(contracts=[READ], patch=P4)],
            "repair": [CERT_REPAIR], "counterexample_repair": [cex_repair(BETA)]}
    summary, _store = gate_campaign(team, plan, fixture=gate_fixture(team, iterations=rows), max_iterations=4,
                                    provider_calls_per_iteration=5)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    calls = log(team)
    rewrites = by_role(calls, "rewriting")
    assert len(rewrites) == 4

    # Where it appears: never in iteration 1; in every rewrite workspace from iteration 2; FEEDBACK.json stays.
    assert rewrites[0]["ladder"] is None and "LADDER.json" not in rewrites[0]["files"]
    for call in rewrites[1:]:
        assert call["ladder"] is not None and {"LADDER.json", "FEEDBACK.json"} <= set(call["files"])
    # Every repair workspace of iteration 3 (two certification repairs, one counterexample repair) gets the
    # same file as iteration 3's rewrite workspace.
    third = rewrites[2]["ladder"]
    repairs = by_role(calls, "repair") + by_role(calls, "counterexample_repair")
    assert len(by_role(calls, "repair")) == 2 and len(by_role(calls, "counterexample_repair")) == 1
    assert [c["ladder"] for c in repairs] == [third] * 3
    # The rewrite prompt names the file.
    prompts = sorted((folder_of(team) / "provider").glob("*/prompt.txt"))
    assert prompts and all("`LADDER.json`" in p.read_text() for p in prompts
                           if "LADDER.json" in json.loads((p.parent / "workspace.json").read_text())["visible_files"])

    # One row per earlier candidate artifact, no gaps; the row count matches state.
    last = ladder_rows(rewrites[3]["ladder"])
    state = state_of(team)
    expected = sum(max(len(it["candidates"]), 1) for it in state["iterations"][:3])
    assert len(last) == expected == 6
    assert [r["iteration"] for r in last] == [1, 1, 2, 3, 3, 3] and [r["row"] for r in last] == list(range(1, 7))
    empty = last[2]
    assert empty["class"] == "-" and empty["reason_codes"] == ["provider_output_invalid"]
    refuted, repaired, rejected = last[3:]
    assert refuted["level"] == "refuted" and "refuted" in refuted["reason_codes"]
    assert refuted["failed_checks"] == ["bounded_threads_1"] and refuted["verdict"] is None
    assert repaired["repair_of"] == refuted["row"] and repaired["level"] == "proven_within_bounds_threads_k"
    assert repaired["verdict"] == "gain" and repaired["ratio"] == 1.5
    assert rejected["level"] == "rejected" and rejected["reason_codes"] == ["certification_failed"]
    assert rejected["failed_checks"] == ["verifier", "negative_controls_not_rejected"]     # one aggregate category
    timeout = last[1]
    assert timeout["level"] == THREADS_1 and "proof_timeout" in timeout["reason_codes"]
    assert {r["level"] for r in last} <= set(iteration_ladder.LEVELS)
    # The new reason codes reached FEEDBACK.json's iterations too.
    assert "proof_timeout" in summary["iterations"][0]["feedback_reasons"]
    assert "refuted" in summary["iterations"][2]["feedback_reasons"]

    # Winner marks move with 15's winners: kronecker's both-winner moves from iteration 1 to the repair.
    second = ladder_rows(rewrites[1]["ladder"])
    assert [r["winner"] for r in second] == ["both", "both"]
    assert [r["winner"] for r in last] == ["", "both", "", "", "both", ""]

    # The file is the renderer's output from state; the campaign folder's copy is the latest one.
    assert (folder_of(team) / "LADDER.json").read_text() == rewrites[3]["ladder"]

    # Auditable: every provider call's workspace record hashes the ladder it saw.
    hashed = []
    for receipt in folder_of(team).rglob("workspace.json"):
        meta = json.loads(receipt.read_text())
        if "LADDER.json" in (meta.get("input_sha256s") or {}):
            hashed.append(meta["input_sha256s"]["LADDER.json"])
        if meta.get("iteration_ladder"):
            hashed.append(meta["iteration_ladder"]["sha256"])
    seen = [c["ladder"] for c in calls if c["ladder"] is not None]
    assert sorted(hashed) == sorted(sha256(text) for text in seen)

    # Workspace version: recorded in state and summary; the summary validates.
    assert state["rewrite_workspace"] == summary["rewrite_workspace"] == "v2"
    result = run_swdb("validate", "--records", team["records"])
    assert result.returncode == 0, result.stdout + result.stderr


# --- resume: rebuilt from state, never from an old file; a v1 campaign never gains a ladder -----------------

def paused(campaign_team):
    """A two-iteration campaign paused by a usage limit on iteration 2's rewrite call."""
    config = provider(campaign_team, {"rewriting": [rewrite(), "usage_limit", rewrite()]})
    path = campaign_file(campaign_team, budgets={"max_iterations": 2})
    fixture = fixture_file(campaign_team)
    first = run(campaign_team, path, fixture, config)
    assert first["state"] == "paused"
    return path, fixture, config


def test_a_resumed_v2_campaign_rebuilds_the_ladder_from_state_never_from_a_planted_file(campaign_team):
    path, fixture, config = paused(campaign_team)
    before = log(campaign_team)[-1]
    assert before["role"] == "rewriting" and before["ladder"] is not None
    copy = folder_of(campaign_team) / "LADDER.json"
    assert copy.read_text() == before["ladder"]
    # Control: an edited copy and a planted file in the campaign folder never reach the next workspace.
    copy.write_text(json.dumps({"format": iteration_ladder.FORMAT, "rows": [{"class": "PLANTED"}]}))
    (folder_of(campaign_team) / "workspace-LADDER.json").write_text("PLANTED")
    summary = run(campaign_team, path, fixture, config, "--resume")
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    after = log(campaign_team)[-1]
    assert after["role"] == "rewriting" and "PLANTED" not in after["ladder"]
    assert after["ladder"] == before["ladder"]                    # the same state gives the same file
    assert len(ladder_rows(after["ladder"])) == len(summary["iterations"][0]["candidates"]) == 2
    assert summary["rewrite_workspace"] == "v2"


def test_a_resumed_v1_campaign_never_gains_a_ladder_and_a_summary_without_the_field_validates(campaign_team):
    path, fixture, config = paused(campaign_team)
    # A campaign started before the iteration ladder: its state names no workspace version.
    state_file = folder_of(campaign_team) / "state.json"
    state = json.loads(state_file.read_text())
    state.pop("rewrite_workspace")
    state_file.write_text(json.dumps(state, indent=2))
    summary = run(campaign_team, path, fixture, config, "--resume")
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    after = log(campaign_team)[-1]
    assert after["role"] == "rewriting" and after["ladder"] is None and "LADDER.json" not in after["files"]
    assert "FEEDBACK.json" in after["files"]
    assert summary["rewrite_workspace"] == "v1" and iteration_ladder.version_of(summary) == "v1"
    # An old summary (no `rewrite_workspace`) reads as v1 and still passes `swdb validate`.
    (team_summary,) = (campaign_team["records"] / "campaign_summaries").glob("*.yaml")
    data = yaml.safe_load(team_summary.read_text())
    data.pop("rewrite_workspace")
    team_summary.write_text(yaml.safe_dump(data, sort_keys=False))
    assert iteration_ladder.version_of(data) == "v1"
    result = run_swdb("validate", "--records", campaign_team["records"])
    assert result.returncode == 0, result.stdout + result.stderr
