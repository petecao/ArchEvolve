// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. C lowering of
// ../06-two-lanes/unit_common.hpp and of the GAPBS / API stand-ins of ../06-two-lanes/spike_api.hpp:
// inputs, P2 (the BFS unit postcondition), the queue buffer, the tile pointer. Hand-lowered:
// templates -> int32_t, references -> pointers, member functions -> functions on structs,
// `assert(x && "name")` -> PROP(x, "name").
#ifndef SWDB_CBMC_COMMON_H
#define SWDB_CBMC_COMMON_H
#include <stddef.h>
#include <stdint.h>

#define TILE_SIZE 2
#define NUM_CORES 1
#define NUM_TILES_PER_CORE 8
#define NUM_REGS_PER_CORE 8
// Spike bounds (map 19 hand minimum): vertices 3, edges <= 3, frontier <= 2.
#define SPIKE_V 3
#define SPIKE_E 3
#define SPIKE_F 2
#define SPIKE_Q 8   // queue capacity: frontier + pushes (<= edges + one forged duplicate)

typedef int32_t NodeID;
typedef int32_t SGOffset;

// Inputs and state (unit_common.hpp).
int32_t g_queue[SPIKE_Q];
SGOffset g_offsets[SPIKE_V + 1];
NodeID g_neighbors[SPIKE_E];
NodeID g_parent[SPIKE_V];
NodeID g_parent0[SPIKE_V];
int32_t swdb_tile_data[NUM_CORES * NUM_TILES_PER_CORE][TILE_SIZE];

#include "dx100_stubs.h"

enum { SWDB_REGION_QUEUE = 0, SWDB_REGION_OFFSETS = 1, SWDB_REGION_NEIGHBORS = 2, SWDB_REGION_PARENT = 3 };
enum { LT_OP = 13 };

// GAPBS stand-ins (spike_api.hpp), C structs.
typedef struct { SGOffset *offsets_; NodeID *out_neighbors_; } Graph;
typedef struct { int32_t *start_; size_t n_; } pvector_i32;
typedef struct { int32_t *shared; size_t shared_in, shared_out_start, shared_out_end; } SlidingQueue;
static size_t sq_size(const SlidingQueue *q) { return q->shared_out_end - q->shared_out_start; }
typedef struct { size_t in; int32_t local_queue[SPIKE_Q]; SlidingQueue *sq; } QueueBuffer;
static void qb_init(QueueBuffer *b, SlidingQueue *master) { b->in = 0; b->sq = master; }
// No capacity check here, as in the C++; CBMC's bounds check rejects a write past local_queue.
static void qb_push_back(QueueBuffer *b, int32_t to_add) { b->local_queue[b->in++] = to_add; }
static void qb_flush(QueueBuffer *b) {
  const size_t copy_start = b->sq->shared_in;   // fetch_and_add, one thread
  for (size_t k = 0; k < b->in; ++k) b->sq->shared[copy_start + k] = b->local_queue[k];
  b->sq->shared_in = copy_start + b->in;
  b->in = 0;
}
static int32_t *get_cacheable_tile_pointer(int32_t SPD_id) { return swdb_tile_data[SPD_id]; }
static int omp_get_thread_num(void) { return 0; }

// P2, the BFS unit postcondition (unit_common.hpp swdb_check_p2, line by line).
static void swdb_check_p2(int nf, size_t next_end) {
  for (int v = 0; v < SPIKE_V; ++v) {
    int reachable = 0;
    for (int k = 0; k < SPIKE_F; ++k) {
      if (k >= nf) continue;
      const int u = g_queue[k];
      for (int e = 0; e < SPIKE_E; ++e)
        if (e >= g_offsets[u] && e < g_offsets[u + 1] && g_neighbors[e] == v) reachable = 1;
    }
    int pushed = 0;
    for (int q = 0; q < SPIKE_Q; ++q)
      if (q >= nf && (size_t)q < next_end && g_queue[q] == v) ++pushed;
    if (g_parent0[v] >= 0) {
      PROP(g_parent[v] == g_parent0[v], "P2_visited_parent_unchanged");
      PROP(pushed == 0, "P2_visited_not_pushed");
    } else if (reachable) {
      PROP(pushed == 1, "P2_reached_pushed_exactly_once");
      const int p = g_parent[v];
      int valid = 0;
      for (int k = 0; k < SPIKE_F; ++k)
        if (k < nf && g_queue[k] == p)
          for (int e = 0; e < SPIKE_E; ++e)
            if (e >= g_offsets[p] && e < g_offsets[p + 1] && g_neighbors[e] == v) valid = 1;
      PROP(valid, "P2_parent_is_frontier_neighbor");
    } else {
      PROP(g_parent[v] == g_parent0[v], "P2_unreached_parent_unchanged");
      PROP(pushed == 0, "P2_unreached_not_pushed");
    }
  }
  for (int q = 0; q < SPIKE_Q; ++q)
    if (q >= nf && (size_t)q < next_end)
      PROP(g_queue[q] >= 0 && g_queue[q] < SPIKE_V, "P2_pushed_is_a_vertex");
}
#endif
