// Prospective same-allocation-path control. Never execute undefined negatives.
#include "gapbs_models.h"

/*@ requires gapbs_queue_domain(queue) && \valid(out);
    requires \separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));
    requires queue->shared_in < queue->shared_max_size;
    assigns *out, queue->shared_in, queue->shared[queue->shared_in];
    ensures *out == 17; */
void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {
  swdb_private_NodeID_array storage; /* no initializer: exact same producer */
  struct QueueBuffer_NodeID buffer;
  QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);
  QueueBuffer_NodeID_push_back(&buffer, 17);
  QueueBuffer_NodeID_flush(&buffer);
  *out = buffer.local_queue[0];
  QueueBuffer_NodeID_destroy(&buffer);
}
