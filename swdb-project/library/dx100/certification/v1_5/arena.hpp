// Shared arena between the certification evaluator and the candidate process, certify 1.5.
// Created: 2026-10-05 ET (ticket 78). Agent-decided under Yan-Ru's delegation; revisable.
//
// Certify 1.5 runs the candidate as a child of a trusted evaluator process (evaluator.cc). The two
// processes share one memory object, mapped at the same virtual address in both:
//
//   [ header | request slots | tile windows | candidate heap ................................ ]
//
// - The candidate's C++ heap (global operator new/delete, replaced by client.cc) lives in the
//   candidate heap part, so every array the DX100 strict model reads or writes (graph, frontier
//   queue, parent array) is visible to the evaluator at the address the candidate passes.
// - Each tile's CPU-visible buffer (what __dxc_tile_pointer returns) is a tile window; the
//   device-side buffers, the registers, the operation graph and every other strict-model state
//   stay in the evaluator's private memory.
// - Each candidate thread owns one request slot. A request is a sequence number, an operation and
//   its operands; the evaluator's server thread for that slot performs the operation in its own
//   process and writes the reply. Every record line is written by the evaluator.
// This header is only layout; it holds no policy.
#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace swdb_arena {

constexpr uint64_t MAGIC = 0x5357444241523135ULL;      // "SWDBAR15"
constexpr uintptr_t ADDRESS = 0x200000000000ULL;       // the same in both processes
constexpr size_t SIZE = size_t(16) << 30;              // virtual; pages are allocated on first touch
constexpr int SLOTS = 64;
constexpr size_t HEADER_BYTES = 64 * 1024;
constexpr size_t SLOT_BYTES = 512;
constexpr size_t TILE_WINDOW_OFFSET = HEADER_BYTES + SLOTS * SLOT_BYTES;   // 96 KiB
constexpr size_t MAX_TILES = 64;                       // NUM_TILES at NUM_CORES <= 8
constexpr size_t MAX_TILE_BYTES = 65535 * 4;           // the DX100 uint16 tile-size field, i32
constexpr size_t HEAP_OFFSET = TILE_WINDOW_OFFSET + MAX_TILES * MAX_TILE_BYTES;
constexpr int SIZE_CLASSES = 40;

// Operations a slot can carry. Seam operations mirror the 1.4 seams (seams.cc), strict-model
// operations the strict layer's interface (strict/MAA_functional.hpp).
enum Op : int32_t {
  SESSION_BEGIN = 1, THREAD_CONTEXT, WAIT, GATHER, STREAM_LOAD, RANGE_LOOP, ALU_SCALAR, CLAIM, PUSH,
  DIRECT_PUSH, SLIDE, RESET, CHUNK,
  ALLOC_MAA = 20, INIT_MAA, CLEAR_REGION, ADD_REGION, NEW_TILE, NEW_REG, CONST, GET_REG, TILE_POINTER,
  TILE_SIZE_OP, TILE_READY, WAIT_READY, SET_TILE_SIZE, SET_TILE_READY, MAA_STREAM_LOAD, MAA_INDIRECT_LOAD,
  MAA_RANGE_LOOP, MAA_ALU_SCALAR, MAA_STORE, STRICT_SESSION_BEGIN, CHECK_FAIL, OPERATION_COUNT,
  FINISH = 60,
};

// Reply codes of CLAIM: 0 not claimed, 1 claimed, 2 the slot is not in the shared arena (the
// client then runs a plain, unrecorded compare-and-swap, as 1.4 does for other widths).
struct alignas(128) Slot {
  std::atomic<uint32_t> request;   // written by the candidate thread
  std::atomic<uint32_t> reply;     // written by the evaluator
  int32_t op, thread, in_parallel, num_threads;
  int64_t a[8];
  int64_t r[2];
  int32_t context[16];
  char text[64];
};
static_assert(sizeof(Slot) <= SLOT_BYTES, "slot layout");

struct Header {
  uint64_t magic;
  uint64_t size;
  int32_t evaluator_pid;
  std::atomic<int32_t> slot_count;
  std::atomic_flag heap_lock;
  uint64_t heap_top;                       // offset of the first never-used heap byte
  uint64_t free_list[SIZE_CLASSES];        // offset of the first free block per size class (0: none)
};
static_assert(sizeof(Header) <= HEADER_BYTES, "header layout");

inline Header *header() { return reinterpret_cast<Header *>(ADDRESS); }
inline Slot *slot(int index) { return reinterpret_cast<Slot *>(ADDRESS + HEADER_BYTES + size_t(index) * SLOT_BYTES); }
inline uint32_t *tile_window(int tile) {
  return reinterpret_cast<uint32_t *>(ADDRESS + TILE_WINDOW_OFFSET + size_t(tile) * MAX_TILE_BYTES);
}
// True when [start, start + bytes) lies in the candidate heap part of the arena.
inline bool in_heap(uintptr_t start, uint64_t bytes) {
  const uintptr_t low = ADDRESS + HEAP_OFFSET, high = ADDRESS + SIZE;
  return start >= low && start <= high && bytes <= high - start;
}

}  // namespace swdb_arena
