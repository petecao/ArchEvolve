// Candidate-process client of the certification evaluator, certify 1.5. Created: 2026-10-05 ET
// (ticket 78). Agent-decided under Yan-Ru's delegation; revisable.
//
// Linked into the candidate binary (the candidate object, this object, nothing else). It holds no
// record channel, no run plan, no fault and no strict-model state; it only
//   - maps the shared arena the evaluator created (descriptor SWDB_ARENA_FD, closed after mapping);
//   - replaces global operator new/delete so the candidate's C++ heap lives in the arena;
//   - sends each seam call (1.4 prelude) and each strict-layer call (client/MAA_functional.hpp) to
//     the evaluator on the calling thread's request slot and waits for the reply;
//   - sends the protected entry point's returned vector's location (driver, FINISH);
//   - exits if the evaluator is gone (parent changed), so no candidate process outlives a run.
// Every record is written by the evaluator from its own state; nothing here writes a record.
#include <atomic>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <initializer_list>
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <sys/mman.h>
#include <unistd.h>
#include <omp.h>
#include "dxc_lowering.hpp"
#include "arena.hpp"

namespace {
using namespace swdb_arena;

[[noreturn]] void fatal(const char *what) {
  const char prefix[] = "swdb certification client: ";
  (void)!::write(2, prefix, sizeof prefix - 1);
  (void)!::write(2, what, std::strlen(what));
  (void)!::write(2, "\n", 1);
  ::_exit(96);
}

void *watchdog(void *) {
  const pid_t evaluator = pid_t(header()->evaluator_pid);
  for (;;) {
    if (::getppid() != evaluator) ::_exit(97);
    ::usleep(20000);
  }
  return nullptr;
}

bool attach_now() {
  const char *value = std::getenv("SWDB_ARENA_FD");
  if (!value) fatal("no arena descriptor (this binary runs only under the certification evaluator)");
  const int fd = std::atoi(value);
  ::unsetenv("SWDB_ARENA_FD");
  void *mapped = ::mmap(reinterpret_cast<void *>(ADDRESS), SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  ::close(fd);
  if (mapped != reinterpret_cast<void *>(ADDRESS)) fatal("arena not mapped at its address");
  if (header()->magic != MAGIC || header()->size != SIZE) fatal("arena header differs");
  pthread_t thread;
  if (pthread_create(&thread, nullptr, watchdog, nullptr) == 0) pthread_detach(thread);
  return true;
}

bool attached() { static const bool value = attach_now(); return value; }

// ---- arena heap: power-of-two size classes, one lock, blocks are reused ----
// A block of class c is 2^(c+5) bytes; the 16 bytes before a returned pointer hold the class and
// the block's start (aligned allocations return a pointer inside the block).
void lock_heap() { while (header()->heap_lock.test_and_set(std::memory_order_acquire)) sched_yield(); }
void unlock_heap() { header()->heap_lock.clear(std::memory_order_release); }

void *allocate(size_t bytes, size_t alignment) {
  attached();
  if (alignment < 16) alignment = 16;
  const size_t need = bytes + 16 + (alignment > 16 ? alignment : 0);
  int cls = 0;
  while ((size_t(32) << cls) < need) {
    if (++cls >= SIZE_CLASSES) throw std::bad_alloc();
  }
  const uint64_t block_bytes = uint64_t(32) << cls;
  uintptr_t block = 0;
  lock_heap();
  if (header()->free_list[cls]) {
    block = ADDRESS + header()->free_list[cls];
    header()->free_list[cls] = *reinterpret_cast<uint64_t *>(block);
  } else if (header()->heap_top + block_bytes <= SIZE) {
    block = ADDRESS + header()->heap_top;
    header()->heap_top += block_bytes;
  }
  unlock_heap();
  if (!block) throw std::bad_alloc();
  uintptr_t user = (block + 16 + alignment - 1) & ~uintptr_t(alignment - 1);
  reinterpret_cast<uint64_t *>(user)[-2] = uint64_t(cls);
  reinterpret_cast<uint64_t *>(user)[-1] = uint64_t(block);
  return reinterpret_cast<void *>(user);
}

void release(void *pointer) {
  if (!pointer) return;
  const uintptr_t user = reinterpret_cast<uintptr_t>(pointer);
  if (!in_heap(user, 1)) fatal("operator delete of a pointer outside the arena heap");
  const uint64_t cls = reinterpret_cast<uint64_t *>(user)[-2];
  const uintptr_t block = uintptr_t(reinterpret_cast<uint64_t *>(user)[-1]);
  if (cls >= uint64_t(SIZE_CLASSES) || !in_heap(block, 16)) fatal("arena heap block header damaged");
  lock_heap();
  *reinterpret_cast<uint64_t *>(block) = header()->free_list[cls];
  header()->free_list[cls] = uint64_t(block - ADDRESS);
  unlock_heap();
}

// ---- requests ----
struct Channel { Slot *slot = nullptr; uint32_t sequence = 0; };
Channel &channel() {
  static thread_local Channel value;
  if (!value.slot) {
    attached();
    const int index = header()->slot_count.fetch_add(1);
    if (index >= SLOTS) fatal("more candidate threads than request slots");
    value.slot = slot(index);
  }
  return value;
}

Slot &begin(Op op) {
  Slot &s = *channel().slot;
  s.op = op;
  s.in_parallel = omp_in_parallel() ? 1 : 0;
  s.thread = s.in_parallel ? omp_get_thread_num() : 0;
  s.num_threads = omp_get_num_threads();
  return s;
}

void call(Slot &s) {
  Channel &c = channel();
  const uint32_t sequence = ++c.sequence;
  s.request.store(sequence, std::memory_order_release);
  for (unsigned spin = 0; s.reply.load(std::memory_order_acquire) != sequence; ++spin) {
    if (spin < 4096) continue;
    if (spin < 200000) { sched_yield(); continue; }
    if ((spin & 1023) == 0 && ::getppid() != pid_t(header()->evaluator_pid)) ::_exit(97);
    ::usleep(20);
  }
}

int64_t call0(Op op) { Slot &s = begin(op); call(s); return s.r[0]; }
int64_t call1(Op op, int64_t a) { Slot &s = begin(op); s.a[0] = a; call(s); return s.r[0]; }
int64_t call2(Op op, int64_t a, int64_t b) { Slot &s = begin(op); s.a[0] = a; s.a[1] = b; call(s); return s.r[0]; }
int64_t call3(Op op, int64_t a, int64_t b, int64_t c) {
  Slot &s = begin(op); s.a[0] = a; s.a[1] = b; s.a[2] = c; call(s); return s.r[0];
}
int64_t calln(Op op, std::initializer_list<int64_t> values) {
  Slot &s = begin(op);
  int i = 0;
  for (int64_t v : values) s.a[i++] = v;
  call(s);
  return s.r[0];
}
int64_t address(const void *p) { return int64_t(reinterpret_cast<uintptr_t>(p)); }

__attribute__((constructor)) void swdb_client_attach() { attached(); }
}  // namespace

// ---- global operator new/delete: the candidate's heap is the arena ----
void *operator new(size_t n) { return allocate(n, 16); }
void *operator new[](size_t n) { return allocate(n, 16); }
void *operator new(size_t n, const std::nothrow_t &) noexcept { try { return allocate(n, 16); } catch (...) { return nullptr; } }
void *operator new[](size_t n, const std::nothrow_t &) noexcept { try { return allocate(n, 16); } catch (...) { return nullptr; } }
void *operator new(size_t n, std::align_val_t a) { return allocate(n, size_t(a)); }
void *operator new[](size_t n, std::align_val_t a) { return allocate(n, size_t(a)); }
void operator delete(void *p) noexcept { release(p); }
void operator delete[](void *p) noexcept { release(p); }
void operator delete(void *p, size_t) noexcept { release(p); }
void operator delete[](void *p, size_t) noexcept { release(p); }
void operator delete(void *p, std::align_val_t) noexcept { release(p); }
void operator delete[](void *p, std::align_val_t) noexcept { release(p); }
void operator delete(void *p, size_t, std::align_val_t) noexcept { release(p); }
void operator delete[](void *p, size_t, std::align_val_t) noexcept { release(p); }
void operator delete(void *p, const std::nothrow_t &) noexcept { release(p); }
void operator delete[](void *p, const std::nothrow_t &) noexcept { release(p); }

// ---- the 1.4 seams (declared by ../v1_4/prelude.hpp), served by the evaluator ----
void swdb_seam_session_begin() { call0(SESSION_BEGIN); }
dxc_context swdb_seam_thread_context() {
  Slot &s = begin(THREAD_CONTEXT);
  call(s);
  dxc_context c;
  for (int i = 0; i < 8; ++i) { c.tile[i] = s.context[i]; c.reg[i] = s.context[8 + i]; }
  return c;
}
void swdb_seam_wait(int tile) { call1(WAIT, tile); }
void swdb_seam_gather_i32(void *base, int index, int dst) { call3(GATHER, address(base), index, dst); }
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst) {
  calln(STREAM_LOAD, {address(base), minimum, maximum, stride, dst});
}
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  calln(RANGE_LOOP, {last_i, last_j, lower, upper, stride, rows, columns});
}
void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op) { calln(ALU_SCALAR, {src, reg, dst, int64_t(op)}); }
bool swdb_seam_claim_i32(int32_t *slot_address, int32_t expected, int32_t desired) {
  const int64_t reply = call3(CLAIM, address(slot_address), expected, desired);
  if (reply == 2) return __sync_bool_compare_and_swap(slot_address, expected, desired);   // not in the arena
  return reply == 1;
}
bool swdb_seam_push(const void *queue, int32_t value) { return call2(PUSH, address(queue), value) == 1; }
void swdb_seam_direct_push(const void *queue, int32_t value) { call2(DIRECT_PUSH, address(queue), value); }
void swdb_seam_slide(const void *queue, const int32_t *window, size_t count) {
  call3(SLIDE, address(queue), address(window), int64_t(count));
}
void swdb_seam_reset(const void *queue) { call1(RESET, address(queue)); }
void swdb_seam_accelerated_chunk() { call0(CHUNK); }

// ---- the strict layer's interface (client/MAA_functional.hpp), served by the evaluator ----
void swdb_client_check_fail(const char *name) {
  Slot &s = begin(CHECK_FAIL);
  std::strncpy(s.text, name ? name : "", sizeof s.text - 1);
  s.text[sizeof s.text - 1] = '\0';
  call(s);
  ::_exit(86);   // not reached: the evaluator records the check and ends the run
}
void swdb_client_strict_session_begin() { call0(STRICT_SESSION_BEGIN); }
uint64_t swdb_client_operation_count() { return uint64_t(call0(OPERATION_COUNT)); }
void swdb_client_alloc_MAA() { call0(ALLOC_MAA); }
void swdb_client_init_MAA() { call0(INIT_MAA); }
void swdb_client_clear_mem_region() { call0(CLEAR_REGION); }
void swdb_client_add_mem_region(void *start, void *end) { call2(ADD_REGION, address(start), address(end)); }
int swdb_client_new_tile() { return int(call0(NEW_TILE)); }
int swdb_client_new_reg() { return int(call0(NEW_REG)); }
void swdb_client_const(int32_t value, int id) { call2(CONST, value, id); }
int32_t swdb_client_get_reg(int id) { return int32_t(call1(GET_REG, id)); }
void *swdb_client_tile_pointer(int id) { return reinterpret_cast<void *>(uintptr_t(call1(TILE_POINTER, id))); }
uint16_t swdb_client_tile_size(int id) { return uint16_t(call1(TILE_SIZE_OP, id)); }
uint16_t swdb_client_tile_ready(int id) { return uint16_t(call1(TILE_READY, id)); }
void swdb_client_wait_ready(int id) { call1(WAIT_READY, id); }
void swdb_client_set_tile_size(int id, uint16_t size) { call2(SET_TILE_SIZE, id, size); }
void swdb_client_set_tile_ready(int id, uint16_t ready) { call2(SET_TILE_READY, id, ready); }
void swdb_client_stream_load(void *base, int lo, int hi, int stride, int dst, int cond) {
  calln(MAA_STREAM_LOAD, {address(base), lo, hi, stride, dst, cond});
}
void swdb_client_indirect_load(void *base, int index, int dst, int cond) {
  calln(MAA_INDIRECT_LOAD, {address(base), index, dst, cond});
}
void swdb_client_range_loop(int last_i, int last_j, int minimum, int maximum, int stride, int rows, int columns, int cond) {
  calln(MAA_RANGE_LOOP, {last_i, last_j, minimum, maximum, stride, rows, columns, cond});
}
void swdb_client_alu_scalar(int src, int scalar, int dst, Operation_t op, int cond) {
  calln(MAA_ALU_SCALAR, {src, scalar, dst, int64_t(op), cond});
}
void swdb_client_indirect_store(void *base, int index, int src, int cond, int dst) {
  calln(MAA_STORE, {address(base), index, src, cond, dst});
}

// ---- the driver's hand-off: where the protected entry point's returned vector is ----
void swdb_client_finish(const void *base, size_t count, int kind) { call3(FINISH, address(base), int64_t(count), kind); }
