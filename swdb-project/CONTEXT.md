# ArchEvolve — Software Database

Updated: 2026-10-05 (ticket 76: seam witness; attributed negative-control rejection)

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
Code that realizes a kernel and passes that kernel's correctness check on the hardware
target it is written for.
_Avoid_: option, variant, alternative

**Baseline implementation**:
An implementation of a kernel as found in a particular application's source.
_Avoid_: original, vanilla, reference implementation

**Region**:
A portion of one implementation's code identified for profiling or rewriting,
with its surrounding application context retained.
_Avoid_: extracted kernel, hot kernel

**Memory region**:
An address range registered with an accelerator so its operations may access it, distinct from
a region of code.
_Avoid_: region (alone)

**Candidate artifact**:
A specific source snapshot, together with any build outputs, submitted for
evaluation as a possible implementation of a kernel.
_Avoid_: optimized implementation (before its correctness check passes); candidate
(alone), which the HW side uses for a hardware composition ("hardware candidate")

**Certified candidate artifact**:
A candidate artifact whose every change applies a rewrite contract and that passes
certification for those contracts. A candidate artifact with a change that applies no contract
is uncertified; one that fails certification is rejected, not uncertified.
_Avoid_: verified, proven (for this testing evidence)

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
restructure a loop, or offload accesses to a hardware operation outside the core.
Together with the target, it is the strategy's identity.
_Avoid_: benefit, speedup

**Rewrite proposal**:
A request to change identified source regions according to an optimization intent,
carrying instructions or supplied code and the requirements the change must preserve.
_Avoid_: strategy (for a request tied to particular source)

**Intrinsic specification**:
A teammate's document that defines intrinsics for a hardware candidate: names, signatures,
pre- and postconditions, and an example rewrite. It is input to the typed library, not
reference semantics.
_Avoid_: spec (alone), intrinsic contract

**Rewrite contract**:
A reusable statement of how to rewrite code whose access patterns match its pattern key,
realizing one or more optimization strategies with given intrinsics and library operations:
when it applies, what it must preserve, and which knobs may be tuned. A rewrite proposal
applies it to particular source regions.
_Avoid_: template, recipe, transformation

**Pattern key**:
The pattern classes a rewrite contract matches, one per access pattern, with arrays named by
role rather than by name.
_Avoid_: signature, match pattern

**Knob**:
A tunable value of a rewrite contract, such as chunk size or frontier threshold, with a
default, an origin, and an allowed range that a legality clause enforces.
_Avoid_: parameter (for a contract's tunable value), setting

**Derived contract**:
A rewrite contract with its own ID that cites a parent contract and adds kernel-specific
clauses.
_Avoid_: sub-contract, contract variant

**Preservation obligation**:
A property a rewrite must keep beyond passing the kernel's correctness check, such as
enqueuing each discovered vertex once; a rewrite contract states it as a clause with role
preservation.
_Avoid_: correctness check (for these), invariant (alone)

**Clause**:
One condition in a typed-library entry, with an ID and a role (precondition, postcondition,
frame, legality, or preservation), written in natural language and, where a formal language
can express it, also as a formal half.
_Avoid_: rule (alone), assertion (for the condition)

**Formal half**:
The part of a clause written as a predicate in the ported Extensa grammar or as a pinned
reference into reference semantics; a clause without one is natural-language only.
_Avoid_: formalization

**Formal label**:
Whether a clause's formal half is proven (a formal verifier returned that verdict) or stated
(written down and checked in its formal language, backed only by the evidence its discharge
mode names).
_Avoid_: verified, assumed (for stated)

**Discharge mode**:
How a clause is backed: a runtime guard, a static assertion, a structural check, a
differential test, an observation on a hardware target, an assumption with its evidence and
owner, not applicable, or open.
_Avoid_: proof status, verification status

**Site finder**:
The stage that matches rewrite contracts against profiled regions and emits rewrite
proposals, recording why each region was chosen; it may be a coding agent or a query.
_Avoid_: planner, scout, rewrite provider (for this stage)

**ArchEvolve mode**:
Running each rewrite proposal once: one candidate artifact, measured by the evaluator,
with the result handed to the team. Only bounded build or correctness repair may repeat;
nothing loops on performance.
_Avoid_: handoff mode, single-pass mode

**Extensa mode**:
Running a loop of site finding, rewriting, certification, and evaluation that judges candidate
artifacts' performance only on evaluator results, ranks them by certification level first, and
may add library entries; its candidate artifacts stay out of team comparisons until promoted.
_Avoid_: refinement mode, research mode

**Extensa**:
Yan-Ru's published loop system for contract-guided rewrites: the AgenticRefiner folder of the
MemAcc repository, from which Extensa mode is seeded.
_Avoid_: LACT (for the system), refiner (alone)

**Extensa campaign**:
One run of Extensa mode over chosen hardware targets, workload classes, library tier and
rewrite contracts, with its own iteration, lane-hour, provider-call and disk budgets.
_Avoid_: campaign (alone) in prose, which also names ArchEvolve-mode evaluation batches in
existing record IDs; the `swdb campaign` command name is the exception

**Rewrite provider**:
The external coding agent that interprets a rewrite proposal and produces the source
edits for a candidate artifact; its kind (for example Codex or Claude) is part of the record.
_Avoid_: coding agent, backend, LLM, worker (for the agent itself)

**Agent role**:
One job an external coding agent does through the provider launcher (rewriting, independent
test generation, synthesis, or profiling), each with its own workspace input and output schema.
_Avoid_: role launcher (for the launcher), worker

**Provider workspace**:
The files one agent-role invocation may read, edit, build, and run during one attempt: only what
that role's input needs (for the rewriting role, its rewrite proposal). Everything else,
including evaluator code, workload inputs, other candidate artifacts and the authors' accelerated
code, is hidden from it.
_Avoid_: sandbox, context, allowlist

**Intrinsic**:
A function that source code calls to use one hardware capability, either an ISA
instruction (for example `_mm512_i32gather_ps`) or an accelerator command (for example
`__dxc_gather`), with what it requires and the memory it touches. One intrinsic may use any
number of hardware operations, including none.
_Avoid_: builtin, instruction (alone), pseudo-intrinsic

**Hardware operation**:
One operation that a hardware target performs, as its catalog or design documents describe it,
such as DX100's 32-bit indirect load. Intrinsics expose hardware operations to source code.
_Avoid_: primitive, instruction (alone); opcode for the operation itself (an opcode is the
encoded field a trace reports)

**Hardware interface**:
A versioned programming interface through which code drives a hardware target's operations,
named by an interface ID and version, such as `dx100-mmio 1.0-e4fc4af` (DX100's `maa_*` calls).
_Avoid_: hardware API, accelerator interface, accelerator API

**Lowering**:
Code that realizes one intrinsic over one hardware interface version, such as `__dxc_gather`
written with DX100's `maa_*` calls. The hardware targets it is tested on are evidence about it,
not separate lowerings.
_Avoid_: implementation or intrinsic implementation (for this code), backend, shim, wrapper

**Reference semantics**:
The executable description of what an intrinsic or library operation computes, such as the
body of an operation in the DX100 functional model. Lowerings and library operations are
tested against it.
_Avoid_: oracle (alone), golden model, spec (alone)

**Functional model**:
The DX100 authors' untimed model of DX100's programming interface, which completes every
operation at once.
_Avoid_: simulator (alone), emulator

**Strict layer**:
A drop-in replacement for the functional model's interface, with the same calls, that exposes
hazards the plain model hides: reads before a covering wait, tiles shared between threads,
truncation, and accesses outside registered memory regions.
_Avoid_: shim, mock

**Certification**:
The certification command's test of a lowering or library operation against its reference
semantics, or of a candidate artifact against the checks of the rewrite contract it applies,
with every negative control run; it holds for one content hash. An intrinsic is certified when
its lowerings are, and a rewrite contract when a candidate artifact applying it is.
_Avoid_: verification, validation

**Certification level**:
How a candidate artifact ranks by certification in Extensa-mode selection: certified, then
uncertified; a proven level is reserved until formal verification is settled.
_Avoid_: trust level, proof level

**Certified lowering**:
A lowering whose differential tests match its intrinsic's reference semantics and reject every
negative control. It says nothing about whether a rewrite using it is legal on a given hardware
target.
_Avoid_: verified lowering, proven lowering

**Library operation**:
A typed C++ function in the typed library, with clauses, written in plain C++ or on top of
intrinsics (for example packing indirectly read values into a contiguous buffer). Unlike a
lowering, it never calls a hardware interface directly.
_Avoid_: intrinsic (for software functions), helper, API (alone)

**Typed library**:
The collection of intrinsics with their reference semantics, lowerings, library operations, and
rewrite contracts, each entry in one of two tiers. Experimental entries (made in Extensa mode,
seeded from Extensa, or hand-built and not yet reviewed) are usable only in Extensa mode; shared
entries have been reviewed by Yan-Ru and, once certified, are usable in both modes.
_Avoid_: intrinsic library, transformation library

**Entry status**:
How far a library entry's evidence has reached: draft, certified, or evaluated on target, with
the side states refuted and inconclusive; derived from records and separate from its tier.
_Avoid_: maturity

**Promotion**:
Yan-Ru's recorded review that makes a library entry shared, or that admits an Extensa-mode
candidate artifact to team results after re-evaluation under a team protocol.
_Avoid_: approval (alone), publishing

**Hardware target**:
A real machine or simulated system, with its configuration and capabilities,
against which code is evaluated.
_Avoid_: host (when referring to the system being simulated)

### Evidence

**Evaluator**:
The Software Database stage that builds a candidate artifact or baseline implementation, runs it
on a hardware target, applies the kernel's correctness check, and measures it under a frozen
protocol. Comparisons and selection take performance numbers only from it, in both modes.
_Avoid_: launcher, harness, benchmark runner

**Frozen protocol**:
A protocol record, fixed when frozen, that declares how the evaluator measures and compares runs
on one hardware target; comparisons cite it, and runs bound before its freeze are refused.
_Avoid_: config, benchmark setup

**Team protocol**:
A frozen protocol written in ArchEvolve mode; only comparisons under it count as team results.
_Avoid_: ArchEvolve-mode protocol (as a second name)

**Comparison baseline**:
The explicitly selected implementation and evaluation evidence against which a
candidate's performance is compared under a declared protocol.
_Avoid_: parent implementation (unless it is the selected comparator)

**Region of interest (ROI)**:
A declared computational region whose execution duration is the subject of a
performance comparison.
_Avoid_: whole-invocation time (unless the declared boundaries coincide)

**Workload class**:
A family of workloads made by one graph generator, such as Kronecker or uniform random.
_Avoid_: input class, dataset (alone)

**Completion witness**:
Evidence on a simulator that the protected correctness check ran after the region of interest
and passed, and that the program then requested exit with status zero; part of the correctness
check, unlike an execution witness.
_Avoid_: execution witness (for this), seal (alone)

**Execution witness**:
Evidence that a run executed the intended code path, such as counts of hardware operations in a
trace. It shows coverage, not correctness.
_Avoid_: proof, verification

**Accelerator case**:
A named requirement in a gem5 protocol that a run's trace must satisfy, such as the read-only
execution case, full tiles, or tail tiles; it checks an execution witness, not correctness.
_Avoid_: coverage case, execution-witness case

**Companion case**:
A short run on a small graph that a protocol requires before timed runs, testing one hardware
assumption, such as the parent-gather race case.
_Avoid_: pilot run, smoke test

**Pre-check evidence**:
Results from functional-model builds, with basis simulated, that are neither performance
evidence nor the correctness check on the hardware target.
_Avoid_: validation result

**Team claim**:
A comparison result, finding, or figure that has been sent to a teammate or published.
_Avoid_: shared claim, gain claim (for the sending), claim (alone)

**Bulky raw output**:
The compressed debug traces and checkpoint payloads a run leaves; the only files pruned
automatically.
_Avoid_: logs (alone), scratch

**Compact evidence**:
Any run file a record names as evidence, kept whatever its size.
_Avoid_: small files

**Negative control**:
A deliberately broken copy of code that a test must reject. A test that misses its
negative controls is not trusted. A control counts as rejected only when the check that fires is
attributable to the break itself, not to anything else the code under test does.
_Avoid_: mutant (alone), fault injection

**Seam witness**:
Evidence, recorded by evaluator code at a library seam, that every vertex in a frontier was claimed
and enqueued through the seams a rewrite contract requires. It shows structure, not correctness.
_Avoid_: ledger (alone), coverage

**Formal verifier**:
A tool, such as CBMC or Z3, that proves or refutes a formal predicate about code within declared
bounds.
_Avoid_: checker, prover (alone), verifier (alone, for this tool)

**Profiling agent**:
A coding agent in the profiling role that produces profiling evidence for a region: statement
annotations derived from source and existing profiles, or tool runs it chooses. Its own agent
claims have basis read from code or inferred; tool measurements keep their own basis.
_Avoid_: AI profiler, LLM profiler, profiler (alone)

**Agent claim**:
A value an agent asserts about a statement or access pattern, stored beside recorded facts with
its basis and the agent's settings, and marked contradicted when a stated rule refutes it.
_Avoid_: claim (alone), fact (for an unconfirmed value)

**Basis**:
The stated source of a recorded fact: measured on the machine, simulated by a
model of the machine, read from code, reported by a person, inferred, or unknown.
Unknown never means false.
_Avoid_: confidence, provenance (alone)

**Input density**:
How full the data fed to a kernel is (mostly zeros versus full; scattered versus
clustered indices), independent of the storage format.
_Avoid_: sparse format, dense format

