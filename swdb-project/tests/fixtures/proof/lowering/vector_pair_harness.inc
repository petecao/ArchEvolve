/* Probata PoC 25: the bounded-domain harness of vector_pair.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 0; n <= 5; ++n)
    for (int x = -3; x <= 3; ++x)
      for (int y = -3; y <= 3; ++y) {
        int a[5] = {x, y, x * y, x - y, y - x};
        int r = swdb_vector_unit(a, n, x + y);
        printf("%d %d %d -> %d\n", n, x, y, r);
      }
  return 0;
}
