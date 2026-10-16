// PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
// Concrete executable models and the state recorder for the bounded hint falsifier. build.py includes
// this file at the end of an instrumented copy of tdstep_standin.c (one translation unit).
// The DX100 models follow dxc_summaries.h exactly: values as if each command finished at issue, ghost
// pending/dependency state per dxc_issued and dxc_covers. A summary precondition that does not hold
// aborts the run with "PRE <name>": the instance or the model is wrong, never a hint.
// Input (stdin), one instance per line, all integers:
//   n E TILE CHUNK THRESH ACCEL out_start out_end shared_in
//   offsets[0..n] neighbors[0..E-1] parent[0..n-1] shared[0..n-1]
//   tiles[8] regs[8] tile_len[8] dep[64] tile_data[8*TILE]
// Output: JSON lines, one per recorded event; {"inst": i, "end": 1} after each instance.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

unsigned TILE_SIZE;
void TDStep(const Graph *g, struct pvector_SGOffset *VertexOffsets, struct pvector_NodeID *parent,
            struct SlidingQueue_NodeID *queue, int num_nodes, int num_edges);
unsigned SWDB_CHUNK_SIZE;
int SWDB_FRONTIER_THRESHOLD;

#define FZ_MAXN 8
#define FZ_MAXE 16
#define FZ_MAXT 8
#define FZ_LQ_DUMP 32

static SGOffset fz_offsets[FZ_MAXN + 1];
static NodeID fz_neighbors[FZ_MAXE + 1];
static NodeID fz_parent[FZ_MAXN + 1];
static NodeID fz_shared[FZ_MAXN + 1];
static int fz_tiles[DXC_NUM_TILES][FZ_MAXT];
static Graph fz_g;
static struct pvector_SGOffset fz_vo;
static struct pvector_NodeID fz_pv;
static struct SlidingQueue_NodeID fz_q;
static int fz_n, fz_e, fz_inst, fz_seq;

static int dxc_reg_ok_c(int r) { return 0 <= r && r < DXC_NUM_REGS; }
static int dxc_tile_ok_c(int t) { return 0 <= t && t < DXC_NUM_TILES; }

static void fz_pre(int ok, const char *what) {
  if (!ok) { printf("{\"inst\": %d, \"pre\": \"%s\"}\n", fz_inst, what); fflush(stdout); exit(3); }
}

/* ---- pointer descriptors ---- */
struct fz_block { const char *name; const char *base; size_t count; size_t elem; };
static struct fz_block fz_blocks[32];
static int fz_nblocks;
static void fz_reg(const char *name, const void *base, size_t count, size_t elem) {
  fz_blocks[fz_nblocks++] = (struct fz_block){name, (const char *)base, count, elem};
}
static void fz_ptr(const void *p) {
  const char *c = (const char *)p;
  if (!p) { printf("{\"null\": 1}"); return; }
  for (int b = 0; b < fz_nblocks; b++) {
    struct fz_block *k = &fz_blocks[b];
    if (c >= k->base && c <= k->base + k->count * k->elem && (size_t)(c - k->base) % k->elem == 0) {
      printf("{\"b\": \"%s\", \"i\": %ld}", k->name, (long)((c - k->base) / (long)k->elem));
      return;
    }
  }
  printf("{\"b\": \"?\", \"i\": 0}");
}

static void fz_ints(const int *a, int n) {
  printf("[");
  for (int i = 0; i < n; i++) printf(i ? ", %d" : "%d", a[i]);
  printf("]");
}

/* ---- typed local dumpers (C11 _Generic) ---- */
static void fz_d_i64(long long x) { printf("%lld", x); }
static void fz_d_u64(unsigned long long x) { printf("%llu", x); }
static void fz_d_bool(bool x) { printf("%d", x ? 1 : 0); }
static void fz_d_ptr(const void *p) { fz_ptr(p); }
static void fz_d_ctx(dxc_context c) {
  printf("{\"tile\": "); fz_ints(c.tile, 8); printf(", \"reg\": "); fz_ints(c.reg, 8); printf("}");
}
static void fz_d_qb(struct QueueBuffer_NodeID q) {
  printf("{\"in\": %zu, \"local_queue\": ", q.in); fz_ptr(q.local_queue);
  printf(", \"sq\": "); fz_ptr(q.sq); printf(", \"local_size\": %zu}", q.local_size);
}
#define FZ_DUMP(x) _Generic((x), \
  bool: fz_d_bool, int: fz_d_i64, unsigned: fz_d_u64, long: fz_d_i64, unsigned long: fz_d_u64, \
  long long: fz_d_i64, unsigned long long: fz_d_u64, \
  int *: fz_d_ptr, const int *: fz_d_ptr, dxc_context: fz_d_ctx, struct QueueBuffer_NodeID: fz_d_qb)(x)

static int fz_first_local;
#define L(x) do { printf(fz_first_local ? "\"%s\": " : ", \"%s\": ", #x); fz_first_local = 0; FZ_DUMP(x); } while (0);

static void fz_ev_begin(const char *anchor) {
  printf("{\"inst\": %d, \"seq\": %d, \"a\": \"%s\", \"mem\": {", fz_inst, fz_seq++, anchor);
  printf("\"VertexOffsets.start_\": "); fz_ints(fz_offsets, fz_n + 1);
  printf(", \"out_neighbors\": "); fz_ints(fz_neighbors, fz_e);
  printf(", \"parent.start_\": "); fz_ints(fz_parent, fz_n);
  printf(", \"queue.shared\": "); fz_ints(fz_shared, fz_n);
  printf(", \"swdb_lqueue_storage\": "); fz_ints(swdb_lqueue_storage, FZ_LQ_DUMP);
  for (int t = 0; t < DXC_NUM_TILES; t++) { printf(", \"tile%d\": ", t); fz_ints(fz_tiles[t], (int)TILE_SIZE); }
  printf(", \"dxc_tile_len\": "); fz_ints(dxc_tile_len, DXC_NUM_TILES);
  printf(", \"dxc_reg\": "); fz_ints(dxc_reg, DXC_NUM_REGS);
  printf(", \"dxc_pending\": "); fz_ints(dxc_pending, DXC_NUM_TILES);
  printf(", \"dxc_dep\": "); fz_ints(dxc_dep, DXC_NUM_TILES * DXC_NUM_TILES);
  printf(", \"dxc_tile_data\": [");
  for (int t = 0; t < DXC_NUM_TILES; t++) { if (t) printf(", "); fz_ptr(dxc_tile_data[t]); }
  printf("], \"swdb_contexts\": ["); fz_d_ctx(swdb_contexts[0]); printf("]");
  printf(", \"Q\": {\"shared\": "); fz_ptr(fz_q.shared);
  printf(", \"shared_in\": %zu, \"shared_out_start\": %zu, \"shared_out_end\": %zu, \"shared_max_size\": %zu}",
         fz_q.shared_in, fz_q.shared_out_start, fz_q.shared_out_end, fz_q.shared_max_size);
  printf(", \"VO\": {\"start_\": "); fz_ptr(fz_vo.start_); printf(", \"end_size_\": "); fz_ptr(fz_vo.end_size_);
  printf(", \"end_capacity_\": "); fz_ptr(fz_vo.end_capacity_); printf("}");
  printf(", \"PV\": {\"start_\": "); fz_ptr(fz_pv.start_); printf(", \"end_size_\": "); fz_ptr(fz_pv.end_size_);
  printf(", \"end_capacity_\": "); fz_ptr(fz_pv.end_capacity_); printf("}");
  printf(", \"G\": {\"out_neighbors_\": "); fz_ptr(fz_g.out_neighbors_);
  printf(", \"num_nodes_\": %lld, \"num_edges_\": %lld}", (long long)fz_g.num_nodes_, (long long)fz_g.num_edges_);
  printf(", \"scalars\": {\"TILE_SIZE\": %u, \"SWDB_CHUNK_SIZE\": %u, \"SWDB_FRONTIER_THRESHOLD\": %d, "
         "\"swdb_acceleration_enabled\": %d}}, \"loc\": {", TILE_SIZE, SWDB_CHUNK_SIZE, SWDB_FRONTIER_THRESHOLD,
         swdb_acceleration_enabled ? 1 : 0);
  fz_first_local = 1;
}
static void fz_ev_end(void) { printf("}}\n"); }

#define SWDB_EV(anchor, ...) do { fz_ev_begin(anchor); __VA_ARGS__ fz_ev_end(); } while (0)
#define SWDB_LOOPEV(anchor, ...) ({ fz_ev_begin(anchor); __VA_ARGS__ fz_ev_end(); 0; })

/* ---- DX100 models (dxc_summaries.h) ---- */
static int fz_in2(int x, int a, int b) { return x == a || x == b; }
static void fz_issued(int s1, int s2, int d1, int d2) {
  int pend[DXC_NUM_TILES], dep[DXC_NUM_TILES * DXC_NUM_TILES];
  memcpy(pend, dxc_pending, sizeof pend); memcpy(dep, dxc_dep, sizeof dep);
  for (int x = 0; x < DXC_NUM_TILES; x++) {
    int dx = fz_in2(x, d1, d2);
    if (dx) dxc_pending[x] = 1;
    for (int y = 0; y < DXC_NUM_TILES; y++) {
      int v;
      if (dx)
        v = (fz_in2(y, d1, d2) && y != x) || (fz_in2(y, s1, s2) && pend[y] != 0) ||
            (s1 >= 0 && pend[s1] != 0 && dep[s1 * DXC_NUM_TILES + y] != 0) ||
            (s2 >= 0 && pend[s2] != 0 && dep[s2 * DXC_NUM_TILES + y] != 0);
      else
        v = !fz_in2(y, d1, d2) && dep[x * DXC_NUM_TILES + y] != 0;
      dxc_dep[x * DXC_NUM_TILES + y] = v;
    }
  }
}
void __dxc_const_i32(int32_t value, int reg) { fz_pre(dxc_reg_ok_c(reg), "const_i32"); dxc_reg[reg] = value; }
void __dxc_stream_load(const int *base, int minimum, int maximum, int stride, int dst) {
  fz_pre(dxc_reg_ok_c(minimum) && dxc_reg_ok_c(maximum) && dxc_reg_ok_c(stride) && dxc_tile_ok_c(dst), "stream_load ids");
  fz_pre(dxc_reg[stride] == 1 && 0 <= dxc_reg[minimum] && dxc_reg[maximum] - dxc_reg[minimum] <= (int)TILE_SIZE,
         "stream_load range");
  int lo = dxc_reg[minimum], hi = dxc_reg[maximum];
  fz_pre(base == fz_shared ? hi <= (int)fz_q.shared_max_size || hi <= lo : 1, "stream_load valid_read");
  int len = hi > lo ? hi - lo : 0;
  for (int i = 0; i < len; i++) dxc_tile_data[dst][i] = base[lo + i];
  dxc_tile_len[dst] = len;
  fz_issued(-1, -1, dst, -1);
}
static size_t fz_count_of(const int *base) {
  if (base == fz_offsets) return fz_n + 1;
  if (base == fz_offsets + 1) return fz_n;
  if (base == fz_neighbors) return fz_e;
  if (base == fz_parent) return fz_n;
  if (base >= fz_shared && base <= fz_shared + fz_n) return fz_n - (base - fz_shared);
  return 0;
}
void __dxc_gather(const int *base, int index, int dst) {
  fz_pre(dxc_tile_ok_c(index) && dxc_tile_ok_c(dst) && index != dst, "gather ids");
  fz_pre(0 <= dxc_tile_len[index] && dxc_tile_len[index] <= (int)TILE_SIZE, "gather len");
  size_t cnt = fz_count_of(base);
  int tmp[FZ_MAXT];
  for (int i = 0; i < dxc_tile_len[index]; i++) {
    int ix = dxc_tile_data[index][i];
    fz_pre(0 <= ix && (size_t)ix < cnt, "gather valid_read");
    tmp[i] = base[ix];
  }
  for (int i = 0; i < dxc_tile_len[index]; i++) dxc_tile_data[dst][i] = tmp[i];
  dxc_tile_len[dst] = dxc_tile_len[index];
  fz_issued(index, -1, dst, -1);
}
void __dxc_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  fz_pre(dxc_reg_ok_c(last_i) && dxc_reg_ok_c(last_j) && dxc_reg_ok_c(stride) && last_i != last_j, "range ids r");
  fz_pre(dxc_tile_ok_c(lower) && dxc_tile_ok_c(upper) && dxc_tile_ok_c(rows) && dxc_tile_ok_c(columns) &&
         lower != upper && rows != columns && !fz_in2(rows, lower, upper) && !fz_in2(columns, lower, upper), "range ids t");
  fz_pre(dxc_reg[stride] == 1, "range stride");
  int n = dxc_tile_len[lower];
  fz_pre(n == dxc_tile_len[upper] && 0 <= n && n <= (int)TILE_SIZE, "range len");
  int *lo = dxc_tile_data[lower], *hi = dxc_tile_data[upper];
  for (int i = 0; i < n; i++) fz_pre(0 <= lo[i] && lo[i] <= hi[i] && hi[i] <= 1073741823, "range bounds");
  int ci = dxc_reg[last_i], cj = dxc_reg[last_j];
  fz_pre(0 <= ci && ci <= n && (cj == -1 || (ci < n && lo[ci] <= cj && cj < hi[ci])), "range state");
  int len = 0, ri = ci, rj = cj;
  for (int i = ci; i < n && len < (int)TILE_SIZE; i++)
    for (int j = (i == ci && cj != -1) ? cj + 1 : lo[i]; j < hi[i] && len < (int)TILE_SIZE; j++) {
      dxc_tile_data[rows][len] = i; dxc_tile_data[columns][len] = j; len++; ri = i; rj = j;
    }
  dxc_tile_len[rows] = len; dxc_tile_len[columns] = len;
  if (len < (int)TILE_SIZE) { dxc_reg[last_i] = n; dxc_reg[last_j] = -1; }
  else { dxc_reg[last_i] = ri; dxc_reg[last_j] = rj; }
  fz_issued(lower, upper, rows, columns);
}
void __dxc_wait(int tile) {
  fz_pre(dxc_tile_ok_c(tile), "wait id");
  int pend[DXC_NUM_TILES], dep[DXC_NUM_TILES * DXC_NUM_TILES], cov[DXC_NUM_TILES];
  memcpy(pend, dxc_pending, sizeof pend); memcpy(dep, dxc_dep, sizeof dep);
  for (int x = 0; x < DXC_NUM_TILES; x++) cov[x] = pend[tile] != 0 && (x == tile || dep[tile * DXC_NUM_TILES + x] != 0);
  for (int x = 0; x < DXC_NUM_TILES; x++) {
    if (cov[x]) dxc_pending[x] = 0;
    for (int y = 0; y < DXC_NUM_TILES; y++) dxc_dep[x * DXC_NUM_TILES + y] = !cov[x] && dep[x * DXC_NUM_TILES + y] != 0;
  }
}
uint16_t __dxc_tile_size(int tile) {
  fz_pre(dxc_tile_ok_c(tile) && dxc_pending[tile] == 0, "tile_size ready");
  return (uint16_t)dxc_tile_len[tile];
}
int *__dxc_tile_pointer(int tile) { fz_pre(dxc_tile_ok_c(tile), "tile_pointer id"); return dxc_tile_data[tile]; }
void __dxc_accelerated_chunk(void) {}
void clear_mem_region(void) {}
void add_mem_region(void *start, void *end) { (void)start; (void)end; }

/* ---- standard-library and builtin models (gapbs_models.h) ---- */
bool __sync_bool_compare_and_swap_NodeID(NodeID *ptr, NodeID oldval, NodeID newval) {
  if (*ptr == oldval) { *ptr = newval; return true; }
  return false;
}
NodeID __atomic_load_n_NodeID(const NodeID *ptr, int memorder) { (void)memorder; return *ptr; }
size_t __sync_fetch_and_add_size_t(size_t *ptr, size_t value) { size_t o = *ptr; *ptr = o + value; return o; }
NodeID *swdb_new_NodeID_array(size_t n) { fz_pre(n <= SWDB_LQUEUE_CAPACITY, "new"); return &swdb_lqueue_storage[0]; }
void swdb_delete_NodeID_array(NodeID *p) { fz_pre(p == &swdb_lqueue_storage[0], "delete"); }
NodeID *std_copy_NodeID(const NodeID *first, const NodeID *last, NodeID *d_first) {
  fz_pre(first <= last, "copy order");
  if (d_first >= fz_shared && d_first <= fz_shared + fz_n) fz_pre(d_first + (last - first) <= fz_shared + fz_n, "copy dst");
  memmove(d_first, first, (size_t)(last - first) * sizeof(NodeID));
  return d_first + (last - first);
}

/* ---- driver ---- */
static int fz_read(int *x) { return scanf("%d", x) == 1; }
int main(void) {
  int n;
  while (fz_read(&n)) {
    int E, T, C, TH, AC, os, oe, si;
    if (!(fz_read(&E) && fz_read(&T) && fz_read(&C) && fz_read(&TH) && fz_read(&AC) && fz_read(&os) &&
          fz_read(&oe) && fz_read(&si))) return 2;
    if (n < 1 || n > FZ_MAXN || E < 0 || E > FZ_MAXE || T < 1 || T > FZ_MAXT) return 2;
    fz_n = n; fz_e = E; TILE_SIZE = T; SWDB_CHUNK_SIZE = C; SWDB_FRONTIER_THRESHOLD = TH;
    swdb_acceleration_enabled = AC;
    for (int i = 0; i <= n; i++) fz_read(&fz_offsets[i]);
    for (int i = 0; i < E; i++) fz_read(&fz_neighbors[i]);
    for (int i = 0; i < n; i++) fz_read(&fz_parent[i]);
    for (int i = 0; i < n; i++) fz_read(&fz_shared[i]);
    for (int i = 0; i < 8; i++) fz_read(&swdb_contexts[0].tile[i]);
    for (int i = 0; i < 8; i++) fz_read(&swdb_contexts[0].reg[i]);
    for (int i = 0; i < 8; i++) fz_read(&dxc_tile_len[i]);
    for (int i = 0; i < 64; i++) fz_read(&dxc_dep[i]);
    for (int t = 0; t < 8; t++) for (int i = 0; i < T; i++) fz_read(&fz_tiles[t][i]);
    for (int t = 0; t < 8; t++) { dxc_tile_data[t] = fz_tiles[t]; dxc_pending[t] = 0; }
    for (int r = 0; r < 8; r++) dxc_reg[r] = 0;
    memset(swdb_lqueue_storage, 0, sizeof swdb_lqueue_storage);
    fz_g = (Graph){0}; fz_g.out_neighbors_ = fz_neighbors; fz_g.num_nodes_ = n; fz_g.num_edges_ = E;
    fz_vo = (struct pvector_SGOffset){fz_offsets, fz_offsets + n + 1, fz_offsets + n + 1};
    fz_pv = (struct pvector_NodeID){fz_parent, fz_parent + n, fz_parent + n};
    fz_q = (struct SlidingQueue_NodeID){fz_shared, (size_t)si, (size_t)os, (size_t)oe, (size_t)n};
    fz_nblocks = 0;
    fz_reg("VertexOffsets.start_", fz_offsets, n + 1, sizeof(SGOffset));
    fz_reg("out_neighbors", fz_neighbors, E, sizeof(NodeID));
    fz_reg("parent.start_", fz_parent, n, sizeof(NodeID));
    fz_reg("queue.shared", fz_shared, n, sizeof(NodeID));
    fz_reg("swdb_lqueue_storage", swdb_lqueue_storage, SWDB_LQUEUE_CAPACITY, sizeof(NodeID));
    static const char *tn[8] = {"tile0", "tile1", "tile2", "tile3", "tile4", "tile5", "tile6", "tile7"};
    for (int t = 0; t < 8; t++) fz_reg(tn[t], fz_tiles[t], T, sizeof(int));
    fz_reg("Q", &fz_q, 1, sizeof fz_q);
    fz_reg("VO", &fz_vo, 1, sizeof fz_vo);
    fz_reg("PV", &fz_pv, 1, sizeof fz_pv);
    fz_reg("G", &fz_g, 1, sizeof fz_g);
    fz_seq = 0;
    TDStep(&fz_g, &fz_vo, &fz_pv, &fz_q, n, E);
    printf("{\"inst\": %d, \"end\": 1}\n", fz_inst);
    fz_inst++;
  }
  return 0;
}
