// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. The per-call summaries of ticket 06
// (../06-two-lanes/summaries.saw over ../06-two-lanes/ghost.cry) as C stubs, for CBMC 6.11.
//
// One stub per DX100 call and probe the two units make. Each is a line-by-line port of the
// Cryptol in ghost.cry (function names kept: issue, cover, closure, waitT, waitOld, constR,
// streamOk/streamVals/streamG, gatherOk/gatherVals/gatherG, rangeRun/rangeOk/rangeTiles/rangeG,
// aluVals/aluG, storeOk/storeRun/storeDst/storeG, ready, cpuOk). Cryptol bitvector semantics are
// kept: `/`, `<`, `<=` on [64] are unsigned, `>=$`, `<$` are signed, s64 is sign extension,
// zext is zero extension, `drop` to [16] is truncation.
//
// Each SAW summary precondition (llvm_precond) becomes CHECK(cond, "<name>"): under CBMC an
// assertion named after its check, then an assumption (SAW stops a path at a failed
// precondition; CBMC would otherwise run on and report follow-on failures). The names match the
// SAW overrides of ticket 06's run_spike.sh, so a refutation names its check.
// Values as if each command finished at issue (map 12). No strict-layer code.
//
// Build constants: TILE_SIZE 2 (lanes), NUM_CORES 1, 8 tiles and 8 registers per core.
// Compiles as C (CBMC, the lowering) and as C++ (the faithfulness test links the C++ units
// against the same stubs).
#ifndef SWDB_DX100_STUBS_H
#define SWDB_DX100_STUBS_H
#include <stdint.h>

#define DX_NT 8   // tiles of one core
#define DX_NR 8   // scalar registers of one core
#define DX_NM 4   // memory regions: 0 queue, 1 offsets, 2 neighbors, 3 parent
#define DX_TS 2   // TILE_SIZE
typedef uint8_t dx_mask;   // bit t <-> tile t or op id t (LSB = 0); regions use the low 4 bits

// ---- check macros
#if defined(SWDB_CBMC)
#define CHECK(c, name) do { int swdb_c_ = (c); __CPROVER_assert(swdb_c_, name); __CPROVER_assume(swdb_c_); } while (0)
#define PROP(c, name) __CPROVER_assert((c), name)
#else
// Native (faithfulness test): a failed CHECK ends the run (as SAW's failed precondition and the
// CBMC assume do); a failed PROP is recorded and the run goes on. Both defined by the harness.
void swdb_native_check_failed(const char *name);
void swdb_native_prop_failed(const char *name);
#define CHECK(c, name) do { if (!(c)) swdb_native_check_failed(name); } while (0)
#define PROP(c, name) do { if (!(c)) swdb_native_prop_failed(name); } while (0)
#endif

#if defined(SWDB_TRACE)
void swdb_trace_call(const char *name, int64_t a, int64_t b, int64_t c, int64_t d, int64_t e);
#define DX_TRACE(n, a, b, c, d, e) swdb_trace_call(n, a, b, c, d, e)
#else
#define DX_TRACE(n, a, b, c, d, e) ((void)0)
#endif

// Faithfulness test 3 (faith/stub_vectors.py): each summary logs its pre- and post-state, which
// Cryptol then compares with ghost.cry's function of the same name.
#if defined(SWDB_VECTORS)
void swdb_vec_begin(const char *name, int64_t a0, int64_t a1, int64_t a2, int64_t a3, int64_t a4, int64_t a5, int64_t a6, int64_t a7);
void swdb_vec_end(int64_t ret);
#define DX_VB(n, a0, a1, a2, a3, a4, a5, a6, a7) swdb_vec_begin(n, a0, a1, a2, a3, a4, a5, a6, a7)
#define DX_VE(r) swdb_vec_end(r)
#else
#define DX_VB(n, a0, a1, a2, a3, a4, a5, a6, a7) ((void)0)
#define DX_VE(r) ((void)0)
#endif

// ---- ghost state (ghost.cry record G); harness globals, never named by program code
dx_mask gh_rdy;
dx_mask gh_wr[DX_NT], gh_outs[DX_NT], gh_anc[DX_NT], gh_named[DX_NT], gh_users[DX_NT];
dx_mask gh_rrd[DX_NR], gh_rwr[DX_NR];
int32_t gh_reg[DX_NR], gh_sz[DX_NT];
dx_mask gh_fpr[DX_NM], gh_fpw[DX_NM];

// g0: nothing pending, every tile ready.
static void gh_init(void) {
  gh_rdy = 0xFF;
  for (int i = 0; i < DX_NT; ++i) { gh_wr[i] = 0; gh_outs[i] = 0; gh_anc[i] = 0; gh_named[i] = 0; gh_users[i] = 0; gh_sz[i] = 0; }
  for (int r = 0; r < DX_NR; ++r) { gh_rrd[r] = 0; gh_rwr[r] = 0; gh_reg[r] = 0; }
  for (int m = 0; m < DX_NM; ++m) { gh_fpr[m] = 0; gh_fpw[m] = 0; }
}

static dx_mask dx_bit(int32_t t) { return (uint32_t)t < 8u ? (dx_mask)(1u << t) : (dx_mask)0; }   // tbit / rbit

// orOver: OR of xs[i] over the bits i set in sel.
static dx_mask dx_or_over(unsigned sel, const dx_mask *xs, int n) {
  dx_mask r = 0;
  for (int i = 0; i < n; ++i)
    if ((sel >> i) & 1u) r = (dx_mask)(r | xs[i]);
  return r;
}
static dx_mask dx_live(dx_mask m) { return (dx_mask)(m & (dx_mask)~gh_rdy); }
static dx_mask dx_closure(dx_mask s) { return (dx_mask)(s | dx_or_over(s, gh_anc, DX_NT)); }
static void dx_cover(dx_mask s) { gh_rdy = (dx_mask)(gh_rdy | dx_or_over(dx_live(dx_closure(s)), gh_outs, DX_NT)); }

// issue: outs, ins (counted roles), cond, regIn, regOut, rd / wrm (region masks), filled.
static void dx_issue(dx_mask outs, dx_mask ins, dx_mask cond, dx_mask regIn, dx_mask regOut,
                     unsigned rd, unsigned wrm, int filled) {
  dx_mask fpany[DX_NM];
  for (int m = 0; m < DX_NM; ++m) fpany[m] = (dx_mask)(gh_fpr[m] | gh_fpw[m]);
  dx_mask regionLive = (dx_mask)(dx_or_over(wrm, fpany, DX_NM) | dx_or_over(rd, gh_fpw, DX_NM));
  // 1. stalls
  dx_cover((dx_mask)(dx_or_over(outs, gh_users, DX_NT) | regionLive));
  // 2. the output tiles' ids are free again
  dx_mask keep = (dx_mask)~outs;
  for (int i = 0; i < DX_NT; ++i) {
    gh_wr[i] &= keep; gh_anc[i] &= keep; gh_named[i] &= keep; gh_users[i] &= keep;
  }
  for (int r = 0; r < DX_NR; ++r) { gh_rrd[r] &= keep; gh_rwr[r] &= keep; }
  for (int m = 0; m < DX_NM; ++m) { gh_fpr[m] &= keep; gh_fpw[m] &= keep; }
  dx_mask om = (dx_mask)(outs & (dx_mask)(0u - outs));   // op id: lowest output tile
  dx_mask tileDeps = dx_or_over((unsigned)(ins | cond), gh_wr, DX_NT);
  dx_mask regDeps = dx_or_over(regIn, gh_rwr, DX_NR);
  dx_mask deps = filled ? regDeps : (dx_mask)(tileDeps | regDeps);
  dx_mask newAnc = (dx_mask)(deps | dx_or_over(deps, gh_anc, DX_NT));
  for (int i = 0; i < DX_NT; ++i)
    if ((om >> i) & 1u) { gh_anc[i] = newAnc; gh_outs[i] = outs; }
  for (int t = 0; t < DX_NT; ++t) {
    if ((outs >> t) & 1u) gh_wr[t] = om;
    if (((ins | outs) >> t) & 1u) gh_named[t] |= om;
    if (((ins | cond | outs) >> t) & 1u) gh_users[t] |= om;
  }
  gh_rdy &= (dx_mask)~outs;
  for (int r = 0; r < DX_NR; ++r) {
    if ((regIn >> r) & 1u) gh_rrd[r] |= om;
    if ((regOut >> r) & 1u) gh_rwr[r] = om;
  }
  for (int m = 0; m < DX_NM; ++m) {
    if ((rd >> m) & 1u) gh_fpr[m] |= om;
    if ((wrm >> m) & 1u) gh_fpw[m] |= om;
  }
}

static int dx_ready(int32_t t) { return (gh_rdy >> t) & 1; }
static int dx_cpu_ok(int32_t m, int is_write) {
  return dx_live(gh_fpw[m]) == 0 && (!is_write || dx_live(gh_fpr[m]) == 0);
}

static int64_t s64(int32_t x) { return (int64_t)x; }
static uint64_t zext64(int32_t x) { return (uint64_t)(uint32_t)x; }
static int32_t dx_mem_at(const int32_t *mem, uint64_t len, uint64_t i) { return i < len ? mem[i] : 0; }   // memAt
static int32_t dx_tile_at(const int32_t *t, uint64_t i) { return i < (uint64_t)DX_TS ? t[i] : 0; }      // tileAt

// ---- the memory regions the units pass (spike_api.hpp dispatch; SAW had one override each)
// Needs, declared before this header: g_queue[8], g_offsets[4], g_neighbors[3], g_parent[3],
// swdb_tile_data[8][2].
typedef struct { int32_t *mem; uint64_t len; uint64_t off; int32_t region; } dx_region;
static dx_region dx_region_of_gather(const int32_t *p) {
  dx_region r = {0, 0, 0, -1};
  if (p == g_queue) { r.mem = g_queue; r.len = 8; r.off = 0; r.region = 0; }
  else if (p == g_offsets) { r.mem = g_offsets; r.len = 4; r.off = 0; r.region = 1; }
  else if (p == g_offsets + 1) { r.mem = g_offsets; r.len = 4; r.off = 1; r.region = 1; }
  else if (p == g_neighbors) { r.mem = g_neighbors; r.len = 3; r.off = 0; r.region = 2; }
  else if (p == g_parent) { r.mem = g_parent; r.len = 3; r.off = 0; r.region = 3; }
  return r;
}

// ---- maa_const (constR)
static void dx_const(int32_t v, int32_t r) {
  DX_TRACE("const", v, r, 0, 0, 0);
  DX_VB("const", v, r, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)r < 8u, "arg_range");
  dx_cover(gh_rrd[r]);
  gh_rrd[r] = 0; gh_rwr[r] = 0; gh_reg[r] = v;
  DX_VE(0);
}

// ---- wait_ready (waitT; waitOld under the old rule, TDStepMAA control 2)
static void dx_wait(int32_t t) {
  DX_TRACE("wait", t, 0, 0, 0, 0);
  DX_VB("wait", t, 0, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)t < 8u, "arg_range");
#if defined(SWDB_OLD_WAIT_RULE)
  dx_cover(gh_wr[t]);
#else
  dx_cover((dx_mask)(gh_named[t] | gh_wr[t]));
#endif
  DX_VE(0);
}

// ---- get_tile_size: an unready size read is a hazard (map 12 item 3)
static uint16_t dx_get_tile_size(int32_t t) {
  DX_TRACE("size", t, gh_sz[(uint32_t)t & 7u], 0, 0, 0);
  DX_VB("size", t, 0, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)t < 8u, "arg_range");
  CHECK(dx_ready(t), "size_read_before_ready");   // SAW: override _Z13get_tile_sizei
  DX_VE((uint16_t)gh_sz[t]);
  return (uint16_t)gh_sz[t];
}

// ---- probes placed by the harness
static void dx_probe_tile_read(int32_t t) {
  DX_TRACE("probe_tile", t, 0, 0, 0, 0);
  DX_VB("probe_tile", t, 0, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)t < 8u, "arg_range");
  CHECK(dx_ready(t), "tile_read_before_ready");   // SAW: override _Z20swdb_probe_tile_readi
  DX_VE(0);
}
static void dx_probe_cpu(int32_t m, int32_t w) {
  DX_TRACE("probe_cpu", m, w, 0, 0, 0);
  DX_VB("probe_cpu", m, w, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)m < 4u, "arg_range");
  CHECK(dx_cpu_ok(m, w != 0), "cpu_access_overlaps_unfinished");   // SAW: override _Z14swdb_probe_cpuii
  DX_VE(0);
}

// ---- fault tooling only (seams.cc pokes the strict layer's state the same way)
static int32_t dx_fault_peek_reg(int32_t r) { CHECK((uint32_t)r < 8u, "arg_range"); return gh_reg[r]; }
static void dx_fault_poke_reg(int32_t r, int32_t v) {
  DX_TRACE("poke", r, v, 0, 0, 0); DX_VB("poke", r, v, 0, 0, 0, 0, 0, 0);
  CHECK((uint32_t)r < 8u, "arg_range"); gh_reg[r] = v; DX_VE(0);
}
static int32_t dx_fault_peek_size(int32_t t) { CHECK((uint32_t)t < 8u, "arg_range"); return gh_sz[t]; }

// ---- maa_stream_load: three checks, as SAW's three overrides
static uint64_t dx_stream_n(int32_t lo, int32_t hi, int32_t st) {   // streamN / streamNR (unsigned /)
  return (uint64_t)(s64(gh_reg[hi]) - s64(gh_reg[lo]) + s64(gh_reg[st]) - 1) / (uint64_t)s64(gh_reg[st]);
}
// CHECK stream_bounds: begin >= 0, end >= begin, stride > 0 (SAW: _Z21swdb_ps_stream_boundsiii)
static void dx_ps_stream_bounds(int32_t lo, int32_t hi, int32_t st) {
  DX_VB("stream_bounds", lo, hi, st, 0, 0, 0, 0, 0);
  CHECK((uint32_t)lo < 8u && (uint32_t)hi < 8u && (uint32_t)st < 8u, "arg_range");
  CHECK(gh_reg[lo] >= 0 && gh_reg[hi] >= gh_reg[lo] && gh_reg[st] > 0, "stream_bounds");
  DX_VE(0);
}
// CHECK tile_truncation: n <= TILE_SIZE (SAW: _Z23swdb_ps_stream_capacityiii)
static void dx_ps_stream_capacity(int32_t lo, int32_t hi, int32_t st) {
  DX_VB("stream_capacity", lo, hi, st, 0, 0, 0, 0, 0);
  CHECK((uint32_t)lo < 8u && (uint32_t)hi < 8u && (uint32_t)st < 8u, "arg_range");
  CHECK(dx_stream_n(lo, hi, st) <= 2u, "tile_truncation");
  DX_VE(0);
}
// The load: one region, the queue (SAW: one override, g_queue, offset 0, region 0).
static void dx_ps_stream_load(int32_t *data, int32_t lo, int32_t hi, int32_t st, int32_t dst, int32_t cond) {
  DX_TRACE("stream", lo, hi, st, dst, cond);
  DX_VB("stream_load", data == g_queue, lo, hi, st, dst, cond, 0, 0);
  CHECK(data == g_queue, "stream_unknown_region");
  CHECK((uint32_t)lo < 8u && (uint32_t)hi < 8u && (uint32_t)st < 8u && (uint32_t)dst < 8u && cond == -1, "arg_range");
  const uint64_t len = 8, off = 0;
  const int64_t b = s64(gh_reg[lo]), e = s64(gh_reg[hi]), s = s64(gh_reg[st]);
  const uint64_t n = dx_stream_n(lo, hi, st);
  // streamOk (the two checks above again, then the memory region)
  CHECK(b >= 0 && e >= b && s > 0 && n <= (uint64_t)DX_TS &&
        (n == 0 || off + (uint64_t)b + (n - 1) * (uint64_t)s < len), "stream_memory_region");
  int32_t vals[DX_TS];
  for (int k = 0; k < DX_TS; ++k)
    vals[k] = (uint64_t)k < n ? dx_mem_at(g_queue, len, off + (uint64_t)b + (uint64_t)k * (uint64_t)s)
                              : swdb_tile_data[dst][k];
  dx_issue(dx_bit(dst), 0, 0, (dx_mask)(dx_bit(lo) | dx_bit(hi) | dx_bit(st)), 0, 1u << 0, 0, 0);
  gh_sz[dst] = (int32_t)n;
  for (int k = 0; k < DX_TS; ++k) swdb_tile_data[dst][k] = vals[k];
  DX_VE(0);
}
// maa_stream_load as spike_api.hpp defines it: the three summaries in order.
static void dx_stream_load(int32_t *data, int32_t lo, int32_t hi, int32_t st, int32_t dst, int32_t cond) {
  dx_ps_stream_bounds(lo, hi, st);
  dx_ps_stream_capacity(lo, hi, st);
  dx_ps_stream_load(data, lo, hi, st, dst, cond);
}

// ---- maa_indirect_load (gather): dst[k] = base[off + idx[k]], k < size(idx)
static void dx_gather(int32_t *data, int32_t ix, int32_t dst, int32_t cond) {
  DX_TRACE("gather", dx_region_of_gather(data).region * 2 + (int64_t)dx_region_of_gather(data).off, ix, dst, cond, 0);
  dx_region R = dx_region_of_gather(data);
  DX_VB("gather", R.region, (int64_t)R.off, ix, dst, cond, 0, 0, 0);
  CHECK(R.region >= 0, "gather_unknown_region");   // SAW: swdb_ps_gather_unknown has no summary
  CHECK((uint32_t)ix < 8u && (uint32_t)dst < 8u && cond == -1, "arg_range");
  const uint64_t n = zext64(gh_sz[ix]);
  int ok = 1;
  for (int k = 0; k < DX_TS; ++k) {
    const int32_t i = swdb_tile_data[ix][k];
    ok = ok && ((uint64_t)k >= n || (i >= 0 && R.off + (uint64_t)s64(i) < R.len));
  }
  CHECK(ok, "gather_memory_region");
  int32_t vals[DX_TS];
  for (int k = 0; k < DX_TS; ++k)
    vals[k] = (uint64_t)k < n ? dx_mem_at(R.mem, R.len, R.off + (uint64_t)s64(swdb_tile_data[ix][k]))
                              : swdb_tile_data[dst][k];
  const int32_t size = gh_sz[ix];
  dx_issue(dx_bit(dst), dx_bit(ix), 0, 0, 0, 1u << R.region, 0, 0);
  gh_sz[dst] = size;
  for (int k = 0; k < DX_TS; ++k) swdb_tile_data[dst][k] = vals[k];
  DX_VE(0);
}

// ---- maa_range_loop: the CSR pairs (i, j) from (last_i, last_j), at most TILE_SIZE per call
static void dx_range_loop(int32_t li, int32_t lj, int32_t lo, int32_t up, int32_t st, int32_t rows, int32_t cols, int32_t cond) {
  DX_TRACE("range", li, lj, lo * 8 + up, st, rows * 8 + cols);
  DX_VB("range", li, lj, lo, up, st, rows, cols, cond);
  CHECK((uint32_t)li < 8u && (uint32_t)lj < 8u && (uint32_t)lo < 8u && (uint32_t)up < 8u && (uint32_t)st < 8u &&
        (uint32_t)rows < 8u && (uint32_t)cols < 8u && rows != cols && cond == -1, "arg_range");
  // rangeRun: fold of 2 * TS + 1 = 5 steps
  const uint64_t n = zext64(gh_sz[lo]);
  const int64_t s = s64(gh_reg[st]);
  int64_t i = s64(gh_reg[li]), j = s64(gh_reg[lj]);
  uint64_t c = 0;
  int32_t is[DX_TS] = {0, 0}, js[DX_TS] = {0, 0};
  int ok = 1;
  for (int step = 0; step < 2 * DX_TS + 1; ++step) {
    if ((uint64_t)i < n && c < (uint64_t)DX_TS) {
      const int64_t sta = s64(dx_tile_at(swdb_tile_data[lo], (uint64_t)i));
      const int64_t en = s64(dx_tile_at(swdb_tile_data[up], (uint64_t)i));
      ok = ok && sta >= 0 && en >= sta && (uint64_t)en * 4u < (UINT64_C(1) << 32);   // byte_offset_overflow
      const int64_t nx = j < sta ? sta : (int64_t)((uint64_t)j + (uint64_t)s);   // [64] wraps
      if (nx >= en) { i = (int64_t)((uint64_t)i + 1u); j = -1; }
      else { is[c] = (int32_t)i; js[c] = (int32_t)nx; j = nx; c = c + 1; }
    }
  }
  // rangeOk: range_bounds, byte_offset_overflow
  const int64_t i0 = s64(gh_reg[li]);
  CHECK(gh_sz[lo] == gh_sz[up] && s > 0 && i0 >= 0 && (uint64_t)i0 <= n && ok, "range_bounds");
  int32_t rv[DX_TS], cv[DX_TS];
  for (int k = 0; k < DX_TS; ++k) {
    rv[k] = (uint64_t)k < c ? is[k] : swdb_tile_data[rows][k];
    cv[k] = (uint64_t)k < c ? js[k] : swdb_tile_data[cols][k];
  }
  dx_issue((dx_mask)(dx_bit(rows) | dx_bit(cols)), (dx_mask)(dx_bit(lo) | dx_bit(up)), 0,
           (dx_mask)(dx_bit(li) | dx_bit(lj) | dx_bit(st)), (dx_mask)(dx_bit(li) | dx_bit(lj)), 0, 0, c == (uint64_t)DX_TS);
  gh_sz[rows] = (int32_t)c; gh_sz[cols] = (int32_t)c;
  gh_reg[li] = (int32_t)i; gh_reg[lj] = (int32_t)j;
  for (int k = 0; k < DX_TS; ++k) { swdb_tile_data[rows][k] = rv[k]; swdb_tile_data[cols][k] = cv[k]; }
  DX_VE(0);
}

// ---- maa_alu_scalar, LT_OP (13) only: dst[k] = src[k] <s reg
static void dx_alu_scalar(int32_t src, int32_t r, int32_t dst, int32_t op, int32_t cond) {
  DX_TRACE("alu", src, r, dst, op, cond);
  DX_VB("alu", src, r, dst, op, cond, 0, 0, 0);
  CHECK((uint32_t)src < 8u && (uint32_t)r < 8u && (uint32_t)dst < 8u && op == 13 && cond == -1, "arg_range");
  const uint64_t n = zext64(gh_sz[src]);
  int32_t vals[DX_TS];
  for (int k = 0; k < DX_TS; ++k)
    vals[k] = (uint64_t)k < n ? (swdb_tile_data[src][k] < gh_reg[r] ? 1 : 0) : swdb_tile_data[dst][k];
  const int32_t size = gh_sz[src];
  dx_issue(dx_bit(dst), dx_bit(src), 0, dx_bit(r), 0, 0, 0, 0);
  gh_sz[dst] = size;
  for (int k = 0; k < DX_TS; ++k) swdb_tile_data[dst][k] = vals[k];
  DX_VE(0);
}

// ---- maa_indirect_store_vector with a condition and a destination tile (old values), in order k
static void dx_store_vector(int32_t *data, int32_t ix, int32_t sr, int32_t cd, int32_t dst) {
  DX_TRACE("store", ix, sr, cd, dst, 0);
  DX_VB("store", data == g_parent, ix, sr, cd, dst, 0, 0, 0);
  CHECK(data == g_parent, "store_unknown_region");   // SAW: one override, g_parent, region 3
  CHECK((uint32_t)ix < 8u && (uint32_t)sr < 8u && (uint32_t)cd < 8u && (uint32_t)dst < 8u, "arg_range");
  const uint64_t len = 3, off = 0;
  const uint64_t n = zext64(gh_sz[ix]);
  int ok = gh_sz[ix] == gh_sz[sr];   // store_size
  for (int k = 0; k < DX_TS; ++k) {
    const int32_t i = swdb_tile_data[ix][k], c = swdb_tile_data[cd][k];
    ok = ok && ((uint64_t)k >= n || c == 0 || (i >= 0 && off + (uint64_t)s64(i) < len));
  }
  CHECK(ok, "store_size_region");
  // storeRun: memory updated in order k; olds[k] = the value before lane k's write
  int32_t olds[DX_TS] = {0, 0};
  for (int k = 0; k < DX_TS; ++k) {
    if ((uint64_t)k < n && dx_tile_at(swdb_tile_data[cd], (uint64_t)k) != 0) {
      const uint64_t a = off + (uint64_t)s64(dx_tile_at(swdb_tile_data[ix], (uint64_t)k));
      const int32_t old = dx_mem_at(g_parent, len, a);
      if (a < len) g_parent[a] = dx_tile_at(swdb_tile_data[sr], (uint64_t)k);
      olds[k] = old;
    }
  }
  int32_t vals[DX_TS];
  for (int k = 0; k < DX_TS; ++k) vals[k] = (uint64_t)k < n ? olds[k] : swdb_tile_data[dst][k];
  const int32_t size = gh_sz[ix];
  dx_issue(dx_bit(dst), (dx_mask)(dx_bit(ix) | dx_bit(sr)), dx_bit(cd), 0, 0, 1u << 3, 1u << 3, 0);
  gh_sz[dst] = size;
  for (int k = 0; k < DX_TS; ++k) swdb_tile_data[dst][k] = vals[k];
  DX_VE(0);
}
#endif
