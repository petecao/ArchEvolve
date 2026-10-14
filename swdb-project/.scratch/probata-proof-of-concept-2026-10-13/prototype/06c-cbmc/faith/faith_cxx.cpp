// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. Faithfulness test, C++ side: ticket 06's
// C++ proof units (../../06-two-lanes/unit_peter.cpp with Peter's bfs_read_offload.inc unchanged,
// or ../../06-two-lanes/unit_maa.cpp), unchanged, linked against the same C stubs as the C
// lowering. The declared-only DX100 API of spike_api.hpp is defined here, each function by the
// stub of the same name. Build: -DSWDB_NATIVE -DSWDB_TRACE -DSWDB_UNIT_PETER|-DSWDB_UNIT_MAA
// [fault or control flag] -I faith/shim -I <swdb>/library/dx100. The harness main (harness.h,
// SWDB_NATIVE) is the same text the C side uses.
#include <algorithm>
#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstring>
#if defined(SWDB_UNIT_PETER)
#include "../../06-two-lanes/unit_peter.cpp"
#else
#include "../../06-two-lanes/unit_maa.cpp"
#endif
#include "../dx100_stubs.h"

void swdb_cxx_assert(bool ok, const char *text) {
  if (ok) return;
  static char name[128];
  const char *q = std::strchr(text, '"');
  if (!q) { swdb_native_prop_failed(text); return; }
  std::size_t n = 0;
  for (const char *s = q + 1; *s && *s != '"' && n + 1 < sizeof name; ++s) name[n++] = *s;
  name[n] = 0;
  swdb_native_prop_failed(name);
}

// ---- spike_api.hpp's declared-only API, defined by the stubs
template <class T1> void maa_const(T1 data, int dst_reg) { dx_const((int32_t)data, dst_reg); }
void swdb_ps_stream_bounds(int min_reg, int max_reg, int stride_reg) { dx_ps_stream_bounds(min_reg, max_reg, stride_reg); }
void swdb_ps_stream_capacity(int min_reg, int max_reg, int stride_reg) { dx_ps_stream_capacity(min_reg, max_reg, stride_reg); }
template <class T1> void swdb_ps_stream_load(T1 *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile) {
  dx_ps_stream_load(reinterpret_cast<int32_t *>(data), min_reg, max_reg, stride_reg, dst_tile, cond_tile);
}
void swdb_ps_gather_queue(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
void swdb_ps_gather_offsets(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
void swdb_ps_gather_offsets1(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
void swdb_ps_gather_neighbors(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
void swdb_ps_gather_parent(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
void swdb_ps_gather_unknown(int32_t *data, int idx_tile, int dst_tile, int cond_tile) { dx_gather(data, idx_tile, dst_tile, cond_tile); }
template <class T1> void maa_range_loop(int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg,
                                        int dst_i_tile, int dst_j_tile, int cond_tile) {
  dx_range_loop(last_i_reg, last_j_reg, min_tile, max_tile, stride_reg, dst_i_tile, dst_j_tile, cond_tile);
}
template <class T1> void maa_alu_scalar(int src1_tile, int src2_reg, int dst_tile, Operation_t op, int cond_tile) {
  dx_alu_scalar(src1_tile, src2_reg, dst_tile, (int32_t)op, cond_tile);
}
template <class T1> void maa_indirect_store_vector(T1 *data, int idx_tile, int src_tile, int cond_tile, int dst_tile) {
  dx_store_vector(reinterpret_cast<int32_t *>(data), idx_tile, src_tile, cond_tile, dst_tile);
}
void wait_ready(int SPD_id) { dx_wait(SPD_id); }
uint16_t get_tile_size(int SPD_id) { return dx_get_tile_size(SPD_id); }
void swdb_probe_tile_read(int tile) { dx_probe_tile_read(tile); }
void swdb_probe_cpu(int region, int is_write) { dx_probe_cpu(region, is_write); }
int32_t swdb_fault_peek_reg(int reg) { return dx_fault_peek_reg(reg); }
void swdb_fault_poke_reg(int reg, int32_t value) { dx_fault_poke_reg(reg, value); }
int32_t swdb_fault_peek_size(int tile) { return dx_fault_peek_size(tile); }

#include "../harness.h"
