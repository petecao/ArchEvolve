/* Probata PoC 21: the C-versus-C++ differential harness for core_subset.cc (pattern of
   prototype/06c-cbmc/faith/). Included after the C++ source (compiled as C++) and after its C
   lowering (compiled as C); both print one line per input, and the two outputs must be identical.
   Created: 2026-10-14 ET. Plain C, so it means the same in both languages. */
#include <stdio.h>
int main(void) {
  int a[4];
  int32_t out[4];
  for (int seed = 0; seed < 4000; ++seed) {
    unsigned x = (unsigned)seed * 2654435761u;
    int n = (int)(x % 5u);
    for (int k = 0; k < 4; ++k) {
      a[k] = (int)((x >> (3 * k)) % 23u) - 11;
      out[k] = -99;
    }
    int r = swdb_core_kernel(a, n, out, (size_t)(x % 4u));
    printf("%d %d %d %d %d %d %d\n", seed, r, (int)out[0], (int)out[1], (int)out[2], (int)out[3],
           swdb_core_clamp(a[0], -3, 3));
  }
  return 0;
}
