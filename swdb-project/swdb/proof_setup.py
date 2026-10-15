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
# Named sources that generate/check domains or interpret execution evidence.
# Translator, lowering, std-model and semantics bytes also have their own pins.
CHECK_SOURCES = ("proof_setup.py", "proof_report.ml", "proof.py", "cbmc_adapter.py", "cbmc_equivalence.py",
                 "cbmc_product.py", "wp_adapter.py", "crux_adapter.py", "rocq_adapter.py", "rss_watchdog.py",
                 "vocab.py", "formal_frame.py", "acsl_subset.py", "framac.py", "hint_check.py", "hint_tree.ml",
                 "wp_pointer_bounds.py", "proof_semantics.py", "vector_ownership.py", "standard_model_view.py",
                 "array_domains.py", "model_domains.py", "dx_array_domains.py", "bounded_entry_windows.py",
                 "bounded_chain.py", "summary_bindings.py", "helper_windows.py")
REQUIRED_WP_SWITCHES = (("-wp-no-filter-init", "-wp-filter-init"),)
_COMPILED_MODULES = {}
_ASSUME = re.compile(r"\b(?:llvm_assume|crucible_assume|__VERIFIER_assume)\b|\b(?:__CPROVER_assume|SWDB_ASSUME|assume)\s*\(")


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    from swdb import paths
    folder = Path(__file__).parent
    dependencies = [("swdb/" + name, folder / name) for name in CHECK_SOURCES]
    dependencies.append(("vocab/proof_failure_classes.yaml", paths.VOCAB / "proof_failure_classes.yaml"))
    # Frame each name and digest; concatenation must not blur dependency boundaries.
    sha = _digest([{"path": name, "sha256": _sha(path.read_bytes())} for name, path in dependencies])
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


def check_semantics_hints(base, hints):
    """Protect model ghost state with a deliberately small hint-ghost language.

    Frama-C's noninterference check protects real C state, not trusted ghost
    state. Semantics jobs therefore admit only fresh scalar witnesses and the
    checked store-frame bound. Calls, pointers, indexed writes and shadowing
    are refused rather than inferred safe from their spelling.
    """
    existing = set(re.findall(r"\b[A-Za-z_]\w*\b", base))
    macros = set(re.findall(r"^\s*#\s*define\s+([A-Za-z_]\w*)", base, re.M))
    owned = set()
    scalar = r"(?:(?:unsigned|signed)\s+)?(?:int|long|short|char|_Bool)"
    for hint in hints:
        text = re.sub(r"/\*.*?\*/|//[^\n]*", " ", hint["text"], flags=re.S).strip()
        if hint.get("kind") != "ghost" and not re.search(r"\bghost\b", text):
            continue
        if not text.startswith("ghost ") or not text.endswith(";"):
            _fail("semantics_ghost_ownership", "semantics ghost hints require scalar declarations or assignments")
        if macros.intersection(re.findall(r"\b[A-Za-z_]\w*\b", text)):
            _fail("semantics_ghost_ownership", "ghost witness text may not expand a preprocessor macro")
        for statement in text[6:].split(";")[:-1]:
            statement = statement.strip()
            declaration = re.fullmatch(rf"{scalar}\s+([A-Za-z_]\w*)(?:\s*=\s*(.+))?", statement, re.S)
            assignment = re.fullmatch(r"([A-Za-z_]\w*)\s*=\s*(.+)", statement, re.S)
            if declaration:
                name, expression = declaration.groups()
                if name in existing or name in owned:
                    _fail("semantics_ghost_ownership", f"ghost declaration shadows an existing name: {name}")
                owned.add(name)
            elif assignment:
                name, expression = assignment.groups()
                if name not in owned and name != "dx_store_bound":
                    _fail("semantics_ghost_ownership", f"ghost write targets trusted or unowned state: {name}")
            else:
                _fail("semantics_ghost_ownership", "only simple scalar ghost declarations and assignments are allowed")
            if expression is not None and (
                    not re.fullmatch(r"[A-Za-z_0-9\s()+*/%<>=!~^|?:.-]+", expression)
                    or "??" in expression
                    or re.search(r"\b[A-Za-z_]\w*\s*\(|\)\s*\(|\+\+|--|<<=|>>=|(?<![<>=!])=(?!=)", expression)):
                _fail("semantics_ghost_ownership", "ghost witness expressions may not call, take addresses, or mutate state")


def _method(method):
    if method is not None and _sha(Path(method.path).read_bytes()) != method.sha256:
        _fail("method_version", f"method {method.id} changed after the job was planned")
    if method is not None and method.data.get("evidence_kind") == "execution":
        checks = method.data.get("checks") or {}
        for name, current in identity().items():
            frozen = checks.get(name)
            if not isinstance(frozen, dict) or frozen.get("version") != current["version"] or frozen.get("sha256") != current["sha256"]:
                _fail("method_version", f"{method.id} does not pin the installed {name} version and content hash")


def _job_plan(job, adapter):
    return {"bounds": job.bounds, "budget_seconds": job.budget_seconds,
            "defines": list(getattr(adapter, "defines", ())), "function": job.unit.function,
            "contract": job.unit.contract, "contract_sha256": job.unit.contract_sha256}


def begin(job, adapter, pins, method):
    """Universal preflight before adapter.run, including a scripted bounded job."""
    _method(method)
    report = {"check": identity()["proof_setup_check"], "verdict": "passed", "method_version": pins["method_version"],
              "hashes": {"contract": job.unit.contract_sha256, "summaries": _digest(list(job.summaries))}, "runs": []}
    plan_hash = _digest(_job_plan(job, adapter))
    report["hashes"]["run_plan"] = plan_hash
    job.setup.update(report=report, method=method, adapter=adapter, files={}, plan_sha256=plan_hash)
    library = getattr(adapter, "library", None)
    if library is not None and job.unit.contract and not job.unit.contract.startswith("c_model."):
        from swdb.library import Library
        fresh = Library(library.root)
        if fresh.content_sha256(job.unit.contract) != job.unit.contract_sha256:
            _fail("contract_hash", "contract differs from its planned content hash")
        entry = fresh.get(job.unit.contract) or {}
        _placements(entry)
        job.setup["contract_library"] = library.root
    # Scan the actual translation units of both sides; scripted fixtures have no
    # real source traversal and supply their own explicit manifest.
    if library is not None and not str(job.unit.contract or "").startswith("c_model."):
        from swdb.wp_adapter import _unit_source
        trees = [job.unit.tree]
        baseline = (getattr(adapter, "spec", {}) or {}).get("baseline") or {}
        if baseline.get("tree"):
            trees.append(baseline["tree"])
        for tree in trees:
            source = _unit_source(Path(tree), job.unit.function)
            _no_assume(source.read_text(), str(source))
            job.setup["files"][str(source)] = _sha(source.read_bytes())
    plan = getattr(adapter, "script", {}).get("setup") or {}
    if plan:
        if plan.get("run_plan_sha256", plan_hash) != plan_hash:
            _fail("run_plan_hash", "the job differs from its pinned run plan")
        for row in plan.get("inputs", []):
            path = Path(row["path"])
            if not path.is_absolute():
                path = Path(job.scratch) / path
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
            selected = _values(plan.get("flags", []), "-wp-prover")
            if method is not None and selected and any(value.split(",") != wp_provers(method) for value in selected):
                _fail("method_version", "WP solver order differs from the method version")
        elif plan.get("tool") == "cbmc":
            check_cbmc_flags(plan.get("flags", []))
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


def wp_switch_problem(flags):
    """Canonical boolean switches: no pseudo-value argv and no later re-enabling override."""
    for required, opposite in REQUIRED_WP_SWITCHES:
        if flags.count(required) != 1 or any(
                flag == opposite or flag.startswith((required + "=", opposite + "=")) for flag in flags):
            return f"requires exactly {required} without {opposite} or boolean =value overrides"
    return None


def _wp_flags(flags, scratch):
    for name, expected in (("-wp-cache", "none"), ("-machdep", "x86_64"), ("-wp-model", "+real")):
        values = _values(flags, name)
        if not values or any(v != expected for v in values):
            _fail("frozen_flags", f"requires only {name} {expected}, got {values}")
    switch_problem = wp_switch_problem(flags)
    if switch_problem:
        _fail("frozen_switches", switch_problem)
    if any(str(flag).startswith("-wp-prop") for flag in flags):
        _fail("property_selection", "WP may not suppress generated properties or global lemmas")
    if any("warn-key" in str(flag) for flag in flags):
        _fail("warning_defaults", "Frama-C warning keys must stay at their defaults")
    for index, flag in enumerate(flags):
        if flag.startswith("-load"):
            value = flags[index + 1] if index + 1 < len(flags) else ""
            key = str(Path(value).resolve())
            pinned = _COMPILED_MODULES.get(key)
            if flag != "-load-module" or pinned is None or _sha(Path(value).read_bytes()) != pinned[0] or _sha(REPORT_MODULE.read_bytes()) != pinned[1]:
                _fail("fresh_session", "only the checked, freshly compiled proof inventory module may be loaded")
        if flag.startswith(("-wp-session", "-wp-script", "-wp-cache-dir")):
            _fail("fresh_session", "loading WP sessions, scripts, or caches is forbidden")
    if any(p.name in ("wp", ".wp", ".frama-c", "wp-session", "wp-cache") or "session" in p.name
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
        if getattr(job, "setup", None) is None:
            _fail("unplanned_job", "adapter invocation has no planned setup")
        method = getattr(adapter, "method", None)
        begin(job, adapter, {"method_version": {"id": method.id, "sha256": method.sha256}}, method)
    _method(job.setup.get("method"))
    if _digest(_job_plan(job, adapter)) != job.setup["plan_sha256"]:
        _fail("run_plan_hash", "bounds, build constants, budget or proof unit changed after planning")
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
    summary_pins = (context.get("pins") or {}).get("summaries", [])
    if library_root is not None:
        for summary in summary_pins:
            if fresh.content_sha256(summary["id"]) != summary["sha256"]:
                _fail("summary_hash", f"summary {summary['id']} differs from its pinned content")
    hashes = {"summaries": _digest(summary_pins)}
    if adapter.name in {'cbmc', 'wp', 'crux-llvm-c', 'crux-llvm-cxx'}:
        from swdb import summary_bindings
        try:
            checked_summaries = summary_bindings.recheck(adapter, context)
        except (summary_bindings.Refused, ValueError) as exc:
            _fail('summary_binding', str(exc))
        hashes['summary_bindings'] = _digest(checked_summaries)
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
        final_text = "\n".join(Path(path).read_text() for path, _expected in inputs)
        for probe in lowering.probes:
            if f'"{probe["id"]}"' not in lowering.text or f'"{probe["id"]}"' not in final_text:
                _fail("hazard_probes", f"generator probe {probe['id']} is absent from C lowering")
        hashes["lowering"] = _sha(lowering.text)
    baseline = context.get("baseline_lowering")
    if baseline is not None:
        _no_assume(baseline.text, "baseline C lowering")
        pin = context["pins"]["baseline_c_lowering"]
        if pin["sha256"] != _sha(baseline.text):
            _fail("lowering_hash", "baseline C lowering differs from its planned pin")
        hashes["baseline_lowering"] = _sha(baseline.text)
    if adapter.name in {"cbmc", "crux-llvm-c", "crux-llvm-cxx"}:
        from swdb import bounded_initialization
        admissions = context.get("settings", {}).get("bounded_initialization") or {}
        sides = {"candidate": lowering, "baseline": baseline} if baseline is not None else {"unit": lowering}
        for side, lowered in sides.items():
            expected = admissions if side == "unit" else admissions.get(side, {})
            if lowered is None or not expected:
                _fail("bounded_initialization", "bounded verifier has no generated initializedness admission")
            try:
                cap = max((value for name, value in job.bounds.items() if name != "threads"), default=0)
                actual = bounded_initialization.check(lowered, cap, library=getattr(adapter, "library", None),
                                                       model=context.get("model"))
                bounded_initialization.check_model_input(actual, context.get("model"),
                    getattr(adapter, "library", None), lowered.defines,
                    "\n".join(Path(path).read_text() for path, _expected in inputs))
            except ValueError as exc:
                _fail("bounded_initialization", str(exc))
            if actual != expected or actual.get("verdict") != "passed":
                _fail("bounded_initialization", f"{side} initializedness admission changed or refused")
        hashes["bounded_initialization"] = _digest(admissions)
    if adapter.name == "wp" and context.get("semantics"):
        base = context.get("semantics_hint_base")
        if base is None:
            _fail("semantics_ghost_ownership", "semantics invocation has no pinned hint-free base")
        check_semantics_hints(base, getattr(adapter, "hints", []))
    if adapter.name == "wp":
        from swdb import standard_model_view, wp_pointer_bounds
        try:
            if "pointer_bounds_model_source" in context:
                from swdb import c_lowering
                model = c_lowering.model_text(job.unit.function)
                if context.get("standard_model_view"):
                    view = standard_model_view.wp_view(job.unit.function, model, scratch or job.scratch)
                    if view != context["standard_model_view"]["view"]:
                        _fail("pointer_bounds", "checked standard model view changed after planning")
                    model = view.text
                fresh = "\n".join([*c_lowering.HEADERS, model]) + "\n" if model is not None else None
                if fresh != context["pointer_bounds_model_source"]:
                    _fail("pointer_bounds", "generated C model changed after planning")
                generated, report = wp_pointer_bounds.model_view(fresh, scratch or job.scratch)
                if generated != context["wp_expected_text"] or report != context["pointer_bounds_report"]:
                    _fail("pointer_bounds", "generated C model pointer checks changed after planning")
            else:
                if context.get("helper_windows"):
                    try:
                        adapter.check_helper_windows(job, context)
                    except ValueError as exc:
                        _fail("helper_windows", str(exc))
                if ((lowering.pointer_bounds or {}).get("entry_windows") or (lowering.pointer_bounds or {}).get("owner") or
                        any(row.get("kind") in {"call", "producer", "import"} for row in lowering.pointer_bounds.get("sites", []))):
                    wp_pointer_bounds.recheck_source(lowering, context.get("pointer_source_plan"))
                if (lowering.pointer_bounds or {}).get("owner"):
                    from swdb import vector_ownership
                    owner = context.get("vector_ownership")
                    if not owner:
                        _fail("pointer_bounds", "closed-owner source registry has no independently checked view")
                    try:
                        vector_ownership.check_origins(lowering, owner["source"], owner["view"],
                                                       owner["formal_texts"], getattr(adapter, "hints", []))
                    except vector_ownership.Refused as exc:
                        _fail("pointer_bounds", str(exc))
                wp_pointer_bounds.check_semantic_origins(lowering, adapter.library, adapter.defines)
                wp_pointer_bounds.check_input(lowering, context["pointer_bounds_base"], context["pointer_bounds_report"],
                    "\n".join(Path(path).read_text() for path, _expected in inputs))
        except (KeyError, standard_model_view.Refused, wp_pointer_bounds.Refused) as exc:
            _fail("pointer_bounds", str(exc))
        _wp_flags(list(command) if command else flags, scratch or job.scratch)
    elif adapter.name == "cbmc":
        check_cbmc_flags(list(command) if command else flags)
        from swdb import bounded_entry_windows, c_lowering
        try:
            adapter.check_entry_windows(job, context, inputs)
        except (bounded_entry_windows.Refused, c_lowering.LoweringError) as exc:
            _fail('pointer_bounds', str(exc))
    elif adapter.name in {"crux-llvm-c", "crux-llvm-cxx"}:
        from swdb import c_lowering
        try:
            checked = adapter.check_source_admission(job, context, inputs)
        except (ValueError, c_lowering.LoweringError) as exc:
            _fail('bounded_source_admission', str(exc))
        hashes['bounded_source_admission'] = _digest(checked)
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


def wp_provers(method):
    """The explicitly frozen portfolio, or the legacy method's historical order."""
    row = next((r for r in method.data.get("lineup", []) if r.get("tool") == "frama-c-wp"), {})
    declared = _values(row.get("flags", []), "-wp-prover")
    if len(declared) > 1:
        _fail("method_version", "the method declares WP solver selection more than once")
    return declared[0].split(",") if declared else ["alt-ergo", "z3", "cvc5"]


def check_cbmc_flags(flags, *, require=True):
    """Frozen safety checks and full property/entrypoint selection; created 2026-10-15 ET.

    Inspect the complete command too: SWDB_CBMC may include prefix arguments. The
    policy lives in this content-pinned check, independently of adapter constants.
    """
    required = {"--unwinding-assertions", "--pointer-overflow-check"}
    forbidden = {"--no-standard-checks", "--no-bounds-check", "--no-pointer-check", "--no-pointer-primitive-check",
                 "--no-pointer-overflow-check", "--no-signed-overflow-check", "--no-div-by-zero-check",
                 "--no-undefined-shift-check", "--no-unwinding-assertions", "--no-assertions", "--no-assumptions",
                 "--no-built-in-assertions", "--partial-loops", "--property", "--function", "--main", "--cover"}
    words = {str(flag).split("=", 1)[0] for flag in flags}
    disabled = words & forbidden
    if disabled:
        _fail("cbmc_safety_flags", f"CBMC safety/property/entrypoint override is forbidden: {sorted(disabled)}")
    if require and not required <= set(flags):
        _fail("cbmc_safety_flags", f"CBMC must retain frozen flags: {sorted(required - set(flags))}")


def _lineup(method, adapter, tools, flags):
    lineup = {row["tool"]: row for row in method.data.get("lineup", [])}
    for name, identity_ in tools.get("identities", {}).items():
        installed = str(identity_[2])
        pinned = (lineup.get(name) or {}).get("version")
        matches = installed == pinned or (name == "cbmc" and pinned is not None and installed.startswith(pinned + "."))
        if name in lineup and not matches:
            _fail("method_version", f"{name} version {identity_[2]} differs from method {lineup[name]['version']}")
    name = "frama-c-wp" if adapter.name == "wp" else "crux-llvm" if adapter.name.startswith("crux-llvm") else adapter.name
    declared = (lineup.get(name) or {}).get("flags", [])
    if adapter.name == "wp":
        expected_provers = wp_provers(method)
        for key, value in (("-wp-timeout", str(method.data["budgets"]["wp_seconds_per_solver"])),
                           ("-wp-par", "1")):
            if _values(flags, key) != [value] and set(_values(flags, key)) != {value}:
                _fail("method_version", f"{key} differs from the frozen method budget/settings")
        selected = _values(flags, "-wp-prover")
        if not selected or any(value.split(",") != expected_provers for value in selected):
            _fail("method_version", "WP solver selection differs from the method lineup")
        if "-wp-smoke-tests" not in flags:
            _fail("smoke_tests", "the final WP run must generate smoke tests")
    # Every method flag occurs in its original order; derived bounds, property
    # selection and report destinations may be added but cannot override it.
    for i, flag in enumerate(declared):
        if flag.startswith("-") and i + 1 < len(declared) and not declared[i + 1].startswith("-"):
            values = _values(flags, flag)
            if not values or any(v != declared[i + 1] for v in values):
                _fail("method_version", f"{name} flag {flag} differs from method version")
        elif flag.startswith("-") and flag not in flags:
            _fail("method_version", f"{name} flag {flag} is missing")


def _property_rows(stream):
    """Frama-C 33 leaves indented multiline property text unquoted in its TSV.

    Attach only a single indented cell to a preceding complete row. An incomplete
    row with columns, an unindented fragment, or a continuation before a row is malformed.
    A continuation is text of the property, never a new property with a missing status.
    """
    reader = csv.reader(stream, delimiter="\t")
    header = next(reader, [])
    expected = ["directory", "file", "line", "function", "property kind", "status", "property"]
    if header != expected:
        raise ValueError("unexpected WP property report header")
    rows = []
    for values in reader:
        if not values:
            continue
        if len(values) == len(header):
            rows.append(dict(zip(header, values)))
        elif len(values) == 1 and values[0][:1].isspace() and rows:
            rows[-1]["property"] += "\n" + values[0]
        else:
            raise ValueError("incomplete WP property row")
    return rows


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
            properties = _property_rows(stream)
    except (OSError, ValueError, TypeError) as exc:
        return outcome("not_proven", UNCLASSIFIED, f"malformed fresh report: {exc}")
    if not isinstance(inventory, dict) or inventory.get("complete") is not True or inventory.get("version") != "1":
        return outcome("not_proven", UNCLASSIFIED, "incomplete generated-goal inventory")
    if (not isinstance(inventory, dict) or not isinstance(raw, list) or any(not isinstance(g, dict) for g in raw)
            or not isinstance(inventory.get("goals"), list) or not isinstance(inventory.get("properties"), list)
            or any(not isinstance(g, dict) for g in inventory["goals"] + inventory["properties"])):
        return outcome("not_proven", UNCLASSIFIED, "fresh reports have the wrong shape")
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
    smoke_failures = [p for p in inventory.get("properties", []) if p.get("generated_smoke_failure")]
    goals, unproven = [], []
    for name, expected in generated.items():
        raw_goal = reported.get(name)
        if raw_goal is None:
            direct = expected.get("passed") is True and (expected.get("smoke") or "valid" in expected.get("results", []))
            goal = {"goal": name, "property": expected.get("property"), "function": expected.get("function"),
                    "status": "valid" if direct else "unknown", "solver": None, "seconds": None,
                    "smoke": bool(expected.get("smoke")), "source": "wp_inventory"}
            goals.append(goal)
            if not direct:
                smoke_failed = bool(expected.get("smoke")) and not expected.get("passed")
                goal["status"] = "failed_smoke" if smoke_failed else "unknown"
                unproven.append({"property": goal["property"], "goal": name, "status": goal["status"],
                                 "failure_class": "vacuous_pass" if smoke_failed else "unknown"})
            continue
        goal = {**_goal(raw_goal), "smoke": bool(raw_goal.get("smoke")), "source": "wp_json"}
        goals.append(goal)
        if bool(raw_goal.get("smoke")) != bool(expected.get("smoke")) or \
                bool(raw_goal.get("passed")) != bool(expected.get("passed")):
            return outcome("not_proven", UNCLASSIFIED, f"goal {name}: report disagrees with fresh inventory", goals)
        if expected.get("smoke"):
            if not expected.get("passed"):
                goal["status"] = "failed_smoke"
                unproven.append({"property": goal["property"], "goal": name, "status": "failed smoke test",
                                 "failure_class": "vacuous_pass"})
            continue
        if expected.get("passed") and "valid" not in expected.get("results", []):
            return outcome("not_proven", UNCLASSIFIED, f"goal {name} has no direct Valid prover result", goals)
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
    def declared_unit_precondition(row):
        # WP reports a proof unit's own requires as Ignored under -report-untried:
        # it is the explicit condition of this conditional theorem, not a call-site
        # obligation. Never apply this exception to Unknown or failing instances.
        return row.get("status") == "Ignored" and row.get("property kind") == "precondition" and any(
            prop.get("function") == row.get("function") and str(prop.get("line")) == str(row.get("line"))
            and str(prop.get("description", "")).startswith("requires")
            for prop in inventory.get("properties", []))
    invalid = [row for row in properties if row.get("status") != "Valid"
               and row.get("status") != "Considered valid" and not declared_unit_precondition(row)
               and (not functions or row.get("function") in functions or not row.get("function"))]
    classified_properties = []
    for row in invalid:
        smoke = next((prop for prop in smoke_failures if prop.get("function") == row.get("function")
                      and str(prop.get("line")) == str(row.get("line"))), None)
        if smoke is not None:
            classified_properties.append({"property": row.get("property"), "kind": row.get("property kind"),
                "function": row.get("function"), "line": smoke.get("line"), "status": row.get("status"),
                "failure_class": "vacuous_pass"})
            continue
        aliases = {prop.get("property") for prop in inventory.get("properties", [])
                   if prop.get("function") == (row.get("function") or None)
                   and str(prop.get("line", "")) == str(row.get("line", ""))}
        dependency_map = {prop["property"]: set(prop.get("dependencies", [])) | ({prop["origin"]} if prop.get("origin") else set())
                          for prop in inventory.get("properties", [])}
        pending, reachable = list(aliases), set(aliases)
        while pending:
            dependency = pending.pop()
            for dep in dependency_map.get(dependency, set()) - reachable:
                reachable.add(dep)
                pending.append(dep)
        matches = []
        for failed in unproven:
            origin = reported.get(failed["goal"]) or generated.get(failed["goal"], {})
            same_function = origin.get("function") == (row.get("function") or None)
            same_line = str(origin.get("line", "")) == str(row.get("line", ""))
            origins = {prop.get("origin") for prop in inventory.get("properties", [])
                       if prop.get("property") == failed.get("property") and prop.get("origin")}
            doomed = set(generated.get(failed["goal"], {}).get("targets", []))
            same_name = (failed.get("property") == row.get("property") or failed.get("property") in aliases
                         or bool(origins & aliases) or bool(doomed & aliases) or failed.get("property") in reachable)
            if same_name or (same_function and same_line):
                matches.append(failed)
        if not matches:
            return outcome("not_proven", UNCLASSIFIED, "not-Valid property has no classified failing goal: " +
                           str(row.get("property")), goals, classified_properties, assumptions)
        classified_properties.append({"property": row.get("property"), "kind": row.get("property kind"),
            "function": row.get("function"), "line": int(row["line"]) if str(row.get("line", "")).isdigit() else None,
            "status": row.get("status"), "goal": matches[0]["goal"], "failure_class": matches[0]["failure_class"]})
    unproven = classified_properties + unproven
    if smoke_failures or any(p["failure_class"] == "vacuous_pass" for p in unproven):
        return outcome("not_proven", "vacuous_pass", "one or more smoke tests failed", goals, unproven, assumptions)
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
    _COMPILED_MODULES[str(out.resolve())] = (_sha(out.read_bytes()), _sha(REPORT_MODULE.read_bytes()))
    return out
