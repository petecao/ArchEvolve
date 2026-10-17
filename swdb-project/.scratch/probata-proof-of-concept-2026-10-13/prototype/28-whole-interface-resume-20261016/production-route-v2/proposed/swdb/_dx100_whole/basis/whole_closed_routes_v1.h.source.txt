/*2026-10-16 ET. Closed private routes; source/ABI/access admission required. */
#ifndef SWDB_DX_WHOLE_CLOSED_VALUE_ROUTES_H
#define SWDB_DX_WHOLE_CLOSED_VALUE_ROUTES_H
static unsigned dxw_call_maa_alu_scalar(unsigned thread, unsigned dtype, int src1_tile, int src2_reg, int dst_tile, int op, int cond_tile) {
  return dwi_maa_alu_scalar(thread, dtype, src1_tile, src2_reg, dst_tile, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_alu_vector(unsigned thread, unsigned dtype, int src1_tile, int src2_tile, int dst_tile, int op, int cond_tile) {
  return dwi_maa_alu_vector(thread, dtype, src1_tile, src2_tile, dst_tile, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_alu_reduce(unsigned thread, unsigned dtype, int src1_tile, int dst_reg, int op, int cond_tile) {
  return dwi_maa_alu_reduce(thread, dtype, src1_tile, dst_reg, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_stream_load(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_stream_load(thread, dtype, data, min_reg, max_reg, stride_reg, dst_tile, cond_tile, footprint, dxw_stream, (void *)mapping);
}
static unsigned dxw_call_maa_stream_store(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int src_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_stream_store(thread, dtype, data, min_reg, max_reg, stride_reg, src_tile, cond_tile, footprint, dxw_stream, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_load(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_load(thread, dtype, data, idx_tile, dst_tile, cond_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_store_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_store_vector(thread, dtype, data, idx_tile, src_tile, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_store_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_store_scalar(thread, dtype, data, idx_tile, src_reg, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_rmw_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_rmw_vector(thread, dtype, data, idx_tile, src_tile, o_type, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_rmw_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_rmw_scalar(thread, dtype, data, idx_tile, src_reg, o_type, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_range_loop(unsigned thread, unsigned dtype, int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile) {
  return dwi_maa_range_loop(thread, dtype, last_i_reg, last_j_reg, min_tile, max_tile, stride_reg, dst_i_tile, dst_j_tile, cond_tile, 0, dxw_range, 0);
}
#endif
