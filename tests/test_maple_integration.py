from copy import deepcopy
import unittest

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.comparison import compare_designs
from archevolve.hardware_catalog import load_catalog, query_catalog, validate_catalog
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from tools.render_mermaid import RequestError


class MapleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "catalog/hardware-v0.1.yaml"
        self.catalog, self.digest = load_catalog(self.path)
        self.maple = next(d for d in self.catalog["designs"] if d["id"] == "maple-isca2022")
        self.input = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        self.case = load_normalized(self.input, reference_context(ROOT))

    def test_typed_maple_lookup_retains_missing_domains(self):
        result = query_catalog(self.catalog, design_id="maple-isca2022", operation="read", subtype="gather",
                               address_pattern="indirect", payload_type="int32", index_width_bits=32, execution_role="execute")
        self.assertTrue(result["matches"])
        for match in result["matches"]:
            self.assertEqual(match["status"], "needs_evidence")
            self.assertIn("payload_types", match["missing_capability_evidence"])
            self.assertIn("index_width_bits", match["missing_capability_evidence"])
            self.assertEqual(match["operation"]["result"]["form"], "queue_value_stream")

    def test_future_atomic_extension_is_not_promoted_to_a_cas_executor(self):
        result = query_catalog(self.catalog, design_id="maple-isca2022", operation="read_modify_write", subtype="cas")
        self.assertEqual(result["matches"][0]["operation"]["support"], "unknown")
        self.assertIn("operation_support", result["matches"][0]["missing_capability_evidence"])
        request, trace = select_candidates(self.case, self.catalog, str(self.path), self.digest, 4,
                                          ["dx100-artifact-e4fc4af", "maple-isca2022"])
        self.assertFalse(any(o["operation"]["id"] == "maple-cas" for c in request["candidates"] for o in c.get("operation_options", [])))
        self.assertTrue(all(c.get("execution_plan", {}).get("rmw") == "retain_original_CPU_update" for c in request["candidates"][1:]))
        cas = next(q for q in trace["capability_queries"] if q["request"]["purpose"] == "update")
        self.assertTrue(any(m["design_id"] == "maple-isca2022" and m["operation"]["support"] == "unknown" for m in cas["matches"]))

    def test_queue_and_llc_roles_stay_separate(self):
        result = query_catalog(self.catalog, design_id="maple-isca2022", operation="read", subtype="gather", address_pattern="indirect")
        self.assertEqual({m["operation"]["execution_role"] for m in result["matches"]}, {"execute", "assist"})
        execute = [m for m in result["matches"] if m["operation"]["execution_role"] == "execute"]
        assist = [m for m in result["matches"] if m["operation"]["execution_role"] == "assist"]
        self.assertTrue(all(m["operation"]["result"]["form"] == "queue_value_stream" for m in execute))
        self.assertTrue(all(m["operation"]["result"]["form"] == "nonbinding_LLC_fill_hint" for m in assist))
        self.assertTrue(all("acknowledgement precedes" in m["operation"]["completion"]["event"] for m in execute))

    def test_neighbor_interval_uses_caller_bounded_A_zero_mode(self):
        result = query_catalog(self.catalog, design_id="maple-isca2022", operation="read", subtype="gather",
                               address_pattern="ranged_indirect", execution_role="execute")
        self.assertEqual([m["operation_id"] for m in result["matches"]], ["maple-lima-range"])
        self.assertIn("A=0", result["matches"][0]["operation"]["realization"]["description"])
        self.assertIn("Software obtains CSR bounds", result["matches"][0]["operation"]["realization"]["description"])

    def test_fetch_stability_and_cpu_effects_are_requirements_not_assumed_safe(self):
        ids = {r["id"] for r in self.maple["requirements"]}
        self.assertIn("maple-stable-target", ids)
        self.assertIn("maple-cpu-updates", ids)
        stable = next(r for r in self.maple["requirements"] if r["id"] == "maple-stable-target")
        self.assertEqual(stable["verification"], "required")
        self.assertIn("after a CPU write", stable["description"])

    def test_response_association_does_not_infer_target_coalescing(self):
        annotations = {m["id"]: m for m in self.maple["internal_mechanisms"]}
        self.assertEqual(annotations["maple-response-association"]["kind"], "reordering")
        self.assertEqual(annotations["maple-target-coalescing"]["status"], "unknown")
        self.assertIsNone(annotations["maple-target-coalescing"]["description"])
        self.assertEqual(annotations["maple-index-chunks"]["kind"], "buffering")

    def test_supplemental_readiness_and_credit_keep_code_scope(self):
        annotations = {m["id"]: m for m in self.maple["internal_mechanisms"]}
        for mid in ("maple-pinned-head-readiness", "maple-pinned-credit-transfer"):
            annotation = annotations[mid]
            self.assertIn("public RTL 742a22d", annotation["description"])
            self.assertTrue(all(self.catalog["claims"][ref]["evidence_kind"] == "code_inspection"
                                for ref in annotation["claim_refs"]))
        self.assertIn("before", annotations["maple-pinned-credit-transfer"]["description"])
        self.assertEqual([d["id"] for d in self.catalog["designs"]
                          if d["id"].startswith("maple-")], ["maple-isca2022"])

    def test_focus_retains_full_trace_and_produces_both_maple_modes(self):
        focus = ["dx100-artifact-e4fc4af", "maple-isca2022"]
        request, trace = select_candidates(self.case, self.catalog, str(self.path), self.digest, 4, focus)
        self.assertEqual(len(request["candidates"]), 4)
        self.assertEqual({c.get("catalog_design_id") for c in request["candidates"][1:]}, set(focus))
        maple = [c for c in request["candidates"] if c.get("catalog_design_id") == "maple-isca2022"]
        self.assertEqual({c["candidate_scope"] for c in maple}, {"read_execute", "read_assist"})
        self.assertTrue(any(row["decision"] == "outside_requested_design_focus" for row in trace["candidate_selection"]))
        self.assertTrue(any(m["design_id"] == "terminus-micro2024-cas" for q in trace["capability_queries"] for m in q["matches"]))
        self.assertEqual(request["selection_policy"]["focus_design_ids"], focus)

    def test_focus_and_project_selection_reject_unknown_designs(self):
        for focus in ([], ["unknown"], ["maple-isca2022"] * 2):
            with self.assertRaises(RequestError):
                select_candidates(self.case, self.catalog, str(self.path), self.digest, 4, focus)
        catalog = deepcopy(self.catalog)
        catalog["project_selections"]["second_indirect_fetcher"]["design_id"] = "unknown"
        with self.assertRaises(RequestError):
            validate_catalog(catalog)

    def test_structure_requires_known_endpoints_and_located_claims(self):
        for field in ("endpoint", "claims"):
            catalog = deepcopy(self.catalog)
            structure = next(d for d in catalog["designs"] if d["id"] == "maple-isca2022")["hardware_structure"]
            if field == "endpoint":
                structure["connections"][0]["to_block"] = "invented"
            else:
                structure["connections"][0]["claim_refs"] = []
            with self.assertRaises(RequestError):
                validate_catalog(catalog)

    def test_comparison_records_actual_selection_without_a_performance_winner(self):
        request, _ = select_candidates(self.case, self.catalog, str(self.path), self.digest, 1)
        result = compare_designs(request, self.catalog, ["dx100-artifact-e4fc4af", "maple-isca2022"])
        self.assertEqual(result["selected_second_fetcher_design_id"], "maple-isca2022")
        self.assertEqual(result["selected_second_fetcher_status"], "cataloged_paper_evidence_mapping_and_types_pending")
        self.assertFalse(result["performance_evaluated"])
        self.assertIsNone(result["speedup"])
        self.assertIn("coalescing", result["designs"][1]["mechanism_context"]["missing_kinds"])
        self.assertTrue(result["designs"][1]["read_requests_needing_evidence"])

    def test_end_to_end_maple_handoff_has_source_paths_and_review_gates(self):
        focus = ["dx100-artifact-e4fc4af", "maple-isca2022"]
        artifacts, manifest = prepare_run([self.input], self.path, max_candidates=4,
            source_context_path=ROOT / "examples/bfs.source-observations.yaml", compare_design_ids=focus, focus_design_ids=focus)
        candidate = yaml.safe_load(artifacts["case-01/handoffs/candidate-04/candidate.yaml"])
        self.assertEqual(candidate["catalog_design_id"], "maple-isca2022")
        self.assertEqual(candidate["candidate_scope"], "read_execute")
        self.assertIn("structure.mmd", '\n'.join(artifacts))
        self.assertIn("maple-structure", candidate["source_evidence"]["claims"])
        self.assertEqual(candidate["hardware"]["connections"], [])
        draft = yaml.safe_load(artifacts["case-01/handoffs/candidate-04/intrinsic-draft.yaml"])
        self.assertTrue(all(o["concrete_signature"] is None for o in draft["operations"]))
        self.assertFalse(draft["readiness"]["correctness_verified"])
        self.assertEqual(manifest["identity"]["focus_design_ids"], focus)


if __name__ == "__main__":
    unittest.main()
