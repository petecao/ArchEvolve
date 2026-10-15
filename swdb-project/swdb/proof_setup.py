"""Frozen proof setup and fresh-run WP reading. Created: 2026-10-15 ET (ticket 36).

A setup failure is an adapter error: stop the batch without a proof record. The first
check pins the immutable inputs; each generated run checks those pins again immediately
before invocation. Bounded harness input-domain restrictions are generated from pinned
bounds and formal preconditions, never free-form premises. Summary stubs are the only
source of additional assumption statements. The WP reader uses generated-goal inventory
and individual prover outcomes; consolidated status never establishes a proof.
"""
import csv
import hashlib
import json
import os
import re
from pathlib import Path

from swdb.proof import AdapterError

SETUP_VERSION = "1"
READING_VERSION = "1"
REPORT_MODULE = Path(__file__).with_name("proof_report.ml")
_ASSUME = re.compile(r"\b(?:__CPROVER_assume|crucible_assume|llvm_assume|SWDB_ASSUME|assume)\s*\(")


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    sha = _sha(Path(__file__).read_bytes() + REPORT_MODULE.read_bytes())
    return {"proof_setup_check": {"version": SETUP_VERSION, "sha256": sha},
            "verdict_reading": {"version": READING_VERSION, "sha256": sha}}


def _fail(rule, why):
    raise AdapterError(f"proof setup check [{rule}]: {why}")


def _no_assume(text, where):
    # Comments and string literals are not executable assumption statements. ACSL
    # 'assumes' selects a behavior, and is deliberately not the statement 'assume'.
    text = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', " ", text, flags=re.S)
    if _ASSUME.search(text):
        _fail("assumption_provenance", f"{where} contains an assumption not generated from a summary or the pinned domain")


def _method(method):
    if method is not None and _sha(Path(method.path).read_bytes()) != method.sha256:
        _fail("method_version", f"method {method.id} changed after the job was planned")


def begin(job, adapter, pins, method):
    """Universal preflight before adapter.run, including a scripted bounded job."""
    _method(method)
    report = {"check": identity()["proof_setup_check"], "verdict": "passed", "method_version": pins["method_version"],
              "hashes": {"contract": job.unit.contract_sha256, "summaries": _digest(list(job.summaries))}, "runs": []}
    job.setup.update(report=report, method=method, adapter=adapter, files={})
    library = getattr(adapter, "library", None)
    if library is not None and not job.unit.contract.startswith("c_model."):
        from swdb.library import Library
        fresh = Library(library.root)
        if fresh.content_sha256(job.unit.contract) != job.unit.contract_sha256:
            _fail("contract_hash", "contract differs from its planned content hash")
        entry = fresh.get(job.unit.contract) or {}
        _placements(entry)
        job.setup["contract_library"] = library.root
        # Scan only the actual proof translation unit; scripted fixtures have no
        # real source traversal and can explicitly supply their input manifest.
        from swdb.wp_adapter import _unit_source
        source = _unit_source(Path(job.unit.tree), job.unit.function)
        _no_assume(source.read_text(), str(source))
        job.setup["files"][str(source)] = _sha(source.read_bytes())
    plan = getattr(adapter, "script", {}).get("setup") or {}
    if plan:
        for row in plan.get("inputs", []):
            path = Path(row["path"])
            text = path.read_text()
            _no_assume(text, str(path))
            actual = _sha(path.read_bytes())
            if row.get("sha256", actual) != actual:
                _fail("input_hash", f"{path} differs from its planned hash")
            job.setup["files"][str(path)] = actual
        for clause in plan.get("clauses", []):
            if not clause.get("proof_placement"):
                _fail("proof_placement", f"clause {clause.get('id')} has no proof placement")
        for probe in plan.get("probes", []):
            if probe.get("origin") != "generator" or not any(
                    probe["id"] in Path(p).read_text() for p in job.setup["files"]):
                _fail("hazard_probes", f"probe {probe.get('id')} is absent or not generator-made")
        if plan.get("tool") in ("wp", "frama-c-wp"):
            _wp_flags(plan.get("flags", []), job.scratch)
        report["hashes"]["run_plan"] = _digest(plan)
    _environment()
    return report


def _placements(entry):
    for clause in entry.get("clauses", []):
        if not clause.get("proof_placement"):
            _fail("proof_placement", f"clause {clause.get('id')} has no proof placement")


def _environment():
    found = sorted(k for k in os.environ if k.startswith("FRAMAC_WP"))
    if found:
        _fail("wp_environment", f"WP environment variable(s) set: {', '.join(found)}")


def _values(flags, name):
    found = []
    for i, flag in enumerate(flags):
        if flag == name:
            found.append(flags[i + 1] if i + 1 < len(flags) else None)
        elif flag.startswith(name + "="):
            found.append(flag.split("=", 1)[1])
    return found


def _wp_flags(flags, scratch):
    for name, expected in (("-wp-cache", "none"), ("-machdep", "x86_64"), ("-wp-model", "+real")):
        values = _values(flags, name)
        if not values or any(v != expected for v in values):
            _fail("frozen_flags", f"requires only {name} {expected}, got {values}")
    if any("warn-key" in str(flag) for flag in flags):
        _fail("warning_defaults", "Frama-C warning keys must stay at their defaults")
    if any(f.startswith(("-wp-session", "-wp-script", "-load", "-wp-cache-dir")) for f in flags):
        _fail("fresh_session", "loading WP sessions, scripts, or caches is forbidden")
    if any(p.name in ("wp", ".wp", "wp-session", "wp-cache") or "session" in p.name
           for p in Path(scratch).iterdir()):
        _fail("fresh_session", "the working folder contains an existing WP session")


def check_generated(job, adapter, context, inputs, flags, *, command=(), scratch=None, lowering=None):
    """Check generated bytes and frozen plan at the last prelaunch boundary.

    inputs holds (actual path, freshly generated expected text), never a caller-written
    allowlist. The lowering object/its probes come from the generator before hint merge.
    Returns the recorded check for this invocation, also appended to job.setup.
    """
    if not getattr(job, "setup", None):
        # Direct adapter usage outside prove still gets the same preflight.
        from types import SimpleNamespace
        if getattr(job, "setup", None) is None:
            _fail("unplanned_job", "adapter invocation has no planned setup")
        method = getattr(adapter, "method", None)
        begin(job, adapter, {"method_version": {"id": method.id, "sha256": method.sha256}}, method)
    _method(job.setup.get("method"))
    _environment()
    for path, expected in job.setup.get("files", {}).items():
        if _sha(Path(path).read_bytes()) != expected:
            _fail("input_hash", f"{path} changed after the job was planned")
    library_root = job.setup.get("contract_library")
    if library_root is not None:
        from swdb.library import Library
        fresh = Library(library_root)
        if fresh.content_sha256(job.unit.contract) != job.unit.contract_sha256:
            _fail("contract_hash", "the contract changed after planning")
    hashes = {}
    for path, expected in inputs:
        path = Path(path)
        actual = path.read_bytes()
        if actual != expected.encode():
            _fail("input_hash", f"generated input {path.name} differs from its planned bytes")
        hashes[path.name] = _sha(actual)
    lowering = lowering or context.get("lowering")
    if lowering is not None:
        _no_assume(lowering.text, "C lowering")
        pinned = (context.get("pins") or {}).get("c_lowering") or context.get("c_lowering")
        if pinned and pinned.get("sha256") != _sha(lowering.text):
            _fail("lowering_hash", "C lowering differs from its planned pin")
        for probe in lowering.probes:
            if f'"{probe["id"]}"' not in lowering.text:
                _fail("hazard_probes", f"generator probe {probe['id']} is absent from C lowering")
        hashes["lowering"] = _sha(lowering.text)
    if adapter.name == "wp":
        _wp_flags(flags, scratch or job.scratch)
    method = job.setup.get("method")
    tools = context.get("tools") or {}
    if method is not None:
        _lineup(method, adapter, tools, flags)
    plan = {"command": list(map(str, command)), "flags": list(flags), "inputs": hashes,
            "bounds": job.bounds, "method_version": job.setup["report"]["method_version"]}
    result = {"verdict": "passed", "hashes": hashes, "run_plan_sha256": _digest(plan), "tool": adapter.name}
    job.setup["report"]["runs"].append(result)
    job.setup["report"]["hashes"].update(hashes)
    return result


def _lineup(method, adapter, tools, flags):
    lineup = {row["tool"]: row for row in method.data.get("lineup", [])}
    for name, identity_ in tools.get("identities", {}).items():
        if name in lineup and str(identity_[2]) != lineup[name]["version"]:
            _fail("method_version", f"{name} version {identity_[2]} differs from method {lineup[name]['version']}")
    name = "frama-c-wp" if adapter.name == "wp" else adapter.name
    declared = (lineup.get(name) or {}).get("flags", [])
    # Every method flag occurs in its original order; derived bounds, property
    # selection and report destinations may be added but cannot override it.
    for i, flag in enumerate(declared):
        if flag.startswith("-") and i + 1 < len(declared) and not declared[i + 1].startswith("-"):
            values = _values(flags, flag)
            if not values or any(v != declared[i + 1] for v in values):
                _fail("method_version", f"{name} flag {flag} differs from method version")
        elif flag.startswith("-") and flag not in flags:
            _fail("method_version", f"{name} flag {flag} is missing")


def read_wp_reports(goals_json, properties_csv, inventory_path, extern_contracts=None, functions=None):
    """Read a fresh WP run's two reports plus independent generated-goal inventory.

    The adapter owns freshness (exclusive scratch directory, cache none, no sessions),
    never the producer of hint text. Extern allowlist maps exact contracted function
    names to pinned summary/proof-semantics references, prepared by the adapter.
    """
    from swdb.wp_adapter import _goal, UNCLASSIFIED
    def outcome(verdict, failure_class, why, goals=(), unproven=(), assumptions=()):
        return {"verdict": verdict, "failure_class": failure_class, "why": why,
                "goals": list(goals), "unproven": list(unproven), "assumptions": list(assumptions),
                "reading": {"check": identity()["verdict_reading"], "verdict": verdict}}
    if inventory_path is None or not Path(inventory_path).is_file():
        return outcome("not_proven", UNCLASSIFIED, "fresh generated-goal inventory is missing")
    try:
        inventory = json.loads(Path(inventory_path).read_text())
        raw = json.loads(Path(goals_json).read_text())
        with open(properties_csv, newline="") as stream:
            properties = list(csv.DictReader(stream, delimiter="\t"))
    except (OSError, ValueError, TypeError) as exc:
        return outcome("not_proven", UNCLASSIFIED, f"malformed fresh report: {exc}")
    if inventory.get("complete") is not True or inventory.get("version") != "1":
        return outcome("not_proven", UNCLASSIFIED, "incomplete generated-goal inventory")
    reported = {g.get("goal"): g for g in raw}
    generated = {g.get("goal"): g for g in inventory.get("goals", [])}
    if len(reported) != len(raw) or len(generated) != len(inventory.get("goals", [])) or None in reported or None in generated:
        return outcome("not_proven", UNCLASSIFIED, "duplicate or missing goal identity")
    if set(reported) - set(generated):
        return outcome("not_proven", UNCLASSIFIED, "reported goal was not generated by this run")
    extern_contracts = extern_contracts or {}
    assumptions = []
    for prop in inventory.get("properties", []):
        if not prop.get("extern"):
            continue
        function = prop.get("function")
        reference = extern_contracts.get(function)
        if prop.get("kind") != "contract" or not reference:
            raise AdapterError(f"verdict reading [unexpected_extern]: {prop.get('description') or prop.get('property')} "
                               f"in {function or 'global scope'} is not a pinned summary or maa contract; batch stops")
        assumptions.append({"kind": "assumed_clause", "reference": reference,
                            "sentence": f"WP treats contract property {prop['property']} of {function} as Extern: "
                                        f"{prop.get('description') or prop['property']}."})
    goals, unproven = [], []
    for name, expected in generated.items():
        raw_goal = reported.get(name)
        if raw_goal is None:
            goal = {"goal": name, "property": expected.get("property"), "function": expected.get("function"),
                    "status": "unknown", "solver": None, "seconds": None}
            goals.append(goal)
            unproven.append({"property": goal["property"], "goal": name, "status": "untried", "failure_class": "unknown"})
            continue
        goal = _goal(raw_goal)
        goals.append(goal)
        if bool(raw_goal.get("smoke")) != bool(expected.get("smoke")) or \
                bool(raw_goal.get("passed")) != bool(expected.get("passed")):
            return outcome("not_proven", UNCLASSIFIED, f"goal {name}: report disagrees with fresh inventory", goals)
        if expected.get("smoke"):
            if not expected.get("passed"):
                return outcome("not_proven", "vacuous_pass", f"smoke test {name} failed (dead code)", goals,
                               [{"property": goal["property"], "goal": name, "status": "failed smoke test",
                                 "failure_class": "vacuous_pass"}], assumptions)
            continue
        if not expected.get("passed"):
            mapping = {"timeout": "timeout", "stepout": "timeout", "unknown": "unknown", "untried": "unknown",
                       "failed": "solver_error"}
            statuses = expected.get("results") or [str(raw_goal.get("verdict", "unknown")).lower()]
            failure = next((mapping[s] for s in ("failed", "timeout", "stepout", "unknown", "untried") if s in statuses), None)
            if failure is None:
                return outcome("not_proven", UNCLASSIFIED, f"goal {name} is not Valid and has no failure class", goals)
            unproven.append({"property": goal["property"], "goal": name, "status": goal["status"], "failure_class": failure})
    # CSV catches failed call-site preconditions and termination properties that
    # are not captured by a locally Valid target. Global lemmas are never filtered.
    invalid = [row for row in properties if row.get("status") != "Valid"
               and row.get("status") != "Considered valid"
               and (not functions or row.get("function") in functions or not row.get("function"))]
    if invalid and not unproven:
        return outcome("not_proven", UNCLASSIFIED, "not-Valid properties have no classified failing goal", goals, invalid, assumptions)
    if unproven:
        return outcome("not_proven", unproven[0]["failure_class"], "one or more generated properties are not Valid",
                       goals, unproven, assumptions)
    if not goals:
        return outcome("not_proven", "vacuous_pass", "WP generated no goal", assumptions=assumptions)
    return outcome("proven", None, "every generated goal passed; every Extern belongs to a pinned contract",
                   goals, assumptions=assumptions)


def compile_report_module(workdir):
    """Compile the inventory reader against this host's Frama-C/WP API."""
    import shlex
    import shutil
    import subprocess
    source, out = Path(workdir) / "proof_report.ml", Path(workdir) / "proof_report.cmxs"
    shutil.copyfile(REPORT_MODULE, source)
    command = shlex.split(os.environ.get("SWDB_OCAMLFIND") or "opam exec --switch=framac-33 -- ocamlfind")
    done = subprocess.run([*command, "ocamlopt", "-shared", "-linkall", "-package", "frama-c.kernel,frama-c-wp.core",
                           "-o", str(out), str(source)], capture_output=True, text=True, timeout=120)
    if done.returncode:
        _fail("report_reader", f"cannot compile fresh inventory reader: {(done.stderr or done.stdout)[:800]}")
    return out
