"""Checked array windows for exact DX100 pointer calls; created 2026-10-15 ET.

The model-state footprint is read at the call site. Nothing here assumes source
bounds, recovers a typed array from validity, or invents a helper entry domain.
The lowering owns AST binding, placement, imported-callee identity and fresh replay.
"""
import hashlib
import re
from pathlib import Path


class Refused(ValueError):
    pass


# The first pointer argument is the host array. All other arguments are int.
ARITIES = {"maa_stream_load": 6, "maa_indirect_load": 4, "maa_indirect_store_vector": 5}


def identity():
    return {"id": "swdb-dx-array-domains-1", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _children(node):
    return [child for child in node.get("inner", []) if isinstance(child, dict) and child.get("kind")]


def _strip(node, *, callee=False):
    while node.get("kind") in {"ParenExpr", "ImplicitCastExpr"} and len(_children(node)) == 1:
        if node.get("kind") == "ImplicitCastExpr" and node.get("castKind") not in (
                {"NoOp", "FunctionToPointerDecay"} if callee else {"NoOp", "LValueToRValue", "ArrayToPointerDecay"}):
            break
        node = _children(node)[0]
    return node


def _policy(policy, call):
    from swdb import bounded_initialization
    model = (policy or {}).get("model") or {}
    if (not isinstance(policy, dict) or policy.get("check") != identity() or policy.get("call") != call
            or call not in ARITIES or model.get("components") != bounded_initialization.DX100_CONTENT
            or call not in model.get("calls", []) or not model.get("tile_objects")
            or any(type(row.get("elements")) is not int or row["elements"] <= 0
                   for row in model.get("tile_objects", []))
            or any(not re.fullmatch(r"[a-f0-9]{64}", str(model.get(key, "")))
                   for key in ("entry_sha256", "generated_sha256"))):
        raise Refused("DX100 pointer call has no exact audited model/entry/geometry policy")


def _scalar(node):
    """Pure int arguments, preserving the actual source conversion boundary."""
    original = str((node.get("type") or {}).get("qualType", ""))
    if "volatile" in original:
        raise Refused("DX100 footprint operands cannot duplicate volatile reads")
    node = _strip(node)
    kind, children = node.get("kind"), _children(node)
    qual = ' '.join(re.sub(r'\bconst\b', '', str((node.get("type") or {}).get("qualType", ""))).split())
    if qual != "int":
        raise Refused("DX100 footprint operands need checked value-preserving int arguments")
    if kind == "IntegerLiteral":
        return str(int(node["value"]))
    if kind == "DeclRefExpr":
        declaration = node.get("referencedDecl") or {}
        name = declaration.get("name", "")
        if declaration.get("kind") in {"VarDecl", "ParmVarDecl"} and re.fullmatch(r"[A-Za-z_]\w*", name):
            return f"((integer){name})"
    if kind == "UnaryOperator" and node.get("opcode") in {"+", "-"} and len(children) == 1:
        return f"({node['opcode']}{_scalar(children[0])})"
    if kind == "BinaryOperator" and node.get("opcode") in {"+", "-", "*"} and len(children) == 2:
        return f"({_scalar(children[0])} {node['opcode']} {_scalar(children[1])})"
    raise Refused("DX100 footprint operands need pure int expressions without calls or mutation")


def candidate(call_node, policy):
    """An ephemeral candidate; only its exact AST ID may avoid pointer escape.

    The caller must additionally bind this callee to the imported external model
    and reject source definitions, unsafe evaluation placement and shadowed names.
    No exemption becomes admissible until certify resolves the stable origin.
    """
    children = _children(call_node)
    callee = _strip(children[0], callee=True) if children else {}
    declaration = callee.get("referencedDecl") or {}
    call = declaration.get("name")
    _policy(policy, call)
    signature = re.sub(r"\s+", "", str((declaration.get("type") or {}).get("qualType", "")))
    expected = "void(int*" + ",int" * (ARITIES[call] - 1) + ")"
    if (call_node.get("kind") != "CallExpr" or callee.get("kind") != "DeclRefExpr"
            or declaration.get("kind") != "FunctionDecl" or signature != expected
            or len(children) != ARITIES[call] + 1 or not call_node.get("id")):
        raise Refused("DX100 footprint needs the canonical directly imported call signature")
    pointer = children[1]
    if re.sub(r"\s+", "", str((pointer.get("type") or {}).get("qualType", ""))) != "int*":
        raise Refused("DX100 host pointer must retain its exact int element type")
    return {"call": call, "scalar_arguments": [_scalar(node) for node in children[2:]],
            "pointer_argument": pointer, "ast_id": call_node["id"], "callee_id": declaration.get("id"),
            "policy": policy}


def certify(candidate, origin, site):
    """Return a persistent call certificate and checked call-prestate predicate.

    First slice: entry windows only. Other origin kinds need their own complete
    offset/root certificate; a missing offset is never interpreted as zero.
    """
    call = candidate.get("call")
    _policy(candidate.get("policy"), call)
    if site.get("reason"):
        raise Refused("DX100 footprint check placement is unsupported: " + site["reason"])
    if (not isinstance(origin, dict) or origin.get("kind") != "entry_window"
            or origin.get("element_type") != "int" or not origin.get("root")
            or not isinstance(origin.get("elements"), str) or not origin["elements"].strip()
            or not isinstance(origin.get("relative_offset"), str) or not origin["relative_offset"].strip()
            or not re.fullmatch(r"[a-f0-9]{64}", str(origin.get("declarations_sha256", "")))):
        raise Refused("DX100 host footprint needs a stable explicit int entry-window origin and exact offset")
    if not site.get("function") or not site.get("anchor"):
        raise Refused("DX100 footprint check placement needs a source function and statement anchor")
    arguments = candidate["scalar_arguments"]
    if len(arguments) != ARITIES[call] - 1:
        raise Refused("DX100 footprint scalar inventory changed after AST planning")
    names = set(re.findall(r"[A-Za-z_]\w*", " ".join([*arguments, origin["elements"], origin["relative_offset"]])))
    index_name = "swdb_dx_window_index"
    while index_name in names:
        index_name += "_"
    extent, offset = f"({origin['elements']})", f"({origin['relative_offset']})"
    prefix = [f"0 <= {extent}", f"0 <= {offset} <= {extent}"]
    if call == "maa_stream_load":
        begin, end, stride, _destination, _condition = arguments
        prefix += [f"0 <= {reg} < DX_NR" for reg in (begin, end, stride)]
        low, high, step = (f"((integer)dx_reg_value[{reg}])" for reg in (begin, end, stride))
        prefix += [f"0 < {step}", f"{low} <= {high}"]
        index = f"({offset} + {low} + {index_name} * {step})"
        selected = f"0 <= {index_name} < DX_TS && {low} + {index_name} * {step} < {high}"
    else:
        index_tile = arguments[0]
        prefix += [f"0 <= {index_tile} < DX_NT", f"0 <= dx_tile_size[{index_tile}] <= DX_TS"]
        selected = f"0 <= {index_name} < dx_tile_size[{index_tile}]"
        if call == "maa_indirect_store_vector":
            condition = arguments[2]
            prefix += [f"({condition} == -1 || 0 <= {condition} < DX_NT)"]
            selected += f" && ({condition} == -1 || dx_tile_data[{condition}][{index_name}] != 0)"
        index = f"({offset} + (integer)(unsigned int)dx_tile_data[{index_tile}][{index_name}])"
    predicate = " && ".join(f"({part})" for part in prefix)
    predicate += f" && (\\forall integer {index_name}; {selected} ==> 0 <= {index} < {extent})"
    return {key: site.get(key) for key in ("function", "anchor", "source_line", "source_range")} | {
        "call": call, "scalar_arguments": list(arguments), "origin": dict(origin),
        "policy": candidate["policy"], "predicate": predicate}


# Exact trusted WP contract for the audited C query: it observes pointer values,
# never reads the pointed-to host cell, writes state or retains a caller pointer.
QUERY_CONTRACT = r"""requires 0 <= tile < DX_NT;
assigns \nothing;
ensures \result == 1 <==> (dx_tile_writer[tile] >= 0 && dx_in_footprint(dx_tile_writer[tile], (int *)addr));"""


def certify_query(node, policy, site):
    """One exact bodyless imported query; pointer formation stays independently checked."""
    from swdb import bounded_initialization
    model = policy.get('model', {})
    children = _children(node)
    callee = _strip(children[0], callee=True) if children else {}
    ref = callee.get('referencedDecl', {})
    if (policy.get('call') != 'swdb_dx_in_footprint' or
            re.sub(r'\s+', '', policy.get('query_contract', '')) != re.sub(r'\s+', '', QUERY_CONTRACT) or
            model.get('components') != bounded_initialization.DX100_CONTENT or
            policy['call'] not in model.get('calls', []) or
            any(not re.fullmatch(r'[a-f0-9]{64}', str(model.get(key, '')))
                for key in ('entry_sha256', 'generated_sha256')) or
            node.get('kind') != 'CallExpr' or len(children) != 3 or
            callee.get('kind') != 'DeclRefExpr' or ref.get('kind') != 'FunctionDecl' or
            ref.get('name') != policy['call'] or
            re.sub(r'\s+', '', ref.get('type', {}).get('qualType', '')) != 'int(int,constint*)' or
            re.sub(r'\s+', '', children[2].get('type', {}).get('qualType', '')) != 'constint*' or
            not site.get('binding')):
        raise Refused('footprint query needs its exact audited read-only pointer-value model and contract')
    # No generated expression is evaluated twice. Keep a deliberately small pure
    # argument grammar, leaving the normal access and formation inventory intact.
    def walk(part):
        yield part
        for child in _children(part):
            yield from walk(child)
    for argument in children[1:]:
        for part in walk(argument):
            kind, op = part.get('kind'), part.get('opcode')
            if (kind.endswith('CallExpr') or kind in {'ConditionalOperator', 'BinaryConditionalOperator',
                    'CompoundAssignOperator', 'CXXNewExpr', 'CXXDeleteExpr', 'CXXThrowExpr'} or
                    kind == 'UnaryOperator' and op in {'++', '--'} or
                    kind == 'BinaryOperator' and op in {'=', ',', '&&', '||'} or
                    'volatile' in part.get('type', {}).get('qualType', '')):
                raise Refused('footprint query arguments require pure single-evaluation source operands')
    tile = _scalar(children[1])
    statement = site.get('_statement') or {}
    parts = _children(statement)
    value = parts[0] if len(parts) == 1 else {}
    if (statement.get('kind') == 'DeclStmt' and value.get('kind') == 'VarDecl' and _qual_type(value) == 'int'
            and not value.get('storageClass') and not value.get('tls') and not value.get('constexpr')
            and not any(n.get('kind', '').endswith('Attr') for n in _children(value))):
        initializers = _children(value)
        value = initializers[0] if len(initializers) == 1 else {}
    elif statement.get('kind') == 'CallExpr':
        value = statement
    elif statement.get('kind') != 'ReturnStmt':
        value = {}
    if _strip(value).get('id') != node.get('id') or not site.get('anchor'):
        raise Refused('footprint query domain needs one unconditional direct call as its entire statement value')
    return {**{k: v for k, v in site.items() if not k.startswith('_')},
            'kind': 'query', 'call': policy['call'], 'admission_only': False,
            '_pointer_argument': children[2], 'tile_argument': tile,
            'reason': '', 'query_policy': policy, 'check': identity(),
            'pointer_effect': 'pointer value observed only; no host dereference, writes or escape'}



def _qual_type(node):
    return ' '.join(node.get('type', {}).get('qualType', '').split())


def query_domain(query, origin):
    """Conservative native/abstract-pointer agreement boundary, as a checked VC.

    Native uintptr comparisons can conflate one-past and an adjacent object.
    Requiring the queried command and address root to share their array object
    excludes that cross-root case, while allowing same-root one-past misses.
    An idle writer has an empty footprint independently of the address.
    """
    if not origin or origin.get('kind') != 'entry_window' or origin.get('element_type') != 'int':
        raise Refused('footprint query domain needs an exact stable int entry-window array-object origin')
    root = origin.get('root')
    if not root or not re.fullmatch(r'[A-Za-z_]\w*', root):
        raise Refused('footprint query root is not a stable primitive source binding')
    tile = query['tile_argument']
    writer = f'dx_tile_writer[{tile}]'
    return {'origin': origin, 'predicate': f'0 <= {tile} < DX_NT && ({writer} < 0 || '
            f'(0 <= {writer} < DX_K && \\base_addr({root}) == \\base_addr(dx_base[{writer}])))',
            'model_domain': 'idle writer or query and pending command share the same array object'}
