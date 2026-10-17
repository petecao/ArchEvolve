/* INERT synthetic metadata emitted body; no actual compiler/proof admission. */
/* Original automatic object scope, checked without reset/ownership grants. */
static void dws_source_object_leave(unsigned object) {
  struct dws_pointer p=dws_object_pointer(object);
  uint64_t bytes=dws_pointer_bytes(p),begin=dws_objects[object].physical;
  for(unsigned i=0;i<dxc_count;++i) {
    const struct dxc_command *c=&dxc_commands[i];
    DXM_CHECK(!(c->pending && c->access && begin<c->end && c->begin<begin+bytes),"source-object-lifetime-pending");
  }
}

unsigned int dws_source_program(unsigned owned_thread) {
  struct dws_pointer src_local_0 = dws_object_pointer(0);
  dws_cpu_store_u32(owned_thread,src_local_0,0,((unsigned int)(((int)UINT64_C(1)))));
  dws_cpu_store_u32(owned_thread,src_local_0,1,((unsigned int)(((int)UINT64_C(2)))));
  int src_local_1 = dws_get_new_tile_unsigned_int(owned_thread);
  unsigned int src_store_0 = ((unsigned int)(((int)UINT64_C(7))));
  struct dws_pointer src_base_0 = src_local_0;
  int64_t src_index_0 = (int64_t)(((int)UINT64_C(0)));
  dws_cpu_store_u32(owned_thread,src_base_0,src_index_0,src_store_0);
  unsigned int src_local_2 = dws_cpu_load_u32(owned_thread,src_local_0,(int64_t)(((int)UINT64_C(0))));
  SWDB_CHECK((((((unsigned int)(src_local_2))) == (((unsigned int)(((int)UINT64_C(7))))))),"source-assert-L6");
  unsigned int src_return_0 = ((unsigned int)(src_local_2));
  dws_source_object_leave(0);
  return src_return_0;
  dws_source_object_leave(0);
}
