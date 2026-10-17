"""2026-10-16 ET. V2 pure inverse and policy link refusal controls."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
path = HERE / "test_linux_native86_entry_v1.py"
previous = {"__file__": str(path), "__name__": "inert_v1_native_controls"}
exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), previous)
previous["PATH"] = HERE / "linux_native86_entry_v2.py"
previous["TREE"] = ast.parse(previous["PATH"].read_bytes())
previous["FUNCTIONS"] = {n.name: n for n in previous["TREE"].body if isinstance(n, ast.FunctionDef)}


class Controls(previous["NativeSourceControls"]):
    def test_v2_inverse_and_policy_same_bytes_symlink_regression(self):
        delta = json.loads((HERE / "linux-native86-v2-inverse-delta.json").read_bytes())
        original = (HERE / "linux_native86_entry_v1.py").read_text()
        modified = (HERE / "linux_native86_entry_v2.py").read_text()
        inverse = modified
        for change in reversed(delta["changes"]):
            self.assertEqual(inverse.count(change["new"]), 1)
            inverse = inverse.replace(change["new"], change["old"], 1)
        self.assertEqual(inverse, original)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), delta["origin"]["sha256"])
        self.assertEqual(hashlib.sha256(modified.encode()).hexdigest(), delta["new_sha256"])
        def projected(text, context):
            main = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == "main")
            check = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "control_check")
            exec(compile(ast.Module(body=[check], type_ignores=[]), "<policy-physical-fixture>", "exec"), context)
            return context["control_check"]
        with tempfile.TemporaryDirectory(prefix="native86-policy-", dir=HERE) as directory:
            root = Path(directory);control = root / "control";control.mkdir()
            entry = control / "entry.py";entry.write_text("inert source\n")
            policy_path = control / "policy.json";policy_path.write_text("inert policy bytes\n")
            def pin(path):
                return {"path": str(Path(path)), "bytes": Path(path).stat().st_size,
                        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}
            context = {"Path": Path, "stat": stat, "hashlib": hashlib, "control": control, "policy_path": policy_path,
                "controls": {entry.name: {k: v for k, v in pin(entry).items() if k != "path"}}, "pin": pin,
                "__file__": str(entry), "policy": {"entry_sha256": pin(entry)["sha256"]}, "argv": [0, 0, 0, 0, pin(policy_path)["sha256"]]}
            old = projected(original, dict(context));new = projected(modified, dict(context))
            old();new()
            target = root / "same-policy-bytes.json";target.write_bytes(policy_path.read_bytes())
            policy_path.unlink();policy_path.symlink_to(target)
            old()  # Reproduces the previous source-only same-bytes link gap.
            with self.assertRaisesRegex(ValueError, "physical regular policy"): new()
            policy_path.unlink();os.mkfifo(policy_path)
            with self.assertRaisesRegex(ValueError, "physical regular policy"): new()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "cases": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "old_same_bytes_link_gap_reproduced": True,
        "compiler_native_project_child_execution": False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
