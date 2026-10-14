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

/* Item 5: a loop that appends at a moving end. The loop assigns range starts where the function's
   assigns starts and ends at the function's own finite bound, so it covers every index the loop can
   write and stays inside the function's assigns. */
/*@ requires \valid(q) && q->shared_in <= 1000;
    requires \valid(q->shared + (q->shared_in .. q->shared_in + 9));
    requires \separated(q, q->shared + (q->shared_in .. q->shared_in + 9));
    assigns q->shared_in, q->shared[q->shared_in .. 18446744073709551615];
*/
void push10(struct sq *q) {
  /*@ loop invariant 0 <= t <= 10;
      loop invariant q->shared_in == \at(q->shared_in, Pre) + t;
      loop assigns t, q->shared_in, q->shared[\at(q->shared_in, Pre) .. 18446744073709551615];
      loop variant 10 - t; */
  for (int t = 0; t < 10; ++t) {
    q->shared[q->shared_in] = t;
    q->shared_in++;
  }
}
