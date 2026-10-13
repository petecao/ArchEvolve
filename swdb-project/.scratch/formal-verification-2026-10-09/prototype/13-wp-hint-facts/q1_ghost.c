/* Q1: does the Frama-C 33 kernel reject ghost code that interferes with real code?
   Each case is selected with -cpp-extra-args="-DCASE=<n>". See run.sh. */
int x;          /* non-ghost global */
int a[4];       /* non-ghost array */
//@ ghost int g;

void incr(void) { x++; }        /* non-ghost function with a side effect */
int pure(int v) { return v + 1; } /* non-ghost function, no side effect */

#if CASE == 1   /* (a) ghost write to a non-ghost global */
void f(void) { //@ ghost x = 1;
}
#elif CASE == 2 /* (a) ghost write to a non-ghost array element */
void f(void) { //@ ghost a[0] = 1;
}
#elif CASE == 3 /* (a) ghost pointer to non-ghost memory, then a write through it */
void f(void) {
  //@ ghost int *p = &x;
  //@ ghost *p = 0;
}
#elif CASE == 4 /* (a) ghost write through a non-ghost pointer parameter */
void f(int *q) { //@ ghost *q = 0;
}
#elif CASE == 5 /* (a) cast a non-ghost address to a pointer-to-ghost, then write */
void f(void) {
  //@ ghost int \ghost *p = (int \ghost *)&x;
  //@ ghost *p = 0;
}
#elif CASE == 6 /* (b) ghost break out of a non-ghost loop */
void f(int n) {
  for (int i = 0; i < n; i++) {
    //@ ghost break;
  }
}
#elif CASE == 7 /* (b) ghost return in a non-ghost function */
int f(int v) {
  //@ ghost return 0;
  return v;
}
#elif CASE == 8 /* (b) ghost else branch that returns (ACSL manual example 2.69) */
int f(int v) {
  //@ ghost int z = v;
  if (v > 0) { return v; }
  //@ ghost else { z++; return v; }
  return v + 1;
}
#elif CASE == 9 /* (b) ghost goto out of a non-ghost block */
int f(int v) {
  { //@ ghost goto out;
    v++; }
 out:
  return v;
}
#elif CASE == 10 /* (c) ghost call to a non-ghost function with a side effect */
void f(void) { //@ ghost incr();
}
#elif CASE == 11 /* (c) ghost call to a non-ghost pure function */
void f(void) { //@ ghost int r = pure(1);
}
#elif CASE == 12 /* (a) ghost function whose body writes non-ghost memory */
/*@ ghost
  void gf(void) { x = 3; }
*/
void f(void) { //@ ghost gf();
}
#elif CASE == 13 /* control: legal ghost code (ghost writes only) */
void f(void) {
  //@ ghost g = x;
  //@ ghost int \ghost *p = &g;
  //@ ghost *p = 1;
}
#elif CASE == 14 /* (b) ghost infinite loop: no CFG change, but code after it is dead */
/*@ assigns \nothing;
    ensures \result == 1; */
int f(void) {
  //@ ghost while (1) { }
  return 0;               /* real result is 0, so the ensures is false */
}
#elif CASE == 15 /* (b) ghost call to a non-terminating ghost function with terminates \false */
/*@ ghost
  /@ terminates \false; assigns \nothing; ensures \false; @/
  void loop_forever(void) { while (1) { } }
*/
/*@ assigns \nothing;
    ensures \result == 1; */
int f(void) {
  //@ ghost loop_forever();
  return 0;
}
#endif
