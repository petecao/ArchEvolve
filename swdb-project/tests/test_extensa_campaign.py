"""Extensa campaigns on contract fixtures: skeleton, speed rule, selection, budgets.

Created: 2026-10-03 ET (tickets 52-54). Every provider is an external_fixture; every
number comes from the fixture file and is labeled contract_fixture, never evidence.
"""

import copy
import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb
from testkit.extensa import CID, CONTRACT, GEM5, PATCH, campaign_file, campaign_store, comparison, fixture_file, log, provider, records_of, rewrite, run


# --- ticket 52: file format and the skeleton ----------------------------------------

@pytest.mark.parametrize("changes, field", [
    ({"target": "dx100_gem5", "cid": GEM5, "protocol": {"repetitions": 10, "sources": [0]}}, "repetitions"),
    ({"target": "dx100_gem5", "cid": GEM5, "protocol": {"repetitions": 1, "sources": [0, 1]}}, "sources"),
    ({"protocol": {"repetitions": 4}}, "repetitions"),
    ({"protocol": {"region_pairs": True}}, "region_pairs"),
    ({"label": "all graphs"}, "label"),
    ({"budgets": {"max_iterations": 9}}, "budgets.max_iterations"),
    ({"budgets": {"lanes": 2}}, "budgets.lanes"),
])
def test_validate_refuses_every_d5_case(campaign_team, changes, field):
    changes = copy.deepcopy(changes)
    cid = changes.pop("cid", CID)
    target = changes.pop("target", "native_cpu")
    path = campaign_file(campaign_team, cid=cid, target=target, **changes)
    result = run_swdb("validate", "--records", campaign_team["records"])
    assert result.returncode == 1 and path.name in result.stderr and field in result.stderr, result.stderr


def test_validate_accepts_named_approvals(campaign_team):
    campaign_file(campaign_team, budgets={"max_iterations": 9, "lanes": 2},
                  approval={"by": "Yan-Ru Jhou", "date": "2026-10-03", "scope": "fixture",
                            "raised_budgets": ["max_iterations"], "two_lanes": True})
    result = run_swdb("validate", "--records", campaign_team["records"])
    assert result.returncode == 0, result.stderr


def test_campaign_without_fixture_uses_the_real_target_adapter(campaign_team):
    """Updated 2026-10-04 ET (tickets 56/57): without --fixture the target's real adapter runs;
    off mbit10 it stops before any provider call (its inputs or socket lane are unavailable)."""
    path = campaign_file(campaign_team)
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", provider(campaign_team, {}),
                      "--format", "json")
    summary = json.loads(result.stdout)
    assert summary["stop_reason"] == "infrastructure_failure" and summary["evidence_kind"] == "execution"
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0
    assert not (campaign_team["root"] / "provider-log.jsonl").exists()


def test_one_fixture_iteration_end_to_end(campaign_team):
    path = campaign_file(campaign_team)
    summary = run(campaign_team, path, fixture_file(campaign_team), provider(campaign_team, {}))
    store = campaign_store(campaign_team)
    team_ids = {p.stem for p in campaign_team["records"].rglob("*.yaml") if "campaign_summaries" not in p.parts}
    created = [yaml.safe_load(p.read_text()) for p in store.rglob("*.yaml") if p.stem not in team_ids]
    kinds = {r["kind"] for r in created}
    assert {"protocol", "candidate", "certification", "evaluation", "comparison_result", "retention",
            "campaign_summary"} <= kinds
    assert all(r.get("mode") == "extensa" and r.get("campaign") == CID for r in created)
    copies = [p for p in store.rglob("*.yaml") if p.stem in team_ids and "campaign_summaries" not in p.parts]
    assert copies and all("mode" not in yaml.safe_load(p.read_text()) for p in copies)
    # the summary is in both stores, tagged, and both stores validate
    team_summary = records_of(campaign_team["records"], "campaign_summaries")
    assert [s["id"] for s in team_summary] == [f"{CID}.summary"] and team_summary[0]["mode"] == "extensa"
    for folder in (store, campaign_team["records"]):
        result = run_swdb("validate", "--records", folder)
        assert result.returncode == 0, result.stderr
    (it,) = summary["iterations"]
    assert [c["class"] for c in it["candidates"]] == ["kronecker", "uniform_random"]
    assert all(c["level"] == "certified" and c["contracts"] == [CONTRACT] for c in it["candidates"])
    calls = summary["setup"]["provider_calls"] + it["provider_calls"]
    assert [c["role"] for c in calls] == ["profiling", "rewriting", "independent_test_generation"]
    assert all({"role", "model", "effort", "counted"} <= set(c) and c["counted"] for c in calls)
    assert calls[1]["model"] == "gpt-5.6-sol" and calls[1]["effort"] == "xhigh"
    assert summary["stop_reason"] == "max_iterations" and summary["evidence_kind"] == "contract_fixture"
    assert summary["label"] == "single graph per class"
    assert set(it["feedback_reasons"]) == {"certified", "verdict_gain"}


def test_second_iteration_workspace_holds_best_patches_and_feedback_only(campaign_team):
    path = campaign_file(campaign_team, budgets={"max_iterations": 2})
    run(campaign_team, path, fixture_file(campaign_team), provider(campaign_team, {}))
    rewrites = [entry for entry in log(campaign_team) if entry["role"] == "rewriting"]
    assert len(rewrites) == 2
    assert not any(f.startswith("best/") or f == "FEEDBACK.json" for f in rewrites[0]["files"])
    second = set(rewrites[1]["files"])
    assert {"best/kronecker.patch", "best/uniform_random.patch", "FEEDBACK.json", "REGIONS.json"} <= second
    assert not any("records" in f or "workload" in f or f.endswith(".sg") for f in second)


def test_campaign_synthesis_writes_an_experimental_entry_with_campaign_origin(campaign_team):
    library = campaign_team["root"] / "library"
    shutil.copytree(REPO / "library" / "library_operations", library / "library_operations")
    shutil.copytree(REPO / "library" / "profiles", library / "profiles")
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (library / folder).mkdir()
    good = ("#pragma once\n#include <cstddef>\nstruct SynthBackend {\n  template <typename ValueT, typename IndexT>\n"
            "  static void gather(ValueT* out, const ValueT* source, const IndexT* idx, std::size_t n, std::size_t m) {\n"
            "    (void)m; for (std::size_t i = 0; i < n; ++i) out[i] = source[(std::size_t)idx[i]];\n  }\n};\n")
    config = provider(campaign_team, {"rewriting": [rewrite(contracts=())],
                             "synthesis": [{"entry": {"name": "fixture", "summary": "fixture"}, "unresolved": [],
                                            "files": [{"path": "backends/synth_native_cpu_gather.hh",
                                                       "content": good}]}]})
    path = campaign_file(campaign_team, library={"allowed_tiers": ["experimental"], "contracts": [], "synthesize": ["gather"]},
                         budgets={"provider_calls_setup": 0})
    summary = run(campaign_team, path, fixture_file(campaign_team), config, "--library", library)
    (it,) = summary["iterations"]
    assert [c["role"] for c in it["provider_calls"]] == ["rewriting", "synthesis"]
    assert all(c["counted"] for c in it["provider_calls"])
    (added,) = summary["library_entries"]
    assert added["family"] == "gather" and added["state"] == "installed" and added["tier"] == "experimental"
    entry = yaml.safe_load(next((library / "library_operations" / "synthesized").rglob("entry.yaml")).read_text())
    assert entry["id"] == added["entry"] and entry["provenance"]["origin"]["campaign"] == CID
    certifications = [c for c in records_of(campaign_store(campaign_team), "certifications") if c["entry"]["id"] == added["entry"]]
    assert certifications and all(c["mode"] == "extensa" and c["campaign"] == CID for c in certifications)
    assert all(c["level"] == "uncertified" for c in it["candidates"])


# --- 2026-10-04 ET: final code review regressions ------------------------------------------------

LEAKY = PATCH.replace("+int alpha = 14;", "+int alpha = 14; // 2x speedup, 30% faster")


def test_repaired_patch_is_leakage_scanned_like_a_first_rewrite(campaign_team):
    row = {cls: {"certification": ["failed", "certified"],
                 "comparisons": {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)}}
           for cls in ("kronecker", "uniform_random")}
    config = provider(campaign_team, {"repair": [rewrite(patch=LEAKY)]})
    summary = run(campaign_team, campaign_file(campaign_team), fixture_file(campaign_team, iterations=[row]), config)
    candidates = summary["iterations"][0]["candidates"]
    assert candidates and all(c["level"] == "rejected" for c in candidates)
    # The first class receives the leaky repair; the per-iteration call budget leaves the
    # second class without a repair call, so it is rejected for its certification failure.
    assert candidates[0]["rejection"] == "The patch text states a performance outcome."
    assert candidates[1]["rejection"].startswith("Certification failed.")


def test_synthesis_usage_limit_pauses_uncounted_and_is_retried_on_resume(campaign_team):
    library = campaign_team["root"] / "library"
    shutil.copytree(REPO / "library" / "library_operations", library / "library_operations")
    shutil.copytree(REPO / "library" / "profiles", library / "profiles")
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (library / folder).mkdir()
    config = provider(campaign_team, {"rewriting": [rewrite(contracts=())], "synthesis": ["usage_limit"]})
    path = campaign_file(campaign_team, library={"allowed_tiers": ["experimental"], "contracts": [], "synthesize": ["gather"]},
                         budgets={"provider_calls_setup": 0})
    paused = run(campaign_team, path, fixture_file(campaign_team), config, "--library", library)
    assert paused["state"] == "paused" and paused["reason"] == "usage_limit"
    state = json.loads((campaign_store(campaign_team).parent / "state.json").read_text())
    assert "gather" not in state["synthesized"]
    (pause,) = state["pauses"]
    assert pause["provider_calls"][-1]["role"] == "synthesis" and pause["provider_calls"][-1]["counted"] is False
