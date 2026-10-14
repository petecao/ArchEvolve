// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. Stand-ins the two proof units compile against.
//
// * DX100 API (apps/dx100/benchmarks/API/MAA.hpp, MAA_gem5.hpp signatures): every maa_* call the
//   units make is DECLARED ONLY. SAW replaces each with a per-call summary (summaries.saw) over
//   the proof semantics in ghost.cry; nothing of the strict layer or its port is compiled in.
// * Tile memory: one global array, swdb_tile_data, that the summaries write (values as if each
//   command finished at issue). get_cacheable_tile_pointer is plain code returning a pointer into
//   it; reading through that pointer is checked by the probe swdb_probe_tile_read (map 12 item 3:
//   on the C++ path a harness probe sits before each read loop).
// * CPU memory accesses to a registered region are checked by swdb_probe_cpu (map 12 item 4).
// * GAPBS types: minimal stand-ins with the members the units use (SAW bundles no libc++; ticket
//   06 Notes). Fixed arrays instead of new[]; the push-buffer capacity is checked.
// Build constants: TILE_SIZE = 2, NUM_CORES = 1 (map 19: lanes 2, threads 1).
#pragma once
#include <cassert>
#include <cstddef>
#include <cstdint>

#ifndef TILE_SIZE
#define TILE_SIZE 2
#endif
#ifndef NUM_CORES
#define NUM_CORES 1
#endif
static_assert(TILE_SIZE == 2 && NUM_CORES == 1, "ghost.cry is written for TILE_SIZE 2, NUM_CORES 1");
#define NUM_TILES_PER_CORE 8
#define NUM_REGS_PER_CORE 8
#define NUM_TILES (NUM_CORES * NUM_TILES_PER_CORE)
#define NUM_SCALAR_REGS (NUM_CORES * NUM_REGS_PER_CORE)

// Spike bounds (map 19 hand minimum): vertices 3, edges <= 3, frontier <= 2.
#define SPIKE_V 3
#define SPIKE_E 3
#define SPIKE_F 2
#define SPIKE_Q 8   // queue capacity: frontier + pushes (<= edges + one forged duplicate)

enum class Operation_t { ADD_OP = 0, SUB_OP, MUL_OP, DIV_OP, MIN_OP, MAX_OP, AND_OP, OR_OP, XOR_OP,
                         SHL_OP, SHR_OP, GT_OP, GTE_OP, LT_OP = 13, LTE_OP, EQ_OP, NE_OP, MAX };

// ---- DX100 calls: declared only; SAW summaries (summaries.saw) stand in for them.
template <class T1> void maa_const(T1 data, int dst_reg);
// maa_stream_load's summary is three overrides, so that a refutation names the failed check:
// stream_bounds, tile_truncation (capacity), then the load itself (memory region, values, ghost).
void swdb_ps_stream_bounds(int min_reg, int max_reg, int stride_reg);
void swdb_ps_stream_capacity(int min_reg, int max_reg, int stride_reg);
template <class T1> void swdb_ps_stream_load(T1 *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile);
template <class T1> inline void maa_stream_load(T1 *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile = -1) {
  swdb_ps_stream_bounds(min_reg, max_reg, stride_reg);
  swdb_ps_stream_capacity(min_reg, max_reg, stride_reg);
  swdb_ps_stream_load<T1>(data, min_reg, max_reg, stride_reg, dst_tile, cond_tile);
}
// maa_indirect_load's summary is one override per memory region the units gather from. The region
// is chosen here by comparing concrete pointers, not by SAW trying five override variants: SAW
// checks every variant's applicability with a path-satisfiability query, which was most of the
// solver time of a shape job (diagnostic 3: 2,453 queries, 580 s). A base the units do not use
// reaches swdb_ps_gather_unknown, which has no summary, so SAW rejects it.
extern int32_t g_queue[SPIKE_Q], g_offsets[SPIKE_V + 1], g_neighbors[SPIKE_E], g_parent[SPIKE_V];
void swdb_ps_gather_queue(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
void swdb_ps_gather_offsets(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
void swdb_ps_gather_offsets1(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
void swdb_ps_gather_neighbors(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
void swdb_ps_gather_parent(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
void swdb_ps_gather_unknown(int32_t *data, int idx_tile, int dst_tile, int cond_tile);
template <class T1> inline void maa_indirect_load(T1 *data, int idx_tile, int dst_tile, int cond_tile = -1) {
  static_assert(sizeof(T1) == 4, "i32");
  int32_t *p = reinterpret_cast<int32_t *>(data);
  if (p == g_queue) swdb_ps_gather_queue(p, idx_tile, dst_tile, cond_tile);
  else if (p == g_offsets) swdb_ps_gather_offsets(p, idx_tile, dst_tile, cond_tile);
  else if (p == g_offsets + 1) swdb_ps_gather_offsets1(p, idx_tile, dst_tile, cond_tile);
  else if (p == g_neighbors) swdb_ps_gather_neighbors(p, idx_tile, dst_tile, cond_tile);
  else if (p == g_parent) swdb_ps_gather_parent(p, idx_tile, dst_tile, cond_tile);
  else swdb_ps_gather_unknown(p, idx_tile, dst_tile, cond_tile);
}
template <class T1> void maa_range_loop(int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg,
                                        int dst_i_tile, int dst_j_tile, int cond_tile = -1);
template <class T1> void maa_alu_scalar(int src1_tile, int src2_reg, int dst_tile, Operation_t op, int cond_tile = -1);
template <class T1> void maa_indirect_store_vector(T1 *data, int idx_tile, int src_tile, int cond_tile = -1, int dst_tile = -1);
void wait_ready(int SPD_id);
uint16_t get_tile_size(int SPD_id);

// ---- harness probes (summaries: hazard checks only, no state change)
void swdb_probe_tile_read(int tile);            // the CPU reads tile `tile` now
void swdb_probe_cpu(int region, int is_write);  // the CPU touches region `region` now
enum { SWDB_REGION_QUEUE = 0, SWDB_REGION_OFFSETS = 1, SWDB_REGION_NEIGHBORS = 2, SWDB_REGION_PARENT = 3 };

// ---- fault tooling only (seams.hpp): read or poke a register without a hazard check, as
// library/dx100/certification/seams.cc pokes the strict layer's state directly.
int32_t swdb_fault_peek_reg(int reg);
void swdb_fault_poke_reg(int reg, int32_t value);
int32_t swdb_fault_peek_size(int tile);

// Tile memory (written by the summaries).
extern int32_t swdb_tile_data[NUM_TILES][TILE_SIZE];
template <class T1> inline T1 *get_cacheable_tile_pointer(int SPD_id) {
  return reinterpret_cast<T1 *>(swdb_tile_data[SPD_id]);
}
inline void clear_mem_region() {}
inline void add_mem_region(void *, void *) {}

// ---- OpenMP stand-ins (no -fopenmp: pragmas are ignored; one thread)
inline int omp_get_thread_num() { return 0; }
inline int omp_get_num_threads() { return 1; }

// ---- GAPBS stand-ins
typedef int32_t NodeID;
typedef int32_t SGOffset;   // apps/dx100/benchmarks/gapbs/src/graph.h:90

template <class T> struct pvector {
  T *start_;
  size_t n_;
  T *data() { return start_; }
  T *beginp() { return start_; }
  T *endp() { return start_ + n_; }
  T &operator[](size_t i) { return start_[i]; }
  size_t size() const { return n_; }
};

struct Graph {
  SGOffset *offsets_;
  NodeID *out_neighbors_;
  int32_t out_degree(NodeID v) const { return offsets_[v + 1] - offsets_[v]; }
};

// The push-buffer and the shared queue (sliding_queue.h), fixed arrays.
template <class T> struct SlidingQueue {
  T *shared;
  size_t shared_in, shared_out_start, shared_out_end;
  size_t size() const { return shared_out_end - shared_out_start; }
};
template <class T> class QueueBuffer {
  size_t in;
  T local_queue[SPIKE_Q];
  SlidingQueue<T> &sq;
 public:
  explicit QueueBuffer(SlidingQueue<T> &master, size_t = 16384) : in(0), sq(master) {}
  // Capacity: no assert here (an assert is a branch, and SAW's path-satisfiability check on it
  // cost ~2.7 s per push, attempt 5); SAW's own memory-safety goal still rejects any write past
  // local_queue or g_queue.
  void push_back(T to_add) {
    local_queue[in++] = to_add;
  }
  void flush() {
    const size_t copy_start = sq.shared_in;   // fetch_and_add, one thread
    for (size_t k = 0; k < in; ++k) sq.shared[copy_start + k] = local_queue[k];
    sq.shared_in = copy_start + in;
    in = 0;
  }
};

// platform_atomics.h: __sync_bool_compare_and_swap. The CPU claim touches `parent`, so the
// harness probes the access first (a CPU write to region parent).
template <class T> inline bool compare_and_swap(T &x, const T &old_val, const T &new_val) {
  swdb_probe_cpu(SWDB_REGION_PARENT, 1);
  return __sync_bool_compare_and_swap(&x, old_val, new_val);
}
