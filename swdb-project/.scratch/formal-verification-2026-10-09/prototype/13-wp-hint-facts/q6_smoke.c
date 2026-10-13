/* Q6: what do WP smoke tests catch? Every ensures below is false for the real code. */

/*@ axiomatic H {
      logic integer h(integer x);
      axiom H1: \forall integer x; h(x) == 0;
      axiom H2: h(0) == 1;                 // contradicts H1
    } */

// (b) contradictory precondition
/*@ requires P1: x > 0;
    requires P2: x < 0;
    assigns \nothing;
    ensures E1: \result == 42; */
int pre_contra(int x) { return 0; }

// (a) contradictory loop invariants (a hint an LLM might write)
/*@ requires 0 <= n <= 10; assigns \nothing; ensures E2: \result == 42; */
int inv_contra(int n) {
  int i = 0;
  /*@ loop invariant I1: i >= 0;
      loop invariant I2: i < 0;
      loop assigns i;
      loop variant n - i; */
  while (i < n) i++;
  return i;
}

// (a') an invariant that holds and is preserved, but contradicts the loop exit,
//      so the code after the loop looks dead (the loop never terminates)
/*@ assigns \nothing; ensures E3: \result == 42; */
int inv_noexit(void) {
  int i = 0;
  /*@ loop invariant I3: i >= 0; loop assigns i; */
  while (i >= 0) { i = 1; }
  return i;
}

// admit \false makes the rest of the function dead
/*@ assigns \nothing; ensures E4: \result == 42; */
int admit_false(void) { //@ admit \false;
  return 0; }

// behavior with contradictory assumes
/*@ assigns \nothing;
    behavior B: assumes x > 0 && x < 0; ensures E5: \result == 42; */
int dead_assumes(int x) { return 0; }

// call to a body-less function whose contract is ensures \false
/*@ assigns \nothing; ensures \false; */
void no_return(void);
/*@ assigns \nothing; ensures E6: \result == 42; */
int dead_call(void) { no_return(); return 0; }

// contradictory axioms used through an assertion
/*@ assigns \nothing; ensures E7: \result == 42; */
int axiom_contra(void) { //@ assert A7: h(0) == 5;
  return 0; }
