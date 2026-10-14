/* Ticket 03 smoke check for SAW (2026-10-14 ET): map 07's smoke.c as a function, because
   SAW verifies a function against a spec instead of running main. The input x is the
   symbolic argument (smoke_saw.saw); the assertion is the same as in map 07.
   Build with -DBUGGY to get a version whose assertion must fail. */
#include <assert.h>

void smoke(int x) {
  if (x < 0 || x > 100) return;
  int y = x + 1;
#ifdef BUGGY
  assert(y != 42); /* refuted by x = 41 */
#else
  assert(y > x);   /* holds for all x in [0, 100] */
#endif
}
