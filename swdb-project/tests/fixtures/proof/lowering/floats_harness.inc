/* Probata PoC 24: the bounded-domain harness of floats.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 0; n <= 4; ++n)
    for (int s = -30; s <= 30; ++s) {
      double a[4] = {s * 0.1, -s * 1.5, s * s * 0.03125, 7.0 / (s + 37)};
      printf("%d %d -> %.17g\n", n, s, swdb_float_unit(a, n, (float)s / 3.0f));
    }
  return 0;
}
