/* 2026-10-15 ET. Original uint64 count/index/allocator arithmetic VC kernel.
   The loop-state relation supplies k<n; it is not an added original caller premise. */
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
struct t25_receiver_layout { int *data; size_t size; size_t capacity; };
_Static_assert(sizeof(int) == 4, "mapped int width");
_Static_assert(_Alignof(int) == 4, "mapped int alignment");
_Static_assert(_Alignof(struct t25_receiver_layout) == 8, "mapped receiver alignment");
_Static_assert(sizeof(size_t) == 8, "mapped size width");
_Static_assert(sizeof(void *) == 8, "mapped receiver layout");
_Static_assert(sizeof(struct t25_receiver_layout) == 24, "mapped receiver extent");
_Static_assert(offsetof(struct t25_receiver_layout, data) == 0, "mapped data field");
_Static_assert(offsetof(struct t25_receiver_layout, size) == 8, "mapped size field");
_Static_assert(offsetof(struct t25_receiver_layout, capacity) == 16, "mapped capacity field");
/*@ requires n <= 4611686018427387903 && k < n;
    assigns \nothing;
    ensures \result == k+1 && \result <= n;
*/
size_t t25v3_ctor_numeric(size_t n, size_t k) {
  size_t next = k + 1;
  size_t bytes = n * sizeof(int);
  /*@ assert allocation_size_no_wrap: (integer)n * 4 <= 18446744073709551615; */
  /*@ assert allocation_size_exact: bytes == (integer)n * 4; */
  /*@ assert scaled_index_in_range: (integer)k * 4 + 4 <= bytes; */
  /*@ assert variant_nonnegative: 0 <= (integer)n - k; */
  /*@ assert variant_decreases: 0 <= (integer)n - next < (integer)n - k; */
  return next;
}
