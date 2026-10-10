// Native-CPU certification evaluator process, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable. The native form of
// library/dx100/certification/v1_5/evaluator.cc.
//
// Linked from trusted sources only: this file, the shared core
// (library/dx100/certification/v1_5/evaluator_core.inc) and the unchanged native certify 1.4 record
// writer and seams (../v1_4/record.cc, ../v1_4/seams.cc), all built with evaluator_context.hpp. The
// evaluator holds the record descriptor, the run plan, the fault logic and the frontier ledger; each
// pointer the candidate passes is used only after it is checked to lie in the arena's candidate heap.
#include <cstddef>
#include <cstdint>

// seams.cc (native certify 1.4, unchanged)
bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired);
bool swdb_seam_push(const void *queue, int32_t value);
void swdb_seam_direct_push(const void *queue, int32_t value);
void swdb_seam_slide(const void *queue, const int32_t *shared, size_t *out_start, size_t *out_end);
void swdb_seam_reset(const void *queue);
void swdb_seam_offsets(const int32_t *window, size_t count, int32_t *offsets, size_t offsets_count);

#include "../../../dx100/certification/v1_5/evaluator_core.inc"

namespace {
bool counted(int64_t value) { return value >= 0 && value < (int64_t(1) << 31); }
}

void evaluator_prepare() {}

void evaluator_serve(swdb_arena::Slot &s) {
  const int64_t *a = s.a;
  switch (s.op) {
    case CLAIM: {
      void *slot_address = (a[0] & 3) == 0 ? heap_pointer(a[0], 4) : nullptr;
      s.r[0] = slot_address ? (swdb_seam_claim_i32(static_cast<int32_t *>(slot_address), int32_t(a[1]), int32_t(a[2])) ? 1 : 0) : 2;
      break;
    }
    case PUSH: s.r[0] = swdb_seam_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])) ? 1 : 0; break;
    case DIRECT_PUSH: swdb_seam_direct_push(reinterpret_cast<const void *>(a[0]), int32_t(a[1])); break;
    case RESET: swdb_seam_reset(reinterpret_cast<const void *>(a[0])); break;
    case NATIVE_SLIDE: {
      // The queue's shared array must hold [0, out_end) in the heap; the seam reads the window there.
      size_t start = size_t(a[2]), end = size_t(a[3]);
      if (!counted(a[2]) || !counted(a[3]) || a[2] > a[3] || (a[3] > 0 && !heap_pointer(a[1], uint64_t(a[3]) * 4)))
        fail("a frontier window outside the shared arena", 87);
      swdb_seam_slide(reinterpret_cast<const void *>(a[0]), reinterpret_cast<const int32_t *>(a[1]), &start, &end);
      s.r[0] = int64_t(start);
      s.r[1] = int64_t(end);
      break;
    }
    case NATIVE_OFFSETS: {
      if (!counted(a[1]) || !counted(a[3]) || (a[1] > 0 && !heap_pointer(a[0], uint64_t(a[1]) * 4)) ||
          (a[3] > 0 && !heap_pointer(a[2], uint64_t(a[3]) * 4)))
        fail("row offsets outside the shared arena", 87);
      swdb_seam_offsets(reinterpret_cast<const int32_t *>(a[0]), size_t(a[1]), reinterpret_cast<int32_t *>(a[2]), size_t(a[3]));
      break;
    }
    default: fail("unknown request");
  }
}
