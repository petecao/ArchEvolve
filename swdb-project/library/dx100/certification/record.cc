// Evaluator record channel for candidate certification (certify 1.3). Created: 2026-10-04 ET
// (ticket 70).
//
// `swdb certify` opens a fresh record file for each run and passes its descriptor number in
// SWDB_CERT_RECORD_FD. This separately compiled trusted object reads the number once, before
// main, then removes the variable. Every line it writes is raw data; the certifier computes every
// named check from these lines out of process and never reads a verdict from stdout or stderr:
//
//   begin 1                         the channel opened
//   strict <name>                   the strict layer's check <name> failed (the process then exits 86)
//   frontier <n> <v1> ... <vn>      one window of the shared queue at the protected frontier print
//   result i32|f32 <n> <values>     the kernel's returned vector (f32 as IEEE-754 bit patterns, hex)
//   witness chunks=<c> operations=<o>
//   end                             the trusted driver returned the kernel's result
//
// A frontier window that repeats a vertex is recorded and the run then stops (exit 88), as the
// in-process check of certify 1.0-1.2 did; the duplicate itself is judged from the record.
#include <algorithm>
#include <cerrno>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>
#include <fcntl.h>
#include <unistd.h>
#include "dxc_lowering.hpp"

namespace {
int &channel() { static int fd = -1; return fd; }
std::mutex &channel_lock() { static std::mutex m; return m; }

void emit(const std::string &line) {
  std::lock_guard<std::mutex> guard(channel_lock());
  if (channel() < 0) return;
  const char *data = line.data();
  size_t left = line.size();
  while (left) {
    const ssize_t wrote = ::write(channel(), data, left);
    if (wrote < 0 && errno == EINTR) continue;
    if (wrote <= 0) { channel() = -1; return; }  // a lost channel fails closed: no `end` is recorded
    data += wrote;
    left -= size_t(wrote);
  }
}

__attribute__((constructor)) void swdb_cert_open_channel() {
  const char *value = std::getenv("SWDB_CERT_RECORD_FD");
  if (!value) return;
  char *end = nullptr;
  const long fd = std::strtol(value, &end, 10);
  if (end && *end == '\0' && fd > 2 && fd < 65536 && ::fcntl(int(fd), F_GETFD) != -1) channel() = int(fd);
  ::unsetenv("SWDB_CERT_RECORD_FD");
  emit("begin 1\n");
}
}  // namespace

void swdb_cert_record_strict(const char *name) {
  std::string line = "strict ";
  for (const char *p = name; p && *p; ++p) line += (*p >= 'a' && *p <= 'z') || *p == '_' ? *p : '?';
  emit(line + "\n");
}

void swdb_cert_record_frontier(const int32_t *window, size_t count) {
  std::string line = "frontier " + std::to_string(count);
  for (size_t i = 0; i < count; ++i) line += " " + std::to_string(window[i]);
  emit(line + "\n");
  std::vector<int32_t> sorted(window, window + count);
  std::sort(sorted.begin(), sorted.end());
  if (std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end()) std::_Exit(88);
}

void swdb_cert_record_result_i32(const int32_t *values, size_t count) {
  std::string line = "result i32 " + std::to_string(count);
  for (size_t i = 0; i < count; ++i) line += " " + std::to_string(values[i]);
  emit(line + "\n");
}

void swdb_cert_record_result_f32(const float *values, size_t count) {
  std::string line = "result f32 " + std::to_string(count);
  char hex[16];
  for (size_t i = 0; i < count; ++i) {
    uint32_t bits;
    std::memcpy(&bits, &values[i], 4);
    std::snprintf(hex, sizeof hex, " %08" PRIx32, bits);
    line += hex;
  }
  emit(line + "\n");
}

void swdb_cert_record_end() {
  emit("witness chunks=" + std::to_string((unsigned long long)swdb_dxc::chunks().load()) +
       " operations=" + std::to_string((unsigned long long)swdb_strict::operation_count()) + "\n");
  emit("end\n");
}
