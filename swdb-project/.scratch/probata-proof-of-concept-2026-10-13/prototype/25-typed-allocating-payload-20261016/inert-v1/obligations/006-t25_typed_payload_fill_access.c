//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_fill_access: \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall integer b,n,k,address; Heap::well_formed(TypedPayload::objects(s)) && 0 < n && 0 <= k <= n && Heap::bytes(TypedPayload::objects(s),b) == TypedPayload::stride(kind)*n && Heap::typed_writes(TypedPayload::objects(s),b,0,TypedPayload::stride(kind)*n,TypedPayload::stride(kind)) && k < n ==> Heap::typed_writes(TypedPayload::objects(s),b,TypedPayload::stride(kind)*k,TypedPayload::stride(kind),TypedPayload::stride(kind));
*/
