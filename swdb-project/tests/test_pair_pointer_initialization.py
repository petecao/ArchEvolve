"""2026-10-16 ET. Public initializedness admission for value-only mixed pairs.

Small Clang-shaped inputs exercise the policy without launching tools. The real
compiler/native and eight-record workflow tests cover the retained source form.
"""
import copy

import pytest

from swdb.bounded_initialization import analyze


PAIR = "std::pair<int, int *>"
TYPES = {"std_pair_int_int_ptr": {"cpp": PAIR, "kind": "pair", "elements": ["int", "int *"]}}


def node(kind, typ="int", *parts, **fields):
    return {"kind": kind, "type": {"qualType": typ}, "inner": list(parts), **fields}


def ref(name, typ="int"):
    return node("DeclRefExpr", typ, referencedDecl={"id": name, "kind": "VarDecl"})


def local(name, typ, init):
    return node("VarDecl", typ, init, id=name, init="c")


def member(name="second"):
    return node("MemberExpr", "int *" if name == "second" else "int", ref("pair", PAIR), name=name)


def report(*body, standard_types=TYPES):
    function = node("FunctionDecl", "int ()", node("CompoundStmt", "void", *body), name="f")
    return analyze({"f": function}, scalar_types={"int"}, source_sha256="0"*64,
                   text="retained-policy-control", standard_types=standard_types)


def setup():
    return [local("left", "int", node("IntegerLiteral", value="1")),
            local("pair", PAIR, node("CXXConstructExpr", PAIR, node("IntegerLiteral", value="2"),
                  node("UnaryOperator", "int *", ref("left"), opcode="&")))]


def test_initialized_pointer_fields_support_identity_copy_and_assignment():
    body = setup()
    body += [local("copy", PAIR, node("CXXConstructExpr", PAIR, ref("pair", PAIR))),
             node("BinaryOperator", "int *", member(), node("CXXNullPtrLiteralExpr", "std::nullptr_t"), opcode="="),
             node("ReturnStmt", "void", node("BinaryOperator", "bool", member(),
                  node("CXXNullPtrLiteralExpr", "std::nullptr_t"), opcode="=="))]
    result = report(*body)
    assert result["verdict"] == "passed", result
    assert "pointer" in result["standard_policy"]["initialized"]


@pytest.mark.parametrize("operation", ["dereference", "subscript", "arithmetic", "escape", "return", "cast", "assignment"])
def test_initialized_pointer_value_does_not_grant_pointee_access_or_escape(operation):
    body = setup()
    assert report(*body)["verdict"] == "passed"
    if operation == "dereference":
        expression = node("UnaryOperator", "int", member(), opcode="*")
    elif operation == "subscript":
        expression = node("ArraySubscriptExpr", "int", member(), node("IntegerLiteral", value="0"))
    elif operation == "arithmetic":
        expression = node("BinaryOperator", "int *", member(), node("IntegerLiteral", value="1"), opcode="+")
    elif operation == "escape":
        expression = node("CallExpr", "int", node("DeclRefExpr", "int (int *)", referencedDecl={
            "kind": "FunctionDecl", "name": "opaque"}), member())
    elif operation == "return":
        expression = node("ReturnStmt", "void", member())
    elif operation == "cast":
        expression = node("CXXReinterpretCastExpr", "long", member(), castKind="PointerToIntegral")
    else:
        body.append(node("VarDecl", "int *", id="unknown"))
        expression = node("BinaryOperator", "int *", member(), ref("unknown", "int *"), opcode="=")
    result = report(*body, expression)
    assert result["verdict"] == "refused", result


def test_unknown_pointer_and_uninitialized_local_address_remain_refused():
    for body in (setup()[1:], [node("VarDecl", "int", id="left"), *setup()[1:]]):
        result = report(*copy.deepcopy(body))
        assert result["verdict"] == "refused", result


def test_default_null_field_is_initialized_but_cannot_be_dereferenced():
    body = [local("pair", PAIR, node("CXXConstructExpr", PAIR))]
    assert report(*body)["verdict"] == "passed"
    compared = node("BinaryOperator", "bool", member(), node("CXXNullPtrLiteralExpr", "std::nullptr_t"), opcode="==")
    assert report(*body, compared)["verdict"] == "passed"
    assert report(*body, node("UnaryOperator", "int", member(), opcode="*"))["verdict"] == "refused"


def test_nonpointer_comparison_visits_mutating_operand_once():
    types = {**TYPES, "std_vector_int": {"cpp": "std::vector<int>", "kind": "vector", "elements": ["int"]}}
    def call(name, *args):
        return node("CXXMemberCallExpr", "int *" if name == "data" else "void",
                    node("MemberExpr", "void ()", ref("vector", "std::vector<int>"), name=name), *args)
    body = [local("vector", "std::vector<int>", node("CXXConstructExpr", "std::vector<int>")),
            node("BinaryOperator", "bool", node("BinaryOperator", "int",
                 call("push_back", node("IntegerLiteral", value="1")), node("IntegerLiteral", value="1"), opcode=","),
                 node("IntegerLiteral", value="1"), opcode="==")]
    assert report(*body, standard_types=types)["verdict"] == "passed"
    result = report(*body, node("ArraySubscriptExpr", "int", call("data"), node("IntegerLiteral", value="1")),
                    standard_types=types)
    assert result["verdict"] == "refused" and "live prefix" in result["reason"], result
