//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_swap_exchange: \forall Owners::state s; \forall integer frontier,left,right; Owners::valid(s,frontier) && Owners::active_owner(s,left) && Owners::active_owner(s,right) ==> Owners::valid(Owners::swap(s,left,right),frontier) && Owners::buffer(Owners::swap(s,left,right),left) == Owners::buffer(s,right) && Owners::buffer(Owners::swap(s,left,right),right) == Owners::buffer(s,left);
*/
