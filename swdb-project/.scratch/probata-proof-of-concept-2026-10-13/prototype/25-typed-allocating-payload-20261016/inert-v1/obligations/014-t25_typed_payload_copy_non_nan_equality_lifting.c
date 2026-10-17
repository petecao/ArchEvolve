//@ import \wp::why3: heap_reallocation::Heap;
//@ import \wp::why3: vector_typed_payload::TypedPayload;
/*@ check lemma t25_typed_payload_copy_non_nan_equality_lifting: \forall TypedPayload::state before; \forall TypedPayload::state s; \forall TypedPayload::scalar_kind kind; \forall integer source; \forall integer b,n,k,address; TypedPayload::copied(before,s,source,b,n,kind) && TypedPayload::image(before,source,n,kind) && TypedPayload::reflexive_image(before,source,n,kind) ==> \forall integer j; 0 <= j < n ==> TypedPayload::c_equal(TypedPayload::read(s,b,TypedPayload::stride(kind)*j),TypedPayload::read(before,source,TypedPayload::stride(kind)*j));
*/
