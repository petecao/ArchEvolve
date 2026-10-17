// Candidate-process client of the certification evaluator, certify 1.5. Created: 2026-10-05 ET
// (ticket 78). Agent-decided under Yan-Ru's delegation; revisable.
//
// Linked into the candidate binary (the candidate object, this object, nothing else). It holds no
// record channel, no run plan, no fault and no strict-model state; it only
//   - maps the shared arena the evaluator created (descriptor SWDB_ARENA_FD, closed after mapping);
//   - replaces global operator new/delete so the candidate's C++ heap lives in the arena;
//   - sends each seam call (1.4 prelude) and each strict-layer call (client/MAA_functional.hpp) to
//     the evaluator on the calling thread's request slot and waits for the reply;
//   - sends the protected entry point's returned vector's location (driver, FINISH);
//   - exits if the evaluator is gone (parent changed), so no candidate process outlives a run.
// Every record is written by the evaluator from its own state; nothing here writes a record.
#include <cstdint>
#include <cstring>
#include "dxc_lowering.hpp"
#include "client_core.inc"

// ---- the 1.4 seams (declared by ../v1_4/prelude.hpp), served by the evaluator ----
void swdb_seam_session_begin() { call0(SESSION_BEGIN); }
dxc_context swdb_seam_thread_context() {
  Slot &s = begin(THREAD_CONTEXT);
  call(s);
  dxc_context c;
  for (int i = 0; i < 8; ++i) { c.tile[i] = s.context[i]; c.reg[i] = s.context[8 + i]; }
  return c;
}
void swdb_seam_wait(int tile) { call1(WAIT, tile); }
void swdb_seam_gather_i32(void *base, int index, int dst) { call3(GATHER, address(base), index, dst); }
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst) {
  calln(STREAM_LOAD, {address(base), minimum, maximum, stride, dst});
}
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  calln(RANGE_LOOP, {last_i, last_j, lower, upper, stride, rows, columns});
}
void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op) { calln(ALU_SCALAR, {src, reg, dst, int64_t(op)}); }
bool swdb_seam_claim_i32(int32_t *slot_address, int32_t expected, int32_t desired) {
  const int64_t reply = call3(CLAIM, address(slot_address), expected, desired);
  if (reply == 2) return __sync_bool_compare_and_swap(slot_address, expected, desired);   // not in the arena
  return reply == 1;
}
bool swdb_seam_push(const void *queue, int32_t value) { return call2(PUSH, address(queue), value) == 1; }
void swdb_seam_direct_push(const void *queue, int32_t value) { call2(DIRECT_PUSH, address(queue), value); }
void swdb_seam_slide(const void *queue, const int32_t *window, size_t count) {
  call3(SLIDE, address(queue), address(window), int64_t(count));
}
void swdb_seam_reset(const void *queue) { call1(RESET, address(queue)); }
void swdb_seam_accelerated_chunk() { call0(CHUNK); }

// ---- the strict layer's interface (client/MAA_functional.hpp), served by the evaluator ----
void swdb_client_check_fail(const char *name) {
  Slot &s = begin(CHECK_FAIL);
  std::strncpy(s.text, name ? name : "", sizeof s.text - 1);
  s.text[sizeof s.text - 1] = '\0';
  call(s);
  ::_exit(86);   // not reached: the evaluator records the check and ends the run
}
void swdb_client_strict_session_begin() { call0(STRICT_SESSION_BEGIN); }
uint64_t swdb_client_operation_count() { return uint64_t(call0(OPERATION_COUNT)); }
void swdb_client_alloc_MAA() { call0(ALLOC_MAA); }
void swdb_client_init_MAA() { call0(INIT_MAA); }
void swdb_client_clear_mem_region() { call0(CLEAR_REGION); }
void swdb_client_add_mem_region(void *start, void *end) { call2(ADD_REGION, address(start), address(end)); }
int swdb_client_new_tile() { return int(call0(NEW_TILE)); }
int swdb_client_new_reg() { return int(call0(NEW_REG)); }
void swdb_client_const(int32_t value, int id) { call2(CONST, value, id); }
int32_t swdb_client_get_reg(int id) { return int32_t(call1(GET_REG, id)); }
void *swdb_client_tile_pointer(int id) { return reinterpret_cast<void *>(uintptr_t(call1(TILE_POINTER, id))); }
uint16_t swdb_client_tile_size(int id) { return uint16_t(call1(TILE_SIZE_OP, id)); }
uint16_t swdb_client_tile_ready(int id) { return uint16_t(call1(TILE_READY, id)); }
void swdb_client_wait_ready(int id) { call1(WAIT_READY, id); }
void swdb_client_set_tile_size(int id, uint16_t size) { call2(SET_TILE_SIZE, id, size); }
void swdb_client_set_tile_ready(int id, uint16_t ready) { call2(SET_TILE_READY, id, ready); }
void swdb_client_stream_load(void *base, int lo, int hi, int stride, int dst, int cond) {
  calln(MAA_STREAM_LOAD, {address(base), lo, hi, stride, dst, cond});
}
void swdb_client_indirect_load(void *base, int index, int dst, int cond) {
  calln(MAA_INDIRECT_LOAD, {address(base), index, dst, cond});
}
void swdb_client_range_loop(int last_i, int last_j, int minimum, int maximum, int stride, int rows, int columns, int cond) {
  calln(MAA_RANGE_LOOP, {last_i, last_j, minimum, maximum, stride, rows, columns, cond});
}
void swdb_client_alu_scalar(int src, int scalar, int dst, Operation_t op, int cond) {
  calln(MAA_ALU_SCALAR, {src, scalar, dst, int64_t(op), cond});
}
void swdb_client_indirect_store(void *base, int index, int src, int cond, int dst) {
  calln(MAA_STORE, {address(base), index, src, cond, dst});
}
