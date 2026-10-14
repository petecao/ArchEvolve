// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. Proof unit 2: one call of the authors' TDStepMAA
// (apps/dx100/benchmarks/gapbs/src/bfs.cc:63-225, BFS calibration code), copied below. Every
// change to the authors' code is marked EDIT or PROBE:
//   EDIT 1: the tile-size ladder (bfs.cc:107-148) has no rung for TILE_SIZE 2 (its #else is
//           assert(false)); the scaled ladder takes one full tile per core, else the CPU path.
//           The authors' test is `>`; with `>` a frontier of 2 never fills 2 lanes, so `>=`.
//   EDIT 2: `__restrict__ uint32_t *p` (GCC accepts, clang 22 rejects) -> `uint32_t *__restrict__ p`.
//   PROBE: before the CPU reads tile0/tile4/tile5, the harness probe checks the tiles are ready
//          (map 12 item 3; map 08's P1 at the same place).
//   Comment-only lines of the original are dropped; `#pragma omp` lines stay (no -fopenmp).
// Controls (-DMAA_CONTROL=<n>), TDStepMAA's single-thread controls (ticket 06 assumption):
//   1 wait_deleted       its wait_ready(tile3) deleted (map 12 item 9)
//   2 old_wait_rule      the authors' wait under the old wait rule (unit.saw swaps the wait summary)
//   3 cpu_read_parent    a same-thread CPU read of parent while its DX100 store is unfinished
//   4 wait_tile6         a wait on a tile the store does not name (map 08)
//   5 wait_tile7         a wait on the compare's tile (map 08)
#include "unit_common.hpp"
#ifndef MAA_CONTROL
#define MAA_CONTROL 0
#endif

int tiles0[NUM_CORES], tiles1[NUM_CORES], tiles2[NUM_CORES], tiles3[NUM_CORES], tiles4[NUM_CORES], tiles5[NUM_CORES], tilesi[NUM_CORES], tilesj[NUM_CORES];
int regs0[NUM_CORES], regs1[NUM_CORES], regs2[NUM_CORES], regs3[NUM_CORES], regs4[NUM_CORES], regs5[NUM_CORES], last_i_regs[NUM_CORES], last_j_regs[NUM_CORES];

void TDStepMAA(const Graph &g, pvector<SGOffset> &VertexOffsets, pvector<NodeID> &parent, SlidingQueue<NodeID> &queue, int num_nodes, int num_edges) {
#ifdef GEM5
    clear_mem_region();
    add_mem_region(queue.beginp(), queue.endp());                   // 6
    add_mem_region(VertexOffsets.beginp(), VertexOffsets.endp());   // 7
    add_mem_region(g.out_neighbors_, &g.out_neighbors_[num_edges]); // 8
    add_mem_region(parent.beginp(), parent.endp());                 // 9
#endif
#pragma omp parallel
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
        QueueBuffer<NodeID> lqueue(queue);
        maa_const<int>(1, regOne);
        maa_const<int>(0, regZero);
        uint32_t *__restrict__ tile0Ptr = get_cacheable_tile_pointer<uint32_t>(tile0);  // EDIT 2
        uint32_t *__restrict__ tile4Ptr = get_cacheable_tile_pointer<uint32_t>(tile4);  // EDIT 2
        int *tile5Ptr = get_cacheable_tile_pointer<int>(tile5);
        int idx = (int)queue.shared_out_start;
        int len = (int)queue.shared_out_end;
        while (idx < len) {
            int current_len_size = len - idx;
#if TILE_SIZE == 2
            const int tile_size = current_len_size >= NUM_CORES * 2 ? 2 : -1;  // EDIT 1
#else
#error "spike build: TILE_SIZE 2 only"
#endif
            if (tile_size != -1) {
                int min = idx + tid * tile_size;
                int max = min + tile_size;
                maa_const<int>((int)min, reg0);
                maa_const<int>((int)max, reg1);
                maa_stream_load(queue.shared, reg0, reg1, regOne, tile0);
                maa_indirect_load<int>(VertexOffsets.start_, tile0, tile1);
                maa_indirect_load<int>(&VertexOffsets.start_[1], tile0, tile2);
                maa_const<int>(0, last_i_reg);
                maa_const<int>(-1, last_j_reg);
                int curr_tile7_size = 0;
                do {
                    maa_range_loop<int>(last_i_reg, last_j_reg, tile1, tile2, regOne, tile6, tile7);
                    maa_indirect_load<int>(g.out_neighbors_, tile7, tile0);
                    maa_indirect_load<int>((NodeID *)(queue.shared + min), tile6, tile3);
                    wait_ready(tile7);
                    curr_tile7_size = get_tile_size(tile7);
                    if (curr_tile7_size == 0) {
                        break;
                    }
#pragma omp critical
                    {
                        maa_indirect_load<int>(parent.data(), tile0, tile7);
                        maa_alu_scalar<int>(tile7, regZero, tile4, Operation_t::LT_OP);
                        maa_indirect_store_vector<int>(parent.data(), tile0, tile3, tile4, tile5);
#if MAA_CONTROL == 3
                        swdb_probe_cpu(SWDB_REGION_PARENT, 0);  // CONTROL 3: CPU read of parent
                        (void)*(volatile NodeID *)&parent[0];
#endif
#if MAA_CONTROL == 0 || MAA_CONTROL == 2 || MAA_CONTROL == 3
                        wait_ready(tile3);
#elif MAA_CONTROL == 4
                        wait_ready(tile6);
#elif MAA_CONTROL == 5
                        wait_ready(tile7);
#endif
                    }
                    swdb_probe_tile_read(tile0);  // PROBE
                    swdb_probe_tile_read(tile4);  // PROBE
                    swdb_probe_tile_read(tile5);  // PROBE
#pragma omp simd aligned(tile4Ptr, tile0Ptr, tile5Ptr : 16) simdlen(4)
                    for (int i = 0; i < curr_tile7_size; i++) {
                        if (tile4Ptr[i] && tile5Ptr[i] < 0) {
                            lqueue.push_back(tile0Ptr[i]);
                        }
                    }
                } while (curr_tile7_size > 0);
                idx += NUM_CORES * tile_size;
            } else {
#pragma omp barrier
#pragma omp for schedule(dynamic, 64)
                for (int i = idx; i < len; i++) {
                    NodeID u = queue.shared[i];
                    for (int j = VertexOffsets[u]; j < VertexOffsets[u + 1]; j++) {
                        NodeID v = g.out_neighbors_[j];
                        NodeID curr_val = parent[v];
                        if (curr_val < 0) {
                            if (compare_and_swap(parent[v], curr_val, u)) {
                                parent[v] = u;
                                lqueue.push_back(v);
                            }
                        }
                    }
                }
                idx = len;
            }
        }

        lqueue.flush();
    }
#ifdef GEM5
    clear_mem_region();
#endif
}

// The harness entry SAW verifies. Tiles and registers as DOBFSMAA allocates them for thread 0
// (bfs.cc:382-397): tiles 0..7, registers 0..7, in declaration order.
void swdb_unit_maa(int nf) {
  tiles0[0] = 0; tiles1[0] = 1; tiles2[0] = 2; tiles3[0] = 3; tiles4[0] = 4; tiles5[0] = 5; tilesi[0] = 6; tilesj[0] = 7;
  regs0[0] = 0; regs1[0] = 1; regs2[0] = 2; regs3[0] = 3; regs4[0] = 4; regs5[0] = 5; last_i_regs[0] = 6; last_j_regs[0] = 7;
  for (int v = 0; v < SPIKE_V; ++v) g_parent0[v] = g_parent[v];
  // Member-wise set-up: brace-initialized aggregates of global addresses become constant globals
  // whose initializers SAW cannot allocate ("Global symbol not allocated").
  Graph g; g.offsets_ = g_offsets; g.out_neighbors_ = g_neighbors;
  pvector<SGOffset> offsets; offsets.start_ = g_offsets; offsets.n_ = SPIKE_V + 1;
  pvector<NodeID> parent; parent.start_ = g_parent; parent.n_ = SPIKE_V;
  SlidingQueue<NodeID> queue; queue.shared = g_queue; queue.shared_in = size_t(nf);
  queue.shared_out_start = 0; queue.shared_out_end = size_t(nf);
  TDStepMAA(g, offsets, parent, queue, SPIKE_V, g_offsets[SPIKE_V]);
  swdb_check_p2(nf, queue.shared_in);
}
