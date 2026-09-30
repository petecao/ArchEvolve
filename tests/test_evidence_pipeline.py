from copy import deepcopy
import unittest
from unittest.mock import patch

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.evidence_select import capability_requests
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from tools.render_mermaid import load_request, validate_request


class EvidencePipelineTests(unittest.TestCase):
    def setUp(self):
        self.sparse = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        self.dense = ROOT / "examples/received/bfs-fully-connected.features.v1.2.yaml"
        self.catalog_path = ROOT / "catalog/hardware-v0.1.yaml"
        self.methods_path = ROOT / "examples/received/peter-measurement-methods.v1.2.yaml"
        self.catalog, self.catalog_hash = load_request(self.catalog_path)
        self.case = load_normalized(self.sparse, reference_context(ROOT))

    def choose(self, case=None, max_candidates=4):
        return select_candidates(self.case if case is None else case, self.catalog, str(self.catalog_path), self.catalog_hash, max_candidates)

    def test_source_shapes_and_cas_are_requested_separately(self):
        requests, gaps = capability_requests(self.case)
        self.assertFalse(gaps)
        shape = {(r["array"],r["purpose"]):(r["subtype"],r["address_pattern"],r["payload_type"],r["index_width_bits"]) for r in requests}
        self.assertEqual(shape[("queue.shared","read")], ("stream_load","sequential","int32",None))
        self.assertEqual(shape[("VertexOffsets","read")], ("gather","indirect","int32",32))
        self.assertEqual(shape[("g.out_neighbors_","read")], ("gather","ranged_indirect","int32",32))
        self.assertEqual(shape[("parent","update")], ("cas","indirect","int32",32))
        self.assertTrue(next(r for r in requests if r["array"] == "parent" and r["purpose"] == "read")["mutable_target"])
        self.assertFalse(next(r for r in requests if r["purpose"] == "update")["require_old_value"])

    def test_dense_regular_distances_do_not_erase_loaded_index_syntax(self):
        case = load_normalized(self.dense, reference_context(ROOT))
        requests, _ = capability_requests(case)
        offsets = next(r for r in requests if r["array"] == "VertexOffsets")
        self.assertTrue(case["signals"]["reported_near_unit_indices"])
        self.assertEqual(offsets["address_pattern"], "indirect")
        self.assertEqual(offsets["subtype"], "gather")

    def test_dx100_cas_is_excluded_and_unknown_paper_cas_not_promoted(self):
        request, trace = self.choose()
        cas = next(r for r in trace["capability_queries"] if r["request"]["purpose"] == "update")
        excluded = next(m for m in cas["excluded"] if m["design_id"] == "dx100-artifact-e4fc4af")
        self.assertEqual(excluded["operation"]["support"], "unsupported")
        paper = next(m for m in cas["matches"] if m["design_id"] == "dx100-paper-v2")
        self.assertIn("operation_support", paper["missing_capability_evidence"])
        self.assertFalse(any(c.get("catalog_design_id") == "dx100-artifact-e4fc4af" and c.get("candidate_scope") == "update_execute" for c in request["candidates"]))
        self.assertFalse(any(o["operation"]["id"] == "dxp-cas" for c in request["candidates"] for o in c.get("operation_options", [])))

    def test_terminus_is_scoped_paper_cas_not_a_verified_32bit_executor(self):
        request, _ = self.choose()
        c = next(c for c in request["candidates"] if c.get("candidate_scope") == "update_execute")
        self.assertEqual(c["catalog_design_id"], "terminus-micro2024-cas")
        self.assertEqual(c["status"], "needs_evidence")
        self.assertIn("payload_types", c["missing_evidence"])
        self.assertIn("index_width_bits", c["missing_evidence"])
        self.assertEqual(c["operation_options"][0]["operation"]["result"]["form"], "success_flag")
        self.assertEqual(c["requirement_status"], "not_discharged_by_retrieval")
        self.assertEqual(c["execution_plan"]["rmw"], "potential_offload_only_after_CAS_mapping_proof")

    def test_prefetch_is_not_presented_as_returning_the_gather_result(self):
        request, _ = self.choose()
        c = next(c for c in request["candidates"] if c.get("candidate_scope") == "read_assist")
        self.assertEqual(c["catalog_design_id"], "prodigy-hpca2021")
        self.assertTrue(all(o["operation"]["execution_role"] == "assist" for o in c["operation_options"]))
        self.assertIn("assistance only", c["hardware"]["blocks"][0]["outputs"][0]["payload"])
        self.assertEqual(c["execution_plan"]["rmw"], "retain_original_CPU_update")

    def test_reference_values_remain_references_and_domains_remain_unknown(self):
        request, _ = self.choose()
        c = next(c for c in request["candidates"] if c.get("catalog_design_id") == "dx100-artifact-e4fc4af")
        tile = next(p for p in c["parameter_contract"] if p["id"] == "tile_elements")
        self.assertEqual((tile["state"], tile["value"]), ("fixed_reference",16384))
        self.assertEqual(c["selected_configuration"], {})
        self.assertTrue(all(not b["parameters"] for b in c["hardware"]["blocks"]))
        self.assertTrue(all(b["unknown_parameters"][0]["domain"] is None for b in c["hardware"]["blocks"]))

    def test_no_physical_components_connections_or_sequences_are_invented(self):
        request, _ = self.choose()
        for c in request["candidates"][1:]:
            design = next(d for d in self.catalog["designs"] if d["id"] == c["catalog_design_id"])
            operations = {o["id"]:o for o in design["operations"]}
            self.assertEqual(c["hardware"]["connections"], [])
            for block in c["hardware"]["blocks"]:
                self.assertEqual(block["operation_contract"], operations[block["id"]])
                self.assertEqual(block["view_kind"], "software_operation_contract_not_physical_block")
        dx = next(c for c in request["candidates"] if c.get("catalog_design_id") == "dx100-artifact-e4fc4af")
        ranged = next(o for o in dx["operation_options"] if o["operation"]["id"] == "dxc-ranged-gather")
        self.assertEqual(ranged["operation"]["realization"]["kind"], "documented_sequence")

    def test_requirements_and_located_claims_survive_to_the_handoff(self):
        request, _ = self.choose()
        dx = next(c for c in request["candidates"] if c.get("catalog_design_id") == "dx100-artifact-e4fc4af")
        self.assertIn("dxc-byte-offset", [r["id"] for r in dx["requirements"]])
        self.assertIn("dxc-byte-offset-domain", dx["source_evidence"]["claims"])
        for claim in dx["source_evidence"]["claims"].values():
            self.assertTrue(claim["locator"])
            self.assertTrue(set(claim["source_refs"]) <= set(dx["source_evidence"]["sources"]))

    def test_budget_does_not_hide_excluded_or_deferred_evidence(self):
        request, trace = self.choose(max_candidates=1)
        self.assertEqual([c["catalog_entry"] for c in request["candidates"]], ["cpu-baseline"])
        self.assertTrue(trace["capability_queries"])
        self.assertTrue(all(x["decision"] == "eligible_outside_candidate_budget" for x in trace["candidate_selection"]))

    def test_unknown_workload_type_is_not_upgraded_by_catalog_match(self):
        case = deepcopy(self.case)
        for a in case["accesses"]:
            a["reported_element_type"] = None
        request, _ = self.choose(case)
        dx = next(c for c in request["candidates"] if c.get("catalog_design_id") == "dx100-artifact-e4fc4af")
        self.assertEqual(dx["status"], "needs_evidence")
        self.assertIn("workload_payload_type", dx["missing_evidence"])

    def test_same_code_can_have_overlapping_catalog_candidates_across_graphs(self):
        dense = load_normalized(self.dense, reference_context(ROOT))
        sparse_request, _ = self.choose()
        dense_request, _ = self.choose(dense)
        self.assertEqual([c["catalog_entry"] for c in sparse_request["candidates"]], [c["catalog_entry"] for c in dense_request["candidates"]])
        sparse_dx = sparse_request["candidates"][1]
        dense_dx = dense_request["candidates"][1]
        self.assertEqual(sparse_dx["operation_options"][0]["operation"]["id"], "dxc-gather")
        self.assertEqual(dense_dx["operation_options"][0]["operation"]["id"], "dxc-stream_load")

    def test_end_to_end_is_offline_deterministic_and_does_not_mutate_catalog(self):
        before = deepcopy(self.catalog)
        with patch("socket.create_connection", side_effect=AssertionError("No network")):
            artifacts, manifest = prepare_run([self.sparse,self.dense], self.catalog_path, max_candidates=4, methods_path=self.methods_path)
            again, m2 = prepare_run([self.sparse,self.dense], self.catalog_path, max_candidates=4, methods_path=self.methods_path)
        self.assertEqual(artifacts,again)
        self.assertEqual(manifest,m2)
        self.assertEqual(manifest["backend"], "offline_evidence_lookup")
        self.assertEqual(manifest["llm_calls"], 0)
        self.assertEqual(self.catalog,before)
        for path in ("case-01/hardware-request.yaml", "case-02/hardware-request.yaml"):
            request = yaml.safe_load(artifacts[path])
            validate_request(request)
            self.assertEqual(request["catalog_revision"], self.catalog["revision"])
            self.assertTrue(request["capability_requests"])


if __name__ == "__main__":
    unittest.main()
