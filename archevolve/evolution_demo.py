"""Scripted integration fixture: it exercises control flow, it does not learn.

All timings, resources, task labels, responses and reviews are synthetic. No
MAPLE/DX100 capability or real workload performance is asserted by this demo.
"""

from copy import deepcopy
from pathlib import Path
import argparse
import json

from .evolution_policy import COHORT_PINS
from .evolution_runtime import OfflineEvolution
from .evolution_store import EvolutionStore, digest


def seed_inputs():
    catalog = {"kind": "synthetic_catalog", "components": ["metadata_fetcher", "bulk_fetcher"]}
    strategy = {"search_focus": "Try bounded overlap", "mutation_preferences": ["scheduling"],
                "reasoning_guidance": ["Check capacity"], "example_refs": []}
    reflector = {"evidence_selection": "Inspect development outcomes", "diagnosis": "Find missing constraints",
                 "generalization": "Summarize observations", "revision_method": "Propose one supported revision"}
    tasks = []
    for name, split, batch in (("small-rows", "development", 2), ("large-rows", "development", 16),
                               ("unseen-small", "validation", 3), ("unseen-large", "validation", 24),
                               ("sealed-case", "holdout", 9)):
        cohort = {**{k: digest([name, k]) for k in COHORT_PINS}, "catalog_sha256": digest(catalog),
                  "evidence_tier": "analytical_planning", "target_kind": "analytical_model",
                  "latency_unit": "ms", "area_unit": "mm2", "area_convention": "incremental_accelerator"}
        tasks.append({"id": name, "split": split, "input": {"batch": batch}, "cohort": cohort, "baseline_latency_ms": 10.0})
    policy = {"mode": "synthetic_demo", "max_calls": 100, "max_tokens": 10000, "max_evaluations": 100,
              "tokens_per_call": 100, "proposals_per_task": 1, "area_limit_mm2": 2.0, "min_relative_gain": 0.05,
              "tasks": tasks}
    return {"catalog": catalog, "core": "Synthetic fixture only. Keep CPU updates unchanged; preserve bounded completion.",
            "policy": policy, "strategy": strategy, "reflector": reflector}


def scripted_proposer(request):
    ctx, op = request["context"], request["operation"]
    if op == "propose":
        aware = "Account for handoff cost" in ctx["strategy"]["reasoning_guidance"]
        overlap = not aware or ctx["task"]["input"]["batch"] >= 8
        content = {"parent_ref": ctx["parent_ref"], "mutation": "scheduling", "design": {"overlap": overlap},
                   "rationale": "Scripted fixture choice, not model reasoning.", "obligations": ["bounded completion"]}
    elif op == "revise_strategy":
        content = deepcopy(ctx["strategy"])
        if "Compare failures and successes" in ctx["reflector"]["diagnosis"]:
            content["reasoning_guidance"].append("Account for handoff cost")
        else:
            content["reasoning_guidance"].append("Check capacity again")
    elif op == "revise_reflector":
        content = deepcopy(ctx["reflector"])
        if "Compare failures and successes" in content["diagnosis"]:
            content["evidence_selection"] += "; retain contrasting cases across workload shapes"
        else:
            content["diagnosis"] = "Compare failures and successes before proposing a reusable rule"
    elif op == "learn_rule":
        support = [r for r, obs in zip(ctx["history_refs"], ctx["history"]) if obs["eligible"] and obs["task_id"] == "large-rows"]
        negatives = [r for r, obs in zip(ctx["history_refs"], ctx["history"]) if obs["task_id"] == "small-rows"]
        content = {"name": "Synthetic overlap lesson", "transformation": "Choose serial or overlapped stages",
                   "applicability": "Hypothesis: enough work must amortize coordination; fixture threshold is not hardware evidence.",
                   "obligations": ["bounded completion", "account for handoff"], "support_refs": support,
                   "counterexample_refs": negatives, "limitations": "Scripted toy example; no cross-workload hardware validation."}
    else:
        raise ValueError(f"No scripted response for {op}")
    return {"content": content, "tokens": 20}


def toy_evaluator(store):
    def evaluate(request):
        task, candidate = request["task"], request["candidate"]
        batch = task["input"]["batch"]
        latency = (12.0 if batch < 8 else 6.0) if candidate["design"]["overlap"] else 8.0
        evidence_ref = store.put({"kind": "synthetic_formula_trace", "batch": batch, "latency_ms": latency,
                                  "note": "Invented fixture values, not a hardware model or benchmark result."})
        return {"candidate_id": request["candidate_ref"], "candidate_sha256": request["candidate_ref"],
                "evaluated_candidate_sha256": request["candidate_ref"], "design_role": "accelerator_candidate",
                "status": "completed", "target_refuted": False, "cohort": task["cohort"], "placeholder_fields": [],
                "model_applicability": "in_domain", "metrics_complete": True, "latency_ms": latency, "area_mm2": 1.0,
                "evidence_refs": [evidence_ref], "correctness": "functional_model_pass", "execution_witness": "pass",
                "legality": "conditional_reviewed", "evidence_kind": "analytical_model", "synthetic": True}
    return evaluate


def demo(path):
    store = EvolutionStore(path)
    try:
        OfflineEvolution.initialize(store, **seed_inputs())
        loop = OfflineEvolution(store, scripted_proposer, toy_evaluator(store))
        loop.run_epoch()
        review = {"reviewer": "scripted-demo-review", "rationale": "Exercise the fixture state transition only.",
                  "semantic_review_passed": True, "synthetic": True}
        rule = loop.propose_rule()
        loop.admit_rule(rule, review)
        # First show the ordinary fixed-reflector strategy loop.
        strategy = loop.revise("strategy")
        strategy_trial = loop.trial(strategy)  # equal scores: no promotion
        first_reflector = loop.active("reflector")
        revision = loop.revise("reflector")
        reflector_trial = loop.trial(revision)
        loop.promote(reflector_trial, review)
        # Accepted reflector is now the author of ordinary strategy updates.
        strategy = loop.revise("strategy")
        accepted_strategy_trial = loop.trial(strategy)
        loop.promote(accepted_strategy_trial, review)
        loop.run_epoch()
        recursive_revision = loop.revise("reflector")
        recursive_trial = loop.trial(recursive_revision)  # no extra benefit: retain R1
        # Explicitly exercise rollback and preserve all experiment memory.
        loop.rollback("reflector", review)
        return {"synthetic": True, "hardware_improvement_claimed": False, "learned_by_model": False,
                "fixed_reflector_trial": strategy_trial, "reflector_trial": reflector_trial,
                "accepted_strategy_trial": accepted_strategy_trial, "revised_reflector": revision,
                "recursive_revision": recursive_revision, "recursive_trial": recursive_trial,
                "rollback_restored_seed": loop.active("reflector") == first_reflector,
                "usage": loop.usage(), "memory": store.export()}
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("demo", help="Run a deterministic synthetic fixture in a fresh database")
    run.add_argument("--store", required=True)
    run.add_argument("--output", required=True)
    export = sub.add_parser("export", help="Read and hash-check all stored objects")
    export.add_argument("--store", required=True)
    export.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "demo":
        report = demo(args.store)
    else:
        if not Path(args.store).is_file():
            parser.error("Store does not exist")
        store = EvolutionStore(args.store)
        try:
            report = store.export()
        finally:
            store.close()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": args.output, "synthetic": report.get("synthetic"), "usage": report.get("usage")}))


if __name__ == "__main__":
    main()
