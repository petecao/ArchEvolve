# ArchEvolve — Software Database

Updated: 2026-09-29

The Software Database is the ArchEvolve component that knows the applications:
what their kernels compute, how their code touches memory, what profiling
measured, which implementations exist, and which optimization strategies can
change them. Glossary only — no implementation detail, no status.

## Language

### Code

**Application**:
A program that contains one or more kernels, taken from one source at one version.
_Avoid_: benchmark (alone), suite

**Kernel**:
A computation that the database tracks, defined by what it computes and by its
correctness check; implementations in different applications can realize the same kernel.
_Avoid_: hot loop, function, hotspot

**Correctness check**:
The test (a verifier plus a stated tolerance) that decides whether a piece of code
computes a given kernel.
_Avoid_: validation, equivalence proof

**Implementation**:
Code that realizes a kernel and passes that kernel's correctness check.
_Avoid_: option, variant, alternative

**Baseline implementation**:
An implementation of a kernel as found in a particular application's source.
_Avoid_: original, vanilla, reference implementation

**Region**:
A portion of one implementation's code identified for profiling or rewriting,
with its surrounding application context retained.
_Avoid_: extracted kernel, hot kernel

**Candidate artifact**:
A specific source snapshot, together with any build outputs, submitted for
evaluation as a possible implementation of a kernel.
_Avoid_: optimized implementation (before its correctness check passes); candidate
(alone), which the HW side uses for a hardware composition ("hardware candidate")

**Statement**:
A line range in one implementation's source, named by a team-wide ID (for example
`bfs-td-parent-cas`), that performs one or more steps of access patterns.
_Avoid_: access (alone), line, instruction

**Access pattern**:
One memory-access expression in one implementation: a chain of steps that ends at
the array it reads or updates, plus its update kind and semantics.
_Avoid_: pattern (alone), access

**Step**:
One link in an access pattern's chain: one array and the address shape used to
reach it from the previous step.
_Avoid_: level, hop, edge

**Address shape**:
How a step computes its address: stream, single-valued indirect, ranged indirect,
pointer chase, or data-dependent merge.
_Avoid_: access type, stride pattern

**Update kind**:
What an access pattern does to the final array of its chain: read, write,
add-update, min/max-update, compare-and-swap, arbitrary, or prefetch (a non-binding
early access that returns no data).
_Avoid_: memory type, RMW type

**Pattern class**:
The category of an access pattern: the address shapes of its steps plus its
update kind.
_Avoid_: pattern (alone), access type

### Optimization

**Optimization strategy**:
A reusable technique for changing how code touches memory, identified by its
target (access pattern, loop, or input) and its effect on that target; numbers such as
tile size or prefetch distance are its parameters. It is not code and never runs.
_Avoid_: optimization (alone), transformation, technique, variant

**Strategy effect**:
The typed changes an optimization strategy makes to its target: reshape an address
shape, add an access pattern, add a hint, widen the lanes per access, reorder indices,
or restructure a loop. Together with the target, it is the strategy's identity.
_Avoid_: benefit, speedup

**Rewrite proposal**:
A request to change identified source regions according to an optimization intent,
carrying instructions or supplied code and the requirements the change must preserve.
_Avoid_: strategy (for a request tied to particular source)

**Rewrite provider**:
The external coding agent that interprets a rewrite proposal and produces the source
edits for a candidate artifact; its kind (for example Codex or Claude) is part of the record.
_Avoid_: coding agent, backend, LLM, worker (for the agent itself)

**Provider workspace**:
The files a rewrite provider may read, edit, build, and run during one attempt: only
what its rewrite proposal needs. Everything else, including evaluator code, workload
inputs, and other candidates, is hidden from it.
_Avoid_: sandbox, context, allowlist

**Intrinsic**:
One ISA instruction wrapper that code can call (for example `_mm512_i32gather_ps`),
with the ISA extension it needs and the memory access it performs.
_Avoid_: builtin, instruction (alone)

**Hardware target**:
A real machine or simulated system, with its configuration and capabilities,
against which code is evaluated.
_Avoid_: host (when referring to the system being simulated)

### Evidence

**Comparison baseline**:
The explicitly selected implementation and evaluation evidence against which a
candidate's performance is compared under a declared protocol.
_Avoid_: parent implementation (unless it is the selected comparator)

**Region of interest (ROI)**:
A declared computational region whose execution duration is the subject of a
performance comparison.
_Avoid_: whole-invocation time (unless the declared boundaries coincide)

**Basis**:
The stated source of a recorded fact: measured on the machine, simulated by a
model of the machine, read from code, reported by a person, inferred, or unknown.
Unknown never means false.
_Avoid_: confidence, provenance (alone)

**Input density**:
How full the data fed to a kernel is (mostly zeros versus full; scattered versus
clustered indices), independent of the storage format.
_Avoid_: sparse format, dense format
