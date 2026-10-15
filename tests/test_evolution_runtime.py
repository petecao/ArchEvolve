"""Behavioral tests of the offline state machine; all evaluator numbers are synthetic."""

from pathlib import Path
import tempfile
import unittest

from archevolve.evolution_demo import demo, seed_inputs, scripted_proposer, toy_evaluator
from archevolve.evolution_runtime import OfflineEvolution
from archevolve.evolution_store import EvolutionStore, digest


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.sqlite"
        self.store = EvolutionStore(self.path)
        self.inputs = seed_inputs()
        OfflineEvolution.initialize(self.store, **self.inputs)
        self.loop = OfflineEvolution(self.store, scripted_proposer, toy_evaluator(self.store))
        self.review = {"reviewer": "test", "rationale": "Synthetic state-machine test", "semantic_review_passed": True, "synthetic": True}

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def revision_and_trial(self):
        self.loop.run_epoch()
        revision = self.loop.revise("reflector")
        return revision, self.loop.trial(revision)

    def test_complete_demo_recursion_rejection_and_rollback(self):
        report = demo(Path(self.temp.name) / "demo.sqlite")
        memory = report["memory"]["objects"]
        self.assertFalse(report["hardware_improvement_claimed"])
        self.assertTrue(report["rollback_restored_seed"])
        self.assertFalse(memory[report["fixed_reflector_trial"]]["eligible_for_review"])
        self.assertTrue(memory[report["reflector_trial"]]["eligible_for_review"])
        self.assertFalse(memory[report["recursive_trial"]]["eligible_for_review"])
        self.assertEqual(memory[report["recursive_revision"]]["author_reflector"], report["revised_reflector"])
        self.assertEqual(memory[report["recursive_revision"]]["parent_ref"], report["revised_reflector"])

    def test_epoch_archives_lineage_and_durable_restart(self):
        refs = self.loop.run_epoch()
        for ref in refs:
            obs = self.store.get(ref)
            candidate = self.store.get(obs["candidate_ref"])
            self.assertEqual(candidate["parent_ref"], obs["parent_ref"])
            self.assertIsNotNone(self.store.get(obs["evaluation_ref"]))
        previous = self.loop.usage()
        self.store.close()
        self.store = EvolutionStore(self.path)
        restarted = OfflineEvolution(self.store, scripted_proposer, toy_evaluator(self.store))
        self.assertEqual(restarted.history(), refs)
        self.assertEqual(restarted.usage(), previous)

    def test_holdout_and_validation_never_enter_reflection(self):
        revision, trial = self.revision_and_trial()
        validation = self.store.get(trial)["results"]["parent"]["observations"][0]
        with self.assertRaisesRegex(ValueError, "development"):
            self.loop._context(self.loop.active("reflector"), self.loop.active("strategy"), [validation])
        for event in self.store.events("call_start"):
            ctx = event["record"]["context"]
            self.assertNotIn("sealed-case", str(ctx))
            self.assertTrue(all(o["split"] == "development" for o in ctx["history"]))
        self.assertNotIn(validation, self.loop.history())

    def test_trial_has_frozen_history_and_equal_allowances(self):
        _, trial_ref = self.revision_and_trial()
        trial = self.store.get(trial_ref)
        self.assertEqual(trial["results"]["parent"]["usage"], trial["results"]["child"]["usage"])
        requests = [e["record"] for e in self.store.events("call_start") if e["record"]["operation"] == "revise_strategy"]
        self.assertEqual(requests[0]["context"]["history_refs"], requests[1]["context"]["history_refs"])
        self.assertEqual(requests[0]["context"]["strategy_ref"], requests[1]["context"]["strategy_ref"])

    def test_reflector_cannot_edit_policy_and_catalog_unchanged(self):
        self.loop.run_epoch()
        catalog_ref = self.loop.campaign["catalog_ref"]
        def bad(request):
            response = scripted_proposer(request)
            response["content"]["evaluator_override"] = "accept"
            return response
        self.loop.proposer = bad
        with self.assertRaisesRegex(ValueError, "Only reflector"):
            self.loop.revise("reflector")
        self.assertEqual(self.store.get(catalog_ref), self.inputs["catalog"])

    def test_rule_requires_review_links_evidence_and_does_not_write_catalog(self):
        self.loop.run_epoch()
        rule = self.loop.propose_rule()
        self.assertEqual(self.loop.rules(), [])
        with self.assertRaises(ValueError):
            self.loop.admit_rule(rule, {**self.review, "semantic_review_passed": False})
        self.loop.admit_rule(rule, self.review)
        self.assertEqual(self.loop.rules(), [rule])
        self.assertFalse(self.store.events("rule_admission")[0]["record"]["catalog_claim_admitted"])
        self.assertEqual(self.store.get(self.loop.campaign["catalog_ref"]), self.inputs["catalog"])
        self.assertTrue(self.store.get(rule)["content"]["counterexample_refs"])

    def test_rule_cannot_claim_nonimproving_observation_as_support(self):
        self.loop.run_epoch()
        def bad(request):
            result = scripted_proposer(request)
            result["content"]["support_refs"] = [self.loop.history()[0]]
            result["content"]["counterexample_refs"] = []
            return result
        self.loop.proposer = bad
        with self.assertRaisesRegex(ValueError, "baseline"):
            self.loop.propose_rule()

    def test_review_required_and_stale_trial_cannot_be_promoted(self):
        revision, trial = self.revision_and_trial()
        with self.assertRaises(ValueError):
            self.loop.promote(trial, {})
        self.loop.promote(trial, self.review)
        self.assertEqual(self.loop.active("reflector"), revision)
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.loop.promote(trial, self.review)
        self.loop.rollback("reflector", self.review)
        self.assertEqual(self.loop.active("reflector"), self.store.get(revision)["parent_ref"])

    def test_changed_rule_context_blocks_promotion(self):
        _, trial = self.revision_and_trial()
        rule = self.loop.propose_rule()
        self.loop.admit_rule(rule, self.review)
        with self.assertRaisesRegex(ValueError, "rule context"):
            self.loop.promote(trial, self.review)

    def test_placeholder_refuted_mismatched_and_missing_evidence_cannot_win(self):
        for field, value in (("placeholder_fields", ["accelerator_time"]), ("target_refuted", True),
                             ("candidate_sha256", digest("wrong")), ("evidence_refs", [digest("missing")]),
                             ("synthetic", False), ("execution_witness", "missing")):
            with self.subTest(field=field):
                base = toy_evaluator(self.store)
                def evaluate(request):
                    result = base(request)
                    result[field] = value
                    return result
                self.loop.evaluator = evaluate
                observations = self.loop.run_epoch()
                self.assertTrue(all(not self.store.get(r)["eligible"] for r in observations))

    def test_bad_candidate_and_evaluator_failure_are_archived(self):
        def bad(request):
            return {"content": {"mutation": "imaginary"}, "tokens": 1}
        self.loop.proposer = bad
        self.assertTrue(all(not self.store.get(r)["eligible"] for r in self.loop.run_epoch()))
        self.assertEqual(self.loop.usage()["evaluations"], 0)
        self.loop.proposer = scripted_proposer
        def failed(request):
            raise RuntimeError("missing simulator")
        self.loop.evaluator = failed
        self.assertTrue(all(not self.store.get(r)["eligible"] for r in self.loop.run_epoch()))
        self.assertEqual(self.loop.usage()["evaluations"], 2)

    def test_provider_failure_reserves_tokens_and_incomplete_trial_never_promotes(self):
        self.loop.run_epoch()
        revision = self.loop.revise("reflector")
        before = self.loop.usage()
        def failed(request):
            raise RuntimeError("adapter unavailable")
        self.loop.proposer = failed
        with self.assertRaises(RuntimeError):
            self.loop.trial(revision)
        self.assertEqual(self.loop.usage()["tokens"], before["tokens"] + self.inputs["policy"]["tokens_per_call"])
        failure = self.store.events("trial_incomplete")[-1]["ref"]
        with self.assertRaisesRegex(ValueError, "Completed"):
            self.loop.promote(failure, self.review)

    def test_budget_exhaustion_is_durable_and_trial_preflight_is_atomic(self):
        self.store.close()
        self.store = EvolutionStore(Path(self.temp.name) / "small.sqlite")
        inputs = seed_inputs()
        inputs["policy"]["max_calls"] = 3
        OfflineEvolution.initialize(self.store, **inputs)
        loop = OfflineEvolution(self.store, scripted_proposer, toy_evaluator(self.store))
        loop.run_epoch()
        revision = loop.revise("reflector")
        with self.assertRaisesRegex(ValueError, "both trial arms"):
            loop.trial(revision)
        self.assertEqual(self.store.events("trial_start"), [])
        with self.assertRaisesRegex(ValueError, "budget"):
            loop.run_epoch()
        self.assertEqual(loop.usage()["calls"], 3)

    def test_modified_object_is_detected(self):
        ref = self.loop.active("reflector")
        with self.store.db:
            self.store.db.execute("UPDATE objects SET payload='{}' WHERE hash=?", (ref,))
        with self.assertRaisesRegex(ValueError, "Corrupt"):
            self.loop.active("reflector")

    def test_better_candidate_becomes_parent_within_epoch(self):
        store = EvolutionStore(Path(self.temp.name) / "parents.sqlite")
        try:
            inputs = seed_inputs()
            inputs["policy"]["proposals_per_task"] = 2
            OfflineEvolution.initialize(store, **inputs)
            loop = OfflineEvolution(store, scripted_proposer, toy_evaluator(store))
            refs = loop.run_epoch()
            first, second = [store.get(r) for r in refs if store.get(r)["task_id"] == "large-rows"]
            self.assertEqual(second["parent_ref"], first["candidate_ref"])
            self.assertEqual(loop.usage()["evaluations"], 4)
        finally:
            store.close()

    def test_invalid_receipt_reserves_full_allowance(self):
        def over_budget(request):
            response = scripted_proposer(request)
            response["tokens"] = request["max_tokens"] + 1
            return response
        self.loop.proposer = over_budget
        with self.assertRaisesRegex(ValueError, "token receipt"):
            self.loop.run_epoch()
        self.assertEqual(self.loop.usage()["tokens"], self.inputs["policy"]["tokens_per_call"])
        self.assertEqual(len(self.store.events("call_failure")), 1)

    def test_reflection_receives_resolved_evidence_and_decision_history(self):
        self.loop.run_epoch()
        self.loop.revise("reflector")
        context = self.store.events("call_start")[-1]["record"]["context"]
        self.assertEqual(context["history"][0]["evaluation"]["latency_ms"], 12.0)
        self.assertIn(self.loop.active("strategy"), context["strategy_decisions"])
        self.assertEqual(context["history"][0]["candidate"]["mutation"], "scheduling")

    def test_proposer_does_not_read_reflector_procedure_directly(self):
        self.loop.run_epoch()
        for event in self.store.events("call_start"):
            if event["record"]["operation"] == "propose":
                self.assertNotIn("reflector", event["record"]["context"])
                self.assertIn("strategy", event["record"]["context"])

    def test_repeated_trials_keep_distinct_attempt_identities(self):
        revision, first = self.revision_and_trial()
        second = self.loop.trial(revision)
        self.assertNotEqual(self.store.get(first)["trial_id"], self.store.get(second)["trial_id"])

    def test_invalid_task_pins_rejected_before_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvolutionStore(Path(directory) / "memory.sqlite")
            try:
                inputs = seed_inputs()
                inputs["policy"]["tasks"][0]["cohort"]["catalog_sha256"] = digest("other")
                with self.assertRaisesRegex(ValueError, "catalog snapshot"):
                    OfflineEvolution.initialize(store, **inputs)
                self.assertEqual(store.events(), [])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
