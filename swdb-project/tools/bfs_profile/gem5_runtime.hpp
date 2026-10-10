// Evaluator-owned source-scope diagnostic. Updated 2026-09-25.
#pragma once
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <vector>

// m5_rpns returns simulated nanoseconds. These are elapsed intervals summed
// over executing threads, including waits; they are not CPU service time.
namespace swdb_profile {
static std::atomic<bool> active(false);
static std::atomic<uint64_t> errors(0);
struct Counter {
  std::atomic<uint64_t> inclusive, exclusive, calls;
  Counter(): inclusive(0), exclusive(0), calls(0) {}
};
static Counter counters[SWDB_REGION_COUNT];
struct Frame { size_t id; uint64_t start, child; };
static thread_local std::vector<Frame> stack;
struct Scope {
  bool enabled;
  Scope(size_t id): enabled(active.load(std::memory_order_relaxed)) {
    if (enabled) stack.push_back(Frame{id, m5_rpns(), 0});
  }
  ~Scope() {
    if (!enabled) return;
    uint64_t end = m5_rpns();
    if (stack.empty()) { errors.fetch_add(1); return; }
    Frame frame = stack.back(); stack.pop_back();
    if (end < frame.start || end-frame.start < frame.child) { errors.fetch_add(1); return; }
    uint64_t elapsed = end-frame.start;
    counters[frame.id].inclusive.fetch_add(elapsed, std::memory_order_relaxed);
    counters[frame.id].exclusive.fetch_add(elapsed-frame.child, std::memory_order_relaxed);
    counters[frame.id].calls.fetch_add(1, std::memory_order_relaxed);
    if (!stack.empty()) stack.back().child += elapsed;
  }
};
inline void start() { active.store(true); }
inline void stop() { active.store(false); }
inline void write() {
  std::printf("SWDB_DX100_REGIONS {\"format\":\"swdb.dx100.regions.v1\",\"clock\":\"m5_rpns\",\"errors\":%llu,\"regions\":[",
      static_cast<unsigned long long>(errors.load()));
  for (size_t i=0; i<SWDB_REGION_COUNT; ++i) {
    std::printf("%s{\"index\":%llu,\"inclusive_ns\":%llu,\"exclusive_ns\":%llu,\"invocations\":%llu}",
        i ? "," : "", static_cast<unsigned long long>(i),
        static_cast<unsigned long long>(counters[i].inclusive.load()),
        static_cast<unsigned long long>(counters[i].exclusive.load()),
        static_cast<unsigned long long>(counters[i].calls.load()));
  }
  std::puts("]}");
  std::fflush(stdout);
}
}
