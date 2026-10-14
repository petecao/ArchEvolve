// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. The __dxc_* lowering Peter's TDStep calls,
// routed through the contract's library seams, as certification builds it:
//   library/dx100/dxc_lowering.hpp            (each __dxc_* intrinsic -> one maa_* call)
//   library/dx100/certification/candidate_prelude.hpp  (__dxc_* -> swdb_seam_*, CAS and push hooked)
//   library/dx100/certification/seams.cc      (the eight faults, one selected by -DSWDB_DXC_FAULT_<ID>)
// The fault logic is seams.cc's, with its direct pokes into strict-layer state replaced by the
// fault-only summaries swdb_fault_peek_reg / swdb_fault_poke_reg / swdb_fault_peek_size. The maa_*
// calls are summaries (summaries.saw); nothing here models DX100.
// __dxc_tile_pointer: where dxc_lowering.hpp checks get_tile_ready under SWDB_STRICT, the proof
// harness places its tile-read probe (map 12 item 3).
#pragma once
#include <algorithm>
#include <climits>
#include "spike_api.hpp"

#if (defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK) + defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION) + \
     defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE) + defined(SWDB_DXC_FAULT_DROPPED_WAIT) + \
     defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT) + defined(SWDB_DXC_FAULT_INDEX_WRAP) + \
     defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)) > 1
#error "select at most one DX100 certification fault"
#endif

struct dxc_context { int tile[8], reg[8]; };

// ---- dxc_lowering.hpp (hardware interface 1.0-e4fc4af), the calls TDStep makes
inline void swdb_lower_const_i32(int32_t value, int reg) { maa_const<int>(value, reg); }
inline void swdb_lower_wait(int tile) { wait_ready(tile); }
template <class T> inline void swdb_lower_gather(T *base, int index, int dst) { maa_indirect_load<T>(base, index, dst); }
template <class T> inline void swdb_lower_stream_load(T *base, int minimum, int maximum, int stride, int dst) {
  maa_stream_load<T>(base, minimum, maximum, stride, dst);
}
inline void swdb_lower_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  maa_range_loop<int>(last_i, last_j, lower, upper, stride, rows, columns);
}
inline uint16_t __dxc_tile_size(int tile) { return get_tile_size(tile); }
template <class T> inline T *__dxc_tile_pointer(int tile) {
  swdb_probe_tile_read(tile);   // PROBE (map 12 item 3): the CPU reads this tile next
  return get_cacheable_tile_pointer<T>(tile);
}
inline uint64_t swdb_spike_chunks;
inline void __dxc_accelerated_chunk() { ++swdb_spike_chunks; }
inline void __dxc_cas_probe(int, int, bool, int, int, int = INT_MAX) {}

// ---- seams.cc state and faults (single thread)
inline bool swdb_fault_gathered[NUM_TILES];
inline unsigned swdb_fault_range_calls;
inline unsigned swdb_fault_skipped_rechecks;
inline bool swdb_fault_forged_once;
inline void swdb_seam_reset() {
  swdb_fault_range_calls = 0; swdb_fault_skipped_rechecks = 0; swdb_fault_forged_once = false;
  for (int t = 0; t < NUM_TILES; ++t) swdb_fault_gathered[t] = false;
  swdb_spike_chunks = 0;
}
// dropped_wait: no wait completes. read_before_wait: waits on gather results are skipped.
inline void swdb_seam_wait(int tile) {
#if defined(SWDB_DXC_FAULT_DROPPED_WAIT)
  (void)tile; return;
#else
#if defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT)
  if (swdb_fault_gathered[tile]) return;
#endif
  swdb_lower_wait(tile);
#endif
}
inline void swdb_seam_gather_i32(void *base, int index, int dst) {
  swdb_lower_gather(static_cast<int32_t *>(base), index, dst); swdb_fault_gathered[dst] = true;
}
// index_wrap: the stream's start register wraps to INT32_MAX before the load.
// chunk_off_by_one: a stream that fills the tile exactly requests one more element.
inline void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst) {
#if defined(SWDB_DXC_FAULT_INDEX_WRAP)
  swdb_fault_poke_reg(minimum, INT32_MAX);
#elif defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE)
  const int64_t lo = swdb_fault_peek_reg(minimum), hi = swdb_fault_peek_reg(maximum), step = swdb_fault_peek_reg(stride);
  if (step > 0 && hi >= lo && (hi - lo + step - 1) / step == int64_t(TILE_SIZE)) swdb_fault_poke_reg(maximum, int32_t(hi + step));
#endif
  swdb_fault_range_calls = 0;
  swdb_lower_stream_load(static_cast<int32_t *>(base), minimum, maximum, stride, dst); swdb_fault_gathered[dst] = false;
}
// dropped_continuation: after the first range loop of a stream, the loop state is forced to its
// end, so every continuation tile comes back empty.
inline void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
#if defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION)
  if (swdb_fault_range_calls++ > 0) swdb_fault_poke_reg(last_i, swdb_fault_peek_size(lower));
#endif
  swdb_lower_range_loop(last_i, last_j, lower, upper, stride, rows, columns);
  swdb_fault_gathered[rows] = false; swdb_fault_gathered[columns] = false;
}
// skipped_cas_recheck: a claim whose compare fails succeeds anyway (at most eight per session).
inline bool swdb_seam_cas_failed() {
#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)
  return swdb_fault_skipped_rechecks++ < 8;
#else
  return false;
#endif
}
// forged_frontier v2: the first CPU queue push of the run is pushed twice.
inline bool swdb_seam_push_twice() {
#if defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)
  const bool first = !swdb_fault_forged_once; swdb_fault_forged_once = true; return first;
#else
  return false;
#endif
}

// ---- candidate_prelude.hpp hooks
inline void swdb_hooked_wait(int tile) { swdb_seam_wait(tile); }
template <class T> inline void swdb_hooked_gather(T *base, int index, int dst) {
  static_assert(sizeof(T) == 4, "i32"); swdb_seam_gather_i32((void *)base, index, dst);
}
template <class T> inline void swdb_hooked_stream_load(T *base, int minimum, int maximum, int stride, int dst) {
  static_assert(sizeof(T) == 4, "i32"); swdb_seam_stream_load_i32((void *)base, minimum, maximum, stride, dst);
}
inline void swdb_hooked_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  swdb_seam_range_loop(last_i, last_j, lower, upper, stride, rows, columns);
}
template <class T> inline bool swdb_hooked_compare_and_swap(T &x, const T &old_val, const T &new_val) {
  if (compare_and_swap(x, old_val, new_val)) return true;
  if (swdb_seam_cas_failed()) { __atomic_store_n(&x, new_val, __ATOMIC_SEQ_CST); return true; }
  return false;
}
template <typename T> class swdb_hooked_QueueBuffer : public QueueBuffer<T> {
 public:
  explicit swdb_hooked_QueueBuffer(SlidingQueue<T> &master, size_t given_size = 16384)
      : QueueBuffer<T>(master, given_size) {}
  void push_back(T to_add) {
    QueueBuffer<T>::push_back(to_add);
    if (swdb_seam_push_twice()) QueueBuffer<T>::push_back(to_add);
  }
};
#define __dxc_const_i32 swdb_lower_const_i32
#define __dxc_wait swdb_hooked_wait
#define __dxc_gather swdb_hooked_gather
#define __dxc_stream_load swdb_hooked_stream_load
#define __dxc_range_loop swdb_hooked_range_loop
#define compare_and_swap swdb_hooked_compare_and_swap
#define QueueBuffer swdb_hooked_QueueBuffer
