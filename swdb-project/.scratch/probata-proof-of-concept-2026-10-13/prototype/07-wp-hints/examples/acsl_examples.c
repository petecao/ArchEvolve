/* PROTOTYPE (Probata PoC ticket 07, continuation t07c), throwaway. Created 2026-10-14 ET.
 * Method change (b): syntax-checked ACSL examples shown to the proof-hint agent in its prompt.
 * Generic (not BFS): a frontier traversal over a CSR graph, the loop shape every graph kernel
 * has. Frama-C 33 parses it and WP proves every goal (see examples/README.md for the run).
 * Written by the implementing agent as a prompt example; it is never merged into a stand-in.
 *
 * The comment before each annotation names the hint record it would be:
 *   {"anchor": "loop:...", "kind": "loop_invariant", "text": "loop invariant ...;"}
 */
#include <stddef.h>

/*@
  // kind predicate, anchor global. Label parameter {L}: every memory read inside is at L.
  predicate ex_edge{L}(int *off, integer u, integer e) = off[u] <= e < off[u + 1];

  // v is a target of an edge leaving one of the frontier vertices q[lo .. hi - 1].
  predicate ex_hit{L}(int *q, int *off, int *nbr, integer lo, integer hi, integer v) =
    \exists integer p, e; lo <= p < hi && ex_edge{L}(off, q[p], e) && nbr[e] == v;

  // kind lemma, anchor global: proven in the same WP run. Splits the last frontier position off.
  lemma ex_hit_step{L}: \forall int *q, int *off, int *nbr, integer lo, integer i, integer v;
    lo <= i ==>
    (ex_hit{L}(q, off, nbr, lo, i + 1, v) <==>
       (ex_hit{L}(q, off, nbr, lo, i, v) ||
        (\exists integer e; ex_edge{L}(off, q[i], e) && nbr[e] == v)));
*/

/*@ requires sizes: 0 <= n <= 1000000 && 0 <= lo <= hi <= 1000000;
    requires \valid_read(off + (0 .. n)) && \valid_read(q + (lo .. hi - 1));
    requires \forall integer v; 0 <= v < n ==> 0 <= off[v] <= off[v + 1] <= 100000000;
    requires \forall integer p; lo <= p < hi ==> 0 <= q[p] < n;
    requires \forall integer v, e; 0 <= v < n && off[v] <= e < off[v + 1] ==>
               \valid_read(nbr + e) && 0 <= nbr[e] < n;
    requires \valid(flag + (0 .. n - 1));
    requires \forall integer v, e; 0 <= v < n && off[v] <= e < off[v + 1] ==>
               \separated(flag + (0 .. n - 1), nbr + e);
    requires \separated(flag + (0 .. n - 1), off + (0 .. n), q + (lo .. hi - 1));
    requires \valid(count) && \separated(count, flag + (0 .. n - 1), off + (0 .. n), q + (lo .. hi - 1));
    requires \forall integer v, e; 0 <= v < n && off[v] <= e < off[v + 1] ==> \separated(count, nbr + e);
    assigns flag[0 .. n - 1], *count;
    ensures marked: \forall integer v; 0 <= v < n ==>
      (flag[v] != 0 <==> (\old(flag[v]) != 0 || ex_hit{Pre}(q, off, nbr, lo, hi, v)));
*/
void mark_targets(int n, int *off, int *nbr, int *q, int lo, int hi, char *flag, size_t *count) {
  /* kind ghost, anchor stmt:...: a ghost variable needs a C type (int, unsigned, size_t,
     a fixed-size array), never `integer` or `boolean`. */
  /*@ ghost int g_rounds = 0; */
  *count = 0;
  /* Loop hints for one loop go into ONE block right before the loop. Named invariants are fine.
     Inside \at(e, Pre) name only parameters, globals and logic variables (never a loop counter);
     pass a C local as an argument to a predicate instead, as `i` is passed to ex_hit below. */
  /*@ loop invariant i_range: lo <= i <= hi;
      loop invariant g_rounds == i - lo;
      loop invariant done: \forall integer v; 0 <= v < n ==>
        (flag[v] != 0 <==> (\at(flag[v], Pre) != 0 || ex_hit{Pre}(q, off, nbr, lo, i, v)));
      loop assigns i, g_rounds, flag[0 .. n - 1], *count;
      loop variant hi - i; */
  for (int i = lo; i < hi; ++i) {
    int u = q[i];
    /* `loop assigns` takes FINITE ranges only (flag[0 .. n - 1]); `flag[k ..]` aborts WP with
       "Invalid infinite range". LoopEntry is the state right before the loop's first test. */
    /*@ loop invariant j_range: off[u] <= j <= off[u + 1];
        loop invariant u == q[i] && 0 <= u < n;
        loop invariant inner: \forall integer v; 0 <= v < n ==>
          (flag[v] != 0 <==> (\at(flag[v], LoopEntry) != 0 ||
                              (\exists integer e; off[u] <= e < j && nbr[e] == v)));
        loop assigns j, flag[0 .. n - 1], *count;
        loop variant off[u + 1] - j; */
    for (int j = off[u]; j < off[u + 1]; ++j) {
      flag[nbr[j]] = 1;
      *count = *count + 1;
    }
    /* kind assert, anchor stmt:...: a stepping stone right after the inner loop. */
    /*@ assert step: \forall integer v; 0 <= v < n ==>
          (flag[v] != 0 <==> (\at(flag[v], Pre) != 0 || ex_hit{Pre}(q, off, nbr, lo, i + 1, v))); */
    /*@ ghost g_rounds++; */
  }
}
