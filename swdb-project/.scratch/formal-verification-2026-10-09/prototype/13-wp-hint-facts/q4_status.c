/* Q4: which consolidated status does each kind of dependency produce?
   h is abstract, so every fact about h below is unprovable unless assumed. */
/*@ axiomatic H {
      logic integer h(integer x);
      axiom AX: h(0) == 10;              // assumed, no VC
    } */
//@ admit lemma ADL: h(1) == 11;         // assumed, no VC
//@ lemma ULM: h(2) == 12;               // unprovable lemma, gets a VC
//@ lemma ULM2: h(2) == 12;              // same statement, declared after ULM

/*@ assigns \nothing; ensures FULL: \result == 3; */
int full(void) { return 3; }             // fully proven, no dependency

/*@ assigns \nothing; ensures \result == 1; */
int dep_admit(int v) { //@ admit AD: v == 1;
                       return v; }       // ensures relies on an admit

/*@ assigns \nothing; */
void dep_axiom(void)  { //@ assert UAX: h(0) == 10;
}
/*@ assigns \nothing; */
void dep_admitlemma(void) { //@ assert UADL: h(1) == 11;
}
/*@ assigns \nothing; */
void dep_lemma(void)  { //@ assert ULEM: h(2) == 12;
}
/*@ assigns \nothing; */
void dep_assert(int v) { //@ assert UNP: v == 5;
                         //@ assert DEPA: v > 4;
}
/*@ assigns \nothing; */
void before_late(void) { //@ assert ULATE: h(3) == 13;
}
//@ lemma LATE: h(3) == 13;              // unprovable lemma declared after its user
