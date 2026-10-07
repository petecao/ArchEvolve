"""Pipette adds explicit queue semantics without widening existing mappings."""
from copy import deepcopy
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class PipetteAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.base = yaml.safe_load(subprocess.check_output([
            "git", "show", "b031189cce856c2740882537b3d511721c8474de:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))

    def test_existing_records_and_project_selection_unchanged(self):
        by_id = {d["id"]: d for d in self.catalog["designs"]}
        self.assertEqual([by_id[d["id"]] for d in self.base["designs"]], self.base["designs"])
        self.assertEqual(self.catalog["project_selections"], self.base["project_selections"])
        for group in ("sources", "claims"):
            for key, value in self.base[group].items():
                self.assertEqual(self.catalog[group][key], value)
        by_family = {m["id"]: m for m in self.catalog["mechanism_families"]}
        self.assertEqual([by_family[m["id"]] for m in self.base["mechanism_families"]],
                         self.base["mechanism_families"])
        self.assertEqual(self.catalog["decision_questions"], self.base["decision_questions"])

    def test_explicit_reads_remain_conditional_with_unknown_types(self):
        for subtype in ("pipette_ra_indirect", "pipette_ra_scan"):
            untyped = query_catalog(self.catalog, operation="read", subtype=subtype)
            self.assertEqual(untyped["matches"][0]["status"], "conditional_executor")
            result = query_catalog(self.catalog, operation="read", subtype=subtype,
                                   payload_type="float64", index_width_bits=32)
            self.assertEqual(len(result["matches"]), 1)
            match = result["matches"][0]
            self.assertEqual(match["status"], "needs_evidence")
            self.assertEqual(match["requirement_status"], "not_discharged_by_retrieval")
            self.assertEqual(set(match["missing_capability_evidence"]),
                             {"payload_types", "index_width_bits"})

    def test_normal_gather_queries_and_old_value_requirements_do_not_widen(self):
        baseline = deepcopy(self.base)
        baseline["revision"] = self.catalog["revision"]
        for operation, subtype in (("read", "gather"), ("read", "stream_load"),
                                   ("read_modify_write", "min")):
            request = dict(operation=operation, subtype=subtype, payload_type="int32")
            self.assertEqual(query_catalog(baseline, **request),
                             query_catalog(self.catalog, **request))
        self.assertFalse(query_catalog(self.catalog, operation="read_modify_write",
                                      design_id="pipette-micro2020-committed-queue-ra")["matches"])

    def test_aggregate_resources_and_unbound_coalescing_remain_explicit(self):
        design = next(d for d in self.catalog["designs"] if d["id"] == "pipette-micro2020-committed-queue-ra")
        self.assertEqual(len(design["internal_mechanisms"]), 8)
        parameters = {p["id"]: p for p in design["parameters"]}
        self.assertEqual(parameters["qrm-registers"]["value"], 148)
        self.assertTrue(all(p["state"] == "fixed_reference" and p["domain"] is None
                            for p in parameters.values()))
        mechanism = next(m for m in design["internal_mechanisms"] if m["kind"] == "coalescing")
        self.assertEqual(mechanism["status"], "unknown")
        self.assertIsNone(mechanism["description"])
        self.assertEqual(self.catalog["sources"]["pipette-micro2020-author-primary"]["publication_year"], 2020)
