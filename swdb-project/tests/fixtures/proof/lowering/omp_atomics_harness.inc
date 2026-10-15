/* Probata PoC 24: the bounded-domain harness of omp_atomics.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 0; n <= 4; ++n)
    for (int s = -3; s <= 3; ++s) {
      int a[4] = {s, -s, s * s - 2, 3 - s};
      printf("omp %d %d -> %d\n", n, s, swdb_omp_unit(a, n));
    }
  for (int p0 = -2; p0 <= 10; ++p0)
    for (int e0 = -2; e0 <= 10; ++e0)
      for (int v = -3; v <= 3; ++v) {
        int p = p0, e = e0;
        int r = swdb_atomics_unit(&p, &e, v);
        printf("atomics %d %d %d -> %d | %d %d\n", p0, e0, v, r, p, e);
      }
  return 0;
}
