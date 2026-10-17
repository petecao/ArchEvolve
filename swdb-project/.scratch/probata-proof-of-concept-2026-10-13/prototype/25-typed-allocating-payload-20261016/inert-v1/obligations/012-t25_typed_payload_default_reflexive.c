//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_default_reflexive: \forall TypedPayload::scalar_kind kind; \forall TypedPayload::bits64 null_bits; TypedPayload::c_equal(TypedPayload::zero(kind,null_bits),TypedPayload::zero(kind,null_bits));
*/
