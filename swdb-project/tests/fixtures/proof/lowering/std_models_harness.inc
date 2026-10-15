/* Probata PoC 24: the bounded-domain harness of std_models.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 0; n <= 4; ++n)
    for (int x = -4; x <= 4; ++x)
      for (int y = -4; y <= 4; ++y) {
        int a[4] = {x, y, x * y, x - y}, b[4] = {0, 0, 0, 0};
        int r = swdb_std_unit(a, b, n, x, y);
        printf("%d %d %d -> %d | %d %d %d %d\n", n, x, y, r, b[0], b[1], b[2], b[3]);
      }
  return 0;
}
