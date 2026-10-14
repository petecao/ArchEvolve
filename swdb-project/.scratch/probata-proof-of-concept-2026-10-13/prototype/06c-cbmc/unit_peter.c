// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. Proof unit 1, hand-lowered to C:
// one TDStep call with Peter's read offload (library/dx100/bfs_read_offload.inc, hardware
// interface 1.0-e4fc4af) through the lowering and seams of ../06-two-lanes/spike_lowering.hpp
// (dxc_lowering.hpp, candidate_prelude.hpp, seams.cc), the build ticket 06 verified with SAW.
// Lowering rules: one C line per C++ line where possible; templates -> int32_t; references ->
// pointers; pvector::operator[](size_t) -> start_[(size_t)i]; std::min -> ?:; the OpenMP pragmas
// are dropped (no -fopenmp in ticket 06 either: one thread); __sync_bool_compare_and_swap and
// __atomic_* -> plain loads and stores (one thread). Each maa_* call -> its stub (dx100_stubs.h).
// Build constants: TILE_SIZE 2, NUM_CORES 1, SWDB_CHUNK_SIZE 2; frontier threshold symbolic >= 1.
// A fault build adds one -DSWDB_DXC_FAULT_<ID> (seams.cc's eight faults; seven are controls here).
#include "common.h"

#if (defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK) + defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION) + \
     defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE) + defined(SWDB_DXC_FAULT_DROPPED_WAIT) + \
     defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT) + defined(SWDB_DXC_FAULT_INDEX_WRAP) + \
     defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)) > 1
#error "select at most one DX100 certification fault"
#endif

typedef struct { int tile[8], reg[8]; } dxc_context;

int32_t swdb_spike_threshold;
#define SWDB_FRONTIER_THRESHOLD swdb_spike_threshold
#define SWDB_CHUNK_SIZE 2

// ---- dxc_lowering.hpp (each __dxc_* intrinsic -> one maa_* call)
static void swdb_lower_const_i32(int32_t value, int reg) { dx_const(value, reg); }
static void swdb_lower_wait(int tile) { dx_wait(tile); }
static void swdb_lower_gather(int32_t *base, int index, int dst) { dx_gather(base, index, dst, -1); }
static void swdb_lower_stream_load(int32_t *base, int minimum, int maximum, int stride, int dst) {
  dx_stream_load(base, minimum, maximum, stride, dst, -1);
}
static void swdb_lower_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  dx_range_loop(last_i, last_j, lower, upper, stride, rows, columns, -1);
}
static uint16_t dxc_tile_size(int tile) { return dx_get_tile_size(tile); }
static int32_t *dxc_tile_pointer(int tile) {
  dx_probe_tile_read(tile);   // PROBE (map 12 item 3): the CPU reads this tile next
  return get_cacheable_tile_pointer(tile);
}
uint64_t swdb_spike_chunks;

// ---- seams.cc state and faults (single thread)
int swdb_fault_gathered[8];
unsigned swdb_fault_range_calls;
unsigned swdb_fault_skipped_rechecks;
int swdb_fault_forged_once;
static void swdb_seam_reset(void) {
  swdb_fault_range_calls = 0; swdb_fault_skipped_rechecks = 0; swdb_fault_forged_once = 0;
  for (int t = 0; t < 8; ++t) swdb_fault_gathered[t] = 0;
  swdb_spike_chunks = 0;
}
// dropped_wait: no wait completes. read_before_wait: waits on gather results are skipped.
static void swdb_seam_wait(int tile) {
#if defined(SWDB_DXC_FAULT_DROPPED_WAIT)
  (void)tile; return;
#else
#if defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT)
  if (swdb_fault_gathered[tile]) return;
#endif
  swdb_lower_wait(tile);
#endif
}
static void swdb_seam_gather_i32(int32_t *base, int index, int dst) {
  swdb_lower_gather(base, index, dst); swdb_fault_gathered[dst] = 1;
}
// index_wrap: the stream's start register wraps to INT32_MAX before the load.
// chunk_off_by_one: a stream that fills the tile exactly requests one more element.
static void swdb_seam_stream_load_i32(int32_t *base, int minimum, int maximum, int stride, int dst) {
#if defined(SWDB_DXC_FAULT_INDEX_WRAP)
  dx_fault_poke_reg(minimum, INT32_MAX);
#elif defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE)
  const int64_t lo = dx_fault_peek_reg(minimum), hi = dx_fault_peek_reg(maximum), step = dx_fault_peek_reg(stride);
  if (step > 0 && hi >= lo && (hi - lo + step - 1) / step == (int64_t)TILE_SIZE) dx_fault_poke_reg(maximum, (int32_t)(hi + step));
#endif
  swdb_fault_range_calls = 0;
  swdb_lower_stream_load(base, minimum, maximum, stride, dst); swdb_fault_gathered[dst] = 0;
}
// dropped_continuation: after the first range loop of a stream, the loop state is forced to its
// end, so every continuation tile comes back empty.
static void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
#if defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION)
  if (swdb_fault_range_calls++ > 0) dx_fault_poke_reg(last_i, dx_fault_peek_size(lower));
#endif
  swdb_lower_range_loop(last_i, last_j, lower, upper, stride, rows, columns);
  swdb_fault_gathered[rows] = 0; swdb_fault_gathered[columns] = 0;
}
// skipped_cas_recheck: a claim whose compare fails succeeds anyway (at most eight per session).
static int swdb_seam_cas_failed(void) {
#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)
  return swdb_fault_skipped_rechecks++ < 8;
#else
  return 0;
#endif
}
// forged_frontier v2: the first CPU queue push of the run is pushed twice.
static int swdb_seam_push_twice(void) {
#if defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)
  const int first = !swdb_fault_forged_once; swdb_fault_forged_once = 1; return first;
#else
  return 0;
#endif
}

// ---- candidate_prelude.hpp hooks
// platform_atomics.h compare_and_swap, with the harness probe (a CPU write to region parent).
static int compare_and_swap_raw(int32_t *x, int32_t old_val, int32_t new_val) {
  dx_probe_cpu(SWDB_REGION_PARENT, 1);
  if (*x == old_val) { *x = new_val; return 1; }   // __sync_bool_compare_and_swap, one thread
  return 0;
}
static int swdb_hooked_compare_and_swap(int32_t *x, int32_t old_val, int32_t new_val) {
  if (compare_and_swap_raw(x, old_val, new_val)) return 1;
  if (swdb_seam_cas_failed()) { *x = new_val; return 1; }   // __atomic_store_n
  return 0;
}
static void swdb_hooked_push_back(QueueBuffer *b, int32_t to_add) {
  qb_push_back(b, to_add);
  if (swdb_seam_push_twice()) qb_push_back(b, to_add);
}
#define __dxc_const_i32 swdb_lower_const_i32
#define __dxc_wait swdb_seam_wait
#define __dxc_gather swdb_seam_gather_i32
#define __dxc_stream_load swdb_seam_stream_load_i32
#define __dxc_range_loop swdb_seam_range_loop
#define __dxc_tile_size dxc_tile_size
#define __dxc_tile_pointer dxc_tile_pointer
#define __dxc_accelerated_chunk() (++swdb_spike_chunks)

// ---- bfs_read_offload.inc (Peter section 5 read offload, fixes E1-E5), lowered line by line
static dxc_context swdb_contexts[NUM_CORES];
static int swdb_acceleration_enabled = 0;
void TDStep(const Graph *g, pvector_i32 *VertexOffsets, pvector_i32 *parent, SlidingQueue *queue, int num_nodes, int num_edges) {
  (void)num_nodes; (void)num_edges;
  {
    QueueBuffer lqueue; qb_init(&lqueue, queue);
    const int accelerate = swdb_acceleration_enabled && sq_size(queue) >= (size_t)SWDB_FRONTIER_THRESHOLD;
    if (accelerate) {
      dxc_context c = swdb_contexts[omp_get_thread_num()];
      __dxc_const_i32(1, c.reg[2]); __dxc_const_i32(0, c.reg[3]);
      for (size_t begin = queue->shared_out_start; begin < queue->shared_out_end; begin += SWDB_CHUNK_SIZE) {
        const size_t end = begin + (size_t)SWDB_CHUNK_SIZE < (size_t)queue->shared_out_end
                               ? begin + (size_t)SWDB_CHUNK_SIZE : (size_t)queue->shared_out_end;   // std::min
        __dxc_const_i32((int32_t)begin, c.reg[0]); __dxc_const_i32((int32_t)end, c.reg[1]);
        __dxc_stream_load(queue->shared, c.reg[0], c.reg[1], c.reg[2], c.tile[0]);
        __dxc_gather(VertexOffsets->start_, c.tile[0], c.tile[1]);
        __dxc_gather(VertexOffsets->start_ + 1, c.tile[0], c.tile[2]);
        __dxc_const_i32(0, c.reg[4]); __dxc_const_i32(-1, c.reg[5]);
        __dxc_accelerated_chunk();
        for (;;) {
          __dxc_range_loop(c.reg[4], c.reg[5], c.tile[1], c.tile[2], c.reg[2], c.tile[6], c.tile[7]);
          __dxc_wait(c.tile[7]);
          const unsigned count = __dxc_tile_size(c.tile[7]); if (count == 0) break;
          __dxc_gather(g->out_neighbors_, c.tile[7], c.tile[0]);
          __dxc_gather(queue->shared + begin, c.tile[6], c.tile[3]);
          __dxc_gather(parent->start_, c.tile[0], c.tile[5]);
          __dxc_wait(c.tile[3]); __dxc_wait(c.tile[5]);
          int32_t *vertices = __dxc_tile_pointer(c.tile[0]); int32_t *frontier = __dxc_tile_pointer(c.tile[3]);
          int32_t *hints = __dxc_tile_pointer(c.tile[5]);
          for (unsigned k = 0; k < count; ++k) {
            const NodeID v = vertices[k], u = frontier[k]; const NodeID hint = hints[k];
            const int claimed = hint < 0 && swdb_hooked_compare_and_swap(&parent->start_[(size_t)v], hint, u);
            if (claimed) { parent->start_[(size_t)v] = u; swdb_hooked_push_back(&lqueue, v); }
          }
        }
      }
    } else {
      for (size_t i = queue->shared_out_start; i < queue->shared_out_end; ++i) {
        const NodeID u = queue->shared[i];
        for (int j = VertexOffsets->start_[(size_t)u]; j < VertexOffsets->start_[(size_t)(u + 1)]; ++j) {
          const NodeID v = g->out_neighbors_[j], value = parent->start_[(size_t)v];   // __atomic_load_n
          if (value < 0 && swdb_hooked_compare_and_swap(&parent->start_[(size_t)v], value, u)) {
            parent->start_[(size_t)v] = u; swdb_hooked_push_back(&lqueue, v);
          }
        }
      }
    }
    qb_flush(&lqueue);
  }
}

// The harness entry (unit_peter.cpp swdb_unit_peter). nf: frontier size; accel: swdb_acceleration_enabled.
void swdb_unit_peter(int nf, int accel) {
  swdb_seam_reset();
  for (int i = 0; i < 8; ++i) { swdb_contexts[0].tile[i] = i; swdb_contexts[0].reg[i] = i; }
  swdb_acceleration_enabled = accel != 0;
  for (int v = 0; v < SPIKE_V; ++v) g_parent0[v] = g_parent[v];
  Graph g; g.offsets_ = g_offsets; g.out_neighbors_ = g_neighbors;
  pvector_i32 offsets; offsets.start_ = g_offsets; offsets.n_ = SPIKE_V + 1;
  pvector_i32 parent; parent.start_ = g_parent; parent.n_ = SPIKE_V;
  SlidingQueue queue; queue.shared = g_queue; queue.shared_in = (size_t)nf;
  queue.shared_out_start = 0; queue.shared_out_end = (size_t)nf;
  TDStep(&g, &offsets, &parent, &queue, SPIKE_V, g_offsets[SPIKE_V]);
  swdb_check_p2(nf, queue.shared_in);
}
#define SWDB_UNIT_PETER 1
#include "harness.h"
