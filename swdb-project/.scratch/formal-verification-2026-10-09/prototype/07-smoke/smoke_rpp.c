/* Ticket 07 smoke check for RPP: a relational property over two calls (monotonicity).
   Build with -DBUGGY for a version whose relational property is false. */
/*@ requires 0 <= x <= 1000;
    assigns \result \from x; */
int bump(int x) {
#ifdef BUGGY
  return x == 7 ? 0 : x + 1;
#else
  return x + 1;
#endif
}

/*@ relational
      \forall int a, b; 0 <= a <= 1000 && 0 <= b <= 1000 && a < b ==>
        \callpure(bump, a) < \callpure(bump, b); */
