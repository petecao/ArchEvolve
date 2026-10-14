/* Synthetic CSR pull-sum unit (Probata proof of concept ticket 26, 2026-10-14 ET): each vertex's
 * value is the sum of a float input over its incoming edge range, one inner loop per vertex.
 *
 * Written from scratch from the ticket text (a synthetic fixture, map 27 item 3; never PR, BC or SSSP
 * code). CSR layout (logic.csr_graph): vertex u's in-edges are j in [off[u], off[u + 1]); nbr[j] is
 * the source vertex. Sizes n, nx and off[n] are symbolic; one thread; floats read as reals
 * (-wp-model +real).
 *
 * `swdb prove-logic --program` places logic.csr_graph and logic.sum before this file.
 * -DSEEDED_BUG: the negative control; the inner loop skips each vertex's first edge.
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
      loop invariant DONE: \forall integer w; 0 <= w < u ==>
        y[w] == range_sum{Pre}(x, nbr, off[w], off[w + 1]);
      loop assigns u, y[0 .. n - 1];
      loop variant n - u; */
  for (u = 0; u < n; u++) {
    float acc = 0.0f;
    int j;
#ifdef SEEDED_BUG
    j = off[u] + 1;
#else
    j = off[u];
#endif
    /*@ loop invariant J_RANGE: off[u] <= j <= off[u + 1];
        loop invariant ACC: acc == range_sum{Pre}(x, nbr, off[u], j);
        loop assigns j, acc;
        loop variant off[u + 1] - j; */
    while (j < off[u + 1]) {
      acc = acc + x[nbr[j]];
      j++;
    }
    y[u] = acc;
  }
}
