"""SMASH identifies blocks; operand loads and arithmetic remain external."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class SmashAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "fb3133695dacf0ee23f705f2dffc620ba641b647:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.design = next(d for d in cls.catalog["designs"] if d["id"] == "smash-micro2019-bitmap-block-index")

    def test_prior_records_claims_selection_unchanged(self):
        by_id = {d["id"]: d for d in self.catalog["designs"]}
        self.assertEqual([by_id[d["id"]] for d in self.base["designs"]], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        for group in ("sources", "claims"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)
        by_family = {m["id"]: m for m in self.catalog["mechanism_families"]}
        self.assertEqual([by_family[m["id"]] for m in self.base["mechanism_families"]],
                         self.base["mechanism_families"])

    def test_explicit_block_index_is_assistance_with_unknown_ABI(self):
        request = dict(operation="read", subtype="smash_bitmap_block_index", design_id=self.design["id"])
        match = query_catalog(self.catalog, **request)["matches"][0]
        self.assertEqual(match["operation"]["execution_role"], "assist")
        self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
        match = query_catalog(self.catalog, **request, payload_type="float64",
                              index_width_bits=32)["matches"][0]
        self.assertEqual(match["status"], "needs_evidence")
        self.assertEqual(set(match["missing_capability_evidence"]), {"payload_types", "index_width_bits"})

    def test_gather_execution_and_arithmetic_not_inherited(self):
        base = deepcopy(self.base)
        base["revision"] = self.catalog["revision"]
        self.assertEqual(query_catalog(base, operation="read", subtype="gather"),
                         query_catalog(self.catalog, operation="read", subtype="gather"))
        self.assertFalse(query_catalog(self.catalog, operation="read", design_id=self.design["id"],
                                      execution_role="execute")["matches"])
        for operation in ("reduce", "read_modify_write"):
            self.assertFalse(query_catalog(self.catalog, operation=operation,
                                          design_id=self.design["id"])["matches"])

    def test_block_presence_does_not_establish_lane_validity_or_completion(self):
        requirements = {r["id"]: r for r in self.design["requirements"]}
        self.assertEqual(requirements["NZA-rank"]["verification"], "required")
        self.assertIn("all lanes nonzero", requirements["NZA-rank"]["description"])
        self.assertEqual(requirements["actual-ISA-memory-ABI"]["verification"], "unknown")
        self.assertIn("zero", self.catalog["claims"]["smash-zero-lanes"]["statement"])
        self.assertEqual(len(self.design["internal_mechanisms"]), 6)
