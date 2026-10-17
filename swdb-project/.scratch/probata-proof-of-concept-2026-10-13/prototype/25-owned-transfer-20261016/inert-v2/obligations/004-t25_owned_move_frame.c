//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_move_frame: \forall Owners::state s; \forall integer destination,source,q; q != destination && q != source ==> (Owners::active_owner(Owners::move(s,destination,source),q) <==> Owners::active_owner(s,q)) && Owners::buffer(Owners::move(s,destination,source),q) == Owners::buffer(s,q);
*/
