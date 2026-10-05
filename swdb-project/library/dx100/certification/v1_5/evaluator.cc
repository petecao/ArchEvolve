// Certification evaluator process, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// Usage: swdb-evaluator <candidate binary> <candidate arguments...>
//
// The evaluator is linked from trusted sources only: this file, the unchanged certify 1.4 record
// writer and seams (../v1_4/record.cc, ../v1_4/seams.cc) and the unchanged strict layer
// (strict/MAA_functional.hpp), all built with evaluator_context.hpp. It owns everything a verdict
// depends on: the record descriptor and the run plan (record.cc reads both before main), the fault
// logic and the frontier ledger (seams.cc), the strict model's state (device tiles, registers,
// operation graph, registered regions) and the witness counters.
//
// It creates the shared arena (arena.hpp), records the run's source vertex from its own
// arguments, and starts the candidate binary as a child process whose only extra descriptor is the
// arena (descriptor 3, closed by the client once mapped); the child's environment has neither
// record nor plan variable. One server thread per candidate request slot performs each request in
// this process: a pointer the candidate passes is used only after it is checked to lie in the
// arena's candidate heap. The returned vector is read from the arena by the evaluator (FINISH).
//
// Exit status: 0 when the candidate exited 0 after FINISH; 86 or 88 when the strict layer or the
// frontier ledger ended the run (as in 1.4); 87 when the candidate passed a frontier window outside
// the arena; otherwise the candidate's status (128 + signal number for a signal).
#include <algorithm>
#include <atomic>
#include <cerrno>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include "dxc_lowering.hpp"
#include "arena.hpp"

extern char **environ;
static_assert(NUM_TILES <= int(swdb_arena::MAX_TILES), "tile windows");
static_assert(size_t(TILE_SIZE) * 4 <= swdb_arena::MAX_TILE_BYTES, "tile window size");

// record.cc (certify 1.4, unchanged)
void swdb_cert_record_source(int64_t source);
void swdb_cert_record_result_i32(const int32_t *values, size_t count);
void swdb_cert_record_result_f32(const float *values, size_t count);
void swdb_cert_record_result_base(const void *base, size_t count);
void swdb_cert_record_end();
// seams.cc (certify 1.4, unchanged)
void swdb_seam_session_begin();
dxc_context swdb_seam_thread_context();
void swdb_seam_wait(int tile);
void swdb_seam_gather_i32(void *base, int index, int dst);
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst);
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns);
void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op);
bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired);
bool swdb_seam_push(const void *queue, int32_t value);
void swdb_seam_direct_push(const void *queue, int32_t value);
void swdb_seam_slide(const void *queue, const int32_t *window, size_t count);
void swdb_seam_reset(const void *queue);

namespace {
std::atomic<pid_t> candidate_pid(0);
std::atomic<bool> finished(false);
}

namespace swdb_eval {
Caller &caller() { static thread_local Caller value; return value; }
}

// Every end of a run (a strict failure, a repeated frontier vertex, any error) ends the candidate
// first. evaluator_context.hpp redirects std::_Exit here.
namespace std {
void swdb_eval_exit(int code) noexcept {
  const pid_t pid = candidate_pid.load();
  if (pid > 0) ::kill(pid, SIGKILL);
  ::_exit(code);
}
}

namespace {
using namespace swdb_arena;

[[noreturn]] void fail(const char *what, int code = 95) {
  std::fprintf(stderr, "swdb certification evaluator: %s\n", what);
  std::fflush(stderr);
  std::swdb_eval_exit(code);
}

// ---- the strict model's CPU-visible tiles, mirrored into the arena's tile windows ----
// The model is unchanged; the evaluator keeps each window equal to the model's CPU buffer. A
// window is rewritten when its tile's producer, that producer's coverage, or the buffer changes
// (operation issue, wait coverage, reset); before set_tile_size, which reads the CPU buffer, the
// window (what the candidate wrote) is copied into the model.
std::mutex &model_lock() { static std::mutex m; return m; }
struct Mark { size_t writer; bool covered; const uint32_t *cpu; };

void take(Mark *marks) {
  swdb_strict::State &s = swdb_strict::state();
  for (int t = 0; t < NUM_TILES; ++t) {
    const swdb_strict::Tile &tile = s.tiles[t];
    marks[t] = {tile.writer, tile.writer < s.ops.size() && s.ops[tile.writer].covered, tile.cpu.data()};
  }
}

void publish(const Mark *marks) {
  swdb_strict::State &s = swdb_strict::state();
  for (int t = 0; t < NUM_TILES && t < int(s.tiles.size()); ++t) {
    const swdb_strict::Tile &tile = s.tiles[t];
    const bool covered = tile.writer < s.ops.size() && s.ops[tile.writer].covered;
    if (marks && marks[t].writer == tile.writer && marks[t].covered == covered && marks[t].cpu == tile.cpu.data()) continue;
    std::memcpy(tile_window(t), tile.cpu.data(), size_t(TILE_SIZE) * 4);
  }
}

void pull(int id) {
  swdb_strict::State &s = swdb_strict::state();
  if (id >= 0 && id < int(s.tiles.size())) std::memcpy(s.tiles[id].cpu.data(), tile_window(id), size_t(TILE_SIZE) * 4);
}

// A model operation: serialized, with the tile windows brought up to date afterwards.
template <class F> int64_t model(F body) {
  std::lock_guard<std::mutex> guard(model_lock());
  Mark marks[NUM_TILES];
  take(marks);
  const int64_t value = body();
  publish(marks);
  return value;
}

void *heap_pointer(int64_t value, uint64_t bytes) {
  const uintptr_t p = uintptr_t(value);
  return in_heap(p, bytes) ? reinterpret_cast<void *>(p) : nullptr;
}

// A region the strict model may read or write must lie in the candidate heap: the evaluator reads
// candidate memory only through the arena. A region outside it is refused by the strict layer's
// registration check.
void add_region(int64_t start, int64_t end) {
  if (uintptr_t(end) >= uintptr_t(start) && !in_heap(uintptr_t(start), uint64_t(end - start)))
    swdb_strict::check(false, "memory_region_registration");
  add_mem_region(reinterpret_cast<void *>(start), reinterpret_cast<void *>(end));
}

void finish(const Slot &s) {
  const int64_t count = s.a[1];
  const int kind = int(s.a[2]);
  void *base = count >= 0 && count < (int64_t(1) << 31) ? heap_pointer(s.a[0], uint64_t(count) * 4) : nullptr;
  if (base && kind == 0) {
    swdb_cert_record_result_i32(static_cast<const int32_t *>(base), size_t(count));
    swdb_cert_record_result_base(base, size_t(count));
  } else if (base && kind == 1) {
    swdb_cert_record_result_f32(static_cast<const float *>(base), size_t(count));
  }
  // Without a result record in the arena the run has no result: the certifier's verifier fails it.
  {
    std::lock_guard<std::mutex> guard(model_lock());
    swdb_cert_record_end();
  }
  finished = true;
}

void serve(Slot &s) {
  const int64_t *a = s.a;
  int64_t r = 0;
  switch (s.op) {
    // the 1.4 seams
    case SESSION_BEGIN: model([] { swdb_seam_session_begin(); return int64_t(0); }); break;
    case THREAD_CONTEXT: {
      dxc_context c;
      model([&] { c = swdb_seam_thread_context(); return int64_t(0); });
      for (int i = 0; i < 8; ++i) { s.context[i] = c.tile[i]; s.context[8 + i] = c.reg[i]; }
      break;
    }
    case WAIT: model([&] { swdb_seam_wait(int(a[0])); return int64_t(0); }); break;
    case GATHER: model([&] { swdb_seam_gather_i32(reinterpret_cast<void *>(a[0]), int(a[1]), int(a[2])); return int64_t(0); }); break;
    case STREAM_LOAD:
      model([&] { swdb_seam_stream_load_i32(reinterpret_cast<void *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4])); return int64_t(0); });
      break;
    case RANGE_LOOP:
      model([&] { swdb_seam_range_loop(int(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6])); return int64_t(0); });
      break;
    case ALU_SCALAR:
      model([&] { swdb_seam_alu_scalar(int(a[0]), int(a[1]), int(a[2]), Operation_t(a[3])); return int64_t(0); });
      break;
    case CLAIM: {
      void *slot_address = (a[0] & 3) == 0 ? heap_pointer(a[0], 4) : nullptr;
      r = slot_address ? (swdb_seam_claim_i32(static_cast<int32_t *>(slot_address), int32_t(a[1]), int32_t(a[2])) ? 1 : 0) : 2;
      break;
    }
    case PUSH: r = swdb_seam_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])) ? 1 : 0; break;
    case DIRECT_PUSH: swdb_seam_direct_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])); break;
    case SLIDE: {
      const int64_t count = a[2];
      const void *window = count >= 0 && count < (int64_t(1) << 31) ? heap_pointer(a[1], uint64_t(count) * 4) : nullptr;
      if (!window && count > 0) fail("a frontier window outside the shared arena", 87);
      swdb_seam_slide(reinterpret_cast<const void *>(a[0]), static_cast<const int32_t *>(window), size_t(count));
      break;
    }
    case RESET: swdb_seam_reset(reinterpret_cast<const void *>(a[0])); break;
    case CHUNK: model([] { __dxc_accelerated_chunk(); return int64_t(0); }); break;
    // the strict layer's interface
    case ALLOC_MAA: model([] { alloc_MAA(); return int64_t(0); }); break;
    case INIT_MAA: model([] { init_MAA(); return int64_t(0); }); break;
    case CLEAR_REGION: model([] { clear_mem_region(); return int64_t(0); }); break;
    case ADD_REGION: model([&] { add_region(a[0], a[1]); return int64_t(0); }); break;
    case NEW_TILE: r = model([] { return int64_t(get_new_tile<int>()); }); break;
    case NEW_REG: r = model([] { return int64_t(get_new_reg<int>()); }); break;
    case CONST: model([&] { maa_const<int>(int(a[0]), int(a[1])); return int64_t(0); }); break;
    case GET_REG: r = model([&] { return int64_t(get_reg<int>(int(a[0]))); }); break;
    case TILE_POINTER:
      r = model([&] { (void)get_cacheable_tile_pointer<int>(int(a[0])); return int64_t(reinterpret_cast<uintptr_t>(tile_window(int(a[0])))); });
      break;
    case TILE_SIZE_OP: r = model([&] { return int64_t(get_tile_size(int(a[0]))); }); break;
    case TILE_READY: r = model([&] { return int64_t(get_tile_ready(int(a[0]))); }); break;
    case WAIT_READY: model([&] { wait_ready(int(a[0])); return int64_t(0); }); break;
    case SET_TILE_SIZE: model([&] { pull(int(a[0])); set_tile_size(int(a[0]), uint16_t(a[1])); return int64_t(0); }); break;
    case SET_TILE_READY: model([&] { set_tile_ready(int(a[0]), uint16_t(a[1])); return int64_t(0); }); break;
    case MAA_STREAM_LOAD:
      model([&] { maa_stream_load<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5])); return int64_t(0); });
      break;
    case MAA_INDIRECT_LOAD:
      model([&] { maa_indirect_load<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3])); return int64_t(0); });
      break;
    case MAA_RANGE_LOOP:
      model([&] { maa_range_loop<int>(int(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]), int(a[7])); return int64_t(0); });
      break;
    case MAA_ALU_SCALAR:
      model([&] { maa_alu_scalar<int>(int(a[0]), int(a[1]), int(a[2]), Operation_t(a[3]), int(a[4])); return int64_t(0); });
      break;
    case MAA_STORE:
      model([&] { maa_indirect_store_vector<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4])); return int64_t(0); });
      break;
    case STRICT_SESSION_BEGIN: model([] { swdb_strict::session_begin(); return int64_t(0); }); break;
    case CHECK_FAIL: {
      char name[sizeof s.text];
      std::memcpy(name, s.text, sizeof name);
      name[sizeof name - 1] = '\0';
      model([&] { swdb_strict::check(false, name); return int64_t(0); });
      break;
    }
    case OPERATION_COUNT: r = model([] { return int64_t(swdb_strict::operation_count()); }); break;
    case FINISH: finish(s); break;
    default: fail("unknown request");
  }
  s.r[0] = r;
}

void *server(void *argument) {
  Slot &s = *slot(int(reinterpret_cast<intptr_t>(argument)));
  uint32_t last = 0;
  for (;;) {
    uint32_t request;
    for (unsigned spin = 0; (request = s.request.load(std::memory_order_acquire)) == last; ++spin) {
      if (spin < 4096) continue;
      if (spin < 200000) { sched_yield(); continue; }
      ::usleep(20);
    }
    swdb_eval::Caller &who = swdb_eval::caller();
    who.thread = s.thread;
    who.in_parallel = s.in_parallel;
    who.num_threads = s.num_threads;
    serve(s);
    last = request;
    s.reply.store(request, std::memory_order_release);
  }
  return nullptr;
}

int64_t source_argument(int argc, char **argv) {
  for (int i = 2; i + 1 < argc; ++i)
    if (std::strcmp(argv[i], "-r") == 0) return std::strtoll(argv[i + 1], nullptr, 10);
  return -1;
}
}  // namespace

int main(int argc, char **argv) {
  if (argc < 2) fail("usage: swdb-evaluator <candidate binary> <arguments...>", 2);
  swdb_cert_record_source(source_argument(argc, argv));

  // The arena: an unnamed shared memory object, mapped at the agreed address.
  char name[64];
  std::snprintf(name, sizeof name, "/swdb15.%d.%lx", int(::getpid()), long(::random()));
  const int fd = ::shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0600);
  if (fd < 0) fail("shm_open failed");
  ::shm_unlink(name);
  if (::ftruncate(fd, off_t(SIZE)) != 0) fail("arena size");
  void *mapped = ::mmap(reinterpret_cast<void *>(ADDRESS), SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  if (mapped != reinterpret_cast<void *>(ADDRESS)) fail("arena not mapped at its address");
  Header *h = header();
  h->magic = MAGIC;
  h->size = SIZE;
  h->evaluator_pid = int32_t(::getpid());
  h->slot_count = 0;
  h->heap_lock.clear();
  h->heap_top = HEAP_OFFSET;
  {
    std::lock_guard<std::mutex> guard(model_lock());
    publish(nullptr);
  }

  // The candidate's environment: no certification variable, the arena on descriptor 3.
  std::vector<std::string> values;
  for (char **e = environ; *e; ++e)
    if (std::strncmp(*e, "SWDB_CERT_", 10) != 0 && std::strncmp(*e, "SWDB_ARENA_", 11) != 0) values.push_back(*e);
  values.push_back("SWDB_ARENA_FD=3");
  std::vector<char *> envp;
  for (std::string &v : values) envp.push_back(&v[0]);
  envp.push_back(nullptr);
  std::vector<char *> args(argv + 1, argv + argc);
  args.push_back(nullptr);
  const int max_fd = int(::getdtablesize());
  const pid_t pid = ::fork();
  if (pid < 0) fail("fork failed");
  if (pid == 0) {
    if (fd != 3) { if (::dup2(fd, 3) < 0) ::_exit(95); }
    else ::fcntl(3, F_SETFD, 0);
    for (int other = 4; other < max_fd; ++other) ::close(other);
    ::execve(args[0], args.data(), envp.data());
    ::_exit(127);
  }
  candidate_pid = pid;
  ::close(fd);

  int started = 0;
  int status = 0;
  for (;;) {
    const int wanted = std::min(int(h->slot_count.load()), SLOTS);
    while (started < wanted) {
      pthread_t thread;
      if (pthread_create(&thread, nullptr, server, reinterpret_cast<void *>(intptr_t(started))) != 0) fail("server thread");
      pthread_detach(thread);
      ++started;
    }
    const pid_t done = ::waitpid(pid, &status, WNOHANG);
    if (done == pid) break;
    if (done < 0 && errno != EINTR) fail("waitpid");
    ::usleep(started ? 1000 : 100);
  }
  candidate_pid = 0;
  std::lock_guard<std::mutex> guard(model_lock());   // no request is half served when the status is chosen
  if (WIFEXITED(status)) {
    const int code = WEXITSTATUS(status);
    ::_exit(code == 0 && !finished ? 3 : code);
  }
  ::_exit(WIFSIGNALED(status) ? 128 + WTERMSIG(status) : 99);
}
