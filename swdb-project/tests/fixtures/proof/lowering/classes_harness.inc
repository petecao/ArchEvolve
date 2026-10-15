/* Probata PoC 24: the bounded-domain harness of classes.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 0; n <= 4; ++n)
    for (int mode = 0; mode <= 2; ++mode)
      for (int seed = -3; seed <= 3; ++seed) {
        int a[4];
        for (int i = 0; i < 4; ++i) a[i] = seed * (i + 1) - i;
        int r = swdb_class_unit(a, n, mode);
        printf("%d %d %d -> %d | %d %d %d %d\n", n, mode, seed, r, a[0], a[1], a[2], a[3]);
      }
  return 0;
}
