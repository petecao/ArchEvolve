"""2026-10-16 ET. Synthetic AST V3 controls; no compiler/project children."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
test_path = HERE / "test_whole_interface_v2.py"
previous = {"__file__": str(test_path), "__name__": "inherited_v2_controls"}
exec(compile(ast.parse(test_path.read_bytes()), str(test_path), "exec"), previous)
source_path = HERE / "whole_interface_v3.py"
CURRENT = {"__file__": str(source_path), "__name__": "closed_v3_consumer"}
exec(compile(ast.parse(source_path.read_bytes()), str(source_path), "exec"), CURRENT)
previous["REPAIRED"] = CURRENT
previous["context"]["API"] = CURRENT


class Controls(previous["RepairedControls"]):
    def test_09_exact_inverse_only_changes_local_expression_predicate(self):
        delta = json.loads((HERE / "whole-interface-v3-inverse-delta.json").read_bytes())
        old = (HERE / "whole_interface_v2.py").read_text()
        new = source_path.read_text()
        self.assertEqual(new.count(delta["new"]), 1)
        self.assertEqual(new.replace(delta["new"], delta["old"], 1), old)
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(), delta["origin_sha256"])
        self.assertEqual(hashlib.sha256(new.encode()).hexdigest(), delta["repaired_sha256"])

    def test_10_type_traits_including_hidden_vla_bounds_refuse(self):
        row = next(r for r in self.declarations if r["name"] == "maa_alu_scalar")
        for name in ("sizeof", "alignof", "vec_step"):
            for arg_type in ({"qualType": "int"}, {"qualType": "int[n++]"}, {"qualType": "int[side_effect()]"}):
                tu, kw = self.fixture(row)
                tu["inner"][1]["inner"][0]["inner"][0]["inner"][1] = {
                    "kind": "UnaryExprOrTypeTraitExpr", "name": name, "type": {"qualType": "unsigned long"}, "argType": arg_type}
                self.refusal(CURRENT["bind_call"], tu, **kw)

    def test_11_alias_hidden_and_direct_volatile_and_bad_type_metadata_refuse(self):
        row = next(r for r in self.declarations if r["name"] == "maa_alu_scalar")
        for actual_type in ({"qualType": "volatile int"}, {"qualType": "VI", "desugaredQualType": "volatile int"},
                            {"qualType": "VRI", "desugaredQualType": "volatile int &"},
                            {"qualType": "VI", "desugaredQualType": "int *volatile"},
                            {"qualType": "int", "desugaredQualType": 42}, "not a type object"):
            tu, kw = self.fixture(row)
            tu["inner"][1]["inner"][0]["inner"][0]["inner"][1] = {"kind": "DeclRefExpr", "type": actual_type}
            self.refusal(CURRENT["bind_call"], tu, **kw)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "tests": result.testsRun, "refusals": Controls.refusals,
        "synthetic_bindings": Controls.positive_bindings, "failures": len(result.failures), "errors": len(result.errors),
        "skips": len(result.skipped), "compiler_native_project_child_execution": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
