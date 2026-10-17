// Certification evaluator process, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// The evaluator is linked from trusted sources only: this file, the unchanged certify 1.4 record
// writer and seams (../v1_4/record.cc, ../v1_4/seams.cc) and the unchanged strict layer
// (strict/MAA_functional.hpp), all built with evaluator_context.hpp. It owns everything a verdict
// depends on: the record descriptor and the run plan (record.cc reads both before main), the fault
// logic and the frontier ledger (seams.cc), the strict model's state (device tiles, registers,
// operation graph, registered regions) and the witness counters.
//
// The process plumbing (arena, child process, request slots, FINISH, exit status) is the shared
// core, evaluator_core.inc. This file serves the DX100 requests.
#include <cstdint>
#include <cstring>
#include <mutex>
#include "dxc_lowering.hpp"
#include "arena.hpp"

static_assert(NUM_TILES <= int(swdb_arena::MAX_TILES), "tile windows");
static_assert(size_t(TILE_SIZE) * 4 <= swdb_arena::MAX_TILE_BYTES, "tile window size");

// seams.cc (certify 1.4, unchanged)
void swdb_seam_session_begin();
dxc_context swdb_seam_thread_context();
void swdb_seam_wait(int tile);
void swdb_seam_gather_i32(void *base, int index, int dst);
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst);
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns);
void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op);
bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired);
bool swdb_seam_push(const void *queue, int32_t value);
void swdb_seam_direct_push(const void *queue, int32_t value);
void swdb_seam_slide(const void *queue, const int32_t *window, size_t count);
void swdb_seam_reset(const void *queue);

#include "evaluator_core.inc"

namespace {
// ---- the strict model's CPU-visible tiles, mirrored into the arena's tile windows ----
// The model is unchanged; the evaluator keeps each window equal to the model's CPU buffer. A
// window is rewritten when its tile's producer, that producer's coverage, or the buffer changes
// (operation issue, wait coverage, reset); before set_tile_size, which reads the CPU buffer, the
// window (what the candidate wrote) is copied into the model.
struct Mark { size_t writer; bool covered; const uint32_t *cpu; };

void take(Mark *marks) {
  swdb_strict::State &s = swdb_strict::state();
  for (int t = 0; t < NUM_TILES; ++t) {
    const swdb_strict::Tile &tile = s.tiles[t];
    marks[t] = {tile.writer, tile.writer < s.ops.size() && s.ops[tile.writer].covered, tile.cpu.data()};
  }
}

void publish(const Mark *marks) {
  swdb_strict::State &s = swdb_strict::state();
  for (int t = 0; t < NUM_TILES && t < int(s.tiles.size()); ++t) {
    const swdb_strict::Tile &tile = s.tiles[t];
    const bool covered = tile.writer < s.ops.size() && s.ops[tile.writer].covered;
    if (marks && marks[t].writer == tile.writer && marks[t].covered == covered && marks[t].cpu == tile.cpu.data()) continue;
    std::memcpy(tile_window(t), tile.cpu.data(), size_t(TILE_SIZE) * 4);
  }
}

void pull(int id) {
  swdb_strict::State &s = swdb_strict::state();
  if (id >= 0 && id < int(s.tiles.size())) std::memcpy(s.tiles[id].cpu.data(), tile_window(id), size_t(TILE_SIZE) * 4);
}

// A model operation: serialized, with the tile windows brought up to date afterwards.
template <class F> int64_t model(F body) {
  std::lock_guard<std::mutex> guard(model_lock());
  Mark marks[NUM_TILES];
  take(marks);
  const int64_t value = body();
  publish(marks);
  return value;
}

// A region the strict model may read or write must lie in the candidate heap: the evaluator reads
// candidate memory only through the arena. A region outside it is refused by the strict layer's
// registration check.
void add_region(int64_t start, int64_t end) {
  if (uintptr_t(end) >= uintptr_t(start) && !in_heap(uintptr_t(start), uint64_t(end - start)))
    swdb_strict::check(false, "memory_region_registration");
  add_mem_region(reinterpret_cast<void *>(start), reinterpret_cast<void *>(end));
}

void serve(Slot &s) {
  const int64_t *a = s.a;
  int64_t r = 0;
  switch (s.op) {
    // the 1.4 seams
    case SESSION_BEGIN: model([] { swdb_seam_session_begin(); return int64_t(0); }); break;
    case THREAD_CONTEXT: {
      dxc_context c;
      model([&] { c = swdb_seam_thread_context(); return int64_t(0); });
      for (int i = 0; i < 8; ++i) { s.context[i] = c.tile[i]; s.context[8 + i] = c.reg[i]; }
      break;
    }
    case WAIT: model([&] { swdb_seam_wait(int(a[0])); return int64_t(0); }); break;
    case GATHER: model([&] { swdb_seam_gather_i32(reinterpret_cast<void *>(a[0]), int(a[1]), int(a[2])); return int64_t(0); }); break;
    case STREAM_LOAD:
      model([&] { swdb_seam_stream_load_i32(reinterpret_cast<void *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4])); return int64_t(0); });
      break;
    case RANGE_LOOP:
      model([&] { swdb_seam_range_loop(int(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6])); return int64_t(0); });
      break;
    case ALU_SCALAR:
      model([&] { swdb_seam_alu_scalar(int(a[0]), int(a[1]), int(a[2]), Operation_t(a[3])); return int64_t(0); });
      break;
    case CLAIM: {
      void *slot_address = (a[0] & 3) == 0 ? heap_pointer(a[0], 4) : nullptr;
      r = slot_address ? (swdb_seam_claim_i32(static_cast<int32_t *>(slot_address), int32_t(a[1]), int32_t(a[2])) ? 1 : 0) : 2;
      break;
    }
    case PUSH: r = swdb_seam_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])) ? 1 : 0; break;
    case DIRECT_PUSH: swdb_seam_direct_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])); break;
    case SLIDE: {
      const int64_t count = a[2];
      const void *window = count >= 0 && count < (int64_t(1) << 31) ? heap_pointer(a[1], uint64_t(count) * 4) : nullptr;
      if (!window && count > 0) fail("a frontier window outside the shared arena", 87);
      swdb_seam_slide(reinterpret_cast<const void *>(a[0]), static_cast<const int32_t *>(window), size_t(count));
      break;
    }
    case RESET: swdb_seam_reset(reinterpret_cast<const void *>(a[0])); break;
    case CHUNK: model([] { __dxc_accelerated_chunk(); return int64_t(0); }); break;
    // the strict layer's interface
    case ALLOC_MAA: model([] { alloc_MAA(); return int64_t(0); }); break;
    case INIT_MAA: model([] { init_MAA(); return int64_t(0); }); break;
    case CLEAR_REGION: model([] { clear_mem_region(); return int64_t(0); }); break;
    case ADD_REGION: model([&] { add_region(a[0], a[1]); return int64_t(0); }); break;
    case NEW_TILE: r = model([] { return int64_t(get_new_tile<int>()); }); break;
    case NEW_REG: r = model([] { return int64_t(get_new_reg<int>()); }); break;
    case CONST: model([&] { maa_const<int>(int(a[0]), int(a[1])); return int64_t(0); }); break;
    case GET_REG: r = model([&] { return int64_t(get_reg<int>(int(a[0]))); }); break;
    case TILE_POINTER:
      r = model([&] { (void)get_cacheable_tile_pointer<int>(int(a[0])); return int64_t(reinterpret_cast<uintptr_t>(tile_window(int(a[0])))); });
      break;
    case TILE_SIZE_OP: r = model([&] { return int64_t(get_tile_size(int(a[0]))); }); break;
    case TILE_READY: r = model([&] { return int64_t(get_tile_ready(int(a[0]))); }); break;
    case WAIT_READY: model([&] { wait_ready(int(a[0])); return int64_t(0); }); break;
    case SET_TILE_SIZE: model([&] { pull(int(a[0])); set_tile_size(int(a[0]), uint16_t(a[1])); return int64_t(0); }); break;
    case SET_TILE_READY: model([&] { set_tile_ready(int(a[0]), uint16_t(a[1])); return int64_t(0); }); break;
    case MAA_STREAM_LOAD:
      model([&] { maa_stream_load<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5])); return int64_t(0); });
      break;
    case MAA_INDIRECT_LOAD:
      model([&] { maa_indirect_load<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3])); return int64_t(0); });
      break;
    case MAA_RANGE_LOOP:
      model([&] { maa_range_loop<int>(int(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]), int(a[7])); return int64_t(0); });
      break;
    case MAA_ALU_SCALAR:
      model([&] { maa_alu_scalar<int>(int(a[0]), int(a[1]), int(a[2]), Operation_t(a[3]), int(a[4])); return int64_t(0); });
      break;
    case MAA_STORE:
      model([&] { maa_indirect_store_vector<int>(reinterpret_cast<int *>(a[0]), int(a[1]), int(a[2]), int(a[3]), int(a[4])); return int64_t(0); });
      break;
    case STRICT_SESSION_BEGIN: model([] { swdb_strict::session_begin(); return int64_t(0); }); break;
    case CHECK_FAIL: {
      char name[sizeof s.text];
      std::memcpy(name, s.text, sizeof name);
      name[sizeof name - 1] = '\0';
      model([&] { swdb_strict::check(false, name); return int64_t(0); });
      break;
    }
    case OPERATION_COUNT: r = model([] { return int64_t(swdb_strict::operation_count()); }); break;
    default: fail("unknown request");
  }
  s.r[0] = r;
}

}  // namespace

void evaluator_serve(swdb_arena::Slot &s) { serve(s); }

void evaluator_prepare() {
  std::lock_guard<std::mutex> guard(model_lock());
  publish(nullptr);
}
