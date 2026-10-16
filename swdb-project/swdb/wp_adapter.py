"""The real WP adapter: Frama-C/WP 33.0 on the C lowering of a candidate artifact's proof unit.

Created: 2026-10-14 ET (Probata proof of concept ticket 21, the A2 tracer). Design: formal-verification
map spec ("Verifier lineup and order": unbounded verifier, solver portfolio, pinned versions, failure
classes; "Proof-hint loop": anchors, frozen flags, verdict reading); map 11 items 1, 3, 8, 9, 10; 13
items 4, 6, 7; 16 items 3, 6. Format: docs/reference/format-v0.4-c-lowering-wp.md.

One job (`swdb prove --adapter wp`):
1. Find the C++ file of the candidate artifact's tree that defines the function; lower it
   (`swdb.c_lowering`). Outside the core subset: not proven, `unsupported_construct`; unparsable C++:
   `parse_error`.
2. Build WP's input: the C lowering with the contract's per-candidate formal halves at the unit's
   `contract` anchor, the logic-library files they use at `ghost.globals`, and the hint set (`--hint-file`,
   hint records) merged at its anchors, only when the proof hint check accepts it (ticket 35,
   swdb.hint_check); a rejected set never reaches WP, which then runs without hints, and the record lists
   every rejected hint with its rule.
3. Check the installed tools against the pinned method version's lineup (Frama-C/WP, the three solvers,
   clang, the C lowering tool's ID and sha256); a mismatch runs nothing.
4. Run Frama-C/WP with the frozen settings in a fresh process in the job's scratch folder (TMPDIR too, so
   no WP or Why3 scratch survives), under the RSS watchdog (8 GiB) and the job's wall budget.
5. Minimal verdict reader: proven only when every property of this run's per-property report
   (`-report-csv`) is `Valid` and every goal of its per-goal report (`-wp-report-json`) passed; WP's
   consolidated summary line is never read. Ticket 36 owns the full reading rule.
   Ticket 23 (2026-10-14 ET): a callee that a library entry summarizes (its `proof_unit.function`, with
   `once: self` formal halves) gets that entry's formal halves at its own `<callee>.contract` anchor: the ACSL
   form of the summary, the third of the three summary forms (WP uses the contract at the call).
6. Every outcome maps to a class of vocabulary `proof_failure_classes`, and that class's handler runs
   (`handler.json` in the runs folder). An outcome with no class reports `unclassified_wp_outcome`, which is
   not in the vocabulary, so `swdb prove` stops the batch. WP's "not proven" is never a refutation.
"""

import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from dataclasses import replace
from pathlib import Path

from swdb import artifacts, c_lowering, cpu_memory_admission, framac, heap_model_view, helper_windows, nested_entry_reads, hint_check, paths, proof_semantics, proof_setup, rss_watchdog, standard_model_view, standard_range_calls, standard_range_model, std_models, terminal_release, vector_ownership, vocab, wp_pointer_bounds
from swdb.proof import MODEL_PREFIX, AdapterError, Verdict

NAME = "wp"
PROVERS = ("z3", "cvc5", "alt-ergo")   # required tools; invocation order comes from the method
WHY3_NAMES = {"Alt-Ergo": "alt-ergo", "Z3": "z3", "CVC5": "cvc5"}
FROZEN = (("-wp-cache", "none"), ("-wp-model", "+real"), ("-rte-initialized", "@all"))
MACHDEP = ("-machdep", "x86_64")
ALLOCATION_MODEL = "swdb_alloc_"   # new[] success is assumed; an ordinary release still needs lifetime support
DEFAULT_WALL_SECONDS = 3600
DEFAULT_CAP_BYTES = 8 * 2**30                    # O9: the ~8 GB RSS watchdog
UNCLASSIFIED = "unclassified_wp_outcome"         # not a failure class: stops the batch (11 item 9)
SOURCE_SUFFIXES = (".cc", ".cpp", ".cxx", ".c")
SENTENCES = {
    "c_lowering": "The C lowering tool (swdb lower, version {version}) lowers the C++ proof unit to C that behaves the "
                  "same; WP proves the C lowering, not the C++.",
    "clang": "clang {version} parses the C++ proof unit correctly for the C lowering tool.",
    "frama-c-wp": "Frama-C/WP {version} generates only sound proof obligations for the C lowering under its memory "
                  "model and the x86_64 machdep.",
    "alt-ergo": "Alt-Ergo {version} answers valid only for valid proof obligations.",
    "z3": "Z3 {version} answers valid only for valid proof obligations.",
    "cvc5": "CVC5 {version} answers valid only for valid proof obligations.",
}


class WpAdapter:
    """`swdb prove --adapter wp`: one WP job per call (records via swdb.proof)."""
    name = NAME
    real = True                                   # swdb prove takes the machine-wide verifier lock

    def __init__(self, library, contract, method, hints=None, defines=(), records=None):
        self.library, self.contract, self.method = library, contract, method
        self.records = records
        self.hints_path = Path(hints) if hints else None
        try:
            self.hints = hint_check.read_hint_set(self.hints_path) if hints else []
        except hint_check.HintSetError as exc:
            raise AdapterError(str(exc)) from None
        self.defines = tuple(defines)
        proof_semantics.check_defines(self.defines)

    def _entry_view_hints(self, job):
        """Entry scope is unchanged by the independently checked source views."""
        return all(hint.get("anchor") == f"{job.unit.function}.entry" and
                   hint.get("kind") in {"assert", "ghost"} for hint in self.hints)

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        if script is not None:
            raise AdapterError("the wp adapter takes no --script (one WP job per call)")
        return cls(library, contract, method, hints=getattr(args, "hint_file", None),
                   defines=getattr(args, "define", None) or (), records=getattr(args, "records", None))

    # --- the job --------------------------------------------------------------------------------
    def run(self, job):
        started = time.monotonic()
        run_dir = Path(job.log).parent
        wp_dir = run_dir / "wp"
        wp_dir.mkdir(exist_ok=True)
        log = _Log(job.log)
        log.line(f"adapter: wp\nunit: {job.unit.candidate} {job.unit.function}\ncontract: {self.contract}")
        tools = self._tools()                     # missing or mismatched tools: no job, no record
        context = {"job": job, "wp_dir": wp_dir, "log": log, "reports": [], "tools": tools,
                   "functions": {job.unit.function}, "extra_flags": [], "pins": {},
                   "started_monotonic": started}
        if self.contract.startswith(MODEL_PREFIX):            # ticket 24: one C model against its own contract
            text = c_lowering.model_text(job.unit.function)
            if text is None:
                raise AdapterError(f"the C lowering has no C model {job.unit.function}")
            if job.unit.function.startswith(("std_vector_", "std_pair_")):
                context["pins"]["std_models"] = std_models.identity()
            from swdb import vector_reallocation_model
            if job.unit.function in vector_reallocation_model.MEMBERS:
                domain = vector_reallocation_model.certificate(job.unit.function)
                source_path = wp_dir / "vector-reallocation-v3.c"
                source_path.write_text(text)
                original_path = wp_dir / "vector-reallocation-v2.original.c"
                original_path.write_text(std_models.model_text(domain["original_member"]))
                domain_path = wp_dir / "vector-reallocation-v3.json"
                domain_path.write_text(json.dumps(domain, indent=2, sort_keys=True) + "\n")
                context["pins"]["vector_reallocation_model"] = vector_reallocation_model.identity()
                context["settings"] = {"tool": "frama-c-wp", "flags": tools["flags"],
                                       "verifier_launched": False, "vector_reallocation_domain": domain}
                context["reports"] += [("vector_reallocation_model", source_path),
                                       ("vector_reallocation_domain", domain_path),
                                       ("vector_reallocation_original", original_path)]
                from swdb import vector_reallocation_vcs
                draft = wp_dir / "vector-reallocation-obligations"
                plan = vector_reallocation_vcs.prepare(job.unit.function, draft)
                vector_reallocation_vcs.check(job.unit.function, draft)
                context["reports"] += [("vector_reallocation_obligations", draft / "manifest.json"),
                    ("vector_reallocation_semantics", draft / plan["semantics"]["path"])]
                context["reports"] += [("vector_reallocation_staged_" + name,
                                        draft / pin["path"]) for name,pin in plan["sources"].items()]
                context["reports"] += [("vector_reallocation_vc_" + row["id"], draft / row["path"])
                                       for row in plan["obligations"]]
                return heap_model_view.prove(job, self, context)
            if job.unit.function in heap_model_view.MEMBERS:
                return heap_model_view.prove(job, self, context)
            if re.search(r"\b(?:allocates|frees)\b|\\(?:fresh|freeable)\b", text):
                return self._not_proven("unsupported_construct",
                    "WP 33.0 does not model allocation lifetime; this C model needs allocates/frees support", context)
            if job.unit.function == "std_vector_int_at":
                try:
                    view = standard_model_view.wp_view(job.unit.function, text, wp_dir)
                    standard_model_view.check_view(job.unit.function, view, wp_dir)
                except standard_model_view.Refused as exc:
                    return self._not_proven("unsupported_construct", str(exc), context)
                original = wp_dir / "standard_model_original.c"
                original.write_text("\n".join([*c_lowering.HEADERS, text]) + "\n")
                certificate = wp_dir / "standard_model_view.json"
                certificate_text = json.dumps(view.certificate, indent=2) + "\n"
                certificate.write_text(certificate_text)
                context["standard_model_view"] = {"view": view, "original_path": original,
                    "original_text": original.read_text(), "certificate_path": certificate,
                    "certificate_text": certificate_text}
                context["pins"].update(view.pins)
                context.setdefault("assumed", []).append({"kind": "trusted_tool",
                    "reference": standard_model_view.identity(),
                    "sentence": "The exact audited pure defensive-at abort guard is omitted only in the WP view; "
                                "the unchanged contract must prove its negation as at_guard_false. "
                                "The original/native/CBMC model and the input premises are unchanged."})
                context["reports"] += [("standard_model_original", original),
                                       ("standard_model_view_certificate", certificate)]
                text = view.text
            if job.unit.function == standard_range_model.NAME:
                try:
                    range_view = standard_range_model.wp_view(job.unit.function, text, wp_dir)
                    standard_range_model.check_view(job.unit.function, range_view, wp_dir)
                except standard_range_model.Refused as exc:
                    return self._not_proven("unsupported_construct", str(exc), context)
                original = wp_dir / "standard_range_original.c"
                original.write_text("\n".join([*c_lowering.HEADERS, text]) + "\n")
                certificate = wp_dir / "standard_range_model.json"
                certificate_text = json.dumps(range_view.certificate, indent=2) + "\n"
                certificate.write_text(certificate_text)
                context["standard_range_model"] = {"view":range_view, "original_path":original,
                    "original_text":original.read_text(), "certificate_path":certificate,
                    "certificate_text":certificate_text}
                context["pins"].update(range_view.pins)
                context.setdefault("assumed", []).append({"kind":"trusted_tool",
                    "reference":standard_range_model.identity(),
                    "sentence":"The checked std_copy_int body proof is qualified by explicit live typed input/output "
                               "array ranges. This is standard-library valid-range semantics, not a theorem for "
                               "arbitrary pointer parameters; every caller must discharge the typed range domain."})
                context["reports"] += [("standard_range_original",original),
                                       ("standard_range_model_certificate",certificate)]
                text = range_view.text
            input_path = wp_dir / "wp_input.c"
            context["pointer_bounds_model_source"] = "\n".join([*c_lowering.HEADERS, text]) + "\n"
            try:
                context["wp_expected_text"], context["pointer_bounds_report"] = wp_pointer_bounds.model_view(
                    context["pointer_bounds_model_source"], job.scratch,
                    qualified=(context.get("standard_range_model") or {}).get("view"))
            except wp_pointer_bounds.Refused as exc:
                context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False,
                    "pointer_bounds": {"verdict": "refused", "reason": str(exc), "check": wp_pointer_bounds.identity()}}
                return self._not_proven("unsupported_construct", str(exc), context)
            input_path.write_text(context["wp_expected_text"])
            context["reports"].append(("wp_input", input_path))
            context["functions"] = set(context["pointer_bounds_report"]["functions"])
            context["extra_flags"] = ["-wp-fct=" + ",".join(sorted(context["functions"]))]
            return self._wp(job, input_path, context)
        entry = self.library.get(self.contract) or {}
        if (entry.get('proof_unit') or {}).get('correctness_policy') is not None:
            if job.unit.candidate is not None or job.unit.correctness_policy!=(entry.get('proof_unit') or {}).get('correctness_policy'):
                return self._not_proven('unsupported_construct','partial source admission requires its distinct original partial summary unit',context)
        unit = entry.get("proof_unit") or {}
        summary_job = job.unit.candidate is None
        source = _unit_source(Path(job.unit.tree), job.unit.function)
        log.line(f"source: {source.relative_to(job.unit.tree)}")
        summaries = self._summarized()
        covered = proof_semantics.covered_names(self.library)
        semantics_options = proof_semantics.lowering_options(self.library)
        semantics_options.setdefault("semantics", {})["array_origins"] = wp_pointer_bounds.semantic_origins(self.library, self.defines)
        semantics_options["semantics"]["array_call_policies"] = proof_semantics.array_call_policies(self.library, self.defines)
        semantics_options["semantics"]["audited_imports"] = proof_semantics.imported_call_policies(self.library, self.defines)
        summaries.update(semantics_options.pop("summaries", {}))
        context["covered"] = covered
        try:
            source_kwargs = {"defines": self.defines,
                             "summaries": {f: e for f, e in summaries.items() if f != job.unit.function},
                             "array_domains": unit.get("array_domains"),
                             "array_domain_contract": {"id": self.contract, "sha256": job.unit.contract_sha256},
                             **semantics_options}
            lowering = c_lowering.lower(source, job.unit.function, **source_kwargs)
            from swdb import stdlib_source_admission
            context.setdefault("settings", {}).update(tool="frama-c-wp", flags=[], verifier_launched=False)
            provenance_problem = stdlib_source_admission.bind(context, lowering, source, defines=self.defines)
            if provenance_problem:
                context["settings"].update(verifier_launched=False)
                return self._not_proven("unsupported_construct", provenance_problem, context)
            original_lowering = lowering
            try:
                wp_pointer_bounds.check(lowering)
                needs_origins = False
            except wp_pointer_bounds.Refused:
                needs_origins = True
            has_helpers = any(a["kind"] == "contract" and a["function"] != job.unit.function
                              for a in lowering.anchors)
            if needs_origins and has_helpers and proof_semantics.called(lowering, covered):
                if self.hints_path and not self._entry_view_hints(job):
                    raise helper_windows.Refused("helper views admit only assertions/ghost hints at the original unit entry")
                imported = {name: {"id": policy["model"]["entry"],
                                   "sha256": policy["model"]["entry_sha256"]}
                            for name, policy in semantics_options["semantics"]["audited_imports"].items()}
                helper_options = {"defines": self.defines, "imported_calls": imported}
                view = helper_windows.prepare(source, job.unit.function, **helper_options,
                                              scratch=wp_dir / "helper-source")
                if view:
                    helper_windows.check_view(source, job.unit.function, view, **helper_options)
                    effective_kwargs = {**source_kwargs, "includes": view.includes}
                    lowering = c_lowering.lower(view.path, job.unit.function, **effective_kwargs)
                    original_path, original_anchors = original_lowering.write(wp_dir / "helper-original")
                    certificate_path = wp_dir / "helper_windows.json"
                    certificate_text = json.dumps(view.certificate, indent=2) + "\n"
                    certificate_path.write_text(certificate_text)
                    helper_pins = {**view.pins,
                        "helper_original_lowering": {"id": original_path.name, "sha256": original_lowering.sha256},
                        "helper_original_source": {"id": source.name, "sha256": original_lowering.source_sha256},
                        "helper_view_source": {"id": view.path.name, "sha256": lowering.source_sha256}}
                    context["helper_windows"] = {"source": source, "view": view, "options": helper_options,
                        "original_lowering": original_lowering, "original_kwargs": source_kwargs,
                        "effective_kwargs": effective_kwargs, "effective_lowering": lowering, "original_path": original_path,
                        "original_source_text": source.read_text(), "certificate_path": certificate_path,
                        "certificate_text": certificate_text, "pins": helper_pins}
                    context["pins"].update(helper_pins)
                    context["reports"] += [("helper_original_source", source),
                        ("helper_original_lowering", original_path), ("helper_original_anchors", original_anchors),
                        ("helper_view_source", view.path), ("helper_windows_certificate", certificate_path)]
                    context["pointer_source_plan"] = {"source": str(view.path), "kwargs": effective_kwargs}
            try:
                wp_pointer_bounds.check(lowering)
                nested_needed = False
            except wp_pointer_bounds.Refused:
                nested_needed = bool(unit.get("array_domains"))
            if nested_needed:
                if self.hints_path and not self._entry_view_hints(job):
                    raise nested_entry_reads.Refused("nested views admit only assertions/ghost hints at the original unit entry")
                nested_source = context.get("helper_windows", {}).get("view")
                nested_source = nested_source.path if nested_source else source
                nested_kwargs = context.get("helper_windows", {}).get("effective_kwargs", source_kwargs)
                nested_options = {"defines": self.defines, "includes": nested_kwargs.get("includes", ()),
                                  "entry_windows": lowering.pointer_bounds.get("entry_windows", {})}
                nested_view = nested_entry_reads.prepare(nested_source, job.unit.function, **nested_options,
                                                        scratch=wp_dir / "nested-source")
                if nested_view:
                    nested_entry_reads.check_view(nested_source, job.unit.function, nested_view, **nested_options)
                    before_nested = lowering
                    effective_kwargs = {**source_kwargs, "includes": nested_view.includes}
                    lowering = c_lowering.lower(nested_view.path, job.unit.function, **effective_kwargs)
                    original_path, original_anchors = before_nested.write(wp_dir / "nested-original")
                    certificate_path = wp_dir / "nested_entry_reads.json"
                    certificate_text = json.dumps(nested_view.certificate, indent=2) + "\n"
                    certificate_path.write_text(certificate_text)
                    nested_pins = {**nested_view.pins,
                        "nested_read_original_lowering": {"id": original_path.name, "sha256": before_nested.sha256},
                        "nested_read_original_source": {"id": nested_source.name, "sha256": before_nested.source_sha256},
                        "nested_read_view_source": {"id": nested_view.path.name, "sha256": lowering.source_sha256}}
                    context["nested_entry_reads"] = {"source": nested_source, "view": nested_view,
                        "options": nested_options, "original_lowering": before_nested,
                        "original_kwargs": nested_kwargs, "effective_kwargs": effective_kwargs,
                        "original_path": original_path, "original_source_text": nested_source.read_text(),
                        "certificate_path": certificate_path, "certificate_text": certificate_text, "pins": nested_pins}
                    context["pins"].update(nested_pins)
                    context["reports"] += [("nested_original_source", nested_source),
                        ("nested_original_lowering", original_path), ("nested_original_anchors", original_anchors),
                        ("nested_view_source", nested_view.path), ("nested_entry_reads_certificate", certificate_path)]
                    context["pointer_source_plan"] = {"source": str(nested_view.path), "kwargs": effective_kwargs}
            if (unit.get("array_domains") or (lowering.pointer_bounds or {}).get("owner") or
                    (lowering.pointer_bounds or {}).get("member_windows") or
                    any(row.get("kind") in {"call", "producer", "import", "standard_range_call"} for row in lowering.pointer_bounds.get("sites", []))):
                context.setdefault("pointer_source_plan", {"source": str(source), "kwargs": source_kwargs})
        except (helper_windows.Refused, nested_entry_reads.Refused) as exc:
            context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False,
                                   "helper_windows": {"verdict": "refused", "reason": str(exc)}}
            return self._not_proven("unsupported_construct", str(exc), context)
        except c_lowering.Unsupported as exc:
            return self._not_proven("unsupported_construct", str(exc), context)
        except c_lowering.ParseError as exc:
            return self._not_proven("parse_error", str(exc), context)
        except c_lowering.LoweringError as exc:
            raise AdapterError(str(exc)) from None
        problem = std_models.method_problem(self.method, lowering)
        if problem:
            raise AdapterError(problem)
        lowering_tool = c_lowering.identity()["c_lowering"]
        context["assumed"] = std_models.assumptions(lowering, tools["identities"]["clang"][2], lowering_tool)
        if context.get("helper_windows"):
            view = context["helper_windows"]["view"]
            context["assumed"].append({"kind": "trusted_tool", "reference": helper_windows.identity(),
                                       "sentence": view.assumption["text"]})
        if context.get("nested_entry_reads"):
            nested_view = context["nested_entry_reads"]["view"]
            context["assumed"].append({"kind": "trusted_tool", "reference": nested_entry_reads.identity(),
                                       "sentence": nested_view.assumption["text"]})
        context["pins"].update(std_models.pins(lowering))
        if lowering.std_models:
            probe = subprocess.run([*c_lowering.locate().command, "-dM", "-E", "-x", "c++",
                                    "-std=gnu++17", "-include", "vector", "-"],
                                   input="", capture_output=True, text=True, timeout=60)
            if probe.returncode != 0 or not re.search(r"^#define _LIBCPP_VERSION 220108$", probe.stdout, re.M):
                return self._not_proven("unsupported_construct",
                    "the standard models require libc++ 22.1.8 (_LIBCPP_VERSION 220108); "
                    "the selected clang uses an unmatched standard library", context)
        dependency_lowering = lowering
        if any(name == "swdb_free" or name.startswith("swdb_alloc_delete_array_") for name in lowering.models):
            placement = {"once": "self"} if summary_job else "per_candidate"
            formal_texts = [c["acsl"]["text"].strip() for c in entry.get("clauses", [])
                            if isinstance(c, dict) and c.get("acsl") and c.get("proof_placement") == placement]
            try:
                view = terminal_release.wp_view(lowering, formal_texts, self.hints)
                terminal_release.check_view(lowering, view, formal_texts, self.hints)
            except terminal_release.Refused as terminal_error:
                try:
                    if any(c.get("acsl", {}).get("uses") for c in entry.get("clauses", []) if isinstance(c, dict)):
                        raise vector_ownership.Refused("logic-library imports are outside the scalar frame projection")
                    view = vector_ownership.wp_view(lowering, source, formal_texts, self.hints)
                    vector_ownership.check_origins(lowering, source, view, formal_texts, self.hints)
                except vector_ownership.Refused as exc:
                    return self._not_proven("unsupported_construct",
                        "WP 33.0 does not model allocation lifetime; reachable free/delete or vector growth needs "
                        f"a checked view; terminal-release check: {terminal_error}; vector ownership: {exc}", context)
                context["vector_ownership"] = {"view": view, "source": source, "formal_texts": formal_texts}
                context["assumed"].extend(view.assumptions)
            else:
                context["terminal_release"] = {"view": view, "formal_texts": formal_texts}
                context["assumed"].append(view.assumption)
            dependency_lowering = replace(lowering, models=view.models)
            context["pins"].update(view.pins)
        if unit.get("function") not in (None, job.unit.function):
            raise AdapterError(f"contract {self.contract} states the proof unit {unit.get('function')}, not "
                               f"{job.unit.function}")
        c_path, anchors_path = lowering.write(wp_dir)
        context["reports"] += [("c_lowering", c_path), ("anchors", anchors_path)]
        context["c_lowering"] = {"id": c_path.name, "sha256": lowering.sha256}
        if context.get("terminal_release"):
            terminal = context["terminal_release"]
            terminal["path"] = wp_dir / "terminal_release_view.c"
            terminal["path"].write_text(terminal["view"].text)
            context["reports"].append(("terminal_release_view", terminal["path"]))
        if context.get("vector_ownership"):
            owner = context["vector_ownership"]
            owner["path"] = wp_dir / "vector_ownership_view.c"
            owner["path"].write_text(owner["view"].text)
            context["reports"].append(("vector_ownership_view", owner["path"]))
            owner["contract_path"] = wp_dir / "vector_ownership_contracts.json"
            owner["contract_text"] = json.dumps({"source": owner["formal_texts"],
                                                "view": owner["view"].formal_text}, indent=2) + "\n"
            owner["contract_path"].write_text(owner["contract_text"])
            context["reports"].append(("vector_ownership_contracts", owner["contract_path"]))
        called = proof_semantics.called(lowering, covered)
        if called:                                  # ticket 27: the WP form of the proof semantics
            entries = sorted({covered[name] for name in called})
            if len(entries) != 1:
                raise AdapterError(f"{job.unit.function} calls into more than one proof semantics: {', '.join(entries)}")
            sha = artifacts.file_hash(self.library.files[entries[0]])
            context["semantics"] = {"id": entries[0], "sha256": sha, "calls": called}
            context["semantics_settings"] = {
                "id": entries[0], "calls": called,
                "probes": [{k: p[k] for k in ("id", "function", "access", "line")} for p in lowering.probes]}
            if proof_semantics.instance_bindings(lowering):
                context['semantics_settings']['instances'] = proof_semantics.instance_bindings(lowering)
            from swdb import dx100_size_source
            if dx100_size_source.bindings(lowering):
                context['semantics_settings']['source_definitions'] = dx100_size_source.bindings(lowering)
            from swdb import dx100_stream_source
            if dx100_stream_source.bindings(lowering):
                context['semantics_settings']['source_definitions'] = dx100_stream_source.bindings(lowering)
                context['semantics_settings']['termination_policy'] = 'conditional normal return; no hardware liveness'
                context['semantics_settings']['source_refinement'] = 'owned TCB correspondence; all-schedule refinement and contract/body agreement unverified'
            log.line(f"proof semantics: {entries[0]} (sha256 {sha}); calls {', '.join(called)}; "
                     f"{len(lowering.probes)} hazard probe(s)")
        refusal = cpu_memory_admission.check(lowering, covered)
        if refusal:
            context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False,
                                   "proof_semantics_admission": refusal}
            return self._not_proven("unsupported_construct",
                "ordinary CPU memory interference with DX100 commands needs ticket 28's memory-hazard probes", context)
        try:
            if (lowering.pointer_bounds or {}).get("owner") and not context.get("vector_ownership"):
                raise wp_pointer_bounds.Refused("closed-owner source registry requires its independently checked view")
            wp_pointer_bounds.check(lowering)
        except wp_pointer_bounds.Refused as exc:
            context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False,
                "pointer_bounds": {"verdict": "refused", "reason": str(exc), "check": wp_pointer_bounds.identity()}}
            return self._not_proven("unsupported_construct", str(exc), context)
        domain_callees = [row["name"] for row in lowering.summaries
                          if ((self.library.get(row["summary"]) or {}).get("proof_unit") or {}).get("array_domains")]
        if domain_callees:
            context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False, "pointer_bounds": {"verdict": "refused",
                "reason": "imported array-window summaries require checked caller-domain discharge: " + ", ".join(domain_callees)}}
            return self._not_proven("unsupported_construct", context["settings"]["pointer_bounds"]["reason"], context)
        from swdb import summary_bindings
        context['source'] = (context.get("nested_entry_reads") or context.get("helper_windows") or {}).get("view")
        context['source'] = context['source'].path if context['source'] else source
        try:
            contracts = self._dependencies(dependency_lowering, context)
        except (summary_bindings.Refused, standard_range_model.Refused) as exc:
            settings = context.setdefault('settings', {})
            settings.setdefault('tool', 'frama-c-wp')
            settings.setdefault('flags', [])
            settings.update(verifier_launched=False)
            return self._not_proven('unsupported_construct', str(exc), context)
        refusal = cpu_memory_admission.summary_refusal(self.records, [
            pin["proof_record"] for group in ("summaries", "models") for pin in context["pins"].get(group, [])])
        if refusal:
            context["settings"] = {"tool": "frama-c-wp", "flags": [], "verifier_launched": False,
                                   "proof_semantics_admission": refusal}
            return self._not_proven("memory_domain", "opaque semantics dependency needs a checked memory boundary", context)
        context["lowering"] = lowering
        context["extern_contracts"] = {
            used["c_name"]: {"id": used["summary"], "sha256": self.library.content_sha256(used["summary"])}
            for used in lowering.summaries if used["name"] not in covered}
        for model in context["pins"].get("models", []):
            context["extern_contracts"][model["id"]] = {k: model[k] for k in ("id", "sha256")}
        context["extern_contracts"].update(context.get("allocation_contracts", {}))
        if context.get("vector_ownership"):
            context["extern_contracts"].update(context["vector_ownership"]["view"].extern_contracts)
        if context.get("semantics"):
            semantics = context["semantics"]
            pin = {k: semantics[k] for k in ("id", "sha256")}
            context["extern_contracts"].update({name: dict(pin) for name in proof_semantics.contract_names(
                self.library, semantics['id'], semantics['calls'])})
            for probe in (self.library.get(semantics["id"]).get("wp") or {}).get("probes") or []:
                name = re.match(r".*?\b(\w+)\s*\(", probe["prototype"]).group(1)
                context["extern_contracts"][name] = dict(pin)
        callees = sorted({a["function"] for a in lowering.anchors if a["kind"] == "contract"} - {job.unit.function})
        context["extra_flags"] = [f"-wp-fct={job.unit.function}"] + \
            ([f"-inline-calls={','.join(callees)}"] if callees else [])
        view = (context.get("terminal_release") or context.get("vector_ownership") or {}).get("view")
        base = hint_check.wp_base(view.text if view else lowering.text, lowering.anchors,
                                  self._context(lowering, entry, summary_job, context))
        base = self._with_contracts(base, contracts)
        context["pointer_bounds_base"] = base
        base, context["pointer_bounds_report"] = wp_pointer_bounds.prepare(lowering, base)
        if context.get("semantics"):
            context["semantics_hint_base"] = base
            proof_setup.check_semantics_hints(base, self.hints)
        accepted = self._hint_check(job, lowering, base, context) if self.hints_path else []
        text = hint_check.merge(base, lowering.anchors, self.hints, accepted).text
        input_path = wp_dir / "wp_input.c"
        context["wp_expected_text"] = text
        input_path.write_text(text)
        context["reports"].append(("wp_input", input_path))
        context["hints_reaching_wp"] = len(accepted)
        return self._wp(job, input_path, context)

    def check_helper_windows(self, job, context):
        """Recheck both source lowerings and the independent contextual AST relation."""
        helper = context["helper_windows"]
        view = helper["view"]
        if self.hints_path and not self._entry_view_hints(job):
            raise helper_windows.Refused("helper views admit only assertions/ghost hints at the original unit entry")
        helper_windows.check_view(helper["source"], job.unit.function, view, **helper["options"])
        try:
            original = c_lowering.lower(helper["source"], job.unit.function, **helper["original_kwargs"])
            effective = c_lowering.lower(view.path, job.unit.function, **helper["effective_kwargs"])
        except c_lowering.LoweringError as exc:
            raise helper_windows.Refused(f"helper source replay failed: {exc}") from None
        if original != helper["original_lowering"] or effective != helper["effective_lowering"]:
            raise helper_windows.Refused("original or contextual helper lowering changed after planning")
        expected = {**view.pins,
            "helper_original_lowering": {"id": helper["original_path"].name, "sha256": original.sha256},
            "helper_original_source": {"id": helper["source"].name, "sha256": original.source_sha256},
            "helper_view_source": {"id": view.path.name, "sha256": effective.source_sha256}}
        if expected != helper["pins"] or any(context["pins"].get(k) != v for k, v in expected.items()):
            raise helper_windows.Refused("helper checker, certificate, or original/view pins changed before launch")

    def check_nested_entry_reads(self, job, context):
        nested = context["nested_entry_reads"]
        view = nested["view"]
        if self.hints_path and not self._entry_view_hints(job):
            raise nested_entry_reads.Refused("nested views admit only assertions/ghost hints at the original unit entry")
        nested_entry_reads.check_view(nested["source"], job.unit.function, view, **nested["options"])
        try:
            original = c_lowering.lower(nested["source"], job.unit.function, **nested["original_kwargs"])
            effective = c_lowering.lower(view.path, job.unit.function, **nested["effective_kwargs"])
        except c_lowering.LoweringError as exc:
            raise nested_entry_reads.Refused(f"nested source replay failed: {exc}") from None
        if original != nested["original_lowering"] or effective != context["lowering"]:
            raise nested_entry_reads.Refused("nested original or effective lowering changed after planning")
        if nested["options"]["entry_windows"] != original.pointer_bounds.get("entry_windows", {}):
            raise nested_entry_reads.Refused("nested entry-window binding changed")
        expected = {**view.pins,
            "nested_read_original_lowering": {"id": nested["original_path"].name, "sha256": original.sha256},
            "nested_read_original_source": {"id": nested["source"].name, "sha256": original.source_sha256},
            "nested_read_view_source": {"id": view.path.name, "sha256": effective.source_sha256}}
        if expected != nested["pins"] or any(context["pins"].get(k) != v for k, v in expected.items()):
            raise nested_entry_reads.Refused("nested checker, source or certificate pins changed before launch")

    def _hint_check(self, job, lowering, base, context):
        """Ticket 35: the proof hint check; the indices of the hints that reach WP (all of them, or none)."""
        wp_dir, log = context["wp_dir"], context["log"]
        shutil.copyfile(self.hints_path, wp_dir / "hints.yaml")
        context["reports"].append(("hints", wp_dir / "hints.yaml"))
        try:
            result = hint_check.judge(base, lowering.anchors, self.hints, Path(job.scratch) / "hint-check",
                                      wp_flags=context["tools"]["flags"])
        except hint_check.HintCheckError as exc:
            raise AdapterError(f"proof hint check: {exc}") from None
        merged = wp_dir / "hints_merged.c"
        merged.write_text(result.pop("merged"))
        accepted = result.pop("accepted")
        result["reached_wp"] = bool(accepted)
        context["hint_set"] = {"sha256": result.pop("hint_set_sha256"), "hints": [dict(h) for h in self.hints]}
        context["hint_check"] = result
        report = wp_dir / "hint_check.json"
        report.write_text(json.dumps({"hint_set": context["hint_set"], "hint_check": result}, indent=1,
                                     sort_keys=True) + "\n")
        context["reports"] += [("hints_merged", merged), ("hint_check", report)]
        log.line(f"proof hint check: {result['verdict']}, {len(result['rejections'])} rejection(s), "
                 f"{result['frama_c_runs']} Frama-C run(s)")
        return accepted

    def _tools(self):
        """Installed versions and binary hashes, checked against the method version's lineup."""
        lineup = {}
        for row in self.method.data.get("lineup") or []:
            lineup.setdefault(row.get("tool"), row)
        frama, clang = framac.locate(), c_lowering.locate()
        if frama.missing:
            raise AdapterError(frama.missing)
        if clang.missing:
            raise AdapterError(clang.missing)
        found = {"frama-c-wp": (frama.version, _binary_sha256(frama.command)),
                 "clang": (clang.version, c_lowering.identity()["clang"]["sha256"])}
        found.update(_solvers())
        problems = []
        for tool in ("frama-c-wp", "clang", *PROVERS):
            pinned = (lineup.get(tool) or {}).get("version")
            have = found.get(tool, (None, None))[0]
            if have is None:
                problems.append(f"{tool} is not installed (Why3 config lists no such prover)")
            elif pinned != have:
                problems.append(f"{tool} {have} is installed but method version {self.method.id} pins {pinned}")
        lowering_id = c_lowering.identity()["c_lowering"]
        if lowering_id not in (self.method.data.get("c_lowering") or {}).get("translators", []):
            problems.append(f"the C lowering tool {lowering_id['id']} (sha256 {lowering_id['sha256'][:12]}...) is not "
                            f"a translator of method version {self.method.id}")
        flags = (lineup.get("frama-c-wp") or {}).get("flags") or []
        for flag, value in FROZEN:
            if not _has_flag(flags, flag, value):
                problems.append(f"method version {self.method.id} does not freeze {flag} {value} for frama-c-wp")
        switch_problem = proof_setup.wp_switch_problem(flags)
        if switch_problem:
            problems.append(f"method version {self.method.id}: {switch_problem} for frama-c-wp")
        if problems:
            raise AdapterError("; ".join(problems))
        seconds = ((self.method.data.get("budgets") or {}).get("wp_seconds_per_solver"))
        if not isinstance(seconds, int):
            raise AdapterError(f"method version {self.method.id} has no budgets.wp_seconds_per_solver")
        identities = {"c_lowering": (lowering_id["id"], lowering_id["sha256"], c_lowering.TOOL_VERSION)}
        for tool, (version, sha) in found.items():
            identities[tool] = (f"{tool}-{version}", sha, version)
        return {"flags": list(flags), "seconds": seconds, "identities": identities,
                "provers": proof_setup.wp_provers(self.method)}

    # --- ticket 24: summaries and C models the unit calls, each proven by its own record ----------------------
    def _summarized(self):
        """{function: library entry ID} of every function a library entry summarizes (`once: self` formal halves)."""
        found = {}
        for eid, data in sorted(self.library.entries.items()):
            unit = data.get("proof_unit") if isinstance(data, dict) else None
            if eid == self.contract or not isinstance(unit, dict) or not unit.get("function"):
                continue
            if any(isinstance(c, dict) and c.get("proof_placement") == {"once": "self"} and c.get("acsl")
                   for c in data.get("clauses") or []):
                if unit["function"] in found:
                    raise AdapterError(f"{unit['function']} is summarized by more than one library entry: "
                                       f"{found[unit['function']]}, {eid}")
                found[unit["function"]] = eid
        return found

    def _proven(self, kind, ident, sha):
        """Latest counting WP proof of this text under the caller's exact method and evidence boundary."""
        from swdb import level_rule
        from swdb.store import Store
        if self.records is None:
            return None
        store = Store(self.records)
        rule = level_rule.Rule(store, self.library)
        expected_method = {"id": self.method.id, "sha256": self.method.sha256}
        expected_evidence = self.method.data.get("evidence_kind")
        memo = {}

        def admissible(record_id):
            if record_id in memo:
                return memo[record_id]
            memo[record_id] = False  # cyclic dependencies never bootstrap a proof
            data = rule.proofs.get(record_id) or {}
            pins = data.get("pins") or {}
            if (data.get("verdict") != "proven" or pins.get("method_version") != expected_method
                    or data.get("evidence_kind") != expected_evidence
                    or expected_evidence not in ("execution", "contract_fixture")
                    or (data.get("job") or {}).get("adapter") != "wp"):
                return False
            setup, reading = data.get("proof_setup_check") or {}, data.get("verdict_reading") or {}
            current_checks = proof_setup.identity()
            if (setup.get("check") != current_checks["proof_setup_check"]
                    or reading.get("check") != current_checks["verdict_reading"]
                    or setup.get("verdict") != "passed" or not setup.get("runs")
                    or setup.get("method_version") != expected_method
                    or reading.get("verdict") != "proven"):
                return False
            state = rule.status(record_id)
            bounds = state.get("bounds")
            if (not state.get("counts") or not isinstance(bounds, dict)
                    or bounds.get("threads") not in (1, "unbounded")
                    or any(value != "unbounded" for key, value in bounds.items() if key != "threads")):
                return False  # a bounded dependency cannot stand for an unbounded WP call
            for group in ("summaries", "models"):
                for used in pins.get(group) or []:
                    dependency = rule.proofs.get(used.get("proof_record")) or {}
                    expected_kind = "library_summary" if group == "summaries" else "c_model"
                    if (dependency.get("subject") != {"kind": expected_kind, "id": used.get("id")}
                            or (dependency.get("pins") or {}).get("code") !=
                            {k: used.get(k) for k in ("id", "sha256")}
                            or not admissible(used.get("proof_record"))):
                        return False
            memo[record_id] = True
            return True

        proven = []
        for record in store.of_kind("proof"):
            data = record.data
            if (data.get("subject") == {"kind": kind, "id": ident}
                    and (data.get("pins") or {}).get("code") == {"id": ident, "sha256": sha}
                    and admissible(record.id)):
                proven.append(((data.get("job") or {}).get("batch", ""), record.id))
        return sorted(proven)[-1][1] if proven else None

    def _dependencies(self, lowering, context):
        """{C name: ACSL text} of the summarized calls; pins every summary and C model to its proven record."""
        contracts, summaries, models, assumed = {}, [], [], []
        for used in lowering.summaries:
            if used["name"] in context.get("covered", {}):
                continue
            entry_id = used["summary"]
            data = self.library.get(entry_id) or {}
            sha = self.library.content_sha256(entry_id)
            record = self._proven("library_summary", entry_id, sha)
            if record is None:
                raise AdapterError(f"{used['name']} is summarized by library entry {entry_id}, which has no proven summary "
                                   f"record at its current content: run `swdb prove --summary {entry_id} --adapter wp` "
                                   "first")
            texts = [c["acsl"]["text"].strip() for c in data.get("clauses") or [] if isinstance(c, dict)
                     and c.get("acsl") and c.get("proof_placement") == {"once": "self"}]
            from swdb import summary_bindings
            summary_bindings.bind(self, context, context['source'], context['job'].unit.function,
                                  used['name'], entry_id, record)
            contracts[used["c_name"]] = sorted(texts, key=lambda t: 0 if t.startswith("requires") else 1)
            summaries.append({"id": entry_id, "sha256": sha, "proof_record": record})
            assumed.append({"kind": "summary", "reference": {"id": entry_id, "sha256": sha},
                            "sentence": f"The summary of {used['name']} (library entry {entry_id}) stands for its code "
                                        f"here; proof record {record} proves the summary on that code."})
        for name in lowering.models:
            if name == standard_range_model.NAME:
                try:
                    caller_sha = standard_range_calls.check_caller(lowering)
                except standard_range_calls.Refused as exc:
                    raise standard_range_model.Refused(str(exc)) from None
            sha = hashlib.sha256((c_lowering.model_text(name) or "").encode()).hexdigest()
            if name.startswith(ALLOCATION_MODEL):
                context.setdefault("allocation_contracts", {})[name] = {"id": name, "sha256": sha}
                assumed.append({"kind": "assumed_clause", "reference": {"id": name, "sha256": sha},
                                "sentence": f"Allocation succeeds: the allocation model {name} behaves as its contract "
                                            "says (new[] returns as many valid elements as asked); the assumption "
                                            "entry of map 16 item 7, since WP cannot prove allocation success."})
                continue
            record = self._proven("c_model", name, sha)
            if record is None:
                raise AdapterError(f"the C lowering calls the C model {name}, which has no proven record at its current "
                                   f"text: run `swdb prove --model {name} --adapter wp` first")
            if name == standard_range_model.NAME:
                try:
                    dependency = standard_range_calls.bind_dependency(self,record,context["job"].scratch)
                except (standard_range_calls.Refused,standard_range_model.Refused) as exc:
                    raise standard_range_model.Refused(str(exc)) from None
                context["standard_range_calls"] = {"caller_sha256":caller_sha,"dependency":dependency}
                context["pins"]["standard_range_call_check"] = standard_range_calls.identity()
                context.setdefault("settings",{})["standard_range_calls"] = context["standard_range_calls"]
            models.append({"id": name, "sha256": sha, "proof_record": record})
            assumed.append({"kind": "summary", "reference": {"id": name, "sha256": sha},
                            "sentence": f"The C model {name} stands for the call it models (one thread); proof record "
                                        f"{record} proves its contract on its text."})
        context.setdefault("assumed", []).extend(assumed)
        if summaries:
            context["pins"]["summaries"] = summaries
        if models:
            context["pins"]["models"] = models
        return contracts

    def _context(self, lowering, entry, summary_job=False, job_context=None):
        """What WP sees besides the hints, {anchor: [block]}: the contract's formal halves at the unit's contract
        anchor (`requires` first; per-candidate, or `once: self` for a summary job, ticket 24), the logic-library
        files they use at ghost.globals."""
        placement = {"once": "self"} if summary_job else "per_candidate"
        clauses = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                   and c.get("proof_placement") == placement]
        if not clauses:
            raise AdapterError(f"contract {self.contract} has no {'once: self' if summary_job else 'per-candidate'} "
                               "formal half to prove")
        texts = [c["acsl"]["text"].strip() for c in clauses]
        semantics = (job_context or {}).get("semantics")
        prelude = []
        if semantics:
            texts, prelude = self._with_semantics(lowering, texts, semantics)
        texts = sorted(texts, key=lambda t: 0 if t.startswith("requires") else 1)
        if (job_context or {}).get("vector_ownership"):
            texts = [job_context["vector_ownership"]["view"].formal_text]
        uses = []
        for clause in clauses:
            uses += [u for u in clause["acsl"].get("uses", []) if u not in uses]
        from swdb.formal_frame import logic_files
        files = logic_files(self.library.root, self.library)       # ticket 26: an entry's own file too
        inserts = {f"{lowering.function}.contract": ["/*@ " + "\n    ".join("\n".join(texts).splitlines()) + " */"]}
        for anchor in lowering.anchors:                  # ticket 23: summarized callees carry their ACSL summary
            callee = anchor.get("function")
            if anchor["kind"] != "contract" or callee == lowering.function:
                continue
            summary = self._summary_clauses(callee)
            if summary:
                ordered = sorted((c["acsl"]["text"].strip() for c in summary),
                                 key=lambda t: 0 if t.startswith("requires") else 1)
                inserts[anchor["id"]] = ["/*@ " + "\n    ".join("\n".join(ordered).splitlines()) + " */"]
                for clause in summary:
                    uses += [u for u in clause["acsl"].get("uses", []) if u not in uses]
        inserts["ghost.globals"] = prelude + [f"/*@\n{files[u].read_text()}\n*/" for u in uses]
        if semantics:
            from swdb import dx100_size_source
            if dx100_size_source.size_layout(self.library.get(semantics['id']) or {}):
                certificates=dx100_size_source.bindings(lowering)
                if len(certificates)!=1:
                    raise AdapterError('fresh-SPD entry projection needs one checked source/epoch certificate')
                projection=dx100_size_source.constructor_projection(certificates[0]['entry'])
                inserts[f'{lowering.function}.entry']=[
                    '/* Conditional synthetic constructor-state projection; no source reset or wait. */',
                    *projection['entry_assignments']]
                semantics['entry_projection']={'kind':dx100_size_source.CERTIFICATE_KIND,
                    'bytes':projection['metadata_bytes'],'owner':dx100_size_source.OWNER,
                    'statement':dx100_size_source.BOOT_STATEMENT}
            from swdb import dx100_stream_source, dx100_stream_model
            if dx100_stream_source.stream_layout(self.library.get(semantics['id']) or {}):
                certificates=dx100_stream_source.bindings(lowering)
                if {c['call'] for c in certificates}!=set(dx100_stream_source.PROTOTYPES) or len(certificates)!=3:
                    raise AdapterError('isolated stream entry projection needs all three checked source certificates')
                inserts[f'{lowering.function}.entry']=[
                    '/* Conditional source-constructor/RF/input epoch; no source reset or added wait. */',
                    *dx100_stream_model.normal_return_model()['entry']]
                semantics['entry_projection']={'kind':dx100_stream_source.ENTRY['kind'],
                    'owner':dx100_stream_source.OWNER,'statement':dx100_stream_source.BOOT_STATEMENT}
        return inserts

    def _summary_clauses(self, callee):
        """The `once: self` formal halves of the library entry that summarizes `callee` (ticket 23), or []."""
        found = [data for eid, data in sorted(self.library.entries.items())
                 if eid != self.contract and isinstance(data.get("proof_unit"), dict)
                 and data["proof_unit"].get("function") == callee]
        for data in found:
            clauses = [c for c in data.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                       and c.get("proof_placement") == {"once": "self"}]
            if clauses:
                return clauses
        return []

    @staticmethod
    def _with_contracts(text, contracts):
        """Ticket 24: each summarized callee's `once: self` formal halves right before its prototype line."""
        out, waiting = [], dict(contracts or {})
        for line in text.splitlines():
            name = next((n for n in waiting if re.match(rf"^[^/{{]*\b{re.escape(n)}\([^{{]*\);$", line)), None)
            if name is not None:
                out.append("/*@ " + "\n    ".join("\n".join(waiting.pop(name)).splitlines()) + " */")
            out.append(line)
        return "\n".join(out) + "\n"


    def _with_semantics(self, lowering, texts, semantics):
        """(formal-half texts with the semantics' preconditions and state locations, [the WP-form prelude])."""
        entry_id = semantics["id"]
        data = self.library.get(entry_id) or {}
        wp = data.get("wp") or {}
        from swdb.dx100_source_selector import pure_layout
        from swdb import dx100_size_source
        from swdb import dx100_stream_source
        if dx100_stream_source.stream_layout(data):
            try:
                policy=dx100_stream_source.unit_policy(self.library,self.library.get(self.contract) or {})
            except dx100_stream_source.Refused as exc:
                raise AdapterError('partial source admission: '+str(exc)) from None
            if self.method.id!=dx100_stream_source.PARTIAL_METHOD:
                raise AdapterError('partial source admission requires its explicit partial fixture method version')
            semantics['unit_correctness_policy']=policy
            semantics['unit_requires'],semantics['unit_ensures']=[],[]
            rewritten=[re.sub(r"\bassigns\s+\\nothing\s*;",'assigns __swdb_dx_stream_meta;',text) for text in texts]
            rewritten.append(r'terminates \false;')
            return rewritten,[proof_semantics.wp_prelude(self.library,entry_id,semantics['calls'],self.defines)]
        if dx100_size_source.size_layout(data):
            semantics['unit_requires'],semantics['unit_ensures']=[],[]
            rewritten=[re.sub(r"\bassigns\s+\\nothing\s*;",
                'assigns __swdb_dx_size_bytes[0 .. 63];',text) for text in texts]
            return rewritten,[proof_semantics.wp_prelude(self.library,entry_id,semantics['calls'],self.defines)]
        if pure_layout(data):
            semantics["unit_requires"], semantics["unit_ensures"] = [], []
            return texts, [proof_semantics.wp_prelude(self.library, entry_id, semantics["calls"], self.defines)]
        locations = proof_semantics.wp_locations(self.library, entry_id, self.defines)
        joined = ", ".join(locations)
        rewritten = []
        for text in texts:
            text = re.sub(r"\bassigns\s+\\nothing\s*;", f"assigns {joined};", text)
            text = re.sub(r"\bassigns\s+(?!" + re.escape(locations[0]) + r")([^;]+);",
                          lambda m: f"assigns {m.group(1).strip()}, {joined};", text)
            rewritten.append(text)
        extra = []
        if wp.get("unit_requires"):
            extra.append(f"requires {wp['unit_requires']};")
        for name, _ctype, pointer in lowering.parameters:
            if not pointer:
                continue
            for array in wp.get("separate_from") or []:
                if array == "dx_tile_data":
                    extra.append(f"requires \\forall integer swdb_tile; 0 <= swdb_tile < DX_NT ==> "
                                 f"\\base_addr({name}) != \\base_addr(dx_tile_data[swdb_tile]);")
                    continue
                dims = next((loc.count("[") for loc in locations if loc.split("[")[0] == array), 0)
                extra.append(f"requires \\base_addr({name}) != \\base_addr(&{array}{'[0]' * dims});")
        semantics["unit_requires"] = list(extra)
        # Checked exit condition, never an assumed entry premise. Every admitted WP memory command
        # has a destination writer; pending reads remain allowed across this unit boundary.
        semantics["unit_ensures"] = (["ensures memory_domain_exit: dx_memory_clear_after_stall(-1, -1, 0);"]
                                     if set(semantics["calls"]) & cpu_memory_admission.STORE_CALLS else [])
        rewritten += semantics["unit_ensures"]
        prelude = proof_semantics.wp_prelude(self.library, entry_id, semantics["calls"], self.defines)
        return extra + rewritten, [prelude]

    def _wp(self, job, input_path, context):
        tools, log, wp_dir = context["tools"], context["log"], context["wp_dir"]
        scratch = Path(job.scratch)
        shutil.copyfile(input_path, scratch / "wp_input.c")
        (scratch / "tmp").mkdir(exist_ok=True)
        goals_json, properties_csv = scratch / "wp-goals.json", scratch / "wp-properties.csv"
        inventory = scratch / "wp-inventory.json"
        report_module = proof_setup.compile_report_module(scratch)
        prover_flags = [] if any(f == "-wp-prover" or f.startswith("-wp-prover=") for f in tools["flags"]) else \
            ["-wp-prover", ",".join(tools["provers"])]
        settings_flags = [*tools["flags"], *MACHDEP, *prover_flags, "-wp-timeout",
                          str(tools["seconds"]), "-wp-par", "1", "-wp-smoke-tests", *context.get("extra_flags", [])]
        # RTE's function-set option resolves against an existing AST. Parse (and inline)
        # first, then enable initialization checks for every body, including lowered callees.
        # -wp-rte alone does not generate initialization assertions in Frama-C 33.
        parse_flags = [f for f in context.get("extra_flags", []) if f.startswith("-inline-calls=")]
        normalized = scratch / "wp-normalized.c"
        command = [*framac.locate().command, *MACHDEP, *parse_flags, "wp_input.c",
                   "-print", "-ocode", normalized.name, "-then",
                   *settings_flags, "-wp-report-json", goals_json.name,
                   "-then", "-load-module", str(report_module), "-report", "-report-untried",
                   "-report-csv", properties_csv.name]
        removed = []
        env = dict(os.environ)
        env["SWDB_PROOF_REPORT_OUT"] = str(inventory)
        env["TMPDIR"] = str(scratch / "tmp")
        cap = int(os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") or DEFAULT_CAP_BYTES)
        wall = job.budget_seconds or DEFAULT_WALL_SECONDS
        wp_log = wp_dir / "frama-c.log"
        log.line(f"command: {shlex.join(map(str, command))}\ncwd: scratch\nenvironment removed: {removed or 'none'}\n"
                 f"rss cap bytes: {cap}\nwall budget seconds: {wall}")
        context["reports"].append(("wp_log", wp_log))
        context["settings"] = {**context.get('settings', {}), "tool": "frama-c-wp", "flags": settings_flags, "session": "fresh",
                               "pointer_bounds": context["pointer_bounds_report"],
                               "warning_levels": "default", "machdep": "x86_64",
                               "wp_seconds_per_solver": tools["seconds"], "environment_removed": removed,
                               "rss_cap_bytes": cap, "hint_count": context.get("hints_reaching_wp", 0), "build_constants": list(self.defines)}
        inputs = [(scratch / "wp_input.c", context["wp_expected_text"])]
        member = (getattr(context.get("lowering"), "pointer_bounds", None) or {}).get("member_windows")
        if member:
            policy = {"certificate": member, "entry": member["entry"],
                      "inline_functions": member["inline_functions"]}
            context["settings"]["member_windows"] = policy
            member_text = json.dumps(policy, sort_keys=True, indent=2) + "\n"
            member_path = scratch / "member-window-context.json"
            member_path.write_text(member_text)
            inputs.append((member_path, member_text))

        helper = context.get("helper_windows")
        if helper:
            view = helper["view"]
            inputs += [(helper["source"], helper["original_source_text"]),
                       (helper["original_path"], helper["original_lowering"].text), (view.path, view.text),
                       (helper["certificate_path"], helper["certificate_text"])]
            context["settings"]["helper_windows"] = {"certificate": view.certificate,
                "original_lowering_sha256": helper["original_lowering"].sha256,
                "effective_lowering_sha256": helper["effective_lowering"].sha256,
                "input_premises_added": [], "hints": "source-anchored hints unsupported"}
        nested = context.get("nested_entry_reads")
        if nested:
            view = nested["view"]
            inputs += [(nested["source"], nested["original_source_text"]),
                       (nested["original_path"], nested["original_lowering"].text), (view.path, view.text),
                       (nested["certificate_path"], nested["certificate_text"])]
            context["settings"]["nested_entry_reads"] = {"certificate": view.certificate,
                "original_lowering_sha256": nested["original_lowering"].sha256,
                "effective_lowering_sha256": context["lowering"].sha256, "input_premises_added": [],
                "hints": "source-anchored hints unsupported"}
        terminal = context.get("terminal_release")
        if terminal:
            view = terminal["view"]
            try:
                terminal_release.check_view(context["lowering"], view, terminal["formal_texts"], self.hints)
            except terminal_release.Refused as exc:
                raise AdapterError(f"terminal-release prelaunch check: {exc}") from None
            inputs.append((terminal["path"], view.text))
            context["settings"]["terminal_release"] = {
                "certificate": view.certificate, "wp_view_sha256": hashlib.sha256(view.text.encode()).hexdigest()}
        owner = context.get("vector_ownership")
        if owner:
            view = owner["view"]
            try:
                vector_ownership.check_origins(context["lowering"], owner["source"], view,
                                            owner["formal_texts"], self.hints)
            except vector_ownership.Refused as exc:
                raise AdapterError(f"vector ownership prelaunch check: {exc}") from None
            if any(context["pins"].get(name) != pin for name, pin in view.pins.items()):
                raise AdapterError("vector ownership checker/certificate/allocator pins changed before launch")
            inputs += [(owner["path"], view.text), (owner["contract_path"], owner["contract_text"])]
            context["settings"]["vector_ownership"] = {
                "certificate": view.certificate, "wp_view_sha256": hashlib.sha256(view.text.encode()).hexdigest(),
                "source_frame": view.certificate["source_frame"], "source_frame_preservation": "checked",
                "frame_evidence": "structural relational lowering; not a WP goal",
                "original_contract_sha256": view.certificate["original_contract_sha256"],
                "view_contract_sha256": view.certificate["view_contract_sha256"]}
        model_view = context.get("standard_model_view")
        if model_view:
            view = model_view["view"]
            try:
                standard_model_view.check_view(job.unit.function, view, wp_dir)
            except standard_model_view.Refused as exc:
                raise AdapterError(f"standard model view prelaunch check: {exc}") from None
            if any(context["pins"].get(name) != pin for name, pin in view.pins.items()):
                raise AdapterError("standard model view checker/certificate pins changed before launch")
            inputs += [(model_view["original_path"], model_view["original_text"]),
                       (model_view["certificate_path"], model_view["certificate_text"])]
            context["settings"]["standard_model_view"] = view.certificate
        range_model = context.get("standard_range_model")
        if range_model:
            view = range_model["view"]
            try:
                standard_range_model.check_view(job.unit.function, view, wp_dir)
            except standard_range_model.Refused as exc:
                raise AdapterError(f"standard range model prelaunch check: {exc}") from None
            if any(context["pins"].get(name) != pin for name,pin in view.pins.items()):
                raise AdapterError("standard range model checker/certificate pins changed before launch")
            inputs += [(range_model["original_path"], range_model["original_text"]),
                       (range_model["certificate_path"], range_model["certificate_text"])]
            context["settings"]["standard_range_model"] = view.certificate
        proof_setup.check_generated(job, self, context, inputs, settings_flags, command=command, scratch=scratch)
        context["settings"]["verifier_launched"] = True
        result = rss_watchdog.run(command, log=wp_log, cap_bytes=cap, timeout=wall, cwd=scratch, env=env)
        context["peak"] = result.peak_rss_bytes
        log.line(f"frama-c exit {result.exit_code}, wall {result.wall_seconds:.2f} s, peak rss {result.peak_rss_bytes}, "
                 f"out of memory {result.out_of_memory}, timed out {result.timed_out}")
        for name, path in (("wp_goals", goals_json), ("wp_properties", properties_csv), ("wp_inventory", inventory),
                           ("wp_normalized", normalized)):
            if path.exists():
                shutil.copyfile(path, wp_dir / path.name)
                context["reports"].append((name, wp_dir / path.name))
        outcome = read_outcome(result, wp_log.read_text(errors="replace"),
                               goals_json if goals_json.exists() else None,
                               properties_csv if properties_csv.exists() else None, context.get("functions"),
                               inventory=inventory, extern_contracts=context.get("extern_contracts"))
        context.setdefault("assumed", []).extend(outcome.get("assumptions", []))
        context["verdict_reading"] = outcome.get("reading")
        if context.get("semantics") and outcome["verdict"] == "not_proven" and \
                outcome["failure_class"] in {"timeout", "unknown", "solver_error"} and any(
                g.get("status") != "valid" and "ghost_capacity" in str(g.get("goal", ""))
                for g in outcome["goals"]):
            outcome["failure_class"] = "ghost_capacity"
            outcome["why"] = "the named DX100 ghost-capacity obligation is not proven"
        if context.get("semantics") and outcome["verdict"] == "not_proven" and \
                outcome["failure_class"] in {"timeout", "unknown", "solver_error"} and any(
                g.get("status") != "valid" and "memory_domain" in str(g.get("goal", ""))
                for g in outcome["goals"]):
            outcome["failure_class"] = "memory_domain"
            outcome["why"] = "the checked DX100 device-memory domain is not proven; ticket 28 models overlap"
        context["goals"], context["unproven"] = outcome["goals"], outcome["unproven"]
        log.line(f"outcome: {outcome['verdict']} {outcome['failure_class'] or ''} ({outcome['why']})")
        if outcome["verdict"] == "proven":
            return self._verdict("proven", None, context)
        return self._not_proven(outcome["failure_class"], outcome["why"], context)

    # --- verdicts and handlers --------------------------------------------------------------------
    def _not_proven(self, failure_class, why, context):
        context.setdefault("goals", [])
        context.setdefault("unproven", [])
        handler = run_handler(failure_class, why, context)
        if handler:
            context["reports"].append(("handler", handler))
        return self._verdict("not_proven", failure_class, context)

    def _verdict(self, verdict, failure_class, context):
        identities = context["tools"]["identities"]
        assumptions, tools = [], []
        for tool in ("c_lowering", "clang", "frama-c-wp", *PROVERS):
            ident, sha, version = identities[tool]
            assumptions.append({"kind": "trusted_tool", "reference": {"id": ident, "sha256": sha},
                                "sentence": SENTENCES[tool].format(version=version)})
            tools.append(ident)
        assumptions += context.get("assumed", [])            # ticket 24: summaries, C models, allocation
        fields = {"goals": context.get("goals", [])}
        for name in ("hint_set", "hint_check", "verdict_reading"):                   # ticket 35: the hint set and its check result
            if context.get(name) is not None:
                fields[name] = context[name]
        if verdict == "not_proven":
            fields["unproven_properties"] = context.get("unproven", [])
        if context.get("settings"):
            fields["settings"] = context["settings"]
        if self.hints and (context.get("helper_windows") or context.get("nested_entry_reads")):
            source_view = context.get("nested_entry_reads") or context["helper_windows"]
            fields.setdefault("settings", {})["source_view_hints"] = {
                "policy": "original-unit-entry assertions and ghost hints only",
                "anchor": f"{source_view['original_lowering'].function}.entry", "count": len(self.hints),
                "scope": "unchanged original parameters; ordinary hint and semantics checks remain mandatory"}
        pins = {"c_lowering": context["c_lowering"], "naming_rules": c_lowering.naming_rules()} \
            if context.get("c_lowering") else {}
        pins.update(context.get("pins") or {})                 # ticket 24: summaries and C models
        semantics = context.get("semantics")
        if semantics:                               # ticket 27: as the CBMC adapter records it
            assumptions += proof_semantics.record_assumptions(self.library, semantics['id'], semantics['sha256'])
            pins["proof_semantics"] = {"id": semantics["id"], "sha256": semantics["sha256"]}
            fields.setdefault("settings", {})["proof_semantics"] = {
                **context["semantics_settings"], "unit_requires": semantics.get("unit_requires", []),
                "unit_ensures": semantics.get("unit_ensures", []),
                **({"entry_projection":semantics["entry_projection"]} if "entry_projection" in semantics else {}),
                **({"unit_correctness_policy":semantics["unit_correctness_policy"]} if "unit_correctness_policy" in semantics else {})}
            from swdb.dx100_source_selector import pure_layout, PURE_STATEMENT
            from swdb import dx100_size_source
            from swdb import dx100_stream_source
            if dx100_stream_source.stream_layout(self.library.get(semantics['id'])):
                assumptions.append({'kind':'proof_semantics','reference':{'id':semantics['id'],'sha256':semantics['sha256']},
                    'sentence':'Only the source-bound closed one-u32-stream, real returned wait and metadata size observation are admitted on conditional normal return. Input mapping/coherence, exclusive epoch and all-schedule event refinement are owned TCB obligations; source refinement and contract/body agreement remain unverified. No hardware termination, payload CPU read or full-interface theorem is claimed.'})
            elif dx100_size_source.size_layout(self.library.get(semantics['id'])):
                assumptions.append({'kind':'proof_semantics','reference':{'id':semantics['id'],'sha256':semantics['sha256']},
                    'sentence':'Only the source-certified size getter in its explicit synthetic fresh-SPD boot epoch is admitted; no device commands, arbitrary-entry freshness or timing reduction is used.'})
            elif pure_layout(self.library.get(semantics['id'])):
                assumptions.append({"kind": "proof_semantics", "reference": {"id": semantics["id"],
                    "sha256": semantics["sha256"]}, "sentence": PURE_STATEMENT})
            else:
                assumptions.append({"kind": "proof_semantics", "reference": {"id": semantics["id"],
                                                                             "sha256": semantics["sha256"]},
                                    "sentence": f"The DX100 behaves as its proof semantics {semantics['id']} says: each "
                                                "command's values as if it finished at issue, hazards as its rules state."})
                assumptions.append({"kind": "assumed_clause", "reference": {"id": semantics["id"],
                                                                            "sha256": semantics["sha256"]},
                    "sentence": "The WP model-domain preconditions hold: no DX100 command is outstanding at entry, "
                                "the fixed modeled device storage is initialized (dx_state_initialized), "
                                "and CPU pointer parameters occupy objects separate from tile data, tile sizes, and "
                                "register values. The exact generated clauses are recorded in "
                                "settings.proof_semantics.unit_requires; store-frame witnesses and selected-index "
                                "bounds and initialized caller-memory reads remain checked proof obligations. "
                                "Device-call initialization preservation is a trusted semantics contract, "
                                "pending ticket 29's independent contract/body agreement checks."})
                reduction = Path(self.library.root) / "rocq" / "probata" / "Reduction.v"
                if not reduction.is_file():
                    reduction = paths.HOME / "library" / "rocq" / "probata" / "Reduction.v"
                assumptions.append({"kind": "reduction", "reference": {"id": "rocq.probata.dx100_reduction",
                                                                       "sha256": artifacts.file_hash(reduction)},
                                    "sentence": "The DX100 reduction lemma (Reduction.v, statement only; proof: ticket "
                                                "43): a hazard-free at-issue run matches every timing gem5 allows."})
        return Verdict(verdict=verdict, bounds={"threads": 1, "input_size": "unbounded"}, assumptions=assumptions,
                       failure_class=failure_class, tools=tuple(tools), peak_rss_bytes=context.get("peak"),
                       record_fields=fields, pins=pins, reports=tuple(context["reports"]))


# --- the minimal verdict reader -------------------------------------------------------------------------

CRASH = re.compile(r"Unexpected error|internal error|Fatal error|Stack overflow|Please report|Uncaught exception")
USER_ERROR = re.compile(r"User Error|annot-error|invalid user input|syntax error|Ignoring")


def read_outcome(result, log_text, goals_json, properties_csv, functions=None, *, inventory=None, extern_contracts=None):
    """{verdict, failure_class, why, goals, unproven} from one fresh WP run (ticket36 strict reading).

    `functions` (ticket 24): read only the properties and goals of these functions (the proof unit, its inlined
    callees included); C models and summaries in the same file are proven by their own records."""
    def outcome(verdict, failure_class, why, goals=(), unproven=()):
        return {"verdict": verdict, "failure_class": failure_class, "why": why, "goals": list(goals),
                "unproven": list(unproven)}
    if result.out_of_memory:
        return outcome("not_proven", "out_of_memory", "the RSS watchdog killed the job above its cap")
    if result.timed_out:
        return outcome("not_proven", "timeout", "the job ran out of its wall budget")
    if result.exit_code < 0 or CRASH.search(log_text):
        return outcome("not_proven", "tool_crash", f"Frama-C crashed (exit {result.exit_code})")
    if USER_ERROR.search(log_text):
        return outcome("not_proven", "parse_error", _first(log_text, USER_ERROR))
    if result.exit_code != 0:
        return outcome("not_proven", "tool_crash", f"Frama-C exited {result.exit_code} without a user error")
    if goals_json is None or properties_csv is None:
        return outcome("not_proven", UNCLASSIFIED, "WP exited 0 but wrote no per-property or per-goal report")
    return proof_setup.read_wp_reports(goals_json, properties_csv, inventory, extern_contracts, functions)


def _goal(raw):
    solver, seconds = None, None
    for prover in raw.get("provers") or []:
        if prover.get("success"):
            solver = str(prover.get("prover", "")).split(":")[0].lower()
            seconds = float(prover.get("time") or 0)
            break
    status = "valid" if raw.get("passed") else str(raw.get("verdict") or "unknown").lower()
    return {"goal": raw.get("goal"), "property": raw.get("property"), "function": raw.get("function"),
            "status": status, "solver": solver, "seconds": seconds}


def _first(text, pattern):
    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()[:400]
    return "Frama-C refused the input"


# --- handlers (map 11 item 9) ----------------------------------------------------------------------------

def run_handler(failure_class, why, context):
    """Run the handler of `failure_class` (its text from vocabulary proof_failure_classes); write handler.json."""
    vocabs, _problems = vocab.load_all(paths.VOCAB)
    entry = vocabs.entries.get("proof_failure_classes", {}).get(failure_class)
    if entry is None:
        return None                                # unclassified: swdb prove stops the batch
    wp_dir = context["wp_dir"]
    action = {"failure_class": failure_class, "why": why, "handler": entry.get("handler")}
    if failure_class in ("timeout", "unknown"):
        action["for_hint_loop"] = [g["goal"] for g in context.get("goals", []) if g["status"] != "valid"]
    elif failure_class == "out_of_memory":
        action["done"] = "class kept; on the Mac the ~8 GB cap stays, a rerun with more memory needs another host"
    else:                                          # parse error, unsupported construct, solver error, crash, vacuous pass
        reproduction = wp_dir / "reproduction"
        reproduction.mkdir(exist_ok=True)
        for name, path in context["reports"]:
            if name in ("wp_input", "c_lowering", "hints"):
                shutil.copyfile(path, reproduction / Path(path).name)
        if (context.get("settings") or {}).get("flags"):
            (reproduction / "command.txt").write_text(" ".join(context["settings"]["flags"]) + " wp_input.c\n")
        action["minimal_reproduction"] = sorted(p.name for p in reproduction.iterdir())
        action["regression_corpus"] = "add the case (input, class, cause) to tests/fixtures/proof/regression_corpus/"
    path = wp_dir / "handler.json"
    path.write_text(json.dumps(action, indent=1, sort_keys=True) + "\n")
    context["log"].line(f"handler ({failure_class}): {entry.get('handler')}")
    return path


# --- helpers -----------------------------------------------------------------------------------------------

class _Log:
    def __init__(self, path):
        self.path = Path(path)

    def line(self, text):
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(text.rstrip("\n") + "\n")


def _unit_source(tree, function):
    """The one C++ translation unit of the candidate artifact's tree that defines `function`."""
    pattern = re.compile(rf"(?m)^[^\n;{{}}#]*\b{re.escape(function)}\s*\([^;{{}}]*\)\s*(const\s*)?\{{")
    found = [p for p in sorted(tree.rglob("*")) if p.suffix in SOURCE_SUFFIXES and p.is_file()
             and pattern.search(p.read_text(errors="replace"))]
    if len(found) != 1:
        where = ", ".join(str(p.relative_to(tree)) for p in found) or "none"
        raise AdapterError(f"{function} must be defined in exactly one C++ file of {tree} (found: {where})")
    return found[0]


def _has_flag(flags, flag, value):
    return any(flags[i] == flag and flags[i + 1] == value for i in range(len(flags) - 1))


def why3_config():
    return Path(os.environ.get("WHY3CONFIG") or Path.home() / ".why3.conf")


def _solvers():
    """{tool: (version, sha256 of its binary)} from the Why3 configuration WP uses."""
    found, current = {}, {}
    try:
        text = why3_config().read_text()
    except OSError:
        return found
    for line in [*text.splitlines(), "[end]"]:
        line = line.strip()
        if line.startswith("["):
            name = WHY3_NAMES.get(current.get("name"))
            if name and name not in found and current.get("version"):
                binary = current.get("path") or (shlex.split(current.get("command", "")) or [""])[0]
                found[name] = (current["version"], _file_sha256(binary) if binary and Path(binary).is_file() else "0" * 64)
            current = {}
        elif "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip().strip('"')
    return found


_SHA = {}


def _file_sha256(path):
    path = Path(path).resolve()
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _SHA:
        _SHA[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _SHA[key]


def _binary_sha256(command):
    """sha256 of the Frama-C binary a command line runs (through `opam exec` when it is one)."""
    command = list(command)
    try:
        if command and Path(command[0]).name == "opam" and "--" in command:
            head = command[:command.index("--") + 1]
            done = subprocess.run([*head, "sh", "-c", f"command -v {shlex.quote(command[-1])}"], capture_output=True,
                                  text=True, timeout=60)
            binary = done.stdout.strip()
        else:
            binary = next((part for part in reversed(command) if Path(part).is_file()), None) or \
                shutil.which(command[-1])
        return _file_sha256(binary)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        raise AdapterError(f"cannot find the Frama-C binary of {shlex.join(command)} to pin its sha256") from None
