/* Differential public TDStep control: original and prospective compiled separately.
   The device double realizes a finite list of range pairs; this is native evidence,
   not the DX100 proof semantics or a formal caller-domain discharge. */
#include "tdstep_standin.c"
#include <assert.h>
#include <stdio.h>

const unsigned TILE_SIZE = 2;
const unsigned SWDB_CHUNK_SIZE = 2;
const int SWDB_FRONTIER_THRESHOLD = 1;
static int regs[8], lengths[8], storage[8][2];
static unsigned cas_calls, load_calls, issues, regions;
static bool cas(NodeID *p, NodeID old, NodeID value) {
  ++cas_calls; bool claimed = *p == old; if (claimed) *p = value; return claimed;
}
static size_t fetch(size_t *p, size_t n) { size_t old = *p; *p += n; return old; }
static NodeID load(const NodeID *p, int order) { (void)order; ++load_calls; return *p; }
#ifndef SWDB_PRIVATE_ARRAY
static NodeID *allocate(size_t n) { assert(n <= SWDB_LQUEUE_CAPACITY); return swdb_lqueue_storage; }
#endif
static NodeID *copy(const NodeID *first, const NodeID *last, NodeID *dest) {
  while (first != last) *dest++ = *first++; return dest;
}
#ifdef SWDB_OUTSLOT
void __sync_bool_compare_and_swap_NodeID_out(NodeID *p, NodeID old, NodeID value, bool *out) { *out = cas(p, old, value); }
void __atomic_load_n_NodeID_out(const NodeID *p, int order, NodeID *out) { *out = load(p, order); }
void __sync_fetch_and_add_size_t_out(size_t *p, size_t n, size_t *out) { *out = fetch(p, n); }
#ifndef SWDB_PRIVATE_ARRAY
void swdb_new_NodeID_array_out(size_t n, NodeID **out) { *out = allocate(n); }
#endif
void std_copy_NodeID_out(const NodeID *first, const NodeID *last, NodeID *dest, size_t count, NodeID **out) {
  assert(last == first + count); *out = copy(first, last, dest);
}
void __dxc_tile_size_out(int tile, uint16_t *out) { *out = (uint16_t)lengths[tile]; }
void __dxc_tile_pointer_out(int tile, int **out) { *out = dxc_tile_data[tile]; }
#else
bool __sync_bool_compare_and_swap_NodeID(NodeID *p, NodeID old, NodeID value) { return cas(p, old, value); }
NodeID __atomic_load_n_NodeID(const NodeID *p, int order) { return load(p, order); }
size_t __sync_fetch_and_add_size_t(size_t *p, size_t n) { return fetch(p, n); }
NodeID *swdb_new_NodeID_array(size_t n) { return allocate(n); }
NodeID *std_copy_NodeID(const NodeID *first, const NodeID *last, NodeID *dest) { return copy(first, last, dest); }
uint16_t __dxc_tile_size(int tile) { return (uint16_t)lengths[tile]; }
int *__dxc_tile_pointer(int tile) { return dxc_tile_data[tile]; }
#endif
#ifndef SWDB_PRIVATE_ARRAY
void swdb_delete_NodeID_array(NodeID *p) { assert(p == swdb_lqueue_storage); }
#endif
void __dxc_const_i32(int32_t value, int reg) { regs[reg] = value; ++issues; }
void __dxc_stream_load(const int *base, int min, int max, int stride, int dst) {
  unsigned n = 0;
  for (int i = regs[min]; i < regs[max]; i += regs[stride]) {
    assert(n < TILE_SIZE); storage[dst][n++] = base[i];
  }
  lengths[dst] = (int)n; ++issues;
}
void __dxc_gather(const int *base, int index, int dst) {
  lengths[dst] = lengths[index];
  for (int i = 0; i < lengths[index]; ++i) storage[dst][i] = base[storage[index][i]];
  ++issues;
}
void __dxc_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  assert(regs[stride] == 1);
  unsigned n = 0;
  for (int row = 0; row < lengths[lower] && n < TILE_SIZE; ++row) {
    for (int col = storage[lower][row]; col < storage[upper][row] && n < TILE_SIZE; ++col) {
      if (row > regs[last_i] || (row == regs[last_i] && col > regs[last_j])) {
        storage[rows][n] = row; storage[columns][n] = col; ++n;
      }
    }
  }
  if (n) { regs[last_i] = storage[rows][n - 1]; regs[last_j] = storage[columns][n - 1]; }
  lengths[rows] = lengths[columns] = (int)n; ++issues;
}
void __dxc_wait(int tile) { (void)tile; ++issues; }
void __dxc_accelerated_chunk(void) { ++issues; }
void clear_mem_region(void) { ++regions; }
void add_mem_region(void *begin, void *end) { assert(begin && end); ++regions; }

static void run(bool accelerate, size_t frontier_count) {
  SGOffset offsets[6] = {0, 4, 6, 7, 7, 7};
  NodeID neighbors[7] = {2, 2, 0, 3, 3, 4, 4};
  NodeID parents[5] = {0, 1, -1, -1, -1};
  NodeID shared[5] = {0, 1};
  struct pvector_SGOffset vo = {offsets, offsets + 6, offsets + 6};
  struct pvector_NodeID pa = {parents, parents + 5, parents + 5};
  struct SlidingQueue_NodeID q = {shared, frontier_count, 0, frontier_count, 5};
  Graph g = {0}; g.out_neighbors_ = neighbors;
  cas_calls = load_calls = issues = regions = 0;
  swdb_acceleration_enabled = accelerate;
  for (unsigned i = 0; i < 8; ++i) {
    swdb_contexts[0].tile[i] = swdb_contexts[0].reg[i] = (int)i;
    dxc_tile_data[i] = storage[i]; lengths[i] = 0; regs[i] = 0;
  }
  TDStep(&g, &vo, &pa, &q, 5, 7);
  assert(parents[0] == 0 && parents[1] == 1);
  if (frontier_count == 2) {
    assert(parents[2] == 0 && parents[3] == 0 && parents[4] == 1);
    assert(q.shared_in == 5 && shared[2] == 2 && shared[3] == 3 && shared[4] == 4);
    // Device hints are a batch snapshot; a duplicate may make one failed CAS.
    assert(cas_calls == (accelerate ? 4u : 3u));
    assert(load_calls == (accelerate ? 0u : 6u));
  } else {
    assert(q.shared_in == 0 && parents[2] == -1 && parents[3] == -1 && parents[4] == -1);
    assert(cas_calls == 0 && load_calls == 0 && issues == 0);
  }
  assert(regions == 6);
  printf("%d %zu %u %u %u %u", accelerate, frontier_count, cas_calls, load_calls, issues, regions);
  for (unsigned i = 0; i < 5; ++i) printf(" %d", parents[i]);
  for (size_t i = 0; i < q.shared_in; ++i) printf(" %d", shared[i]);
  putchar('\n');
}
int main(void) { run(false, 2); run(true, 2); run(false, 0); run(true, 0); return 0; }
