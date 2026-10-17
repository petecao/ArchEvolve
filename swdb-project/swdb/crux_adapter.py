"""The crux-llvm adapters: crux-llvm 0.12 on the C++ (`crux-llvm-cxx`) and on the C lowering (`crux-llvm-c`).

Created: 2026-10-14 ET (Probata proof of concept ticket 23, bounded fallbacks). Design: formal-verification map
spec ("Verifier lineup and order": fallbacks in order, floats as reals, failure classes; "Bounds": unwinding);
map 11 items 2, 4, 6, 9; 19 item 5. Format: docs/reference/format-v0.4-stubs-check-mode.md. Reference: map 07
(crux-llvm on clang 22 bitcode: compile first, then `--no-compile`).
Updated: 2026-10-15 ET: checked original-source initializedness and fresh source-view replay on both forms.

One job (`swdb prove --adapter crux-llvm-cxx|crux-llvm-c --bounds '{"threads": 1, ...}'`):
1. The code. `crux-llvm-c`: the C lowering (`swdb.c_lowering`) plus the C-versus-C++ differential run of the CBMC
   adapter (the check on the trusted C lowering tool). `crux-llvm-cxx`: the C++ itself, cut from the source by
   clang's source ranges after the same retained closure passes source initializedness admission. An unanalyzed
   C++ cut is unsupported. Summarized callees become the CBMC translator's stubs either way. Before launch,
   source analysis, admission, summaries and the exact harness/view are independently regenerated.
2. The harness is the CBMC translator's, built with `-DSWDB_CRUX`: every oracle value is a crux symbolic value,
   CHECK/PROP/REACH are `crucible_assert` (named by the property, numbered by its line), assumes are
   `crucible_assume`. clang 22.1.8 compiles it to bitcode; crux-llvm runs it with `--no-compile`.
3. Flags: always an explicit float mode, `--floating-point=real` for a real-valued unit (floats as reals) and
   `--floating-point=ieee` otherwise; `--iteration-bound=K --recursion-bound=K` with K = the largest size bound + 1
   (as CBMC's unwind); the lineup's flags; the job's wall budget as crux's `--timeout`.
4. Reading: proven when crux disproves exactly the reachability asserts (every one, so no vacuous pass) and nothing
   else; a disproved named property is replayed on the C++ with the counterexample's values (as the CBMC adapter
   does); a loop or recursion cut at the bound is `unwinding_bound_too_small`, never proven.
5. Every outcome maps to a class of vocabulary `proof_failure_classes` and runs its handler (`<form>/handler.json`);
   an outcome with no class reports `unclassified_crux_outcome`, which stops the batch.
"""

import hashlib
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from swdb import bounded_initialization, c_lowering, cbmc_adapter, cbmc_translator as tr, rss_watchdog
from swdb.proof import AdapterError, Verdict

TOOL = "crux-llvm"
DEFAULT_HOME = Path.home() / "opt" / "verifiers" / "crux-llvm-0.12" / "crux-llvm-0.12-macos-15-ARM64"
UNCLASSIFIED = "unclassified_crux_outcome"        # not a failure class: stops the batch (11 item 9)
FROZEN = ("--no-compile", "--skip-report")
SENTENCES = dict(cbmc_adapter.SENTENCES)
SENTENCES.update({
    "c_lowering": "The source analyzer and C lowering tool ({version}) inventories the retained C++ closure and "
                  "its bounded initialized-input policy; the C form also executes that C lowering.",
    "crux": "crux-llvm {version} symbolically executes every path of the bitcode within the iteration and recursion "
            "bounds and reports every failing assertion (cut paths are reported, never dropped).",
    "solver": "The SMT solver {version} answers unsatisfiable only for unsatisfiable formulas.",
    "cxx_cut": "clang {version} parses the C++ proof unit correctly, and the cut of its functions keeps their meaning "
               "(crux-llvm reads the C++, not a C lowering).",
})

_FOUND = {}


def locate():
    """(command tuple, version, includes folder, missing) of crux-llvm: SWDB_CRUX (a command line; `none` =
    missing), else the Mac install of ticket 03, else PATH."""
    key = os.environ.get("SWDB_CRUX", "")
    if key in _FOUND:
        return _FOUND[key]
    includes = Path(os.environ.get("SWDB_CRUX_INCLUDES") or DEFAULT_HOME / "c-src" / "includes")
    if key == "none":
        found = ((), "", includes, "crux-llvm disabled by SWDB_CRUX=none")
    else:
        if key:
            command = tuple(shlex.split(key))
        elif (DEFAULT_HOME / "bin" / "crux-llvm").exists():
            command = (str(DEFAULT_HOME / "bin" / "crux-llvm"),)
        elif shutil.which("crux-llvm"):
            command = (shutil.which("crux-llvm"),)
            includes = Path(os.environ.get("SWDB_CRUX_INCLUDES") or
                            Path(shutil.which("crux-llvm")).resolve().parent.parent / "c-src" / "includes")
        else:
            command = ()
        found = ((), "", includes, "crux-llvm not found (SWDB_CRUX, ~/opt/verifiers or PATH)")
        if command:
            try:
                done = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=60)
                match = re.search(r"crux-llvm\s+(?:version:?\s*)?v?(\d+\.\d+(?:\.\d+)?)", done.stdout + done.stderr,
                                  re.I)
                found = (command, match.group(1), includes, "") if match else \
                    ((), "", includes, "crux-llvm did not report a version")
            except (OSError, subprocess.SubprocessError) as exc:
                found = ((), "", includes, f"crux-llvm did not start: {exc}")
        if not found[3] and not (includes / "crucible.h").exists():
            found = ((), "", includes, f"crux-llvm's crucible.h is not in {includes} (SWDB_CRUX_INCLUDES)")
    _FOUND[key] = found
    return found


def _z3():
    path = shutil.which("z3")
    if not path:
        return "unknown", "0" * 64
    done = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=60)
    match = re.search(r"(\d+\.\d+\.\d+)", done.stdout)
    return (match.group(1) if match else "unknown"), hashlib.sha256(Path(path).resolve().read_bytes()).hexdigest()


class CruxAdapter:
    """`swdb prove --adapter crux-llvm-cxx|crux-llvm-c`: one bounded job per call (records via swdb.proof)."""
    name = None
    form = None
    real = True

    def __init__(self, library, contract, method, records=None, defines=()):
        self.library, self.contract, self.method = library, contract, method
        self.records = Path(records) if records else None
        self.defines = tuple(sorted(defines))

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        if script is not None:
            raise AdapterError(f"the {cls.name} adapter takes no --script")
        return cls(library, contract, method, records=getattr(args, "records", None),
                   defines=getattr(args, "define", None) or ())

    # the CBMC adapter's summary lookup, differential run, replay and handler work unchanged on this adapter
    _summary = cbmc_adapter.CbmcAdapter._summary
    _differential = cbmc_adapter.CbmcAdapter._differential
    _replay = cbmc_adapter.CbmcAdapter._replay
    _handler = cbmc_adapter.CbmcAdapter._handler
    _knobs = cbmc_adapter.CbmcAdapter._knobs

    def run(self, job):
        out = Path(job.log).parent / self.name
        out.mkdir(exist_ok=True)
        log = cbmc_adapter._Log(job.log)
        entry = self.library.get(self.contract) or {}
        summary_job = job.unit.candidate is None
        log.line(f"adapter: {self.name}\nunit: {job.unit.candidate or 'library summary ' + self.contract} "
                 f"{job.unit.function}\ncontract: {self.contract}")
        tools = self._tools()
        sizes = cbmc_adapter._sizes(job.bounds)
        context = {"job": job, "out": out, "log": log, "reports": [], "tools": tools, "bounds": dict(job.bounds),
                   "pins": {}, "settings": {"tool": TOOL, "form": self.form, "flags": [],
                                            "translator": tools["translator"]["id"],
                                            "build_constants": list(self.defines), "verifier_launched": False}}
        if summary_job:
            source = self.library.resolve((entry.get("proof_unit") or {}).get("source"))
        else:
            from swdb.wp_adapter import _unit_source
            source = _unit_source(Path(job.unit.tree), job.unit.function)
        log.line(f"source: {source.name}")
        try:
            code = self._code(source, job.unit.function, context)
        except c_lowering.Unsupported as exc:
            context["settings"]["outside_cpp_subset"] = f"outside the C++ subset: {exc}"
            return self._not_proven("unsupported_construct", str(exc), context)
        except c_lowering.ParseError as exc:
            return self._not_proven("parse_error", str(exc), context)
        except c_lowering.LoweringError as exc:
            raise AdapterError(str(exc)) from None
        context['lowering'] = code.lowering
        context['pins']['c_lowering'] = {'id': f'{code.lowering.function}.c', 'sha256': code.c_sha256}
        from swdb import stdlib_source_admission
        provenance_problem = stdlib_source_admission.bind(context, code.lowering, source, defines=self.defines)
        if provenance_problem:
            return self._not_proven('unsupported_construct', provenance_problem, context)
        admission = bounded_initialization.check(code.lowering, max(sizes.values(), default=0), library=self.library)
        context['settings']['bounded_initialization'] = admission
        if admission['verdict'] != 'passed':
            return self._not_proven('unsupported_construct', admission['reason'], context)
        from swdb import summary_bindings
        try:
            built = self._build(job, entry, code, sizes, summary_job, context)
        except summary_bindings.Refused as exc:
            return self._not_proven('unsupported_construct', str(exc), context)
        except c_lowering.Unsupported as exc:            # the cut's interface (a reference type, a class)
            context["settings"]["outside_cpp_subset"] = f"outside the C++ subset: {exc}"
            return self._not_proven("unsupported_construct", str(exc), context)
        except tr.Untranslatable as exc:
            context["settings"]["untranslatable"] = str(exc)
            return self._not_proven("unsupported_construct", f"the CBMC translator: {exc}", context)
        if built['plan'].array_domains:
            context['settings'].update(array_domains=built['plan'].array_domains, verifier_launched=False)
            return self._not_proven('unsupported_construct',
                                    'array_domains is planner-only: source-origin, operation and call alignment '
                                    'are not certified by nonnull bounded buffers', context)
        context['source_admission_runtime'] = {'source': source, 'code': code, 'built': built,
                                                'summary_job': summary_job}
        try:
            self.check_source_admission(job, context)
        except (ValueError, c_lowering.LoweringError) as exc:
            return self._not_proven('unsupported_construct', str(exc), context)
        if self.form == "c":
            problem = self._differential(job, code, built, context)
            if problem:
                return problem
        return self._crux(job, code, built, context)

    def check_source_admission(self, job, context, inputs=()):
        """Rebuild the source closure, input policy and exact launched view; never trust a saved certificate."""
        runtime = context.get('source_admission_runtime')
        if not runtime or not context.get('lowering'):
            raise ValueError('Crux has no generator-owned checked source plan')
        entry = self.library.get(self.contract) or {}
        if ((entry.get('proof_unit') or {}).get('array_domains')
                or self.library.content_sha256(self.contract) != job.unit.contract_sha256):
            raise ValueError('Crux source contract changed or needs unsupported array-domain admission')
        if runtime['summary_job']:
            source = self.library.resolve((entry.get('proof_unit') or {}).get('source'))
        else:
            from swdb.wp_adapter import _unit_source
            source = _unit_source(Path(job.unit.tree), job.unit.function)
        if source != runtime['source']:
            raise ValueError('Crux source location changed after planning')
        fresh = c_lowering.lower(source, job.unit.function, defines=self.defines)
        if fresh != runtime['code'].lowering or fresh != context['lowering']:
            raise ValueError('Crux original source/closure admission changed before launch')
        admission = bounded_initialization.check(fresh, max(cbmc_adapter._sizes(job.bounds).values(), default=0),
                                                 library=self.library)
        if admission.get('verdict') != 'passed' or context['settings'].get('bounded_initialization') != admission:
            raise ValueError('Crux checked source initializedness disappeared, changed or refused')
        code = cbmc_adapter.Code(fresh, source, self.defines)
        rebuilt_context = {'settings': {}, 'pins': {}}
        built = self._build(job, entry, code, cbmc_adapter._sizes(job.bounds), runtime['summary_job'], rebuilt_context)
        if (built != runtime['built'] or runtime['code'].text != code.text
                or context['pins'].get('summaries') != rebuilt_context['pins'].get('summaries')):
            raise ValueError('Crux source view, harness or imported summary changed before launch')
        view = code.c_text(built['stubs']) if self.form == 'c' else code.cxx_text(built['stubs'])
        text = tr.prelude() + built['logic'] + view + built['harness']
        checked = {'check': bounded_initialization.identity(), 'source_sha256': fresh.source_sha256,
                   'lowering_sha256': hashlib.sha256(fresh.text.encode()).hexdigest(),
                   'input_sha256': hashlib.sha256(text.encode()).hexdigest(),
                   'functions': list(code.functions), 'defines': list(self.defines), 'form': self.form,
                   'scope': 'checked retained source closure; no unanalyzed C++ cut or implicit array origins'}
        previous = context['settings'].get('source_admission')
        if previous is not None and previous != checked:
            raise ValueError('Crux checked source report changed before launch')
        if inputs and (len(inputs) != 1 or Path(inputs[0][0]).read_text() != text):
            raise ValueError('Crux launched source differs from fresh checked source view')
        context['settings']['source_admission'] = checked
        return checked

    def _code(self, source, function, context):
        """Both forms require a retained source closure; the C++ form executes its original-source cut."""
        if self.form == "c":
            lowering = c_lowering.lower(source, function, defines=self.defines)
            code = cbmc_adapter.Code(lowering, source, self.defines)
            code.apply_fault(os.environ.get("SWDB_CBMC_LOWERING_FAULT"))
            context["pins"]["c_lowering"] = {"id": f"{lowering.function}.c", "sha256": code.c_sha256}
            context["lowered"] = True
            return code
        try:
            lowering = c_lowering.lower(source, function, defines=self.defines)
            context["lowered"] = True
            return cbmc_adapter.Code(lowering, source, self.defines)
        except c_lowering.Unsupported as exc:
            context["settings"]["cxx_cut"] = f"no checked source initializedness for a C++ cut: {exc}"
            context["lowered"] = False
            raise c_lowering.Unsupported(context['settings']['cxx_cut']) from None

    def _tools(self):
        lineup = {}
        for row in self.method.data.get("lineup") or []:
            lineup.setdefault(row.get("tool"), row)
        command, version, includes, missing = locate()
        clang = c_lowering.locate()
        if missing:
            raise AdapterError(missing)
        if clang.missing:
            raise AdapterError(clang.missing)
        problems = []
        pinned = (lineup.get(TOOL) or {}).get("version")
        if not cbmc_adapter._version_matches(pinned, version):
            problems.append(f"{TOOL} {version} is installed but method version {self.method.id} pins {pinned}")
        if (lineup.get("clang") or {}).get("version") != clang.version:
            problems.append(f"clang {clang.version} is installed but method version {self.method.id} pins "
                            f"{(lineup.get('clang') or {}).get('version')}")
        translators = (self.method.data.get("c_lowering") or {}).get("translators") or []
        ident = c_lowering.identity()
        names = [("CBMC translator", tr.identity()), ("source analyzer/C lowering tool", ident["c_lowering"])]
        for name, found in names:
            if found not in translators:
                problems.append(f"the {name} {found['id']} (sha256 {found['sha256'][:12]}...) is not a translator of "
                                f"method version {self.method.id}")
        if problems:
            raise AdapterError("; ".join(problems))
        flags = [str(f) for f in (lineup.get(TOOL) or {}).get("flags") or [] if f not in FROZEN]
        solver = next((f.split("=", 1)[1] for f in flags if f.startswith("--solver=")), "z3")
        z3_version, z3_sha = _z3() if solver == "z3" else ("unknown", "0" * 64)
        crux_sha = cbmc_adapter._sha256(cbmc_adapter._binary(command))
        return {"command": command, "version": version, "includes": includes, "flags": flags, "solver": solver,
                "clang": clang, "translator": tr.identity(),
                "identities": {"c_lowering": (ident["c_lowering"]["id"], ident["c_lowering"]["sha256"],
                                              c_lowering.TOOL_VERSION),
                               "clang": (f"clang-{clang.version}", ident["clang"]["sha256"], clang.version),
                               "translator": (tr.identity()["id"], tr.identity()["sha256"], tr.identity()["id"]),
                               "crux": (f"crux-llvm-{version}", crux_sha, version),
                               "solver": (f"{solver}-{z3_version}", z3_sha, f"{solver} {z3_version}")}}

    def _build(self, job, entry, code, sizes, summary_job, context):
        unit = code.interface(job.unit.function)
        rows = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")]
        placement = {"once": "self"} if summary_job else "per_candidate"
        chosen = [c for c in rows if c.get("proof_placement") == placement]
        knobs, symbolic = self._knobs(entry, code, rows, chosen) if hasattr(code, "uses") else ([], [])
        if not chosen:
            raise AdapterError(f"{self.contract} has no {'once: self' if summary_job else 'per-candidate'} formal "
                               "half to check")
        clauses = tr.clauses(self.contract, chosen)
        for name in sizes:
            if not unit.scalar(name):
                raise AdapterError(f"bound {name} is not an integer parameter of {unit.function}")
        cap = max(sizes.values()) if sizes else 0
        if [p for p in unit.parameters if p[2]] and not sizes:
            raise AdapterError(f"{unit.function} takes arrays: the bounds need a size bound on an integer parameter")
        logic = cbmc_adapter.logic_of(self.library)
        setup, state = (), ()
        if getattr(code, "model", None) is not None:    # ticket 27: ghost state g0, then havoc the tile elements
            from swdb import proof_semantics
            setup = ("swdb_dx_init();",)
            state = proof_semantics.state_draws(self.library, code.model.entry, self.defines)
        harness, plan = tr.harness(unit, clauses, sizes=sizes, cap=cap, knobs=knobs, logic=logic, setup=setup,
                                   state=state, array_domains=(entry.get('proof_unit') or {}).get('array_domains'))
        drop = cbmc_adapter.stub_fault()
        stubs, summaries = {}, []
        for callee in code.functions:
            if callee == job.unit.function:
                continue
            from swdb import summary_bindings
            found = self._summary(callee, accept=lambda eid, rid: summary_bindings.check(
                self, code.source, job.unit.function, callee, eid, rid, caller_bounds=job.bounds))
            if found is None:
                continue
            entry_id, data, record_id = found
            from swdb import summary_bindings
            summary_bindings.bind(self, context, code.source, job.unit.function, callee, entry_id, record_id,
                                  caller_bounds=job.bounds)
            sha = self.library.content_sha256(entry_id)
            rows_s = [c for c in data.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                      and c.get("proof_placement") == {"once": "self"}]
            clauses_s = tr.clauses(entry_id, rows_s)
            stubs[callee] = tr.stub(code.interface(callee), code.prototypes[callee], clauses_s, entry_id, sha,
                                    logic=logic, drop=drop,
                                    array_domains=(data.get('proof_unit') or {}).get('array_domains'))
            summaries.append({"id": entry_id, "sha256": sha, "proof_record": record_id,
                              "assumes": tr.stub_assumes(clauses_s, drop)})
        real = tr.real_valued(unit, clauses)
        unwind = cap + 1
        context["settings"].update(unwind=unwind, array_length=cap, symbolic_knobs=symbolic, real_valued=real,
                                   summaries=[s["id"] for s in summaries])
        if summaries:
            context["pins"]["summaries"] = summaries
        return {"harness": harness, "plan": plan, "stubs": stubs, "unwind": unwind, "sizes": sizes,
                "logic": logic.block(), "real": real}

    # --- crux-llvm ---------------------------------------------------------------------------------------
    def _crux(self, job, code, built, context):
        tools, log, out, scratch = context["tools"], context["log"], context["out"], Path(job.scratch) / self.name
        scratch.mkdir(exist_ok=True)
        if self.form == "c":
            text, suffix, side = tr.prelude() + built["logic"] + code.c_text(built["stubs"]) + built["harness"], "c", "c"
        else:
            text, suffix, side = (tr.prelude() + built["logic"] + code.cxx_text(built["stubs"]) + built["harness"],
                                  "cc", "cxx")
        source = out / f"job.{suffix}"
        source.write_text(text)
        context["reports"].append(("crux_input", source))
        bitcode = scratch / "job.bc"
        compiler = tools["clang"].command[0]
        if side == "c":
            compiler = compiler.replace("clang++", "clang")
            std = ["-x", "c", "-std=gnu11"]
        else:
            std = ["-x", "c++", "-std=gnu++17"]
        compile_cmd = [compiler, *std, "-c", "-emit-llvm", "-g", "-O0", "-w", "-DSWDB_CRUX",
                       f"-I{tools['includes']}", *(code.cxx_defines() if side == "cxx" else ()), str(source),
                       "-o", str(bitcode)]
        done = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=300)
        if done.returncode != 0:
            errors = [line for line in done.stderr.splitlines() if "error" in line]
            return self._not_proven("parse_error", "clang could not compile the crux-llvm job: " +
                                    ("; ".join(errors[:3]) or done.stderr[-400:]), context)
        float_mode = "real" if built["real"] else "ieee"
        unwind, iterations, recursion = built["unwind"], *iteration_bounds(built)
        wall = job.budget_seconds or cbmc_adapter.DEFAULT_WALL_SECONDS
        flags = [*FROZEN, f"--solver={tools['solver']}", f"--floating-point={float_mode}",
                 f"--iteration-bound={iterations}", f"--recursion-bound={recursion}", f"--timeout={int(max(wall, 1))}",
                 *[f for f in tools["flags"] if not f.startswith("--solver=")]]
        report_dir = scratch / "crux-out"
        command = [*tools["command"], *flags, f"--output-directory={report_dir}", str(bitcode.resolve())]
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or cbmc_adapter.DEFAULT_CAP_BYTES)
        crux_log = out / "crux.log"
        log.line(f"command: {shlex.join(map(str, command))}\nrss cap bytes: {cap}\nwall budget seconds: {wall}")
        context["settings"].update(flags=flags, float_mode=float_mode, rss_cap_bytes=cap, wall_budget_seconds=wall,
                                   iteration_bound={"value": iterations, "unwind": unwind, "rule": ITERATION_RULE})
        from swdb import proof_setup
        proof_setup.check_generated(job, self, context, [(source, text)], flags,
                                    command=command, scratch=scratch, lowering=getattr(code, "lowering", None))
        context['settings']['verifier_launched'] = True
        result = rss_watchdog.run(command, log=crux_log, cap_bytes=cap, timeout=wall + 5, cwd=scratch,
                                  env={**os.environ, "TMPDIR": str(scratch)})
        context["reports"].append(("crux_output", crux_log))
        context["peak"] = result.peak_rss_bytes
        log.line(f"crux-llvm exit {result.exit_code}, wall {result.wall_seconds:.2f} s, peak rss "
                 f"{result.peak_rss_bytes}, out of memory {result.out_of_memory}, timed out {result.timed_out}")
        required = [tr.REACH_END] + [f"{tr.REACH_SUMMARY}{callee}" for callee in built["stubs"]]
        outcome = read_outcome(result, crux_log.read_text(errors="replace"), report_dir, built["plan"], required,
                               wall)
        context["goals"], context["unproven"] = outcome["goals"], outcome["unproven"]
        log.line(f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})")
        if outcome["verdict"] == "proven":
            context["settings"]["forms"] = {side: "proven"}
            return self._verdict("proven", context)
        if outcome["verdict"] == "failed":
            verdict = self._replay(job, code, built, outcome, context)
            context["settings"]["forms"] = {side: "refuted" if verdict.verdict == "refuted" else "not refuted",
                                            "cxx_replay": "replayed" if verdict.verdict == "refuted" else "did not replay"}
            return verdict
        return self._not_proven(outcome["failure_class"], outcome["why"], context)

    # --- verdicts ----------------------------------------------------------------------------------------
    def _not_proven(self, failure_class, why, context, unreplayed=None):
        context.setdefault("goals", [])
        context.setdefault("unproven", [])
        self._handler(failure_class, why, context)
        return self._verdict("not_proven", context, failure_class=failure_class, unreplayed=unreplayed)

    def _verdict(self, verdict, context, failure_class=None, counterexample=None, unreplayed=None):
        identities = context["tools"]["identities"]
        assumptions, tools = [], []
        used = ["clang", "translator", "crux", "solver"]
        if context.get("lowered"):
            used.insert(0, "c_lowering")
        for tool in used:
            ident, sha, version = identities[tool]
            sentence = SENTENCES["cxx_cut" if (tool == "clang" and self.form == "cxx") else tool]
            assumptions.append({"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                                "sentence": sentence.format(version=version)})
            tools.append(ident)
        fields = {"goals": context.get("goals", []), "settings": context["settings"]}
        if verdict == "not_proven":
            fields["unproven_properties"] = context.get("unproven", [])
        pins = dict(context.get("pins") or {})
        translator = context["tools"]["translator"]
        pins["translator"] = {"id": translator["id"], "sha256": translator["sha256"]}
        return Verdict(verdict=verdict, bounds=dict(context["bounds"]), assumptions=assumptions,
                       failure_class=failure_class, counterexample=counterexample, unreplayed_counterexample=unreplayed,
                       tools=tuple(tools), peak_rss_bytes=context.get("peak"), record_fields=fields, pins=pins,
                       reports=tuple(context["reports"]))


class CruxCxxAdapter(CruxAdapter):
    name, form = "crux-llvm-cxx", "cxx"


class CruxCAdapter(CruxAdapter):
    name, form = "crux-llvm-c", "c"


ITERATION_RULE = ("crux-llvm 0.12 counts loop iterations per call frame, summed over the frame's loops (measured on the "
                  "Mac, 2026-10-14), and a call frame once against the recursion bound: the iteration bound is the "
                  "largest of K (the largest size bound + 1, as CBMC's unwind) and each generated frame's need (its "
                  "loops times K); the recursion bound is K + 1")


def iteration_bounds(built):
    """(iteration bound, recursion bound) for crux-llvm (see ITERATION_RULE)."""
    unwind = built["unwind"]
    run = built["harness"].split("#if defined(SWDB_DIFFERENTIAL)")[0]
    frames = [run] + list(built["stubs"].values())
    need = max([unwind] + [text.count("for (") * unwind for text in frames])
    return need, unwind + 1


# --- reading crux-llvm's output -------------------------------------------------------------------------------

GOAL = re.compile(r"Found counterexample for verification goal\s*\n(?:\[Crux\])?\s*(.+?):(\d+):(\d+): error: in (\S+)")
COUNTS = {key: re.compile(rf"\[Crux\]\s+{key}:\s+(\d+)") for key in ("Total", "Proved", "Disproved", "Incomplete",
                                                                     "Unknown")}


def read_outcome(result, text, report_dir, plan, required, wall):
    """{verdict: proven|failed|not_proven, failure_class, why, goals, unproven, failures} from one crux-llvm run."""
    def outcome(verdict, failure_class, why, goals=(), unproven=(), failures=()):
        return {"verdict": verdict, "failure_class": failure_class, "why": why, "goals": list(goals),
                "unproven": list(unproven), "failures": list(failures)}
    if result.out_of_memory:
        return outcome("not_proven", "out_of_memory", "the RSS watchdog killed the job above its cap")
    if result.timed_out or result.wall_seconds >= wall or re.search(r"[Tt]imed? ?out|Timeout", text):
        return outcome("not_proven", "timeout", "the job ran out of its wall budget")
    counts = {key: int(m.group(1)) for key, rx in COUNTS.items() for m in [rx.search(text)] if m}
    if "Total" not in counts:
        if "Simulating function" not in text and re.search(
                r"Invalid magic number|llvm-bitstream|could not parse|parse error|failed to parse|Failed to load", text,
                re.I):
            return outcome("not_proven", "parse_error", _tail(text))
        if re.search(r"unsupported|not supported|unimplemented|Unknown intrinsic|unknown instruction", text, re.I):
            return outcome("not_proven", "unsupported_construct", _tail(text))
        if re.search(r"solver|z3|yices|cvc", text, re.I) and re.search(r"error|fail", text, re.I):
            return outcome("not_proven", "solver_error", _tail(text))
        if result.exit_code != 0:
            return outcome("not_proven", "tool_crash", f"crux-llvm exited {result.exit_code} with no goal status: "
                                                      f"{_tail(text)}")
        return outcome("not_proven", UNCLASSIFIED, f"crux-llvm exited {result.exit_code} with no goal status")
    disproved = [(name.strip(), int(line), function) for name, line, _col, function in GOAL.findall(text)]
    goals, unproven, failures, reached = [], [], [], set()
    for name, line, function in disproved:
        goals.append({"goal": f"{name}:{line}", "property": name, "function": function, "status": "failure",
                      "solver": None, "seconds": None})
        if name == tr.REACH_END or name.startswith(tr.REACH_SUMMARY):
            reached.add(name)
            continue
        if name == tr.ORACLE_CAPACITY:
            continue
        unproven.append({"property": name, "kind": "property", "function": function, "line": line,
                         "status": "failure"})
        failures.append({"check": f"{name}:{line}", "property": name, "function": function, "builtin": "#" not in name,
                         "oracle": _oracle(report_dir, line, plan)})
    if failures:
        return outcome("failed", None, f"{len(failures)} propert(ies) failed", goals, unproven, failures)
    cut = re.search(r"iteration bound|recursion bound|bound exceeded|unwinding|loop bound", text, re.I)
    if counts.get("Incomplete") or cut:
        why = "a loop or recursion ran past the iteration bound" if cut else \
            f"{counts.get('Incomplete')} goal(s) incomplete (paths cut at the bound)"
        return outcome("not_proven", "unwinding_bound_too_small", why, goals,
                       unproven + [{"property": "iteration bound", "kind": "unwinding", "function": None, "line": None,
                                    "status": "incomplete"}])
    if counts.get("Unknown"):
        return outcome("not_proven", "unknown", f"{counts['Unknown']} goal(s) unknown", goals, unproven)
    missing = [name for name in required if name not in reached]
    if missing:
        return outcome("not_proven", "vacuous_pass", f"reachability assert(s) never disproved: {', '.join(missing)} "
                       "(the assumptions admit no execution there)", goals,
                       [{"property": name, "kind": "reachability", "function": None, "line": None, "status": "success"}
                        for name in missing])
    return outcome("proven", None, "every property holds and every reachability assert fails", goals)


def _tail(text):
    lines = [line for line in text.splitlines() if line.strip() and "Invalid record size" not in line
             and "Expected size" not in line and "METADATA" not in line]
    return " | ".join(lines[-4:])[:400]


def _oracle(report_dir, line, plan):
    """The values crux's counterexample gives the oracle, in draw order (integers and reals merged by the plan).
    crux-llvm names a goal's counterexample by the goal's line (`counter-example-<line>.c`); every property
    statement of a generated job is on its own line. In `-f real` mode crux gives no value for a real variable:
    it replays as 0.0."""
    path = Path(report_dir) / f"counter-example-{line}.c"
    if not path.exists():
        return []
    text = path.read_text(errors="replace")
    ints = [_int(v) for v in _values(text, "int64_t")]
    reals = [float(v.rstrip("fFlL")) for v in _values(text, "double")]
    values = []
    for draw in plan.draws:
        if tr.is_real_type(draw.get("ctype")):
            values.append(reals.pop(0) if reals else 0.0)
        else:
            values.append(ints.pop(0) if ints else 0)
    return values + ints + reals


def _values(text, kind):
    match = re.search(rf"crucible_values_{kind}\[\]\s*=\s*\{{([^}}]*)\}}", text)
    if not match:
        return []
    return [v.strip() for v in match.group(1).split(",") if v.strip()]


def _int(text):
    text = text.strip().rstrip("uUlL")
    value = int(text, 16) if text.lower().lstrip("-").startswith("0x") else int(text)
    return value - 2**64 if value >= 2**63 else value


from swdb import proof as _proof_module      # noqa: E402  (registered here, so either module may be imported first)
_proof_module.ADAPTERS[CruxCxxAdapter.name] = CruxCxxAdapter
_proof_module.ADAPTERS[CruxCAdapter.name] = CruxCAdapter
