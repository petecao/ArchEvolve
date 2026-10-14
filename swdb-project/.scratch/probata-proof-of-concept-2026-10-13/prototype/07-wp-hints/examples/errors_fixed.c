/* PROTOTYPE (Probata PoC ticket 07, continuation t07c), throwaway. Created 2026-10-14 ET.
 * Method change (b): the corrected forms named in frama_c_errors.txt, checked by Frama-C 33 parse
 * and WP (examples/README.md). Not shown to the agent as code; frama_c_errors.txt quotes them. */
#include <stddef.h>

struct sq { int *shared; size_t shared_in; };

/*@ predicate same_at{L1, L2}(int *a, integer i) = \at(a[i], L1) == \at(a[i], L2);
    lemma first_nonneg{L}: \forall int *a; a[0] >= 0 ==> a[0] + 1 > 0;
*/

/*@ requires \valid(q) && \valid(q->shared + (0 .. 99)) && \separated(q, q->shared + (0 .. 99));
    requires q->shared_in <= 50;
    assigns q->shared[0 .. 99];
*/
void fill(struct sq *q) {
  /*@ ghost int td_chunk_end = 0; */
  /*@ loop invariant 0 <= begin <= 10;
      loop invariant td_chunk_end == begin;
      loop invariant \forall integer k; 0 <= k < 50 ==> same_at{Pre, Here}(q->shared, k);
      loop assigns begin, td_chunk_end, q->shared[50 .. 99];
      loop variant 10 - begin; */
  for (size_t begin = 0; begin < 10; ++begin) {
    /*@ assert same_at{Pre, Here}(q->shared, begin); */
    q->shared[50 + begin] = 1;
    /*@ ghost td_chunk_end++; */
  }
}
