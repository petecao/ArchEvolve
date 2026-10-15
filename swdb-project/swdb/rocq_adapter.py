"""Approved Rocq method parts through swdb prove. Created: 2026-10-15 ET.

Fresh source compilation, exact statement guard and Rocq's own assumption listing
are separate gates. Pending or changed statements never write checked records.
"""
import hashlib
import types
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from swdb import artifacts, paths
from swdb.cli import Failure, UsageError
from swdb.proof import AdapterError, Verdict

NAME = "rocq"
DEVELOPMENT_ID = "rocq.probata"
PARTS = {"composition_theorem": "parallel_composition"}
FILES = ("Vocabulary.v", "Composition.v", "Reduction.v", "Sanity.v", "check/Checks.v", "check/statement.expected")
UNSAFE = re.compile(r"\b(?:Axioms?|Parameters?|Conjecture|Admitted|admit|give_up)\b")


def _guard():
    path = paths.HOME / "library" / "rocq" / "probata" / "check" / "check_approved.py"
    module = types.ModuleType("swdb_approved_composition")
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module, path


def development_identity(folder):
    folder = Path(folder)
    files = [{"path": name, "sha256": artifacts.file_hash(folder / name)} for name in FILES]
    _module, guard_path = _guard()
    files.append({"path": "trusted_statement_guard", "sha256": artifacts.file_hash(guard_path)})
    return {"id": DEVELOPMENT_ID, "sha256": artifacts.digest(files)}


def preflight(folder):
    folder = Path(folder)
    guard, _path = _guard()
    text = (folder / "Composition.v").read_text()
    unsafe = UNSAFE.search(guard.strip_comments(text))
    if unsafe:
        raise Failure(f"Rocq method part contains {unsafe.group(0)}; no Rocq-checked record written")
    try:
        reconstructed = guard.reconstruct(text)
    except SystemExit as exc:
        raise Failure(f"Rocq statement guard: {exc}") from None
    for name, data in (("Vocabulary.v", (folder / "Vocabulary.v").read_bytes()),
                       ("Composition.v", reconstructed.encode())):
        if hashlib.sha256(data).hexdigest() != guard.APPROVED[name]:
            raise Failure(f"Rocq statement guard: {name} differs from the approved statement")
    # The elaboration and assumptions harness is trusted repository code too.
    canonical = paths.HOME / "library" / "rocq" / "probata" / "check"
    for name in ("Checks.v", "statement.expected"):
        if (folder / "check" / name).read_bytes() != (canonical / name).read_bytes():
            raise Failure(f"Rocq statement guard: {name} differs from the approved elaboration harness")


def prove(args, store):
    from swdb import method_version, proof, vocab
    from swdb.library import default_root
    if args.method_part not in PARTS or args.adapter != NAME or any((args.candidate, args.summary, args.model,
           args.script, args.skip, args.contract, args.function, args.hint_file, args.define, args.bounds,
           args.whole_function, args.minimum_bounds)):
        raise UsageError("--method-part composition_theorem runs only --adapter rocq, without candidate/contract/bounded inputs")
    folder = Path(args.development or default_root(args.records) / "rocq" / "probata").resolve()
    preflight(folder)
    identity = development_identity(folder)
    method = proof._current_method(args.records, args.method_version)
    declared = method.data.get("rocq_development") or {}
    if {k: declared.get(k) for k in ("id", "sha256")} != identity:
        raise Failure("Rocq development differs from the method version's pinned content hash")
    if declared.get("composition_theorem") != "Composition.parallel_composition":
        raise Failure("method version must name Composition.parallel_composition")
    na = {"not_applicable": "A Rocq method-part check has no candidate code or contract."}
    pins = {k: dict(na) for k in ("code", "contract", "baseline_function", "reference_semantics", "proof_semantics",
                                 "minimum_bounds", "predecessor_snapshot")}
    pins.update(method_version=method_version.pin(method), summaries=[], build_constants=[], rocq_development=identity)
    unit = proof.ProofUnit(None, PARTS[args.method_part], str(folder), identity["sha256"],
                           "method_part." + args.method_part, identity["sha256"])
    rid = args.id or proof._new_id(args.method_part)
    if store.get(rid) is not None:
        raise Failure(f"ID {rid!r} is already used; nothing written")
    adapter = RocqAdapter(folder, identity, method)
    vocabs, _ = vocab.load_all(paths.VOCAB)
    record = proof._run_job(rid, unit, pins, adapter, proof._outside_repo(args.runs_dir),
                            {"batch": args.batch or f"batch.{rid}", "position": args.position},
                            proof.listed(vocabs, "failure_class"), method,
                            budget_minutes=args.budget_minutes or method.data["budgets"]["bounded_job_minutes"])
    record["subject"] = {"kind": "method_part", "id": "rocq.probata.composition", "part": args.method_part}
    if record["verdict"] == "proven":
        record["method_part_status"] = "rocq_checked"
    record.update(proof._run_fields(args))
    return {"record": record, "path": proof._write(args.records, record)}


class RocqAdapter:
    name = NAME
    real = True
    library = None

    def __init__(self, folder, identity, method):
        self.folder, self.identity, self.method = folder, identity, method

    def run(self, job):
        from swdb import proof_setup, rss_watchdog
        command = shlex.split(os.environ.get("SWDB_ROCQ") or "opam exec --switch=rocq-9 -- rocq")
        try:
            version = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=15)
            match = re.search(r"version (\d+\.\d+\.\d+)", version.stdout)
            if version.returncode or not match or match[1] != "9.3.0":
                raise AdapterError("Rocq 9.3.0 is required")
            # Resolve the actual compiler inside opam's environment, not the opam launcher.
            resolved = subprocess.run([*command[:-1], "which", command[-1]] if len(command) > 1 else
                                      ["which", command[0]], capture_output=True, text=True, timeout=15)
            binary = Path(resolved.stdout.strip())
            sha = artifacts.file_hash(binary)
        except (OSError, subprocess.SubprocessError) as exc:
            raise AdapterError(f"cannot locate Rocq: {exc}") from None
        declared = next((r for r in self.method.data["lineup"] if r["tool"] == NAME), {})
        if declared.get("version") != match[1]:
            raise AdapterError("Rocq differs from the method's pinned version")
        flags = list(declared.get("flags", []))
        if flags:
            raise AdapterError("Rocq method-part compilation currently requires the empty frozen extra-flag list")
        inputs = []
        for name in FILES:
            expected = (self.folder / name).read_text()
            target = job.scratch / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected)
            inputs.append((target, expected))
        if development_identity(job.scratch) != self.identity:
            raise AdapterError("copied Rocq sources differ from the planned development")
        preflight(job.scratch)
        context = {"tools": {"identities": {NAME: (f"rocq-{match[1]}", sha, match[1])}}}
        started, peak, reports = time.monotonic(), 0, []
        outcome, failure = "proven", None
        with job.log.open("w") as log:
            for name in ("Vocabulary.v", "Composition.v", "check/Checks.v"):
                if development_identity(self.folder) != self.identity or development_identity(job.scratch) != self.identity:
                    raise AdapterError("Rocq development changed after planning")
                cmd = [*command, "compile", "-Q", ".", "Probata", name]
                proof_setup.check_generated(job, self, context, inputs, flags, command=cmd, scratch=job.scratch)
                output = job.log.parent / (Path(name).stem + ".log")
                result = rss_watchdog.run(cmd, log=output, cap_bytes=rss_watchdog.DEFAULT_CAP_BYTES,
                    timeout=max(0.1, (job.budget_seconds or 900) - (time.monotonic() - started)), cwd=job.scratch,
                    env={k: v for k, v in os.environ.items() if k not in ("ROCQPATH", "COQPATH")})
                peak = max(peak, result.peak_rss_bytes)
                reports.append((Path(name).stem, output))
                log.write(f"{name}: exit {result.exit_code}, peak {result.peak_rss_bytes}, wall {result.wall_seconds:.3f}\n")
                if result.exit_code:
                    outcome = "not_proven"
                    failure = "out_of_memory" if result.out_of_memory else "timeout" if result.timed_out else "solver_error"
                    break
            if outcome == "proven":
                checked = reports[-1][1].read_text()
                marker = "Closed under the global context"
                if checked.count(marker) != 1 or "Axioms:" in checked:
                    raise AdapterError("Rocq's assumption listing is not closed; no Rocq-checked record written")
                statement, suffix = checked.split(marker)
                if suffix.strip() or statement.rstrip() != (job.scratch / "check" / "statement.expected").read_text().rstrip():
                    raise AdapterError("Rocq elaborated statement differs from the approved statement snapshot")
                log.write("Approved elaborated statement matches; theorem closed under the global context.\n")
        assumptions = [{"kind": "trusted_tool", "reference": {"id": f"rocq-{match[1]}", "sha256": sha},
                        "sentence": f"Rocq {match[1]} correctly checks proof terms and reports their assumptions."}]
        return Verdict(outcome, {"threads": "unbounded"}, assumptions=assumptions, failure_class=failure,
                       tools=(f"rocq-{match[1]}",), peak_rss_bytes=peak, reports=tuple(reports),
                       record_fields={"settings": {"tool": NAME, "flags": flags, "session": "fresh",
                           "development": self.identity, "statement_guard": "approved_content_and_elaboration",
                           "rss_cap_bytes": rss_watchdog.DEFAULT_CAP_BYTES}})
