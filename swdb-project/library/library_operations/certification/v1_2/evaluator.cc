// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Adapted 2026-10-05 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: AgenticRefiner/refiner/synthesis/drivers/{pack,gather,regroup,bin_drain,gather_stream}_run.cpp.tmpl
// Trusted evaluator of library-operation certification 1.2. Created: 2026-10-05 ET (ticket 78).
// Original SWDB code, adapted from the 1.1 driver (../v1_1/driver.cc; same arguments, inputs, output
// canary, driver faults, frame check and records). Agent-decided under Yan-Ru's delegation; revisable.
//
// Usage: <evaluator> <candidate binary> <the family's 1.1 driver arguments...>
//
// Linked with the unchanged 1.1 record writer (../v1_1/record.cc: the record pipe and the plan are
// read and removed before main). It never runs candidate code: it reads the case, places every input
// and the output canary in the shared arena (call.hpp) and keeps private copies of the inputs, starts
// the candidate binary as a child (only the arena is passed on, as descriptor 3), and waits. When the
// child exited 0 after its call, the evaluator applies the plan's driver fault, checks the frame and
// records the output from its own view of the arena, then `end`. Otherwise it records nothing more
// and exits with the child's status (128 + signal for a signal; 3 for exit 0 without a call).
#include <cerrno>
#include <csignal>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include "call.hpp"

int swdb_lo_plan_fault();
unsigned long long swdb_lo_plan_seed();
void swdb_lo_record(const std::string &line);
extern char **environ;

namespace {
using namespace swdb_arena;
using swdb_lo_call::Call;

[[noreturn]] void fail(const char *what) {
  std::fprintf(stderr, "swdb library-operation evaluator: %s\n", what);
  std::exit(95);
}

uint64_t &heap_top() { static uint64_t top = HEAP_OFFSET; return top; }
unsigned char *arena_bytes(std::size_t bytes) {
  const uint64_t at = (heap_top() + 63) & ~uint64_t(63);
  if (at + bytes + 64 > SIZE) fail("arena exhausted");
  heap_top() = at + bytes;
  return reinterpret_cast<unsigned char *>(ADDRESS + at);
}

struct Tracked {
  std::string name;
  unsigned char *data;
  std::size_t bytes;
  std::vector<unsigned char> copy;   // the evaluator's private copy
};
std::vector<Tracked> &tracked() { static std::vector<Tracked> value; return value; }

// A case input, read from the case folder into the arena; the evaluator keeps a private copy.
template <typename T>
T *input(const char *name, const std::string &path, std::size_t *count = nullptr) {
  FILE *f = std::fopen(path.c_str(), "rb");
  if (!f) std::exit(2);
  std::fseek(f, 0, SEEK_END);
  const long sz = std::ftell(f);
  std::fseek(f, 0, SEEK_SET);
  const std::size_t bytes = (std::size_t)sz / sizeof(T) * sizeof(T);
  unsigned char *data = arena_bytes(bytes);
  if (bytes > 0 && std::fread(data, 1, bytes, f) != bytes) std::exit(2);
  std::fclose(f);
  Tracked t;
  t.name = name;
  t.data = data;
  t.bytes = bytes;
  t.copy.assign(data, data + bytes);
  tracked().push_back(t);
  Call &c = *swdb_lo_call::call();
  if (c.inputs >= swdb_lo_call::MAX_INPUTS) fail("too many inputs");
  c.input_address[c.inputs] = uint64_t(reinterpret_cast<uintptr_t>(data));
  c.input_bytes[c.inputs] = bytes;
  ++c.inputs;
  if (count) *count = bytes / sizeof(T);
  return reinterpret_cast<T *>(data);
}

double *canary(std::size_t n) {
  double *out = reinterpret_cast<double *>(arena_bytes(n * sizeof(double)));
  for (std::size_t i = 0; i < n; ++i) out[i] = 1.0 + (double)(i % 7);
  Call &c = *swdb_lo_call::call();
  c.output_address = uint64_t(reinterpret_cast<uintptr_t>(out));
  c.output_count = n;
  return out;
}

// After the candidate's call: the plan's driver fault, the frame check, the output, end (1.1's).
int finish(double *out_data, std::size_t out_size) {
  const int fault = swdb_lo_plan_fault();
  const unsigned long long seed = swdb_lo_plan_seed();
  if (fault == 1) {  // input_write: one input bit flipped by trusted code
    std::vector<std::size_t> live;
    for (std::size_t k = 0; k < tracked().size(); ++k)
      if (tracked()[k].bytes) live.push_back(k);
    if (!live.empty()) {
      Tracked &t = tracked()[live[seed % live.size()]];
      const std::size_t byte = std::size_t((seed >> 20) % t.bytes);
      t.data[byte] ^= 1u;
      swdb_lo_record("fault input_write " + t.name + " " + std::to_string((unsigned long long)byte));
    }
  } else if (fault == 2 && out_size) {  // output_perturb: one output bit flipped by trusted code
    const std::size_t element = std::size_t(seed % out_size);
    reinterpret_cast<unsigned char *>(&out_data[element])[0] ^= 1u;
    swdb_lo_record("fault output_perturb " + std::to_string((unsigned long long)element));
  }
  bool clean = true;
  for (std::size_t k = 0; k < tracked().size(); ++k) {
    const Tracked &t = tracked()[k];
    std::size_t first = 0, changed = 0;
    for (std::size_t b = 0; b < t.bytes; ++b)
      if (t.data[b] != t.copy[b]) {
        if (!changed) first = b;
        ++changed;
      }
    if (changed) {
      clean = false;
      swdb_lo_record("frame violation " + t.name + " " + std::to_string((unsigned long long)first) + " " +
                     std::to_string((unsigned long long)changed));
    }
  }
  if (clean) swdb_lo_record("frame ok");
  static const char digits[] = "0123456789abcdef";
  const unsigned char *bytes = reinterpret_cast<const unsigned char *>(out_data);
  const std::size_t count = out_size * sizeof(double);
  std::string line = "result " + std::to_string((unsigned long long)count) + " ";
  line.reserve(line.size() + 2 * count);
  for (std::size_t i = 0; i < count; ++i) {
    line += digits[bytes[i] >> 4];
    line += digits[bytes[i] & 15];
  }
  swdb_lo_record(line);
  swdb_lo_record("end");
  return 0;
}

std::size_t arg(char **argv, int i) { return std::strtoull(argv[i], nullptr, 10); }

// Maps the arena and clears the call block.
int create_arena() {
  char name[64];
  std::snprintf(name, sizeof name, "/swdblo12.%d.%lx", int(::getpid()), long(::random()));
  const int fd = ::shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0600);
  if (fd < 0) fail("shm_open failed");
  ::shm_unlink(name);
  if (::ftruncate(fd, off_t(SIZE)) != 0) fail("arena size");
  void *mapped = ::mmap(reinterpret_cast<void *>(ADDRESS), SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  if (mapped != reinterpret_cast<void *>(ADDRESS)) fail("arena not mapped at its address");
  header()->magic = MAGIC;
  header()->size = SIZE;
  header()->evaluator_pid = int32_t(::getpid());
  Call &c = *swdb_lo_call::call();
  std::memset(static_cast<void *>(&c), 0, sizeof c);
  c.magic = swdb_lo_call::MAGIC;
  return fd;
}

// Runs the candidate binary with the arena on descriptor 3 and no certification variable; returns
// its exit status (the evaluator's convention above).
int run_candidate(const char *binary, int fd) {
  std::vector<std::string> values;
  for (char **e = environ; *e; ++e)
    if (std::strncmp(*e, "SWDB_LO_", 8) != 0 && std::strncmp(*e, "SWDB_ARENA_", 11) != 0) values.push_back(*e);
  values.push_back("SWDB_ARENA_FD=3");
  std::vector<char *> envp;
  for (std::string &v : values) envp.push_back(&v[0]);
  envp.push_back(nullptr);
  char *args[] = {const_cast<char *>(binary), nullptr};
  const int max_fd = int(::getdtablesize());
  std::fflush(nullptr);
  const pid_t pid = ::fork();
  if (pid < 0) fail("fork failed");
  if (pid == 0) {
    if (fd != 3) { if (::dup2(fd, 3) < 0) ::_exit(95); }
    else ::fcntl(3, F_SETFD, 0);
    for (int other = 4; other < max_fd; ++other) ::close(other);
    ::execve(binary, args, envp.data());
    ::_exit(127);
  }
  ::close(fd);
  int status = 0;
  while (::waitpid(pid, &status, 0) < 0)
    if (errno != EINTR) fail("waitpid");
  if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
  if (!WIFEXITED(status)) return 99;
  const int code = WEXITSTATUS(status);
  return code == 0 && swdb_lo_call::call()->done.load() != 1 ? 3 : code;
}

int complete(const char *binary, int fd, double *out, std::size_t n) {
  const int code = run_candidate(binary, fd);
  if (code != 0) return code;
  return finish(out, n);
}
}  // namespace

// argv[1] is the candidate binary; argv[1..] read as the 1.1 driver's argv[0..].
int main(int argc_all, char **argv_all) {
  if (argc_all < 2) return 2;
  const int argc = argc_all - 1;
  char **argv = argv_all + 1;
  const char *binary = argv[0];
  const int fd = create_arena();
  Call &c = *swdb_lo_call::call();
#if defined(SWDB_LO_FAMILY_PACK)
  if (argc != 7) return 2;
  const std::size_t n = arg(argv, 1), n_src = arg(argv, 2), depth = arg(argv, 3);
  const std::int64_t coeff = std::strtoll(argv[4], nullptr, 10), offset = std::strtoll(argv[5], nullptr, 10);
  const std::string dir = argv[6];
  c.family = swdb_lo_call::PACK;
  input<double>("src", dir + "/src.bin");
  input<std::int32_t>("chain0", dir + "/chain0.bin");
  input<std::int32_t>("chain1", dir + "/chain1.bin");
  double *out = canary(n);
  c.scalar[0] = int64_t(depth); c.scalar[1] = int64_t(n); c.scalar[2] = coeff; c.scalar[3] = offset;
  c.scalar[4] = int64_t(n_src);
  return complete(binary, fd, out, n);
#elif defined(SWDB_LO_FAMILY_GATHER)
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), n_src = arg(argv, 2);
  const std::string dir = argv[3];
  c.family = swdb_lo_call::GATHER;
  input<double>("src", dir + "/src.bin");
  input<std::int32_t>("idx", dir + "/idx.bin");
  double *out = canary(n);
  c.scalar[0] = int64_t(n); c.scalar[1] = int64_t(n_src);
  return complete(binary, fd, out, n);
#elif defined(SWDB_LO_FAMILY_REGROUP)
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), k = arg(argv, 2);
  const std::string dir = argv[3];
  if (k != 3) return 2;
  c.family = swdb_lo_call::REGROUP;
  input<double>("arr0", dir + "/arr0.bin");
  input<double>("arr1", dir + "/arr1.bin");
  input<double>("arr2", dir + "/arr2.bin");
  double *out = canary(k * n);
  c.scalar[0] = int64_t(k); c.scalar[1] = int64_t(n);
  return complete(binary, fd, out, k * n);
#elif defined(SWDB_LO_FAMILY_BIN_DRAIN)
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), n_target = arg(argv, 2);
  const std::string dir = argv[3];
  c.family = swdb_lo_call::BIN_DRAIN;
  input<std::int32_t>("dests", dir + "/dests.bin");
  input<double>("vals", dir + "/vals.bin");
  double *out = canary(n_target);
  c.scalar[0] = int64_t(n);
  return complete(binary, fd, out, n_target);
#elif defined(SWDB_LO_FAMILY_GATHER_STREAM)
  if (argc != 6) return 2;
  const std::size_t rows = arg(argv, 1), row_len = arg(argv, 2), dst_stride = arg(argv, 3), src_stride = arg(argv, 4);
  const std::string dir = argv[5];
  c.family = swdb_lo_call::GATHER_STREAM;
  input<double>("src", dir + "/src.bin");
  input<std::int32_t>("idx", dir + "/idx.bin");
  double *out = canary(rows * dst_stride);
  c.scalar[0] = int64_t(rows); c.scalar[1] = int64_t(row_len); c.scalar[2] = int64_t(dst_stride);
  c.scalar[3] = int64_t(src_stride);
  return complete(binary, fd, out, rows * dst_stride);
#elif defined(SWDB_LO_FAMILY_RELABEL)
  if (argc != 3) return 2;
  const std::size_t n = arg(argv, 1);
  const std::string dir = argv[2];
  c.family = swdb_lo_call::RELABEL;
  input<double>("values", dir + "/values.bin");
  input<std::int32_t>("perm", dir + "/perm.bin");
  double *out = canary(n);
  c.scalar[0] = int64_t(n);
  return complete(binary, fd, out, n);
#else
#error "define SWDB_LO_FAMILY_<FAMILY>"
#endif
}
