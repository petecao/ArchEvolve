# Scoped original statement preparation

2026-10-16 ET. Source only. `source_statements_v1.py` composes the retained actual
unit-preparation interface with binder V4, dispatch V3 and argument stager V2.
It emits checked C for a no-parameter, scalar-return source function. This is an
inert consumer and source-lowering proposal. No compiler, project import, native
job, verifier, network child or shared production edit occurred.

The complete selected source body is consumed. Explicitly initialized scalar and
pointer locals, rank-one scalar aggregates, direct API calls, typed CPU accesses,
standalone assignments, scalar returns, compound scopes, simple if/while and loop
exits are supported by this first slice. Every selected original API call site
must be freshly rebound and consumed exactly once in the emitted source tree.
Source defaults remain pinned literals. Calls under arbitrary expression operators
refuse, so emitted staging cannot escape original lazy evaluation. General class,
heap, pointer-return/assignment, unknown-call, for-loop, noncacheable dereference
and unsupported macro/control paths refuse. Ordinary C arithmetic remains in C,
with the original RTE and unwinding obligations required at public admission.

Pointer copies are admitted only at declaration initialization. Each records its
exact ordinary-object origins, and every formation, CPU use and API argument
checks those origins against current source scopes. Pointer assignment, fields,
containers, returns and unknown pointer calls cannot bypass that relation. A
noncacheable getter may initialize an address-only local, whose sole admitted
subsequent use is a live explicit void discard. Source scalar array initialization
writes the shared cells; it adds neither a model reset nor source ownership.
Automatic arrays inside loops require a separate lifetime/provenance extension
and currently refuse. The receiver/harness must bind original local-allocation
ownership before the source writes; those allocations are not a fresh device.

Scope exit additionally emits a checked pending-command overlap refusal before
an ordinary automatic object dies. Return values are evaluated before those
lifetime checks. Break/continue preserve outer live objects and check only the
exited scopes. The emitted lifetime helper checks pending physical intervals and
grants no value, ownership or initializedness. A copied descriptor whose object
has already left scope refuses even when no command was pending at that exit.
The pointer bridge's lack of a runtime liveness field is therefore not silently
used as a lifetime proof. This is a closed static slice; no general escaping
source pointer receives admission.

Original assertions require an exact selected physical Linux assert header and
its observed complete conditional: bool conversion, void(0) success and the
same-TU global external noreturn failure declaration. The full original condition
span, stringized predicate, file/line and pretty-function diagnostics are checked.
Both the literal and current typed SourceLocExpr file/line profiles are closed:
the latter binds original pinned header spelling and original caller expansion
coordinates, with no `.ii`/`.cpp` offset join. They become named SWDB_CHECK source
properties. Assertion sites are independently counted from the original lexical
body, excluding comments and quoted tokens. Missing, duplicated, altered or
unrecognized assertions refuse. This remains an observation/owned compiler
premise; it is not a theorem about Clang or libc. No source check is assumed.

Multiple unsequenced CPU reads are limited to source-proven ordinary-memory
views, whose backend reads only check and return their current cells. Multiple
tile reads under an unsequenced operator refuse because they may cover deferred
state. Lazy scalar controls retain their C expression structure. A broader C++
sequencing route needs its own checked consumer; a single chosen source order is
not silently promoted to all source evaluation orders.

The first control run exposed a real integration defect in the frozen binder V3
and dispatch V2: searching for a direct API site attempted direct spans for every
unrelated macro CallExpr. Versioned binder V4, dispatch V3 and stager V2 repair
only that lookup (plus derived pins); selected macro API sites still refuse and
ordinary macro effects remain the statement consumer's responsibility. The exact
three inverses and nine narrow controls are retained separately. All inventory,
contract, ABI, role and C renderer functions remain unchanged.

Fourteen statement controls pass, alongside nine macro-location, thirteen argument
and three global controls. Inputs are deliberately hand-authored compiler metadata
for protocol/refusal checks. They establish no actual TU, compiler or public
verdict. The generated `source-statements-synthetic-v1.c` is an inert emitted-body
example, requiring the exact model, receiver and independent harness-draw binding.
The root-admitted actual compiler capture, actual assertion-header profile,
source/global/program context, complete producer integration, original source RTE
checks and paired positive/negative public CBMC verdicts with independent audit
remain required. Owned MMIO semantics are accepted TCB; optional hardware/body
refinement is not added as a blocker. The existing0.1 entry remains untouched.
