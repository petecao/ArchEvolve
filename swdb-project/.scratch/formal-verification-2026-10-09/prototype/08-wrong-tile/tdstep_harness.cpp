// PROTOTYPE (ticket 08), throwaway. Created 2026-10-11 ET.
// The authors' TDStepMAA MAA path (apps/dx100/benchmarks/gapbs/src/bfs.cc:66-185), one thread,
// on the strict-layer port, over every graph within the declared bounds.
//
// Bounds: N vertices, at most MAXE directed edges, a frontier of exactly TILE_SIZE distinct
// visited vertices (one full tile, so the MAA path is taken), any parent[] state.
// Variants (-DWAIT_VARIANT=):
//   0 the authors' wait_ready(tile3)            (tile3 is the store's source)
//   1 the wait removed                          (seeded bug)
//   2 wait_ready(tile6)                         (seeded bug: a tile the store does not name)
//   3 wait_ready(tile7)                         (seeded bug: names the compare, not the store)
//   4 wait_ready(tile5)                         (the store's result; calibration 1.1's patch)
// Rule: -DSWDB_STRICT_WAIT_RULE_GEM5 for the gem5 rule (certify 1.7); without it, the old rule.
// Properties:
//   P1 hazard: when the CPU reads tile0, tile4 and tile5, their writers have finished.
//   P2 function: one BFS level step. Already-visited parents unchanged; a vertex is newly visited
//      iff some frontier vertex has an edge to it; its parent is such a frontier vertex; the next
//      frontier holds each newly visited vertex exactly once.
// Harness edits to the authors' code, each marked "EDIT" below.
#include "port/strict_port.hpp"
#ifndef N
#define N 4
#endif
#ifndef MAXE
#define MAXE 4
#endif
#ifndef WAIT_VARIANT
#define WAIT_VARIANT 0
#endif
#define F TILE_SIZE
static_assert(NUM_CORES == 1, "single thread");
#ifdef NATIVE  // random testing driver: argv[1] is the seed; a failed assumption exits 0
static unsigned seed_state = 1;
static int __VERIFIER_nondet_int() { seed_state = seed_state * 1103515245u + 12345u; return int((seed_state >> 16) % 6) - 1; }
static void __VERIFIER_assume(int c) { if (!c) std::exit(0); }
#else
extern "C" int __VERIFIER_nondet_int();
extern "C" void __VERIFIER_assume(int);
#endif
typedef int32_t NodeID;

static NodeID queue_shared[F];        // queue.shared, frontier [0, F)
static int32_t offsets[N + 1];        // VertexOffsets
static NodeID neighbors[MAXE];        // g.out_neighbors_
static NodeID parent[N];
static NodeID parent0[N];             // parent[] before the step
static NodeID next_frontier[MAXE];    // EDIT: lqueue (QueueBuffer) -> a plain array
static int next_count = 0;

static bool cpu_may_read(int t) {     // P1 probe into the port's state
  return swdb_strict::ops[swdb_strict::tiles[t].writer].covered; }

#ifdef NATIVE
int main(int argc, char **argv) {
  seed_state = argc > 1 ? unsigned(std::atoi(argv[1])) : 1;
#else
int main() {
#endif
  // ---- nondeterministic graph and BFS state within bounds
#ifdef DEGREES  // shape mode: frontier = vertices 0..F-1 (WLOG by relabeling), their out-degrees fixed
  const int degree[F] = {DEGREES};  // e.g. -DDEGREES=1,3 ; non-frontier vertices: degree 0 (never read)
  offsets[0] = 0;
  for (int v = 0; v < N; ++v) offsets[v + 1] = offsets[v] + (v < F ? degree[v] : 0);
  static_assert(F <= N, "frontier fits");
  __VERIFIER_assume(offsets[N] <= MAXE);
#else
  offsets[0] = 0;
  for (int v = 0; v < N; ++v) { offsets[v + 1] = __VERIFIER_nondet_int();
    __VERIFIER_assume(offsets[v + 1] >= offsets[v] && offsets[v + 1] <= MAXE); }
#endif
  for (int e = 0; e < MAXE; ++e) { neighbors[e] = __VERIFIER_nondet_int();
    __VERIFIER_assume(neighbors[e] >= 0 && neighbors[e] < N); }
  for (int v = 0; v < N; ++v) { parent[v] = __VERIFIER_nondet_int();
    __VERIFIER_assume(parent[v] >= -1 && parent[v] < N); parent0[v] = parent[v]; }
  for (int k = 0; k < F; ++k) {
#ifdef DEGREES
    queue_shared[k] = k;
#else
    queue_shared[k] = __VERIFIER_nondet_int();
#endif
    __VERIFIER_assume(queue_shared[k] >= 0 && queue_shared[k] < N);
    __VERIFIER_assume(parent[queue_shared[k]] >= 0);                    // frontier is visited
    for (int m = 0; m < k; ++m) __VERIFIER_assume(queue_shared[m] != queue_shared[k]); }

  // ---- DOBFSMAA setup (bfs.cc:373-394), thread 0
  alloc_MAA(); init_MAA();
  int tile0 = get_new_tile<int>(), tile1 = get_new_tile<int>(), tile2 = get_new_tile<int>(), tile3 = get_new_tile<int>();
  int tile4 = get_new_tile<int>(), tile5 = get_new_tile<int>(), tile6 = get_new_tile<int>(), tile7 = get_new_tile<int>();
  int reg0 = get_new_reg<int>(), reg1 = get_new_reg<int>(), regOne = get_new_reg<int>(), regZero = get_new_reg<int>();
  get_new_reg<int>(); get_new_reg<int>();
  int last_i_reg = get_new_reg<int>(), last_j_reg = get_new_reg<int>();

  // ---- TDStepMAA (bfs.cc:66-185), MAA path, tid = 0
  clear_mem_region();
  add_mem_region(queue_shared, queue_shared + F);
  add_mem_region(offsets, offsets + N + 1);
  add_mem_region(neighbors, neighbors + MAXE);
  add_mem_region(parent, parent + N);
  maa_const<int>(1, regOne);
  maa_const<int>(0, regZero);
  uint32_t *tile0Ptr = get_cacheable_tile_pointer<uint32_t>(tile0);
  uint32_t *tile4Ptr = get_cacheable_tile_pointer<uint32_t>(tile4);
  int *tile5Ptr = get_cacheable_tile_pointer<int>(tile5);
  int idx = 0, len = F;
  while (idx < len) {
    const int tile_size = TILE_SIZE;   // EDIT: the authors pick 1024..32768 from the queue length
    int min = idx;                     // EDIT: + tid * tile_size with tid = 0
    int max = min + tile_size;
    maa_const<int>((int)min, reg0);
    maa_const<int>((int)max, reg1);
    maa_stream_load(queue_shared, reg0, reg1, regOne, tile0);
    maa_indirect_load<int>(offsets, tile0, tile1);
    maa_indirect_load<int>(&offsets[1], tile0, tile2);
    maa_const<int>(0, last_i_reg);
    maa_const<int>(-1, last_j_reg);
    int curr_tile7_size = 0;
    do {
      maa_range_loop<int>(last_i_reg, last_j_reg, tile1, tile2, regOne, tile6, tile7);
      maa_indirect_load<int>(neighbors, tile7, tile0);
      maa_indirect_load<int>((NodeID *)(queue_shared + min), tile6, tile3);
      wait_ready(tile7);
      curr_tile7_size = get_tile_size(tile7);
      if (curr_tile7_size == 0) break;
      {  // EDIT: #pragma omp critical dropped (one thread)
        maa_indirect_load<int>(parent, tile0, tile7);
        maa_alu_scalar<int>(tile7, regZero, tile4, Operation_t::LT_OP);
        maa_indirect_store_vector<int>(parent, tile0, tile3, tile4, tile5);
#if WAIT_VARIANT == 0
        wait_ready(tile3);
#elif WAIT_VARIANT == 2
        wait_ready(tile6);
#elif WAIT_VARIANT == 3
        wait_ready(tile7);
#elif WAIT_VARIANT == 4
        wait_ready(tile5);
#endif
      }
#ifndef NO_P1
      assert(cpu_may_read(tile0) && cpu_may_read(tile4) && cpu_may_read(tile5) && "P1_cpu_reads_finished_data");
#endif
      for (int i = 0; i < curr_tile7_size; i++) {
        if (tile4Ptr[i] && tile5Ptr[i] < 0) {
          assert(next_count < MAXE && "P2_next_frontier_capacity");
          next_frontier[next_count++] = tile0Ptr[i];
        }
      }
    } while (curr_tile7_size > 0);
    idx += NUM_CORES * tile_size;
  }

  // ---- P2: the step's postcondition
#ifndef NO_P2
  for (int v = 0; v < N; ++v) {
    bool reachable = false;
    for (int k = 0; k < F; ++k) { const int u = queue_shared[k];
      for (int e = offsets[u]; e < offsets[u + 1]; ++e) if (neighbors[e] == v) reachable = true; }
    int pushed = 0;
    for (int q = 0; q < next_count; ++q) if (next_frontier[q] == NodeID(v)) ++pushed;
    if (parent0[v] >= 0) {
      assert(parent[v] == parent0[v] && "P2_visited_parent_unchanged");
      assert(pushed == 0 && "P2_visited_not_pushed");
    } else {
      assert((parent[v] >= 0) == reachable && "P2_visited_iff_reachable");
      assert(pushed == (reachable ? 1 : 0) && "P2_pushed_exactly_once");
      if (reachable) {
        bool valid = false; const int p = parent[v];
        for (int k = 0; k < F; ++k) if (queue_shared[k] == p)
          for (int e = offsets[p]; e < offsets[p + 1]; ++e) if (neighbors[e] == v) valid = true;
        assert(valid && "P2_parent_is_frontier_neighbor");
      }
    }
  }
  for (int q = 0; q < next_count; ++q)
    assert(next_frontier[q] < uint32_t(N) && "P2_pushed_is_a_vertex");
#endif  // NO_P2
#ifdef NATIVE
  std::printf("REACHED_END edges=%d next=%d\n", offsets[N], next_count);
#endif
  return 0;
}
