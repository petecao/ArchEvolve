/* C lowering of vector_realloc_v3_no_growth from vector_reallocation_v3.cc (sha256 1172e62dbff5076d25471285afcfa17927707dbe6fae121d9570109d39e62b57) by swdb-c-lowering 9 (kept-names.3), clang 22.1.8. Generated: do not edit. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
typedef struct std_vector_int std_vector_int;
struct std_vector_int { int *data; size_t size; size_t capacity; };
/* swdb-anchor ghost.globals */
/* swdb-std-models: the model's two check hooks (CBMC and the native harness define them first). */
#ifndef SWDB_MODEL_REQUIRE
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#endif
#ifndef SWDB_MODEL_FAIL
#define SWDB_MODEL_FAIL(name) abort()
#endif
/* swdb-std-models: the representation invariant of std_vector_int (data, size, capacity). */
/*@ predicate std_vector_int_valid(std_vector_int *v) =
      \valid(v) && \initialized(v) && v->size <= v->capacity && v->capacity <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int)) &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
    predicate std_vector_int_readable(std_vector_int *v) =
      \valid_read(v) && \initialized(v) && v->size <= v->capacity &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
*/
/* swdb-std-models allocator (trusted: "allocation succeeds"): n fresh, valid elements. */
#ifdef __FRAMAC__
/*@ requires n >= 0;
    assigns \nothing;
    allocates \result;
    ensures \fresh(\result, n * sizeof(int)) && \valid(\result + (0 .. n - 1)); */
int *swdb_alloc_int(size_t n);
#else
static inline int *swdb_alloc_int(size_t n) { return (int *)malloc(n * sizeof(int)); }
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
/*@ requires \valid(this) && n <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int));
    assigns *this;
    allocates this->data;
    ensures std_vector_int_valid(this) && this->size == n;
    ensures \forall integer k; 0 <= k < n ==> this->data[k] == value; */
static void std_vector_int_ctor_count_value(std_vector_int *this, size_t n, int value) {
  this->data = NULL; this->size = 0; this->capacity = 0;
  if (n == 0) return;
  this->data = swdb_alloc_int(n);   /* allocation succeeds (assumption entry) */
  this->capacity = n;
  /*@ loop invariant 0 <= k <= n;
      loop invariant \forall integer j; 0 <= j < k ==> this->data[j] == value;
      loop invariant \initialized(this->data + (0 .. k - 1));
      loop assigns k, this->data[0 .. n - 1];
      loop variant n - k; */
  for (size_t k = 0; k < n; ++k) this->data[k] = value;
  this->size = n;
}
/* [container.requirements.general] Table 83 (a.~X()): destroys the elements, frees all memory. */
/*@ requires std_vector_int_valid(this) && (this->capacity == 0 || \freeable(this->data));
    assigns \nothing;
    frees this->data;
    ensures \old(this->capacity) > 0 ==> !\valid(\old(this->data)); */
static void std_vector_int_dtor(std_vector_int *this) { swdb_free(this->data); }
/* [vector.data] p1: [data(), data() + size()) is a valid range. */
/*@ requires std_vector_int_readable(this);
    assigns \nothing;
    ensures \result == this->data; */
static int *std_vector_int_data(const std_vector_int *this) { return this->data; }
/* swdb-std-models helper: reallocation to capacity cap (allocate, move the elements, free the old buffer). */
/*@ requires std_vector_int_valid(this) && this->size <= cap && cap > this->capacity && cap <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int));
    requires this->capacity == 0 || \freeable(this->data);
    assigns *this;
    allocates this->data;
    frees this->data;
    ensures std_vector_int_valid(this) && this->capacity == cap && this->size == \old(this->size);
    ensures \forall integer k; 0 <= k < this->size ==> this->data[k] == \old(this->data[k]);
    ensures \old(this->capacity) > 0 ==> !\valid(\old(this->data)); */
static void std_vector_int_grow(std_vector_int *this, size_t cap) {
  int *fresh = swdb_alloc_int(cap);   /* allocation succeeds (assumption entry) */
  /*@ loop invariant 0 <= k <= this->size;
      loop invariant \forall integer j; 0 <= j < k ==> fresh[j] == this->data[j];
      loop invariant \initialized(fresh + (0 .. k - 1));
      loop assigns k, fresh[0 .. cap - 1];
      loop variant this->size - k; */
  for (size_t k = 0; k < this->size; ++k) fresh[k] = this->data[k];
  swdb_free(this->data);
  this->data = fresh;
  this->capacity = cap;
}
/* [vector.capacity] p3-p5: reserve(n): if n > capacity(), reallocation happens (capacity() >= n after);
   n > max_size() throws length_error: an exception, so n <= max_size() is the caller's obligation. */
/*@ requires std_vector_int_valid(this) && n <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int));
    assigns *this;
    allocates this->data;
    frees this->data;
    ensures std_vector_int_valid(this) && this->size == \old(this->size) && this->capacity >= n;
    ensures \forall integer k; 0 <= k < this->size ==> this->data[k] == \old(this->data[k]);
    ensures n <= \old(this->capacity) ==> this->data == \old(this->data);
    ensures n > \old(this->capacity) && \old(this->capacity) > 0 ==> !\valid(\old(this->data)); */
static void std_vector_int_reserve(std_vector_int *this, size_t n) {
  if (n > this->capacity) std_vector_int_grow(this, n);
}
int vector_realloc_v3_no_growth(int n);
/* swdb-anchor vector_realloc_v3_no_growth.contract */
/*@ requires 0 <= n;
    assigns \nothing;
    ensures \result == (n > 0 ? 7 : 0); */
int vector_realloc_v3_no_growth(int n) {
  /* swdb-anchor vector_realloc_v3_no_growth.entry */
  /* swdb-anchor vector_realloc_v3_no_growth.s1.before */
  std_vector_int v;
  std_vector_int_ctor_count_value(&v, (unsigned long)n, 7);
  /* swdb-anchor vector_realloc_v3_no_growth.s1.after */
  /* swdb-anchor vector_realloc_v3_no_growth.s2.before */
  int *saved = std_vector_int_data(&v);
  /* swdb-anchor vector_realloc_v3_no_growth.s2.after */
  /* swdb-anchor vector_realloc_v3_no_growth.s3.before */
  std_vector_int_reserve(&v, (unsigned long)n);
  /* swdb-anchor vector_realloc_v3_no_growth.s3.after */
  /* swdb-anchor vector_realloc_v3_no_growth.s4.before */
  {
    int swdb_return = (n > 0) ? (*saved) : 0;
    std_vector_int_dtor(&v);
    return swdb_return;
  }
  /* swdb-anchor vector_realloc_v3_no_growth.s4.after */
  /* swdb-anchor vector_realloc_v3_no_growth.s5.before */
  std_vector_int_dtor(&v);
  /* swdb-anchor vector_realloc_v3_no_growth.s5.after */
}
