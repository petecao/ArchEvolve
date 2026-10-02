from copy import deepcopy
import unittest

import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.normalize import normalize
from tools.render_mermaid import RequestError, load_request


class ProfileContextTests(unittest.TestCase):
    def setUp(self):
        self.sparse_path = ROOT / "examples/received/bfs-sparse.features.v1.2.yaml"
        self.dense_path = ROOT / "examples/received/bfs-fully-connected.features.v1.2.yaml"
        self.data, self.digest = load_request(self.sparse_path)
        self.reference = reference_context(ROOT)

    def normalize(self, data=None):
        return normalize(self.data if data is None else data, self.digest, str(self.sparse_path), self.reference)

    def test_v12_sections_are_retained_without_mutating_the_report(self):
        original = deepcopy(self.data)
        case = self.normalize()
        self.assertEqual(case["profiling_provenance"], self.data["profiling_provenance"])
        self.assertEqual(case["frontier_evolution_profile"], self.data["frontier_evolution_profile"])
        self.assertEqual(case["reported_counters"], self.data["hardware_performance_profile"])
        self.assertEqual(case["evidence_status"], "reported_not_reproduced")
        self.assertEqual(self.data, original)
        case["profiling_provenance"]["compiler_toolchain"] = "changed in copy"
        self.assertEqual(self.data, original)

    def test_single_traversal_levels_are_not_joined_to_five_trial_command(self):
        case = self.normalize()
        context = case["profiling_context"]
        self.assertIn("-n 5", context["reported_command_line"])
        self.assertEqual(context["frontier_measurement_scope"], "Kronecker scale 18, 1 BFS trial traversal")
        self.assertIsNone(context["counter_measurement_scope"])
        self.assertEqual(context["cross_section_trial_binding"], "not_established")
        self.assertEqual(len(context["frontier_level_observations"]), 7)
        raw_issue = next(i for i in case["issues"] if i["id"] == "raw-profile-missing")
        self.assertIn("provenance is supplied", raw_issue["message"])

    def test_one_vertex_frontier_mean_is_not_a_real_zero_pair_distance(self):
        case = self.normalize()
        self.assertEqual(case["frontier_evolution_profile"]["levels"][0]["mean_queue_distance"], 0.0)
        first = case["profiling_context"]["frontier_level_observations"][0]
        self.assertIsNone(first["usable_mean_queue_distance"])
        self.assertEqual(first["distance_status"], "not_applicable_no_adjacent_pairs")
        # A genuine zero reported for a frontier with at least two entries is retained.
        data = deepcopy(self.data)
        data["frontier_evolution_profile"]["levels"][0]["frontier_size"] = 2
        first = self.normalize(data)["profiling_context"]["frontier_level_observations"][0]
        self.assertEqual(first["usable_mean_queue_distance"], 0.0)
        self.assertEqual(first["distance_status"], "reported")

    def test_provenance_revision_conflict_cannot_look_like_a_source_match(self):
        self.data["profiling_provenance"]["source_revision"] = "different-revision"
        case = self.normalize()
        self.assertEqual(case["source_binding"]["status"], "conflicting_reported_revisions")
        self.assertTrue(any(i["id"] == "profile-source-conflict" for i in case["issues"]))
        self.assertEqual(case["kernel"]["source_revision"], self.reference["revision"])
        self.assertEqual(case["profiling_provenance"]["source_revision"], "different-revision")

    def test_absent_sections_stay_absent_for_dense_and_legacy_inputs(self):
        for path in (self.dense_path, ROOT / "examples/received/bfs-sparse.features.v1.1.yaml"):
            data, _ = load_request(path)
            case = self.normalize(data)
            self.assertIsNone(case["profiling_provenance"])
            self.assertIsNone(case["frontier_evolution_profile"])
            self.assertEqual(case["profiling_context"]["frontier_level_observations"], [])

    def test_invalid_or_ambiguous_level_records_are_rejected(self):
        for change in ("negative_size", "duplicate_level", "bad_mean"):
            data = deepcopy(self.data)
            levels = data["frontier_evolution_profile"]["levels"]
            if change == "negative_size":
                levels[0]["frontier_size"] = -1
            elif change == "duplicate_level":
                levels.append(deepcopy(levels[0]))
            else:
                levels[0]["mean_queue_distance"] = "unknown"
            with self.subTest(change=change), self.assertRaises(RequestError):
                self.normalize(data)

    def test_context_reaches_handoff_without_changing_candidate_shortlists(self):
        artifacts, manifest = prepare_run(
            [self.sparse_path, self.dense_path], ROOT / "catalog/seed.yaml",
            methods_path=ROOT / "examples/received/peter-measurement-methods.v1.2.yaml")
        sparse = yaml.safe_load(artifacts["case-01/hardware-request.yaml"])
        dense = yaml.safe_load(artifacts["case-02/hardware-request.yaml"])
        summary = sparse["workload_summary"]
        self.assertEqual(summary["profiling_provenance"], self.data["profiling_provenance"])
        self.assertEqual(summary["frontier_evolution_profile"], self.data["frontier_evolution_profile"])
        self.assertEqual(summary["reported_counters"], self.data["hardware_performance_profile"])
        self.assertIsNone(dense["workload_summary"]["frontier_evolution_profile"])
        self.assertIn("profiling_provenance:", artifacts["case-01/diagrams/README.md"])
        self.assertEqual(manifest["cases"][0]["selected_entries"], ["cpu-baseline", "indirect-prefetch-family", "declared-gather-family"])
        self.assertEqual(manifest["cases"][1]["selected_entries"], ["cpu-baseline", "stride-prefetch-family", "declared-bulk-read-family"])
        for candidate in sparse["candidates"] + dense["candidates"]:
            self.assertFalse(any("reported as 8 bytes" in note for note in candidate["unresolved_requirements"]))


if __name__ == "__main__":
    unittest.main()
