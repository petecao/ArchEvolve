"""The query site finder (ticket 55) on BFS TDStep fixtures.

Created: 2026-10-04 ET. The fixture team store holds the repository's DX100 scalar BFS
implementation (statements index from ticket 35) and, where a test says so, legality facts
recorded as statement annotation facts. The library is the repository's, read only.
Updated 2026-10-05 ET (code review T4): the implementation, application and kernel records are
read as committed at a pinned commit (`testkit.pinned`), not from the live checkout.
"""

import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb import db, site_finder
from swdb.library_operations import pattern_key_problems
from testkit.extensa import campaign_file, campaign_store, fixture_file, log, provider, rewrite
from testkit.pinned import pinned_folder

READ = "contract.bfs_read_offload"
BC = "contract.bc_read_offload"
IMPL = "dx100-bfs-scalar"
READ_REGION = f"{IMPL}/TDStep:240-243"
LIBRARY = REPO / "library"
LEGALITY = ["L1", "L2", "L3", "L4", "L5", "chunk_size", "frontier_threshold", "schedule"]


def campaign(target, contracts=(READ,), tiers=("shared", "experimental")):
    return {"kernel": "gapbs-bfs", "target": target,
            "library": {"allowed_tiers": list(tiers), "contracts": list(contracts)}}


def implementation_path(records):
    return records / "implementations" / f"{IMPL}.yaml"


@pytest.fixture(scope="module")
def source_records(tmp_path_factory):
    """The repository records at the pinned evidence commit (ticket 57's legality facts included)."""
    return pinned_folder("records", tmp_path_factory.mktemp("pinned"))


def copy_without_facts(records, source):
    """The scalar TDStep implementation without its recorded facts (each test records its own).

    Updated 2026-10-04 ET: ticket 57 recorded the real legality facts in the repository."""
    data = yaml.safe_load((source / "implementations" / f"{IMPL}.yaml").read_text())
    for row in data["extensions"]["statements"]["annotations"]:
        row.pop("annotation_facts", None)
    implementation_path(records).write_text(yaml.safe_dump(data, sort_keys=False))


def bfs_records(root, source):
    """A records folder with the BFS application, kernel and the scalar TDStep implementation."""
    records = root / "records"
    for folder in ("applications", "kernels"):
        shutil.copytree(source / folder, records / folder, dirs_exist_ok=True)
    (records / "implementations").mkdir(parents=True, exist_ok=True)
    copy_without_facts(records, source)
    return records


def test_recorded_repository_facts_apply_the_read_offload_contract(tmp_path, source_records):
    """Ticket 57: the repository's evidence-cited legality facts select the gem5 region."""
    records = tmp_path / "records"
    for folder in ("applications", "kernels"):
        shutil.copytree(source_records / folder, records / folder, dirs_exist_ok=True)
    (records / "implementations").mkdir(parents=True, exist_ok=True)
    shutil.copy(source_records / "implementations" / f"{IMPL}.yaml", implementation_path(records))
    result = find(tmp_path, records, campaign("dx100_gem5"))
    assert [r["id"] for r in result["regions"]] == [READ_REGION]
    data = yaml.safe_load(implementation_path(records).read_text())
    facts = [f for r in data["extensions"]["statements"]["annotations"] for f in r.get("annotation_facts", [])
             if f["field"].startswith(f"legality:{READ}:")]
    assert sorted(f["field"].rsplit(":", 1)[1] for f in facts) == sorted(LEGALITY)
    assert all(f["value"] is True and f["basis"] in {"simulated", "reported"} for f in facts)
    cited = ("certification.1e4397e31d594245bc10bd80ff2107f5",
             "typed-library-bfs-gem5-20261003-a2.companion.diagnostic.evaluation", "contract.bfs_read_offload")
    assert all(any(c in f["evidence"] for c in cited) for f in facts)


def record_facts(records, facts, entry=READ):
    """facts: {clause: (statement, value)}; written as annotation facts with code_reading basis."""
    path = implementation_path(records)
    data = yaml.safe_load(path.read_text())
    rows = {r["id"]: r for r in data["extensions"]["statements"]["annotations"]}
    for clause, (statement, value) in facts.items():
        rows[statement].setdefault("annotation_facts", []).append(
            {"field": f"legality:{entry}:{clause}", "value": value, "basis": "code_reading",
             "evidence": f"fixture fact for {clause}"})
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def all_true(statement="bfs-td-neighbor"):
    return {clause: (statement, True) for clause in LEGALITY}


def find(tmp_path, records, data):
    return site_finder.find(records, data, library=LIBRARY, db_path=tmp_path / "finder.sqlite")


@pytest.fixture
def records(tmp_path, source_records):
    return bfs_records(tmp_path, source_records)


# --- gem5: the read-offload region ---------------------------------------------------------

def test_gem5_selects_the_read_offload_region_with_why(tmp_path, records):
    record_facts(records, all_true())
    result = find(tmp_path, records, campaign("dx100_gem5"))
    assert result["query_sha256"] == site_finder.QUERY_SHA256 and len(result["query_sha256"]) == 64
    (region,) = result["regions"]
    assert region["id"] == READ_REGION
    assert region["statements"] == ["bfs-td-frontier", "bfs-td-row-bounds", "bfs-td-neighbor", "bfs-td-parent-read"]
    assert region["source"] == {"path": "benchmarks/gapbs/src/bfs.cc",
                                "revision": "e4fc4afdf894f295442cef3604667a469fab8e62", "lines": [240, 243]}
    (app,) = region["applications"]
    assert app["entry"] == READ and app["contract"] == READ and app["kind"] == "rewrite_contract"
    assert [p["assigned"] for p in app["pattern_key"]] == [
        "td-frontier-read", "td-row-bounds-read", "td-neighbor-read", "td-parent-read"]
    assert app["pattern_key"][1]["patterns"] == ["td-row-bounds-read", "td-row-end-read"]
    assert sorted(c["clause"] for c in app["legality"]) == sorted(LEGALITY)
    assert all(c["holds"] for c in app["legality"])
    assert READ in region["reason"] and "8 legality clause(s) hold" in region["reason"]
    # library operations are plain CPU code: not bound to the DX100 target
    assert not any(r["entry"].startswith("operation.") for r in result["rejected"])


def test_results_are_deterministic(tmp_path, records):
    record_facts(records, all_true())
    first = find(tmp_path, records, campaign("dx100_gem5"))
    again = find(tmp_path, records, campaign("dx100_gem5"))
    rebuilt = site_finder.find(records, campaign("dx100_gem5"), library=LIBRARY, db_path=tmp_path / "other.sqlite")
    assert json.dumps(first, sort_keys=True) == json.dumps(again, sort_keys=True)
    assert first["regions"] == rebuilt["regions"] and first["rejected"] == rebuilt["rejected"]


def test_the_query_never_reads_library_yaml(tmp_path, records):
    record_facts(records, all_true())
    path = tmp_path / "finder.sqlite"
    library = tmp_path / "library"
    shutil.copytree(LIBRARY, library)
    db.build(records, path, library)
    expected = site_finder.assemble(site_finder.run_query(path, site_finder.parameters(campaign("dx100_gem5"))))
    shutil.rmtree(library)          # the index alone answers
    rows = site_finder.run_query(path, site_finder.parameters(campaign("dx100_gem5")))
    assert site_finder.assemble(rows) == expected and expected["regions"][0]["id"] == READ_REGION


# --- negative cases: pattern key matches, a legality clause fails ---------------------------

@pytest.mark.parametrize("change, clause, words", [
    ({"L3": ("bfs-td-neighbor", False)}, "L3", "recorded fact says it does not hold: bfs-td-neighbor (code_reading)"),
    ({"L5": None}, "L5", "no recorded fact"),
    ({"schedule": ("bfs-td-neighbor", "static")}, "schedule", "not true or false"),
    # a fact on a statement outside the region (the parent CAS, line 247) does not count
    ({"chunk_size": ("bfs-td-parent-cas", True)}, "chunk_size", "no recorded fact"),
])
def test_key_match_with_a_failing_legality_clause_is_not_applied(tmp_path, records, change, clause, words):
    facts = all_true()
    for name, fact in change.items():
        if fact is None:
            facts.pop(name)
        else:
            facts[name] = fact
    record_facts(records, facts)
    result = find(tmp_path, records, campaign("dx100_gem5"))
    assert result["regions"] == []
    (rejected,) = [r for r in result["rejected"] if r["entry"] == READ]
    assert rejected["region"] == READ_REGION
    assert [p["assigned"] for p in rejected["application"]["pattern_key"]] == [
        "td-frontier-read", "td-row-bounds-read", "td-neighbor-read", "td-parent-read"]
    failing = [c for c in rejected["application"]["legality"] if not c["holds"]]
    assert [c["clause"] for c in failing] == [clause] and words in failing[0]["reason"]
    assert f"{clause}: " in rejected["reason"]


def test_contradicting_facts_do_not_hold(tmp_path, records):
    record_facts(records, all_true())
    record_facts(records, {"L2": ("bfs-td-parent-read", False)})
    result = find(tmp_path, records, campaign("dx100_gem5"))
    assert result["regions"] == []
    (rejected,) = result["rejected"]
    assert "L2: recorded fact says it does not hold: bfs-td-parent-read" in rejected["reason"]


def test_no_fact_at_all_rejects_every_legality_clause(tmp_path, records):
    result = find(tmp_path, records, campaign("dx100_gem5"))
    (rejected,) = result["rejected"]
    assert result["regions"] == [] and all(not c["holds"] for c in rejected["application"]["legality"])
    assert len(rejected["application"]["legality"]) == len(LEGALITY)


def test_a_derived_contract_needs_its_own_facts(tmp_path, records):
    """BC's derived contract has the BFS pattern key, so it matches TDStep, but facts recorded
    for the parent's clauses are not facts about the derived contract's clauses."""
    record_facts(records, all_true())
    result = find(tmp_path, records, campaign("dx100_gem5", contracts=(READ, BC)))
    assert [a["entry"] for r in result["regions"] for a in r["applications"]] == [READ]
    (bc,) = [r for r in result["rejected"] if r["entry"] == BC]
    assert bc["region"] == READ_REGION and "BC-L1: no recorded fact" in bc["reason"]


def test_contracts_outside_the_campaign_or_its_tiers_are_not_considered(tmp_path, records):
    record_facts(records, all_true())
    assert find(tmp_path, records, campaign("dx100_gem5", contracts=()))["regions"] == []
    # without review records every entry is experimental
    assert find(tmp_path, records, campaign("dx100_gem5", tiers=("shared",)))["regions"] == []


# --- native: the library-operation regions ----------------------------------------------------

def test_native_selects_library_operation_regions(tmp_path, records):
    record_facts(records, all_true())
    result = find(tmp_path, records, campaign("native_cpu"))
    assert [r["id"] for r in result["regions"]] == [f"{IMPL}/TDStep:240-241", f"{IMPL}/TDStep:241-241"]
    staging, regroup = result["regions"]
    (app,) = staging["applications"]
    assert app["entry"] == "operation.gather_staging_executor" and app["contract"] is None
    assert [p["assigned"] for p in app["pattern_key"]] == ["td-frontier-read", "td-row-bounds-read"]
    assert app["legality"] == [] and "declares no legality clause" in staging["reason"]
    (app,) = regroup["applications"]
    assert app["entry"] == "operation.regroup_executor"
    # two key patterns need two distinct access patterns: row start and row end
    assert [p["assigned"] for p in app["pattern_key"]] == ["td-row-bounds-read", "td-row-end-read"]
    rejected = {r["entry"]: r["reason"] for r in result["rejected"]}
    assert "add_update" in rejected["operation.update_binning_executor"]
    assert "offsets:stream > target:ranged_indirect" in rejected["operation.vertex_relabel_executor"]
    # the DX100 contract is bound to the DX100 target, never to native CPU
    assert READ not in rejected and all(a["entry"] != READ for r in result["regions"] for a in r["applications"])


def test_a_key_needing_more_distinct_patterns_than_the_region_has_is_rejected(tmp_path, records):
    """Removing the row-end pattern leaves one access pattern for regroup's two key patterns."""
    path = implementation_path(records)
    data = yaml.safe_load(path.read_text())
    data["access_patterns"] = [p for p in data["access_patterns"] if p["id"] != "td-row-end-read"]
    for row in data["extensions"]["statements"]["annotations"]:
        row["access_pattern_steps"] = [s for s in row["access_pattern_steps"] if s["pattern"] != "td-row-end-read"]
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = find(tmp_path, records, campaign("native_cpu"))
    assert [r["id"] for r in result["regions"]] == [f"{IMPL}/TDStep:240-241"]
    (regroup,) = [r for r in result["rejected"] if r["entry"] == "operation.regroup_executor"]
    assert "no distinct access patterns" in regroup["reason"]


# --- pattern-key chain form ---------------------------------------------------------------------

def test_pattern_keys_must_be_chains():
    old_form = [{"roles": ["index", "target"], "address_shapes": ["single_valued_indirect"], "update_kind": "read"}]
    assert any("one role per address shape" in why for _where, why in pattern_key_problems(old_form))
    no_offsets = [{"roles": ["index", "target"], "address_shapes": ["stream", "ranged_indirect"], "update_kind": "read"}]
    assert any("role offsets" in why for _where, why in pattern_key_problems(no_offsets))
    early_target = [{"roles": ["target", "index"], "address_shapes": ["stream", "stream"], "update_kind": "read"}]
    assert len(pattern_key_problems(early_target)) == 2
    for path in sorted((LIBRARY / "library_operations").glob("*.yaml")):
        assert pattern_key_problems(yaml.safe_load(path.read_text()).get("pattern_key")) == []


# --- `swdb campaign` with `regions: query` --------------------------------------------------

def add_bfs_implementation(campaign_team, facts, source):
    copy_without_facts(campaign_team["records"], source)
    if facts:
        record_facts(campaign_team["records"], facts)


def test_campaign_with_query_regions_records_why(campaign_team, source_records):
    add_bfs_implementation(campaign_team, all_true(), source_records)
    path = campaign_file(campaign_team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query")
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", provider(campaign_team, {}),
                      "--fixture", fixture_file(campaign_team), "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    summary = json.loads(result.stdout)
    assert summary["site_finder"]["query_sha256"] == site_finder.QUERY_SHA256
    assert summary["site_finder"]["parameters"]["target"] == "dx100_gem5"
    (it,) = summary["iterations"]
    (region,) = it["regions"]
    assert region["id"] == READ_REGION and READ in region["reason"]
    (app,) = region["why"]["applications"]
    assert app["contract"] == READ and region["why"]["statements"][-1] == "bfs-td-parent-read"
    assert it["site_finder"]["query_sha256"] == site_finder.QUERY_SHA256
    assert all(c["level"] == "certified" for c in it["candidates"])
    store = campaign_store(campaign_team, "extensa-gem5-bfs-20261004-a1")
    for folder in (store, campaign_team["records"]):
        checked = run_swdb("validate", "--records", folder)
        assert checked.returncode == 0, checked.stderr
    workspace = json.loads((store.parent / "state.json").read_text())
    assert workspace["site_finder"]["query_sha256"] == site_finder.QUERY_SHA256


def test_native_campaign_keeps_library_operations_out_of_regions_json_with_a_reason(campaign_team, source_records):
    """Ticket 80 (C15, 2026-10-05 ET): native a8's iteration 2 named a library operation offered in REGIONS.json and
    was refused. Library operations stay out of REGIONS.json until candidates can use them; the region stays."""
    add_bfs_implementation(campaign_team, None, source_records)
    config = provider(campaign_team, {"rewriting": [rewrite(contracts=())]})
    path = campaign_file(campaign_team, regions="query", budgets={"provider_calls_setup": 0},
                         library={"allowed_tiers": ["shared", "experimental"], "contracts": []})
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", config,
                      "--fixture", fixture_file(campaign_team), "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    (it,) = json.loads(result.stdout)["iterations"]
    # the site finder's own record is unchanged: it chose the regions because library operations match there
    assert sorted(r["id"] for r in it["regions"]) == [f"{IMPL}/TDStep:240-241", f"{IMPL}/TDStep:241-241"]
    assert {a["kind"] for r in it["regions"] for a in r["why"]["applications"]} == {"library_operation"}
    excluded = it["site_finder"]["excluded"]
    assert sorted(e["entry"] for e in excluded) == ["operation.gather_staging_executor", "operation.regroup_executor"]
    assert all("not yet usable in candidate artifacts" in e["reason"] for e in excluded)
    (call,) = [entry for entry in log(campaign_team) if entry["role"] == "rewriting"]
    offered = call["regions"]["regions"]
    assert sorted(r["id"] for r in offered) == [f"{IMPL}/TDStep:240-241", f"{IMPL}/TDStep:241-241"]
    assert all(r["applications"] == [] for r in offered)
    assert "operation." not in json.dumps(call["regions"])
    assert all(c["level"] == "uncertified" for c in it["candidates"])


def test_campaign_rejects_a_contract_the_site_finder_did_not_apply(campaign_team, source_records):
    add_bfs_implementation(campaign_team, all_true(), source_records)
    config = provider(campaign_team, {"rewriting": [rewrite(contracts=(BC,))]})
    path = campaign_file(campaign_team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query",
                         library={"allowed_tiers": ["shared", "experimental"], "contracts": [READ, BC]})
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", config,
                      "--fixture", fixture_file(campaign_team), "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    (it,) = json.loads(result.stdout)["iterations"]
    assert all(c["level"] == "rejected" and "applies to no region the site finder chose" in c["rejection"]
               for c in it["candidates"])
    assert any("BC-L1: no recorded fact" in r["reason"] for r in it["site_finder"]["rejected"])


def test_campaign_refuses_when_the_query_chooses_no_region(campaign_team, source_records):
    add_bfs_implementation(campaign_team, {k: v for k, v in all_true().items() if k != "L4"}, source_records)
    path = campaign_file(campaign_team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query")
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", provider(campaign_team, {}),
                      "--fixture", fixture_file(campaign_team), "--format", "json")
    assert result.returncode != 0
    assert "regions: query chose no region" in result.stderr and "L4: no recorded fact" in result.stderr
    assert not (campaign_team["root"] / "provider-log.jsonl").exists()


# --- order by the latest attribution report's ranking (fine-grained attribution ticket 10) ----
# Created 2026-10-11 ET. Spec F20/F23, seam 2. The reports are hand-written fixture attribution
# records (never evidence); only the fields the SQLite index reads are filled in.

STAGING, REGROUP = f"{IMPL}/TDStep:240-241", f"{IMPL}/TDStep:241-241"


def attribution_report(records, rid, ranked, *, verdict="passed", created="2026-10-11",
                       kernel="gapbs-bfs", target="native_cpu"):
    """A report whose ranking lists one candidate region per site-finder region in `ranked`, best
    first. `verdict` None leaves `split_check` out (not checked)."""
    rows = [{"side": "candidate", "region": f"cand.{i}", "origin": "agent_rewritten", "reason": "fixture",
             "path": "bfs.cc", "lines": [240, 241], "seconds": 1.0, "sites": [], "mixed": False,
             "matched_region": None, "headroom": [],
             "resource_floor": {"seconds": None, "limiting_term": None, "missing": []},
             "catalog_bound": {"seconds": None, "entry": None, "reason": "no_catalog_match", "mixed": False,
                               "site_finder_regions": [sf], "entries": [], "missing": []}}
            for i, sf in enumerate(ranked)]
    data = {"kind": "attribution", "schema_version": "0.4", "id": rid, "status": "draft",
            "created": created, "updated": created,
            "baseline_estimate": {"id": "fixture.baseline"}, "candidate_estimate": {"id": "fixture.candidate"},
            "baseline_source": {"id": "fixture.baseline.source"}, "candidate_source": {"id": "fixture.candidate.source"},
            "target_description": {"id": "fixture.target", "sha256": "0" * 64},
            "input": "fixture-input", "threads": 1, "evidence_kind": "contract_fixture",
            "site_finder": {"campaign_summary": {"id": "fixture.summary", "sha256": "0" * 64}, "iteration": 1,
                            "query_sha256": None, "kernel": kernel, "target": target, "regions": []},
            "regions": rows, "groups": [],
            "whole_program": {"baseline_seconds": None, "candidate_seconds": None, "total_speedup": None,
                              "amdahl_ceiling": None, "unattributed_flagged": None},
            "ranking": [{"position": i, "side": "candidate", "region": r["region"], "tier": "floor_headroom",
                         "limit": "resource_floor", "value": float(len(rows) - i), "reason": None}
                        for i, r in enumerate(rows, start=1)]}
    if verdict is not None:
        data["split_check"] = {"verdict": verdict}
    path = records / "attributions" / f"{rid}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def native(tmp_path, records, name):
    return site_finder.find(records, campaign("native_cpu"), library=LIBRARY, db_path=tmp_path / f"{name}.sqlite")


def test_a_passed_report_orders_regions_by_its_ranking_and_changes_nothing_else(tmp_path, records):
    today = native(tmp_path, records, "today")
    assert [r["id"] for r in today["regions"]] == [STAGING, REGROUP]
    attribution_report(records, "fixture.attribution", [REGROUP])
    ranked = native(tmp_path, records, "ranked")
    # the ranked region first; an unranked one keeps today's relative order after it
    assert [r["id"] for r in ranked["regions"]] == [REGROUP, STAGING]
    assert ranked["ordering"] == {"attribution": "fixture.attribution", "split_check": "passed", "applied": True,
                                  "rule": site_finder.ORDERING_RULE}
    # eligibility, legality and recorded reasons are unchanged: only the order moved
    assert sorted(ranked["regions"], key=lambda r: r["id"]) == sorted(today["regions"], key=lambda r: r["id"])
    assert ranked["rejected"] == today["rejected"]
    assert sorted(site_finder.region_rows(ranked), key=lambda r: r["id"]) == site_finder.region_rows(today)


@pytest.mark.parametrize("verdict", ["split_unverified", None])
def test_an_unverified_or_unchecked_report_keeps_todays_order_byte_identical(tmp_path, records, verdict):
    today = native(tmp_path, records, "today")
    attribution_report(records, "fixture.attribution", [REGROUP], verdict=verdict)
    kept = native(tmp_path, records, "kept")
    assert json.dumps(site_finder.region_rows(kept)) == json.dumps(site_finder.region_rows(today))
    assert json.dumps(kept["regions"]) == json.dumps(today["regions"]) and kept["rejected"] == today["rejected"]
    assert kept["ordering"]["attribution"] == "fixture.attribution" and kept["ordering"]["applied"] is False
    assert kept["ordering"]["split_check"] == verdict


def test_without_a_report_the_order_is_todays(tmp_path, records):
    result = native(tmp_path, records, "none")
    assert [r["id"] for r in result["regions"]] == [STAGING, REGROUP]
    assert result["ordering"] == {"attribution": None, "split_check": None, "applied": False,
                                  "rule": site_finder.ORDERING_RULE}


def test_only_the_latest_report_for_the_campaigns_kernel_and_target_counts(tmp_path, records):
    # an older passed report is superseded by a newer unverified one: today's order, no fallback
    attribution_report(records, "fixture.old", [REGROUP], created="2026-10-10")
    attribution_report(records, "fixture.new", [REGROUP], verdict="split_unverified", created="2026-10-11")
    # newer reports for another target or kernel are never read
    attribution_report(records, "fixture.gem5", [REGROUP], created="2026-10-12", target="dx100_gem5")
    attribution_report(records, "fixture.other", [REGROUP], created="2026-10-12", kernel="gapbs-bc")
    result = native(tmp_path, records, "latest")
    assert result["ordering"]["attribution"] == "fixture.new"
    assert [r["id"] for r in result["regions"]] == [STAGING, REGROUP]


def test_reports_created_on_the_same_date_are_broken_by_the_greatest_id(tmp_path, records):
    attribution_report(records, "fixture.a", [STAGING])
    attribution_report(records, "fixture.b", [REGROUP])
    result = native(tmp_path, records, "tie")
    assert result["ordering"]["attribution"] == "fixture.b"
    assert [r["id"] for r in result["regions"]] == [REGROUP, STAGING]


#: sha256 of the rewriting role's prompt.txt in the native query campaign below, pinned before
#: ticket 10 changed the site finder (2026-10-11 ET). The ranking reaches the agent only as order.
#: A campaign with a report in its team store needs a valid report, which needs ticket 09's
#: `split_check` schema; until then the order is checked through `site_finder.find` above.
REWRITE_PROMPT_SHA256 = "8b6f410943238b3f2b67330bb3eb1468cb47a49da28a2c2f90588ebef5aa9979"


def test_campaign_without_a_report_keeps_todays_order_and_the_rewrite_prompt_is_unchanged(campaign_team, source_records):
    import hashlib
    add_bfs_implementation(campaign_team, None, source_records)
    config = provider(campaign_team, {"rewriting": [rewrite(contracts=())]})
    path = campaign_file(campaign_team, regions="query", budgets={"provider_calls_setup": 0},
                         library={"allowed_tiers": ["shared", "experimental"], "contracts": []})
    result = run_swdb("campaign", path, "--records", campaign_team["records"], "--provider-config", config,
                      "--fixture", fixture_file(campaign_team), "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    (call,) = [entry for entry in log(campaign_team) if entry["role"] == "rewriting"]
    assert [r["id"] for r in call["regions"]["regions"]] == [STAGING, REGROUP]
    (it,) = json.loads(result.stdout)["iterations"]
    assert sorted(r["id"] for r in it["regions"]) == [STAGING, REGROUP]
    prompts = sorted(campaign_team["root"].rglob("prompt.txt"))
    assert len(prompts) == 1 and "Agent role: extensa_rewriting." in prompts[0].read_text()
    digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in prompts}
    assert digests == {REWRITE_PROMPT_SHA256}
