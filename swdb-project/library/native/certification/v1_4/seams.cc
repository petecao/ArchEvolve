// Native-CPU certification seams, certify 1.4. Created: 2026-10-05 ET (ticket 75).
// Agent-decided under Yan-Ru's delegation; revisable. The native form of
// library/dx100/certification/v1_4/seams.cc (ticket 76); certify 1.3 keeps ../seams.cc.
//
// One object holds every fault; the run's plan (record.cc) selects one or none. Each fault's
// behavior is the 1.3 native fault's (../seams.cc), unchanged. What is new is evidence: every
// successful claim (address), every push (queue), each window read from the queue at its slide,
// and where a fault acted, so the certifier attributes a control's rejection to the fault:
//
//   fault lost <t> 2 <address> <value>     claim_without_write: this claim's write was undone
//   fault hidden <t> <n> <vertices>        partial_batch_dropped: these window positions are skipped
//   fault stale <t> 3 <u> <begin> <end>    stale_row_offset: u's row bounds became [begin, end)
//
// Epoch events (ticket 76 syntax): c<t>:<address> claim, C<t>:<address> claim whose write the fault
// undid, p<t>:<q>:<v> queue-buffer push, P<t>:<q>:<v> forged copy, d<t>:<q>:<v> direct push,
// r<t>:<q> reset.
#include <algorithm>
#include <atomic>
#include <cinttypes>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <map>
#include <mutex>
#include <string>
#include <vector>
#include <omp.h>

#ifndef SWDB_NATIVE_FAULT_BATCH
#define SWDB_NATIVE_FAULT_BATCH 16
#endif

int swdb_cert_plan_fault();                          // record.cc
void swdb_cert_record_line(const std::string &line);  // record.cc

namespace {
enum Fault { NONE = 0, CLAIM_WITHOUT_WRITE = 1, PARTIAL_BATCH_DROPPED = 2, STALE_ROW_OFFSET = 3, FORGED_FRONTIER = 4 };
int fault() { static const int value = swdb_cert_plan_fault(); return value; }

std::atomic<unsigned long long> &claims() { static std::atomic<unsigned long long> v(0); return v; }
std::atomic<unsigned long long> &pushes() { static std::atomic<unsigned long long> v(0); return v; }
std::atomic<bool> &lost_once() { static std::atomic<bool> v(false); return v; }
std::atomic<bool> &forged_once() { static std::atomic<bool> v(false); return v; }
size_t &hidden_tail() { static size_t v = 0; return v; }
bool &stale_applied() { static bool v = false; return v; }
bool &stale_pending() { static bool v = false; return v; }
int32_t *&stale_base() { static int32_t *v = nullptr; return v; }
size_t &stale_index() { static size_t v = 0; return v; }
int32_t (&stale_saved())[2] { static int32_t v[2] = {0, 0}; return v; }

std::mutex &ledger_lock() { static std::mutex m; return m; }
std::string &events() { static std::string s; return s; }
std::map<const void *, int> &queue_index() { static std::map<const void *, int> m; return m; }

std::string hex(uintptr_t value) { char text[24]; std::snprintf(text, sizeof text, "%" PRIxPTR, value); return text; }
int thread() { return omp_get_thread_num(); }

int queue_of(const void *queue) {   // under ledger_lock
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
}  // namespace

unsigned long long swdb_seam_claims() { return claims().load(); }
unsigned long long swdb_seam_pushes() { return pushes().load(); }

// The CPU claim. claim_without_write: the first successful claim of the run returns true but its
// write is undone, as a claim primitive that compares without writing would behave.
bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired) {
  if (!__sync_bool_compare_and_swap(slot, expected, desired)) return false;
  claims().fetch_add(1);
  const bool lost = fault() == CLAIM_WITHOUT_WRITE && !lost_once().exchange(true);
  if (lost) {
    __atomic_store_n(slot, expected, __ATOMIC_SEQ_CST);
    swdb_cert_record_line("fault lost " + std::to_string(thread()) + " 2 " +
                          std::to_string((unsigned long long)reinterpret_cast<uintptr_t>(slot)) + " " +
                          std::to_string(desired));
  }
  event(std::string(lost ? "C" : "c") + std::to_string(thread()) + ":" + hex(reinterpret_cast<uintptr_t>(slot)));
  return true;
}

// The queue push. forged_frontier: the first queue-buffer push of the run is pushed twice.
bool swdb_seam_push(const void *queue, int32_t value) {
  pushes().fetch_add(1);
  const bool twice = fault() == FORGED_FRONTIER && !forged_once().exchange(true);
  const std::string t = std::to_string(thread());
  std::lock_guard<std::mutex> guard(ledger_lock());
  const std::string tail = std::to_string(queue_of(queue)) + ":" + std::to_string(value) + " ";
  events() += "p" + t + ":" + tail;
  if (twice) events() += "P" + t + ":" + tail;
  return twice;
}

void swdb_seam_direct_push(const void *queue, int32_t value) {
  std::lock_guard<std::mutex> guard(ledger_lock());
  events() += "d" + std::to_string(thread()) + ":" + std::to_string(queue_of(queue)) + ":" + std::to_string(value) + " ";
}

void swdb_seam_reset(const void *queue) {
  std::lock_guard<std::mutex> guard(ledger_lock());
  events() += "r" + std::to_string(thread()) + ":" + std::to_string(queue_of(queue)) + " ";
}

// A slide. partial_batch_dropped: in every step whose window holds more than BATCH positions, the
// trailing (size mod BATCH) positions are never expanded; they are cut from the window the step is
// handed and skipped at the next slide. The recorded window is the slide's (before the cut).
void swdb_seam_slide(const void *queue, const int32_t *shared, size_t *out_start, size_t *out_end) {
  if (fault() == PARTIAL_BATCH_DROPPED && hidden_tail()) {
    *out_start += hidden_tail();
    hidden_tail() = 0;
  }
  const int32_t *window = shared + *out_start;
  const size_t count = *out_end - *out_start;
  std::string epoch;
  int index;
  {
    std::lock_guard<std::mutex> guard(ledger_lock());
    index = queue_of(queue);
    std::string text = events();
    events().clear();
    if (!text.empty() && text.back() == ' ') text.pop_back();
    size_t n = 0;
    for (char ch : text) n += ch == ' ';
    epoch = "epoch " + std::to_string(index) + " " + std::to_string(text.empty() ? 0 : n + 1) +
            (text.empty() ? "" : " ") + text;
  }
  swdb_cert_record_line(epoch);
  std::string line = "window " + std::to_string(index) + " " + std::to_string(count);
  for (size_t i = 0; i < count; ++i) line += " " + std::to_string(window[i]);
  swdb_cert_record_line(line);
  std::vector<int32_t> sorted(window, window + count);
  std::sort(sorted.begin(), sorted.end());
  if (std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end()) std::_Exit(88);
  if (fault() == PARTIAL_BATCH_DROPPED) {
    const size_t batch = size_t(SWDB_NATIVE_FAULT_BATCH);
    const size_t tail = count > batch ? count % batch : 0;
    if (tail) {
      std::string hidden = "fault hidden " + std::to_string(thread()) + " " + std::to_string(tail);
      for (size_t i = count - tail; i < count; ++i) hidden += " " + std::to_string(window[i]);
      swdb_cert_record_line(hidden);
      *out_end -= tail;
      hidden_tail() = tail;
    }
  }
}

// The row offsets, before each step. stale_row_offset: in the first step the first window vertex u
// is expanded over vertex u + 1's row; the bounds are restored before the next step.
void swdb_seam_offsets(const int32_t *window, size_t count, int32_t *offsets, size_t offsets_count) {
  if (fault() != STALE_ROW_OFFSET) return;
  if (stale_pending()) {
    stale_base()[stale_index()] = stale_saved()[0];
    stale_base()[stale_index() + 1] = stale_saved()[1];
    stale_pending() = false;
  }
  if (stale_applied() || count == 0) return;
  stale_applied() = true;
  const int32_t u = window[0];
  if (u < 0 || size_t(u) + 2 >= offsets_count) return;
  const int32_t begin = offsets[u + 1], end = offsets[u + 2];
  stale_base() = offsets;
  stale_index() = size_t(u);
  stale_saved()[0] = offsets[u];
  stale_saved()[1] = offsets[u + 1];
  offsets[u] = begin;
  offsets[u + 1] = end;
  stale_pending() = true;
  swdb_cert_record_line("fault stale " + std::to_string(thread()) + " 3 " + std::to_string(u) + " " +
                        std::to_string(begin) + " " + std::to_string(end));
}
