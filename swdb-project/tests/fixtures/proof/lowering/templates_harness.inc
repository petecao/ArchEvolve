/* Probata PoC 24: the bounded-domain harness of templates.cc (C and C++ alike). Created: 2026-10-14 ET. */
#include <stdio.h>
int main(void) {
  for (int a = -20; a <= 20; ++a)
    for (long b = -20; b <= 20; ++b) printf("%d %ld -> %d\n", a, b, swdb_template_unit(a, b));
  return 0;
}
