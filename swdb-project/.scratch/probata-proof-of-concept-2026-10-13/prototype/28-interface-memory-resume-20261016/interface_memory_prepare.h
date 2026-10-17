/* 2026-10-16 ET. PRIVATE preparation only; not a complete source call model.
 * Include after pinned command_state + region_state. No register/value/history
 * effect is supplied. Source-site admission must generate correspondence inputs;
 * candidate code must not call these helpers or choose its own footprint.
 * No public get_tile_ready is introduced. wait_ready remains a blocking MMIO read.
 */
#ifndef SWDB_DXI_MEMORY_PREPARE_H
#define SWDB_DXI_MEMORY_PREPARE_H
struct dxi_masks { uint64_t er,ew,pr,pw,ready; };
struct dxi_memory_correspondence {
  uint64_t logical_begin,logical_end,physical_begin,physical_end,line_bytes;
};
/* The same ID can occur in several source roles. IF::getWordSize uses condition,
 * src1,src2,dst1,dst2 priority. Different required widths at one ID refuse as a
 * software correspondence obligation rather than inventing independent widths.
 * Odd eight-byte starts remain allowed if both physical halves exist. */
static void dxi_add_role(struct dxi_masks *m,unsigned *widths,int tile,unsigned bytes,
                         unsigned optional,unsigned write,unsigned counted) {
  if (optional && tile == -1) return;
  DXM_CHECK(tile >= 0 && (unsigned)tile < DXM_TILES,"source-tile-domain");
  DXM_CHECK(bytes == 4 || bytes == 8,"source-role-width");
  DXM_CHECK(bytes/4 <= DXM_TILES-(unsigned)tile,"source-pair-domain");
  DXM_CHECK(widths[tile] == 0 || widths[tile] == bytes,"source-role-alias-width");
  widths[tile]=bytes;
  uint64_t explicit_mask=UINT64_C(1) << tile,physical=dxc_tile_mask((unsigned)tile,bytes);
  if (write) { m->ew|=explicit_mask; m->pw|=physical; }
  else { m->er|=explicit_mask; m->pr|=physical; }
  if (counted) m->ready|=physical;
}
static unsigned dxi_prepare_memory(unsigned thread,unsigned access,uint64_t source_base,
    struct dxi_memory_correspondence domain,struct dxi_masks masks) {
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  DXM_CHECK(access == 1 || access == 2,"access-kind-domain");
  DXM_CHECK(domain.logical_begin < domain.logical_end,"logical-footprint-domain");
  DXM_CHECK(domain.physical_begin < domain.physical_end,"physical-footprint-domain");
  /* Actual source addresses and physical addresses are distinct. This checks
     region/F2 in source space; it never assumes their translation is identity. */
  int assigned=dxr_assign(source_base);
  dxr_check_span(assigned,domain.logical_begin,domain.logical_end);
  uint64_t begin=domain.physical_begin,end=domain.physical_end;
  if (access == 2) {
    struct dxc_span line=dxc_store_span(begin,end-begin,domain.line_bytes);
    begin=line.begin; end=line.end;
  }
  return dxc_prepare_counted(thread,assigned,access,masks.er,masks.ew,
                             masks.pr,masks.pw,begin,end,masks.ready);
}

/* MAA_gem5.hpp:232-249; STREAM_LD. Register arguments not bound: min_reg,max_reg,stride_reg. */
static unsigned dxi_prepare_maa_stream_load(unsigned thread,unsigned dtype,uint64_t source_base,int dst_tile,int cond_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),0,1,1);
  return dxi_prepare_memory(thread,1,source_base,domain,masks);
}

/* MAA_gem5.hpp:251-268; STREAM_ST. Register arguments not bound: min_reg,max_reg,stride_reg. */
static unsigned dxi_prepare_maa_stream_store(unsigned thread,unsigned dtype,uint64_t source_base,int src_tile,int cond_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,src_tile,(dtype < 3 ? 4 : 8),0,0,1);
  return dxi_prepare_memory(thread,2,source_base,domain,masks);
}

/* MAA_gem5.hpp:270-287; INDIR_LD. Register arguments not bound: none. */
static unsigned dxi_prepare_maa_indirect_load(unsigned thread,unsigned dtype,uint64_t source_base,int idx_tile,int dst_tile,int cond_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,idx_tile,4,0,0,1);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),0,1,1);
  return dxi_prepare_memory(thread,1,source_base,domain,masks);
}

/* MAA_gem5.hpp:289-306; INDIR_ST_VECTOR. Register arguments not bound: none. */
static unsigned dxi_prepare_maa_indirect_store_vector(unsigned thread,unsigned dtype,uint64_t source_base,int idx_tile,int src_tile,int cond_tile,int dst_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,idx_tile,4,0,0,1);
  dxi_add_role(&masks,widths,src_tile,(dtype < 3 ? 4 : 8),0,0,1);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),1,1,1);
  return dxi_prepare_memory(thread,2,source_base,domain,masks);
}

/* MAA_gem5.hpp:308-325; INDIR_ST_SCALAR. Register arguments not bound: src_reg. */
static unsigned dxi_prepare_maa_indirect_store_scalar(unsigned thread,unsigned dtype,uint64_t source_base,int idx_tile,int cond_tile,int dst_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,idx_tile,4,0,0,1);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),1,1,1);
  return dxi_prepare_memory(thread,2,source_base,domain,masks);
}

/* MAA_gem5.hpp:327-344; INDIR_RMW_VECTOR. Register arguments not bound: none. */
static unsigned dxi_prepare_maa_indirect_rmw_vector(unsigned thread,unsigned dtype,uint64_t source_base,int idx_tile,int src_tile,int cond_tile,int dst_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,idx_tile,4,0,0,1);
  dxi_add_role(&masks,widths,src_tile,(dtype < 3 ? 4 : 8),0,0,1);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),1,1,1);
  return dxi_prepare_memory(thread,2,source_base,domain,masks);
}

/* MAA_gem5.hpp:346-363; INDIR_RMW_SCALAR. Register arguments not bound: src_reg. */
static unsigned dxi_prepare_maa_indirect_rmw_scalar(unsigned thread,unsigned dtype,uint64_t source_base,int idx_tile,int cond_tile,int dst_tile,struct dxi_memory_correspondence domain) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(DXM_TILES <= 64,"tile-mask-capacity");
  struct dxi_masks masks={0,0,0,0,0}; unsigned widths[64]={0};
  dxi_add_role(&masks,widths,cond_tile,4,1,0,0);
  dxi_add_role(&masks,widths,idx_tile,4,0,0,1);
  dxi_add_role(&masks,widths,dst_tile,(dtype < 3 ? 4 : 8),1,1,1);
  return dxi_prepare_memory(thread,2,source_base,domain,masks);
}

#endif
