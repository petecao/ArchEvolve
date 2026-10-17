//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_value_non_nan_equality_lifting: \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall TypedPayload::payload value; \forall integer b,n,k,address; TypedPayload::has_kind(kind,value) && !TypedPayload::is_nan(value) && TypedPayload::prefix(s,b,n,kind,value) ==> \forall integer j; 0 <= j < n ==> TypedPayload::c_equal(TypedPayload::read(s,b,TypedPayload::stride(kind)*j),value);
*/
