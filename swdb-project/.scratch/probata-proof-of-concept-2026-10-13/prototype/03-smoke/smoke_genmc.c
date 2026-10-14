/* Ticket 03 smoke check for GenMC (2026-10-14 ET): map 07's smoke.c with the input range
   enumerated. GenMC is a stateless model checker: its __VERIFIER_nondet_int returns a fixed
   sequence per thread (GenMC manual, "SV-COMP API"), so it would never try x = 41. A loop
   over [0, 100] checks the same assertion for every input map 07's precondition allows.
   Build with -DBUGGY to get a version whose assertion must fail. */
#include <assert.h>

int main(void) {
  for (int x = 0; x <= 100; x++) {
    int y = x + 1;
#ifdef BUGGY
    assert(y != 42); /* refuted by x = 41 */
#else
    assert(y > x);   /* holds for all x in [0, 100] */
#endif
  }
  return 0;
}
