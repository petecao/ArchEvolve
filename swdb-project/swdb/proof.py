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
- Ticket 11 (2026-10-14 ET): one call runs a batch (one job per script, or one skip); every record
  pins the current method version (swdb.method_version); a failure class outside vocabulary
  proof_failure_classes stops the batch; `validate_record` checks the class, skip reason and pin.
  Updated 2026-10-14 02:26 ET (Yan-Ru's decision of 02:25 ET): an unreplayed counterexample goes with
  failure class spurious_counterexample and no other, both ways; repair never takes that class.
- Ticket 12 (2026-10-14 ET): the job block's one field list (`_job`), run fields (`--run-index`,
  `--provider-*`), and the cross-record checks of repair lineage (`validate_proposal`) and of the proof
  records a promotion review cites (`validate_promotion`).
- Ticket 14 (2026-10-14 ET): a job may name the bounds it runs at (`--bounds`, the bounded gate's minimum
  bounds) and its wall budget (`--budget-minutes`, the method version's `bounded_job_minutes`); a record
  may pin the minimum-bounds derivation it ran at (`--minimum-bounds`).
- Levels are computed on read by the versioned level rule (`swdb.level_rule`, ticket 10), which
  replaced this tracer's code-and-contract-pin rule; nothing here stores a level (ADR 0016).
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
UNPINNED = "unpinned"
OUT_OF_MEMORY = "out_of_memory"       # ticket 57: the class the worker's RSS watchdog gives (O9)
SPURIOUS = "spurious_counterexample"   # Yan-Ru 2026-10-14 02:25 ET: the class of a counterexample that did not replay


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
    bounds: dict = None            # ticket 14: the bounds the job runs at (the gate's minimum bounds), if named
    budget_seconds: float = None   # ticket 14: the job's wall budget; a job that runs out is not proven, timeout


@dataclass(frozen=True)
class Verdict:
    """What an adapter returns: the verdict and what it holds under."""
    verdict: str
    bounds: dict
    assumptions: list = field(default_factory=list)
    counterexample: dict = None
    failure_class: str = None
    unreplayed_counterexample: dict = None   # ticket 11: a reported counterexample that did not replay;
                                             # present exactly when failure_class is spurious_counterexample
    tools: tuple = ()                        # ticket 10 (S14): verifiers and solvers used, each a trusted-tool entry
    peak_rss_bytes: int = None               # ticket 12 (O9): the tree peak the adapter's RSS watchdog read, if any
    record_fields: dict = None               # ticket 21: real-adapter fields (goals, unproven_properties, settings)
    pins: dict = None                        # ticket 21: extra pins (c_lowering: the C lowering's {id, sha256})
    reports: tuple = ()                      # ticket 21: (name, path) of tool reports in the runs folder

    def __post_init__(self):
        if self.unreplayed_counterexample and self.verdict != "not_proven":
            raise AdapterError("a counterexample that does not replay is never a refutation: only a not-proven "
                               "verdict carries an unreplayed counterexample")
        if self.verdict not in VERDICTS:
            raise AdapterError(f"verdict must be one of {', '.join(VERDICTS)}, not {self.verdict!r}")
        if (self.verdict == "refuted") != bool(self.counterexample):
            raise AdapterError("a refuted verdict, and only a refuted verdict, carries a counterexample")
        if (self.verdict == "not_proven") != bool(self.failure_class):
            raise AdapterError("a not-proven verdict, and only a not-proven verdict, carries a failure class")
        if self.verdict == "not_proven" and \
                (self.failure_class == SPURIOUS) != bool(self.unreplayed_counterexample):
            raise AdapterError(f"failure class {SPURIOUS} and an unreplayed counterexample go together: a "
                               "not-proven verdict carries both or neither")
        if not isinstance(self.bounds, dict) or "threads" not in self.bounds:
            raise AdapterError("a verdict states its bounds, the thread count always among them")


class ScriptedAdapter:
    """The scripted verifier adapter: the verdict comes from a YAML script file.

    Script keys: `verdict`, `bounds`, `assumptions`, and `counterexample` (refuted) or
    `failure_class` (not proven). It uses the scratch folder as a real tool would, and logs.
    Ticket 57: optional `run`, a command it runs in the scratch folder first, standing in for a tool's
    process (so the worker's RSS watchdog has something to watch and, above the cap, to kill).
    Ticket 14: without `bounds` in the script, the verdict holds at the bounds the job names; a `run`
    command that outlives the job's wall budget is killed and the verdict is not proven, timeout."""
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
        bounds = self.script.get("bounds") or (dict(job.bounds) if job.bounds else None)
        if self.script.get("run"):          # ticket 57: a stand-in for a tool's process (watchdog fixtures)
            import subprocess
            with open(job.log, "ab") as log:
                try:
                    subprocess.run([str(part) for part in self.script["run"]], cwd=job.scratch, stdout=log,
                                   stderr=subprocess.STDOUT, timeout=job.budget_seconds)
                except subprocess.TimeoutExpired:      # ticket 14: the job ran out of its wall budget
                    log.write(f"wall budget of {job.budget_seconds} s spent\n".encode())
                    return Verdict(verdict="not_proven", bounds=bounds, failure_class="timeout",
                                   assumptions=list(self.script.get("assumptions") or []))
        verdict = Verdict(verdict=self.script.get("verdict"), bounds=bounds,
                          assumptions=list(self.script.get("assumptions") or []),
                          counterexample=self.script.get("counterexample"),
                          failure_class=self.script.get("failure_class"),
                          unreplayed_counterexample=self.script.get("unreplayed_counterexample"),
                          tools=tuple(self.script.get("tools") or ()),
                          peak_rss_bytes=self.script.get("peak_rss_bytes"))
        with open(job.log, "a", encoding="utf-8") as log:
            log.write(f"adapter: scripted\nscript: {self.source}\n"
                      f"unit: {job.unit.candidate} {job.unit.function}\n"
                      f"contract: {job.unit.contract} {job.unit.contract_sha256}\n"
                      f"scratch used: {job.scratch}\nverdict: {verdict.verdict}\n")
        return verdict


ADAPTERS = {"scripted": ScriptedAdapter}
RECORD_FIELDS = ("goals", "unproven_properties", "settings",     # ticket 21: what a real adapter may add
                 "hint_set", "hint_check")                       # ticket 35: the hint set and its check result


# --- swdb prove -----------------------------------------------------------------------

def register_cli(commands):
    sub = commands.add_parser("prove", help="run a batch of proof jobs on one candidate proof unit; one proof record each",
                              description="run a batch of proof jobs on one candidate artifact's proof unit through a "
                                          "verifier adapter and write one proof record per job (never changed). A "
                                          "failure class outside vocabulary proof_failure_classes stops the batch.")
    sub.add_argument("--records", type=Path, default=paths.RECORDS)
    sub.add_argument("--candidate", required=True, help="the candidate artifact")
    sub.add_argument("--function", required=True, help="the function that holds the rewrite site")
    sub.add_argument("--contract", help="the rewrite contract (default: the one its certification records name)")
    sub.add_argument("--adapter", choices=sorted(ADAPTERS), required=True)
    sub.add_argument("--script", type=Path, action="append",
                     help="scripted adapter: a verdict script; repeat it for a batch (one job per script, in order)")
    sub.add_argument("--skip", metavar="REASON",
                     help="run no verifier; record one skip with this skip reason (vocabulary proof_failure_classes)")
    sub.add_argument("--runs-dir", type=Path, required=True, help="runs folder outside the repo for the adapter log")
    sub.add_argument("--batch", help="batch ID (default: a new one for this call)")
    sub.add_argument("--position", type=int, default=1, help="position of the first job in the batch (default 1)")
    sub.add_argument("--id", help="proof record ID of a one-job batch (default: a new one)")
    gate = sub.add_argument_group("bounded jobs (ticket 14): the bounded gate names its bounds, budget and minimum")
    gate.add_argument("--bounds", type=_bounds_argument, help="JSON object: the bounds the job runs at")
    gate.add_argument("--minimum-bounds", metavar="RECORD",
                      help="pin this minimum-bounds derivation record (a contract-proof part of the contract)")
    gate.add_argument("--budget-minutes", type=float, help="the job's wall budget in minutes")
    run = sub.add_argument_group("run fields (ticket 12, S10): a proof-hint run or a repeated run carries them; a "
                                 "bounded job with no provider call carries none")
    run.add_argument("--run-index", type=int, help="which of the three independent runs (1-3)")
    run.add_argument("--provider-kind", choices=["codex", "claude"], help="provider pin: kind")
    run.add_argument("--provider-model", help="provider pin: model (for example gpt-5.6-sol)")
    run.add_argument("--provider-effort", help="provider pin: effort (for example xhigh)")
    real = sub.add_argument_group("real adapters (ticket 21): the wp adapter")
    real.add_argument("--hint-file", type=Path, help="wp only: a hint set {hints: [{anchor, kind, text, provenance}]}; "
                                                     "it reaches WP only when the proof hint check accepts it "
                                                     "(ticket 35); any other adapter refuses it")
    real.add_argument("--define", action="append", default=[], help="wp: a build constant NAME or NAME=VALUE for "
                                                                    "the C lowering (repeatable; pinned as build_constants)")
    from swdb import archevolve_proof      # Probata PoC 18: ArchEvolve mode's whole proof path
    archevolve_proof.register_options(sub)
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=prove)


def prove(args):
    """Run the batch (one job per --script, or one skip) and write one record per job, in order.

    Output: {record, path} for a one-job batch, else {batch, jobs: [{record, path}, ...]}. With
    `--proof-path` (ticket 18), ArchEvolve mode's proof path runs instead (`swdb.archevolve_proof`)."""
    if getattr(args, "proof_path", None):
        from swdb import archevolve_proof
        return archevolve_proof.run_cli(args)
    from swdb import vocab
    from swdb.cli import _require_valid
    store = _require_valid(args.records)
    candidate = store.get(args.candidate, "candidate")
    if candidate is None:
        raise Failure(f"candidate {args.candidate!r} does not exist")
    library = _library(store)
    contract = args.contract or _certified_contract(store, args.candidate, library)
    if library is None or library.get(contract) is None:
        raise Failure(f"contract {contract!r} is not in the library beside {args.records}")
    vocabs, _problems = vocab.load_all(paths.VOCAB)
    if args.skip is not None and args.skip not in listed(vocabs, "skip_reason"):
        raise UsageError(f"--skip {args.skip!r} is not a skip reason in vocabulary {FAILURE_VOCAB}")
    if getattr(args, "hint_file", None) is not None and args.adapter != "wp":     # ticket 35; map 13 item 2
        raise UsageError(f"a hint set goes only to the WP adapter: the {args.adapter} adapter (a bounded-verifier job) "
                         "takes no --hint-file, so no refutation depends on hint text")
    scripts = [None] if args.skip is not None else (args.script or [None])
    if args.id and len(scripts) > 1:
        raise UsageError("--id names the record of a one-job batch only")
    run_fields = _run_fields(args)
    method = _current_method(args.records)
    runs = _outside_repo(args.runs_dir)
    artifact = candidate.get("artifact") or {}
    unit = ProofUnit(args.candidate, args.function, artifact.get("path"), artifact.get("sha256"),
                     contract, library.content_sha256(contract))
    pins = _pins(store, candidate, unit, (), method)
    if getattr(args, "minimum_bounds", None):
        pins["minimum_bounds"] = _minimum_pin(store, args.minimum_bounds, unit)
    if getattr(args, "define", None):
        pins["build_constants"] = [{"name": d.split("=", 1)[0], "value": d.split("=", 1)[1] if "=" in d else "1"}
                                   for d in sorted(args.define)]
    adapters = [None if args.skip is not None else _adapter(args, script, library, contract, method) for script in scripts]
    batch = args.batch
    done = []
    for offset, adapter in enumerate(adapters):
        rid = args.id or _new_id(args.candidate)
        if store.get(rid) is not None:
            raise Failure(f"ID {rid!r} is already used; nothing written")
        batch = batch or f"batch.{rid}"
        place = {"batch": batch, "position": args.position + offset}
        if adapter is None:
            record = _skip_record(rid, unit, pins, args.adapter, args.skip, place)
        else:
            record = _run_job(rid, unit, pins, adapter, runs, place, listed(vocabs, "failure_class"), method,
                              bounds=getattr(args, "bounds", None), budget_minutes=getattr(args, "budget_minutes", None))
        record.update(run_fields)
        done.append({"record": record, "path": _write(args.records, record)})
    return done[0] if len(done) == 1 else {"batch": batch, "jobs": done}


def _adapter(args, script, library, contract, method):
    """The adapter of one job: a real adapter builds itself from the call (ticket 21), the scripted one from its script."""
    kind = ADAPTERS[args.adapter]
    if hasattr(kind, "from_args"):
        try:
            return kind.from_args(args, script, library=library, contract=contract, method=method)
        except AdapterError as exc:
            raise Failure(f"adapter {kind.name}: {exc}") from None
    return kind(script)


def _run_fields(args):
    """{run_index, provider_pin} from the command line: each present only when given (ticket 12, S10)."""
    fields = {}
    if args.run_index is not None:
        fields["run_index"] = args.run_index
    pin = {"kind": args.provider_kind, "model": args.provider_model, "effort": args.provider_effort}
    given = [key for key, value in pin.items() if value is not None]
    if given and len(given) != len(pin):
        missing = ", ".join(f"--provider-{key}" for key, value in pin.items() if value is None)
        raise UsageError(f"a provider pin needs its kind, model and effort: also pass {missing}")
    if given:
        fields["provider_pin"] = pin
    return fields


def _bounds_argument(text):
    import json
    try:
        value = json.loads(text)
    except ValueError:
        value = None
    if not isinstance(value, dict) or "threads" not in value:
        raise ValueError("--bounds is a JSON object with a threads dimension")
    return value


def _minimum_pin(store, rid, unit):
    """The minimum_bounds pin (ticket 14): a minimum-bounds derivation record of the unit's contract."""
    from swdb import artifacts
    record = store.get(rid, "proof")
    subject = (record or {}).get("subject") or {}
    if record is None or subject.get("kind") != "contract_proof_part" or \
            subject.get("part") != "minimum_bounds_derivation" or subject.get("id") != unit.contract:
        raise Failure(f"--minimum-bounds {rid!r} is not a minimum-bounds derivation record of contract {unit.contract}")
    return {"id": rid, "sha256": artifacts.digest(record)}


def _run_job(rid, unit, pins, adapter, runs, place, failure_classes, method=None, bounds=None, budget_minutes=None):
    """Run one job through the adapter and return its record (not yet written).

    A failure class outside the list stops the batch: no record for this job, and the message
    names the class and the adapter's raw output by path (the log stays)."""
    run = runs / rid
    run.mkdir(parents=True, exist_ok=False)
    job = Job(unit=unit, summaries=(), scratch=run / "scratch", log=run / "adapter.log", bounds=bounds,
              budget_seconds=None if budget_minutes is None else budget_minutes * 60)
    job.scratch.mkdir()
    with _verifier_lock(adapter, rid):                # ticket 21: one real verifier job per machine
        load = os.getloadavg()[0]
        wall, cpu = time.perf_counter(), _cpu_seconds()
        watch = _worker_watch()
        try:
            with watch:
                verdict = adapter.run(job)
        except AdapterError as exc:
            raise Failure(f"adapter {adapter.name}: {exc}. Adapter output: {job.log}") from None
        finally:
            shutil.rmtree(job.scratch, ignore_errors=True)     # never named; gone when the job ends
        wall, cpu = time.perf_counter() - wall, _cpu_seconds() - cpu
    load = {"start": round(load, 3), "end": round(os.getloadavg()[0], 3)}
    if getattr(watch, "error", None):
        raise Failure(f"{watch.error}; no record was written for this job. Adapter output: {job.log}")
    if verdict.peak_rss_bytes is not None:
        peak = verdict.peak_rss_bytes
    elif watch.active:
        peak = max(watch.peak, _peak_rss_bytes())                  # ticket 57: the worker watchdog's reading
    else:
        peak = _peak_rss_bytes()
    if watch.tripped:                                              # ticket 57 (O9): the watchdog ended the tool
        verdict = Verdict(verdict="not_proven", bounds=verdict.bounds, assumptions=verdict.assumptions,
                          failure_class=OUT_OF_MEMORY, tools=verdict.tools, pins=verdict.pins, reports=verdict.reports)
    if verdict.failure_class and verdict.failure_class not in failure_classes:
        raise Failure(f"adapter {adapter.name} reported failure class {verdict.failure_class!r}, which is not a "
                      f"failure class in vocabulary {FAILURE_VOCAB}: the batch stops here (position "
                      f"{place['position']}); no record was written for this job and no later job started. "
                      f"Adapter output: {job.log}")
    record = _head(rid, unit, f"Written by swdb prove with the {adapter.name} adapter.")
    record["verdict"] = verdict.verdict
    if verdict.counterexample:
        record["counterexample"] = verdict.counterexample
    if verdict.failure_class:
        record["failure_class"] = verdict.failure_class
    if verdict.unreplayed_counterexample:
        record["unreplayed_counterexample"] = verdict.unreplayed_counterexample
    if verdict.tools:
        record["tools"] = list(verdict.tools)
    for key, value in (verdict.record_fields or {}).items():
        if key not in RECORD_FIELDS:
            raise Failure(f"adapter {adapter.name} returned field {key!r}, which a proof record does not hold")
        if verdict.verdict == "not_proven" or key != "unproven_properties":
            record[key] = value
    evidence = {"adapter_log": {"path": str(job.log), "sha256": _sha256(job.log)}}
    if verdict.reports:                                            # ticket 21: tool reports, by path and sha256
        evidence["reports"] = [{"name": name, "path": str(Path(path).resolve()), "sha256": _sha256(path)}
                               for name, path in verdict.reports]
    record.update(
        pins={**pins, **(verdict.pins or {})}, bounds=verdict.bounds, assumptions=verdict.assumptions,
        job=_job(adapter.name, round(wall, 6), round(cpu, 6), load, peak, place),
        evidence=evidence, evidence_kind=_evidence_kind(adapter, method))
    return record


def _evidence_kind(adapter, method):
    """Ticket 21: a real adapter under a real method version gives execution evidence; a scripted adapter or a
    contract_fixture method version gives contract_fixture evidence (fixture records stay fixtures)."""
    if getattr(adapter, "real", False) and method is not None and method.data.get("evidence_kind") == "execution":
        return "execution"
    return "contract_fixture"


def _verifier_lock(adapter, rid):
    """Ticket 21: the machine-wide verifier lock around a real adapter's job (the scripted adapter takes none)."""
    import contextlib
    if not getattr(adapter, "real", False):
        return contextlib.nullcontext()
    from swdb import verifier_lock
    return verifier_lock.hold(f"swdb prove {rid}")


def _skip_record(rid, unit, pins, adapter_name, reason, place):
    """A skip: no verifier runs; the record has its reason and no verdict, bounds, assumptions or log."""
    record = _head(rid, unit, f"Written by swdb prove: skipped ({reason}); no verifier ran.")
    load = round(os.getloadavg()[0], 3)
    record.update(skip_reason=reason, pins=pins,
                  job=_job(adapter_name, 0.0, 0.0, {"start": load, "end": load}, _peak_rss_bytes(), place),
                  evidence_kind="contract_fixture")
    return record


def _head(rid, unit, description):
    from swdb import writer
    return {"kind": "proof", "schema_version": "0.4", "id": rid, "status": "draft",
            "created": writer.today(), "updated": writer.today(),
            "provenance": [{"id": "prove", "kind": "agent_run", "description": description, "uri": None}],
            "subject": {"kind": "candidate_proof_unit", "candidate": unit.candidate, "function": unit.function}}


def _write(records, record):
    from swdb import workflow, writer
    for key, value in workflow.CREATION_TAGS.items():
        record[key] = value
    return writer.commit(records, new=[record])[0]


def _current_method(records):
    """The current method version beside the records folder; `swdb prove` refuses to run without one."""
    from swdb import method_version
    from swdb.library import default_root
    root = default_root(records)
    found = method_version.current(root)
    if found is None:
        raise Failure(f"no method-version file in {root / method_version.FOLDER}: every proof record pins one")
    return found


def _pins(store, candidate, unit, summaries, method):
    from swdb import method_version
    snapshot = store.get(candidate.get("source_snapshot") or "", "source_snapshot") or {}
    baseline = (snapshot.get("artifact") or {}).get("sha256")
    return {
        "code": {"id": unit.candidate, "sha256": unit.tree_sha256},
        "contract": {"id": unit.contract, "sha256": unit.contract_sha256},
        "baseline_function": ({"id": snapshot["id"], "function": unit.function, "sha256": baseline} if baseline else
                              {"not_applicable": "The candidate artifact names no source snapshot to pin."}),
        "reference_semantics": {"not_applicable": "No reference-semantics definition is pinned before ticket 30."},
        "proof_semantics": {"not_applicable": "No proof-semantics version exists before ticket 27."},
        "method_version": method_version.pin(method),
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


def _job(adapter, wall, cpu, load, peak, place):
    """The job block: ticket 12's one field list (docs/reference/format-v0.4-proof.md, "The job block")."""
    return {"adapter": adapter, "host": _host(), "worker_core": _worker_core(), "wall_seconds": wall,
            "cpu_seconds": cpu, "batch_load": load, "peak_rss_bytes": peak, **place}


def _host():
    from swdb import host_identity
    return "mac" if sys.platform == "darwin" else host_identity.short_name()


def _worker_core():
    """The one core the job is pinned to, else "unpinned" (macOS pins nothing; 57 pins on mbit10)."""
    try:
        cores = os.sched_getaffinity(0)
    except AttributeError:
        return UNPINNED
    return next(iter(cores)) if len(cores) == 1 else UNPINNED


class _NoWatch:
    """Outside a lane batch: no worker watchdog."""
    active = tripped = False
    peak = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _worker_watch():
    """Ticket 57: inside a lane batch, the worker's RSS watchdog watches this process and its children.

    The batch hands the cap in SWDB_WORKER_RSS_CAP_BYTES. Above it, the watchdog kills the adapter's
    tool processes (never this one) and the job ends not proven, failure class out_of_memory."""
    from swdb import rss_watchdog
    cap = rss_watchdog.cap_from_environment()
    if cap is None:
        return _NoWatch()
    return rss_watchdog.TreeWatch(os.getpid(), cap, spare_root=True)


def _cpu_seconds():
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def _peak_rss_bytes():
    scale = 1 if sys.platform == "darwin" else 1024          # ru_maxrss: bytes on macOS, KiB on Linux
    return max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) * scale


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- swdb validate: the rules the schema cannot express (ticket 11) -----------------------

FAILURE_VOCAB = "proof_failure_classes"
PART_VOCAB = "proof_part_names"


def listed(vocabs, role):
    """The values of the failure-class vocabulary with this role (`failure_class` or `skip_reason`)."""
    return {value for value, entry in vocabs.entries.get(FAILURE_VOCAB, {}).items() if entry.get("role") == role}


def validate_record(record, ctx):
    """A proof record's failure class and skip reason come from their role in the one list."""
    from swdb.problems import Problem
    data = record.data
    for field_name in ("failure_class", "skip_reason"):
        value = data.get(field_name)
        if value is not None and value not in listed(ctx.vocabs, field_name):
            yield Problem(record.rel, field_name,
                          f"{value!r} is not a {field_name.replace('_', ' ')} in vocabulary {FAILURE_VOCAB}")
    subject = data.get("subject") or {}
    part = subject.get("part")
    if part is not None:                                             # ticket 10: one list of part names
        entry = ctx.vocabs.entries.get(PART_VOCAB, {}).get(part)
        if entry is None:
            yield Problem(record.rel, "subject.part", f"{part!r} is not a part name in vocabulary {PART_VOCAB}")
        elif entry.get("subject_kind") != subject.get("kind"):
            yield Problem(record.rel, "subject.part", f"part {part!r} belongs to a {entry.get('subject_kind')} "
                          f"subject (vocabulary {PART_VOCAB}), not to {subject.get('kind')}")
    trusted = {(a.get("reference") or {}).get("id") for a in data.get("assumptions") or []
               if isinstance(a, dict) and a.get("kind") == "trusted_tool"}
    for position, tool in enumerate(data.get("tools") or []):      # ticket 10, S14
        if tool not in trusted:
            yield Problem(record.rel, f"tools[{position}]",
                          f"tool {tool!r} is used but the assumption set holds no trusted-tool entry for it (S14)")
    from swdb import method_version
    from swdb.library import default_root
    problem = method_version.pin_problem((data.get("pins") or {}).get("method_version"), default_root(ctx.records_dir))
    if problem:
        yield Problem(record.rel, "pins.method_version", problem)


# --- swdb validate: repair lineage on proposals (ticket 12) -----------------------------------

def validate_proposal(record, ctx):
    """Repair lineage names a refuted proof record, counterexample inline, about the refuted candidate artifact.

    The schema checks the fields (round >= 1, the flag present) and that both IDs exist; this checks
    what the counterexample record is. An unreplayed counterexample (not proven) never qualifies."""
    from swdb.problems import Problem
    lineage = record.data.get("repair_lineage")
    if not lineage:
        return
    rid, refuted = lineage["counterexample_record"], lineage["refuted_candidate"]
    proof = ctx.store.get(rid, "proof")
    if proof is None:
        return                                   # the schema's x-ref already names it
    where = "repair_lineage.counterexample_record"
    if proof.get("verdict") != "refuted" or not proof.get("counterexample"):
        yield Problem(record.rel, where, f"{rid} is not a refutation with an inline counterexample "
                      f"(verdict {proof.get('verdict') or 'none'}); only a refuted proof record starts a repair")
    subject = proof.get("subject") or {}
    if subject.get("kind") != "candidate_proof_unit" or subject.get("candidate") != refuted:
        about = subject.get("candidate") or subject.get("id") or "-"
        yield Problem(record.rel, where, f"{rid} is about {about}, not the refuted candidate artifact {refuted}")


# --- swdb validate: what a promotion review cites (ticket 12) ----------------------------------

def validate_promotion(record, ctx):
    """Every proof record a candidate review cites (`proof_records`, the snapshot's `records`) is about the
    reviewed candidate artifact's proof unit. The schema checks that the records exist and the snapshot's shape."""
    from swdb.problems import Problem
    data = record.data
    candidate = (data.get("target") or {}).get("id")
    cited = [("proof_records", rid) for rid in data.get("proof_records") or []]
    cited += [("level_snapshot.records", rid) for rid in (data.get("level_snapshot") or {}).get("records") or []]
    for where, rid in cited:
        proof = ctx.store.get(rid, "proof")
        subject = (proof or {}).get("subject") or {}
        if proof is not None and (subject.get("kind") != "candidate_proof_unit" or subject.get("candidate") != candidate):
            about = subject.get("candidate") or subject.get("id") or "-"
            yield Problem(record.rel, where, f"{rid} is about {about}, not the reviewed candidate artifact {candidate}")


# --- real adapters (ticket 21 on) ------------------------------------------------------------------
from swdb import wp_adapter as _wp_adapter   # noqa: E402  (it imports Verdict and AdapterError from here)
ADAPTERS[_wp_adapter.NAME] = _wp_adapter.WpAdapter
