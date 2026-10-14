"""Counterexample-guided repair (Probata proof of concept, ticket 13).

Created: 2026-10-14 ET. Seams 1 and 4 of the formal-verification map's spec: `swdb repair` (ArchEvolve
mode's command, and the evaluation's), the loop API `swdb.counterexample_repair.loop` that 14 (campaigns)
and 18 (ArchEvolve mode) call, the provider guard (`provider_roles.run`, `provider_roles.rewriting`),
`swdb validate`, `swdb build` and `swdb candidate-level`. A scripted bounded verifier (`swdb prove
--adapter scripted`) and a scripted provider (an `external_fixture` emulating Codex) stand in; no real
verifier or provider runs. Fixture code is contract-fixture code only: the refuted candidate artifact
adds a never-compiled function that calls the read-offload contract's intrinsics.
"""

import difflib
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_proof_records import ASSUMPTION, CONTRACT, FUNCTION, _certify, _library_roots
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

COUNTEREXAMPLE = {"source": 0, "graph": "3 vertices, 2 edges", "differs_at": "parent[2]"}
ONE = {"threads": 1, "vertices": 3, "edges": 3}
ANCHOR = "using namespace std;\n"
OFFLOAD = """
// Contract-fixture code (Probata ticket 13): never compiled.
static void ProbataFixtureOffload(int32_t *parent, int tile) {
  int probata_round = 0;
  __dxc_session_begin();
  __dxc_gather(parent, tile, tile + 1);
  __dxc_wait(tile + 1);
}
"""
GUARDED = "TDStepMAA"           # a guarded authors' name in contract-fixture code, certified
AUTHORS = "PageRankPullMAA"     # the same, standing in for the authors' code that failed certification (O1)


def _offload(name="ProbataFixtureOffload"):
    return ANCHOR + OFFLOAD.replace("ProbataFixtureOffload", name)


@pytest.fixture(scope="module")
def repair_seed(tmp_path_factory):
    """Fixture candidate artifacts, built once, each applying the offload: `offload` (certified), `guarded`
    (a guarded authors' name, certified) and `authors` (a guarded name, failed certification)."""
    path = tmp_path_factory.mktemp("repair-seed")
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    (path / "library" / "methods").mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", path / "library" / "methods")
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    made = {}
    for key, rid, name, verdict in (("offload", "test-proposal", "ProbataFixtureOffload", "certified"),
                                    ("guarded", "guarded-proposal", GUARDED, "certified"),
                                    ("authors", "authors-proposal", AUTHORS, "failed")):
        submitted = records.swdb("submit", request(ANCHOR, _offload(name), id=rid), "--runs-dir", runs,
                                 "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        made[key] = json.loads(submitted.stdout)["candidate"]
        _certify(records.path, path, made[key], f"certification.{rid}", verdict)
    return path, made


class Seed:
    def __init__(self, root, made):
        self.root, self.made = root, made
        self.candidate = made["offload"]
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"
        self.calls = root / "provider-calls.jsonl"

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args)

    def read(self, rid, kind):
        return yaml.safe_load((self.records / kind / f"{rid}.yaml").read_text())

    def prove(self, candidate=None, **script):
        """The scripted bounded verifier: one proof record of `candidate`'s proof unit."""
        script.setdefault("verdict", "refuted")
        if script["verdict"] == "refuted":
            script.setdefault("counterexample", COUNTEREXAMPLE)
        script.setdefault("bounds", ONE)
        script.setdefault("assumptions", [ASSUMPTION])
        path = self.root / f"script-{len(list(self.root.glob('script-*')))}.yaml"
        path.write_text(yaml.safe_dump(script))
        result = self.swdb("prove", "--candidate", candidate or self.candidate, "--function", FUNCTION,
                           "--contract", CONTRACT, "--adapter", "scripted", "--script", path,
                           "--runs-dir", self.runs, "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)["record"]["id"]

    def provider(self, mode="genuine", emulates="codex"):
        """The scripted provider: one line in `provider-calls.jsonl` per call that opens."""
        plan = self.root / f"plan-{mode}.json"
        baseline = Path(yaml.safe_load((self.records / "source_snapshots" / "test-source.yaml").read_text())
                        ["artifact"]["path"]) / "src" / "bfs.cc"
        plan.write_text(json.dumps({"mode": mode, "calls": str(self.calls), "baseline": str(baseline)}))
        config = self.root / f"provider-{mode}-{emulates}.yaml"
        config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": emulates,
                                          "command": [sys.executable, str(FIXTURE_PROVIDER), str(plan)],
                                          "timeout_s": 30, "total_seconds": 600}))
        return config

    def calls_made(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def repair(self, proof, *extra, mode="genuine", ok=True):
        result = self.swdb("repair", proof, "--runs-dir", self.runs, "--provider-config", self.provider(mode),
                           "--format", "json", *extra)
        if ok:
            assert result.returncode == 0, result.stderr + result.stdout
            return json.loads(result.stdout)
        return result


FIXTURE_PROVIDER = Path(__file__).resolve().parent / "fixtures" / "counterexample_repair" / "provider.py"


@pytest.fixture
def seed(repair_seed, tmp_path):
    source, made = repair_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, made)


# --- feedback goes to the rewriting role ------------------------------------------------------

def test_repair_of_a_refuted_record_opens_one_rewriting_repair_call_with_patch_and_counterexample(seed):
    proof = seed.prove()
    proposal = seed.repair(proof)
    assert proposal["outcome"]["state"] == "candidate_created"
    assert len(seed.calls_made()) == 1
    (attempt,) = proposal["attempts"]
    provider = attempt["provider"]
    assert provider["role"] == "rewriting" and attempt["call"] == "counterexample_repair"
    manifest = provider["workspace_manifest"]
    root = Path(manifest["root"])
    inputs = manifest["repair_inputs"]
    refuted = seed.read(seed.candidate, "candidates")
    patch = root / inputs["refuted_patch"]["path"]
    assert patch.read_text() == Path(refuted["diff"]).read_text()
    assert inputs["refuted_patch"]["sha256"] == refuted["diff_sha256"]
    shown = json.loads((root / inputs["counterexample"]["path"]).read_text())
    assert shown["counterexample"] == COUNTEREXAMPLE and shown["proof_record"] == proof
    from swdb import artifacts
    assert inputs["counterexample"]["sha256"] == artifacts.file_hash(root / inputs["counterexample"]["path"])
    for item in inputs.values():
        assert item["path"] in manifest["visible_files"] and item["path"] in manifest["immutable_files"]


# --- only a refutation reaches repair (the spurious-counterexample filter) ---------------------

def _proposals(seed):
    return sorted(p.stem for p in (seed.records / "proposals").glob("*.yaml"))


@pytest.mark.parametrize("script, word", [
    ({"verdict": "not_proven", "failure_class": "spurious_counterexample", "unreplayed_counterexample": COUNTEREXAMPLE},
     "spurious_counterexample"),
    ({"verdict": "proven"}, "not a refutation"),
    ({"verdict": "not_proven", "failure_class": "timeout"}, "not a refutation"),
])
def test_only_a_refutation_starts_a_repair_and_a_spurious_counterexample_never_does(seed, script, word):
    proof = seed.prove(**script)
    before = _proposals(seed)
    result = seed.repair(proof, ok=False)
    assert result.returncode == 1 and word in result.stderr, result.stderr + result.stdout
    assert seed.calls_made() == [] and _proposals(seed) == before


def test_the_filter_names_the_spurious_class_whatever_the_verdict_field_says():
    """Explicit filter (Yan-Ru 2026-10-14): an unreplayed counterexample never qualifies, even beside a
    refuted verdict a broken adapter might write."""
    from swdb.counterexample_repair import repairable
    record = {"kind": "proof", "id": "p", "verdict": "refuted", "counterexample": COUNTEREXAMPLE,
              "unreplayed_counterexample": COUNTEREXAMPLE, "subject": {"kind": "candidate_proof_unit"}}
    assert "spurious_counterexample" in repairable(record)
    record.pop("unreplayed_counterexample")
    assert repairable(record) is None


# --- never to the proof-hint agent: the guard ----------------------------------------------------

REFUSAL = "counterexample"
SHOWN = {"cex.json": json.dumps({"format": "swdb.counterexample.v1", "proof_record": "proof.x",
                                 "counterexample": COUNTEREXAMPLE}),
         "proof.yaml": yaml.safe_dump({"kind": "proof", "id": "proof.x", "verdict": "refuted",
                                       "counterexample": COUNTEREXAMPLE}),
         "notes.json": json.dumps({"why": {"counterexample": COUNTEREXAMPLE}})}


@pytest.fixture
def marker_provider(tmp_path):
    """An external fixture provider that leaves a marker file if a call ever opens."""
    from swdb import rewrite
    marker = tmp_path / "provider-called"
    program = tmp_path / "fixture.py"
    program.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('called')\nprint('{{}}')\n")
    configfile = tmp_path / "provider.yaml"
    configfile.write_text(yaml.safe_dump({"kind": "external_fixture", "command": [sys.executable, str(program)],
                                          "timeout_s": 5, "total_seconds": 5}))
    return rewrite.configuration(configfile), marker


@pytest.mark.parametrize("role", ["profiling", "estimation", "independent_test_generation", "synthesis",
                                  "campaign_rewriting", "campaign_repair", "campaign_profiling"])
@pytest.mark.parametrize("name", sorted(SHOWN))
def test_a_counterexample_in_any_agent_role_workspace_is_refused_before_the_call(role, name, marker_provider, tmp_path):
    from swdb import campaign, provider_roles
    from swdb.annotation import PROFILING  # noqa: F401  (registers the profiling role)
    from swdb.cli import Failure
    config, marker = marker_provider
    chosen = (campaign._roles()[role.removeprefix("campaign_")] if role.startswith("campaign_")
              else provider_roles.ROLES[role])
    folder = tmp_path / "blocked"
    with pytest.raises(Failure, match=REFUSAL):
        provider_roles.run(chosen, {name: SHOWN[name]}, "read", config, folder)
    assert not folder.exists() and not marker.exists()


def test_an_agent_role_input_without_a_counterexample_reaches_the_provider(marker_provider, tmp_path):
    """Control: the same role, the same file shape, no counterexample."""
    from swdb import provider_roles
    config, marker = marker_provider
    role = provider_roles.Role("read_only_fixture", {"type": "object"})
    provider_roles.run(role, {"notes.json": json.dumps({"why": {"first_counterexample_index": 3}})}, "read",
                       config, tmp_path / "role")
    assert marker.read_text() == "called"


def test_a_counterexample_in_an_ordinary_rewriting_workspace_is_refused_before_the_call(seed):
    """`swdb submit` with an instruction route: the request carries the counterexample file's format."""
    request = yaml.safe_load((seed.root / "records" / "proposals" / "test-proposal.yaml").read_text())["request"]
    request.update(id="cex-in-submit", payload={"kind": "natural_language",
                                                "content": "Fix it. " + SHOWN["cex.json"]})
    path = seed.root / "cex-in-submit.yaml"
    path.write_text(yaml.safe_dump(request))
    result = seed.swdb("submit", path, "--runs-dir", seed.runs, "--provider-config", seed.provider(),
                       "--format", "json")
    proposal = json.loads(result.stdout)
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed"
    assert REFUSAL in proposal["outcome"]["reason"] and "candidate" not in proposal
    assert seed.calls_made() == []


def test_a_counterexample_in_a_build_or_correctness_repair_workspace_is_refused_before_the_call(seed, marker_provider):
    """The ordinary repair evidence (an evaluation's logs) is not a counterexample repair."""
    from swdb import provider_roles
    from swdb.cli import Failure
    from swdb.store import Store
    config, marker = marker_provider
    config = {**config, "workspace": True}
    store = Store(seed.records)
    proposal = store.get("test-proposal", "proposal")
    candidate = store.get(seed.candidate, "candidate")
    source = {"artifact": candidate["artifact"], "context": candidate["context"], "protections": candidate["protections"]}
    evidence = {"evaluation": "evaluation.x", "outcome": {"state": "failed", "stage": "correctness"},
                "logs": [{"stage": "verify", "text": SHOWN["cex.json"]}]}
    with pytest.raises(Failure, match=REFUSAL):
        provider_roles.rewriting(config, proposal["request"], source, store.get("test-package", "profile_package"),
                                 store, seed.root / "blocked" / "provider", repair=evidence)
    assert not marker.exists()


# --- the loop: at most 5 rounds, one call each ----------------------------------------------------

def _loop(seed, proof, *, refute_rounds, mode="genuine", setting="campaign", certified=True):
    """Run the loop with the scripted rungs: rounds in `refute_rounds` are refuted, the others proven."""
    from swdb import counterexample_repair
    seen = []

    def certify(candidate):
        _certify(seed.records, seed.root, candidate, f"certification.{candidate}",
                 "certified" if certified else "failed")

    def gate(candidate):
        seen.append(candidate)
        if len(seen) in refute_rounds:
            return [seed.prove(candidate)]
        return [seed.prove(candidate, verdict="proven", bounds=ONE)]

    return counterexample_repair.loop(seed.records, proof, runs_dir=seed.runs, provider_config=seed.provider(mode),
                                      certify=certify, gate=gate, setting=setting)


def test_the_loop_stops_after_exactly_5_calls_when_every_repair_is_refuted(seed):
    outcome = _loop(seed, seed.prove(), refute_rounds=range(1, 99))
    assert outcome["state"] == "budget_spent" and "budget spent" in outcome["reason"]
    assert outcome["calls"] == 5 and len(seed.calls_made()) == 5 and outcome["cap"] == 5
    assert outcome["repairs"] == [] and outcome["reverted_repairs"] == []
    chain = outcome["chain"]
    assert [row["round"] for row in chain] == [1, 2, 3, 4, 5]
    refuted = seed.candidate
    for row in chain:                                  # round r repairs what round r-1 produced
        lineage = seed.read(row["proposal"], "proposals")["repair_lineage"]
        assert lineage == {"refuted_candidate": refuted, "counterexample_record": row["trigger"],
                           "round": row["round"], "reverted_repair": False}
        refuted = row["candidate"]
    # A sixth `swdb repair` on the last refutation is refused before any call: the budget is spent.
    result = seed.repair(chain[-1]["proof_records"][0], ok=False)
    assert result.returncode == 1 and json.loads(result.stdout)["loop"]["state"] == "budget_spent"
    assert len(seed.calls_made()) == 5


def test_a_repair_the_rungs_do_not_refute_in_round_2_ends_the_loop_after_2_calls(seed):
    outcome = _loop(seed, seed.prove(), refute_rounds={1})
    assert outcome["state"] == "repaired" and outcome["calls"] == 2 and len(seed.calls_made()) == 2
    assert outcome["repairs"] == [outcome["chain"][1]["candidate"]]


def test_a_spurious_counterexample_from_the_rungs_never_continues_the_loop(seed):
    from swdb import counterexample_repair
    outcome = counterexample_repair.loop(
        seed.records, seed.prove(), runs_dir=seed.runs, provider_config=seed.provider(),
        certify=lambda c: _certify(seed.records, seed.root, c, f"certification.{c}", "certified"),
        gate=lambda c: [seed.prove(c, verdict="not_proven", failure_class="spurious_counterexample",
                                   unreplayed_counterexample=COUNTEREXAMPLE)])
    assert outcome["calls"] == 1 and len(seed.calls_made()) == 1
    assert outcome["chain"][0]["refuted"] is False


def test_a_repair_that_fails_certification_ends_the_loop(seed):
    outcome = _loop(seed, seed.prove(), refute_rounds=range(1, 99), certified=False)
    assert outcome["state"] == "certification_failed" and outcome["calls"] == 1


# --- a repaired candidate artifact is new; the refuted one stays as it was --------------------------

def _files(seed, candidate):
    """Every record about the refuted candidate artifact: itself, its proposal, certification and proofs."""
    found = {}
    for path in sorted(seed.records.rglob("*.yaml")):
        text = path.read_text()
        if candidate in text and ".cex-repair-" not in path.name:
            found[str(path.relative_to(seed.records))] = path.read_bytes()
    return found


def _level(seed, candidate):
    result = seed.swdb("candidate-level", candidate, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_a_repaired_candidate_is_new_and_the_refuted_one_keeps_every_record_byte_identical(seed):
    proof = seed.prove()
    before = _files(seed, seed.candidate)
    assert _level(seed, seed.candidate)["refuted"]["flag"]
    outcome = _loop(seed, proof, refute_rounds=set())
    assert outcome["state"] == "repaired"
    assert _files(seed, seed.candidate) == before                       # byte-identical afterward
    old = _level(seed, seed.candidate)
    assert old["refuted"]["flag"] and old["certification_level"] == "certified"
    (row,) = outcome["chain"]
    repaired = seed.read(row["candidate"], "candidates")
    refuted = seed.read(seed.candidate, "candidates")
    assert repaired["artifact"]["sha256"] != refuted["artifact"]["sha256"]
    assert repaired["proposal"] == row["proposal"] != refuted["proposal"]
    proposal = seed.read(row["proposal"], "proposals")
    assert proposal["provider_pin"] == {"kind": "codex", "model": "gpt-5.6-sol", "effort": "xhigh"}
    assert proposal["repair_lineage"]["counterexample_record"] == proof
    new = _level(seed, row["candidate"])
    assert new["level"] == "proven_within_bounds_threads_1" and not new["refuted"]["flag"]
    assert seed.swdb("validate").returncode == 0, seed.swdb("validate").stderr
    built = seed.swdb("build")
    assert built.returncode == 0, built.stderr
    rows = json.loads(seed.swdb("sql", "SELECT * FROM swdb_repair_lineage", "--format", "json").stdout)
    assert rows == [{"proposal": row["proposal"], "refuted_candidate": seed.candidate,
                     "counterexample_record": proof, "round": 1, "reverted_repair": 0}]


# --- reverted repairs: a deterministic contract-match check --------------------------------------

@pytest.mark.parametrize("mode, flagged, reason", [("genuine", False, None), ("drop", True, "drops_offload"),
                                                   ("baseline", True, "equals_baseline")])
def test_the_contract_match_check_flags_a_reverted_repair(seed, mode, flagged, reason):
    proposal = seed.repair(seed.prove(), mode=mode)
    assert proposal["outcome"]["state"] == "candidate_created"
    assert proposal["repair_lineage"]["reverted_repair"] is flagged
    match = proposal["attempts"][0]["contract_match"]
    assert match["reverted_repair"] is flagged and (reason in match["reasons"] if flagged else match["reasons"] == [])
    if mode == "drop":
        assert match["offload_calls"]["dropped"] == ["__dxc_gather"]


def test_a_flagged_repair_competes_at_its_own_level_but_never_counts_as_a_repair(seed):
    outcome = _loop(seed, seed.prove(), refute_rounds=set(), mode="drop")
    assert outcome["state"] == "reverted" and outcome["calls"] == 1
    (row,) = outcome["chain"]
    assert outcome["repairs"] == [] and outcome["reverted_repairs"] == [row["candidate"]]
    level = _level(seed, row["candidate"])                 # still a candidate artifact with its own level
    assert level["level"] == "proven_within_bounds_threads_1"


# --- works outside campaigns: ArchEvolve mode's `swdb repair` --------------------------------------

def test_archevolve_repair_admits_a_refuted_record_and_its_records_validate_and_build(seed):
    proposal = seed.repair(seed.prove())
    assert proposal["outcome"]["state"] == "candidate_created"
    assert proposal["repair_budget"]["setting"] == "archevolve"
    manifest = proposal["attempts"][0]["provider"]["workspace_manifest"]
    assert manifest["evaluation_repair"] is None              # ArchEvolve mode never sets the mark
    assert seed.swdb("validate").returncode == 0, seed.swdb("validate").stderr
    assert seed.swdb("build").returncode == 0


def test_evaluation_run_flags_apply_only_to_a_proof_record_trigger(seed):
    result = seed.swdb("repair", "test-proposal", "--runs-dir", seed.runs, "--provider-config", seed.provider(),
                       "--evaluation-run")
    assert result.returncode == 1 and "refuted proof record trigger" in result.stderr


# --- the authors' code under repair (O5) ----------------------------------------------------------

AUTHORS_REFUSAL = "authors' accelerated code"


def test_an_evaluation_repair_run_may_show_the_guarded_function_it_repairs(seed):
    proposal = seed.repair(seed.prove(seed.made["guarded"]), "--evaluation-run")
    assert proposal["outcome"]["state"] == "candidate_created" and len(seed.calls_made()) == 1
    manifest = proposal["attempts"][0]["provider"]["workspace_manifest"]
    tree = seed.read(seed.made["guarded"], "candidates")["artifact"]["sha256"]
    assert manifest["evaluation_repair"] == {"refuted_candidate": seed.made["guarded"], "tree_sha256": tree}
    assert GUARDED in (Path(manifest["root"]) / "src" / "bfs.cc").read_text()


def test_archevolve_repair_never_shows_the_guarded_function(seed):
    proposal = seed.repair(seed.prove(seed.made["guarded"]), ok=False)
    data = json.loads(proposal.stdout)
    assert proposal.returncode == 1 and data["outcome"]["state"] == "failed"
    assert AUTHORS_REFUSAL in data["outcome"]["reason"] and seed.calls_made() == []


def test_a_campaign_repair_never_shows_the_guarded_function(seed):
    outcome = _loop(seed, seed.prove(seed.made["guarded"]), refute_rounds=set(), setting="campaign")
    assert outcome["state"] == "provider_failed" and AUTHORS_REFUSAL in outcome["reason"]
    assert outcome["calls"] == 0 and seed.calls_made() == []


def _guarded_workspace(seed, marker_provider, repair):
    from swdb import provider_roles
    from swdb.store import Store
    config, marker = marker_provider
    store = Store(seed.records)
    guarded = store.get(seed.made["guarded"], "candidate")
    source = {"artifact": guarded["artifact"], "context": guarded["context"], "protections": guarded["protections"]}
    proposal = store.get(guarded["proposal"], "proposal")
    provider_roles.rewriting({**config, "workspace": True}, proposal["request"], source,
                             store.get("test-package", "profile_package"), store, seed.root / "blocked" / "provider",
                             repair=repair)
    return marker


def test_an_ordinary_rewriting_workspace_never_shows_the_guarded_function(seed, marker_provider):
    from swdb.cli import Failure
    with pytest.raises(Failure, match=AUTHORS_REFUSAL):
        _guarded_workspace(seed, marker_provider, None)
    assert not marker_provider[1].exists()


def test_an_evaluation_repair_workspace_of_another_refuted_candidate_never_shows_the_guarded_function(seed, marker_provider):
    from swdb.cli import Failure
    from swdb.store import Store
    other = Store(seed.records).get(seed.candidate, "candidate")
    repair = {"kind": "counterexample_repair", "setting": "evaluation", "round": 1, "proof_record": "proof.x",
              "refuted_candidate": other["id"], "refuted_tree_sha256": other["artifact"]["sha256"],
              "counterexample": COUNTEREXAMPLE, "refuted_patch": Path(other["diff"]).read_text()}
    with pytest.raises(Failure, match=AUTHORS_REFUSAL):
        _guarded_workspace(seed, marker_provider, repair)
    assert not marker_provider[1].exists()


# --- refuted but uncertified (O1, O5) ----------------------------------------------------------------

def test_an_evaluation_repair_run_takes_a_refuted_record_of_a_candidate_that_failed_certification(seed):
    authors = seed.made["authors"]
    assert _level(seed, authors)["certification_level"] != "certified"
    outcome = _loop(seed, seed.prove(authors), refute_rounds={1}, setting="evaluation")
    assert outcome["state"] == "repaired" and outcome["calls"] == 2 and outcome["cap"] == 5
    first = seed.read(outcome["chain"][0]["proposal"], "proposals")
    assert first["repair_lineage"]["refuted_candidate"] == authors and first["repair_lineage"]["reverted_repair"] is False
    assert first["attempts"][0]["contract_match"]["reverted_repair"] is False
    assert seed.swdb("validate").returncode == 0, seed.swdb("validate").stderr


def test_outside_an_evaluation_repair_run_a_refuted_uncertified_candidate_is_refused_before_any_call(seed):
    from swdb.cli import Failure
    proof = seed.prove(seed.made["authors"])
    before = _proposals(seed)
    result = seed.repair(proof, ok=False)                                   # ArchEvolve mode
    assert result.returncode == 1 and "not certified" in result.stderr
    with pytest.raises(Failure, match="not certified"):                    # a campaign (14 calls the loop)
        _loop(seed, proof, refute_rounds=set(), setting="campaign")
    assert seed.calls_made() == [] and _proposals(seed) == before
