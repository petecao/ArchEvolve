"""ArchEvolve mode's proof path: the one final candidate artifact gets Extensa mode's proof steps.

Created: 2026-10-14 ET (Probata proof of concept ticket 18). Design: formal-verification map spec ("ArchEvolve
mode", "Refutation, repair and bugs", "Verifier lineup and order"; S1, S6; O1, O7); map decisions 25 items 2,
3, 5 and 26 item 7. Format: docs/reference/format-v0.4-archevolve-proof.md.

A rewrite proposal's candidate artifact, once `swdb certify` has certified it, runs through `swdb prove
--proof-path`:

- `bounded`: the bounded gate of Extensa mode (`swdb.bounded_gate.Gate`: both rungs at the contract's minimum
  bounds, threads raised to k on the multi-thread rung, `bounded_job_minutes` per job). A refutation calls
  13's counterexample-guided repair loop (`swdb.counterexample_repair.loop`, setting `archevolve`), the mode's
  allowed bounded correctness repair; each repaired candidate artifact is certified and comes back through
  this same gate. The 5-round cap and the reverted-repair flag stay in 13's loop.
- `unbounded` (S6): a candidate artifact the bounded rungs did not refute (proven, timed out, skipped) runs
  the unbounded rung, one proof record per proof unit, with the method version's hint budgets
  (`hint_rounds`, `hint_loop_wall_minutes`). A refuted candidate artifact never reaches it.

Neither step runs on a candidate artifact that is not certified (O1: proven requires certified). Budgets are
the method version's per-candidate budgets, the same as in Extensa mode; ArchEvolve mode has no campaign, so
no campaign call cap or lane-hours apply. Nothing here stores a level: `swdb candidate-level` reads it.

`swdb certify`'s hook (`record_derived`, from ticket 19's gap): a certified rewrite proposal's candidate
artifact whose contract is enabling (no offload) is recorded as a derived implementation in the store that
certified it (the research database), as the Extensa campaign loop does.
"""

import uuid
from argparse import Namespace
from pathlib import Path

from swdb.cli import Failure, UsageError

STEPS = ("bounded", "unbounded")
PLAN_FORMAT = "archevolve_proof_fixture.1"
GATE_BATCH = "batch.gate."
OUTSIDE_SUBSET, NO_CONTRACT_PROOF = "outside_cpp_subset", "no_contract_proof"
METHOD_BUDGETS = ("hint_rounds", "hint_loop_wall_minutes")


# --- what the candidate artifact is --------------------------------------------------------------

def _library(store_dir):
    from swdb.library import Library, default_root
    from swdb.store import Store
    root = default_root(Path(store_dir))
    if not root.is_dir():
        raise Failure(f"no library beside {store_dir}: the proof path reads contracts and the method version there")
    return Library(root, Store(Path(store_dir)))


def certified_contracts(store_dir, candidate_id):
    """The counted certified contracts of an ArchEvolve-mode candidate artifact; refuses any other one."""
    from swdb.extensa_boundary import candidate_certifications, certification_level
    from swdb.store import Store
    store = Store(Path(store_dir))
    candidate = store.get(candidate_id, "candidate")
    if candidate is None:
        raise Failure(f"candidate {candidate_id!r} does not exist")
    if candidate.get("mode") == "extensa":
        raise Failure(f"candidate {candidate_id} is an Extensa campaign's: its campaign runs its proof steps")
    library = _library(store_dir)
    level = certification_level(store, candidate_id, library)["level"]
    if level != "certified":
        raise Failure(f"candidate {candidate_id} is {level}: an uncertified or rejected candidate artifact runs no "
                      "proof step (proven requires certified)")
    _bound, counted = candidate_certifications(store, candidate_id, library)
    contracts = sorted({(r.get("candidate") or {}).get("contract") or (r.get("entry") or {}).get("id")
                        for r in counted if r.get("verdict") == "certified"} - {None})
    # Probata PoC 63: ArchEvolve mode uses shared certified contracts only, at every rewrite of a chain.
    from swdb import experimental_contracts
    problems = [experimental_contracts.shared_problem(library, c) for c in contracts]
    problems.append(experimental_contracts.lineage_problem(library, store.get(candidate.get("implementation") or "",
                                                                              "implementation")))
    found = [p for p in problems if p]
    if found:
        raise Failure(f"candidate {candidate_id} runs no ArchEvolve-mode proof step: " + "; ".join(found))
    return contracts


def _method(store_dir):
    from swdb import bounded_gate
    from swdb.library import default_root
    found = bounded_gate.method_version_of(default_root(Path(store_dir)))
    if found is None:
        raise Failure("no method version beside the records: the proof path reads its per-candidate budgets there")
    return found


def _gate(store_dir, runs_dir, adapter):
    from swdb import bounded_gate
    from swdb.library import default_root
    return bounded_gate.Gate(store_dir, Path(runs_dir), default_root(Path(store_dir)), adapter, _method(store_dir))


def _round(store_dir, candidate_id):
    """The candidate artifact's place in its repair chain: 0, or its repair lineage's round."""
    from swdb import counterexample_repair
    from swdb.store import Store
    return (counterexample_repair.lineage(Store(Path(store_dir)), candidate_id) or {}).get("round", 0)


# --- bounded: the gate, then counterexample-guided repair ------------------------------------------

def bounded(store_dir, candidate_id, *, runs_dir, adapter, provider_config=None, certify=None, db_path=None):
    """The bounded gate on a certified candidate artifact; a refutation goes to 13's repair loop.

    `certify(candidate_id, contracts)` certifies a repaired candidate artifact (default: the certification
    command, `certify_candidate`). Returns {candidate, gate, counterexample_repair, repairs, final_candidate}:
    `final_candidate` is the candidate artifact that goes on (to the evaluator and the unbounded rung), or
    None when every one was refuted or the repair ended without one."""
    store_dir, runs_dir = Path(store_dir), Path(runs_dir)
    contracts = certified_contracts(store_dir, candidate_id)
    gate = _gate(store_dir, runs_dir / "gate", adapter)
    result = {"candidate": candidate_id, "gate": _run_gate(gate, store_dir, candidate_id, contracts),
              "counterexample_repair": None, "repairs": [], "final_candidate": candidate_id}
    if not result["gate"]["refuted"]:
        return result
    result["final_candidate"] = None
    if provider_config is None:
        result["counterexample_repair"] = {"state": "not_started",
                                           "reason": "no provider configuration: pass --provider-config"}
        return result
    from swdb import counterexample_repair
    from swdb.store import Store
    certify = certify or (lambda cid, names: [certify_candidate(store_dir, cid, name, runs_dir=runs_dir / "certify")
                                              for name in names])
    gates = {}

    def certify_one(cid):
        certify(cid, contracts)

    def gate_one(cid):
        if (counterexample_repair.lineage(Store(store_dir), cid) or {}).get("reverted_repair"):
            return []           # a reverted repair applies no contract: no bounded job; it keeps its own level
        gates[cid] = _run_gate(gate, store_dir, cid, certified_contracts(store_dir, cid))
        return [job["record"] for job in gates[cid]["jobs"]]

    runs = runs_dir / "repairs"
    runs.mkdir(parents=True, exist_ok=True)
    outcome = counterexample_repair.loop(store_dir, result["gate"]["refutations"][0], runs_dir=runs,
                                         provider_config=provider_config, certify=certify_one, gate=gate_one,
                                         setting="archevolve", db_path=db_path)
    result["counterexample_repair"] = {key: outcome[key] for key in
                                       ("state", "reason", "cap", "rounds", "calls", "repairs", "reverted_repairs")}
    result["repairs"] = [{"round": row["round"], "proposal": row["proposal"], "candidate": row["candidate"],
                          "trigger": row["trigger"], "reverted_repair": row["reverted_repair"],
                          "gate": gates.get(row["candidate"])} for row in outcome["chain"]]
    if outcome["state"] in {"repaired", "reverted"}:
        result["final_candidate"] = outcome["chain"][-1]["candidate"]
    return result


def _run_gate(gate, store_dir, candidate_id, contracts):
    (Path(gate.runs_dir)).mkdir(parents=True, exist_ok=True)
    return gate.run(candidate_id, contracts, {"position": _round(store_dir, candidate_id)})


# --- unbounded: the unbounded rung (S6) -------------------------------------------------------------

def _gate_ran(store, candidate_id):
    prefix = GATE_BATCH + candidate_id + "."
    return any((r.data.get("subject") or {}).get("candidate") == candidate_id
               and str((r.data.get("job") or {}).get("batch", "")).startswith(prefix) for r in store.of_kind("proof"))


def unbounded(store_dir, candidate_id, *, runs_dir, adapter):
    """The unbounded rung on a certified candidate artifact the bounded rungs did not refute.

    One proof job per proof unit (one per rewrite contract): WP alone, then the contract seeds (when the
    contract has a counting contract proof), then at most `hint_rounds` proof-hint rounds, all within
    `hint_loop_wall_minutes`. Skips (O7): code outside the C++ subset, or no contract proof and no unit
    postcondition, writes a skip record. Returns {candidate, budgets, jobs, level}."""
    from swdb.level_rule import Rule
    from swdb.store import Store
    store_dir, runs_dir = Path(store_dir), Path(runs_dir)
    contracts = certified_contracts(store_dir, candidate_id)
    store = Store(store_dir)
    if not _gate_ran(store, candidate_id):
        raise Failure(f"candidate {candidate_id} has not run the bounded gate: run `swdb prove --proof-path bounded` "
                      "first")
    if Rule(store, _library(store_dir)).candidate(candidate_id)["refuted"]["flag"]:
        raise Failure(f"candidate {candidate_id} is refuted: a refuted candidate artifact never reaches the "
                      "unbounded rung")
    found = _method(store_dir)
    values = found.data.get("budgets") or {}
    for name in METHOD_BUDGETS:
        value = values.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise Failure(f"method version {found.id} has no budgets.{name}: the unbounded rung reads it there")
    budgets = {name: values[name] for name in METHOD_BUDGETS}
    gate = _gate(store_dir, runs_dir / "unbounded", adapter)
    context = {"position": _round(store_dir, candidate_id)}
    batch = f"batch.unbounded.{candidate_id}.{uuid.uuid4().hex[:8]}"
    rounds, jobs = budgets["hint_rounds"], []
    for position, contract in enumerate(contracts, start=1):
        job = {"contract": contract, "position": position}
        if adapter.outside_cpp_subset(candidate_id, **context):
            job.update(skip_reason=OUTSIDE_SUBSET)
        else:
            seeds = bool(gate.contract_proof(Store(store_dir), contract)["parts"])
            plan = adapter.unbounded_plan(candidate_id, contract, **context)
            if not seeds and not plan.get("unit_postcondition", True):
                job.update(skip_reason=NO_CONTRACT_PROOF)
        if "skip_reason" in job:
            job["record"] = _prove(store_dir, runs_dir, adapter, candidate_id, contract, batch, position,
                                   skip=job["skip_reason"])["id"]
            jobs.append(job)
            continue
        stages, proven = [], False
        for stage in ["wp"] + (["seeds"] if seeds else []) + list(range(1, int(rounds) + 1)):
            stages.append(stage)
            if stage == plan.get("proven_at"):
                proven = True
                break
        rounds -= sum(1 for stage in stages if isinstance(stage, int))
        script = adapter.unbounded_job(candidate_id, contract, proven, **context)
        record = _prove(store_dir, runs_dir, adapter, candidate_id, contract, batch, position,
                        adapter_name=script["adapter"], script=script.get("script"),
                        budget_minutes=budgets["hint_loop_wall_minutes"])
        job.update(record=record["id"], verdict=record["verdict"], stages=stages,
                   hint_rounds=sum(1 for stage in stages if isinstance(stage, int)))
        if record.get("failure_class"):
            job["failure_class"] = record["failure_class"]
        jobs.append(job)
    level = Rule(Store(store_dir), _library(store_dir)).candidate(candidate_id)
    return {"candidate": candidate_id, "method_version": gate.describe()["method_version"], "budgets": budgets,
            "batch": batch, "jobs": jobs, "level": level["level"]}


def _prove(store_dir, runs_dir, adapter, candidate_id, contract, batch, position, *, skip=None,
           adapter_name="scripted", script=None, budget_minutes=None):
    from swdb import proof
    runs = runs_dir / "unbounded"
    runs.mkdir(parents=True, exist_ok=True)
    args = Namespace(records=store_dir, candidate=candidate_id, function=adapter.proof_function(contract),
                     contract=contract, adapter=adapter_name, script=[script] if script else None, skip=skip,
                     runs_dir=runs, batch=batch, position=position, id=None, run_index=None, provider_kind=None,
                     provider_model=None, provider_effort=None, format="json", bounds=None, minimum_bounds=None,
                     budget_minutes=None if skip else budget_minutes)
    return proof.prove(args)["record"]


# --- the scripted proof plan (contract fixtures) -----------------------------------------------------

class ScriptedPlan:
    """The scripted adapter's proof plan: what each rung's job reports, per candidate artifact of the chain.

    Plan file (YAML): `plan: archevolve_proof_fixture.1`; `candidates`: one row per candidate artifact of the
    repair chain, in order (row 0 the submitted candidate artifact, row r the round-r repair; the last row
    repeats). A row may set `threads_1`, `threads_k` (a verdict word of `swdb.campaign_fixture.SCRIPTED`, or a
    mapping with `verdict` plus scripted-adapter keys; default proven), `unbounded` (`proven_at`: `wp`,
    `seeds`, a hint round, or absent: never; `unit_postcondition`, default true; `bounds`; `assumptions`), and
    `cpp_subset` (default true). Records are contract fixtures, never evidence."""

    def __init__(self, path, function, runs_dir):
        from swdb import yamlio
        data = yamlio.load(Path(path))
        if not isinstance(data, dict) or data.get("plan") != PLAN_FORMAT or not data.get("candidates"):
            raise UsageError(f"--plan {path} is not a {PLAN_FORMAT} plan with candidates")
        self.rows, self.function = list(data["candidates"]), function
        self.folder = Path(runs_dir) / "proof-scripts"

    def _row(self, position):
        return self.rows[min(position, len(self.rows) - 1)] or {}

    def proof_function(self, contract):
        return self.function

    def prepare_proofs(self, store_dir):
        """Contract proofs are the contract's own records in the store; a plan writes none."""

    def outside_cpp_subset(self, candidate_id, position=0, **_context):
        return self._row(position).get("cpp_subset", True) is False

    def bounded_job(self, candidate_id, contract, rung, bounds, position=0, **_context):
        from swdb.campaign_fixture import SCRIPTED
        spec = self._row(position).get(rung, "proven")
        spec = dict(spec) if isinstance(spec, dict) else {"verdict": spec}
        script = {**SCRIPTED[spec.pop("verdict")], **spec}
        return self._script(f"{candidate_id}.{contract}.{rung}", script)

    def unbounded_plan(self, candidate_id, contract, position=0, **_context):
        spec = self._row(position).get("unbounded") or {}
        return {"proven_at": spec.get("proven_at"), "unit_postcondition": spec.get("unit_postcondition", True)}

    def unbounded_job(self, candidate_id, contract, proven, position=0, **_context):
        from swdb.campaign_fixture import SCRIPTED
        spec = self._row(position).get("unbounded") or {}
        script = dict(SCRIPTED["unbounded" if proven else "hint_budget_spent"])
        for key in ("bounds", "assumptions", "tools"):
            if key in spec:
                script[key] = spec[key]
        return self._script(f"{candidate_id}.{contract}.unbounded", script)

    def _script(self, name, script):
        from swdb import yamlio
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{name}.{uuid.uuid4().hex[:8]}.yaml"
        path.write_text(yamlio.dumps(script))
        return {"adapter": "scripted", "script": path}


# --- `swdb certify`'s hook: derived implementations in ArchEvolve mode ----------------------------------

def record_derived(store_dir, certification, library_root=None):
    """Record a certified enabling rewrite proposal's candidate artifact as a derived implementation.

    Returns {derived_implementation} or {derived_note} (why none), or None when the certification is not of
    an ArchEvolve-mode rewrite proposal's candidate artifact. Never raises for a refused recording: the
    certification itself stands."""
    from swdb import derived
    from swdb.library import Library, default_root
    from swdb.store import Store
    pin = (certification or {}).get("candidate") or {}
    store_dir = Path(store_dir)
    store = Store(store_dir)
    candidate = store.get(pin.get("id") or "", "candidate")
    if candidate is None or not candidate.get("proposal") or candidate.get("mode") == "extensa":
        return None
    if certification.get("verdict") != "certified":
        return {"derived_note": "not recorded: the certification failed"}
    contract = pin.get("contract") or (certification.get("entry") or {}).get("id")
    root = Path(library_root) if library_root else default_root(store_dir)
    library = Library(root, store)
    if not derived.is_enabling(library, [store], contract):
        return {"derived_note": f"not recorded: {contract} is not an enabling contract (it offloads, or the store "
                                "lacks its strategy records)"}
    try:
        rid = derived.record(store_dir, candidate_id=candidate["id"], contracts=[contract],
                             links=[{"contract": contract, "record": certification["id"]}],
                             predecessor_snapshot=candidate["source_snapshot"], library=library)
    except Failure as exc:
        return {"derived_note": f"not recorded: {exc}"[:1000]}
    return {"derived_implementation": rid}


def certify_cli(args):
    """`swdb certify`: the certification command, then `record_derived` on its record.

    Moved here from `swdb.certification.run_cli` (2026-10-14 ET, suite fix): every certify procedure version's
    frozen source digest hashes swdb/certification.py, so the hook must live outside it. The non-profile body
    repeats `certification.run_cli`'s; a library-operation profile run has no hook and goes to it unchanged."""
    import json
    from swdb import certification
    from swdb.store import Store
    if getattr(args, "profile", None):
        return certification.run_cli(args)
    try:
        sizes = tuple(int(x) for x in args.tile_sizes.split(","))
        sources = tuple(int(x) for x in args.sources.split(","))
    except ValueError:
        raise UsageError("tile sizes and sources must be comma-separated integers") from None
    record = certification.certify(Store(Path(args.records)), args.entry_id, runs_dir=args.runs_dir,
                                   library=args.library, candidate=args.candidate, snapshot=args.snapshot,
                                   patch=args.patch, calibrate=args.calibrate, tile_sizes=sizes,
                                   threads=args.threads, sources=sources,
                                   candidate_record=getattr(args, "candidate_record", None),
                                   version=getattr(args, "command_version", None))
    output = {"id": record["id"], "verdict": record["verdict"], "matrix_cells": len(record["matrix"]),
              "negative_controls": len(record["negative_controls"])}
    output.update(record_derived(Path(args.records), record, args.library) or {})
    print(json.dumps(output, indent=2))
    return 0 if record["verdict"] == "certified" else 1


def certify_candidate(store_dir, candidate_id, contract, *, runs_dir=None, library_root=None):
    """The certification command on one candidate artifact, then its derived-implementation hook."""
    from swdb import certification
    from swdb.library import default_root
    from swdb.store import Store
    root = Path(library_root) if library_root else default_root(Path(store_dir))
    record = certification.certify(Store(Path(store_dir)), contract, runs_dir=runs_dir, library=root,
                                   candidate=candidate_id)
    record_derived(store_dir, record, root)
    return record


# --- `swdb prove --proof-path` ------------------------------------------------------------------------

def register_options(sub):
    group = sub.add_argument_group("ArchEvolve-mode proof path (ticket 18): a certified rewrite proposal's candidate "
                                   "artifact runs Extensa mode's proof steps")
    group.add_argument("--proof-path", choices=STEPS,
                       help="bounded: the bounded gate, then counterexample-guided repair of a refutation; "
                            "unbounded: the unbounded rung on a candidate artifact the gate did not refute")
    group.add_argument("--plan", type=Path, help="scripted adapter: the proof plan (format archevolve_proof_fixture.1)")
    group.add_argument("--provider-config", type=Path,
                       help="bounded: the rewriting provider of counterexample-guided repair (none: no repair)")


def run_cli(args):
    from swdb import proof
    if args.adapter != "scripted" or args.plan is None:
        raise UsageError("--proof-path needs --adapter scripted with --plan (no real verifier adapter is built yet)")
    for name in ("script", "skip", "bounds", "minimum_bounds", "budget_minutes", "batch", "id"):
        if getattr(args, name, None) not in (None, []):
            raise UsageError(f"--proof-path sets its own jobs: --{name.replace('_', '-')} is not allowed with it")
    runs = proof._outside_repo(args.runs_dir)
    store_dir = Path(args.records)
    certified_contracts(store_dir, args.candidate)          # refuse before any job or call
    adapter = ScriptedPlan(args.plan, args.function, runs)
    if args.proof_path == "unbounded":
        return unbounded(store_dir, args.candidate, runs_dir=runs, adapter=adapter)
    return bounded(store_dir, args.candidate, runs_dir=runs, adapter=adapter, provider_config=args.provider_config)
