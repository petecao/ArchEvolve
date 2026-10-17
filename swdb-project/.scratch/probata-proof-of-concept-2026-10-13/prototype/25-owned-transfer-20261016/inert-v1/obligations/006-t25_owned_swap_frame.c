//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_swap_frame: \forall Owners::state s; \forall integer left,right,q; q != left && q != right ==> (Owners::active_owner(Owners::swap(s,left,right),q) <==> Owners::active_owner(s,q)) && Owners::buffer(Owners::swap(s,left,right),q) == Owners::buffer(s,q);
*/
