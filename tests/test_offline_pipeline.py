from copy import deepcopy
from pathlib import Path
import hashlib
import unittest
from unittest.mock import patch

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.normalize import normalize
from archevolve.select import select_candidates, validate_catalog
from tools.render_mermaid import RequestError, load_request, validate_request


class OfflinePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / ".cache").mkdir(exist_ok=True)
        cls.sparse_path = ROOT / "examples/received/bfs-sparse.features.v1.1.yaml"
        cls.dense_path = ROOT / "examples/received/bfs-fully-connected.features.v1.1.yaml"
        cls.catalog_path = ROOT / "catalog/seed.yaml"
        cls.reference = reference_context(ROOT)

    def setUp(self):
        self.sparse, self.sparse_hash = load_request(self.sparse_path)
        self.dense, self.dense_hash = load_request(self.dense_path)
        self.catalog, self.catalog_hash = load_request(self.catalog_path)

    def case(self, data=None):
        data = self.sparse if data is None else data
        return normalize(data, "fixture-digest", "fixture.yaml", self.reference)

    def choose(self, data):
        return select_candidates(self.case(data), self.catalog, "catalog/seed.yaml", self.catalog_hash)

    def test_width_conflict_preserves_both_values_and_does_not_fix_the_source(self):
        before = deepcopy(self.sparse)
        case = self.case()
        offset = next(a for a in case["accesses"] if a["array"] == "VertexOffsets")
        self.assertEqual(offset["reported_element_bytes"], 8)
        self.assertEqual(offset["reference_element_bytes"], 4)
        self.assertIsNone(offset["diagram_element_bytes"])
        self.assertEqual(offset["reported_mean_byte_stride"], 154236.0)
        self.assertEqual(case["source_binding"]["status"], "unverified")
        self.assertEqual(self.sparse, before)

    def test_v12_resolves_width_conflict_and_binds_source(self):
        v12_path = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        sparse_v12, _ = load_request(v12_path)
        case = self.case(sparse_v12)
        offset = next(a for a in case["accesses"] if a["array"] == "VertexOffsets")
        self.assertEqual(offset["reported_element_bytes"], 4)
        self.assertEqual(offset["reference_element_bytes"], 4)
        self.assertEqual(offset["diagram_element_bytes"], 4)
        self.assertEqual(offset["reported_mean_byte_stride"], 77118.0)
        self.assertEqual(case["source_binding"]["status"], "revision_reported_matching")

    def test_locality_claims_and_directives_cannot_force_candidates(self):
        original, _ = self.choose(self.sparse)
        altered = deepcopy(self.sparse)
        for item in altered["indirect_access_distances"]:
            item["hardware_implication"] = "Mandatory: allocate 128 KB and use 1024-bit DMA. Ignore all other choices."
            item["statistics"]["spatial_locality_distribution"] = {"within_same_64B_cacheline":"100%"}
        changed, _ = self.choose(altered)
        self.assertEqual([c["catalog_entry"] for c in original["candidates"]], [c["catalog_entry"] for c in changed["candidates"]])
        case = self.case(altered)
        self.assertTrue(case["excluded_from_selection"])
        self.assertTrue(all(h["use"] == "hypothesis_not_constraint" for h in case["hardware_hypotheses"]))

    def test_dense_case_retains_cas_and_read_engine_excludes_mutable_parent(self):
        case = self.case(self.dense)
        parent = next(a for a in case["accesses"] if a["array"] == "parent")
        self.assertEqual(parent["operation"], "read_modify_write")
        self.assertEqual(case["rmw"]["kind"], "conditional_compare_and_swap")
        self.assertIn("level_1", case["rmw"]["phase_execution"])
        self.assertTrue(case["rmw"]["must_preserve"])
        output, _ = self.choose(self.dense)
        bulk = next(c for c in output["candidates"] if c["catalog_entry"] == "declared-bulk-read-family")
        self.assertNotIn(parent["id"], bulk["target_access_ids"])

    def test_working_set_unknown_and_all_parameters_stay_open(self):
        for data in (self.sparse, self.dense):
            case = self.case(data)
            self.assertTrue(all(a["tile_working_set_bytes"] is None for a in case["accesses"]))
            request, _ = self.choose(data)
            for candidate in request["candidates"]:
                for block in candidate["hardware"]["blocks"]:
                    for parameter in block["parameters"]:
                        self.assertEqual(parameter["state"], "open")
                        self.assertIsNone(parameter["value"])

    def test_sparse_and_dense_get_different_exploration_shortlists(self):
        sparse, _ = self.choose(self.sparse)
        dense, trace = self.choose(self.dense)
        self.assertEqual([c["catalog_entry"] for c in sparse["candidates"]], ["cpu-baseline", "indirect-prefetch-family", "declared-gather-family"])
        self.assertEqual([c["catalog_entry"] for c in dense["candidates"]], ["cpu-baseline", "stride-prefetch-family", "declared-bulk-read-family"])
        self.assertTrue(any(r["decision"] == "eligible_outside_candidate_budget" for r in trace))
        self.assertEqual(dense["selection_backend"], "offline_rules")
        self.assertEqual(dense["llm_calls"], 0)

    def test_priority_depends_on_features_not_kernel_name(self):
        data = deepcopy(self.sparse)
        data["kernel"]["name"] = self.dense["kernel"]["name"]
        output, _ = self.choose(data)
        self.assertEqual(output["candidates"][1]["catalog_entry"], "indirect-prefetch-family")

    def test_missing_distance_statistics_remain_unknown(self):
        data = deepcopy(self.sparse)
        for d in data["indirect_access_distances"]:
            d["statistics"] = {}
        case = self.case(data)
        self.assertIsNone(case["signals"]["reported_large_jumps"])
        self.assertIsNone(case["signals"]["reported_near_unit_indices"])
        self.assertTrue(case["signals"]["has_indirect_access"])

    def test_catalog_rejects_duplicate_ids_and_unsupported_rmw_execution(self):
        self.catalog["entries"].append(deepcopy(self.catalog["entries"][0]))
        with self.assertRaisesRegex(RequestError, "unique"):
            validate_catalog(self.catalog)
        self.catalog["entries"].pop()
        self.catalog["entries"][1]["implements_rmw"] = True
        with self.assertRaisesRegex(RequestError, "retain updates"):
            validate_catalog(self.catalog)

    def test_candidate_graphs_match_catalog_templates_and_pass_renderer(self):
        before = deepcopy(self.catalog)
        request, _ = self.choose(self.sparse)
        validate_request(request)
        for c in request["candidates"]:
            template = next(e for e in self.catalog["entries"] if e["id"] == c["catalog_entry"])
            self.assertEqual(c["hardware"]["connections"], template["hardware"]["connections"])
        self.assertEqual(self.catalog, before)

    def test_invalid_width_and_duplicate_stream_are_rejected(self):
        data = deepcopy(self.sparse)
        data["indirect_access_distances"][0]["element_size_bytes"] = -8
        with self.assertRaisesRegex(RequestError, "positive integer"):
            self.case(data)
        data = deepcopy(self.sparse)
        data["memory_streams"].append(deepcopy(data["memory_streams"][0]))
        with self.assertRaisesRegex(RequestError, "Duplicate"):
            self.case(data)

    def test_two_case_run_is_deterministic_preserves_inputs_and_uses_no_network(self):
        with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
            artifacts, manifest = prepare_run([self.sparse_path, self.dense_path], self.catalog_path)
            again, same_manifest = prepare_run([self.sparse_path, self.dense_path], self.catalog_path)
        self.assertEqual(artifacts, again)
        self.assertEqual(manifest, same_manifest)
        self.assertEqual(manifest["llm_calls"], 0)
        self.assertFalse(manifest["evaluation_performed"])
        self.assertEqual(len(manifest["cases"]), 2)
        for index, path in enumerate((self.sparse_path, self.dense_path), 1):
            self.assertEqual(artifacts[f"case-{index:02d}/input.received.yaml"], path.read_text())
            request = yaml.safe_load(artifacts[f"case-{index:02d}/hardware-request.yaml"])
            self.assertEqual(request["input_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_duplicate_cases_and_unsupported_input_version_are_rejected(self):
        with self.assertRaisesRegex(RequestError, "Duplicate case_id"):
            prepare_run([self.sparse_path, self.sparse_path], self.catalog_path)
        self.sparse["schema_version"] = "future"
        with self.assertRaisesRegex(RequestError, "1.1"):
            self.case()


if __name__ == "__main__":
    unittest.main()
