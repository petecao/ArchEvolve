// Exact normalized LLVM primitive fixture. Updated: 2026-10-06 ET.
// Independent contract fixture; no application or CPU timing evidence.
#include <cstdint>
using Vec = int64_t __attribute__((ext_vector_type(2)));
extern "C" __attribute__((noinline)) void primitives(int64_t *value, _Atomic(double) *fp,
                                                     volatile Vec *vector, volatile int64_t *ordinary, int64_t * volatile *pointer) {
  *ordinary = *ordinary + 1;
  __atomic_fetch_add(value, 1, __ATOMIC_SEQ_CST);
  __atomic_fetch_sub(value, 1, __ATOMIC_RELAXED);
  __atomic_exchange_n(value, 7, __ATOMIC_ACQ_REL);
  int64_t expected=7;
  __atomic_compare_exchange_n(value, &expected, 8, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
  expected=8;
  __atomic_compare_exchange_n(value, &expected, 9, true, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
  __c11_atomic_fetch_add(fp, 1., __ATOMIC_SEQ_CST);
  __c11_atomic_fetch_sub(fp, 1., __ATOMIC_RELAXED);
  int64_t *address=*pointer;
  *pointer=address;
  Vec copy=*vector;
  *vector=copy;
}
int main() {
  int64_t value=3; _Atomic(double) fp; __c11_atomic_init(&fp, 2.);
  Vec vector={1,2}; int64_t ordinary=0;
  int64_t *pointer=&value;
  primitives(&value,&fp,&vector,&ordinary,&pointer);
  return 0;
}
