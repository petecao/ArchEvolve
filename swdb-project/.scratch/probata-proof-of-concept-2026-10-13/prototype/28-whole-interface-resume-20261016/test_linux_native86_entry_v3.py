"""2026-10-16 ET. V3 raw-name-only pure inverse; V1/V2 remain frozen."""
import ast
import hashlib
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
path = HERE / "test_linux_native86_entry_v2.py"
previous = {"__file__": str(path), "__name__": "inert_native_v2_controls"}
exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), previous)


class Controls(previous["Controls"]):
    def test_v3_raw_only_inverse(self):
        delta = json.loads((HERE / "linux-native86-v3-inverse-delta.json").read_bytes())
        before = (HERE / "linux_native86_entry_v2.py").read_text()
        after = (HERE / "linux_native86_entry_v3.py").read_text()
        self.assertEqual(after.count(delta["new"]), 1)
        self.assertEqual(after.replace(delta["new"], delta["old"], 1), before)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), delta["origin_sha256"])
        self.assertEqual(hashlib.sha256(after.encode()).hexdigest(), delta["new_sha256"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "cases": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "compiler_native_project_child_execution": False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
