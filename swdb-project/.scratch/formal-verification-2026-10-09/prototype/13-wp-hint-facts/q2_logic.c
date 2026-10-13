/* Q2: can a logic definition with a body, a recursive logic function, or an
   inductive predicate prove \false? Each case defines symbols, then f() uses them in
   one assertion (USE). f's ensures is false (f returns 0), so it is proved only if the
   assertion makes the context inconsistent. Case 9 shows WP's context filtering.
   Select a case with -cpp-extra-args="-DCASE=<n>". See run.sh. */

#if CASE == 1   /* control: non-recursive definitions */
//@ logic integer sq(integer x) = x * x;
//@ predicate is_pos(integer x) = x > 0;
//@ lemma L_sq: \forall integer x; is_pos(x) ==> sq(x) > 0;
#define USE is_pos(sq(1))
#elif CASE == 2 /* recursive logic function that does not terminate: bad(x) = bad(x) + 1 */
//@ logic integer bad(integer x) = bad(x) + 1;
#define USE bad(0) == 42
#elif CASE == 3 /* recursive predicate with negative self-reference: p(x) <==> !p(x) */
//@ predicate pbad(integer x) = !pbad(x);
#define USE pbad(0)
#elif CASE == 4 /* non-positive inductive: nb occurs negatively in a hypothesis */
/*@ inductive nb(integer x) {
      case c1: \forall integer x; !nb(x) ==> nb(x);
    } */
#define USE nb(0)
#elif CASE == 5 /* inductive whose only case does not conclude with the predicate */
/*@ inductive ib(integer x) {
      case c1: \false;
    } */
#define USE ib(0)
#elif CASE == 6 /* control: positive (Horn) inductive, ACSL manual example 2.42 */
/*@ inductive is_gcd(integer a, integer b, integer d) {
      case gcd_zero: \forall integer n; is_gcd(n,0,n);
      case gcd_succ: \forall integer a,b,d; is_gcd(b, a % b, d) ==> is_gcd(a,b,d);
    } */
#define USE is_gcd(4,0,4)
#elif CASE == 7 /* mutual recursion: mf(x) = mg(x) + 1, mg(x) = mf(x) */
/*@ axiomatic Mutual {
      logic integer mf(integer x) = mg(x) + 1;
      logic integer mg(integer x) = mf(x);
    } */
#define USE mf(0) == 42
#elif CASE == 8 /* control: terminating recursive definition */
//@ logic integer fact(integer n) = n <= 0 ? 1 : n * fact(n - 1);
#define USE fact(3) == 6
#elif CASE == 9 /* context filtering: bad() plus a lemma \false that does not mention it */
//@ logic integer bad(integer x) = bad(x) + 1;
//@ lemma L_false: \false;
#endif

#if CASE != 9
/*@ assigns \nothing;
    ensures \result == 1; */
int f(void) {
  //@ assert USE;
  return 0;
}
#endif
