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

## Typed physical byte image — 2026-10-16 ET

`tile_image.py` separates the source physical uint32 tile stride from the bounded
value prefix. A sparse byte image stores immutable producer IDs and byte offsets;
8-byte and neighboring4-byte views share those bytes. It binds command outputs
without settling them, so a narrower dependent operation captures the producer
version and later CPU writes cannot rewrite an observed scalar. Native controls
use an explicit little-endian toy geometry (8 source words,6 prefix elements), not
the actual default16384-word source geometry. All six scalar helpers copy through
legal scalar objects with `memcpy`; this is no certificate for an arbitrary T*
cast, source pointer escape, platform ABI or IEEE proof relation.

The command layer now rejects read/write physical-half alias inside one command,
even when explicit starting IDs differ. This is a software no-alias obligation;
no even-ID hardware restriction or extra second-half wait is invented. Output
binding requires the constructing command, its explicit starting output and both
physical halves for8bytes. CPU observations still enforce pending-output and
ownership guards. Byte initializedness and sparse capacity are checked; command
output views may remain unresolved until their covering completion.

Final53/53 native C11/C++17 controls pass under ASan/UBSan and the shared workerB
8GiB guard (19.56s,221495296B peak). Four genuine RED profiles and all retained
native source/executable/header references are pinned in
[the compact receipt](../../evidence/t28-tile-byte-image-controls-20261016.json).
This is a backend prototype slice, not public proof acceptance. Source CPU pointer
routing, inactive preserved uninitialized payloads, full wrappers/register/setup
semantics, source ABI/geometry binding, formal IEEE relations and the explicitly
owned finite-progress assumption remain required before whole28 closure.

## Inactive byte preservation — 2026-10-16 ET

Uninitialized tile bytes now have an immutable undefined value node. Capturing a
producer version is not a value read; evaluation of a selected undefined byte
still fails initializedness. Inactive RMW completion publishes a descending,
once-only alias to the captured old version without evaluating it, and its
completion root evaluates neither inactive index/value nor preserved output.
This also avoids forcing an unnecessary value read merely to finish a command.

`dxp_bind_conditional_output` preserves each prior byte independently. In
particular, a false8-byte output can preserve initialized lower32bits and undefined
upper32bits: the narrower read succeeds and the full64-bit read fails. It never
fills undefined bytes with zero. The active branch writes the complete payload;
an inactive unfulfilled payload node is not evaluated. Source wrappers must use
the call-specific rule (ALU false lanes write zero; fake stream/indirect data
preserve payload), not apply this preservation rule universally. Source CPU
routing, complete wrappers and public/formal admission remain separate work.

Two genuine RED profiles precede final58/58 native controls under ASan/UBSan,
workerB and the8GiB cap (22.06s,222150656B peak), with all raw source/executable/
header references pinned in
[the preservation receipt](../../evidence/t28-inactive-byte-preservation-controls-20261016.json).

## Register byte state and source write stalls — 2026-10-16 ET

`register_state.py` supplies dense raw-byte versions, the global source allocation
counter, initialized/uninitialized allocation and six dtype widths. The explicit
source scalar alignment vector is checked against the compiling C/C++ types.
Allocation can return an odd8-byte starting ID; only the later typed MMIO/RF access
checks alignment. Exact unchanged RF class/constructor excerpts at the pinned
revision reproduce the misaligned64-bit read under the retained native8-byte ABI.
This is source C++ undefined behavior on that ABI, not a hardware allocation rule.

`IF::canPushRegister` blocks a CPU register write whose starting ID matches any
explicit register operand of a pending command. The backend performs those covers
before replacing bytes. Conflicts visible only through an8-byte second half
refuse as conservative software obligations; neither hardware pair expansion nor
a covering CPU register read is invented. Command register roles similarly
refuse unresolved cross-command RF races. Software ownership here is a declared
caller isolation domain, not a claim that hardware enforces register ownership.
Counter reinitialization preserves values, pending commands and ownership; the
same owner may reuse an allocated ID, while another owner cannot silently take it.

Final75/75 native controls pass with C11/C++17 ASan/UBSan, workerB and8GiB cap
(26.44s,222347264B peak). One case deliberately expects the pinned RF source's
UBSan misalignment failure; it is not clean-source agreement. Its initial Mac
abort/exit harness mismatch is retained and explicitly excluded from final
acceptance. Final per-case receipts record deterministic sanitizer options.
[Exact source/RED/native/resource pins](../../evidence/t28-register-state-controls-20261016.json).
Source-bound wrappers/setup, full pointer admission, formal IEEE bit-image
coherence and unbounded progress/public proofs remain active work. The read-only
[installed-tool source map](../../evidence/t28-wp-ieee-progress-source-map-20261016.md)
records supported IEEE operations and the unsupported ACSL model-field rank route.

## Exact setup and source geometry — 2026-10-16 ET

`setup_state.py` computes the source six MMIO intervals, including both full
physical tile mappings. Native controls use32tiles/32registers and the default
16384-word source stride, independently of the two-element value prefix. This
64-bit role-mask prototype supports4/8-core configurations and explicitly refuses
the16-core128-tile geometry. Source/target configuration admission remains work.

`alloc_MAA` clears/re-registers the six reserved regions and resets next-region
ID to6; it does not reset host tile/register counters, byte payloads or pending
commands. `init_MAA` resets only host counters/next region. Existing user range
definitions, payloads, ownership and pending commands survive. The source int8
region counter narrows127+1 to-128 in the explicit static-checked native
conversion profile; it is not signed-overflow UB. A subsequent negative hardware
ID refuses, and clear restores the six reserved ranges/counter. Whole-span F2
and physical store-line domains remain separate from this registration state.

Source boundary corrections for future wrappers: `CpuSidePort.cc` implements no
`SPD_DATA_NONCACHEABLE_RANGE` case for either reads or writes. Its WriteReq comment
says writes should use that range, but there is no corresponding branch; do not
model an implemented operation from the comment. The getter returns a pointer;
unsupported dereferences must refuse absent another independently established
routing path. Cacheable writes use ReadExReq acquisition and WritebackDirty.
`SPD::getSize` requires Finished status and is not a wait. SPD/RF constructors
zero payloads and initial sizes, but alloc/init do not rerun those constructors.
Our harness unestablished-byte state denotes a conservative arbitrary preexisting
device entry, not a theorem that fresh gem5 payloads are uninitialized. A fresh
zero entry state needs its own constructor/source certificate.

Final81/81 native controls pass, including one deliberately expected RF alignment
UB case, under the recorded sanitizer options/workerB/8GiB guard
(29.27s,222953472B peak).
[Exact source/RED/native/resource pins](../../evidence/t28-setup-state-controls-20261016.json).
The API/source CPU wrappers, typed IEEE coherence, separate unbounded rank/source
simulation and public actual acceptance remain incomplete; no current0.2 exists.
