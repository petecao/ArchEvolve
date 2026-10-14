// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. Proof unit 2, hand-lowered to C:
// one call of the authors' TDStepMAA as ticket 06 verified it with SAW (../06-two-lanes/unit_maa.cpp:
// apps/dx100/benchmarks/gapbs/src/bfs.cc:63-225 with the same EDIT 1, EDIT 2, PROBE lines and
// controls). Lowering rules as in unit_peter.c: templates -> int32_t / uint32_t, references ->
// pointers, pvector::operator[](size_t) -> start_[(size_t)i], OpenMP pragmas dropped (one thread),
// __sync_bool_compare_and_swap -> a plain compare and store, maa_* -> stubs (dx100_stubs.h).
// Controls (-DMAA_CONTROL=<n>), as in unit_maa.cpp:
//   1 wait_deleted       its wait_ready(tile3) deleted (map 12 item 9)
//   2 old_wait_rule      the authors' wait under the old wait rule (build adds -DSWDB_OLD_WAIT_RULE)
//   3 cpu_read_parent    a same-thread CPU read of parent while its DX100 store is unfinished
//   4 wait_tile6         a wait on a tile the store does not name (map 08)
//   5 wait_tile7         a wait on the compare's tile (map 08)
#include "common.h"
#ifndef MAA_CONTROL
#define MAA_CONTROL 0
#endif

// spike_api.hpp compare_and_swap: the harness probe, then __sync_bool_compare_and_swap (one thread).
static int compare_and_swap(int32_t *x, int32_t old_val, int32_t new_val) {
  dx_probe_cpu(SWDB_REGION_PARENT, 1);
  if (*x == old_val) { *x = new_val; return 1; }
  return 0;
}

int tiles0[NUM_CORES], tiles1[NUM_CORES], tiles2[NUM_CORES], tiles3[NUM_CORES], tiles4[NUM_CORES], tiles5[NUM_CORES], tilesi[NUM_CORES], tilesj[NUM_CORES];
int regs0[NUM_CORES], regs1[NUM_CORES], regs2[NUM_CORES], regs3[NUM_CORES], regs4[NUM_CORES], regs5[NUM_CORES], last_i_regs[NUM_CORES], last_j_regs[NUM_CORES];

void TDStepMAA(const Graph *g, pvector_i32 *VertexOffsets, pvector_i32 *parent, SlidingQueue *queue, int num_nodes, int num_edges) {
  (void)num_nodes; (void)num_edges;
  {
    int tile0, tile1, tile2, tile3, tile4, tile5, tile6, tile7;
    int reg0, reg1, regOne, regZero, last_i_reg, last_j_reg;
    int tid = omp_get_thread_num();
    tile0 = tiles0[tid];
    tile1 = tiles1[tid];
    tile2 = tiles2[tid];
    tile3 = tiles3[tid];
    tile4 = tiles4[tid];
    tile5 = tiles5[tid];
    tile6 = tilesi[tid];
    tile7 = tilesj[tid];
    reg0 = regs0[tid];
    reg1 = regs1[tid];
    regOne = regs2[tid];
    regZero = regs3[tid];
    last_i_reg = last_i_regs[tid];
    last_j_reg = last_j_regs[tid];
    QueueBuffer lqueue; qb_init(&lqueue, queue);
    dx_const(1, regOne);
    dx_const(0, regZero);
    uint32_t *tile0Ptr = (uint32_t *)get_cacheable_tile_pointer(tile0);  // EDIT 2 (restrict dropped: no effect on one thread)
    uint32_t *tile4Ptr = (uint32_t *)get_cacheable_tile_pointer(tile4);  // EDIT 2
    int *tile5Ptr = get_cacheable_tile_pointer(tile5);
    int idx = (int)queue->shared_out_start;
    int len = (int)queue->shared_out_end;
    while (idx < len) {
      int current_len_size = len - idx;
      const int tile_size = current_len_size >= NUM_CORES * 2 ? 2 : -1;  // EDIT 1
      if (tile_size != -1) {
        int min = idx + tid * tile_size;
        int max = min + tile_size;
        dx_const((int)min, reg0);
        dx_const((int)max, reg1);
        dx_stream_load(queue->shared, reg0, reg1, regOne, tile0, -1);
        dx_gather(VertexOffsets->start_, tile0, tile1, -1);
        dx_gather(&VertexOffsets->start_[1], tile0, tile2, -1);
        dx_const(0, last_i_reg);
        dx_const(-1, last_j_reg);
        int curr_tile7_size = 0;
        do {
          dx_range_loop(last_i_reg, last_j_reg, tile1, tile2, regOne, tile6, tile7, -1);
          dx_gather(g->out_neighbors_, tile7, tile0, -1);
          dx_gather((NodeID *)(queue->shared + min), tile6, tile3, -1);
          dx_wait(tile7);
          curr_tile7_size = dx_get_tile_size(tile7);
          if (curr_tile7_size == 0) {
            break;
          }
          {   // #pragma omp critical
            dx_gather(parent->start_, tile0, tile7, -1);
            dx_alu_scalar(tile7, regZero, tile4, LT_OP, -1);
            dx_store_vector(parent->start_, tile0, tile3, tile4, tile5);
#if MAA_CONTROL == 3
            dx_probe_cpu(SWDB_REGION_PARENT, 0);  // CONTROL 3: CPU read of parent
            (void)*(volatile NodeID *)&parent->start_[0];
#endif
#if MAA_CONTROL == 0 || MAA_CONTROL == 2 || MAA_CONTROL == 3
            dx_wait(tile3);
#elif MAA_CONTROL == 4
            dx_wait(tile6);
#elif MAA_CONTROL == 5
            dx_wait(tile7);
#endif
          }
          dx_probe_tile_read(tile0);  // PROBE
          dx_probe_tile_read(tile4);  // PROBE
          dx_probe_tile_read(tile5);  // PROBE
          for (int i = 0; i < curr_tile7_size; i++) {
            if (tile4Ptr[i] && tile5Ptr[i] < 0) {
              qb_push_back(&lqueue, (NodeID)tile0Ptr[i]);
            }
          }
        } while (curr_tile7_size > 0);
        idx += NUM_CORES * tile_size;
      } else {
        for (int i = idx; i < len; i++) {
          NodeID u = queue->shared[i];
          for (int j = VertexOffsets->start_[(size_t)u]; j < VertexOffsets->start_[(size_t)(u + 1)]; j++) {
            NodeID v = g->out_neighbors_[j];
            NodeID curr_val = parent->start_[(size_t)v];
            if (curr_val < 0) {
              if (compare_and_swap(&parent->start_[(size_t)v], curr_val, u)) {
                parent->start_[(size_t)v] = u;
                qb_push_back(&lqueue, v);
              }
            }
          }
        }
        idx = len;
      }
    }
    qb_flush(&lqueue);
  }
}

// The harness entry (unit_maa.cpp swdb_unit_maa). Tiles and registers as DOBFSMAA allocates them
// for thread 0 (bfs.cc:382-397): tiles 0..7, registers 0..7, in declaration order.
void swdb_unit_maa(int nf) {
  tiles0[0] = 0; tiles1[0] = 1; tiles2[0] = 2; tiles3[0] = 3; tiles4[0] = 4; tiles5[0] = 5; tilesi[0] = 6; tilesj[0] = 7;
  regs0[0] = 0; regs1[0] = 1; regs2[0] = 2; regs3[0] = 3; regs4[0] = 4; regs5[0] = 5; last_i_regs[0] = 6; last_j_regs[0] = 7;
  for (int v = 0; v < SPIKE_V; ++v) g_parent0[v] = g_parent[v];
  Graph g; g.offsets_ = g_offsets; g.out_neighbors_ = g_neighbors;
  pvector_i32 offsets; offsets.start_ = g_offsets; offsets.n_ = SPIKE_V + 1;
  pvector_i32 parent; parent.start_ = g_parent; parent.n_ = SPIKE_V;
  SlidingQueue queue; queue.shared = g_queue; queue.shared_in = (size_t)nf;
  queue.shared_out_start = 0; queue.shared_out_end = (size_t)nf;
  TDStepMAA(&g, &offsets, &parent, &queue, SPIKE_V, g_offsets[SPIKE_V]);
  swdb_check_p2(nf, queue.shared_in);
}
#define SWDB_UNIT_MAA 1
#include "harness.h"
