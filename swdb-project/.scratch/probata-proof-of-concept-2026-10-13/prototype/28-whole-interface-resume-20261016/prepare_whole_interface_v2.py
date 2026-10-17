"""2026-10-16 ET. Source-only repair of independently found argument gap.

Original source/value packets stay frozen. Replace the one local expression
predicate with a closed grammar; no production import, compiler or runtime.
"""
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGIN_SHA256 = "b859035b88dd267a7515e208c5a524ea7bd2cacde147e43b6723e2067303b44c"
GRAMMAR = '''    def pure(node):
        kind, op = node.get("kind"), node.get("opcode")
        arities = {
            "IntegerLiteral": (0,), "FloatingLiteral": (0,), "CharacterLiteral": (0,),
            "CXXBoolLiteralExpr": (0,), "CXXNullPtrLiteralExpr": (0,), "GNUNullExpr": (0,),
            "DeclRefExpr": (0,), "CXXDefaultArgExpr": (0,),
            "ParenExpr": (1,), "ConstantExpr": (1,), "UnaryOperator": (1,),
            "ImplicitCastExpr": (1,), "CStyleCastExpr": (1,), "CXXStaticCastExpr": (1,),
            "CXXFunctionalCastExpr": (1,), "CXXReinterpretCastExpr": (1,),
            "MemberExpr": (1,), "ArraySubscriptExpr": (2,), "BinaryOperator": (2,),
            "UnaryExprOrTypeTraitExpr": (0, 1),
        }
        _need(kind in arities, "source argument expression is outside the closed pure grammar")
        children = node.get("inner", [])
        _need(isinstance(children, list) and all(isinstance(c, dict) for c in children)
              and len(children) in arities[kind], "source argument expression arity differs")
        _need("volatile" not in node.get("type", {}).get("qualType", ""), "volatile source argument refused")
        if kind == "UnaryOperator":
            _need(op in ("+", "-", "~", "!", "&", "*"), "source unary effect/operator refused")
        elif kind == "BinaryOperator":
            _need(op in ("+", "-", "*", "/", "%", "<<", ">>", "&", "|", "^", "<", ">", "<=", ">=", "==", "!="),
                  "source binary effect/operator refused")
        elif kind.endswith("CastExpr"):
            _need(node.get("castKind") in ("LValueToRValue", "ArrayToPointerDecay", "NoOp", "IntegralCast",
                  "IntegralToBoolean", "PointerToBoolean", "BitCast", "FloatingCast", "IntegralToFloating",
                  "FloatingToIntegral", "FloatingToBoolean", "NullToPointer", "PointerToIntegral", "IntegralToPointer"),
                  "source argument conversion is outside the closed grammar")
        elif kind == "UnaryExprOrTypeTraitExpr":
            _need(node.get("name") in ("sizeof", "alignof"), "source type-trait expression refused")
        for child in children:
            pure(child)
'''


def prepare():
    original = (HERE / "whole_interface.py").read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGIN_SHA256:
        raise ValueError("frozen original binder changed")
    text = original.decode()
    begin = text.index("    def pure(node):\n")
    end = text.index("    for argument in arguments:\n", begin)
    old = text[begin:end]
    repaired = text[:begin] + GRAMMAR + text[end:]
    tree = ast.parse(repaired)
    (HERE / "whole_interface_v2.py").write_text(repaired)
    recipe = {"date": "2026-10-16", "origin_sha256": ORIGIN_SHA256,
              "repaired_sha256": hashlib.sha256(repaired.encode()).hexdigest(),
              "old": old, "new": GRAMMAR,
              "scope": "closed source-argument AST grammar only; source/value packets unchanged; no public admission"}
    (HERE / "whole-interface-v2-inverse-delta.json").write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n")
    return tree


if __name__ == "__main__":
    prepare()
