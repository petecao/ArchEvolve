//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_owned_state::Owners;
//@ import \wp::why3: vector_owned_effects::OwnedEffects;
/*@ check lemma t25_owned_swap_parts_heap_frontier: \forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer l,r,a,bl,nl,cl,br,nr,cr; OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a) ==> (0 < Heap::fresh_id(OwnedEffects::swap(h,l,r,a)));
*/
