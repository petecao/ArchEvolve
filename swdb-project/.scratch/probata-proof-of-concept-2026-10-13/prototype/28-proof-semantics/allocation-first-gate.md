# Original-total software allocation gate

2026-10-16 ET. Fixture preparation; no actual proof or whole28 acceptance.

This slice admits the pinned `init_MAA`, `get_new_tile<unsigned int/unsigned
long long>()` and zero-argument `get_new_reg` for those same two types in one
unchanged synthetic source caller. It models software allocation counters;
alloc/init establish no device freshness, ownership, payload/register values,
MMIO mapping or hardware progress.

| Call | Checked original effect and obligation |
|---|---|
| `init_MAA()` | Reset `SPD_count=0`, `REG_count=0`, `region_count=6` |
| `get_new_tile<T>()` | Return old signed-int counter, add width1/2, preserve both source asserts; caller proves `0<=old<=32-width` |
| zero-argument `get_new_reg<T>()` | Same counter rule for `REG_count`; initialized overload is explicitly unsupported |

The source permits an odd64-bit tile start: ID1 consumes physical IDs1 and2,
then returns counter3. The model preserves this behavior; it does not add an
even-ID premise. Width32/64 means these exact builtins under the pinned
int32/unsigned-int32/unsigned-long-long64 ABI, not every spelling or all six
interface value types. The full26-name/27-declaration inventory remains
validated, with other calls and the initialized overload unreachable/refused.
This is a smaller type/call matrix, not whole28 closure.

The public unit is the recorded one-thread sequential call sequence. It does
not establish concurrent software-counter allocation or cross-thread ownership;
the source counters are ordinary non-atomic globals. Later per-thread/shared
action work must supply its own concurrency premises and obligations.

The original caller resets counters, allocates tile32 then tile64, register64
then register32 and returns `1000*t0+100*t1+10*r0+r1`. Expected IDs0,1,0,2
give102; final counters are3,3,6. The wrong101 contract uses identical source,
model, initialization and flags. Ordinary global names and signed types are
preserved. The original unit explicitly assigns all three counters. An
assigns-nothing original is refused instead of silently widened. No original
unit requires, ensures or partial-normal-return marker is inserted: this is the
original total software-counter unit, not a hardware termination claim.

Both immutable API headers are pinned. Original main-TU preprocessing is frozen
under original parser flags before appending probes; original directives are
not reinterpreted. Same-process dumps uniquely bind the actual three source
families, both typed instances and the zero-argument overload. Original assert
predicate/abort polarity and canonical bodies are checked. The original source
assertions remain present, including signed-int capacity duties. Source and
independent reference LLVM effects are compared under the explicit arithmetic
domain. Source/compiler/header inputs and operation evidence are rechecked
before launch; the new module belongs to translator/checker dependency closure.

LLVM equality is a trusted compiler observation, not a contract/body or
hardware refinement theorem. That remaining owned TCB duty is explicit in every
touched verdict, owned by the Probata proof-semantics maintainer pending Yan-Ru
freeze review59. The inherited five trust entries remain explicit metadata;
no legacy at-issue/reduction premise enters this route. CBMC refuses this
fixture before whole-function forwarding or adapter/tool work; only the WP
route is prepared. The unchanged0.1 library is not replaced by a current0.2.

Public scripted preparation plus C/C++ ASan/UBSan checks cover exact IDs/state,
odd pairs, last valid capacity, capacity33 source assertion abort, disabled or
removed assertions/reset, initialized-overload refusal, model/contract changes,
original-frame refusal and changed dependency rejection. The native original
side uses only exact pure counter body excerpts: compiling unrelated full-header
MMIO asm on ARM was refused and is not called native full-header agreement.
Full original header preprocessing/AST/LLVM remains the source certificate.

`run_allocation_acceptance.sh` is inert until root admission. Root must freeze
and publish clean source, review source/entry and normal Frama parser inputs,
bind the explicit four-tool actual lineup and complete physical runtime/source
closure, then use one8GiB worker under1200s whole/1320s outer guards. RTE,
initialization, no-filter-init, cache-none and smoke remain mandatory. Actual
tests skip by default. Acceptance requires complete current reporter/native
goal/property/dependency/smoke inventories; a wrong-result solver/resource error
is not a healthy negative. No actual execution was performed by the author.
