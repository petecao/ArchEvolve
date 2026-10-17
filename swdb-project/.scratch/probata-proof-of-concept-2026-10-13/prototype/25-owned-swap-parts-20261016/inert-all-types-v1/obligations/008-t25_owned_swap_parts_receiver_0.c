//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_owned_state::Owners;
//@ import \wp::why3: vector_owned_effects::OwnedEffects;
/*@ check lemma t25_owned_swap_parts_receiver_0: \forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer l,r,a,bl,nl,cl,br,nr,cr; \forall integer observed; OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a) ==> (Owners::active_owner(Owners::swap(owners,l,r),observed) ==> Heap::typed_writes(OwnedEffects::swap(h,l,r,a),observed,0,8,8));
*/
