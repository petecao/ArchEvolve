// Probata PoC 27 fixture proof units for the DX100 proof semantics (semantics.dx100_bfs_0_1), in the core C++
// subset. Created: 2026-10-14 ET. Tests insert this text into a candidate artifact's src/bfs.cc. The dx100-mmio
// calls are declared, never defined: the proof semantics' C model defines them in every bounded job.
// Core-subset spellings: template argument int, every operand explicit (the condition tile is -1 when unused).
// Build constants pick the variants: SWDB_EARLY_READ_<N> (tile read N before its covering wait),
// SWDB_EARLY_SIZE, SWDB_CPU_WRITE, SWDB_WRONG_VALUE, SWDB_OUTSIDE (an address outside the footprint).
int get_new_tile();
void maa_const(int value, int reg);
void wait_ready(int tile);
unsigned short get_tile_size(int tile);
int *get_cacheable_tile_pointer(int tile);
void maa_stream_load(int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile);
void maa_indirect_load(int *data, int idx_tile, int dst_tile, int cond_tile);
void maa_range_loop(int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg, int dst_i_tile,
                    int dst_j_tile, int cond_tile);
void maa_alu_scalar(int src_tile, int src_reg, int dst_tile, int op, int cond_tile);
void maa_indirect_store_vector(int *data, int idx_tile, int src_tile, int cond_tile, int dst_tile);
int swdb_dx_in_footprint(int tile, const int *addr);

// tile t = q[0 .. n) (registers 0, 1, 2: begin, end, stride 1); the stream load stays uncovered.
void dxf_load(int *q, int n, int t) {
  maa_const(0, 0);
  maa_const(n, 1);
  maa_const(1, 2);
  maa_stream_load(q, 0, 1, 2, t, -1);
}

// Boolean result predicates use eager, side-effect-free conjunctions so WP smoke tests do not add
// provably unreachable short-circuit false branches. All operand reads are valid under the fixture contract.
// Three tile-pointer reads, each after its covering wait (SWDB_EARLY_READ_<N> moves read N before it).
int dxf_three_reads(int *q, int *base, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  int *t1 = get_cacheable_tile_pointer(1);
  int *t2 = get_cacheable_tile_pointer(2);
  int a = 0;
  int b = 0;
  int c = 0;
  dxf_load(q, n, 0);
#ifdef SWDB_EARLY_READ_1
  a = t0[0];
#endif
  wait_ready(0);
#ifndef SWDB_EARLY_READ_1
  a = t0[0];
#endif
  maa_indirect_load(base, 0, 1, -1);
#ifdef SWDB_EARLY_READ_2
  b = t1[0];
#endif
  wait_ready(1);
#ifndef SWDB_EARLY_READ_2
  b = t1[0];
#endif
  maa_indirect_load(base, 0, 2, -1);
#ifdef SWDB_EARLY_READ_3
  c = t2[0];
#endif
  wait_ready(2);
#ifndef SWDB_EARLY_READ_3
  c = t2[0];
#endif
  return (a == q[0]) & (b == base[q[0]]) & (c == base[q[0]]);
}

// get_tile_size after (or, with SWDB_EARLY_SIZE, before) the covering wait.
int dxf_size(int *q, int n) {
  dxf_load(q, n, 0);
#ifndef SWDB_EARLY_SIZE
  wait_ready(0);
#endif
  int s = get_tile_size(0);
  wait_ready(0);
  return s == n;
}

// A CPU read of a tile an uncovered gather only reads is no hazard; a CPU write (SWDB_CPU_WRITE) is.
int dxf_cpu_write(int *q, int *base, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  dxf_load(q, n, 0);
  wait_ready(0);
  maa_indirect_load(base, 0, 1, -1);
  int a = t0[0];
#ifdef SWDB_CPU_WRITE
  t0[0] = 0;
#endif
  wait_ready(1);
  return a == q[0];
}

// A wait on a store's source tile covers the store and its result tile (old values).
int dxf_store_source_wait(int *q, int *p, int n) {
  int *t5 = get_cacheable_tile_pointer(5);
  dxf_load(q, n, 0);
  wait_ready(0);
  dxf_load(q, n, 3);
  wait_ready(3);
  int old0 = p[q[0]];
  maa_indirect_store_vector(p, 0, 3, -1, 5);
  wait_ready(3);
  return t5[0] == old0;
}

// A wait covers the producers of the covered command's input tiles (the stream load that filled tile 0).
int dxf_transitive(int *q, int *base, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  int *t1 = get_cacheable_tile_pointer(1);
  dxf_load(q, n, 0);
  maa_indirect_load(base, 0, 1, -1);
  wait_ready(1);
  return (t0[0] == q[0]) & (t1[0] == base[q[0]]);
}

// Issuing a command whose destination is tile 4 first covers every uncovered command naming tile 4 in any
// role, condition included: the store (tile 4 is its condition) and the ALU (tile 4 is its destination).
int dxf_stall_condition(int *q, int *p, int *base, int n) {
  int *t5 = get_cacheable_tile_pointer(5);
  dxf_load(q, n, 0);
  wait_ready(0);
  dxf_load(q, n, 3);
  wait_ready(3);
  maa_const(5, 6);
  int old0 = p[q[0]];
  maa_alu_scalar(0, 6, 4, 13, -1);
  maa_indirect_store_vector(p, 0, 3, 4, 5);
  maa_indirect_load(base, 0, 4, -1);
  int r = t5[0] == old0;
  wait_ready(4);
  return r;
}

// Writing a constant into a register first covers every uncovered command naming it (the device holds it).
int dxf_register_write(int *q, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  dxf_load(q, n, 0);
  maa_const(7, 0);
  return t0[0] == q[0];
}

// The range-loop exception: a wait on the range loop's output covers it, not the gathers that filled its input
// tiles, so reading tile 1 after it is refuted.
int dxf_range_exception(int *q, int *offs, int n) {
  int *t1 = get_cacheable_tile_pointer(1);
  dxf_load(q, n, 0);
  wait_ready(0);
  maa_indirect_load(offs, 0, 1, -1);
  maa_indirect_load(offs + 1, 0, 2, -1);
  maa_const(0, 4);
  maa_const(-1, 5);
  maa_range_loop(4, 5, 1, 2, 2, 6, 7, -1);
  wait_ready(7);
  return t1[0] == offs[q[0]];
}

// A wait on a tile the store names only as its condition does not cover the store: reading its result is refuted.
int dxf_condition_wait(int *q, int *p, int n) {
  int *t5 = get_cacheable_tile_pointer(5);
  dxf_load(q, n, 0);
  wait_ready(0);
  dxf_load(q, n, 3);
  wait_ready(3);
  maa_const(5, 6);
  int old0 = p[q[0]];
  maa_alu_scalar(0, 6, 4, 13, -1);
  maa_indirect_store_vector(p, 0, 3, 4, 5);
  wait_ready(4);
  return t5[0] == old0;
}

// A wait on an unrelated tile covers nothing: reading tile 0 after it is refuted.
int dxf_unrelated_wait(int *q, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  dxf_load(q, n, 0);
  wait_ready(3);
  return t0[0] == q[0];
}

// Values at issue: a stream load, a gather and a range loop, read after the covering wait.
int dxf_value_stream(int *q, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  dxf_load(q, n, 0);
  wait_ready(0);
#ifdef SWDB_WRONG_VALUE
  return t0[n - 1] != q[n - 1];
#else
  return t0[n - 1] == q[n - 1];
#endif
}

int dxf_value_gather(int *q, int *base, int n) {
  int *t1 = get_cacheable_tile_pointer(1);
  dxf_load(q, n, 0);
  maa_indirect_load(base, 0, 1, -1);
  wait_ready(1);
#ifdef SWDB_WRONG_VALUE
  return t1[n - 1] != base[q[n - 1]];
#else
  return t1[n - 1] == base[q[n - 1]];
#endif
}

// One vertex u = q[0] whose neighbors are offs[u] .. offs[u + 1]: the range loop's first pair is (0, offs[u]).
int dxf_value_range(int *q, int *offs, int n) {
  int *t6 = get_cacheable_tile_pointer(6);
  int *t7 = get_cacheable_tile_pointer(7);
  dxf_load(q, n, 0);
  wait_ready(0);
  maa_indirect_load(offs, 0, 1, -1);
  maa_indirect_load(offs + 1, 0, 2, -1);
  wait_ready(1);
  wait_ready(2);
  maa_const(0, 4);
  maa_const(-1, 5);
  maa_range_loop(4, 5, 1, 2, 2, 6, 7, -1);
  wait_ready(7);
  int count = get_tile_size(7);
#ifdef SWDB_WRONG_VALUE
  return (count >= 1) & (t6[0] == 0) & (t7[0] == offs[q[0]] + 1);
#else
  return (count >= 1) & (t6[0] == 0) & (t7[0] == offs[q[0]]);
#endif
}

// The footprint of an uncovered gather: base + each index in its index tile (SWDB_OUTSIDE: an address past them).
int dxf_footprint(int *q, int *base, int n) {
  dxf_load(q, n, 0);
  wait_ready(0);
  maa_indirect_load(base, 0, 1, -1);
#ifdef SWDB_OUTSIDE
  int member = swdb_dx_in_footprint(1, base + n);
#else
  int member = swdb_dx_in_footprint(1, base + q[0]);
#endif
  wait_ready(1);
  return member;
}

// Ghost capacity: n uncovered stream loads into n distinct tiles (build with DX_NT=40 DX_TS=1).
int dxf_capacity(int *q, int n) {
  maa_const(0, 0);
  maa_const(1, 1);
  maa_const(1, 2);
  for (int t = 0; t < n; ++t) {
    maa_stream_load(q, 0, 1, 2, t, -1);
  }
  return 1;
}
