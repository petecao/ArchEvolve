"""Check mode: the runtime form of a contract's formal halves, run on a candidate's C++ (`swdb runtime-check`).

Created: 2026-10-14 ET (Probata proof of concept ticket 23). Design: formal-verification map spec ("Formal-half
language and the C++ subset": the runtime-check form); map 16 items 1 and 8 (E-ACSL is only a cross-check: it drops
`\\old` under quantifiers). Format: docs/reference/format-v0.4-stubs-check-mode.md.

- The runtime form (`swdb.cbmc_translator.runtime_form`) wraps the unit: it checks each `requires` (the caller's
  duty), snapshots each `\\old` value on entry (under a bounded quantifier, the whole range, so a frame clause such
  as `\\forall k; 0 <= k < n ==> b[k] == \\old(a[k])` gets a runtime form), calls the unit, and checks each
  `ensures` with bounded quantifiers as loops. `==` and `!=` on reals compare within the kernel's certify tolerance
  (the kernel record's `correctness_check.tolerance.value`; `--tolerance` overrides; none means exact). A
  quantifier bound that reads the post-state is refused (its range could not be snapshotted on entry).
- `swdb runtime-check` runs that form on the candidate's own C++ (cut from its tree; no stubs, the real callees) for
  every input of the bounded domain that meets the `requires` (the CBMC adapter's differential domain), natively,
  and reports each failing property with its input. It writes no record: it is a check, not a proof. Ticket 31's
  certification gate 4 calls `run()` on each certify run of the reference instance.
- Assumption (not decided in the map): check mode is exposed as its own command, not as an entry of `swdb prove`,
  because a passing runtime check proves nothing. An `assigns` clause has no runtime form (it names locations).
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path

from swdb import c_lowering, cbmc_adapter, cbmc_translator as tr, cxx_cut
from swdb.cli import Failure, UsageError


def register_cli(commands):
    sub = commands.add_parser(
        "runtime-check", help="check mode: run a contract's formal halves as runtime checks on a candidate's C++",
        description="Run the runtime form of a contract's per-candidate formal halves (requires, \\old snapshots on "
                    "entry, ensures with bounded quantifiers as loops, reals within the kernel's certify tolerance) on "
                    "the candidate's C++ for every input of the bounded domain. Writes no record.")
    sub.add_argument("--records", type=Path, default=None)
    sub.add_argument("--candidate", required=True)
    sub.add_argument("--function", required=True)
    sub.add_argument("--contract", required=True)
    sub.add_argument("--bounds", required=True, help='JSON object: {"threads": 1, "<integer parameter>": <size>, ...}')
    sub.add_argument("--define", action="append", default=[], help="a build constant NAME or NAME=VALUE (repeatable)")
    sub.add_argument("--tolerance", type=float, help="absolute tolerance for reals (default: the kernel's certify "
                                                     "tolerance)")
    sub.add_argument("--runs-dir", type=Path, required=True, help="runs folder outside the repo")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=_cli)


def _cli(args):
    from swdb import paths
    from swdb.cli import _require_valid
    from swdb.proof import _library, _outside_repo
    records = args.records or paths.RECORDS
    store = _require_valid(records)
    candidate = store.get(args.candidate, "candidate")
    if candidate is None:
        raise Failure(f"candidate {args.candidate!r} does not exist")
    library = _library(store)
    entry = library.get(args.contract) if library is not None else None
    if entry is None:
        raise Failure(f"contract {args.contract!r} is not in the library beside {records}")
    try:
        bounds = json.loads(args.bounds)
    except ValueError:
        bounds = None
    if not isinstance(bounds, dict):
        raise UsageError("--bounds is a JSON object")
    tolerance, source = _tolerance(store, entry, args.tolerance)
    runs = _outside_repo(args.runs_dir)
    from swdb.wp_adapter import _unit_source
    tree = Path((candidate.get("artifact") or {}).get("path"))
    try:
        return run(library, args.contract, _unit_source(tree, args.function), args.function, bounds, args.define,
                   tolerance, source, runs / f"runtime-check.{args.candidate}.{args.function}")
    except tr.Untranslatable as exc:
        raise Failure(f"check mode refuses {args.contract}: {exc}") from None
    except c_lowering.LoweringError as exc:
        raise Failure(f"check mode cannot read {args.function}: {exc}") from None


def _tolerance(store, entry, given):
    if given is not None:
        return given, "--tolerance"
    kernel = ((entry.get("correctness_check") or {}).get("kernel"))
    record = store.get(kernel, "kernel") if isinstance(kernel, str) else None
    value = (((record or {}).get("correctness_check") or {}).get("tolerance") or {}).get("value")
    if isinstance(value, (int, float)):
        return float(value), f"kernel {kernel} correctness_check.tolerance"
    return 0.0, f"kernel {kernel}: no numeric tolerance (exact)"


def run(library, contract, source, function, bounds, defines, tolerance, tolerance_source, out):
    """Run the runtime form on every feasible input of the bounded domain; return the report."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    defines = tuple(sorted(defines or ()))
    try:
        code = cbmc_adapter.Code(c_lowering.lower(source, function, defines=defines), source, defines)
    except c_lowering.Unsupported:
        code = cxx_cut.CxxCode(source, function, defines)
    entry = library.get(contract) or {}
    rows = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
            and c.get("proof_placement") == "per_candidate"]
    if not rows:
        raise Failure(f"{contract} has no per-candidate formal half")
    clauses = tr.clauses(contract, rows)
    unit = code.interface(function)
    sizes = cbmc_adapter._sizes(bounds)
    cap = max(sizes.values()) if sizes else 0
    logic = cbmc_adapter.logic_of(library)
    form = tr.runtime_form(unit, clauses, logic=logic)
    driver, plan = tr.harness(unit, clauses, sizes=sizes, cap=cap, logic=logic, call=f"swdb_check_{function}",
                              check=True)
    text = tr.prelude() + logic.block() + code.cxx_text() + form + driver
    program = out / "runtime_check.cc"
    program.write_text(text)
    lines, sampled, domain = cbmc_adapter._domain(plan)
    inputs = out / "domain.txt"
    inputs.write_text("".join(" ".join(str(v) for v in line) + "\n" for line in lines))
    binary = out / "runtime_check"
    clang = c_lowering.locate()
    command = [clang.command[0], "-x", "c++", "-std=gnu++17", "-O0", "-fwrapv", "-w", "-DSWDB_NATIVE",
               "-DSWDB_CHECK_MODE", f"-DSWDB_TOLERANCE={tolerance!r}", *code.cxx_defines(), str(program),
               "-o", str(binary)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if done.returncode != 0:
        errors = [line for line in done.stderr.splitlines() if "error" in line]
        raise Failure(f"the runtime form does not compile: {'; '.join(errors[:3]) or done.stderr[-400:]}")
    with open(inputs) as stdin:
        ran = subprocess.run([str(binary)], stdin=stdin, capture_output=True, text=True, timeout=600)
    if ran.returncode != 0:
        raise Failure(f"the runtime check exited {ran.returncode}: {ran.stderr[-400:]}")
    (out / "runtime_check.out").write_text(ran.stdout)
    failures, feasible = [], 0
    for k, line in enumerate(ran.stdout.splitlines()):
        end = (re.findall(r" end=(\S+)", line) or ["none"])[0]
        if end == "infeasible":
            continue
        feasible += 1
        for name in re.findall(r" fail=(\S+)", line):
            failures.append({"property": name, "run": k, "input": " ".join(str(v) for v in lines[k])})
    by_property = {}
    for failure in failures:
        by_property.setdefault(failure["property"], failure)
    return {"check": "runtime_form", "contract": contract, "function": function, "translator": tr.identity()["id"],
            "verdict": "fail" if failures else "pass", "runs": len(lines), "feasible_runs": feasible,
            "sampled": sampled, "tolerance": tolerance, "tolerance_source": tolerance_source,
            "failed_properties": sorted(by_property), "first_failures": [by_property[p] for p in sorted(by_property)],
            "failures": len(failures), "program": {"path": str(program), "sha256": _sha(program)},
            "output": {"path": str(out / "runtime_check.out"), "sha256": _sha(out / "runtime_check.out")}}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
