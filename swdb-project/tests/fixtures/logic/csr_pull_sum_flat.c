/* Synthetic CSR pull-sum unit, flattened (Probata proof of concept ticket 26, 2026-10-14 ET): the same
 * unit postcondition as csr_pull_sum.c, computed by one flat loop over the whole edge range (the
 * flattening case of map 24 item 4). A step either moves the owner vertex v forward or adds edge j to
 * v's value; the proof goes through the sum library's regrouping lemma (REGROUP_OWNER).
 *
 * Written from scratch (spike (d), prototype/08-sums-over-reals/csr_pull_sum.c, carried over); never PR,
 * BC or SSSP code. `swdb prove-logic --program` places logic.csr_graph and logic.sum before this file.
 * -DSEEDED_BUG: the negative control; the owner test uses ">" for ">=", so each vertex also takes the
 * first edge of the next vertex.
 * Proof hints (map 13 item 5 kinds): loop invariants, loop assigns, integer loop variants.
 */

/*@ requires SIZE: 0 <= n < 2147483647 && 0 <= nx;
    requires OFF_VALID: \valid_read(off + (0 .. n));
    requires GRAPH: csr_offsets(off, n) && csr_ends_in(off, nbr, n, nx);
    requires NBR_VALID: \valid_read(nbr + (0 .. off[n] - 1));
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
