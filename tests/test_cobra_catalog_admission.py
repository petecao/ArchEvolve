"""Binning may materialize tuples without becoming a destination-update engine."""
from copy import deepcopy
import json
import subprocess
import unittest
from unittest.mock import patch

import yaml

from archevolve.__main__ import ROOT, reference_context
from archevolve.hardware_catalog import load_catalog, query_catalog
from archevolve.intrinsic_handoff import build_handoff_artifacts
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates

DESIGN = "cobra-hpca2022-tuple-binning"


class COBRACatalogAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.digest = load_catalog(ROOT / "catalog/hardware-v0.1.yaml")
        cls.addition = json.loads((ROOT / "docs/proposals/cobra-hpca2022/proposed-addition.json").read_text())
        cls.design = next(d for d in cls.catalog["designs"] if d["id"] == DESIGN)
        cls.baseline = yaml.safe_load(subprocess.check_output(
            ["git", "show", "5608d112667b72e971b3093325edda7454f579c8:catalog/hardware-v0.1.yaml"], cwd=ROOT))
        cls.historical = cls.baseline
        cls.baseline = deepcopy(cls.catalog)
        cls.baseline["designs"] = [d for d in cls.catalog["designs"] if d["id"] != DESIGN]

    def test_admitted_record_and_original_designs_are_preserved(self):
        original = deepcopy(self.addition["designs"][0])
        for annotation in original.get("internal_mechanisms", []):
            self.assertIn(annotation, self.design.get("internal_mechanisms", []))
        original["internal_mechanisms"] = self.design["internal_mechanisms"]
        self.assertEqual(self.design, original)
        for field in ("sources", "claims"):
            for key, value in self.addition[field].items():
                self.assertEqual(self.catalog[field][key], value)
        for design in self.historical["designs"]:
            actual = next(d for d in self.catalog["designs"] if d["id"] == design["id"])
            self.assertTrue(set(design["source_refs"]) <= set(actual["source_refs"]))
            comparable = deepcopy(actual)
            if "internal_mechanisms" in design:
                comparable["internal_mechanisms"] = deepcopy(design["internal_mechanisms"])
            else:
                comparable.pop("internal_mechanisms", None)
            comparable["source_refs"] = design["source_refs"]
            self.assertEqual(comparable, design)
        result = query_catalog(self.catalog, design_id=DESIGN, operation="write")["matches"][0]
        self.assertEqual(result["status"], "mapping_reference")
        self.assertEqual(result["operation"], self.design["operations"][0])
        self.assertEqual(result["requirements"], self.design["requirements"])

    def test_types_patterns_and_old_value_are_not_inferred(self):
        query = dict(design_id=DESIGN, operation="write", subtype="tuple_bin",
                     address_pattern="indirect", payload_type="uint32", index_width_bits=32)
        self.assertEqual(query_catalog(self.catalog, **query)["matches"][0]["status"], "needs_evidence")
        result = query_catalog(self.catalog, **query, require_old_value=True)
        self.assertFalse(result["matches"])
        self.assertEqual(result["excluded"][0]["status"], "excluded")
        for operation, subtype in (("write", "scatter"), ("read", "gather"),
                                   ("read_modify_write", "add"), ("reduce", "add")):
            self.assertFalse(query_catalog(self.catalog, design_id=DESIGN, operation=operation,
                                           subtype=subtype)["matches"])

    def test_generic_bfs_and_explicit_handoff_keep_destination_updates_on_cpu(self):
        case = load_normalized(ROOT / "examples/received/bfs-sparse.features.v1.2.yaml", reference_context(ROOT))
        before = select_candidates(case, self.baseline, "bound-catalog", "fixed-review-digest", 12)
        after = select_candidates(case, self.catalog, "bound-catalog", "fixed-review-digest", 12)
        self.assertEqual(before, after)
        intent = deepcopy(after[0]["capability_requests"][0])
        intent.update(operation="write", subtype="tuple_bin", purpose="update", array="tuple_bins",
                      address_pattern="indirect", payload_type="uint32", index_width_bits=32,
                      require_old_value=False, mutable_target=False, statement_ids=[], source_locations=[],
                      statement_binding_status="unbound", missing_workload_evidence=[],
                      mapping_basis="Synthetic tuple-bin inspection, not a BFS transformation.")
        with patch("archevolve.evidence_select.capability_requests", return_value=([intent], [])):
            request, _ = select_candidates(case, self.catalog, "bound-catalog", self.digest, 2, [DESIGN])
        candidate = request["candidates"][1]
        self.assertEqual(candidate["candidate_scope"], "mapping_reference")
        self.assertEqual(candidate["execution_plan"]["rmw"], "retain_original_CPU_update")
        artifacts = build_handoff_artifacts(request, self.digest)
        draft = yaml.safe_load(artifacts["candidate-02/intrinsic-draft.yaml"])
        op = draft["operations"][0]
        self.assertEqual(op["postconditions"]["catalog_result"], self.design["operations"][0]["result"])
        self.assertEqual(op["completion"], self.design["operations"][0]["completion"])
        self.assertEqual(draft["requirements"], self.design["requirements"])
        self.assertEqual(op["postconditions"]["program_equivalence_status"], "not_established")
        self.assertIsNone(op["concrete_signature"])
        self.assertFalse(draft["readiness"]["correctness_verified"])


if __name__ == "__main__":
    unittest.main()
