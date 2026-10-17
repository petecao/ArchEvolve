// Prospective same-path lexical retirement/reentry. Undefined negative is never executed.
#include "gapbs_models.h"

/*@ requires gapbs_queue_domain(queue) && \valid(out);
    requires \separated(out, queue, queue->shared + (0 .. queue->shared_max_size - 1));
    assigns *out; */
void swdb_allocation_site(struct SlidingQueue_NodeID *queue, NodeID *out) {
  for (unsigned lifetime = 0; lifetime < 2; ++lifetime) {
    swdb_private_NodeID_array storage; /* new uninitialized lifetime each iteration */
    struct QueueBuffer_NodeID buffer;
    QueueBuffer_NodeID_QueueBuffer(&buffer, queue, 16384, &storage);
    if (lifetime == 0) QueueBuffer_NodeID_push_back(&buffer, 17);
    *out = buffer.local_queue[0];
    QueueBuffer_NodeID_destroy(&buffer);
  }
}
