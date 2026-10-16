//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_receiver_fresh: \forall Owners::state s; \forall integer frontier; Owners::valid(s,frontier) ==> Owners::valid(Owners::begin_owner(s,frontier),frontier+1) && Owners::active_owner(Owners::begin_owner(s,frontier),frontier) && Owners::buffer(Owners::begin_owner(s,frontier),frontier) == 0;
*/
