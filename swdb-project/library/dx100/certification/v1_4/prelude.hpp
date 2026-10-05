// Candidate certification prelude, certify 1.4. Created: 2026-10-05 ET (ticket 76).
// Agent-decided under Yan-Ru's delegation; revisable. Certify 1.3 keeps ../candidate_prelude.hpp.
//
// `swdb certify` force-includes this file (-include) at the top of the candidate's translation
// unit. Per tile size the candidate object is compiled once, and the positive matrix and every
// library-fault control run the SAME linked binary: the fault, if any, is chosen at run time by a
// plan the harness writes into a pipe that trusted code (record.cc) drains before main. Nothing in
// the candidate's text, code bytes, symbol addresses, arguments, environment variable names or
// descriptor layout differs between a positive run and a control run.
//
// Library seams (each forwards to trusted code in seams.cc):
//   - the DX100 intrinsics (as in 1.3);
//   - compare_and_swap on 4-byte integers (the CPU claim): the whole compare-and-swap runs in
//     seams.cc, which records every successful claim's address;
//   - QueueBuffer::push_back and SlidingQueue::push_back (the queue push): recorded per queue;
//   - SlidingQueue::slide_window and reset: at each slide, trusted code reads the queue's new
//     window from the queue object itself and records it with the claims and pushes since the
//     previous slide. This replaces 1.3's frontier inspection inside the candidate's function.
// Candidate source that names any swdb_* symbol declared here is refused by the harness scan.
#pragma once
#include <cstddef>
#include <cstdint>
#include <type_traits>
#include "platform_atomics.h"
#include "sliding_queue.h"
#include "swdb_dxc_lowering.hpp"

// ---- library seams (defined in seams.cc) ----
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

// The CPU claim. A 4-byte integer compare-and-swap runs entirely in seams.cc (recorded; the
// skipped_cas_recheck fault acts there). Other widths keep the platform primitive, unrecorded:
// they are not frontier claims (for example Bitmap::set_bit_atomic on 64-bit words).
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

// The queue push. seams.cc records each push for the queue it feeds and decides whether a push is
// duplicated (the forged_frontier fault; the copy is recorded as forged).
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

// The frontier queue. Trusted code observes each window at the slide that creates it.
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
    swdb_seam_slide(swdb_id(), reinterpret_cast<const int32_t *>(this->shared + this->shared_out_start),
                    size_t(this->shared_out_end - this->shared_out_start));
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
#define SlidingQueue swdb_hooked_SlidingQueue
