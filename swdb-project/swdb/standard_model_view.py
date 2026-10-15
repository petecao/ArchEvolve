"""Checked defensive-at view; created 2026-10-15 ET (ticket 25).

The source/native/CBMC model retains its defensive abort. Under its unchanged contract,
WP checks a named assertion of the guard's negation before the identical return. Only
the exact audited model and a pure, independently parsed C-AST shape are admitted.
This does not discharge pointer array-object provenance or broaden the model domain.
"""
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from swdb import c_lowering, std_models

MODEL_SHA256 = "cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2"
TEXT_SHA256 = "558f2f79db45fc8d947335193a572585d34f81861d1f02157608a966ae8700e9"
GUARD = '  if (n >= this->size) SWDB_MODEL_FAIL("std.vector.at.out_of_range");'
ASSERTION = "  /*@ assert at_guard_false: n < this->size; */"


class Refused(ValueError):
    """The exact pure defensive guard relation is not established."""


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    return {"id": "standard-model-view-check-1", "sha256": _sha(Path(__file__).read_bytes())}


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def _strip(node):
    while node.get("kind") == "ImplicitCastExpr":
        children = _children(node)
        if len(children) != 1 or node.get("castKind") not in ("LValueToRValue", "FunctionToPointerDecay"):
            raise Refused("the defensive guard contains an unsupported conversion")
        node = children[0]
    return node


def _ref(node, declaration):
    node = _strip(node)
    return node.get("kind") == "DeclRefExpr" and (node.get("referencedDecl") or {}).get("id") == declaration["id"]


def _member(node, field, owner):
    node = _strip(node)
    children = _children(node)
    return (node.get("kind") == "MemberExpr" and node.get("name") == field and node.get("isArrow")
            and len(children) == 1 and _ref(children[0], owner))


def _shape(text, directory):
    # stdlib supplies abort's declaration for independent C parsing; it does not
    # change the original model or introduce a WP premise.
    path = Path(directory) / "standard_model_original_ast.c"
    path.write_text("\n".join([*c_lowering.HEADERS, "#include <stdlib.h>", text]) + "\n")
    result = subprocess.run([*c_lowering.locate().command, "-x", "c", "-std=c11", "-fsyntax-only",
                             "-Xclang", "-ast-dump=json", "-Xclang", "-ast-dump-filter=std_vector_int_at",
                             str(path)], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise Refused("the pinned C parser rejected the original defensive-at model")
    try:
        function = json.loads(result.stdout)
        owner, index, body = _children(function)
        guard, returned = _children(body)
        condition, abort = _children(guard)
        left, right = _children(condition)
        callee, = _children(abort)
        addition, = _children(returned)
        data, offset = _children(addition)
    except (ValueError, KeyError, TypeError):
        raise Refused("the defensive-at model does not have the audited C-AST structure") from None
    if not (function.get("kind") == "FunctionDecl" and function.get("name") == "std_vector_int_at"
            and owner.get("kind") == index.get("kind") == "ParmVarDecl"
            and owner.get("name") == "this" and index.get("name") == "n"
            and body.get("kind") == "CompoundStmt" and guard.get("kind") == "IfStmt"
            and condition.get("kind") == "BinaryOperator" and condition.get("opcode") == ">="
            and _ref(left, index) and _member(right, "size", owner)
            and abort.get("kind") == "CallExpr" and _strip(callee).get("kind") == "DeclRefExpr"
            and (_strip(callee).get("referencedDecl") or {}).get("name") == "abort"
            and returned.get("kind") == "ReturnStmt"
            and addition.get("kind") == "BinaryOperator" and addition.get("opcode") == "+"
            and _member(data, "data", owner) and _ref(offset, index)):
        raise Refused("only the pure n>=this->size abort and unchanged data+n return are admitted")
    return {"function": "std_vector_int_at", "guard": "n >= this->size", "guard_effects": [],
            "then": "abort()", "else": None, "return": "this->data + n"}


@dataclass(frozen=True)
class View:
    original: str
    text: str
    certificate: dict
    pins: dict


def wp_view(name, text, directory):
    if name != "std_vector_int_at" or std_models.identity()["sha256"] != MODEL_SHA256:
        raise Refused("the defensive-at view requires the exact audited standard-model version")
    if _sha(text) != TEXT_SHA256 or text.count(GUARD) != 1:
        raise Refused("the original defensive-at body and bounds contract must match the audited model exactly")
    shape = _shape(text, directory)
    transformed = text.replace(GUARD, ASSERTION)
    contract = text[text.index("/*@ requires"):text.index("static int *std_vector_int_at")]
    certificate = {"version": 1, "model": std_models.identity(), "original_text_sha256": _sha(text),
                   "view_text_sha256": _sha(transformed), "original_contract_sha256": _sha(contract),
                   "view_contract_sha256": _sha(contract), "source_ast": shape,
                   "mapping": {"source": GUARD.strip(), "view": ASSERTION.strip()},
                   "guard_elision_obligation": "at_guard_false", "input_premises_added": []}
    return View(text, transformed, certificate,
                {"standard_model_view_check": identity(),
                 "standard_model_view_certificate": {"id": "standard-model-view-certificate-1",
                                                     "sha256": _digest(certificate)}})


def check_view(name, view, directory):
    if view != wp_view(name, c_lowering.model_text(name), directory):
        raise Refused("the defensive-at source, bounds contract, view or certificate changed before launch")
