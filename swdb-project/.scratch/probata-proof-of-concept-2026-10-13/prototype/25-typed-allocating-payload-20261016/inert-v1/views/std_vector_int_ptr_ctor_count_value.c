#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include <float.h>
typedef struct std_vector_int_ptr std_vector_int_ptr;
struct std_vector_int_ptr { int * *data; size_t size; size_t capacity; };
/* swdb-std-models: the model's two check hooks (CBMC and the native harness define them first). */
#ifndef SWDB_MODEL_REQUIRE
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#endif
#ifndef SWDB_MODEL_FAIL
#define SWDB_MODEL_FAIL(name) abort()
#endif
/* swdb-std-models: the representation invariant of std_vector_int_ptr (data, size, capacity). */
/*@ predicate std_vector_int_ptr_valid(std_vector_int_ptr *v) =
      \valid(v) && \initialized(v) && v->size <= v->capacity && v->capacity <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int *) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int *)) &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
    predicate std_vector_int_ptr_readable(std_vector_int_ptr *v) =
      \valid_read(v) && \initialized(v) && v->size <= v->capacity &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
*/
/* swdb-std-models allocator (trusted: "allocation succeeds"): n fresh, valid elements. */
#ifdef __FRAMAC__
/*@ requires n >= 0;
    assigns \nothing;
    allocates \result;
    ensures \fresh(\result, n * sizeof(int *)) && \valid(\result + (0 .. n - 1)); */
int * *swdb_alloc_int_ptr(size_t n);
#else
static inline int * *swdb_alloc_int_ptr(size_t n) { return (int * *)malloc(n * sizeof(int *)); }
#endif
/* swdb-std-models deallocator (trusted with the allocator). */
#ifdef __FRAMAC__
/*@ requires p == \null || \freeable(p);
    assigns \nothing;
    frees p; */
void swdb_free(void *p);
#else
static inline void swdb_free(void *p) { free(p); }
#endif
/* [vector.cons] p6-p7: vector(size_type n, const T& value): n copies of value. */
/*@ requires \valid(this) && n <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int *) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int *));
    assigns *this;
    allocates this->data;
    ensures std_vector_int_ptr_valid(this) && this->size == n;
    ensures \forall integer k; 0 <= k < n ==> this->data[k] == value; */
static void std_vector_int_ptr_ctor_count_value(std_vector_int_ptr *this, size_t n, int *value) {
  this->data = NULL; this->size = 0; this->capacity = 0;
  if (n == 0) return;
  this->data = swdb_alloc_int_ptr(n);   /* allocation succeeds (assumption entry) */
  this->capacity = n;
  /*@ loop invariant 0 <= k <= n;
      loop invariant \forall integer j; 0 <= j < k ==> this->data[j] == value;
      loop invariant \initialized(this->data + (0 .. k - 1));
      loop assigns k, this->data[0 .. n - 1];
      loop variant n - k; */
  for (size_t k = 0; k < n; ++k) this->data[k] = value;
  this->size = n;
}
/* Conditional target layout; these assertions have not been executed. */
_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&
               sizeof(ptrdiff_t) == 8 && sizeof(void *) == 8 && _Alignof(void *) == 8 &&
               sizeof(int *) == 8 && _Alignof(int *) == 8 &&
               sizeof(std_vector_int_ptr) == 24 && _Alignof(std_vector_int_ptr) == 8 &&
               offsetof(std_vector_int_ptr, data) == 0 && offsetof(std_vector_int_ptr, size) == 8 &&
               offsetof(std_vector_int_ptr, capacity) == 16, "typed constructor target layout");
