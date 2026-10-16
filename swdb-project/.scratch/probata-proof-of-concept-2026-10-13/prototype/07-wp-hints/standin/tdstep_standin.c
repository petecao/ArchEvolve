// PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
// Hand-made C stand-in for the C lowering (ticket 21) of one TDStep call with Peter's read offload
// (library/dx100/bfs_read_offload.inc, GEM5 build), threads = 1. C++ names are kept (map 16 item 3).
// The lowering inserts a hazard check (`check hazard_*`) at each tile-pointer read (map 12 item 3).
// Stand-in fix (t07c, 2026-10-14 ET): TDStep's assigns names queue->shared[queue->shared_in .. 2^65 - 1]
// instead of the infinite range [queue->shared_in ..]; WP 33 proves no write into an infinite assigns range
// (dev probe t07c/dev/assigns-probe). 2^65 - 1 lies above every index the queue can write: a size_t
// shared_in plus at most SWDB_LQUEUE_CAPACITY buffered entries. Same frame for every reachable index.
// Every data dimension is symbolic; TILE_SIZE, SWDB_CHUNK_SIZE and SWDB_FRONTIER_THRESHOLD are
// symbolic constants limited by their legality clauses (map 19 item 2).
// `/* @anchor ... */` comments are hint anchors: `global` (definitions), `stmt:<name>` (assert,
// ghost statement or declaration) and `loop:<name>` (loop invariant, assigns, variant).
#include "dxc_summaries.h"
#include "gapbs_models.h"
#include "bfs_unit.h"

static dxc_context swdb_contexts[1];          /* NUM_CORES = 1 */
static bool swdb_acceleration_enabled;        /* any value */
extern const int SWDB_FRONTIER_THRESHOLD;     /* knob, only compared: symbolic, >= 1 */
extern const unsigned SWDB_CHUNK_SIZE;        /* knob: symbolic, 1 .. TILE_SIZE */

/* @anchor global */

/*@ requires guard_sizes: 0 <= num_nodes <= 1073741823 && 0 <= num_edges <= 1073741823;
    requires knobs: 1 <= SWDB_FRONTIER_THRESHOLD && 1 <= SWDB_CHUNK_SIZE <= TILE_SIZE <= 65535;
    requires \valid_read(g) && \valid(VertexOffsets) && \valid(parent) && \valid(queue);
    // Only fields/cells actually read need initialized values; padding is irrelevant.
    requires initialized_metadata: \initialized(&g->out_neighbors_) &&
      \initialized(&VertexOffsets->start_) && \initialized(&VertexOffsets->end_size_) &&
      \initialized(&VertexOffsets->end_capacity_) && \initialized(&parent->start_) &&
      \initialized(&parent->end_size_) && \initialized(&parent->end_capacity_);
    requires initialized_inputs: \initialized(VertexOffsets->start_ + (0 .. num_nodes)) &&
      \initialized(g->out_neighbors_ + (0 .. num_edges - 1)) &&
      \initialized(parent->start_ + (0 .. num_nodes - 1));
    requires initialized_queue_prefix: gapbs_queue_domain(queue) &&
      \initialized(queue->shared + (0 .. queue->shared_in - 1));
    requires csr_offsets: \valid(VertexOffsets->start_ + (0 .. num_nodes)) &&
      VertexOffsets->start_[0] == 0 && VertexOffsets->start_[num_nodes] == num_edges &&
      (\forall integer v; 0 <= v <= num_nodes ==> 0 <= VertexOffsets->start_[v] <= num_edges) &&
      (\forall integer v; 0 <= v < num_nodes ==> VertexOffsets->start_[v] <= VertexOffsets->start_[v + 1]);
    requires csr_neighbors: \valid_read(g->out_neighbors_ + (0 .. num_edges - 1)) &&
      (\forall integer e; 0 <= e < num_edges ==> 0 <= g->out_neighbors_[e] < num_nodes);
    requires parent_valid: \valid(parent->start_ + (0 .. num_nodes - 1));
    // Representation of the live pvector ranges used by registration/accessors.
    requires vector_ranges: gapbs_nodeid_span(VertexOffsets->start_, (integer)num_nodes + 1) &&
      VertexOffsets->end_size_ == VertexOffsets->start_ + num_nodes + 1 &&
      \object_pointer(VertexOffsets->end_capacity_) &&
      \base_addr(VertexOffsets->start_) == \base_addr(VertexOffsets->end_capacity_) &&
      VertexOffsets->end_size_ <= VertexOffsets->end_capacity_ &&
      \offset(VertexOffsets->end_capacity_) - \offset(VertexOffsets->start_) <= (integer)PTRDIFF_MAX * sizeof(SGOffset) &&
      gapbs_nodeid_span(parent->start_, num_nodes) &&
      parent->end_size_ == parent->start_ + num_nodes &&
      \object_pointer(parent->end_capacity_) &&
      \base_addr(parent->start_) == \base_addr(parent->end_capacity_) &&
      parent->end_size_ <= parent->end_capacity_ &&
      \offset(parent->end_capacity_) - \offset(parent->start_) <= (integer)PTRDIFF_MAX * sizeof(NodeID) &&
      gapbs_nodeid_span(g->out_neighbors_, num_edges);
    requires queue_window: \valid(queue->shared + (0 .. queue->shared_max_size - 1)) &&
      queue->shared_out_start <= queue->shared_out_end <= queue->shared_in <= queue->shared_max_size <= 1073741823 &&
      (\forall integer p; queue->shared_out_start <= p < queue->shared_out_end ==> 0 <= queue->shared[p] < num_nodes);
    // DOBFS allocates num_nodes slots. Its occupied prefix contains distinct
    // already-visited vertices; newly claimed vertices consume the remaining
    // finite vertex domain. This is a caller-history domain, not a promised
    // final occupancy or a precomputed proof hint (source repair 2026-10-16 ET).
    requires queue_storage: gapbs_queue_domain(queue) && queue->shared_max_size == num_nodes;
    requires occupied_visited: \forall integer p; 0 <= p < queue->shared_in ==>
      0 <= queue->shared[p] < num_nodes && parent->start_[queue->shared[p]] >= 0;
    requires occupied_distinct: \forall integer p, q; 0 <= p < q < queue->shared_in ==>
      queue->shared[p] != queue->shared[q];
    requires separation: bfs_distinct_blocks(\base_addr(VertexOffsets->start_), \base_addr(g->out_neighbors_),
      \base_addr(parent->start_), \base_addr(queue->shared), \base_addr(&swdb_lqueue_storage[0]),
      \base_addr(g), \base_addr(VertexOffsets), \base_addr(parent), \base_addr(queue));
    requires context: \forall integer a; 0 <= a < 8 ==>
      dxc_tile_ok(swdb_contexts[0].tile[a]) && dxc_reg_ok(swdb_contexts[0].reg[a]) &&
      (\forall integer b; 0 <= b < a ==> swdb_contexts[0].tile[a] != swdb_contexts[0].tile[b] &&
                                         swdb_contexts[0].reg[a] != swdb_contexts[0].reg[b]);
    requires spd: \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. TILE_SIZE - 1)) && 0 <= dxc_tile_len[t] <= TILE_SIZE &&
      \base_addr(dxc_tile_data[t]) != \base_addr(VertexOffsets->start_) &&
      \base_addr(dxc_tile_data[t]) != \base_addr(g->out_neighbors_) &&
      \base_addr(dxc_tile_data[t]) != \base_addr(parent->start_) &&
      \base_addr(dxc_tile_data[t]) != \base_addr(queue->shared) &&
      \base_addr(dxc_tile_data[t]) != \base_addr(&swdb_lqueue_storage[0]) &&
      (\forall integer t2; 0 <= t2 < t ==> \base_addr(dxc_tile_data[t]) != \base_addr(dxc_tile_data[t2]));
    requires dx100_idle: dxc_idle;
    assigns parent->start_[0 .. num_nodes - 1], queue->shared_in, queue->shared[queue->shared_in .. 36893488147419103231],
      swdb_lqueue_storage[0 .. SWDB_LQUEUE_CAPACITY - 1],
      dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. TILE_SIZE - 1], dxc_tile_len[0 .. DXC_NUM_TILES - 1],
      dxc_reg[0 .. DXC_NUM_REGS - 1], dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures visited_parent_unchanged: \forall integer v; 0 <= v < num_nodes && \old(parent->start_[v]) >= 0 ==>
      parent->start_[v] == \old(parent->start_[v]);
    ensures visited_iff_reachable: \forall integer v; 0 <= v < num_nodes && \old(parent->start_[v]) < 0 ==>
      (parent->start_[v] >= 0 <==> bfs_reach{Pre}(queue, VertexOffsets->start_, g->out_neighbors_, v));
    ensures unreached_unchanged: \forall integer v; 0 <= v < num_nodes && \old(parent->start_[v]) < 0 && parent->start_[v] < 0 ==>
      parent->start_[v] == \old(parent->start_[v]);
    ensures parent_is_frontier_neighbor: \forall integer v; 0 <= v < num_nodes && \old(parent->start_[v]) < 0 && parent->start_[v] >= 0 ==>
      bfs_frontier_edge{Pre}(queue, VertexOffsets->start_, g->out_neighbors_, parent->start_[v], v);
    ensures pushed_are_new: \forall integer i; \old(queue->shared_in) <= i < queue->shared_in ==>
      0 <= queue->shared[i] < num_nodes && \old(parent->start_[queue->shared[i]]) < 0 && parent->start_[queue->shared[i]] >= 0;
    ensures new_are_pushed: \forall integer v; 0 <= v < num_nodes && \old(parent->start_[v]) < 0 && parent->start_[v] >= 0 ==>
      \exists integer i; \old(queue->shared_in) <= i < queue->shared_in && queue->shared[i] == v;
    ensures pushed_once: \forall integer i, j; \old(queue->shared_in) <= i < j < queue->shared_in ==>
      queue->shared[i] != queue->shared[j];
    ensures queue_kept: queue->shared_in >= \old(queue->shared_in) &&
      (\forall integer p; 0 <= p < \old(queue->shared_in) ==> queue->shared[p] == \old(queue->shared[p]));
    ensures dx100_idle_after: dxc_idle;
*/
void TDStep(const Graph *g, struct pvector_SGOffset *VertexOffsets, struct pvector_NodeID *parent,
            struct SlidingQueue_NodeID *queue, int num_nodes, int num_edges) {
  /* @anchor stmt:entry */
  /* #ifdef GEM5 */
  clear_mem_region();
  add_mem_region(SlidingQueue_NodeID_beginp(queue), SlidingQueue_NodeID_endp(queue));
  add_mem_region(pvector_SGOffset_beginp(VertexOffsets), pvector_SGOffset_endp(VertexOffsets));
  add_mem_region((void *)g->out_neighbors_, (void *)&g->out_neighbors_[num_edges]);
  add_mem_region(pvector_NodeID_beginp(parent), pvector_NodeID_endp(parent));
  /* #endif */
  /* #pragma omp parallel: threads = 1, so the region body runs once, on thread 0 */
  {
    struct QueueBuffer_NodeID lqueue;
    QueueBuffer_NodeID_QueueBuffer(&lqueue, queue, 16384);
    /* @anchor stmt:after_lqueue */
    const bool accelerate = swdb_acceleration_enabled && SlidingQueue_NodeID_size(queue) >= (size_t)SWDB_FRONTIER_THRESHOLD;
    /* @anchor stmt:after_accelerate */
    if (accelerate) {
      dxc_context c = swdb_contexts[omp_get_thread_num()];
      __dxc_const_i32(1, c.reg[2]);
      __dxc_const_i32(0, c.reg[3]);
      /* @anchor stmt:before_chunk_loop */
      /* #pragma omp for schedule(dynamic,1): threads = 1, chunks run in order */
      /* @anchor loop:chunk_loop */
      for (size_t begin = queue->shared_out_start; begin < queue->shared_out_end; begin += SWDB_CHUNK_SIZE) {
        /* @anchor stmt:chunk_start */
        const size_t end = std_min_size_t(begin + (size_t)SWDB_CHUNK_SIZE, (size_t)queue->shared_out_end);
        __dxc_const_i32((int32_t)begin, c.reg[0]);
        __dxc_const_i32((int32_t)end, c.reg[1]);
        __dxc_stream_load(queue->shared, c.reg[0], c.reg[1], c.reg[2], c.tile[0]);
        __dxc_gather(pvector_SGOffset_data(VertexOffsets), c.tile[0], c.tile[1]);
        __dxc_gather(pvector_SGOffset_data(VertexOffsets) + 1, c.tile[0], c.tile[2]);
        __dxc_const_i32(0, c.reg[4]);
        __dxc_const_i32(-1, c.reg[5]);
        __dxc_accelerated_chunk();
        /* @anchor stmt:before_range_loop */
        /* @anchor loop:range_loop */
        for (;;) {
          /* @anchor stmt:range_start */
          __dxc_range_loop(c.reg[4], c.reg[5], c.tile[1], c.tile[2], c.reg[2], c.tile[6], c.tile[7]);
          /* @anchor stmt:after_range_call */
          __dxc_wait(c.tile[7]);
          /* @anchor stmt:after_wait7 */
          const unsigned count = __dxc_tile_size(c.tile[7]);
          if (count == 0) break;
          /* @anchor stmt:after_count */
          __dxc_gather(g->out_neighbors_, c.tile[7], c.tile[0]);
          /* @anchor stmt:after_neighbor_gather */
          __dxc_gather(queue->shared + begin, c.tile[6], c.tile[3]);
          __dxc_gather(pvector_NodeID_data(parent), c.tile[0], c.tile[5]);
          /* @anchor stmt:after_gathers */
          __dxc_wait(c.tile[3]);
          __dxc_wait(c.tile[5]);
          /* @anchor stmt:after_waits */
          int *vertices = __dxc_tile_pointer(c.tile[0]);
          int *frontier = __dxc_tile_pointer(c.tile[3]);
          int *hints = __dxc_tile_pointer(c.tile[5]);
          /* @anchor stmt:before_k_loop */
          /* @anchor loop:k_loop */
          for (unsigned k = 0; k < count; ++k) {
            /* @anchor stmt:k_start */
            /*@ check hazard_vertices_read: dxc_cpu_may_read(vertices + k); */
            const NodeID v = vertices[k];
            /*@ check hazard_frontier_read: dxc_cpu_may_read(frontier + k); */
            const NodeID u = frontier[k];
            /*@ check hazard_hints_read: dxc_cpu_may_read(hints + k); */
            const NodeID hint = hints[k];
            /* @anchor stmt:after_reads */
            const bool claimed = hint < 0 && compare_and_swap(pvector_NodeID_operator_index(parent, (size_t)v), hint, u);
            /* @anchor stmt:after_cas */
            if (claimed) {
              /* @anchor stmt:claimed_start */
              *pvector_NodeID_operator_index(parent, (size_t)v) = u;
              /* @anchor stmt:after_parent_store */
              QueueBuffer_NodeID_push_back(&lqueue, v);
              /* @anchor stmt:after_push */
            }
            /* @anchor stmt:k_end */
          }
          /* @anchor stmt:after_k_loop */
        }
        /* @anchor stmt:after_range_loop */
      }
      /* @anchor stmt:after_chunk_loop */
    } else {
      /* @anchor stmt:before_i_loop */
      /* #pragma omp for nowait: threads = 1 */
      /* @anchor loop:i_loop */
      for (size_t i = queue->shared_out_start; i < queue->shared_out_end; ++i) {
        /* @anchor stmt:i_start */
        const NodeID u = queue->shared[i];
        /* @anchor stmt:before_j_loop */
        /* @anchor loop:j_loop */
        for (int j = *pvector_SGOffset_operator_index(VertexOffsets, (size_t)u);
             j < *pvector_SGOffset_operator_index(VertexOffsets, (size_t)(u + 1)); ++j) {
          /* @anchor stmt:j_start */
          const NodeID v = g->out_neighbors_[j];
          const NodeID value = __atomic_load_n_NodeID(pvector_NodeID_operator_index(parent, (size_t)v), __ATOMIC_RELAXED);
          /* @anchor stmt:after_load */
          if (value < 0 && compare_and_swap(pvector_NodeID_operator_index(parent, (size_t)v), value, u)) {
            /* @anchor stmt:scalar_claimed_start */
            *pvector_NodeID_operator_index(parent, (size_t)v) = u;
            /* @anchor stmt:scalar_after_parent_store */
            QueueBuffer_NodeID_push_back(&lqueue, v);
            /* @anchor stmt:scalar_after_push */
          }
          /* @anchor stmt:j_end */
        }
        /* @anchor stmt:after_j_loop */
      }
      /* @anchor stmt:after_i_loop */
    }
    /* @anchor stmt:before_flush */
    QueueBuffer_NodeID_flush(&lqueue);
    /* @anchor stmt:after_flush */
    QueueBuffer_NodeID_destroy(&lqueue);
  }
  /* #ifdef GEM5: clear_mem_region() */
  clear_mem_region();
  /* @anchor stmt:exit */
}
