// Candidate-process runner of library-operation certification 1.2. Created: 2026-10-05 ET (ticket 78).
// Original SWDB code. Agent-decided under Yan-Ru's delegation; revisable.
//
// Linked into the candidate binary with the candidate's unit only, compiled with two macros on this
// object's command line: SWDB_LO_FAMILY_<FAMILY> and SWDB_LO_RUN_SYMBOL (the candidate adapter's
// extern "C" entry). It holds no record channel and no plan, and writes no record. It maps the arena
// its evaluator created (descriptor SWDB_ARENA_FD, closed after mapping), copies every input and the
// output canary from the call block into this process's own heap (a sanitized build keeps its
// redzones around each operand, as under 1.1), calls the entry once, copies the output and the inputs
// back into the arena, and marks the call done. The evaluator judges the arena.
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include "call.hpp"

namespace {
using swdb_lo_call::Call;

const Call &attach() {
  const char *value = std::getenv("SWDB_ARENA_FD");
  if (!value) std::_Exit(96);
  const int fd = std::atoi(value);
  ::unsetenv("SWDB_ARENA_FD");
  void *mapped = ::mmap(reinterpret_cast<void *>(swdb_arena::ADDRESS), swdb_arena::SIZE, PROT_READ | PROT_WRITE,
                        MAP_SHARED, fd, 0);
  ::close(fd);
  if (mapped != reinterpret_cast<void *>(swdb_arena::ADDRESS)) std::_Exit(96);
  const Call &c = *swdb_lo_call::call();
  if (swdb_arena::header()->magic != swdb_arena::MAGIC || c.magic != swdb_lo_call::MAGIC) std::_Exit(96);
  return c;
}

struct Operand {
  std::vector<unsigned char> bytes;
  unsigned char *arena;
};

std::vector<Operand> &operands() { static std::vector<Operand> value; return value; }

template <typename T> T *operand(const Call &c, int k) {
  if (k >= c.inputs || !swdb_arena::in_heap(uintptr_t(c.input_address[k]), c.input_bytes[k])) std::_Exit(96);
  Operand o;
  o.arena = reinterpret_cast<unsigned char *>(uintptr_t(c.input_address[k]));
  o.bytes.assign(o.arena, o.arena + c.input_bytes[k]);
  operands().push_back(o);
  return reinterpret_cast<T *>(operands().back().bytes.data());
}

int done(const Call &c, std::vector<double> &out) {
  std::memcpy(reinterpret_cast<void *>(uintptr_t(c.output_address)), out.data(), out.size() * sizeof(double));
  for (const Operand &o : operands()) std::memcpy(o.arena, o.bytes.data(), o.bytes.size());
  swdb_lo_call::call()->done.store(1);
  return 0;
}

std::vector<double> output(const Call &c) {
  if (!swdb_arena::in_heap(uintptr_t(c.output_address), c.output_count * sizeof(double))) std::_Exit(96);
  const double *arena = reinterpret_cast<const double *>(uintptr_t(c.output_address));
  return std::vector<double>(arena, arena + c.output_count);
}
}  // namespace

#if defined(SWDB_LO_FAMILY_PACK)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, const std::int32_t *, std::size_t,
                                   std::size_t, std::int64_t, std::int64_t, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const double *src = operand<double>(c, 0);
  const std::int32_t *chain0 = operand<std::int32_t>(c, 1), *chain1 = operand<std::int32_t>(c, 2);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), src, chain0, chain1, std::size_t(c.scalar[0]), std::size_t(c.scalar[1]), c.scalar[2],
                     c.scalar[3], std::size_t(c.scalar[4]));
  return done(c, out);
}
#elif defined(SWDB_LO_FAMILY_GATHER)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const double *src = operand<double>(c, 0);
  const std::int32_t *idx = operand<std::int32_t>(c, 1);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), src, idx, std::size_t(c.scalar[0]), std::size_t(c.scalar[1]));
  return done(c, out);
}
#elif defined(SWDB_LO_FAMILY_REGROUP)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const double *, const double *, std::size_t, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const double *a0 = operand<double>(c, 0), *a1 = operand<double>(c, 1), *a2 = operand<double>(c, 2);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), a0, a1, a2, std::size_t(c.scalar[0]), std::size_t(c.scalar[1]));
  return done(c, out);
}
#elif defined(SWDB_LO_FAMILY_BIN_DRAIN)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const std::int32_t *, const double *, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const std::int32_t *dests = operand<std::int32_t>(c, 0);
  const double *vals = operand<double>(c, 1);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), dests, vals, std::size_t(c.scalar[0]));
  return done(c, out);
}
#elif defined(SWDB_LO_FAMILY_GATHER_STREAM)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t, std::size_t,
                                   std::size_t, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const double *src = operand<double>(c, 0);
  const std::int32_t *idx = operand<std::int32_t>(c, 1);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), src, idx, std::size_t(c.scalar[0]), std::size_t(c.scalar[1]), std::size_t(c.scalar[2]),
                     std::size_t(c.scalar[3]));
  return done(c, out);
}
#elif defined(SWDB_LO_FAMILY_RELABEL)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t);
int main() {
  const Call &c = attach();
  operands().reserve(4);
  const double *values = operand<double>(c, 0);
  const std::int32_t *perm = operand<std::int32_t>(c, 1);
  std::vector<double> out = output(c);
  SWDB_LO_RUN_SYMBOL(out.data(), values, perm, std::size_t(c.scalar[0]));
  return done(c, out);
}
#else
#error "define SWDB_LO_FAMILY_<FAMILY>"
#endif
