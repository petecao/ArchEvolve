//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_buffer_fresh: \forall Owners::state s; \forall integer frontier,r; Owners::valid(s,frontier) && Owners::active_owner(s,r) && Owners::buffer(s,r) == 0 ==> Owners::valid(Owners::bind(s,r,frontier),frontier+1) && Owners::buffer(Owners::bind(s,r,frontier),r) == frontier;
*/
