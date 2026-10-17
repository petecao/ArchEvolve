# Original compiler unit and new0.2 integration proposal

2026-10-16 ET. SOURCE ONLY. The original two-header API, an inert all-name caller,
an inert ABI probe and a strict consumer are now concrete. No compiler, native,
verifier, project import or network child was run for this packet.

`compiler_unit_adapter_v1.py` consumes one retained complete original TU and an
independent literal ABI probe. Every source call and callee declaration ID is
resolved in that single original TU; separate filtered function dumps cannot be
joined. The ABI probe supplies only canonical typedef identities, sizes,
alignments, representation and source geometry constants, with no cross-TU ID
use. Its exact physical source hash is mandatory. JSON duplicates, nonfinite
constants, malformed/concatenated full TUs, missing/foreign probe roots, changed
source bytes and unsupported source geometry refuse.

Location normalization preserves raw fields and fills Clang's elided file/line
state by the existing deterministic traversal. It is an explicit parser premise.
Every raw observation and normalized TU has its own hash. No capture-receipt hash
is treated as proof that a compiler actually ran. Root must independently bind
the real driver/process/recipe/dependency/input/output/runtime observation.

The prospective four-phase recipe preprocesses each original source with used
headers/dependencies, then captures full caller AST and filtered ABI literals
from frozen preprocessed sources. It uses Clang22 C++17 and the original exact
MAA.hpp/MAA_gem5.hpp headers. The 133-byte gem5 declaration-only stub is copied
from the existing initialized-register public test helper and matches its
previously pinned SHA. It provides declarations, never replacement MMIO bodies.

`source_call_fixture_v2.cpp` observes queries and CPU values into source locals
before assert macros, so interface/CPU event locations are original direct spans.
Its exact inverse to the preserved V1 fixture is retained. It still exercises all
26 names and both get_new_reg overloads. Its predicted final ordinary result is80;
this is not an actual public verdict. The independently reviewed 0.2 dispatch V2
and explicit owned MMIO rules supply the prospective model behavior.

The current 180-second/4-GiB and 128-MiB-per-file/256-MiB-total boundaries remain
explicit. Full unfiltered AST JSON may exceed them or require too much parsing
memory. This consumer refuses oversize data; it neither changes budgets nor
falls back to joining filtered declaration IDs. Any future checked streaming or
compressed full-observation producer requires its own source review and explicit
root admission. This recipe is not a ready-to-launch controller. Root still owns
actual physical/runtime/guard/lane/source/closed-environment/output admission.

The first prospective compiler fixture is root-owned and byte pinned, with
NUM_CORES4/TILE_SIZE16384 and no caller macro changes. A separate ABI probe does
**not** establish the macro/pragma configuration at each original header
definition. General caller admission must additionally check that original-TU
configuration against the modeled fixed identity-MMIO profile or refuse. This is
a concrete compiler/source configuration gate, not an optional body/hardware
theorem. No arbitrary caller receives public admission from this passive module.

Original caller code cannot refer to private model names or directly manipulate
header counters/MMIO globals behind the modeled API. The consumer rejects those
references in source-owned functions. Complete scoped pointer/CPU expression and
local-array-initialization lowering remains necessary; raw source pointers must
not bypass the shared atlas/ownership/history bridge. C++ expression evaluation
order and undefinedness remain the original lowerer's checked responsibility.

Twelve compiler-free controls pass. They cover 29 synthetic ABI roots, real-TU
protocol binding, malformed/filter-join/source/ABI/configuration refusals, fixed
budgets/recipe, source fixture inverse and private/direct-MMIO bypass refusals.
An added negative control initially exposed the missing INSTR_baseaddr name in
the bypass set; that guard was added and the retained final run passes. No actual
AST, ABI observation, source admission or public proof is claimed.

## Exact proposed ownership and minimal production changes

These are proposals. Existing production files remain untouched by this agent.

| Owner | File and exact surface | Required change |
| --- | --- | --- |
| public_review, after root coordination | New `swdb/dx100_whole_interface_source.py` | Actual original-source compiler capture/certificate producer and strict reader using the V3 same-TU binder, actual ABI, source configuration, input closure, final rechecks, reserved-name and source-call attribution gates. |
| parent ticket28 | New `swdb/dx100_whole_interface_model.py` and new0.2 model assets | Actual-ABI generation of the fixed dws routes, descriptor bridge and direct family bodies over the reviewed concrete backend; no synthetic ABI promotion. |
| parent ticket28 | New `library/proof_semantics/dx100_bfs_0_2.yaml` and isolated assets | One entry per26 names with typed/arity instances, the nonempty concrete contract relations in new-0.2-contract-design-v1.json and explicit owned MMIO/compiler/numeric rules. Preserve all0.1 bytes. |
| root + ticket25 coordination | `swdb/c_lowering.py`: `_Unit`, `_Printer._call`, scoped ctype/local/initializer/expr/address/_pointer_access/_pointer_formation paths, tool identity | Gate solely on the exact new source kind/entry, certify original full-TU binding before any replacement, stage original scalar/pointer expressions once, register concrete dws ABI, route every certified pointer/CPU use and retain ordinary/source assertions/effects. Final unit recheck and tool hash include new module/model bytes. |
| parent/root | `swdb/proof_semantics.py`: check/lowering_options/model_for and instance bindings | Recognize only the exact new source kind/model, preserve default body/substitution/provenance refusal, expose actual source certificates/model identity/26 contracts in the formal frame. |
| root admitted public fixtures | New isolated tests/helper/fixture assets | Positive80 and negative79, typed/pair/wait/history/alias/ownership/region/line cases; actual compiler/CBMC jobs followed by independent ordinary-property/term/record/counterexample reconciliation. |

The minimal `_call` branch belongs alongside existing source-definition policies,
after ordinary callee/provenance checks and only when the new0.2 entry selects its
source kind. It must not accept every `maa_*` name or turn source bodies into
generic imported summaries. The scoped pointer lowering is a required part of
that branch, not a later optional optimization. Source/model MMIO correspondence
is the accepted TCB; hardware refinement is not a new blocker.

The contract design keeps concrete C bodies reachable in CBMC. All call
preconditions/capacities/source arithmetic and original assertions remain checked
properties. Only internal model nondeterministic choices may be restricted to
their complete permitted finite choice set. No original-unit precondition is
assumed to make a negative disappear, and WP summaries require a separate
concrete-body admission. Source preparation/private native/public proof stay
separate until the actual admitted public route is complete.
