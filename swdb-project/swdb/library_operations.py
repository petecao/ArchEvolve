"""Library-operation certification and body rules (tickets 49-51). Created 2026-10-03 ET.

Original SWDB code. `swdb certify ENTRY --profile PROFILE` certifies a library operation
(plain C++, never a hardware API) against its plain C++ reference semantics with the
ported two-binary harness (`swdb.extensa.synthesis.certify`) and a certification profile
(`swdb.extensa.profiles`). Every matrix cell and every negative control runs; a control
counts as rejected only when it builds and fails its expected named check. When the
entry declares a contract probe, one more cell compiles the ported runtime probes into a
certification-only build; the timed-style builds never contain them.
"""
from __future__ import annotations

import datetime
import json
import os
import platform
import re
import secrets
import shutil
import signal
import socket
import subprocess
import uuid
from pathlib import Path

from swdb import artifacts, paths, workflow
from swdb.cli import Failure, UsageError

VERSION = "1.0"
DX100_INCLUDE = re.compile(r'(?:#|%:)\s*include\s*[<"]([^>"]+)[>"]')
DX100_NAMES = re.compile(r"(?i)(?:^|/)(?:maa[^/]*|.*dx100[^/]*|.*dxc_[^/]*|reference\.hpp)$")
MAA_CALL = re.compile(r"\bmaa_\w*\s*\(")


# --- swdb validate: library-operation bodies never call a hardware interface ------

def body_problems(library, entry):
    """(field, reason) for a body that includes a DX100 header or calls `maa_*`."""
    location = entry.get("location") or {}
    try:
        body = library.resolve(location)
    except (KeyError, TypeError, ValueError):
        return []
    text = body.read_text(errors="ignore")
    found = []
    for target in DX100_INCLUDE.findall(text):
        if DX100_NAMES.search(target.strip()):
            found.append(("location", f"library-operation body includes a DX100 header: {target}"))
    if MAA_CALL.search(re.sub(r"//[^\n]*|/\*.*?\*/", " ", text, flags=re.S)):
        found.append(("location", "library-operation body calls a maa_* hardware function"))
    return found


# --- compilers and targets ----------------------------------------------------------

def _which(*names):
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def sanitize_compiler():
    chosen = os.environ.get("SWDB_LIBOP_SANITIZE_CXX")
    if chosen:
        return chosen
    return _which("clang++", "g++") if platform.system() == "Darwin" else _which("g++", "clang++")


def openmp_compiler():
    chosen = os.environ.get("SWDB_LIBOP_OPENMP_CXX")
    if chosen:
        return chosen
    if platform.system() == "Darwin":
        return _which("g++-16", "g++-15", "g++-14", "g++-13")
    return _which("g++")


def targets(profile, include_dirs):
    from swdb.extensa.synthesis.spec import TargetSpec
    from swdb.extensa.synthesis.targets.cpu_like import CpuCompileTarget
    incs = tuple(f"-I{d}" for d in include_dirs)
    result = {}
    for build in profile.builds:
        if build == "sanitized":
            cc = sanitize_compiler()
            if not cc:
                raise Failure("no C++ compiler for the sanitized certification build")
            result[build] = CpuCompileTarget(TargetSpec("sanitized", platform.machine(), cc,
                                                        ("-std=c++11", "-O1", *incs)))
        else:
            cc = openmp_compiler()
            if not cc:
                raise Failure("no OpenMP-capable C++ compiler (set SWDB_LIBOP_OPENMP_CXX)")
            result[build] = OmpTarget(TargetSpec("openmp", platform.machine(), cc,
                                                 ("-std=c++11", "-O3", "-fopenmp", *incs)), profile.threads)
    return result


def _omp_target_class():
    from swdb.extensa.synthesis.targets.cpu_like import CpuCompileTarget

    class _Omp(CpuCompileTarget):
        """The OpenMP cell: same build seam, runs with a fixed OMP thread count."""

        def __init__(self, spec, threads):
            super().__init__(spec)
            self.threads = threads

        def run(self, binary, args, cwd=None, timeout_s=600):
            env = {**os.environ, "OMP_NUM_THREADS": str(self.threads), "OMP_DYNAMIC": "FALSE"}
            with subprocess.Popen([str(binary), *map(str, args)], cwd=cwd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, start_new_session=True, env=env) as proc:
                try:
                    out, err = proc.communicate(timeout=timeout_s)
                    return proc.returncode, (out or "") + (err or "")
                except subprocess.TimeoutExpired:
                    return 124, f"timeout after {timeout_s}s"
                finally:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass

        def sanitized_run(self, binary, args, cwd=None, timeout_s=600):
            return self.run(binary, args, cwd=cwd, timeout_s=timeout_s)
    return _Omp


def OmpTarget(spec, threads):
    return _omp_target_class()(spec, threads)


# --- certification --------------------------------------------------------------------

def _pin(library, pin, what):
    if not isinstance(pin, dict) or "path" not in pin or "sha256" not in pin:
        raise UsageError(f"{what} needs a path and sha256 pin")
    try:
        path = library.resolve(pin)
    except ValueError as exc:
        raise UsageError(f"{what}: {exc}") from None
    if artifacts.file_hash(path) != pin["sha256"]:
        raise UsageError(f"{what} sha256 differs from its pin: {pin['path']}")
    return path


def inputs(library, entry):
    """Resolve and verify every pinned input of a library-operation certification."""
    test = entry.get("differential_test") or {}
    family = test.get("family")
    from swdb.extensa.synthesis.families import FAMILIES
    if family not in FAMILIES:
        raise UsageError(f"library operation {entry['id']} names no supported differential family")
    files = test.get("files") or {}
    controls = {}
    for clause in entry.get("clauses", []):
        control = clause.get("negative_control") or {}
        if control.get("id") and control["id"] != "none":
            if "mutation" not in control:
                raise UsageError(f"control {control['id']} has no pinned mutation")
            controls[control["id"]] = {"check": control.get("check"), "kind": control.get("kind"),
                                       "clause": clause["id"],
                                       "path": _pin(library, control["mutation"], f"control {control['id']}")}
    return {"family": family,
            "body": _pin(library, {**entry["location"], "sha256": entry["code_sha256"]}, "body"),
            "reference": _pin(library, entry["reference_semantics"], "reference semantics"),
            "run_template": _pin(library, test, "differential driver"),
            "reference_template": _pin(library, files.get("reference_template"), "reference template"),
            "candidate_template": _pin(library, files.get("candidate_template"), "candidate template"),
            "probe": test.get("probe"), "controls": controls,
            "sizes": dict((test.get("input_set") or {}).get("sizes") or {})}


def _source_digest(library_root):
    roots = [Path(__file__), *sorted((paths.HOME / "swdb/extensa").rglob("*.py"))]
    rows = [{"path": p.relative_to(paths.HOME).as_posix(), "sha256": artifacts.file_hash(p)} for p in roots]
    return artifacts.digest(rows)


def _run_cell(family, header, target, folder, resolved, profile, seed, sanitize):
    from swdb.extensa.synthesis.certify import certify_backend
    drivers = folder / "drivers"
    drivers.mkdir(parents=True, exist_ok=True)
    from swdb.extensa.synthesis.certify import family_and_shape
    _fam, sc = family_and_shape(family)
    shutil.copy(resolved["run_template"], drivers / sc.run_template)
    shutil.copy(resolved["reference_template"], drivers / sc.ref_template)
    sizes = {**resolved["sizes"], **dict(profile.sizes)}
    return certify_backend(family, header, target, folder, drivers_dir=drivers,
                           reference_header=resolved["reference"], seed=seed, n_cases=profile.n_cases,
                           sizes=sizes, cand_template=resolved["candidate_template"], sanitize=sanitize)


def _control_status(cells, expected):
    if any(c["outcome"] == "survived" for c in cells):
        return "survived", "a matrix build accepted the control"
    if any(c["outcome"] == "invalid" for c in cells):
        return "invalid", "a control build failed or the reference aborted"
    if any(c["check"] == expected for c in cells):
        return "rejected", expected
    return "invalid", "rejected only by checks other than " + str(expected)


def certify_entry(store, library, entry_id, profile_path, runs_dir=None, seed=None):
    from swdb.extensa.profiles import ProfileError, check_against_entry, load_profile
    entry = library.get(entry_id)
    if entry is None or entry.get("kind") != "library_operation":
        raise UsageError("profile certification requires a library-operation entry")
    try:
        profile = load_profile(Path(profile_path))
        check_against_entry(profile, entry)
    except ProfileError as exc:
        raise Failure(f"certification refused: {exc}") from None
    resolved = inputs(library, entry)
    seed = secrets.randbits(32) if seed is None else int(seed)
    base = artifacts.external_directory(runs_dir or "/private/tmp/swdb-certification")
    folder = base / ("certify-" + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    content_sha256 = library.content_sha256(entry_id)
    dependencies = library.dependency_pins(entry_id)
    command_hash = _source_digest(library.root)
    builds = targets(profile, [resolved["reference"].parent, resolved["body"].parent])
    matrix, control_cells = [], {cid: [] for cid in resolved["controls"]}
    for build, target in builds.items():
        sanitize = build == "sanitized"
        result = _run_cell(resolved["family"], resolved["body"], target, folder / build / "positive",
                           resolved, profile, seed, sanitize)
        matrix.append({"cell": f"{build}/differential", "build": build, "compiler": target.spec.cc,
                       "status": "passed" if result.accepted else "failed", "reason": result.reason,
                       "check": result.check, "seed": seed, "n_cases": result.n_cases,
                       "coverage": result.coverage})
        for cid, control in resolved["controls"].items():
            outcome = _run_cell(resolved["family"], control["path"], target, folder / build / cid,
                                resolved, profile, seed, sanitize)
            state = ("survived" if outcome.accepted else
                     "invalid" if outcome.infrastructure_error or outcome.check == "build_failed" else "rejected")
            control_cells[cid].append({"build": build, "outcome": state, "check": outcome.check,
                                       "reason": outcome.reason[:500]})
    if resolved["probe"]:
        matrix.append(probe_cell(entry, resolved, builds, folder / "probe", profile, seed))
    controls = []
    for cid, control in resolved["controls"].items():
        status, reason = _control_status(control_cells[cid], control["check"])
        controls.append({"id": cid, "kind": control["kind"], "clause": control["clause"],
                         "expected_check": control["check"], "status": status, "reason": reason,
                         "cells": control_cells[cid]})
    verdict = ("certified" if matrix and all(c["status"] == "passed" for c in matrix)
               and controls and all(c["status"] == "rejected" for c in controls) else "failed")
    if library.content_sha256(entry_id) != content_sha256 or _source_digest(library.root) != command_hash:
        raise Failure("library entry or certification sources changed during execution")
    record = workflow.record(
        "certification", "certification." + uuid.uuid4().hex,
        entry={"id": entry_id, "content_sha256": content_sha256}, dependencies=dependencies,
        command={"version": VERSION, "sources_sha256": command_hash, "kind": "library_operation_differential",
                 "profile": profile.to_record(), "seed": seed},
        host={"hostname": socket.gethostname(), "system": platform.system(), "architecture": platform.machine(),
              "compilers": {b: t.spec.cc for b, t in builds.items()}},
        matrix=matrix, negative_controls=controls, verdict=verdict, evidence_basis="simulated",
        evidence_kind="execution", created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        raw_artifacts=[str(folder)])
    (folder / "certification.json").write_text(json.dumps(record, indent=2) + "\n")
    workflow.persist(store.dir, record, create=True)
    return record


# --- contract probe cell (certification build only) -----------------------------------

def probe_cell(entry, resolved, builds, folder, profile, seed):
    """Compile the entry's runtime probes into a certification-only candidate build."""
    import random
    from swdb.extensa import probes as P
    from swdb.extensa.synthesis.certify import family_and_shape, render_two_binaries
    from swdb.extensa.synthesis.spec import TargetSpec
    from swdb.extensa.synthesis.targets.cpu_like import CpuCompileTarget
    spec = resolved["probe"]
    family = resolved["family"]
    _fam, sc = family_and_shape(family)
    drivers = folder / "drivers"
    drivers.mkdir(parents=True, exist_ok=True)
    shutil.copy(resolved["run_template"], drivers / sc.run_template)
    shutil.copy(resolved["reference_template"], drivers / sc.ref_template)
    _ref, cand = render_two_binaries(folder, family, resolved["body"], drivers_dir=drivers,
                                     reference_header=resolved["reference"],
                                     cand_template=resolved["candidate_template"])
    source = cand[0].read_text()
    line = next((i + 1 for i, text in enumerate(source.splitlines()) if spec["marker"] in text), None)
    if line is None:
        return {"cell": "probe/contract", "status": "failed", "reason": "probe marker not found in candidate TU"}
    sites = [{"line": line, "method": spec["method"], "var": spec.get("var", ""),
              "origins": spec.get("origins", {}), "predicates": spec.get("predicates")}]
    if sites[0]["predicates"] is None:
        sites[0].pop("predicates")
    plan = P.plan_for_entry(entry, sites)
    verdict = folder / "verdict.txt"
    region = re.sub(r"[^0-9A-Za-z_.-]", "_", entry["id"])
    probe = P.emit_contract_probe(plan, {entry["id"]: spec.get("binding", {})}, region_id=region,
                                  verdict_path=str(verdict), device_tu=False)
    text, report = P.splice_probes(source, probe.probes, probe.globals)
    cand[0].write_text(text)
    cc = sanitize_compiler()
    flags = (*P.probe_build_flags(), f"-I{resolved['reference'].parent}", f"-I{resolved['body'].parent}")
    target = CpuCompileTarget(TargetSpec("probe", platform.machine(), cc, flags))
    build = target.build(cand, folder / "probe_bin")
    if not build.ok:
        record = P.contract_record_from_verdict(plan, probe, [], spliced=False,
                                                probe_fault=P.REASON_PROBE_BUILD_FAILED + ": " + build.log[-300:])
        return {**P.certification_matrix_cell(record, cell="probe/contract"), "binary": None}
    rng = random.Random(seed)
    sizes = {**dict(sc.default_sizes), **resolved["sizes"], **dict(profile.sizes)}
    for c in range(min(profile.n_cases, 4)):
        case = sc.gen_case(rng, sizes, case_idx=c, n_cases=profile.n_cases)
        case_dir = folder / f"case_{c}"
        sc.write_case(case_dir, case)
        target.run(build.binary, sc.argv(sizes, case, case_dir))
    record = P.contract_record_from_verdict(plan, probe, P.read_verdict(verdict, region),
                                            spliced=all(r[2] for r in report))
    return {**P.certification_matrix_cell(record, cell="probe/contract"), "binary": str(build.binary)}


def certify_cli(args):
    from swdb.library import Library
    from swdb.store import Store
    store = Store(Path(args.records))
    library = Library(Path(args.library), store=store)
    problems = library.validate()
    if problems:
        raise UsageError("typed library is invalid: " + str(problems[0]))
    profile = Path(args.profile)
    if not profile.is_absolute() and not profile.exists():
        profile = library.root / "profiles" / (args.profile if args.profile.endswith(".yaml")
                                                                     else args.profile + ".yaml")
    record = certify_entry(store, library, args.entry_id, profile, runs_dir=args.runs_dir,
                           seed=getattr(args, "seed", None))
    print(json.dumps({"id": record["id"], "verdict": record["verdict"], "matrix_cells": len(record["matrix"]),
                      "negative_controls": len(record["negative_controls"]),
                      "controls": {c["id"]: c["status"] for c in record["negative_controls"]}}, indent=2))
    return 0 if record["verdict"] == "certified" else 1


# --- synthesized entries (ticket 49) -----------------------------------------------------

MUTANT_CATEGORY = {"off_by_one": "index_bounds", "final_index_off_by_one": "index_bounds",
                   "gather_index_shift": "index_bounds", "off_by_one_dest": "index_bounds",
                   "reversed_iteration": "ordering", "transposed_layout": "ordering",
                   "arrays_reversed": "ordering", "stale_staging": "ordering",
                   "skip_last_chain_level": "dropped_operand", "dropped_last_record": "dropped_operand",
                   "partial_stream": "dropped_operand", "zero_first": "dropped_operand",
                   "assign_not_accumulate": "double_claim", "subtract_not_add": "double_claim",
                   "padding_overrun": "capacity", "inverse_direction": "ordering",
                   "skip_last_vertex": "dropped_operand"}
SYNTH_REFERENCE_SYMBOL = {"gather": "gather", "pack": "pack_gather", "regroup": "interleave",
                          "bin_drain": "bin_drain", "gather_stream": "gather_stream", "relabel": "relabel_apply"}


def install_synthesized(library_root, family, header_text, *, origin, summary=""):
    """Write a synthesized backend as a library-operation entry plus its profile.

    Returns (entry_id, folder, profile path). The caller certifies it and removes the
    files again if certification fails: an entry enters the experimental tier only
    certified."""
    import hashlib
    from swdb import yamlio
    from swdb.extensa.synthesis.families import FAMILIES
    from swdb.extensa.synthesis.mutants import mutant_text, variants_for
    from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES
    root = Path(library_root)
    short = hashlib.sha256(header_text.encode()).hexdigest()[:12]
    entry_id = f"operation.synth_{family}_{short}"
    folder = root / "library_operations" / "synthesized" / entry_id
    if folder.exists():
        raise Failure(f"synthesized entry {entry_id} already exists")
    folder.mkdir(parents=True)

    def rel(p):
        return p.relative_to(root).as_posix()

    def pin(p, **extra):
        return {"root": "library", "path": rel(p), "sha256": artifacts.file_hash(p), **extra}

    body = folder / "backend.hh"
    body.write_text(header_text)
    sc = SHAPE_CLASSES[FAMILIES[family].shape_class]
    drivers = root / "library_operations" / "drivers"
    reference = root / "library_operations" / "reference" / "movement_reference.hh"
    clauses, controls = [], []
    for variant in variants_for(family):
        mutation = folder / f"control.{variant}.hh"
        mutation.write_text(mutant_text(family, variant))
        category = MUTANT_CATEGORY.get(variant, "dropped_operand")
        clauses.append({"id": f"equivalence.{variant}", "role": "postcondition",
                        "statement": f"The output equals the reference semantics bitwise; the {variant} defect fails.",
                        "natural_language_only": "bitwise equality with the reference is checked by the differential test",
                        "discharge_mode": "differential_test",
                        "negative_control": {"id": variant, "kind": category, "check": "differential_mismatch",
                                             "mutation": pin(mutation)}})
        controls.append({"id": variant, "category": category, "expected_check": "differential_mismatch"})
    entry = {"id": entry_id, "kind": "library_operation",
             "provenance": {"origin": origin,
                            "license": "Apache-2.0 WITH LLVM-exception (ported harness; Q66 assumption)"},
             "signature": sc.hook, "intent": summary or f"Synthesized {family} backend (SynthBackend hook).",
             "location": {"root": "library", "path": rel(body), "symbol": "SynthBackend"},
             "code_sha256": artifacts.file_hash(body),
             "reference_semantics": pin(reference, symbol=SYNTH_REFERENCE_SYMBOL[family]),
             "uses_intrinsics": [], "uses_library_operations": [],
             "differential_test": {**pin(drivers / sc.run_template), "family": family,
                                   "files": {"reference_template": pin(drivers / sc.ref_template),
                                             "candidate_template": pin(drivers / sc.cand_template)},
                                   "input_set": {"generator": sc.name, "seeds": "post_hoc",
                                                 "sizes": dict(sc.default_sizes)}},
             "clauses": clauses}
    (folder / "entry.yaml").write_text(yamlio.dumps(entry))
    profiles = root / "profiles"
    profiles.mkdir(exist_ok=True)
    profile_file = profiles / f"{entry_id}.yaml"
    profile_file.write_text(yamlio.dumps({
        "format": "swdb.certification-profile.v1", "id": f"profile.{entry_id}", "entry": entry_id,
        "date": datetime.datetime.now().date().isoformat(),
        "matrix": {"builds": ["sanitized", "openmp"], "threads": 4, "n_cases": 6, "sizes": dict(sc.default_sizes)},
        "controls": controls, "required_categories": sorted({c["category"] for c in controls})}))
    return entry_id, folder, profile_file


def synthesize_cli(args):
    """`swdb synthesize FAMILY`: one charged synthesis-role call, then `swdb certify`.

    The entry stays in the library (experimental tier) only if certification passes."""
    import dataclasses
    from swdb import provider_roles, rewrite
    from swdb.library import Library
    from swdb.store import Store
    from swdb.extensa.synthesis.families import FAMILIES, contract_sha256, resolve_contract
    from swdb.extensa.synthesis.spec import load_doc
    from swdb.extensa.synthesis.synthesize import run_synthesis
    from swdb.extensa.synthesis.targets.cpu_like import CpuCompileTarget
    if args.family not in FAMILIES:
        raise UsageError(f"unknown synthesis family {args.family!r}")
    library_root = Path(args.library)
    store = Store(Path(args.records))
    contract = resolve_contract(FAMILIES[args.family], library_root)
    spec = load_doc({"family": args.family, "goal": args.goal,
                     "target": {"name": "native-cpu", "harness": "cpu_like", "isa": platform.machine(),
                                "toolchain": {"cc": sanitize_compiler(), "flags": ["-std=c++11", "-O1"]}}})
    config = rewrite.configuration(Path(args.provider_config))
    runs = artifacts.external_directory(args.runs_dir)
    session = runs / ("synthesis-" + uuid.uuid4().hex)
    calls = []

    def invoker(files, prompt):
        try:
            response, metadata = provider_roles.run("synthesis", files, prompt, config, session / "provider")
        finally:
            receipt = session / "provider" / "provider.json"
            meta = json.loads(receipt.read_text()) if receipt.is_file() else {}
            calls.append({"role": "synthesis", "classification": meta.get("classification"),
                          "model": meta.get("model"), "effort": meta.get("effort")})
        return response

    reference_dir = library_root / "library_operations" / "reference"
    target = CpuCompileTarget(dataclasses.replace(spec.target, flags=(*spec.target.flags, f"-I{reference_dir}")))
    outcome = run_synthesis(spec, contract, target, session / "synthesis", invoker=invoker)
    result = {"family": args.family, "contract_sha256": contract_sha256(contract), "provider_calls": calls,
              "synthesis": {"ok": outcome.ok, "reason": outcome.reason[:1000]}, "entry": None, "certification": None}
    if not outcome.ok:
        result["state"] = "rejected"
        return result
    origin = {"kind": "extensa_synthesis", "campaign": args.campaign,
              "harness": {"repository": "MaizeHPC/MemAcc", "commit": "af3d6d7f7a69a72facdc3b95b42e78c952f44a76",
                          "path": "AgenticRefiner/refiner/synthesis/"},
              "contract_sha256": contract_sha256(contract)}
    entry_id, folder, profile_file = install_synthesized(library_root, args.family, outcome.header_text,
                                                         origin=origin, summary=outcome.entry.get("summary", ""))
    try:
        library = Library(library_root, store=store)
        problems = library.validate()
        if problems:
            raise Failure("synthesized entry is invalid: " + str(problems[0]))
        record = certify_entry(store, library, entry_id, profile_file, runs_dir=runs)
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        profile_file.unlink(missing_ok=True)
        raise
    result["certification"] = {"id": record["id"], "verdict": record["verdict"],
                               "controls": {c["id"]: c["status"] for c in record["negative_controls"]}}
    if record["verdict"] != "certified":
        shutil.rmtree(folder, ignore_errors=True)
        profile_file.unlink(missing_ok=True)
        result["state"] = "rejected"
        return result
    state = Library(library_root, store=Store(Path(args.records))).state(entry_id)
    result.update(state="installed", entry=entry_id, tier=state["tier"], status=state["status"])
    return result


def register_cli(commands, paths_module):
    sub = commands.add_parser("synthesize", help="synthesize one experimental library operation and certify it",
                              description="one synthesis-role call through the provider launcher; the entry "
                                          "enters the experimental tier only if swdb certify passes its profile")
    sub.add_argument("family")
    sub.add_argument("--provider-config", type=Path, required=True)
    sub.add_argument("--goal", default="A correct, simple C++11 backend for this hook.")
    sub.add_argument("--campaign", default=None, help="the Extensa campaign this synthesis belongs to")
    sub.add_argument("--runs-dir", type=Path, required=True)
    sub.add_argument("--records", type=Path, default=paths_module.RECORDS)
    sub.add_argument("--library", type=Path, default=paths_module.HOME / "library")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(extensa_handler=synthesize_cli)
