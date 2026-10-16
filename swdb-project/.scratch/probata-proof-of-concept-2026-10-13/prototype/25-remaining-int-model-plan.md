# Remaining int vector models after the first public heap records

Created: 2026-10-16 ET. Prospective implementation plan; no new proof or growth
diagnostic execution is claimed. The coordinator owns all actual admissions.

The original count/value constructor and destructor have independently accepted
fresh public fixture records at `cea5652b`. The separate original int/int pair
records are accepted at `1278f2d9`. These scoped results do not close ticket25,
adopt records into the production store or compose generic vector callers.

## Next complete public slice: original int count construction

Implement `std_vector_int_ctor_count`, whose original body and contract differ
from count/value construction by the missing value argument and zero fill.
Preserve the original model version/body/contract; add no caller premise. Pin the
entire original function and contract and enumerate every source event and
clause/RTE/init/frame/lifetime obligation before admission. Its arbitrary
incoming heap, escaped aliases, old-buffer retention and unbounded allocation
identity domain are the same as the accepted count/value route.

The reviewed count/value semantics may be instantiated with mathematical
`value=0`, but this is an explicit source-to-VC translation rule, not permission
to reuse an old proof result. The new exact-source gate must reject a nonzero
fill, changed postcondition, extra write, omitted prefix stage or forged model
pin. Prefix establishment/step/exit, full range initialization, allocation
extent/alignment, all receiver accesses, fresh-object frame and source-entry
feasibility remain mandatory. Retain the full numeric/layout C kernel and its
ordinary plus smoke obligations through the ordinary report reader; inspect its
closed local dependencies. No imported desired-result axiom is allowed.

Start with a public compiler/native stand-in RED at ordinary `swdb prove --model`
showing the existing refusal. Then add the smallest mapping/dispatch change and
public GREEN controls, including complete successful record persistence/schema
and negative source/manifest controls. Keep every target under one remaining
public deadline and the existing process-tree cap. Freeze clean source, obtain
independent source/mapping review, and provide one exact prospective actual
profile to the coordinator. Only a fresh complete actual record and cold
task/import/runtime/source audit accept this member; no successful previous
member needs a duplicate formal run merely for preparation.

## Growth-domain review boundary

Source inspection of `_helpers().grow` exposes a concrete admitted counterstate.
Let a malloc-backed 24-byte receiver be initialized with `data=(int*)this`,
`size=0`, `capacity=6`; use aligned storage and request `cap=7`. Its receiver and
six-int backing extent refer to the same dynamic allocation. The current valid
predicate permits that overlap, the zero-length initialized prefix is vacuous,
and the data pointer is freeable. The source allocates fresh storage, skips the
zero-length copy, frees `this->data`, then writes `this->data` and
`this->capacity` through the freed receiver. This is a static source-domain
counterstate, not an executed sanitizer result or solver refutation.

Also, `push_back`, `resize` and `reserve` require current vector validity but do
not require the helper's freeability condition. The current predicate permits
borrowed writable backing storage, so a growth call cannot soundly assume its
deallocation is legal. Allocation success alone does not establish either
receiver survival or old-buffer ownership. The already accepted destructor
deliberately supports receiver/buffer overlap because it performs no receiver
write after release; its proof must not be silently narrowed or relabeled.

Do not add disjointness or freeability inside the proof view and call it the
unchanged original theorem. A future repair must use a declared new model
version/domain: a source-backed representation/ownership invariant must give
the receiver a surviving object separate from the full backing allocation and
justify deallocation when reallocation occurs. Escaped aliases may exist and
must become stale after release; ownership does not erase them. Audit helper
and every wrapper's requirements, assigns/frees/allocates, pointer formation,
initialized prefixes and exit frame under that invariant. The C++/C lowering
and caller proof must establish the invariant, preserve it through construction,
copy/move/swap and discharge it before each affected call. All method/model and
dependency eligibility pins must change normally; old records do not become
proofs of a new model version.

Until such a reviewed repair and complete caller discharge exist, original
growth/related unsupported-domain cases stay not proven or explicitly refused.
Do not suppress a lifetime/RTE goal, strengthen premises covertly, use finite
heaps/epochs, or accept an isolated helper law as an original-body proof. A later
finite ASan witness may corroborate the source diagnosis only after the
coordinator admits a concrete prospective command; no such run is needed or
requested for this count-constructor slice.
