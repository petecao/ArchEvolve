//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_move_transfer: \forall Owners::state s; \forall integer frontier,destination,source; Owners::valid(s,frontier) && Owners::active_owner(s,destination) && Owners::active_owner(s,source) && destination != source && Owners::buffer(s,destination) == 0 ==> Owners::valid(Owners::move(s,destination,source),frontier) && Owners::buffer(Owners::move(s,destination,source),destination) == Owners::buffer(s,source) && Owners::buffer(Owners::move(s,destination,source),source) == 0;
*/
