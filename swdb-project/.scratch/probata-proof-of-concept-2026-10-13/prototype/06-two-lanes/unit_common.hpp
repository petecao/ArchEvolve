// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. Inputs and the BFS unit postcondition shared by
// both proof units.
//
// Inputs (globals; SAW gives them symbolic values, constrained only by the proof-unit
// preconditions in unit.saw): a CSR graph of SPIKE_V = 3 vertices and at most SPIKE_E = 3 edges,
// parent[], and a frontier of nf <= SPIKE_F = 2 vertices at the start of the queue.
//
// P2, the BFS unit postcondition (map 08's P2, map 09 item 1's unit relation), after one call:
//   * an already-visited vertex keeps its parent and is not pushed;
//   * an unvisited vertex is visited iff some frontier vertex has an edge to it; if so, it is
//     pushed exactly once and its parent is such a frontier vertex; if not, its parent is unchanged
//     and it is not pushed;
//   * every pushed entry is a vertex.
// Hazard freedom (P1) is not here: it is the summaries' and probes' preconditions.
#pragma once
#include "spike_api.hpp"

int32_t g_queue[SPIKE_Q];
SGOffset g_offsets[SPIKE_V + 1];
NodeID g_neighbors[SPIKE_E];
NodeID g_parent[SPIKE_V];
NodeID g_parent0[SPIKE_V];
int32_t swdb_tile_data[NUM_TILES][TILE_SIZE];
// The DX100 hazard state (ghost.cry's record G, one global per field; summaries.saw). Only the
// summaries touch these; program code never names them.
uint32_t swdb_g_rdy[1], swdb_g_wr[8], swdb_g_outs[8], swdb_g_anc[8], swdb_g_named[8], swdb_g_users[8],
    swdb_g_rrd[8], swdb_g_rwr[8], swdb_g_reg[8], swdb_g_sz[8], swdb_g_fp[8];

static void swdb_check_p2(int nf, size_t next_end) {
  for (int v = 0; v < SPIKE_V; ++v) {
    bool reachable = false;
    for (int k = 0; k < SPIKE_F; ++k) {
      if (k >= nf) continue;
      const int u = g_queue[k];
      for (int e = 0; e < SPIKE_E; ++e)
        if (e >= g_offsets[u] && e < g_offsets[u + 1] && g_neighbors[e] == v) reachable = true;
    }
    int pushed = 0;
    for (int q = 0; q < SPIKE_Q; ++q)
      if (q >= nf && size_t(q) < next_end && g_queue[q] == v) ++pushed;
    if (g_parent0[v] >= 0) {
      assert(g_parent[v] == g_parent0[v] && "P2_visited_parent_unchanged");
      assert(pushed == 0 && "P2_visited_not_pushed");
    } else if (reachable) {
      assert(pushed == 1 && "P2_reached_pushed_exactly_once");
      const int p = g_parent[v];
      bool valid = false;
      for (int k = 0; k < SPIKE_F; ++k)
        if (k < nf && g_queue[k] == p)
          for (int e = 0; e < SPIKE_E; ++e)
            if (e >= g_offsets[p] && e < g_offsets[p + 1] && g_neighbors[e] == v) valid = true;
      assert(valid && "P2_parent_is_frontier_neighbor");
    } else {
      assert(g_parent[v] == g_parent0[v] && "P2_unreached_parent_unchanged");
      assert(pushed == 0 && "P2_unreached_not_pushed");
    }
  }
  for (int q = 0; q < SPIKE_Q; ++q)
    if (q >= nf && size_t(q) < next_end)
      assert(g_queue[q] >= 0 && g_queue[q] < SPIKE_V && "P2_pushed_is_a_vertex");
}
