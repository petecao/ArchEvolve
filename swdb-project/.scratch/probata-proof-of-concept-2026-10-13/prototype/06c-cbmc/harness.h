// Ticket 06 continuation (CBMC box), 2026-10-14 ET. THROWAWAY. The two harness mains, included at
// the end of unit_peter.c / unit_maa.c, and (faithfulness test) at the end of the C++ units' TU.
//
// SWDB_CBMC: the proof harness. Every input symbolic within the proof-unit preconditions of
//   ../06-two-lanes/units.saw (lever 1: no shape splitting), one __CPROVER_assume per
//   llvm_precond, no other assume. Bounds (map 19 hand minimum): threads 1, lanes 2, chunk 2,
//   vertices 3, edges <= 3, frontier <= 2, parent in [-3, 3). DX100 state at entry: g0.
//   Sanity builds: SWDB_SANITY_REACH (two reachability asserts that must fail: the harness end,
//   and an accelerated claim), SWDB_DROP_PRE_NEIGHBOR (deletes the "edge targets are vertices"
//   precondition: must be refuted), SWDB_DROP_PRE_PARENT_LOWER (deletes the lower bound -3 on
//   parent: must still prove, the code treats every negative value as unvisited),
//   SWDB_CONCRETE (ticket 06's SAW concrete input instead of symbolic inputs).
// SWDB_NATIVE: the differential test. Enumerates every input of the bounded domain (tile memory
//   zero) and prints one line per run: inputs, the failed CHECK (a failed CHECK ends the run), the
//   failed P2 properties, and a hash of the final state and of the DX100 call trace.
#if defined(SWDB_CBMC)
int32_t nondet_i32(void);

int main(void) {
  for (int i = 0; i < SPIKE_Q; ++i) g_queue[i] = nondet_i32();
  for (int i = 0; i < SPIKE_V + 1; ++i) g_offsets[i] = nondet_i32();
  for (int i = 0; i < SPIKE_E; ++i) g_neighbors[i] = nondet_i32();
  for (int i = 0; i < SPIKE_V; ++i) g_parent[i] = nondet_i32();
  for (int t = 0; t < NUM_TILES_PER_CORE; ++t)
    for (int k = 0; k < TILE_SIZE; ++k) swdb_tile_data[t][k] = nondet_i32();
  int nf = nondet_i32();
#if defined(SWDB_CONCRETE)
  // ticket 06 diagnostics 1 and 6: frontier {0, 1}, edges 0->2, 1->2, 1->0; parent [0, 0, -1];
  // tile memory zero; threshold 1; acceleration on.
  { const int32_t q[8] = {0, 1, 0, 0, 0, 0, 0, 0}, o[4] = {0, 1, 3, 3}, n[3] = {2, 2, 0}, p[3] = {0, 0, -1};
    for (int i = 0; i < 8; ++i) g_queue[i] = q[i];
    for (int i = 0; i < 4; ++i) g_offsets[i] = o[i];
    for (int i = 0; i < 3; ++i) { g_neighbors[i] = n[i]; g_parent[i] = p[i]; }
    for (int t = 0; t < NUM_TILES_PER_CORE; ++t) for (int k = 0; k < TILE_SIZE; ++k) swdb_tile_data[t][k] = 0;
    nf = 2; }
#endif
  // Proof-unit preconditions (units.saw unit_inputs), one assume each.
  __CPROVER_assume(g_offsets[0] == 0 && g_offsets[0] <= g_offsets[1] && g_offsets[1] <= g_offsets[2] &&
                   g_offsets[2] <= g_offsets[3] && g_offsets[3] <= 3);
#if !defined(SWDB_DROP_PRE_NEIGHBOR)
  for (int e = 0; e < SPIKE_E; ++e)
    __CPROVER_assume(e >= g_offsets[3] || (g_neighbors[e] >= 0 && g_neighbors[e] < 3));
#endif
  for (int v = 0; v < SPIKE_V; ++v) {
#if defined(SWDB_DROP_PRE_PARENT_LOWER)
    __CPROVER_assume(g_parent[v] < 3);
#else
    __CPROVER_assume(g_parent[v] >= -3 && g_parent[v] < 3);
#endif
  }
  __CPROVER_assume(nf >= 0 && nf <= 2);
  for (int k = 0; k < SPIKE_F; ++k)
    __CPROVER_assume(k >= nf || (g_queue[k] >= 0 && g_queue[k] < 3 && g_parent[g_queue[k]] >= 0));
  __CPROVER_assume(nf < 2 || g_queue[0] != g_queue[1]);
  gh_init();   // DX100 state at entry: nothing pending
#if defined(SWDB_UNIT_PETER)
  swdb_spike_threshold = nondet_i32();
  __CPROVER_assume(swdb_spike_threshold >= 1);   // legality clause of the knob
  int accel = nondet_i32();
#if defined(SWDB_CONCRETE)
  swdb_spike_threshold = 1; accel = 1;
#endif
  swdb_unit_peter(nf, accel);
#if defined(SWDB_SANITY_REACH)
  __CPROVER_assert(!(swdb_spike_chunks > 0 && g_parent[0] + g_parent[1] + g_parent[2] != g_parent0[0] + g_parent0[1] + g_parent0[2]),
                   "sanity_reach_accelerated_claim");
#endif
#else
  swdb_unit_maa(nf);
#if defined(SWDB_SANITY_REACH)
  __CPROVER_assert(!(nf == 2 && g_parent[0] + g_parent[1] + g_parent[2] != g_parent0[0] + g_parent0[1] + g_parent0[2]),
                   "sanity_reach_accelerated_claim");
#endif
#endif
#if defined(SWDB_SANITY_REACH)
  __CPROVER_assert(0, "sanity_reach_end");
#endif
  return 0;
}

#elif defined(SWDB_NATIVE)
#include <setjmp.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static jmp_buf swdb_jb;
static const char *swdb_failed_check;
static char swdb_props[512];
static uint64_t swdb_trace_hash;
static int swdb_verbose;

static uint64_t fnv(uint64_t h, int64_t x) {
  for (int b = 0; b < 8; ++b) { h ^= (uint64_t)((x >> (8 * b)) & 0xFF); h *= UINT64_C(1099511628211); }
  return h;
}
#if defined(SWDB_VECTORS)
// One line per summary call: V <name> <8 args> | pre: G (ghost.cry's 81-word pack layout), tile
// memory (16), queue (8), offsets (4), neighbors (3), parent (3) | post: the same, or FAIL <check> | ret.
static int swdb_vec_on, swdb_vec_open;
static char swdb_vec_head[2048];
static int swdb_vec_dump(char *b, size_t cap) {
  int n = 0;
#define VW(x) n += snprintf(b + n, cap - (size_t)n, " %d", (int32_t)(x))
  VW(gh_rdy);
  for (int i = 0; i < 8; ++i) VW(gh_wr[i]);
  for (int i = 0; i < 8; ++i) VW(gh_outs[i]);
  for (int i = 0; i < 8; ++i) VW(gh_anc[i]);
  for (int i = 0; i < 8; ++i) VW(gh_named[i]);
  for (int i = 0; i < 8; ++i) VW(gh_users[i]);
  for (int i = 0; i < 8; ++i) VW(gh_rrd[i]);
  for (int i = 0; i < 8; ++i) VW(gh_rwr[i]);
  for (int i = 0; i < 8; ++i) VW(gh_reg[i]);
  for (int i = 0; i < 8; ++i) VW(gh_sz[i]);
  for (int i = 0; i < 4; ++i) VW(gh_fpr[i]);
  for (int i = 0; i < 4; ++i) VW(gh_fpw[i]);
  for (int t = 0; t < 8; ++t) for (int k = 0; k < 2; ++k) VW(swdb_tile_data[t][k]);
  for (int i = 0; i < 8; ++i) VW(g_queue[i]);
  for (int i = 0; i < 4; ++i) VW(g_offsets[i]);
  for (int i = 0; i < 3; ++i) VW(g_neighbors[i]);
  for (int i = 0; i < 3; ++i) VW(g_parent[i]);
#undef VW
  return n;
}
void swdb_vec_begin(const char *name, int64_t a0, int64_t a1, int64_t a2, int64_t a3, int64_t a4, int64_t a5, int64_t a6, int64_t a7) {
  if (!swdb_vec_on) return;
  int n = snprintf(swdb_vec_head, sizeof swdb_vec_head, "V %s %lld %lld %lld %lld %lld %lld %lld %lld |", name, (long long)a0,
                   (long long)a1, (long long)a2, (long long)a3, (long long)a4, (long long)a5, (long long)a6, (long long)a7);
  swdb_vec_dump(swdb_vec_head + n, sizeof swdb_vec_head - (size_t)n);
  swdb_vec_open = 1;
}
void swdb_vec_end(int64_t ret) {
  if (!swdb_vec_on || !swdb_vec_open) return;
  char post[1024];
  swdb_vec_dump(post, sizeof post);
  printf("%s |%s | %lld\n", swdb_vec_head, post, (long long)ret);
  swdb_vec_open = 0;
}
#endif
void swdb_native_check_failed(const char *name) {
  swdb_failed_check = name;
#if defined(SWDB_VECTORS)
  if (swdb_vec_on && swdb_vec_open) { printf("%s | FAIL %s | 0\n", swdb_vec_head, name); swdb_vec_open = 0; }
#endif
  longjmp(swdb_jb, 1);
}
void swdb_native_prop_failed(const char *name) {
  if (strstr(swdb_props, name)) return;
  if (strlen(swdb_props) + strlen(name) + 2 < sizeof swdb_props) { strcat(swdb_props, name); strcat(swdb_props, ","); }
}
void swdb_trace_call(const char *name, int64_t a, int64_t b, int64_t c, int64_t d, int64_t e) {
  for (const char *s = name; *s; ++s) swdb_trace_hash = fnv(swdb_trace_hash, *s);
  swdb_trace_hash = fnv(fnv(fnv(fnv(fnv(swdb_trace_hash, a), b), c), d), e);
  if (swdb_verbose) printf("  call %s %lld %lld %lld %lld %lld\n", name, (long long)a, (long long)b, (long long)c, (long long)d, (long long)e);
}

static uint64_t swdb_state_hash(void) {
  uint64_t h = UINT64_C(1469598103934665603);
  for (int i = 0; i < SPIKE_Q; ++i) h = fnv(h, g_queue[i]);
  for (int i = 0; i < SPIKE_V; ++i) h = fnv(h, g_parent[i]);
  for (int t = 0; t < 8; ++t) for (int k = 0; k < 2; ++k) h = fnv(h, swdb_tile_data[t][k]);
  h = fnv(h, gh_rdy);
  for (int i = 0; i < 8; ++i) {
    h = fnv(h, gh_wr[i]); h = fnv(h, gh_outs[i]); h = fnv(h, gh_anc[i]); h = fnv(h, gh_named[i]);
    h = fnv(h, gh_users[i]); h = fnv(h, gh_rrd[i]); h = fnv(h, gh_rwr[i]); h = fnv(h, gh_reg[i]); h = fnv(h, gh_sz[i]);
  }
  for (int m = 0; m < 4; ++m) { h = fnv(h, gh_fpr[m]); h = fnv(h, gh_fpw[m]); }
  return h;
}

static long swdb_runs, swdb_runs_check, swdb_runs_prop;
static int swdb_quiet;
static uint64_t swdb_stride, swdb_counter;   // vectors mode: run a pseudo-random 1/stride sample

static void swdb_run_one(int nf, int accel, int threshold) {
  if (swdb_stride) {
    if (fnv(UINT64_C(1469598103934665603), (int64_t)swdb_counter++) % swdb_stride != 0) return;
#if defined(SWDB_VECTORS)
    swdb_vec_on = 1;
#endif
    swdb_quiet = 1;
  }
  for (int t = 0; t < 8; ++t) for (int k = 0; k < 2; ++k) swdb_tile_data[t][k] = 0;
  gh_init();
  swdb_failed_check = "-"; swdb_props[0] = 0; swdb_trace_hash = UINT64_C(1469598103934665603);
  const int32_t o1 = g_offsets[1], o2 = g_offsets[2], o3 = g_offsets[3];
  const int32_t p0 = g_parent[0], p1 = g_parent[1], p2 = g_parent[2], q0 = g_queue[0], q1 = g_queue[1];
  const int32_t n0 = g_neighbors[0], n1 = g_neighbors[1], n2 = g_neighbors[2];
#if defined(SWDB_UNIT_PETER)
  swdb_spike_threshold = threshold;
  if (setjmp(swdb_jb) == 0) swdb_unit_peter(nf, accel);
#else
  (void)accel; (void)threshold;
  if (setjmp(swdb_jb) == 0) swdb_unit_maa(nf);
#endif
  ++swdb_runs;
  if (swdb_quiet) return;
  if (strcmp(swdb_failed_check, "-") != 0) ++swdb_runs_check;
  if (swdb_props[0]) ++swdb_runs_prop;
  printf("o%d%d%d n%d%d%d p%d,%d,%d f%d:%d,%d a%d t%d | %s | %s | %016llx %016llx\n", o1, o2, o3, n0, n1, n2, p0, p1, p2,
         nf, q0, q1, accel, threshold, swdb_failed_check, swdb_props[0] ? swdb_props : "-",
         (unsigned long long)swdb_state_hash(), (unsigned long long)swdb_trace_hash);
}

int main(int argc, char **argv) {
  if (argc > 2 && strcmp(argv[1], "vectors") == 0) swdb_stride = (uint64_t)atoll(argv[2]);
  if (argc > 1 && strcmp(argv[1], "concrete") == 0) {   // ticket 06's SAW concrete input, full trace
    const int32_t q[8] = {0, 1, 0, 0, 0, 0, 0, 0}, o[4] = {0, 1, 3, 3}, n[3] = {2, 2, 0}, p[3] = {0, 0, -1};
    for (int i = 0; i < 8; ++i) g_queue[i] = q[i];
    for (int i = 0; i < 4; ++i) g_offsets[i] = o[i];
    for (int i = 0; i < 3; ++i) { g_neighbors[i] = n[i]; g_parent[i] = p[i]; }
    swdb_verbose = 1;
#if defined(SWDB_VECTORS)
    swdb_vec_on = 1;
#endif
    swdb_run_one(2, 1, 1);
    printf("  final queue %d %d %d %d %d %d %d %d parent %d %d %d\n", g_queue[0], g_queue[1], g_queue[2], g_queue[3],
           g_queue[4], g_queue[5], g_queue[6], g_queue[7], g_parent[0], g_parent[1], g_parent[2]);
    return 0;
  }
  // Every input of the bounded domain: CSR offsets (0 <= o1 <= o2 <= o3 <= 3), edge targets of
  // the o3 real edges in 0..2 (slots past o3 hold 0), parent[v] in [-3, 3), a frontier of 0..2
  // distinct visited vertices in queue order (the rest of the queue 0); Peter: acceleration
  // off/on and threshold 1..3 (queue.size() <= 2, so 3 stands for every larger value).
  for (int o1 = 0; o1 <= 3; ++o1) for (int o2 = o1; o2 <= 3; ++o2) for (int o3 = o2; o3 <= 3; ++o3)
  for (int nc = 0; nc < 27; ++nc) {
    const int nv[3] = {nc % 3, (nc / 3) % 3, nc / 9};
    if ((o3 < 3 && nv[2]) || (o3 < 2 && nv[1]) || (o3 < 1 && nv[0])) continue;
    for (int pc = 0; pc < 216; ++pc) {
      const int pv[3] = {pc % 6 - 3, (pc / 6) % 6 - 3, pc / 36 - 3};
      for (int nf = 0; nf <= 2; ++nf) for (int a = 0; a < 3; ++a) for (int b = 0; b < 3; ++b) {
        if (nf < 1 && a) continue;
        if (nf < 2 && b) continue;
        if (nf >= 1 && pv[a] < 0) continue;
        if (nf >= 2 && (pv[b] < 0 || a == b)) continue;
#if defined(SWDB_UNIT_PETER)
        for (int accel = 0; accel <= 1; ++accel) for (int th = 1; th <= 3; ++th) {
#else
        { const int accel = 0, th = 0;
#endif
          for (int i = 0; i < 8; ++i) g_queue[i] = 0;
          g_queue[0] = nf >= 1 ? a : 0; g_queue[1] = nf >= 2 ? b : 0;
          g_offsets[0] = 0; g_offsets[1] = o1; g_offsets[2] = o2; g_offsets[3] = o3;
          for (int i = 0; i < 3; ++i) { g_neighbors[i] = nv[i]; g_parent[i] = pv[i]; }
          swdb_run_one(nf, accel, th);
        }
      }
    }
  }
  fprintf(stderr, "RUNS %ld failed_check %ld failed_p2 %ld\n", swdb_runs, swdb_runs_check, swdb_runs_prop);
  return 0;
}
#endif
