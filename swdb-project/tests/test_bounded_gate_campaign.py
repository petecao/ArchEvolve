"""The bounded gate in the campaign: refuted code never spends evaluation time.

Created: 2026-10-14 ET (Probata proof of concept, ticket 14). Seam 3 of the formal-verification map's spec
(`swdb campaign --fixture`, a contract-fixture campaign with the scripted verifier adapter) and seam 2
(`swdb candidate-level`). Every certification, comparison, contract proof and proof record here is a
contract fixture, never evidence; no real verifier or provider runs. The fixture's base snapshot is the
seeded `test-source` snapshot of upstream GAPBS (`gapbs-bfs-do`); fixture patches edit its `src/bfs.cc`.
The campaign's library is a copy of the repository library plus ticket 11's `contract_fixture` method
version, whose budgets (15 minutes per bounded job, k = 3, 5 repair rounds) the gate reads.
"""

import difflib
import json
import shutil
import sys
import time

import pytest
import yaml

from conftest import FIXTURES, REPO, run_swdb
from test_proof_records import _library_roots
from testkit.extensa import (campaign_file, campaign_store, comparison, edit_workspace, fixture_file, provider,
                             records_of, rewrite)
from testkit.extensa import run as run_fixture
from testkit.record_subset import copy_record_subset

READ = "contract.bfs_read_offload"
STAGING = "contract.bfs_tdstep_frontier_staging"
CID = "extensa-native-bfs-20261004-a1"
ORIGINAL = (REPO / "apps/gapbs/src/bfs.cc").read_text()
MIN_ONE = {"threads": 1, "lanes": 2, "chunk": 2, "frontier": 2, "vertices": 3, "edges": 3}
MIN_MANY = {"threads": 2, "lanes": 2, "chunk": 2, "frontier": 2, "vertices": 3, "edges": 3}
K = 3
COUNTEREXAMPLE = {"source": 0, "graph": "3 vertices, 2 edges", "differs_at": "parent[2]"}


def edit(before, after, text=ORIGINAL):
    """A -p1 patch of src/bfs.cc replacing one fragment."""
    changed = text.replace(before, after, 1)
    assert changed != text, before
    return "".join(difflib.unified_diff(text.splitlines(keepends=True), changed.splitlines(keepends=True),
                                        fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))


ALPHA = edit("int alpha = 15", "int alpha = 14")
BETA = ("int beta = 18", "int beta = 17")         # a repair of ALPHA's tree
UNDO = ("int alpha = 14", "int alpha = 15")       # a repair that returns the baseline


def cex_repair(*pairs):
    """The fixture provider's answer to a counterexample repair call: it edits the refuted tree's src/bfs.cc."""
    return edit_workspace({"src/bfs.cc": pairs})


@pytest.fixture(scope="module")
def gate_seed(campaign_team_seed, tmp_path_factory):
    """The seeded campaign team store plus the records the library names (record closure, LR-03), and a
    library with the contract-fixture method version."""
    root = tmp_path_factory.mktemp("gate-seed")
    records = root / "records"
    shutil.copytree(campaign_team_seed["records"], records)
    copy_record_subset(REPO / "records", records, sorted(_library_roots() | {"packing", "loop_tiling"}))
    library = root / "library"
    shutil.copytree(REPO / "library", library)
    (library / "methods").mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", library / "methods")
    return {**campaign_team_seed, "records": records, "library": library}


@pytest.fixture
def team(gate_seed, tmp_path):
    records = tmp_path / "records"
    shutil.copytree(gate_seed["records"], records)
    return {**gate_seed, "records": records, "root": tmp_path}


def class_row(proof=None, certification=None):
    row = {"comparisons": {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)}}
    if proof is not None:
        row["proof"] = proof
    if certification is not None:
        row["certification"] = certification
    return row


def gate_fixture(team, *, kronecker=None, uniform=None, contract_proofs=None, iterations=None, **changes):
    """The fixture file: base snapshot, contract-fixture contract proofs, and per class the scripted
    bounded verdicts (`proof`) and certification outcomes."""
    proofs = {READ: {"minimum_bounds": {"threads_1": MIN_ONE, "threads_k": MIN_MANY}}}
    row = {"kronecker": class_row(**(kronecker or {})), "uniform_random": class_row(**(uniform or {}))}
    return fixture_file(team, base_snapshot="test-source", iterations=iterations or [row],
                        contract_proofs=proofs if contract_proofs is None else contract_proofs,
                        proof={"function": "DOBFS"}, **changes)


def gate_campaign(team, plan, *, contracts=(READ,), fixture=None, library=True, expect=0, **budgets):
    raised = {"approval": {"by": "Yan-Ru Jhou", "date": "2026-10-14", "scope": "contract-fixture test",
                           "raised_budgets": ["provider_calls_per_iteration"]}} \
        if budgets.get("provider_calls_per_iteration", 3) > 3 else {}
    path = campaign_file(team, library={"contracts": list(contracts)}, budgets={"max_iterations": 1, **budgets},
                         **raised)
    extra = ["--library", team["library"]] if library else []
    summary = run_fixture(team, path, fixture or gate_fixture(team), provider(team, plan), *extra, expect=expect)
    return summary, campaign_store(team)


def entries(summary, index=0):
    """{class: [entries in order]} of one iteration."""
    found = {}
    for entry in summary["iterations"][index]["candidates"]:
        found.setdefault(entry["class"], []).append(entry)
    return found


def proofs(store, candidate=None):
    rows = [r for r in records_of(store, "proofs") if (r.get("subject") or {}).get("kind") == "candidate_proof_unit"]
    return [r for r in rows if candidate is None or r["subject"]["candidate"] == candidate]


def level(store, candidate):
    result = run_swdb("candidate-level", "--records", store, candidate, "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def state(team, cid=CID):
    return json.loads((team["root"] / "runs" / "extensa" / cid / "state.json").read_text())


# --- the tracer: both rungs at the minimum bounds, then evaluation ------------------------------------

def test_a_certified_candidate_runs_both_rungs_at_the_minimum_bounds_with_k_from_the_method_version(team):
    summary, store = gate_campaign(team, {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)]})
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    (kron,) = entries(summary)["kronecker"]
    assert kron["level"] == "certified" and kron["comparisons"], kron
    jobs = {job["rung"]: job for job in kron["bounded_gate"]["jobs"]}
    assert set(jobs) == {"threads_1", "threads_k"}
    records = {r["id"]: r for r in proofs(store, kron["id"])}
    one, many = records[jobs["threads_1"]["record"]], records[jobs["threads_k"]["record"]]
    assert one["bounds"] == MIN_ONE
    assert many["bounds"] == {**MIN_MANY, "threads": K}            # k = 3, the one exception
    assert one["verdict"] == many["verdict"] == "proven"
    for record in (one, many):
        assert record["pins"]["method_version"]["id"] == "method.contract-fixture-1"
        assert record["pins"]["contract"]["id"] == READ
        assert not record["pins"]["minimum_bounds"].get("not_applicable")
    derivations = {r["id"]: r for r in records_of(store, "proofs")
                   if (r.get("subject") or {}).get("part") == "minimum_bounds_derivation"}
    assert derivations[one["pins"]["minimum_bounds"]["id"]]["bounds"] == MIN_ONE
    assert derivations[many["pins"]["minimum_bounds"]["id"]]["bounds"] == MIN_MANY
    gate = kron["bounded_gate"]
    assert gate["budget_minutes"] == 15 and gate["k"] == K and gate["refuted"] is False
    # Level read, never stored: the level rule reads the sub-rung both rungs proved.
    assert level(store, kron["id"])["level"] == "proven_within_bounds_threads_k"


# --- refuted code is never evaluated; repairs; the reverted-repair control -------------------------------

def evaluations_of(store, candidate):
    return [r["id"] for r in records_of(store, "evaluations") if r.get("candidate") == candidate]


def json_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def repair_calls(summary):
    return [c for c in summary["iterations"][0]["provider_calls"] if c["role"] == "counterexample_repair"]


def test_a_refuted_candidate_is_never_evaluated_and_its_repair_is_certified_gated_and_evaluated(team):
    fixture = gate_fixture(team, kronecker={"proof": {"threads_1": ["refuted", "proven"]}},
                           uniform={"proof": {"threads_1": ["refuted"]}})
    plan = {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)],
            "counterexample_repair": [cex_repair(BETA), cex_repair(UNDO)]}
    summary, store = gate_campaign(team, plan, fixture=fixture)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    rows = entries(summary)
    refuted, repaired = rows["kronecker"]
    # Refuted: no evaluator call, no comparison, so it cannot win; its counterexample went to 13's loop.
    assert refuted["bounded_gate"]["refuted"] is True and refuted["level"] == "certified"
    assert refuted["comparisons"] == [] and refuted["selection"] is None
    assert evaluations_of(store, refuted["id"]) == []
    assert level(store, refuted["id"])["refuted"]["flag"] is True
    assert refuted["counterexample_repair"]["state"] == "repaired"
    assert refuted["counterexample_repair"]["repairs"] == [repaired["id"]]
    # The repaired candidate artifact: certified, gated (both rungs, not refuted), evaluated and ranked.
    assert repaired["repaired_from"]["candidate"] == refuted["id"] and repaired["repaired_from"]["round"] == 1
    assert repaired["level"] == "certified" and repaired["certification"]["outcome"] == "certified"
    assert {j["rung"] for j in repaired["bounded_gate"]["jobs"]} == {"threads_1", "threads_k"}
    assert repaired["bounded_gate"]["refuted"] is False
    assert repaired["comparisons"] and evaluations_of(store, repaired["id"])
    kron = next(c for c in summary["per_class"] if c["class"] == "kronecker")
    assert kron["best"] == repaired["id"]
    # Control (seam 3's reverted-repair case): a repair that returns the baseline is flagged, gets no bounded
    # job, keeps the level certification gives it, is evaluated and may compete, and is never a repair.
    uniform_refuted, reverted = rows["uniform_random"]
    assert uniform_refuted["counterexample_repair"]["state"] == "reverted"
    assert uniform_refuted["counterexample_repair"]["repairs"] == []
    assert reverted["reverted_repair"] is True and reverted["repaired_from"]["reverted_repair"] is True
    assert "bounded_gate" not in reverted and proofs(store, reverted["id"]) == []
    assert reverted["level"] == "certified" and reverted["comparisons"]
    counters = state(team)["repair_counters"]
    assert counters["repairs"] == [repaired["id"]] and counters["reverted_repairs"] == [reverted["id"]]
    assert counters["counterexample_repair_rounds"] == 2 and counters["certification_repairs"] == 0
    assert len(repair_calls(summary)) == 2 and all(c["counted"] for c in repair_calls(summary))
    shown = [row for row in json_lines(team["root"] / "provider-log.jsonl") if row["role"] == "counterexample_repair"]
    assert len(shown) == 2 and all(".swdb-context/counterexample.json" in row["files"] for row in shown)


# --- order: after certification, before evaluation; only certified candidates are gated --------------------

PROBE = """import json, sys, time
from pathlib import Path
store, candidate, rung, log = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
start = time.time()
certified = (store / "certifications" / f"certification.{candidate}.yaml").exists()
evaluated = any(p.name.startswith(candidate + ".") for p in (store / "evaluations").glob("*.yaml"))
time.sleep(1.5)
with open(log, "a") as out:
    out.write(json.dumps({"candidate": candidate, "rung": rung, "start": start, "end": time.time(),
                          "certified": certified, "evaluated": evaluated}) + "\\n")
"""


def probe(team, verdict="proven"):
    """A scripted verdict whose `run` command records when it ran and what the store held then."""
    script = team["root"] / "probe.py"
    script.write_text(PROBE)
    return {"verdict": verdict, "run": [sys.executable, str(script), "{store}", "{candidate}", "{rung}",
                                        str(team["root"] / "probe.jsonl")]}


def test_bounded_jobs_start_after_certification_and_before_evaluation_and_only_for_certified_artifacts(team):
    first = {"kronecker": class_row(proof={"threads_1": [probe(team)], "threads_k": [probe(team)]}),
             "uniform_random": class_row(certification=["failed"])}
    second = {"kronecker": class_row(), "uniform_random": class_row()}
    fixture = gate_fixture(team, iterations=[first, second])
    plan = {"rewriting": [rewrite(contracts=[READ], patch=ALPHA), rewrite(contracts=[], patch=ALPHA)],
            "repair": [rewrite(contracts=[READ], patch=ALPHA)]}
    summary, store = gate_campaign(team, plan, fixture=fixture, max_iterations=2)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    (kron,) = entries(summary)["kronecker"]
    ran = json_lines(team["root"] / "probe.jsonl")
    assert {r["rung"] for r in ran} == {"threads_1", "threads_k"} and {r["candidate"] for r in ran} == {kron["id"]}
    assert all(r["certified"] and not r["evaluated"] for r in ran)
    assert evaluations_of(store, kron["id"])                  # evaluated afterward
    # Parallel: the two rungs' jobs overlap in time.
    one, many = sorted(ran, key=lambda r: r["rung"])
    assert one["start"] < many["end"] and many["start"] < one["end"]
    # Rejected (certification failed after D7's repairs) and uncertified (no contract): no bounded job.
    (rejected,) = entries(summary)["uniform_random"]
    assert rejected["level"] == "rejected" and "bounded_gate" not in rejected
    later = [e for rows in entries(summary, 1).values() for e in rows]
    assert {e["level"] for e in later} == {"uncertified"} and all("bounded_gate" not in e for e in later)
    assert {r["subject"]["candidate"] for r in proofs(store)} == {kron["id"]}


# --- every contract ------------------------------------------------------------------------------------------

def test_each_contract_runs_its_rungs_at_its_own_minimum_bounds_and_either_refutation_refutes(team):
    staging_one, staging_many = dict(MIN_ONE, vertices=4), dict(MIN_MANY, vertices=4)
    by_contract = {READ: {"minimum_bounds": {"threads_1": MIN_ONE, "threads_k": MIN_MANY}},
                   STAGING: {"minimum_bounds": {"threads_1": staging_one, "threads_k": staging_many}}}
    fixture = gate_fixture(team, contract_proofs=by_contract,
                           kronecker={"proof": {"contracts": {STAGING: {"threads_k": ["refuted"]}}}})
    summary, store = gate_campaign(team, {"rewriting": [rewrite(contracts=[READ, STAGING], patch=ALPHA)]},
                                   contracts=(READ, STAGING), fixture=fixture)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    expected = {(READ, "threads_1"): MIN_ONE, (READ, "threads_k"): {**MIN_MANY, "threads": K},
                (STAGING, "threads_1"): staging_one, (STAGING, "threads_k"): {**staging_many, "threads": K}}
    for cls in ("kronecker", "uniform_random"):
        entry = entries(summary)[cls][0]
        records = {r["id"]: r for r in proofs(store, entry["id"])}
        jobs = {(j["contract"], j["rung"]): records[j["record"]] for j in entry["bounded_gate"]["jobs"]}
        assert {key: r["bounds"] for key, r in jobs.items()} == expected
        assert all(r["pins"]["contract"]["id"] == key[0] for key, r in jobs.items())
    kron, uniform = entries(summary)["kronecker"][0], entries(summary)["uniform_random"][0]
    assert kron["bounded_gate"]["refuted"] is True and kron["comparisons"] == []     # refuted under STAGING only
    assert uniform["bounded_gate"]["refuted"] is False and uniform["comparisons"]
    assert level(store, uniform["id"])["level"] == "proven_within_bounds_threads_k"


# --- a timeout is that rung's alone; a spurious counterexample is no refutation ---------------------------

def test_a_timeout_gives_no_level_from_that_rung_and_no_retry_and_the_candidate_is_evaluated(team):
    fixture = gate_fixture(team, kronecker={"proof": {"threads_k": ["timeout"]}},
                           uniform={"proof": {"threads_k": ["spurious"]}})
    summary, store = gate_campaign(team, {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)]}, fixture=fixture)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    (kron,), (uniform,) = entries(summary)["kronecker"], entries(summary)["uniform_random"]
    jobs = {j["rung"]: j for j in kron["bounded_gate"]["jobs"]}
    assert jobs["threads_k"]["verdict"] == "not_proven" and jobs["threads_k"]["failure_class"] == "timeout"
    assert jobs["threads_1"]["verdict"] == "proven"
    assert len(proofs(store, kron["id"])) == 2                              # no retry at smaller bounds
    assert kron["comparisons"] and level(store, kron["id"])["level"] == "proven_within_bounds_threads_1"
    # A spurious counterexample (13's filter) never refutes and never reaches repair.
    assert uniform["bounded_gate"]["refuted"] is False and uniform["comparisons"]
    assert "counterexample_repair" not in uniform and repair_calls(summary) == []


def test_the_scripted_adapter_ends_a_job_that_outlives_its_wall_budget_as_not_proven_timeout(tmp_path):
    """Seam 1 (the verifier adapter interface): the job's wall budget is enforced, not only scripted."""
    from swdb.proof import Job, ProofUnit, ScriptedAdapter
    script = tmp_path / "slow.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "run": [sys.executable, "-c", "import time; time.sleep(30)"]}))
    (tmp_path / "scratch").mkdir()
    unit = ProofUnit("c", "DOBFS", str(tmp_path), "0" * 64, READ, "0" * 64)
    started = time.monotonic()
    verdict = ScriptedAdapter(script).run(Job(unit=unit, scratch=tmp_path / "scratch", log=tmp_path / "log",
                                              bounds=MIN_ONE, budget_seconds=1))
    assert time.monotonic() - started < 20
    assert verdict.verdict == "not_proven" and verdict.failure_class == "timeout" and verdict.bounds == MIN_ONE


# --- two repair counters --------------------------------------------------------------------------------------

def alpha_chain(rounds):
    """Each round's repair edits the tree the previous round made (alpha 14 -> 13 -> ...)."""
    return [(f"int alpha = {14 - r}", f"int alpha = {13 - r}") for r in range(rounds)]


def test_a_refuted_candidate_gets_at_most_five_counterexample_rounds_from_13s_cap(team):
    fixture = gate_fixture(team, kronecker={"proof": {"threads_1": ["refuted"]}})
    plan = {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)],
            "counterexample_repair": [cex_repair(p) for p in alpha_chain(6)]}
    summary, store = gate_campaign(team, plan, fixture=fixture, provider_calls_per_iteration=9)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    first, *chain = entries(summary)["kronecker"]
    repair = first["counterexample_repair"]
    assert repair["state"] == "budget_spent" and repair["cap"] == 5 and repair["calls"] == 5
    assert [e["repaired_from"]["round"] for e in chain] == [1, 2, 3, 4, 5]
    assert all(e["bounded_gate"]["refuted"] and e["comparisons"] == [] for e in [first, *chain])
    shown = [row for row in json_lines(team["root"] / "provider-log.jsonl") if row["role"] == "counterexample_repair"]
    assert len(shown) == 5                                                   # a sixth call never opens
    counters = state(team)["repair_counters"]
    assert counters["counterexample_repair_rounds"] == 5 and counters["certification_repairs"] == 0
    assert counters["repairs"] == []


def test_a_repair_that_fails_certification_uses_one_certification_repair_and_no_counterexample_round(team):
    changed = ORIGINAL.replace("int alpha = 15", "int alpha = 14", 1).replace("int beta = 18", "int beta = 17", 1)
    both = "".join(difflib.unified_diff(ORIGINAL.splitlines(keepends=True), changed.splitlines(keepends=True),
                                        fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))
    fixture = gate_fixture(team, kronecker={"proof": {"threads_1": ["refuted", "proven"]},
                                            "certification": ["certified", "failed", "certified"]})
    plan = {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)],
            "counterexample_repair": [cex_repair(BETA)],
            "repair": [rewrite(contracts=[READ], patch=both)]}
    summary, store = gate_campaign(team, plan, fixture=fixture, provider_calls_per_iteration=4)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    refuted, fixed = entries(summary)["kronecker"]
    assert refuted["counterexample_repair"]["state"] == "certification_failed"
    assert refuted["counterexample_repair"]["calls"] == 1
    # The certification repair replaced the failing repair: certified, gated, evaluated.
    assert fixed["certification"]["outcome"] == "certified" and fixed["level"] == "certified"
    assert fixed["bounded_gate"]["refuted"] is False and fixed["comparisons"]
    counters = state(team)["repair_counters"]
    assert counters["certification_repairs"] == 1 and counters["counterexample_repair_rounds"] == 1
    roles = sorted(c["role"] for c in summary["iterations"][0]["provider_calls"] if c["counted"])
    assert roles == ["counterexample_repair", "repair", "rewriting"]
    # Both kinds count in the rewriting total: the setup call, the rewrite, one repair of each kind.
    assert summary["budgets"]["used"]["provider_calls_counted"] == 4
    assert summary["bounded_gate"]["repair_counters"]["certification_repairs"] == 1


# --- skips keep the level (O7) ---------------------------------------------------------------------------------

def test_no_contract_proof_and_no_minimum_bounds_skip_both_rungs_and_keep_the_level(team):
    fixture = gate_fixture(team, contract_proofs={READ: {}})            # READ: proof parts, no minimum bounds
    summary, store = gate_campaign(team, {"rewriting": [rewrite(contracts=[READ, STAGING], patch=ALPHA)]},
                                   contracts=(READ, STAGING), fixture=fixture)    # STAGING: no contract proof
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    for rows in entries(summary).values():
        (entry,) = rows
        skips = {(j["contract"], j["rung"]): j["skip_reason"] for j in entry["bounded_gate"]["jobs"]}
        assert skips == {(READ, "threads_1"): "no_minimum_bounds", (READ, "threads_k"): "no_minimum_bounds",
                         (STAGING, "threads_1"): "no_contract_proof", (STAGING, "threads_k"): "no_contract_proof"}
        records = proofs(store, entry["id"])
        assert len(records) == 4 and all("verdict" not in r and r["skip_reason"] for r in records)
        assert entry["level"] == "certified" and entry["comparisons"]
        assert level(store, entry["id"])["level"] == "certified"


def test_code_outside_the_cpp_subset_runs_only_the_one_thread_rung(team):
    fixture = gate_fixture(team, kronecker={"proof": {"cpp_subset": False}})
    summary, store = gate_campaign(team, {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)]}, fixture=fixture)
    (kron,), (control,) = entries(summary)["kronecker"], entries(summary)["uniform_random"]
    jobs = {j["rung"]: j for j in kron["bounded_gate"]["jobs"]}
    assert jobs["threads_1"]["verdict"] == "proven" and jobs["threads_k"]["skip_reason"] == "outside_cpp_subset"
    assert kron["comparisons"] and level(store, kron["id"])["level"] == "proven_within_bounds_threads_1"
    # Control: the same candidate artifact with a contract proof, minimum bounds and subset code runs both.
    assert {j["rung"]: j.get("verdict") for j in control["bounded_gate"]["jobs"]} == \
        {"threads_1": "proven", "threads_k": "proven"}
    assert level(store, control["id"])["level"] == "proven_within_bounds_threads_k"


# --- no change when nothing is gated ------------------------------------------------------------------------

#: Run-specific fields (times, paths, random record IDs, a protocol identity that hashes paths, pairing records);
#: what the gate could change (iterations, entries, comparisons, selection, budgets) is compared.
VOLATILE = {"started", "ended", "created", "updated", "at", "disk_gb_peak", "swdb_commit", "campaign_file",
            "bounded_gate", "protocol", "paired_estimates", "retentions"}


def _stable(value):
    if isinstance(value, dict):
        return {k: _stable(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [_stable(v) for v in value]
    return value


def test_a_campaign_whose_candidates_all_skip_runs_the_same_steps_and_summary_as_without_the_gate(team, tmp_path):
    steps = {"step_hours": {"provider": 0.1, "certification": 0.1, "evaluation": 0.1}}
    plan = {"rewriting": [rewrite(contracts=[READ], patch=ALPHA)]}
    gated, gated_store = gate_campaign(team, plan, fixture=gate_fixture(team, contract_proofs={}, **steps))
    other = {**team, "root": tmp_path / "ungated", "records": tmp_path / "ungated" / "records"}
    shutil.copytree(team["records"], other["records"], ignore=shutil.ignore_patterns("campaign_summaries"))
    plain, plain_store = gate_campaign(other, plan, fixture=gate_fixture(other, contract_proofs={}, **steps),
                                       library=False)
    assert "bounded_gate" in gated and "bounded_gate" not in plain
    skips = [j["skip_reason"] for rows in entries(gated).values() for e in rows for j in e["bounded_gate"]["jobs"]]
    assert skips == ["no_contract_proof"] * 4
    assert _stable(gated) == _stable(plain)
    ids = [e["id"] for rows in entries(gated).values() for e in rows]
    assert [evaluations_of(gated_store, i) for i in ids] == [evaluations_of(plain_store, i) for i in ids]
