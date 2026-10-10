// Candidate certification prelude (certify 1.3). Created: 2026-10-04 ET (ticket 70).
//
// `swdb certify` force-includes this file (-include) at the top of the candidate's translation
// unit in EVERY build of one candidate: the positive matrix and every negative control use the
// same bytes and the same flags. Nothing here names a fault, so the candidate's translation unit
// cannot tell a control build from a positive build; library-fault controls even link the very
// same candidate object file. Each fault lives only in a separately compiled trusted object
// (seams.cc, selected by -DSWDB_DXC_FAULT_<ID> on that object's command line alone).
//
// The seams below are the contract's library seams (ticket 62): the DX100 intrinsics, the CPU
// claim primitive compare_and_swap and the queue push (clause L4). Each forwards to an extern
// function defined in seams.cc. Quoted includes resolve from the candidate tree's source
// directory (-iquote), so the canonical lowering header included here is the tree's own copy,
// which certify has already checked byte for byte; its #pragma once makes the candidate's own
// include of it a no-op.
//
// Evaluator records (named checks, frontier windows, the kernel's result and the execution
// witness) are written by record.cc to a file descriptor the harness opened; the certifier never
// reads a verdict from the candidate's stdout or stderr. Candidate source that names any swdb_*
// harness symbol declared here is refused by the harness scan before any build.
#pragma once
#include <cstddef>
#include <cstdint>
#include "platform_atomics.h"
#include "sliding_queue.h"
#include "swdb_dxc_lowering.hpp"

// ---- evaluator records (defined in record.cc) ----
void swdb_cert_record_frontier(const int32_t *window, size_t count);
void swdb_cert_record_result_i32(const int32_t *values, size_t count);
void swdb_cert_record_result_f32(const float *values, size_t count);
void swdb_cert_record_end();

// The protected frontier print is preceded by this call (inserted by the evaluator): the current
// window of the shared queue, as raw vertex IDs. Duplicates and sizes are judged out of process.
template <class Queue> inline void swdb_certification_frontier(const Queue &queue) {
  static_assert(sizeof(*queue.shared) == 4, "certification frontier windows hold 32-bit vertex IDs");
  swdb_cert_record_frontier(reinterpret_cast<const int32_t *>(queue.shared + queue.shared_out_start),
                            size_t(queue.shared_out_end - queue.shared_out_start));
}

// ---- library seams (defined in seams.cc; faults act there) ----
void swdb_seam_session_begin();
dxc_context swdb_seam_thread_context();
void swdb_seam_wait(int tile);
void swdb_seam_gather_i32(void *base, int index, int dst);
void swdb_seam_stream_load_i32(void *base, int minimum, int maximum, int stride, int dst);
void swdb_seam_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns);
void swdb_seam_alu_scalar(int src, int reg, int dst, Operation_t op);
bool swdb_seam_cas_failed();
bool swdb_seam_push_twice();

inline void swdb_hooked_session_begin() { swdb_seam_session_begin(); }
inline dxc_context swdb_hooked_thread_context() { return swdb_seam_thread_context(); }
inline void swdb_hooked_wait(int tile) { swdb_seam_wait(tile); }
template <class T> inline void swdb_hooked_gather(T *base, int index, int dst) {
  static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32");
  swdb_seam_gather_i32((void *)base, index, dst);
}
template <class T> inline void swdb_hooked_stream_load(T *base, int minimum, int maximum, int stride, int dst) {
  static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32");
  swdb_seam_stream_load_i32((void *)base, minimum, maximum, stride, dst);
}
inline void swdb_hooked_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns) {
  swdb_seam_range_loop(last_i, last_j, lower, upper, stride, rows, columns);
}
inline void swdb_hooked_alu_scalar(int src, int reg, int dst, Operation_t op) { swdb_seam_alu_scalar(src, reg, dst, op); }
// The CPU claim: the real compare_and_swap first; seams.cc decides whether a failed compare
// "succeeds" anyway (the skipped_cas_recheck fault).
template <class T> inline bool swdb_hooked_compare_and_swap(T &x, const T &old_val, const T &new_val) {
  if (compare_and_swap(x, old_val, new_val)) return true;
  if (swdb_seam_cas_failed()) { __atomic_store_n(&x, new_val, __ATOMIC_SEQ_CST); return true; }
  return false;
}
// The queue push: seams.cc decides whether a push is duplicated (the forged_frontier fault).
template <typename T> class swdb_hooked_QueueBuffer : public QueueBuffer<T> {
 public:
  explicit swdb_hooked_QueueBuffer(SlidingQueue<T> &master, size_t given_size = 16384)
      : QueueBuffer<T>(master, given_size) {}
  void push_back(T to_add) {
    QueueBuffer<T>::push_back(to_add);
    if (swdb_seam_push_twice()) QueueBuffer<T>::push_back(to_add);
  }
};
#define __dxc_session_begin swdb_hooked_session_begin
#define __dxc_thread_context swdb_hooked_thread_context
#define __dxc_wait swdb_hooked_wait
#define __dxc_gather swdb_hooked_gather
#define __dxc_stream_load swdb_hooked_stream_load
#define __dxc_range_loop swdb_hooked_range_loop
#define __dxc_alu_scalar swdb_hooked_alu_scalar
#define compare_and_swap swdb_hooked_compare_and_swap
#define QueueBuffer swdb_hooked_QueueBuffer
