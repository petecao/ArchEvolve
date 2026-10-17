// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Adapted 2026-10-05 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: AgenticRefiner/refiner/synthesis/drivers/{pack,gather,regroup,bin_drain,gather_stream}_run.cpp.tmpl
// Trusted differential-test driver of library-operation certification 1.1. Created: 2026-10-05 ET
// (ticket 77). Original SWDB code, adapted from the family run templates in ../../drivers/ (ported
// from Extensa; same arguments, inputs, output canary and frame check). Agent-decided under
// Yan-Ru's delegation; revisable.
//
// Compiled separately from the candidate, once per family and build, with two macros on this
// object's command line only: SWDB_LO_FAMILY_<FAMILY> and SWDB_LO_RUN_SYMBOL (the reference or the
// candidate adapter's extern "C" entry). It reads the case, keeps a copy of every input, seeds the
// output with the canary, calls the entry, then (in trusted code) applies the plan's driver fault,
// records the frame check and the output on the record channel, and records `end`. It prints
// nothing a verdict depends on: the certifier compares the recorded output with the reference
// output out of process.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

int swdb_lo_plan_fault();
unsigned long long swdb_lo_plan_seed();
void swdb_lo_record(const std::string &line);

namespace {
template <typename T>
std::vector<T> slurp_as(const std::string &p) {
  FILE *f = std::fopen(p.c_str(), "rb");
  if (!f) std::exit(2);
  std::fseek(f, 0, SEEK_END);
  long sz = std::ftell(f);
  std::fseek(f, 0, SEEK_SET);
  std::vector<T> buf((std::size_t)sz / sizeof(T));
  if (sz > 0 && std::fread(&buf[0], 1, (std::size_t)sz, f) != (std::size_t)sz) std::exit(2);
  std::fclose(f);
  return buf;
}

struct Tracked {
  std::string name;
  unsigned char *data;
  std::size_t bytes;
  std::vector<unsigned char> copy;
};
std::vector<Tracked> &tracked() { static std::vector<Tracked> value; return value; }

template <typename T>
void track(const char *name, std::vector<T> &values) {
  Tracked t;
  t.name = name;
  t.data = reinterpret_cast<unsigned char *>(values.data());
  t.bytes = values.size() * sizeof(T);
  t.copy.assign(t.data, t.data + t.bytes);
  tracked().push_back(t);
}

std::vector<double> canary(std::size_t n) {
  std::vector<double> out(n);
  for (std::size_t i = 0; i < out.size(); ++i) out[i] = 1.0 + (double)(i % 7);
  return out;
}

// After the call: the plan's driver fault, the frame check, the output, end.
int finish(std::vector<double> &out) {
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
  } else if (fault == 2 && !out.empty()) {  // output_perturb: one output bit flipped by trusted code
    const std::size_t element = std::size_t(seed % out.size());
    reinterpret_cast<unsigned char *>(&out[element])[0] ^= 1u;
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
  const unsigned char *bytes = reinterpret_cast<const unsigned char *>(out.data());
  const std::size_t count = out.size() * sizeof(double);
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
}  // namespace

#if defined(SWDB_LO_FAMILY_PACK)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, const std::int32_t *, std::size_t,
                                   std::size_t, std::int64_t, std::int64_t, std::size_t);
int main(int argc, char **argv) {
  if (argc != 7) return 2;
  const std::size_t n = arg(argv, 1), n_src = arg(argv, 2), depth = arg(argv, 3);
  const std::int64_t coeff = std::strtoll(argv[4], nullptr, 10), offset = std::strtoll(argv[5], nullptr, 10);
  const std::string dir = argv[6];
  std::vector<double> src = slurp_as<double>(dir + "/src.bin");
  std::vector<std::int32_t> chain0 = slurp_as<std::int32_t>(dir + "/chain0.bin");
  std::vector<std::int32_t> chain1 = slurp_as<std::int32_t>(dir + "/chain1.bin");
  track("src", src);
  track("chain0", chain0);
  track("chain1", chain1);
  std::vector<double> out = canary(n);
  SWDB_LO_RUN_SYMBOL(out.data(), src.data(), chain0.data(), chain1.data(), depth, n, coeff, offset, n_src);
  return finish(out);
}
#elif defined(SWDB_LO_FAMILY_GATHER)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t, std::size_t);
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), n_src = arg(argv, 2);
  const std::string dir = argv[3];
  std::vector<double> src = slurp_as<double>(dir + "/src.bin");
  std::vector<std::int32_t> idx = slurp_as<std::int32_t>(dir + "/idx.bin");
  track("src", src);
  track("idx", idx);
  std::vector<double> out = canary(n);
  SWDB_LO_RUN_SYMBOL(out.data(), src.data(), idx.data(), n, n_src);
  return finish(out);
}
#elif defined(SWDB_LO_FAMILY_REGROUP)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const double *, const double *, std::size_t, std::size_t);
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), k = arg(argv, 2);
  const std::string dir = argv[3];
  if (k != 3) return 2;
  std::vector<double> a0 = slurp_as<double>(dir + "/arr0.bin");
  std::vector<double> a1 = slurp_as<double>(dir + "/arr1.bin");
  std::vector<double> a2 = slurp_as<double>(dir + "/arr2.bin");
  track("arr0", a0);
  track("arr1", a1);
  track("arr2", a2);
  std::vector<double> out = canary(k * n);
  SWDB_LO_RUN_SYMBOL(out.data(), a0.data(), a1.data(), a2.data(), k, n);
  return finish(out);
}
#elif defined(SWDB_LO_FAMILY_BIN_DRAIN)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const std::int32_t *, const double *, std::size_t);
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  const std::size_t n = arg(argv, 1), n_target = arg(argv, 2);
  const std::string dir = argv[3];
  std::vector<std::int32_t> dests = slurp_as<std::int32_t>(dir + "/dests.bin");
  std::vector<double> vals = slurp_as<double>(dir + "/vals.bin");
  track("dests", dests);
  track("vals", vals);
  std::vector<double> out = canary(n_target);
  SWDB_LO_RUN_SYMBOL(out.data(), dests.data(), vals.data(), n);
  return finish(out);
}
#elif defined(SWDB_LO_FAMILY_GATHER_STREAM)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t, std::size_t,
                                   std::size_t, std::size_t);
int main(int argc, char **argv) {
  if (argc != 6) return 2;
  const std::size_t rows = arg(argv, 1), row_len = arg(argv, 2), dst_stride = arg(argv, 3), src_stride = arg(argv, 4);
  const std::string dir = argv[5];
  std::vector<double> src = slurp_as<double>(dir + "/src.bin");
  std::vector<std::int32_t> idx = slurp_as<std::int32_t>(dir + "/idx.bin");
  track("src", src);
  track("idx", idx);
  std::vector<double> out = canary(rows * dst_stride);
  SWDB_LO_RUN_SYMBOL(out.data(), src.data(), idx.data(), rows, row_len, dst_stride, src_stride);
  return finish(out);
}
#elif defined(SWDB_LO_FAMILY_RELABEL)
extern "C" void SWDB_LO_RUN_SYMBOL(double *, const double *, const std::int32_t *, std::size_t);
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const std::size_t n = arg(argv, 1);
  const std::string dir = argv[2];
  std::vector<double> values = slurp_as<double>(dir + "/values.bin");
  std::vector<std::int32_t> perm = slurp_as<std::int32_t>(dir + "/perm.bin");
  track("values", values);
  track("perm", perm);
  std::vector<double> out = canary(n);
  SWDB_LO_RUN_SYMBOL(out.data(), values.data(), perm.data(), n);
  return finish(out);
}
#else
#error "define SWDB_LO_FAMILY_<FAMILY>"
#endif
