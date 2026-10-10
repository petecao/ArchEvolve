"""PHI is an explicit bulk interface, not a generic scatter substitution."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class PhiAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "11eb2c2b4ea7d416d29c7c14ec573e33c33133ff:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.design = next(d for d in cls.catalog["designs"]
                          if d["id"] == "phi-micro2019-relaxed-bulk-scatter")

    def test_prior_records_and_project_choices_unchanged(self):
        by_id = {d["id"]: d for d in self.catalog["designs"]}
        self.assertEqual([by_id[d["id"]] for d in self.base["designs"]], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        by_family = {m["id"]: m for m in self.catalog["mechanism_families"]}
        self.assertEqual([by_family[m["id"]] for m in self.base["mechanism_families"]],
                         self.base["mechanism_families"])
        for group in ("sources", "claims"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)

    def test_gather_and_returned_old_are_not_granted(self):
        base = deepcopy(self.base)
        base["revision"] = self.catalog["revision"]
        self.assertEqual(query_catalog(base, operation="read", subtype="gather"),
                         query_catalog(self.catalog, operation="read", subtype="gather"))
        self.assertFalse(query_catalog(self.catalog, operation="reduce",
                                      design_id=self.design["id"], require_old_value=True)["matches"])
        self.assertFalse(query_catalog(self.catalog, operation="read_modify_write",
                                      design_id=self.design["id"])["matches"])

    def test_double_add_conditional_integer_abi_needs_evidence(self):
        result = query_catalog(self.catalog, operation="reduce", subtype="phi_bulk_float64_add",
                               payload_type="float64")
        match = result["matches"][0]
        self.assertEqual(match["status"], "conditional_executor")
        self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
        result = query_catalog(self.catalog, operation="reduce", subtype="phi_bulk_integer_update",
                               payload_type="int32", index_width_bits=32)
        self.assertEqual(result["matches"][0]["status"], "needs_evidence")
        self.assertEqual(set(result["matches"][0]["missing_capability_evidence"]),
                         {"payload_types", "index_width_bits"})

    def test_flush_physical_and_numeric_obligations_remain_required(self):
        requirements = {r["id"]: r for r in self.design["requirements"]}
        for key in ("bulk-no-reads", "flush-before-read", "physical-data-bins", "numeric-legality"):
            self.assertEqual(requirements[key]["verification"], "required")
        self.assertEqual(requirements["actual-source"]["verification"], "unknown")
        self.assertEqual(len(self.design["internal_mechanisms"]), 6)
        source = self.catalog["sources"]["phi-micro2019-author-primary"]
        self.assertEqual(source["publication_year"], 2019)
        self.assertEqual(source["doi"], "10.1145/3352460.3358254")
