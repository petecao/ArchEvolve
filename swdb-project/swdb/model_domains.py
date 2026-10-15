"""Typed origins for the closed two-site vector relation; created 2026-10-15 ET.

No validity-to-array inference and no generic field/model admission. Source registries
must be coupled to the independently checked generated view before WP admission.
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from swdb import std_models

MODEL_SHA256 = "cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2"
ALLOCATOR_SHA256 = "30e4a75965ae91dd1c50fb23b4c6010fdd620b286f43d00b73ac559529139d74"
VIEW_PREFIX_SHA256 = "7a0e60d25b448de2a498aa53628e7b2d75c35ca2d8188dae1dafd64c6f70b3f6"


class Refused(ValueError):
    pass


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    return {"id": "closed-owner-model-domain-1", "sha256": _sha(Path(__file__).read_bytes())}


def children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def walk(node):
    yield node
    for child in children(node):
        yield from walk(child)


def span(node):
    begin, end = (node.get("range") or {}).get("begin") or {}, (node.get("range") or {}).get("end") or {}
    if "offset" not in begin or "offset" not in end:
        raise Refused("closed-owner origin has macro or unknown source coordinates")
    return begin["offset"], end["offset"] + end.get("tokLen", 0)


def strip(node):
    while node.get("kind") in {"ImplicitCastExpr", "ParenExpr", "ExprWithCleanups"} and len(children(node)) == 1:
        if node.get("kind") == "ImplicitCastExpr" and node.get("castKind") not in {
                "NoOp", "LValueToRValue", "FunctionToPointerDecay", "IntegralCast"}:
            break
        node = children(node)[0]
    return node


def reference(node):
    node = strip(node)
    return (node.get("referencedDecl") or {}).get("name") if node.get("kind") == "DeclRefExpr" else None


def source_owner(node, protocol, *, source_sha256, lowering_sha256, models, anchors, owner_check, allocator):
    """Exact persistent declaration registry after the closed source grammar was checked."""
    from swdb import c_lowering
    if std_models.identity()["sha256"] != MODEL_SHA256 or allocator != {
            "id": "vector-owner-private-allocator-1", "sha256": ALLOCATOR_SHA256}:
        raise Refused("the closed owner typed allocator/model needs a new content audit")
    function = node["name"]
    body = next(c for c in children(node) if c.get("kind") == "CompoundStmt")
    statements = children(body)
    owner = children(statements[0])[0]
    alias = children(statements[1])[0]
    n = protocol["parameter"]
    entry = rf"\at((integer){n},Pre)"
    append_at = span(statements[-2])[0]
    declarations = [{"function": function, "name": alias["name"], "begin": span(alias)[0], "end": span(alias)[1],
                     "kind": "closed_vector_alias", "element_type": "int", "elements": entry,
                     "relative_offset": 0, "allocation_site": "initial", "requires_liveness": True}]
    accesses, calls = [], []
    index = 0
    permitted = {p["id"] for p in children(node) if p.get("kind") == "ParmVarDecl"}
    permitted.update(p["id"] for p in walk(body) if p.get("kind") == "VarDecl")
    for part in walk(body):
        kind = part.get("kind")
        if kind == "DeclRefExpr" and (part.get("referencedDecl") or {}).get("kind") in {"VarDecl", "ParmVarDecl"} \
                and (part.get("referencedDecl") or {}).get("id") not in permitted:
            raise Refused("closed source observes an external object")
        if kind == "CallExpr" or kind in {"CompoundAssignOperator", "BinaryConditionalOperator", "ConditionalOperator"} \
                or kind == "BinaryOperator" and part.get("opcode") in {"=", ",", "&&", "||"} \
                or kind == "UnaryOperator" and part.get("opcode") in {"&", "++", "--"}:
            raise Refused("closed source has an unmodeled call, mutation or conditional effect")
        if kind == "CXXMemberCallExpr":
            callee = children(part)[0]
            if callee.get("kind") != "MemberExpr" or callee.get("name") not in {"data", "push_back"} \
                    or len(children(callee)) != 1 or reference(children(callee)[0]) != owner["name"]:
                raise Refused("closed source has an unmodeled member origin/effect")
        if kind == "CXXOperatorCallExpr" and reference(children(part)[0]) != "operator[]":
            raise Refused("closed source has an unmodeled operator origin/effect")
        if kind == "UnaryOperator" and part.get("opcode") == "*":
            if len(children(part)) != 1 or reference(children(part)[0]) != alias["name"]:
                raise Refused("untracked source pointer read")
            phase = "before" if span(part)[0] < append_at else "after"
            accesses.append({"kind": "alias_read", "begin": span(part)[0], "end": span(part)[1],
                "allocation_site": "initial", "relative_offset": 0,
                "bounds_guard": f"owner_alias_{phase}_range", "liveness_guard": f"alias_live_{phase}"})
        if kind == "CXXOperatorCallExpr":
            index += 1
            accesses.append({"kind": "owner_index", "begin": span(part)[0], "end": span(part)[1],
                "allocation_site": "growth", "bounds_guard": f"owner_storage_index_{index}",
                "live_prefix_guard": f"owner_index_{index}", "liveness_guard": "owner_current_growth"})
        if kind in {"CXXConstructExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"}:
            model = "std_vector_int_" + ("ctor_count_value" if kind == "CXXConstructExpr" else
                "operator_index" if kind == "CXXOperatorCallExpr" else children(part)[0]["name"])
            calls.append({"kind": kind, "begin": span(part)[0], "end": span(part)[1], "model": model,
                "model_sha256": _sha(c_lowering.model_text(model)), "receiver": owner["name"],
                "allocation_in": None if kind == "CXXConstructExpr" else
                                 "initial" if span(part)[0] <= append_at else "growth",
                "allocation_out": "growth" if model.endswith("push_back") else
                                  "initial" if span(part)[0] < append_at else "growth"})
    model_bodies = []
    for name in sorted(set(models)):
        text = c_lowering.model_text(name)
        if text is not None:
            model_bodies.append({"id": name, "sha256": _sha(text)})
    out = {"check": identity(), "owner_check": owner_check, "source_sha256": source_sha256,
           "lowering_sha256": lowering_sha256, "model": std_models.identity(), "allocator": allocator,
           "function": function, "owner": {"name": owner["name"], "begin": span(owner)[0], "end": span(owner)[1]},
           "declarations": declarations, "source_accesses": accesses, "calls": calls,
           "allocations": [{"site": "initial", "element_type": "int", "elements": entry,
                            "live_elements": entry, "executions": 1},
                           {"site": "growth", "element_type": "int", "elements": f"(2 * {entry})",
                            "live_elements": f"({entry} + 1)", "executions": 1}],
           "aliases": [{"name": alias["name"], "allocation_site": "initial", "invalidated_by": "growth"}],
           "model_bodies": model_bodies, "anchors_sha256": _digest(list(anchors)),
           "binding_effects": "closed scalar protocol; count unchanged; no alias reassignment, escape, callback or hidden call",
           "storage_boundary": "backing extents do not grant spare-capacity source reads; every source index checks current live size"}
    out["certificate_sha256"] = _digest(out)
    return out


def _pointer(node):
    return bool(re.search(r"\*\s*(?:(?:const|volatile|restrict)\s*)*$", str((node.get("type") or {}).get("qualType", ""))))


def closed_owner_view(text, protocol, source_certificate):
    """Independently inventory every C view access and its exact typed root and checked guard."""
    from swdb import c_lowering
    if not source_certificate or source_certificate.get("check") != identity():
        raise Refused("closed owner has no current source origin certificate")
    prefix, marker, _body = text.partition("  /* swdb-anchor ghost.globals */")
    if not marker or _sha(prefix) != VIEW_PREFIX_SHA256:
        raise Refused("the imported typed allocator contracts/layout need a new exact-content audit")
    source = dict(source_certificate)
    digest = source.pop("certificate_sha256", None)
    if digest != _digest(source):
        raise Refused("closed owner source origin certificate changed")
    with tempfile.TemporaryDirectory(prefix="swdb-owner-domain-") as folder:
        path = Path(folder) / "owner.c"
        path.write_text(text)
        done = subprocess.run([*c_lowering.locate().command, "-x", "c", "-std=gnu11", "-fsyntax-only",
                               "-Xclang", "-ast-dump=json", str(path)], capture_output=True, text=True, timeout=60)
        if done.returncode:
            raise Refused("closed owner C view cannot be independently parsed: " + done.stderr[-500:])
        try:
            ast = json.loads(done.stdout)
        except ValueError:
            raise Refused("closed owner C view AST is malformed") from None
    definitions = [n for n in walk(ast) if n.get("kind") == "FunctionDecl" and
                   any(c.get("kind") == "CompoundStmt" for c in children(n))]
    if len(definitions) != 1 or definitions[0].get("name") != source["function"]:
        raise Refused("closed owner view has an untracked function body")
    body = next(c for c in children(definitions[0]) if c.get("kind") == "CompoundStmt")
    raw = text.encode()
    expr = lambda n: raw[slice(*span(n))].decode()
    compact = lambda s: re.sub(r"\s+", "", s)
    guards = {m.group(1): (m.start(), m.end(), compact(m.group(2)))
              for m in re.finditer(r"/\*@\s*assert\s+(\w+)\s*:\s*(.*?);\s*\*/", text, re.S)}
    guard_count = len(re.findall(r"/\*@\s*assert\s+", text))
    if len(guards) != guard_count:
        raise Refused("closed owner view repeats an assertion name")

    def guarded(name, predicate, node):
        if name not in guards or guards[name][2] != compact(predicate) or guards[name][1] > span(node)[0]:
            raise Refused(f"closed owner view access lacks its exact preceding {name} obligation")
        return name

    def data(node):
        node = strip(node)
        return (node.get("kind") == "MemberExpr" and node.get("name") == "data" and
                not node.get("isArrow") and len(children(node)) == 1 and reference(children(node)[0]) == "swdb_owner_v")

    writes = []
    for n in walk(body):
        parts = children(n)
        if n.get("kind") == "BinaryOperator" and n.get("opcode") == "=" and data(parts[0]):
            writes.append((span(n)[0], reference(parts[1])))
    if [name for _at, name in writes] != ["swdb_owner_fresh0", "swdb_owner_fresh1"]:
        raise Refused("closed owner data binding does not follow the two fresh allocation sites")
    growth_at = writes[1][0]
    top = children(body)
    expected_kinds = ["DeclStmt", "DeclStmt", "DeclStmt", "BinaryOperator", "ForStmt",
        "BinaryOperator", "BinaryOperator", "BinaryOperator", "DeclStmt", "DeclStmt", "DeclStmt",
        "DeclStmt", "BinaryOperator", "ForStmt", "BinaryOperator", "BinaryOperator", "BinaryOperator",
        "UnaryOperator", "ReturnStmt"]
    if [p.get("kind") for p in top] != expected_kinds:
        raise Refused("the C view has a hidden statement/control transition")
    initializers = {"swdb_owner_v": "{0,0,0}", "swdb_owner_bound0": "(size_t)"+protocol["parameter"],
        "swdb_owner_k0": "0", "swdb_owner_fresh0": None, "swdb_owner_alias": "swdb_owner_v.data",
        "swdb_owner_old": "*swdb_owner_alias" if protocol["old"] else "0",
        "swdb_owner_bound1": "2*swdb_owner_v.capacity", "swdb_owner_k1": "0", "swdb_owner_fresh1": None}
    declarations = [p for p in walk(body) if p.get("kind") == "VarDecl"]
    if len(declarations) != len(initializers) or {p.get("name") for p in declarations} != set(initializers):
        raise Refused("the C view has a hidden/shadowed local or alias")
    for declaration in declarations:
        init = children(declaration)
        expected = initializers[declaration["name"]]
        if (expected is None and init) or (expected is not None and
                (len(init) != 1 or compact(expr(init[0])) != expected)):
            raise Refused("the C view has an unmodeled pointer/count/scalar initializer")
    expected_assignments = {3: "swdb_owner_fresh0=swdb_owner_allocate_initial", 5: "swdb_owner_v.data=swdb_owner_fresh0",
        6: "swdb_owner_v.size=swdb_owner_bound0", 7: "swdb_owner_v.capacity=swdb_owner_bound0",
        12: "swdb_owner_fresh1=swdb_owner_allocate_growth", 14: "swdb_owner_v.data=swdb_owner_fresh1",
        15: "swdb_owner_v.capacity=swdb_owner_bound1",
        16: "swdb_owner_v.data[swdb_owner_v.size]="+str(protocol["pushed"])}
    for at, expected in expected_assignments.items():
        actual = compact(expr(top[at]))
        if not (actual.startswith(expected+"(") and actual.endswith(")+0") if at in {3,12} else actual == expected):
            raise Refused("the C view has an unmodeled binding/write transition")
    if compact(expr(top[17])) != "swdb_owner_v.size++" or compact(expr(children(top[18])[0])) != compact(protocol["return"]):
        raise Refused("the C view has an unmodeled live-prefix/result transition")
    for at, k, stop, assignment in ((4,"swdb_owner_k0","swdb_owner_bound0",
            "swdb_owner_fresh0[swdb_owner_k0]="+str(protocol["fill"])),
            (13,"swdb_owner_k1","swdb_owner_v.size",
             "swdb_owner_fresh1[swdb_owner_k1]=swdb_owner_v.data[swdb_owner_k1]")):
        parts = children(top[at])
        if len(parts) != 4 or [compact(expr(p)) for p in parts[:3]] != [k+"=0",k+"<"+stop,"++"+k] \
                or parts[3].get("kind") != "CompoundStmt" or len(children(parts[3])) != 1 \
                or compact(expr(children(parts[3])[0])) != assignment:
            raise Refused("the C view loop has an unmodeled condition/body/effect")
    invalidation = text.find("/*@ ghost swdb_owner_alias_live=0; */")
    capture = text.find("/*@ ghost int swdb_owner_alias_live=1; */")
    ghost = [compact(m.group(1)) for m in re.finditer(r"/\*@\s*ghost\s+(.*?)\*/", text, re.S)]
    if ghost != ["intswdb_owner_alias_live=1;", "swdb_owner_alias_live=0;"]:
        raise Refused("the C view contains an extra liveness ghost effect")
    if not span(top[8])[1] < capture < span(top[9])[0] or not span(top[13])[1] < invalidation < growth_at:
        raise Refused("closed owner liveness guards are not at the exact capture/release transition")
    if not 0 <= capture < invalidation < growth_at or text.count("swdb_owner_alias_live=0;") != 1:
        raise Refused("closed owner alias capture/invalidation transition is absent or misplaced")
    calls, accesses, index = [], [], 0
    n = protocol["parameter"]
    expected_calls = {
        "swdb_owner_allocate_initial": ["swdb_owner_bound0", "&swdb_owner_v", "&"+n,
            "&swdb_owner_fresh0", "&swdb_owner_k0", "&swdb_owner_bound0"],
        "swdb_owner_allocate_growth": ["swdb_owner_bound1", "&swdb_owner_v", "&"+n,
            "&swdb_owner_alias", "&swdb_owner_old", "&swdb_owner_fresh1", "&swdb_owner_k1",
            "&swdb_owner_bound1", "swdb_owner_v.data", "swdb_owner_v.capacity"]}
    for node in walk(body):
        kind, parts = node.get("kind"), children(node)
        if kind == "CallExpr":
            name = reference(parts[0])
            if name not in expected_calls or [compact(expr(p)) for p in parts[1:]] != expected_calls[name]:
                raise Refused("closed owner view has an untracked allocation/call effect")
            calls.append(name)
        if kind == "BinaryOperator" and node.get("opcode") in {"+", "-"} and _pointer(node):
            if len(parts) != 2 or parts[0].get("kind") != "CallExpr" or parts[1].get("value") != "0":
                raise Refused("closed owner view has untracked pointer formation")
            site = "initial" if reference(children(parts[0])[0]) == "swdb_owner_allocate_initial" else "growth"
            bound = "swdb_owner_bound0" if site == "initial" else "swdb_owner_bound1"
            guard = guarded("owner_"+site+"_zero", f"0 <= {bound}", node)
            accesses.append({"kind": "formation", "allocation_site": site, "relative_offset": 0,
                             "bounds_guard": guard, "liveness_guard": "fresh_allocation"})
        if kind == "ArraySubscriptExpr":
            base, offset = parts
            root, position = reference(base), compact(expr(offset))
            if root == "swdb_owner_fresh0" and position == "swdb_owner_k0":
                site, guard, predicate = "initial", "owner_initial_range", "0 <= swdb_owner_k0 < swdb_owner_bound0"
            elif root == "swdb_owner_fresh1" and position == "swdb_owner_k1" or data(base) and span(node)[0] < growth_at and position == "swdb_owner_k1":
                site = "growth" if root else "initial"
                guard, predicate = "owner_copy_range", "0 <= swdb_owner_k1 < swdb_owner_bound0 && swdb_owner_k1 < swdb_owner_bound1"
            elif data(base) and span(node)[0] > growth_at and position == "swdb_owner_v.size":
                site, guard, predicate = "growth", "owner_append_range", "0 <= swdb_owner_v.size < swdb_owner_bound1"
            elif data(base) and span(node)[0] > growth_at and position in {"(size_t)(0)", "(size_t)("+n+")"}:
                index += 1
                value = "0" if position == "(size_t)(0)" else n
                site, guard, predicate = "growth", f"owner_storage_index_{index}", f"0 <= {value} < swdb_owner_bound1"
                guarded(f"owner_index_{index}", f"0 <= {value} < swdb_owner_v.size", node)
            else:
                raise Refused("closed owner view has an untracked array root/index")
            accesses.append({"kind": "array_access", "allocation_site": site, "offset": expr(offset),
                "bounds_guard": guarded(guard, predicate, node), "liveness_guard": "current_owned_storage"})
        if kind == "UnaryOperator" and node.get("opcode") == "*":
            if len(parts) != 1 or reference(parts[0]) != "swdb_owner_alias":
                raise Refused("closed owner view has an untracked indirect read")
            phase = "before" if span(node)[0] < invalidation else "after"
            accesses.append({"kind": "alias_read", "allocation_site": "initial", "alias": True, "relative_offset": 0,
                "bounds_guard": guarded(f"owner_alias_{phase}_range", "0 < swdb_owner_bound0", node),
                "liveness_guard": guarded(f"alias_live_{phase}", "swdb_owner_alias_live == 1", node)})
        if kind == "CompoundAssignOperator" and _pointer(node) or kind == "UnaryOperator" and node.get("opcode") in {"++", "--"} and _pointer(node):
            raise Refused("closed owner view has untracked pointer mutation")
    if calls != list(expected_calls):
        raise Refused("closed owner view allocation site multiplicity differs")
    if "owner_count" not in guards or guards["owner_count"][2] != compact(f"{n} >= 1"):
        raise Refused("closed owner count obligation is missing")
    if index != sum(a["kind"] == "owner_index" for a in source["source_accesses"]):
        raise Refused("closed owner source/view indexed observations differ")
    if sum(a["kind"] == "alias_read" for a in accesses) != sum(a["kind"] == "alias_read" for a in source["source_accesses"]):
        raise Refused("closed owner source/view alias observations differ")
    out = {"check": identity(), "complete": True, "source_certificate_sha256": digest,
           "view_sha256": _sha(text), "allocations": source["allocations"], "aliases": source["aliases"],
           "source_accesses": source["source_accesses"], "view_accesses": accesses,
           "calls": calls, "boundaries": "exact closed two-site typed allocator relation; no generic field/parameter origin"}
    out["certificate_sha256"] = _digest(out)
    return out
