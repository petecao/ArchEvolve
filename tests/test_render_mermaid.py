"""Behavioral tests for the provisional YAML-to-diagram handoff."""

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from tools.render_mermaid import RequestError, build_artifacts, load_request, validate_request


ROOT = Path(__file__).resolve().parents[1]


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / ".cache").mkdir(exist_ok=True)

    def setUp(self):
        self.request, self.digest = load_request(ROOT / "examples/sparta-sort.hardware-request.yaml")

    def render(self, request=None, **kwargs):
        return build_artifacts(self.request if request is None else request, "example.yaml", self.digest, **kwargs)

    def test_sparta_generates_two_graphs_without_invented_edges_or_values(self):
        before = deepcopy(self.request)
        artifacts = self.render()
        self.assertEqual(self.request, before)
        manifest = json.loads(artifacts["manifest.json"])
        self.assertEqual(len(manifest["diagrams"]), 2)
        self.assertEqual(manifest["source"]["source_sha256"], self.digest)
        for item, candidate in zip(manifest["diagrams"], self.request["candidates"]):
            diagram = artifacts[item["file"]]
            self.assertEqual(diagram.count(" -->"), len(candidate["hardware"]["connections"]))
            self.assertIn("ILLUSTRATIVE", diagram)
            self.assertIn("OPEN", diagram)
            self.assertIn("unknown B/element", diagram)
        self.assertIn("19471976073", artifacts["README.md"])
        self.assertIn("source_bindings: unresolved", artifacts["README.md"])

    def test_same_input_is_deterministic(self):
        self.assertEqual(self.render(), self.render())

    def test_exact_candidate_selection_and_unknown_candidate(self):
        artifacts = self.render(candidate_id="sparta-sort-declared-fetch-1")
        self.assertEqual(len(json.loads(artifacts["manifest.json"])["diagrams"]), 1)
        self.assertIn("return-storage", artifacts["candidate-01.mmd"])
        with self.assertRaisesRegex(RequestError, "not found"):
            self.render(candidate_id="does-not-exist")

    def test_duplicate_candidate_block_and_port_ids(self):
        for target in ("candidate", "block", "port"):
            with self.subTest(target=target):
                data = deepcopy(self.request)
                blocks = data["candidates"][0]["hardware"]["blocks"]
                if target == "candidate":
                    data["candidates"].append(deepcopy(data["candidates"][0]))
                elif target == "block":
                    blocks.append(deepcopy(blocks[0]))
                else:
                    blocks[0]["outputs"][0]["id"] = blocks[0]["inputs"][0]["id"]
                with self.assertRaisesRegex(RequestError, "[Dd]uplicate"):
                    validate_request(data)

    def test_bad_endpoints_and_reversed_directions(self):
        data = deepcopy(self.request)
        edge = data["candidates"][0]["hardware"]["connections"][0]
        edge["to_port"] = "missing"
        with self.assertRaisesRegex(RequestError, "unknown block/port"):
            validate_request(data)
        edge["to_port"] = "predicted-addresses"
        edge["from_port"] = "observed-accesses"
        with self.assertRaisesRegex(RequestError, "output port to an input"):
            validate_request(data)

    def test_open_value_is_not_silently_fixed(self):
        data = deepcopy(self.request)
        parameter = data["candidates"][0]["hardware"]["blocks"][1]["parameters"][0]
        parameter["value"] = 16384
        with self.assertRaisesRegex(RequestError, "open parameter"):
            validate_request(data)
        parameter.update(state="fixed", value=None)
        with self.assertRaisesRegex(RequestError, "fixed parameter needs"):
            validate_request(data)

    def test_template_requires_explicit_preview_and_stays_labeled(self):
        data, digest = load_request(ROOT / "examples/hardware-request.template.yaml")
        with self.assertRaisesRegex(RequestError, "Unfilled template"):
            validate_request(data)
        artifacts = build_artifacts(data, "template.yaml", digest, allow_template=True)
        self.assertIn("TEMPLATE", artifacts["candidate-01.mmd"])
        self.assertIn("unknown B/element", artifacts["candidate-01.mmd"])

    def test_empty_candidate_response_has_report_but_no_fake_diagram(self):
        self.request["candidates"] = []
        artifacts = self.render()
        self.assertFalse(any(name.endswith(".mmd") for name in artifacts))
        self.assertIn("No candidates were supplied", artifacts["README.md"])

    def test_ids_are_not_used_as_paths_or_mermaid_syntax(self):
        data = deepcopy(self.request)
        data["candidates"][0]["id"] = "../../outside\n---\nunsafe"
        data["candidates"][0]["hardware"]["blocks"][0]["function"] = '\"]\nclick injected "https://example.invalid"\n<script>bad</script> ``` | #'
        artifacts = self.render(data)
        self.assertTrue(all(Path(name).name == name for name in artifacts))
        diagram = artifacts["candidate-01.mmd"]
        self.assertNotIn("\nclick ", diagram)
        self.assertNotIn("<script>", diagram)
        self.assertNotIn("```", diagram)
        self.assertIn("#34;", diagram)
        self.assertIn("#60;script#62;", diagram)

    def test_duplicate_yaml_keys_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as directory:
            path = Path(directory) / "duplicate.yaml"
            path.write_text("kernel_id: first\nkernel_id: second\n")
            with self.assertRaisesRegex(RequestError, "Duplicate YAML key"):
                load_request(path)

    def test_unsafe_yaml_tags_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as directory:
            path = Path(directory) / "unsafe.yaml"
            path.write_text("!!python/object/apply:builtins.print ['must not run']")
            with self.assertRaises(RequestError):
                load_request(path)


if __name__ == "__main__":
    unittest.main()
