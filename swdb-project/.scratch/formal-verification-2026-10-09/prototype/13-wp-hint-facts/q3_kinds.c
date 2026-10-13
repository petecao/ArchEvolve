/* Q3: which clause kinds make a VC, and which ones become a hypothesis for later goals?
   In every function the first annotation is false or unprovable (v is unconstrained),
   and the second one is provable only if the first one is a hypothesis. */

/*@ axiomatic H { logic integer h(integer x); } */ /* abstract: no axiom, no body */

// ---- statement annotations
/*@ assigns \nothing; */
void s_assert(int v) { //@ assert A1: v > 100;
                       //@ assert A2: v > 50;
}
/*@ assigns \nothing; */
void s_check(int v)  { //@ check C1: v > 100;
                       //@ assert C2: v > 50;
}
/*@ assigns \nothing; */
void s_admit(int v)  { //@ admit D1: v > 100;
                       //@ assert D2: v > 50;
}

// ---- requires kinds: callee body uses it, caller violates it
/*@ check requires RQC: v > 100; assigns \nothing; ensures EC: \result > 50; */
int r_check(int v) { return v; }
/*@ admit requires RQA: v > 100; assigns \nothing; ensures EA: \result > 50; */
int r_admit(int v) { return v; }
/*@ assigns \nothing; */
void r_caller(void) { int a = r_check(0); int b = r_admit(0); }

// ---- ensures kinds: callee does not satisfy it, caller relies on it
/*@ assigns \nothing; check ensures ECK: \result == 7; */
int e_check(void) { return 0; }
/*@ assigns \nothing; admit ensures EAD: \result == 7; */
int e_admit(void) { return 0; }
/*@ assigns \nothing; */
void e_caller(void) { int a = e_check(); //@ assert ECU: a == 7;
                      int b = e_admit(); //@ assert EAU: b == 7;
}

// ---- lemma kinds over the abstract h (none of them is provable)
//@ lemma     LP: h(3) == 7;
//@ check lemma LC: h(1) == 5;
//@ admit lemma LA: h(2) == 6;
/*@ assigns \nothing; */
void l_user(void) { //@ assert ULP: h(3) == 7;
                    //@ assert ULC: h(1) == 5;
                    //@ assert ULA: h(2) == 6;
}

// ---- loop invariant kinds: each invariant is false
/*@ requires 0 <= n <= 10; assigns \nothing; */
void i_check(int n) {
  int i = 0;
  /*@ check loop invariant ICK: i == 1000; loop invariant 0 <= i <= n; loop assigns i; loop variant n - i; */
  while (i < n) i++;
  //@ assert ICKU: i == 1000;
}
/*@ requires 0 <= n <= 10; assigns \nothing; */
void i_admit(int n) {
  int i = 0;
  /*@ admit loop invariant IAD: i == 1000; loop invariant 0 <= i <= n; loop assigns i; loop variant n - i; */
  while (i < n) i++;
  //@ assert IADU: i == 1000;
}

// ---- general (non-loop) invariant with a kind
/*@ assigns \nothing; */
void g_admit(int v) { //@ admit invariant GI: v > 100;
                      //@ assert GIU: v > 50;
}
