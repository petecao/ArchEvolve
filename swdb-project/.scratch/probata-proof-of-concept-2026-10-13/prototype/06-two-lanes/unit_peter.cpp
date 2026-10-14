// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. Proof unit 1: one TDStep call with Peter's read
// offload, the contract's reference instance. Peter's code is included UNCHANGED from
// library/dx100/bfs_read_offload.inc (build: -I<swdb-project>/library/dx100).
// Build constants: TILE_SIZE 2, NUM_CORES 1, SWDB_CHUNK_SIZE 2. The frontier threshold is only
// compared, so it is a symbolic constant within its legality clause (>= 1; map 19 item 2).
// A fault build adds one -DSWDB_DXC_FAULT_<ID> (spike_lowering.hpp, from seams.cc).
#include "spike_lowering.hpp"
#include "unit_common.hpp"

int32_t swdb_spike_threshold;
#define SWDB_FRONTIER_THRESHOLD swdb_spike_threshold
#define SWDB_CHUNK_SIZE 2
#include "bfs_read_offload.inc"

// The harness entry SAW verifies. nf: frontier size; accel: swdb_acceleration_enabled.
void swdb_unit_peter(int nf, int accel) {
  swdb_seam_reset();
  for (int i = 0; i < 8; ++i) { swdb_contexts[0].tile[i] = i; swdb_contexts[0].reg[i] = i; }
  swdb_acceleration_enabled = accel != 0;
  for (int v = 0; v < SPIKE_V; ++v) g_parent0[v] = g_parent[v];
  // Member-wise set-up: brace-initialized aggregates of global addresses become constant globals
  // whose initializers SAW cannot allocate ("Global symbol not allocated").
  Graph g; g.offsets_ = g_offsets; g.out_neighbors_ = g_neighbors;
  pvector<SGOffset> offsets; offsets.start_ = g_offsets; offsets.n_ = SPIKE_V + 1;
  pvector<NodeID> parent; parent.start_ = g_parent; parent.n_ = SPIKE_V;
  SlidingQueue<NodeID> queue; queue.shared = g_queue; queue.shared_in = size_t(nf);
  queue.shared_out_start = 0; queue.shared_out_end = size_t(nf);
  TDStep(g, offsets, parent, queue, SPIKE_V, g_offsets[SPIKE_V]);
  swdb_check_p2(nf, queue.shared_in);
}
