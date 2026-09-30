from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from archevolve.hardware_catalog import load_catalog, navigation_tree, query_catalog, validate_catalog
from tools.render_mermaid import RequestError, load_request


def fixture():
    """Explicitly synthetic contracts for adversarial tests, never catalog evidence."""
    claim = {"source_refs": ["test-source"], "locator": "test fixture only", "statement": "Synthetic test contract",
             "evidence_kind": "code_inspection", "limitations": ["Not a hardware claim."]}
    def op(oid, operation, subtype, role="execute", support="code_observed", old="not_applicable", pattern="indirect"):
        return {"id": oid, "operation": operation, "subtype": subtype, "execution_role": role,
                "support": support, "address_patterns": [pattern], "claim_refs": ["c"],
                "result": {"form": "fixture payload", "old_value": old, "validity": "mask required", "claim_refs": ["c"]},
                "ordering": {"scope": "fixture local", "description": "no global promise", "claim_refs": ["c"]},
                "completion": {"event": "fixture event", "visibility": "unknown", "claim_refs": []},
                "datatype_notes": "fixture int32 only", "limitations": ["No actual implementation."]}
    def design(did, ops):
        return {"id": did, "name": did, "revision": "fixture-r1", "record_kind": "design_version",
                "summary": "Synthetic test design", "mechanism_refs": ["family"], "source_refs": ["test-source"],
                "operations": ops, "requirements": [{"id": "ownership", "description": "Establish exclusive writer",
                    "scope": "mapped array during operation", "verification": "required", "claim_refs": ["c"]}],
                "parameters": [{"id": "window", "unit": "elements", "state": "fixed_reference", "value": 16,
                                "domain": None, "claim_refs": ["c"], "notes": "Fixture reference, not a chosen value."}],
                "interface": {"software_supplies": "fixture instruction", "invocation": "fixture command",
                              "outputs": "fixture results", "claim_refs": ["c"]}, "limitations": ["Synthetic only."]}
    return {"catalog_id": "synthetic-tests", "revision": "r1", "format": "hardware-catalog-v0.1",
            "status": "research_reviewed_prototype",
            "sources": {"test-source": {"title": "Synthetic test fixture", "edition": "r1",
                         "url": "https://example.invalid/fixture", "locator_basis": "test only"}},
            "claims": {"c": claim}, "mechanism_families": [{"id": "family", "description": "Fixture family, no inherited capabilities"}],
            "decision_questions": [{"id": "writers", "question": "Who writes?", "why_it_matters": "Fixture ownership", "claim_refs": ["c"]}],
            "designs": [design("update", [op("add", "read_modify_write", "add", old="returned"),
                                         op("cas", "read_modify_write", "cas", support="unsupported", old="not_returned"),
                                         op("gather", "read", "gather"),
                                         op("stream", "read", "stream_load", pattern="sequential")]),
                        design("prefetch", [op("prefetch", "read", "prefetch", role="assist")]),
                        design("uncertain", [op("cas", "read_modify_write", "cas", support="unknown", old="unknown")])]}


class HardwareCatalogTests(unittest.TestCase):
    def test_fetch_old_does_not_establish_cas_or_global_atomicity(self):
        c = fixture()
        add = query_catalog(c, operation="read_modify_write", subtype="add", require_old_value=True)
        self.assertEqual([m["design_id"] for m in add["matches"]], ["update"])
        self.assertEqual(add["matches"][0]["status"], "conditional_executor")
        self.assertEqual(add["matches"][0]["operation"]["ordering"]["scope"], "fixture local")
        self.assertTrue(add["matches"][0]["requirements"])
        cas = query_catalog(c, operation="read_modify_write", subtype="cas", require_old_value=True)
        self.assertEqual([m["design_id"] for m in cas["matches"]], ["uncertain"])
        self.assertEqual(cas["matches"][0]["status"], "needs_evidence")
        self.assertIn("old_value_return", cas["matches"][0]["missing_capability_evidence"])
        self.assertEqual(cas["excluded"][0]["design_id"], "update")

    def test_prefetch_match_does_not_become_gather_executor(self):
        matches = query_catalog(fixture(), operation="read", subtype="gather", address_pattern="indirect")["matches"]
        self.assertEqual({m["design_id"]: m["status"] for m in matches},
                         {"prefetch": "assistance_only", "update": "conditional_executor"})
        only = query_catalog(fixture(), operation="read", subtype="gather", execution_role="execute")
        self.assertEqual([m["design_id"] for m in only["matches"]], ["update"])

    def test_unknown_read_subtype_is_not_satisfied_by_prefetch_wildcard(self):
        result = query_catalog(fixture(), operation="read", subtype="totally_nonexistent", address_pattern="indirect")
        self.assertFalse(result["matches"])
        self.assertFalse(result["excluded"])

    def test_payload_width_is_not_index_width_and_missing_type_evidence_survives(self):
        catalog = fixture()
        op = catalog["designs"][0]["operations"][2]
        op["type_constraints"] = {"payload_types": ["float64", "int64"], "index_width_bits": [32],
                                  "notes": "Synthetic distinction only", "claim_refs": ["c"]}
        query = dict(operation="read", subtype="gather", execution_role="execute", payload_type="float64")
        self.assertEqual(query_catalog(catalog, **query, index_width_bits=32)["matches"][0]["status"], "conditional_executor")
        wide = query_catalog(catalog, **query, index_width_bits=64)
        self.assertFalse(wide["matches"])
        self.assertEqual(wide["excluded"][0]["status"], "not_covered")
        op.pop("type_constraints")
        unknown = query_catalog(catalog, **query, index_width_bits=64)["matches"][0]
        self.assertEqual(unknown["status"], "needs_evidence")
        self.assertIn("index_width_bits", unknown["missing_capability_evidence"])

    def test_patterns_are_not_inferred_and_unknown_pattern_is_not_false(self):
        c = fixture()
        result = query_catalog(c, operation="read", subtype="gather", address_pattern="pointer_chase")
        self.assertFalse(result["matches"])
        self.assertTrue(all(m["status"] == "not_covered" for m in result["excluded"]))
        c["designs"][0]["operations"][2]["address_patterns"] = []
        result = query_catalog(c, operation="read", subtype="gather", address_pattern="pointer_chase")
        self.assertEqual(result["matches"][0]["status"], "needs_evidence")
        self.assertEqual(result["matches"][0]["missing_capability_evidence"], ["address_pattern_support"])

    def test_no_family_capability_inheritance_or_unknown_evidence_refs(self):
        c = fixture()
        c["mechanism_families"][0]["operations"] = ["cas"]
        with self.assertRaisesRegex(RequestError, "Families"):
            validate_catalog(c)
        c = fixture()
        c["designs"][0]["operations"][0]["completion"]["claim_refs"] = ["missing"]
        with self.assertRaisesRegex(RequestError, "unknown reference"):
            validate_catalog(c)

    def test_code_support_requires_code_evidence_and_open_sizes_have_no_value(self):
        c = fixture()
        c["claims"]["c"]["evidence_kind"] = "research_inference"
        with self.assertRaisesRegex(RequestError, "code_inspection"):
            validate_catalog(c)
        c = fixture()
        c["designs"][0]["parameters"][0]["state"] = "open"
        with self.assertRaisesRegex(RequestError, "silently fix"):
            validate_catalog(c)

    def test_assist_cannot_claim_required_old_result_and_ids_are_unique(self):
        c = fixture()
        c["designs"][1]["operations"][0]["result"]["old_value"] = "returned"
        with self.assertRaisesRegex(RequestError, "assistance"):
            validate_catalog(c)
        c = fixture()
        c["designs"].append(deepcopy(c["designs"][0]))
        with self.assertRaisesRegex(RequestError, "duplicate ID"):
            validate_catalog(c)

    def test_queries_are_pure_and_invalid_queries_are_errors(self):
        c = fixture()
        before = deepcopy(c)
        result = query_catalog(c, operation="read", subtype="gather")
        result["matches"][0]["requirements"][0]["description"] = "mutated"
        self.assertEqual(c, before)
        with self.assertRaises(RequestError):
            query_catalog(c, operation="read", require_old_value="yes")
        with self.assertRaises(RequestError):
            query_catalog(c, operation="read", design_id="misspelled")

    def test_navigation_tree_does_not_inherit_or_hide_capabilities(self):
        c = fixture()
        c["designs"][1]["record_kind"] = "mapping"
        tree = navigation_tree(c)
        self.assertIn("mapping_reference", tree["branches"]["read"])
        updates = tree["branches"]["read_modify_write"]["execute"]["indirect"]
        self.assertEqual({(x["design_id"],x["operation_id"],x["support"]) for x in updates},
                         {("update","add","code_observed"),("update","cas","unsupported"),("uncertain","cas","unknown")})
        self.assertTrue(all(x["requirement_ids"] for x in updates))
        self.assertEqual(tree["revision"], c["revision"])

    def test_loader_rejects_yaml_overwrite_and_unsafe_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "catalog.yaml"
            p.write_text("format: hardware-catalog-v0.1\nformat: other\n")
            with self.assertRaises(RequestError):
                load_catalog(p)
            p.write_text("!!python/object/apply:os.system ['false']")
            with self.assertRaises(RequestError):
                load_catalog(p)
            p.write_text(yaml.safe_dump(fixture()))
            loaded, digest = load_catalog(p)
            self.assertEqual(loaded, fixture())
            self.assertEqual(len(digest), 64)


