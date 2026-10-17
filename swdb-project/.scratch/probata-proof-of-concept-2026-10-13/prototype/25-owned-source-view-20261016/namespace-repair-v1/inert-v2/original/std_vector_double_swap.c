typedef struct std_vector_double std_vector_double;
struct std_vector_double { double *data; size_t size; size_t capacity; };
/* swdb-std-models: the model's two check hooks (CBMC and the native harness define them first). */
#ifndef SWDB_MODEL_REQUIRE
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#endif
#ifndef SWDB_MODEL_FAIL
#define SWDB_MODEL_FAIL(name) abort()
#endif
/* swdb-std-models: the representation invariant of std_vector_double (data, size, capacity). */
/*@ predicate std_vector_double_valid(std_vector_double *v) =
      \valid(v) && \initialized(v) && v->size <= v->capacity && v->capacity <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(double) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(double)) &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
    predicate std_vector_double_readable(std_vector_double *v) =
      \valid_read(v) && \initialized(v) && v->size <= v->capacity &&
      (v->capacity == 0 ? v->data == \null : \valid(v->data + (0 .. v->capacity - 1))) &&
      \initialized(v->data + (0 .. v->size - 1));
*/
/* [vector.special] p1, [container.requirements.general] Table 83 (a.swap(b): exchanges the contents;
   no iterator is invalidated). */
/*@ requires std_vector_double_valid(this) && std_vector_double_valid(other) && \separated(this, other);
    assigns *this, *other;
    ensures this->data == \old(other->data) && this->size == \old(other->size);
    ensures other->data == \old(this->data) && other->size == \old(this->size);
    ensures std_vector_double_valid(this) && std_vector_double_valid(other); */
static void std_vector_double_swap(std_vector_double *this, std_vector_double *other) { std_vector_double t = *this; *this = *other; *other = t; }