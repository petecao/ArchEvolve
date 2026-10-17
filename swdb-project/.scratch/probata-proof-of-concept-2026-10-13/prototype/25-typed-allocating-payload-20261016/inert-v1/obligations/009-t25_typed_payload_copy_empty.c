//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_copy_empty: \forall TypedPayload::state before; \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall integer source; \forall integer b,n,k,address; TypedPayload::copied(before,s,source,b,0,kind);
*/
