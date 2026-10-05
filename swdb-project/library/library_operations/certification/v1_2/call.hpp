// The call block of library-operation certification 1.2. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// Command 1.2 runs each library-operation call in two processes: the trusted evaluator
// (evaluator.cc + the unchanged 1.1 record.cc) and the candidate binary (the candidate's unit +
// runner.cc). They share the certify 1.5 arena (library/dx100/certification/v1_5/arena.hpp, mapped at
// one address in both). The evaluator places the case's inputs and the output canary in the arena's
// heap part and describes them here; the runner copies them into the candidate process's own heap
// (so a sanitized build keeps its redzones around every operand, as in 1.1), calls the entry, copies
// the output and the inputs back, and sets `done`. The evaluator then judges the arena from its own
// private copies: driver fault, frame check, output record, end.
#pragma once
#include <atomic>
#include <cstdint>
#include "../../../dx100/certification/v1_5/arena.hpp"

namespace swdb_lo_call {
constexpr uint64_t MAGIC = 0x53574442434c3132ULL;   // "SWDBCL12"
constexpr int MAX_INPUTS = 4;
struct Call {
  uint64_t magic;
  int32_t family;
  int32_t inputs;
  uint64_t input_address[MAX_INPUTS], input_bytes[MAX_INPUTS];
  uint64_t output_address, output_count;            // doubles
  int64_t scalar[8];
  std::atomic<int32_t> done;
};
static_assert(sizeof(Call) <= swdb_arena::SLOTS * swdb_arena::SLOT_BYTES, "call block");
// The call block uses the arena's request-slot area (library-operation runs make no requests).
inline Call *call() { return reinterpret_cast<Call *>(swdb_arena::ADDRESS + swdb_arena::HEADER_BYTES); }
enum Family : int32_t { PACK = 1, GATHER, REGROUP, BIN_DRAIN, GATHER_STREAM, RELABEL };
}  // namespace swdb_lo_call
