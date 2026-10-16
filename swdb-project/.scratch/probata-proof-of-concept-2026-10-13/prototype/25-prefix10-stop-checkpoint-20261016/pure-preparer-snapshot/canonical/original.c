typedef struct std_vector_int std_vector_int;
struct std_vector_int { int *data; size_t size; size_t capacity; };
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