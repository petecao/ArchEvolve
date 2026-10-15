"""Whole-function equivalence: CBMC on a product program of two C lowerings (the bounded direct route).

Created: 2026-10-14 ET (Probata proof of concept ticket 61). Yan-Ru's 13:19 ET decision made CBMC 6.11 on the C
lowering the bounded verifier, so the ticket's SAW form lost its role; the main session, under Yan-Ru's delegation,
chose CBMC on a product program (self-composition) of the two functions' C lowerings, reusing ticket 22's harness,
oracle, differential run and replay. Design: formal-verification map spec ("Proof routes" (bounded direct),
"Bounds", "Evaluation design" (the no-contract baseline)); decisions 17 item 4, 23 item 2, 24 items 1 and 3.
Format: docs/reference/format-v0.4-cbmc.md ("Whole-function equivalence").

`swdb prove --adapter cbmc --whole-function MODE` compares the candidate artifact's function with the baseline's
(the candidate's source snapshot, or `--baseline-candidate`) on the same symbolic inputs within the bounds, at one
thread, and compares every output: the return value, every element of every array parameter and every global both
versions declare. Equal: proven within bounds, threads = 1. Unequal: refuted, the counterexample naming the concrete
inputs, the first differing location and both values. Never more than proven within bounds (no alignment: 24 item
1). MODE:
- `bounded_direct`: the route for a proof unit with no unit postcondition: its contract carries
  `relational_template: {reason}`. The contract's per-candidate formal halves are checked in the same job.
- `no_contract_baseline`: the evaluation's baseline (23 item 2): no contract; the record's contract pin is not
  applicable, so the level rule reads it as a measurement and never as a level.
Both modes write `route: bounded_direct`.

The product program: the candidate's C lowering as it is, then the baseline's with every function and global
renamed (`swdb_base_*`, by the preprocessor), then one harness that draws the inputs once, gives each call its own
copy of every array, calls both, and asserts equality per output location. Loops keep their own bounds per copy:
`--unwind K` (K = the largest size bound + 1) plus `--unwindset side:<function>.<n>=K` per loop; unwinding
assertions stay on, so a copy whose loop runs longer is never proven. No alignment hints (out of scope, map 24).
"""

import hashlib
import itertools
import os
import re
import subprocess
from pathlib import Path

from swdb import c_lowering, cbmc_product as product, cbmc_translator as tr, rss_watchdog, yamlio
from swdb.cbmc_adapter import (DEFAULT_CAP_BYTES, DEFAULT_WALL_SECONDS, DISAGREEMENT, FROZEN, SANITIZERS, CbmcAdapter,
                               Code, _Log, _compile, _domain, _inputs, _sizes, read_outcome)
from swdb.proof import AdapterError

MODES = ("bounded_direct", "no_contract_baseline")
ROUTE = "bounded_direct"
SIDES = ("candidate", "baseline")
TYPE_DEFINITION = re.compile(r"^\s*(typedef\b|struct\s+\w+\s*\{|union\s+\w+\s*\{|enum\b)", re.M)


# --- what `swdb prove` resolves before the job ------------------------------------------------------------------

def contract(args, store, library, certified):
    """The contract of a whole-function job, or None for the no-contract baseline; the route guard."""
    from swdb.cli import Failure, UsageError
    if args.whole_function == "no_contract_baseline":
        if args.contract:
            raise UsageError("--whole-function no_contract_baseline runs with no contract: drop --contract")
        return None
    chosen = args.contract or certified()
    entry = library.get(chosen) if library is not None else None
    if entry is None:
        raise Failure(f"contract {chosen!r} is not in the library beside {args.records}")
    reason = (entry.get("relational_template") or {}).get("reason") if isinstance(entry.get("relational_template"),
                                                                                  dict) else None
    if not isinstance(reason, str) or not reason.strip():
        raise Failure(f"the bounded direct route runs only for a proof unit with no unit postcondition, and contract "
                      f"{chosen} does not say it has none (no `relational_template: {{reason}}`): prove it by route 1 "
                      "against its unit postcondition, or run the no-contract baseline (--whole-function "
                      "no_contract_baseline)")
    return chosen


def prepare(args, store, candidate, function):
    """Pin updates for a whole-function job; stashes the baseline and the bounds' origin on `args` for the adapter."""
    from swdb.cli import Failure, UsageError
    if args.baseline_candidate:
        other = store.get(args.baseline_candidate, "candidate")
        if other is None:
            raise Failure(f"baseline candidate {args.baseline_candidate!r} does not exist")
        baseline = {"kind": "candidate", "id": args.baseline_candidate, **_artifact(other)}
    else:
        snapshot = store.get(candidate.get("source_snapshot") or "", "source_snapshot")
        if snapshot is None:
            raise Failure("the candidate artifact names no source snapshot: give --baseline-candidate")
        baseline = {"kind": "source_snapshot", "id": snapshot["id"], **_artifact(snapshot)}
    baseline["function"] = function
    pins = {"baseline_function": {"id": baseline["id"], "function": function, "sha256": baseline["sha256"]}}
    origin = {"kind": "passed"}
    borrowed = getattr(args, "borrowed_bounds", None)
    if args.whole_function == "no_contract_baseline":
        if args.minimum_bounds:
            raise UsageError("the no-contract baseline has no minimum bounds (map 19 item 1): use --borrowed-bounds")
        pins["contract"] = {"not_applicable": "The no-contract baseline (evaluation baseline, map 23 item 2) "
                                              "compares against the baseline with no contract."}
        pins["minimum_bounds"] = {"not_applicable": "Without a contract there are no minimum bounds (map 19 item 1)."}
        if borrowed:
            if args.bounds is not None:
                raise UsageError("give either --bounds or --borrowed-bounds, not both")
            record = _derivation(store, borrowed)
            args.bounds = dict(record["bounds"])
            origin = {"kind": "borrowed", "record": borrowed, "contract": record["subject"]["id"]}
    else:
        if borrowed:
            raise UsageError("--borrowed-bounds is for the no-contract baseline; the bounded direct route runs at its "
                             "contract's minimum bounds (--minimum-bounds)")
        if args.minimum_bounds and args.bounds is None:
            args.bounds = dict(_derivation(store, args.minimum_bounds)["bounds"])
            origin = {"kind": "minimum_bounds", "record": args.minimum_bounds}
    args.swdb_equivalence = {"mode": args.whole_function, "baseline": baseline, "bounds_origin": origin}
    return pins


def _artifact(record):
    artifact = record.get("artifact") or {}
    return {"tree": artifact.get("path"), "sha256": artifact.get("sha256")}


def _derivation(store, rid):
    from swdb.cli import Failure
    record = store.get(rid, "proof")
    subject = (record or {}).get("subject") or {}
    if record is None or subject.get("kind") != "contract_proof_part" or subject.get("part") != "minimum_bounds_derivation":
        raise Failure(f"{rid!r} is not a minimum-bounds derivation record")
    return record


# --- the adapter ------------------------------------------------------------------------------------------------

class EquivalenceAdapter(CbmcAdapter):
    """`swdb prove --adapter cbmc --whole-function MODE`: one product-program job per call."""

    def __init__(self, library, contract, method, records=None, defines=(), spec=None, unwindset=()):
        super().__init__(library, contract, method, records=records, defines=defines)
        self.spec, self.unwindset = spec, tuple(unwindset)

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        if script is not None:
            raise AdapterError("the cbmc adapter takes no --script (one CBMC job per call)")
        return cls(library, contract, method, records=getattr(args, "records", None),
                   defines=getattr(args, "define", None) or (), spec=args.swdb_equivalence,
                   unwindset=getattr(args, "unwindset", None) or ())

    def _tools(self):
        """22's checks, plus the product-program generator: the method version must list it as a translator."""
        tools = super()._tools()
        found = product.identity()
        if found not in ((self.method.data.get("c_lowering") or {}).get("translators") or []):
            raise AdapterError(f"the CBMC product-program generator {found['id']} (sha256 {found['sha256'][:12]}...) is "
                               f"not a translator of method version {self.method.id}: whole-function equivalence needs "
                               "a method version that lists it")
        tools["identities"]["product"] = (found["id"], found["sha256"], found["id"])
        return tools

    def _verdict(self, verdict, context, failure_class=None, counterexample=None, unreplayed=None):
        """22's verdict, plus the product-program generator as a trusted-tool entry and in `tools`."""
        import dataclasses
        found = super()._verdict(verdict, context, failure_class=failure_class, counterexample=counterexample,
                                 unreplayed=unreplayed)
        ident, sha, version = context["tools"]["identities"]["product"]
        entry = {"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                 "sentence": f"The CBMC product-program generator ({version}) builds a harness that runs both "
                             "functions on the same inputs and compares every output location."}
        return dataclasses.replace(found, assumptions=[*found.assumptions, entry], tools=(*found.tools, ident))

    def run(self, job):
        from swdb.wp_adapter import _unit_source
        out = Path(job.log).parent / "cbmc"
        out.mkdir(exist_ok=True)
        log = _Log(job.log)
        baseline = self.spec["baseline"]
        log.line(f"adapter: cbmc (whole-function equivalence, {self.spec['mode']})\nunit: {job.unit.candidate} "
                 f"{job.unit.function}\nbaseline: {baseline['kind']} {baseline['id']}\ncontract: {self.contract}")
        tools = self._tools()
        sizes = _sizes(job.bounds)
        constants = [{"name": d.split("=", 1)[0], "value": d.split("=", 1)[1] if "=" in d else "1"} for d in self.defines]
        context = {"job": job, "out": out, "log": log, "reports": [], "tools": tools, "bounds": dict(job.bounds),
                   "pins": {},
                   "settings": {"tool": "cbmc", "flags": [], "translator": tools["translator"]["id"],
                                "build_constants": list(self.defines), "whole_function": self.spec["mode"],
                                "baseline": {k: baseline[k] for k in ("kind", "id", "function")},
                                "bounds_origin": self.spec["bounds_origin"],
                                "build_constants_by_build": {"candidate": constants, "baseline": constants}}}
        codes = {}
        for side, tree in (("candidate", job.unit.tree), ("baseline", baseline["tree"])):
            source = _unit_source(Path(tree), job.unit.function)
            log.line(f"{side} source: {source}")
            try:
                lowering = c_lowering.lower(source, job.unit.function, defines=self.defines)
            except c_lowering.Unsupported as exc:
                context["settings"]["outside_cpp_subset"] = f"outside the C++ subset ({side}): {exc}"
                return self._not_proven("unsupported_construct", f"{side}: {exc}", context)
            except c_lowering.ParseError as exc:
                return self._not_proven("parse_error", f"{side}: {exc}", context)
            except c_lowering.LoweringError as exc:
                raise AdapterError(f"{side}: {exc}") from None
            codes[side] = Code(lowering, source, self.defines)
        self._fault(codes, os.environ.get("SWDB_CBMC_LOWERING_FAULT"))
        cand, base = codes["candidate"], codes["baseline"]
        context["pins"] = {"c_lowering": {"id": f"{cand.lowering.function}.c", "sha256": cand.c_sha256},
                           "baseline_c_lowering": {"id": f"{base.lowering.function}.c", "sha256": base.c_sha256},
                           "naming_rules": c_lowering.naming_rules()}           # ticket 24, as 22's adapter
        for side, code in codes.items():
            if TYPE_DEFINITION.search(code.text):
                context["settings"]["untranslatable"] = f"the {side}'s C lowering defines a type"
                return self._not_proven("unsupported_construct", f"the product program cannot hold the {side}'s type "
                                        "definitions twice yet", context)
        try:
            built = self._build(job, cand, base, sizes, context)
        except tr.Untranslatable as exc:
            context["settings"]["untranslatable"] = str(exc)
            return self._not_proven("unsupported_construct", f"the CBMC translator: {exc}", context)
        problem = self._differential(job, built, context)
        if problem:
            return problem
        return self._cbmc(job, built, context)

    def _fault(self, codes, path):
        """A scripted lowering fault (tests) on every side whose C lowering holds all of its old texts."""
        if not path:
            return
        pairs = (yamlio.load(Path(path)) or {}).get("replace") or []
        hit = [side for side, code in codes.items() if all(old in code.text for old, _new in pairs)]
        if not hit:
            raise AdapterError(f"lowering fault {path}: no side's C lowering holds its texts")
        for side in hit:
            for old, new in pairs:
                codes[side].text = codes[side].text.replace(old, new, 1)

    # --- the product program --------------------------------------------------------------------------------
    def _build(self, job, cand, base, sizes, context):
        function = job.unit.function
        unit, other = cand.interface(function), base.interface(function)
        rows = []
        if self.contract is not None:
            entry = self.library.get(self.contract) or {}
            chosen = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                      and c.get("proof_placement") == "per_candidate"]
            rows = tr.clauses(self.contract, chosen)
        for name in sizes:
            if not unit.scalar(name):
                raise AdapterError(f"bound {name} is not an integer parameter of {function}")
        if any(p[2] for p in unit.parameters) and not sizes:
            raise AdapterError(f"{function} takes arrays: the bounds need a size bound on an integer parameter")
        cap = max(sizes.values()) if sizes else 0
        base_globals = {name: ctype for name, ctype, _line in base.globals}
        cand_globals = {name: ctype for name, ctype, _line in cand.globals}
        common = [(name, ctype) for name, ctype in cand_globals.items()
                  if name in base_globals and (ctype is None) == (base_globals[name] is None)]
        one_sided = [(name, ctype, side) for side, mine, theirs in (("candidate", cand_globals, base_globals),
                                                                    ("baseline", base_globals, cand_globals))
                     for name, ctype in mine.items() if name not in theirs and ctype]
        names = {name for name, _ctype in common} | {name for name, _ctype, _side in one_sided}
        harness, plan, compared = product.product_harness(unit, other, rows, sizes=sizes, cap=cap,
                                                          compared_globals=common, one_sided=one_sided)
        renames = list(base.functions) + [name for name, _ctype, _line in base.globals]
        unwind = cap + 1
        loops = [self._loop(entry) for entry in self.unwindset]
        context["settings"].update(unwind=unwind, unwindset=[f"{loop}:{k}" for loop, k in loops], array_length=cap,
                                   compared=compared, formal_halves=[c.name for c in rows],
                                   uncompared_globals=sorted((set(cand_globals) | set(base_globals)) - names))
        return {"harness": harness, "plan": plan, "unwind": unwind, "loops": loops, "compared": compared,
                "c": tr.prelude() + cand.c_text() + product.renamed(base.c_text(), renames) + harness,
                "cxx": tr.prelude() + cand.cxx_text() + product.renamed(base.cxx_text(), renames) + harness,
                "codes": (cand, base)}

    @staticmethod
    def _loop(text):
        """`candidate:<function>.<n>=K` or `baseline:...` to CBMC's (loop ID in the product program, K)."""
        match = re.fullmatch(r"(candidate|baseline):([A-Za-z_]\w*\.\d+)=(\d+)", text)
        if not match or int(match.group(3)) < 1:
            raise AdapterError(f"--unwindset {text!r}: give side:<function>.<loop number>=K (side candidate or "
                               "baseline, K >= 1; loop numbers from `cbmc --show-loops`)")
        loop = match.group(2) if match.group(1) == "candidate" else product.BASELINE_PREFIX + match.group(2)
        return loop, int(match.group(3))

    # --- the differential run (both sides' C lowering against their C++) -------------------------------------
    def _differential(self, job, built, context):
        out, log, scratch = context["out"], context["log"], Path(job.scratch)
        lines, sampled, domain = _domain(built["plan"])
        inputs = scratch / "domain.txt"
        inputs.write_text("".join(" ".join(str(v) for v in line) + "\n" for line in lines))
        paths_ = {"c": out / "differential_c.c", "cxx": out / "differential_cxx.cc"}
        paths_["c"].write_text(built["c"])
        paths_["cxx"].write_text(built["cxx"])
        context["reports"] += [("differential_c", paths_["c"]), ("differential_cxx", paths_["cxx"])]
        cand = built["codes"][0]
        outputs = {}
        for side in ("c", "cxx"):
            binary = scratch / f"differential_{side}"
            problem = _compile(context["tools"]["clang"], side, paths_[side], binary,
                               ["-DSWDB_NATIVE", "-DSWDB_DIFFERENTIAL", "-O0", "-fwrapv", "-w",
                                *(cand.cxx_defines() if side == "cxx" else ())])
            if problem:
                return self._not_proven("parse_error", f"the {side} side of the differential run does not compile: "
                                        f"{problem}", context)
            with open(inputs) as stdin:
                done = subprocess.run([binary], stdin=stdin, capture_output=True, text=True, timeout=600)
            if done.returncode != 0:
                return self._not_proven("tool_crash", f"the {side} side of the differential run exited "
                                        f"{done.returncode}: {done.stderr[-400:]}", context)
            outputs[side] = done.stdout
            path = out / f"differential_{side}.out"
            path.write_text(done.stdout)
            context["reports"].append((f"differential_{side}_output", path))
        if outputs["c"] != outputs["cxx"]:
            c_lines, x_lines = outputs["c"].splitlines(), outputs["cxx"].splitlines()
            first = next(k for k, (a, b) in enumerate(itertools.zip_longest(c_lines, x_lines)) if a != b)
            c_line = c_lines[first] if first < len(c_lines) else ""
            x_line = x_lines[first] if first < len(x_lines) else ""
            sides = sorted({"baseline" if t.startswith("base=") else "candidate" if t.startswith("cand=") else "both"
                            for t, u in itertools.zip_longest(c_line.split(), x_line.split(), fillvalue="")
                            if t != u})
            message = (f"{DISAGREEMENT}: the C lowering and the C++ of {job.unit.function} disagree (side: "
                       f"{', '.join(sides)}) on input {' '.join(map(str, lines[first])) if first < len(lines) else '?'}"
                       f": C lowering `{c_line}`, C++ `{x_line}`. The batch stops; no verdict is recorded (root-cause "
                       "it as a C lowering tool defect and add the case to the regression corpus)")
            log.line(message)
            self._handler(DISAGREEMENT, message, context)
            raise AdapterError(message + f". Reproduction: {out}")
        context["settings"]["agreement"] = {
            "runs": len(lines), "sampled": sampled, "domain": domain, "verdict": "agree", "sides": list(SIDES),
            "c_output_sha256": hashlib.sha256(outputs["c"].encode()).hexdigest(),
            "cxx_output_sha256": hashlib.sha256(outputs["cxx"].encode()).hexdigest()}
        log.line(f"differential: {len(lines)} runs, C lowering and C++ agree on both sides")
        return None

    # --- CBMC and the replay ------------------------------------------------------------------------------------
    def _cbmc(self, job, built, context):
        tools, log, out, scratch = context["tools"], context["log"], context["out"], Path(job.scratch)
        job_c = out / "job.c"
        job_c.write_text(built["c"])
        (scratch / "job.c").write_text(built["c"])
        context["reports"].append(("cbmc_input", job_c))
        flags = ["-DSWDB_CBMC", "--unwind", str(built["unwind"])]
        if built["loops"]:
            flags += ["--unwindset", ",".join(f"{loop}:{k}" for loop, k in built["loops"])]
        flags += [*FROZEN, *tools["flags"]]
        command = [*tools["command"], "job.c", *flags, "--json-ui"]
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
        wall = job.budget_seconds or DEFAULT_WALL_SECONDS
        cbmc_log = out / "cbmc.json"
        log.line(f"command: {' '.join(map(str, command))}\ncwd: scratch\nrss cap bytes: {cap}\nwall budget seconds: {wall}")
        context["settings"].update(flags=flags, rss_cap_bytes=cap, wall_budget_seconds=wall)
        result = rss_watchdog.run(command, log=cbmc_log, cap_bytes=cap, timeout=wall, cwd=scratch,
                                  env={**os.environ, "TMPDIR": str(scratch)})
        context["reports"].append(("cbmc_output", cbmc_log))
        context["peak"] = result.peak_rss_bytes
        log.line(f"cbmc exit {result.exit_code}, wall {result.wall_seconds:.2f} s, peak rss {result.peak_rss_bytes}")
        outcome = read_outcome(result, cbmc_log.read_text(errors="replace"))
        context["goals"], context["unproven"] = outcome["goals"], outcome["unproven"]
        log.line(f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})")
        if outcome["verdict"] == "proven":
            return self._verdict("proven", context)
        if outcome["verdict"] == "failed":
            return self._replay(job, built, outcome, context)
        return self._not_proven(outcome["failure_class"], outcome["why"], context)

    def _replay(self, job, built, outcome, context):
        """Replay each failure's trace on the product of the two C++ cuts, sanitizers on; equality failures first."""
        out, scratch = context["out"], Path(job.scratch)
        replay_cc = out / "replay_cxx.cc"
        replay_cc.write_text(built["cxx"])
        context["reports"].append(("replay_cxx", replay_cc))
        binary = scratch / "replay_cxx"
        problem = _compile(context["tools"]["clang"], "cxx", replay_cc, binary,
                           ["-DSWDB_NATIVE", "-DSWDB_REPLAY", "-O0", "-g", "-w", *SANITIZERS,
                            *built["codes"][0].cxx_defines()])
        if problem:
            return self._not_proven("parse_error", f"the C++ replay does not compile: {problem}", context)
        order = {f"{product.EQUAL}{loc}": k for k, loc in enumerate(built["compared"])}
        failures = sorted(outcome["failures"], key=lambda f: (f["property"] not in order, order.get(f["property"], 0)))
        tries = []
        for failure in failures:
            done = subprocess.run([binary], input=" ".join(str(v) for v in failure["oracle"]) + "\n",
                                  capture_output=True, text=True, timeout=120, env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"})
            failed = re.findall(r" fail=(\S+)", done.stdout)
            sanitizer = "runtime error" in done.stderr or "AddressSanitizer" in done.stderr
            replayed = sanitizer if failure["builtin"] else failure["property"] in failed
            first = next(({"location": loc, "baseline": int(b), "candidate": int(c)}
                          for loc, b, c in re.findall(r" out (\S+) base=(-?\d+) cand=(-?\d+)", done.stdout) if b != c),
                         None)
            counterexample = {"property": failure["property"], "check": failure["check"],
                              "function": failure["function"], "inputs": _inputs(done.stdout),
                              "first_difference": first, "oracle": failure["oracle"],
                              "replay": {"form": "cxx", "replayed": replayed, "failed": failed,
                                         "sanitizer": done.stderr.strip().splitlines()[0][:300] if sanitizer else None,
                                         "end": (re.findall(r" end=(\S+)", done.stdout) or ["none"])[0]}}
            tries.append(counterexample)
            context["log"].line(f"replay of {failure['check']} ({failure['property']}): "
                                f"{'replayed' if replayed else 'did not replay'}; first difference {first}")
            if replayed:
                context["settings"]["forms"] = {"c_lowering": "refuted", "cxx": "refuted (counterexample replayed)"}
                return self._verdict("refuted", context, counterexample=counterexample)
        context["settings"]["forms"] = {"c_lowering": "refuted", "cxx": "not refuted (no counterexample replayed)"}
        return self._not_proven("spurious_counterexample", "no CBMC counterexample replays on the C++", context,
                                unreplayed=tries[0])
