"""The admitted TMU mapping must retain its event contract and evidence limits."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.hardware_catalog import load_catalog, query_catalog
from archevolve.intrinsic_handoff import build_handoff_artifacts
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates

DESIGN = "tmu-micro2023-fig8-spmv"
SUBTYPE = "csr_spmv_two_lane_operand_event_supply"


class TMUCatalogAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.digest = load_catalog(ROOT / "catalog/hardware-v0.1.yaml")
        cls.proposal = json.loads((ROOT / "docs/proposals/tmu-micro2023/proposed-catalog.json").read_text())
        cls.design = next(d for d in cls.catalog["designs"] if d["id"] == DESIGN)

    def test_admission_preserves_the_exact_independently_reviewed_record(self):
        original = deepcopy(self.proposal["designs"][0])
        for annotation in original.get("internal_mechanisms", []):
            self.assertIn(annotation, self.design.get("internal_mechanisms", []))
        original["internal_mechanisms"] = self.design["internal_mechanisms"]
        self.assertEqual(self.design, original)
        for field in ("sources", "claims"):
            for key, value in self.proposal[field].items():
                self.assertEqual(self.catalog[field][key], value)
        result = query_catalog(self.catalog, design_id=DESIGN, operation="read", subtype=SUBTYPE)
        self.assertEqual(result["matches"][0]["status"], "mapping_reference")
        self.assertEqual(result["matches"][0]["requirements"], self.design["requirements"])
        typed = query_catalog(self.catalog, design_id=DESIGN, operation="read", subtype=SUBTYPE,
                              payload_type="float32", index_width_bits=32)["matches"][0]
        self.assertEqual(typed["status"], "needs_evidence")
        self.assertEqual(typed["missing_capability_evidence"], ["payload_types", "index_width_bits"])

    def test_normal_bfs_generation_does_not_invent_a_tmu_callback_mapping(self):
        path = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        for subtype in ("gather", "stream_load"):
            result = query_catalog(self.catalog, operation="read", subtype=subtype)
            self.assertFalse(any(m["design_id"] == DESIGN for m in result["matches"]))
        artifacts, _ = prepare_run([path], ROOT / "catalog/hardware-v0.1.yaml",
                                  max_candidates=2, focus_design_ids=[DESIGN])
        request = yaml.safe_load(artifacts["case-01/hardware-request.yaml"])
        self.assertEqual([c["catalog_entry"] for c in request["candidates"]], ["cpu-baseline"])

    def test_explicit_mapping_handoff_preserves_events_cpu_work_and_unknowns(self):
        case = load_normalized(ROOT / "examples/received/bfs-sparse.features.v1.2.yaml", reference_context(ROOT))
        generic, _ = select_candidates(case, self.catalog, "admitted-catalog", self.digest, 2, [DESIGN])
        intent = deepcopy(generic["capability_requests"][0])
        intent.update(operation="read", subtype=SUBTYPE, address_pattern="indirect",
                      payload_type=None, index_width_bits=None, require_old_value=False,
                      purpose="read", mutable_target=False,
                      missing_workload_evidence=["workload_payload_type", "workload_index_width"],
                      mapping_basis="Synthetic explicit mapping intent; no BFS compatibility assertion.")
        with patch("archevolve.evidence_select.capability_requests", return_value=([intent], [])):
            request, _ = select_candidates(case, self.catalog, "admitted-catalog", self.digest, 2, [DESIGN])
        candidate = request["candidates"][1]
        self.assertEqual(candidate["candidate_scope"], "mapping_reference")
        self.assertEqual(candidate["status"], "needs_evidence")
        artifacts = build_handoff_artifacts(request, self.digest)
        draft = yaml.safe_load(artifacts["candidate-02/intrinsic-draft.yaml"])
        self.assertEqual(draft["operations"][0]["postconditions"]["catalog_result"], self.design["operations"][0]["result"])
        self.assertEqual(draft["operations"][0]["design_interface"], self.design["interface"])
        self.assertEqual(draft["requirements"], self.design["requirements"])
        self.assertIsNone(draft["operations"][0]["concrete_signature"])
        self.assertFalse(draft["readiness"]["correctness_verified"])


if __name__ == "__main__":
    unittest.main()
