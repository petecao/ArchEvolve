/* Ticket 07 smoke check (C): one assertion over a nondeterministic input.
   Build with -DBUGGY to get a version whose assertion must fail. */
#include <assert.h>
int __VERIFIER_nondet_int(void);

int main(void) {
  int x = __VERIFIER_nondet_int();
  if (x < 0 || x > 100) return 0;
  int y = x + 1;
#ifdef BUGGY
  assert(y != 42); /* refuted by x = 41 */
#else
  assert(y > x);   /* holds for all x in [0, 100] */
#endif
  return 0;
}
