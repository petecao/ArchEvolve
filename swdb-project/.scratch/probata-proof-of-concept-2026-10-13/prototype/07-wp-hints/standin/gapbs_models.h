// PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
// Hand lowering of the GAPBS types and members the unit calls (map 16 item 3: a class becomes a
// struct of the same name and fields, references become pointers, members and operators become
// named functions). Threads = 1. Members with a body here are proven in the same WP run.
// Body-less functions (compiler builtins, operator new[] / delete[], std::copy) are
// standard-library summaries: Extern contracts, each an assumption entry (map 16 item 7).
// Lowering choice: a `const T &` scalar parameter is passed by value.
#ifndef GAPBS_MODELS_H
#define GAPBS_MODELS_H
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef int32_t NodeID;    /* benchmark.h:29 */
typedef int32_t SGOffset;  /* graph.h:90 */

/* CSRGraph<NodeID> (graph.h:93); Graph is its typedef (benchmark.h:33). */
typedef struct CSRGraph_NodeID {
  bool directed_;
  int64_t num_nodes_;
  int64_t num_edges_;
  NodeID **out_index_;
  NodeID *out_neighbors_;
  NodeID **in_index_;
  NodeID *in_neighbors_;
} Graph;

struct pvector_NodeID { NodeID *start_; NodeID *end_size_; NodeID *end_capacity_; };
struct pvector_SGOffset { SGOffset *start_; SGOffset *end_size_; SGOffset *end_capacity_; };

struct SlidingQueue_NodeID {
  NodeID *shared;
  size_t shared_in;
  size_t shared_out_start;
  size_t shared_out_end;
  size_t shared_max_size;
};

struct QueueBuffer_NodeID {
  size_t in;
  NodeID *local_queue;
  struct SlidingQueue_NodeID *sq;  /* SlidingQueue<T> &sq */
  size_t local_size;               /* const size_t */
};

/* Source-domain repair, 2026-10-16 ET. These are representation/call domains,
   not loop proof hints. Empty spans permit a live one-past endpoint, never a
   null or expired pointer. This is the restricted C hand model, not a complete
   contract for every C++11 iterator accepted by the standard library. */
/*@
  predicate gapbs_nodeid_span{L}(NodeID *base, integer count) =
    0 <= count <= PTRDIFF_MAX && \object_pointer(base) &&
    \object_pointer(base + count) && \base_addr(base) == \base_addr(base + count) &&
    \pointer_comparable(base, base + count);

  predicate gapbs_queue_domain{L}(struct SlidingQueue_NodeID *self) =
    \valid(self) &&
    \initialized(&self->shared) && \initialized(&self->shared_in) &&
    \initialized(&self->shared_out_start) && \initialized(&self->shared_out_end) &&
    \initialized(&self->shared_max_size) &&
    self->shared_out_start <= self->shared_out_end <= self->shared_in <= self->shared_max_size &&
    gapbs_nodeid_span(self->shared, self->shared_max_size) &&
    \valid(self->shared + (0 .. self->shared_max_size - 1)) &&
    \separated(self, self->shared + (0 .. self->shared_max_size - 1));
*/

/* ---- standard-library and builtin summaries (Extern) ---- */

/*@ requires \valid(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns *ptr;
    ensures \initialized(ptr);
    ensures (\result != 0) <==> (\old(*ptr) == oldval);
    ensures \old(*ptr) == oldval ==> *ptr == newval;
    ensures \old(*ptr) != oldval ==> *ptr == \old(*ptr);
    exits \false; */
bool __sync_bool_compare_and_swap_NodeID(NodeID *ptr, NodeID oldval, NodeID newval);

/*@ requires \valid_read(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns \nothing;
    ensures \result == *ptr;
    exits \false; */
NodeID __atomic_load_n_NodeID(const NodeID *ptr, int memorder);

/*@ requires \valid(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns *ptr;
    ensures \initialized(ptr);
    ensures *ptr == ((integer)\old(*ptr) + value) % ((integer)SIZE_MAX + 1);
    ensures \result == \old(*ptr);
    exits \false; */
size_t __sync_fetch_and_add_size_t(size_t *ptr, size_t value);

/* operator new NodeID[n] for the QueueBuffer of thread 0. WP does not implement \fresh
   ("Allocation ... not yet implemented"), so the lowering gives each thread's QueueBuffer its
   own storage block; TDStep's precondition separates it from the unit's arrays.
   Scope: exactly one thread-zero QueueBuffer construction/destruction lifetime
   per TDStep, no escaped local-buffer view, no overlapping live construction and
   no repeated destruction. This fixed-storage abstraction does not model a
   general allocator, dangling pointers or reuse across simultaneous instances. */
#define SWDB_LQUEUE_CAPACITY 16384
NodeID swdb_lqueue_storage[SWDB_LQUEUE_CAPACITY];
/*@
  predicate gapbs_buffer_domain{L}(struct QueueBuffer_NodeID *self) =
    \valid(self) &&
    \initialized(&self->sq) && \initialized(&self->local_size) &&
    \initialized(&self->in) && \initialized(&self->local_queue) &&
    gapbs_queue_domain(self->sq) &&
    1 <= self->local_size <= SWDB_LQUEUE_CAPACITY && self->in <= self->local_size &&
    self->local_queue == &swdb_lqueue_storage[0] &&
    \separated(self, self->sq,
      self->local_queue + (0 .. self->local_size - 1),
      self->sq->shared + (0 .. self->sq->shared_max_size - 1));
*/
/*@ requires n <= SWDB_LQUEUE_CAPACITY;
    terminates \true;
    assigns \nothing;
    ensures \result == &swdb_lqueue_storage[0];
    exits \false; */
NodeID *swdb_new_NodeID_array(size_t n);

/*@ requires p == &swdb_lqueue_storage[0];
    terminates \true;
    assigns \nothing;
    exits \false; */
void swdb_delete_NodeID_array(NodeID *p);

/*@ requires \object_pointer(first) && \object_pointer(last);
    requires \base_addr(first) == \base_addr(last);
    requires \pointer_comparable(first, last) && first <= last;
    requires \offset(last) - \offset(first) <= (integer)PTRDIFF_MAX * sizeof(NodeID);
    requires \valid_read(first + (0 .. last - first - 1));
    requires \initialized(first + (0 .. last - first - 1));
    requires gapbs_nodeid_span(d_first, last - first);
    requires \valid(d_first + (0 .. last - first - 1));
    requires \separated(first + (0 .. last - first - 1), d_first + (0 .. last - first - 1));
    terminates \true;
    assigns d_first[0 .. last - first - 1];
    ensures \forall integer i; 0 <= i < last - first ==> d_first[i] == \old(first[i]);
    ensures \result == d_first + (last - first);
    ensures \initialized(d_first + (0 .. last - first - 1));
    exits \false; */
NodeID *std_copy_NodeID(const NodeID *first, const NodeID *last, NodeID *d_first);

/* ---- GAPBS members (bodies; proven in the run) ---- */

#define __ATOMIC_RELAXED 0

/* platform_atomics.h:30 */
/*@ requires \valid(x);
    requires \initialized(x);
    assigns *x;
    ensures \initialized(x);
    ensures (\result != 0) <==> (\old(*x) == old_val);
    ensures \old(*x) == old_val ==> *x == new_val;
    ensures \old(*x) != old_val ==> *x == \old(*x); */
bool compare_and_swap(NodeID *x, NodeID old_val, NodeID new_val) {
  return __sync_bool_compare_and_swap_NodeID(x, old_val, new_val);
}

/* platform_atomics.h:25 */
/*@ requires \valid(x);
    requires \initialized(x);
    assigns *x;
    ensures \initialized(x);
    ensures *x == ((integer)\old(*x) + inc) % ((integer)SIZE_MAX + 1);
    ensures \result == \old(*x); */
size_t fetch_and_add_size_t(size_t *x, size_t inc) {
  return __sync_fetch_and_add_size_t(x, inc);
}

/* std::min<size_t> */
/*@ assigns \nothing;
    ensures a <= b ==> \result == a;
    ensures a > b ==> \result == b; */
size_t std_min_size_t(size_t a, size_t b) {
  return (b < a) ? b : a;
}

/* omp_get_thread_num under the threads = 1 lowering */
/*@ assigns \nothing;
    ensures \result == 0; */
int omp_get_thread_num(void) { return 0; }

/* pvector.h:113, 152, 156 and data() */
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \object_pointer(self->start_) && \object_pointer(self->end_size_);
    requires \base_addr(self->start_) == \base_addr(self->end_size_);
    requires \pointer_comparable(self->start_, self->end_size_) && self->start_ <= self->end_size_;
    requires \offset(self->end_size_) - \offset(self->start_) <= (integer)PTRDIFF_MAX * sizeof(*self->start_);
    requires 0 <= n < self->end_size_ - self->start_;
    requires \valid(self->start_ + n);
    assigns \nothing; ensures \result == self->start_ + n; */
NodeID *pvector_NodeID_operator_index(struct pvector_NodeID *self, size_t n) { return self->start_ + n; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns \nothing; ensures \result == self->start_; */
NodeID *pvector_NodeID_data(struct pvector_NodeID *self) { return self->start_; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns \nothing; ensures \result == self->start_; */
NodeID *pvector_NodeID_beginp(struct pvector_NodeID *self) { return self->start_; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \object_pointer(self->start_) && \object_pointer(self->end_size_);
    requires \base_addr(self->start_) == \base_addr(self->end_size_);
    requires \pointer_comparable(self->start_, self->end_size_) && self->start_ <= self->end_size_;
    requires \offset(self->end_size_) - \offset(self->start_) <= (integer)PTRDIFF_MAX * sizeof(*self->start_);
    assigns \nothing; ensures \result == self->end_size_; */
NodeID *pvector_NodeID_endp(struct pvector_NodeID *self) { return self->end_size_; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \object_pointer(self->start_) && \object_pointer(self->end_size_);
    requires \base_addr(self->start_) == \base_addr(self->end_size_);
    requires \pointer_comparable(self->start_, self->end_size_) && self->start_ <= self->end_size_;
    requires \offset(self->end_size_) - \offset(self->start_) <= (integer)PTRDIFF_MAX * sizeof(*self->start_);
    requires 0 <= n < self->end_size_ - self->start_;
    requires \valid(self->start_ + n);
    assigns \nothing; ensures \result == self->start_ + n; */
SGOffset *pvector_SGOffset_operator_index(struct pvector_SGOffset *self, size_t n) { return self->start_ + n; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns \nothing; ensures \result == self->start_; */
SGOffset *pvector_SGOffset_data(struct pvector_SGOffset *self) { return self->start_; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns \nothing; ensures \result == self->start_; */
SGOffset *pvector_SGOffset_beginp(struct pvector_SGOffset *self) { return self->start_; }
/*@ requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \object_pointer(self->start_) && \object_pointer(self->end_size_);
    requires \base_addr(self->start_) == \base_addr(self->end_size_);
    requires \pointer_comparable(self->start_, self->end_size_) && self->start_ <= self->end_size_;
    requires \offset(self->end_size_) - \offset(self->start_) <= (integer)PTRDIFF_MAX * sizeof(*self->start_);
    assigns \nothing; ensures \result == self->end_size_; */
SGOffset *pvector_SGOffset_endp(struct pvector_SGOffset *self) { return self->end_size_; }

/* arkhadem/DX100 e4fc4af, benchmarks/gapbs/src/sliding_queue.h:73-78.
   beginp/endp register full allocated storage; begin/end separately select the
   active frontier window. The named APIs must not be conflated. */
/*@ requires gapbs_queue_domain(self);
    assigns \nothing; ensures \result == self->shared; */
NodeID *SlidingQueue_NodeID_beginp(struct SlidingQueue_NodeID *self) { return self->shared; }
/*@ requires gapbs_queue_domain(self);
    assigns \nothing; ensures \result == self->shared + self->shared_max_size; */
NodeID *SlidingQueue_NodeID_endp(struct SlidingQueue_NodeID *self) { return self->shared + self->shared_max_size; }
/*@ requires gapbs_queue_domain(self);
    assigns \nothing;
    ensures \result == self->shared_out_end - self->shared_out_start; */
size_t SlidingQueue_NodeID_size(struct SlidingQueue_NodeID *self) {
  return (size_t)((self->shared + self->shared_out_end) - (self->shared + self->shared_out_start));
}

/* sliding_queue.h:89-94 */
/*@ requires \valid(self) && gapbs_queue_domain(master);
    requires 1 <= given_size <= SWDB_LQUEUE_CAPACITY;
    requires \separated(self, master, swdb_lqueue_storage + (0 .. SWDB_LQUEUE_CAPACITY - 1),
      master->shared + (0 .. master->shared_max_size - 1));
    assigns self->sq, self->local_size, self->in, self->local_queue;
    ensures self->sq == master && self->local_size == given_size && self->in == 0;
    ensures self->local_queue == &swdb_lqueue_storage[0];
    ensures gapbs_buffer_domain(self); */
void QueueBuffer_NodeID_QueueBuffer(struct QueueBuffer_NodeID *self, struct SlidingQueue_NodeID *master, size_t given_size) {
  self->sq = master;
  self->local_size = given_size;
  self->in = 0;
  self->local_queue = swdb_new_NodeID_array(self->local_size);
}

/* sliding_queue.h:96-98 */
/*@ requires gapbs_buffer_domain(self);
    assigns \nothing; */
void QueueBuffer_NodeID_destroy(struct QueueBuffer_NodeID *self) {
  swdb_delete_NodeID_array(self->local_queue);
}

/* sliding_queue.h:106-111 */
/*@ requires gapbs_buffer_domain(self);
    requires self->in <= self->sq->shared_max_size - self->sq->shared_in;
    requires \valid_read(self->local_queue + (0 .. self->in - 1));
    requires \initialized(self->local_queue + (0 .. self->in - 1));
    assigns self->in, self->sq->shared_in,
            self->sq->shared[self->sq->shared_in .. self->sq->shared_in + self->in - 1];
    ensures self->sq->shared_in == \old(self->sq->shared_in) + \old(self->in);
    ensures \initialized(self->sq->shared +
      (\old(self->sq->shared_in) .. \old(self->sq->shared_in) + \old(self->in) - 1));
    ensures \forall integer i; 0 <= i < \old(self->in) ==>
              self->sq->shared[\old(self->sq->shared_in) + i] == \old(self->local_queue[i]);
    ensures self->in == 0;
    ensures gapbs_buffer_domain(self); */
void QueueBuffer_NodeID_flush(struct QueueBuffer_NodeID *self) {
  NodeID *shared_queue = self->sq->shared;
  size_t copy_start = fetch_and_add_size_t(&self->sq->shared_in, self->in);
  std_copy_NodeID(self->local_queue, self->local_queue + self->in, shared_queue + copy_start);
  self->in = 0;
}

/* sliding_queue.h:100-104 */
/*@ requires gapbs_buffer_domain(self);
    requires self->in == self->local_size ==>
      self->in <= self->sq->shared_max_size - self->sq->shared_in;
    requires \valid_read(self->local_queue + (0 .. self->in - 1));
    requires \initialized(self->local_queue + (0 .. self->in - 1));
    assigns self->in, self->local_queue[0 .. self->local_size - 1], self->sq->shared_in,
            self->sq->shared[self->sq->shared_in .. self->sq->shared_in + self->in - 1];
    ensures gapbs_buffer_domain(self);
    behavior buffered:
      assumes self->in < self->local_size;
      ensures self->in == \old(self->in) + 1;
      ensures self->local_queue[\old(self->in)] == to_add;
      ensures \initialized(self->local_queue + (0 .. self->in - 1));
      ensures \forall integer i; 0 <= i < \old(self->in) ==> self->local_queue[i] == \old(self->local_queue[i]);
      ensures self->sq->shared_in == \old(self->sq->shared_in);
    behavior flushed:
      assumes self->in == self->local_size;
      ensures self->sq->shared_in == \old(self->sq->shared_in) + \old(self->in);
      ensures \initialized(self->sq->shared +
        (\old(self->sq->shared_in) .. \old(self->sq->shared_in) + \old(self->in) - 1));
      ensures \forall integer i; 0 <= i < \old(self->in) ==>
                self->sq->shared[\old(self->sq->shared_in) + i] == \old(self->local_queue[i]);
      ensures self->in == 1;
      ensures self->local_queue[0] == to_add;
      ensures \initialized(self->local_queue);
    complete behaviors;
    disjoint behaviors; */
void QueueBuffer_NodeID_push_back(struct QueueBuffer_NodeID *self, NodeID to_add) {
  if (self->in == self->local_size)
    QueueBuffer_NodeID_flush(self);
  self->local_queue[self->in++] = to_add;
}

#endif
