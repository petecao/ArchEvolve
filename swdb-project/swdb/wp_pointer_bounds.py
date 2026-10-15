"""Checked WP pointer formation obligations; created 2026-10-15 ET (tickets 24/36).

Frama-C 33 RTE does not check discarded pointer addition. The lowering inventories
source operations before simplification; WP adds assertions at safe statement
anchors. These assertions are obligations, never assumptions. Unsupported
evaluation contexts stop admission rather than guessing where a check belongs.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path


class Refused(ValueError):
    pass


def identity():
    return {"id": "swdb-wp-pointer-bounds-1", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _walk(node):
    yield node
    for child in node.get("inner", []):
        if isinstance(child, dict) and child.get("kind"):
            yield from _walk(child)


def _pointer(node):
    return bool(re.search(r"\*\s*(?:(?:const|volatile|restrict)\s*)*$",
                          str((node.get("type") or {}).get("qualType", ""))))


def _strip_origin(node):
    while node.get("kind") in {"ParenExpr", "ImplicitCastExpr", "ExprWithCleanups"} and node.get("inner"):
        if node.get("kind") == "ImplicitCastExpr" and node.get("castKind") not in {
                "NoOp", "LValueToRValue", "ArrayToPointerDecay", "NullToPointer"}:
            break
        node = node["inner"][0]
    return node


def semantic_origins(library, defines=()):
    """Origins of exact audited independent tile rows, with live content/entry pins."""
    from swdb import bounded_initialization, proof_semantics
    origins = {}
    for entry in proof_semantics.current(library):
        model = proof_semantics.model_for(library, entry, defines)
        policy = bounded_initialization._dx100_policy(library, model, defines)
        if policy is None or proof_semantics.TILE_POINTER not in policy["calls"]:
            continue
        extents = {row["elements"] for row in policy["tile_objects"]}
        if len(extents) != 1 or next(iter(extents)) <= 0:
            continue
        origins[proof_semantics.TILE_POINTER] = {
            "kind": "semantic_rows", "producer": proof_semantics.TILE_POINTER,
            "element_type": "int", "elements": next(iter(extents)), "policy": policy}
    return origins


def check_semantic_origins(lowering, library, defines=()):
    fresh = semantic_origins(library, defines)
    for row in (lowering.pointer_bounds or {}).get("sites", []):
        origin = row.get("origin") or {}
        if origin.get("kind") == "semantic_rows" and origin != fresh.get(origin.get("producer")):
            raise Refused("array-object origin model content, entry or geometry changed after planning")


class _Origins:
    """Conservative source origins; no allocation-validity-to-array inference."""
    def __init__(self, definitions, globals=(), known=None, terminal=None):
        self.definitions, self.known, self.terminal = definitions, known or {}, terminal or {}
        self.declarations = {function: {n.get("id"): n for n in _walk(root)
                                     if n.get("kind") in {"VarDecl", "ParmVarDecl"}}
                             for function, root in definitions.items()}
        self.globals = {n.get("name"): n for n in globals}
        self.unstable = set()
        for function, root in definitions.items():
            for node in _walk(root):
                children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
                kind, opcode = node.get("kind"), node.get("opcode")
                if children and (kind == "CompoundAssignOperator" or kind == "BinaryOperator" and opcode == "="
                                 or kind == "UnaryOperator" and opcode in {"++", "--", "&"}):
                    target = _strip_origin(children[0])
                    if target.get("kind") == "DeclRefExpr" and _pointer(target):
                        self.unstable.add((function, (target.get("referencedDecl") or {}).get("id")))
                if kind == "VarDecl" and "&" in str((node.get("type") or {}).get("qualType", "")):
                    self.unstable.update((function, (n.get("referencedDecl") or {}).get("id")) for n in _walk(node)
                                         if n.get("kind") == "DeclRefExpr" and _pointer(n))
                # A by-reference parameter can change an alias without an explicit
                # assignment in this closure. Unknown calls receive no exemption.
                if kind in {"CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"} and children:
                    refs = [(n.get("referencedDecl") or {}).get("name") for n in _walk(children[0])]
                    if not any(name in self.known for name in refs):
                        for arg in children[1:]:
                            self.unstable.update((function, (n.get("referencedDecl") or {}).get("id")) for n in _walk(arg)
                                                 if n.get("kind") == "DeclRefExpr" and _pointer(n))

    def get(self, node, function, seen=()):
        node = _strip_origin(node)
        kind, children = node.get("kind"), [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
        if kind == "BinaryOperator" and node.get("opcode") in {"+", "-"}:
            pointers = [n for n in children if _pointer(n)]
            if len(pointers) == 1:
                return self.get(pointers[0], function, seen)
        if kind == "CallExpr" and children:
            refs = [(n.get("referencedDecl") or {}).get("name") for n in _walk(children[0])]
            return next((self.known[name] for name in refs if name in self.known), None)
        if kind != "DeclRefExpr":
            return None
        ref = node.get("referencedDecl") or {}
        key, name = ref.get("id"), ref.get("name")
        declaration = self.declarations.get(function, {}).get(key)
        if declaration is None and ref.get("kind") == "VarDecl":
            declaration = self.globals.get(name)
        if declaration is None or key in seen or declaration.get("kind") == "ParmVarDecl":
            return None
        qual = str((declaration.get("type") or {}).get("qualType", ""))
        match = re.fullmatch(r"((?:const )?(?:unsigned |signed )?(?:int|long|long long|short|char|float|double|bool))\s*\[(\d+)\]", qual)
        if match and int(match[2]) > 0 and declaration.get("storageClass") != "extern":
            return {"kind": "one_dimensional_array", "name": name,
                    "element_type": match[1], "elements": int(match[2])}
        if (function, key) in self.unstable or declaration.get("storageClass") or not _pointer(declaration):
            return None
        if function == self.terminal.get("function") and name == self.terminal.get("owner"):
            from swdb import terminal_release
            if self.terminal.get("checker") == terminal_release.identity():
                return {"kind": "certified_terminal_allocation", "name": name, "element_type": "int",
                        "elements": self.terminal["count"], "certificate": self.terminal}
        initializers = [n for n in declaration.get("inner", []) if isinstance(n, dict) and n.get("kind")]
        if len(initializers) != 1:
            return None
        return self.get(initializers[0], function, (*seen, key))


def _origin_base(node):
    children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
    if node.get("kind") == "UnaryOperator" and node.get("opcode") == "&" and children:
        return _origin_base(children[0])
    return next((n for n in children if _pointer(n)), None)


def complete(sites, definitions, observed, *, external_calls=(), known_pointer_calls=(),
             global_nodes=(), known_origins=None, terminal=None):
    """Refuse source operations omitted by printing and untracked subobject origins.

    The printer owns normalizations. This independent closure walk ensures that
    wrapper expressions cannot hide an operation from that inventory. Pointer
    casts and array subobjects need a typed extent policy beyond block bounds.
    """
    rows = [dict(row) for row in sites]
    # Clang dumps for separate functions may reuse process-local AST IDs.
    by_node = {(row["function"], row.pop("_ast_id", None)): row for row in rows}
    origins = _Origins(definitions, global_nodes, known_origins, terminal)
    has_arithmetic = bool(rows)
    external = {row.get("name") if isinstance(row, dict) else row for row in external_calls}
    for function, root in definitions.items():
        for node in _walk(root):
            kind, children = node.get("kind"), node.get("inner", [])
            children = [c for c in children if isinstance(c, dict) and c.get("kind")]
            pointer_children = [c for c in children if _pointer(c)]
            operation = (kind == "BinaryOperator" and node.get("opcode") in {"+", "-"} and pointer_children
                         or kind == "CompoundAssignOperator" and children and _pointer(children[0])
                         or kind == "UnaryOperator" and children and
                         (node.get("opcode") in {"++", "--"} and _pointer(children[0])
                          or node.get("opcode") == "&" and children[0].get("kind") == "ArraySubscriptExpr"))
            reason = ""
            indexed = kind == "ArraySubscriptExpr"
            if operation or indexed:
                base = _origin_base(node)
                origin = origins.get(base, function) if base is not None else None
                row = by_node.get((function, node.get("id"))) if operation else None
                offset_nodes = [c for c in children if not _pointer(c)]
                null_zero = (kind == "BinaryOperator" and node.get("opcode") in {"+", "-"}
                             and len(offset_nodes) == 1 and _strip_origin(offset_nodes[0]).get("kind") == "IntegerLiteral"
                             and _strip_origin(offset_nodes[0]).get("value") == "0")
                if origin is None and null_zero and row is not None:
                    # The checked assertion will require an actual null pointer;
                    # invalid nonnull pointers receive no zero-offset exemption.
                    row["null_only"] = True
                elif origin is None:
                    reason = "pointer arithmetic/indexing needs a certified array-object origin; incoming pointer domains are unsupported"
                elif row is not None:
                    row["origin"] = origin
                elif indexed:
                    rows.append({"function": function, "source_line": ((node.get("loc") or {}).get("line") or
                                                 ((node.get("range") or {}).get("begin") or {}).get("line")),
                                 "admission_only": True, "origin": origin, "reason": ""})
            if operation and (function, node.get("id")) not in observed:
                reason = "pointer operation was not captured at a checked source statement"
            if kind.endswith("CastExpr") and _pointer(node) and node.get("castKind") not in {
                    "NoOp", "LValueToRValue", "ArrayToPointerDecay", "FunctionToPointerDecay", "NullToPointer"}:
                reason = "pointer cast needs a checked typed object-origin policy"
            if kind == "ImplicitCastExpr" and node.get("castKind") == "ArrayToPointerDecay" and children:
                origin = children[0]
                while origin.get("kind") in {"ParenExpr", "ImplicitCastExpr"} and origin.get("inner"):
                    origin = origin["inner"][0]
                qual = str((origin.get("type") or {}).get("qualType", ""))
                if origin.get("kind") in {"ArraySubscriptExpr", "MemberExpr"} or qual.count("[") > 1:
                    reason = "embedded or multidimensional array pointer needs an exact subobject extent policy"
            if has_arithmetic and kind == "UnaryOperator" and node.get("opcode") == "&" and children:
                origin = children[0]
                while origin.get("kind") in {"ParenExpr", "ImplicitCastExpr"} and origin.get("inner"):
                    origin = origin["inner"][0]
                if origin.get("kind") == "MemberExpr":
                    reason = "member-address pointer arithmetic needs an exact subobject extent policy"
            if has_arithmetic and kind == "CallExpr" and _pointer(node) and children:
                refs = [(n.get("referencedDecl") or {}).get("name") for n in _walk(children[0])]
                if any(name in external and name not in known_pointer_calls for name in refs):
                    reason = "opaque summary pointer results need a checked typed object-origin policy"
            if reason:
                rows.append({"function": function, "source_line": ((node.get("loc") or {}).get("line") or
                                                 ((node.get("range") or {}).get("begin") or {}).get("line")),
                             "anchor": "", "base": "", "expression": "", "offset": None,
                             "reason": reason, "normalized_expression": None})
    return rows


def site(node, *, expression, base, statement, anchor, function, line, reason="", offset=None):
    """One printer-owned site. AST IDs are used locally, never serialized."""
    if statement is None or statement.get("kind") not in {
            "DeclStmt", "ReturnStmt", "CStyleCastExpr", "CXXStaticCastExpr", "ParenExpr", "CallExpr",
            "CXXMemberCallExpr", "ExprWithCleanups", "BinaryOperator", "ImplicitCastExpr"}:
        reason = reason or "pointer formation in a loop header, condition or generated context needs a precise check placement"
    if statement is not None:
        nodes = list(_walk(statement))
        if any(n.get("kind") in {"ConditionalOperator", "BinaryConditionalOperator"} or
               n.get("kind") in {"BinaryOperator", "CompoundAssignOperator"} and n.get("opcode") in
               {"=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "|=", "^=", ",", "&&", "||"} or
               n.get("kind") == "UnaryOperator" and n.get("opcode") in {"++", "--"} for n in nodes):
            reason = reason or "pointer formation with mutation or conditional evaluation needs a precise check placement"
        if any("volatile" in str((n.get("type") or {}).get("qualType", "")) for n in nodes):
            reason = reason or "pointer formation with volatile operands needs single-evaluation normalization"
        calls = {"CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"}
        if sum(n.get("kind") in calls for n in nodes) > 1 or any(n.get("kind") in calls for n in _walk(node)):
            reason = reason or "pointer formation operands or sibling arguments have opaque effects"
        declared = {n.get("id") for n in nodes if n.get("kind") == "VarDecl"}
        if any((n.get("referencedDecl") or {}).get("id") in declared for n in _walk(node)):
            reason = reason or "pointer formation depends on a binding inside its containing statement"
    return {"function": function, "anchor": anchor, "source_line": line, "base": base,
            "expression": expression, "offset": offset, "reason": reason,
            "normalized_expression": normalize(expression, base, offset) if not reason else None, "_ast_id": node.get("id")}


def normalize(expression, base, offset):
    if offset is None:
        return expression
    return f"(({offset}) == 0 ? ({base}) : ({expression}))"


def inventory(sites, *, source_sha256, text):
    report = {"check": identity(), "source_sha256": source_sha256,
              "lowering_sha256": hashlib.sha256(text.encode()).hexdigest(), "sites": list(sites),
              "domain_boundary": "Only certified whole one-dimensional arrays, exact audited semantic rows and terminal typed allocations; "
                                 "opaque incoming pointer arithmetic/indexing is unsupported; exact C++ null-plus-zero is checked."}
    report["certificate_sha256"] = _hash(report)
    return report


def check(lowering):
    report = dict(getattr(lowering, "pointer_bounds", {}) or {})
    digest = report.pop("certificate_sha256", None)
    if (not report or digest != _hash(report) or report.get("check") != identity()
            or report.get("source_sha256") != lowering.source_sha256
            or report.get("lowering_sha256") != hashlib.sha256(lowering.text.encode()).hexdigest()):
        raise Refused("pointer formation inventory is absent, stale or differs from its generated lowering")
    for row in report["sites"]:
        if row["reason"]:
            raise Refused(f"{row['function']}:{row['source_line']}: {row['reason']}")
        if row.get("admission_only"):
            continue
        normalized = normalize(row["expression"], row["base"], row.get("offset"))
        if normalized != row.get("normalized_expression") or normalized not in lowering.text:
            raise Refused("pointer formation normalization differs from its generated lowering")
    report["certificate_sha256"] = digest
    return report


def _in_object_or_one_past(pointer, base):
    # Keep the original object's provenance even when the result is one-past.
    # A predecessor in a different allocation cannot justify an invalid pointer.
    return (f"({pointer} != \\null && \\base_addr({pointer}) == \\base_addr({base}) && "
            f"(\\valid_read({pointer}) || (\\base_addr(({pointer}) - 1) == \\base_addr({base}) && "
            f"\\valid_read(({pointer}) - 1))))")


def prepare(lowering, text):
    """Insert independently named checked assertions into a generated WP view."""
    report = check(lowering)
    additions = {}
    for i, row in enumerate(report["sites"], 1):
        if row.get("admission_only"):
            continue
        base, result = f"({row['base']})", f"({row['expression']})"
        predicate = f"{_in_object_or_one_past(base, base)} && {_in_object_or_one_past(result, base)}"
        if row.get("offset") is not None:
            predicate = f"(({base} == \\null && ({row['offset']}) == 0) || ({predicate}))"
        if row.get("null_only"):
            predicate = f"{base} == \\null && ({row['offset']}) == 0"
        assertion = f"/*@ assert swdb_pointer_formation_{i}: {predicate}; */"
        additions.setdefault(row["anchor"], []).append(assertion)
    for anchor, assertions in additions.items():
        marker = f"/* swdb-anchor {anchor} */"
        if text.count(marker) != 1:
            raise Refused(f"pointer check anchor {anchor} is absent or duplicated")
        text = text.replace(marker, marker + "\n" + "\n".join(assertions))
    return text, report


def check_input(lowering, base, report, text):
    """Regenerate the guard view and retain every checked obligation at launch."""
    generated, fresh = prepare(lowering, base)
    if fresh != report:
        raise Refused("pointer formation admission changed after planning")
    for assertion in re.findall(r"/\*@ assert swdb_pointer_formation_.*?\*/", generated, re.S):
        if text.count(assertion) != 1:
            raise Refused("a checked pointer formation obligation is missing or duplicated")


def model_view(text, scratch):
    """Check actual generated C bodies too, without assigning them C++ null rules.

    Clang inventories every generated function definition. The view adds only
    assertions; it never normalizes away a C operation. In particular an actual
    C null+zero operation must fail, while a guarded C++ emulation can skip it.
    """
    from swdb import c_lowering
    if re.search(r"^\s*#\s*(?:if|elif|ifdef|ifndef).*\b__FRAMAC__\b", text, re.M):
        raise Refused("generated C model has a Frama-C-specific preprocessing branch")
    source = Path(scratch) / "pointer_model_source.c"
    source.write_text(text)
    tool = c_lowering.locate()
    if tool.missing:
        raise Refused(tool.missing)
    command = [*tool.command, "-x", "c", "-std=gnu11", "-fsyntax-only", "-Xclang", "-ast-dump=json", str(source)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refused(f"cannot inventory generated C model: {exc}") from None
    if done.returncode:
        raise Refused("cannot inventory generated C model pointer operations: " + done.stderr[-1000:])
    try:
        ast = json.loads(done.stdout)
    except ValueError:
        raise Refused("clang generated C model inventory is malformed") from None
    names = set(re.findall(r"^(?:static\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{", text, re.M))
    functions = [node for node in _walk(ast) if node.get("kind") == "FunctionDecl"
                 and any(c.get("kind") == "CompoundStmt" for c in node.get("inner", []))
                 and (node.get("loc") or {}).get("file", str(source)) == str(source)
                 and not (node.get("loc") or {}).get("includedFrom")]
    if {n["name"] for n in functions} != names:
        raise Refused("clang omitted a generated C model function definition")
    raw, sites = text.encode(), []
    model_definitions = {n["name"]: n for n in functions}
    model_origins = _Origins(model_definitions, [n for n in ast.get("inner", []) if n.get("kind") == "VarDecl"])

    def span(node):
        begin, end = (node.get("range") or {}).get("begin") or {}, (node.get("range") or {}).get("end") or {}
        if "offset" not in begin or "offset" not in end:
            raise Refused("generated C pointer operation has macro or unknown source positions")
        return begin["offset"], end["offset"] + end.get("tokLen", 0)

    def expression(node):
        start, stop = span(node)
        return raw[start:stop].decode()

    def pointer(node):
        return bool(re.search(r"\*\s*(?:(?:const|volatile|restrict)\s*)*$",
                              str((node.get("type") or {}).get("qualType", ""))))

    def visit(node, function, statement=None, path=(), header=False):
        kind = node.get("kind")
        children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
        if kind.endswith("CastExpr") and pointer(node) and node.get("castKind") not in {
                "NoOp", "LValueToRValue", "ArrayToPointerDecay", "FunctionToPointerDecay", "NullToPointer"}:
            raise Refused("generated C model pointer cast needs an exact typed origin policy")
        if kind == "ImplicitCastExpr" and node.get("castKind") == "ArrayToPointerDecay" and children:
            origin = children[0]
            if origin.get("kind") in {"ArraySubscriptExpr", "MemberExpr"} or \
                    str((origin.get("type") or {}).get("qualType", "")).count("[") > 1:
                raise Refused("generated C model embedded array pointer needs an exact subobject extent policy")
        if kind == "CompoundStmt":
            for child in children:
                visit(child, function, child, path)
            return
        if kind in {"ForStmt", "WhileStmt", "DoStmt"}:
            # Array indexing in the body gets RTE checks. Explicit pointer loop
            # header operations need induction/placement support before admission.
            for child in children:
                visit(child, function, statement, path, child.get("kind") != "CompoundStmt")
            return
        if kind == "ConditionalOperator" and len(children) == 3:
            if any(n.get("kind") in {"CallExpr", "CompoundAssignOperator"} or
                   n.get("kind") == "BinaryOperator" and n.get("opcode") in {"=", ","} or
                   n.get("kind") == "UnaryOperator" and n.get("opcode") in {"++", "--"} or
                   "volatile" in str((n.get("type") or {}).get("qualType", ""))
                   for n in _walk(children[0])):
                raise Refused("generated C model branch condition cannot be duplicated in a pointer check")
            visit(children[0], function, statement, path, header)
            condition = expression(children[0])
            visit(children[1], function, statement, (*path, f"({condition})"), header)
            visit(children[2], function, statement, (*path, f"!({condition})"), header)
            return
        if kind in {"IfStmt", "SwitchStmt"}:
            for child in children:
                visit(child, function, child, path, child is children[0])
            return
        operands = [child for child in children if pointer(child)]
        arithmetic = kind == "BinaryOperator" and node.get("opcode") in {"+", "-"} and operands
        mutation = kind == "CompoundAssignOperator" and children and pointer(children[0]) or \
            kind == "UnaryOperator" and node.get("opcode") in {"++", "--"} and children and pointer(children[0])
        address = kind == "UnaryOperator" and node.get("opcode") == "&" and children and \
            children[0].get("kind") == "ArraySubscriptExpr"
        if arithmetic or address or kind == "ArraySubscriptExpr":
            base = _origin_base(node)
            if base is None or model_origins.get(base, function) is None:
                raise Refused("generated C model pointer arithmetic/indexing needs a certified array-object origin; opaque parameter domains are unsupported")
        if mutation:
            raise Refused("generated C model pointer mutation needs a checked transition policy")
        if arithmetic or address:
            if header or statement is None:
                raise Refused("generated C model pointer operation has no safe statement check placement")
            statement_nodes = list(_walk(statement))
            declared = {n.get("id") for n in statement_nodes if n.get("kind") == "VarDecl"}
            if any((n.get("referencedDecl") or {}).get("id") in declared for n in statement_nodes):
                raise Refused("generated C pointer check depends on a binding inside its statement")
            if any(n.get("kind") in {"CallExpr", "CompoundAssignOperator"} or
                   n.get("kind") == "BinaryOperator" and n.get("opcode") in {"=", ",", "&&", "||"} or
                   n.get("kind") == "UnaryOperator" and n.get("opcode") in {"++", "--"}
                   for n in statement_nodes):
                raise Refused("generated C model pointer operands have side effects")
            if any("volatile" in str((n.get("type") or {}).get("qualType", "")) for n in _walk(node)):
                raise Refused("generated C model pointer operand is volatile")
            if arithmetic and len(operands) == 2:
                left, right = (f"({expression(c)})" for c in children)
                # ACSL's mathematical pointer difference is in elements of this
                # exact C type. Byte-offset conversion in WP's typed model uses
                # a separate layout abstraction and needlessly loses this link.
                distance = f"({left} - {right})"
                predicate = (f"{_in_object_or_one_past(left, left)} && {_in_object_or_one_past(right, left)} && "
                             f"PTRDIFF_MIN <= {distance} <= PTRDIFF_MAX")
            else:
                base_node = operands[0] if arithmetic else next(
                    (c for c in children[0].get("inner", []) if pointer(c)), None)
                if base_node is None:
                    raise Refused("generated C model indexed address has no typed pointer origin")
                base, result = f"({expression(base_node)})", f"({expression(node)})"
                predicate = f"{_in_object_or_one_past(base, base)} && {_in_object_or_one_past(result, base)}"
            if path:
                predicate = f"({' && '.join(path)}) ==> ({predicate})"
            at, _stop = span(statement)
            sites.append({"function": function, "offset": at, "expression": expression(node), "predicate": predicate})
        for child in children:
            visit(child, function, statement, path, header)

    for function in functions:
        body = next(n for n in function["inner"] if n.get("kind") == "CompoundStmt")
        visit(body, function["name"])
    edits = {}
    for i, row in enumerate(sites, 1):
        assertion = f"/*@ assert swdb_model_pointer_formation_{i}: {row['predicate']}; */\n"
        edits.setdefault(row["offset"], []).append(assertion)
    for at in sorted(edits, reverse=True):
        raw = raw[:at] + "".join(edits[at]).encode() + raw[at:]
    report = {"check": identity(), "kind": "generated_c_model", "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "functions": sorted(names), "sites": sites}
    report["certificate_sha256"] = _hash(report)
    return raw.decode(), report
