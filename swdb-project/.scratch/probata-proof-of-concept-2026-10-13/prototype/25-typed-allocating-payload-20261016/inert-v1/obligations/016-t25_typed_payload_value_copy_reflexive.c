//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_value_copy_reflexive: \forall TypedPayload::scalar_kind kind; \forall TypedPayload::payload value; TypedPayload::has_kind(kind,value) ==> TypedPayload::value_copy(value,value);
*/
