# Qualified v3 reallocation and caller vertical

Created: 2026-10-16 ET. Preparation only; no body/caller proof is claimed.

The public candidate names are `std_vector_int_realloc_v3_` followed by
`ctor_count_value`, `grow`, `reserve` or `dtor`. `swdb prove --model` records the
qualified source, original v2 source and explicit contract/domain certificate,
then returns not proven before a verifier launch. The original v2 catalog and
its broader contracts remain unchanged; this new ID never certifies them.

`reallocatable_v3` is unary eligibility: valid writable receiver, freeable
nonempty backing, and distinct receiver/backing allocation bases. Ordinary byte
separation is insufficient when a larger allocation contains both regions.
Freeability is not an exclusive ownership token; caller composition must track
cross-view deallocation rights or invalidation. Escaped raw aliases remain
legal, and release makes them stale. Destruction keeps its original overlap
domain because it performs no receiver write after release.

The qualified constructor keeps its original precondition and adds eligibility
and `capacity == n` postconditions. These are new proof obligations, not
assumptions. Exact capacity is justified by the modeled C body and the pinned
C++17 implementation's count/value construction/`__allocate_at_least` source,
not by a universal C++ capacity rule. Grow/reserve require and preserve the
qualified domain. Executable bodies remain byte-identical after reversing the
explicit helper-name aliases; four defined native cases per grow body preserve
size, capacity and initialized values. No invalid-growth/ASan case was run.

The complete public vertical uses the full source in
`tests/fixtures/proof/vector_reallocation_v3.cc`: construct from scalar `n`,
capture `data()`, reserve, observe and destruct. Safe current-buffer, stale
post-growth alias and no-growth old-alias functions include guarded empty cases.
The planned entry contract is `n >= 0`; conversion/bounds, constructor
eligibility/exact capacity, reserve helper requirements, observations, implicit
destruction and source frame must all be discharged, with no extra caller
premise inserted. Ordinary current dependency eligibility is mandatory.

Next implementation connects source-backed caller obligations through public
lowering, then the complete unbounded source-to-heap mapping and public proof
adapter. Grow must copy arbitrary initialized typed int values, prove prefix
establishment/step/exit and frame, release only the old identity, and show the
receiver survives before field writes. Do not assume a uniformly filled old
buffer or import an unproved copy law. Automatic caller receiver storage also
needs explicit local-object lifetime semantics, separate from dynamic buffer
freeability. Zero size, legal address reuse, aliases and stale reads remain
mandatory. No finite allocation pool/epoch replaces those obligations.

See [preparation controls](../../evidence/t25-reallocation-domain-preparation-controls-20261016.json),
[prospective domain review](../../evidence/t25-reallocation-domain-prospective-review-20261016.md)
and [complete coverage matrix](../25-acceptance-coverage-20261016.md).
