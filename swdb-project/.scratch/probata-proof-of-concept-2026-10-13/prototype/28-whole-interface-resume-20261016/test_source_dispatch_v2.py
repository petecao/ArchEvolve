"""2026-10-16 ET. V2 ordinary/MMIO exclusion and exact inverse controls."""
import ast
import hashlib
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
path = HERE / "test_source_dispatch_v1.py"
previous = {"__file__": str(path), "__name__": "inherited_source_dispatch_v1"}
exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), previous)
source = previous["own"]("source_dispatch_v2.py")
previous["SOURCE"] = source


class Controls(previous["Controls"]):
    def test_14_mmio_guest_and_physical_overlap_refuse_and_exact_inverse(self):
        begin, end = source["MMIO_BEGIN"], source["MMIO_END"]
        self.assertEqual(begin, 0x400000000)
        self.assertEqual(end-begin, 2*(32*16384*4)+2*(32*2)+(32*4)+24)
        for key in ("guest_base", "physical_base"):
            for address in (begin, begin+2097152, end-4, begin-4):
                row = previous["object_row"](extent=2);row[key] = address
                with self.assertRaises(source["Refused"]): source["prepare_atlas"]([row])
        atlas = source["prepare_atlas"]([previous["object_row"](guest=end, physical=end)])
        self.assertEqual(atlas["mmio_excluded_span"], [begin, end])
        header = source["render_pointer_bridge"](atlas)
        self.assertIn("ordinary-mmio-alias-refused", header)
        self.assertIn("source-mmio-profile", header)
        self.assertIn("o->guest+span<=begin", header)
        self.assertIn("o->physical+span<=begin", header)
        delta = json.loads((HERE / "source-dispatch-v2-inverse-delta.json").read_bytes())
        original = (HERE / "source_dispatch_v1.py").read_text()
        current = (HERE / "source_dispatch_v2.py").read_text()
        inverse = current
        for edit in reversed(delta["edits"]):
            self.assertEqual(inverse.count(edit["new"]), 1)
            inverse = inverse.replace(edit["new"], edit["old"], 1)
        self.assertEqual(inverse, original)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), delta["origin_sha256"])
        self.assertEqual(hashlib.sha256(current.encode()).hexdigest(), delta["new_sha256"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "compiler_native_project_child_execution": False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
