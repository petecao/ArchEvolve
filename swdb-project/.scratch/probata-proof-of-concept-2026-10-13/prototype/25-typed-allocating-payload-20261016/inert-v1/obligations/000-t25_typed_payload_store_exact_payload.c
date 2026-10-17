//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_store_exact_payload: \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall TypedPayload::payload value; \forall integer b,n,k,address; TypedPayload::has_kind(kind,value) ==> TypedPayload::read(TypedPayload::put(s,b,TypedPayload::stride(kind)*k,value),b,TypedPayload::stride(kind)*k) == value && Heap::initialized_at(TypedPayload::objects(TypedPayload::put(s,b,TypedPayload::stride(kind)*k,value)),b,TypedPayload::stride(kind)*k);
*/
