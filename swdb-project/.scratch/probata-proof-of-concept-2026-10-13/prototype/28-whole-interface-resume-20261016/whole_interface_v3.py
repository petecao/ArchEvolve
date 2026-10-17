"""2026-10-16 ET. Closed source-call preparation, never public admission.

The input is normalized full-TU compiler metadata from a separately admitted
producer. No compiler/project imports or tool discovery occur here. A returned
binding selects a private model adapter; it does not authorize substitution.
Source/model/MMIO correspondence is an explicit owned premise. Value builders,
pointer-access instrumentation and the final source replay remain separate gates.
"""
import hashlib
import json
from pathlib import Path
import re


COMMIT = "e4fc4afdf894f295442cef3604667a469fab8e62"
HEADER_PINS = {
    "MAA.hpp": "4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd",
    "MAA_gem5.hpp": "5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174",
}
TYPE_KEYS = ("uint32_t", "int32_t", "float", "uint64_t", "int64_t", "double")
PACKET_SLOTS = {56: "src1", 48: "src2", 40: "rdst1", 32: "rdst2",
                24: "rsrc1", 16: "rsrc2", 8: "rsrc3", 0: "condition"}
OPCODES = {"STREAM_LD": 0, "STREAM_ST": 1, "INDIR_LD": 2,
           "INDIR_ST_SCALAR": 3, "INDIR_ST_VECTOR": 4,
           "INDIR_RMW_SCALAR": 5, "INDIR_RMW_VECTOR": 6,
           "RANGE_LOOP": 7, "ALU_SCALAR": 8, "ALU_VECTOR": 9, "ALU_REDUCE": 10}
MEMORY = {0: 1, 1: 2, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2}
PREMISES = {
    "mmio": "Owned MMIO/event correspondence: these exact header calls have the modeled effects on normal return; no termination claim.",
    "source": "The admitted compiler binds the actual global source declaration, template identity and ABI; final replay must recheck the complete source closure.",
    "state": "Entry metadata/payload/ownership describe the actual receiver state; alloc/init do not create a fresh zero device.",
    "addresses": "Explicit C-object/guest/physical-line mapping, first region/F2, full-line no-interference and bounds are call-site obligations.",
    "numeric": "Exact numeric runtime profile/guards apply to active values; IEEE bit semantics are not replaced by real arithmetic.",
    "deferred": "Consumers capture immutable size/value versions; history chooses at cover, and a known value is not command completion.",
}


class Refused(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _need(condition, message):
    if not condition:
        raise Refused(message)


def _parameters(text):
    if text.strip() in ("", "void"):
        return []
    result = []
    for raw in text.split(","):
        match = re.fullmatch(r"\s*(.*?)\b([A-Za-z_]\w*)\s*(?:=\s*(-1))?\s*", raw)
        _need(match is not None and match[1].strip(), "noncanonical parameter")
        result.append({"type": match[1].strip(), "name": match[2],
                       "default": int(match[3]) if match[3] is not None else None})
    _need(len({row["name"] for row in result}) == len(result), "duplicate parameter")
    return result


def _packet(expression):
    expression = re.sub(r"//[^\n]*|/\*.*?\*/", "", expression, flags=re.S)
    result = {}
    for term in expression.split("|"):
        shift = re.search(r"<<\s*([0-9]+)\s*\)*\s*$", term)
        at = int(shift[1]) if shift else 0
        value = term[:shift.start()] if shift else term
        value = re.sub(r"\(uint64_t\)", "", value).strip().strip("() ")
        _need(at not in result, "duplicate packet field")
        result[at] = value
    return result


def inventory(project):
    """Read exactly the pinned two headers and retained declaration inventory."""
    project = Path(project).resolve()
    directory = project / "apps/dx100/benchmarks/API"
    texts = {}
    for name, expected in HEADER_PINS.items():
        data = (directory / name).read_bytes()
        _need(digest(data) == expected, "pinned interface changed: " + name)
        texts[name] = data.decode()
    index = project / "tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json"
    data = index.read_bytes()
    _need(digest(data) == "d48a3971f2e9421e736d72ff160074f22e9cbbb7c9c756ef52457a5c4314b3b6", "declaration inventory changed")
    rows = json.loads(data)["declarations"]
    result = []
    for row in rows:
        text = texts[row["file"]]
        lines = text.splitlines(keepends=True)
        declaration = row["declaration"]
        _need(lines[row["line"] - 1].strip() == declaration + " {", "declaration source line differs")
        start = sum(map(len, lines[:row["line"] - 1]))
        body_start = text.index("{", start)
        # These pinned bodies have no braces in literals/comments. Their hashes
        # close that parser domain; this is not a general C++ parser.
        depth, end = 1, body_start + 1
        while depth:
            _need(end < len(text), "unclosed pinned function")
            depth += (text[end] == "{") - (text[end] == "}")
            end += 1
        match = re.fullmatch(r"(?:inline\s+)?(.*?)\b" + row["name"] + r"\((.*)\)", declaration)
        _need(match is not None, "declaration grammar")
        params = _parameters(match[2])
        templated = row["line"] > 1 and lines[row["line"] - 2].strip() == "template <class T1>"
        body = text[body_start:end]
        record = {**row, "header_path": str(directory / row["file"]),
                  "header_sha256": HEADER_PINS[row["file"]], "source_range": [start, end],
                  "body_sha256": digest(body.encode()), "line_end": text.count("\n", 0, end) + 1,
                  "template": templated, "returns": match[1].strip(), "parameters": params,
                  "formal_arity": len(params), "minimum_arity": sum(p["default"] is None for p in params)}
        assignments = dict(re.findall(r"\*(INSTR_[A-Za-z0-9_]+)\s*=\s*(.*?);", body, re.S))
        if assignments:
            first = _packet(assignments["INSTR_opcode_datatype_optype_tdst1_tdst2"])
            second = _packet(assignments["INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc"])
            _need(set(first) == {32, 24, 16, 8, 0} and set(second) == set(PACKET_SLOTS), "packet fields")
            opcode = first[32].removeprefix("OpcodeType::")
            _need(opcode in OPCODES, "unknown exact packet opcode")
            datatype = re.search(r"DataType data_type\s*=\s*(.*?);", body)
            _need(first[24] == "data_type" and datatype is not None
                  and datatype[1] in ("DataType::INT32_TYPE", "get_data_type<T1>()"), "exact source datatype selection")
            fields = {PACKET_SLOTS[at]: value for at, value in second.items()}
            fields.update(dst1=first[8], dst2=first[0])
            operands = {}
            for role, expression in fields.items():
                if expression == "NA_UINT8":
                    operands[role] = None
                    continue
                conditional = re.fullmatch(r"([A-Za-z_]\w*)\s*==\s*-1\s*\?\s*NA_UINT8\s*:\s*\1", expression)
                name = conditional[1] if conditional else expression
                _need(name in {p["name"] for p in params}, "operand is not a source parameter")
                operands[role] = {"parameter": name, "optional": conditional is not None}
            record["packet"] = {"opcode": OPCODES[opcode], "opcode_name": opcode,
                                "dtype": "int32_t" if datatype[1] == "DataType::INT32_TYPE" else "T1",
                                "operation": None if first[16] == "NA_UINT8" else first[16],
                                "operands": operands, "memory_access": MEMORY.get(OPCODES[opcode], 0),
                                "base_parameter": "data" if OPCODES[opcode] in MEMORY else None}
        result.append(record)
    _need(len(result) == 27 and len({r["name"] for r in result}) == 26, "complete declaration coverage")
    _need(len([r for r in result if "packet" in r]) == 11, "complete packet family coverage")
    return result


def validate_abi(abi):
    """Validate shape only; the root binds observations to its admitted compiler."""
    _need(isinstance(abi, dict) and abi.get("byte_order") == "little" and abi.get("int_bits") == 32
          and abi.get("pointer_bits") == 64, "explicit source ABI required")
    types = abi.get("canonical_types")
    _need(isinstance(types, dict) and set(types) == set(TYPE_KEYS), "six actual typedef identities required")
    _need(all(isinstance(t, str) and re.fullmatch(r"[a-z]+(?: [a-z]+)*", t) for t in types.values())
          and len(set(types.values())) == 6, "unambiguous canonical scalar identities required")
    _need(types["float"] == "float" and types["double"] == "double", "floating identities differ")
    _need(types["uint32_t"] == "unsigned int" and types["int32_t"] == "int"
          and types["uint64_t"] in ("unsigned long", "unsigned long long")
          and types["int64_t"] == types["uint64_t"].removeprefix("unsigned "), "selected Mac/Linux integer identity domain")
    alignments = abi.get("alignments")
    _need(isinstance(alignments, list) and len(alignments) == 6
          and all(type(a) is int and a in (1, 2, 4, 8) for a in alignments), "six source alignments required")
    _need(abi.get("sizes") == [4, 4, 4, 8, 8, 8], "six source scalar sizes required")
    return abi


def _type_tokens(text):
    tokens = re.findall(r"[A-Za-z_]\w*|\*|&|\(|\)|,|::", text)
    _need("".join(tokens) == re.sub(r"\s+", "", text), "unsupported function type tokens")
    return tokens


def signature(record, canonical_type=None):
    replace = lambda text: re.sub(r"\bT1\b", canonical_type or "T1", text)
    return replace(record["returns"]) + " (" + ", ".join(replace(p["type"]) for p in record["parameters"]) + ")"


def _span(node):
    begin, end = (node.get("range", {}).get(key, {}) for key in ("begin", "end"))
    _need(not any(key in point for point in (begin, end) for key in ("spellingLoc", "expansionLoc")), "macro coordinates refused")
    _need(all(type(point.get("offset")) is int and point["offset"] >= 0 for point in (begin, end))
          and type(end.get("tokLen")) is int and end["tokLen"] > 0, "direct compiler spans required")
    return [begin["offset"], end["offset"] + end["tokLen"]]


def bind_call(tu, *, caller, call_range, source_path, source_text, declarations, abi):
    """Bind one actual same-TU source call. No body/name-only bypass exists.

    Normalized locations must retain `_file` (or explicit `file`) on declaration
    and caller locs. Existing compiler location normalization supplies this data.
    The complete original source/probe/compiler closure is a root-owned input.
    """
    validate_abi(abi)
    _need(isinstance(declarations, list) and declarations, "closed source inventory required")
    origin = Path(declarations[0]["header_path"]).parents[4]
    _need(declarations == inventory(origin), "source declaration registry is not freshly source-derived")
    _need(Path(source_path).is_file() and Path(source_path).read_text() == source_text, "actual caller source changed")
    _need(source_text.isascii(), "this preparation slice requires ASCII byte-offset source")
    _need(isinstance(call_range, list) and len(call_range) == 2
          and all(type(value) is int for value in call_range)
          and 0 <= call_range[0] < call_range[1] <= len(source_text), "call span is outside the original source")
    _need(tu.get("kind") == "TranslationUnitDecl", "one complete TU required")
    functions, contexts, calls = {}, {}, []
    def walk(node, namespace=(), owner=None, parent=None):
        kind = node.get("kind")
        if kind in ("NamespaceDecl", "CXXRecordDecl", "RecordDecl"):
            namespace += ((kind, node.get("name", "")),)
        if kind == "FunctionDecl":
            identity = node.get("id")
            _need(isinstance(identity, str) and identity, "declaration ID required")
            _need(identity not in functions or functions[identity] == node, "ambiguous full-TU declaration ID")
            functions[identity], contexts[identity] = node, namespace
            owner = node
        if kind == "CallExpr" and owner is not None and owner.get("mangledName") == caller and _span(node) == call_range:
            calls.append((node, owner, parent))
        for child in node.get("inner", []):
            if isinstance(child, dict):
                walk(child, namespace, owner, node)
    walk(tu)
    _need(len(calls) == 1, "source call does not resolve uniquely in its actual TU/caller")
    call, owner, parent = calls[0]
    loc = owner.get("loc", {})
    _need(loc.get("_file", loc.get("file")) == str(Path(source_path).resolve()), "caller source identity differs")
    children = call.get("inner", [])
    _need(children, "callee expression missing")
    callee = children[0]
    if callee.get("kind") == "ImplicitCastExpr" and callee.get("castKind") == "FunctionToPointerDecay":
        _need(len(callee.get("inner", [])) == 1, "callee decay shape")
        callee = callee["inner"][0]
    reference = callee.get("referencedDecl", {})
    _need(callee.get("kind") == "DeclRefExpr" and reference.get("id") in functions, "direct bound callee required")
    decl = functions[reference["id"]]
    name = decl.get("name")
    _need(reference.get("name") == name and not contexts[reference["id"]]
          and decl.get("storageClass") != "static", "global actual source callee required")
    _need(not any(c.get("kind", "").endswith("Attr") for c in decl.get("inner", [])), "unreviewed callee attributes")
    loc = decl.get("loc", {})
    candidates = [r for r in declarations if r["name"] == name and r["line"] == loc.get("line")
                  and loc.get("_file", loc.get("file")) == r["header_path"]]
    _need(len(candidates) == 1, "actual declaration is not the pinned header definition")
    record = candidates[0]
    _need("packet" not in record or parent is not None and parent.get("kind") == "CompoundStmt", "packet calls require a standalone source statement")
    _need(_span(decl) == record["source_range"]
          and any(c.get("kind") == "CompoundStmt" for c in decl.get("inner", [])), "exact pinned header body span required")
    params = [c for c in decl.get("inner", []) if c.get("kind") == "ParmVarDecl"]
    _need(len(params) == record["formal_arity"], "resolved declaration arity differs")
    arguments = children[1:]
    def pure(node):
        kind, op = node.get("kind"), node.get("opcode")
        arities = {
            "IntegerLiteral": (0,), "FloatingLiteral": (0,), "CharacterLiteral": (0,),
            "CXXBoolLiteralExpr": (0,), "CXXNullPtrLiteralExpr": (0,), "GNUNullExpr": (0,),
            "DeclRefExpr": (0,), "CXXDefaultArgExpr": (0,),
            "ParenExpr": (1,), "ConstantExpr": (1,), "UnaryOperator": (1,),
            "ImplicitCastExpr": (1,), "CStyleCastExpr": (1,), "CXXStaticCastExpr": (1,),
            "CXXFunctionalCastExpr": (1,), "CXXReinterpretCastExpr": (1,),
            "MemberExpr": (1,), "ArraySubscriptExpr": (2,), "BinaryOperator": (2,),
        }
        _need(kind in arities, "source argument expression is outside the closed pure grammar")
        children = node.get("inner", [])
        _need(isinstance(children, list) and all(isinstance(c, dict) for c in children)
              and len(children) in arities[kind], "source argument expression arity differs")
        actual_type = node.get("type", {})
        _need(isinstance(actual_type, dict), "source argument type metadata differs")
        for spelling in ("qualType", "desugaredQualType"):
            value = actual_type.get(spelling, "")
            _need(isinstance(value, str) and "volatile" not in value, "volatile source argument refused")
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
        for child in children:
            pure(child)
    for argument in arguments:
        pure(argument)
    _need(len(arguments) == record["formal_arity"], "compiler must retain all effective/default arguments")
    explicit = sum(arg.get("kind") != "CXXDefaultArgExpr" for arg in arguments)
    _need(record["minimum_arity"] <= explicit <= record["formal_arity"]
          and all(arg.get("kind") == "CXXDefaultArgExpr" for arg in arguments[explicit:]), "default argument placement differs")
    template = [c for c in decl.get("inner", []) if c.get("kind") == "TemplateArgument"]
    _need(len(template) == int(record["template"]), "exact template/type arity required")
    canonical = None
    dtype = None
    if template:
        typ = template[0].get("type", {})
        canonical = typ.get("desugaredQualType", typ.get("qualType"))
        _need(isinstance(canonical, str) and canonical, "actual canonical template type missing")
        dtype = next((i for i, key in enumerate(TYPE_KEYS) if abi["canonical_types"][key] == canonical), 6)
        _need(dtype < 6 or name == "get_data_type", "unsupported exact source type; widths never substitute for type identity")
    _need(_type_tokens(decl.get("type", {}).get("qualType", "")) == _type_tokens(signature(record, canonical)), "actual instantiated source signature differs")
    cname = name
    if template:
        cname += "_" + re.sub(r"\s+", "_", re.sub(r"\s*\*", " ptr", canonical.strip()))
        if len({r["formal_arity"] for r in declarations if r["name"] == name}) > 1:
            cname += "_args" + str(record["formal_arity"])
    return {"name": name, "formal_arity": record["formal_arity"], "explicit_arity": explicit,
            "dtype": dtype, "effective_dtype": 1 if record.get("packet", {}).get("dtype") == "int32_t" else dtype,
            "canonical_type": canonical, "c_name": cname, "source_sha256": digest(source_text.encode()),
            "source_path": str(Path(source_path).resolve()), "call_range": list(call_range),
            "caller_mangled": caller, "callee_id": decl["id"], "header_sha256": record["header_sha256"],
            "header_body_sha256": record["body_sha256"], "source_declaration": record["declaration"],
            "full_tu_metadata_sha256": digest(json.dumps(tu, sort_keys=True, separators=(",", ":")).encode()),
            "abi_sha256": digest(json.dumps(abi, sort_keys=True, separators=(",", ":")).encode()),
            "private_adapter": "dwi_" + name + ("_initialized" if name == "get_new_reg" and explicit else ""),
            "admission": "PREPARATION_ONLY; original source replay and owned per-call model premise required"}


def recheck_binding(expected, *args, **kwargs):
    fresh = bind_call(*args, **kwargs)
    _need(fresh == expected, "actual source/type/arity binding changed before model dispatch")
    return fresh


def dispatch_plan(binding, declarations, abi):
    """Describe the private ABI after successful bind/recheck, never admit it.

    Argument indexes refer to effective compiler arguments (including defaults).
    Scalar conversions are bit copies; pointer projections require independently
    bound C-object, guest-address and physical-envelope observations.
    """
    validate_abi(abi)
    _need(binding.get("abi_sha256") == digest(json.dumps(abi, sort_keys=True, separators=(",", ":")).encode()),
          "dispatch ABI differs from source binding")
    selected = [r for r in declarations if r["name"] == binding.get("name")
                and r["formal_arity"] == binding.get("formal_arity")
                and r["declaration"] == binding.get("source_declaration")
                and r["header_sha256"] == binding.get("header_sha256")
                and r["body_sha256"] == binding.get("header_body_sha256")]
    _need(len(selected) == 1, "dispatch must use the exact bound source declaration")
    row, name, dtype = selected[0], binding["name"], binding["dtype"]
    canonical = binding["canonical_type"]
    source = [{"index": i, "name": p["name"], "source_type": re.sub(r"\bT1\b", canonical or "T1", p["type"]),
               "conversion": "C-object/guest/physical projection" if "*" in p["type"] else
                             "exact typed object-representation bit copy" if p["type"] == "T1" else "same checked scalar value"}
              for i, p in enumerate(row["parameters"])]
    arg = lambda index: {"effective_source_argument": index, "conversion": source[index]["conversion"]}
    thread, typed = {"owned_thread": True}, {"bound_dtype": dtype}
    routes = {
        "alloc_MAA": [], "init_MAA": [], "clear_mem_region": [],
        "add_mem_region": [arg(0), arg(1)] if name == "add_mem_region" else [],
        "wait_ready": [arg(0)] if name == "wait_ready" else [],
        "get_tile_size": [arg(0)] if name == "get_tile_size" else [],
        "get_data_type": [typed], "get_new_tile": [thread, typed],
        "get_new_reg": [thread, typed] + ([arg(0)] if row["formal_arity"] else []),
        "get_reg": [thread, typed, arg(0)] if name == "get_reg" else [],
        "set_reg": [thread, typed, arg(0), arg(1)] if name == "set_reg" else [],
        "maa_const": [thread, typed, arg(0), arg(1)] if name == "maa_const" else [],
        "get_cacheable_tile_pointer": [typed, arg(0)] if name == "get_cacheable_tile_pointer" else [],
        "get_noncacheable_tile_pointer": [typed, arg(0)] if name == "get_noncacheable_tile_pointer" else [],
        "print_tile": [thread, typed, arg(0), {"owned_print_observer": True}, {"owned_context": True}] if name == "print_tile" else [],
    }
    if "packet" in row:
        operands = [thread, typed] + [arg(i) for i in range(row["formal_arity"])]
        operands += [{"closed_footprint": "required" if row["packet"]["memory_access"] else "null"},
                     {"closed_source_bound_family_builder": name}, {"owned_context": True}]
    else:
        operands = routes[name]
    result = "same scalar value"
    if name == "get_reg":
        result = "raw object-representation bits copied into exact bound canonical scalar type"
    elif name in ("get_cacheable_tile_pointer", "get_noncacheable_tile_pointer"):
        result = "modeled guest address; compiler-bound pointer provenance/access instrumentation still required"
    return {"name": name, "c_name": binding["c_name"], "private_adapter": binding["private_adapter"],
            "source_arguments": source, "private_arguments_in_order": operands, "result_conversion": result,
            "binding_recheck_required": True, "public_admission": False}


def project_operands(record, dtype, arguments, *, operation=None, tiles=32, registers=32):
    """Literal source roles, physical widths and counted roles remain distinct."""
    _need(type(dtype) is int and 0 <= dtype < 6 and type(tiles) is int and 1 <= tiles <= 64
          and type(registers) is int and 1 <= registers <= 64, "typed geometry domain")
    packet = record.get("packet")
    _need(packet is not None, "not a packet declaration")
    opcode = packet["opcode"]
    dtype = 1 if opcode == 7 else dtype
    if packet["operation"]:
        _need(type(operation) is int and 0 <= operation <= 15, "source opcode16/NE has no admitted execution branch")
        _need(arguments.get(packet["operation"]) == operation, "operation differs from the actual source operand")
        _need(opcode not in (5, 6) or operation in (0, 4, 5), "RMW opcode domain")
        _need(opcode != 10 or operation <= (5 if dtype in (2, 5) else 7), "reduction initializer domain")
        _need(dtype not in (2, 5) or operation not in range(6, 11), "floating bit/shift domain")
    else:
        _need(operation is None, "unexpected operation parameter")
    masks = {kind: 0 for kind in ("tile_explicit_read", "tile_explicit_write", "tile_physical_read",
             "tile_physical_write", "ready_roles", "register_explicit_read", "register_explicit_write",
             "register_physical_read", "register_physical_write")}
    widths = {}
    for role, binding in packet["operands"].items():
        if binding is None:
            continue
        value = arguments.get(binding["parameter"])
        _need(type(value) is int, "resolved integer operand required")
        if value == -1 and binding["optional"]:
            continue
        is_register = role.startswith("r")
        limit = registers if is_register else tiles
        width = 4 if dtype < 3 else 8
        if role == "condition" or opcode == 7 or role == "src1" and opcode in (2, 3, 4, 5, 6):
            width = 4
        if role == "dst1" and opcode in (8, 9) and operation >= 11:
            width = 4
        if is_register and opcode in (0, 1):
            width = 4  # StreamAccess.cc:143-145 reads signed int RF values.
        _need(0 <= value < limit and width // 4 <= limit - value, "physical pair/ID domain")
        key = ("register" if is_register else "tile", value)
        _need(key not in widths or widths[key] == width, "same starting ID has conflicting source widths")
        widths[key] = width
        physical = ((1 << (width // 4)) - 1) << value
        prefix = "register" if is_register else "tile"
        write = role in ("dst1", "dst2", "rdst1", "rdst2")
        directions = ["write"] if write else ["read"]
        if opcode == 7 and role in ("rdst1", "rdst2"):
            directions.append("read")  # Captured continuation state, not a false dependency stall.
        for direction in directions:
            masks[prefix + "_explicit_" + direction] |= 1 << value
            masks[prefix + "_physical_" + direction] |= physical
        if not is_register and role != "condition":
            masks["ready_roles"] |= physical
    _need(not masks["tile_physical_read"] & masks["tile_physical_write"], "intra-command physical tile alias")
    return {"opcode": opcode, "dtype": dtype, "access": packet["memory_access"],
            "masks": masks, "widths": [{"storage": key[0], "id": key[1], "bytes": value}
                                      for key, value in sorted(widths.items())]}


def contract(record):
    """Owned per-call recipe. Conditions are caller obligations, not new unit premises."""
    name = record["name"]
    recipes = {
        "alloc_MAA": ("dxs_alloc", "Set seven exact MMIO endpoints and replace six built-in regions; do not reset payload, pending commands or allocation counters."),
        "init_MAA": ("dxs_init", "Reset host REG/SPD counters and next region6 only; preserve device payload, pending commands and registrations."),
        "add_mem_region": ("dxs_add_region", "One-sided source overlap rejection, int8 ID conversion and first-ID/F2 lookup; negative/wrapped region domains refuse."),
        "clear_mem_region": ("dxs_clear_regions", "Replace registrations with exact six MMIO intervals, set next region6; no command/payload reset."),
        "get_cacheable_tile_pointer": ("dwi_tile_address", "Return cacheable MMIO base+tile*TILE_SIZE*4; no ownership, readiness, validity or initializedness grant."),
        "get_noncacheable_tile_pointer": ("dwi_tile_address", "Return noncacheable MMIO base+tile*TILE_SIZE*4; later dereference needs its own source access policy."),
        "get_data_type": ("dwi_dtype", "Exact canonical uint32/int32/float/uint64/int64/double identity selects0..5; every other type selectsMAX6."),
        "get_new_tile": ("dxs_new_tile", "Allocate sizeof(T1)/4 physical halves; odd8-byte starts are permitted; preserve data and size versions."),
        "get_new_reg": ("dxg_new_initialized" if record["formal_arity"] else "dxg_new", "Allocate sizeof(T1)/4 physical halves; initialized overload additionally performs the explicit-ID-stalling typed MMIO write; capacity precedes that write as a call obligation."),
        "get_reg": ("dxg_cpu_read_bits", "Observe the typed shared RF byte image after ownership/alignment/pending-write checks; no invented read stall."),
        "set_reg": ("dxg_cpu_write_bits", "Explicit starting-ID write stalls matching pending explicit RF operands, then checks whole physical pair interference and replaces bytes."),
        "maa_const": ("dxg_cpu_write_bits", "Same MMIO RF payload write, without adding the set_reg source fence; owned MMIO ordering premise remains recorded."),
        "wait_ready": ("dxc_wait_tile", "Returned blocking read covers globally counted source/destination roles on this physical half; a condition-only role does not count; no polling/liveness claim."),
        "get_tile_size": ("dxz_get_size", "Read exact starting-tile immutable size only when Finished; no wait/cover, no second-half metadata copy or fresh-zero assumption."),
        "print_tile": ("dwi_print_tile", "Read size without cover, then ordered typed CPU tile reads and explicit observed-output events; preserve IO projection premise."),
        "maa_alu_scalar": ("dwi_maa_alu_scalar", "Capture src tile/size, RF scalar and condition versions; deferred typed binary per active lane; comparisons outputu32; inactive bytes preserved."),
        "maa_alu_vector": ("dwi_maa_alu_vector", "Capture two tile/size versions and condition versions; deferred typed lane binary; comparisons outputu32; inactive bytes preserved."),
        "maa_alu_reduce": ("dwi_maa_alu_reduce", "Source initializer and operand order src OP accumulator; deferred masked fold into RF typed result; no at-issue value evaluation."),
        "maa_stream_load": ("dwi_maa_stream_load", "Capture signed-int RF min/max/stride; checked nonempty source count/prefix; active ordinary-array cells create issue-to-cover history nodes; inactive bytes preserved."),
        "maa_stream_store": ("dwi_maa_stream_store", "Capture signed-int RF bounds/stride and source/condition versions; deferred stores complete under full physical-line guards."),
        "maa_indirect_load": ("dwi_maa_indirect_load", "Capture u32 index/condition and source size versions; checked uint32 offset correspondence and first-ID/F2; active indexed history nodes, inactive bytes preserved."),
        "maa_indirect_store_vector": ("dwi_maa_indirect_store_vector", "Capture u32 indices, typed source and conditions; deferred store actions; optional output is progressively copied line old values, not untouched response data."),
        "maa_indirect_store_scalar": ("dwi_maa_indirect_store_scalar", "Capture u32 indices, typed RF scalar and conditions; deferred store actions with optional old-result output and inactive-byte preservation."),
        "maa_indirect_rmw_vector": ("dwi_maa_indirect_rmw_vector", "Deferred ADD/MIN/MAX with typed vector values and arbitrary permitted action order; old result aliases progressively updated copied line."),
        "maa_indirect_rmw_scalar": ("dwi_maa_indirect_rmw_scalar", "Deferred ADD/MIN/MAX with captured typed RF scalar; old result aliases progressively updated copied line; source numeric guards retained."),
        "maa_range_loop": ("dwi_maa_range_loop", "Header forces INT32 independent of T1; capture two continuation RF states, min/max/condition size/value versions and signed-int stride; both RF states and two tile/size outputs update at deferred cover."),
    }
    adapter, effect = recipes[name]
    domains = ["actual full-TU source/type/arity binding", "all structural bounds/capacities remain checked obligations",
               "per-thread ownership and shared global-instance hazards", "conditional normal return; no added original-unit premise"]
    if "packet" in record:
        domains += ["atomic prepare/capture/build/bind with no intervening source action",
                    "no implicit history settlement to choose a size or address", "condition/size/byte initializedness checked only when selected"]
        if record["packet"]["memory_access"]:
            domains += ["nonempty logical/physical envelope; empty or all-inactive memory calls remain outside this preparation domain",
                        "supplied envelope covers every possible deferred active address; source and physical mappings agree"]
    basis = [{"file": record["file"], "lines": [record["line"], record["line_end"]],
              "role": "exact source declaration/body; owned normal-return MMIO correspondence"}]
    if "packet" in record:
        basis += [{"file": "IF.cc", "lines": [66, 154], "role": "source priority/role widths"},
                  {"file": "IF.cc", "lines": [193, 218], "role": "explicit destination/global-region stalls"},
                  {"file": "MAA.cc", "lines": [563, 580], "role": "counted source/destination roles"},
                  {"file": "SPD.cc", "lines": [120, 138], "role": "both physical halves counted"}]
    if name.startswith("maa_alu_"):
        basis += [{"file": "ALU.cc", "lines": [99, 224], "role": "scalar/reduction initialization and immutable size agreement"},
                  {"file": "ALU.cc", "lines": [266, 861], "role": "six typed operations and final tile/RF outputs"}]
    elif name.startswith("maa_indirect_"):
        basis += [{"file": "IndirectAccess.cc", "lines": [406, 418], "role": "condition/index size agreement"},
                  {"file": "IndirectAccess.cc", "lines": [492, 494], "role": "uint32 product then address addition"},
                  {"file": "IndirectAccess.cc", "lines": [898, 1128], "role": "progressive old values and six typed RMW branches"}]
    elif name.startswith("maa_stream_"):
        basis += [{"file": "StreamAccess.cc", "lines": [143, 146], "role": "signed-int RF bounds and stride"},
                  {"file": "StreamAccess.cc", "lines": [340, 340], "role": "starting-tile result size"}]
    if record.get("packet", {}).get("memory_access") or name in ("add_mem_region", "clear_mem_region", "alloc_MAA"):
        basis += [{"file": "MAA.cc", "lines": [200, 241], "role": "source overlap predicate and first containing region"}]
    return {"call": name, "formal_arity": record["formal_arity"], "adapter": adapter,
            "effect": effect, "domains": domains, "owned_premises": dict(PREMISES),
            "source_basis": basis,
            "source": {"commit": COMMIT, "file": record["file"], "line": record["line"],
                       "end_line": record["line_end"], "header_sha256": record["header_sha256"],
                       "body_sha256": record["body_sha256"]},
            "value_builder": "required separately source-bound family implementation" if "packet" in record else None,
            "public_supported": False}
