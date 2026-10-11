/* Ticket 07 smoke check for Frama-C/WP: one assertion that needs a loop invariant
   (an unbounded proof, no loop bound). Build with -DBUGGY for a version WP must not prove. */
/*@ requires 0 <= n <= 1000000;
    assigns \nothing;
    ensures \result == n; */
int count_up(int n) {
  int i = 0;
  /*@ loop invariant 0 <= i <= n;
      loop assigns i;
      loop variant n - i; */
  while (i < n) i++;
#ifdef BUGGY
  /*@ assert i == n + 1; */
#else
  /*@ assert i == n; */
#endif
  return i;
}
