//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_shared_backing_rejected: \forall Owners::state s; \forall integer r,q; Owners::active_owner(s,r) && Owners::active_owner(s,q) && r != q && Owners::buffer(s,r) != 0 && Owners::buffer(s,r) == Owners::buffer(s,q) ==> !Owners::exclusive(s);
*/
