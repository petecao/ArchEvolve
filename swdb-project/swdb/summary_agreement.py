"""Agreement of the summary forms on fixture scenarios (`swdb summary-agreement`).

Created: 2026-10-14 ET (Probata proof of concept ticket 23). Design: formal-verification map spec ("Verifier lineup
and order": one summary source; "DX100 proof semantics": the summary forms agree); map 12 item 8. Format:
docs/reference/format-v0.4-stubs-check-mode.md.

One summary source (a library entry's formal halves) gives every form a verifier reads. Since Yan-Ru's decision of
2026-10-14 13:19 ET (CBMC replaces SAW as the bounded verifier) the forms are two: the C stubs (CBMC on the C
lowering, `swdb.cbmc_translator`) and the ACSL contracts (Frama-C/WP, the callee's contract at its anchor). The
SAWScript form has no verifier in the lineup any more (assumption: it drops out of the check, as the ticket's own
crux-llvm assumption already allowed).

- A scenario is one proof unit (candidate, function, contract, bounds) expected `safe` or `buggy`.
- They agree on a safe scenario when both forms prove it; on a buggy scenario when the C-stub form refutes it and
  WP does not prove it (WP never refutes). Any other pair is a disagreement: the command stops with the scenario's
  name and both verdicts (exit 1). It writes no proof record: the jobs' logs stay in the runs folder.
- Tickets 29 and 30 run the same check on the proof-semantics fixtures and on each per-call `dxc_*` summary.
"""

import argparse
import uuid
from pathlib import Path

from swdb import paths, yamlio
from swdb.cli import Failure, UsageError

FORMS = (("c_stub", "cbmc"), ("acsl", "wp"))


def register_cli(commands):
    sub = commands.add_parser(
        "summary-agreement", help="check that the C-stub and ACSL forms of the summaries agree on fixture scenarios",
        description="Run each scenario's proof unit through the C-stub form (CBMC) and the ACSL form (WP): every safe "
                    "scenario must prove in both; on every buggy one the C-stub form refutes and WP does not prove. "
                    "A disagreement names the scenario and exits 1. Writes no proof record.")
    sub.add_argument("--records", type=Path, default=None)
    sub.add_argument("--scenarios", type=Path, required=True,
                     help="YAML list of {name, candidate, function, contract, bounds, expect: safe|buggy, defines?}")
    sub.add_argument("--runs-dir", type=Path, required=True, help="runs folder outside the repo")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=_cli)


def _cli(args):
    from swdb import proof, vocab
    from swdb.cli import _require_valid
    records = args.records or paths.RECORDS
    store = _require_valid(records)
    library = proof._library(store)
    method = proof._current_method(records)
    runs = proof._outside_repo(args.runs_dir)
    scenarios = yamlio.load(args.scenarios)
    if not isinstance(scenarios, list) or not scenarios:
        raise UsageError("--scenarios is a YAML list of scenarios")
    vocabs, _problems = vocab.load_all(paths.VOCAB)
    classes = proof.listed(vocabs, "failure_class")
    batch = f"agreement.{uuid.uuid4().hex[:8]}"
    results, disagreements = [], []
    for position, scenario in enumerate(scenarios, start=1):
        name, expect = scenario.get("name"), scenario.get("expect")
        if not name or expect not in ("safe", "buggy"):
            raise UsageError(f"scenario {position}: needs a name and expect: safe|buggy")
        candidate = store.get(scenario.get("candidate"), "candidate")
        if candidate is None:
            raise Failure(f"scenario {name}: candidate {scenario.get('candidate')!r} does not exist")
        contract = scenario.get("contract")
        if library is None or library.get(contract) is None:
            raise Failure(f"scenario {name}: contract {contract!r} is not in the library")
        artifact = candidate.get("artifact") or {}
        unit = proof.ProofUnit(scenario["candidate"], scenario["function"], artifact.get("path"),
                               artifact.get("sha256"), contract, library.content_sha256(contract))
        pins = proof._pins(store, candidate, unit, (), method)
        verdicts = {}
        for form, adapter_name in FORMS:
            call = argparse.Namespace(records=records, define=list(scenario.get("defines") or []), hint_file=None)
            adapter = proof._adapter(argparse.Namespace(adapter=adapter_name, **vars(call)), None, library, contract,
                                     method)
            rid = f"{batch}.{name}.{form}"
            record = proof._run_job(rid, unit, pins, adapter, runs, {"batch": batch, "position": position}, classes,
                                    method, bounds=scenario.get("bounds") if adapter_name == "cbmc" else None)
            verdicts[form] = {"verdict": record["verdict"], **({"failure_class": record["failure_class"]}
                                                                if record.get("failure_class") else {}),
                              "log": record["evidence"]["adapter_log"]["path"]}
        stub, acsl = verdicts["c_stub"]["verdict"], verdicts["acsl"]["verdict"]
        agree = (stub == "proven" and acsl == "proven") if expect == "safe" else \
            (stub == "refuted" and acsl != "proven")
        results.append({"name": name, "expect": expect, "forms": verdicts, "agree": agree})
        if not agree:
            disagreements.append(f"{name} (expected {expect}: C stub {stub}, ACSL {acsl})")
    report = {"check": "summary_forms_agreement", "forms": [f for f, _ in FORMS], "scenarios": results,
              "agree": not disagreements, "disagreements": disagreements}
    path = runs / f"{batch}.yaml"
    path.write_text(yamlio.dumps(report))
    if disagreements:
        raise Failure(f"the summary forms disagree on scenario(s): {'; '.join(disagreements)}. Report: {path}")
    return report
