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
/* [vector.cons] p1, [container.requirements.general] Table 83 (X u;): an empty vector. */
/*@ requires \valid(this);
    assigns *this;
    ensures std_vector_int_ptr_valid(this) && this->size == 0; */
static void std_vector_int_ptr_ctor(std_vector_int_ptr *this) { this->data = NULL; this->size = 0; this->capacity = 0; }