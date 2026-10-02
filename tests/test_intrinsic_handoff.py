from copy import deepcopy
import json
import unittest
from unittest.mock import patch

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.comparison import compare_designs
from archevolve.hardware_catalog import validate_catalog
from archevolve.intrinsic_handoff import draft_intrinsics, render_workload_context, validate_draft
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from archevolve.workload_context import bind_context, validate_context
from tools.render_mermaid import RequestError, load_request, render_candidate


class IntrinsicHandoffTests(unittest.TestCase):
    def setUp(self):
        self.input = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        self.catalog_path = ROOT / "catalog/hardware-v0.1.yaml"
        self.catalog, self.catalog_digest = load_request(self.catalog_path)
        self.context_path = ROOT / "examples/bfs.source-observations.yaml"
        self.context, self.context_digest = load_request(self.context_path)
        self.case = load_normalized(self.input, reference_context(ROOT))
        self.case = bind_context(self.case, self.context, self.context_digest, str(self.context_path))

    def choose(self, case=None, catalog=None, budget=4):
        request, _ = select_candidates(case or self.case, catalog or self.catalog,
                                       str(self.catalog_path), self.catalog_digest, budget)
        return request

    def test_request_bundle_preserves_dependencies_and_cpu_side_effects(self):
        request = self.choose()
        dx = request["candidates"][1]
        group = dx["request_groups"][0]
        self.assertIn("bfs-td-row-bounds", dx["target_statement_ids"])
        self.assertIn("bfs-td-parent-cas", group["statement_ids"])
        self.assertIn("bfs-td-parent-store", group["statement_ids"])
        self.assertIn("bfs-td-queue-append", group["statement_ids"])
        self.assertIn("access-04-update", group["uncovered_request_ids"])
        self.assertIn({"from_statement": "bfs-td-parent-cas", "to_statement": "bfs-td-queue-append"}, group["dependencies"])
        self.assertEqual(group["joint_execution_status"], "requires_mapping_and_composition_review")
        self.assertEqual(dx["hardware"]["connections"], [])
        diagram = render_workload_context(request, dx)
        self.assertIn("uncovered request", diagram)
        self.assertIn("lqueue.push_back(v)", diagram)
        self.assertIn("recorded statement relation", diagram)

    def test_unbound_context_does_not_supply_statement_locations_or_groups(self):
        bad = deepcopy(self.context)
        bad["kernel"]["revision"] = "different"
        case = bind_context(self.case, bad, "unused", "fixture")
        request = self.choose(case)
        self.assertEqual(case["source_context"]["status"], "not_bound")
        self.assertTrue(all(not r["statement_ids"] for r in request["capability_requests"]))
        self.assertTrue(all(g["basis"] == "singleton_no_context_group" for g in request["request_groups"]))
        self.assertTrue(all(not c.get("target_statement_ids") for c in request["candidates"]))

    def test_context_requires_matching_function_file_and_unconflicted_revision(self):
        for field in ("source_file", "feature_function_proposal"):
            context = deepcopy(self.context)
            context["kernel"][field] = "different"
            if field == "source_file":
                for s in context["statements"]:
                    s["location"]["file"] = "different"
            self.assertEqual(bind_context(self.case, context, "digest", "fixture")["source_context"]["status"], "not_bound")
        case = deepcopy(self.case)
        case["source_binding"]["status"] = "conflicting_reported_revisions"
        self.assertEqual(bind_context(case, self.context, "digest", "fixture")["source_context"]["status"], "not_bound")

    def test_context_rejects_unknown_statements_and_duplicate_bindings(self):
        context = deepcopy(self.context)
        context["request_groups"][0]["statement_ids"].append("nonexistent")
        with self.assertRaisesRegex(RequestError, "unknown reference"):
            validate_context(context)
        context = deepcopy(self.context)
        context["access_bindings"].append(deepcopy(context["access_bindings"][0]))
        with self.assertRaisesRegex(RequestError, "Duplicate"):
            validate_context(context)

    def test_older_source_observations_without_explicit_bindings_remain_usable(self):
        context = deepcopy(self.context)
        del context["access_bindings"]
        del context["request_groups"]
        case = bind_context(self.case, context, "digest", "older-reference")
        request = self.choose(case)
        self.assertTrue(all(not r["statement_ids"] for r in request["capability_requests"]))
        self.assertTrue(all(g["basis"] == "singleton_no_context_group" for g in request["request_groups"]))

    def test_unknown_internal_mechanisms_are_not_inferred_from_operation_support(self):
        dx = self.choose()["candidates"][1]
        self.assertIn("reordering", dx["mechanism_context"]["missing_kinds"])
        self.assertTrue(all(m["description"] is None for m in dx["mechanism_context"]["annotations"]))
        self.assertEqual(dx["status"], "conditional")

    def annotated_catalog(self):
        catalog = deepcopy(self.catalog)
        # Explicitly synthetic annotation, not evidence about the real design.
        catalog["claims"]["synthetic-mechanism-test"] = {
            "source_refs": [next(iter(catalog["sources"]))], "locator": "Synthetic test fixture only",
            "statement": "Synthetic grouping description", "evidence_kind": "code_inspection",
            "limitations": ["Not an actual hardware claim."]}
        d = next(d for d in catalog["designs"] if d["id"] == "dx100-artifact-e4fc4af")
        d["internal_mechanisms"] = [{"id": "fixture-grouping", "kind": "coalescing", "status": "described",
                                    "description": "Synthetic test grouping only", "claim_refs": ["synthetic-mechanism-test"]}]
        d["performance_hypotheses"] = [{"id": "fixture-payoff", "description": "Synthetic conditional benefit",
            "workload_conditions": ["Fixture adjacent requests"], "limiting_factors": ["Fixture dependency constraint"],
            "claim_refs": ["synthetic-mechanism-test"]}]
        return catalog

    def test_mechanism_annotations_and_evidence_survive_without_creating_wiring(self):
        catalog = self.annotated_catalog()
        before = deepcopy(catalog)
        request = self.choose(catalog=catalog)
        dx = request["candidates"][1]
        self.assertEqual(dx["mechanism_context"]["annotations"][0]["description"], "Synthetic test grouping only")
        self.assertNotIn("coalescing", dx["mechanism_context"]["missing_kinds"])
        self.assertIn("synthetic-mechanism-test", dx["source_evidence"]["claims"])
        self.assertTrue(dx["mechanism_context"]["performance_hypotheses"])
        self.assertIn("Synthetic test grouping only", render_candidate(request, dx))
        self.assertEqual(dx["hardware"]["connections"], [])
        self.assertEqual(catalog, before)

    def test_mechanism_schema_rejects_unlocated_or_inferred_facts(self):
        for mutation in ("missing-ref", "inference", "unknown-description"):
            catalog = self.annotated_catalog()
            mechanism = next(d for d in catalog["designs"] if "internal_mechanisms" in d)["internal_mechanisms"][0]
            if mutation == "missing-ref":
                mechanism["claim_refs"] = ["missing"]
            elif mutation == "inference":
                catalog["claims"]["synthetic-mechanism-test"]["evidence_kind"] = "research_inference"
            else:
                mechanism["status"] = "unknown"
            with self.assertRaises(RequestError):
                validate_catalog(catalog)

    def test_draft_retains_sequences_mutable_loads_and_reference_parameters(self):
        request = self.choose()
        dx = request["candidates"][1]
        draft = draft_intrinsics(request, dx)
        ranged = next(o for o in draft["operations"] if o["id"] == "dxc-ranged-gather")
        self.assertEqual(ranged["realization"]["kind"], "documented_sequence")
        gather = next(o for o in draft["operations"] if o["id"] == "dxc-gather")
        self.assertTrue(gather["preconditions"]["mutable_target_review_required"])
        tile = next(p for p in draft["parameter_contract"] if p["id"] == "tile_elements")
        self.assertEqual((tile["state"], tile["value"]), ("fixed_reference", 16384))
        self.assertEqual(draft["selected_configuration"], {})
        self.assertIn("expected=curr_val", draft["workload_semantics"]["reported_rmw"]["reported_details"]["primitive"])
        self.assertTrue(all(o["concrete_signature"] is None for o in draft["operations"]))

    def test_draft_cas_and_assistance_do_not_change_semantics(self):
        request = self.choose()
        cas = draft_intrinsics(request, request["candidates"][2])
        self.assertEqual(cas["operations"][0]["postconditions"]["catalog_result"]["form"], "success_flag")
        self.assertIn("payload_types", cas["operations"][0]["missing_capability_evidence"])
        assist_candidate = request["candidates"][3]
        assist = draft_intrinsics(request, assist_candidate)
        self.assertTrue(all(o["postconditions"]["satisfies_program_result"] == "no_assistance_only" for o in assist["operations"]))
        assist["operations"][0]["postconditions"]["satisfies_program_result"] = "conditional_on_mapping_proof"
        with self.assertRaisesRegex(RequestError, "assist upgraded"):
            validate_draft(assist, assist_candidate)

    def test_comparison_uses_same_requests_independent_of_candidate_budget(self):
        request = self.choose(budget=1)
        comparison = compare_designs(request, self.catalog, ["dx100-artifact-e4fc4af", "spzip-isca2021-push", "prodigy-hpca2021"])
        self.assertEqual(len(request["candidates"]), 1)
        self.assertEqual(len(comparison["designs"]), 3)
        for d in comparison["designs"]:
            self.assertEqual([q["request_id"] for q in d["queries"]], [r["id"] for r in request["capability_requests"]])
        dx, spzip, prodigy = comparison["designs"]
        self.assertTrue(dx["conditionally_matched_read_requests"])
        self.assertTrue(spzip["read_requests_needing_evidence"])
        self.assertFalse(prodigy["conditionally_matched_read_requests"])
        self.assertTrue(prodigy["assisted_read_requests"])
        self.assertIsNone(comparison["speedup"])
        cas = next(q for q in dx["queries"] if q["request_id"] == "access-04-update")
        self.assertTrue(any(m["operation"]["support"] == "unsupported" for m in cas["excluded"]))

    def test_comparison_rejects_unknown_or_duplicate_designs(self):
        for ids in (["unknown"], ["dx100-artifact-e4fc4af"] * 2):
            with self.assertRaises(RequestError):
                compare_designs(self.choose(), self.catalog, ids)

    def test_comparison_does_not_hide_missing_workload_types(self):
        case = deepcopy(self.case)
        for access in case["accesses"]:
            access["reported_element_type"] = None
        request = self.choose(case)
        dx = compare_designs(request, self.catalog, ["dx100-artifact-e4fc4af"])["designs"][0]
        self.assertFalse(dx["conditionally_matched_read_requests"])
        self.assertTrue(dx["read_requests_needing_evidence"])
        self.assertTrue(all(q["workload_request"]["missing_workload_evidence"] for q in dx["queries"]))

    def test_offline_packages_are_deterministic_and_keep_input_identity(self):
        kwargs = dict(max_candidates=4, source_context_path=self.context_path)
        with patch("socket.create_connection", side_effect=AssertionError("No network")):
            artifacts, manifest = prepare_run([self.input], self.catalog_path, **kwargs)
            again, same = prepare_run([self.input], self.catalog_path, **kwargs)
        self.assertEqual(artifacts, again)
        self.assertEqual(manifest, same)
        index = json.loads(artifacts["case-01/handoffs/manifest.json"])
        self.assertEqual(len(index["packages"]), 3)
        draft = yaml.safe_load(artifacts["case-01/handoffs/candidate-02/intrinsic-draft.yaml"])
        self.assertEqual(draft["provenance"]["source_context_sha256"], self.context_digest)
        self.assertFalse(draft["readiness"]["implementation_generated"])
        no_context, _ = prepare_run([self.input], self.catalog_path, max_candidates=4)
        plain = yaml.safe_load(no_context["case-01/handoffs/candidate-02/intrinsic-draft.yaml"])
        self.assertIsNone(plain["provenance"]["source_context_sha256"])
        self.assertTrue(all(not i["statement_ids"] for o in plain["operations"] for i in o["logical_inputs"]))


if __name__ == "__main__":
    unittest.main()
