/* Probata PoC 24: the bounded-domain harness of new_array.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int n = 1; n <= 40; ++n)
    for (int k = -5; k <= 5; ++k) printf("%d %d -> %d\n", n, k, swdb_new_unit(n, k));
  return 0;
}
