/*2026-10-16 ET. PRIVATE typed deferred family builders.
 * Include extended whole backend and exact source packet adapters first.
 * Source/MMIO effects are owned premises. No source/pointer/ABI admission is
 * granted by calling these private functions. Candidate callbacks are forbidden.
 */
#ifndef SWDB_DX_WHOLE_VALUE_BUILDERS_H
#define SWDB_DX_WHOLE_VALUE_BUILDERS_H
static unsigned dxw_require(unsigned predicate,unsigned value,const char *rule) {
  DXM_CHECK(predicate<dxm_count && value<dxm_count && rule,"producer-version-domain");
  DXM_CHECK(dxm_count<DXM_NODES,"node-capacity");
  unsigned id=dxm_count++;struct dxm_node *n=&dxm_nodes[id];
  n->kind=11;n->left=predicate;n->right=value;n->guard_rule=rule;n->settled=0;
  return id;
}
static unsigned dxw_cmp(unsigned thread,unsigned op,unsigned left,unsigned right) {
  return dxt_binary(thread,0,op,left,right);
}
static unsigned dxw_bound_size(unsigned thread,unsigned size) {
  return dxw_require(dxw_cmp(thread,14,size,dxm_constant(DXP_VALUE_BOUND)),size,"value-prefix-capacity");
}
static unsigned dxw_same_size(unsigned thread,unsigned size,unsigned other) {
  return dxw_require(dxw_cmp(thread,15,size,other),size,"source-size-agreement");
}
static unsigned dxw_active(unsigned thread,unsigned size,int condition,unsigned lane) {
  unsigned inside=dxw_cmp(thread,13,dxm_constant(lane),size);
  if(condition<0) return inside;
  /* Outside the source size, do not observe even a condition's initializedness. */
  return dxm_select(thread,inside,dxp_capture_bits((unsigned)condition,lane,0),dxm_constant(0));
}
static unsigned dxw_work_root(unsigned thread,unsigned active,unsigned value) {
  return dxm_select(thread,active,value,dxm_constant(0));
}
static unsigned dxw_alu(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *unused) {
  (void)unused;DXM_CHECK(!footprint && opcode>=8 && opcode<=10,"alu-family-binding");
  unsigned thread=dxc_commands[command].thread;
  unsigned size=dxz_capture_size((unsigned)p->src1);
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  if(opcode==9) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->src2));
  size=dxw_bound_size(thread,size);
  unsigned root=size,scalar=UINT_MAX,acc=UINT_MAX;
  if(opcode==8) scalar=dxg_capture_bits((unsigned)p->rsrc1,dtype);
  if(opcode==10) {
    uint64_t bits=0;enum dx_num_status status=dxv_initializer_bits(dtype,op,&dxt_runtime,&bits);
    DXM_CHECK(status==DX_NUM_OK,"source-reduction-initializer-domain");acc=dxm_constant(bits);
  }
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned left=dxp_capture_bits((unsigned)p->src1,lane,dtype);
    unsigned right=opcode==8?scalar:opcode==9?dxp_capture_bits((unsigned)p->src2,lane,dtype):acc;
    /* ALU.cc folds src OP accumulator, including SUB and DIV. */
    unsigned value=dxt_binary(thread,dtype,op,left,right);
    if(opcode==10) acc=dxm_select(thread,active,value,acc);
    else {
      unsigned output_dtype=op>=11?0:dtype;
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,output_dtype,active,value);
      root=dxm_join(root,dxw_work_root(thread,active,value));
    }
  }
  if(opcode==10) {dxg_bind_output(command,(unsigned)p->rdst1,dtype,acc);root=dxm_join(root,acc);}
  else dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}

/* This describes an already established typed ordinary-array mapping. An actual
 * compiler/source access certificate must justify C object, guest addresses,
 * physical envelopes, cell identity, endianness and alias consistency together.
 */
struct dxw_memory {unsigned base_cell,extent;uint64_t source_base;unsigned source_page_bytes;};
static void dxw_memory_domain(unsigned dtype,const struct dwi_footprint *f,const struct dxw_memory *m) {
  DXM_CHECK(f && m && m->base_cell<DXM_CELLS && m->extent>0 && m->extent<=DXM_CELLS-m->base_cell,"cell-domain");
  unsigned bytes=dxp_width(dtype);
  DXM_CHECK(m->source_base==f->source_base,"source-address-binding");
  DXM_CHECK(m->extent-1<=UINT32_MAX/bytes,"numeric-indirect-offset-wrap");
  uint64_t span=(uint64_t)m->extent*bytes;
  DXM_CHECK(m->source_base<=UINT64_MAX-span,"source-address-overflow");
  DXM_CHECK(f->logical_begin<=m->source_base && m->source_base+span<=f->logical_end,"logical-object-envelope");
}
static unsigned dxw_store_old(unsigned command,unsigned dtype,unsigned base,unsigned extent,
    unsigned index,unsigned value,unsigned active,unsigned result,unsigned preserved) {
  DXM_CHECK(result<dxm_count && dxm_nodes[result].kind==6 && !dxm_nodes[result].settled,"action-result-domain");
  DXM_CHECK(preserved<result,"acyclic-producer-version");
  unsigned root=dxa_store(command,dtype,base,extent,index,value,active);
  struct dxa_action *a=&dxa_actions[dxa_count-1];
  a->kind=2;a->old_result=result;a->preserved=preserved;return root;
}
static unsigned dxw_indirect(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *context) {
  DXM_CHECK(opcode>=2 && opcode<=6,"indirect-family-binding");
  const struct dxw_memory *m=(const struct dxw_memory *)context;
  dxw_memory_domain(dtype,footprint,m);
  unsigned thread=dxc_commands[command].thread;
  unsigned size=dxz_capture_size((unsigned)p->src1);
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  size=dxw_bound_size(thread,size);
  unsigned root=size,scalar=UINT_MAX;
  if(opcode==3 || opcode==5) scalar=dxg_capture_bits((unsigned)p->rsrc1,dtype);
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned index=dxp_capture_bits((unsigned)p->src1,lane,0);
    if(opcode==2) {
      unsigned read=dxm_issue_indexed_read(thread,index,m->base_cell,m->extent);
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,dtype,active,read);
      root=dxm_join(root,dxw_work_root(thread,active,read));
    } else {
      unsigned value=opcode==3 || opcode==5?scalar:dxp_capture_bits((unsigned)p->src2,lane,dtype);
      unsigned action;
      if(opcode==5 || opcode==6 || p->dst1>=0) {
        unsigned preserved=p->dst1>=0?dxp_capture_bits((unsigned)p->dst1,lane,dtype):dxm_constant(0);
        unsigned old=dxm_result();
        if(opcode==5 || opcode==6) action=dxa_rmw(command,dtype,op,m->base_cell,m->extent,index,value,active,old,preserved);
        else action=dxw_store_old(command,dtype,m->base_cell,m->extent,index,value,active,old,preserved);
        if(p->dst1>=0) dxp_bind_output(command,(unsigned)p->dst1,lane,dtype,old);
      } else action=dxa_store(command,dtype,m->base_cell,m->extent,index,value,active);
      root=dxm_join(root,action);
    }
  }
  if(p->dst1>=0) dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}
static unsigned dxw_stream(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *context) {
  DXM_CHECK(opcode<=1 && op==255,"stream-family-binding");
  const struct dxw_memory *m=(const struct dxw_memory *)context;
  dxw_memory_domain(dtype,footprint,m);
  unsigned thread=dxc_commands[command].thread,bytes=dxp_width(dtype);
  DXM_CHECK(m->source_page_bytes>=bytes && m->source_page_bytes%bytes==0
            && m->source_page_bytes/bytes<INT_MAX,"source-page-geometry-domain");
  unsigned zero=dxm_constant(0),one=dxm_constant(1);
  unsigned min=dxg_capture_bits((unsigned)p->rsrc1,1);
  unsigned max=dxg_capture_bits((unsigned)p->rsrc2,1);
  unsigned stride=dxg_capture_bits((unsigned)p->rsrc3,1);
  min=dxw_require(dxt_binary(thread,1,12,min,zero),min,"stream-nonnegative-min");
  stride=dxw_require(dxt_binary(thread,1,11,stride,zero),stride,"stream-positive-stride");
  max=dxw_require(dxt_binary(thread,1,11,max,min),max,"stream-nonempty-range");
  /* Preserve source signed multiplication, page-loop increment and final
   * stride increment domains. These checked restrictions are not assumptions. */
  max=dxw_require(dxt_binary(thread,1,14,max,dxm_constant(INT_MAX/bytes)),max,"stream-byte-offset-domain");
  max=dxw_require(dxt_binary(thread,1,14,max,dxm_constant(INT_MAX-m->source_page_bytes/bytes)),max,"stream-page-increment-domain");
  unsigned stride_limit=dxt_binary(thread,1,1,dxm_constant(INT_MAX),stride);
  max=dxw_require(dxt_binary(thread,1,14,max,stride_limit),max,"stream-stride-increment-domain");
  unsigned difference=dxt_binary(thread,1,1,max,min);
  unsigned minus_one=dxt_binary(thread,1,1,difference,one);
  unsigned quotient=dxt_binary(thread,1,3,minus_one,stride);
  unsigned size=dxt_binary(thread,1,4,dxt_binary(thread,1,0,quotient,one),dxm_constant(DXP_TILE_WORDS));
  size=dxw_bound_size(thread,size);
  unsigned root=size;
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned index=dxt_binary(thread,1,0,min,dxt_binary(thread,1,2,dxm_constant(lane),stride));
    if(opcode==0) {
      unsigned read=dxm_issue_indexed_read(thread,index,m->base_cell,m->extent);
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,dtype,active,read);
      root=dxm_join(root,dxw_work_root(thread,active,read));
    } else {
      unsigned value=dxp_capture_bits((unsigned)p->src1,lane,dtype);
      unsigned action=dxa_store(command,dtype,m->base_cell,m->extent,index,value,active);
      root=dxm_join(root,action);
    }
  }
  if(opcode==0) dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}
static unsigned dxw_range(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *unused) {
  (void)unused;
  DXM_CHECK(opcode==7 && dtype==1 && op==255 && !footprint,"range-family-binding");
  /* This slice accepts a call only when its complete output fits the private
   * prefix, strictly below source capacity. Thus it reaches the end of its
   * input rows; source mid-row capacity continuation is a checked refusal. */
  DXM_CHECK(DXP_VALUE_BOUND<DXP_TILE_WORDS,"range-source-capacity-profile");
  unsigned thread=dxc_commands[command].thread,zero=dxm_constant(0),one=dxm_constant(1);
  unsigned size=dxz_capture_size((unsigned)p->src1);
  size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->src2));
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  size=dxw_bound_size(thread,size);
  unsigned initial_i=dxg_capture_bits((unsigned)p->rdst1,1);
  unsigned initial_j=dxg_capture_bits((unsigned)p->rdst2,1);
  unsigned stride=dxg_capture_bits((unsigned)p->rsrc1,1);
  initial_i=dxw_require(dxt_binary(thread,1,12,initial_i,zero),initial_i,"range-nonnegative-row");
  initial_j=dxw_require(dxt_binary(thread,1,12,initial_j,dxm_constant(UINT32_MAX)),initial_j,"range-continuation-domain");
  stride=dxw_require(dxt_binary(thread,1,11,stride,zero),stride,"range-positive-stride");
  unsigned root=dxm_join(size,dxm_join(initial_i,dxm_join(initial_j,stride)));
  unsigned last_j=initial_j,total=zero;
  for(unsigned row=0;row<DXP_VALUE_BOUND;++row) {
    unsigned eligible=dxw_cmp(thread,12,dxm_constant(row),initial_i);
    unsigned active=dxm_select(thread,eligible,dxw_active(thread,size,p->condition,row),zero);
    unsigned min=dxp_capture_bits((unsigned)p->src1,row,0);
    unsigned max=dxp_capture_bits((unsigned)p->src2,row,0);
    min=dxw_require(dxw_cmp(thread,14,min,dxm_constant(INT_MAX)),min,"range-signed-min-conversion");
    max=dxw_require(dxw_cmp(thread,14,max,dxm_constant(INT_MAX)),max,"range-signed-max-domain");
    unsigned start=dxm_select(thread,dxw_cmp(thread,15,last_j,dxm_constant(UINT32_MAX)),min,last_j);
    unsigned less=dxt_binary(thread,1,13,start,max);
    unsigned difference=dxt_binary(thread,1,1,max,start);
    unsigned count=dxt_binary(thread,1,0,dxt_binary(thread,1,3,dxt_binary(thread,1,1,difference,one),stride),one);
    count=dxm_select(thread,less,count,zero);
    /* RangeFuser.cc:211 increments signed my_last_j even after the last
     * emitted item; retain that source overflow obligation at cover. */
    unsigned after=dxt_binary(thread,3,0,start,dxt_binary(thread,3,2,count,stride));
    count=dxw_require(dxt_binary(thread,3,14,after,dxm_constant(INT_MAX)),count,"range-stride-increment-domain");
    unsigned row_checks=dxm_join(min,dxm_join(max,count));
    root=dxm_join(root,dxw_work_root(thread,active,row_checks));
    count=dxm_select(thread,active,count,zero);
    unsigned previous=total;
    total=dxw_bound_size(thread,dxt_binary(thread,0,0,previous,count));
    root=dxm_join(root,total);
    for(unsigned slot=0;slot<DXP_VALUE_BOUND;++slot) {
      unsigned at=dxm_constant(slot);
      unsigned belongs=dxm_select(thread,dxw_cmp(thread,12,at,previous),dxw_cmp(thread,13,at,total),zero);
      unsigned offset=dxt_binary(thread,0,1,at,previous);
      unsigned j=dxt_binary(thread,1,0,start,dxt_binary(thread,1,2,offset,stride));
      dxp_bind_conditional_output(command,(unsigned)p->dst1,slot,1,belongs,dxm_constant(row));
      dxp_bind_conditional_output(command,(unsigned)p->dst2,slot,1,belongs,j);
      root=dxm_join(root,dxw_work_root(thread,belongs,j));
    }
    last_j=dxm_select(thread,active,dxm_constant(UINT32_MAX),last_j);
  }
  unsigned last_i=dxm_select(thread,dxw_cmp(thread,13,initial_i,size),size,initial_i);
  dxg_bind_output(command,(unsigned)p->rdst1,1,last_i);
  dxg_bind_output(command,(unsigned)p->rdst2,1,last_j);
  dxz_bind_size(command,(unsigned)p->dst1,total);dxz_bind_size(command,(unsigned)p->dst2,total);
  return dxm_join(root,dxm_join(last_i,last_j));
}
#endif
