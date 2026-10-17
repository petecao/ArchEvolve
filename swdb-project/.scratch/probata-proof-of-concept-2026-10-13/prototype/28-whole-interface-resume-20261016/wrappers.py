"""2026-10-16 ET. Emit private whole-interface adapters; never compile them.

Packet adapters require a separately source-bound deferred value builder. This
closes preparation/capture/bind as one private call without claiming that an
arbitrary callback implements device values. Public substitution remains closed.
"""
import ast
import hashlib
from pathlib import Path


RENDERER_PINS = {
    "numeric_values": "f49ebff7a85a88d93c20c78ad313b67a3459f0620254bba9b3cd91fcbd3ba018",
    "deferred_state": "7dd77d2d5ff38391ab1475d5a0695279ead70fc96ee5a4db4ba17f6679ec9c01",
    "typed_state": "28a2864142ac8575c8eba54033c5a129395162ae446f7892bf34e346ca3525a2",
    "command_state": "e50b667cb0bfe4f25fa01cbdb892f2bac35135073b01b4bf582835c6e7931670",
    "action_state": "4567eba2086c435104f6f280d37096471d86df16e8600771a4cd79f91872028b",
    "region_state": "c80bc03d0045b47fa680a14fd0ca9d42602920e5322337cb4f85d31a9ea9e017",
    "register_state": "52ea1cdac02b843f6eb096b2d520bf8431577af073a66fb99410c62187eca07d",
    "tile_image": "867234cb4f9ee1ba63d614bb1535a0e80e6b07740fb8b341a461651328ac5ac6",
    "size_state": "a68668b6b9eeb60e3e151dec49206854783a4e3f9cbb92b62027c82115ee86e5",
    "setup_state": "ffd98ba40539751783eb7abf5f956a2472851468f42e23895b80628fb42cd8b3",
}


def render_backend(project, *, expected_pins, source_cores=4, source_words=16384, value_bound=2,
                   alignments=(4, 4, 4, 8, 8, 8)):
    """Execute only pinned pure renderer AST; no production/project imports."""
    folder = Path(project) / ".scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics"
    def generator(name):
        path = folder / (name + ".py")
        source = path.read_bytes()
        if not (expected_pins.get(str(path.resolve())) == hashlib.sha256(source).hexdigest() == RENDERER_PINS[name]):
            raise ValueError("renderer source is not frozen: " + name)
        tree = ast.parse(source)
        if any(not isinstance(node, (ast.Expr, ast.Assign, ast.FunctionDef)) for node in tree.body):
            raise ValueError("non-renderer module needs separate review: " + name)
        for node in tree.body:
            if isinstance(node, ast.Expr) and not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                raise ValueError("only module docstrings may execute before rendering")
            if isinstance(node, ast.Assign):
                ast.literal_eval(node.value)
        namespace = {}
        exec(compile(tree, str(path), "exec"), namespace)
        return namespace
    modules = {name: generator(name) for name in (
        "numeric_values", "deferred_state", "typed_state", "command_state", "action_state",
        "region_state", "register_state", "tile_image", "size_state", "setup_state")}
    text = modules["deferred_state"]["render_header"]()
    text = modules["typed_state"]["render_header"](text, modules["numeric_values"]["render_header"]())
    for name in ("command_state", "action_state", "region_state"):
        text = modules[name]["render_header"](text)
    text = modules["register_state"]["render_header"](text, register_words=source_cores * 8,
                                                       alignment_by_dtype=alignments)
    text = modules["tile_image"]["render_header"](text, source_tile_words=source_words,
                    value_bound=value_bound, byte_order="little")
    text = modules["size_state"]["render_header"](text)
    text = modules["setup_state"]["render_header"](text, source_tile_words=source_words, source_cores=source_cores)
    return ("/*2026-10-16 ET. Source-only private composition; fatal hooks required. */\n"
            "#ifndef DXM_CHECK\n#error \"bind classified fatal DXM_CHECK before inclusion\"\n#endif\n"
            "#ifndef DXM_CHOOSE\n#error \"bind bounded independent DXM_CHOOSE before inclusion\"\n#endif\n"
            f"#define DXM_TILES {source_cores * 8}\n#define DXC_REGIONS 256\n" + text)


def render_adapters(declarations):
    prefix = r'''/*2026-10-16 ET. PRIVATE preparation adapters, no public admission.
 * Include after the frozen backend. Never hand candidate code access to these
 * entry points or to a value-builder callback. Owned source/MMIO/ABI premises,
 * source replay and checked per-call value recipes are mandatory integration.
 */
#ifndef SWDB_DX_WHOLE_INTERFACE_PREPARATION_H
#define SWDB_DX_WHOLE_INTERFACE_PREPARATION_H
struct dwi_packet { int src1,src2,dst1,dst2,rdst1,rdst2,rsrc1,rsrc2,rsrc3,condition; };
struct dwi_footprint {
  uint64_t source_base,logical_begin,logical_end,physical_begin,physical_end,line_bytes;
};
struct dwi_roles {
  uint64_t er,ew,pr,pw,ready,re, we,rp,wp;
  unsigned tile_width[64],register_width[64];
};
static void dwi_add_tile(struct dwi_roles *r,int id,unsigned bytes,unsigned write,unsigned counted) {
  if(id==-1) return;
  DXM_CHECK(id>=0,"tile-domain");
  uint64_t mask=dxc_tile_mask((unsigned)id,bytes);
  DXM_CHECK(!r->tile_width[id] || r->tile_width[id]==bytes,"source-role-width-conflict");
  r->tile_width[id]=bytes;
  if(write) {r->ew|=UINT64_C(1)<<id;r->pw|=mask;}
  else {r->er|=UINT64_C(1)<<id;r->pr|=mask;}
  if(counted) r->ready|=mask;
}
static void dwi_add_register(struct dwi_roles *r,unsigned thread,int id,unsigned dtype,unsigned write,unsigned read) {
  if(id==-1) return;
  DXM_CHECK(id>=0,"register-pair-domain");
  dxg_use(thread,(unsigned)id,dtype);
  unsigned bytes=dxg_width(dtype);uint64_t mask=dxg_mask((unsigned)id,dtype);
  DXM_CHECK(!r->register_width[id] || r->register_width[id]==bytes,"source-register-width-conflict");
  r->register_width[id]=bytes;
  if(write) {r->we|=UINT64_C(1)<<id;r->wp|=mask;}
  if(read) {r->re|=UINT64_C(1)<<id;r->rp|=mask;}
}
static void dwi_operation(unsigned opcode,unsigned dtype,unsigned op) {
  DXM_CHECK(opcode<=10 && dtype<6,"source-type-opcode-domain");
  if(opcode==5 || opcode==6) DXM_CHECK(op==0 || op==4 || op==5,"numeric-rmw-opcode-domain");
  else if(opcode==10) DXM_CHECK(op<=(dtype==2 || dtype==5 ? 5u:7u),"numeric-reduction-opcode-domain");
  else if(opcode==8 || opcode==9) DXM_CHECK(op<=15,"numeric-opcode-domain");
  else DXM_CHECK(op==255,"source-unused-opcode");
  DXM_CHECK(!(dtype==2 || dtype==5) || !(6<=op && op<=10),"numeric-float-opcode-domain");
}
static unsigned dwi_prepare_packet(unsigned thread,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *f) {
  DXM_CHECK(p!=0,"source-packet-domain");
  if(opcode==7) dtype=1;
  dwi_operation(opcode,dtype,op);
  unsigned bytes=dxp_width(dtype), source1=bytes,source2=bytes,destination=bytes;
  if(opcode>=2 && opcode<=7) source1=4;
  if(opcode==7) source2=destination=4;
  if((opcode==8 || opcode==9) && op>=11) destination=4;
  struct dwi_roles r={0};
  dwi_add_tile(&r,p->src1,source1,0,1);dwi_add_tile(&r,p->src2,source2,0,1);
  dwi_add_tile(&r,p->dst1,destination,1,1);dwi_add_tile(&r,p->dst2,destination,1,1);
  dwi_add_tile(&r,p->condition,4,0,0);
  unsigned rdtype=(opcode==0 || opcode==1 || opcode==7)?1:dtype;
  dwi_add_register(&r,thread,p->rsrc1,rdtype,0,1);
  dwi_add_register(&r,thread,p->rsrc2,rdtype,0,1);
  dwi_add_register(&r,thread,p->rsrc3,rdtype,0,1);
  dwi_add_register(&r,thread,p->rdst1,rdtype,1,opcode==7);
  dwi_add_register(&r,thread,p->rdst2,rdtype,1,opcode==7);
  unsigned access=opcode==0 || opcode==2 ? 1 : opcode<=6 ? 2:0;
  int region=-1;uint64_t begin=0,end=0;
  if(access) {
    DXM_CHECK(f && f->logical_begin<f->logical_end && f->physical_begin<f->physical_end,"nonempty-source-footprint");
    region=dxr_assign(f->source_base);dxr_check_span(region,f->logical_begin,f->logical_end);
    begin=f->physical_begin;end=f->physical_end;
    if(access==2) {struct dxc_span span=dxc_store_span(begin,end-begin,f->line_bytes);begin=span.begin;end=span.end;}
  } else DXM_CHECK(f==0,"compute-memory-footprint");
  unsigned command=dxc_prepare_counted(thread,region,access,r.er,r.ew,r.pr,r.pw,begin,end,r.ready);
  dxg_bind_roles(command,r.re,r.we,r.rp,r.wp);
  return command;
}
/* A source-owned builder captures IMMUTABLE input/size versions, installs
 * deferred typed outputs/actions, and returns one root covering every active
 * effect. It may not invoke a CPU/source action, settle history or add premises.
 * This seam alone is not a completed value model or public support certificate.
 */
typedef unsigned (*dwi_value_builder)(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *,const struct dwi_footprint *,void *context);
static unsigned dwi_atomic_packet(unsigned thread,unsigned opcode,unsigned dtype,unsigned op,
    struct dwi_packet packet,const struct dwi_footprint *footprint,dwi_value_builder build,void *context) {
  DXM_CHECK(build!=0,"source-bound-value-builder-required");
  unsigned command=dwi_prepare_packet(thread,opcode,dtype,op,&packet,footprint);
  unsigned root=build(command,opcode,opcode==7?1:dtype,op,&packet,footprint,context);
  DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");
  dxc_bind(command,root);
  return command;
}
static void dwi_alloc_MAA(void) {dxs_alloc();}
static void dwi_init_MAA(void) {dxs_init();}
static void dwi_add_mem_region(uint64_t begin,uint64_t end) {dxs_add_region(begin,end);}
static void dwi_clear_mem_region(void) {dxs_clear_regions();}
static void dwi_wait_ready(unsigned tile) {dxc_wait_tile(tile);}
static uint16_t dwi_get_tile_size(unsigned tile) {return dxz_get_size(tile);}
static unsigned dwi_get_data_type(unsigned actual_type_identity) {
  DXM_CHECK(actual_type_identity<=6,"source-type-identity-domain");return actual_type_identity;
}
static unsigned dwi_get_new_tile(unsigned thread,unsigned dtype) {return dxs_new_tile(thread,dtype);}
static unsigned dwi_get_new_reg(unsigned thread,unsigned dtype) {return dxg_new(thread,dtype);}
static unsigned dwi_get_new_reg_initialized(unsigned thread,unsigned dtype,uint64_t value) {return dxg_new_initialized(thread,dtype,value);}
static uint64_t dwi_get_reg(unsigned thread,unsigned dtype,unsigned reg) {return dxg_cpu_read_bits(thread,reg,dtype);}
static void dwi_set_reg(unsigned thread,unsigned dtype,unsigned reg,uint64_t value) {dxg_cpu_write_bits(thread,reg,dtype,value);}
static void dwi_maa_const(unsigned thread,unsigned dtype,uint64_t value,unsigned reg) {dxg_cpu_write_bits(thread,reg,dtype,value);}
/* Address identity only. Never cast this modeled address to a host pointer or
 * infer that the noncacheable range supports the same CPU dereference policy.
 */
static uint64_t dwi_tile_address(unsigned dtype,unsigned tile,unsigned noncacheable) {
  DXM_CHECK(!dxc_constructing && dxs_allocated && noncacheable<=1,"mmio-setup-domain");
  dxm_tile_halves(tile,dxp_width(dtype));
  DXM_CHECK(tile<=INT_MAX/DXP_TILE_WORDS,"tile-source-index-domain");
  return dxs_mmio[noncacheable]+(uint64_t)(tile*DXP_TILE_WORDS)*4;
}
static uint64_t dwi_get_cacheable_tile_pointer(unsigned dtype,unsigned tile) {return dwi_tile_address(dtype,tile,0);}
static uint64_t dwi_get_noncacheable_tile_pointer(unsigned dtype,unsigned tile) {return dwi_tile_address(dtype,tile,1);}
typedef void (*dwi_print_observer)(unsigned tile,unsigned lane,unsigned dtype,uint64_t bits,void *context);
static void dwi_print_tile(unsigned thread,unsigned dtype,unsigned tile,dwi_print_observer observe,void *context) {
  DXM_CHECK(observe!=0,"source-owned-io-projection-required");
  uint16_t size=dxz_get_size(tile);
  DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");
  for(unsigned lane=0;lane<size;++lane) observe(tile,lane,dtype,dxp_cpu_read_bits(thread,tile,lane,dtype),context);
}
'''
    rows = [prefix]
    fields = ("src1", "src2", "dst1", "dst2", "rdst1", "rdst2", "rsrc1", "rsrc2", "rsrc3", "condition")
    for record in declarations:
        if "packet" not in record:
            continue
        packet = record["packet"]
        params = ["uint64_t " + p["name"] if "*" in p["type"] else "int " + p["name"] for p in record["parameters"]]
        params = ["unsigned thread", "unsigned dtype", *params,
                  "const struct dwi_footprint *footprint", "dwi_value_builder build", "void *context"]
        rows += [f'/* {record["file"]}:{record["line"]}-{record["line_end"]}; exact packed operand map. */',
                 f'static unsigned dwi_{record["name"]}({", ".join(params)}) {{']
        for role, binding in packet["operands"].items():
            if binding:
                rows.append(f'  DXM_CHECK({binding["parameter"]}>={-1 if binding["optional"] else 0},"source-{role}-operand-domain");')
        values = [str(-1) if packet["operands"][role] is None else packet["operands"][role]["parameter"] for role in fields]
        rows.append('  struct dwi_packet packet={' + ','.join(values) + '};')
        if packet["memory_access"]:
            rows.append('  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");')
        operation = packet["operation"] or "255"
        rows += [f'  return dwi_atomic_packet(thread,{packet["opcode"]},dtype,{operation},packet,footprint,build,context);', '}']
    return '\n'.join(rows) + '\n#endif\n'
