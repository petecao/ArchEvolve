"""Conservative CPU-memory effect inventory for proof-semantics admission; created 2026-10-15 ET.

This is an admission aid, not ticket 28's cache-line hazard model. Source writes and loads, model effects,
opaque summaries, call sites, and loop-containing functions remain explicit. Matching generated tile probes
already cover tile accesses. Top-level statement ordinals preserve sequencing without guessing operand order.
"""

import json


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def _walk(node):
    yield node
    for child in _children(node):
        yield from _walk(child)


def _strip(node):
    while node.get("kind") in ("ParenExpr", "ImplicitCastExpr") and len(_children(node)) == 1:
        node = _children(node)[0]
    return node


def _qual(node):
    typ = node.get("type") or {}
    return typ.get("desugaredQualType", typ.get("qualType", ""))


def _site(node, function, statement, kind):
    begin = (node.get("range") or {}).get("begin") or node.get("loc") or {}
    end = (node.get("range") or {}).get("end") or {}
    offset = begin.get("offset")
    stop = end.get("offset")
    return {"function": function, "kind": kind, "line": begin.get("_line", begin.get("line")),
            "begin": offset, "end": stop + end.get("tokLen", 0) if stop is not None else None,
            "statement": statement}


def collect(nodes, probes, models, summaries, scalar_types):
    """Inventory every lowered function, including callees. No caller-provided write/read allowlist is used."""
    result = {"reads": [], "writes": [], "calls": [], "loop_functions": []}
    summary_names = {row["name"] for row in summaries}
    seen_summaries = set()
    tile = {(p["function"], p["access"], p["begin"], p["end"]) for p in probes}

    for function, node in nodes.items():
        all_nodes = list(_walk(node))
        locals_ = {n["id"] for n in all_nodes if n.get("kind") in ("VarDecl", "ParmVarDecl")}
        address_taken = set()
        for expression in all_nodes:
            if expression.get("kind") == "UnaryOperator" and expression.get("opcode") == "&":
                for target in _children(expression):
                    target = _strip(target)
                    if target.get("kind") == "DeclRefExpr":
                        address_taken.add((target.get("referencedDecl") or {}).get("id"))
        # A reference can expose the address of an otherwise ordinary scalar local without an '&'
        # expression at its binding. Retain the referred storage even when later writes use its name.
        for declaration in all_nodes:
            if declaration.get("kind") == "VarDecl" and "&" in _qual(declaration):
                for target in _children(declaration):
                    target = _strip(target)
                    if target.get("kind") == "DeclRefExpr":
                        address_taken.add((target.get("referencedDecl") or {}).get("id"))
        statics = {n["id"] for n in all_nodes if n.get("kind") == "VarDecl" and
                   (n.get("storageClass") or n.get("tls"))}

        def location(target):
            target = _strip(target)
            kind = target.get("kind")
            if kind == "DeclRefExpr":
                declaration = target.get("referencedDecl") or {}
                if declaration.get("kind") not in ("VarDecl", "ParmVarDecl"):
                    return None
                if "&" in _qual(declaration):
                    return "reference"
                if declaration.get("id") not in locals_ or declaration.get("id") in statics:
                    return "global"
                if declaration.get("id") in address_taken:
                    return "address_taken_local"
                plain = _qual(declaration).replace("const ", "").replace("volatile ", "").strip()
                return None if plain in scalar_types or "*" in plain else "local_aggregate"
            if kind == "ArraySubscriptExpr":
                return "array"
            if kind == "MemberExpr":
                return "member"
            if kind == "UnaryOperator" and target.get("opcode") == "*":
                return "dereference"
            return "opaque_lvalue" if target.get("valueCategory") == "lvalue" else None

        def effect(target, access, statement):
            target = _strip(target)
            kind = location(target)
            if kind is None:
                return
            row = _site(target, function, statement, kind)
            if (function, access, row["begin"], row["end"]) not in tile:
                result["reads" if access == "read" else "writes"].append(row)

        def visit(current, statement):
            kind, children = current.get("kind"), _children(current)
            if kind in ("ForStmt", "WhileStmt", "DoStmt", "CXXForRangeStmt"):
                result["loop_functions"].append(function)
            if (kind == "BinaryOperator" and current.get("opcode") == "=") or kind == "CompoundAssignOperator":
                if children:
                    effect(children[0], "write", statement)
                    if kind == "CompoundAssignOperator":
                        effect(children[0], "read", statement)
            elif kind == "UnaryOperator" and current.get("opcode") in ("++", "--") and children:
                effect(children[0], "write", statement)
                effect(children[0], "read", statement)
            elif kind == "ImplicitCastExpr" and current.get("castKind") == "LValueToRValue" and children:
                effect(children[0], "read", statement)
            elif kind == "AtomicExpr":
                row = _site(current, function, statement, "atomic")
                result["reads"].append(row)
                result["writes"].append(row)  # includes unknown atomic effects; conservatively rejects loads too
            elif kind in ("CXXCtorInitializer", "CXXConstructExpr", "CXXTemporaryObjectExpr"):
                result["writes"].append(_site(current, function, statement, "construction"))
            elif kind == "VarDecl" and (current.get("storageClass") or current.get("tls")):
                result["writes"].append(_site(current, function, statement, "static_local"))
            elif kind == "VarDecl" and current.get("id") in address_taken and children:
                result["writes"].append(_site(current, function, statement, "address_taken_local"))
            if kind in ("CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr") and children:
                callee = _strip(children[0])
                name = (callee.get("referencedDecl") or {}).get("name") or callee.get("name")
                row = {**_site(current, function, statement, "call"), "callee": name}
                result["calls"].append(row)
                if name in summary_names:
                    result["writes"].append({**row, "kind": "summary_call"})
                    result["reads"].append({**row, "kind": "summary_call"})
                    seen_summaries.add(name)
                # A by-reference standard model may read an lvalue without a source LValueToRValue cast.
                for argument in children[1:]:
                    if argument.get("castKind") not in ("ArrayToPointerDecay", "FunctionToPointerDecay"):
                        effect(argument, "read", statement)
            for child in children:
                visit(child, statement)

        for initializer in (c for c in _children(node) if c.get("kind") == "CXXCtorInitializer"):
            visit(initializer, None)
        body = next((c for c in _children(node) if c.get("kind") == "CompoundStmt"), {})
        for ordinal, statement in enumerate(_children(body)):
            visit(statement, ordinal)

    for name in sorted(summary_names - seen_summaries):
        row = {"function": None, "kind": "summary_call", "line": None, "begin": None, "end": None,
               "statement": None, "callee": name}
        result["calls"].append(row)
        result["reads"].append(row)
        result["writes"].append(row)
    for name, text in models.items():
        if name == "SWDB_MODEL_FAIL" or name.endswith("_valid"):
            continue
        if name.startswith(("std_min_", "std_max_")) or name.startswith("omp_") and "assigns \\nothing;" in text:
            continue  # Known pure scalar models; argument memory reads remain in the source inventory.
        row = {"function": None, "kind": "model_call", "line": None, "begin": None, "end": None,
               "statement": None, "callee": name}
        result["reads"].append(row)
        if "assigns \\nothing;" not in text or name.startswith("swdb_alloc_") or "frees " in text or "allocates " in text:
            result["writes"].append(row)
    for kind in ("reads", "writes", "calls"):
        unique = {json.dumps(row, sort_keys=True): row for row in result[kind]}
        result[kind] = [unique[key] for key in sorted(unique)]
    result["loop_functions"] = sorted(set(result["loop_functions"]))
    return result
