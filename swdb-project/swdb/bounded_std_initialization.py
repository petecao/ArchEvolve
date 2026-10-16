"""Initialized live-prefix admission for exact std-model bodies; created 2026-10-15 ET.

This is a restricted source protocol, not an assumption that arbitrary std code is initialized.
The audited scalar vector bodies initialize every live element; spare capacity is never included.
Raw data/iterator reads require a statically initialized prefix at capture. Real malloc/free and
CBMC pointer checks still decide lifetime failures after growth; no pool or lifetime premise is added.
"""

from dataclasses import dataclass
import re

from swdb import std_models


# Audited ctor/count/value, append/grow, accessors, scalar pair constructors/copy/assignment and scope destructor.
# A body change requires a new audit; the method's model pin alone cannot grant this policy.
AUDITED_MODEL = {"id": "swdb-std-models-2",
                 "sha256": "cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2"}
POLICY_ID = "std-live-prefix-initialization-1"
UNHANDLED = object()


def children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def qual(node):
    typ = node.get("type") or {}
    return typ.get("desugaredQualType", typ.get("qualType", ""))


def canonical(text):
    return re.sub(r"\s+", "", re.sub(r"std::__\w+::", "std::", text).replace("const ", ""))


def strip(node):
    while node.get("kind") in ("ImplicitCastExpr", "ParenExpr", "ExprWithCleanups", "MaterializeTemporaryExpr") \
            and len(children(node)) == 1:
        node = children(node)[0]
    return node


def integer(node):
    converted = False
    while node.get("kind") in ("ImplicitCastExpr", "ParenExpr", "CStyleCastExpr", "CXXStaticCastExpr") \
            and len(children(node)) == 1:
        if node.get("kind") != "ParenExpr" and node.get("castKind") not in ("NoOp", "LValueToRValue"):
            converted = True
        node = children(node)[0]
    if node.get("kind") == "IntegerLiteral":
        value = int(node["value"])
        # Do not infer a prefix from pre-conversion syntax: (unsigned char)256 is zero. Zero/one
        # survive the supported scalar conversions; larger converted literals need a real folder.
        return value if not converted or value in (0, 1) else None
    return None


@dataclass(frozen=True)
class Value:
    kind: str
    ctype: str
    owner: str = ""
    minimum: int = 0


def is_value(value):
    return isinstance(value, Value)


class Policy:
    def __init__(self, types, scalars, bound, refuse):
        self.types, self.scalars, self.bound, self.refuse = types, scalars, bound, refuse
        self.names = {canonical(info["cpp"]): name for name, info in types.items()
                      if all(element in scalars or info["kind"] == "pair" and self.pointer_element(element)
                             for element in info["elements"])}
        self.pointer_pairs = any(info["kind"] == "pair" and any(self.pointer_element(e) for e in info["elements"])
                                 for name, info in types.items() if name in self.names.values())
        self.prefix = {}

    def pointer_element(self, text):
        text = canonical(text)
        return text.endswith("*") and text[:-1] in {canonical(t) for t in self.scalars}

    def argument(self, element, node, visit):
        value = visit(node)
        if not self.pointer_element(element):
            if value != "scalar":
                self.refuse("pair scalar field has no initialized scalar value", node)
        elif not ((value == "pointer" and canonical(qual(node)) == canonical(element)) or
                  is_value(value) and value.kind == "identity_pointer" and
                  value.ctype in (canonical(element), "nullptr")):
            self.refuse("pair pointer field has no checked initialized pointer value", node)

    def classify(self, node):
        return self.names.get(canonical(qual(node)))

    def info(self, value, kind, node):
        if not isinstance(value, Value) or value.kind != kind or value.owner not in self.prefix:
            self.refuse(f"standard {kind} has no checked initialized local-object origin", node)
        return self.types[value.ctype]

    def scalar(self, node, visit):
        if visit(node) != "scalar":
            self.refuse("standard-model scalar argument has no initialized scalar origin", node)

    def read(self, value, index, node):
        if value.kind != "pointer" or index is None or not 0 <= index < value.minimum:
            self.refuse("raw vector read is outside its statically checked initialized live prefix", node)
        return "scalar"

    def wrapper(self, node, values):
        if node.get("kind") in ("DeclStmt", "CompoundStmt"):
            return UNHANDLED
        if not any(is_value(v) for v in values):
            return UNHANDLED
        if len(values) == 1 and is_value(values[0]) and values[0].kind == "identity_pointer":
            if node.get("kind") in ("ParenExpr", "ExprWithCleanups", "MaterializeTemporaryExpr"):
                return values[0]
            if node.get("kind") == "ImplicitCastExpr":
                if node.get("castKind") in ("NoOp", "LValueToRValue") and \
                        canonical(qual(node)) == values[0].ctype:
                    return values[0]
                if node.get("castKind") == "NullToPointer" and values[0].ctype == "nullptr" and \
                        self.pointer_element(qual(node)):
                    return Value("identity_pointer", canonical(qual(node)))
            self.refuse("pointer identity cannot pass through this cast or expression", node)
        if len(values) != 1 or node.get("kind") not in ("ParenExpr", "ExprWithCleanups", "ImplicitCastExpr"):
            self.refuse("standard-object or data origin cannot pass through this expression", node)
        if node.get("kind") == "ImplicitCastExpr" and node.get("castKind") not in ("NoOp", "LValueToRValue"):
            self.refuse("standard-object or data origin cannot pass through this cast", node)
        return values[0]

    def handle(self, node, visit, primitive_type):
        kind, parts = node.get("kind"), children(node)
        name = self.classify(node)
        # 2026-10-16 ET: pointer fields carry initialized values only. Never
        # infer an initialized pointee, live prefix or escaping ownership from
        # an address, null value, copy, assignment or field read.
        if self.pointer_pairs and kind == "CXXNullPtrLiteralExpr":
            return Value("identity_pointer", "nullptr")
        if self.pointer_pairs and kind == "UnaryOperator" and node.get("opcode") == "&" and len(parts) == 1:
            target = strip(parts[0])
            declaration = target.get("referencedDecl") or {}
            if target.get("kind") != "DeclRefExpr" or self.bound.get(declaration.get("id")) != "scalar" or \
                    qual(target) not in self.scalars or not self.pointer_element(qual(node)):
                self.refuse("pointer identity address needs an initialized local scalar", node)
            visit(parts[0])
            return Value("identity_pointer", canonical(qual(node)))
        if kind == "BinaryOperator" and node.get("opcode") == "=" and len(parts) == 2:
            target = strip(parts[0])
            if target.get("kind") == "MemberExpr" and target.get("name") in ("first", "second") and \
                    self.pointer_element(qual(target)):
                value = visit(parts[0])
                if not is_value(value) or value.kind != "identity_pointer":
                    self.refuse("pair pointer assignment needs a checked local field", node)
                self.argument(qual(target), parts[1], visit)
                return value
        if kind == "BinaryOperator" and node.get("opcode") in ("==", "!=") and len(parts) == 2:
            values = [visit(part) for part in parts]
            if any(is_value(v) and v.kind == "identity_pointer" for v in values):
                if not all(v == "pointer" or is_value(v) and v.kind == "identity_pointer" for v in values):
                    self.refuse("pointer identity comparison needs two initialized pointer values", node)
                return "scalar"
            if any(is_value(v) for v in values):
                self.refuse("standard origin cannot pass through this binary operation", node)
            # Each operand is visited exactly once: a second visit could count
            # a vector mutation twice and invent an initialized live prefix.
            return primitive_type
        if self.types and kind in ("GotoStmt", "LabelStmt", "SwitchStmt", "CaseStmt", "DefaultStmt"):
            self.refuse("standard-object initialized-prefix flow excludes goto and switch", node)
        if kind == "VarDecl" and (name or "__wrap_iter<" in qual(node)):
            if len(parts) != 1 or not node.get("init"):
                self.refuse("standard local needs one checked initializer", node)
            value = visit(parts[0])
            if name:
                info = self.types[name]
                if not is_value(value) or value.kind != "constructed_" + info["kind"] or value.ctype != name:
                    self.refuse("standard local initializer has no checked constructor", node)
                self.prefix[node["id"]] = value.minimum
                value = Value(info["kind"], name, owner=node["id"])
            elif not is_value(value) or value.kind != "pointer":
                self.refuse("iterator has no checked vector-buffer origin", node)
            self.bound[node["id"]] = value
            return value
        if kind == "CXXConstructExpr" and name:
            info = self.types[name]
            if std_models.identity() != AUDITED_MODEL:
                self.refuse("standard model lacks the audited exact-content initializedness policy", node)
            # The lowerer models only std::allocator defaults. Never skip default scalar expressions.
            for arg in parts:
                if arg.get("kind") == "CXXDefaultArgExpr" and "allocator<" not in qual(arg):
                    self.refuse("unexpanded standard default argument needs an initializedness check", arg)
            args = [arg for arg in parts if arg.get("kind") != "CXXDefaultArgExpr"]
            # 2026-10-15 ET: exact same-type local pair copies preserve the two
            # initialized scalar fields. Unknown pointers/references/objects do
            # not obtain initializedness from the copy operation itself.
            if info["kind"] == "pair" and len(args) == 1:
                source = visit(args[0])
                self.info(source, "pair", node)
                if source.ctype != name:
                    self.refuse("pair copy has no checked same-type initialized source", node)
                return Value("constructed_pair", name)
            if info["kind"] == "pair" and len(args) in (0, 2):
                for element, arg in zip(info["elements"], args):
                    self.argument(element, arg, visit)
                return Value("constructed_pair", name)
            for arg in args:
                self.scalar(arg, visit)
            if info["kind"] == "vector" and len(args) in (0, 1, 2):
                minimum = integer(args[0]) if args else 0
                return Value("constructed_vector", name, minimum=max(minimum or 0, 0))
            self.refuse("standard constructor is outside the audited initializedness protocol", node)
        if kind == "MaterializeTemporaryExpr" and primitive_type == "scalar" and len(parts) == 1:
            self.scalar(parts[0], visit)
            return "scalar"
        if kind == "MaterializeTemporaryExpr" and primitive_type == "pointer" and len(parts) == 1:
            value = visit(parts[0])
            if value == "pointer" or is_value(value) and value.kind == "identity_pointer":
                return value
            self.refuse("temporary pointer argument has no initialized value", node)
        if kind == "MemberExpr" and node.get("name") in ("first", "second") and len(parts) == 1:
            info = self.info(visit(parts[0]), "pair", node)
            element = info["elements"][node["name"] == "second"]
            if self.pointer_element(element):
                return Value("identity_pointer", canonical(element))
            return "scalar"
        if kind == "CXXMemberCallExpr" and parts and parts[0].get("kind") == "MemberExpr":
            member = parts[0]
            bases = children(member)
            if len(bases) == 1 and self.classify(strip(bases[0])):
                value = visit(bases[0])
                info = self.info(value, "vector", member)
                args = parts[1:]
                for arg in args:
                    self.scalar(arg, visit)
                method = member.get("name")
                if method in ("size", "empty") and not args:
                    return "scalar"
                if method == "push_back" and len(args) == 1:
                    self.prefix[value.owner] += 1
                    return "scalar"
                if method == "at" and len(args) == 1:
                    return "scalar"  # the exact body checks index<size; every live element is initialized
                if method in ("data", "begin", "end") and not args:
                    minimum = self.prefix[value.owner] if method != "end" else 0
                    return Value("pointer", info["elements"][0], minimum=minimum)
                self.refuse("standard member is outside the audited initializedness protocol", node)
        if kind == "CXXOperatorCallExpr" and parts:
            callee = strip(parts[0])
            # FunctionToPointerDecay is not a no-op object cast, but only the declaration is inspected.
            while callee.get("kind") == "ImplicitCastExpr" and len(children(callee)) == 1:
                callee = children(callee)[0]
            operator = (callee.get("referencedDecl") or {}).get("name")
            args = parts[1:]
            if operator == "operator=" and len(args) == 2 and self.classify(strip(args[0])):
                target, source = visit(args[0]), visit(args[1])
                self.info(target, "pair", node)
                self.info(source, "pair", node)
                if target.ctype != source.ctype:
                    self.refuse("pair assignment has no checked same-type initialized source", node)
                return target
            if operator == "operator[]" and len(args) == 2 and self.classify(strip(args[0])):
                self.info(visit(args[0]), "vector", node)
                self.scalar(args[1], visit)
                return "scalar"  # the model's index<size obligation bounds the initialized live prefix
            if operator == "operator*" and len(args) == 1 and "__wrap_iter<" in qual(args[0]):
                value = visit(args[0])
                if is_value(value):
                    return self.read(value, 0, node)
        if kind == "CXXForRangeStmt":
            return self.range_for(node, parts, visit, primitive_type)
        if kind in ("IfStmt", "ForStmt", "WhileStmt", "DoStmt", "ConditionalOperator") or \
                kind == "BinaryOperator" and node.get("opcode") in ("&&", "||"):
            # Each alternative/iteration is checked from the conservative entry prefix. Nothing
            # written only on a branch or a possibly zero-trip loop becomes definite afterwards.
            before = dict(self.prefix)
            for part in parts:
                self.prefix.update(before)
                result = visit(part)
                if is_value(result):
                    self.refuse("standard origin cannot escape a conditional expression", node)
            self.prefix.update(before)
            return "scalar"
        if kind == "ReturnStmt":
            for part in parts:
                if is_value(visit(part)):
                    self.refuse("returning standard storage needs a checked ownership boundary", node)
            return "scalar"
        return UNHANDLED

    def range_for(self, node, parts, visit, primitive_type):
        if len(parts) != 7 or any(parts[i].get("kind") != "DeclStmt" for i in (0, 1, 2, 5)):
            self.refuse("range loop is not the checked canonical vector form", node)
        declarations = [children(parts[i]) for i in (0, 1, 2, 5)]
        if any(len(ds) != 1 or ds[0].get("kind") != "VarDecl" for ds in declarations):
            self.refuse("range loop declarations are not canonical", node)
        range_, begin, end, variable = [ds[0] for ds in declarations]
        if len(children(range_)) != 1:
            self.refuse("range loop has no exact source object", range_)
        source = visit(children(range_)[0])
        self.info(source, "vector", node)

        def ref(expr, decl):
            return (strip(expr).get("referencedDecl") or {}).get("id") == decl.get("id")

        def method(decl, name):
            init = children(decl)
            if len(init) != 1 or strip(init[0]).get("kind") != "CXXMemberCallExpr":
                return False
            call = children(strip(init[0]))
            return len(call) == 1 and call[0].get("kind") == "MemberExpr" and call[0].get("name") == name \
                and len(children(call[0])) == 1 and ref(children(call[0])[0], range_)

        def operator(expr, name, operands):
            expr = strip(expr)
            args = children(expr)
            if expr.get("kind") != "CXXOperatorCallExpr" or len(args) != len(operands) + 1:
                return False
            target = strip(args[0])
            return (target.get("referencedDecl") or {}).get("name") == name \
                and all(ref(arg, decl) for arg, decl in zip(args[1:], operands))

        init = children(variable)
        if not method(begin, "begin") or not method(end, "end") or \
                not operator(parts[3], "operator!=", [begin, end]) or \
                not operator(parts[4], "operator++", [begin]) or len(init) != 1 or \
                not operator(init[0], "operator*", [begin]) or qual(variable) not in self.scalars:
            self.refuse("range iterator/element operations are not the checked canonical vector form", node)
        self.bound[variable["id"]] = "scalar"
        before = dict(self.prefix)
        visit(parts[6])
        self.prefix.update(before)
        return "scalar"


def report(types):
    return {"id": POLICY_ID, "models": dict(AUDITED_MODEL), "types": sorted(types),
            "vector_members": ["ctor", "ctor_count", "ctor_count_value", "push_back", "operator_index", "at",
                               "size", "empty", "data", "begin", "end", "dtor", "scalar_range_for"],
            "pair_members": ["ctor_default", "ctor", "copy_ctor", "operator_assign", "first", "second"],
            "initialized": "scalar representations, pair pointer values and vector live elements only; pointer values grant no pointee access or escape; spare capacity excluded",
            "raw_reads": "literal indices within a definite initialized live prefix captured from data/begin",
            "lifetime": "CBMC executes real allocation/free; growth does not add an assumed lifetime fact"}


def valid_report(value, lowering):
    return (isinstance(value, dict) and value.get("id") == POLICY_ID and value.get("models") == AUDITED_MODEL
            and std_models.identity() == AUDITED_MODEL and value.get("types") == list(lowering.std_models))
