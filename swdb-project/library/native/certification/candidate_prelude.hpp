// Native-CPU candidate certification prelude (certify 1.4). Created: 2026-10-05 ET (ticket 75).
// Agent-decided under Yan-Ru's 2026-10-05 delegation; revisable.
//
// The native counterpart of library/dx100/certification/candidate_prelude.hpp (ticket 70). `swdb
// certify` force-includes this file (-include) at the top of the candidate's translation unit in
// EVERY build of one candidate at one build configuration: the positive matrix and every negative
// control link the very same candidate object. Nothing here names a fault. Each fault lives only
// in the separately compiled trusted object seams.cc, selected by -DSWDB_NATIVE_FAULT_<ID> on that
// object's command line alone, so the candidate's translation unit cannot tell a control build
// from a positive build.
//
// Seams (contract.bfs_tdstep_frontier_staging, clauses C1, C2, S1, S2):
//   * compare_and_swap: the CPU claim. The real compare-and-swap runs first; seams.cc decides
//     whether a successful claim loses its write (the claim_without_write fault).
//   * QueueBuffer::push_back: the enqueue. seams.cc decides whether a push is duplicated
//     (forged_frontier).
//   * the evaluator's frontier hook, inserted by the evaluator into a private build copy right
//     before DOBFS's protected frontier print (outside the rewritten TDStep): it hands the step's
//     window and the row-offset array to seams.cc, which records the window and may apply one
//     step-input fault (partial_batch_dropped, stale_row_offset).
//
// Evaluator records (frontier windows, the kernel's result and the execution witness) are written
// by record.cc to a file descriptor the harness opened; the certifier never reads a verdict from
// the candidate's stdout or stderr. Candidate source that names any swdb_* symbol declared here is
// refused by the harness scan before any build.
#pragma once
#include <cstddef>
#include <cstdint>
#include "platform_atomics.h"
#include "sliding_queue.h"

// ---- evaluator records (defined in record.cc) ----
void swdb_cert_record_frontier(const int32_t *window, size_t count);
void swdb_cert_record_result_i32(const int32_t *values, size_t count);
void swdb_cert_record_result_f32(const float *values, size_t count);
void swdb_cert_record_end();

// ---- library seams (defined in seams.cc; faults act there) ----
void swdb_seam_frontier(size_t *out_start, size_t *out_end, size_t shared_in, const int32_t *shared,
                        int32_t *offsets, size_t offsets_count);
void swdb_seam_count_claim();
void swdb_seam_count_push();
bool swdb_seam_claim_lost();
bool swdb_seam_push_twice();

// The evaluator inserts `swdb_certification_frontier(queue, VertexOffsetsOut);` before the protected
// frontier print of DOBFS (which the contract's rewrite scope leaves unchanged).
template <class Queue, class Offsets> inline void swdb_certification_frontier(Queue &queue, Offsets &offsets) {
  static_assert(sizeof(*queue.shared) == 4, "certification frontier windows hold 32-bit vertex IDs");
  static_assert(sizeof(*offsets.data()) == 4, "the DX100 fork's row offsets (SGOffset) are 32-bit");
  swdb_seam_frontier(&queue.shared_out_start, &queue.shared_out_end, queue.shared_in,
                     reinterpret_cast<const int32_t *>(queue.shared), reinterpret_cast<int32_t *>(offsets.data()),
                     size_t(offsets.endp() - offsets.beginp()));
}

// The CPU claim: the real compare_and_swap; on success the claim is counted (execution witness)
// and seams.cc decides whether the write is lost (claim_without_write).
template <class T> inline bool swdb_hooked_compare_and_swap(T &x, const T &old_val, const T &new_val) {
  if (!compare_and_swap(x, old_val, new_val)) return false;
  swdb_seam_count_claim();
  if (swdb_seam_claim_lost()) __atomic_store_n(&x, old_val, __ATOMIC_SEQ_CST);
  return true;
}
// The enqueue: counted; seams.cc decides whether a push is duplicated (forged_frontier).
template <typename T> class swdb_hooked_QueueBuffer : public QueueBuffer<T> {
 public:
  explicit swdb_hooked_QueueBuffer(SlidingQueue<T> &master, size_t given_size = 16384)
      : QueueBuffer<T>(master, given_size) {}
  void push_back(T to_add) {
    swdb_seam_count_push();
    QueueBuffer<T>::push_back(to_add);
    if (swdb_seam_push_twice()) QueueBuffer<T>::push_back(to_add);
  }
};
#define compare_and_swap swdb_hooked_compare_and_swap
#define QueueBuffer swdb_hooked_QueueBuffer
