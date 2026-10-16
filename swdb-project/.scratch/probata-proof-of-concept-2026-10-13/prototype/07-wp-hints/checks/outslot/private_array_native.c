/* Defined native executions only. All payload reads follow actual writes. */
#include "gapbs_models.h"
#include <assert.h>

void __sync_bool_compare_and_swap_NodeID_out(NodeID *p, NodeID old, NodeID value, bool *out) {
  *out = *p == old; if (*out) *p = value;
}
void __atomic_load_n_NodeID_out(const NodeID *p, int order, NodeID *out) { (void)order; *out = *p; }
void __sync_fetch_and_add_size_t_out(size_t *p, size_t n, size_t *out) { *out = *p; *p += n; }
void std_copy_NodeID_out(const NodeID *first, const NodeID *last, NodeID *dest, size_t count, NodeID **out) {
  assert(last == first + count);
  for (size_t i = 0; i < count; ++i) dest[i] = first[i];
  *out = dest + count;
}

int main(void) {
  NodeID shared[SWDB_LQUEUE_CAPACITY + 1];
  struct SlidingQueue_NodeID queue = {shared, 0, 0, 0, SWDB_LQUEUE_CAPACITY + 1};
  {
    NodeID storage[SWDB_LQUEUE_CAPACITY]; /* no initializer */
    struct QueueBuffer_NodeID buffer;
    QueueBuffer_NodeID_QueueBuffer(&buffer, &queue, SWDB_LQUEUE_CAPACITY, &storage);
    assert(buffer.local_queue == storage && buffer.local_size == SWDB_LQUEUE_CAPACITY && buffer.in == 0);
    for (unsigned i = 0; i < SWDB_LQUEUE_CAPACITY + 1; ++i)
      QueueBuffer_NodeID_push_back(&buffer, (NodeID)(3 * i + 7));
    assert(queue.shared_in == SWDB_LQUEUE_CAPACITY && buffer.in == 1);
    QueueBuffer_NodeID_flush(&buffer);
    assert(queue.shared_in == SWDB_LQUEUE_CAPACITY + 1 && buffer.in == 0);
    for (unsigned i = 0; i < SWDB_LQUEUE_CAPACITY + 1; ++i)
      assert(shared[i] == (NodeID)(3 * i + 7));
    // Initialization history is retained across flush/reset.
    assert(buffer.local_queue[0] == (NodeID)(3 * SWDB_LQUEUE_CAPACITY + 7));
    QueueBuffer_NodeID_destroy(&buffer);
  } /* actual automatic-object retirement, immediately after destructor marker */
  return 0;
}
