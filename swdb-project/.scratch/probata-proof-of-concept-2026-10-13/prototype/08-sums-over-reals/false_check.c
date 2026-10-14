/* Spike (d), ticket 08: the \false check (map 16 item 9). WP must NOT prove \false from the
   throwaway definitions and lemmas alone. Two separate runs, because an unproven lemma is a
   hypothesis of every function goal (research 13, Q4): with both goals in one file, the
   lemma below (simplified by Qed to "false") made the function goal Valid in 0.01 s
   (2026-10-14 02:30 ET, run kept in /tmp/claude/probata-runs/t08/scratch/).
   - -DFALSE_LEMMA: FALSE_FROM_LEMMAS, a lemma goal stated after every library lemma, so all
     of them are in its context.
   - otherwise: false_from_context, a function goal; every global lemma is in every
     function goal's context, with the definitions of the symbols they use.
   The Why3 tasks are printed into the log (-wp-msg-key print-generated) to show that the
   definitions and lemmas are in the context. */
#include "sum_logic.h"

#ifdef FALSE_LEMMA
/*@ lemma FALSE_FROM_LEMMAS: \false; */
#else
/*@ assigns \nothing;
    ensures FALSE_FROM_CONTEXT: \false; */
void false_from_context(void)
{
}
#endif
