# Source argument, CPU access and fresh-program global preparation

2026-10-16 ET. Source only. These modules advance the new0.2 consumer and do not
admit a compiler observation, source call, receiver state, native run or proof.
The first private source fixture still requires an actual original-TU capture.
No production file, compiler, native tool, verifier or network child was used.

`source_argument_staging_v1.py` takes the exact reviewed V3 binder and dispatch V2,
one original TU, its original physical source, actual ABI and the complete shared
ordinary-memory atlas. The scoped lowerer supplies its current live, definitely
initialized local declaration IDs. Registration binds a unique source-owned
VarDecl and direct original span to an internal C name; it grants no lifetime,
initializedness or ownership. An ordinary array additionally requires its exact
source/TU declaration certificate in the atlas, type and complete extent.

Each call is freshly rebound against that exact TU. A closed expression grammar
renders pure scalar locals/constants/conversions and typed descriptor offsets,
stages each argument once, and emits only its fixed `dws_` route. The grammar
refuses calls, allocation, statement expressions, type-trait expressions, writes,
volatile reads, memory reads inside arguments, unbound locals, raw pointer casts
and offsets wider than32 bits. Its pure argument order does not introduce shared
memory events. Original scalar arithmetic, conversions and their UB obligations
remain executable C expressions for the existing lowerer's checks. The outer
consumer must preserve lazy evaluation, scopes, assertions and all source effects.
Unsupported general C++ expression shapes still refuse; this is not a replacement
for the ordinary lowerer.

Original Operation_t and DataType constants bind by same-TU declaration ID to the
complete enum spans in the physically pinned headers, with exact source literals
and observed explicit ConstantExpr values. No enum value is selected from its
name alone. The source has default int Operation_t and explicit uint8_t DataType;
this local C representation follows that pinned source and admitted ABI profile.

CPU subscript projections require an actual node of the unchanged selected caller
and direct original coordinates. They use `dws_cpu_load_*`/`dws_cpu_store_*`, so
ordinary CPU and device events share the atlas cells and physical intervals;
cacheable tile accesses share byte history through the existing tile bridge.
Standalone stores stage the RHS before the LHS, as C++17 requires, and perform
one shared-model write. Noncacheable/volatile dereferences are refused. Source
aggregate initialization emits the original scalar element stores in order,
including the actual trailing value initialization described by Clang's filler;
it never calls a model reset. Local allocation ownership is a separate checked
source/harness binding. Loads within initializers and arbitrary effectful
initializers are outside this first slice.

`source_program_globals_v1.py` observes all12 original global definitions from
the pinned two-header API in that same TU. Exact spans, types, declaration IDs,
source hashes, scope, storage and absent explicit initialization are checked.
Under the separately admitted fresh-C++-program interpretation, eight pointer
globals start at semantic null and four scalar globals at zero. Those facts come
from original static initialization. They do not initialize tile/RF data, grant
device ownership, erase pending commands or establish a fresh device. The two
instruction pointer offsets are derived only after alloc_MAA; a null initial
pointer is never replaced with base+8 or base+16. Root's model/receiver consumer
owns the corresponding conditional setup-state representation. Reused program
state requires a different explicit binding and is refused by this slice.

The policy/interface proposal is in `source-integration-schema-v1.json`. It fixes
one new source kind and checked-body model kind, exact source/model/module pins,
actual capture/ABI/global/program-context receipts, atlas, receiver state and
harness draw plan. None of those prospective hashes is manufactured here. Calls
retain the existing binder/dispatch record and append staged statements, source
RTE/lifetime obligations and receiver/draw obligations. CPU projection records
must compose with the ordinary lowerer's complete access inventory; this module
cannot prove that a caller omitted no access merely by counting its own outputs.

Thirteen argument/CPU controls and three source-global controls pass without
children. The argument tests exercise all132 type/arity routes using deliberately
synthetic compiler metadata, plus defaults, descriptor bounds, scope/effect/type
refusals, same-TU access identity, aggregate prefix/zero fill and original enum
attribution. These hand-authored metadata fixtures are protocol controls; they
are not source that an actual Clang invocation has validated. The earlier failed
staging run is retained. Actual full-TU/ABI/global capture, complete scoped source
lowering, admitted receiver/draw initialization and positive/negative public
CBMC verdicts remain required. Owned MMIO semantics are the accepted TCB; an
optional hardware/body theorem is not introduced as a blocker.
