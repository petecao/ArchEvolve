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


def _span(node):
    begin, end = ((node.get("range") or {}).get(key) or {} for key in ("begin", "end"))
    if ("offset" not in begin or "offset" not in end or
            any(key in point for point in (begin, end) for key in ("spellingLoc", "expansionLoc"))):
        raise Refused("DX100 call binding needs direct source coordinates")
    return [begin["offset"], end["offset"] + end.get("tokLen", 0)]


def imported_binding(node, translation_units, name, *, summary, policy):
    """Resolve the actual callee in one full TU; filtered dumps have distinct IDs."""
    declarations, contexts, calls = {}, {}, []
    def visit(part, context=()):
        kind = part.get("kind")
        if kind in {"NamespaceDecl", "CXXRecordDecl", "RecordDecl", "FunctionTemplateDecl"}:
            context += ((kind, part.get("name", "")),)
        if kind == "FunctionDecl":
            declarations[part.get("id")] = part
            contexts[part.get("id")] = context
        if kind == "CallExpr":
            try:
                if _span(part) == _span(node):
                    calls.append(part)
            except Refused:
                pass
        for child in part.get("inner", []):
            if isinstance(child, dict):
                visit(child, context)
    for root in translation_units:
        visit(root)
    matching = []
    for call in calls:
        callee = _strip_origin(call["inner"][0])
        if callee.get("kind") == "ImplicitCastExpr" and callee.get("castKind") == "FunctionToPointerDecay":
            callee = callee["inner"][0]
        ref = callee.get("referencedDecl") or {}
        if ref.get("name") == name:
            matching.append(ref)
    if len(matching) != 1:
        raise Refused("DX100 source call has no unique full-TU callee binding")
    declaration = declarations.get(matching[0].get("id"))
    if not declaration or contexts.get(declaration.get("id")) or declaration.get("storageClass") == "static":
        raise Refused("DX100 source call is not a global imported function")
    if any(c.get("kind") == "TemplateArgument" for c in declaration.get("inner", [])):
        raise Refused("DX100 source callee is a template rather than its canonical imported function")
    if any(d.get("name") == name and any(c.get("kind", "").endswith("Attr") for c in d.get("inner", []))
           for d in declarations.values()):
        raise Refused("DX100 imported callee has unsupported code/linkage attributes")
    signature = str((declaration.get("type") or {}).get("qualType", ""))
    mangled = declaration.get("mangledName", "")
    if mangled not in {name, "_" + name} and not mangled.startswith((f"_Z{len(name)}{name}", f"__Z{len(name)}{name}")):
        raise Refused("DX100 source callee has a noncanonical linkage binding")
    if any(d.get("name") == name and any(c.get("kind") == "CompoundStmt" for c in d.get("inner", []))
           for d in declarations.values()):
        raise Refused("DX100 source callee is defined rather than imported")
    if not summary or summary != policy.get("model", {}).get("entry"):
        raise Refused("DX100 source callee does not bind the audited semantics entry")
    location = declaration.get("loc") or {}
    path = Path(location.get("_file", location.get("file", "")))
    if not path.is_file():
        raise Refused("DX100 imported declaration has no pinned source file")
    return {"name": name, "signature": signature, "mangled_name": mangled, "namespace": [],
            "summary": summary, "source_name": path.name,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_range": _span(declaration)}


def call_site(node, *, statement, anchor, function, line):
    """First slice accepts a single standalone call, with pure argument evaluation."""
    reason = ""
    if statement is not node or not anchor:
        reason = "DX100 window calls need a standalone statement and exact preceding anchor"
    for part in _walk(node):
        kind, op = part.get("kind"), part.get("opcode")
        if (part is not node and kind in {"CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"}
                or kind in {"CompoundAssignOperator", "ConditionalOperator", "BinaryConditionalOperator"}
                or kind == "UnaryOperator" and op in {"++", "--"}
                or kind == "BinaryOperator" and op in {"=", ",", "&&", "||"}
                or "volatile" in str((part.get("type") or {}).get("qualType", ""))):
            reason = "DX100 window call arguments need pure single-evaluation placement"
    try:
        span = _span(node)
    except Refused as exc:
        span, reason = None, str(exc)
    return {"function": function, "anchor": anchor, "source_line": line, "source_range": span,
            "reason": reason, "_ast_id": node.get("id")}


def check_import_signature(binding, policy):
    prototype = policy.get("prototype", "")
    name = policy.get("call", "")
    match = re.fullmatch(r"\s*(.*?)\b" + re.escape(name) + r"\s*\((.*?)\)\s*;?\s*", prototype, re.S)
    if not match:
        raise Refused("DX100 imported call has no canonical pinned prototype")
    params = []
    if match[2].strip() not in {"", "void"}:
        for parameter in match[2].split(","):
            param = re.sub(r"\b[A-Za-z_]\w*\s*$", "", parameter).strip()
            if not param:
                raise Refused("DX100 prototype needs explicit primitive named parameters")
            params.append(param)
    expected = re.sub(r"\s+", "", match[1] + "(" + ",".join(params) + ")")
    if re.sub(r"\s+", "", binding["signature"]) != expected:
        raise Refused("DX100 imported signature differs from its audited pinned prototype")


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
    from swdb import proof_semantics
    fresh = semantic_origins(library, defines)
    calls = proof_semantics.array_call_policies(library, defines)
    imports = proof_semantics.imported_call_policies(library, defines)
    for row in (lowering.pointer_bounds or {}).get("sites", []):
        if row.get("kind") == "call" and row.get("policy") != calls.get(row.get("call")):
            raise Refused("DX100 call footprint policy, model content, entry or geometry changed after planning")
        if row.get("kind") == "import" and row.get("import_policy") != imports.get(row.get("call")):
            raise Refused("DX100 imported-call prototype, entry or model changed after planning")
        origin = row.get("origin") or {}
        if origin.get("kind") == "semantic_rows" and origin != fresh.get(origin.get("producer")):
            raise Refused("array-object origin model content, entry or geometry changed after planning")


def _scalar_math(node):
    """Pure signed integer source arithmetic; RTE independently checks C overflow."""
    from swdb.c_lowering import INTEGER_TYPES
    kind = node.get("kind")
    children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
    qual = ' '.join(re.sub(r'\b(?:const|volatile)\b', '',
                          str((node.get("type") or {}).get("qualType", ""))).split())
    if "volatile" in str((node.get("type") or {}).get("qualType", "")):
        raise Refused("window offsets cannot duplicate volatile reads")
    if kind in {"ParenExpr", "ImplicitCastExpr"} and len(children) == 1:
        if kind == "ImplicitCastExpr" and node.get("castKind") not in {"NoOp", "LValueToRValue"}:
            raise Refused("window offsets need a value-preserving scalar conversion policy")
        return _scalar_math(children[0])
    if kind == "IntegerLiteral":
        return node["value"]
    if kind == "DeclRefExpr" and qual in INTEGER_TYPES:
        name = (node.get("referencedDecl") or {}).get("name", "")
        if re.fullmatch(r'[A-Za-z_]\w*', name):
            return f'((integer){name})'
    if kind == "BinaryOperator" and node.get("opcode") in {"+", "-", "*"} and len(children) == 2:
        if qual not in INTEGER_TYPES or qual.startswith("unsigned") or qual in {"size_t", "uintptr_t"} or qual.startswith("uint"):
            raise Refused("window offset arithmetic needs a checked unsigned/mixed-width conversion policy")
        return f'({_scalar_math(children[0])} {node["opcode"]} {_scalar_math(children[1])})'
    if kind == "UnaryOperator" and node.get("opcode") in {"+", "-"} and len(children) == 1:
        if qual not in INTEGER_TYPES or qual.startswith("unsigned") or qual in {"size_t", "uintptr_t"} or qual.startswith("uint"):
            raise Refused("window offset arithmetic needs a checked unsigned conversion policy")
        return f'({node["opcode"]}{_scalar_math(children[0])})'
    raise Refused("window offsets need pure primitive integer expressions")


def _window_target(node, origin):
    children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
    if node.get("kind") == "UnaryOperator" and node.get("opcode") == "&":
        return _window_target(_strip_origin(children[0]), origin)
    if node.get("kind") == "UnaryOperator" and node.get("opcode") == "*":
        return origin.get("relative_offset", "0")
    scalar = next((n for n in children if not _pointer(n)), None)
    if scalar is None:
        raise Refused("window operation has no primitive scalar offset")
    sign = '-' if node.get("kind") == "BinaryOperator" and node.get("opcode") == '-' else '+'
    return f'({origin.get("relative_offset", "0")} {sign} {_scalar_math(scalar)})'


def recheck_source(lowering, plan):
    """Freshly parse the source/closure; no candidate-supplied certificate is loaded."""
    from swdb import c_lowering
    if not isinstance(plan, dict) or not (plan.get("kwargs", {}).get("array_domains") or
            (lowering.pointer_bounds or {}).get("owner") or
            any(row.get("kind") in {"call", "producer", "import"} for row in lowering.pointer_bounds.get("sites", []))):
        raise Refused("entry windows have no generator-owned source recheck plan")
    fresh = c_lowering.lower(Path(plan["source"]), lowering.function, **plan["kwargs"])
    if fresh.pointer_bounds != lowering.pointer_bounds or fresh.text != lowering.text:
        raise Refused("entry-window AST, binding, source closure or checked lowering changed after planning")


class _Origins:
    """Conservative source origins; no allocation-validity-to-array inference."""
    def __init__(self, definitions, globals=(), known=None, terminal=None, entry_windows=None, entry_function=None,
                 checked_calls=(), checked_producers=()):
        self.definitions, self.known, self.terminal = definitions, known or {}, terminal or {}
        self.entry_windows, self.entry_function = entry_windows or {}, entry_function
        self.checked_producers = checked_producers
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
                    if (function, node.get("id")) not in checked_calls:
                        for arg in children[1:]:
                            self.unstable.update((function, (n.get("referencedDecl") or {}).get("id")) for n in _walk(arg)
                                                 if n.get("kind") == "DeclRefExpr" and _pointer(n))

    def get(self, node, function, seen=()):
        node = _strip_origin(node)
        kind, children = node.get("kind"), [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
        if kind == "BinaryOperator" and node.get("opcode") in {"+", "-"}:
            pointers = [n for n in children if _pointer(n)]
            if len(pointers) == 1:
                origin = self.get(pointers[0], function, seen)
                if origin and origin.get("kind") == "entry_window":
                    return {**origin, "relative_offset": _window_target(node, origin)}
                return origin
        if kind == "CallExpr" and children:
            if (function, node.get("id")) not in self.checked_producers:
                return None
            refs = [(n.get("referencedDecl") or {}).get("name") for n in _walk(children[0])]
            return next((self.known[name] for name in refs if name in self.known), None)
        if kind != "DeclRefExpr":
            return None
        ref = node.get("referencedDecl") or {}
        key, name = ref.get("id"), ref.get("name")
        declaration = self.declarations.get(function, {}).get(key)
        if declaration is None and ref.get("kind") == "VarDecl":
            declaration = self.globals.get(name)
        if declaration is None or key in seen or (function, key) in self.unstable:
            return None
        if declaration.get("kind") == "ParmVarDecl":
            window = self.entry_windows.get("windows", {}).get(name) if function == self.entry_function else None
            if window and _pointer(declaration):
                return {"kind": "entry_window", "parameter": name, "root": name,
                        "element_type": window["element_type"], "elements": window["entry_acsl"],
                        "relative_offset": "0", "declarations_sha256": self.entry_windows["declarations_sha256"]}
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
        # A variable offset in an alias initializer would require a value
        # snapshot at that declaration, distinct from the unit-entry extent.
        initializer = _strip_origin(initializers[0])
        if initializer.get("kind") == "BinaryOperator" and any(
                n.get("kind") == "DeclRefExpr" and not _pointer(n)
                for n in _walk(initializer)):
            return None
        return self.get(initializers[0], function, (*seen, key))


def _origin_base(node):
    children = [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]
    if node.get("kind") == "UnaryOperator" and node.get("opcode") == "&" and children:
        return _origin_base(children[0])
    return next((n for n in children if _pointer(n)), None)


def complete(sites, definitions, observed, *, external_calls=(), known_pointer_calls=(),
             global_nodes=(), known_origins=None, terminal=None, entry_windows=None, entry_function=None, owner=None,
             call_sites=(), call_policies=None, audited_imports=None):
    """Refuse source operations omitted by printing and untracked subobject origins.

    The printer owns normalizations. This independent closure walk ensures that
    wrapper expressions cannot hide an operation from that inventory. Pointer
    casts and array subobjects need a typed extent policy beyond block bounds.
    """
    all_rows = [dict(row) for row in sites]
    # Clang dumps for separate functions may reuse process-local AST IDs.
    by_node = {(row["function"], row.pop("_ast_id", None)): row for row in all_rows}
    rows = [row for row in all_rows if row.get("kind") != "access"]
    if owner:
        # The closed source grammar certifies each alias/member observation.
        # Its independent C-view checker maps these to renamed range/liveness
        # assertions; generic source-name guards cannot be emitted in that view.
        from swdb import model_domains, vector_ownership
        if owner.get("check") != model_domains.identity() or owner.get("owner_check") != vector_ownership.identity():
            raise Refused("closed-owner source registry has stale policy bytes")
        root = definitions.get(owner.get("function"))
        if root is None:
            raise Refused("closed-owner source registry has no emitted source definition")
        for access in owner["source_accesses"]:
            try:
                model_domains.bind_source_access(root, owner, access)
            except model_domains.Refused as exc:
                raise Refused(str(exc)) from None
            rows.append({"function": owner["function"], "source_line": None, "admission_only": True,
                         "reason": "", "owner_access": access,
                         "owner_certificate_sha256": owner["certificate_sha256"]})
    from swdb import dx_array_domains
    candidates, producers, call_rows = {}, {}, {(s["function"], s["_ast_id"]): s for s in call_sites}
    for function, root in definitions.items():
        for node in _walk(root):
            if node.get("kind") != "CallExpr" or not node.get("inner"):
                continue
            names = [(n.get("referencedDecl") or {}).get("name") for n in _walk(node["inner"][0])]
            name = next((name for name in names if name in (call_policies or {}) or name in (known_origins or {})
                         or name in (audited_imports or {})), None)
            if name is None:
                continue
            key = (function, node.get("id"))
            site = call_rows.get(key)
            try:
                if not site or site.get("reason") or not site.get("binding"):
                    raise Refused((site or {}).get("reason") or "DX100 call has no checked source placement/binding")
                if name in (audited_imports or {}):
                    check_import_signature(site["binding"], audited_imports[name])
                    rows.append({**{k: v for k, v in site.items() if not k.startswith("_")},
                                 "kind": "import", "admission_only": True, "call": name,
                                 "import_policy": audited_imports[name]})
                if site.get("producer"):
                    origin = (known_origins or {}).get(name)
                    if (not origin or site["binding"]["summary"] != origin["policy"]["entry"] or
                            re.sub(r"\s+", "", site["binding"]["signature"]) != "int*(int)"):
                        raise Refused("DX100 tile producer has no canonical imported int-row binding")
                    producers[key] = origin
                    rows.append({**{k: v for k, v in site.items() if not k.startswith("_")},
                                 "kind": "producer", "admission_only": True, "call": name, "origin": origin})
                    continue
                if name not in (call_policies or {}):
                    if any(_pointer(arg) for arg in node.get("inner", [])[1:]):
                        raise Refused("DX100 pointer query/region call needs its own checked footprint policy")
                    continue
                candidate = dx_array_domains.candidate(node, call_policies[name])
                binding = site["binding"]
                if binding["name"] != name or binding["summary"] != candidate["policy"]["model"]["entry"]:
                    raise Refused("DX100 call imported binding and exact semantics policy differ")
                candidates[key] = candidate
            except (Refused, dx_array_domains.Refused) as exc:
                rows.append({"function": function, "source_line": (site or {}).get("source_line"), "reason": str(exc)})
    origins = _Origins(definitions, global_nodes, known_origins, terminal, entry_windows, entry_function,
                       set(candidates) | set(producers), producers)
    if call_sites:
        declarations = [n for root in definitions.values() for n in _walk(root)
                        if n.get("kind") in {"VarDecl", "ParmVarDecl"}]
        declarations += list(global_nodes)
        if any(str(n.get("name", "")).startswith(("dx_", "DX_")) for n in declarations):
            rows.append({"function": entry_function, "source_line": None,
                         "reason": "source declarations shadow the reserved DX100 proof-state namespace"})
    for key, candidate in candidates.items():
        site = call_rows[key]
        try:
            origin = origins.get(candidate["pointer_argument"], key[0])
            record = dx_array_domains.certify(candidate, origin, site)
            rows.append({**record, "binding": site["binding"], "kind": "call", "reason": ""})
        except (Refused, dx_array_domains.Refused) as exc:
            rows.append({"function": key[0], "source_line": site["source_line"], "reason": str(exc)})
    has_arithmetic = bool(rows)
    external = {row.get("name") if isinstance(row, dict) else row for row in external_calls}
    for function, root in definitions.items():
        if function == entry_function and entry_windows:
            names = set(entry_windows.get("windows", {})) | {name for w in entry_windows.get("windows", {}).values() for name in w["parameters"]}
            params = {n.get("name"): n for n in root.get("inner", []) if n.get("kind") == "ParmVarDecl"}
            for name in entry_windows.get("windows", {}):
                if name not in params or not _pointer(params[name]) or (function, params[name].get("id")) in origins.unstable:
                    rows.append({"function": function, "source_line": None, "reason": "entry-window pointer binding is not a stable primitive source parameter"})
            if any(n.get("kind") == "VarDecl" and n.get("name") in names for n in _walk(root)):
                rows.append({"function": function, "source_line": None, "reason": "entry-window parameter shadowing needs captured collision-free names"})
        addressed = set()
        for parent in _walk(root):
            if parent.get("kind") == "UnaryOperator" and parent.get("opcode") == "&" and parent.get("inner"):
                addressed.add(_strip_origin(parent["inner"][0]).get("id"))
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
            dereferenced = bool(entry_windows and entry_windows.get("windows") and kind == "UnaryOperator" and node.get("opcode") == "*")
            if (entry_windows and entry_windows.get("windows") and kind in {"CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"}
                    and any(_pointer(c) for c in children[1:]) and (function, node.get("id")) not in candidates):
                reason = "entry-window pointer call boundaries need checked callee-domain discharge"
            if operation or indexed or dereferenced:
                base = _origin_base(node)
                try:
                    origin = origins.get(base, function) if base is not None else None
                except Refused as exc:
                    origin, reason = None, str(exc)
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
                    if origin.get("kind") == "entry_window":
                        try:
                            target = _window_target(node, origin)
                            row["window_guard"] = f'0 <= ({target}) <= ({origin["elements"]})'
                        except Refused as exc:
                            reason = str(exc)
                elif (indexed or dereferenced) and origin.get("kind") == "entry_window":
                    access = by_node.get((function, node.get("id")))
                    if access is None or access.get("kind") != "access":
                        reason = "entry-window access was not captured at a checked source statement"
                    elif dereferenced and node.get("id") in addressed:
                        reason = "entry-window address-of indirection needs a checked cancellation policy"
                    else:
                        try:
                            target = _window_target(node, origin)
                            relation = "<=" if node.get("id") in addressed else "<"
                            access["origin"] = origin
                            access["window_guard"] = f'0 <= ({target}) {relation} ({origin["elements"]})'
                            rows.append(access)
                        except Refused as exc:
                            reason = str(exc)
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


def site(node, *, expression, base, statement, anchor, function, line, reason="", offset=None, literal_offset=None):
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
    span = _statement_span(statement)
    return {"function": function, "anchor": anchor, "source_line": line, "source_statement": span, "base": base,
            "expression": expression, "offset": offset, "literal_offset": literal_offset, "reason": reason,
            "normalized_expression": normalize(expression, base, offset, literal_offset) if not reason else None, "_ast_id": node.get("id")}


def access_site(node, *, expression, statement, anchor, function, line):
    """Pure access at a statement entry; legacy whole-object accesses keep RTE."""
    reason = ""
    if statement is None or statement.get("kind") not in {"DeclStmt", "ReturnStmt", "BinaryOperator",
            "CStyleCastExpr", "CXXStaticCastExpr", "ParenExpr", "ImplicitCastExpr"}:
        reason = "entry-window access needs a precise statement check placement"
    if statement is not None:
        nodes = list(_walk(statement))
        for n in nodes:
            kind, op = n.get("kind"), n.get("opcode")
            if (kind in {"CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr", "ConditionalOperator", "BinaryConditionalOperator", "CompoundAssignOperator"}
                    or kind == "UnaryOperator" and op in {"++", "--"}
                    or kind == "BinaryOperator" and (op in {",", "&&", "||"} or op == "=" and n is not statement)
                    or "volatile" in str((n.get("type") or {}).get("qualType", ""))):
                reason = "entry-window access with side effects/conditional evaluation needs single-evaluation support"
        declared = {n.get("id") for n in nodes if n.get("kind") == "VarDecl"}
        if any((n.get("referencedDecl") or {}).get("id") in declared for n in _walk(node)):
            reason = "entry-window access depends on a declaration inside its statement"
    return {"function": function, "source_line": line, "source_statement": _statement_span(statement), "anchor": anchor, "kind": "access",
            "expression": expression, "reason": reason, "_ast_id": node.get("id")}


def normalize(expression, base, offset, literal_offset=None):
    if offset is None:
        return expression
    if type(literal_offset) is int:
        return f"({base})" if literal_offset == 0 else expression
    return f"(({offset}) == 0 ? ({base}) : ({expression}))"


def _statement_span(statement):
    try:
        begin, end = _span(statement or {})
        return {"begin": begin, "end": end}
    except Refused:
        return None


def function_entries(definitions, source):
    """Original main-source byte spans; macros/headers grant no position."""
    entries = {}
    for name, node in definitions.items():
        bodies = [c for c in node.get("inner", []) if c.get("kind") == "CompoundStmt"]
        if len(bodies) != 1:
            continue
        body = bodies[0]
        start = (body.get("range") or {}).get("begin") or {}
        if start.get("_file", start.get("file")) != str(source):
            continue
        try:
            begin, end = _span(body)
            definition_begin, definition_end = _span(node)
            entries[name] = {"body_begin": begin, "body_end": end,
                             "begin": definition_begin, "end": definition_end}
        except Refused:
            pass
    return entries


def inventory(sites, *, source_sha256, text, entry_windows=None, entry_contract=None, owner=None, source_entries=None):
    report = {"check": identity(), "source_sha256": source_sha256,
              "lowering_sha256": hashlib.sha256(text.encode()).hexdigest(), "sites": list(sites),
              "source_functions": source_entries or {},
              "domain_boundary": "Only certified whole one-dimensional arrays, exact audited semantic rows and terminal typed allocations; "
                                 "incoming arithmetic/indexing requires a pinned explicit entry-window contract and checked numerical bounds; "
                                 "opaque origins remain unsupported; exact C++ null-plus-zero is checked."}
    if entry_windows and entry_windows.get("windows"):
        report["entry_windows"], report["entry_contract"] = entry_windows, entry_contract
        report["entry_window_semantics"] = {
            "role": "explicit typed-array-window input-contract premise; not inferred from validity",
            "checked": "entry extent nonnegative/target byte capacity/null-empty; numerical operation bounds; ordinary RTE",
            "smoke_scope": "projected ACSL preconditions; no complete typed-domain/formal realizability proof",
            "caller_boundary": "imported domain-bearing summaries and unmodeled pointer calls are refused"}
    if owner:
        report["owner"] = owner
    report["certificate_sha256"] = _hash(report)
    return report


def check(lowering):
    report = dict(getattr(lowering, "pointer_bounds", {}) or {})
    digest = report.pop("certificate_sha256", None)
    if (not report or digest != _hash(report) or report.get("check") != identity()
            or report.get("source_sha256") != lowering.source_sha256
            or report.get("lowering_sha256") != hashlib.sha256(lowering.text.encode()).hexdigest()):
        raise Refused("pointer formation inventory is absent, stale or differs from its generated lowering")
    if report.get("entry_windows"):
        from swdb import array_domains
        if report["entry_windows"].get("check") != array_domains.identity() or not report.get("entry_contract"):
            raise Refused("entry-window declaration/check/contract pin is absent or stale")
    if report.get("owner"):
        from swdb import model_domains, vector_ownership
        owner = dict(report["owner"])
        owner_digest = owner.pop("certificate_sha256", None)
        if (owner_digest != _hash(owner) or owner.get("check") != model_domains.identity()
                or owner.get("owner_check") != vector_ownership.identity()
                or owner.get("source_sha256") != lowering.source_sha256
                or owner.get("lowering_sha256") != report["lowering_sha256"]):
            raise Refused("closed-owner source registry is absent, stale or changed")
    for row in report["sites"]:
        if row["reason"]:
            raise Refused(f"{row['function']}:{row['source_line']}: {row['reason']}")
        if row.get("admission_only"):
            continue
        if row.get("kind") == "call":
            from swdb import dx_array_domains
            if row["policy"].get("check") != dx_array_domains.identity() or not row.get("predicate") or not row.get("binding"):
                raise Refused("DX100 source-call guard/binding is missing or stale")
            continue
        if row.get("kind") == "access":
            if not row.get("window_guard") or row["expression"] not in lowering.text:
                raise Refused("entry-window access differs from its generated lowering")
            continue
        normalized = normalize(row["expression"], row["base"], row.get("offset"), row.get("literal_offset"))
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
    if report.get("entry_windows"):
        clauses = []
        for i, (name, window) in enumerate(report["entry_windows"]["windows"].items(), 1):
            extent = window["entry_acsl"]
            predicate = (f'0 <= ({extent}) <= SIZE_MAX / sizeof({window["element_type"]}) && '
                         f'(\\at({name},Pre) == \\null ==> ({extent}) == 0)')
            clauses.append(f'/*@ assert swdb_window_entry_{i}: {predicate}; */')
        additions[f"{lowering.function}.entry"] = clauses
    for i, row in enumerate(report["sites"], 1):
        if row.get("admission_only"):
            continue
        if row.get("kind") == "call":
            additions.setdefault(row["anchor"], []).append(f'/*@ assert swdb_window_call_{i}: {row["predicate"]}; */')
            continue
        if row.get("kind") == "access":
            assertion = f'/*@ assert swdb_window_access_{i}: {row["window_guard"]}; */'
            additions.setdefault(row["anchor"], []).append(assertion)
            continue
        base, result = f"({row['base']})", f"({row['expression']})"
        predicate = f"{_in_object_or_one_past(base, base)} && {_in_object_or_one_past(result, base)}"
        if row.get("offset") is not None:
            predicate = f"(({base} == \\null && ({row['offset']}) == 0) || ({predicate}))"
        if row.get("null_only"):
            predicate = f"{base} == \\null && ({row['offset']}) == 0"
        if row.get("window_guard"):
            predicate = f'({row["window_guard"]}) && ({predicate})'
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
    for assertion in re.findall(r"/\*@ assert swdb_(?:pointer_formation|window_).*?\*/", generated, re.S):
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
