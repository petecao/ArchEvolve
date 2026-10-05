// Native-CPU candidate certification prelude, certify 1.4. Created: 2026-10-05 ET (ticket 75).
// Agent-decided under Yan-Ru's delegation; revisable. The native form of
// library/dx100/certification/v1_4/prelude.hpp (ticket 76); certify 1.3 keeps ../candidate_prelude.hpp.
//
// `swdb certify` force-includes this file at the top of the candidate's translation unit. Per build
// configuration the candidate object is compiled once, and the positive matrix and every control
// run the SAME linked binary; the fault, if any, comes from a fixed-length plan that trusted code
// (record.cc) drains from a pipe before main. Nothing in the candidate's text, code, arguments,
// environment variable names or descriptor layout differs between a positive and a control run.
//
// Seams (each forwards to trusted code in seams.cc):
//   - compare_and_swap on 4-byte integers (the CPU claim): runs in seams.cc, which records every
//     successful claim's address (claim_without_write acts there);
//   - QueueBuffer::push_back and SlidingQueue::push_back: recorded per queue (forged_frontier);
//   - SlidingQueue::slide_window and reset: at each slide trusted code reads the new window from the
//     queue object, records it with the claims and pushes since the previous slide, and may shorten
//     the window the next step is handed (partial_batch_dropped). Nothing is inserted into the
//     candidate's rewritten function;
//   - the row offsets: the evaluator inserts `swdb_certification_offsets(queue, VertexOffsetsOut);`
//     before DOBFS's protected frontier print (DOBFS is outside the rewrite scope and unchanged), so
//     trusted code can substitute one row's bounds for one step (stale_row_offset).
#pragma once
#include <cstddef>
#include <cstdint>
#include <type_traits>
#include "platform_atomics.h"
#include "sliding_queue.h"

bool swdb_seam_claim_i32(int32_t *slot, int32_t expected, int32_t desired);
bool swdb_seam_push(const void *queue, int32_t value);
void swdb_seam_direct_push(const void *queue, int32_t value);
void swdb_seam_slide(const void *queue, const int32_t *shared, size_t *out_start, size_t *out_end);
void swdb_seam_reset(const void *queue);
void swdb_seam_offsets(const int32_t *window, size_t count, int32_t *offsets, size_t offsets_count);

template <class T> inline bool swdb_hooked_cas(T &x, const T &old_val, const T &new_val, std::true_type) {
  return swdb_seam_claim_i32(reinterpret_cast<int32_t *>(&x), int32_t(old_val), int32_t(new_val));
}
template <class T> inline bool swdb_hooked_cas(T &x, const T &old_val, const T &new_val, std::false_type) {
  return compare_and_swap(x, old_val, new_val);
}
template <class T> inline bool swdb_hooked_compare_and_swap(T &x, const T &old_val, const T &new_val) {
  return swdb_hooked_cas(x, old_val, new_val,
                         std::integral_constant<bool, sizeof(T) == 4 && std::is_integral<T>::value>());
}

template <typename T> class swdb_hooked_QueueBuffer : public QueueBuffer<T> {
  const void *swdb_queue_;
 public:
  explicit swdb_hooked_QueueBuffer(SlidingQueue<T> &master, size_t given_size = 16384)
      : QueueBuffer<T>(master, given_size), swdb_queue_(static_cast<const void *>(&master)) {}
  void push_back(T to_add) {
    static_assert(sizeof(T) == 4, "certification records 32-bit frontier values");
    QueueBuffer<T>::push_back(to_add);
    if (swdb_seam_push(swdb_queue_, int32_t(to_add))) QueueBuffer<T>::push_back(to_add);
  }
};

template <typename T> class swdb_hooked_SlidingQueue : public SlidingQueue<T> {
  const void *swdb_id() const { return static_cast<const void *>(static_cast<const SlidingQueue<T> *>(this)); }
 public:
  explicit swdb_hooked_SlidingQueue(size_t shared_size) : SlidingQueue<T>(shared_size) {}
  void push_back(T to_add) {
    static_assert(sizeof(T) == 4, "certification records 32-bit frontier values");
    SlidingQueue<T>::push_back(to_add);
    swdb_seam_direct_push(swdb_id(), int32_t(to_add));
  }
  void reset() {
    SlidingQueue<T>::reset();
    swdb_seam_reset(swdb_id());
  }
  void slide_window() {
    SlidingQueue<T>::slide_window();
    swdb_seam_slide(swdb_id(), reinterpret_cast<const int32_t *>(this->shared), &this->shared_out_start,
                    &this->shared_out_end);
  }
};

template <class Queue, class Offsets> inline void swdb_certification_offsets(Queue &queue, Offsets &offsets) {
  static_assert(sizeof(*offsets.data()) == 4, "the DX100 fork's row offsets (SGOffset) are 32-bit");
  swdb_seam_offsets(reinterpret_cast<const int32_t *>(queue.shared + queue.shared_out_start),
                    size_t(queue.shared_out_end - queue.shared_out_start), reinterpret_cast<int32_t *>(offsets.data()),
                    size_t(offsets.endp() - offsets.beginp()));
}

#define compare_and_swap swdb_hooked_compare_and_swap
#define QueueBuffer swdb_hooked_QueueBuffer
#define SlidingQueue swdb_hooked_SlidingQueue
