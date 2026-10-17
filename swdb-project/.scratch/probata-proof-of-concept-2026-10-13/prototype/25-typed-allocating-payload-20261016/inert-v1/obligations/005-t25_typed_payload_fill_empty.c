//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_fill_empty: \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall TypedPayload::payload value; \forall integer b,n,k,address; TypedPayload::prefix(s,b,0,kind,value);
*/
