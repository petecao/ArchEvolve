"""Checked private-heap WP view for a closed scalar vector protocol; created 2026-10-15 ET.

The original C++/C and source contract remain unchanged. This relational lowering checks the
source frame structurally: every source heap write targets source-fresh, nonescaping storage.
WP proves an explicitly broader *private-view* frame, functional facts and alias liveness.
Its imported allocator premise is explicit; unsupported ACSL fresh/allocates/frees supply no fact.
Version 1 has two allocation sites executed once each. It does not support repeated allocation,
move/swap, pointer comparisons, opaque effects, escaped aliases, or heap-bearing formal contracts.
"""
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from swdb import model_domains, std_models, vector_pipeline

MODEL_SHA256 = "cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2"
PREFIX = "swdb_owner_"


class Refused(ValueError):
    """A protocol, model, annotation or view is outside the checked relation."""


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    return {"id": "vector-ownership-check-1", "sha256": _sha(Path(__file__).read_bytes())}


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def _type(node):
    types = node.get("type") or {}
    return types.get("desugaredQualType", types.get("qualType", ""))


def _strip(node):
    # Every wrapper is checked. In particular, narrowing integral conversions are not erased.
    while node.get("kind") in ("ExprWithCleanups", "MaterializeTemporaryExpr", "ParenExpr",
                               "ImplicitCastExpr", "CStyleCastExpr"):
        children = _children(node)
        if len(children) != 1:
            raise Refused("a unary scalar/materialization wrapper is required")
        if node["kind"] == "CStyleCastExpr" and _type(node) != "unsigned long":
            raise Refused("explicit pointer/narrowing casts are unsupported")
        if node["kind"] in ("ImplicitCastExpr", "CStyleCastExpr"):
            if node.get("castKind") not in ("NoOp", "LValueToRValue", "IntegralCast"):
                raise Refused("pointer conversion or unsupported conversion")
            if node.get("castKind") == "IntegralCast" and _type(node) != "unsigned long":
                raise Refused("only the exact int-to-size_t widening is modeled")
        node = children[0]
    return node


def _ref(node, declaration):
    node = _strip(node)
    return node.get("kind") == "DeclRefExpr" and (node.get("referencedDecl") or {}).get("id") == declaration["id"]


def _decl(statement):
    children = _children(statement)
    if statement.get("kind") != "DeclStmt" or len(children) != 1 or children[0].get("kind") != "VarDecl":
        raise Refused("one automatic declaration per statement is required")
    decl = children[0]
    if decl.get("storageClass") or decl.get("tls") or len(_children(decl)) != 1:
        raise Refused("only initialized automatic locals are supported")
    return decl, _strip(_children(decl)[0])


def _literal(node):
    node = _strip(node)
    if node.get("kind") != "IntegerLiteral" or _type(node) != "int":
        raise Refused("this protocol requires an int literal fill and appended value")
    value = int(node["value"])
    if not 0 <= value <= 2147483647:
        raise Refused("the int literal is outside the modeled range")
    return value


def _member(node, name, owner):
    node = _strip(node)
    children = _children(node)
    if node.get("kind") != "CXXMemberCallExpr" or not children:
        raise Refused(f"the exact vector {name} call is required")
    member = children[0]
    if member.get("kind") != "MemberExpr" or member.get("name") != name or member.get("isArrow"):
        raise Refused(f"the exact vector {name} member is required")
    objects = _children(member)
    if len(objects) != 1 or not _ref(objects[0], owner):
        raise Refused("the vector object must be the unchanged local owner")
    return children[1:]


def _protocol(node):
    params = [c for c in _children(node) if c.get("kind") == "ParmVarDecl"]
    if len(params) != 1 or _type(params[0]) != "int" or _type(node) != "int (int)":
        raise Refused("only one scalar int parameter and an int result are supported")
    body = next((c for c in _children(node) if c.get("kind") == "CompoundStmt"), {})
    statements = _children(body)
    if len(statements) not in (4, 5):
        raise Refused("expected construction, one data alias, optional old-value read, one append and return")
    owner, ctor = _decl(statements[0])
    if _type(owner) not in ("std::vector<int>", "std::vector<int, std::allocator<int>>"):
        raise Refused("only a local std::vector<int> is supported")
    arguments = _children(ctor)
    if ctor.get("kind") != "CXXConstructExpr" or len(arguments) != 2 or not _ref(arguments[0], params[0]):
        raise Refused("the count-value constructor must use the unchanged scalar count parameter")
    fill = _literal(arguments[1])
    alias, data = _decl(statements[1])
    if _type(alias) != "int *" or _member(data, "data", owner):
        raise Refused("one direct data() pointer alias is required")
    old = None
    if len(statements) == 5:
        old, value = _decl(statements[2])
        children = _children(value)
        if _type(old) != "int" or value.get("kind") != "UnaryOperator" or value.get("opcode") != "*" or \
                len(children) != 1 or not _ref(children[0], alias):
            raise Refused("the optional saved scalar must read exactly the live captured alias")
    append = _member(statements[-2], "push_back", owner)
    if len(append) != 1:
        raise Refused("exactly one scalar append is required")
    pushed = _literal(append[0])
    result = statements[-1]
    if result.get("kind") != "ReturnStmt" or len(_children(result)) != 1:
        raise Refused("a scalar return must immediately follow the append")
    names = [d.get("name", "") for d in (params[0], owner, alias, *([old] if old else []))]
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name) or name.startswith((PREFIX, "SWDB_OWNER_")) for name in names):
        raise Refused("source names overlap generated ownership names")
    checks, observations, data_reads = [], [], []

    def scalar(expr):
        expr = _strip(expr)
        kind, parts = expr.get("kind"), _children(expr)
        if kind == "IntegerLiteral":
            return str(_literal(expr))
        if kind == "DeclRefExpr":
            if _ref(expr, params[0]):
                return params[0]["name"]
            if old and _ref(expr, old):
                return "swdb_owner_old"
            raise Refused("global, pointer value, or untracked scalar observation")
        if kind == "UnaryOperator" and len(parts) == 1:
            op = expr.get("opcode")
            if op == "*" and _ref(parts[0], alias):
                if any("alias_live_after" in check for check in checks):
                    raise Refused("at most one post-growth alias read is supported")
                checks.append("/*@ assert owner_alias_after_range: 0 < swdb_owner_bound0; */")
                checks.append("/*@ assert alias_live_after: swdb_owner_alias_live == 1; */")
                return "*swdb_owner_alias"
            if op == "*" and _strip(parts[0]).get("kind") == "CXXMemberCallExpr":
                if _member(parts[0], "data", owner):
                    raise Refused("immediate owner data read takes no arguments")
                ordinal = len(data_reads) + 1
                data_reads.append({"ordinal": ordinal, "begin": model_domains.span(expr)[0],
                                   "end": model_domains.span(expr)[1]})
                checks.append(f"/*@ assert owner_data_live_{ordinal}: 0 < swdb_owner_v.size; */")
                checks.append(f"/*@ assert owner_data_storage_{ordinal}: 0 < swdb_owner_bound1; */")
                return "swdb_owner_v.data[0]"
            if op in ("+", "-", "!", "~") and _type(expr) == "int":
                return f"({op}{scalar(parts[0])})"
        if kind == "BinaryOperator" and len(parts) == 2 and _type(expr) == "int" and expr.get("opcode") in \
                ("+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=", "&", "|", "^", "<<", ">>"):
            return f"({scalar(parts[0])} {expr['opcode']} {scalar(parts[1])})"
        member, argument = None, None
        if kind == "CXXOperatorCallExpr" and len(parts) == 3 and _ref(parts[1], owner):
            function = parts[0]
            while function.get("kind") == "ImplicitCastExpr" and len(_children(function)) == 1:
                function = _children(function)[0]
            if function.get("kind") == "DeclRefExpr" and (function.get("referencedDecl") or {}).get("name") == "operator[]":
                member, argument = "operator_index", parts[2]
        elif kind == "CXXMemberCallExpr":
            arguments = _member(expr, "at", owner)
            if len(arguments) == 1:
                member, argument = "at", arguments[0]
        if member:
            index = _strip(argument)
            if not (_ref(index, params[0]) or index.get("kind") == "IntegerLiteral"):
                raise Refused("only the unchanged count or a literal index is supported")
            rendered = params[0]["name"] if _ref(index, params[0]) else str(_literal(index))
            ordinal = len(observations) + 1
            observations.append({"member": member, "index": rendered, "ordinal": ordinal})
            if member == "at":
                checks.append(f"/*@ assert owner_at_guard_{ordinal}: 0 <= {rendered} < swdb_owner_v.size; */")
            checks.append(f"/*@ assert owner_index_{ordinal}: 0 <= {rendered} < swdb_owner_v.size; */")
            checks.append(f"/*@ assert owner_storage_index_{ordinal}: 0 <= {rendered} < swdb_owner_bound1; */")
            return f"swdb_owner_v.data[(size_t)({rendered})]"
        raise Refused(f"unmodeled return observation: {kind}")

    returned = scalar(_children(result)[0])
    return {"parameter": params[0]["name"], "fill": fill, "pushed": pushed, "old": old is not None,
            "return": returned, "checks": checks, "source_names": names,
            "source_statements": len(statements), "observations": observations, "data_reads": data_reads}


def certify_origins(node, *, source, source_sha256, models, anchors, text, entry_windows=None):
    """Generator-owned exact source registry; unsupported protocols grant no origin."""
    try:
        if _sha(source) != source_sha256 or std_models.identity()["sha256"] != MODEL_SHA256:
            raise Refused("the source or audited standard model changed")
        if re.search(r"\boperator\s*(?:new|delete)\b|\bnamespace\s+std\b", source):
            raise Refused("replacement allocation or standard definitions are unsupported")
        for directive in re.findall(r"^\s*#.*$", source, re.M):
            if not re.fullmatch(r"\s*#\s*include\s*<(?:vector|utility|cstddef)>\s*", directive):
                raise Refused("unmodeled preprocessing")
        try:
            protocol = _protocol(node)
        except Refused:
            return vector_pipeline.certify(node, source=source, source_sha256=source_sha256,
                models=models, anchors=anchors, text=text, entry_windows=entry_windows, owner_check=identity())
        return model_domains.source_owner(node, protocol, source_sha256=source_sha256,
            lowering_sha256=_sha(text), models=models, anchors=anchors, owner_check=identity(),
            allocator=allocator_identity())
    except (Refused, model_domains.Refused, vector_pipeline.Refused):
        return {}


def _formal(texts, parameter):
    joined = "\n".join(texts)
    clauses = [c.strip() for c in joined.split(";") if c.strip()]
    if clauses.count(r"assigns \nothing") != 1:
        raise Refused("exactly one original assigns nothing clause is required")
    for clause in clauses:
        if clause == r"assigns \nothing":
            continue
        if not re.match(r"^(requires|ensures)\s+", clause):
            raise Refused("only scalar requires/ensures and assigns nothing are supported")
        expression = re.sub(r"^(requires|ensures)\s+", "", clause)
        if re.search(r"[^\w\s\\+*/%<>=!&|^~()?0-9-]", expression):
            raise Refused("heap/address/formal logic observations are outside the frame projection")
        if "&" in expression.replace("&&", ""):
            raise Refused("formal address observations are unsupported")
        names = re.findall(r"\\?[A-Za-z_]\w*", expression)
        if any(name not in (parameter, r"\result", r"\true", r"\false") for name in names):
            raise Refused("formal observations must use only scalar input/result")
    frame = (f"assigns SWDB_OWNER_PRIVATE0({parameter},&{parameter})[0..{parameter}-1], "
             f"SWDB_OWNER_PRIVATE1(2*(integer){parameter},&{parameter})[0..2*(integer){parameter}-1];")
    return re.sub(r"assigns\s+\\nothing\s*;", lambda _: frame, joined), frame


ALLOCATORS = r"""/*@ logic int *SWDB_OWNER_PRIVATE0(integer count, int *activation);
    logic int *SWDB_OWNER_PRIVATE1(integer count, int *activation); */
typedef struct { int *data; size_t size; size_t capacity; } swdb_owner_vector;
/*@ requires 0 < count <= SIZE_MAX / sizeof(int);
    terminates \true;
    assigns \result \from count,n;
    exits \false;
    ensures \valid(\result + (0 .. count-1));
    ensures \result == SWDB_OWNER_PRIVATE0(count,n);
    ensures \separated(\result + (0 .. count-1), v, n, dst, k, bound);
*/
int *swdb_owner_allocate_initial(size_t count, swdb_owner_vector*v, int*n, int**dst, size_t*k, size_t*bound);
/*@ requires 0 < count <= SIZE_MAX / sizeof(int);
    terminates \true;
    assigns \result \from count,n;
    exits \false;
    ensures \valid(\result + (0 .. count-1));
    ensures \result == SWDB_OWNER_PRIVATE1(count,n);
    ensures \separated(\result + (0 .. count-1), v, n, alias, old_value, dst, k, bound, old+(0..old_size-1));
*/
int *swdb_owner_allocate_growth(size_t count, swdb_owner_vector*v, int*n, int**alias, int*old_value,
                               int**dst, size_t*k, size_t*bound, int*old, size_t old_size);
"""


def allocator_identity():
    return {"id": "vector-owner-private-allocator-1", "sha256": _sha(ALLOCATORS)}


@dataclass(frozen=True)
class View:
    text: str
    models: tuple
    formal_text: str
    certificate: dict
    pins: dict
    assumptions: tuple
    extern_contracts: dict


def wp_view(lowering, source, formal_texts, hints=()):
    """Generate a fresh certificate from source AST and exact audited model bodies, never an input certificate."""
    if ((lowering.pointer_bounds or {}).get("owner") or {}).get("protocol") == vector_pipeline.PROTOCOL:
        try:
            return vector_pipeline.wp_view(lowering, source, formal_texts, hints)
        except vector_pipeline.Refused as exc:
            raise Refused(str(exc)) from None

    from swdb import c_lowering
    if hints:
        raise Refused("version 1 admits no user hints or post-release ghost effects")
    source = Path(source)
    source_text = source.read_text()
    if re.search(r"\boperator\s*(?:new|delete)\b|\bnamespace\s+std\b|\b(?:class|struct)\s+std::", source_text):
        raise Refused("replacement allocation or standard-library definitions are unsupported")
    for directive in re.findall(r"^\s*#.*$", source_text, re.M):
        if not re.fullmatch(r"\s*#\s*include\s*<(?:vector|utility|cstddef)>\s*", directive):
            raise Refused("only the pinned vector/cstddef includes are supported")
    if _sha(source.read_bytes()) != lowering.source_sha256:
        raise Refused("the source changed after lowering")
    if std_models.identity() != {"id": "swdb-std-models-2", "sha256": MODEL_SHA256}:
        raise Refused("the exact standard-model content needs a new ownership audit")
    if lowering.summaries or lowering.probes or lowering.std_models != ("std_vector_int",) or lowering.defines:
        raise Refused("opaque effects, semantics, additional standard types and preprocessing options are unsupported")
    if [a["function"] for a in lowering.anchors if a["kind"] == "contract"] != [lowering.function]:
        raise Refused("only one lowered source function is supported")
    unit = c_lowering._Unit(c_lowering.locate(), source, (), (), {}, None)
    node = unit.function_node(lowering.function, None, None, unit=True)
    protocol = _protocol(node)
    formal, frame = _formal(formal_texts, protocol["parameter"])
    required = {"swdb_alloc_int", "swdb_free", "std_vector_int_ctor_count_value", "std_vector_int_dtor",
                "std_vector_int_data", "std_vector_int_recommend", "std_vector_int_grow", "std_vector_int_push_back"}
    allowed = required | {"std_vector_int_operator_index", "std_vector_int_at"}
    if not required <= set(lowering.models) <= allowed:
        raise Refused("the source uses a model outside the exact allocation/access protocol")
    # Re-lower under the exact same options. This ties the source inventory to every original generated byte.
    checked = c_lowering.lower(source, lowering.function)
    if checked != lowering:
        raise Refused("the source inventory and original lowering/provenance differ")
    text = _render(lowering, protocol)
    origins = certify_origins(node, source=source_text, source_sha256=lowering.source_sha256,
        models=lowering.models, anchors=lowering.anchors, text=lowering.text)
    if not origins:
        raise Refused("closed source has no exact typed-owner origin certificate")
    planned = (lowering.pointer_bounds or {}).get("owner")
    if planned is not None and planned != origins:
        raise Refused("closed source origin registry changed after lowering")
    try:
        view_origins = model_domains.closed_owner_view(text, protocol, origins)
    except model_domains.Refused as exc:
        raise Refused(str(exc)) from None
    model_bodies = dict(std_models.allocator("int"))
    for member in std_models.VECTOR_MEMBERS:
        model_bodies.update(std_models.vector_member("std_vector_int", "int", member))
    certificate = {"id": "vector-private-frame-projection-1", "source_sha256": lowering.source_sha256,
                   "original_c_sha256": lowering.sha256, "original_contract_sha256": _digest(list(formal_texts)),
                   "view_contract_sha256": _sha(formal), "view_sha256": _sha(text), "protocol": protocol,
                   "source_frame": r"assigns \nothing;", "view_frame": frame,
                   "source_frame_preservation": "checked structurally from fresh owned writes and no escape",
                   "wp_frame_scope": "private view only; structural projection is not a WP goal",
                   "allocation_sites": [{"name": "SWDB_OWNER_PRIVATE0", "executions": 1},
                                        {"name": "SWDB_OWNER_PRIVATE1", "executions": 1}],
                   "alias_rule": "capture live; growth invalidates; every retained alias read asserts live",
                   "origins": view_origins, "source_origins": origins,
                   "model_bodies": [{"id": name, "sha256": _sha(model_bodies[name])}
                                    for name in sorted(lowering.models)]}
    pins = {"vector_ownership_check": identity(), "vector_ownership_certificate":
            {"id": lowering.function + ".vector-private-frame", "sha256": _digest(certificate)},
            "vector_ownership_allocator": allocator_identity()}
    assumptions = (
        {"kind": "trusted_tool", "reference": model_domains.identity(), "sentence":
         "The exact audited closed vector constructor and growing append carry typed int allocation origins with "
         "the entry-frozen extents and live prefixes in the origin certificate. This source allocator/model "
         "relation is explicit; WP validity alone supplies no array-object provenance. Each source and view "
         "access is tied to its recorded numerical and alias-liveness obligations; spare capacity grants no "
         "source read permission."},
        {"kind": "trusted_tool", "reference": identity(), "sentence":
         "The checked relational vector lowering preserves scalar observations and the original assigns nothing "
         "frame because every source heap write targets fresh owned nonescaping storage; WP checks the separate "
         "private-region view frame, functional properties and alias liveness, not that structural projection."},
        {"kind": "trusted_tool", "reference": allocator_identity(), "sentence":
         "Under successful ordinary C++ allocation, each of the two unique allocation sites denotes fresh storage "
         "separated from every previously live source object. Private-view addresses rename only this storage; "
         "the imported allocator contracts explicitly expose required validity, separation and frame names."})
    return View(text, (), formal, certificate, pins, assumptions,
                {name: allocator_identity() for name in ("swdb_owner_allocate_initial", "swdb_owner_allocate_growth")})


def check_view(lowering, source, view, formal_texts, hints=()):
    if wp_view(lowering, source, formal_texts, hints) != view:
        raise Refused("the vector ownership view, source, contract or certificate changed after planning")


def check_origins(lowering, source, view, formal_texts, hints=()):
    """Adapter prelaunch coupling: no source-registry-only waiver of pointer admission."""
    check_view(lowering, source, view, formal_texts, hints)
    if (lowering.pointer_bounds or {}).get("owner") != view.certificate["source_origins"]:
        raise Refused("the checked source registry is absent or differs from the owner view")
    return view.certificate["origins"]


def _render(lowering, protocol):
    n, fill, pushed = protocol["parameter"], protocol["fill"], protocol["pushed"]
    lines = ["#include <stddef.h>", "#include <stdint.h>", "#include <limits.h>", ALLOCATORS]
    anchors = [a["id"] for a in lowering.anchors]
    def anchor(name):
        if name not in anchors:
            raise Refused("an original source statement anchor is missing")
        lines.append("  /* swdb-anchor " + name + " */")
    anchor("ghost.globals")
    anchor(lowering.function + ".contract")
    lines += [f"int {lowering.function}(int {n}) {{"]
    anchor(lowering.function + ".entry")
    s = 0
    def begin():
        nonlocal s
        s += 1
        anchor(f"{lowering.function}.s{s}.before")
    def end():
        anchor(f"{lowering.function}.s{s}.after")
    begin()
    lines += [f"  /*@ assert owner_count: {n} >= 1; */", "  swdb_owner_vector swdb_owner_v = {0,0,0};",
              f"  size_t swdb_owner_bound0=(size_t){n}, swdb_owner_k0=0;", "  int *swdb_owner_fresh0;",
              "  /*@ assert owner_initial_zero: 0 <= swdb_owner_bound0; */",
              f"  swdb_owner_fresh0=swdb_owner_allocate_initial(swdb_owner_bound0,&swdb_owner_v,&{n},"
              "&swdb_owner_fresh0,&swdb_owner_k0,&swdb_owner_bound0)+0;",
              f"  /*@ loop invariant 0 <= swdb_owner_k0 <= swdb_owner_bound0;\n"
              f"      loop invariant swdb_owner_bound0 == {n};\n"
              "      loop invariant \\initialized(&swdb_owner_fresh0);\n"
              "      loop invariant \\initialized(swdb_owner_fresh0+(0..swdb_owner_k0-1));\n"
              f"      loop invariant \\forall integer j; 0 <= j < swdb_owner_k0 ==> swdb_owner_fresh0[j] == {fill};\n"
              "      loop assigns swdb_owner_k0, swdb_owner_fresh0[0..swdb_owner_bound0-1];\n"
              "      loop variant swdb_owner_bound0-swdb_owner_k0; */",
              f"  for(swdb_owner_k0=0;swdb_owner_k0<swdb_owner_bound0;++swdb_owner_k0) {{",
              "    /*@ assert owner_initial_range: 0 <= swdb_owner_k0 < swdb_owner_bound0; */",
              f"    swdb_owner_fresh0[swdb_owner_k0]={fill}; }}",
              "  swdb_owner_v.data=swdb_owner_fresh0; swdb_owner_v.size=swdb_owner_bound0; swdb_owner_v.capacity=swdb_owner_bound0;"]
    end(); begin()
    lines += ["  int *swdb_owner_alias=swdb_owner_v.data;", "  /*@ ghost int swdb_owner_alias_live=1; */"]
    end()
    # A harmless initialized local exists even when source has no saved value: the second allocator separates it.
    if protocol["old"]:
        begin()
        lines += ["  /*@ assert owner_alias_before_range: 0 < swdb_owner_bound0; */",
                  "  /*@ assert alias_live_before: swdb_owner_alias_live == 1; */",
                  "  int swdb_owner_old=*swdb_owner_alias;"]
        end()
    else:
        lines += ["  int swdb_owner_old=0;"]
    begin()
    lines += ["  /*@ assert owner_growth_policy: swdb_owner_v.capacity < (SIZE_MAX/sizeof(int))/2; */",
              "  size_t swdb_owner_bound1=2*swdb_owner_v.capacity, swdb_owner_k1=0;", "  int *swdb_owner_fresh1;",
              "  /*@ assert owner_growth_zero: 0 <= swdb_owner_bound1; */",
              f"  swdb_owner_fresh1=swdb_owner_allocate_growth(swdb_owner_bound1,&swdb_owner_v,&{n},&swdb_owner_alias,"
              "&swdb_owner_old,&swdb_owner_fresh1,&swdb_owner_k1,&swdb_owner_bound1,swdb_owner_v.data,swdb_owner_v.capacity)+0;",
              "  /*@ loop invariant 0 <= swdb_owner_k1 <= swdb_owner_v.size;\n"
              f"      loop invariant swdb_owner_v.size == {n};\n"
              "      loop invariant \\initialized(&swdb_owner_fresh1);\n"
              "      loop invariant \\initialized(swdb_owner_fresh1+(0..swdb_owner_k1-1));\n"
              f"      loop invariant \\forall integer j; 0 <= j < swdb_owner_v.size ==> swdb_owner_v.data[j] == {fill};\n"
              f"      loop invariant \\forall integer j; 0 <= j < swdb_owner_k1 ==> swdb_owner_fresh1[j] == {fill};\n"
              "      loop assigns swdb_owner_k1, swdb_owner_fresh1[0..swdb_owner_bound1-1];\n"
              "      loop variant swdb_owner_v.size-swdb_owner_k1; */",
              "  for(swdb_owner_k1=0;swdb_owner_k1<swdb_owner_v.size;++swdb_owner_k1) {",
              "    /*@ assert owner_copy_range: 0 <= swdb_owner_k1 < swdb_owner_bound0 && swdb_owner_k1 < swdb_owner_bound1; */",
              "    swdb_owner_fresh1[swdb_owner_k1]=swdb_owner_v.data[swdb_owner_k1]; }",
              "  /*@ ghost swdb_owner_alias_live=0; */",
              "  swdb_owner_v.data=swdb_owner_fresh1; swdb_owner_v.capacity=swdb_owner_bound1;",
              "  /*@ assert owner_append_range: 0 <= swdb_owner_v.size < swdb_owner_bound1; */",
              f"  swdb_owner_v.data[swdb_owner_v.size]={pushed}; swdb_owner_v.size++;"]
    end(); begin()
    lines.extend("  " + check for check in protocol["checks"])
    lines += ["  return " + protocol["return"] + ";"]
    end()
    # Original lowerer emits an unreachable destructor after the return as well. Preserve its anchors only.
    if s + 1 != protocol["source_statements"] + 1:
        raise Refused("the source statement inventory differs")
    begin(); end()
    lines += ["}"]
    return "\n".join(lines) + "\n"
