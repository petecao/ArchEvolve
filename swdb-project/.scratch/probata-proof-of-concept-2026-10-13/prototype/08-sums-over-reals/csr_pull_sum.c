/* Spike (d), Probata PoC ticket 08: a synthetic CSR pull-sum fixture (2026-10-14 ET).
 *
 * Written from scratch for this spike from the ticket's own statement: "each vertex's output
 * is a sum of float inputs over its in-edge range", as one flat loop over the edge range (the
 * flattening case of map 24 item 4). It is NOT a PageRank or BC unit: no damping, no degree
 * division, no scores, no frontier. Nothing comes from the fork's PR or BC code or the authors'
 * DX100 code.
 *
 * CSR layout: vertex v's in-edges are j in [off[v], off[v + 1]); nbr[j] is the source vertex.
 * Output: y[v] = sum_{j in [off[v], off[v + 1])} x[nbr[j]]   (over reals: -wp-model +real).
 * Sizes n, nx and off[n] are symbolic. One thread.
 *
 * -DSEEDED_BUG: the negative control. The owner test uses ">" instead of ">=", so edge
 * off[v + 1] is added to vertex v: each edge range is one edge too long. Same hints.
 *
 * Proof hints in this file (map 13 item 5 kinds): loop invariants, loop assigns, loop variants
 * with an integer measure. Provenance: agent (Claude Code subagent for ticket 08).
 */
#include "sum_logic.h"

/*@ requires SIZE: 0 <= n < 2147483647 && 0 <= nx;
    requires OFF_VALID: \valid_read(off + (0 .. n));
    requires OFF_BASE: off[0] == 0;
    requires OFF_SORTED: \forall integer u, w; 0 <= u <= w <= n ==> off[u] <= off[w];
    requires NBR_VALID: \valid_read(nbr + (0 .. off[n] - 1));
    requires NBR_RANGE: \forall integer j; 0 <= j < off[n] ==> 0 <= nbr[j] < nx;
    requires X_VALID: \valid_read(x + (0 .. nx - 1));
    requires Y_VALID: \valid(y + (0 .. n - 1));
    requires SEP: \separated(y + (0 .. n - 1), off + (0 .. n), nbr + (0 .. off[n] - 1),
                             x + (0 .. nx - 1));
    assigns y[0 .. n - 1];
    ensures UNIT: \forall integer u; 0 <= u < n ==>
      y[u] == range_sum{Pre}(x, nbr, off[u], off[u + 1]);
*/
void csr_pull_sum(int n, int nx, int *off, int *nbr, float *x, float *y)
{
  int u;
  /*@ loop invariant 0 <= u <= n;
      loop invariant \forall integer w; 0 <= w < u ==> y[w] == 0.0;
      loop assigns u, y[0 .. n - 1];
      loop variant n - u; */
  for (u = 0; u < n; u++)
    y[u] = 0.0f;

  int m = off[n];
  int v = 0;
  int j = 0;
  /* One flat loop over the edge range [0, m): a step either moves the owner vertex v
     forward or adds edge j to v's output. */
  /*@ loop invariant J_RANGE: 0 <= j <= m;
      loop invariant V_RANGE: 0 <= v <= n;
      loop invariant OWNER: off[v] <= j;
      loop invariant PARTIAL: \forall integer w; 0 <= w < n ==>
        y[w] == filtered_sum{Pre}(x, nbr, off, w, 0, j);
      loop assigns j, v, y[0 .. n - 1];
      loop variant (m - j) + (n - v); */
  while (j < m) {
#ifdef SEEDED_BUG
    if (j > off[v + 1]) {
#else
    if (j >= off[v + 1]) {
#endif
      v++;
    } else {
      y[v] = y[v] + x[nbr[j]];
      j++;
    }
  }
}
