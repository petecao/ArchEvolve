# Whole-interface proof semantics implementation

Created: 2026-10-15 ET. Ticket28 is claimed and incomplete.

The public seams are `swdb validate --library`, `swdb prove` and
`swdb candidate-level`, already authorized for this ticket. Controls run under
the shared workerB scheduling wrapper plus their own 8GiB/time watchdog. Actual
Frama-C/WP/CBMC and remote jobs require coordinator admission.

First vertical slice: validation of both immutable upstream header byte hashes,
all 26 names / 27 declarations (including helpers and the allocation overload),
and coverage by distinct per-name/overload contracts. The old use inventory is
separate. Three public RED/GREEN cycles reproduce and reject smaller-name-set and
missing-initialized-overload acceptance. Final scripted controls: 18 passed,
tools disabled. Exact logs/resources/source pins:
[declaration controls](../../evidence/t28-declaration-inventory-controls-20261015.json).

This does not supply semantics0.2 or establish typed implementation agreement.
The complete-header validation fixture deliberately uses unreachable contracts
for unimplemented calls: it proves no call behavior. Typed contract/source
signature binding, type/opcode domains, paired storage, ownership, exact region
selection/F2, history values and full cache-line store hazards remain work.
No new semantics entry becomes current before these boundaries are concrete.
The complete upstream inventory and source bytes are independently retained at
`/private/tmp/probata-ticket28-complete-interface-inventory-20261015.{md,json}` and
`/private/tmp/probata-ticket28-interface-upstream-20261015/`.

Assumptions and implementation choices: preserve all semantics0.1 bytes; new
version/sequence/files; fixed sequential two-thread scenarios precede general
concurrency; unsupported type/opcode/geometry combinations fail closed. Device
consumers capture producer-version dependencies without settling history at
issue. Future CAS must never change values already observed. Pending stores/RMW
must retain conservative full physical-line interference unless an explicit,
checked address-space/line correspondence supports greater precision. A line
size or virtual-to-physical relation is never inferred from C object validity.

Typed call ABI slice — 2026-10-15 ET: public `swdb lower` is the existing compiler
prerequisite seam for the authorized synthetic `prove` cases. RED reproduced
both initialized/uninitialized template allocation sharing a C symbol and six
zero-argument type specializations silently collapsing to the first type. The
repair resolves the actual source call in one full-TU AST, using exact file/span
and its enclosing stable mangled function, then follows its declaration ID only
inside that TU. Different-arity template families receive deterministic arity
suffixes, independent of first-use order. Existing single-arity/non-template
names remain. Same-arity collisions and unsupported macro coordinates fail closed.

Ten compiler/native controls pass, including both call orders, nested template
owners, the six distinct scalar types and native C++/C width results under
ASan/UBSan, plus existing deterministic/summary/template controls. No actual
formal tool ran. [Exact sources, outputs and resources](../../evidence/t28-typed-call-abi-controls-20261015.json).
These are compiler prerequisites; no semantics0.2call behavior or whole-interface
acceptance is inferred. Full typed model/import/initializedness policy remains
pending.

Source correction: [indirect old-value alias](indirect-old-value-correction-20261015.md).
Optional old-result reads alias the progressively modified `new_data` buffer,
not the untouched response payload. Global lane/packet order remains unproven.

Composed verification — 2026-10-15 ET: after merging ticket36's configured-runtime
identity change, the combined focused profile passes28/28 (13.45s guard,
172,359,680B peak, no timeout/OOM). Exact source is `ac3301837fa16e6011c9eebf1921631064deeaec`.
[Composed sources/output/resources](../../evidence/t28-prerequisites-composed-20261015.json).
The six literal builtin types in the compiler control do not establish device
encoding: source `get_data_type` recognizes exact `int64_t`/`uint64_t` identities,
which differ between Apple and Linux headers. Semantics0.2 must bind the pinned
source/header ABI instead of treating every same-width long/long-long as one type.
