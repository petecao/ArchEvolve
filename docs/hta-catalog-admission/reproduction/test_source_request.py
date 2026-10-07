import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from source_request import (
    MODES,
    inspect_inputs,
    request_template,
)


class SourceRequestTests(unittest.TestCase):
    def package(self, root):
        manifest = {
            "schema": "HTA_source_package_v1",
            "mode": "zsim_execution_driven",
            "source_root": str(root),
            "files": {},
        }
        for role in MODES[manifest["mode"]]:
            path = root / (role + ".txt")
            path.write_text(
                "NEW synthetic source-role fixture only: " + role + "\n"
            )
            manifest["files"][role] = {
                "path": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        return manifest

    def test_complete_role_pins_do_not_certify_semantics_or_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.package(Path(temporary))
            result = inspect_inputs(manifest)
            self.assertEqual(len(result["roles"]), 6)
            self.assertFalse(result["author_origin_authenticated"])
            self.assertFalse(result["effective_build_flags_certified"])
            self.assertFalse(result["ISA_or_atomic_semantics_certified"])
            self.assertFalse(result["build_or_run_performed"])
        self.assertIsNone(request_template()["source_root"])

    def test_stock_or_native_backend_and_missing_decoder_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self.package(Path(temporary))
            for mode in ["native_x86", "stock_zsim", True]:
                bad = copy.deepcopy(manifest)
                bad["mode"] = mode
                with self.assertRaises(ValueError):
                    inspect_inputs(bad)
            del manifest["files"]["nop_decoder"]
            with self.assertRaisesRegex(ValueError, "nop_decoder"):
                inspect_inputs(manifest)

    def test_mutation_path_escape_symlink_and_binary_substitution_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.package(root)
            source = root / manifest["files"]["nop_decoder"]["path"]
            source.write_text("changed after source pin\n")
            with self.assertRaises(ValueError):
                inspect_inputs(manifest)
            manifest = self.package(root)
            manifest["files"]["nop_decoder"]["path"] = "../outside.cc"
            with self.assertRaises(ValueError):
                inspect_inputs(manifest)
            manifest = self.package(root)
            link = root / "alias.txt"
            link.symlink_to(root / "nop_decoder.txt")
            manifest["files"]["nop_decoder"]["path"] = link.name
            with self.assertRaises(ValueError):
                inspect_inputs(manifest)
            manifest = self.package(root)
            source.write_bytes(b"\x7fELF fake source\n")
            manifest["files"]["nop_decoder"]["sha256"] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            with self.assertRaisesRegex(ValueError, "binary"):
                inspect_inputs(manifest)


if __name__ == "__main__":
    unittest.main()
