// Prospective lexical private-array refinement; source/formal acceptance pending.
// Prospective private out-slot ABI, 2026-10-16 ET. Not a proof record.
// PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
// Logic definitions for the BFS unit postcondition (map 09 item 1; 08's P2), non-recursive.
#ifndef BFS_UNIT_H
#define BFS_UNIT_H
#include "gapbs_models.h"

/*@
  // Edge e leaves vertex u in the CSR graph (offsets, neighbors).
  predicate bfs_edge{L}(SGOffset *offsets, integer u, integer e) =
    \at(offsets[u], L) <= e < \at(offsets[u + 1], L);

  // Some frontier vertex (queue->shared[out_start .. out_end - 1]) has an edge to v.
  predicate bfs_reach{L}(struct SlidingQueue_NodeID *queue, SGOffset *offsets, NodeID *neighbors, integer v) =
    \exists integer p, e;
      \at(queue->shared_out_start, L) <= p < \at(queue->shared_out_end, L) &&
      bfs_edge{L}(offsets, \at(queue->shared[p], L), e) && \at(neighbors[e], L) == v;

  // u is a frontier vertex with an edge to v.
  predicate bfs_frontier_edge{L}(struct SlidingQueue_NodeID *queue, SGOffset *offsets, NodeID *neighbors,
                                 integer u, integer v) =
    \exists integer p, e;
      \at(queue->shared_out_start, L) <= p < \at(queue->shared_out_end, L) &&
      \at(queue->shared[p], L) == u &&
      bfs_edge{L}(offsets, u, e) && \at(neighbors[e], L) == v;

  // Pairwise distinct allocation blocks: CSR offsets, neighbors, parent, queue storage,
  // Four interface objects. Private QueueBuffer storage is created later.
  predicate bfs_distinct_blocks(char *o, char *n, char *p, char *q, char *g, char *vo, char *pa, char *qu) =
    o != n &&
    o != p &&
    o != q &&
    o != g &&
    o != vo &&
    o != pa &&
    o != qu &&
    n != p &&
    n != q &&
    n != g &&
    n != vo &&
    n != pa &&
    n != qu &&
    p != q &&
    p != g &&
    p != vo &&
    p != pa &&
    p != qu &&
    q != g &&
    q != vo &&
    q != pa &&
    q != qu &&
    g != vo &&
    g != pa &&
    g != qu &&
    vo != pa &&
    vo != qu &&
    pa != qu;
*/
#endif
