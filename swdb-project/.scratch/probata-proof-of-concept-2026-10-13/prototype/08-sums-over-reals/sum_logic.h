/* Throwaway sum logic for spike (d), Probata proof of concept ticket 08 (2026-10-14 ET).
 *
 * NOT the sum library of ticket 26. Written from scratch for this spike from the ticket text
 * and map 24 item 4 (a range sum, a filtered sum by an offsets array, and the lemmas
 * additivity, regrouping a flat edge range by owner vertex, permutation of a finite sum).
 * Nothing here comes from the fork's PR or BC code or the authors' DX100 code.
 *
 * Rules (map 16 item 2, map 13 item 5):
 * - Every recursive definition is primitive recursive on its LAST argument n: the only
 *   recursive call takes n - 1 under the guard n <= 0. All other definitions are
 *   non-recursive. Recursive definitions appear only in this file.
 * - No axiom, no admit, no axiomatic block, no inductive definition, no import.
 * - Every lemma is proven in the same WP run. Induction lemmas carry a \wp::strategy hint
 *   (Wp.induction, base -1; see the note below) whose generated script is saved in
 *   scripts/ and replayed on a fresh run.
 *
 * Note on base -1: with base 0 and a hypothesis 0 <= n, WP 33.0 leaves the
 * "Induction (inf)" child untried (no prover is called, Qed does not close it), so the
 * lemma stays unknown at 2/3 subgoals. With base -1 both the base case and the inf
 * case are vacuous and Qed closes them. Runs: /tmp/claude/probata-runs/t08/ (exp e2, e3).
 *
 * Terms are floats read as reals: run WP with -wp-model +real (rounding is an assumption
 * entry of kind platform choice, see the ticket Answer).
 */
#ifndef PROBATA_T08_SUM_LOGIC_H
#define PROBATA_T08_SUM_LOGIC_H

/* ---------------------------------------------------------------------------------------
 * Definitions
 * ------------------------------------------------------------------------------------- */

/*@
  // sum_{j in [lo, lo + n)} x[a[j]]   (primitive recursive on n)
  logic real sum_n{L}(float *x, int *a, integer lo, integer n) =
    n <= 0 ? 0.0 : sum_n(x, a, lo, n - 1) + x[a[lo + n - 1]];

  // RANGE SUM: sum_{j in [lo, hi)} x[a[j]]; 0 when hi <= lo   (non-recursive)
  logic real range_sum{L}(float *x, int *a, integer lo, integer hi) =
    sum_n(x, a, lo, hi - lo);

  // edge j belongs to vertex v under the offsets array off
  predicate owns{L}(int *off, integer v, integer j) = off[v] <= j < off[v + 1];

  // sum_{j in [lo, lo + n), owns(off, v, j)} x[a[j]]   (primitive recursive on n)
  logic real fsum_n{L}(float *x, int *a, int *off, integer v, integer lo, integer n) =
    n <= 0 ? 0.0 :
      fsum_n(x, a, off, v, lo, n - 1) + (owns(off, v, lo + n - 1) ? x[a[lo + n - 1]] : 0.0);

  // FILTERED SUM by an offsets array: the part of the flat edge range [lo, hi) that
  // vertex v owns   (non-recursive)
  logic real filtered_sum{L}(float *x, int *a, int *off, integer v, integer lo, integer hi) =
    fsum_n(x, a, off, v, lo, hi - lo);

  // sum_{u in [0, n)} range_sum(x, a, off[u], off[u + 1])   (primitive recursive on n)
  logic real vsum_n{L}(float *x, int *a, int *off, integer n) =
    n <= 0 ? 0.0 : vsum_n(x, a, off, n - 1) + range_sum(x, a, off[n - 1], off[n]);

  // Permutation helpers (a double sum over the 0/1 matrix [p[j] == i]).
  // row_n(j, n) = sum_{i in [0, n)} (p[j] == i ? x[a[i]] : 0)
  logic real row_n{L}(float *x, int *a, int *p, integer j, integer n) =
    n <= 0 ? 0.0 : row_n(x, a, p, j, n - 1) + (p[j] == n - 1 ? x[a[n - 1]] : 0.0);

  // col_n(i, n) = sum_{j in [0, n)} (p[j] == i ? x[a[i]] : 0)
  logic real col_n{L}(float *x, int *a, int *p, integer i, integer n) =
    n <= 0 ? 0.0 : col_n(x, a, p, i, n - 1) + (p[n - 1] == i ? x[a[i]] : 0.0);

  // rows_n(m, n) = sum_{j in [0, n)} row_n(j, m)
  logic real rows_n{L}(float *x, int *a, int *p, integer m, integer n) =
    n <= 0 ? 0.0 : rows_n(x, a, p, m, n - 1) + row_n(x, a, p, n - 1, m);

  // cols_n(m, n) = sum_{i in [0, n)} col_n(i, m)
  logic real cols_n{L}(float *x, int *a, int *p, integer m, integer n) =
    n <= 0 ? 0.0 : cols_n(x, a, p, m, n - 1) + col_n(x, a, p, n - 1, m);

  // p is a bijection of [0, n) and q is its inverse
  predicate is_perm{L}(int *p, int *q, integer n) =
    (\forall integer j; 0 <= j < n ==> 0 <= p[j] < n && q[p[j]] == j) &&
    (\forall integer i; 0 <= i < n ==> 0 <= q[i] < n && p[q[i]] == i);

  // Non-recursive wrappers used in lemma statements. WP adds a typing premise
  // (is_sint32) for every int memory read that appears at the top of a lemma statement;
  // a read inside a definition gets none. Without the wrappers, a lemma such as ROW_PICK
  // cannot be applied inside another lemma's proof, where the read value has no typing
  // fact (seen 2026-10-14 ET: PERM_ROWS timed out on all three solvers).
  logic real term{L}(float *x, int *a, integer j) = x[a[j]];
  logic real col_val{L}(float *x, int *a, int *q, integer i, integer m) =
    q[i] < m ? x[a[i]] : 0.0;
  logic real pick{L}(float *x, int *a, int *p, integer j, integer n) =
    0 <= p[j] < n ? x[a[p[j]]] : 0.0;
  logic integer clip_lo{L}(int *off, integer v, integer lo) = \max(lo, off[v]);
  logic integer clip_hi{L}(int *off, integer v, integer hi) = \min(hi, off[v + 1]);
*/

/* ---------------------------------------------------------------------------------------
 * Proof hints: one prover strategy and one induction strategy per induction lemma.
 * \pattern picks the first matching term in WP's normalized goal; \select names the
 * pattern variable that is the induction variable. The generated scripts (scripts/)
 * record the chosen variable; the replay checks it.
 * ------------------------------------------------------------------------------------- */

//@ \wp::strategy Leaf: \prover("Alt-Ergo", 30), \prover("Z3", 30), \prover("CVC5", 30);

/* ---------------------------------------------------------------------------------------
 * Lemma 1: ADDITIVITY
 * ------------------------------------------------------------------------------------- */

/*@ \wp::strategy Ind_add:
      \tactic("Wp.induction", \pattern(L_sum_n(_, _, _, _, m, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma ADD_N: \forall float *x, int *a, integer lo, mid, n;
      lo <= mid && 0 <= n ==>
      sum_n(x, a, mid, n) + sum_n(x, a, lo, mid - lo) == sum_n(x, a, lo, mid - lo + n);
*/
//@ \wp::proof Ind_add: ADD_N;

/*@ lemma ADDITIVITY: \forall float *x, int *a, integer lo, mid, hi;
      lo <= mid <= hi ==>
      range_sum(x, a, lo, hi) == range_sum(x, a, lo, mid) + range_sum(x, a, mid, hi);
*/

/*@ lemma RANGE_SNOC: \forall float *x, int *a, integer lo, hi;
      lo <= hi ==> range_sum(x, a, lo, hi + 1) == range_sum(x, a, lo, hi) + term(x, a, hi);
*/

/*@ lemma RANGE_EMPTY: \forall float *x, int *a, integer lo, hi;
      hi <= lo ==> range_sum(x, a, lo, hi) == 0.0;
*/

/* ---------------------------------------------------------------------------------------
 * Lemma 2: REGROUPING a flat edge range by owner vertex
 *   per-owner form (used by the fixture's unit) and total form
 * ------------------------------------------------------------------------------------- */

/*@ \wp::strategy Ind_own:
      \tactic("Wp.induction", \pattern(L_fsum_n(_, _, _, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma REGROUP_OWNER_N: \forall float *x, int *a, int *off, integer v, lo, n;
      0 <= n ==>
      fsum_n(x, a, off, v, lo, n) ==
        range_sum(x, a, clip_lo(off, v, lo), clip_hi(off, v, lo + n));
*/
//@ \wp::proof Ind_own: REGROUP_OWNER_N;

/*@ lemma REGROUP_OWNER: \forall float *x, int *a, int *off, integer v, lo, hi;
      lo <= hi ==>
      filtered_sum(x, a, off, v, lo, hi) ==
        range_sum(x, a, clip_lo(off, v, lo), clip_hi(off, v, hi));
*/

/*@ \wp::strategy Ind_tot:
      \tactic("Wp.induction", \pattern(L_vsum_n(_, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma REGROUP_TOTAL: \forall float *x, int *a, int *off, integer n;
      0 <= n && (\forall integer u, w; 0 <= u <= w <= n ==> off[u] <= off[w]) ==>
      vsum_n(x, a, off, n) == range_sum(x, a, off[0], off[n]);
*/
//@ \wp::proof Ind_tot: REGROUP_TOTAL;

/* ---------------------------------------------------------------------------------------
 * Lemma 3: PERMUTATION of a finite sum
 *   sum_j x[a[p[j]]] == sum_i x[a[i]] for a bijection p of [0, n) with inverse q, through
 *   the double sum sum_j sum_i [p[j] == i] x[a[i]] summed in both orders.
 * ------------------------------------------------------------------------------------- */

/*@ \wp::strategy Ind_row:
      \tactic("Wp.induction", \pattern(L_row_n(_, _, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma ROW_PICK: \forall float *x, int *a, int *p, integer j, n;
      0 <= n ==>
      row_n(x, a, p, j, n) == pick(x, a, p, j, n);
*/
//@ \wp::proof Ind_row: ROW_PICK;

/*@ \wp::strategy Ind_col:
      \tactic("Wp.induction", \pattern(L_col_n(_, _, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma COL_PERM: \forall float *x, int *a, int *p, int *q, integer i, n, m;
      0 <= m <= n && is_perm(p, q, n) && 0 <= i < n ==>
      col_n(x, a, p, i, m) == col_val(x, a, q, i, m);
*/
//@ \wp::proof Ind_col: COL_PERM;

/*@ \wp::strategy Ind_cols:
      \tactic("Wp.induction", \pattern(L_cols_n(_, _, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma COLS_ZERO: \forall float *x, int *a, int *p, integer n;
      0 <= n ==> cols_n(x, a, p, 0, n) == 0.0;
*/
//@ \wp::proof Ind_cols: COLS_ZERO;

/*@ lemma COLS_STEP: \forall float *x, int *a, int *p, integer m, n;
      0 <= m && 0 <= n ==>
      cols_n(x, a, p, m + 1, n) == cols_n(x, a, p, m, n) + row_n(x, a, p, m, n);
*/
//@ \wp::proof Ind_cols: COLS_STEP;

/*@ \wp::strategy Ind_rows:
      \tactic("Wp.induction", \pattern(L_rows_n(_, _, _, _, _, _, k)), \select(k),
              \param("base", -1), \children(Leaf)); */
/*@ lemma FUBINI: \forall float *x, int *a, int *p, integer m, n;
      0 <= m && 0 <= n ==> rows_n(x, a, p, n, m) == cols_n(x, a, p, m, n);
*/
//@ \wp::proof Ind_rows: FUBINI;

/*@ lemma PERM_ROWS: \forall float *x, int *a, int *b, int *p, int *q, integer n, m;
      0 <= m <= n && is_perm(p, q, n) &&
      (\forall integer j; 0 <= j < n ==> b[j] == a[p[j]]) ==>
      rows_n(x, a, p, n, m) == sum_n(x, b, 0, m);
*/
//@ \wp::proof Ind_rows: PERM_ROWS;

/*@ lemma PERM_COLS: \forall float *x, int *a, int *p, int *q, integer n, m;
      0 <= m <= n && is_perm(p, q, n) ==> cols_n(x, a, p, n, m) == sum_n(x, a, 0, m);
*/
//@ \wp::proof Ind_cols: PERM_COLS;

// Chain lemmas: each equates a range_sum, the term the final goal holds, with the same
// cols_n term, so that the SMT solvers' trigger-based instantiation closes PERMUTATION
// (with PERM_ROWS_R stated against rows_n, PERMUTATION timed out on all three solvers).
/*@ lemma PERM_ROWS_R: \forall float *x, int *a, int *b, int *p, int *q, integer n;
      0 <= n && is_perm(p, q, n) && (\forall integer j; 0 <= j < n ==> b[j] == a[p[j]]) ==>
      range_sum(x, b, 0, n) == cols_n(x, a, p, n, n);
*/

/*@ lemma PERM_COLS_R: \forall float *x, int *a, int *p, int *q, integer n;
      0 <= n && is_perm(p, q, n) ==> range_sum(x, a, 0, n) == cols_n(x, a, p, n, n);
*/

// The final step needs one lemma instance the solvers' triggers do not find: the goal holds
// no cols_n term. The hint instantiates PERM_ROWS_R on the goal's own terms (Wp.lemma);
// PERM_COLS_R then fires on the cols_n term that instance brings in.
/*@ \wp::strategy Link:
      \tactic("Wp.lemma",
        \goal(L_range_sum(m1, m2, x, b, 0, n) == L_range_sum(m1, m2, x, a, 0, n)),
        \incontext(P_is_perm(m2, p, q, n)),
        \param("lemma", "PERM_ROWS_R"),
        \param("P1", m1), \param("P2", m2), \param("P3", x), \param("P4", a),
        \param("P5", b), \param("P6", p), \param("P7", q), \param("P8", n),
        \children(Leaf)); */
/*@ lemma PERMUTATION: \forall float *x, int *a, int *b, int *p, int *q, integer n;
      0 <= n && is_perm(p, q, n) && (\forall integer j; 0 <= j < n ==> b[j] == a[p[j]]) ==>
      range_sum(x, b, 0, n) == range_sum(x, a, 0, n);
*/
//@ \wp::proof Link: PERMUTATION;

#endif
