"""2026-10-16 ET. V4 raw inverse and exact native guard binding; no tools."""
import ast
import hashlib
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
path = HERE / "test_linux_native86_entry_v3.py"
previous = {"__file__": str(path), "__name__": "inert_native_v3_controls"}
exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), previous)


class Controls(previous["Controls"]):
    def test_v4_raw_inverse_and_root_native_guard_literals(self):
        delta = json.loads((HERE / "linux-native86-v4-inverse-delta.json").read_bytes())
        before = (HERE / "linux_native86_entry_v3.py").read_text()
        after = (HERE / "linux_native86_entry_v4.py").read_text()
        self.assertEqual(after.count(delta["new"]), 1)
        self.assertEqual(after.replace(delta["new"], delta["old"], 1), before)
        self.assertEqual(hashlib.sha256(before.encode()).hexdigest(), delta["origin_sha256"])
        self.assertEqual(hashlib.sha256(after.encode()).hexdigest(), delta["new_sha256"])
        tree = ast.parse((HERE / "prepare_linux_native86_v4.py").read_bytes())
        literals = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                        and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "ROOT_NATIVE_GUARD_FILES")
        self.assertEqual(literals, {"execute.py": "8442533f911e2ba7f10757a5b16ba451d4ece7d9d5dc292ce5b9d8c29eabdcbf",
                                   "watch.py": "49be8a36d6e04b50e1ab599dad8b00f78a1c639132c3079c523c2c0c9177c5f0"})
        self.assertEqual(literals, delta["guard_files"])
        self.assertIn("WHOLE_SECONDS, ENTRY_SECONDS, RSS_BYTES = 180, 165, 4294967296", after)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "cases": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "compiler_native_project_child_execution": False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
