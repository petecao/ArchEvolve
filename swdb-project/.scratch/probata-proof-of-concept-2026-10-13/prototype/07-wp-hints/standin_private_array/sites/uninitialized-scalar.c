// Prospective same-allocation-path control. Never execute undefined negatives.
#include "gapbs_models.h"

/*@ requires gapbs_queue_domain(queue) && \valid(out);
    requires \separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));
    assigns *out; */
void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {
  swdb_private_NodeID_array storage; /* no initializer: exact same producer */
  struct QueueBuffer_NodeID buffer;
  QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);
  NodeID uninitialized;
  *out = uninitialized;
  QueueBuffer_NodeID_destroy(&buffer);
}
