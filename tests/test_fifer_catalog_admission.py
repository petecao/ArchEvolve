"""Fifer has explicit stage/DRM mappings without inherited queue ABIs."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class FiferAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "2171ecd61f55b516c4f38b9ac82422d9f148e1ac:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.design = next(d for d in cls.catalog["designs"] if d["id"] == "fifer-micro2021-staged-DRM")

    def test_prior_records_claims_and_selections_unchanged(self):
        self.assertEqual(self.catalog["designs"][:-1], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        for group in ("sources", "claims"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)
        self.assertEqual(self.catalog["mechanism_families"][:-1], self.base["mechanism_families"])

    def test_explicit_DRM_mapping_and_typed_evidence_boundary(self):
        for subtype in ("fifer_drm_dereference", "fifer_drm_scan"):
            request = dict(operation="read", subtype=subtype, design_id=self.design["id"])
            match = query_catalog(self.catalog, **request)["matches"][0]
            self.assertEqual(match["status"], "mapping_reference")
            self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
            match = query_catalog(self.catalog, **request, payload_type="float64",
                                  index_width_bits=32)["matches"][0]
            self.assertEqual(match["status"], "needs_evidence")
            self.assertEqual(set(match["missing_capability_evidence"]),
                             {"payload_types", "index_width_bits"})

    def test_gather_Pipette_and_old_value_not_inherited(self):
        base = deepcopy(self.base)
        base["revision"] = self.catalog["revision"]
        self.assertEqual(query_catalog(base, operation="read", subtype="gather"),
                         query_catalog(self.catalog, operation="read", subtype="gather"))
        for subtype in ("gather", "pipette_ra_indirect", "extensor_ordered_fiber_operand_pair"):
            self.assertFalse(query_catalog(self.catalog, operation="read", subtype=subtype,
                                          design_id=self.design["id"])["matches"])
        self.assertFalse(query_catalog(self.catalog, operation="read", design_id=self.design["id"],
                                      require_old_value=True)["matches"])

    def test_reference_capacity_and_switch_order_obligations(self):
        requirements = {r["id"]: r for r in self.design["requirements"]}
        self.assertEqual(requirements["switch-drain"]["verification"], "required")
        self.assertEqual(requirements["DRM-order"]["verification"], "required")
        self.assertEqual(requirements["physical-ABI-completion"]["verification"], "unknown")
        parameters = {p["id"]: p for p in self.design["parameters"]}
        self.assertEqual(parameters["queue-SRAM"]["value"], 16)
        self.assertEqual(parameters["configuration-activation"]["value"], 2)
        self.assertEqual(parameters["queue-SRAM"]["state"], "fixed_reference")
        self.assertIsNone(parameters["queue-SRAM"]["domain"])
