from copy import deepcopy
import unittest

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.normalize import normalize
from archevolve.select import select_candidates
from tools.render_mermaid import RequestError, load_request


class MeasurementMethodTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "examples/received/bfs-sparse.features.v1.1.yaml"
        self.data, self.digest = load_request(self.path)
        self.methods_path = ROOT / "examples/received/peter-measurement-methods.yaml"
        self.methods, self.methods_hash = load_request(self.methods_path)
        self.methods["record_sha256"] = self.methods_hash
        self.reference = reference_context(ROOT)

    def normalize(self):
        return normalize(self.data, self.digest, str(self.path), self.reference, methods=self.methods)

    def test_proximity_is_relabelled_with_scope_not_promoted_to_cache_hits(self):
        result = self.normalize()
        offsets = next(a for a in result["accesses"] if a["array"] == "VertexOffsets")
        parent = next(a for a in result["accesses"] if a["array"] == "parent")
        proximity = offsets["adjacent_pair_proximity"][0]
        self.assertEqual(proximity["threshold_bytes"], 64)
        self.assertAlmostEqual(proximity["fraction"], 0.0352)
        self.assertFalse(proximity["measures_cache_hits"])
        self.assertFalse(proximity["measures_same_block_membership"])
        self.assertEqual(offsets["reported_mean_distance_scope"], "adjacent_positions_within_each_frontier")
        self.assertEqual(parent["reported_mean_distance_scope"], "adjacent_neighbors_within_each_vertex_row")
        self.assertFalse(parent["cross_segment_pairs_included"])
        self.assertFalse(parent["runtime_thread_interleaving_observed"])

    def test_sparse_binary_unit_claim_is_checked_against_exact_bytes(self):
        result = self.normalize()
        g18 = next(x for x in result["derived_array_capacities"] if x["scope"] == "small_scale_g18")
        parent = g18["arrays"]["parent"]
        self.assertEqual(parent["capacity_bytes"], 1048572)
        self.assertAlmostEqual(parent["MiB"], 0.9999961853027344)
        self.assertAlmostEqual(parent["MB"], 1.048572)
        self.assertEqual(parent["reported_unit_checks"][0]["matches_conversion"], "decimal")
        self.assertTrue(any(i["id"] == "footprint-unit-inconsistency" for i in result["issues"]))
        self.assertIsNone(g18["active_working_set_bytes"])

    def test_dense_capacities_use_reported_widths_without_claiming_local_source_match(self):
        path = ROOT / "examples/received/bfs-fully-connected.features.v1.1.yaml"
        self.data, self.digest = load_request(path)
        result = self.normalize()
        arrays = result["derived_array_capacities"][0]["arrays"]
        self.assertEqual(arrays["parent"]["capacity_bytes"], 100000)
        self.assertEqual(arrays["VertexOffsets"]["capacity_bytes"], 200008)
        self.assertEqual(arrays["g.out_neighbors_"]["capacity_bytes"], 2499900000)
        self.assertAlmostEqual(arrays["parent"]["KiB"], 97.65625)
        self.assertEqual(result["source_binding"]["status"], "unverified")
        offsets = next(a for a in result["accesses"] if a["array"] == "VertexOffsets")
        self.assertIsNone(offsets["diagram_element_bytes"])

    def test_explanation_is_not_applied_to_a_different_report_hash(self):
        result = normalize(self.data, "different-hash", str(self.path), self.reference, methods=self.methods)
        self.assertEqual(result["methodology"]["status"], "not_applied_input_hash_mismatch")
        self.assertNotIn("derived_array_capacities", result)
        self.assertFalse(any("adjacent_pair_proximity" in a for a in result["accesses"]))

    def test_invalid_method_threshold_is_rejected(self):
        self.methods["locality"]["arrays"]["parent"]["threshold_elements"]["64"] = 15
        with self.assertRaisesRegex(RequestError, "threshold"):
            self.normalize()

    def test_raw_report_stays_unchanged_and_resolved_questions_stop_being_asked(self):
        original = deepcopy(self.data)
        result = self.normalize()
        catalog, digest = load_request(ROOT / "catalog/seed.yaml")
        request, _ = select_candidates(result, catalog, "catalog/seed.yaml", digest)
        self.assertEqual(self.data, original)
        ids = {q["id"] for q in request["clarification_requests"]}
        self.assertNotIn("locality-not-hit-rate", ids)
        self.assertNotIn("footprint-not-working-set", ids)
        self.assertIn("source-unbound", ids)
        self.assertIn("footprint-unit-inconsistency", ids)
        self.assertEqual([c["catalog_entry"] for c in request["candidates"]], ["cpu-baseline", "indirect-prefetch-family", "declared-gather-family"])

    def test_methodology_is_part_of_run_identity_and_is_snapshotted(self):
        plain, before = prepare_run([self.path], ROOT / "catalog/seed.yaml")
        artifacts, after = prepare_run([self.path], ROOT / "catalog/seed.yaml", methods_path=self.methods_path)
        self.assertNotEqual(before["run_id"], after["run_id"])
        self.assertEqual(after["identity"]["methodology_sha256"], self.methods_hash)
        self.assertEqual(artifacts["methodology.snapshot.yaml"], self.methods_path.read_text())
        self.assertEqual(plain["case-01/input.received.yaml"], artifacts["case-01/input.received.yaml"])


if __name__ == "__main__":
    unittest.main()
