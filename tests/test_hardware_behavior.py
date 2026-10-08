from copy import deepcopy
import hashlib
import unittest

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.hardware_behavior import describe_behavior, render_behavior, validate_behavior
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from tools.render_mermaid import RequestError, load_request


class HardwareBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.input = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        self.catalog_path = ROOT / "examples/received/eric-hardware-catalog.20261006.yaml"
        self.catalog, self.digest = load_request(self.catalog_path)
        self.case = load_normalized(self.input, reference_context(ROOT))
        self.request, _ = select_candidates(self.case, self.catalog, str(self.catalog_path), self.digest,
                                            4, ["dx100-artifact-e4fc4af", "maple-isca2022"])

    def test_dx100_benefit_is_conditional_and_preserves_logical_consumers(self):
        c = self.request["candidates"][1]
        r = describe_behavior(self.request, c)
        self.assertTrue(any(m["kind"] == "coalescing" and m["status"] == "described" for m in r["internal_mechanisms"]))
        self.assertTrue(r["why_it_may_accelerate"])
        self.assertTrue(all(h["basis"].startswith("derived_reasoning") and h["evaluated"] is False for h in r["why_it_may_accelerate"]))
        self.assertTrue(all(set(h["claim_refs"]) <= set(r["source_evidence"]["claims"]) for h in r["why_it_may_accelerate"]))
        self.assertEqual(r["implementation_requirements"], c["requirements"])
        self.assertEqual(r["selected_configuration"], {})
        self.assertFalse(r["proof_status"]["performance_evaluated"])

    def test_annotated_absence_does_not_create_mechanisms_or_benefits(self):
        c = deepcopy(self.request["candidates"][1])
        for m in c["mechanism_context"]["annotations"]:
            m.update(status="unknown", description=None, claim_refs=[])
        c["mechanism_context"]["performance_hypotheses"] = []
        r = describe_behavior(self.request, c)
        self.assertFalse(r["why_it_may_accelerate"])
        self.assertIn("No source-supported payoff hypothesis", render_behavior(r))

    def test_maple_catalog_hypothesis_and_modes_remain_separate(self):
        for c in self.request["candidates"][2:]:
            r = describe_behavior(self.request, c)
            self.assertTrue(all(h["basis"] == "catalog_conditional_hypothesis" for h in r["why_it_may_accelerate"]))
            roles = {o["execution_role"] for o in r["desired_observable_semantics"]}
            self.assertEqual(roles, {"assist"} if c["candidate_scope"] == "read_assist" else {"execute"})
            self.assertEqual(r["design_revision"], c["catalog_design_revision"])
            for o, original in zip(r["desired_observable_semantics"], c["operation_options"]):
                self.assertEqual(o["completion"], original["operation"]["completion"])
                self.assertEqual(o["result"], original["operation"]["result"])

    def test_description_cannot_promote_ordering_or_unlocated_hypothesis(self):
        c = self.request["candidates"][1]
        for error in ("order", "support", "hypothesis"):
            r = describe_behavior(self.request, c)
            if error == "order":
                r["desired_observable_semantics"][0]["ordering"]["description"] = "global FIFO guaranteed"
            elif error == "support":
                r["desired_observable_semantics"][0]["support"] = "verified"
            else:
                r["why_it_may_accelerate"][0]["claim_refs"] = ["unlocated"]
            with self.assertRaises(RequestError):
                validate_behavior(r, c)

    def test_generator_emits_behavior_without_mutating_old_handoff(self):
        old = ROOT / "runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/intrinsic-draft.yaml"
        before = hashlib.sha256(old.read_bytes()).hexdigest()
        kwargs = dict(max_candidates=4, focus_design_ids=["dx100-artifact-e4fc4af", "maple-isca2022"])
        files, _ = prepare_run([self.input], self.catalog_path, **kwargs)
        again, _ = prepare_run([self.input], self.catalog_path, **kwargs)
        self.assertEqual(files, again)
        root = "case-01/handoffs/candidate-02/"
        r = yaml.safe_load(files[root + "hardware-behavior.yaml"])
        self.assertEqual(r["catalog_sha256"], self.digest)
        self.assertIn("What software must observe", files[root + "hardware-behavior.md"])
        self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
