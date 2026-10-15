"""The bounded verifier with its fallbacks, in a fixed order (`swdb prove --adapter bounded`).

Created: 2026-10-14 ET (Probata proof of concept ticket 23). Design: formal-verification map spec ("Verifier lineup
and order": bounded verifier, fallbacks in order, floats as reals; Later change of 2026-10-14 13:19 ET: CBMC 6.11 on
the C lowering is the bounded verifier at threads = 1); map 11 items 2, 6, 9. Format:
docs/reference/format-v0.4-stubs-check-mode.md.

- Route of a unit that is not real-valued: CBMC on the C lowering (the bounded verifier), then crux-llvm on the
  C++, then crux-llvm on the C lowering (the design's remaining fallbacks, in its order).
- Route of a real-valued unit (its interface or its formal halves use a floating type or `real`): crux-llvm
  `-f real` on the C++, then on the C lowering. CBMC checks floats bit-precisely, so it never serves a real-valued
  unit. SAW would serve them only after a passing SAW float-mode check; none counts in this effort (SAW is no
  longer the bounded verifier and has no adapter), so the route names that reason.
- A fallback runs only when the tool before it cannot read the code: not proven with `parse_error` or
  `unsupported_construct` (the handler of those two classes in a chain is the next fallback). A proof, a
  refutation, a timeout or any other class is that tool's verdict and ends the chain; a timeout never moves on.
  When the last tool cannot read the code either, the unit reads not proven with that run's class.
- An explicit initializedness/origin-policy refusal ends the route (2026-10-15 ET). A fallback cannot relax
  the checked input domain merely because that refusal uses unsupported_construct.
- The record is the verdict tool's, plus `settings.route`: the order, every attempt (tool, verdict, class, why it
  moved on), the reason for the order, and `verdict_tool`, the tool that gave the verdict.
"""

import json
from pathlib import Path

from swdb import c_lowering, cbmc_translator as tr, cxx_cut
from swdb.proof import ADAPTERS, AdapterError, Verdict

NAME = "bounded"
READ_FAILURES = ("parse_error", "unsupported_construct")
ROUTE = ("cbmc", "crux-llvm-cxx", "crux-llvm-c")
REAL_ROUTE = ("crux-llvm-cxx", "crux-llvm-c")
SAW_FLOAT_MODE = ("SAW's float mode is not confirmed in this effort (SAW is no longer the bounded verifier and has no "
                  "adapter since 2026-10-14 13:19 ET), so crux-llvm -f real serves real-valued units")
NO_CBMC = "CBMC checks floats bit-precisely, so it never serves a real-valued unit (design: floats as reals)"


class BoundedChain:
    name = NAME
    real = True

    def __init__(self, library, contract, method, records=None, defines=(), args=None):
        self.library, self.contract, self.method = library, contract, method
        self.records, self.defines, self.args = records, tuple(sorted(defines)), args

    @classmethod
    def from_args(cls, args, script, *, library, contract, method):
        if script is not None:
            raise AdapterError("the bounded adapter takes no --script")
        return cls(library, contract, method, records=getattr(args, "records", None),
                   defines=getattr(args, "define", None) or (), args=args)

    def _real_valued(self, job):
        entry = self.library.get(self.contract) or {}
        placement = {"once": "self"} if job.unit.candidate is None else "per_candidate"
        rows = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                and c.get("proof_placement") == placement]
        try:
            clauses = tr.clauses(self.contract, rows)
        except tr.Untranslatable:
            clauses = []
        interface = None
        try:
            if job.unit.candidate is None:
                source = self.library.resolve((entry.get("proof_unit") or {}).get("source"))
            else:
                from swdb.wp_adapter import _unit_source
                source = _unit_source(Path(job.unit.tree), job.unit.function)
            interface = cxx_cut.CxxCode(source, job.unit.function, self.defines).interface(job.unit.function)
        except (c_lowering.LoweringError, AdapterError, KeyError, StopIteration):
            interface = None
        return tr.real_valued(interface, clauses)

    def run(self, job):
        log = Path(job.log)
        real = self._real_valued(job)
        route = REAL_ROUTE if real else ROUTE
        reason = f"real-valued unit: {NO_CBMC}; {SAW_FLOAT_MODE}" if real else \
            "CBMC on the C lowering is the bounded verifier (2026-10-14 13:19 ET); crux-llvm on the C++, then on the " \
            "C lowering, are the fallbacks in the design's order"
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(f"adapter: bounded\nroute: {' -> '.join(route)}\nreason: {reason}\n")
        attempts, reports, verdict = [], [], None
        for position, name in enumerate(route):
            adapter = ADAPTERS[name](self.library, self.contract, self.method, records=self.records,
                                     defines=self.defines)
            verdict = adapter.run(job)
            attempt = {"tool": name, "verdict": verdict.verdict}
            if verdict.failure_class:
                attempt["failure_class"] = verdict.failure_class
            admission = ((verdict.record_fields or {}).get('settings') or {}).get('bounded_initialization') or {}
            standard = ((verdict.record_fields or {}).get('settings') or {}).get('stdlib_provenance') or {}
            if admission.get('verdict') == 'refused' or standard.get('verdict') == 'refused':
                attempt['handler'] = ('original standard declaration/header provenance refused; no fallback may relax it'
                    if standard.get('verdict') == 'refused' else
                    'checked source initializedness/origin policy refused; no fallback may relax it')
                attempts.append(attempt)
                break
            last = position == len(route) - 1
            if verdict.verdict == "not_proven" and verdict.failure_class in READ_FAILURES and not last:
                attempt["handler"] = f"next fallback: {route[position + 1]} ({name} cannot read the code)"
                attempts.append(attempt)
                reports += [(f"{name}_{label}", path) for label, path in verdict.reports if label == "handler"]
                with open(log, "a", encoding="utf-8") as handle:
                    handle.write(f"bounded: {name} gave {verdict.failure_class}; next fallback {route[position + 1]}\n")
                continue
            if verdict.verdict == "not_proven" and verdict.failure_class in READ_FAILURES:
                attempt["handler"] = "no fallback left: the chain ends; the unit reads not proven with this class"
            attempts.append(attempt)
            break
        fields = dict(verdict.record_fields or {})
        settings = dict(fields.get("settings") or {})
        settings["route"] = {"order": list(route), "attempts": attempts, "reason": reason,
                             "verdict_tool": attempts[-1]["tool"], "real_valued": real}
        if real:
            settings["route"]["cbmc"] = NO_CBMC
        fields["settings"] = settings
        path = log.parent / "bounded-route.json"
        path.write_text(json.dumps(settings["route"], indent=1, sort_keys=True) + "\n")
        return Verdict(verdict=verdict.verdict, bounds=verdict.bounds, assumptions=verdict.assumptions,
                       counterexample=verdict.counterexample, failure_class=verdict.failure_class,
                       unreplayed_counterexample=verdict.unreplayed_counterexample, tools=verdict.tools,
                       peak_rss_bytes=verdict.peak_rss_bytes, record_fields=fields, pins=verdict.pins,
                       reports=tuple(reports) + tuple(verdict.reports) + (("bounded_route", path),))


ADAPTERS[NAME] = BoundedChain
