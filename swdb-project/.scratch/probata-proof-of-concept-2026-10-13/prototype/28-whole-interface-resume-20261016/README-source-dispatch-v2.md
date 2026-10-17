# Source dispatch and CPU pointer bridge

2026-10-16 ET. Compiler-free implementation/preparation. No production edits,
project imports, compiler, native executable, solver, verifier or SSH were used
for this slice. Owned source/model/MMIO semantics are the accepted premise;
optional hardware or source-body refinement is not a required gate.

`source_dispatch_v2.py` now implements a source-call consumer and C emitters:

- `bind_dispatch` freshly rechecks the exact independently reviewed V3 full-TU
  binding, source/header/body/ABI identity and argument subtrees. It emits only a
  fixed private route with checked staged identifiers and an owned thread value.
  Pinned literal default arguments are emitted as `-1`; an unknown exact selector
  type reaches the fixed MAX6 helper. No name-only substitution or candidate
  builder callback is accepted.
- `render_routes` covers all 27 declarations / 26 names: 132 exact six-type or
  non-template instances, plus one shared unsupported-type selector. Scalar input
  and result conversions copy object representations with `memcpy`, including
  signed integers and floating-point values. Source integer/enum results preserve
  their modeled values. Pointer arguments/results use private descriptors.
- `render_direct_families` specializes the 11 actual source operand maps into
  direct prepare → fixed family value builder → bind calls. This prospective
  source call graph has no value-builder function-pointer seam. The independently
  reviewed private native86 packet remains unchanged.
- `prepare_atlas` allocates one stable scalar cell per physical typed location
  after collecting all source objects/views. Partial aliases therefore reuse
  history cells regardless of registration order. Inconsistent guest projections
  and overlapping mixed-width/type views refuse. Registration grants no value,
  initializedness, ownership or history event.
- `render_pointer_bridge` routes ordinary CPU loads/stores through the same cells
  and physical spans used by memory commands. Tile accesses call the existing
  byte-coherent tile model, preserving pair ownership/pending-command checks and
  initializedness. Pointer formation checks bounds/overflow, allows one-past
  formation and rejects one-past dereference. Modeled guest addresses are never
  cast into host pointers.

The generated `*_synthetic_v1.h` files use an explicitly illustrative little-
endian x86_64 ABI/address layout. They are source assembly controls, not actual
compiler observations. The emitter accepts an actual future source-certified ABI
and object mapping instead. `source_direct_families_v1.h` is ABI-independent;
every header retains exact source line/body pins. All 49 frozen value input/output
pins are rechecked before assembly, and every slice input is rechecked afterward.

Fourteen pure tests pass, including 132 synthetic call dispatches, all 132 route
instances, all 11 direct family specializations, exact source defaults, MAX6,
partial physical aliases, order-independent cell assignment, mixed-type/width
refusals, malformed staging/subtree/source refusals and CPU/device cell/span
relationships. They execute only stdlib and owned AST-projected source. They do
not compile the emitted C or establish any real Clang AST/source correlation.

`source_call_fixture_v1.cpp` is an inert original-source input that exercises all
26 names and both get_new_reg declarations, using separate uint32/int32 ordinary
arrays and cacheable tile views. It contains initialization, all 11 families,
waits, scalar/CPU observations and assertions. It is not a recorded positive
verdict. Its illustrative object addresses and ABI require a new actual producer
certificate before this fixture may be submitted as a public source case.

The private pointer domain is deliberately explicit. Ordinary arrays are live,
nonempty bounded scalar objects, with source-owned provenance/lifetime and exact
guest/physical projections. Partial aliases of the same type preserve one
history; mixed-width/type overlapping views require a future byte-coherent
ordinary-memory extension. Tile pointer arithmetic is limited to the two-element
value prefix. Noncacheable address formation is modeled, but CPU dereference
still refuses until that separate MMIO access policy is supplied. Pointer casts,
escapes, subtraction/comparison, atomics and lifetime changes need their own
complete source producer route or a refusal. These restrictions preserve the
current model; they never turn into assumptions that accept unsupported input.

Memory command footprints conservatively cover the whole remaining source object
from the passed pointer. This avoids evaluating deferred RF bounds/indices at
issue. The existing first-ID/F2 region lookup, full-line store envelope, ownership,
counted readiness, immutable input versions, source undefinedness and numeric
checks remain in the preparation/value backends. Zero-length streams and inactive
empty commands remain outside this nonempty footprint slice.

Print emits a bounded typed observation trace through a fixed direct recorder;
the public consumer must compare its source formatting/I/O projection if printed
bytes are in the observation scope. No candidate callback supplies print values.

The remaining production seams are concrete:

| Seam | Proposed narrow integration |
| --- | --- |
| Actual source/ABI producer | New `dx100_whole_interface_source` module retains original complete TU, resolved declaration IDs/bodies, Clang input/recipe closure and actual ABI/object layout; rechecks immediately before dispatch and at unit finalization. |
| Typed call routing | A new source-kind branch in `c_lowering.Printer._call`, alongside existing source policies, stages original expressions once with their C++ evaluation/undefinedness rules and records this exact binding. No global summary/body bypass. |
| Pointer and CPU effects | Add a scoped descriptor type only for certified DX100 pointers. Ordinary local-array initialization, dereference, subscript and writes must reach the shared bridge; unsupported casts/escapes/lifetimes refuse. Existing `_pointer_access`, `_pointer_formation`, `address`, tile access and `cpu_effects` receipts are the relevant seams. |
| Model and method | A new whole-interface model module and a new0.2 semantics entry select the owned fixed backends/direct routes, geometry and observation policy. Existing default source substitution/provenance checks remain intact. |
| Actual public acceptance | Review/freeze the producer/integration; root admits real compiler/model/public synthetic positive and negative jobs, then independently reconciles source/term/property/DAG/CPU-access/record evidence and both same/other-thread histories. |

The current production files were read only. Any changes to `c_lowering`,
`proof_semantics`, model registration or public tests must be announced and owned
with root before edits. This source packet alone establishes no actual source
admission, public/formal success, current0.2 or full ticket28 acceptance.

V2 closes the independent ordinary-to-MMIO alias finding. Both guest and physical
ordinary spans must be disjoint from the complete six-region MMIO window derived
from pinned MAA_gem5.hpp:71-91 and the unchanged backend: 16-GiB base,32 tiles,
32 registers,16384 tile words. The emitted runtime checks the same profile and
exclusion before CPU or command projection, including pre-alloc CPU initialization.
Actual source geometry or a different MMIO physical mapping must match this
explicit profile or refuse; no arbitrary source producer flag bypasses it. V1,
value and native packets are preserved.
