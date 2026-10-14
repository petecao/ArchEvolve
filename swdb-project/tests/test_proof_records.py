"""Proof records through the scripted verifier adapter (Probata proof of concept, ticket 04).

Created: 2026-10-14 ET. Seams 1, 2 and 4 of the formal-verification map's spec: `swdb prove`,
`swdb candidate-level`, `swdb validate` and `swdb build`. Fixture records only (evidence_kind
contract_fixture); no real verifier runs. The certified fixture candidate artifact is built through
the public workflow (`source-snapshot`, `fixture-package`, `submit`) on the record closure of its
roots (LR-03), with the repository library beside the records folder.
"""

import json
import shutil
import sqlite3
import sys

import pytest
import yaml

from conftest import REPO, make_records, run_swdb
from testkit.bfs_protocol import _payload
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

CONTRACT = "contract.bfs_read_offload"
FUNCTION = "DOBFS"
JOB_FIELDS = {"adapter", "host", "worker_core", "wall_seconds", "cpu_seconds", "batch_load",
              "peak_rss_bytes", "batch", "position"}
PIN_KINDS = {"code", "contract", "baseline_function", "reference_semantics", "proof_semantics",
             "method_version", "summaries", "minimum_bounds", "predecessor_snapshot", "build_constants"}
ASSUMPTION = {"kind": "trusted_tool", "reference": {"id": "clang-22.1.8", "sha256": "a" * 64},
              "sentence": "clang 22.1.8 compiles the proof unit correctly."}


def _library_roots():
    from swdb.library import Library
    roots = set()
    for entry in Library(REPO / "library").entries.values():
        if entry.get("intrinsic_record"):
            roots.add(entry["intrinsic_record"])
        roots.update(entry.get("hardware_operations", []))
        roots.update(entry.get("strategies", []))
    return roots


@pytest.fixture(scope="module")
def proof_seed(tmp_path_factory):
    """A certified fixture candidate artifact, built once per module."""
    path = tmp_path_factory.mktemp("proof-seed")
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    submitted = records.swdb("submit", request(), "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    _certify(records.path, path, candidate, "certification.proof-fixture-pass", "certified")
    return path, candidate


@pytest.fixture
def seed(proof_seed, tmp_path):
    """A fresh copy of the seed (records and library side by side) for one test."""
    source, candidate = proof_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return _Seed(tmp_path, candidate)


class _Seed:
    def __init__(self, root, candidate):
        self.root, self.candidate = root, candidate
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args)

    def script(self, name="proven", **data):
        data.setdefault("verdict", "proven")
        data.setdefault("bounds", {"threads": 1, "vertices": 3, "edges": 3})
        data.setdefault("assumptions", [ASSUMPTION])
        path = self.root / f"script-{name}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path

    def prove(self, script, *extra, ok=True):
        result = self.swdb("prove", "--candidate", self.candidate, "--function", FUNCTION,
                           "--adapter", "scripted", "--script", script, "--runs-dir", self.runs,
                           "--format", "json", *extra)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout) if ok else result

    def proof_files(self):
        return sorted((self.records / "proofs").glob("*.yaml")) if (self.records / "proofs").exists() else []

    def read(self, path):
        return yaml.safe_load(path.read_text())

    def level(self):
        result = self.swdb("candidate-level", self.candidate, "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)


def _certify(records, tmp_path, candidate, rid, verdict):
    """A fixture certification of the contract's current content (as in test_extensa_boundary)."""
    from swdb.library import Library
    data = yaml.safe_load((records / "candidates" / f"{candidate}.yaml").read_text())
    content = Library(REPO / "library").content_sha256(CONTRACT)
    passed = verdict == "certified"
    record = {"kind": "certification", "schema_version": "0.4", "id": rid, "status": "draft",
              "created": "2026-10-14", "updated": "2026-10-14",
              "provenance": [{"id": "fixture", "kind": "agent_run", "description": "Contract fixture.", "uri": None}],
              "entry": {"id": CONTRACT, "content_sha256": content},
              "candidate": {"id": candidate, "contract": CONTRACT, "contract_sha256": content,
                            "tree_sha256": data["artifact"]["sha256"]},
              "command": {"version": "1.7"}, "host": {"hostname": "fixture"},
              "matrix": [{"cell": "fixture", "status": "passed" if passed else "failed"}],
              "negative_controls": [{"id": "fixture", "status": "rejected"}],
              "verdict": verdict, "evidence_basis": "simulated", "evidence_kind": "contract_fixture"}
    result = run_swdb("add", "--records", records, "--db", tmp_path / "build" / "swdb.sqlite",
                      _payload(tmp_path, rid, record))
    assert result.returncode == 0, result.stderr


# --- write ---------------------------------------------------------------------------

def test_prove_writes_one_proven_record_with_subject_pins_bounds_assumptions_and_job(seed):
    result = seed.prove(seed.script())
    files = seed.proof_files()
    assert len(files) == 1
    record = seed.read(files[0])
    assert record["kind"] == "proof" and record["id"] == result["record"]["id"]
    assert record["verdict"] == "proven" and record["evidence_kind"] == "contract_fixture"
    assert record["subject"] == {"kind": "candidate_proof_unit", "candidate": seed.candidate, "function": FUNCTION}
    assert "route" not in record
    candidate = seed.read(seed.records / "candidates" / f"{seed.candidate}.yaml")
    assert set(record["pins"]) == PIN_KINDS
    assert record["pins"]["code"] == {"id": seed.candidate, "sha256": candidate["artifact"]["sha256"]}
    from swdb.library import Library
    assert record["pins"]["contract"] == {"id": CONTRACT, "sha256": Library(REPO / "library").content_sha256(CONTRACT)}
    assert record["pins"]["summaries"] == [] and record["pins"]["build_constants"] == []
    for kind in ("method_version", "proof_semantics", "minimum_bounds", "predecessor_snapshot", "reference_semantics"):
        assert record["pins"][kind]["not_applicable"]          # explicit, never left out
    assert record["bounds"] == {"threads": 1, "vertices": 3, "edges": 3}
    assert record["assumptions"] == [ASSUMPTION]
    assert set(record["job"]) == JOB_FIELDS
    assert record["job"]["adapter"] == "scripted"
    if sys.platform == "darwin":
        assert record["job"]["host"] == "mac"
    assert record["job"]["position"] == 1 and record["job"]["wall_seconds"] >= 0
    assert "counterexample" not in record and "failure_class" not in record


COUNTEREXAMPLE = {"inputs": {"vertices": 3, "edges": [[0, 1], [1, 2]], "source": 0},
                  "violated": "parent[2] differs from the reference"}


def test_refuted_writes_its_counterexample_inline_and_not_proven_its_failure_class(seed):
    seed.prove(seed.script("refuted", verdict="refuted", counterexample=COUNTEREXAMPLE))
    seed.prove(seed.script("not-proven", verdict="not_proven", failure_class="timeout"))
    records = {r["verdict"]: r for r in map(seed.read, seed.proof_files())}
    assert sorted(records) == ["not_proven", "refuted"]          # one record per job
    assert records["refuted"]["counterexample"] == COUNTEREXAMPLE
    assert "failure_class" not in records["refuted"]
    assert records["not_proven"]["failure_class"] == "timeout"
    assert "counterexample" not in records["not_proven"]


def test_proving_again_writes_a_new_record_and_leaves_the_first_byte_identical(seed):
    first = seed.prove(seed.script())["path"]
    before = (seed.records / first).read_bytes()
    second = seed.prove(seed.script())["path"]
    assert second != first and len(seed.proof_files()) == 2
    assert (seed.records / first).read_bytes() == before
    assert seed.read(seed.records / second)["id"] != seed.read(seed.records / first)["id"]


def test_the_record_writer_refuses_to_replace_a_proof_record(seed):
    from swdb import writer
    from swdb.cli import Failure
    path = seed.records / seed.prove(seed.script())["path"]
    before = path.read_bytes()
    record = seed.read(path)
    record["notes"] = ["an edit"]
    with pytest.raises(Failure, match="never changes"):
        writer.commit(seed.records, replace=[record])
    assert path.read_bytes() == before


# --- validate --------------------------------------------------------------------------

def _validate(seed):
    return seed.swdb("validate")


def test_validate_accepts_every_written_verdict(seed):
    seed.prove(seed.script())
    seed.prove(seed.script("refuted", verdict="refuted", counterexample=COUNTEREXAMPLE))
    seed.prove(seed.script("not-proven", verdict="not_proven", failure_class="timeout"))
    result = _validate(seed)
    assert result.returncode == 0, result.stderr


def _drop(path):
    def change(record):
        *parents, last = path.split(".")
        node = record
        for name in parents:
            node = node[name]
        del node[last]
    return change


@pytest.mark.parametrize("change, field, reason", [
    (_drop("bounds.threads"), "bounds.threads", "thread count"),
    (lambda r: r["assumptions"][0].update(kind="hunch"), "assumptions[0].kind", "proof_assumption_kinds"),
    (lambda r: r["assumptions"][0].pop("sentence"), "assumptions[0].sentence", "plain sentence"),
    (lambda r: r["assumptions"][0].update(sentence="  "), "assumptions[0].sentence", "not empty"),
    *[(_drop(f"pins.{kind}"), f"pins.{kind}", "content-hash set") for kind in sorted(PIN_KINDS)],
    (lambda r: r.update(verdict="refuted"), "counterexample", "counterexample inline"),
    (lambda r: r.update(verdict="not_proven"), "failure_class", "failure class"),
    (lambda r: r.update(counterexample=COUNTEREXAMPLE), "counterexample", "only a refuted record"),
    (lambda r: r.update(failure_class="timeout"), "failure_class", "only a not-proven record"),
])
def test_validate_refuses_each_negative_control(seed, change, field, reason):
    path = seed.records / seed.prove(seed.script())["path"]
    record = seed.read(path)
    change(record)
    path.write_text(yaml.safe_dump(record, sort_keys=False))
    result = _validate(seed)
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if path.name in line and field in line]
    assert problem and reason in problem[0], result.stderr


# --- route field -----------------------------------------------------------------------

def _with(seed, change):
    """A proven record, then a fixture edit of its YAML (later tickets write these fields)."""
    path = seed.records / seed.prove(seed.script())["path"]
    record = seed.read(path)
    change(record)
    path.write_text(yaml.safe_dump(record, sort_keys=False))
    return path, record


@pytest.mark.parametrize("route", [None, "route_1", "route_3", "bounded_direct"])
def test_validate_accepts_no_route_and_each_route_on_a_candidate_proof_unit(seed, route):
    _with(seed, lambda r: r.update(route=route) if route else None)
    result = _validate(seed)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("change, field, reason", [
    (lambda r: r.update(route="route_2"), "route", "route_1 (direct), route_3 (lockstep) or bounded_direct"),
    (lambda r: r.update(route="route_1", subject={"kind": "library_summary", "id": "intrinsic.dxc_gather"}),
     "subject.kind", "only a candidate proof unit carries a proof route"),
])
def test_validate_refuses_an_unknown_route_or_a_route_on_another_subject(seed, change, field, reason):
    path, _record = _with(seed, change)
    result = _validate(seed)
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if path.name in line and field in line]
    assert problem and reason in problem[0], result.stderr


def test_a_non_candidate_subject_without_a_route_is_valid(seed):
    _with(seed, lambda r: r.update(subject={"kind": "library_summary", "id": "intrinsic.dxc_gather"}))
    result = _validate(seed)
    assert result.returncode == 0, result.stderr


# --- build ------------------------------------------------------------------------------

PROOF_TABLES = ("swdb_proofs", "swdb_proof_pins", "swdb_proof_assumptions", "swdb_proof_bounds")


def _build(seed):
    result = seed.swdb("build")
    assert result.returncode == 0, result.stderr
    return seed.root / "build" / "swdb.sqlite"


def _dump(db, lanl=False, tables=()):
    """Every row of the named tables (or of every LANL core table), read from the built file."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        names = [n for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
                 if (not n.startswith(("swdb_", "sqlite_")) if lanl else n in tables)]
        return {n: sorted(map(repr, con.execute(f'SELECT * FROM "{n}"'))) for n in names}
    finally:
        con.close()


def test_build_indexes_proof_records_in_the_swdb_extension_only(seed):
    lanl_before = _dump(_build(seed), lanl=True)
    assert lanl_before                                     # the LANL core exists
    seed.prove(seed.script())
    seed.prove(seed.script("refuted", verdict="refuted", counterexample=COUNTEREXAMPLE))
    path, _ = _with(seed, lambda r: r.update(route="route_3"))
    db = _build(seed)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT id, verdict, route, subject_kind, candidate, function, evidence_kind "
                           "FROM swdb_proofs ORDER BY verdict").fetchall()
        counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in PROOF_TABLES}
        routed = con.execute("SELECT route FROM swdb_proofs WHERE id = ?", (seed.read(path)["id"],)).fetchone()
    finally:
        con.close()
    assert [r[1] for r in rows] == ["proven", "proven", "refuted"]
    assert {r[3:] for r in rows} == {("candidate_proof_unit", seed.candidate, FUNCTION, "contract_fixture")}
    assert routed == ("route_3",) and sum(r[2] is None for r in rows) == 2
    # Per record: 8 single pins (no summaries, no build constants), 1 assumption, 3 bounds.
    assert counts == {"swdb_proofs": 3, "swdb_proof_pins": 24, "swdb_proof_assumptions": 3, "swdb_proof_bounds": 9}
    assert _dump(db, lanl=True) == lanl_before            # every LANL core table unchanged
    proof_rows = _dump(db, tables=PROOF_TABLES)
    db.unlink()
    assert _dump(_build(seed), tables=PROOF_TABLES) == proof_rows   # the YAML alone rebuilds them


# --- level -----------------------------------------------------------------------------

def _files(seed):
    return {p: p.read_bytes() for p in [*seed.proof_files(), seed.records / "candidates" / f"{seed.candidate}.yaml"]}


def test_a_proven_record_at_one_thread_reads_proven_within_bounds_computed_on_read(seed):
    assert seed.level()["level"] == "certified"
    rid = seed.prove(seed.script())["record"]["id"]
    before = _files(seed)
    level = seed.level()
    assert level["level"] == "proven_within_bounds"
    assert level["certification_level"] == "certified"
    assert level["proven"] == {"level": "proven_within_bounds", "bounds": {"threads": 1, "vertices": 3, "edges": 3},
                               "records": [rid]}
    assert level["proof_records"] == [rid]
    assert _files(seed) == before                          # nothing writes a level anywhere


def test_every_dimension_unbounded_reads_proven_unbounded(seed):
    rid = seed.prove(seed.script(bounds={"threads": "unbounded", "vertices": "unbounded"}))["record"]["id"]
    level = seed.level()
    assert level["level"] == "proven_unbounded"
    assert level["proven"]["records"] == [rid]
    assert level["proven"]["bounds"] == {"threads": "unbounded", "vertices": "unbounded"}


def _uncertified(seed):
    (seed.records / "certifications" / "certification.proof-fixture-pass.yaml").unlink()


def _rejected(seed):
    _certify(seed.records, seed.root, seed.candidate, "certification.proof-fixture-fail", "failed")


def _code_pin(seed):
    path = seed.proof_files()[0]
    record = seed.read(path)
    record["pins"]["code"]["sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(record, sort_keys=False))


def _contract_pin(seed):
    path = seed.proof_files()[0]
    record = seed.read(path)
    record["pins"]["contract"]["sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(record, sort_keys=False))


def _contract_content(seed):
    """The contract's content changes after the proof: its pin (and its certification) stop counting."""
    path = seed.root / "library" / "rewrite_contracts" / "bfs_read_offload.yaml"
    data = yaml.safe_load(path.read_text())
    data["provenance"]["intrinsic_specification"]["section"] = "5 (fixture revision)"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    from swdb.library import Library                       # re-pin the one entry derived from it
    derived = seed.root / "library" / "rewrite_contracts" / "bc_read_offload.yaml"
    data = yaml.safe_load(derived.read_text())
    data["provenance"]["derived_from"]["content_sha256"] = Library(seed.root / "library").content_sha256(CONTRACT)
    derived.write_text(yaml.safe_dump(data, sort_keys=False))


@pytest.mark.parametrize("change, expected", [
    (_uncertified, "uncertified"),
    (_rejected, "rejected"),
    (_code_pin, "certified"),
    (_contract_pin, "certified"),
    (_contract_content, "uncertified"),
])
def test_a_proven_record_stops_giving_a_proven_level(seed, change, expected):
    rid = seed.prove(seed.script())["record"]["id"]
    change(seed)
    assert _validate(seed).returncode == 0
    level = seed.level()
    assert level["level"] == level["certification_level"] == expected
    assert level["proven"] is None and level["proof_records"] == [rid]


@pytest.mark.parametrize("script", [
    {"verdict": "refuted", "counterexample": COUNTEREXAMPLE},
    {"verdict": "not_proven", "failure_class": "timeout"},
])
def test_a_refuted_or_not_proven_record_gives_no_proven_level(seed, script):
    seed.prove(seed.script("other", **script))
    level = seed.level()
    assert level["level"] == "certified" and level["proven"] is None


# --- evidence ----------------------------------------------------------------------------

def test_the_adapter_log_is_named_by_path_and_hash_and_the_scratch_is_gone(seed):
    import hashlib
    record = seed.prove(seed.script())["record"]
    log = record["evidence"]["adapter_log"]
    path = seed.runs.resolve() / record["id"] / "adapter.log"
    assert log["path"] == str(path) and REPO.resolve() not in path.parents
    assert log["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    scratch = [line.split(": ", 1)[1] for line in path.read_text().splitlines() if line.startswith("scratch used: ")]
    assert scratch, "the scripted adapter logs the scratch folder it used"
    assert not any((seed.runs / record["id"]).glob("scratch*"))      # deleted when the job ends
    assert sorted(p.name for p in (seed.runs / record["id"]).iterdir()) == ["adapter.log"]
    text = json.dumps(record)
    assert scratch[0] not in text and "scratch" not in text            # the record never names it


def test_prove_refuses_a_runs_folder_inside_the_repository(seed):
    result = seed.swdb("prove", "--candidate", seed.candidate, "--function", FUNCTION, "--adapter", "scripted",
                       "--script", seed.script(), "--runs-dir", REPO / "build" / "proof-runs")
    assert result.returncode == 2 and "outside the repository" in result.stderr
    assert not seed.proof_files() and not (REPO / "build" / "proof-runs").exists()
