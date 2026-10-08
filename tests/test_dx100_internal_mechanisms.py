from copy import deepcopy
import unittest

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.comparison import build_comparison_artifacts, compare_designs
from archevolve.hardware_catalog import load_catalog, query_catalog
from archevolve.mechanisms import mechanism_context
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates


class DX100InternalMechanismTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "catalog/hardware-v0.1.yaml"
        self.catalog, self.digest = load_catalog(self.path)
        self.designs = {d["id"]: d for d in self.catalog["designs"]}
        self.input = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"

    def test_paper_and_model_mechanisms_keep_separate_evidence_editions(self):
        for did, kind in (("dx100-paper-v2", "paper_specification"),
                          ("dx100-artifact-e4fc4af", "code_inspection")):
            for mechanism in self.designs[did]["internal_mechanisms"]:
                for ref in mechanism["claim_refs"]:
                    claim = self.catalog["claims"][ref]
                    self.assertEqual(claim["evidence_kind"], kind)
                    self.assertTrue(claim["locator"])
                    self.assertTrue(claim["limitations"])
                    for source in claim["source_refs"]:
                        self.assertIn(source, self.designs[did]["source_refs"])
                        self.assertEqual(len(self.catalog["sources"][source]["sha256"]), 64)
        paper = mechanism_context(self.designs["dx100-paper-v2"])
        self.assertIn("completion", paper["missing_kinds"])
        self.assertIn("publisher", str(self.catalog["sources"]["dx100-paper"]).lower())

    def test_annotations_do_not_change_typed_operation_queries(self):
        stripped = deepcopy(self.catalog)
        for design in stripped["designs"]:
            if design["id"].startswith("dx100-"):
                design.pop("internal_mechanisms", None)
        for did in ("dx100-paper-v2", "dx100-artifact-e4fc4af"):
            for subtype, width in (("gather", 32), ("gather", 64), ("stream_load", 32)):
                query = dict(design_id=did, operation="read", subtype=subtype,
                             payload_type="int32", index_width_bits=width)
                self.assertEqual(query_catalog(self.catalog, **query), query_catalog(stripped, **query))
            query = dict(design_id=did, operation="read_modify_write", subtype="cas", require_old_value=True)
            self.assertEqual(query_catalog(self.catalog, **query), query_catalog(stripped, **query))

    def test_comparison_preserves_mechanism_claim_closure_and_unknown_performance(self):
        case = load_normalized(self.input, reference_context(ROOT))
        request, _ = select_candidates(case, self.catalog, str(self.path), self.digest, 1)
        ids = ["dx100-paper-v2", "dx100-artifact-e4fc4af", "maple-isca2022"]
        comparison = compare_designs(request, self.catalog, ids)
        self.assertFalse(comparison["performance_evaluated"])
        self.assertIsNone(comparison["speedup"])
        for design in comparison["designs"][:2]:
            for mechanism in design["mechanism_context"]["annotations"]:
                for ref in mechanism["claim_refs"]:
                    self.assertEqual(design["source_evidence"]["claims"][ref], self.catalog["claims"][ref])
        self.assertIn("coalescing", comparison["designs"][2]["mechanism_context"]["missing_kinds"])
        rendered = build_comparison_artifacts(request, self.catalog, ids)
        text = rendered["hardware-comparison.md"]
        for detail in ("Previous i", "next_itr", "producer wait alone", "until retry", "TD[itr]", "reset/reusable"):
            self.assertIn(detail, text)

    def test_end_to_end_handoff_renders_details_without_inventing_wiring(self):
        artifacts, _ = prepare_run([self.input], self.path, max_candidates=2,
                                  focus_design_ids=["dx100-artifact-e4fc4af"])
        candidate = yaml.safe_load(artifacts["case-01/handoffs/candidate-02/candidate.yaml"])
        context = candidate["mechanism_context"]
        self.assertEqual(context["missing_kinds"], [])
        self.assertIsNone(context["hardware_structure"])
        self.assertFalse(context["performance_hypotheses"])
        self.assertEqual(candidate["hardware"]["connections"], [])
        self.assertIn("dx-internal-c11", candidate["source_evidence"]["claims"])
        diagrams = "\n".join(value for name, value in artifacts.items() if name.endswith(".mmd"))
        self.assertIn("TD#91;itr#93;", diagrams)
        self.assertIn("until retry", diagrams)
        draft = yaml.safe_load(artifacts["case-01/handoffs/candidate-02/intrinsic-draft.yaml"])
        self.assertTrue(all(op["concrete_signature"] is None for op in draft["operations"]))
        self.assertFalse(draft["readiness"]["correctness_verified"])


if __name__ == "__main__":
    unittest.main()
