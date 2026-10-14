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

/* ---- standard-library and builtin summaries (Extern) ---- */

/*@ requires \valid(ptr);
    terminates \true;
    assigns *ptr;
    ensures (\result != 0) <==> (\old(*ptr) == oldval);
    ensures \old(*ptr) == oldval ==> *ptr == newval;
    ensures \old(*ptr) != oldval ==> *ptr == \old(*ptr);
    exits \false; */
bool __sync_bool_compare_and_swap_NodeID(NodeID *ptr, NodeID oldval, NodeID newval);

/*@ requires \valid_read(ptr);
    terminates \true;
    assigns \nothing;
    ensures \result == *ptr;
    exits \false; */
NodeID __atomic_load_n_NodeID(const NodeID *ptr, int memorder);

/*@ requires \valid(ptr);
    terminates \true;
    assigns *ptr;
    ensures *ptr == \old(*ptr) + value;
    ensures \result == \old(*ptr);
    exits \false; */
size_t __sync_fetch_and_add_size_t(size_t *ptr, size_t value);

/* operator new NodeID[n] for the QueueBuffer of thread 0. WP does not implement \fresh
   ("Allocation ... not yet implemented"), so the lowering gives each thread's QueueBuffer its
   own storage block; TDStep's precondition separates it from the unit's arrays. */
#define SWDB_LQUEUE_CAPACITY 16384
NodeID swdb_lqueue_storage[SWDB_LQUEUE_CAPACITY];
/*@ requires n <= SWDB_LQUEUE_CAPACITY;
    terminates \true;
    assigns \nothing;
    ensures \result == &swdb_lqueue_storage[0];
    exits \false; */
NodeID *swdb_new_NodeID_array(size_t n);

/*@ terminates \true;
    assigns \nothing;
    exits \false; */
void swdb_delete_NodeID_array(NodeID *p);

/*@ requires first <= last;
    requires \separated(first + (0 .. last - first - 1), d_first + (0 .. last - first - 1));
    terminates \true;
    assigns d_first[0 .. last - first - 1];
    ensures \forall integer i; 0 <= i < last - first ==> d_first[i] == \old(first[i]);
    ensures \result == d_first + (last - first);
    exits \false; */
NodeID *std_copy_NodeID(const NodeID *first, const NodeID *last, NodeID *d_first);

/* ---- GAPBS members (bodies; proven in the run) ---- */

#define __ATOMIC_RELAXED 0

/* platform_atomics.h:30 */
/*@ requires \valid(x);
    assigns *x;
    ensures (\result != 0) <==> (\old(*x) == old_val);
    ensures \old(*x) == old_val ==> *x == new_val;
    ensures \old(*x) != old_val ==> *x == \old(*x); */
bool compare_and_swap(NodeID *x, NodeID old_val, NodeID new_val) {
  return __sync_bool_compare_and_swap_NodeID(x, old_val, new_val);
}

/* platform_atomics.h:25 */
/*@ requires \valid(x);
    assigns *x;
    ensures *x == \old(*x) + inc;
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
/*@ assigns \nothing; ensures \result == self->start_ + n; */
NodeID *pvector_NodeID_operator_index(struct pvector_NodeID *self, size_t n) { return self->start_ + n; }
/*@ assigns \nothing; ensures \result == self->start_; */
NodeID *pvector_NodeID_data(struct pvector_NodeID *self) { return self->start_; }
/*@ assigns \nothing; ensures \result == self->start_; */
NodeID *pvector_NodeID_beginp(struct pvector_NodeID *self) { return self->start_; }
/*@ assigns \nothing; ensures \result == self->end_size_; */
NodeID *pvector_NodeID_endp(struct pvector_NodeID *self) { return self->end_size_; }
/*@ assigns \nothing; ensures \result == self->start_ + n; */
SGOffset *pvector_SGOffset_operator_index(struct pvector_SGOffset *self, size_t n) { return self->start_ + n; }
/*@ assigns \nothing; ensures \result == self->start_; */
SGOffset *pvector_SGOffset_data(struct pvector_SGOffset *self) { return self->start_; }
/*@ assigns \nothing; ensures \result == self->start_; */
SGOffset *pvector_SGOffset_beginp(struct pvector_SGOffset *self) { return self->start_; }
/*@ assigns \nothing; ensures \result == self->end_size_; */
SGOffset *pvector_SGOffset_endp(struct pvector_SGOffset *self) { return self->end_size_; }

/* sliding_queue.h:63-79 */
/*@ assigns \nothing; ensures \result == self->shared; */
NodeID *SlidingQueue_NodeID_beginp(struct SlidingQueue_NodeID *self) { return self->shared; }
/*@ assigns \nothing; ensures \result == self->shared + self->shared_max_size; */
NodeID *SlidingQueue_NodeID_endp(struct SlidingQueue_NodeID *self) { return self->shared + self->shared_max_size; }
/*@ requires self->shared_out_start <= self->shared_out_end;
    assigns \nothing;
    ensures \result == self->shared_out_end - self->shared_out_start; */
size_t SlidingQueue_NodeID_size(struct SlidingQueue_NodeID *self) {
  return (size_t)((self->shared + self->shared_out_end) - (self->shared + self->shared_out_start));
}

/* sliding_queue.h:89-94 */
/*@ requires \valid(self);
    requires 1 <= given_size <= SWDB_LQUEUE_CAPACITY;
    assigns self->sq, self->local_size, self->in, self->local_queue;
    ensures self->sq == master && self->local_size == given_size && self->in == 0;
    ensures self->local_queue == &swdb_lqueue_storage[0]; */
void QueueBuffer_NodeID_QueueBuffer(struct QueueBuffer_NodeID *self, struct SlidingQueue_NodeID *master, size_t given_size) {
  self->sq = master;
  self->local_size = given_size;
  self->in = 0;
  self->local_queue = swdb_new_NodeID_array(self->local_size);
}

/* sliding_queue.h:96-98 */
/*@ assigns \nothing; */
void QueueBuffer_NodeID_destroy(struct QueueBuffer_NodeID *self) {
  swdb_delete_NodeID_array(self->local_queue);
}

/* sliding_queue.h:106-111 */
/*@ requires \valid(self) && \valid(self->sq);
    requires \separated(self, self->sq);
    requires \separated(self->local_queue + (0 .. self->in - 1),
                        self->sq->shared + (self->sq->shared_in .. self->sq->shared_in + self->in - 1));
    requires \separated(self->sq->shared + (self->sq->shared_in .. self->sq->shared_in + self->in - 1), self, self->sq);
    assigns self->in, self->sq->shared_in,
            self->sq->shared[self->sq->shared_in .. self->sq->shared_in + self->in - 1];
    ensures self->sq->shared_in == \old(self->sq->shared_in) + \old(self->in);
    ensures \forall integer i; 0 <= i < \old(self->in) ==>
              self->sq->shared[\old(self->sq->shared_in) + i] == \old(self->local_queue[i]);
    ensures self->in == 0; */
void QueueBuffer_NodeID_flush(struct QueueBuffer_NodeID *self) {
  NodeID *shared_queue = self->sq->shared;
  size_t copy_start = fetch_and_add_size_t(&self->sq->shared_in, self->in);
  std_copy_NodeID(self->local_queue, self->local_queue + self->in, shared_queue + copy_start);
  self->in = 0;
}

/* sliding_queue.h:100-104 */
/*@ requires \valid(self) && \valid(self->sq);
    requires 1 <= self->local_size && self->in <= self->local_size;
    requires \valid(self->local_queue + (0 .. self->local_size - 1));
    requires \separated(self, self->sq);
    requires \separated(self->local_queue + (0 .. self->local_size - 1), self, self->sq);
    requires \separated(self->local_queue + (0 .. self->local_size - 1),
                        self->sq->shared + (self->sq->shared_in .. self->sq->shared_in + self->in - 1));
    requires \separated(self->sq->shared + (self->sq->shared_in .. self->sq->shared_in + self->in - 1), self, self->sq);
    assigns self->in, self->local_queue[0 .. self->local_size - 1], self->sq->shared_in,
            self->sq->shared[self->sq->shared_in .. self->sq->shared_in + self->in - 1];
    behavior buffered:
      assumes self->in < self->local_size;
      ensures self->in == \old(self->in) + 1;
      ensures self->local_queue[\old(self->in)] == to_add;
      ensures \forall integer i; 0 <= i < \old(self->in) ==> self->local_queue[i] == \old(self->local_queue[i]);
      ensures self->sq->shared_in == \old(self->sq->shared_in);
    behavior flushed:
      assumes self->in == self->local_size;
      ensures self->sq->shared_in == \old(self->sq->shared_in) + \old(self->in);
      ensures \forall integer i; 0 <= i < \old(self->in) ==>
                self->sq->shared[\old(self->sq->shared_in) + i] == \old(self->local_queue[i]);
      ensures self->in == 1;
      ensures self->local_queue[0] == to_add;
    complete behaviors;
    disjoint behaviors; */
void QueueBuffer_NodeID_push_back(struct QueueBuffer_NodeID *self, NodeID to_add) {
  if (self->in == self->local_size)
    QueueBuffer_NodeID_flush(self);
  self->local_queue[self->in++] = to_add;
}

#endif
