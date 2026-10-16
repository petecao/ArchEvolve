// Prospective lexical private-array refinement; source/formal acceptance pending.
// Prospective private out-slot ABI, 2026-10-16 ET. Not a proof record.
// PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
// Hand lowering of the GAPBS types and members the unit calls (map 16 item 3: a class becomes a
// struct of the same name and fields, references become pointers, members and operators become
// named functions). Threads = 1. All bodies here must be proved in a fresh WP component.
// Body-less atomic/copy interfaces retain Extern summary assumptions.
// Private binding is an ordinary body; retirement is a caller-scope obligation.
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
    \valid(base + (0 .. count - 1)) && \object_pointer(base + count);

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

/*@ requires \valid(swdb_out); requires \separated(swdb_out, ptr);
 requires \valid(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns *ptr, *swdb_out;
    ensures \initialized(ptr);
    ensures ((*swdb_out) != 0) <==> (\old(*ptr) == oldval);
    ensures \old(*ptr) == oldval ==> *ptr == newval;
    ensures \old(*ptr) != oldval ==> *ptr == \old(*ptr);
    exits \false;
    ensures \initialized(swdb_out); */
void __sync_bool_compare_and_swap_NodeID_out(NodeID *ptr, NodeID oldval, NodeID newval, bool *swdb_out);

/*@ requires \valid(swdb_out); requires \separated(swdb_out, ptr);
 requires \valid_read(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns *swdb_out;
    ensures (*swdb_out) == *ptr;
    exits \false;
    ensures \initialized(swdb_out); */
void __atomic_load_n_NodeID_out(const NodeID *ptr, int memorder, NodeID *swdb_out);

/*@ requires \valid(swdb_out); requires \separated(swdb_out, ptr);
 requires \valid(ptr);
    requires \initialized(ptr);
    terminates \true;
    assigns *ptr, *swdb_out;
    ensures \initialized(ptr);
    ensures *ptr == ((integer)\old(*ptr) + value) % ((integer)SIZE_MAX + 1);
    ensures (*swdb_out) == \old(*ptr);
    exits \false;
    ensures \initialized(swdb_out); */
void __sync_fetch_and_add_size_t_out(size_t *ptr, size_t value, size_t *swdb_out);

/* Private storage for the source's one default QueueBuffer lifetime.
   Caller creates one uninitialized typed automatic object. This adapter only
   binds its address; it does not initialize payload or implement an allocator.
   Source refinement, lifetime and actual initialization-map gates remain open. */
#define SWDB_LQUEUE_CAPACITY 16384
typedef NodeID swdb_private_NodeID_array[SWDB_LQUEUE_CAPACITY];
/*@
  predicate gapbs_buffer_domain{L}(struct QueueBuffer_NodeID *self) =
    \valid(self) &&
    \initialized(&self->sq) && \initialized(&self->local_size) &&
    \initialized(&self->in) && \initialized(&self->local_queue) &&
    gapbs_queue_domain(self->sq) &&
    self->local_size == SWDB_LQUEUE_CAPACITY && self->in <= self->local_size &&
    gapbs_nodeid_span(self->local_queue, self->local_size) &&
    \separated(self, self->sq,
      self->local_queue + (0 .. self->local_size - 1),
      self->sq->shared + (0 .. self->sq->shared_max_size - 1));
*/
/*@ requires \valid(storage) && \valid(swdb_out);
    requires n == SWDB_LQUEUE_CAPACITY;
    requires gapbs_nodeid_span(&(*storage)[0], n);
    requires \separated(storage, swdb_out);
    assigns *swdb_out;
    ensures *swdb_out == &(*storage)[0];
    ensures \initialized(swdb_out); */
void swdb_bind_private_NodeID_array(swdb_private_NodeID_array *storage, size_t n, NodeID **swdb_out) {
  (void)n;
  *swdb_out = &(*storage)[0];
}

/*@ requires \valid(swdb_out); requires \separated(swdb_out, first + (0 .. swdb_count - 1), d_first + (0 .. swdb_count - 1));
 requires gapbs_nodeid_span((NodeID *)first, swdb_count);
    requires last == first + swdb_count;
    requires \valid_read(first + (0 .. swdb_count - 1));
    requires \initialized(first + (0 .. swdb_count - 1));
    requires gapbs_nodeid_span(d_first, swdb_count);
    requires \valid(d_first + (0 .. swdb_count - 1));
    requires \separated(first + (0 .. swdb_count - 1), d_first + (0 .. swdb_count - 1));
    terminates \true;
    assigns d_first[0 .. swdb_count - 1], *swdb_out;
    ensures \forall integer i; 0 <= i < swdb_count ==> d_first[i] == \old(first[i]);
    ensures (*swdb_out) == d_first + (swdb_count);
    ensures \initialized(d_first + (0 .. swdb_count - 1));
    exits \false;
    ensures \initialized(swdb_out); */
void std_copy_NodeID_out(const NodeID *first, const NodeID *last, NodeID *d_first, size_t swdb_count, NodeID * *swdb_out);

/* ---- GAPBS members (bodies; proven in the run) ---- */

#define __ATOMIC_RELAXED 0

/* platform_atomics.h:30 */
/*@ requires \valid(swdb_out); requires \separated(swdb_out, x);
 requires \valid(x);
    requires \initialized(x);
    assigns *x, *swdb_out;
    ensures \initialized(x);
    ensures ((*swdb_out) != 0) <==> (\old(*x) == old_val);
    ensures \old(*x) == old_val ==> *x == new_val;
    ensures \old(*x) != old_val ==> *x == \old(*x);
    ensures \initialized(swdb_out); */
void compare_and_swap_out(NodeID *x, NodeID old_val, NodeID new_val, bool *swdb_out) {
  bool swdb_ret_atomic;
  __sync_bool_compare_and_swap_NodeID_out(x, old_val, new_val, &swdb_ret_atomic);
  *swdb_out = swdb_ret_atomic;
}

/* platform_atomics.h:25 */
/*@ requires \valid(swdb_out); requires \separated(swdb_out, x);
 requires \valid(x);
    requires \initialized(x);
    assigns *x, *swdb_out;
    ensures \initialized(x);
    ensures *x == ((integer)\old(*x) + inc) % ((integer)SIZE_MAX + 1);
    ensures (*swdb_out) == \old(*x);
    ensures \initialized(swdb_out); */
void fetch_and_add_size_t_out(size_t *x, size_t inc, size_t *swdb_out) {
  size_t swdb_ret_atomic;
  __sync_fetch_and_add_size_t_out(x, inc, &swdb_ret_atomic);
  *swdb_out = swdb_ret_atomic;
}

/* std::min<size_t> */
/*@ requires \valid(swdb_out);
 assigns *swdb_out;
    ensures a <= b ==> (*swdb_out) == a;
    ensures a > b ==> (*swdb_out) == b;
    ensures \initialized(swdb_out); */
void std_min_size_t_out(size_t a, size_t b, size_t *swdb_out) {
  *swdb_out = (b < a) ? b : a;
}

/* omp_get_thread_num under the threads = 1 lowering */
/*@ requires \valid(swdb_out);
 assigns *swdb_out;
    ensures (*swdb_out) == 0;
    ensures \initialized(swdb_out); */
void omp_get_thread_num_out(int *swdb_out) { *swdb_out = 0; }

/* pvector.h:113, 152, 156 and data() */
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \exists integer count; gapbs_nodeid_span(self->start_, count) && self->end_size_ == self->start_ + count;
    requires 0 <= n < self->end_size_ - self->start_;
    requires \valid(self->start_ + n);
    assigns *swdb_out; ensures (*swdb_out) == self->start_ + n;
    ensures \initialized(swdb_out); */
void pvector_NodeID_operator_index_out(struct pvector_NodeID *self, size_t n, NodeID * *swdb_out) { *swdb_out = self->start_ + n; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns *swdb_out; ensures (*swdb_out) == self->start_;
    ensures \initialized(swdb_out); */
void pvector_NodeID_data_out(struct pvector_NodeID *self, NodeID * *swdb_out) { *swdb_out = self->start_; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns *swdb_out; ensures (*swdb_out) == self->start_;
    ensures \initialized(swdb_out); */
void pvector_NodeID_beginp_out(struct pvector_NodeID *self, NodeID * *swdb_out) { *swdb_out = self->start_; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \exists integer count; gapbs_nodeid_span(self->start_, count) && self->end_size_ == self->start_ + count;
    assigns *swdb_out; ensures (*swdb_out) == self->end_size_;
    ensures \initialized(swdb_out); */
void pvector_NodeID_endp_out(struct pvector_NodeID *self, NodeID * *swdb_out) { *swdb_out = self->end_size_; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \exists integer count; gapbs_nodeid_span(self->start_, count) && self->end_size_ == self->start_ + count;
    requires 0 <= n < self->end_size_ - self->start_;
    requires \valid(self->start_ + n);
    assigns *swdb_out; ensures (*swdb_out) == self->start_ + n;
    ensures \initialized(swdb_out); */
void pvector_SGOffset_operator_index_out(struct pvector_SGOffset *self, size_t n, SGOffset * *swdb_out) { *swdb_out = self->start_ + n; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns *swdb_out; ensures (*swdb_out) == self->start_;
    ensures \initialized(swdb_out); */
void pvector_SGOffset_data_out(struct pvector_SGOffset *self, SGOffset * *swdb_out) { *swdb_out = self->start_; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \object_pointer(self->start_);
    assigns *swdb_out; ensures (*swdb_out) == self->start_;
    ensures \initialized(swdb_out); */
void pvector_SGOffset_beginp_out(struct pvector_SGOffset *self, SGOffset * *swdb_out) { *swdb_out = self->start_; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires \valid_read(self);
    requires \initialized(&self->start_) && \initialized(&self->end_size_);
    requires \exists integer count; gapbs_nodeid_span(self->start_, count) && self->end_size_ == self->start_ + count;
    assigns *swdb_out; ensures (*swdb_out) == self->end_size_;
    ensures \initialized(swdb_out); */
void pvector_SGOffset_endp_out(struct pvector_SGOffset *self, SGOffset * *swdb_out) { *swdb_out = self->end_size_; }

/* arkhadem/DX100 e4fc4af, benchmarks/gapbs/src/sliding_queue.h:73-78.
   beginp/endp register full allocated storage; begin/end separately select the
   active frontier window. The named APIs must not be conflated. */
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires gapbs_queue_domain(self);
    assigns *swdb_out; ensures (*swdb_out) == self->shared;
    ensures \initialized(swdb_out); */
void SlidingQueue_NodeID_beginp_out(struct SlidingQueue_NodeID *self, NodeID * *swdb_out) { *swdb_out = self->shared; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires gapbs_queue_domain(self);
    assigns *swdb_out; ensures (*swdb_out) == self->shared + self->shared_max_size;
    ensures \initialized(swdb_out); */
void SlidingQueue_NodeID_endp_out(struct SlidingQueue_NodeID *self, NodeID * *swdb_out) { *swdb_out = self->shared + self->shared_max_size; }
/*@ requires \valid(swdb_out); requires \separated(swdb_out, self);
 requires gapbs_queue_domain(self);
    assigns *swdb_out;
    ensures (*swdb_out) == self->shared_out_end - self->shared_out_start;
    ensures \initialized(swdb_out); */
void SlidingQueue_NodeID_size_out(struct SlidingQueue_NodeID *self, size_t *swdb_out) {
  *swdb_out = (size_t)((self->shared + self->shared_out_end) - (self->shared + self->shared_out_start));
}

/* sliding_queue.h:89-94 */
/*@ requires \valid(self) && gapbs_queue_domain(master);
    requires given_size == SWDB_LQUEUE_CAPACITY;
    requires \valid(storage) && gapbs_nodeid_span(&(*storage)[0], given_size);
    requires \separated(self, master, storage,
      master->shared + (0 .. master->shared_max_size - 1));
    assigns self->sq, self->local_size, self->in, self->local_queue;
    ensures self->sq == master && self->local_size == given_size && self->in == 0;
    ensures self->local_queue == &(*storage)[0];
    ensures gapbs_buffer_domain(self); */
void QueueBuffer_NodeID_QueueBuffer(struct QueueBuffer_NodeID *self, struct SlidingQueue_NodeID *master, size_t given_size, swdb_private_NodeID_array *storage) {
  self->sq = master;
  self->local_size = given_size;
  self->in = 0;
  NodeID *swdb_ret_alloc;
  swdb_bind_private_NodeID_array(storage, self->local_size, &swdb_ret_alloc);
  self->local_queue = swdb_ret_alloc;
}

/* sliding_queue.h:96-98 */
/*@ requires gapbs_buffer_domain(self);
    assigns \nothing; */
void QueueBuffer_NodeID_destroy(struct QueueBuffer_NodeID *self) {
  /* Lexical destruction marker: every admitted caller ends the array's
     block immediately after this call. No deallocation claim for this body. */
  (void)self;
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
  size_t swdb_ret_fetch;
  fetch_and_add_size_t_out(&self->sq->shared_in, self->in, &swdb_ret_fetch);
  size_t copy_start = swdb_ret_fetch;
  NodeID *swdb_ret_copy;
  std_copy_NodeID_out(self->local_queue, self->local_queue + self->in, shared_queue + copy_start, self->in, &swdb_ret_copy);
  (void)swdb_ret_copy;
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
