#include <stddef.h>
#include <limits.h>
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
/* [vector.special] p1, [container.requirements.general] Table 83 (a.swap(b): exchanges the contents;
   no iterator is invalidated). */
/*@ requires std_vector_float_valid(this) && std_vector_float_valid(other) && \separated(this, other);
    assigns *this, *other;
    ensures this->data == \old(other->data) && this->size == \old(other->size);
    ensures other->data == \old(this->data) && other->size == \old(this->size);
    ensures std_vector_float_valid(this) && std_vector_float_valid(other); */
static void std_vector_float_swap(std_vector_float *this, std_vector_float *other) { std_vector_float t = *this; *this = *other; *other = t; }

/* Target checks are pending execution; logical offsets do not assert a native C++ ABI. */
_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&
               sizeof(void *) == 8 && _Alignof(void *) == 8 &&
               sizeof(std_vector_float) == 24 && _Alignof(std_vector_float) == 8 &&
               offsetof(std_vector_float, data) == 0 && offsetof(std_vector_float, size) == 8 &&
               offsetof(std_vector_float, capacity) == 16, "owned header layout");
