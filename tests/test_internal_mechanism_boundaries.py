"""Mechanism evidence must not silently expand operation or mapping support."""
from copy import deepcopy
import itertools
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import (
    OPERATIONS, PATTERNS, ROLES, load_catalog, navigation_tree, query_catalog,
)
from archevolve.mechanisms import mechanism_context


class InternalMechanismBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current, _ = load_catalog(ROOT / "catalog/hardware-v0.1.yaml")
        cls.baseline = yaml.safe_load(subprocess.check_output(
            ["git", "show", "ef155cd621c466000b5beb910eb66a217a72b50d:catalog/hardware-v0.1.yaml"], cwd=ROOT))
        # A document revision changes provenance, not the supported-operation answer.
        cls.comparable = deepcopy(cls.baseline)
        cls.comparable["revision"] = cls.current["revision"]
        cls.existing_view = deepcopy(cls.current)
        ids = {d["id"] for d in cls.baseline["designs"]}
        cls.existing_view["designs"] = [d for d in cls.current["designs"] if d["id"] in ids]
        old_questions = {q["id"] for q in cls.baseline["decision_questions"]}
        cls.existing_view["decision_questions"] = [q for q in cls.current["decision_questions"] if q["id"] in old_questions]

    def test_all_operation_contracts_and_parameter_states_are_preserved(self):
        before = {d["id"]: d for d in self.baseline["designs"]}
        self.assertEqual({d["id"] for d in self.existing_view["designs"]}, set(before))
        for design in self.existing_view["designs"]:
            for field in ("operations", "requirements", "parameters", "interface", "revision"):
                self.assertEqual(design.get(field), before[design["id"]].get(field), (design["id"], field))
        self.assertEqual(navigation_tree(self.existing_view), navigation_tree(self.comparable))
        for operation, pattern, role, old in itertools.product(
                sorted(OPERATIONS), [None] + sorted(PATTERNS), [None] + sorted(ROLES), [False, True]):
            query = dict(operation=operation, address_pattern=pattern, execution_role=role, require_old_value=old)
            self.assertEqual(query_catalog(self.existing_view, **query), query_catalog(self.comparable, **query))

    def test_new_evidence_remains_within_its_design_and_selected_mapping(self):
        for design in self.current["designs"]:
            for annotation in design.get("internal_mechanisms", []):
                if annotation["status"] != "described":
                    self.assertIsNone(annotation["description"])
                    continue
                for ref in annotation["claim_refs"]:
                    claim = self.current["claims"][ref]
                    self.assertTrue(set(claim["source_refs"]) <= set(design["source_refs"]))
        self.assertNotIn("omi-spzip-ablation", self.current["claims"])
        self.assertEqual(query_catalog(self.current, design_id="prodigy-hpca2021",
                                       operation="read", subtype="gather", execution_role="execute"),
                         query_catalog(self.comparable, design_id="prodigy-hpca2021",
                                       operation="read", subtype="gather", execution_role="execute"))

    def test_described_state_transitions_do_not_hide_remaining_unknowns(self):
        designs = {d["id"]: d for d in self.current["designs"]}
        for did in ("terminus-micro2024-cas", "terminus-micro2024-deferred", "spzip-isca2021-push"):
            context = mechanism_context(designs[did])
            self.assertIn("coalescing", context["missing_kinds"])
            self.assertTrue(any(m["kind"] == "completion" and m["status"] == "unknown"
                                for m in context["annotations"]))
            self.assertIsNone(context["hardware_structure"])
        context = mechanism_context(designs["prodigy-hpca2021"])
        self.assertIn("reordering", context["missing_kinds"])
        self.assertIn("completion", context["missing_kinds"])


if __name__ == "__main__":
    unittest.main()
