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