/* Q5: tactics and JSON scripts. SUM_NONNEG needs induction (no SMT proves it alone).
   BAD is false (bad() returns 0); q5_scripts.sh plants a fake script and a fake cache
   entry claiming it is valid. */
//@ logic integer sum(integer n) = n <= 0 ? 0 : n + sum(n - 1);

//@ \wp::strategy AE: \prover("Alt-Ergo", 5);
/*@ \wp::strategy Ind:
      \tactic("Wp.induction", \pattern(L_sum(n)), \select(n), \param("base", 0),
              \children(AE)); */
//@ lemma SUM_NONNEG: \forall integer n; sum(n) >= 0;
//@ \wp::proof Ind: SUM_NONNEG;

/*@ assigns \nothing; ensures BAD: \result == 1; */
int bad(void) { return 0; }
