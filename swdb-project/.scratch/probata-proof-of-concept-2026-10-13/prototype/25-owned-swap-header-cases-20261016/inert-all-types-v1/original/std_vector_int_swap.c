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
/* [vector.special] p1, [container.requirements.general] Table 83 (a.swap(b): exchanges the contents;
   no iterator is invalidated). */
/*@ requires std_vector_int_valid(this) && std_vector_int_valid(other) && \separated(this, other);
    assigns *this, *other;
    ensures this->data == \old(other->data) && this->size == \old(other->size);
    ensures other->data == \old(this->data) && other->size == \old(this->size);
    ensures std_vector_int_valid(this) && std_vector_int_valid(other); */
static void std_vector_int_swap(std_vector_int *this, std_vector_int *other) { std_vector_int t = *this; *this = *other; *other = t; }