# Exact selected DX100 source observation

2026-10-16 ET. **Source-selection/compiler preparation only. Allocator refinement,
Typed initializedness/lifetime, full source/TD proof and counted admission remain
refused.** Earlier canonical and historical source/evidence freezes are unchanged.

`selected_source.py` first checks physical bytes, before decoding or output. It
binds the exact e4fc4af BFS source and source-header manifest, the actual project
offload include and lowering header, and both real composition functions. It
executes only the pinned `scalar_source` definition from
`scripts/prepare_dx100_scalar_snapshot.py` and `peter_source` definition from
`swdb/certification.py`. This follows the real scalar-only source derivation and
offload insertion; patch hunk offsets alone are not selected-TU evidence. Other
kernel/example implementation files are neither read nor copied.

The public source-only command materializes a fresh external selected TU and
header tree. `--compiler-qualify`, run only under shared B/time/RSS guard, then
parses that entire TU with the physically pinned Clang driver, C++11, OpenMP,
pthread and FUNC. Ambient include/config selectors are refused, driver defaults
are disabled, and the known macOS27 SDK is explicit and physically pinned. No
version/resource-directory/config probe or installation change is used. API
defaults remain NUM_CORES 4/TILE_SIZE 16384; NUM_CORES is capacity, and does not
establish the proposed threads=1 runtime caller restriction.

The compiler retains full token, preprocessor, macro, dependency and TDStep/
QueueBuffer AST records. Discovery preprocessing finds the physical include
closure; every subsequent syntax/macro/token/AST step is bracketed by exact
rehashes of all 901 discovered files. Inputs and staged headers are checked again
afterward. This is filesystem sampling, not atomic containment. The exact fork
`sliding_queue.h` must be the selected physical dependency, not merely a matching
class name in an unrelated clean probe. The selected main has SHA256
`093c56b91837122380fd5e66766c92947e5f1c5194dd4c038936bc28934864dc`.

The actual main-TU declaration resolves `QueueBuffer<NodeID>` to
`QueueBuffer<int>`, with the exact `SlidingQueue<int>&, size_t` constructor and
default argument 16384. The selected class definition has the actual fields
`in:size_t`, `local_queue:int*`, `sq:SlidingQueue<int>&` and
`local_size:const size_t`. Its array `new` has no payload initializer, and the
destructor uses array delete. These are observations of selected source, not a
proof of allocator success, freshness masks or generic replacement-allocator
semantics. Actual typed C++ array creation supplies language alignment/liveness
on successful normal return; transferring those facts to the hand model remains
a source-refinement obligation. Arbitrary incoming pointers/Graph objects do not
gain those facts from these observations.

The exact TDStep local variable has two push uses and one final flush use.
OpenMP emits two additional implicit for-loop capture references at the same
variable/source locations. IDs are compared only within one retained TDStep AST;
each capture must bind an already verified same-variable/source-range push.
Persistent bindings use selected main SHA, exact function, node kinds and
exclusive source byte ranges. No compiler declaration ID is reused across AST
dumps/processes; raw IDs are retained only as dump-local diagnostics. Captures
are explicitly retained, and there is no generic noescape or OpenMP theorem.
The source's private class fields and exact call/scope structure support the
proposed restricted nonescape/adjacent-retirement argument; that argument still
needs independent source-refinement review.

The final public profile has 35 passing compiler/pure controls in 14.087 seconds,
161.34MiB under an 8GiB/120-second guard. It compiles source without executing a
program. Actual constructor/default/new initializer/type and unmatched-capture
mutations are checked against the retained compiler AST; coherent renaming of
IDs within that dump preserves the stable result. Five real producer-header
mutation families and two actual offload-unit mutation families refuse before
output. All original, historical and canonical hand-model bytes remain unchanged.

Retained development receipts distinguish feature absence from semantic failure:
the initial public-command RED was an absent feature, not evidence of a false
existing source contract. The first compiler-reader profile refused implicit
OpenMP captures; its successor binds and retains them. A later configuration
hardening profile exposed the missing SDK after disabling driver defaults; its
successor supplies the explicit pinned SDK. No failed profile is counted as
initializedness, proof or successful source correspondence evidence. Compact
pins and complete raw-artifact manifest are in
`../../evidence/t07-selected-source-preparation-20261016.json`.

The observation qualifies this local macOS compiler/source selection. It does
not establish remote Linux/GEM5 ABI or execution, linker allocator replacement,
exceptions/failure behavior, arbitrary constructor sizes, multiple overlapping
buffer lifetimes, general OpenMP execution, physical C++/C struct/reference
layout, member/helper value and frame refinement, atomic/device semantics,
default graph-builder invariants or the unsupported `-m`/raw-Graph families.
The incoming SlidingQueue remains symbolic `num_nodes`; its producer/caller
domain is not replaced by the private 16384-element buffer.

The private-array generator still refuses allocator correspondence. Source
selection, a compiler `new[]` observation and native agreement cannot establish
WP's actual address-taken-array `T_init` mapping or scope reentry/retirement.
The separately reviewed ten-unit generation packet remains rooted in immutable
canonical Git blobs, and this source package does not modify or execute it.
