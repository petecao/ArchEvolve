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

Trust-record slice — 2026-10-15 ET: a rule may explicitly request an assumption
entry on every verdict using its version, with the rule fragment ID, exact entry
hash and literal statement. Both adapters include it on prelaunch refusals too.
Thirteen public scripted/compiler controls pass for the five required trust
entries, booleans/refused malformed markers, and `candidate-level` noncapping.
Synthetic clones and level records establish record plumbing only. Version and
WP parse stand-ins run; no actual verifier, prover or ACSL type evidence.

A public CBMC mutation RED exposed cached rule text paired with newly hashed
entry bytes. Verdict generation now requires the current file hash, a fresh
parse equal to the job's cached entry, and another matching hash. A late change
refuses the record. The WP probe in these controls occurs earlier, during
validation before its job snapshot: that changed, freshly loaded version is
recorded consistently. [Exact RED/GREEN and resource pins](../../evidence/t28-trust-record-controls-20261015.json).
All production semantics0.1 library bytes are unchanged; no semantics0.2 behavior
or whole-interface acceptance is established by this slice.

Typed instance contracts — 2026-10-15 ET: explicit canonical template arguments
and source arity select a concrete C signature and contract. Validation refuses
missing contracts, duplicate selectors/symbols, malformed metadata and omitted
overloaded header declarations. Source binding checks the actual same-TU
instantiation, deterministic emitted C name and complete C signature. Selected
instances are recorded by both adapters. No generic family contract fills a
missing type/arity. The shared trust fixture is factored without changing its
record-control assertions.

Three public REDs reproduce ignored typed contracts, ignored type selection and
an unpinned source definition inheriting a device contract. The composed focused
set passes39/39; final instance/ABI/native/template controls pass29/29 after the
checker-list update (35.23s guard,207,929,344B peak). These overlap, not68unique
cases. [Exact source/control/resource pins](../../evidence/t28-typed-instance-controls-20261015.json).
No actual formal tool runs. Body-bearing real MMIO templates still refuse:
raw header identity alone cannot certify candidate macro/typedef/trait context.
A source-bound effective-interface audit and the six device type/value domains
remain required before claiming per-call implementation behavior.

Checker closure RED: changing copied `dx100_interface.py` originally left a frozen
execution method admitted and ran the scripted command. Adding this imported
validator/contract generator to `proof_setup.CHECK_SOURCES` makes the same
mutation refuse before command/record. A fresh identity-bound method admits its
scripted fixture command. Historical2033/74 setup/facts are not upgraded.

Source typedef identity — 2026-10-15 ET: exact device types cannot be inferred
from a familiar alias name. A real native C++/C mismatch showed local `uint64_t`
meaning double becoming an integer in emitted C; a second RED covered function
returns without desugared type metadata. The lowerer now honors clang's source-node
type and requires unique source targets for unresolved alias names, including
class/global collisions. Parameter pointer metadata follows the actual lowered
type, so a pointer typedef retains its explicit primitive array domain. Reference
typedefs conservatively refuse until reference-use binding is implemented; ordinary
literal references retain their behavior.

Final49/49 compiler/native/stand-in controls pass (55.53s guard,346,636,288B peak),
including local/return/field/cast/summary paths under ASan/UBSan, both adapter
domain controls, and exact original constant atomic C/anchors/models/names.
[Source, genuine REDs, intermediate fixture misfire and final evidence](../../evidence/t28-source-typedef-identity-controls-20261015.json).
No actual formal tool ran. Existing typedef-bearing C may change to preserve its
source type; historical producer records stay scoped to their original freeze.
Semantics0.1 library bytes remain unchanged. This does not implement the new
typed DX100 state/value/history model or close ticket28.
