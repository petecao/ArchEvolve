"""Synthetic record-policy tests; no real hardware/model performance evidence."""

from copy import deepcopy
import hashlib
import unittest

from archevolve.evolution_policy import COHORT_PINS, pareto_frontier, validate_prompt_revision


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def cohort(tier="analytical_planning"):
    return {**{k: sha("synthetic-" + k) for k in COHORT_PINS}, "evidence_tier": tier,
            "target_kind": "analytical_model" if tier == "analytical_planning" else "simulator",
            "latency_unit": "ms", "area_unit": "mm2", "area_convention": "incremental_accelerator"}


def record(cid, latency, area, c=None):
    c = deepcopy(c or cohort())
    target = c["evidence_tier"] == "target_measured"
    return {"candidate_id": cid, "candidate_sha256": sha(cid), "evaluated_candidate_sha256": sha(cid),
            "design_role": "accelerator_candidate", "status": "completed", "target_refuted": False,
            "cohort": c, "placeholder_fields": [], "model_applicability": "in_domain", "metrics_complete": True,
            "latency_ms": latency, "area_mm2": area, "evidence_refs": ["synthetic-fixture-only"],
            "correctness": "target_pass" if target else "functional_model_pass", "execution_witness": "pass",
            "legality": "discharged" if target else "conditional_reviewed",
            "evidence_kind": "target_measurement" if target else "analytical_model"}


def strategy():
    return {"strategy_id": "s0", "parent_strategy_id": None, "core_sha256": sha("core"),
            "task_sha256": sha("task"), "policy_sha256": sha("policy"),
            "editable": {"search_focus": "inspect one partition", "mutation_preferences": ["placement"],
                         "reasoning_guidance": ["preserve association"], "example_refs": ["fixture-reference"]},
            "feedback_refs": []}


def child_strategy():
    p = strategy()
    c = deepcopy(p)
    c.update(strategy_id="s1", parent_strategy_id="s0", feedback_refs=["fixture-feedback"])
    c["editable"]["reasoning_guidance"].append("show capacity lifetime")
    return p, c


class EvolutionPolicyTests(unittest.TestCase):
    def test_minimization_retains_tradeoffs_and_equal_points(self):
        rows = [record("fast", 4, 2), record("small", 6, 1), record("worse", 7, 3), record("tie", 4, 2)]
        before = deepcopy(rows)
        out = pareto_frontier(rows, cohort())
        self.assertEqual(out["frontier_ids"], ["fast", "small", "tie"])
        self.assertIsNone(out["selected_winner"])
        self.assertEqual(rows, before)

    def test_zero_time_placeholder_and_unknown_area_cannot_win(self):
        zero = record("zero", 1, 1)
        zero["placeholder_fields"] = ["accelerator_time_ms"]
        missing = record("missing", 2, None)
        out = pareto_frontier([zero, missing], cohort())
        self.assertFalse(out["frontier_ids"])
        self.assertEqual(out["status"], "no_rankable_candidates")
        self.assertIn("placeholder_or_unspecified_fields", out["excluded"]["zero"])
        self.assertIn("invalid_or_unknown_area", out["excluded"]["missing"])

    def test_different_workload_model_assumptions_or_target_never_mix(self):
        for field in ("task_sha256", "catalog_sha256", "workload_bundle_sha256", "evaluator_sha256", "assumption_set_sha256", "cost_model_sha256"):
            row = record("other", 1, 1)
            row["cohort"][field] = sha("different")
            self.assertFalse(pareto_frontier([row], cohort())["frontier_ids"])
        measured = cohort("target_measured")
        row = record("silicon", 1, 1, measured)
        row["cohort"]["target_kind"] = "hardware"
        self.assertFalse(pareto_frontier([row], measured)["frontier_ids"])

    def test_incomplete_cohort_units_or_basis_is_rejected(self):
        for key, value in (("baseline_sha256", None), ("area_unit", "gates"),
                           ("evidence_tier", "placeholder"), ("target_kind", "hardware")):
            c = cohort()
            c[key] = value
            with self.assertRaises(ValueError):
                pareto_frontier([], c)

    def test_nan_infinite_boolean_negative_or_zero_latency_is_excluded(self):
        for x in (float("nan"), float("inf"), True, -1, 0, None):
            self.assertFalse(pareto_frontier([record("bad", x, 1)], cohort())["frontier_ids"])
        for x in (float("nan"), float("inf"), False, -1):
            self.assertFalse(pareto_frontier([record("bad", 1, x)], cohort())["frontier_ids"])

    def test_zero_incremental_area_is_only_a_cpu_control(self):
        row = record("cpu", 8, 0)
        self.assertFalse(pareto_frontier([row], cohort())["frontier_ids"])
        row["design_role"] = "cpu_control"
        self.assertEqual(pareto_frontier([row], cohort())["frontier_ids"], ["cpu"])
        c = cohort()
        c["area_convention"] = "total_system"
        row["cohort"] = c
        self.assertFalse(pareto_frontier([row], c)["frontier_ids"])

    def test_refutation_incompletion_and_missing_witness_are_not_repaired_by_scores(self):
        for field, value in (("target_refuted", True), ("target_refuted", None), ("status", "inconclusive"),
                             ("execution_witness", "missing"), ("metrics_complete", False),
                             ("model_applicability", "unknown"), ("legality", "unknown")):
            row = record("bad", 1, 1)
            row[field] = value
            self.assertFalse(pareto_frontier([row], cohort())["frontier_ids"])

    def test_content_and_evidence_binding_are_required(self):
        row = record("stale", 1, 1)
        row["evaluated_candidate_sha256"] = sha("older")
        self.assertFalse(pareto_frontier([row], cohort())["frontier_ids"])
        row = record("unbacked", 1, 1)
        row["evidence_refs"] = []
        self.assertFalse(pareto_frontier([row], cohort())["frontier_ids"])

    def test_target_tier_requires_target_evidence(self):
        c = cohort("target_measured")
        good = record("target", 1, 1, c)
        self.assertEqual(pareto_frontier([good], c)["frontier_ids"], ["target"])
        for field, value in (("correctness", "functional_model_pass"), ("evidence_kind", "analytical_model"),
                             ("legality", "conditional_reviewed")):
            bad = deepcopy(good)
            bad[field] = value
            self.assertFalse(pareto_frontier([bad], c)["frontier_ids"])

    def test_duplicate_candidate_trials_must_be_aggregated_first(self):
        with self.assertRaises(ValueError):
            pareto_frontier([record("same", 1, 1), record("same", 2, 2)], cohort())
        with self.assertRaises(ValueError):
            pareto_frontier([None], cohort())

    def test_strategy_revision_is_pending_and_non_mutating(self):
        p, c = child_strategy()
        before = deepcopy((p, c))
        out = validate_prompt_revision(p, c)
        self.assertEqual(out["changed_sections"], ["reasoning_guidance"])
        self.assertFalse(out["promoted"])
        self.assertEqual((p, c), before)

    def test_core_task_and_policy_cannot_be_changed_by_prompt_evolution(self):
        for field in ("core_sha256", "task_sha256", "policy_sha256"):
            p, c = child_strategy()
            c[field] = sha("changed")
            with self.assertRaises(ValueError):
                validate_prompt_revision(p, c)

    def test_prompt_edits_require_parent_feedback_and_real_change(self):
        for error in ("parent", "same_id", "feedback", "noop", "unknown_field"):
            p, c = child_strategy()
            if error == "parent": c["parent_strategy_id"] = "other"
            if error == "same_id": c["strategy_id"] = p["strategy_id"]
            if error == "feedback": c["feedback_refs"] = []
            if error == "noop": c["editable"] = deepcopy(p["editable"])
            if error == "unknown_field": c["evaluator_override"] = "accept everything"
            with self.assertRaises(ValueError):
                validate_prompt_revision(p, c)


if __name__ == "__main__":
    unittest.main()
