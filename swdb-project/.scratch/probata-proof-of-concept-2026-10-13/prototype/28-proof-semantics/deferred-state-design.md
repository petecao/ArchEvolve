# Deferred state prototype

Created: 2026-10-15 ET. Ticket28 remains claimed and incomplete.

`deferred_state.py::render_header()` emits a bounded C value engine.
`command_state.py::render_header(value_header)` adds command completion,
ownership, explicit tile-ID waits, region stalls and CPU footprint checks.
These are prototype APIs, exercised by native synthetic C11 callers. They are
not imported by the production proof path and do not constitute semantics0.2.

Read nodes keep actual values from their issue-to-cover interval. Known-cell
reads capture the issue value and subsequent writes. An unresolved index captures
a producer version, a logical issue image and a position in the actual write
log; cover settles the index before reconstructing that cell's value interval.
No placeholder index is dereferenced. A read picks once and retains that value.
Independent read choices overapproximate correlations; they are not a packet
schedule and do not establish a replayable hardware counterexample.

Producer IDs are immutable and strictly precede their consumers. Settlement uses
an explicit bounded stack. Conditional expressions settle the condition before
evaluating only the selected branch. This skips inactive arithmetic or memory
operands; it never cancels a separately issued command. Command completion is
separate from knowing an output value: a constant-valued command still has
pending hazards until covered.

Tile numbers belong to one global pool. Software ownership checks every physical
half of a four- or eight-byte operand. Hardware comparisons use separate explicit
starting-ID masks, following `IF.cc:193-218` at
`e4fc4afdf894f295442cef3604667a469fab8e62`. Waiting on the second physical half
does not cover a command whose explicit ID is the first half. Waits have no
thread-owner filter. Same-region read/write conflicts cover prior commands from
either thread; read/read and another assigned region do not. A readiness query
can return zero or one while matching commands are pending; only one covers.
There is no polling fairness or termination premise.

CPU memory checks distinguish reads and writes. A same-thread CPU write conflicts
with a pending device read, while another thread's successful CAS contributes an
actual write to the interval. A failed CAS only updates its expected operand.
Any CPU access conflicts with a pending store's full physical-line footprint.
`dxc_store_span` computes that envelope with checked address arithmetic; its line
size and physical address domain are explicit inputs. It does not infer physical
addresses from C object validity or distinguish physical lines by allocation ID.

The native tests use fatal check callbacks, bounded enumerated choices, and
ASan/UBSan under the shared workerB and 8GiB/time guard. Final22/22 controls pass
in8.11s at205,455,360B peak. Fourteen retained RED profiles precede the individual
slices. Every final native unit, executable, compiler command, runtime identity,
actual C dependency header and result is retained and hashed in
[the compact receipt](../../evidence/t28-deferred-state-initial-controls-20261015.json).
No actual formal tool, public `prove` result, whole-interface behavior or native
link-DSO closure is claimed.

Integration obligations remain substantial: complete source-bound per-call/type
wrappers, explicit runtime/type identities, region registration and F2, checked
source access-to-cell/physical-span mappings, alias/typed-bit-image coherence,
deferred store/RMW effects and duplicate-entry order, command dependencies,
conditional action footprints, and formal IEEE relations. Candidate source must
not be able to call private helpers or bypass preparation/binding. Bounds and
model check callbacks need proof-path classification; exhaustion must become a
domain/capacity failure, not a hardware refutation. The current default C
`assert` macro is used only by controlled native builds without `NDEBUG`.
The hardware's defined uint32 index-offset wrap must be preserved separately
from ordinary typed-array correspondence checks, which callers must discharge.

No library0.1 bytes have changed. No new current library version is installed.

## Numeric actions successor — 2026-10-15 ET

The prototype now composes the independently reviewed raw-bit numeric helper
with deferred nodes. Source dtype/opcode checks apply even to inactive calls;
arithmetic checks apply only when the selected expression executes. Missing
runtime policies and arithmetic failures retain their helper status guards.
All six scalar ADD examples retain their integer/float bit representation.
This supplies no source ABI certificate or formal IEEE relation.

Command dependencies cover producers at consumer completion, without settling
their history when the consumer is issued. Store actions wait for captured
producer values. RMW actions publish old-result nodes once; false conditions
preserve supplied prior tile payload. Duplicate entries use a conservative
arbitrary permutation, with old values taken from progressively updated copied
values, following `IndirectAccess.cc:898-940`. There is no global ascending lane
order claim. A later wait cannot repeat an effect or rewrite an observed value.

These per-entry logical writes are observational completion effects under the
full-line no-interference premise. They are not claims that intermediate copied
buffer values become externally visible memory events. The command layer now
also rejects unresolved device conflicts on overlapping physical store lines
across distinct assigned regions. Checked source/F2/physical mapping is still
needed to establish that an admitted pending read cannot observe an internal
write sequence. General overlapping packet schedules remain unsupported.

The final successor profile passes36/36 native controls in12.74s at208,879,616B
peak. Its36 compiler/header/runtime/native receipts rehash without errors;
seven new genuine RED profiles precede the added slices. See
[the exact successor receipt](../../evidence/t28-deferred-actions-numeric-controls-20261015.json).
This supersedes none of the original22-record source pins. Production proof
paths and library0.1 remain unchanged. Public proof, source mapping, complete
call/type and tile-image acceptance remain open. Readiness still permits
unbounded polling: termination needs a separate source/trust-bound progress
domain; no extra wait or desired-postcondition assumption has been introduced.

## Region/address successor — 2026-10-15 ET

`region_state.py` follows `MAA.cc:200-241`: registration has the source's
one-sided overlap refusal and lookup returns the first containing ID. F2 checks
the complete logical span against the base-selected ID, including earlier-ID
interference. The preparation bridge checks logical membership before invoking
command stalls and preserves the separate full physical hazard span. Distinct
logical regions inside one physical store line therefore retain a conflict;
registration never shrinks a physical write footprint.

The raw indirect-address helper reproduces `IndirectAccess.cc:492-494` with the
int32 word-size ABI from `IndirectAccess.hh:113`: uint32 multiplication wraps
before widening, and unsigned64 Addr addition can wrap too. The ordinary-array
no-offset-wrap condition is a separate checked correspondence obligation. It is
not source UB, an assumed equation, or a strengthened original-unit precondition.
Object/translation/Addr and physical-line correspondence remain separate.

Final43/43 native controls pass in15.30s at209,747,968B peak, with43 rehashed
native/compiler/header receipts and no pin errors. Three new RED profiles are
retained. An intermediate38-case run changed the test file after collection;
it is excluded from exact-source acceptance. The final43-case source was held
stationary. [Exact evidence](../../evidence/t28-region-address-controls-20261015.json).
Source public wrappers, reserved six MMIO regions and full geometry/type/ABI
bindings remain incomplete; no production proof or current0.2claim is made.
The approved prospective progress rule is an explicitly owned environment
assumption, pending human freeze review59, not a proved source liveness fact.
