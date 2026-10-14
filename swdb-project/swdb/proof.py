"""Proof records: `swdb prove`, the verifier adapter interface, and proven levels on read.

Created: 2026-10-14 ET (Probata proof of concept ticket 04, the proof record tracer).
Design: `.scratch/formal-verification-2026-10-09/spec.md` ("Records and levels", S1, S2),
map ticket 26 and ADR 0016. Format: docs/reference/format-v0.4-proof.md.

- `swdb prove` runs one proof job on one subject (here: a candidate artifact's proof unit)
  through one verifier adapter and writes one `proof` record into `records/proofs/`. A record
  is never edited (the writer refuses to replace one); proving again writes a new record.
- The adapter interface is the one the real tools use (tickets 21, 22): in, a `Job` (the
  `ProofUnit`, the summaries used, a scratch folder and the log path); out, a `Verdict`
  (proven; refuted with a counterexample; not proven with a failure class) with the bounds
  and assumption set it holds under. The scripted adapter reads its verdict from a file and
  is `contract_fixture` evidence only.
- The adapter's log stays in a runs folder outside the repo, named by path and sha256. The
  job's scratch folder is never named by the record and is deleted when the job ends.
- `proven_level` reads a candidate artifact's proven level from the records that count,
  computed on read and never stored (ADR 0016). This tracer checks only the code pin and the
  contract pin; ticket 10 adds every other pin kind and the versioned level rule.
"""

import datetime
import hashlib
import os
import resource
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from swdb import paths, yamlio
from swdb.cli import Failure, UsageError

VERDICTS = ("proven", "refuted", "not_proven")
UNBOUNDED = "unbounded"


# --- the adapter interface ----------------------------------------------------------

class AdapterError(Exception):
    """An adapter could not give a verdict in the interface's terms."""


@dataclass(frozen=True)
class ProofUnit:
    """One call of the function that holds a candidate artifact's rewrite site."""
    candidate: str
    function: str
    tree: str            # the candidate artifact's source tree (path on the run host)
    tree_sha256: str
    contract: str
    contract_sha256: str


@dataclass(frozen=True)
class Job:
    """What an adapter receives. `scratch` is deleted when the job ends; `log` is kept."""
    unit: ProofUnit
    summaries: tuple = ()          # pins {id, sha256, proof_record} of the summaries used
    scratch: Path = None
    log: Path = None


@dataclass(frozen=True)
class Verdict:
    """What an adapter returns: the verdict and what it holds under."""
    verdict: str
    bounds: dict
    assumptions: list = field(default_factory=list)
    counterexample: dict = None
    failure_class: str = None

    def __post_init__(self):
        if self.verdict not in VERDICTS:
            raise AdapterError(f"verdict must be one of {', '.join(VERDICTS)}, not {self.verdict!r}")
        if (self.verdict == "refuted") != bool(self.counterexample):
            raise AdapterError("a refuted verdict, and only a refuted verdict, carries a counterexample")
        if (self.verdict == "not_proven") != bool(self.failure_class):
            raise AdapterError("a not-proven verdict, and only a not-proven verdict, carries a failure class")
        if not isinstance(self.bounds, dict) or "threads" not in self.bounds:
            raise AdapterError("a verdict states its bounds, the thread count always among them")


class ScriptedAdapter:
    """The scripted verifier adapter: the verdict comes from a YAML script file.

    Script keys: `verdict`, `bounds`, `assumptions`, and `counterexample` (refuted) or
    `failure_class` (not proven). It uses the scratch folder as a real tool would, and logs."""
    name = "scripted"

    def __init__(self, script):
        if script is None:
            raise UsageError("the scripted adapter needs --script")
        try:
            self.script = yamlio.load(Path(script))
        except (OSError, ValueError) as exc:
            raise Failure(f"cannot read the adapter script {script}: {exc}") from None
        if not isinstance(self.script, dict):
            raise Failure(f"adapter script {script} must be a YAML mapping")
        self.source = Path(script)

    def run(self, job):
        (job.scratch / "scripted-work.txt").write_text(f"{job.unit.candidate} {job.unit.function}\n")
        verdict = Verdict(verdict=self.script.get("verdict"), bounds=self.script.get("bounds"),
                          assumptions=list(self.script.get("assumptions") or []),
                          counterexample=self.script.get("counterexample"),
                          failure_class=self.script.get("failure_class"))
        with open(job.log, "a", encoding="utf-8") as log:
            log.write(f"adapter: scripted\nscript: {self.source}\n"
                      f"unit: {job.unit.candidate} {job.unit.function}\n"
                      f"contract: {job.unit.contract} {job.unit.contract_sha256}\n"
                      f"scratch used: {job.scratch}\nverdict: {verdict.verdict}\n")
        return verdict


ADAPTERS = {"scripted": ScriptedAdapter}


# --- swdb prove -----------------------------------------------------------------------

def register_cli(commands):
    sub = commands.add_parser("prove", help="run one proof job on one candidate proof unit; write one proof record",
                              description="run one proof job on one candidate artifact's proof unit through a "
                                          "verifier adapter and write one proof record (never changed)")
    sub.add_argument("--records", type=Path, default=paths.RECORDS)
    sub.add_argument("--candidate", required=True, help="the candidate artifact")
    sub.add_argument("--function", required=True, help="the function that holds the rewrite site")
    sub.add_argument("--contract", help="the rewrite contract (default: the one its certification records name)")
    sub.add_argument("--adapter", choices=sorted(ADAPTERS), required=True)
    sub.add_argument("--script", type=Path, help="scripted adapter: the verdict script")
    sub.add_argument("--runs-dir", type=Path, required=True, help="runs folder outside the repo for the adapter log")
    sub.add_argument("--batch", help="batch ID (default: a new one for this job)")
    sub.add_argument("--position", type=int, default=1, help="position in the batch (default 1)")
    sub.add_argument("--id", help="proof record ID (default: a new one)")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=prove)


def prove(args):
    from swdb import workflow, writer
    from swdb.cli import _require_valid
    store = _require_valid(args.records)
    candidate = store.get(args.candidate, "candidate")
    if candidate is None:
        raise Failure(f"candidate {args.candidate!r} does not exist")
    library = _library(store)
    contract = args.contract or _certified_contract(store, args.candidate, library)
    if library is None or library.get(contract) is None:
        raise Failure(f"contract {contract!r} is not in the library beside {args.records}")
    runs = _outside_repo(args.runs_dir)
    adapter = ADAPTERS[args.adapter](args.script)
    rid = args.id or _new_id(args.candidate)
    if store.get(rid) is not None:
        raise Failure(f"ID {rid!r} is already used; nothing written")
    artifact = candidate.get("artifact") or {}
    unit = ProofUnit(args.candidate, args.function, artifact.get("path"), artifact.get("sha256"),
                     contract, library.content_sha256(contract))
    run = runs / rid
    run.mkdir(parents=True, exist_ok=False)
    job = Job(unit=unit, summaries=(), scratch=run / "scratch", log=run / "adapter.log")
    job.scratch.mkdir()
    load = os.getloadavg()[0]
    wall, cpu = time.perf_counter(), _cpu_seconds()
    try:
        verdict = adapter.run(job)
    except AdapterError as exc:
        raise Failure(f"adapter {adapter.name}: {exc}") from None
    finally:
        shutil.rmtree(job.scratch, ignore_errors=True)     # never named; gone when the job ends
    wall, cpu = time.perf_counter() - wall, _cpu_seconds() - cpu
    record = {"kind": "proof", "schema_version": "0.4", "id": rid, "status": "draft",
              "created": writer.today(), "updated": writer.today(),
              "provenance": [{"id": "prove", "kind": "agent_run",
                              "description": f"Written by swdb prove with the {adapter.name} adapter.", "uri": None}],
              "subject": {"kind": "candidate_proof_unit", "candidate": unit.candidate, "function": unit.function},
              "verdict": verdict.verdict}
    if verdict.counterexample:
        record["counterexample"] = verdict.counterexample
    if verdict.failure_class:
        record["failure_class"] = verdict.failure_class
    record.update(
        pins=_pins(store, candidate, unit, job.summaries),
        bounds=verdict.bounds, assumptions=verdict.assumptions,
        job={"adapter": adapter.name, "host": _host(), "worker_core": _worker_core(),
             "wall_seconds": round(wall, 6), "cpu_seconds": round(cpu, 6), "batch_load": round(load, 3),
             "peak_rss_bytes": _peak_rss_bytes(), "batch": args.batch or f"batch.{rid}",
             "position": args.position},
        evidence={"adapter_log": {"path": str(job.log), "sha256": _sha256(job.log)}},
        evidence_kind="contract_fixture")
    for key, value in workflow.CREATION_TAGS.items():
        record[key] = value
    written = writer.commit(args.records, new=[record])[0]
    return {"record": record, "path": written}


def _pins(store, candidate, unit, summaries):
    snapshot = store.get(candidate.get("source_snapshot") or "", "source_snapshot") or {}
    baseline = (snapshot.get("artifact") or {}).get("sha256")
    return {
        "code": {"id": unit.candidate, "sha256": unit.tree_sha256},
        "contract": {"id": unit.contract, "sha256": unit.contract_sha256},
        "baseline_function": ({"id": snapshot["id"], "function": unit.function, "sha256": baseline} if baseline else
                              {"not_applicable": "The candidate artifact names no source snapshot to pin."}),
        "reference_semantics": {"not_applicable": "No reference-semantics definition is pinned before ticket 30."},
        "proof_semantics": {"not_applicable": "No proof-semantics version exists before ticket 27."},
        "method_version": {"not_applicable": "No method-version file exists before ticket 11."},
        "summaries": [dict(pin) for pin in summaries],
        "minimum_bounds": {"not_applicable": "No minimum-bounds version exists before ticket 33."},
        "predecessor_snapshot": {"not_applicable": "This proof unit has no proven predecessor."},
        "build_constants": [],
    }


def _certified_contract(store, candidate_id, library):
    from swdb.extensa_boundary import candidate_certifications
    _bound, counted = candidate_certifications(store, candidate_id, library)
    contracts = sorted({(r.get("candidate") or {}).get("contract") or (r.get("entry") or {}).get("id")
                        for r in counted} - {None})
    if len(contracts) != 1:
        found = ", ".join(contracts) or "none"
        raise Failure(f"pass --contract: the certification records of {candidate_id} name {found}")
    return contracts[0]


def _library(store):
    from swdb.extensa_boundary import _library_for
    return _library_for(store)


def _outside_repo(runs_dir):
    runs = Path(runs_dir).resolve()
    home = paths.HOME.resolve()
    checkout = home.parent if (home.parent / ".git").exists() else home
    if runs == checkout or checkout in runs.parents:
        raise UsageError(f"--runs-dir must be outside the repository checkout ({checkout})")
    return runs


def _new_id(candidate):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dt%H%M%Sz")
    return f"proof.{candidate}.{stamp}.{uuid.uuid4().hex[:8]}"


def _host():
    from swdb import host_identity
    return "mac" if sys.platform == "darwin" else host_identity.short_name()


def _worker_core():
    """The one core the job is pinned to, else None (the Mac pins nothing; 57 pins on mbit10)."""
    try:
        cores = os.sched_getaffinity(0)
    except AttributeError:
        return None
    return next(iter(cores)) if len(cores) == 1 else None


def _cpu_seconds():
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def _peak_rss_bytes():
    scale = 1 if sys.platform == "darwin" else 1024          # ru_maxrss: bytes on macOS, KiB on Linux
    return max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) * scale


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- proven level, computed on read ------------------------------------------------------

def unit_records(store, candidate_id):
    """Every proof record whose subject is one of this candidate artifact's proof units."""
    return [r.data for r in store.of_kind("proof")
            if (r.data.get("subject") or {}).get("kind") == "candidate_proof_unit"
            and r.data["subject"].get("candidate") == candidate_id]


def counts(record, candidate, library):
    """True while a proven record's code and contract pins match the current hashes.

    Tracer rule (ticket 04): only these two pins are checked; ticket 10 checks every pin kind.
    A contract the library does not know cannot be checked, so the record does not count."""
    if record.get("verdict") != "proven":
        return False
    pins = record.get("pins") or {}
    code, contract = pins.get("code") or {}, pins.get("contract") or {}
    if code.get("sha256") != (candidate.get("artifact") or {}).get("sha256"):
        return False
    if library is None or library.get(contract.get("id")) is None:
        return False
    return contract.get("sha256") == library.content_sha256(contract["id"])


def bounded_level(record):
    """`proven_unbounded` when every dimension, the thread count included, is unbounded."""
    return ("proven_unbounded" if all(v == UNBOUNDED for v in record["bounds"].values())
            else "proven_within_bounds")


def proven_level(store, candidate_id, certification_level, library=None):
    """The proven part of `swdb candidate-level` (S2), computed on read and never stored.

    Proven requires certified. Returns {level, proven, proof_records}: `level` is the proven
    level when a record counts, else `certification_level`; `proven` is None or {level, bounds,
    records} (the best counting level, the bounds of its first record by ID, and every counting
    record at that level); `proof_records` lists every proof record of the candidate's units."""
    candidate = store.get(candidate_id, "candidate")
    library = library if library is not None else _library(store)
    records = sorted(unit_records(store, candidate_id), key=lambda r: r["id"])
    counted = [r for r in records if counts(r, candidate, library)] if certification_level == "certified" else []
    proven = None
    if counted:
        best = "proven_unbounded" if any(bounded_level(r) == "proven_unbounded" for r in counted) else "proven_within_bounds"
        top = [r for r in counted if bounded_level(r) == best]
        proven = {"level": best, "bounds": dict(top[0]["bounds"]), "records": [r["id"] for r in top]}
    return {"level": proven["level"] if proven else certification_level, "proven": proven,
            "proof_records": [r["id"] for r in records]}
