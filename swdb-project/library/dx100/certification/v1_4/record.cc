// Evaluator record channel and run plan, certify 1.4. Created: 2026-10-05 ET (ticket 76).
// Agent-decided under Yan-Ru's delegation; revisable. Certify 1.3 keeps ../record.cc.
//
// Every run (positive or control) gets two descriptors from the harness, named by
// SWDB_CERT_RECORD_FD (a fresh record file, write only) and SWDB_CERT_PLAN_FD (the read end of a
// pipe holding a fixed-length plan line). This trusted object reads both numbers once, before
// main, drains and closes the plan pipe, and removes both variables. The plan names the fault the
// trusted seams apply in this run, or none, plus a nonce echoed into the record. A positive run's
// plan has the same length as a control's.
//
// Records (raw data; the certifier computes every check out of process):
//   begin 2
//   plan <nonce>                     the nonce of the plan this run received
//   source <s>                       the trusted driver's source vertex
//   strict <name> <a>                a strict-layer check failed (the process then exits 86);
//                                    a = 2 inside a seam call the fault modified, 1 on a thread the
//                                    fault acted on earlier, 0 otherwise
//   fault <kind> <thread> [<n> <values>]   the seam's fault acted (control runs only)
//   epoch <queue> <n> <events>       at a slide of <queue>: claims, pushes and gathers since the
//                                    previous slide, in one global order (see seams.cc)
//   window <queue> <n> <values>      the new window of <queue> after that slide
//   result i32|f32 <n> <values>      the kernel's returned vector (f32 as IEEE-754 bit patterns)
//   result_base <address> <n>        the returned vector's buffer (hex), BFS only
//   witness chunks=<c> operations=<o>
//   end
// A window that repeats a value is recorded, then the run stops (exit 88) as in 1.0-1.3.
#include <cerrno>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <fcntl.h>
#include <unistd.h>
#include "dxc_lowering.hpp"

int swdb_seam_attribution(int thread);   // seams.cc

namespace {
struct Plan { int fault = -1; char nonce[33] = {0}; bool read = false; };

int parse_fd(const char *name) {
  const char *value = std::getenv(name);
  if (!value) return -1;
  char *end = nullptr;
  const long fd = std::strtol(value, &end, 10);
  ::unsetenv(name);
  if (!end || *end != '\0' || fd <= 2 || fd >= 65536 || ::fcntl(int(fd), F_GETFD) == -1) return -1;
  return int(fd);
}

int &channel() { static int fd = parse_fd("SWDB_CERT_RECORD_FD"); return fd; }
std::mutex &channel_lock() { static std::mutex m; return m; }

void write_all(const std::string &line) {
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

// The plan line: "plan 2 <fault index, 2 digits> <nonce, 32 hex>\n" (43 bytes). Index 0 is no fault.
Plan read_plan() {
  Plan plan;
  const int fd = parse_fd("SWDB_CERT_PLAN_FD");
  if (fd < 0) return plan;
  char buffer[64] = {0};
  size_t got = 0;
  while (got < sizeof buffer - 1) {
    const ssize_t n = ::read(fd, buffer + got, sizeof buffer - 1 - got);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) break;
    got += size_t(n);
  }
  ::close(fd);
  int fault = -1;
  char nonce[33] = {0};
  if (got == 43 && std::sscanf(buffer, "plan 2 %2d %32[0-9a-f]", &fault, nonce) == 2 && std::strlen(nonce) == 32 &&
      fault >= 0 && fault < 16) {
    plan.fault = fault;
    std::memcpy(plan.nonce, nonce, 33);
    plan.read = true;
  }
  return plan;
}

Plan &plan_state() { static Plan plan = read_plan(); return plan; }

struct Opening {
  Opening() {
    channel();
    const Plan &plan = plan_state();
    std::lock_guard<std::mutex> guard(channel_lock());
    if (channel() < 0) return;
    write_all("begin 2\n");
    if (plan.read) write_all(std::string("plan ") + plan.nonce + "\n");
  }
};
Opening &opening() { static Opening value; return value; }

void emit(const std::string &line) {
  opening();
  std::lock_guard<std::mutex> guard(channel_lock());
  if (channel() < 0) return;
  write_all(line);
}

__attribute__((constructor)) void swdb_cert_open_channel() { opening(); }
}  // namespace

// The fault index of this run's plan: 0 none; -1 no valid plan (the seams then apply no fault and
// the record has no plan line, so the certifier refuses the run).
int swdb_cert_plan_fault() { return plan_state().read ? plan_state().fault : -1; }

void swdb_cert_record_line(const std::string &line) { emit(line + "\n"); }

void swdb_cert_record_strict(const char *name) {
  std::string line = "strict ";
  for (const char *p = name; p && *p; ++p) line += (*p >= 'a' && *p <= 'z') || *p == '_' ? *p : '?';
  emit(line + " " + std::to_string(swdb_seam_attribution(swdb_strict::thread())) + "\n");
}

void swdb_cert_record_source(int64_t source) { emit("source " + std::to_string((long long)source) + "\n"); }

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

void swdb_cert_record_result_base(const void *base, size_t count) {
  char text[64];
  std::snprintf(text, sizeof text, "result_base %" PRIxPTR " %zu\n", reinterpret_cast<uintptr_t>(base), count);
  emit(text);
}

void swdb_cert_record_end() {
  emit("witness chunks=" + std::to_string((unsigned long long)swdb_dxc::chunks().load()) +
       " operations=" + std::to_string((unsigned long long)swdb_strict::operation_count()) + "\n");
  emit("end\n");
}
