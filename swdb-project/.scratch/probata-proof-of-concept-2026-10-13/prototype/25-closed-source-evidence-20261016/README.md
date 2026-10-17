# Closed source effects and observations

Created: 2026-10-16 ET. An unadmitted source derivation with an explicit pending
scientific evidence boundary. This module creates no proof record.

`vector_reallocation_closed_evidence.prepare/check` reconstructs the complete
source certificate, original models, source event order, and both semantic
branches. It checks the entire executable constructor grammar after removing
comments and whitespace, retaining every initial field store, the successful
fresh allocation, capacity store, unbounded fill loop and final size store.
The public artifact records each concrete source span, the actual null/dynamic
release and receiver automatic entry/end. Unknown effect operations fail closed.

The frame argument is a structural operational rule. Fix any object allocated
before entry, including a dead object, and any byte in that object. Source-fresh
receiver and buffer identities differ from that object. Each actual source store
changes one private target; each release/scope transition ends one private target;
null release is identity. Composition preserves the pointwise identity on the
incoming object. The loop preserves the same property for every iteration, and
induction preserves it for the full source count. Allocator/deallocator effects
are covered only under their explicit pinned framing/freshness/freeability/
release model TCB. The checker does not infer that library internal effects or
replacement operators are absent from standard conformance or TU screening.

This rule preserves allocation identity, liveness, extent, address, writability,
contents and initialization in allocation-identity coordinates. For live incoming
objects these are actual physical byte observations. For dead identities they
are retained ghost history snapshots and non-formation facts. A new private
allocation may reuse a dead object's physical address and overwrite its physical
bytes; the rule explicitly does not claim those freed physical bytes unchanged.
The new allocation has a different identity from the retained history. It does not impose an
integer/pointer type restriction on incoming memory and does not pretend that
the current two-constructor `Heap::cell` encodes arbitrary Typed float/union/byte
state. The actual private integer/receiver projection is used for scalar and
safety obligations. C local scalar assignment captures the result before
destruction; no pointer escapes or is observed after release in the exact checked
whole source body.

Fresh automatic administrative storage is also explicit: constructor/data/
reserve/destructor parameter copies, the positive fill-loop counter `k`, local
pointer `saved` and the captured scalar. Their entry, initialization, counter
updates and scope-end transitions preserve the same incoming observer. They form
a separate private source-store component that is existentially hidden; they do
not silently consume the selected receiver/buffer `Heap.next` counter. The caller
count parameter already exists at entry and is read-only. Initializing `saved`
from the exact pure data-field return is checked separately from initializing
the pointee and initializing the later captured return scalar.

Zero count initializes the receiver, performs no buffer expression or read,
captures zero, executes null release and ends receiver storage. Positive count
uses the actual constructor body/loop obligations to establish fresh private
storage, count=capacity and filled initialized element0=7. The original reserve
argument is count, so the growth branch is false. The scalar is captured before
the actual buffer release and receiver scope end. Nonnegative signed32 count
widens exactly into the pinned 64-bit size domain and is below the model maximum;
the source multiplication and loop arithmetic have the existing complete
constructor numeric proof dependency. The fill loop is finite; the observation
theorem remains conditional on modeled normal return and makes no allocator or
hardware termination claim.

The 17-entry ordinary-source ledger accounts for every obligation in the retained
projected-C diagnostic, including its scalar/access/init/representation/frame
and constructor-entry duties. It derives their source facts from the direct
rule and exact scientific targets. The seven external native goals and ten
internal Qed goals remain supplemental conditional observations; their modular
constructor post-state is not a source ownership or nonvacuity theorem. Four
smoke outcomes have no proof credit. The original entry refusal and reader
`not_proven` remain unchanged. Native WP33's unsupported freeability/lifetime
facts are handled only by the separate source-allocation/release rule and its
required mathematical dependencies.

The required scientific bundle is complete constructor35, destructor11,
private-frame9, four unchanged successful gluing duties, and the new 23 exact
positive conjunctions. Unchanged components may use content-identical accepted
evidence with their actual historical method/compiler/checker identities.
Neither old records nor current admission are relabeled by a matching name.
The module does not yet validate or admit that bundle. Independent interpretation
review and a concrete evidence-binding policy remain required; the source and
caller launch gate refuses unconditionally. Hashes and acceptance strings alone
cannot establish the source theorem.

The separate `original-obligation-ledger-v1.json` also reconstructs every goal
in the original generation-only census: 24 ordinary obligations, including all
13 frame partitions, and nine smoke obligations with no proof credit. It
explicitly names the source reconstruction of the original modular data-return
initialization and original destructor freeability duties. That original-to-
direct-source ledger is integrated in the successor production certificate and
awaits independent review; none of those
original duties is discharged merely because projection removes its native goal.

The compiler-free public RED had two missing-module failures. GREEN exercises the
public artifact and nine tampering controls for an incomplete incoming observer,
removed cleanup, pointer escape, missing event, missing original census, omitted
alias initialization, omitted administrative storage, a false dead-physical-byte
claim and an extra file. The retained
harness uses the unchanged original lowering, rejects all native/process calls,
and reports two passing tests with no external execution. The earlier canonical
drafts remain retained; the successor packet is `inert-reviewed-working-source-v3`.
