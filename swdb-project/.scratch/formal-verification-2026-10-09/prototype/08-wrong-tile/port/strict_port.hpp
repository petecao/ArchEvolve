// PROTOTYPE (ticket 08), throwaway. Verification port of library/dx100/strict/MAA_functional.hpp
// (the 2026-10-09 header with both wait rules). Created 2026-10-11 ET.
//
// Why a port: ESBMC 8.5 parses the real header (after a std::_Exit shim) but does not finish a
// one-command program in 240 s; its std::vector model explodes on the nested vector copies in the
// operation log. crux-llvm 0.12 cannot run libc++ 22 code. This port keeps the same functions, the
// same checks and the same wait rules, with fixed-size arrays instead of std::vector:
//   - Op log bounded by PORT_MAX_OPS (a port-only check fails if a run needs more);
//   - cover() is one descending pass over the log (dependencies always point to earlier ops), which
//     computes the same closure as the recursive (old) and stack (gem5) versions;
//   - no mutex, no atomics, no OpenMP: single thread only (thread() == 0);
//   - plain memory loads and stores instead of __atomic_*.
// Built natively (check -> stderr + _Exit(86), as the real header) or with -DSWDB_PORT_VERIFY
// (check -> assert). Equivalence evidence: run_port_diff.sh runs tests/fixtures/strict_wait_rule.cc
// against both headers under both rules and diffs the output.
#pragma once
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#ifndef TILE_SIZE
#define TILE_SIZE 16384
#endif
#ifndef NUM_CORES
#define NUM_CORES 4
#endif
#ifndef PORT_MAX_OPS
#define PORT_MAX_OPS 32
#endif
#define NUM_TILES_PER_CORE 8
#define NUM_REGS_PER_CORE 8
#define NUM_TILES (NUM_CORES * NUM_TILES_PER_CORE)
#define NUM_SCALAR_REGS (NUM_CORES * NUM_REGS_PER_CORE)
#define PORT_MAX_DEPS 6
#define PORT_MAX_NAMED 5
#define PORT_MAX_REGIONS 8
#define SWDB_STRICT 1
static_assert(TILE_SIZE > 0 && TILE_SIZE <= 65535, "DX100 tile size exceeds uint16 field");
enum class Operation_t { ADD_OP, SUB_OP, MUL_OP, DIV_OP, MIN_OP, MAX_OP,
 AND_OP, OR_OP, XOR_OP, SHL_OP, SHR_OP, GT_OP, GTE_OP, LT_OP, LTE_OP, EQ_OP, NE_OP, MAX };

#ifdef SWDB_PORT_VERIFY
#define SWDB_CHECK(value, name) assert((value) && name)
#else
#define SWDB_CHECK(value, name) do { if (!(value)) { std::fprintf(stderr, "SWDB_STRICT_ASSERT:%s\n", name); \
  std::fflush(stderr); std::_Exit(86); } } while (0)
#endif

namespace swdb_strict {
struct Tile { uint32_t device[TILE_SIZE], cpu[TILE_SIZE]; int owner; size_t writer; uint16_t size; };
struct Reg { uint32_t value; int owner; size_t writer; size_t readers[PORT_MAX_OPS]; int nreaders; };
struct Op { size_t deps[PORT_MAX_DEPS]; int ndeps; int tiles[2]; int ntiles; bool covered; };
struct Region { uintptr_t start, end; };
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
struct Roles { int named[PORT_MAX_NAMED]; int nnamed, inputs, tile_dependencies; bool filled; };
struct List { size_t op[PORT_MAX_OPS]; int n; };
#endif
// The state is split into separate globals (not one State struct): ESBMC's symbolic execution
// timed out with one large struct object (every field write rebuilt the whole object).
inline Tile tiles[NUM_TILES]; inline Reg regs[NUM_SCALAR_REGS]; inline Op ops[PORT_MAX_OPS]; inline int nops;
inline Region regions[PORT_MAX_REGIONS]; inline int nregions; inline int tile_count, reg_count; inline uint64_t operations;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
inline Roles roles[PORT_MAX_OPS]; inline List pending[NUM_TILES], users[NUM_TILES];
#endif
inline void list_push(size_t *list, int &n, size_t value) {
  SWDB_CHECK(n < PORT_MAX_OPS, "port_list_capacity"); list[n++] = value; }

inline void reset() {
  for (int t = 0; t < NUM_TILES; ++t) {
    for (int k = 0; k < TILE_SIZE; ++k) { tiles[t].device[k] = 0; tiles[t].cpu[k] = 0; }
    tiles[t].owner = -1; tiles[t].writer = 0; tiles[t].size = 0;
  }
  for (int r = 0; r < NUM_SCALAR_REGS; ++r) {
    regs[r].value = 0; regs[r].owner = -1; regs[r].writer = 0; regs[r].nreaders = 0; }
  ops[0].ndeps = 0; ops[0].ntiles = 0; ops[0].covered = true; nops = 1;
  nregions = 0; tile_count = reg_count = 0; operations = 0;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
  roles[0].nnamed = roles[0].inputs = roles[0].tile_dependencies = 0; roles[0].filled = false;
  for (int t = 0; t < NUM_TILES; ++t) { pending[t].n = 0; users[t].n = 0; }
#endif
}

inline int thread() { return 0; }
inline Tile &tile(int id) { SWDB_CHECK(id >= 0 && id < NUM_TILES, "tile_handle");
  SWDB_CHECK(tiles[id].owner == thread(), "thread_ownership_tile"); return tiles[id]; }
inline Reg &reg(int id) { SWDB_CHECK(id >= 0 && id < NUM_SCALAR_REGS, "register_handle");
  SWDB_CHECK(regs[id].owner == thread(), "thread_ownership_register"); return regs[id]; }
inline void capacity(uint64_t n) { SWDB_CHECK(n <= TILE_SIZE && n <= 65535, "tile_truncation"); }
inline void address(const void *base, int64_t index, size_t bytes) {
  SWDB_CHECK(index >= 0 && uint64_t(index) * bytes < UINT64_C(4294967296), "byte_offset_overflow");
#ifdef SWDB_PORT_NO_REGION_CHECK
  // crux-llvm: pointers are (allocation, offset) pairs, so a pointer-to-integer range test is
  // undefined. The verifier's own bounds check on the access replaces "memory_region"; equivalent
  // when every array the kernel touches is registered whole (true in tdstep_harness.cpp).
  (void)base; return;
#endif
  const uintptr_t origin = reinterpret_cast<uintptr_t>(base), offset = uint64_t(index) * bytes;
  SWDB_CHECK(origin <= UINTPTR_MAX - offset && origin + offset <= UINTPTR_MAX - bytes, "memory_region");
  const uintptr_t start = origin + offset, end = start + bytes; bool found = false;
  for (int r = 0; r < PORT_MAX_REGIONS; ++r)
    if (r < nregions && start >= regions[r].start && end <= regions[r].end) found = true;
  SWDB_CHECK(found, "memory_region");
}

// Cover op `id` and, transitively, the producers of its inputs. Dependencies always name earlier
// operations, so one descending pass over the log finds the closure. Under the gem5 rule a range
// loop that filled its output tile does not follow its tile inputs (RangeFuser.cc:166-168, 214-218).
// Every loop over the log or a list has a constant bound and a guard (ESBMC cannot see that the
// counts are constants, and a count-bounded loop is unwound to the --unwind limit at each call).
inline void cover(size_t id) { if (!id || ops[id].covered) return;
  bool mark[PORT_MAX_OPS];
  for (int k = 0; k < PORT_MAX_OPS; ++k) mark[k] = false;
  mark[id] = true;
  for (int op = PORT_MAX_OPS - 1; op > 0; --op) {
    if (size_t(op) > id || !mark[op] || ops[op].covered) continue;
    ops[op].covered = true;
    int first = 0;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
    if (roles[op].filled) first = roles[op].tile_dependencies;
#endif
    for (int k = 0; k < PORT_MAX_DEPS; ++k) if (k >= first && k < ops[op].ndeps) mark[ops[op].deps[k]] = true;
    for (int k = 0; k < 2; ++k) { if (k >= ops[op].ntiles) continue;
      const int t = ops[op].tiles[k];
      if (tiles[t].writer == size_t(op))
        for (int e = 0; e < TILE_SIZE; ++e) tiles[t].cpu[e] = tiles[t].device[e];
    }
  }
}

#ifdef SWDB_STRICT_WAIT_RULE_GEM5
inline void prune_list(List &p) { int w = 0;
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < p.n && !ops[p.op[k]].covered) p.op[w++] = p.op[k];
  p.n = w; }
inline void prune(int t) { prune_list(pending[t]); }
// Rule 5, the dispatch stall (IF.cc:193-212).
inline void stall(int t) { tile(t); List current = users[t];
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < current.n) cover(current.op[k]);
  prune_list(users[t]); }
#endif

inline size_t issue(const int *inputs, int nin, const int *registers, int nreg,
                    const int *outputs, int nout, const int *reg_outputs = nullptr, int nregout = 0) {
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
  for (int k = 0; k < nout; ++k) stall(outputs[k]);
#endif
  SWDB_CHECK(nops < PORT_MAX_OPS, "port_op_capacity");
  const size_t index = size_t(nops);
  Op &op = ops[index]; op.ndeps = 0; op.covered = false;
  for (int k = 0; k < nin; ++k) op.deps[op.ndeps++] = tile(inputs[k]).writer;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
  Roles &role = roles[index]; role.tile_dependencies = op.ndeps; role.filled = false;
#endif
  for (int k = 0; k < nreg; ++k) op.deps[op.ndeps++] = reg(registers[k]).writer;
  op.ntiles = nout; for (int k = 0; k < nout; ++k) op.tiles[k] = outputs[k];
  nops++;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
  role.nnamed = 0; for (int k = 0; k < nin; ++k) role.named[role.nnamed++] = inputs[k];
  role.inputs = nin; for (int k = 0; k < nout; ++k) role.named[role.nnamed++] = outputs[k];
  for (int k = 0; k < role.nnamed; ++k) { const int id = role.named[k];
    prune(id); list_push(pending[id].op, pending[id].n, index);
    prune_list(users[id]); list_push(users[id].op, users[id].n, index); }
#endif
  for (int k = 0; k < nreg; ++k) { Reg &r = reg(registers[k]); list_push(r.readers, r.nreaders, index); }
  for (int k = 0; k < nout; ++k) { Tile &t = tile(outputs[k]); t.writer = index;
    for (int e = 0; e < TILE_SIZE; ++e) t.cpu[e] = UINT32_C(0xa5a5a5a5); }
  for (int k = 0; k < nregout; ++k) reg(reg_outputs[k]).writer = index;
  ++operations; return index;
}

#ifdef SWDB_STRICT_WAIT_RULE_GEM5
// The last issued op's condition tile names no counted role (it stays in users[cond] for rule 5).
inline void condition(int cond) { if (cond < 0) return;
  const size_t index = size_t(nops - 1); Roles &r = roles[index];
  for (int k = 0; k + 1 < PORT_MAX_NAMED; ++k) if (k >= r.inputs - 1 && k + 1 < r.nnamed) r.named[k] = r.named[k + 1];
  --r.nnamed; --r.inputs;
  List &p = pending[cond];
  int found = -1;
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < p.n && p.op[k] == index) found = k;  // the last one
  if (found >= 0) { for (int m = 0; m + 1 < PORT_MAX_OPS; ++m) if (m >= found && m + 1 < p.n) p.op[m] = p.op[m + 1];
    --p.n; } }
inline void range_filled(bool filled) { roles[nops - 1].filled = filled; }
inline void wait_gem5(int id) { Tile &t = tile(id); List named = pending[id];
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < named.n) cover(named.op[k]);
  cover(t.writer); prune(id); }
#else
inline void condition(int) {}
inline void range_filled(bool) {}
#endif

template <class T> inline T read_memory(T *base, int64_t i) { address(base, i, sizeof(T));
  static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32"); return base[i]; }
template <class T> inline T *data(int id) { return reinterpret_cast<T *>(tile(id).device); }
inline int32_t rval(int id) { return int32_t(reg(id).value); }
inline uint64_t operation_count() { return operations; }
}  // namespace swdb_strict

inline void alloc_MAA() { swdb_strict::reset(); }
inline void init_MAA() { swdb_strict::reset(); }
inline void clear_mem_region() { swdb_strict::nregions = 0; }
inline void add_mem_region(void *start, void *end) {
#ifdef SWDB_PORT_NO_REGION_CHECK
  (void)start; (void)end; return;
#endif
  SWDB_CHECK(start && end && reinterpret_cast<uintptr_t>(end) >= reinterpret_cast<uintptr_t>(start), "memory_region_registration");
  SWDB_CHECK(swdb_strict::nregions < PORT_MAX_REGIONS, "port_region_capacity");
  swdb_strict::regions[swdb_strict::nregions].start = reinterpret_cast<uintptr_t>(start);
  swdb_strict::regions[swdb_strict::nregions].end = reinterpret_cast<uintptr_t>(end); swdb_strict::nregions++; }
template <class T> inline int get_new_tile() { static_assert(sizeof(T) == 4, "i32 tile"); SWDB_CHECK(swdb_strict::tile_count < NUM_TILES, "tile_budget"); int id = swdb_strict::tile_count++; swdb_strict::tiles[id].owner = swdb_strict::thread(); return id; }
template <class T> inline int get_new_reg() { static_assert(sizeof(T) == 4, "i32 register"); SWDB_CHECK(swdb_strict::reg_count < NUM_SCALAR_REGS, "register_budget"); int id = swdb_strict::reg_count++; swdb_strict::regs[id].owner = swdb_strict::thread(); return id; }
template <class T> inline void maa_const(T value, int id) { auto &r = swdb_strict::reg(id);
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < r.nreaders) SWDB_CHECK(swdb_strict::ops[r.readers[k]].covered, "constant_uncovered_register");
#else
  // gem5 holds a CPU register write until no unfinished command names the register.
  const int n = r.nreaders; size_t readers[PORT_MAX_OPS];
  for (int k = 0; k < PORT_MAX_OPS; ++k) readers[k] = r.readers[k];
  for (int k = 0; k < PORT_MAX_OPS; ++k) if (k < n) swdb_strict::cover(readers[k]);
#endif
  r.nreaders = 0; r.value = uint32_t(value); r.writer = 0; }
template <class T> inline int get_new_reg(T value) { int id = get_new_reg<T>(); maa_const(value, id); return id; }
template <class T> inline T get_reg(int id) { auto &r = swdb_strict::reg(id);
  return swdb_strict::ops[r.writer].covered ? T(r.value) : T(0xa5a5a5a5); }
template <class T> inline T *get_cacheable_tile_pointer(int id) { return reinterpret_cast<T *>(swdb_strict::tile(id).cpu); }
inline uint16_t get_tile_size(int id) { auto &t = swdb_strict::tile(id);
  return swdb_strict::ops[t.writer].covered ? t.size : 65535; }
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
inline uint16_t get_tile_ready(int id) { auto &t = swdb_strict::tile(id); return swdb_strict::ops[t.writer].covered ? 1 : 0; }
inline void wait_ready(int id) { swdb_strict::cover(swdb_strict::tile(id).writer); }
#else
inline uint16_t get_tile_ready(int id) { auto &t = swdb_strict::tile(id); swdb_strict::prune(id);
  return swdb_strict::pending[id].n == 0 && swdb_strict::ops[t.writer].covered ? 1 : 0; }
inline void wait_ready(int id) { swdb_strict::wait_gem5(id); }
#endif
inline void set_tile_size(int id, uint16_t size) { swdb_strict::capacity(size); auto &t = swdb_strict::tile(id);
  t.size = size; for (int e = 0; e < TILE_SIZE; ++e) t.device[e] = t.cpu[e]; t.writer = 0; }
inline void set_tile_ready(int id, uint16_t ready) { if (ready) wait_ready(id); }

template <class T> inline void maa_stream_load(T *base, int lo, int hi, int stride, int dst, int cond = -1) {
  int64_t begin = swdb_strict::rval(lo), end = swdb_strict::rval(hi), step = swdb_strict::rval(stride);
  SWDB_CHECK(begin >= 0 && end >= begin && step > 0, "stream_bounds"); uint64_t n = (end - begin + step - 1) / step;
  swdb_strict::capacity(n);
  int inputs[1]; int nin = 0; if (cond >= 0) inputs[nin++] = cond;
  T out[TILE_SIZE]; for (uint64_t k = 0; k < n; ++k) out[k] = T();
  for (uint64_t k = 0; k < n; ++k)
    if (cond < 0 || swdb_strict::data<uint32_t>(cond)[k]) out[k] = swdb_strict::read_memory(base, begin + k * step);
  const int regs[3] = {lo, hi, stride}, outs[1] = {dst};
  swdb_strict::issue(inputs, nin, regs, 3, outs, 1);
  for (uint64_t k = 0; k < n; ++k) swdb_strict::data<T>(dst)[k] = out[k];
  swdb_strict::tile(dst).size = uint16_t(n);
  swdb_strict::condition(cond);
}
template <class T> inline void maa_indirect_load(T *base, int index, int dst, int cond = -1) {
  size_t n = swdb_strict::tile(index).size; swdb_strict::capacity(n);
  T out[TILE_SIZE]; for (size_t k = 0; k < n; ++k) out[k] = T();
  for (size_t k = 0; k < n; ++k)
    if (cond < 0 || swdb_strict::data<uint32_t>(cond)[k]) out[k] = swdb_strict::read_memory(base, swdb_strict::data<int32_t>(index)[k]);
  int inputs[2] = {index, cond}; const int outs[1] = {dst};
  swdb_strict::issue(inputs, cond >= 0 ? 2 : 1, nullptr, 0, outs, 1);
  swdb_strict::condition(cond);
  for (size_t k = 0; k < n; ++k) swdb_strict::data<T>(dst)[k] = out[k];
  swdb_strict::tile(dst).size = uint16_t(n);
}
template <class T> inline void maa_range_loop(int last_i, int last_j, int minimum, int maximum, int stride, int rows, int columns, int cond = -1) {
  int64_t i = swdb_strict::rval(last_i), j = swdb_strict::rval(last_j), step = swdb_strict::rval(stride);
  size_t n = swdb_strict::tile(minimum).size;
  SWDB_CHECK(n == swdb_strict::tile(maximum).size && step > 0 && i >= 0 && uint64_t(i) <= n, "range_bounds");
  int32_t is[TILE_SIZE], js[TILE_SIZE]; int count = 0;
  while (uint64_t(i) < n && count < TILE_SIZE) {
    int64_t start = swdb_strict::data<T>(minimum)[i], end = swdb_strict::data<T>(maximum)[i];
    SWDB_CHECK(start >= 0 && end >= start && uint64_t(end) * 4 < UINT64_C(4294967296), "byte_offset_overflow");
    int64_t next = j < start ? start : j + step;
    if (next >= end) { ++i; j = -1; continue; }
    j = next;
    if (cond < 0 || swdb_strict::data<uint32_t>(cond)[i]) { is[count] = int32_t(i); js[count] = int32_t(j); ++count; }
  }
  int inputs[3] = {minimum, maximum, cond}; const int regs[3] = {last_i, last_j, stride};
  const int outs[2] = {rows, columns}, reg_outs[2] = {last_i, last_j};
  swdb_strict::issue(inputs, cond >= 0 ? 3 : 2, regs, 3, outs, 2, reg_outs, 2);
  swdb_strict::condition(cond); swdb_strict::range_filled(count == TILE_SIZE);
  for (int k = 0; k < count; ++k) { swdb_strict::data<int32_t>(rows)[k] = is[k]; swdb_strict::data<int32_t>(columns)[k] = js[k]; }
  swdb_strict::tile(rows).size = uint16_t(count); swdb_strict::tile(columns).size = uint16_t(count);
  swdb_strict::reg(last_i).value = uint32_t(i); swdb_strict::reg(last_j).value = uint32_t(j);
}
template <class T> inline T swdb_alu(T a, T b, Operation_t op) { switch (op) {
  case Operation_t::ADD_OP: return a + b; case Operation_t::SUB_OP: return a - b; case Operation_t::MUL_OP: return a * b;
  case Operation_t::DIV_OP: SWDB_CHECK(b != 0, "alu_division"); return a / b;
  case Operation_t::MIN_OP: return a < b ? a : b; case Operation_t::MAX_OP: return a < b ? b : a;
  case Operation_t::LT_OP: return a < b; case Operation_t::LTE_OP: return a <= b; case Operation_t::GT_OP: return a > b;
  case Operation_t::GTE_OP: return a >= b; case Operation_t::EQ_OP: return a == b; case Operation_t::NE_OP: return a != b;
  case Operation_t::AND_OP: return a & b; case Operation_t::OR_OP: return a | b; case Operation_t::XOR_OP: return a ^ b;
  case Operation_t::SHL_OP: return uint32_t(a) << b; case Operation_t::SHR_OP: return uint32_t(a) >> b;
  default: SWDB_CHECK(false, "alu_opcode"); return T(); } }
template <class T> inline void maa_alu_scalar(int src, int scalar, int dst, Operation_t op, int cond = -1) {
  size_t n = swdb_strict::tile(src).size; T out[TILE_SIZE]; for (size_t k = 0; k < n; ++k) out[k] = T();
  for (size_t k = 0; k < n; ++k)
    if (cond < 0 || swdb_strict::data<uint32_t>(cond)[k]) out[k] = swdb_alu(swdb_strict::data<T>(src)[k], T(swdb_strict::rval(scalar)), op);
  int inputs[2] = {src, cond}; const int regs[1] = {scalar}, outs[1] = {dst};
  swdb_strict::issue(inputs, cond >= 0 ? 2 : 1, regs, 1, outs, 1);
  swdb_strict::condition(cond);
  for (size_t k = 0; k < n; ++k) swdb_strict::data<T>(dst)[k] = out[k];
  swdb_strict::tile(dst).size = uint16_t(n);
}
template <class T> inline void maa_indirect_store_vector(T *base, int index, int src, int cond = -1, int dst = -1) {
  size_t n = swdb_strict::tile(index).size;
  SWDB_CHECK(n == swdb_strict::tile(src).size, "store_size");
  T old[TILE_SIZE]; for (size_t k = 0; k < n; ++k) old[k] = T();
  for (size_t k = 0; k < n; ++k) if (cond < 0 || swdb_strict::data<uint32_t>(cond)[k]) {
    const int32_t j = swdb_strict::data<int32_t>(index)[k]; old[k] = swdb_strict::read_memory(base, j);
    base[j] = swdb_strict::data<T>(src)[k];
  }
  int inputs[3] = {index, src, cond}; const int outs[1] = {dst};
  swdb_strict::issue(inputs, cond >= 0 ? 3 : 2, nullptr, 0, outs, dst >= 0 ? 1 : 0);
  if (dst >= 0) { for (size_t k = 0; k < n; ++k) swdb_strict::data<T>(dst)[k] = old[k]; swdb_strict::tile(dst).size = uint16_t(n); }
  swdb_strict::condition(cond);
}
