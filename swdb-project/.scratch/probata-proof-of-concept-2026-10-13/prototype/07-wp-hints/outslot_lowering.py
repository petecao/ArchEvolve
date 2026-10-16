"""Finite, source-pinned return-ABI rewrite for ticket 07; not a C++ translator.

Only the reviewed hand model is admitted. No input with changed bytes, additional
returning interfaces, indirect calls, exceptions, references, aggregate returns,
varargs or unknown expression contexts is accepted. Original inputs stay intact.
Generated output is prospective and carries no proof acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PINNED = {
    "gapbs_models.h": "eccc1c111f32698043682509be8effad02e8cec82957a889f7a4fb6c54ff490c",
    "tdstep_standin.c": "f24d4fbac9646f3eb28637c591c8cef83a529d96907b1d3071bfadccc3a24de7",
    "bfs_unit.h": "1bcbf4dac683d6a46269fcd5f896fefc2571adc49d059b46f93fb25eb0f7b235",
    "dxc_summaries.h": "d708c0ef974e5ede1aaadd2b5e66dd785affa5e1dc6ef37419bf9e72517ae0d2",
}
RETURNS = {
    "__sync_bool_compare_and_swap_NodeID": "bool",
    "__atomic_load_n_NodeID": "NodeID",
    "__sync_fetch_and_add_size_t": "size_t",
    "swdb_new_NodeID_array": "NodeID *",
    "std_copy_NodeID": "NodeID *",
    "compare_and_swap": "bool", "fetch_and_add_size_t": "size_t",
    "std_min_size_t": "size_t", "omp_get_thread_num": "int",
    **{f"pvector_{t}_{n}": f"{t} *" for t in ("NodeID", "SGOffset")
       for n in ("operator_index", "data", "beginp", "endp")},
    "SlidingQueue_NodeID_beginp": "NodeID *",
    "SlidingQueue_NodeID_endp": "NodeID *", "SlidingQueue_NodeID_size": "size_t",
    "__dxc_tile_size": "uint16_t", "__dxc_tile_pointer": "int *",
}


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"unsupported source/context: expected one {old[:100]!r}")
    return text.replace(old, new, 1)


def interface(text: str, name: str, result_type: str) -> tuple[str, dict]:
    # Finite source recognizer: exact pinned input, simple top-level signatures,
    # and brace-free return expressions. It never guesses at arbitrary C syntax.
    pat = re.compile(r"/\*@(?P<contract>(?:(?!/\*@).)*?)\*/\s*"
                     + re.escape(result_type).replace(r"\ ", r"\s*")
                     + r"\s*" + re.escape(name) + r"\((?P<params>[^()]*)\)\s*(?P<end>[;{])", re.S)
    found = list(pat.finditer(text))
    if len(found) != 1:
        raise ValueError(f"unsupported declaration: {name}: {len(found)}")
    m = found[0]
    contract = m["contract"].replace(r"\result", "(*swdb_out)")
    contract = re.sub(r"assigns\s+([^;]+);", lambda a: "assigns " +
                      ("*swdb_out" if a[1].strip() == r"\nothing" else a[1] + ", *swdb_out") + ";", contract)
    if "assigns " not in contract:
        raise ValueError(f"missing frame: {name}")
    params = m["params"]
    # The out slot is a private caller automatic object. Separation from every
    # source object is a lowering obligation, not a source caller precondition.
    sep = ""
    if "self" in params: sep = r"requires \separated(swdb_out, self);"
    elif "NodeID *ptr" in params or "size_t *ptr" in params:
        sep = r"requires \separated(swdb_out, ptr);"
    elif "NodeID *x" in params or "size_t *x" in params:
        sep = r"requires \separated(swdb_out, x);"
    if name == "std_copy_NodeID":
        sep = r"requires \separated(swdb_out, first + (0 .. swdb_count - 1), d_first + (0 .. swdb_count - 1));"
    if name == "swdb_new_NodeID_array":
        sep = r"requires \separated(swdb_out, swdb_lqueue_storage + (0 .. SWDB_LQUEUE_CAPACITY - 1));"
    if name.startswith("__dxc_"):
        sep = (r"requires \separated(swdb_out, dxc_tile_len + (0 .. DXC_NUM_TILES - 1), "
               r"dxc_tile_data + (0 .. DXC_NUM_TILES - 1), dxc_pending + (0 .. DXC_NUM_TILES - 1));")
    contract = (r" requires \valid(swdb_out); " + sep + "\n" + contract)
    # A procedure has a real typed store: helper bodies must prove this; opaque
    # summaries specify the defined normal-return/store ABI. No pointee init.
    contract += "\n    " + r"ensures \initialized(swdb_out); "
    args = "" if params.strip() == "void" else params.strip() + ", "
    if name == "std_copy_NodeID": args += "size_t swdb_count, "
    signature = f"void {name}_out({args}{result_type} *swdb_out)"
    replacement = "/*@" + contract + "*/\n" + signature + (";" if m["end"] == ";" else " {")
    end = m.end()
    if m["end"] == "{":
        depth, pos = 1, end
        while depth:
            if text[pos] == "{": depth += 1
            elif text[pos] == "}": depth -= 1
            pos += 1
        body = text[end:pos - 1]
        matches = list(re.finditer(r"\breturn\s+([^;]+);", body))
        if len(matches) != 1:
            raise ValueError(f"unsupported body return: {name}")
        body = re.sub(r"\breturn\s+([^;]+);", r"*swdb_out = \1;", body)
        replacement += body + "}"
        end = pos
    row = {"name": name, "result_type": result_type, "new_name": name + "_out",
           "body": m["end"] == "{", "old_contract": m["contract"].strip(),
           "new_contract": contract.strip(), "old_declaration": text[m.start():end],
           "new_declaration": replacement}
    return text[:m.start()] + replacement + text[end:], row


def spans(text: str) -> str:
    text = once(text,
        r"0 <= count <= PTRDIFF_MAX && \object_pointer(base) &&" + "\n    " +
        r"\object_pointer(base + count) && \base_addr(base) == \base_addr(base + count);",
        r"0 <= count <= PTRDIFF_MAX && \object_pointer(base) &&" + "\n    " +
        r"\valid(base + (0 .. count - 1)) && \object_pointer(base + count);" )
    # Source pvector owns one live contiguous typed array. The endpoint witness
    # establishes a representable element difference before any subtraction.
    old = (r"requires \object_pointer(self->start_) && \object_pointer(self->end_size_);" + "\n    " +
           r"requires \base_addr(self->start_) == \base_addr(self->end_size_);" + "\n    " +
           r"requires self->start_ <= self->end_size_;" + "\n    " +
           r"requires \offset(self->end_size_) - \offset(self->start_) <= (integer)PTRDIFF_MAX * sizeof(*self->start_);")
    if text.count(old) != 4: raise ValueError("pvector span census")
    text = text.replace(old, r"requires \exists integer count; gapbs_nodeid_span(self->start_, count) && self->end_size_ == self->start_ + count;")
    old = (r"requires \object_pointer(first) && \object_pointer(last);" + "\n    " +
           r"requires \base_addr(first) == \base_addr(last);" + "\n    " +
           r"requires first <= last;" + "\n    " +
           r"requires \offset(last) - \offset(first) <= (integer)PTRDIFF_MAX * sizeof(NodeID);")
    text = once(text, old, r"requires gapbs_nodeid_span((NodeID *)first, swdb_count);" + "\n    " +
                r"requires last == first + swdb_count;")
    # Only the copy summary uses this difference after the domain rewrite.
    start = text.index("/*@ requires gapbs_nodeid_span((NodeID *)first")
    end = text.index("/* ---- GAPBS members", start)
    text = text[:start] + text[start:end].replace("last - first", "swdb_count") + text[end:]
    return text


def build(source: Path) -> tuple[dict[str, str], dict]:
    # Physical bytes are the admission boundary. Text I/O would normalize CRLF
    # and admit an input whose actual SHA differs from its declared source pin.
    raw = {n: (source / n).read_bytes() for n in PINNED}
    for name, pin in PINNED.items():
        if hashlib.sha256(raw[name]).hexdigest() != pin:
            raise ValueError(f"unsupported changed source: {name}")
    files = {n: value.decode("utf-8", errors="strict") for n, value in raw.items()}
    original = dict(files)
    source_pins = {n: hashlib.sha256(value).hexdigest() for n, value in raw.items()}
    g = spans(files["gapbs_models.h"])
    inventory = []
    for name, typ in RETURNS.items():
        file = "dxc_summaries.h" if name.startswith("__dxc_") else "gapbs_models.h"
        value, row = interface(files[file] if file != "gapbs_models.h" else g, name, typ)
        if file == "gapbs_models.h": g = value
        else: files[file] = value
        row["file"] = file
        inventory.append(row)
    g = once(g, "*swdb_out = __sync_bool_compare_and_swap_NodeID(x, old_val, new_val);",
             "bool swdb_ret_atomic;\n  __sync_bool_compare_and_swap_NodeID_out(x, old_val, new_val, &swdb_ret_atomic);\n  *swdb_out = swdb_ret_atomic;")
    g = once(g, "*swdb_out = __sync_fetch_and_add_size_t(x, inc);",
             "size_t swdb_ret_atomic;\n  __sync_fetch_and_add_size_t_out(x, inc, &swdb_ret_atomic);\n  *swdb_out = swdb_ret_atomic;")
    g = once(g, "self->local_queue = swdb_new_NodeID_array(self->local_size);",
             "NodeID *swdb_ret_alloc;\n  swdb_new_NodeID_array_out(self->local_size, &swdb_ret_alloc);\n  self->local_queue = swdb_ret_alloc;")
    g = once(g, "size_t copy_start = fetch_and_add_size_t(&self->sq->shared_in, self->in);",
             "size_t swdb_ret_fetch;\n  fetch_and_add_size_t_out(&self->sq->shared_in, self->in, &swdb_ret_fetch);\n  size_t copy_start = swdb_ret_fetch;")
    g = once(g, "std_copy_NodeID(self->local_queue, self->local_queue + self->in, shared_queue + copy_start);",
             "NodeID *swdb_ret_copy;\n  std_copy_NodeID_out(self->local_queue, self->local_queue + self->in, shared_queue + copy_start, self->in, &swdb_ret_copy);\n  (void)swdb_ret_copy;")
    files["gapbs_models.h"] = g
    td = lower_td(files["tdstep_standin.c"])
    files["tdstep_standin.c"] = td
    for name in files:
        files[name] = "// Prospective private out-slot ABI, 2026-10-16 ET. Not a proof record.\n" + files[name]
    for row in inventory:
        text = original[row["file"]]
        pos = re.search(r"\b" + re.escape(row["name"]) + r"\s*\(", text).start()
        begin = text.rfind("/*@", 0, pos)
        row["original_contract"] = text[begin + 3:text.index("*/", begin)].strip()
        text = files[row["file"]]
        pos = re.search(r"\b" + re.escape(row["new_name"]) + r"\s*\(", text).start()
        begin = text.rfind("/*@", 0, pos)
        row["new_contract"] = text[begin + 3:text.index("*/", begin)].strip()
        # Contracts are the obligation map; no stale intermediate body is saved.
        row.pop("old_contract")
        row.pop("old_declaration")
        row.pop("new_declaration")
    manifest = {"method": "t07-private-outslot-v1", "source_pins": source_pins,
                "interfaces": inventory, "helper_bodies": 19,
                "returning_helpers": 15, "returning_standard_summaries": 5,
                "returning_device_summaries": 2, "proof_acceptance": False}
    manifest["source_interface_occurrences"] = []
    for filename, content in original.items():
        # Keep line positions while removing comments; capture declarations and
        # calls, explicitly labeled lexical occurrences rather than an AST proof.
        code = re.sub(r"/\*.*?\*/|//[^\n]*", lambda m: "\n" * m[0].count("\n"), content, flags=re.S)
        for name in RETURNS:
            for m in re.finditer(r"\b" + re.escape(name) + r"\s*\(", code):
                line = code[:m.start()].count("\n") + 1
                manifest["source_interface_occurrences"].append({
                    "file": filename, "line": line, "interface": name,
                    "source_line": content.splitlines()[line - 1].strip()})
    manifest["unit_postconditions_sha256"] = hashlib.sha256(
        original["tdstep_standin.c"].split("    ensures visited_parent_unchanged:", 1)[1].split("void TDStep(", 1)[0].encode()).hexdigest()
    manifest["private_slot_rule"] = "Each call receives the address of a fresh automatic scalar/pointer object; never initialized by this rewrite, never passed to a source operation except as its private out cell, never escaped, and consumed after the call. Semantic short-circuit accumulators are separate objects."
    manifest["unsupported"] = ["changed input bytes", "unknown/indirect/variadic calls", "aggregate or reference returns",
                               "exceptions/nonlocal exits", "volatile/atomic object qualifiers not in pinned source",
                               "arbitrary raw-pointer Graph producers", "in-place -m allocator/type-punning path",
                               "full C++/OpenMP/DX100/allocator correspondence", "fresh allocation payload initializedness proof"]
    manifest["allocator_correspondence"] = {
        "status": "REFUSED_PENDING_SEPARATE_REPAIR",
        "reason": "swdb_lqueue_storage has static storage duration and implicit zero initialization; it cannot represent the initial payload initializedness of new NodeID[n]",
        "same_path_negative_closed": False, "TD_or_source_proof_admissible": False,
    }
    return files, manifest


def lower_td(td: str) -> str:
    # This source has exactly these expression contexts. Fresh local slots are
    # never initialized by the lowering; the procedure's typed store defines them.
    for typ, obj, prefix in (("NodeID", "queue", "SlidingQueue_NodeID"),
                             ("SGOffset", "VertexOffsets", "pvector_SGOffset"),
                             ("NodeID", "parent", "pvector_NodeID")):
        td = once(td, f"add_mem_region({prefix}_beginp({obj}), {prefix}_endp({obj}));",
                  f"{{ {typ} *swdb_begin, *swdb_end;\n    {prefix}_beginp_out({obj}, &swdb_begin);\n    {prefix}_endp_out({obj}, &swdb_end);\n    add_mem_region(swdb_begin, swdb_end); }}")
    td = once(td, "const bool accelerate = swdb_acceleration_enabled && SlidingQueue_NodeID_size(queue) >= (size_t)SWDB_FRONTIER_THRESHOLD;",
              "bool accelerate = false;\n    if (swdb_acceleration_enabled) {\n      size_t swdb_size; SlidingQueue_NodeID_size_out(queue, &swdb_size);\n      accelerate = swdb_size >= (size_t)SWDB_FRONTIER_THRESHOLD;\n    }")
    td = once(td, "dxc_context c = swdb_contexts[omp_get_thread_num()];",
              "int swdb_tid; omp_get_thread_num_out(&swdb_tid);\n      dxc_context c = swdb_contexts[swdb_tid];")
    td = once(td, "const size_t end = std_min_size_t(begin + (size_t)SWDB_CHUNK_SIZE, (size_t)queue->shared_out_end);",
              "size_t swdb_end; std_min_size_t_out(begin + (size_t)SWDB_CHUNK_SIZE, (size_t)queue->shared_out_end, &swdb_end);\n        const size_t end = swdb_end;")
    for old, new in (
        ("__dxc_gather(pvector_SGOffset_data(VertexOffsets), c.tile[0], c.tile[1]);",
         "{ SGOffset *swdb_data; pvector_SGOffset_data_out(VertexOffsets, &swdb_data);\n          __dxc_gather(swdb_data, c.tile[0], c.tile[1]); }"),
        ("__dxc_gather(pvector_SGOffset_data(VertexOffsets) + 1, c.tile[0], c.tile[2]);",
         "{ SGOffset *swdb_data; pvector_SGOffset_data_out(VertexOffsets, &swdb_data);\n          __dxc_gather(swdb_data + 1, c.tile[0], c.tile[2]); }"),
        ("__dxc_gather(pvector_NodeID_data(parent), c.tile[0], c.tile[5]);",
         "{ NodeID *swdb_data; pvector_NodeID_data_out(parent, &swdb_data);\n            __dxc_gather(swdb_data, c.tile[0], c.tile[5]); }"),
        ("const unsigned count = __dxc_tile_size(c.tile[7]);",
         "uint16_t swdb_count; __dxc_tile_size_out(c.tile[7], &swdb_count);\n          const unsigned count = swdb_count;"),
    ): td = once(td, old, new)
    for var, tile in (("vertices", 0), ("frontier", 3), ("hints", 5)):
        td = once(td, f"int *{var} = __dxc_tile_pointer(c.tile[{tile}]);",
                  f"int *swdb_{var}; __dxc_tile_pointer_out(c.tile[{tile}], &swdb_{var});\n          int *{var} = swdb_{var};")
    td = once(td, "const bool claimed = hint < 0 && compare_and_swap(pvector_NodeID_operator_index(parent, (size_t)v), hint, u);",
              "bool claimed = false;\n            if (hint < 0) {\n              NodeID *swdb_parent; pvector_NodeID_operator_index_out(parent, (size_t)v, &swdb_parent);\n              bool swdb_claimed; compare_and_swap_out(swdb_parent, hint, u, &swdb_claimed);\n              claimed = swdb_claimed;\n            }")
    # Each store remains independently evaluated at its original sequence point.
    old = "*pvector_NodeID_operator_index(parent, (size_t)v) = u;"
    if td.count(old) != 2: raise ValueError("parent-store census")
    td = td.replace(old, "{ NodeID *swdb_parent; pvector_NodeID_operator_index_out(parent, (size_t)v, &swdb_parent);\n                *swdb_parent = u; }")
    td = once(td, "for (int j = *pvector_SGOffset_operator_index(VertexOffsets, (size_t)u);\n             j < *pvector_SGOffset_operator_index(VertexOffsets, (size_t)(u + 1)); ++j) {",
              "SGOffset *swdb_first; pvector_SGOffset_operator_index_out(VertexOffsets, (size_t)u, &swdb_first);\n        for (int j = *swdb_first; ; ++j) {\n          SGOffset *swdb_last; pvector_SGOffset_operator_index_out(VertexOffsets, (size_t)(u + 1), &swdb_last);\n          if (!(j < *swdb_last)) break;")
    td = once(td, "const NodeID value = __atomic_load_n_NodeID(pvector_NodeID_operator_index(parent, (size_t)v), __ATOMIC_RELAXED);",
              "NodeID *swdb_load_ptr; pvector_NodeID_operator_index_out(parent, (size_t)v, &swdb_load_ptr);\n          NodeID swdb_loaded; __atomic_load_n_NodeID_out(swdb_load_ptr, __ATOMIC_RELAXED, &swdb_loaded);\n          const NodeID value = swdb_loaded;")
    td = once(td, "if (value < 0 && compare_and_swap(pvector_NodeID_operator_index(parent, (size_t)v), value, u)) {",
              "bool swdb_claimed = false;\n          if (value < 0) {\n            NodeID *swdb_cas_ptr; pvector_NodeID_operator_index_out(parent, (size_t)v, &swdb_cas_ptr);\n            bool swdb_result; compare_and_swap_out(swdb_cas_ptr, value, u, &swdb_result);\n            swdb_claimed = swdb_result;\n          }\n          if (swdb_claimed) {")
    for typ, obj in (("SGOffset", "VertexOffsets"), ("NodeID", "parent")):
        old = (rf"\object_pointer({obj}->end_capacity_) &&" + "\n      " +
               rf"\base_addr({obj}->start_) == \base_addr({obj}->end_capacity_) &&" + "\n      " +
               f"{obj}->end_size_ <= {obj}->end_capacity_ &&" + "\n      " +
               rf"\offset({obj}->end_capacity_) - \offset({obj}->start_) <= (integer)PTRDIFF_MAX * sizeof({typ})")
        td = once(td, old,
            rf"(\exists integer cap; gapbs_nodeid_span({obj}->start_, cap) && {obj}->end_capacity_ == {obj}->start_ + cap && {obj}->end_size_ <= {obj}->end_capacity_)")
    # Reject any forgotten old returning-interface call, including device calls.
    for name in RETURNS:
        if re.search(r"\b" + re.escape(name) + r"\s*\(", td):
            raise ValueError(f"unlowered call: {name}")
    return td


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=HERE / "standin")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--refresh-generated", action="store_true",
                   help="replace only an intact prior generated packet")
    p.add_argument("--require-allocator-correspondence", action="store_true",
                   help="fail closed until a separate fresh-allocation repair is reviewed")
    args = p.parse_args()
    files, manifest = build(args.source)
    if args.require_allocator_correspondence:
        raise ValueError("allocator source correspondence pending: static storage is implicitly initialized")
    if args.output.exists():
        if not args.refresh_generated: raise ValueError("output must be absent")
        previous = json.loads((args.output / "abi-map.json").read_text())
        if previous["method"] != manifest["method"] or previous["source_pins"] != manifest["source_pins"]:
            raise ValueError("unrecognized prior output")
        if {p.name for p in args.output.iterdir()} != {*files, "abi-map.json"}:
            raise ValueError("unexpected output entries")
        if set(previous["output_pins"]) != set(files):
            raise ValueError("incomplete prior output pins")
        for name, pin in previous["output_pins"].items():
            if hashlib.sha256((args.output / name).read_bytes()).hexdigest() != pin:
                raise ValueError("edited generated output")
    else:
        args.output.mkdir(parents=True)
    for name, value in files.items(): (args.output / name).write_bytes(value.encode("utf-8"))
    manifest["output_pins"] = {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()}
    (args.output / "abi-map.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
