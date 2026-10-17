//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_nan_not_reflexive: \forall TypedPayload::payload value; TypedPayload::is_nan(value) ==> !TypedPayload::c_equal(value,value);
*/
