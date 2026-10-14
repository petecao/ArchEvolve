/* Ticket 03 smoke check for CIVL (2026-10-14 ET): map 07's smoke.c with CIVL's symbolic
   input instead of __VERIFIER_nondet_int (CIVL 1.23 has no SV-COMP mode).
   Build with -DBUGGY (civl verify -DBUGGY ...) to get a version whose assertion must fail. */
#include <assert.h>
#include <civlc.cvh>

$input int x;

int main(void) {
  if (x < 0 || x > 100) return 0;
  int y = x + 1;
#ifdef BUGGY
  assert(y != 42); /* refuted by x = 41 */
#else
  assert(y > x);   /* holds for all x in [0, 100] */
#endif
  return 0;
}
