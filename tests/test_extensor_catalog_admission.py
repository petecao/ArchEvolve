"""Explicit tensor operand delivery preserves existing catalog mappings."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class ExTensorAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "e5895a50a3d876583f575eb3886b0c14c55ef834:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.design = next(d for d in cls.catalog["designs"]
                          if d["id"] == "extensor-micro2019-ordered-fiber-operands")

    def test_prior_semantics_claims_and_selection_unchanged(self):
        self.assertEqual(self.catalog["designs"][:-1], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        for group in ("claims", "sources"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)
        self.assertEqual(self.catalog["mechanism_families"][:-1], self.base["mechanism_families"])

    def test_generic_gather_reduction_and_old_value_not_inherited(self):
        base = deepcopy(self.base)
        base["revision"] = self.catalog["revision"]
        self.assertEqual(query_catalog(base, operation="read", subtype="gather"),
                         query_catalog(self.catalog, operation="read", subtype="gather"))
        for operation in ("reduce", "read_modify_write"):
            self.assertFalse(query_catalog(self.catalog, operation=operation,
                                          design_id=self.design["id"])["matches"])

    def test_explicit_pair_has_scoped_payload_and_unknown_coordinate_width(self):
        request = dict(operation="read", subtype="extensor_ordered_fiber_operand_pair",
                       design_id=self.design["id"], payload_type="float64")
        match = query_catalog(self.catalog, **request)["matches"][0]
        self.assertEqual(match["status"], "mapping_reference")
        self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
        match = query_catalog(self.catalog, **request, index_width_bits=32)["matches"][0]
        self.assertEqual(match["status"], "needs_evidence")
        self.assertIn("index_width_bits", match["missing_capability_evidence"])
        request["payload_type"] = "float32"
        self.assertFalse(query_catalog(self.catalog, **request)["matches"])

    def test_canonical_and_completion_obligations_are_explicit(self):
        required = {r["id"]: r for r in self.design["requirements"]}
        self.assertEqual(required["canonical-fibers"]["verification"], "required")
        self.assertIn("unique", required["canonical-fibers"]["description"])
        self.assertEqual(required["numeric-order"]["verification"], "required")
        host = next(m for m in self.design["internal_mechanisms"] if m["id"] == "host-completion-ABI")
        self.assertEqual(host["status"], "unknown")
        self.assertTrue(all(p["state"] == "fixed_reference" and p["domain"] is None
                            for p in self.design["parameters"]))
