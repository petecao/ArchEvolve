//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_owned_state::Owners;
//@ import \wp::why3: vector_owned_effects::OwnedEffects;
/*@ check lemma t25_owned_swap_parts_heap_separated: \forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer l,r,a,bl,nl,cl,br,nr,cr; \forall integer observed,other; OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a) ==> (Heap::live(OwnedEffects::swap(h,l,r,a),observed) && Heap::live(OwnedEffects::swap(h,l,r,a),other) && observed != other ==> Heap::numerical_address(OwnedEffects::swap(h,l,r,a),observed) != Heap::numerical_address(OwnedEffects::swap(h,l,r,a),other) && Heap::separated(OwnedEffects::swap(h,l,r,a),observed,other));
*/
