/*2026-10-16 ET. PRIVATE source pointer bridge; no host pointer casts.
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
  {UINT64_C(65536),UINT64_C(65536),2u,0u,0u},
  {UINT64_C(69632),UINT64_C(69632),2u,2u,1u}
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
    return (uint64_t)o->extent*bytes;
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
  m->source_base=o->guest+p.offset;m->source_page_bytes=4096u;
  f->source_base=m->source_base;f->logical_begin=m->source_base;f->logical_end=o->guest+total;
  f->physical_begin=o->physical+p.offset;f->physical_end=o->physical+total;f->line_bytes=64u;
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
static uint64_t dws_pack_u32(uint32_t value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static uint32_t dws_unpack_u32(uint64_t raw) { uint32_t bits=(uint32_t)raw;uint32_t value;memcpy(&value,&bits,4);return value; }
static uint32_t dws_cpu_load_u32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==0u,"source-pointer-type");return dws_unpack_u32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_u32(unsigned thread,struct dws_pointer p,int64_t index,uint32_t value) {DXM_CHECK(p.dtype==0u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_u32(value));}
static uint64_t dws_pack_i32(int32_t value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static int32_t dws_unpack_i32(uint64_t raw) { uint32_t bits=(uint32_t)raw;int32_t value;memcpy(&value,&bits,4);return value; }
static int32_t dws_cpu_load_i32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==1u,"source-pointer-type");return dws_unpack_i32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_i32(unsigned thread,struct dws_pointer p,int64_t index,int32_t value) {DXM_CHECK(p.dtype==1u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_i32(value));}
static uint64_t dws_pack_f32(float value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static float dws_unpack_f32(uint64_t raw) { uint32_t bits=(uint32_t)raw;float value;memcpy(&value,&bits,4);return value; }
static float dws_cpu_load_f32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==2u,"source-pointer-type");return dws_unpack_f32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_f32(unsigned thread,struct dws_pointer p,int64_t index,float value) {DXM_CHECK(p.dtype==2u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_f32(value));}
static uint64_t dws_pack_u64(uint64_t value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static uint64_t dws_unpack_u64(uint64_t raw) { uint64_t bits=(uint64_t)raw;uint64_t value;memcpy(&value,&bits,8);return value; }
static uint64_t dws_cpu_load_u64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==3u,"source-pointer-type");return dws_unpack_u64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_u64(unsigned thread,struct dws_pointer p,int64_t index,uint64_t value) {DXM_CHECK(p.dtype==3u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_u64(value));}
static uint64_t dws_pack_i64(int64_t value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static int64_t dws_unpack_i64(uint64_t raw) { uint64_t bits=(uint64_t)raw;int64_t value;memcpy(&value,&bits,8);return value; }
static int64_t dws_cpu_load_i64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==4u,"source-pointer-type");return dws_unpack_i64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_i64(unsigned thread,struct dws_pointer p,int64_t index,int64_t value) {DXM_CHECK(p.dtype==4u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_i64(value));}
static uint64_t dws_pack_f64(double value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static double dws_unpack_f64(uint64_t raw) { uint64_t bits=(uint64_t)raw;double value;memcpy(&value,&bits,8);return value; }
static double dws_cpu_load_f64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==5u,"source-pointer-type");return dws_unpack_f64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_f64(unsigned thread,struct dws_pointer p,int64_t index,double value) {DXM_CHECK(p.dtype==5u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_f64(value));}
#endif
