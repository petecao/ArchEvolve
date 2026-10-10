// Independent intrinsic semantics fixture. Updated: 2026-10-06 ET.
#include <cstdint>
#include <cstdio>
#include <limits>
inline uint64_t add_one(const uint64_t *__restrict x,uint64_t *__restrict y) {
  *y=*x+1;
  return *y;
}
extern "C" __attribute__((noinline)) uint64_t intrinsic_math(uint64_t a,uint64_t b,const uint64_t *x,uint64_t *y) {
  uint64_t product;
  bool overflow=__builtin_mul_overflow(a,b,&product);
  uint64_t added=add_one(x,y);
  std::puts("intrinsic fixture");
  return __builtin_expect(overflow,0)?added:product+added;
}
int main() {
  uint64_t x=2,y=0;
  return intrinsic_math(7,9,&x,&y)==66 &&
    intrinsic_math(std::numeric_limits<uint64_t>::max(),2,&x,&y)==3 ? 0 : 1;
}
