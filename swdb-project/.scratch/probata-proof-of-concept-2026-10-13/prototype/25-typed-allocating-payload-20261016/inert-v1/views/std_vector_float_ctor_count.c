#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include <float.h>
typedef struct std_vector_float std_vector_float;
struct std_vector_float { float *data; size_t size; size_t capacity; };
/* swdb-std-models: the model's two check hooks (CBMC and the native harness define them first). */
#ifndef SWDB_MODEL_REQUIRE
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#endif
#ifndef SWDB_MODEL_FAIL
#define SWDB_MODEL_FAIL(name) abort()
#endif
/* swdb-std-models: the representation invariant of std_vector_float (data, size, capacity). */
/*@ predicate std_vector_float_valid(std_vector_float *v) =
      \valid(v) && \initialized(v) && v->size <= v->capacity && v->capacity <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(float) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(float)) &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
    predicate std_vector_float_readable(std_vector_float *v) =
      \valid_read(v) && \initialized(v) && v->size <= v->capacity &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
*/
/* swdb-std-models allocator (trusted: "allocation succeeds"): n fresh, valid elements. */
#ifdef __FRAMAC__
/*@ requires n >= 0;
    assigns \nothing;
    allocates \result;
    ensures \fresh(\result, n * sizeof(float)) && \valid(\result + (0 .. n - 1)); */
float *swdb_alloc_float(size_t n);
#else
static inline float *swdb_alloc_float(size_t n) { return (float *)malloc(n * sizeof(float)); }
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
/* [vector.cons] p3-p4: explicit vector(size_type n): n value-initialized elements. */
/*@ requires \valid(this) && n <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(float) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(float));
    assigns *this;
    allocates this->data;
    ensures std_vector_float_valid(this) && this->size == n;
    ensures \forall integer k; 0 <= k < n ==> this->data[k] == 0; */
static void std_vector_float_ctor_count(std_vector_float *this, size_t n) {
  this->data = NULL; this->size = 0; this->capacity = 0;
  if (n == 0) return;
  this->data = swdb_alloc_float(n);   /* allocation succeeds (assumption entry) */
  this->capacity = n;
  /*@ loop invariant 0 <= k <= n;
      loop invariant \forall integer j; 0 <= j < k ==> this->data[j] == 0;
      loop invariant \initialized(this->data + (0 .. k - 1));
      loop assigns k, this->data[0 .. n - 1];
      loop variant n - k; */
  for (size_t k = 0; k < n; ++k) this->data[k] = (float)0;
  this->size = n;
}
/* Conditional target layout; these assertions have not been executed. */
_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&
               sizeof(ptrdiff_t) == 8 && sizeof(void *) == 8 && _Alignof(void *) == 8 &&
               sizeof(float) == 4 && _Alignof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128 &&
               sizeof(std_vector_float) == 24 && _Alignof(std_vector_float) == 8 &&
               offsetof(std_vector_float, data) == 0 && offsetof(std_vector_float, size) == 8 &&
               offsetof(std_vector_float, capacity) == 16, "typed constructor target layout");
