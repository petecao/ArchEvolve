"""Flat-HTA maps keys explicitly and separates consumer inference from facts."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class HtaAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "4982b73b3bc1ea13cc6d3d130ec90ae21b827fb3:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.design = next(d for d in cls.catalog["designs"] if d["id"] == "flat-hta-micro2019-integer-key-map")

    def test_latest_SMASH_and_all_prior_records_preserved(self):
        self.assertEqual(self.catalog["designs"][:-1], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        for group in ("sources", "claims"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)
        self.assertEqual(self.catalog["mechanism_families"][:-1], self.base["mechanism_families"])

    def test_four_explicit_key_operations_keep_unknown_index_ABI(self):
        for operation, suffix in (("read", "lookup"), ("write", "update"),
                                  ("write", "swap"), ("write", "delete")):
            request = dict(operation=operation, subtype="flat_hta_integer64_key_" + suffix,
                           design_id=self.design["id"], payload_type="uint64")
            match = query_catalog(self.catalog, **request)["matches"][0]
            self.assertEqual(match["status"], "mapping_reference")
            self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
            match = query_catalog(self.catalog, **request, index_width_bits=32)["matches"][0]
            self.assertEqual(match["status"], "needs_evidence")
            self.assertIn("index_width_bits", match["missing_capability_evidence"])

    def test_gather_CAS_requested_old_value_and_FP_not_granted(self):
        base = deepcopy(self.base)
        base["revision"] = self.catalog["revision"]
        self.assertEqual(query_catalog(base, operation="read", subtype="gather"),
                         query_catalog(self.catalog, operation="read", subtype="gather"))
        self.assertFalse(query_catalog(self.catalog, operation="read_modify_write",
                                      design_id=self.design["id"])["matches"])
        self.assertFalse(query_catalog(self.catalog, operation="write", require_old_value=True,
                                      design_id=self.design["id"])["matches"])
        self.assertFalse(query_catalog(self.catalog, operation="read", payload_type="float64",
                                      design_id=self.design["id"])["matches"])

    def test_mixed_owner_regression_is_inference_not_published_wrapper_fault(self):
        claim = self.catalog["claims"]["hta-mixed-owner-obligation"]
        self.assertEqual(claim["evidence_kind"], "research_inference")
        self.assertIn("not a demonstrated fault", claim["statement"])
        for key in ("hta-line-format", "hta-update-swap-delete", "hta-concurrent-fallback"):
            self.assertEqual(self.catalog["claims"][key]["evidence_kind"], "paper_specification")
        self.assertEqual(len(self.design["operations"]), 4)
