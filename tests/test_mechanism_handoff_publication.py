"""Publication adds annotations without changing operation semantics."""
import hashlib
import itertools
import json
import subprocess
import unittest

import yaml

from archevolve.__main__ import ROOT
from archevolve.hardware_catalog import load_catalog, query_catalog


class MechanismHandoffPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog()
        cls.baseline = yaml.safe_load(subprocess.check_output([
            "git", "show", "5f420867d46e417ecf1d5c269730e83224a11793:catalog/hardware-v0.1.yaml"
        ], cwd=ROOT))
        cls.baseline["revision"] = cls.catalog["revision"]
        cls.docs = ROOT / "docs/mechanism-handoff-2026-10-06"

    def test_operation_types_requirements_and_parameter_contracts_unchanged(self):
        self.assertEqual(len(self.catalog["designs"]), 10)
        for old, new in zip(self.baseline["designs"], self.catalog["designs"]):
            for field in ("id", "revision", "operations", "requirements", "parameters", "interface"):
                self.assertEqual(old[field], new[field], (old["id"], field))
        for operation, pattern, role, old_value in itertools.product(
                ("read", "write", "read_modify_write", "reduce"),
                (None, "indirect", "ranged_indirect"), (None, "execute", "assist"), (False, True)):
            request = dict(operation=operation, address_pattern=pattern,
                           execution_role=role, require_old_value=old_value)
            self.assertEqual(query_catalog(self.baseline, **request), query_catalog(self.catalog, **request))

    def test_thirteen_maple_fields_preserve_target_coalescing_unknown(self):
        design = next(d for d in self.catalog["designs"] if d["id"] == "maple-isca2022")
        additions = [m for m in design["internal_mechanisms"] if m["id"].startswith("integration-maple-")]
        self.assertEqual(len(additions), 13)
        grouping = next(m for m in additions if m["id"] == "integration-maple-grouping")
        self.assertEqual(grouping["kind"], "buffering")
        context = json.loads((self.docs / "mechanism-handoff.json").read_text())
        self.assertFalse(any(context["claims"].values()))
        self.assertTrue(any(m["kind"] == "coalescing" and m["status"] == "unknown"
                            for m in design["internal_mechanisms"]))

    def test_published_paths_and_scaffold_hash_are_portable(self):
        raw = (self.docs / "mechanism-handoff.json").read_text()
        self.assertNotIn("/data1/", raw)
        self.assertNotIn("/tmp/", raw)
        data = json.loads(raw)
        scaffold = ROOT / data["scaffold_reference"]
        self.assertEqual(hashlib.sha256(scaffold.read_bytes()).hexdigest(), data["scaffold_sha256"])
        for source in data["DX_source_grounding"]:
            for snapshot in source["selected_source_snapshots"]:
                self.assertTrue((ROOT / snapshot["snapshot_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
