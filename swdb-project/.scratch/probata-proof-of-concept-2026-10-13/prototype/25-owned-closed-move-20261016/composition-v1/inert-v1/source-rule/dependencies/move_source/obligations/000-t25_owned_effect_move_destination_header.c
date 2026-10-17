//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_owned_state::Owners;
//@ import \wp::why3: vector_owned_effects::OwnedEffects;
/*@ check lemma t25_owned_effect_move_destination_header: \forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer d,s,b,n,c; OwnedEffects::world(h,owners,ready) && OwnedEffects::reserved(h,owners,ready,d) && Owners::active_owner(owners,s) && OwnedEffects::is_ready(ready,s) && d != s && OwnedEffects::header(h,s,b,n,c) ==> OwnedEffects::header(OwnedEffects::move(h,d,s),d,b,n,c);
*/
