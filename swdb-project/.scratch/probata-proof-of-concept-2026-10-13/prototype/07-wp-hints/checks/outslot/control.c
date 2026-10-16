/* Public ABI behavior control. Independent expected values, not a proof. */
#include "gapbs_models.h"
#include <assert.h>
#include <string.h>

static unsigned cas_calls;
void __sync_bool_compare_and_swap_NodeID_out(NodeID *p, NodeID old, NodeID value, bool *out) {
  ++cas_calls;
  *out = *p == old;
  if (*out) *p = value;
}
void __atomic_load_n_NodeID_out(const NodeID *p, int order, NodeID *out) {
  (void)order; *out = *p;
}
void __sync_fetch_and_add_size_t_out(size_t *p, size_t n, size_t *out) {
  *out = *p; *p += n;
}
void swdb_new_NodeID_array_out(size_t n, NodeID **out) {
  assert(n <= SWDB_LQUEUE_CAPACITY); *out = swdb_lqueue_storage;
}
void swdb_delete_NodeID_array(NodeID *p) { assert(p == swdb_lqueue_storage); }
void std_copy_NodeID_out(const NodeID *first, const NodeID *last, NodeID *dst,
                        size_t count, NodeID **out) {
  assert(last == first + count);
  for (size_t i = 0; i < count; ++i) dst[i] = first[i];
  *out = dst + count;
}

int main(void) {
  NodeID data[5] = {-7, 11, 23, 37, 41};
  struct pvector_NodeID pv = {data, data + 5, data + 5};
  NodeID *p;
  pvector_NodeID_operator_index_out(&pv, 2, &p); assert(p == data + 2 && *p == 23);
  pvector_NodeID_data_out(&pv, &p); assert(p == data);
  pvector_NodeID_beginp_out(&pv, &p); assert(p == data);
  pvector_NodeID_endp_out(&pv, &p); assert(p == data + 5);
  SGOffset offsets[3] = {0, 2, 5};
  struct pvector_SGOffset vo = {offsets, offsets + 3, offsets + 3};
  SGOffset *op;
  pvector_SGOffset_operator_index_out(&vo, 1, &op); assert(op == offsets + 1 && *op == 2);
  pvector_SGOffset_data_out(&vo, &op); assert(op == offsets);
  pvector_SGOffset_beginp_out(&vo, &op); assert(op == offsets);
  pvector_SGOffset_endp_out(&vo, &op); assert(op == offsets + 3);
  bool claimed;
  compare_and_swap_out(data, -7, 9, &claimed); assert(claimed && data[0] == 9);
  compare_and_swap_out(data, -7, 15, &claimed); assert(!claimed && data[0] == 9 && cas_calls == 2);
  size_t n = SIZE_MAX - 1, prior;
  fetch_and_add_size_t_out(&n, 4, &prior); assert(prior == SIZE_MAX - 1 && n == 2);
  std_min_size_t_out(8, 3, &n); assert(n == 3);
  int tid; omp_get_thread_num_out(&tid); assert(tid == 0);
  NodeID shared[8] = {17, 19};
  struct SlidingQueue_NodeID sq = {shared, 2, 0, 2, 8};
  SlidingQueue_NodeID_beginp_out(&sq, &p); assert(p == shared);
  SlidingQueue_NodeID_endp_out(&sq, &p); assert(p == shared + 8);
  SlidingQueue_NodeID_size_out(&sq, &n); assert(n == 2);
  struct QueueBuffer_NodeID qb;
  QueueBuffer_NodeID_QueueBuffer(&qb, &sq, 2);
  QueueBuffer_NodeID_push_back(&qb, 29);
  QueueBuffer_NodeID_push_back(&qb, 31);
  QueueBuffer_NodeID_push_back(&qb, 43);
  assert(sq.shared_in == 4 && shared[2] == 29 && shared[3] == 31 && qb.in == 1);
  QueueBuffer_NodeID_flush(&qb);
  assert(sq.shared_in == 5 && shared[4] == 43 && qb.in == 0);
  QueueBuffer_NodeID_destroy(&qb);
  return 0;
}
