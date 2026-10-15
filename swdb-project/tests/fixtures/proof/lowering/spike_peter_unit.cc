// Probata PoC 24 differential fixture. Created: 2026-10-14 ET.
// Ticket 06's spike (b) proof unit 1 (prototype/06-two-lanes/unit_peter.cpp), with one change: the
// candidate prelude's push hook (`swdb_hooked_QueueBuffer : public QueueBuffer<T>`) uses inheritance,
// which is outside the C++ subset, so it is undone here (#undef). The push hook only matters for the
// forged_frontier fault; the safe build never pushes twice, so the safe build's behavior is unchanged.
// Everything else is the spike as ticket 06 built it: the GAPBS stand-ins and DX100 API of
// spike_api.hpp, the lowering and seams of spike_lowering.hpp, Peter's code included UNCHANGED from
// library/dx100/bfs_read_offload.inc, and swdb_unit_peter copied from unit_peter.cpp.
// Build: -I prototype/06-two-lanes -I prototype/06c-cbmc/faith/shim -I library/dx100.
#include "spike_lowering.hpp"
#undef QueueBuffer
#include "unit_common.hpp"

int32_t swdb_spike_threshold;
#define SWDB_FRONTIER_THRESHOLD swdb_spike_threshold
#define SWDB_CHUNK_SIZE 2
#include "bfs_read_offload.inc"

// The harness entry (unit_peter.cpp). nf: frontier size; accel: swdb_acceleration_enabled.
void swdb_unit_peter(int nf, int accel) {
  swdb_seam_reset();
  for (int i = 0; i < 8; ++i) { swdb_contexts[0].tile[i] = i; swdb_contexts[0].reg[i] = i; }
  swdb_acceleration_enabled = accel != 0;
  for (int v = 0; v < SPIKE_V; ++v) g_parent0[v] = g_parent[v];
  Graph g; g.offsets_ = g_offsets; g.out_neighbors_ = g_neighbors;
  pvector<SGOffset> offsets; offsets.start_ = g_offsets; offsets.n_ = SPIKE_V + 1;
  pvector<NodeID> parent; parent.start_ = g_parent; parent.n_ = SPIKE_V;
  SlidingQueue<NodeID> queue; queue.shared = g_queue; queue.shared_in = size_t(nf);
  queue.shared_out_start = 0; queue.shared_out_end = size_t(nf);
  TDStep(g, offsets, parent, queue, SPIKE_V, g_offsets[SPIKE_V]);
  swdb_check_p2(nf, queue.shared_in);
}
