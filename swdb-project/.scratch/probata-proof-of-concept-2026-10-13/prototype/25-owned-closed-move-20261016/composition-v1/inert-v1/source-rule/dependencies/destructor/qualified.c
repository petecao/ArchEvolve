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
/* Explicit v3 unary reallocation domain. It does not grant exclusive ownership.
   Distinct allocation bases are required: byte-disjoint ranges can share a free.
   This predicate's qualified proof scope also requires the source image of initialized int
   objects in the selected WP Typed integer chunk. Raw address validity and
   initialized bytes alone do not establish effective-type safety. Callers must
   discharge the typed-object image from admitted source constructions/stores;
   opaque raw storage and type-punning remain unsupported. Destruction does not
   use this predicate or load buffer elements, and retains its broad domain. */
/*@ predicate std_vector_int_reallocatable_v3(std_vector_int *v) =
      std_vector_int_valid(v) &&
      (v->capacity == 0 || (\freeable(v->data) &&
        \base_addr(v) != \base_addr(v->data)));
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
/* [container.requirements.general] Table 83 (a.~X()): destroys the elements, frees all memory. */
/*@ requires std_vector_int_valid(this) && (this->capacity == 0 || \freeable(this->data));
    assigns \nothing;
    frees this->data;
    ensures \old(this->capacity) > 0 ==> !\valid(\old(this->data)); */
static void std_vector_int_realloc_v3_dtor(std_vector_int *this) { swdb_free(this->data); }