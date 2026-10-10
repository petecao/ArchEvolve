// Native-CPU candidate-process client, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable. The native form of
// library/dx100/certification/v1_5/client.cc.
//
// Linked into the native candidate binary with the candidate object only. The candidate keeps the
// unchanged native 1.4 prelude (../v1_4/prelude.hpp); the swdb_seam_* functions it calls are
// defined here and send each call to the evaluator process (evaluator.cc), where the unchanged
// native 1.4 seams and record writer run. The slide seam's queue bounds live in the candidate's
// queue object, so they travel by value and the evaluator's new bounds are written back here.
#include <cstddef>
#include <cstdint>
#include "../../../dx100/certification/v1_5/client_core.inc"

bool swdb_seam_claim_i32(int32_t *slot_address, int32_t expected, int32_t desired) {
  const int64_t reply = call3(CLAIM, address(slot_address), expected, desired);
  if (reply == 2) return __sync_bool_compare_and_swap(slot_address, expected, desired);   // not in the arena
  return reply == 1;
}
bool swdb_seam_push(const void *queue, int32_t value) { return call2(PUSH, address(queue), value) == 1; }
void swdb_seam_direct_push(const void *queue, int32_t value) { call2(DIRECT_PUSH, address(queue), value); }
void swdb_seam_reset(const void *queue) { call1(RESET, address(queue)); }
void swdb_seam_slide(const void *queue, const int32_t *shared, size_t *out_start, size_t *out_end) {
  Slot &s = begin(NATIVE_SLIDE);
  s.a[0] = address(queue);
  s.a[1] = address(shared);
  s.a[2] = int64_t(*out_start);
  s.a[3] = int64_t(*out_end);
  call(s);
  *out_start = size_t(s.r[0]);
  *out_end = size_t(s.r[1]);
}
void swdb_seam_offsets(const int32_t *window, size_t count, int32_t *offsets, size_t offsets_count) {
  calln(NATIVE_OFFSETS, {address(window), int64_t(count), address(offsets), int64_t(offsets_count)});
}
