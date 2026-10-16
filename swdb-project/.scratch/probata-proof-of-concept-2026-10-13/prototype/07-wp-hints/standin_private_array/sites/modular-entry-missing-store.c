// Prospective same-path repeated modular entry. Undefined negative is never executed.
#include "gapbs_models.h"

/*@ requires gapbs_queue_domain(queue) && \valid(out);
    requires \separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));
    assigns *out;
    ensures write ==> *out == 17; */
void swdb_lifetime_entry(struct SlidingQueue_NodeID *queue, bool write, NodeID *out) {
  swdb_private_NodeID_array storage; /* new uninitialized function lifetime */
  struct QueueBuffer_NodeID buffer;
  QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);
  if (write) QueueBuffer_NodeID_push_back(&buffer, 17);
  *out = buffer.local_queue[0];
  QueueBuffer_NodeID_destroy(&buffer);
}

/*@ requires gapbs_queue_domain(queue) && \valid(out);
    requires \separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));
    assigns *out; */
void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {
  NodeID first;
  swdb_lifetime_entry(queue, true, &first);
  swdb_lifetime_entry(queue, false, out);
}
