"""Run fields, the job block and repair lineage (Probata proof of concept ticket 12).

Created: 2026-10-14 ET. Seams 2 and 4 of the formal-verification map's spec: `swdb prove`,
`swdb validate` and `swdb build`. Fixture records only (evidence_kind contract_fixture); no verifier
runs. The certified fixture candidate artifact and its proposal come from ticket 04's seed (record
closure of its roots, LR-03); proof records start from the record `swdb prove` writes.
"""

import copy
import json
import shutil
import sqlite3

import pytest
import yaml

from conftest import run_swdb
from test_proof_records import ASSUMPTION, FUNCTION, proof_seed  # noqa: F401  (the certified fixture candidate)

ONE = {"threads": 1, "vertices": 3, "edges": 3}
PIN = {"kind": "codex", "model": "gpt-5.6-sol", "effort": "xhigh"}
JOB_FIELDS = ("adapter", "host", "worker_core", "wall_seconds", "cpu_seconds", "batch_load", "peak_rss_bytes",
              "batch", "position")


@pytest.fixture
def seed(proof_seed, tmp_path):
    source, candidate = proof_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidate)


class Seed:
    def __init__(self, root, candidate):
        self.root, self.candidate = root, candidate
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args)

    def prove(self, *extra, ok=True, **script):
        script.setdefault("verdict", "proven")
        script.setdefault("bounds", ONE)
        script.setdefault("assumptions", [ASSUMPTION])
        path = self.root / f"script-{len(list(self.root.glob('script-*')))}.yaml"
        path.write_text(yaml.safe_dump(script))
        result = self.swdb("prove", "--candidate", self.candidate, "--function", FUNCTION, "--adapter", "scripted",
                           "--script", path, "--runs-dir", self.runs, "--format", "json", *extra)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout)["record"] if ok else result

    def path(self, rid, kind="proofs"):
        return self.records / kind / f"{rid}.yaml"

    def read(self, rid, kind="proofs"):
        return yaml.safe_load(self.path(rid, kind).read_text())

    def write(self, record, kind="proofs"):
        self.path(record["id"], kind).write_text(yaml.safe_dump(record, sort_keys=False))
        return record["id"]

    def validate(self):
        return self.swdb("validate")


PIN_ARGS = ("--run-index", "2", "--provider-kind", "codex", "--provider-model", "gpt-5.6-sol",
            "--provider-effort", "xhigh")


def _fails(seed, *words):
    result = seed.validate()
    assert result.returncode == 1, result.stdout
    for word in words:
        assert word in result.stderr, result.stderr
    return result


# --- the job block ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", JOB_FIELDS)
def test_a_job_block_missing_a_field_fails_validation(seed, field):
    record = seed.prove()
    del record["job"][field]
    seed.write(record)
    _fails(seed, field)


def test_prove_writes_every_job_field_measured_on_the_mac(seed):
    job = seed.prove()["job"]
    assert set(job) == set(JOB_FIELDS)
    assert job["adapter"] == "scripted" and job["host"] == "mac"
    assert job["worker_core"] == "unpinned"                  # macOS pins no job to a core
    assert job["wall_seconds"] >= 0 and job["cpu_seconds"] >= 0 and job["peak_rss_bytes"] > 0
    assert set(job["batch_load"]) == {"start", "end"} and min(job["batch_load"].values()) >= 0
    assert job["position"] == 1 and job["batch"].startswith("batch.")


def test_peak_rss_is_the_one_the_adapter_reads_from_its_watchdog(seed):
    """An adapter that runs its tool under the RSS watchdog reports the watchdog's peak; the record keeps it."""
    assert seed.prove(peak_rss_bytes=123456789)["job"]["peak_rss_bytes"] == 123456789


def test_a_skip_record_has_the_same_job_block(seed):
    result = seed.swdb("prove", "--candidate", seed.candidate, "--function", FUNCTION, "--adapter", "scripted",
                       "--skip", "no_contract_proof", "--runs-dir", seed.runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    job = json.loads(result.stdout)["record"]["job"]
    assert set(job) == set(JOB_FIELDS) and job["wall_seconds"] == 0 and job["worker_core"] == "unpinned"


def test_a_proof_record_written_before_ticket_12_still_validates_and_builds(seed):
    """04's form: worker_core null, batch_load a bare start sample, no run fields."""
    record = seed.prove()
    record["job"].update(worker_core=None, batch_load=1.25)
    seed.write(record)
    assert seed.validate().returncode == 0, seed.validate().stderr
    assert seed.swdb("build").returncode == 0


@pytest.mark.parametrize("field, value", [("wall_seconds", -0.5), ("cpu_seconds", -1), ("peak_rss_bytes", -1),
                                          ("batch_load", {"start": -0.1, "end": 1.0}), ("position", 0)])
def test_a_negative_measurement_fails_validation(seed, field, value):
    record = seed.prove()
    record["job"][field] = value
    seed.write(record)
    _fails(seed, field)


# --- run fields on proof records (S10) ----------------------------------------------------------

def test_a_proof_hint_run_carries_run_index_and_provider_pin_on_its_proof_record(seed):
    record = seed.prove(*PIN_ARGS)
    assert record["run_index"] == 2 and record["provider_pin"] == PIN
    assert seed.validate().returncode == 0


def test_a_bounded_job_with_no_provider_call_carries_no_run_fields(seed):
    record = seed.prove()
    assert "run_index" not in record and "provider_pin" not in record


@pytest.mark.parametrize("change, word", [
    ({"run_index": 4}, "run_index"),
    ({"run_index": 0}, "run_index"),
    ({"provider_pin": {"kind": "codex", "model": "gpt-5.6-sol"}}, "effort"),
    ({"provider_pin": {"kind": "codex", "effort": "xhigh"}}, "model"),
])
def test_a_proof_record_with_a_bad_run_field_fails_validation(seed, change, word):
    record = seed.prove(*PIN_ARGS)
    record.update(change)
    seed.write(record)
    _fails(seed, word)


def test_prove_refuses_a_partial_provider_pin(seed):
    result = seed.prove("--run-index", "1", "--provider-kind", "codex", ok=False)
    assert result.returncode == 2 and "provider" in result.stderr


# --- proposals: run fields and repair lineage --------------------------------------------------

REPAIR = "test-proposal.repair-1"
COUNTEREXAMPLE = {"source": 0, "graph": "3 vertices, 2 edges", "differs_at": "parent[2]"}


def _proposal(seed, **fields):
    """The repaired candidate's proposal: the seed's proposal under a new ID, plus `fields`."""
    record = seed.read("test-proposal", "proposals")
    record["id"] = REPAIR
    record.pop("candidate")
    record.update(fields)
    return seed.write(record, "proposals")


def _refuted(seed, candidate=None):
    """A refuted proof record (counterexample inline) of `candidate`'s proof unit."""
    record = seed.prove(verdict="refuted", counterexample=COUNTEREXAMPLE)
    if candidate is not None:
        record["subject"]["candidate"] = candidate
        seed.write(record)
    return record["id"]


def _lineage(seed, **change):
    lineage = {"refuted_candidate": seed.candidate, "counterexample_record": _refuted(seed), "round": 1,
               "reverted_repair": False}
    lineage.update(change)
    return {key: value for key, value in lineage.items() if value is not None}


@pytest.mark.parametrize("index", [1, 2, 3])
def test_a_proposal_accepts_a_run_index_and_provider_pin(seed, index):
    _proposal(seed, run_index=index, provider_pin=PIN)
    assert seed.validate().returncode == 0, seed.validate().stderr


@pytest.mark.parametrize("fields, word", [
    ({"run_index": 0}, "run_index"),
    ({"run_index": 4}, "run_index"),
    ({"provider_pin": {"kind": "codex", "effort": "xhigh"}}, "model"),
    ({"provider_pin": {"kind": "codex", "model": "gpt-5.6-sol"}}, "effort"),
])
def test_a_proposal_with_a_bad_run_field_fails_validation(seed, fields, word):
    _proposal(seed, **fields)
    _fails(seed, REPAIR, word)


def test_a_proposal_with_repair_lineage_validates(seed):
    _proposal(seed, repair_lineage=_lineage(seed), run_index=1, provider_pin=PIN)
    assert seed.validate().returncode == 0, seed.validate().stderr


def test_repair_lineage_naming_a_missing_proof_record_fails(seed):
    _proposal(seed, repair_lineage=_lineage(seed, counterexample_record="proof.does-not-exist"))
    _fails(seed, REPAIR, "counterexample_record", "does not exist")


@pytest.mark.parametrize("script", [
    {"verdict": "proven"},
    {"verdict": "not_proven", "failure_class": "unknown", "unreplayed_counterexample": COUNTEREXAMPLE},
])
def test_repair_lineage_naming_a_record_that_is_not_a_refutation_fails(seed, script):
    """A counterexample that did not replay is never a refutation and never reaches repair."""
    rid = seed.prove(**script)["id"]
    _proposal(seed, repair_lineage=_lineage(seed, counterexample_record=rid))
    _fails(seed, REPAIR, "counterexample_record", "refutation")


def test_repair_lineage_naming_a_refutation_of_another_candidate_fails(seed):
    other = seed.read(seed.candidate, "candidates")
    other["id"] = "test-proposal.candidate-2"
    seed.write(other, "candidates")
    _proposal(seed, repair_lineage=_lineage(seed, counterexample_record=_refuted(seed, other["id"])))
    _fails(seed, REPAIR, "counterexample_record", seed.candidate)


@pytest.mark.parametrize("change, word", [({"reverted_repair": None}, "reverted_repair"), ({"round": 0}, "round")])
def test_repair_lineage_without_its_flag_or_with_round_0_fails(seed, change, word):
    _proposal(seed, repair_lineage=_lineage(seed, **change))
    _fails(seed, REPAIR, word)


# --- swdb build ---------------------------------------------------------------------------------

def _sql(seed, query):
    result = seed.swdb("sql", query, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _lanl(seed):
    """Every LANL core table's columns and rows (no `swdb_` prefix), read from the built file."""
    con = sqlite3.connect(f"file:{seed.root / 'build' / 'swdb.sqlite'}?mode=ro", uri=True)
    try:
        names = [n for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                 if not n.startswith(("swdb_", "sqlite_"))]
        return {n: ([c[1] for c in con.execute(f'PRAGMA table_info("{n}")')],
                    sorted(map(repr, con.execute(f'SELECT * FROM "{n}"')))) for n in names}
    finally:
        con.close()


def test_build_loads_run_fields_job_blocks_and_repair_lineage_into_the_swdb_extension_only(seed):
    assert seed.swdb("build").returncode == 0
    lanl = _lanl(seed)
    assert lanl
    hinted = seed.prove(*PIN_ARGS)["id"]
    bounded = seed.prove()["id"]
    lineage = _lineage(seed, round=2, reverted_repair=True)
    _proposal(seed, repair_lineage=lineage, run_index=3, provider_pin={**PIN, "kind": "claude",
                                                                        "model": "claude-sonnet-5-5", "effort": "high"})
    assert seed.swdb("build").returncode == 0, seed.swdb("build").stderr
    assert _lanl(seed) == lanl                                # no new field, no new row in a LANL core table
    runs = _sql(seed, "SELECT record, record_kind, run_index, provider_kind, provider_model, provider_effort "
                      "FROM swdb_run_fields ORDER BY record_kind, record")
    assert runs == [
        {"record": hinted, "record_kind": "proof", "run_index": 2, "provider_kind": "codex",
         "provider_model": "gpt-5.6-sol", "provider_effort": "xhigh"},
        {"record": REPAIR, "record_kind": "proposal", "run_index": 3, "provider_kind": "claude",
         "provider_model": "claude-sonnet-5-5", "provider_effort": "high"}]
    (repair,) = _sql(seed, "SELECT * FROM swdb_repair_lineage")
    assert repair == {"proposal": REPAIR, "refuted_candidate": seed.candidate,
                      "counterexample_record": lineage["counterexample_record"], "round": 2, "reverted_repair": 1}
    jobs = _sql(seed, "SELECT * FROM swdb_proof_jobs WHERE proof = '%s'" % bounded)
    record = seed.read(bounded)["job"]
    assert jobs == [{"proof": bounded, "adapter": "scripted", "host": "mac", "worker_core": "unpinned",
                     "wall_seconds": record["wall_seconds"], "cpu_seconds": record["cpu_seconds"],
                     "batch_load_start": record["batch_load"]["start"], "batch_load_end": record["batch_load"]["end"],
                     "peak_rss_bytes": record["peak_rss_bytes"], "batch": record["batch"], "position": 1}]
    assert _sql(seed, "SELECT count(*) AS n FROM swdb_proof_jobs")[0]["n"] == 3     # every proof record has one


def test_a_job_block_written_before_ticket_12_loads_with_no_end_load(seed):
    record = seed.prove()
    record["job"].update(worker_core=None, batch_load=1.25)
    seed.write(record)
    assert seed.swdb("build").returncode == 0
    (row,) = _sql(seed, "SELECT worker_core, batch_load_start, batch_load_end FROM swdb_proof_jobs")
    assert row == {"worker_core": None, "batch_load_start": 1.25, "batch_load_end": None}


def test_a_proposal_written_before_ticket_12_still_validates(seed):
    assert "repair_lineage" not in seed.read("test-proposal", "proposals")
    assert seed.validate().returncode == 0
