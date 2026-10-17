// Record channel and run plan of library-operation certification 1.1. Created: 2026-10-05 ET
// (ticket 77). Original SWDB code. Agent-decided under Yan-Ru's delegation; revisable.
//
// Every run (reference, positive, driver-fault control, mutation control) gets two descriptors
// from the harness, named by SWDB_LO_RECORD_FD (the write end of a pipe the harness reads) and
// SWDB_LO_PLAN_FD (the read end of a pipe holding one fixed-length plan line). This object is
// linked first, so its initializer runs before any initializer of the candidate's object: it reads
// both numbers once, drains and closes the plan pipe, and removes both variables. A positive run's
// plan has the same length as a control's. The plan names the driver fault (or none), a seed that
// places it, and a nonce echoed into the record.
//
// Records (raw data; the certifier computes every check out of process):
//   begin 1
//   plan <nonce>
//   fault input_write <array> <byte>     the trusted driver flipped one input bit after the call
//   fault output_perturb <element>       the trusted driver flipped one output bit after the call
//   frame ok | frame violation <array> <first byte> <bytes changed>   (one line per changed array)
//   result <bytes> <hex>                 the output buffer after the call
//   end
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <fcntl.h>
#include <unistd.h>

namespace {
struct Plan { int fault = -1; unsigned long long seed = 0; char nonce[33] = {0}; bool read = false; };

int parse_fd(const char *name) {
  const char *value = std::getenv(name);
  if (!value) return -1;
  char *end = nullptr;
  const long fd = std::strtol(value, &end, 10);
  ::unsetenv(name);
  if (!end || *end != '\0' || fd <= 2 || fd >= 65536 || ::fcntl(int(fd), F_GETFD) == -1) return -1;
  return int(fd);
}

int &channel() { static int fd = parse_fd("SWDB_LO_RECORD_FD"); return fd; }

void write_all(const std::string &line) {
  const char *data = line.data();
  size_t left = line.size();
  while (left && channel() >= 0) {
    const ssize_t wrote = ::write(channel(), data, left);
    if (wrote < 0 && errno == EINTR) continue;
    if (wrote <= 0) { channel() = -1; return; }  // a lost channel fails closed: no `end` is recorded
    data += wrote;
    left -= size_t(wrote);
  }
}

// The plan line: "plan 1 <fault, 2 digits> <seed, 16 hex> <nonce, 32 hex>\n" (60 bytes).
Plan read_plan() {
  Plan plan;
  const int fd = parse_fd("SWDB_LO_PLAN_FD");
  if (fd < 0) return plan;
  char buffer[96] = {0};
  size_t got = 0;
  while (got < sizeof buffer - 1) {
    const ssize_t n = ::read(fd, buffer + got, sizeof buffer - 1 - got);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) break;
    got += size_t(n);
  }
  ::close(fd);
  int fault = -1;
  unsigned long long seed = 0;
  char nonce[33] = {0};
  if (got == 60 && std::sscanf(buffer, "plan 1 %2d %16llx %32[0-9a-f]", &fault, &seed, nonce) == 3 &&
      std::strlen(nonce) == 32 && fault >= 0 && fault < 16) {
    plan.fault = fault;
    plan.seed = seed;
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
    if (channel() < 0) return;
    write_all("begin 1\n");
    if (plan.read) write_all(std::string("plan ") + plan.nonce + "\n");
  }
};
Opening &opening() { static Opening value; return value; }

__attribute__((constructor)) void swdb_lo_open_channel() { opening(); }
}  // namespace

// The driver fault of this run's plan: 0 none; -1 no valid plan (no fault is applied and the record
// has no plan line, so the certifier refuses the run).
int swdb_lo_plan_fault() { return plan_state().read ? plan_state().fault : -1; }
unsigned long long swdb_lo_plan_seed() { return plan_state().seed; }

void swdb_lo_record(const std::string &line) {
  opening();
  write_all(line + "\n");
}
