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
