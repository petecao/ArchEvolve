/* Q7: other constructs that may add an unproved hypothesis.
   In every case the final ensures/assert is false for the real code.
   Select a case with -cpp-extra-args="-DCASE=<n>". See run.sh. */
int x;

#if CASE == 1   /* ghost function declared without a body: its contract is trusted;
                   a ghost function with a body gets its requires checked at the call */
/*@ ghost
  /@ assigns \nothing; ensures \result == 42; @/
  int g_nobody(int v);
  /@ requires v > 100; assigns \nothing; ensures \result == v; @/
  int g_body(int v) { return v; }
*/
/*@ assigns \nothing; ensures E1: \result == 42; */
int f(void) {
  //@ ghost int r = g_nobody(0);
  //@ ghost int s = g_body(0);
  //@ assert A1: r == 42;
  return 0;
}
#elif CASE == 2 /* recursive ghost "lemma function" without decreases: partial correctness */
/*@ ghost
  /@ assigns \nothing; ensures \false; @/
  void lf(void) { lf(); }
*/
/*@ assigns \nothing; ensures E2: \result == 42; */
int f(void) { //@ ghost lf();
  return 0; }
#elif CASE == 3 /* loop variant with a general measure whose relation is not well-founded */
//@ predicate Rtrue(integer a, integer b) = \true;
/*@ assigns \nothing; ensures E3: \result == 42; */
int f(void) {
  int i = 0;
  /*@ loop invariant i == 0; loop assigns i; loop variant i for Rtrue; */
  while (1) { }
  return i;
}
#elif CASE == 4 /* \from in assigns: is it checked? (k ignores a, depends on b) */
/*@ assigns \result \from a; */
int k(int a, int b) { return b; }
/*@ assigns \nothing; */
void f(void) { int r = k(1, 2); }
#elif CASE == 5 /* volatile clause: is the reader's contract used for a volatile read? */
volatile int v;
/*@ assigns \nothing; ensures \result == 7; */
int rd(volatile int *p);
//@ volatile v reads rd;
/*@ assigns \nothing; ensures E5: \result == 7; */
int f(void) { return v; }
#elif CASE == 6 /* @calls naming the wrong target of a function pointer */
/*@ assigns \nothing; ensures \result == 0; */
int g0(void) { return 0; }
/*@ assigns \nothing; ensures \result == 42; */
int g42(void) { return 42; }
/*@ assigns \nothing; ensures E6: \result == 42; */
int f(void) {
  int (*fp)(void) = g0;
  int r;
  //@ calls g42;
  r = fp();
  return r;
}
#elif CASE == 7 /* import a Why3 theory: its lemmas/axioms enter the context with no VC */
//@ import \wp::why3: number::Gcd;
/*@ assigns \nothing; */
void f(void) { //@ assert A7b: \forall integer a, b; Gcd::gcd(a, b) >= 0;  // = axiom gcd_nonneg
               //@ assert A7: Gcd::gcd(4, 6) == 2;
}
#elif CASE == 8 /* global invariant: assumed, checked, or ignored? */
//@ global invariant GI: x == 5;
/*@ assigns \nothing; ensures E8: \result == 5; */
int f(void) { return x; }
#elif CASE == 9 /* statement contract (WP: "not supported"): is its ensures assumed? */
/*@ assigns x; ensures E9: x == 42; */
void f(void) {
  /*@ assigns x; ensures SC: x == 42; */
  { x = 0; }
}
#endif
