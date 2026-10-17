// DX100 certification seams, certify 1.4. Created: 2026-10-05 ET (ticket 76).
// Agent-decided under Yan-Ru's delegation; revisable. Certify 1.3 keeps ../seams.cc.
//
// One object holds every fault. `swdb certify` compiles it once per tile size, with no fault
// macro, and links the same binary for the positive matrix and every library-fault control. The
// fault of a run comes from its plan (record.cc), which the candidate cannot see without reading
// trusted memory. Each fault's behavior is the 1.3 fault's (tickets 62 and 67), unchanged.
//
// What is new is evidence. The seams record, for the certifier's out-of-process judge:
//   - every successful CPU claim (4-byte compare_and_swap) with its address, a forged claim
//     (skipped_cas_recheck) marked as forged;
//   - every queue push with its queue, a forged copy (forged_frontier) marked as forged;
//   - every DX100 gather's base address (counted per epoch);
//   - each window of each queue, read from the queue at the slide that creates it;
//   - where a fault acted: the thread that received a forged context, had a wait dropped or
//     skipped, or ran a stream load the fault modified, and the edge offsets a dropped
//     continuation removed.
// The judge accepts a control's rejection only when the check that fired is attributable to the
// fault's own action on the candidate's data (see swdb/certification_blinding.py).
//
// Epoch events, in one global order between two slides (t is the OpenMP thread, q a queue index):
//   c<t>:<address>   successful claim          C<t>:<address>   forged claim
//   p<t>:<q>:<v>     queue-buffer push         P<t>:<q>:<v>     forged copy of the push before it
//   d<t>:<q>:<v>     direct SlidingQueue push  r<t>:<q>         SlidingQueue reset
//   g:<base>:<n>     n gathers from base (aggregated per epoch, after the ordered events)
#include <algorithm>
#include <atomic>
#include <cinttypes>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <mutex>
#include <string>
#include <vector>
#include "dxc_lowering.hpp"
#ifndef SWDB_STRICT
#error "DX100 certification seams require the strict functional layer"
#endif

int swdb_cert_plan_fault();                          // record.cc
void swdb_cert_record_line(const std::string &line);  // record.cc

namespace {
enum Fault { NONE = 0, SHARED_CONTEXT = 1, SKIPPED_CAS_RECHECK = 2, DROPPED_CONTINUATION = 3, CHUNK_OFF_BY_ONE = 4,
             DROPPED_WAIT = 5, READ_BEFORE_WAIT = 6, INDEX_WRAP = 7, FORGED_FRONTIER_V2 = 8 };
int fault() { static const int value = swdb_cert_plan_fault(); return value; }

std::atomic<bool> &context_made() { static std::atomic<bool> v(false); return v; }
dxc_context &first_context() { static dxc_context c; return c; }
int &context_owner() { static int t = -1; return t; }
std::atomic<bool> &forged_once() { static std::atomic<bool> v(false); return v; }   // never reset (v2)
std::atomic<unsigned> &skipped_rechecks() { static std::atomic<unsigned> v(0); return v; }
unsigned &range_calls(int thread) { static unsigned v[256]; return v[thread & 255]; }
bool &gathered(int tile) { static bool v[NUM_TILES]; return v[tile >= 0 && tile < NUM_TILES ? tile : 0]; }
std::atomic<int> &tainted(int thread) { static std::atomic<int> v[256]; return v[thread & 255]; }
std::atomic<int> &in_fault_call(int thread) { static std::atomic<int> v[256]; return v[thread & 255]; }
std::atomic<int> &noted(int kind, int thread) { static std::atomic<int> v[4][256]; return v[kind & 3][thread & 255]; }

std::mutex &ledger_lock() { static std::mutex m; return m; }
std::string &events() { static std::string s; return s; }
std::map<uintptr_t, unsigned long long> &gather_counts() { static std::map<uintptr_t, unsigned long long> m; return m; }
std::map<const void *, int> &queue_index() { static std::map<const void *, int> m; return m; }

std::string hex(uintptr_t value) { char text[24]; std::snprintf(text, sizeof text, "%" PRIxPTR, value); return text; }

// Under ledger_lock: the queue's small index, announced once with its address.
int queue_of(const void *queue) {
  auto found = queue_index().find(queue);
  if (found != queue_index().end()) return found->second;
  const int index = int(queue_index().size());
  queue_index()[queue] = index;
  swdb_cert_record_line("queue " + std::to_string(index) + " " + hex(reinterpret_cast<uintptr_t>(queue)));
  return index;
}

void event(const std::string &text) {
  std::lock_guard<std::mutex> guard(ledger_lock());
  events() += text;
  events() += ' ';
}

// A fault acted on this thread: its later strict failures are attributable (record once per kind).
void taint(int thread, int kind, const char *what) {
  tainted(thread) = 1;
  if (!noted(kind, thread).exchange(1)) swdb_cert_record_line(std::string("fault ") + what + " " + std::to_string(thread));
}
}  // namespace

// 2 inside a seam call the fault modified, 1 on a thread the fault acted on, 0 otherwise.
int swdb_seam_attribution(int thread) {
  if (fault() <= NONE) return 0;
  if (in_fault_call(thread).load()) return 2;
  return tainted(thread).load() ? 1 : 0;
}

void swdb_seam_session_begin() {
  __dxc_session_begin();
  context_made() = false; context_owner() = -1; skipped_rechecks() = 0;
  for (int t = 0; t < 256; ++t) range_calls(t) = 0;
  for (int t = 0; t < NUM_TILES; ++t) gathered(t) = false;
}

// shared_context: every thread receives the first context allocated in the session.
dxc_context swdb_seam_thread_context() {
  if (fault() != SHARED_CONTEXT) return __dxc_thread_context();
  dxc_context c;
  bool forged = false;
  const int thread = swdb_strict::thread();
#pragma omp critical(swdb_fault_context)
  {
    if (!context_made()) { first_context() = __dxc_thread_context(); context_made() = true; context_owner() = thread; }
    c = first_context();
    forged = context_owner() != thread;
  }
  if (forged) taint(thread, 0, "context");
  return c;
}

// dropped_wait: no wait completes. read_before_wait: waits on gather results are skipped.
void swdb_seam_wait(int tile) {
  if (fault() == DROPPED_WAIT) { taint(swdb_strict::thread(), 1, "wait"); return; }
  if (fault() == READ_BEFORE_WAIT && gathered(tile)) { taint(swdb_strict::thread(), 1, "wait"); return; }
  __dxc_wait(tile);
}

void swdb_seam_gather_i32(void *base, int index, int dst) {
  {
    std::lock_guard<std::mutex> guard(ledger_lock());
    ++gather_counts()[reinterpret_cast<uintptr_t>(base)];
  }
  __dxc_gather(static_cast<int32_t *>(base), index, dst);
  gathered(dst) = true;
}

// index_wrap: the stream's start register wraps to INT32_MAX before the load.
// chunk_off_by_one: a stream that fills the tile exactly requests one more element.
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst) {
  const int thread = swdb_strict::thread();
  bool modified = false;
  {
    std::lock_guard<std::mutex> guard(swdb_strict::state().lock);
    if (fault() == INDEX_WRAP) {
      swdb_strict::reg(minimum).value = uint32_t(INT32_MAX);
      modified = true;
    } else if (fault() == CHUNK_OFF_BY_ONE) {
      const int64_t lo = swdb_strict::rval(minimum), hi = swdb_strict::rval(maximum), step = swdb_strict::rval(stride);
      if (step > 0 && hi >= lo && (hi - lo + step - 1) / step == int64_t(TILE_SIZE)) {
        swdb_strict::reg(maximum).value = uint32_t(hi + step);
        modified = true;
      }
    }
    range_calls(thread) = 0;
  }
  if (modified) {
    in_fault_call(thread) = 1;
    if (!noted(2, thread).exchange(1)) swdb_cert_record_line("fault stream " + std::to_string(thread));
  }
  __dxc_stream_load(static_cast<int32_t *>(base), minimum, maximum, stride, dst);
  if (modified) in_fault_call(thread) = 0;
  gathered(dst) = false;
}

// dropped_continuation: after the first range loop of a stream, the loop state is forced to its
// end, so every continuation tile comes back empty. The seam records the edge offsets (column
// values) the unmodified loop would still have produced for that stream.
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  if (fault() == DROPPED_CONTINUATION) {
    const int thread = swdb_strict::thread();
    bool fired = false;
    std::vector<int32_t> lost;
    {
      std::lock_guard<std::mutex> guard(swdb_strict::state().lock);
      if (range_calls(thread)++ > 0) {
        fired = true;
        int64_t i = swdb_strict::rval(last_i), j = swdb_strict::rval(last_j);
        const int64_t step = swdb_strict::rval(stride);
        const size_t n = swdb_strict::tile(lower).size;
        if (step > 0 && i >= 0 && uint64_t(i) <= n && n == swdb_strict::tile(upper).size) {
          const int *starts = swdb_strict::data<int>(lower), *ends = swdb_strict::data<int>(upper);
          while (uint64_t(i) < n && lost.size() < (size_t(1) << 22)) {
            const int64_t start = starts[i], end = ends[i];
            if (start < 0 || end < start) break;
            const int64_t next = j < start ? start : j + step;
            if (next >= end) { ++i; j = -1; continue; }
            j = next;
            lost.push_back(int32_t(j));
          }
        }
        swdb_strict::reg(last_i).value = uint32_t(swdb_strict::tile(lower).size);
      }
    }
    if (fired) {
      tainted(thread) = 1;
      if (!lost.empty()) {
        std::string line = "fault continuation " + std::to_string(thread) + " " + std::to_string(lost.size());
        for (int32_t value : lost) line += " " + std::to_string(value);
        swdb_cert_record_line(line);
      }
    }
  }
  __dxc_range_loop(last_i, last_j, lower, upper, stride, rows, columns);
  gathered(rows) = false;
  gathered(columns) = false;
}

void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op) {
  __dxc_alu_scalar(src, reg, dst, op);
  gathered(dst) = false;
}

// The CPU claim. skipped_cas_recheck: a claim whose compare fails succeeds anyway (at most eight
// per session), as if the CPU skipped the recheck of a stale DX100 hint.
bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired) {
  bool claimed = __sync_bool_compare_and_swap(slot, expected, desired);
  bool forged = false;
  if (!claimed && fault() == SKIPPED_CAS_RECHECK && skipped_rechecks().fetch_add(1) < 8) {
    __atomic_store_n(slot, desired, __ATOMIC_SEQ_CST);
    claimed = forged = true;
  }
  if (claimed)
    event(std::string(forged ? "C" : "c") + std::to_string(swdb_strict::thread()) + ":" +
          hex(reinterpret_cast<uintptr_t>(slot)));
  return claimed;
}

// The queue push. forged_frontier, version 2 (ticket 67): the first queue-buffer push of the run
// is pushed twice; the copy is recorded as forged.
bool swdb_seam_push(const void *queue, int32_t value) {
  const bool twice = fault() == FORGED_FRONTIER_V2 && !forged_once().exchange(true);
  const std::string thread = std::to_string(swdb_strict::thread());
  std::lock_guard<std::mutex> guard(ledger_lock());
  const std::string tail = std::to_string(queue_of(queue)) + ":" + std::to_string(value) + " ";
  events() += "p" + thread + ":" + tail;
  if (twice) events() += "P" + thread + ":" + tail;
  return twice;
}

void swdb_seam_direct_push(const void *queue, int32_t value) {
  std::lock_guard<std::mutex> guard(ledger_lock());
  events() += "d" + std::to_string(swdb_strict::thread()) + ":" + std::to_string(queue_of(queue)) + ":" +
              std::to_string(value) + " ";
}

void swdb_seam_reset(const void *queue) {
  std::lock_guard<std::mutex> guard(ledger_lock());
  events() += "r" + std::to_string(swdb_strict::thread()) + ":" + std::to_string(queue_of(queue)) + " ";
}

// A slide: the epoch's events and the queue's new window, read from the queue itself. A window
// that repeats a value is recorded, then the run stops (exit 88), as in certify 1.0-1.3.
void swdb_seam_slide(const void *queue, const int32_t *window, size_t count) {
  std::string epoch, line;
  int index;
  {
    std::lock_guard<std::mutex> guard(ledger_lock());
    index = queue_of(queue);
    std::string text = events();
    for (const auto &entry : gather_counts()) text += "g:" + hex(entry.first) + ":" + std::to_string(entry.second) + " ";
    events().clear();
    gather_counts().clear();
    if (!text.empty() && text.back() == ' ') text.pop_back();
    size_t n = 0;
    for (char ch : text) n += ch == ' ';
    epoch = "epoch " + std::to_string(index) + " " + std::to_string(text.empty() ? 0 : n + 1) + (text.empty() ? "" : " ") + text;
  }
  swdb_cert_record_line(epoch);
  line = "window " + std::to_string(index) + " " + std::to_string(count);
  std::vector<int32_t> sorted(window, window + count);
  for (size_t i = 0; i < count; ++i) line += " " + std::to_string(window[i]);
  swdb_cert_record_line(line);
  std::sort(sorted.begin(), sorted.end());
  if (std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end()) std::_Exit(88);
}
