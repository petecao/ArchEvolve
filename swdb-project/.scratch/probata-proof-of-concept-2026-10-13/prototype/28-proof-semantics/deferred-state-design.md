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
