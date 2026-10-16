#include <stddef.h>
#include <limits.h>
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
/* [container.requirements.general] Table 83 (X u(rv);): u holds rv's former value; rv is left valid. */
/*@ requires \valid(this) && std_vector_int_valid(other) && \separated(this, other);
    assigns *this, *other;
    ensures std_vector_int_valid(this) && std_vector_int_valid(other);
    ensures this->data == \old(other->data) && this->size == \old(other->size); */
static void std_vector_int_move_ctor(std_vector_int *this, std_vector_int *other) {
  *this = *other;
  other->data = NULL; other->size = 0; other->capacity = 0;
}

/* Target checks are pending execution; logical offsets do not assert a native C++ ABI. */
_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&
               sizeof(void *) == 8 && _Alignof(void *) == 8 &&
               sizeof(std_vector_int) == 24 && _Alignof(std_vector_int) == 8 &&
               offsetof(std_vector_int, data) == 0 && offsetof(std_vector_int, size) == 8 &&
               offsetof(std_vector_int, capacity) == 16, "owned header layout");
