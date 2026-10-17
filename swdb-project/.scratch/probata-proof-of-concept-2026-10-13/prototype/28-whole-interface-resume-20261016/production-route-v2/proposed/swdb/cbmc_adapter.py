"""The CBMC adapter: CBMC 6.11 on the C lowering of a proof unit, the bounded verifier at threads = 1.

Created: 2026-10-14 ET (Probata proof of concept ticket 22; Yan-Ru's 13:19 ET decision replaced SAW with CBMC
on ticket 21's C lowering). Design: formal-verification map spec ("Verifier lineup and order", "Bounds"); map
11 items 1-4, 8, 9; 16 items 1, 3; 19 items 2, 8. Reference: prototype/06c-cbmc/ (cbmc-two-lanes.md).
Format: docs/reference/format-v0.4-cbmc.md.

One job (`swdb prove --adapter cbmc --bounds '{"threads": 1, "<size parameter>": N, ...}'`):
1. Lower the proof unit (`swdb.c_lowering`). Outside the core subset: not proven, `unsupported_construct`,
   and the record's settings name the reason (`outside_cpp_subset`); CBMC never reads the C++ itself.
2. Translate the formal halves (`swdb.cbmc_translator`): the unit's harness; for each callee that a library
   entry summarizes (its `proof_unit.function`), the entry's stub replaces the callee's code. The unit's
   record pins each summary (entry hash plus its proven `library_summary` proof record). A compared knob (a
   contract knob that is a global the code only compares) is drawn symbolically and assumed legal.
3. C-versus-C++ differential (the check on the trusted C lowering tool): the C lowering and the C++ of the same
   functions, with one shared harness, run every input of the bounded domain natively; any difference stops
   the batch (`c_lowering_disagreement`: no record, no proven verdict).
4. CBMC with `--unwind K --unwinding-assertions` (K = the largest size bound + 1) and the method version's
   flags, under the RSS watchdog and the job's wall budget (default 15 minutes).
5. Read every property: proven when all hold and every reachability assert (`swdb_reach.*`) fails (else
   `vacuous_pass`); an unwinding assertion that fails is `unwinding_bound_too_small`; a failed property is
   replayed on the C++ (callees by their stubs, the proof semantics) with the trace's oracle values and
   sanitizers on. It replays: refuted, with the concrete inputs. It does not: not proven,
   `spurious_counterexample`, with the counterexample in `unreplayed_counterexample`.
6. Every outcome maps to a class of vocabulary `proof_failure_classes`, and that class's handler runs
   (`cbmc/handler.json`). An outcome with no class reports `unclassified_cbmc_outcome`, which stops the batch.

Updated: 2026-10-14 ET (Probata PoC 23): the formal halves may call logic-library definitions (library/logic/,
one C function each, ahead of the code); each summary pin lists the `assume`s its stub emitted (`assumes`);
SWDB_CBMC_STUB_FAULT (a YAML file `drop: [clause name, ...]`) hand-weakens a stub for the agreement negative
control. CBMC never serves a real-valued unit (the `bounded` adapter routes those to crux-llvm `-f real`).
"""

import hashlib
import itertools
import json
import os
import random
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from swdb import c_lowering, cbmc_translator as tr, cpu_memory_admission, paths, proof_semantics, rss_watchdog, std_models, vocab, yamlio
from swdb.proof import AdapterError, Verdict

NAME = "cbmc"
DEFAULT_WALL_SECONDS = 15 * 60                   # map 19 item 8: 15 minutes per bounded job
DEFAULT_CAP_BYTES = 8 * 2**30                    # O9: the ~8 GB RSS watchdog
FROZEN = ("--unwinding-assertions", "--pointer-overflow-check")
UNCLASSIFIED = "unclassified_cbmc_outcome"       # not a failure class: stops the batch (11 item 9)
DISAGREEMENT = "c_lowering_disagreement"
MAX_RUNS = 20000
VALUES = (-2, -1, 0, 1, 2)
SCALAR_EXTREMES = (-2147483648, 2147483647)
SANITIZERS = ("-fsanitize=address,undefined", "-fno-sanitize-recover=all")
REPLAY_SECONDS = 120

# CBMC builtin check kinds and the sanitizer reports of the same kind of fault (code review 2026-10-14).
_FAULTS = {"overflow": ("overflow",), "undefined-shift": ("shift",), "division-by-zero": ("division by zero",),
           "pointer_dereference": ("AddressSanitizer", "null pointer", "misaligned", "out of bounds"),
           "array_bounds": ("AddressSanitizer", "out of bounds"), "pointer": ("AddressSanitizer", "null pointer")}


def _same_fault(check, report):
    """Whether a sanitizer report is the kind of fault the CBMC check names (None: an unmapped check kind)."""
    kinds = [k for k in _FAULTS if f".{k}." in check]
    if not kinds:
        return None
    return any(word in report for word in _FAULTS[kinds[0]])
SENTENCES = {
    "c_lowering": "The C lowering tool (swdb lower, version {version}) lowers the C++ proof unit to C that behaves the "
                  "same; CBMC checks the C lowering, not the C++ (the differential run on the bounded domain is the "
                  "cross-check).",
    "clang": "clang {version} parses and compiles the C++ proof unit correctly (C lowering, differential run, replay).",
    "translator": "The CBMC translator ({version}) turns formal halves into a harness and summary stubs that mean "
                  "what the ACSL means within the bounds.",
    "cbmc": "CBMC {version} explores every path of the C lowering within the unwinding bound and reports every "
            "failing property (unwinding assertions on).",
    "solver": "The SAT solver {version} answers unsatisfiable only for unsatisfiable formulas.",
}


# --- the tools ----------------------------------------------------------------------------------------------

_FOUND = {}


def locate():
    """(command tuple, version, missing) of CBMC: SWDB_CBMC (a command line; `none` = missing), else PATH."""
    key = os.environ.get("SWDB_CBMC", "")
    if key in _FOUND:
        return _FOUND[key]
    if key == "none":
        found = ((), "", "CBMC disabled by SWDB_CBMC=none")
    else:
        command = tuple(shlex.split(key)) if key else ((shutil.which("cbmc"),) if shutil.which("cbmc") else ())
        found = ((), "", "cbmc not found (SWDB_CBMC or PATH)")
        if command:
            try:
                done = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=60)
                match = re.match(r"\s*(\d+\.\d+(?:\.\d+)?)", done.stdout)
                found = (command, match.group(1), "") if done.returncode == 0 and match else \
                    ((), "", "cbmc did not report a version")
            except (OSError, subprocess.SubprocessError) as exc:
                found = ((), "", f"cbmc did not start: {exc}")
    _FOUND[key] = found
    return found


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _binary(command):
    """The file a command line runs: its last argument that is a file (a script), else its program."""
    for part in reversed(command):
        if Path(part).is_file():
            return Path(part).resolve()
    return Path(shutil.which(command[0]) or command[0]).resolve()


def _version_matches(pinned, installed):
    return pinned is not None and (installed == pinned or installed.startswith(f"{pinned}."))


# --- the adapter --------------------------------------------------------------------------------------------

class CbmcAdapter:
    """`swdb prove --adapter cbmc`: one bounded job per call (records via swdb.proof)."""
    name = NAME
    real = True                                   # swdb prove takes the machine-wide verifier lock

    def __init__(self, library, contract, method, records=None, defines=()):
        self.library, self.contract, self.method = library, contract, method
        self.records = Path(records) if records else None
        self.defines = tuple(sorted(defines))
        proof_semantics.check_defines(self.defines)

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        # This fixture binds original software-counter source and a WP-only
        # contract route. The legacy CBMC model/assumptions are not admitted.
        from swdb import dx100_initialized_register_source
        if library is not None and any(dx100_initialized_register_source.initialized_register_layout(data)
                                       for data in proof_semantics.current(library).values()):
            raise AdapterError("the partial initialized register fixture is admitted only through its WP route")
        from swdb import dx100_register_source
        if library is not None and any(dx100_register_source.register_layout(data)
                                       for data in proof_semantics.current(library).values()):
            raise AdapterError("the partial register fixture is admitted only through its WP route")
        from swdb import dx100_allocation_source
        if library is not None and any(dx100_allocation_source.allocation_layout(data)
                                       for data in proof_semantics.current(library).values()):
            raise AdapterError("the software allocator fixture is admitted only through its WP route")
        if getattr(args, "whole_function", None):          # ticket 61: whole-function equivalence
            from swdb.cbmc_equivalence import EquivalenceAdapter
            return EquivalenceAdapter.from_args(args, script, library=library, contract=contract, method=method)
        if script is not None:
            raise AdapterError("the cbmc adapter takes no --script (one CBMC job per call)")
        return cls(library, contract, method, records=getattr(args, "records", None),
                   defines=getattr(args, "define", None) or ())

    # --- the job ---------------------------------------------------------------------------------------
    def run(self, job):
        out = Path(job.log).parent / "cbmc"
        out.mkdir(exist_ok=True)
        log = _Log(job.log)
        entry = self.library.get(self.contract) or {}
        summary_job = job.unit.candidate is None
        log.line(f"adapter: cbmc\nunit: {job.unit.candidate or 'library summary ' + self.contract} {job.unit.function}\n"
                 f"contract: {self.contract}")
        tools = self._tools()
        sizes = _sizes(job.bounds)
        context = {"job": job, "out": out, "log": log, "reports": [], "tools": tools, "bounds": dict(job.bounds),
                   "settings": {"tool": "cbmc", "flags": [], "translator": tools["translator"]["id"],
                                "build_constants": list(self.defines), "verifier_launched": False}}
        if summary_job:
            source = self.library.resolve((entry.get("proof_unit") or {}).get("source"))
        else:
            from swdb.wp_adapter import _unit_source
            source = _unit_source(Path(job.unit.tree), job.unit.function)
        log.line(f"source: {source.name}")
        from swdb import dx100_checked_source, dx100_checked_adapter
        selected_whole = dx100_checked_source.select_baseline(self.library, entry.get('proof_unit') or {})
        if selected_whole is not None:
            return dx100_checked_adapter.run(self,job,entry,context,source,selected_whole)
        covered = proof_semantics.covered_names(self.library)
        declarations = (entry.get('proof_unit') or {}).get('array_domains')
        source_kwargs = dict(defines=self.defines, **proof_semantics.lowering_options(self.library))
        # The exact synthetic trace imports scalar bodyless ghost queries only.
        # Reuse the established full-TU callee/signature checker, without adding
        # any pointer-domain or real-header exemption to the generic path.
        from swdb import bounded_initialization
        trace_policy = None
        if bounded_initialization.DX100_TRACE_ENTRY in proof_semantics.current(self.library):
            trace_model = proof_semantics.model_for(self.library, bounded_initialization.DX100_TRACE_ENTRY, self.defines)
            trace_policy = bounded_initialization._dx100_trace_policy(self.library, trace_model, self.defines)
            if trace_policy is not None:
                source_kwargs['semantics']['audited_imports'] = {
                    name: row for name, row in proof_semantics.imported_call_policies(self.library, self.defines).items()
                    if name in trace_policy['calls']}
        if declarations:
            source_kwargs.update(array_domains=json.loads(json.dumps(declarations)),
                array_domain_contract={'id': self.contract, 'sha256': job.unit.contract_sha256})
        try:
            lowering = c_lowering.lower(source, job.unit.function, **source_kwargs)
        except c_lowering.Unsupported as exc:
            context["settings"]["outside_cpp_subset"] = f"outside the C++ subset: {exc}"
            return self._not_proven("unsupported_construct", str(exc), context)
        except c_lowering.ParseError as exc:
            return self._not_proven("parse_error", str(exc), context)
        except c_lowering.LoweringError as exc:
            raise AdapterError(str(exc)) from None
        from swdb import stdlib_source_admission
        provenance_problem = stdlib_source_admission.bind(context, lowering, source, defines=self.defines)
        if provenance_problem:
            return self._not_proven("unsupported_construct", provenance_problem, context)
        model = None
        externals = proof_semantics.called(lowering, covered)
        if externals:
            entries = sorted({covered[name] for name in externals})
            if len(entries) != 1:
                raise AdapterError(f"{job.unit.function} calls into more than one proof semantics: {', '.join(entries)}")
            model = proof_semantics.model_for(self.library, entries[0], self.defines)
            log.line(f"proof semantics: {model.entry} (sha256 {model.sha256}); calls {', '.join(externals)}; "
                     f"{len(lowering.probes)} hazard probe(s)")
        code = Code(lowering, source, self.defines, model)
        code.apply_fault(os.environ.get("SWDB_CBMC_LOWERING_FAULT"))
        context["pins"] = {"c_lowering": {"id": f"{lowering.function}.c", "sha256": code.c_sha256},
                           "naming_rules": c_lowering.naming_rules()}           # ticket 24
        if model is not None:
            context["pins"]["proof_semantics"] = {"id": model.entry, "sha256": model.sha256}
            context["settings"]["proof_semantics"] = {
                "id": model.entry, "calls": list(externals),
                "exit_check": "no pending device store before formal poststate observations; pending reads allowed",
                "native_address_abi": "flat 64-bit uintptr_t data addresses, 32-bit int; CBMC retains object IDs",
                "probes": [{k: p[k] for k in ("id", "function", "access", "line")} for p in lowering.probes]}
            if proof_semantics.instance_bindings(lowering):
                context['settings']['proof_semantics']['instances'] = proof_semantics.instance_bindings(lowering)
            context["model"] = model
            if model.entry == bounded_initialization.DX100_TRACE_ENTRY:
                settings = context['settings']['proof_semantics']
                settings.update(scope='synthetic abstract scalar event trace only',
                    exit_check='no pending abstract command at unit exit',
                    native_address_abi='scalar abstract cell/region/tile IDs; no caller pointer mapping',
                    counterexample_scope='abstract-model trace only; no hardware counterexample or source refinement')
                from swdb import wp_pointer_bounds
                try:
                    import_report = wp_pointer_bounds.check(lowering)
                    wp_pointer_bounds.check_semantic_origins(lowering, self.library, self.defines)
                except wp_pointer_bounds.Refused as exc:
                    context['settings']['verifier_launched'] = False
                    return self._not_proven('unsupported_construct', str(exc), context)
                imports = [row for row in import_report['sites'] if row.get('kind') == 'import'
                           and row.get('call') in (trace_policy or {}).get('calls', [])]
                settings['source_imports'] = [{k: v for k, v in row.items() if not k.startswith('_')} for row in imports]
                bound_names = {(row.get('binding') or {}).get('name') for row in imports
                               if row.get('binding') and not row.get('reason')}
                if (trace_policy is None or not set(externals) <= bound_names
                        or any(not row.get('binding') or row.get('reason') for row in imports)):
                    context['settings']['verifier_launched'] = False
                    return self._not_proven('unsupported_construct',
                        'synthetic scalar queries need exact bodyless full-TU imports and model policy', context)
                context['synthetic_trace_source_plan'] = {'source': str(source), 'kwargs': source_kwargs}
        problem = std_models.method_problem(self.method, lowering)
        if problem:
            raise AdapterError(problem)
        context["pins"].update(std_models.pins(lowering))
        context["lowering"] = lowering
        refusal = cpu_memory_admission.check(lowering, covered)
        if refusal:
            context["settings"]["proof_semantics_admission"] = refusal
            return self._not_proven("unsupported_construct",
                "ordinary CPU memory interference with DX100 commands needs ticket 28's memory-hazard probes", context)
        from swdb import bounded_initialization
        admission = bounded_initialization.check(lowering, max(sizes.values(), default=0), library=self.library, model=model)
        context["settings"]["bounded_initialization"] = admission
        if admission["verdict"] != "passed":
            return self._not_proven("unsupported_construct", admission["reason"], context)
        if lowering.std_models:
            context["settings"]["std_models"] = list(lowering.std_models)
            # The concrete growth policy follows libc++ 22.1.8. Clang's version does not identify its STL:
            # Linux commonly pairs that clang with libstdc++, whose capacity policy can differ.
            probe = subprocess.run([*context["tools"]["clang"].command, "-dM", "-E", "-x", "c++",
                                    "-std=gnu++17", "-include", "vector", "-"],
                                   input="", capture_output=True, text=True, timeout=60)
            if probe.returncode != 0 or not re.search(r"^#define _LIBCPP_VERSION 220108$", probe.stdout, re.M):
                return self._not_proven("unsupported_construct",
                                       "the standard models require libc++ 22.1.8 (_LIBCPP_VERSION 220108); "
                                       "the selected clang uses an unmatched standard library", context)
            context["settings"]["standard_library"] = {"implementation": "libc++", "version": "22.1.8",
                                                         "header_macro": "_LIBCPP_VERSION=220108"}
        from swdb import summary_bindings
        try:
            built = self._build(job, entry, code, sizes, summary_job, context)
        except summary_bindings.Refused as exc:
            return self._not_proven('unsupported_construct', str(exc), context)
        except tr.Untranslatable as exc:
            context["settings"]["untranslatable"] = str(exc)
            return self._not_proven("unsupported_construct", f"the CBMC translator: {exc}", context)
        if built['plan'].array_domains:
            context['settings'].update(array_domains=built['plan'].array_domains, verifier_launched=False)
            from swdb import bounded_entry_windows
            try:
                code.text, source_view, checked = bounded_entry_windows.prepare(
                    lowering, source, built['plan'].array_domains, defines=self.defines)
            except bounded_entry_windows.Refused as exc:
                context['settings']['array_domains'] = dict(built['plan'].array_domains, refusal=str(exc))
                return self._not_proven('unsupported_construct', str(exc), context)
            code.window_cxx[lowering.function] = source_view
            context['settings']['array_domains'] = checked
            context['array_domain_runtime'] = {'source': source, 'kwargs': source_kwargs,
                'code': code, 'built': built, 'summary_job': summary_job}
        refusal = cpu_memory_admission.summary_refusal(self.records, [
            pin["proof_record"] for pin in context["pins"].get("summaries", [])])
        if refusal:
            context["settings"]["proof_semantics_admission"] = refusal
            context["settings"]["verifier_launched"] = False
            return self._not_proven("memory_domain", "opaque semantics dependency needs a checked memory boundary", context)
        from swdb import bounded_entry_windows
        try:
            self.check_entry_windows(job, context)
            problem = self._differential(job, code, built, context)
        except bounded_entry_windows.Refused as exc:
            return self._not_proven('unsupported_construct', str(exc), context)
        if problem:
            return problem
        return self._cbmc(job, code, built, context)

    def check_entry_windows(self, job, context, inputs=()):
        """Regenerate source, planner and both checked views immediately before launch."""
        if 'whole_source_unit' in context:
            from swdb import dx100_checked_adapter
            dx100_checked_adapter.check_launch(self,job,context,inputs)
            return
        trace_plan = context.get('synthetic_trace_source_plan')
        if trace_plan is not None:
            from swdb import bounded_initialization, bounded_entry_windows, wp_pointer_bounds
            model = context.get('model')
            if bounded_initialization._dx100_trace_policy(self.library, model, self.defines) is None:
                raise bounded_entry_windows.Refused('synthetic scalar model policy changed before launch')
            try:
                wp_pointer_bounds.recheck_source(context['lowering'], trace_plan)
                wp_pointer_bounds.check_semantic_origins(context['lowering'], self.library, self.defines)
            except wp_pointer_bounds.Refused as exc:
                raise bounded_entry_windows.Refused(str(exc)) from None
        entry = self.library.get(self.contract) or {}
        declarations = (entry.get('proof_unit') or {}).get('array_domains')
        runtime = context.get('array_domain_runtime')
        planned = bool(runtime or context.get('settings', {}).get('array_domains'))
        if not declarations and not planned:
            return
        from swdb import bounded_entry_windows
        if not declarations or not runtime:
            raise bounded_entry_windows.Refused('bounded window declarations or source replay plan disappeared')
        if self.library.content_sha256(self.contract) != job.unit.contract_sha256:
            raise bounded_entry_windows.Refused('bounded window input contract changed after planning')
        fresh = c_lowering.lower(runtime['source'], job.unit.function, **runtime['kwargs'])
        if fresh != runtime['code'].lowering:
            raise bounded_entry_windows.Refused('bounded window source/closure lowering changed before launch')
        code = Code(fresh, runtime['source'], self.defines)
        rebuilt = self._build(job, entry, code, _sizes(job.bounds), runtime['summary_job'],
                              {'settings': {}, 'pins': {}})
        if rebuilt != runtime['built']:
            raise bounded_entry_windows.Refused('bounded window harness, declarations or planner changed before launch')
        c_text, source_view, checked = bounded_entry_windows.prepare(
            fresh, runtime['source'], rebuilt['plan'].array_domains, defines=self.defines)
        if (runtime['code'].text != c_text or runtime['code'].window_cxx != {fresh.function: source_view}
                or context['settings'].get('array_domains') != checked):
            raise bounded_entry_windows.Refused('bounded window source views or operation checks changed before launch')
        if inputs:
            expected = tr.prelude() + rebuilt['logic'] + c_text + rebuilt['harness']
            if len(inputs) != 1 or Path(inputs[0][0]).read_text() != expected:
                raise bounded_entry_windows.Refused('bounded window launched input differs from fresh checked view')

    def _tools(self):
        """Installed CBMC and clang against the method version's lineup; the translator and the C lowering tool
        against its translators. A mismatch runs nothing (no record)."""
        lineup = {}
        for row in self.method.data.get("lineup") or []:
            lineup.setdefault(row.get("tool"), row)
        command, version, missing = locate()
        clang = c_lowering.locate()
        if missing:
            raise AdapterError(missing)
        if clang.missing:
            raise AdapterError(clang.missing)
        problems = []
        pinned = (lineup.get("cbmc") or {}).get("version")
        if not _version_matches(pinned, version):
            problems.append(f"cbmc {version} is installed but method version {self.method.id} pins {pinned}")
        if (lineup.get("clang") or {}).get("version") != clang.version:
            problems.append(f"clang {clang.version} is installed but method version {self.method.id} pins "
                            f"{(lineup.get('clang') or {}).get('version')}")
        translators = (self.method.data.get("c_lowering") or {}).get("translators") or []
        ident = c_lowering.identity()
        for name, found in (("C lowering tool", ident["c_lowering"]), ("CBMC translator", tr.identity())):
            if found not in translators:
                problems.append(f"the {name} {found['id']} (sha256 {found['sha256'][:12]}...) is not a translator of "
                                f"method version {self.method.id}")
        if problems:
            raise AdapterError("; ".join(problems))
        flags = [str(f) for f in (lineup.get("cbmc") or {}).get("flags") or []]
        from swdb import proof_setup
        proof_setup.check_cbmc_flags([*command[1:], *flags], require=False)
        solver = flags[flags.index("--sat-solver") + 1] if "--sat-solver" in flags[:-1] else "minisat2"
        cbmc_sha = _sha256(_binary(command))
        return {"command": command, "version": version, "flags": flags, "clang": clang,
                "translator": tr.identity(),
                "identities": {"c_lowering": (ident["c_lowering"]["id"], ident["c_lowering"]["sha256"],
                                              c_lowering.TOOL_VERSION),
                               "clang": (f"clang-{clang.version}", ident["clang"]["sha256"], clang.version),
                               "translator": (tr.identity()["id"], tr.identity()["sha256"], tr.identity()["id"]),
                               "cbmc": (f"cbmc-{version}", cbmc_sha, version),
                               "solver": (f"{solver}-in-cbmc-{version}", cbmc_sha, f"{solver} (bundled with CBMC {version})")}}

    # --- translation ---------------------------------------------------------------------------------------
    def _build(self, job, entry, code, sizes, summary_job, context):
        """The harness, the stubs and the plan."""
        if code.lowering.whole_source is not None:
            from swdb import dx100_checked_adapter
            if sizes:
                raise AdapterError('whole checked source has no size parameter')
            return dx100_checked_adapter.build(self,job,entry,code,context)
        unit = code.interface(job.unit.function)
        rows = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")]
        if summary_job:
            chosen = [c for c in rows if c.get("proof_placement") == {"once": "self"}]
        else:
            chosen = [c for c in rows if c.get("proof_placement") == "per_candidate"]
        knobs, symbolic = self._knobs(entry, code, rows, chosen)
        if not chosen:
            raise AdapterError(f"{self.contract} has no {'once: self' if summary_job else 'per-candidate'} formal "
                               "half to check")
        clauses = tr.clauses(self.contract, chosen)
        for name in sizes:
            if not unit.scalar(name):
                raise AdapterError(f"bound {name} is not an integer parameter of {unit.function} (its size dimensions "
                                   f"are its integer parameters: {', '.join(p[0] for p in unit.parameters if not p[2])})")
        pointers = [p for p in unit.parameters if p[2]]
        cap = max(sizes.values()) if sizes else 0
        if pointers and not sizes:
            raise AdapterError(f"{unit.function} takes arrays ({', '.join(p[0] for p in pointers)}): the bounds need a "
                               "size bound on an integer parameter")
        logic = logic_of(self.library)
        setup, state, finish = (), (), ()
        if code.model is not None:                    # ticket 27: ghost state g0, then havoc the tile elements
            setup = ("swdb_dx_init();",)
            state = proof_semantics.state_draws(self.library, code.model.entry, self.defines)
            finish = ("swdb_dx_check_exit();",)
        harness, plan = tr.harness(unit, clauses, sizes=sizes, cap=cap, knobs=knobs, logic=logic, setup=setup,
                                   state=state, finish=finish,
                                   array_domains=(entry.get('proof_unit') or {}).get('array_domains'))
        drop = stub_fault()
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
        unwind = cap + 1
        context["settings"].update(unwind=unwind, array_length=cap, symbolic_knobs=symbolic,
                                   summaries=[s["id"] for s in summaries])
        if summaries:
            context["pins"]["summaries"] = summaries
        return {"harness": harness, "plan": plan, "stubs": stubs, "unwind": unwind, "sizes": sizes,
                "logic": logic.block()}

    def _knobs(self, entry, code, rows, chosen):
        """[(name, C condition, (min, max))] of the compared knobs this code uses; their legality clauses join `chosen`."""
        knobs, symbolic = [], []
        defined = {d.split("=", 1)[0] for d in self.defines}
        for knob in entry.get("knobs") or []:
            name = knob.get("name") if isinstance(knob, dict) else None
            if not name or name in defined or name not in code.scalar_globals:
                continue
            uses = code.uses(name)
            if not uses["compared_only"]:
                raise AdapterError(f"knob {name} is used other than in comparisons ({uses['other']}): give it as a build "
                                   "constant (--define), not a symbolic knob")
            legal = knob.get("range") or {}
            low, high = legal.get("min"), legal.get("max")
            if not isinstance(low, int) or not isinstance(high, int):
                raise AdapterError(f"knob {name} has no integer range (min, max) to bound it")
            clause = next((c for c in rows if c.get("id") == knob.get("legality_clause")), None)
            if clause is not None and clause not in chosen:
                chosen.append(clause)
            knobs.append((name, f"{name} >= {low} && {name} <= {high}", (low, high)))
            symbolic.append({"name": name, "legality_clause": knob.get("legality_clause"),
                             "acsl": (clause or {}).get("acsl", {}).get("text", "").strip() or None,
                             "range": {"min": low, "max": high}})
        return knobs, symbolic

    def _summary(self, callee, *, accept=None):
        """(entry ID, entry, proven summary record ID) of the library entry that summarizes `callee`, or None."""
        entries = [(eid, data) for eid, data in sorted(self.library.entries.items())
                   if eid != self.contract and isinstance(data.get("proof_unit"), dict)
                   and data["proof_unit"].get("function") == callee
                   and any(isinstance(c, dict) and c.get("proof_placement") == {"once": "self"} and c.get("acsl")
                           for c in data.get("clauses") or [])]
        if not entries:
            return None
        if len(entries) > 1:
            raise AdapterError(f"callee {callee} is summarized by more than one library entry: "
                               f"{', '.join(e for e, _ in entries)}")
        entry_id, data = entries[0]
        sha = self.library.content_sha256(entry_id)
        from swdb.store import Store
        proven = []
        if self.records is not None:
            for record in Store(self.records).of_kind("proof"):
                d = record.data
                subject = d.get("subject") or {}
                if subject.get("kind") == "library_summary" and subject.get("id") == entry_id and \
                        d.get("verdict") == "proven" and ((d.get("pins") or {}).get("contract") or {}).get("sha256") == sha:
                    proven.append(((d.get("job") or {}).get("batch", ""), record.id))
        if not proven:
            raise AdapterError(f"callee {callee} is summarized by library entry {entry_id}, which has no proven summary "
                               f"record at its current content: run `swdb prove --summary {entry_id} --adapter cbmc` first")
        refused = None
        for _, record_id in sorted(proven, reverse=True):
            if accept is not None:
                from swdb import summary_bindings
                try:
                    accept(entry_id, record_id)
                except summary_bindings.Refused as exc:
                    refused = exc
                    continue
            return entry_id, data, record_id
        raise refused

    # --- the differential run ------------------------------------------------------------------------------
    def _differential(self, job, code, built, context):
        from swdb import stdlib_source_admission
        try:
            stdlib_source_admission.recheck(context)
        except stdlib_source_admission.Refused as exc:
            raise AdapterError(f"proof setup check [stdlib_provenance]: {exc}") from None
        """C lowering versus C++ on every input of the bounded domain (no stubs: the real callees on both sides)."""
        out, log, scratch = context["out"], context["log"], Path(job.scratch)
        lines, sampled, domain = _domain(built["plan"])
        inputs = scratch / "domain.txt"
        inputs.write_text("".join(" ".join(str(v) for v in line) + "\n" for line in lines))
        c_text = tr.prelude(whole_source=code.lowering.whole_source) + built["logic"] + code.c_text() + built["harness"]
        cxx_text = tr.prelude(whole_source=code.lowering.whole_source) + built["logic"] + code.cxx_text() + built["harness"]
        paths_ = {"c": out / "differential_c.c", "cxx": out / "differential_cxx.cc"}
        paths_["c"].write_text(c_text)
        paths_["cxx"].write_text(cxx_text)
        context["reports"] += [("differential_c", paths_["c"]), ("differential_cxx", paths_["cxx"])]
        outputs, undefined = {}, set()
        whole = code.lowering.whole_source is not None
        heap = code.lowering.allocation           # ticket 25: heap use (models, new[]) runs under AddressSanitizer
        for side in ("c", "cxx"):
            binary = scratch / f"differential_{side}"
            if whole:
                from swdb import dx100_checked_adapter
                dx100_checked_adapter.check_launch(self,job,context,[(paths_[side],c_text if side == 'c' else cxx_text)])
                problem = dx100_checked_adapter.compile_native(context['tools'],side,paths_[side],binary,
                    ['-DSWDB_NATIVE','-DSWDB_DIFFERENTIAL','-O0','-w',*SANITIZERS,*code.cxx_defines()])
            else:
                problem = _compile(context["tools"]["clang"], side, paths_[side], binary,
                                   ["-DSWDB_NATIVE", "-DSWDB_DIFFERENTIAL", "-O0", "-fwrapv", "-w",
                                    *(("-fsanitize=address",) if heap else ()),
                                    *(code.cxx_defines() if side == "cxx" else ())])
            if problem:
                return self._not_proven("parse_error", f"the {side} side of the differential run does not compile: "
                                        f"{problem}", context)
            if whole:
                dx100_checked_adapter.check_launch(self,job,context)
                done, crashed = dx100_checked_adapter.run_fresh_domain(binary,lines)
                dx100_checked_adapter.check_launch(self,job,context)
            else:
                done, crashed = _run_domain(binary, lines, sanitized=heap)
            if done.returncode != 0:
                return self._not_proven("tool_crash", f"the {side} side of the differential run exited "
                                        f"{done.returncode}: {done.stderr[-400:]}", context)
            undefined |= crashed
            outputs[side] = done.stdout
            path = out / f"differential_{side}.out"
            path.write_text(done.stdout)
            context["reports"].append((f"differential_{side}_output", path))
        if undefined:                             # either side's sanitizer fired: no agreement evidence there
            for side in outputs:
                rows = outputs[side].splitlines(keepends=True)
                outputs[side] = "".join(f"run {k}: undefined behavior\n" if k in undefined else row
                                        for k, row in enumerate(rows))
        agreement = {"runs": len(lines), "sampled": sampled, "domain": domain,
                     "c_output_sha256": hashlib.sha256(outputs["c"].encode()).hexdigest(),
                     "cxx_output_sha256": hashlib.sha256(outputs["cxx"].encode()).hexdigest()}
        if heap:
            agreement["undefined_behavior_runs"] = len(undefined)
        if outputs["c"] != outputs["cxx"]:
            first = next(k for k, (a, b) in enumerate(itertools.zip_longest(outputs["c"].splitlines(),
                                                                                outputs["cxx"].splitlines())) if a != b)
            c_line = (outputs["c"].splitlines() + [""])[min(first, len(outputs["c"].splitlines()))]
            x_line = (outputs["cxx"].splitlines() + [""])[min(first, len(outputs["cxx"].splitlines()))]
            message = (f"{DISAGREEMENT}: the C lowering of {job.unit.function} and its C++ disagree on input "
                       f"{' '.join(map(str, lines[first])) if first < len(lines) else '?'}: C lowering `{c_line}`, "
                       f"C++ `{x_line}`. The batch stops; no verdict is recorded (root-cause it as a C lowering tool "
                       "defect and add the case to the regression corpus)")
            log.line(message)
            self._handler(DISAGREEMENT, message, context)
            raise AdapterError(message + f". Reproduction: {out}")
        agreement["verdict"] = "agree"
        log.line(f"differential: {len(lines)} runs, C lowering and C++ agree")
        context["settings"]["agreement"] = agreement
        return None

    # --- CBMC ------------------------------------------------------------------------------------------
    def _cbmc(self, job, code, built, context):
        tools, log, out, scratch = context["tools"], context["log"], context["out"], Path(job.scratch)
        text = tr.prelude(whole_source=code.lowering.whole_source) + built["logic"] + code.c_text(built["stubs"]) + built["harness"]
        job_c = out / "job.c"
        job_c.write_text(text)
        shutil.copyfile(job_c, scratch / "job.c")
        context["reports"].append(("cbmc_input", job_c))
        flags = ["-DSWDB_CBMC", "--unwind", str(built["unwind"]), *FROZEN,
                 *(flag for flag in tools["flags"] if flag not in FROZEN)]
        if code.model is not None:                   # ticket 27: the model's loops get the model's own bound
            if code.lowering.whole_source is not None:
                from swdb import dx100_checked_adapter
                loops = dx100_checked_adapter.model_loops(self,tools,scratch,code.lowering.whole_source,context)
            else:
                loops = self._model_loops(tools, scratch, code.model)
            if loops:
                flags += ["--unwindset", ",".join(f"{loop}:{code.model.unwind}" for loop in loops)]
        if code.lowering.allocation:              # ticket 25: the "allocation succeeds" assumption entry (CBMC 6
            flags.append("--no-malloc-may-fail")  # lets malloc return NULL by default)
        command = [*tools["command"], "job.c", *flags, "--json-ui"]
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
        wall = job.budget_seconds or DEFAULT_WALL_SECONDS
        cbmc_log = out / "cbmc.json"
        log.line(f"command: {shlex.join(map(str, command))}\ncwd: scratch\nrss cap bytes: {cap}\n"
                 f"wall budget seconds: {wall}")
        context["settings"].update(flags=flags, rss_cap_bytes=cap, wall_budget_seconds=wall)
        from swdb import proof_setup
        proof_setup.check_generated(job, self, context, [(scratch / "job.c", text)], flags,
                                    command=command, scratch=scratch, lowering=code.lowering)
        context['settings']['verifier_launched'] = True
        result = rss_watchdog.run(command, log=cbmc_log, cap_bytes=cap, timeout=wall, cwd=scratch,
                                  env={**os.environ, "TMPDIR": str(scratch)})
        context["reports"].append(("cbmc_output", cbmc_log))
        context["peak"] = result.peak_rss_bytes
        log.line(f"cbmc exit {result.exit_code}, wall {result.wall_seconds:.2f} s, peak rss {result.peak_rss_bytes}, "
                 f"out of memory {result.out_of_memory}, timed out {result.timed_out}")
        outcome = read_outcome(result, cbmc_log.read_text(errors="replace"))
        context["goals"], context["unproven"] = outcome["goals"], outcome["unproven"]
        log.line(f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})")
        if outcome["verdict"] == "proven":
            return self._verdict("proven", context)
        if outcome["verdict"] == "failed":
            return self._replay(job, code, built, outcome, context)
        return self._not_proven(outcome["failure_class"], outcome["why"], context)

    def _model_loops(self, tools, scratch, model):
        """CBMC's IDs of the loops inside the proof-semantics model's functions (`cbmc --show-loops`, parse only)."""
        done = subprocess.run([*tools["command"], "job.c", "-DSWDB_CBMC", *FROZEN,
                               *(flag for flag in tools["flags"] if flag not in FROZEN), "--show-loops"], cwd=scratch,
                              capture_output=True, text=True, timeout=300)
        loops = re.findall(r"^Loop (\S+):", done.stdout, re.M)
        return [loop for loop in loops if loop.rsplit(".", 1)[0] in model.functions]

    def _replay(self, job, code, built, outcome, context):
        """Replay each failing property's trace on the C++ (callees by their stubs) with sanitizers on."""
        out, scratch = context["out"], Path(job.scratch)
        replay_cc = out / "replay_cxx.cc"
        replay_cc.write_text(tr.prelude(whole_source=code.lowering.whole_source) + built["logic"] + code.cxx_text(built["stubs"]) + built["harness"])
        context["reports"].append(("replay_cxx", replay_cc))
        binary = scratch / "replay_cxx"
        if code.lowering.whole_source is not None:
            from swdb import dx100_checked_adapter
            dx100_checked_adapter.check_launch(self,job,context,[(replay_cc,replay_cc.read_text())])
            problem=dx100_checked_adapter.compile_native(context['tools'],'cxx',replay_cc,binary,
                ['-DSWDB_NATIVE','-DSWDB_REPLAY','-O0','-g','-w',*SANITIZERS,*code.cxx_defines()])
        else:
            problem = _compile(context["tools"]["clang"], "cxx", replay_cc, binary,
                               ["-DSWDB_NATIVE", "-DSWDB_REPLAY", "-O0", "-g", "-w", *SANITIZERS, *code.cxx_defines()])
        if problem:
            return self._not_proven("parse_error", f"the C++ replay does not compile: {problem}", context)
        tries = []
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
        for index, failure in enumerate(outcome["failures"]):
            # Code review 2026-10-14: the replay runs under the RSS watchdog, and its timeout is a record.
            given = scratch / f"replay_input_{index}.txt"
            given.write_text(" ".join(str(v) for v in failure["oracle"]) + "\n")
            replay_log = scratch / f"replay_{index}.log"
            if code.lowering.whole_source is not None:
                dx100_checked_adapter.check_launch(self,job,context)
            with open(given) as stdin:
                done = rss_watchdog.run([str(binary)], log=replay_log, cap_bytes=cap, timeout=REPLAY_SECONDS,
                                        cwd=scratch, env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"},
                                        stdin=stdin)
            if code.lowering.whole_source is not None:
                dx100_checked_adapter.check_launch(self,job,context)
            text = replay_log.read_text(errors="replace")
            if done.timed_out or done.out_of_memory:
                return self._not_proven("timeout" if done.timed_out else "out_of_memory",
                                        f"the C++ replay of {failure['check']} exceeded its "
                                        f"{'time' if done.timed_out else 'memory'} budget", context)
            if code.lowering.whole_source is not None:
                retained_replay = out / f'whole-source-replay-{index}.log'
                retained_replay.write_text(text)
                context['reports'].append((f'whole_source_replay_termination_{index}',retained_replay))
                context['settings'].setdefault('whole_source_replay_terminations',[]).append({
                    'exit_code':done.exit_code,'original_assert_abort_observed':
                        bool(re.search(r'__assert_fail|Assertion .*failed',text)),
                    'scope':'original C++ assert abort is retained; missing exact failure marker grants no replay'})
            inputs = _inputs(text)
            failed = re.findall(r" fail=(\S+)", text)
            reports = [ln for ln in text.splitlines() if "runtime error" in ln or "AddressSanitizer" in ln]
            sanitizer = bool(reports)
            # A sanitizer trap is a real counterexample to the candidate's safety whichever CBMC check
            # reported the trace, so it refutes; whether it is the same kind of fault is recorded for repair.
            if failure["builtin"]:
                replayed = sanitizer
            else:
                replayed = failure["property"] in failed
            counterexample = {"property": failure["property"], "check": failure["check"],
                              "function": failure["function"], "inputs": inputs, "oracle": failure["oracle"],
                              "replay": {"form": "cxx", "replayed": replayed, "failed": failed,
                                         "sanitizer": reports[0].strip()[:300] if sanitizer else None,
                                         "sanitizer_matches_check": (_same_fault(failure["check"], reports[0])
                                                                     if sanitizer and failure["builtin"] else None),
                                         "end": (re.findall(r" end=(\S+)", text) or ["none"])[0]}}
            tries.append(counterexample)
            context["log"].line(f"replay of {failure['check']} ({failure['property']}): "
                                f"{'replayed' if replayed else 'did not replay'}; native {text.strip()[:300]}")
            if replayed:
                context["settings"]["forms"] = {"c_lowering": "refuted", "cxx": "refuted (counterexample replayed)"}
                return self._verdict("refuted", context, counterexample=counterexample)
        context["settings"]["forms"] = {"c_lowering": "refuted", "cxx": "not refuted (no counterexample replayed)"}
        return self._not_proven("spurious_counterexample",
                                "no CBMC counterexample replays on the C++", context, unreplayed=tries[0])

    # --- verdicts and handlers ---------------------------------------------------------------------------
    def _not_proven(self, failure_class, why, context, unreplayed=None):
        context.setdefault("goals", [])
        context.setdefault("unproven", [])
        self._handler(failure_class, why, context)
        return self._verdict("not_proven", context, failure_class=failure_class, unreplayed=unreplayed)

    def _verdict(self, verdict, context, failure_class=None, counterexample=None, unreplayed=None):
        identities = context["tools"]["identities"]
        assumptions, tools = [], []
        for tool in ("c_lowering", "clang", "translator", "cbmc", "solver"):
            ident, sha, version = identities[tool]
            assumptions.append({"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                                "sentence": SENTENCES[tool].format(version=version)})
            tools.append(ident)
        model = context.get("model")
        if model is not None:                        # ticket 27: the proof semantics and the reduction it rests on
            assumptions += proof_semantics.record_assumptions(self.library, model.entry, model.sha256)
            from swdb import bounded_initialization
            if context.get('whole_source_unit') is not None:
                from swdb import dx100_checked_source
                assumptions += dx100_checked_source.record_assumptions(context['whole_source_unit'])
            elif model.entry == bounded_initialization.DX100_TRACE_ENTRY:
                assumptions.append({'kind': 'proof_semantics',
                    'reference': {'id': model.entry, 'sha256': model.sha256},
                    'sentence': 'This is a synthetic abstract scalar trace. Deferred history, ownership, '
                                'region and pair checks describe its exact pinned model only; there is no '
                                'real-header, CPU-access, typed-value, physical-address or hardware refinement '
                                'certificate and no at-issue reduction claim.'})
            else:
                assumptions.append({"kind": "proof_semantics", "reference": {"id": model.entry, "sha256": model.sha256},
                                    "sentence": f"The DX100 behaves as its proof semantics {model.entry} says: each "
                                                "command's values as if it finished at issue, hazards as its rules state."})
                assumptions.append({"kind": "assumed_clause", "reference": {"id": model.entry, "sha256": model.sha256},
                    "sentence": "Native agreement and replay use Clang's flat 64-bit uintptr_t data-address ABI "
                                "with 32-bit int; the model checks these widths at compilation. CBMC separately "
                                "uses allocation-object IDs and offsets for footprint membership."})
                reduction = Path(self.library.root) / "rocq" / "probata" / "Reduction.v"
                if not reduction.is_file():
                    reduction = paths.HOME / "library" / "rocq" / "probata" / "Reduction.v"
                assumptions.append({"kind": "reduction", "reference": {
                    "id": "rocq.probata.dx100_reduction", "sha256": _sha256(reduction)},
                    "sentence": "The DX100 reduction lemma (Reduction.v, statement only; proof: ticket 43): a hazard-free "
                                "at-issue run matches every timing gem5 allows."})
        if context.get("lowering") is not None:                                  # ticket 25
            ident, sha, _version = identities["c_lowering"]
            assumptions += std_models.assumptions(context["lowering"], identities["clang"][2],
                                                  {"id": ident, "sha256": sha})
        if verdict == "proven":
            context["settings"].setdefault("forms", {"c_lowering": "proven", "cxx": "agrees on the bounded domain"})
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

    def _handler(self, failure_class, why, context):
        """Run the handler of `failure_class` (map 11 item 9): write cbmc/handler.json."""
        vocabs, _problems = vocab.load_all(paths.VOCAB)
        entry = vocabs.entries.get("proof_failure_classes", {}).get(failure_class)
        out = context["out"]
        action = {"failure_class": failure_class, "why": why,
                  "handler": (entry or {}).get("handler") or "No class: the batch stops; root-cause it as a C lowering "
                                                             "tool defect and add the case to the regression corpus."}
        if failure_class == "timeout":
            action["done"] = "recorded; the candidate keeps its level; never retried at smaller bounds"
        elif failure_class == "out_of_memory":
            action["done"] = "class kept; on the Mac the ~8 GB cap stays, a rerun with more memory needs another host"
        elif failure_class == "unwinding_bound_too_small":
            action["loops"] = [g["goal"] for g in context.get("goals", []) if ".unwind." in g["goal"]
                               and g["status"] != "success"]
            action["unwind"] = context["settings"].get("unwind")
        else:
            reproduction = out / "reproduction"
            reproduction.mkdir(exist_ok=True)
            for name, path in context["reports"]:
                if name in ("cbmc_input", "crux_input", "differential_c", "differential_cxx", "replay_cxx"):
                    shutil.copyfile(path, reproduction / Path(path).name)
            if context["settings"].get("flags"):
                (reproduction / "command.txt").write_text("cbmc job.c " + " ".join(context["settings"]["flags"]) +
                                                          " --json-ui\n")
            action["minimal_reproduction"] = sorted(p.name for p in reproduction.iterdir())
            action["regression_corpus"] = "add the case (input, class, cause) to tests/fixtures/proof/regression_corpus/"
        if failure_class == "spurious_counterexample":
            action["repair"] = "never sent to counterexample-guided repair"
        path = out / "handler.json"
        path.write_text(json.dumps(action, indent=1, sort_keys=True) + "\n")
        context["reports"].append(("handler", path))
        context["log"].line(f"handler ({failure_class}): {action['handler']}")


# --- reading CBMC's output ------------------------------------------------------------------------------------

def read_outcome(result, text):
    """{verdict: proven|failed|not_proven, failure_class, why, goals, unproven, failures} from one CBMC run."""
    def outcome(verdict, failure_class, why, goals=(), unproven=(), failures=()):
        return {"verdict": verdict, "failure_class": failure_class, "why": why, "goals": list(goals),
                "unproven": list(unproven), "failures": list(failures)}
    if result.out_of_memory:
        return outcome("not_proven", "out_of_memory", "the RSS watchdog killed the job above its cap")
    if result.timed_out:
        return outcome("not_proven", "timeout", "the job ran out of its wall budget")
    try:
        messages = json.loads(text)
    except ValueError:
        messages = None
    errors = [m.get("messageText", "") for m in messages or [] if isinstance(m, dict) and m.get("messageType") == "ERROR"]
    results = next((m["result"] for m in messages or [] if isinstance(m, dict) and "result" in m), None)
    if result.exit_code < 0 or (result.exit_code not in (0, 6, 10) and results is None):
        return outcome("not_proven", "tool_crash", f"CBMC crashed (exit {result.exit_code})")
    if results is None:
        joined = "; ".join(errors) or text[-400:]
        if re.search(r"solver|SAT checker|propositional", joined, re.I):
            return outcome("not_proven", "solver_error", joined[:400])
        if result.exit_code == 6 or errors:
            return outcome("not_proven", "parse_error", joined[:400])
        return outcome("not_proven", UNCLASSIFIED, f"CBMC exited {result.exit_code} with no property results")
    goals, unproven, failures = [], [], []
    reach_ok, unwind_failed, real_failed, capacity, ghost, memory_domain = True, [], [], False, False, False
    for row in results:
        prop, status = row.get("property", ""), str(row.get("status", "")).lower()
        description = row.get("description", "")
        location = row.get("sourceLocation") or {}
        goals.append({"goal": prop, "property": description, "function": location.get("function"),
                      "status": status, "solver": None, "seconds": None})
        reach = description == tr.REACH_END or description.startswith(tr.REACH_SUMMARY)
        if reach:
            if status != "failure":
                reach_ok = False
                unproven.append(_unproven(row, "reachability"))
            continue
        if status == "success":
            continue
        unproven.append(_unproven(row, "unwinding" if ".unwind." in prop else "property"))
        if ".unwind." in prop:
            unwind_failed.append(prop)
        elif description == tr.ORACLE_CAPACITY:
            capacity = True
        elif description == proof_semantics.CAPACITY:      # ticket 27: never a refutation (S3)
            ghost = True
        elif description == proof_semantics.MEMORY_DOMAIN:
            memory_domain = True
        elif status == "failure":
            builtin = ".assertion." not in prop
            failures.append({"check": prop, "property": description, "function": location.get("function"),
                             "builtin": builtin, "oracle": _oracle(row.get("trace") or [])})
            real_failed.append(prop)
    unknown = [g for g in goals if g["status"] not in ("success", "failure")]
    if failures:
        return outcome("failed", None, f"{len(failures)} propert(ies) failed", goals, unproven, failures)
    if ghost:
        return outcome("not_proven", "ghost_capacity", f"more uncovered DX100 commands than the ghost capacity "
                       f"({proof_semantics.CAPACITY} failed)", goals, unproven)
    if memory_domain:
        return outcome("not_proven", "memory_domain",
                       "device memory overlap or a pending store at unit exit needs coverage or more precise semantics",
                       goals, unproven)
    if unwind_failed or capacity:
        why = f"unwinding assertions failed: {', '.join(unwind_failed)}" if unwind_failed else \
            "the oracle of the bounded encoding ran out (more havocked values than its capacity)"
        return outcome("not_proven", "unwinding_bound_too_small", why, goals, unproven)
    if unknown:
        return outcome("not_proven", UNCLASSIFIED, f"properties neither success nor failure: "
                       f"{sorted({g['status'] for g in unknown})}", goals, unproven)
    if not reach_ok:
        return outcome("not_proven", "vacuous_pass", "a reachability assert held: the assumptions (bounds, "
                       "preconditions or a summary's postconditions) admit no execution there", goals, unproven)
    if not any(row.get("description") == tr.REACH_END for row in results):
        return outcome("not_proven", "vacuous_pass", "no reachability assert was checked", goals, unproven)
    return outcome("proven", None, "every property holds and every reachability assert fails", goals)


def _unproven(row, kind):
    location = row.get("sourceLocation") or {}
    line = location.get("line")
    return {"property": row.get("description"), "kind": kind, "function": location.get("function"),
            "line": int(line) if str(line or "").isdigit() else None, "status": row.get("status")}


def _oracle(trace):
    """The values swdb_next() returned along a trace, in order."""
    values = []
    for step in trace:
        if step.get("stepType") == "assignment" and step.get("lhs") == "goto_symex$$return_value$$swdb_next":
            match = re.match(r"-?\d+", str((step.get("value") or {}).get("data", "")))
            values.append(int(match.group()) if match else 0)
    return values


def _inputs(stdout):
    """{name: value, array: [values]} from the replay's ` input name=value` fields."""
    found = {}
    for name, value in re.findall(r" input (\S+?)=(-?\d+)", stdout):
        if "[" in name:
            base = name.split("[")[0]
            found.setdefault(base, []).append(int(value))
        else:
            found[name] = int(value)
    return found


# --- the differential domain ------------------------------------------------------------------------------

def _domain(plan):
    """(oracle lines, sampled, summary) of the bounded domain: every size up to its bound, knobs over their legal
    range, values from a small fixed set; at most MAX_RUNS lines (a fixed-seed sample beyond that)."""
    choices, summary = [], {}
    for draw in plan.draws:
        if draw['role'] == 'whole-model-choice':
            values = [0,1,2,3,2**31-1,2**31,2**32-1]
        elif draw["role"] == "size":
            values = list(range(-1, int(draw["bound"]) + 1))
        elif draw["role"] == "knob":
            low, high = draw["range"]
            values = list(range(low, high + 1)) if high - low <= 15 else [low, low + 1, (low + high) // 2, high - 1, high]
        elif draw["role"] in ("element", "state"):        # state: proof-semantics device state (ticket 27)
            values = list(VALUES)
        else:
            values = list(VALUES) + list(SCALAR_EXTREMES)
        choices.append(values)
        key = draw["name"].split("[")[0]
        summary[key] = {"role": draw["role"], "values": values}
    total = 1
    for values in choices:
        total *= len(values)
    if total <= MAX_RUNS:
        return [list(line) for line in itertools.product(*choices)], False, summary
    rng = random.Random(22)
    return [[rng.choice(values) for values in choices] for _ in range(MAX_RUNS)], True, summary


class _Done:
    def __init__(self, returncode, stdout, stderr):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _run_domain(binary, lines, sanitized=False):
    """(result, crashed) of the native harness over every oracle line. Sanitized (ticket 25): a run that ends in an
    AddressSanitizer report prints `run K: sanitizer` and the harness resumes at the next line, so one run's
    undefined behavior neither hides the other runs nor counts as agreement; `crashed` holds those run indexes."""
    if not sanitized:
        done = subprocess.run([binary], input="".join(" ".join(map(str, line)) + "\n" for line in lines),
                              capture_output=True, text=True, timeout=600)
        return done, set()
    rows, crashed, start = [], set(), 0
    env = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0:abort_on_error=0"}
    while start < len(lines):
        feed = "".join(" ".join(map(str, line)) + "\n" for line in lines[start:])
        done = subprocess.run([binary], input=feed, capture_output=True, text=True, timeout=600, env=env)
        complete = [row for row in done.stdout.splitlines() if re.search(r" end=\S+$", row)]
        rows += [re.sub(r"^run \d+:", f"run {start + k}:", row) for k, row in enumerate(complete)]
        if done.returncode == 0 and len(complete) == len(lines) - start:
            break
        if "AddressSanitizer" not in done.stderr:
            return _Done(done.returncode or 1, "\n".join(rows) + "\n", done.stderr), crashed
        index = start + len(complete)
        rows.append(f"run {index}: sanitizer")
        crashed.add(index)
        start = index + 1
    return _Done(0, "\n".join(rows) + "\n", ""), crashed


def _compile(clang, side, source, binary, flags):
    compiler = clang.command[0]
    if side == "c":
        compiler = compiler.replace("clang++", "clang")
        std = ["-x", "c", "-std=gnu11"]
    else:
        std = ["-x", "c++", "-std=gnu++17"]
    done = subprocess.run([compiler, *std, *flags, str(source), "-o", str(binary)], capture_output=True, text=True,
                          timeout=300)
    if done.returncode != 0:
        errors = [line for line in done.stderr.splitlines() if "error" in line]
        return "; ".join(errors[:3]) or done.stderr[-400:]
    return None


# --- the code: the C lowering and the C++ of the same functions -----------------------------------------------

PROTOTYPE = re.compile(r"^(static\s+)?(.+?)\b([A-Za-z_]\w*)\((.*)\)$")


class Code:
    """The C lowering of a proof unit plus the C++ text of the same functions and globals."""

    def __init__(self, lowering, source, defines, model=None):
        self.lowering, self.source, self.defines = lowering, Path(source), tuple(defines)
        self.model = model                             # ticket 27: the proof semantics' C model, or None
        self.text = lowering.text
        self.window_cxx = {}
        self.functions = [a["function"] for a in lowering.anchors if a["kind"] == "contract"]
        self.prototypes = {}
        lines = self.text.splitlines()
        for anchor in (a for a in lowering.anchors if a["kind"] == "contract"):
            self.prototypes[anchor["function"]] = lines[anchor["line"]].rstrip(" {")
        head = lowering.declaration.rstrip("\n").splitlines()
        self.globals = []                              # (name, scalar C type or None, declaration text)
        for line in head[len(c_lowering.HEADERS):-1]:
            if line.startswith(("typedef ", "struct ", "#")):     # types (ticket 24 classes, ticket 25 models)
                continue
            match = re.match(r"^(static\s+)?(.+?)\b([A-Za-z_]\w*)\s*((?:\[[^\]]*\])*)\s*(=.*)?;$", line)
            if match:
                self.globals.append((match.group(3), None if match.group(4) else match.group(2).strip(), line))
        self.scalar_globals = {name for name, ctype, _line in self.globals if ctype}

    @property
    def c_sha256(self):
        return hashlib.sha256(self.text.encode()).hexdigest()

    def cxx_defines(self):
        """The build constants as compiler flags: the C++ cut is raw source (the C lowering is already preprocessed)."""
        return [f"-D{define}" for define in self.defines]

    def apply_fault(self, path):
        """A scripted fault (tests): `replace: [[old, new], ...]` applied to the C lowering's text only."""
        if not path:
            return
        for old, new in (yamlio.load(Path(path)) or {}).get("replace") or []:
            if old not in self.text:
                raise AdapterError(f"lowering fault {path}: {old!r} is not in the C lowering")
            self.text = self.text.replace(old, new, 1)

    def interface(self, function):
        match = PROTOTYPE.match(self.prototypes[function])
        if not match:
            raise AdapterError(f"cannot read the prototype of {function}: {self.prototypes[function]}")
        params = []
        for part in [p.strip() for p in match.group(4).split(",") if p.strip() and p.strip() != "void"]:
            found = re.match(r"^(.*?)\b([A-Za-z_]\w*)$", part)
            ctype = found.group(1).strip()
            params.append((found.group(2), ctype, "*" in ctype))
        return tr.Interface(function=function, returns=match.group(2).strip(), parameters=tuple(params),
                            globals=tuple((name, ctype) for name, ctype, _line in self.globals))

    def uses(self, name):
        """Whether every use of global `name` in the function bodies is an operand of a comparison."""
        body = "\n".join(line for line in self.text.splitlines()
                         if line.startswith("  ") and "swdb-anchor" not in line)
        other = []
        for match in re.finditer(rf"\b{re.escape(name)}\b", body):
            before, after = body[:match.start()].rstrip(), body[match.end():].lstrip()
            if re.match(r"(==|!=|<=|>=|<(?!<)|>(?!>))", after) or \
                    re.search(r"(==|!=|<=|>=|(?<![<-])<|(?<![>-])>)$", before):
                continue
            other.append(body[max(0, match.start() - 20):match.end() + 20].strip())
        return {"compared_only": not other, "other": other[:2]}

    def c_text(self, stubs=None):
        """The proof semantics' C model (if the unit calls into one), then the C lowering, with each summarized
        callee's definition replaced by its stub."""
        return (self.model.c_text if self.model is not None else "") + self._c_lowering_text(stubs)

    def _c_lowering_text(self, stubs):
        if not stubs:
            return self.text
        lines, out, skip = self.text.splitlines(), [], None
        for k, line in enumerate(lines):
            if skip is not None:
                if line == "}":
                    out.append(stubs[skip].rstrip("\n"))
                    skip = None
                continue
            match = c_lowering.ANCHOR_LINE.match(line)
            if match and match.group(1).endswith(".contract") and match.group(1)[:-len(".contract")] in stubs:
                skip = match.group(1)[:-len(".contract")]
                out.append(line)
                continue
            out.append(line)
        return "\n".join(out) + "\n"

    def cxx_text(self, stubs=None):
        """The C++ text of the lowered functions and globals, cut from the source by clang's source ranges."""
        stubs = stubs or {}
        if self.lowering.whole_source is not None:
            from swdb import dx100_checked_native
            if stubs:
                raise AdapterError('whole checked source cannot substitute C++ summary bodies')
            return self.model.c_text + dx100_checked_native.view(self.lowering.whole_source)['cxx_text']
        tool = c_lowering.locate()
        data = self.source.read_bytes()
        parts = [self.model.c_text] if self.model is not None else []
        parts += [f"/* C++ of {self.lowering.function} cut from {self.source.name} by the CBMC adapter. */",
                  "#include <cstddef>", "#include <cstdint>", "#include <stdexcept>", "#include <utility>", "#include <vector>"]
        for name, _ctype, _line in self.globals:
            parts.append(self._cut(tool, data, name, {"VarDecl"}) + ";")
        parts += [f"{self.prototypes[name]};" for name in self.functions]
        for name in self.functions:
            parts.append(stubs[name].rstrip("\n") if name in stubs else self.window_cxx[name]
                         if name in self.window_cxx else self._cut(tool, data, name, {"FunctionDecl"}))
        return "\n".join(parts) + "\n"

    def _cut(self, tool, data, name, kinds):
        nodes = c_lowering._named(c_lowering._dump(tool, self.source, name, (), self.defines), name, kinds)
        nodes = [n for n in nodes if kinds != {"FunctionDecl"} or
                 any(c.get("kind") == "CompoundStmt" for c in n.get("inner", []))]
        if len(nodes) != 1:
            raise AdapterError(f"cannot cut the C++ of {name} from {self.source.name} (found {len(nodes)} definitions)")
        begin, end = nodes[0]["range"]["begin"], nodes[0]["range"]["end"]
        if "includedFrom" in begin or "offset" not in begin or "offset" not in end:
            raise AdapterError(f"{name} is not defined in {self.source.name} itself")
        start, stop = begin["offset"], end["offset"] + end.get("tokLen", 0)
        sites = [p for p in self.lowering.probes if start <= p["begin"] and p["end"] <= stop]
        return _probed(data, start, stop, sites).decode()


# --- helpers ---------------------------------------------------------------------------------------------------

def _probed(data, start, stop, sites):
    """data[start:stop] with each hazard-probe site (C++ byte range) wrapped in the probe the C lowering placed there:
    the same macro and ID, so a probe refutation on the C lowering replays at the same probe on the C++."""
    out, at = [], start
    top = [s for s in sorted(sites, key=lambda s: (s["begin"], -s["end"]))
           if not any(o is not s and o["begin"] <= s["begin"] and s["end"] <= o["end"] and
                      (o["begin"], o["end"]) != (s["begin"], s["end"]) for o in sites)]
    for site in top:
        if site["begin"] < at:
            continue
        inner = [s for s in sites if s is not site and site["begin"] <= s["begin"] and s["end"] <= site["end"]]
        out.append(data[at:site["begin"]])
        macro = b"SWDB_TILE_READ" if site["access"] == "read" else b"SWDB_TILE_WRITE"
        out.append(b"(*" + macro + b"(&(" + _probed(data, site["begin"], site["end"], inner) + b'), "' +
                   site["id"].encode() + b'"))')
        at = site["end"]
    out.append(data[at:stop])
    return b"".join(out)


def logic_of(library):
    """The logic-library definitions a job's formal halves may call (ticket 23): every library/logic/*.acsl file."""
    from swdb.formal_frame import logic_files
    root = getattr(library, "root", None)
    files = logic_files(Path(root), library) if root is not None else {}
    return tr.Logic({entry: path.read_text() for entry, path in files.items()})


def stub_fault():
    """Clause names a scripted fault drops from every generated stub (SWDB_CBMC_STUB_FAULT, tests only)."""
    path = os.environ.get("SWDB_CBMC_STUB_FAULT")
    if not path:
        return ()
    return tuple((yamlio.load(Path(path)) or {}).get("drop") or ())


def _sizes(bounds):
    """{parameter: bound} from the job's bounds; threads must be 1 (threads > 1 is CIVL's, ticket 46)."""
    if not isinstance(bounds, dict):
        raise AdapterError("the cbmc adapter needs --bounds: {\"threads\": 1, \"<integer parameter>\": <size bound>}")
    if bounds.get("threads") != 1:
        raise AdapterError(f"the cbmc adapter checks one thread (threads = 1), not threads = {bounds.get('threads')} "
                           "(threads > 1: CIVL and GenMC, tickets 46 and 47)")
    sizes = {}
    for name, value in bounds.items():
        if name == "threads":
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AdapterError(f"bound {name} must be a size (an integer >= 0) for a bounded job, not {value!r}")
        sizes[name] = value
    return sizes


class _Log:
    def __init__(self, path):
        self.path = Path(path)

    def line(self, text):
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(text.rstrip("\n") + "\n")


from swdb import proof as _proof_module      # noqa: E402  (registered here, so either module may be imported first)
_proof_module.ADAPTERS[NAME] = CbmcAdapter
from swdb import crux_adapter as _crux, bounded_chain as _chain   # noqa: E402,F401  (ticket 23: imported after this
#                                                                  module is complete; each registers itself)
