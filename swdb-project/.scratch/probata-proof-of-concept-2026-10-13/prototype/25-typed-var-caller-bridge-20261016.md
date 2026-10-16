# Caller bridge: selected Typed+Var semantics — 2026-10-16 ET

**The existing source hashes do not prove a caller correspondence.** The next
original no-growth generation diagnostic must expose the actual terms before
the bridge is connected to a public caller record.

| Operation | Selected primary implementation | Required relation |
|---|---|---|
| Receiver and buffer positions | `MemTyped.ml:236–269`; `Ctypes.ml:522–536` | Typed receiver offsets 0/1/2 and extent 3 map to bytes 0/8/16 and extent 24. Int element `j` maps from one-cell stride to byte offset `4*j`. Preserve pointer identity separately. |
| Values and initialization | `MemTyped.ml:996–1014`; `MemVar.ml:513–570` | Signed32, unsigned64, pointer and initialization chunks are distinct. MemVar can use SSA/record variables. A value store and its initialization update require separate correspondence; pointer cells never become integer projections. |
| Automatic scope | `MemTyped.ml:1083–1095`; `MemVar.ml:990–1035` | Raw Typed scope updates allocation extent only. MemVar updates `SALLOC` and conditionally `SINIT`. Do not infer an initialization reset from raw Typed scope. Derive the relevant actual variable class and stores from generated tasks. |
| Integer bounds and selected wrapper | `MemTyped.ml:940–975`; `Cint.ml:400–428`; `Factory.ml:235–237,354–359` | Machine integer chunks have source-kind bounds. Default Typed/Fits is wrapped by Var; `+real` does not remove that wrapper. Neither Natural integer semantics nor identity byte-offset assumptions can substitute. |

All paths are relative to the selected `lib/frama-c-wp/core/`. The six source
hashes are pinned in the prospective source view and original generation packet.
The observations above came from reading the selected local package source, not
from a new formal result. The actual remote package must match before use.

The bridge should relate the source-created receiver, its backing int buffer and
the captured alias to the custom Heap while retaining an arbitrary incoming heap.
For admitted source-created slots, the relation includes equations such as
`Heap.contents(H,receiver,8) = Integer(source_u64[receiver_base,1])` and
`Heap.contents(H,buffer,4*j) = Integer(source_i32[buffer_base,j])`. Initialization
has its own relation, established by actual stores and their initialization
updates. These equations are design obligations, not added caller premises.
Before a slot's defining stores, avoid demanding unsupported initial-map facts.
The actual constructor fill must establish the complete post-constructor image.

A source-local identity renaming must be injective and tied to actual creation
events and the existing uniform successful-allocation relation. The protocol has
no address-to-integer observation; `int_of_addr` is not a physical-address bridge.
The saved alias retains its captured identity when growth replaces the current
buffer. Source allocation and release events must separately drive custom
allocation history: the selected WP memory support supplies no theorem that a
dynamic `free` performs that lifetime update.

Installed `memaddr.mlw`, `memory.mlw`, `cint.mlw` and standard `map.mlw` provide
definitional addresses, map updates, bounds and frame vocabulary. They can express
local store/load/frame correspondence without project ownership axioms. They do
not provide an importable OCaml `MemTyped.sigma` or a whole-source simulation
theorem. A relation over unconstrained maps alone leaves the connection to actual
generated terms missing. New standard-support imports require prospective
source/closure review; existing standalone heap foundation admission is not an
automatic admission of those imports.

The no-growth execution must retain construction/fill, the actual alias capture,
the checked reserve branch, guarded scalar capture, destructor, automatic scope
end and the scalar return. The final theorem must preserve incoming live objects
and bind the result to seven/zero. Current qualified body dependencies, exact
contract placement, complete ordinary/smoke reports and source/runtime/task
correspondence all remain mandatory. The new source view's launch refusal keeps
this boundary explicit until these duties are implemented and checked.
