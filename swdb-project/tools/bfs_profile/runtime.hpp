// Evaluator-owned diagnostic source-scope accounting. Updated 2026-09-25.
#pragma once
#include <atomic>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <vector>

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
inline uint64_t clock_ns() {
    timespec time;
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &time)) {
        errors.fetch_add(1, std::memory_order_relaxed); return 0;
    }
    return uint64_t(time.tv_sec) * 1000000000ULL + time.tv_nsec;
}
struct Scope {
    bool enabled;
    Scope(size_t id): enabled(active.load(std::memory_order_relaxed)) {
        if (enabled) stack.push_back(Frame{id, clock_ns(), 0});
    }
    ~Scope() {
        if (!enabled) return;
        uint64_t end = clock_ns();
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
inline void write(const char *path) {
    std::ofstream out(path);
    out << "{\"format\":\"swdb.bfs.regions.v1\",\"clock\":\"CLOCK_THREAD_CPUTIME_ID\",\"errors\":"
        << errors.load() << ",\"regions\":[";
    for (size_t i=0; i<SWDB_REGION_COUNT; ++i) {
        if(i) out << ',';
        out << "{\"index\":" << i << ",\"inclusive_ns\":" << counters[i].inclusive.load()
            << ",\"exclusive_ns\":" << counters[i].exclusive.load()
            << ",\"invocations\":" << counters[i].calls.load() << '}';
    }
    out << "]}\n";
    out.close();
    if (!out) throw std::runtime_error("cannot persist region counters");
}
}
