//@ import \wp::why3: vector_owned_state::Owners;
/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
/*@ check lemma t25_owned_retire_frame: \forall Owners::state s; \forall integer frontier,r,q; Owners::valid(s,frontier) && Owners::active_owner(s,r) && q != r ==> Owners::valid(Owners::retire(s,r),frontier) && !Owners::active_owner(Owners::retire(s,r),r) && Owners::buffer(Owners::retire(s,r),r) == 0 && (Owners::active_owner(Owners::retire(s,r),q) <==> Owners::active_owner(s,q)) && Owners::buffer(Owners::retire(s,r),q) == Owners::buffer(s,q) && (Owners::active_owner(s,q) && Owners::buffer(s,r) != 0 ==> Owners::buffer(s,q) != Owners::buffer(s,r) && q != Owners::buffer(s,r));
*/
