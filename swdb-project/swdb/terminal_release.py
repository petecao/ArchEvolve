"""Checked terminal delete[] abstraction for WP 33; created 2026-10-15 ET.

This is a deliberately small ownership checker, not a general lifetime model. A single local int array
may be released immediately before a scalar return when it never escapes and has no pointer aliases.
The ordinary lowering keeps delete[]; only the checked WP view omits that unobservable final release.
Every unknown AST construct, address-taking, call, extra pointer and nonterminal release is refused.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


class Refused(ValueError):
    """The unit or its annotations are outside the checked terminal-release fragment."""


def identity():
    return {"id": "terminal-release-check-2", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def _strip(node):
    while node.get("kind") in ("ImplicitCastExpr", "ParenExpr") and len(_children(node)) == 1:
        node = _children(node)[0]
    return node


def _type(node):
    return (node.get("type") or {}).get("desugaredQualType", (node.get("type") or {}).get("qualType", ""))


def _scalar(node):
    # Version 1 intentionally accepts only int, including const int scalar locals. No volatile/atomic objects.
    return _type(node) in ("int", "const int")


def _reference(node, ident):
    node = _strip(node)
    return node.get("kind") == "DeclRefExpr" and (node.get("referencedDecl") or {}).get("id") == ident


def _full_initialization(statement, owner, count, params):
    """Establish initializedness syntactically instead of relying on default RTE coverage.

    The first operation is exactly `for (int i=0; i<count; ++i) owner[i]=pure_scalar_expression`,
    or its overrun negative with `i<=count`. Both cover every legitimate element;
    the latter's extra write remains in C and must fail an ordinary RTE obligation.
    Count cannot change in this loop; neither calls, pointer reads nor assignments occur in its RHS.
    WP still must prove every RTE obligation, including the positivity assertion before allocation.
    """
    parts = _children(statement)
    if statement.get("kind") != "ForStmt" or len(parts) != 4:
        raise Refused("a complete initialization loop must immediately follow allocation")
    init, condition, step, body = parts
    decls = _children(init)
    if init.get("kind") != "DeclStmt" or len(decls) != 1 or decls[0].get("kind") != "VarDecl" or not _scalar(decls[0]):
        raise Refused("initialization uses a fresh scalar induction variable")
    induction = decls[0]
    values = _children(induction)
    if len(values) != 1 or _strip(values[0]).get("kind") != "IntegerLiteral" or _strip(values[0]).get("value") != "0":
        raise Refused("initialization starts at zero")
    conds = _children(condition)
    if condition.get("kind") != "BinaryOperator" or condition.get("opcode") not in {"<","<="} or len(conds) != 2 or not _reference(conds[0], induction["id"]):
        raise Refused("initialization stops at the allocation count")
    bound = _strip(conds[1])
    if count.get("kind") == "DeclRefExpr":
        same_bound = _reference(bound, (count.get("referencedDecl") or {}).get("id"))
    else:
        same_bound = bound.get("kind") == "IntegerLiteral" and bound.get("value") == count.get("value")
    if not same_bound:
        raise Refused("initialization and allocation counts differ")
    if step.get("kind") != "UnaryOperator" or step.get("opcode") != "++" or len(_children(step)) != 1 or not _reference(_children(step)[0], induction["id"]):
        raise Refused("initialization increments the induction variable once")
    operations = _children(body) if body.get("kind") == "CompoundStmt" else [body]
    if len(operations) != 1 or operations[0].get("kind") != "BinaryOperator" or operations[0].get("opcode") != "=":
        raise Refused("initialization has exactly one element assignment")
    assignments = _children(operations[0])
    lhs = _strip(assignments[0]) if len(assignments) == 2 else {}
    indexes = _children(lhs)
    if lhs.get("kind") != "ArraySubscriptExpr" or len(indexes) != 2 or not _reference(indexes[0], owner["id"]) or not _reference(indexes[1], induction["id"]):
        raise Refused("initialization writes precisely owner[i]")
    allowed_ids = {p["id"] for p in params} | {induction["id"]}
    pending = [assignments[1]]
    while pending:
        value = pending.pop()
        kind = value.get("kind")
        if kind == "DeclRefExpr":
            if not _scalar(value) or (value.get("referencedDecl") or {}).get("id") not in allowed_ids:
                raise Refused("initialization reads only initialized scalar parameters and its induction variable")
        elif kind == "BinaryOperator":
            if value.get("opcode") not in ("+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=", "&&", "||", "&", "|", "^", "<<", ">>"):
                raise Refused("initialization RHS must be pure")
        elif kind == "UnaryOperator":
            if value.get("opcode") not in ("+", "-", "!", "~"):
                raise Refused("initialization RHS must not mutate state")
        elif kind not in ("IntegerLiteral", "ImplicitCastExpr", "ParenExpr", "CStyleCastExpr") or not _scalar(value):
            raise Refused("initialization RHS contains an unmodeled or pointer expression")
        pending.extend(_children(value))
    return condition['opcode']


def certify(node, *, source, source_sha256, models, anchors, text):
    """A generator-owned certificate or None. Never accepts a certificate read from a candidate artifact."""
    try:
        return _certify(node, source=source, source_sha256=source_sha256, models=models, anchors=anchors, text=text)
    except Refused:
        return None


def _certify(node, *, source, source_sha256, models, anchors, text):
    name = node.get("name")
    body = next((c for c in _children(node) if c.get("kind") == "CompoundStmt"), {})
    statements = _children(body)
    if _type(node).split("(", 1)[0].strip() != "int" or len(statements) < 3:
        raise Refused("an int-returning function with a terminal release is required")
    params = [c for c in _children(node) if c.get("kind") == "ParmVarDecl"]
    if not all(_scalar(p) for p in params):
        raise Refused("only scalar int parameters are accepted")
    if re.search(r"\boperator\s+(?:new|delete)\b", source):
        raise Refused("replacement allocation/deallocation functions are outside the model")
    first, release, result = statements[0], statements[-2], statements[-1]
    variables = _children(first)
    if first.get("kind") != "DeclStmt" or len(variables) != 1 or variables[0].get("kind") != "VarDecl":
        raise Refused("the first statement must initialize the sole owner")
    owner = variables[0]
    initializers = _children(owner)
    if _type(owner) != "int *" or owner.get("storageClass") or len(initializers) != 1:
        raise Refused("the owner must be an automatic int pointer")
    allocation = _strip(initializers[0])
    if allocation.get("kind") != "CXXNewExpr" or not allocation.get("isArray") or allocation.get("isPlacement"):
        raise Refused("only ordinary new int[n] is accepted")
    if len(_children(allocation)) != 1:
        raise Refused("only a size expression and no initializer or placement arguments are accepted")
    count = _strip(_children(allocation)[0])
    if count.get("kind") == "DeclRefExpr" and (count.get("referencedDecl") or {}).get("id") in {
            p.get("id") for p in params} and _scalar(count):
        count_text = (count.get("referencedDecl") or {})["name"]
    elif count.get("kind") == "IntegerLiteral" and _scalar(count) and int(count.get("value", "0")) > 0:
        count_text = count["value"]
    else:
        raise Refused("the allocation count must be an int parameter or positive integer literal")
    if release.get("kind") != "CXXDeleteExpr" or not release.get("isArray") or result.get("kind") != "ReturnStmt":
        raise Refused("exactly one top-level delete[] followed by return is required")
    operands = _children(release)
    ref = _strip(operands[0]) if len(operands) == 1 else {}
    if ref.get("kind") != "DeclRefExpr" or (ref.get("referencedDecl") or {}).get("id") != owner.get("id"):
        raise Refused("delete[] must receive the unchanged original allocation base")
    model = "swdb_alloc_delete_array_int"
    if set(models) != {"swdb_alloc_new_array_int", model} or len([a for a in anchors if a["kind"] == "contract"]) != 1:
        raise Refused("no other calls, models, or lowered functions may be present")
    fill_comparison = _full_initialization(statements[1], owner, count, params)
    local_ids = {p.get("id") for p in params}

    def visit(current):
        kind, children = current.get("kind"), _children(current)
        if kind == "DeclRefExpr":
            decl = current.get("referencedDecl") or {}
            if decl.get("id") not in local_ids or not _scalar(current):
                raise Refused("pointer alias, global access, or owner escape")
        elif kind == "ArraySubscriptExpr":
            base = _strip(children[0]) if len(children) == 2 else {}
            if base.get("kind") != "DeclRefExpr" or (base.get("referencedDecl") or {}).get("id") != owner.get("id"):
                raise Refused("only direct indexing of the owner is accepted")
            visit(children[1])
            return
        elif kind == "VarDecl":
            if not _scalar(current) or current.get("storageClass") or current.get("tls"):
                raise Refused("all other locals must be automatic scalar ints")
            if len(children) != 1:
                raise Refused("all scalar locals must have an initializer")
            for child in children:
                visit(child)
            local_ids.add(current.get("id"))
            return
        elif kind == "UnaryOperator":
            if current.get("opcode") not in ("+", "-", "!", "~", "++", "--"):
                raise Refused("address-taking and pointer dereferences are not accepted")
        elif kind in ("BinaryOperator", "CompoundAssignOperator"):
            if current.get("opcode") not in ("=", "+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=",
                                              "&&", "||", "&", "|", "^", "<<", ">>", "+=", "-=", "*=", "/=", "%="):
                raise Refused("unknown scalar operation")
        elif kind == "ImplicitCastExpr":
            if not _scalar(current) or current.get("castKind") not in ("LValueToRValue", "IntegralCast", "NoOp"):
                raise Refused("only scalar implicit conversions are accepted")
        elif kind == "CStyleCastExpr":
            if not _scalar(current):
                raise Refused("only scalar casts are accepted")
        elif kind not in ("IntegerLiteral", "ParenExpr", "CompoundStmt", "DeclStmt", "ForStmt", "WhileStmt", "DoStmt",
                           "IfStmt", "NullStmt", "BreakStmt", "ContinueStmt"):
            raise Refused(f"unmodeled ownership construct: {kind}")
        for child in children:
            visit(child)

    visit(_strip(_children(allocation)[0]))
    for statement in statements[1:-2]:
        visit(statement)
    values = _children(result)
    if len(values) != 1:
        raise Refused("a scalar return value is required")
    pending = list(values)
    while pending:
        value = pending.pop()
        if value.get("kind") == "DeclRefExpr" and (value.get("referencedDecl") or {}).get("id") == owner.get("id"):
            raise Refused("the return must not observe the released owner, including through indexing")
        pending.extend(_children(value))
    visit(values[0])
    call = f"  {model}({owner['name']});"
    lines = text.splitlines()
    allocation_sites = [i for i, line in enumerate(lines) if line ==
                        f"  int *{owner['name']} = swdb_alloc_new_array_int((size_t)({count_text}));"]
    if len(allocation_sites) != 1:
        raise Refused("the allocation must have exactly one canonical C call")
    sites = [i for i, line in enumerate(lines) if line == call]
    if len(sites) != 1:
        raise Refused("the release must have exactly one canonical C call")
    line = sites[0]
    before = next((a for a in anchors if a["kind"] == "before" and a["line"] == line), None)
    if before is None:
        raise Refused("the release has no canonical before anchor")
    return {"function": name, "owner": owner["name"], "model": model, "release_anchor": before["id"],
            "release_line": line + 1, "allocation_line": allocation_sites[0] + 1, "count": count_text,
            "source_sha256": source_sha256, "checker": identity(),
            "initialization": "canonical complete fill before every array read",
            "initialization_loop_comparison": fill_comparison,
            "scope": "one nonescaping initialized new int[] owner; terminal delete[]; scalar int parameters, locals, and return"}


@dataclass(frozen=True)
class View:
    text: str
    models: tuple
    certificate: dict
    pins: dict
    assumption: dict


def wp_view(lowering, formal_texts, hints=()):
    """The checked WP view; annotations may not observe allocation state or introduce ghost behavior."""
    certificate = lowering.terminal_release
    if not certificate or certificate.get("checker") != identity():
        raise Refused("no current ownership certificate")
    # Scalar function contracts only. In-loop hints may mention buf elements, but never allocation status,
    # pointer equality, ghost variables, assumptions, or user-defined logic/axioms.
    for text in formal_texts:
        if re.search(r"[^\w\s\\+\-*/%<>=!&|?:;().,]", text) or re.search(r"\\(?!result\b|nothing\b)\w+", text):
            raise Refused("terminal release requires scalar-only formal halves")
        names = set(re.findall(r"\b[A-Za-z_]\w*\b", text))
        allowed = {p[0] for p in lowering.parameters} | {"requires", "ensures", "assigns", "result", "nothing"}
        if names - allowed:
            raise Refused("terminal release formal halves may name only scalar parameters and result")
    for hint in hints:
        if hint.get("kind") not in ("loop_invariant", "loop_assigns", "loop_variant") or not re.fullmatch(
                re.escape(lowering.function) + r"\.loop\d+\.head", hint.get("anchor", "")):
            raise Refused("terminal release accepts only pre-release loop annotations")
        if re.search(r"\\(?!forall\b|exists\b|old\b|at\b|initialized\b)\w+|\b(?:axiom|assume|admit|ghost|allocates|frees)\b", hint.get("text", "")):
            raise Refused("hint observes allocation state or introduces unsupported ghost behavior")
    lines = lowering.text.splitlines(keepends=True)
    index = certificate["release_line"] - 1
    expected = f"  {certificate['model']}({certificate['owner']});\n"
    if index < 0 or index >= len(lines) or lines[index] != expected:
        raise Refused("the certified release call differs from the lowering")
    lines[index] = "  /* checked terminal delete[]: owner does not escape; no later heap observation */\n"
    alloc_index = certificate["allocation_line"] - 1
    expected_alloc = (f"  int *{certificate['owner']} = "
                      f"swdb_alloc_new_array_int((size_t)({certificate['count']}));\n")
    if alloc_index < 0 or alloc_index >= len(lines) or lines[alloc_index] != expected_alloc:
        raise Refused("the certified allocation call differs from the lowering")
    # A negative C++ array bound throws before allocation. Prove nonnegativity before the size_t conversion;
    # never use allocation success to hide invalid array lengths. One line keeps the original anchors stable.
    # WP33's modular call-result rule binds the value without initializing the receiving lvalue.
    # The existing allocator contract requires a valid nonempty array; adding zero is defined C pointer
    # arithmetic and preserves that exact address. Kernel normalization introduces a temporary and an
    # ordinary expression assignment, whose initializedness WP tracks. This initializes only the owner
    # pointer representation, never its array elements. No new allocator or lifetime premise is added.
    identity_alloc = expected_alloc.removesuffix(";\n") + " + 0;\n"
    lines[alloc_index] = f"  /*@ assert {certificate['count']} >= 0; */ " + identity_alloc.lstrip()
    sha = hashlib.sha256(json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    pin = {"id": f"{lowering.function}.terminal-release", "sha256": sha}
    return View("".join(lines), tuple(m for m in lowering.models if m != certificate["model"]), certificate,
                {"terminal_release_check": identity(), "terminal_release_certificate": pin},
                {"kind": "trusted_tool", "reference": identity(), "sentence":
                 "The terminal-release ownership checker establishes that the final delete[] of a fresh nonescaping "
                 "int array is unobservable to this unit's scalar result and caller memory; ordinary allocation "
                 "and deallocation obey the pinned allocator model. WP checks all earlier accesses."})


def check_view(lowering, view, formal_texts, hints=()):
    """Revalidate exact generator bytes and certificate before hint checking and again before launch."""
    if wp_view(lowering, formal_texts, hints) != view:
        raise Refused("the terminal-release view or certificate changed after planning")
