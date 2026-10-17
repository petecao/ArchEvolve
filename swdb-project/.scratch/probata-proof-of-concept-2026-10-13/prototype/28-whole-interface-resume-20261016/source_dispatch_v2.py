"""2026-10-16 ET. Compiler-bound source dispatch and pointer bridge preparation.

Pure stdlib. This is a consumer/emitter, never a compiler or admission producer.
Every actual call is freshly rebound by the pinned V3 binder supplied by the
root-owned integration. User code never receives a builder/callback/private ABI.
Owned MMIO semantics are the accepted premise; the remaining producer seams are
full TU/ABI, source expression staging and complete CPU pointer instrumentation.
"""
import hashlib
import json
from pathlib import Path
import re


BINDER_SHA = "074b974f4a4dd1074247a90d2a727d1cb0ee37b576055d738dd746fd6d4cc1db"
C_TYPES = ("uint32_t", "int32_t", "float", "uint64_t", "int64_t", "double")
TYPE_SUFFIX = ("u32", "i32", "f32", "u64", "i64", "f64")
WIDTH = (4, 4, 4, 8, 8, 8)
U64_MAX = 2**64 - 1
# Exact identity-MMIO profile of the pinned DXS backend and MAA_gem5.hpp:71-91.
MMIO_BEGIN = 17179869184
MMIO_END = MMIO_BEGIN + 8 * 32 * 16384 + 4 * 32 + 4 * 32 + 24


class Refused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def identifier(value):
    need(isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value)
         and not value.startswith(("dws_", "dwi_", "dxw_", "dxm_", "dxc_")), "owned staged identifier required")
    return value


def prepare_atlas(objects, *, cells=256):
    """Bind all ordinary scalar views before assigning shared physical cells.

    The source producer owns object lifetime/provenance and guest→physical
    projection. Partial aliases of exactly the same dtype share cell IDs. Mixed
    width or mixed dtype overlapping views refuse: current ordinary storage is a
    typed scalar cell, unlike the byte-coherent tile/register storage.
    Registration grants no initializedness, value, ownership or history event.
    """
    need(type(cells) is int and 1 <= cells <= 256 and isinstance(objects, list) and objects,
         "bounded nonempty ordinary object atlas required")
    units, checked, identities = {}, [], set()
    for row in objects:
        need(isinstance(row, dict) and set(row) == {"object_id", "guest_base", "physical_base", "extent", "dtype", "source_pin"},
             "exact source object fields required")
        identity = row["object_id"]
        need(isinstance(identity, str) and identity and identity not in identities, "unique source object identity required")
        identities.add(identity)
        dtype, extent = row["dtype"], row["extent"]
        need(type(dtype) is int and 0 <= dtype < 6 and type(extent) is int and 1 <= extent <= cells,
             "bounded exact ordinary scalar type/extent required")
        pin = row["source_pin"]
        need(isinstance(pin, str) and re.fullmatch("[0-9a-f]{64}", pin), "object compiler/source certificate pin required")
        width = WIDTH[dtype]
        for key in ("guest_base", "physical_base"):
            base = row[key]
            need(type(base) is int and 0 <= base <= U64_MAX - extent * width and base % width == 0,
                 "aligned nonwrapping complete source object projection required")
            need(base + extent * width <= MMIO_BEGIN or MMIO_END <= base,
                 "ordinary object overlaps modeled MMIO storage")
        for prior in checked:
            overlap = row["guest_base"] < prior["guest_base"] + prior["extent"] * WIDTH[prior["dtype"]] and prior["guest_base"] < row["guest_base"] + extent * width
            need(not overlap or (dtype == prior["dtype"] and row["physical_base"] - row["guest_base"] == prior["physical_base"] - prior["guest_base"]),
                 "same guest bytes have inconsistent physical/type projection")
        for lane in range(extent):
            begin = row["physical_base"] + lane * width
            unit = (begin, begin + width, dtype)
            for prior in units:
                need(not (begin < prior[1] and prior[0] < begin + width) or prior == unit,
                     "mixed-width/type ordinary alias view refused")
            units[unit] = None
        checked.append(dict(row))
    need(len(units) <= cells, "ordinary cell capacity")
    numbering = {unit: index for index, unit in enumerate(sorted(units))}
    result = []
    for row in checked:
        width = WIDTH[row["dtype"]]
        ids = [numbering[(row["physical_base"] + i * width, row["physical_base"] + (i + 1) * width, row["dtype"])]
               for i in range(row["extent"])]
        need(ids == list(range(ids[0], ids[0] + row["extent"])), "ordinary view cell mapping must be contiguous")
        result.append({**row, "base_cell": ids[0], "cell_ids": ids})
    return {"schema": "source-ordinary-cell-atlas-1", "objects": result,
            "cells": [{"cell": numbering[unit], "physical_begin": unit[0], "physical_end": unit[1], "dtype": unit[2]}
                      for unit in sorted(units)],
            "mmio_excluded_span": [MMIO_BEGIN, MMIO_END],
            "initialization_granted": False, "history_events_added": 0,
            "owned_premises": ["source object identity/lifetime", "guest→physical projection", "complete CPU-access instrumentation"],
            "public_admission": False}


def bind_dispatch(api, tu, *, binding, staged_arguments, thread, **source):
    """Fresh actual-TU binding → fixed C route with typed staged arguments.

    Each argument must carry the hash of its exact compiler subtree. A source
    lowerer must stage the original expression once under its ordinary C++
    evaluation/undefinedness rules. Identifiers prevent code injection; hashes
    bind attribution but cannot prove expression lowering. No arbitrary callback
    or precomputed numeric argument substitutes for the actual expression.
    """
    origin = Path(api["__file__"])
    need(hashlib.sha256(origin.read_bytes()).hexdigest() == BINDER_SHA, "exact independently reviewed V3 binder required")
    fresh = api["recheck_binding"](binding, tu, **source)
    plan = api["dispatch_plan"](fresh, source["declarations"], source["abi"])
    # Locate the exact already-bound call again; no name-only traversal succeeds.
    matches = []
    def walk(node, owner=None):
        if node.get("kind") == "FunctionDecl": owner = node
        if node.get("kind") == "CallExpr" and owner and owner.get("mangledName") == fresh["caller_mangled"]:
            if api["_span"](node) == fresh["call_range"]: matches.append(node)
        for child in node.get("inner", []):
            if isinstance(child, dict): walk(child, owner)
    walk(tu)
    need(len(matches) == 1, "fresh bound call disappeared")
    arguments = matches[0]["inner"][1:]
    need(isinstance(staged_arguments, list) and len(staged_arguments) == len(arguments), "one staged value for every effective argument required")
    rows = [row for row in source["declarations"] if row["name"] == fresh["name"] and row["formal_arity"] == fresh["formal_arity"] and row["declaration"] == fresh["source_declaration"]]
    need(len(rows) == 1, "source defaults require one exact declaration")
    actual = []
    for index, (node, staged, parameter) in enumerate(zip(arguments, staged_arguments, plan["source_arguments"])):
        need(isinstance(staged, dict) and set(staged) == {"index", "ast_sha256", "identifier", "model_type"}
             and staged["index"] == index and type(staged["index"]) is int
             and staged["ast_sha256"] == digest(node), "staged argument attribution differs")
        expected = "pointer-descriptor" if "*" in parameter["source_type"] else "exact-scalar"
        need(staged["model_type"] == expected, "source pointer/scalar lowering differs")
        value = identifier(staged["identifier"])
        if node.get("kind") == "CXXDefaultArgExpr":
            default = rows[0]["parameters"][index]["default"]
            need(type(default) is int and default == -1, "unhandled exact source default")
            value = "-1"
        actual.append(value)
    route = "dws_get_data_type_other" if fresh["name"] == "get_data_type" and fresh["dtype"] == 6 else "dws_" + fresh["c_name"]
    expression = route + "(" + ", ".join([identifier(thread), *actual]) + ")"
    return {"binding": fresh, "dispatch_plan": plan, "model_expression": expression,
        "staged_arguments": staged_arguments, "owned_thread_identifier": thread,
        "binder_sha256": BINDER_SHA, "expression_staging_tcb": True,
        "source_pointer_return": fresh["name"] in ("get_cacheable_tile_pointer", "get_noncacheable_tile_pointer"),
        "public_admission": False}


def render_pointer_bridge(atlas, *, page_bytes=4096, line_bytes=64):
    need(type(page_bytes) is int and type(line_bytes) is int and 1 <= line_bytes <= page_bytes <= 2**30
         and page_bytes % line_bytes == 0 and line_bytes & (line_bytes - 1) == 0,
         "owned source page/cache-line geometry required")
    need(isinstance(atlas, dict) and atlas.get("schema") == "source-ordinary-cell-atlas-1"
         and atlas == prepare_atlas([{k: row[k] for k in ("object_id", "guest_base", "physical_base", "extent", "dtype", "source_pin")}
                                    for row in atlas["objects"]]), "fresh source atlas required")
    rows = ["  {UINT64_C(%d),UINT64_C(%d),%du,%du,%du}" %
            (row["guest_base"], row["physical_base"], row["extent"], row["base_cell"], row["dtype"]) for row in atlas["objects"]]
    source = r'''/*2026-10-16 ET. PRIVATE source pointer bridge; no host pointer casts.
 * Include exact value backend/adapters/builders/closed routes first.
 * Only the compiler-owned lowering may construct or inspect these descriptors.
 * Object/source/provenance/geometry and complete access instrumentation are TCB.
 */
#ifndef SWDB_DX_SOURCE_POINTER_BRIDGE_V1_H
#define SWDB_DX_SOURCE_POINTER_BRIDGE_V1_H
#if defined(__cplusplus)
static_assert(sizeof(float)==4 && sizeof(double)==8,"source scalar representation ABI");
#else
_Static_assert(sizeof(float)==4 && sizeof(double)==8,"source scalar representation ABI");
#endif
struct dws_object {uint64_t guest,physical;unsigned extent,base_cell,dtype;};
static const struct dws_object dws_objects[] = {
__OBJECTS__
};
struct dws_pointer {unsigned kind,object,tile,dtype;uint64_t offset;};
static struct dws_pointer dws_object_pointer(unsigned object) {
  DXM_CHECK(object<sizeof(dws_objects)/sizeof(dws_objects[0]),"source-object-domain");
  struct dws_pointer p={1,object,0,dws_objects[object].dtype,0};return p;
}
static uint64_t dws_pointer_bytes(struct dws_pointer p) {
  DXM_CHECK(p.dtype<6,"source-pointer-type");unsigned bytes=dxp_width(p.dtype);
  if(p.kind==1) {
    DXM_CHECK(p.object<sizeof(dws_objects)/sizeof(dws_objects[0]),"source-object-domain");
    const struct dws_object *o=&dws_objects[p.object];
    DXM_CHECK(p.dtype==o->dtype && o->base_cell<DXM_CELLS && o->extent<=DXM_CELLS-o->base_cell,"source-cell-binding");
    uint64_t span=(uint64_t)o->extent*bytes;
    uint64_t begin=DXS_SOURCE_MEMORY;
    uint64_t end=begin+UINT64_C(8)*DXS_SOURCE_TILES*DXS_SOURCE_WORDS+UINT64_C(4)*DXS_SOURCE_TILES+UINT64_C(4)*DXS_SOURCE_REGS+24;
    DXM_CHECK(DXS_SOURCE_MEMORY==UINT64_C(17179869184) && DXS_SOURCE_TILES==32 && DXS_SOURCE_REGS==32 && DXS_SOURCE_WORDS==16384,"source-mmio-profile");
    DXM_CHECK(o->guest<=UINT64_MAX-span && o->physical<=UINT64_MAX-span,"source-object-overflow");
    DXM_CHECK((o->guest+span<=begin || end<=o->guest) && (o->physical+span<=begin || end<=o->physical),"ordinary-mmio-alias-refused");
    return span;
  }
  DXM_CHECK(p.kind==2 || p.kind==3,"source-pointer-domain");
  dxm_tile_halves(p.tile,bytes);return (uint64_t)DXP_VALUE_BOUND*bytes;
}
static struct dws_pointer dws_pointer_offset(struct dws_pointer p,int64_t elements) {
  uint64_t total=dws_pointer_bytes(p),bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<=total && p.offset%bytes==0,"source-pointer-formation");
  if(elements>=0) {
    uint64_t n=(uint64_t)elements;DXM_CHECK(n<=(total-p.offset)/bytes,"source-pointer-formation");p.offset+=n*bytes;
  } else {
    uint64_t n=(uint64_t)(-(elements+1))+1;DXM_CHECK(n<=p.offset/bytes,"source-pointer-formation");p.offset-=n*bytes;
  }
  return p;
}
static uint64_t dws_guest_address(struct dws_pointer p) {
  uint64_t total=dws_pointer_bytes(p);DXM_CHECK(p.offset<=total,"source-pointer-formation");
  if(p.kind==1) return dws_objects[p.object].guest+p.offset;
  return dwi_tile_address(p.dtype,p.tile,p.kind==3)+p.offset;
}
static struct dws_pointer dws_tile_pointer(unsigned dtype,int tile,unsigned noncacheable) {
  DXM_CHECK(tile>=0 && noncacheable<=1,"source-tile-pointer-domain");
  (void)dwi_tile_address(dtype,(unsigned)tile,noncacheable);
  struct dws_pointer p={noncacheable?3u:2u,0,(unsigned)tile,dtype,0};return p;
}
static uint64_t dws_cpu_read_bits(unsigned thread,struct dws_pointer p,int64_t index) {
  p=dws_pointer_offset(p,index);uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<total,"source-one-past-dereference");
  if(p.kind==1) {
    const struct dws_object *o=&dws_objects[p.object];uint64_t physical=o->physical+p.offset;
    return dxc_cpu_read(thread,o->base_cell+(unsigned)(p.offset/bytes),physical,physical+bytes);
  }
  DXM_CHECK(p.kind==2,"noncacheable-cpu-access-outside-source-policy");
  return dxp_cpu_read_bits(thread,p.tile,(unsigned)(p.offset/bytes),p.dtype);
}
static void dws_cpu_write_bits(unsigned thread,struct dws_pointer p,int64_t index,uint64_t bits) {
  p=dws_pointer_offset(p,index);uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<total,"source-one-past-dereference");
  DXM_CHECK(bytes==8 || bits<=UINT32_MAX,"source-scalar-representation");
  if(p.kind==1) {
    const struct dws_object *o=&dws_objects[p.object];uint64_t physical=o->physical+p.offset;
    dxc_cpu_write(thread,o->base_cell+(unsigned)(p.offset/bytes),physical,physical+bytes,bits);return;
  }
  DXM_CHECK(p.kind==2,"noncacheable-cpu-access-outside-source-policy");
  dxp_cpu_write_bits(thread,p.tile,(unsigned)(p.offset/bytes),p.dtype,bits);
}
static void dws_memory_view(struct dws_pointer p,unsigned dtype,struct dwi_footprint *f,struct dxw_memory *m) {
  uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(dtype);
  DXM_CHECK(p.kind==1 && p.dtype==dtype && p.offset<total && p.offset%bytes==0,"source-array-pointer-binding");
  const struct dws_object *o=&dws_objects[p.object];
  m->base_cell=o->base_cell+(unsigned)(p.offset/bytes);m->extent=o->extent-(unsigned)(p.offset/bytes);
  m->source_base=o->guest+p.offset;m->source_page_bytes=__PAGE_BYTES__u;
  f->source_base=m->source_base;f->logical_begin=m->source_base;f->logical_end=o->guest+total;
  f->physical_begin=o->physical+p.offset;f->physical_end=o->physical+total;f->line_bytes=__LINE_BYTES__u;
  /* Conservative whole remaining object envelope. Never evaluates a deferred
   * index or RF bound at issue and never grants a source region assignment. */
}
struct dws_print_event {unsigned tile,lane,dtype;uint64_t bits;};
#ifndef DWS_PRINT_EVENTS
#define DWS_PRINT_EVENTS 64
#endif
static struct dws_print_event dws_print_events[DWS_PRINT_EVENTS];
static unsigned dws_print_count;
static void dws_print_record(unsigned tile,unsigned lane,unsigned dtype,uint64_t bits,void *context) {
  (void)context;DXM_CHECK(dws_print_count<DWS_PRINT_EVENTS,"source-print-trace-capacity");
  struct dws_print_event *event=&dws_print_events[dws_print_count++];
  event->tile=tile;event->lane=lane;event->dtype=dtype;event->bits=bits;
}
__TYPED_HELPERS__
#endif
'''
    typed = []
    for dtype, (ctype, suffix, width) in enumerate(zip(C_TYPES, TYPE_SUFFIX, WIDTH)):
        bits = "uint32_t" if width == 4 else "uint64_t"
        typed += [f"static uint64_t dws_pack_{suffix}({ctype} value) {{ {bits} bits=0;memcpy(&bits,&value,{width});return bits; }}",
                  f"static {ctype} dws_unpack_{suffix}(uint64_t raw) {{ {bits} bits=({bits})raw;{ctype} value;memcpy(&value,&bits,{width});return value; }}",
                  f"static {ctype} dws_cpu_load_{suffix}(unsigned thread,struct dws_pointer p,int64_t index) {{DXM_CHECK(p.dtype=={dtype}u,\"source-pointer-type\");return dws_unpack_{suffix}(dws_cpu_read_bits(thread,p,index));}}",
                  f"static void dws_cpu_store_{suffix}(unsigned thread,struct dws_pointer p,int64_t index,{ctype} value) {{DXM_CHECK(p.dtype=={dtype}u,\"source-pointer-type\");dws_cpu_write_bits(thread,p,index,dws_pack_{suffix}(value));}}"]
    return source.replace("__OBJECTS__", ",\n".join(rows)).replace("__PAGE_BYTES__", str(page_bytes)).replace(
        "__LINE_BYTES__", str(line_bytes)).replace("__TYPED_HELPERS__", "\n".join(typed))


def render_routes(api, declarations, abi):
    """132 exact six-type source signatures → closed private calls.

    Emitted pointer parameters/returns are descriptors. Production source type
    lowering must use those only for source-certified modeled pointers and route
    every use through the pointer bridge; opaque casts/escapes refuse.
    """
    api["validate_abi"](abi)
    need(hashlib.sha256(Path(api["__file__"]).read_bytes()).hexdigest() == BINDER_SHA, "exact independently reviewed V3 binder required")
    need(declarations and declarations == api["inventory"](Path(declarations[0]["header_path"]).parents[4]), "fresh exact source inventory required")
    functions, contracts = [], []
    for row in declarations:
        for dtype in range(6) if row["template"] else (None,):
            canonical = abi["canonical_types"][api["TYPE_KEYS"][dtype]] if dtype is not None else None
            cname = row["name"]
            if canonical:
                cname += "_" + re.sub(r"\s+", "_", re.sub(r"\s*\*", " ptr", canonical.strip()))
                if len({r["formal_arity"] for r in declarations if r["name"] == row["name"]}) > 1:
                    cname += "_args" + str(row["formal_arity"])
            ctype = C_TYPES[dtype] if dtype is not None else None
            def source_type(value):
                value = value.replace("volatile ", "").strip()
                if "*" in value: return "struct dws_pointer"
                if value.replace("volatile ", "").strip() == "T1": return ctype
                if value == "Operation_t": return "int"
                need(value in ("void", "int", "uint16_t", "DataType"), "unhandled source scalar signature")
                return "unsigned" if value == "DataType" else value
            parameters = ["unsigned thread"] + [source_type(p["type"]) + " " + p["name"] for p in row["parameters"]]
            result = source_type(row["returns"])
            args = [p["name"] for p in row["parameters"]]
            name = row["name"]
            prelude = ["(void)thread;"]
            if "packet" in row:
                if row["packet"]["memory_access"]:
                    prelude += ["struct dwi_footprint footprint;struct dxw_memory mapping;",
                                f"dws_memory_view(data,{dtype}u,&footprint,&mapping);"]
                    args = ["dws_guest_address(data)" if p["name"] == "data" else p["name"] for p in row["parameters"]]
                    call = f"dws_fixed_{name}(" + ",".join(["thread", str(dtype) + "u", *args, "&footprint", "&mapping"]) + ")"
                else:
                    call = f"dws_fixed_{name}(" + ",".join(["thread", str(dtype) + "u", *args]) + ")"
                body = "(void)" + call + ";"
            elif name in ("alloc_MAA", "init_MAA", "clear_mem_region"):
                body = "dwi_" + name + "();"
            elif name == "add_mem_region": body = "dwi_add_mem_region(dws_guest_address(start),dws_guest_address(end));"
            elif name in ("get_cacheable_tile_pointer", "get_noncacheable_tile_pointer"):
                body = f"return dws_tile_pointer({dtype}u,SPD_id,{int(name == 'get_noncacheable_tile_pointer')}u);"
            elif name == "get_data_type": body = f"return dwi_get_data_type({dtype}u);"
            elif name == "wait_ready":
                body = 'DXM_CHECK(SPD_id>=0,"source-tile-domain");dwi_wait_ready((unsigned)SPD_id);'
            elif name == "get_tile_size":
                body = 'DXM_CHECK(SPD_id>=0,"source-tile-domain");return dwi_get_tile_size((unsigned)SPD_id);'
            elif name == "get_new_tile": body = f"return (int)dwi_get_new_tile(thread,{dtype}u);"
            elif name == "get_new_reg":
                body = f"return (int)dwi_get_new_reg_initialized(thread,{dtype}u,dws_pack_{TYPE_SUFFIX[dtype]}(data));" if args else f"return (int)dwi_get_new_reg(thread,{dtype}u);"
            elif name == "get_reg":
                body = f'DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_{TYPE_SUFFIX[dtype]}(dwi_get_reg(thread,{dtype}u,(unsigned)reg_id));'
            elif name == "set_reg":
                body = f'DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,{dtype}u,(unsigned)reg_id,dws_pack_{TYPE_SUFFIX[dtype]}(data));'
            elif name == "maa_const":
                body = f'DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,{dtype}u,dws_pack_{TYPE_SUFFIX[dtype]}(data),(unsigned)dst_reg);'
            elif name == "print_tile":
                body = f'DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,{dtype}u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,{dtype}u),0);'
            else: raise Refused("no closed route: " + name)
            functions.append(f"/* {row['file']}:{row['line']} {row['body_sha256']} */\nstatic {result} dws_{cname}(" + ",".join(parameters) + ") {" + "".join(prelude) + body + "}")
            contracts.append({"name": name, "formal_arity": row["formal_arity"], "dtype": dtype, "canonical_type": canonical,
                "c_name": "dws_" + cname, "source_header_sha256": row["header_sha256"], "body_sha256": row["body_sha256"],
                "source_line": row["line"], "fixed_route": "dws_fixed_" + name if "packet" in row else "dwi_" + name,
                "model_result_type": result, "pointer_descriptor_abi": True, "public_admission": False})
    need(len(functions) == 132 and len({row["c_name"] for row in contracts}) == 132, "complete distinct exact source route census")
    functions.append("static unsigned dws_get_data_type_other(unsigned thread) {(void)thread;return dwi_get_data_type(6);}")
    return "/*2026-10-16 ET. PRIVATE closed source-call routes. */\n#ifndef SWDB_DX_SOURCE_ROUTES_V1_H\n#define SWDB_DX_SOURCE_ROUTES_V1_H\n" + "\n".join(functions) + "\n#endif\n", contracts


def render_direct_families(api, declarations):
    """Specialize exact source operands into direct prepare→family→bind calls.

    The private native86 packet remains unchanged. These source-only routes
    remove its fixed function-pointer forwarding seam from the prospective
    public call graph without weakening preparation or per-family value checks.
    """
    need(hashlib.sha256(Path(api["__file__"]).read_bytes()).hexdigest() == BINDER_SHA, "exact independently reviewed V3 binder required")
    need(declarations and declarations == api["inventory"](Path(declarations[0]["header_path"]).parents[4]), "fresh exact source inventory required")
    fields = ("src1", "src2", "dst1", "dst2", "rdst1", "rdst2", "rsrc1", "rsrc2", "rsrc3", "condition")
    result = ["/*2026-10-16 ET. PRIVATE direct family specializations, no callback ABI. */",
              "#ifndef SWDB_DX_SOURCE_DIRECT_FAMILIES_V1_H", "#define SWDB_DX_SOURCE_DIRECT_FAMILIES_V1_H"]
    for row in declarations:
        if "packet" not in row: continue
        packet = row["packet"];opcode = packet["opcode"];memory = bool(packet["memory_access"])
        family = "dxw_stream" if opcode <= 1 else "dxw_indirect" if opcode <= 6 else "dxw_range" if opcode == 7 else "dxw_alu"
        parameters = ["unsigned thread", "unsigned dtype"] + [
            ("uint64_t" if "*" in p["type"] else "int") + " " + p["name"] for p in row["parameters"]]
        if memory: parameters += ["const struct dwi_footprint *footprint", "const struct dxw_memory *mapping"]
        body = []
        for role, operand in packet["operands"].items():
            if operand is not None:
                body.append(f'DXM_CHECK({operand["parameter"]}>={-1 if operand["optional"] else 0},"source-{role}-operand-domain");')
        if memory: body.append('DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");')
        elif opcode == 7: body.append("dtype=1;")
        operands = ",".join(packet["operands"][role]["parameter"] if packet["operands"][role] is not None else "-1" for role in fields)
        op = packet["operation"] or "255"
        foot = "footprint" if memory else "0"
        context = "(void *)mapping" if memory else "0"
        body += ["struct dwi_packet packet={" + operands + "};",
                 f"unsigned command=dwi_prepare_packet(thread,{opcode}u,dtype,{op},&packet,{foot});",
                 f"unsigned root={family}(command,{opcode}u,dtype,{op},&packet,{foot},{context});",
                 'DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;']
        result.append(f"/* {row['file']}:{row['line']} {row['body_sha256']} */\nstatic unsigned dws_fixed_{row['name']}(" + ",".join(parameters) + ") {" + "".join(body) + "}")
    result.append("#endif")
    return "\n".join(result) + "\n"
