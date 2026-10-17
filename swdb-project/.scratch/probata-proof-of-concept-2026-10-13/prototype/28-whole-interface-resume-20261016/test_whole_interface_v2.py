"""2026-10-16 ET. Closed-expression regression and original132 binding controls.

Pure synthetic metadata only. No production import or compiler/native child.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("closed grammar controls: " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
base_path = HERE / "test_whole_interface.py"
context = {"__file__": str(base_path), "__name__": "inherited_source_controls"}
exec(compile(ast.parse(base_path.read_bytes()), str(base_path), "exec"), context)
OLD_API = context["API"]
repaired_path = HERE / "whole_interface_v2.py"
REPAIRED = {"__file__": str(repaired_path), "__name__": "repaired_source_consumer"}
exec(compile(ast.parse(repaired_path.read_bytes()), str(repaired_path), "exec"), REPAIRED)
context["API"] = REPAIRED


class RepairedControls(context["Controls"]):
    def test_07_new_without_call_reproduces_original_gap_and_now_refuses(self):
        row = next(r for r in self.declarations if r["name"] == "maa_stream_load")
        tu, kw = self.fixture(row)
        call = tu["inner"][1]["inner"][0]["inner"][0]
        call["inner"][1] = {"kind": "CXXNewExpr", "isArray": True, "type": {"qualType": "unsigned int *"},
                             "inner": [{"kind": "IntegerLiteral", "value": "2", "type": {"qualType": "unsigned long"}}]}
        # This explicitly reproduces the old defect; it is never admission.
        self.assertEqual(OLD_API["bind_call"](tu, **kw)["name"], "maa_stream_load")
        self.refusal(REPAIRED["bind_call"], tu, **kw)

    def test_08_closed_grammar_effects_unknown_nodes_and_arity_refuse(self):
        row = next(r for r in self.declarations if r["name"] == "maa_alu_scalar")
        kinds = ("CXXDeleteExpr", "StmtExpr", "GCCAsmStmt", "MSAsmStmt", "CXXThrowExpr", "LambdaExpr",
                 "AtomicExpr", "VAArgExpr", "CXXConstructExpr", "CXXTemporaryObjectExpr", "ExprWithCleanups",
                 "MaterializeTemporaryExpr", "OpaqueValueExpr", "UserDefinedLiteral", "CXXFoldExpr", "CXXTypeidExpr",
                 "CoawaitExpr", "CXXBindTemporaryExpr", "CXXDefaultInitExpr", "FutureUnknownExpr")
        mutations = [{"kind": kind, "type": {"qualType": "int"}} for kind in kinds]
        mutations += [{"kind": "UnaryOperator", "opcode": op, "inner": [{"kind": "IntegerLiteral"}]} for op in ("++", "--", "unknown")]
        mutations += [{"kind": "BinaryOperator", "opcode": op, "inner": [{"kind": "IntegerLiteral"}] * 2} for op in ("=", ",", "&&", "||", "unknown")]
        mutations += [{"kind": "ImplicitCastExpr", "castKind": "UserDefinedConversion", "inner": [{"kind": "IntegerLiteral"}]},
                      {"kind": "UnaryExprOrTypeTraitExpr", "name": "vec_step"},
                      {"kind": "IntegerLiteral", "inner": [{"kind": "CXXNewExpr"}]},
                      {"kind": "BinaryOperator", "opcode": "+", "inner": [{"kind": "IntegerLiteral"}]},
                      {"kind": "ParenExpr", "inner": "not compiler children"}]
        for mutation in mutations:
            tu, kw = self.fixture(row)
            tu["inner"][1]["inner"][0]["inner"][0]["inner"][1] = mutation
            self.refusal(REPAIRED["bind_call"], tu, **kw)
        for expression in ({"kind": "DeclRefExpr"},
                           {"kind": "UnaryOperator", "opcode": "-", "inner": [{"kind": "IntegerLiteral"}]},
                           {"kind": "BinaryOperator", "opcode": "+", "inner": [{"kind": "IntegerLiteral"}, {"kind": "DeclRefExpr"}]},
                           {"kind": "ImplicitCastExpr", "castKind": "IntegralCast", "inner": [{"kind": "IntegerLiteral"}]}):
            tu, kw = self.fixture(row)
            tu["inner"][1]["inner"][0]["inner"][0]["inner"][1] = expression
            self.assertEqual(REPAIRED["bind_call"](tu, **kw)["name"], row["name"])

    def test_09_exact_inverse_only_changes_local_expression_predicate(self):
        delta = json.loads((HERE / "whole-interface-v2-inverse-delta.json").read_bytes())
        original = (HERE / "whole_interface.py").read_text()
        repaired = repaired_path.read_text()
        self.assertEqual(repaired.count(delta["new"]), 1)
        self.assertEqual(repaired.replace(delta["new"], delta["old"], 1), original)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), delta["origin_sha256"])
        self.assertEqual(hashlib.sha256(repaired.encode()).hexdigest(), delta["repaired_sha256"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RepairedControls))
    print(json.dumps({"date": "2026-10-16", "tests": result.testsRun, "refusals": RepairedControls.refusals,
                      "original_gap_reproduced": True, "synthetic_bindings": RepairedControls.positive_bindings,
                      "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
                      "compiler_native_execution": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
