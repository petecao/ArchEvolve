//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_allocate_incoming_frame: \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall integer b,n,k,address; Heap::well_formed(TypedPayload::objects(s)) && TypedPayload::available(s,n,address,kind) ==> TypedPayload::incoming_frame(s,TypedPayload::allocate(s,n,address,kind));
*/
