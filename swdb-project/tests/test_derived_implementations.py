"""Derived implementations: a certified enabling rewrite's result, its lineage and per-rewrite links.

Created: 2026-10-14 ET (Probata proof of concept, ticket 19). Every campaign here is a contract-fixture
campaign (`swdb campaign --fixture`): certifications, comparisons and proof records are fixtures,
never evidence. The fixture's base snapshot is the seeded `test-source` snapshot of upstream GAPBS
(`gapbs-bfs-do`); fixture patches edit its `src/bfs.cc`. Contract fixtures only; no held-out kernel.
"""

import difflib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb import campaign as campaign_module
from swdb import provider_roles
from swdb.library import Library
from testkit.record_subset import copy_record_subset
from testkit.extensa import campaign_file, campaign_store, comparison, fixture_file, log, provider, records_of, rewrite
from testkit.extensa import run as run_fixture

STAGING = "contract.bfs_tdstep_frontier_staging"     # enabling: packing and loop tiling, no offload
READ = "contract.bfs_read_offload"                    # offloads
LIBRARY = REPO / "library"
BASE_SNAPSHOT = "test-source"
BASE_IMPL = "gapbs-bfs-do"
ORIGINAL = (REPO / "apps/gapbs/src/bfs.cc").read_text()


def edit(before, after, text=ORIGINAL):
    """A -p1 patch of src/bfs.cc replacing one fragment (the fixture provider returns it as is)."""
    changed = text.replace(before, after, 1)
    assert changed != text, before
    return "".join(difflib.unified_diff(text.splitlines(keepends=True), changed.splitlines(keepends=True),
                                        fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))


ALPHA = edit("int alpha = 15", "int alpha = 14")
AFTER_ALPHA = ORIGINAL.replace("int alpha = 15", "int alpha = 14", 1)
BETA = edit("int beta = 18", "int beta = 17", AFTER_ALPHA)                 # applies to D1's snapshot only
AFTER_BETA = AFTER_ALPHA.replace("int beta = 18", "int beta = 17", 1)
GAMMA = edit("scout_count > edges_to_check / alpha", "scout_count >= edges_to_check / alpha", AFTER_BETA)
CID = "extensa-native-bfs-20261004-a1"
D1 = f"{CID}.it1.kronecker.a0.derived"
D2 = f"{CID}.it2.kronecker.a0.derived"
FINAL = f"{CID}.it3.kronecker.a0"


def step(contracts, patch, start=None):
    """A rewrite answer of a campaign that lists derived starts (the role then names `start`)."""
    return {**rewrite(contracts=contracts, patch=patch), "start": start}


@pytest.fixture
def team(campaign_team):
    """The seeded campaign team store plus the strategy records of the contracts used (record closure)."""
    copy_record_subset(REPO / "records", campaign_team["records"], ["packing", "loop_tiling", "dx100_read_offload"])
    return campaign_team


@pytest.fixture(scope="module")
def staging_library(tmp_path_factory):
    """A library holding only the enabling contract and the files it cites (byte copies, same hashes).

    The campaign store holds no intrinsic or operation records, so the whole repository library cannot
    validate against it; lineage checks need only the contracts a lineage names."""
    root = tmp_path_factory.mktemp("staging-library") / "library"
    (root / "rewrite_contracts").mkdir(parents=True)
    shutil.copy(LIBRARY / "rewrite_contracts" / "bfs_tdstep_frontier_staging.yaml", root / "rewrite_contracts")
    for folder in ("profiles", "native", "dx100", "library_operations/reference"):
        shutil.copytree(LIBRARY / folder, root / folder)
    (root / "methods").mkdir()               # the contract-fixture method version `swdb prove` pins (ticket 11)
    shutil.copy(REPO / "tests" / "fixtures" / "proof" / "methods" / "contract-fixture-1.yaml", root / "methods")
    return root


def validate(store, library):
    return run_swdb("validate", "--records", store, "--library", library)


def derived_fixture(team, **changes):
    """The fixture file with the base snapshot every derived implementation's chain starts from."""
    return fixture_file(team, base_snapshot=BASE_SNAPSHOT, **changes)


def campaign(team, plan, *, contracts=(STAGING,), starts=None, iterations=1, fixture_changes=None, **budgets):
    path = campaign_file(team, library={"contracts": list(contracts)},
                         budgets={"max_iterations": iterations, **budgets},
                         **({"derived_starts": list(starts)} if starts else {}))
    summary = run_fixture(team, path, derived_fixture(team, **(fixture_changes or {})), provider(team, plan))
    return summary, campaign_store(team)


def fixture_rows(*outcomes):
    """Fixture iteration rows: per iteration, the certification outcome of both classes' attempts."""
    rows = []
    for outcome in outcomes:
        row = {"comparisons": {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)},
               "certification": [outcome]}
        rows.append({"kronecker": dict(row), "uniform_random": dict(row)})
    return rows


def implementations(store):
    return {r["id"]: r for r in records_of(store, "implementations")}


def entries(summary, index=0):
    return {e["class"]: e for e in summary["iterations"][index]["candidates"]}


# --- the record -------------------------------------------------------------------------------

def test_a_certified_enabling_rewrite_yields_a_derived_implementation(team, staging_library):
    summary, store = campaign(team, {"rewriting": [rewrite(contracts=[STAGING], patch=ALPHA)]})
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    kron = entries(summary)["kronecker"]
    assert kron["level"] == "certified"
    derived = implementations(store)[kron["derived_implementation"]]
    assert derived["origin"]["kind"] == "derived" and derived["origin"]["derived_from"] == BASE_IMPL
    assert derived["kernel"] == "gapbs-bfs"
    # the contract's strategies, in the contract's order (packing, then loop tiling)
    assert [a["strategy"] for a in derived["applies"]] == ["packing", "loop_tiling"]
    assert derived["contract_lineage"] == [
        {"contract": STAGING, "version": None, "content_sha256": Library(LIBRARY).content_sha256(STAGING)}]
    checked = validate(store, staging_library)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    built = run_swdb("build", "--records", store, "--db", store.parent / "research.sqlite")
    assert built.returncode == 0, built.stderr


# --- negative controls for the record ---------------------------------------------------------

def test_rejected_uncertified_and_offloading_results_yield_no_derived_implementation(team):
    plan = {"rewriting": [rewrite(contracts=[STAGING], patch=ALPHA),         # certification fails, no repair
                          rewrite(contracts=[], patch=ALPHA),                # uncertified: no contract
                          rewrite(contracts=[READ], patch=ALPHA),            # certified, but it offloads
                          rewrite(contracts=[STAGING, READ], patch=ALPHA)]}  # not every contract enabling
    summary, store = campaign(team, plan, contracts=(STAGING, READ), iterations=4, plateau_iterations=4,
                              max_repairs=0,
                              fixture_changes={"iterations": fixture_rows("failed", "certified", "certified",
                                                                          "certified")})
    levels = [[e["level"] for e in row["candidates"]] for row in summary["iterations"]]
    assert levels == [["rejected"] * 2, ["uncertified"] * 2, ["certified"] * 2, ["certified"] * 2]
    assert not any(e.get("derived_implementation") for row in summary["iterations"] for e in row["candidates"])
    assert not [i for i in implementations(store).values() if i["origin"]["kind"] == "derived"]


# --- iteration start: controls ----------------------------------------------------------------

def control_implementation(team, rid, **changes):
    """A hand-made derived implementation in the team store (no rewrite links: never certified)."""
    data = yaml.safe_load((REPO / "records" / "implementations" / f"{BASE_IMPL}.yaml").read_text())
    data.update(id=rid, origin={"kind": "derived", "description": "Control fixture: never certified.",
                                "derived_from": None},
                verification={"status": "unchecked", "evidence": [], "scope": "Control fixture."})
    data.update(changes)
    (team["records"] / "implementations" / f"{rid}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))


def test_an_iteration_may_start_only_from_a_listed_certified_derived_implementation_of_the_kernel(team):
    copy_record_subset(REPO / "records", team["records"], ["gapbs-pr"])
    control_implementation(team, "control-other-kernel", kernel="gapbs-pr", source_baseline="gapbs-pr-gs")
    control_implementation(team, "control-uncertified", origin={
        "kind": "derived", "description": "Control fixture: never certified.", "derived_from": BASE_IMPL})
    stale = edit("int beta = 18", "int beta = 17")            # written against the base source, not D1's
    plan = {"rewriting": [step([STAGING], ALPHA), step([STAGING], ALPHA, "control-other-kernel"),
                          step([STAGING], ALPHA, "control-uncertified"), step([STAGING], ALPHA, "not-listed"),
                          step([STAGING], stale, D1)]}
    summary, _store = campaign(team, plan, starts=("control-other-kernel", "control-uncertified", D1), iterations=5,
                               plateau_iterations=4, max_repairs=0)
    reasons = [entries(summary, i)["kronecker"].get("rejection") for i in range(5)]
    assert reasons[0] is None and entries(summary, 0)["kronecker"]["derived_implementation"] == D1
    assert "implements kernel gapbs-pr, not the campaign's kernel gapbs-bfs" in reasons[1]
    assert "is not a certified derived implementation: it has no certification record" in reasons[2]
    assert "is not one of the campaign file's derived_starts" in reasons[3]
    assert "The patch does not apply to the start's source" in reasons[4]
    for i in (1, 2, 3, 4):
        assert all(e["level"] == "rejected" for e in entries(summary, i).values())


# --- a rewrite chain: baseline -> D1 -> D2 -> final candidate artifact --------------------------

@pytest.fixture(scope="module")
def chain(campaign_team_seed, tmp_path_factory):
    """One fixture campaign, read by several tests (copy the store before changing it).

    Iteration 1 rewrites the base source with the enabling contract (D1); iteration 2 starts from D1 with
    the enabling contract again (D2); iteration 3 starts from D2 with the offloading contract (the final
    candidate artifact)."""
    root = tmp_path_factory.mktemp("chain")
    records = root / "records"
    shutil.copytree(campaign_team_seed["records"], records)
    team = {**campaign_team_seed, "records": records, "root": root}
    copy_record_subset(REPO / "records", records, ["packing", "loop_tiling", "dx100_read_offload"])
    plan = {"rewriting": [step([STAGING], ALPHA), step([STAGING], BETA, D1), step([READ], GAMMA, D2)]}
    summary, store = campaign(team, plan, contracts=(STAGING, READ), starts=(D1, D2), iterations=3,
                              fixture_changes={"iterations": fixture_rows("certified", "certified", "certified")})
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    return {"team": team, "summary": summary, "store": store}


def record(store, kind, rid):
    return yaml.safe_load((store / kind / f"{rid}.yaml").read_text())


def test_the_rewrite_role_sees_each_certified_start_and_names_its_start(chain):
    calls = [e for e in log(chain["team"]) if e["role"] == "rewriting"]
    assert "STARTS.json" not in calls[0]["files"]                     # no listed start exists yet
    assert {"STARTS.json", f"starts/{D1}/src/bfs.cc"} <= set(calls[1]["files"])
    assert f"starts/{D2}/src/bfs.cc" in calls[2]["files"]
    rewriting = campaign_module._roles(starts=True)["rewriting"].output_schema
    assert "start" in rewriting["required"] and "start" not in campaign_module._roles()["rewriting"].output_schema["required"]
    assert provider_roles.strict_problems(provider_roles.wire_schema(rewriting)) == []


def test_an_iteration_starts_from_a_certified_derived_implementation(chain):
    store = chain["store"]
    second = entries(chain["summary"], 1)
    for cls, entry in second.items():
        assert entry["start"] == D1 and entry["level"] == "certified"
        candidate = record(store, "candidates", entry["id"])
        assert candidate["source_snapshot"] == f"{D1}.source"           # built on D1's snapshot
        text = (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
        assert "int alpha = 14, int beta = 17" in text                   # D1's change and this patch


def test_a_derived_implementation_of_a_derived_implementation_carries_the_full_lineage(chain):
    store = chain["store"]
    pin = Library(LIBRARY).content_sha256(STAGING)
    d2 = record(store, "implementations", D2)
    assert entries(chain["summary"], 1)["kronecker"]["derived_implementation"] == D2
    assert d2["origin"]["derived_from"] == D1
    assert d2["contract_lineage"] == [{"contract": STAGING, "version": None, "content_sha256": pin}] * 2
    assert [a["strategy"] for a in d2["applies"]] == ["packing", "loop_tiling"] * 2
    (link,) = d2["rewrite_links"]
    assert link["predecessor_snapshot"]["id"] == f"{D1}.source"
    assert link["result"]["candidate"] == f"{CID}.it2.kronecker.a0"


def test_a_candidate_on_a_derived_implementation_is_certified_against_its_snapshot_and_the_root_baseline(chain):
    store, final = chain["store"], entries(chain["summary"], 2)["kronecker"]
    assert final["id"] == FINAL and final["start"] == D2 and final["level"] == "certified"
    assert "derived_implementation" not in final                      # it offloads: a final candidate artifact
    (link,) = final["certification"]["records"]                       # one contract, one run
    certification = record(store, "certifications", link["record"])
    assert certification["command"]["contracts"] == [READ] and certification["command"]["start"] == D2
    assert record(store, "candidates", FINAL)["source_snapshot"] == f"{D2}.source"
    (root_check,) = [c for c in certification["matrix"] if c["cell"] == "root_baseline_correctness"]
    assert root_check["baseline"] == BASE_IMPL and root_check["status"] == "passed"


def copied(chain, tmp_path):
    """A copy of the chain's store (its records-folder code files included) for one test to change."""
    store = tmp_path / "records"
    shutil.copytree(chain["store"], store, ignore=shutil.ignore_patterns("*.sqlite", ".swdb.lock"))
    return store


def change(store, rid, edit_record, kind="implementations"):
    path = store / kind / f"{rid}.yaml"
    data = yaml.safe_load(path.read_text())
    edit_record(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_validate_accepts_the_chain_and_refuses_broken_lineages_and_links(chain, tmp_path, staging_library):
    checked = validate(copied(chain, tmp_path / "ok"), staging_library)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    final_record = entries(chain["summary"], 2)["kronecker"]["certification"]["record"]
    d1_record = record(chain["store"], "implementations", D1)["rewrite_links"][0]["certification"]
    cases = {
        "missing": (lambda d: d["contract_lineage"][0].update(contract="contract.no_such_contract"),
                    "names contract contract.no_such_contract, which the library does not hold"),
        "skipped": (lambda d: d.update(contract_lineage=d["contract_lineage"][1:]),
                    "skips, adds or reorders a rewrite of the chain"),
        "other contract": (lambda d: d["rewrite_links"][0].update(certification=final_record),
                           f"covers contract {READ}, not {STAGING}"),
        "other snapshot": (lambda d: d["rewrite_links"][0].update(certification=d1_record),
                           f"was built on snapshot {BASE_SNAPSHOT}, not the link's predecessor snapshot {D1}.source"),
    }
    for name, (broken, words) in cases.items():
        store = copied(chain, tmp_path / name.replace(" ", "-"))
        change(store, D2, broken)
        refused = validate(store, staging_library)
        assert refused.returncode != 0 and words in refused.stdout + refused.stderr, (name, refused.stdout)


LINK_COLUMNS = ("contract", "contract_sha256", "predecessor", "predecessor_snapshot", "predecessor_snapshot_sha256",
                "result_candidate", "result_sha256", "certification", "proof_route", "matches", "reason")


def links(store, tmp_path):
    """`swdb build`, then the per-rewrite link rows by subject (derived implementation or candidate)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    database = tmp_path / "research.sqlite"
    built = run_swdb("build", "--records", store, "--db", database)
    assert built.returncode == 0, built.stdout + built.stderr
    con = sqlite3.connect(database)
    try:
        rows = con.execute(f"SELECT subject, {', '.join(LINK_COLUMNS)} FROM swdb_rewrite_links").fetchall()
    finally:
        con.close()
    return {row[0]: dict(zip(LINK_COLUMNS, row[1:])) for row in rows}


def prove_with_route(store, candidate, contract, runs, route):
    """A fixture proof record of the rewrite's result candidate artifact that names its proof route.

    `swdb prove` (scripted adapter) writes the record with no route (ticket 04: 61 and 62 fill it); the
    fixture then names a route in its file, as those tickets will."""
    script = runs.parent / "proven.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": {"threads": 1}, "assumptions": [
        {"kind": "trusted_tool", "reference": {"id": "clang-22.1.8", "sha256": "a" * 64},
         "sentence": "clang 22.1.8 compiles the proof unit correctly."}]}))
    proved = run_swdb("prove", "--records", store, "--candidate", candidate, "--function", "DOBFS", "--adapter",
                      "scripted", "--script", script, "--runs-dir", runs, "--contract", contract, "--format", "json")
    assert proved.returncode == 0, proved.stdout + proved.stderr
    change(store, json.loads(proved.stdout)["record"]["id"], lambda d: d.update(route=route), kind="proofs")


def test_each_rewrite_of_the_chain_has_a_link_with_its_proof_route(chain, tmp_path, staging_library):
    store = copied(chain, tmp_path)
    shutil.copytree(staging_library, store.parent / "library")       # the library beside the records
    first = f"{CID}.it1.kronecker.a0"
    prove_with_route(store, first, STAGING, tmp_path / "runs", "route_1")
    rows = links(store, tmp_path)
    d1, d2 = record(store, "implementations", D1), record(store, "implementations", D2)
    pin = Library(LIBRARY).content_sha256(STAGING)
    assert rows[D1] == {"contract": STAGING, "contract_sha256": pin, "predecessor": BASE_IMPL,
                        "predecessor_snapshot": BASE_SNAPSHOT,
                        "predecessor_snapshot_sha256": record(store, "source_snapshots", BASE_SNAPSHOT)["artifact"]["sha256"],
                        "result_candidate": first, "result_sha256": record(store, "candidates", first)["artifact"]["sha256"],
                        "certification": d1["rewrite_links"][0]["certification"], "proof_route": "route_1",
                        "matches": 1, "reason": None}
    assert rows[D2]["predecessor"] == D1 and rows[D2]["predecessor_snapshot"] == f"{D1}.source"
    assert rows[D2]["certification"] == d2["rewrite_links"][0]["certification"]
    assert rows[D2]["proof_route"] == "none yet" and rows[D2]["matches"] == 1
    final = entries(chain["summary"], 2)["kronecker"]
    assert rows[FINAL]["predecessor"] == D2 and rows[FINAL]["contract"] == READ
    assert rows[FINAL]["certification"] == final["certification"]["record"]
    assert rows[FINAL]["predecessor_snapshot_sha256"] == record(store, "source_snapshots", f"{D2}.source")["artifact"]["sha256"]
    assert rows[FINAL]["proof_route"] == "none yet"
    # the library beside these records holds only the enabling contract, so the offload's link cannot match
    assert rows[FINAL]["matches"] == 0 and rows[FINAL]["reason"] == "the contract is not in the library"


def test_changing_a_predecessor_snapshot_reopens_that_rewrite_and_every_later_one(chain, tmp_path):
    store = copied(chain, tmp_path)
    assert {rid: row["matches"] for rid, row in links(store, tmp_path / "before").items()
            if rid in (D1, D2, FINAL)} == {D1: 1, D2: 1, FINAL: 1}
    kept = {rid: (store / "implementations" / f"{rid}.yaml").read_bytes() for rid in (D1, D2)}
    change(store, BASE_SNAPSHOT, lambda d: d["artifact"].update(sha256="0" * 64), kind="source_snapshots")
    rows = links(store, tmp_path)
    assert rows[D1]["matches"] == 0 and "predecessor snapshot changed" in rows[D1]["reason"]
    for later in (D2, FINAL):
        assert rows[later]["matches"] == 0 and "an earlier rewrite of the chain no longer matches" in rows[later]["reason"]
    assert {rid: (store / "implementations" / f"{rid}.yaml").read_bytes() for rid in (D1, D2)} == kept


# --- consumers unchanged ------------------------------------------------------------------------

def test_a_rewrite_proposal_targeting_the_derived_snapshot_takes_the_existing_proposal_path(chain, tmp_path):
    store = copied(chain, tmp_path)
    snapshot = record(store, "source_snapshots", f"{D1}.source")
    packaged = run_swdb("fixture-package", f"{D1}.source", "--id", "d1-package", "--records", store)
    assert packaged.returncode == 0, packaged.stdout + packaged.stderr
    request = {"message_version": "1.0", "id": "d1-proposal",
               "producer": {"name": "derived-proposal-test", "role": "sw", "test_client": True},
               "profile_package": "d1-package", "source_snapshot": f"{D1}.source", "implementation": D1,
               "source_sha256": snapshot["artifact"]["sha256"], "intent": "Fixture rewrite of a derived implementation.",
               "regions": [snapshot["regions"][0]["id"]],
               "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
               "payload": {"kind": "patch", "content": BETA}, "required_operations": []}
    path = tmp_path / "d1-proposal.yaml"
    path.write_text(yaml.safe_dump(request))
    # ArchEvolve mode refuses the campaign's records (ADR 0013; promotion is not built here), so the
    # proposal is submitted in Extensa mode for the campaign that made the derived implementation.
    refused = run_swdb("submit", path, "--records", store, "--runs-dir", tmp_path / "runs", "--format", "json")
    assert refused.returncode != 0 and "ADR 0013" in refused.stderr
    submitted = run_swdb("submit", path, "--records", store, "--runs-dir", tmp_path / "runs", "--format", "json",
                         "--mode", "extensa", "--campaign", CID)
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    result = json.loads(submitted.stdout)
    assert result["outcome"]["state"] == "candidate_created", result["outcome"]
    candidate = record(store, "candidates", result["candidate"])
    assert candidate["implementation"] == D1 and candidate["source_snapshot"] == f"{D1}.source"
    assert "int alpha = 14, int beta = 17" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()


def test_the_site_finder_matches_a_contract_against_the_derived_implementations_annotations(chain, tmp_path):
    """The profiling agent annotates a derived implementation like any implementation (decision 17 item 5).

    Fixture: the annotation it records here is the scalar TDStep implementation's (access patterns,
    statements and legality facts for the read offload); the site finder's code is unchanged."""
    from swdb import site_finder
    store = copied(chain, tmp_path)
    scalar = yaml.safe_load((REPO / "records" / "implementations" / "dx100-bfs-scalar.yaml").read_text())
    statements = scalar["extensions"]["statements"]
    for row in statements["annotations"]:
        row["annotation_facts"] = [{"field": f"legality:{READ}:{clause}", "value": True, "basis": "code_reading",
                                    "evidence": "fixture fact"} for clause in
                                   ("L1", "L2", "L3", "L4", "L5", "chunk_size", "frontier_threshold", "schedule")]
    change(store, D1, lambda d: d.update(loops=scalar["loops"], access_patterns=[
        {k: v for k, v in p.items() if k not in {"evidence_refs", "agent_claims", "annotation_facts"}}
        for p in scalar["access_patterns"]], extensions={"statements": statements}))
    found = site_finder.find(store, {"kernel": "gapbs-bfs", "target": "dx100_gem5",
                                     "library": {"allowed_tiers": ["shared", "experimental"], "contracts": [READ]}},
                             library=LIBRARY, db_path=tmp_path / "finder.sqlite")
    assert [r["id"] for r in found["regions"]] == [f"{D1}/TDStep:240-243"]
    (application,) = found["regions"][0]["applications"]
    assert application["entry"] == READ and application["applies"] is True


def test_speed_is_compared_against_the_root_baseline_never_the_predecessor(chain):
    store, team = chain["store"], chain["team"]
    roots = {team["baseline"], team["candidate"]}                     # the campaign's baseline roles
    predecessors = {record(store, "implementations", d)["rewrite_links"][0]["result"]["candidate"] for d in (D1, D2)}
    final = entries(chain["summary"], 2)["kronecker"]
    assert {c["baseline_role"] for c in final["comparisons"]} == {"fork_scalar_tdstep", "upstream_do_bfs"}
    for row in final["comparisons"]:
        compared = record(store, "comparison_results", row["comparison"])
        baseline = record(store, "evaluations", compared["baseline_evaluation"])["candidate"]
        assert baseline in roots and baseline not in predecessors


# --- a real target adapter (native, scripted certification; no real target run) ----------------

def test_a_real_target_records_a_derived_implementation_on_its_scalar_only_snapshot(repo_team, base_source,
                                                                                   monkeypatch):
    from swdb import campaign_targets
    from test_campaign_certification_links import ScriptedCertify, native_campaign
    from testkit.extensa_targets import FakeHost, FakeRunner, diff
    from testkit.extensa_targets import run as run_target
    copy_record_subset(REPO / "records", repo_team["records"], ["packing", "loop_tiling"])
    monkeypatch.setattr("testkit.extensa_targets.fake_certify", ScriptedCertify())
    patch = diff(base_source, base_source + "// campaign fixture edit\n")
    config = provider(repo_team, {"rewriting": [{"patch": patch, "contracts": [STAGING], "knobs": [],
                                                 "unresolved": []}]})
    runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    loop, summary = run_target(repo_team, native_campaign(repo_team, [STAGING]), config, runner, FakeHost())
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    entry = summary["iterations"][0]["candidates"][0]
    assert entry["level"] == "certified" and entry["derived_implementation"] == entry["id"] + ".derived"
    derived = record(loop.store_dir, "implementations", entry["derived_implementation"])
    assert derived["origin"]["derived_from"] == "dx100-bfs-scalar"
    (link,) = derived["rewrite_links"]
    assert link["predecessor_snapshot"]["id"] == campaign_targets.SNAPSHOT
    assert link["result"]["sha256"] == record(loop.store_dir, "candidates", entry["id"])["artifact"]["sha256"]
