# Receiver state and harness draws, proposal V1

2026-10-16 ET. This is source-only preparation for
`dx100-whole-interface-source-v1` and
`dx100-whole-interface-checked-body-1`. It installs no production consumer and
claims no hardware refinement, current 0.2 entry, or ticket completion.

`prepare(OwnedSelection(Pin(path, bytes, sha256)))` returns immutable receiver C,
receiver-binding JSON, draw-plan JSON and integration-plan JSON. The launch
owner independently selects the policy pin. Matching bytes and an owner label
cannot attest that the execution context is true. The unfilled templates
deliberately refuse preparation.

The exact context receipt records six owned premises: fresh unchanged host
globals; exclusive control of the modeled DX100 instance; quiescent entry;
valid initial Finished/unknown-size metadata; original automatic allocation
origin and lifetime; and selected physical/compiler/numeric policies. Fresh C++
static initialization establishes only the twelve source host values. It does
not establish any device premise. Initial sizes remain unknown in 0..16384;
the first capture uses the unchanged model choice. Numeric flags come from a
separate exact runtime-selection receipt and physical pins. A value of zero
leaves the corresponding backend policy unavailable.

The generated one-shot setup checks untouched model counters and initializedness.
It changes only ghost ownership, unknown-size sentinels, allocation-origin
bookkeeping and explicitly selected numeric flags. It neither writes payload
values nor calls reset, alloc or init. Model payload bytes remain unavailable
until actual modeled source writes initialize them. Counts and histories are
never cleared. The two derived instruction pointer offsets apply only after an
actual source allocation; their original initial values are semantic nulls.

Ordinary allocations start inactive. Fixed declaration-specific enter/leave
hooks track allocation origin and live scope. A require hook checks live storage
and the admitted thread domain. It does not require the accessing thread to be
the allocation-origin thread: another modeled thread's CAS/history access stays
subject to the existing memory/command rules. This first fixture profile refuses
local aliases/reuse and arrays outside the fixed 64-cell backend capacity.

Every choice-table element is assigned `(uint32_t)swdb_next()` before the source
unit. Independent full signed-64 oracle slots cover the full uint32 domain.
The producer must add every ordered draw to `Plan`, count it before fixing
capacity, and retain the same oracle sequence in CBMC, differential and replay.
The exact model V2 zero-choice and choice-exhaustion checks and existing oracle
capacity check remain fatal properties. Budget failure is never assumed away.

Integration is still required: wire the fixed enter hook before each original
array initializer; require live allocations at every ordinary CPU access and
device footprint; preserve pending-command checks on all exits; and invoke the
one-shot preparation before the single source entry. The existing public
compiler/TU/ABI/source/CPU/lifetime/RTE/unwinding/method gates must independently
validate their artifacts. This emitter hashes opaque full-TU/ABI/capture inputs;
it does not reimplement those certificate producers or infer their execution.

Seventeen deterministic stdlib controls pass with no child/tool/network execution.
Their compiler observations, ABI/capture documents and context receipts are
explicitly synthetic protocol stand-ins. They do not constitute an actual
receiver context or scientific evaluation. Shared production and predecessors
are unchanged; independent review and root admission remain pending.
