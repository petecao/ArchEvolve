"""The query site finder (ticket 55) on BFS TDStep fixtures.

Created: 2026-10-04 ET. The fixture team store holds the repository's DX100 scalar BFS
implementation (statements index from ticket 35) and, where a test says so, legality facts
recorded as statement annotation facts. The library is the repository's, read only.
"""

import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb import db, site_finder
from swdb.library_operations import pattern_key_problems
from test_bfs_protocol import protocol_seed  # noqa: F401
from test_extensa_campaign import (campaign_file, campaign_store, fixture_file, provider, rewrite,  # noqa: F401
                                   team, team_seed)

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


def bfs_records(root):
    """A records folder with the BFS application, kernel and the scalar TDStep implementation."""
    records = root / "records"
    for folder in ("applications", "kernels"):
        shutil.copytree(REPO / "records" / folder, records / folder, dirs_exist_ok=True)
    (records / "implementations").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "records" / "implementations" / f"{IMPL}.yaml", implementation_path(records))
    return records


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
def records(tmp_path):
    return bfs_records(tmp_path)


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

def add_bfs_implementation(team, facts):
    shutil.copy(REPO / "records" / "implementations" / f"{IMPL}.yaml", implementation_path(team["records"]))
    if facts:
        record_facts(team["records"], facts)


def test_campaign_with_query_regions_records_why(team):
    add_bfs_implementation(team, all_true())
    path = campaign_file(team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query")
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", provider(team, {}),
                      "--fixture", fixture_file(team), "--format", "json")
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
    store = campaign_store(team, "extensa-gem5-bfs-20261004-a1")
    for folder in (store, team["records"]):
        checked = run_swdb("validate", "--records", folder)
        assert checked.returncode == 0, checked.stderr
    workspace = json.loads((store.parent / "state.json").read_text())
    assert workspace["site_finder"]["query_sha256"] == site_finder.QUERY_SHA256


def test_campaign_rejects_a_contract_the_site_finder_did_not_apply(team):
    add_bfs_implementation(team, all_true())
    config = provider(team, {"rewriting": [rewrite(contracts=(BC,))]})
    path = campaign_file(team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query",
                         library={"allowed_tiers": ["shared", "experimental"], "contracts": [READ, BC]})
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", config,
                      "--fixture", fixture_file(team), "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    (it,) = json.loads(result.stdout)["iterations"]
    assert all(c["level"] == "rejected" and "applies to no region the site finder chose" in c["rejection"]
               for c in it["candidates"])
    assert any("BC-L1: no recorded fact" in r["reason"] for r in it["site_finder"]["rejected"])


def test_campaign_refuses_when_the_query_chooses_no_region(team):
    add_bfs_implementation(team, {k: v for k, v in all_true().items() if k != "L4"})
    path = campaign_file(team, cid="extensa-gem5-bfs-20261004-a1", target="dx100_gem5", regions="query")
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", provider(team, {}),
                      "--fixture", fixture_file(team), "--format", "json")
    assert result.returncode != 0
    assert "regions: query chose no region" in result.stderr and "L4: no recorded fact" in result.stderr
    assert not (team["root"] / "provider-log.jsonl").exists()
