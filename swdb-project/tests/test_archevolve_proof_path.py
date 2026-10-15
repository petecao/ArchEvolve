"""ArchEvolve mode's proof path and the handoff's `certification_level` block (Probata PoC ticket 18).

Created: 2026-10-14 ET. Seams of the formal-verification map's spec: the proof command (`swdb prove
--proof-path`, seam 1), `swdb candidate-level` (seam 2), and the existing record seams (seam 4): the
`evaluation_result` handoff envelope, `swdb validate`, `swdb build` and `swdb certify`'s derived-
implementation hook. A scripted verifier (`--adapter scripted` with a proof plan), a scripted
certification (the scripted-certify pattern of tickets 02 and 19) and ticket 13's scripted provider stand
in; no real verifier, certification run or provider runs. Every record here is a contract fixture.
"""

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_counterexample_repair import ANCHOR, FIXTURE_PROVIDER, _offload
from test_proof_records import CONTRACT, FUNCTION, _certify, _library_roots
from testkit.bfs_native import PROGRAM
from testkit.library_promotion import promote
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

ONE = {"threads": 1, "vertices": 3, "edges": 3}            # the single-thread minimum bounds (fixture)
MULTI = {"threads": 2, "vertices": 4, "edges": 4}          # the multi-thread minimum bounds (fixture)
K = 3                                                       # the fixture method version's civl_k
SPEED = "Says nothing about speed."
STAGING = "contract.bfs_tdstep_frontier_staging"           # an enabling contract (no offload)


# --- the seed: certified, uncertified and rejected fixture candidate artifacts, one evaluation ------

@pytest.fixture(scope="module")
def path_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("archevolve-proof-seed")
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10",
                                                  "packing", "loop_tiling"}))
    shutil.copytree(REPO / "library", path / "library")
    (path / "library" / "methods").mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", path / "library" / "methods")
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    # Ticket 63 (2026-10-14 ET): ArchEvolve mode's proof path takes shared certified contracts only.
    promote(records.path, path / "library", CONTRACT)
    promote(records.path, path / "library", STAGING)
    made = {}
    for key, rid, verdict in (("certified", "test-proposal", "certified"), ("rejected", "rejected-proposal", "failed"),
                              ("uncertified", "uncertified-proposal", None), ("staging", "staging-proposal", None)):
        submitted = records.swdb("submit", request(ANCHOR, _offload(f"Fixture{key.title()}"), id=rid),
                                 "--runs-dir", runs, "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        made[key] = json.loads(submitted.stdout)["candidate"]
        if verdict:
            _certify(records.path, path, made[key], f"certification.{rid}", verdict)
    made["evaluation"] = _evaluate(records, path, runs, made["certified"])
    made["evaluation_uncertified"] = _evaluate(records, path, runs, made["uncertified"], "eval-uncertified")
    _contract_proofs(path, made["certified"])
    return path, made


def _evaluate(records, path, runs, candidate, rid="eval-proof-path"):
    """One native evaluation of the candidate artifact with the external compiler fixture (no gain claim)."""
    import socket
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="native-testhost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/native-testhost.yaml", machine)
    compiler = path / "fixture-cxx"
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({PROGRAM!r}); p.chmod(0o755)\n")
    compiler.chmod(0o755)
    request = {"message_version": "1.0", "id": rid, "candidate": candidate, "machine": "native-testhost",
               "threads": 1, "sources": [0], "repetitions": 1, "roi": "bfs.complete_call.v1", "fixture": True,
               "comparison_baseline": "gapbs-bfs-do", "build": {"compiler": str(compiler), "flags": ["-std=c++11", "-O2"]},
               "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 60},
               "workload": {"family": "contract_fixture", "graph": {"num_vertices": 5, "directed": True,
                                                                    "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}}}
    file = path / f"{rid}.yaml"
    file.write_text(yaml.safe_dump(request))
    result = records.swdb("evaluate", file, "--runs-dir", runs, "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)["id"]


def _proof_template(path, candidate):
    """One record written by `swdb prove` on the seed (then removed): the shape fixture records start from."""
    script = path / "template-script.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": ONE, "assumptions": [TOOL]}))
    result = run_swdb("prove", "--records", path / "records", "--candidate", candidate, "--function", FUNCTION,
                      "--adapter", "scripted", "--script", script, "--runs-dir", path / "template-runs",
                      "--format", "json")
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    (path / "records" / out["path"]).unlink()
    return out["record"]


TOOL = {"kind": "trusted_tool", "reference": {"id": "scripted-verifier", "sha256": "0" * 64},
        "sentence": "The scripted verifier adapter stands in for the verifiers (contract fixture)."}


def _contract_proofs(path, candidate):
    """The contract's contract proof (contract fixture): a proven unit postcondition over unbounded data and
    threads, and the single- and multi-thread minimum-bounds derivations."""
    from swdb.library import Library
    template = _proof_template(path, candidate)
    pin = {"id": CONTRACT, "sha256": Library(path / "library").content_sha256(CONTRACT)}
    na = {"not_applicable": "A contract-fixture contract proof pins no such version."}
    rows = [("unit_postcondition", "unit", {"threads": "unbounded", "vertices": "unbounded", "edges": "unbounded"}),
            ("minimum_bounds_derivation", "minimum-1", ONE), ("minimum_bounds_derivation", "minimum-k", MULTI)]
    for position, (part, tag, bounds) in enumerate(rows, start=1):
        record = copy.deepcopy(template)
        record.update(id=f"proof.t18.contract.{tag}", subject={"kind": "contract_proof_part", "id": CONTRACT, "part": part},
                      verdict="proven", bounds=bounds, assumptions=[TOOL])
        record["pins"].update(code=dict(pin), contract=dict(pin), baseline_function=dict(na))
        record["job"] = dict(record["job"], batch="batch.t18.contract", position=position)
        (path / "records" / "proofs").mkdir(exist_ok=True)
        (path / "records" / "proofs" / f"{record['id']}.yaml").write_text(yaml.safe_dump(record, sort_keys=False))


class Seed:
    def __init__(self, root, made):
        self.root, self.made = root, made
        self.candidate = made["certified"]
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql", "handoff-message"} else []
        return run_swdb(command, "--records", self.records, *db, *args)

    def plan(self, *rows, name="plan"):
        """A scripted proof plan: one row per candidate artifact of the repair chain (the last repeats)."""
        path = self.root / f"{name}.yaml"
        path.write_text(yaml.safe_dump({"plan": "archevolve_proof_fixture.1", "candidates": list(rows)}))
        return path

    def path(self, step, plan, candidate=None, *extra, ok=True):
        result = self.swdb("prove", "--proof-path", step, "--candidate", candidate or self.candidate,
                           "--function", FUNCTION, "--adapter", "scripted", "--plan", plan,
                           "--runs-dir", self.runs, "--format", "json", *extra)
        if ok:
            assert result.returncode == 0, result.stderr + result.stdout
            return json.loads(result.stdout)
        return result

    def read(self, rid, kind="proofs"):
        return yaml.safe_load((self.records / kind / f"{rid}.yaml").read_text())

    def proofs_of(self, candidate=None):
        candidate = candidate or self.candidate
        return sorted(p.stem for p in (self.records / "proofs").glob("*.yaml")
                      if (yaml.safe_load(p.read_text()).get("subject") or {}).get("candidate") == candidate)

    def level(self, candidate=None):
        result = self.swdb("candidate-level", candidate or self.candidate, "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)


@pytest.fixture
def seed(path_seed, tmp_path):
    source, made = path_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, made)


# --- same gate ---------------------------------------------------------------------------------------

def test_a_certified_candidate_runs_both_bounded_rungs_at_its_contract_minimum_bounds_through_swdb_prove(seed):
    out = seed.path("bounded", seed.plan({"threads_1": "proven", "threads_k": "proven"}))
    gate = out["gate"]
    # The method version's per-candidate budgets, as in Extensa mode: 15 minutes per job, k = 3.
    assert gate["budget_minutes"] == 15 and gate["k"] == K
    assert gate["method_version"]["id"] == "method.contract-fixture-1" and gate["refuted"] is False
    jobs = {job["rung"]: job for job in gate["jobs"]}
    assert jobs["threads_1"]["bounds"] == ONE
    assert jobs["threads_k"]["bounds"] == {**MULTI, "threads": K}       # the one exception to "minimum only"
    assert jobs["threads_1"]["minimum_bounds"] == "proof.t18.contract.minimum-1"
    for job in jobs.values():
        record = seed.read(job["record"])
        assert record["verdict"] == "proven" and record["bounds"] == job["bounds"]
        assert record["pins"]["minimum_bounds"]["id"] == job["minimum_bounds"]
        assert record["subject"] == {"kind": "candidate_proof_unit", "candidate": seed.candidate, "function": FUNCTION}
    assert out["final_candidate"] == seed.candidate and out["counterexample_repair"] is None
    assert seed.level()["level"] == "proven_within_bounds_threads_k"


@pytest.mark.parametrize("key", ["uncertified", "rejected"])
def test_an_uncertified_or_rejected_candidate_runs_no_proof_step(seed, key):
    for step in ("bounded", "unbounded"):
        result = seed.path(step, seed.plan({}), seed.made[key], ok=False)
        assert result.returncode == 1 and "runs no proof step" in result.stderr, result.stderr
    assert seed.proofs_of(seed.made[key]) == []


# --- refutation calls 13's repair loop ------------------------------------------------------------------

class ScriptedCertify:
    """`swdb.certification.certify`, scripted: one persisted contract-fixture certification per call."""

    def __init__(self, verdict="certified"):
        self.calls, self.verdict = [], verdict

    def __call__(self, store, entry_id, *, candidate=None, library=None, **_kw):
        from swdb import workflow
        from swdb.library import Library
        self.calls.append(candidate)
        content = Library(Path(library)).content_sha256(entry_id)
        tree = store.get(candidate, "candidate")["artifact"]["sha256"]
        record = workflow.record(
            "certification", f"certification.scripted.{candidate}.{len(self.calls)}",
            entry={"id": entry_id, "content_sha256": content}, dependencies=[],
            candidate={"id": candidate, "contract": entry_id, "contract_sha256": content, "tree_sha256": tree},
            command={"version": "1.7"}, host={"hostname": "scripted"},
            matrix=[{"cell": "fixture", "status": "passed" if self.verdict == "certified" else "failed"}],
            negative_controls=[{"id": "fixture_control", "status": "rejected"}], verdict=self.verdict,
            evidence_basis="simulated", evidence_kind="contract_fixture", created_at="2026-10-14T13:40:00Z")
        workflow.persist(store.dir, record, create=True)
        return record


def _provider(seed):
    """Ticket 13's scripted rewriting provider; each call that opens adds one line to `calls.jsonl`."""
    plan = seed.root / "provider-plan.json"
    baseline = Path(seed.read("test-source", "source_snapshots")["artifact"]["path"]) / "src" / "bfs.cc"
    plan.write_text(json.dumps({"mode": "genuine", "calls": str(seed.root / "calls.jsonl"), "baseline": str(baseline)}))
    config = seed.root / "provider.yaml"
    config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": "codex",
                                      "command": [sys.executable, str(FIXTURE_PROVIDER), str(plan)],
                                      "timeout_s": 30, "total_seconds": 600}))
    return config


def _calls(seed):
    path = seed.root / "calls.jsonl"
    return path.read_text().splitlines() if path.exists() else []


def _in_process(capsys, *argv):
    """`swdb <argv>` in this process (so a scripted certification can stand in); returns (exit code, output)."""
    from swdb import cli
    capsys.readouterr()
    code = cli.main([str(a) for a in argv])
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip().startswith("{") else out)


def _bounded_in_process(seed, capsys, plan, *extra):
    return _in_process(capsys, "prove", "--records", seed.records, "--proof-path", "bounded", "--candidate",
                       seed.candidate, "--function", FUNCTION, "--adapter", "scripted", "--plan", plan,
                       "--runs-dir", seed.runs, "--format", "json", *extra)


def test_a_refutation_on_this_modes_gate_calls_the_repair_loop_and_each_repair_comes_back_through_the_gate(
        seed, monkeypatch, capsys):
    certify = ScriptedCertify()
    monkeypatch.setattr("swdb.certification.certify", certify)
    # Row 0 (the submitted candidate artifact) and row 1 (the first repair) are refuted; row 2 is not.
    plan = seed.plan({"threads_1": "refuted"}, {"threads_k": "refuted"}, {})
    code, out = _bounded_in_process(seed, capsys, plan, "--provider-config", _provider(seed))
    assert code == 0, out
    assert out["gate"]["refuted"] is True and out["gate"]["refutations"]
    repair = out["counterexample_repair"]
    assert repair["state"] == "repaired" and repair["calls"] == 2 == len(_calls(seed))
    assert repair["cap"] == 5                                      # the method version's rounds (13's cap)
    first, second = out["repairs"]
    assert first["trigger"] == out["gate"]["refutations"][0]
    assert certify.calls == [first["candidate"], second["candidate"]]
    for row, refuted in ((first, True), (second, False)):          # each repair ran this mode's gate
        assert row["gate"]["refuted"] is refuted
        assert {job["rung"] for job in row["gate"]["jobs"]} == {"threads_1", "threads_k"}
        proposal = seed.read(seed.read(row["candidate"], "candidates")["proposal"], "proposals")
        assert proposal["repair_budget"]["setting"] == "archevolve"
    assert second["trigger"] == first["gate"]["refutations"][0]
    assert out["final_candidate"] == second["candidate"]
    assert seed.level(second["candidate"])["level"] == "proven_within_bounds_threads_k"
    assert seed.level()["refuted"]["flag"] is True


def test_control_a_candidate_the_gate_does_not_refute_opens_no_repair(seed, monkeypatch, capsys):
    certify = ScriptedCertify()
    monkeypatch.setattr("swdb.certification.certify", certify)
    code, out = _bounded_in_process(seed, capsys, seed.plan({"threads_1": "timeout"}), "--provider-config",
                                    _provider(seed))
    assert code == 0 and out["gate"]["refuted"] is False
    assert out["counterexample_repair"] is None and out["repairs"] == [] and _calls(seed) == []
    assert certify.calls == [] and out["final_candidate"] == seed.candidate


# --- the unbounded rung (S6) ------------------------------------------------------------------------------

def _drop_minimum_bounds(seed):
    for tag in ("minimum-1", "minimum-k"):
        (seed.records / "proofs" / f"proof.t18.contract.{tag}.yaml").unlink()


@pytest.mark.parametrize("bounded_row, minimum", [
    ({"threads_1": "proven", "threads_k": "proven"}, True),
    ({"threads_1": "timeout", "threads_k": "timeout"}, True),
    ({}, False),                                              # no minimum bounds: both rungs skipped
])
def test_a_candidate_the_bounded_rung_did_not_refute_goes_on_to_the_unbounded_rung_with_one_record(
        seed, bounded_row, minimum):
    if not minimum:
        _drop_minimum_bounds(seed)
    plan = seed.plan({**bounded_row, "unbounded": {"proven_at": "wp"}})
    gate = seed.path("bounded", plan)["gate"]
    assert gate["refuted"] is False
    if not minimum:
        assert {job.get("skip_reason") for job in gate["jobs"]} == {"no_minimum_bounds"}
    before = set(seed.proofs_of())
    out = seed.path("unbounded", plan)
    (job,) = out["jobs"]
    assert set(seed.proofs_of()) - before == {job["record"]}            # one proof record
    record = seed.read(job["record"])
    assert record["verdict"] == "proven" and set(record["bounds"].values()) == {"unbounded"}
    assert out["budgets"] == {"hint_rounds": 10, "hint_loop_wall_minutes": 60}   # the method version's
    assert job["stages"] == ["wp"] and out["level"] == "proven_unbounded" == seed.level()["level"]


def test_a_refuted_candidate_never_reaches_the_unbounded_rung(seed):
    plan = seed.plan({"threads_1": "refuted", "unbounded": {"proven_at": "wp"}})
    assert seed.path("bounded", plan)["gate"]["refuted"] is True
    before = seed.proofs_of()
    result = seed.path("unbounded", plan, ok=False)
    assert result.returncode == 1 and "never reaches the unbounded rung" in result.stderr, result.stderr
    assert seed.proofs_of() == before


def test_the_unbounded_rung_waits_for_the_bounded_gate(seed):
    result = seed.path("unbounded", seed.plan({"unbounded": {"proven_at": "wp"}}), ok=False)
    assert result.returncode == 1 and "has not run the bounded gate" in result.stderr, result.stderr
    assert seed.proofs_of() == []


def test_a_spent_hint_budget_leaves_the_unbounded_record_not_proven(seed):
    plan = seed.plan({"unbounded": {"proven_at": None}})
    seed.path("bounded", plan)
    (job,) = seed.path("unbounded", plan)["jobs"]
    assert job["verdict"] == "not_proven" and job["failure_class"] == "hint_budget_spent"
    assert job["stages"] == ["wp", "seeds", *range(1, 11)]               # WP, the contract seeds, 10 rounds
    assert seed.level()["level"] == "proven_within_bounds_threads_k"


# --- the handoff's `certification_level` block ------------------------------------------------------------

def _handoff(seed, evaluation=None):
    result = seed.swdb("handoff-message", "evaluation_result", evaluation or seed.made["evaluation"], "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _prove(seed, bounded_row=None, unbounded=None):
    """Run both steps of the proof path with one scripted plan row."""
    plan = seed.plan({**(bounded_row or {}), "unbounded": {"proven_at": "wp", **(unbounded or {})}})
    seed.path("bounded", plan)
    return seed.path("unbounded", plan)


TOOL_SENTENCE = "scripted-verifier works correctly (a trusted tool, not checked)."


def test_block_when_proven_unbounded_shows_any_for_every_bound_the_assumptions_the_speed_sentence_and_the_records(seed):
    out = _prove(seed)
    message = _handoff(seed)
    assert message["format_version"] == "1.2"
    block = message["content"]["certification_level"]
    assert block["level"] == "proven_unbounded" and block["proven"] is True
    assert block["bounds"] == [{"dimension": "threads", "value": "any"}, {"dimension": "edges", "value": "any"},
                               {"dimension": "vertices", "value": "any"}]
    assert [a["sentence"] for a in block["assumptions"]] == [TOOL_SENTENCE]
    assert block["speed"] == SPEED
    assert block["proof_records"] == [out["jobs"][0]["record"]]
    assert block["text"] == ("Proven for every size and every thread count (threads: any; edges: any; vertices: any). "
                             f"Assumes: {TOOL_SENTENCE} {SPEED}")


def test_block_when_proven_within_bounds_shows_each_bound_value_with_the_thread_count(seed):
    seed.path("bounded", seed.plan({"threads_1": "proven", "threads_k": "timeout"}))
    block = _handoff(seed)["content"]["certification_level"]
    assert block["level"] == "proven_within_bounds_threads_1"
    assert block["bounds"] == [{"dimension": "threads", "value": 1}, {"dimension": "edges", "value": 3},
                               {"dimension": "vertices", "value": 3}]
    assert block["text"].startswith("Proven within bounds, one thread (threads: up to 1; edges: up to 3; vertices: up to 3).")
    assert block["proof_records"] == seed.level()["proven"]["records"]


def test_block_when_not_proven_gives_the_highest_level_reached_and_the_failure_class_in_words(seed):
    out = _prove(seed, {"threads_1": "timeout", "threads_k": "timeout"}, {"proven_at": None})
    block = _handoff(seed)["content"]["certification_level"]
    assert block["level"] == "certified" and block["proven"] is False and block["bounds"] is None
    assert block["highest_level_reached"] == "certified"
    assert {(f["class"], f["words"]) for f in block["failures"]} == {
        ("timeout", "the verifier ran out of time"), ("hint_budget_spent", "hint budget spent")}
    assert sorted(block["proof_records"]) == sorted(seed.proofs_of())
    assert out["jobs"][0]["record"] in block["proof_records"]
    assert block["text"] == ("Not proven. Highest level reached: certified. Proof attempts ended: hint budget spent; "
                             f"the verifier ran out of time. {SPEED}")


def test_block_of_a_refuted_candidate_says_refuted_in_words(seed):
    seed.path("bounded", seed.plan({"threads_1": "refuted"}))
    block = _handoff(seed)["content"]["certification_level"]
    assert block["level"] == "certified" and block["proven"] is False
    assert ("refuted", "refuted: the verifier found a counterexample") in {(f["class"], f["words"]) for f in block["failures"]}


def test_an_uncertified_candidates_block_shows_the_level_certification_gives(seed):
    block = _handoff(seed, seed.made["evaluation_uncertified"])["content"]["certification_level"]
    assert block["level"] == "uncertified" and block["proven"] is False and block["proof_records"] == []
    assert block["text"] == f"Not proven. Highest level reached: uncertified. No proof attempt yet. {SPEED}"


def _assume(kind, ident, sentence):
    return {"kind": kind, "reference": {"id": ident, "sha256": "b" * 64}, "sentence": sentence}


PLANTED = "PLANTED free text that only a template may replace"
SEVEN = [_assume(kind, ident, f"{PLANTED} ({kind}).") for kind, ident in (
    ("assumed_clause", "contract.bfs_read_offload#L3"), ("proof_semantics", "proof_semantics.v1"),
    ("summary", "intrinsic.dxc_gather"), ("reduction", "lemma.dx100-reduction"), ("trusted_tool", "clang-22.1.8"),
    ("written_proof", "theorem.parallel-composition"), ("platform_choice", "platform.float-as-reals"))]
SEVEN_SENTENCES = [
    "DX100 parent gathers return no value older than parent initialization (assumed; owner Eric).",
    "The hardware target follows its proof semantics proof_semantics.v1.",
    "intrinsic.dxc_gather behaves as its summary states (not proven in this job).",
    "The reduction lemma.dx100-reduction holds (it narrows what was checked).",
    "clang-22.1.8 works correctly (a trusted tool, not checked).",
    "theorem.parallel-composition holds as written (not yet machine-checked).",
    "The platform fixes platform.float-as-reals by choice.",
]


def test_every_assumption_kind_renders_from_its_fixed_template_and_planted_free_text_never_reaches_the_block(seed):
    _prove(seed, unbounded={"assumptions": SEVEN})
    message = _handoff(seed)
    block = message["content"]["certification_level"]
    sentences = {a["reference"]["id"]: a["sentence"] for a in block["assumptions"]}
    assert [sentences[a["reference"]["id"]] for a in SEVEN] == SEVEN_SENTENCES
    assert PLANTED not in json.dumps(message)
    assert all(sentence in block["text"] for sentence in SEVEN_SENTENCES)


def test_the_templates_cover_exactly_the_seven_assumption_kinds():
    from swdb import handoff_level, paths, vocab
    vocabs, _ = vocab.load_all(paths.VOCAB)
    assert set(handoff_level.TEMPLATES) == set(vocabs.entries["proof_assumption_kinds"]) and len(handoff_level.TEMPLATES) == 7


def _render_in_process(seed):
    from swdb import handoff
    from swdb.store import Store
    store = Store(seed.records)
    return handoff.evaluation_result(store, store.get(seed.made["evaluation"], "evaluation"))


def test_an_assumption_kind_with_no_template_stops_rendering_with_an_error(seed, monkeypatch):
    from swdb import handoff_level
    from swdb.cli import Failure
    _prove(seed, unbounded={"assumptions": SEVEN})
    assert _render_in_process(seed)["content"]["certification_level"]["proven"] is True
    monkeypatch.delitem(handoff_level.TEMPLATES, "reduction")
    with pytest.raises(Failure, match="no template for assumption kind reduction"):
        _render_in_process(seed)


@pytest.mark.parametrize("entry, words", [
    (_assume("assumed_clause", "contract.bfs_read_offload#L99", "Free text."), "no clause L99"),
    (_assume("trusted_tool", "clang trusts itself, and so should you", "Free text."), "not a reference ID"),
])
def test_an_assumption_the_templates_cannot_fill_stops_rendering_with_an_error(seed, entry, words):
    from swdb.cli import Failure
    _prove(seed, unbounded={"assumptions": [entry]})
    with pytest.raises(Failure, match=words):
        _render_in_process(seed)


def test_the_block_is_a_dated_snapshot_naming_the_level_rule_and_a_rendered_handoff_keeps_it(seed):
    import re
    _prove(seed)
    rendered = json.dumps(_handoff(seed))
    snapshot = json.loads(rendered)["content"]["certification_level"]["snapshot"]
    assert snapshot["level"] == "proven_unbounded" and snapshot["level_rule"] == "level-rule.4"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} ET", snapshot["at"])
    # A pin changes: a newer method version, so every proof record pins one that is no longer current.
    newer = yaml.safe_load((seed.root / "library" / "methods" / "contract-fixture-1.yaml").read_text())
    newer.update(id="method.contract-fixture-2", sequence=2)
    (seed.root / "library" / "methods" / "contract-fixture-2.yaml").write_text(yaml.safe_dump(newer))
    assert seed.level()["level"] == "certified"
    assert json.loads(rendered)["content"]["certification_level"]["snapshot"] == snapshot   # kept, dated
    again = _handoff(seed)["content"]["certification_level"]
    assert again["level"] == again["snapshot"]["level"] == "certified"


def _keys(value):
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def test_the_level_is_reported_never_ranked_and_never_changes_the_speed_claim(seed):
    before = _handoff(seed)["content"]
    _prove(seed)                                       # proven unbounded, and the evaluation shows no gain
    after = _handoff(seed)["content"]
    assert after["certification_level"]["level"] == "proven_unbounded"
    assert not _keys(after["certification_level"]) & {"rank", "score", "ranking"}
    assert after["performance_claim"] == before["performance_claim"] == "none"
    assert after["result_class"] == before["result_class"]
    assert {k: v for k, v in after.items() if k != "certification_level"} == \
        {k: v for k, v in before.items() if k != "certification_level"}


def test_a_proven_level_whose_records_cannot_be_resolved_stops_rendering(seed, monkeypatch):
    from swdb import level_rule
    from swdb.cli import Failure
    _prove(seed)
    real = level_rule.Rule.candidate

    def unresolvable(self, candidate_id):
        result = copy.deepcopy(real(self, candidate_id))
        result["proven"]["records"] = ["proof.t18.never-written"]
        return result

    monkeypatch.setattr(level_rule.Rule, "candidate", unresolvable)
    with pytest.raises(Failure, match="cannot be resolved"):
        _render_in_process(seed)


def test_a_block_missing_the_speed_sentence_stops_rendering(seed, monkeypatch):
    from swdb import handoff_level
    from swdb.cli import Failure
    real = handoff_level.block

    def silent(store, candidate_id, **kw):
        made = real(store, candidate_id, **kw)
        made["text"] = made["text"].replace(" " + SPEED, "")
        return made

    monkeypatch.setattr(handoff_level, "block", silent)
    with pytest.raises(Failure, match="Says nothing about speed"):
        _render_in_process(seed)


def _undated(message):
    message = copy.deepcopy(message)
    message["content"]["certification_level"]["snapshot"].pop("at")
    return message


def test_several_messages_render_from_one_validated_store_exactly_as_the_command_renders_them(seed):
    """The example driver renders every message from one validated snapshot (2026-10-14 ET): the whole store
    is validated once, not once per message, and each message equals `swdb handoff-message`'s."""
    from swdb import db, handoff
    _prove(seed)
    command = _handoff(seed)
    store = db.query_store(seed.records, seed.root / "build" / "swdb.sqlite")
    rendered = handoff.render(store, "evaluation_result", seed.made["evaluation"])
    assert _undated(json.loads(json.dumps(rendered))) == _undated(command)
    again = handoff.render(store, "evaluation_result", seed.made["evaluation_uncertified"])
    assert again["content"]["certification_level"]["level"] == "uncertified"


def test_the_proof_records_behind_the_block_pass_validate_and_build(seed):
    _prove(seed, unbounded={"assumptions": SEVEN})
    assert _handoff(seed)["content"]["certification_level"]["proven"] is True
    validated = seed.swdb("validate")
    assert validated.returncode == 0, validated.stderr
    built = seed.swdb("build")
    assert built.returncode == 0, built.stderr


# --- `swdb certify` records a derived implementation in ArchEvolve mode (ticket 19's gap) ----------------

def _certify_in_process(seed, capsys, contract, candidate):
    return _in_process(capsys, "certify", contract, "--candidate", candidate, "--records", seed.records,
                       "--library", seed.root / "library", "--runs-dir", seed.runs)


def test_certify_records_a_certified_enabling_rewrite_proposals_result_as_a_derived_implementation(
        seed, monkeypatch, capsys):
    certify = ScriptedCertify()
    monkeypatch.setattr("swdb.certification.certify", certify)
    candidate = seed.made["staging"]
    code, out = _certify_in_process(seed, capsys, STAGING, candidate)
    assert code == 0 and out["verdict"] == "certified", out
    assert out["derived_implementation"] == candidate + ".derived"
    derived = seed.read(candidate + ".derived", "implementations")
    assert derived["origin"] == {"kind": "derived", "derived_from": "gapbs-bfs-do",
                                 "description": derived["origin"]["description"]}
    (link,) = derived["rewrite_links"]
    assert link["contract"] == STAGING and link["certification"] == out["id"]
    assert link["predecessor_snapshot"]["id"] == "test-source"
    assert link["result"]["sha256"] == seed.read(candidate, "candidates")["artifact"]["sha256"]
    assert "mode" not in derived                                    # ArchEvolve mode: no Extensa tags
    validated = seed.swdb("validate")
    assert validated.returncode == 0, validated.stderr


@pytest.mark.parametrize("contract, verdict, note", [
    (CONTRACT, "certified", "not an enabling contract"),          # an offloading contract
    (STAGING, "failed", "the certification failed"),
])
def test_certify_records_no_derived_implementation_for_an_offload_or_a_failed_certification(
        seed, monkeypatch, capsys, contract, verdict, note):
    monkeypatch.setattr("swdb.certification.certify", ScriptedCertify(verdict))
    candidate = seed.made["staging"]
    code, out = _certify_in_process(seed, capsys, contract, candidate)
    assert code == (0 if verdict == "certified" else 1) and note in out["derived_note"], out
    assert "derived_implementation" not in out
    assert not (seed.records / "implementations" / f"{candidate}.derived.yaml").exists()
