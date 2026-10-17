/*2026-10-16 ET. PRIVATE preparation adapters, no public admission.
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

/* MAA_gem5.hpp:175-192; exact packed operand map. */
static unsigned dwi_maa_alu_scalar(unsigned thread, unsigned dtype, int src1_tile, int src2_reg, int dst_tile, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src2_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={src1_tile,-1,dst_tile,-1,-1,-1,src2_reg,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,8,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:194-211; exact packed operand map. */
static unsigned dwi_maa_alu_vector(unsigned thread, unsigned dtype, int src1_tile, int src2_tile, int dst_tile, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src2_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={src1_tile,src2_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,9,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:213-230; exact packed operand map. */
static unsigned dwi_maa_alu_reduce(unsigned thread, unsigned dtype, int src1_tile, int dst_reg, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(dst_reg>=0,"source-rdst1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  struct dwi_packet packet={src1_tile,-1,-1,-1,dst_reg,-1,-1,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,10,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:232-249; exact packed operand map. */
static unsigned dwi_maa_stream_load(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={-1,-1,dst_tile,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,0,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:251-268; exact packed operand map. */
static unsigned dwi_maa_stream_store(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int src_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  struct dwi_packet packet={src_tile,-1,-1,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,1,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:270-287; exact packed operand map. */
static unsigned dwi_maa_indirect_load(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,2,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:289-306; exact packed operand map. */
static unsigned dwi_maa_indirect_store_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,4,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:308-325; exact packed operand map. */
static unsigned dwi_maa_indirect_store_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,3,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:327-344; exact packed operand map. */
static unsigned dwi_maa_indirect_rmw_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,6,dtype,o_type,packet,footprint,build,context);
}
/* MAA_gem5.hpp:346-363; exact packed operand map. */
static unsigned dwi_maa_indirect_rmw_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,5,dtype,o_type,packet,footprint,build,context);
}
/* MAA_gem5.hpp:366-383; exact packed operand map. */
static unsigned dwi_maa_range_loop(unsigned thread, unsigned dtype, int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(min_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(max_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(last_i_reg>=0,"source-rdst1-operand-domain");
  DXM_CHECK(last_j_reg>=0,"source-rdst2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_i_tile>=0,"source-dst1-operand-domain");
  DXM_CHECK(dst_j_tile>=0,"source-dst2-operand-domain");
  struct dwi_packet packet={min_tile,max_tile,dst_i_tile,dst_j_tile,last_i_reg,last_j_reg,stride_reg,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,7,dtype,255,packet,footprint,build,context);
}
#endif
