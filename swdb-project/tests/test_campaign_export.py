"""Ticket 80: `swdb campaign-export` copies a candidate artifact's closure to the team store (spec review C17).

Created: 2026-10-05 ET. Runs a contract-fixture campaign; every number is a fixture, never evidence.
"""

import hashlib
import json
from pathlib import Path

import yaml

from conftest import run_swdb
from swdb.extensa_boundary import refusal
from swdb.store import Store
from testkit.extensa import CID, campaign_file, campaign_store, comparison, fixture_file, provider, run


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _export(team, path, *extra):
    result = run_swdb("campaign-export", path, "--records", team["records"], "--format", "json", *extra)
    return result, (json.loads(result.stdout) if result.returncode == 0 else None)


def _files(folder):
    return sorted(p.relative_to(folder) for p in folder.rglob("*.yaml"))


def test_campaign_export_copies_the_candidate_closure_byte_for_byte_with_tags(campaign_team):
    path = campaign_file(campaign_team, budgets={"provider_calls_setup": 0})
    fx = fixture_file(campaign_team, claim_runs=["it1.kronecker.a0.fork_scalar_tdstep.candidate-eval"])
    summary = run(campaign_team, path, fx, provider(campaign_team, {}))
    best = next(r["best"] for r in summary["per_class"] if r["class"] == "kronecker")
    team, store = campaign_team["records"], campaign_store(campaign_team)
    before = _files(team)
    result, dry = _export(campaign_team, path, "--candidate", best, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert dry["copied"] == 0 and any(r["action"] == "would_copy" for r in dry["records"])
    assert _files(team) == before                                         # a dry run writes nothing
    result, out = _export(campaign_team, path, "--candidate", best)
    assert result.returncode == 0, result.stderr
    copied = [r for r in out["records"] if r["action"] == "copied"]
    assert {"candidate", "certification", "evaluation", "comparison_result", "protocol", "retention",
            "team_claim"} <= {r["kind"] for r in copied}
    assert best in {r["id"] for r in copied} and out["claims"]
    for row in copied:
        assert _sha256(team / row["path"]) == _sha256(store / row["path"]) == row["sha256"]
        data = yaml.safe_load((team / row["path"]).read_text())
        assert data["mode"] == "extensa" and data["campaign"] == CID                  # tags kept
    # team inputs the campaign copied in are already in the team store, byte for byte
    assert all(r["mode"] is None for r in out["records"] if r["action"] == "present" and r["kind"] != "campaign_summary")
    assert run_swdb("validate", "--records", team).returncode == 0
    level = json.loads(run_swdb("candidate-level", best, "--records", team, "--format", "json").stdout)
    assert level["level"] == "certified" and level["promotion"] is None
    assert out["candidates"] == [{"id": best, "level": "certified", "promotion": None}]
    assert Path(out["receipt"]).is_file() and Path(out["receipt"]).parent == store.parent / "exports"
    # an unpromoted export stays outside team results (the boundary refuses it)
    assert "is not promoted" in refusal(Store(team), [best], command="compare-evaluations")
    # exporting again copies nothing
    result, again = _export(campaign_team, path, "--candidate", best)
    assert result.returncode == 0 and again["copied"] == 0 and "receipt" not in again


def test_campaign_export_refuses_different_bytes_and_unlisted_or_rejected_candidates(campaign_team):
    path = campaign_file(campaign_team, budgets={"provider_calls_setup": 0, "max_repairs": 0})
    numbers = {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)}
    rows = {"kronecker": {"certification": ["failed"], "comparisons": numbers},
            "uniform_random": {"comparisons": numbers}}
    summary = run(campaign_team, path, fixture_file(campaign_team, iterations=[rows]), provider(campaign_team, {}))
    by = {c["class"]: c for c in summary["iterations"][0]["candidates"]}
    assert by["kronecker"]["level"] == "rejected"
    result, _ = _export(campaign_team, path, "--candidate", by["kronecker"]["id"])
    assert result.returncode == 1 and "never promoted or exported" in result.stderr
    result, _ = _export(campaign_team, path, "--candidate", f"{CID}.it9.kronecker.a0")
    assert result.returncode == 1 and "not a candidate artifact" in result.stderr
    result, _ = _export(campaign_team, path)
    assert result.returncode == 2                                          # nothing named
    good = by["uniform_random"]["id"]
    team = campaign_team["records"]
    target = team / "candidates" / f"{good}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((campaign_store(campaign_team) / "candidates" / f"{good}.yaml").read_text() + "# edited\n")
    before = _files(team)
    result, _ = _export(campaign_team, path, "--candidate", good)
    assert result.returncode == 1 and "other bytes" in result.stderr and "nothing written" in result.stderr
    assert _files(team) == before
