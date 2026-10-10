// Certification evaluator core, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// Included by exactly one translation unit of an evaluator binary: the DX100 evaluator
// (evaluator.cc) and the native-CPU evaluator (library/native/certification/v1_5/evaluator.cc),
// after they declare the record functions below. The includer defines
//   void evaluator_serve(swdb_arena::Slot &s);   // one request, in this process
//   void evaluator_prepare();                    // after the arena exists, before the candidate
//
// Usage: <evaluator> <candidate binary> <candidate arguments...>
//
// The core creates the shared arena (arena.hpp), records the run's source vertex from its own
// arguments, and starts the candidate binary as a child process whose only extra descriptor is the
// arena (descriptor 3, which the client closes once mapped); the child's environment has neither
// record nor plan variable (record.cc read and removed both before main). One server thread per
// candidate request slot performs each request in this process. FINISH: the returned vector is read
// from the arena by the evaluator, and the evaluator writes the result and end records.
//
// Exit status: 0 when the candidate exited 0 after FINISH; 86 or 88 when the strict layer or the
// frontier ledger ended the run (as in 1.4); 87 when the candidate passed a frontier window outside
// the arena; 3 when the candidate exited 0 without FINISH; otherwise the candidate's status (128 +
// signal number for a signal).
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
#include "arena.hpp"

extern char **environ;

// record.cc (certify 1.4, unchanged)
void swdb_cert_record_source(int64_t source);
void swdb_cert_record_result_i32(const int32_t *values, size_t count);
void swdb_cert_record_result_f32(const float *values, size_t count);
void swdb_cert_record_result_base(const void *base, size_t count);
void swdb_cert_record_end();

void evaluator_serve(swdb_arena::Slot &s);
void evaluator_prepare();

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

// Serializes model state and the end record (requests that touch only the ledger take its own lock).
std::mutex &model_lock() { static std::mutex m; return m; }

void *heap_pointer(int64_t value, uint64_t bytes) {
  const uintptr_t p = uintptr_t(value);
  return in_heap(p, bytes) ? reinterpret_cast<void *>(p) : nullptr;
}

// FINISH: the returned vector, read by the evaluator from the arena (a location outside the heap
// gives no result record, and the certifier's verifier fails the run).
void finish(const Slot &s) {
  const int64_t count = s.a[1];
  const int kind = int(s.a[2]);
  void *base = count >= 0 && count < (int64_t(1) << 31) ? heap_pointer(s.a[0], uint64_t(count) * 4) : nullptr;
  std::lock_guard<std::mutex> guard(model_lock());
  if (base && kind == 0) {
    swdb_cert_record_result_i32(static_cast<const int32_t *>(base), size_t(count));
    swdb_cert_record_result_base(base, size_t(count));
  } else if (base && kind == 1) {
    swdb_cert_record_result_f32(static_cast<const float *>(base), size_t(count));
  }
  swdb_cert_record_end();
  finished = true;
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
    s.r[0] = 0;
    if (s.op == FINISH) finish(s);
    else evaluator_serve(s);
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
  if (argc < 2) fail("usage: <evaluator> <candidate binary> <arguments...>", 2);
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
  evaluator_prepare();

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
  std::lock_guard<std::mutex> guard(model_lock());   // no FINISH is half written when the status is chosen
  if (WIFEXITED(status)) {
    const int code = WEXITSTATUS(status);
    ::_exit(code == 0 && !finished ? 3 : code);
  }
  ::_exit(WIFSIGNALED(status) ? 128 + WTERMSIG(status) : 99);
}
