# EvolveSWDB — ArchEvolve's research database

Updated: 2026-10-13 20:12 ET (formal-verification ticket 23: reverted repair added); 2026-10-13 20:07 ET (formal-verification ticket 19: minimum bounds, build constant added); 2026-10-13 19:46 ET (formal-verification ticket 18: method version added); 2026-10-13 16:47 ET (formal-verification ticket 17: rewrite chain, predecessor, derived implementation, offload-only contract added; enabling rewrite sharpened); 2026-10-13 16:38 ET (formal-verification ticket 16: formal half sharpened; C lowering, proof placement, logic library added); 2026-10-13 16:09 ET (formal-verification ticket 15: enabling rewrite, shared action, sharing class, history read, parallel composition theorem added); 2026-10-13 15:22 ET (formal-verification ticket 13: proof-hint agent, counterexample-guided repair, proof-hint loop, hint set, proof setup check, proof hint check added; proof hint sharpened); 2026-10-13 14:05 ET (formal-verification ticket 12: proof semantics added; functional model and assumption set sharpened); 2026-10-12 23:51 ET (formal-verification ticket 11: Extensa Probata, verifier lineup, bounded verifier, unbounded verifier added); 2026-10-12 22:50 ET (formal-verification ticket 10: unit postcondition, relational template, contract proof, reference instance, summary added; negative control and certification level sharpened); 2026-10-12 22:25 ET (formal-verification ticket 09: certification level and formal verifier sharpened; proof unit, unit relation, output relation, lifting lemma, assumption set added); 2026-10-12 00:37 ET (final review of fine-grained attribution: code origin and catalog bound reworded; attribution report, split check, site-finder region and measured scope added); 2026-10-11 22:10 ET (review fix: rewrite site reworded to merged spans); 2026-10-11 21:52 ET (ADR 0015: LANL core, guessed column, SWDB extension; crosswalk now historical); 2026-10-11 14:51 ET (fine-grained attribution design: rewrite site, code origin, resource floor, catalog bound, headroom, remaining gain bound); 2026-10-09 23:45 ET (code review of tickets 16/17: paired estimate widened to baselines and untimed artifacts; numeric pairing check for D35); 2026-10-09 14:04 ET (formal-verification charting: certification level, proof hint); 2026-10-06 ET, before the 16:01 ET commit (design session and grilling: estimator, estimate, workload characterization, mechanism model, target description, paired estimate, screening, functional-target correctness; databases group; retitled as the research database); 2026-10-05 17:10 ET (code review: A/A pilot); 2026-10-05 (ticket 76: seam witness; attributed negative-control rejection; certification review fixes: library fault, driver fault, certification evaluator process, certify command version, legacy identifiers)

The Software Database is the ArchEvolve component that knows the applications:
what their kernels compute, how their code touches memory, what profiling
measured, which implementations exist, and which optimization strategies can
change them. LANL's main database fills that role for the team; EvolveSWDB is the
research database. Glossary only — no implementation detail, no status.

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

**Output relation**:
Which differences between a kernel's final output and its baseline implementation's are
acceptable (for BFS, a different but valid parent); stated once per kernel, beside its
correctness check.
_Avoid_: equivalence (alone), unit relation (for the final output)

**Implementation**:
Code that realizes a kernel and passes that kernel's correctness check on the hardware
target it is written for.
_Avoid_: option, variant, alternative

**Baseline implementation**:
An implementation of a kernel as found in a particular application's source.
_Avoid_: original, vanilla, reference implementation

**Derived implementation**:
An implementation made by a certified rewrite of another implementation, recorded with what it came
from. It is never a baseline implementation.
_Avoid_: equivalent baseline, normalized baseline, intermediate

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

**Enabling rewrite**:
A rewrite whose contract offloads nothing and only reshapes code, so that a rewrite contract that
does offload can then match. Its result is a candidate artifact, compared against the baseline
implementation like any other. Once certified, its result is a derived implementation.
_Avoid_: equivalent baseline, normalized baseline, enabling transformation

**Offload-only contract**:
A rewrite contract that only offloads: it keeps its predecessor's thread split and loop order, and
names, in order, the enabling rewrite contracts it requires.
_Avoid_: thin contract

**Rewrite chain**:
An ordered sequence of rewrites from a baseline implementation to a final candidate artifact, each
applying one rewrite contract to the result of the one before.
_Avoid_: chain (alone), which names an access pattern's steps; pipeline, stack

**Predecessor**:
The code one rewrite in a rewrite chain is applied to: the baseline implementation or a derived
implementation.
_Avoid_: parent (names a repair's earlier candidate artifact), base

**Preservation obligation**:
A property a rewrite must keep beyond passing the kernel's correctness check, such as
enqueuing each discovered vertex once; a rewrite contract states it as a clause with role
preservation.
_Avoid_: correctness check (for these), invariant (alone)

**Unit relation**:
What a rewrite contract requires one proof unit of a candidate artifact to preserve relative to
the same unit of the baseline implementation, and what may differ (for BFS, the next-frontier set
but not its order).
_Avoid_: output relation (for one unit), equivalence (alone)

**Unit postcondition**:
A postcondition a rewrite contract states for one proof unit, strong enough that any two units
meeting it from the same starting state satisfy the contract's unit relation.
_Avoid_: postcondition (alone) when a clause with role postcondition is meant

**Relational template**:
The alignment between the steps of a baseline unit and of a candidate artifact's unit, with the
coupling invariant that links their states, which a rewrite contract supplies when it has no unit
postcondition.
_Avoid_: template (alone), product program (for the template)

**Clause**:
One condition in a typed-library entry, with an ID and a role (precondition, postcondition,
frame, legality, or preservation), written in natural language and, where a formal language
can express it, also as a formal half.
_Avoid_: rule (alone), assertion (for the condition)

**Formal half**:
The part of a clause written in a formal language: an ACSL formula, the form verifiers read; a
predicate in the ported Extensa grammar, used only for runtime probes; or a pinned reference into
reference semantics. A clause without one is natural-language only.
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

**Extensa Probata**:
The system of Yan-Ru's next paper: Extensa extended with the proven certification levels, where
each candidate artifact is proven against its rewrite contract by the verifier lineup, with proof
hints written by an LLM. Short form after first use: Probata.
_Avoid_: proven Extensa, Extensa 2

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

**C lowering**:
The C program made mechanically from a proof unit written in the declared C++ subset, keeping its
C++ names; the form the unbounded verifier reads. It contains calls to lowerings but is not one.
_Avoid_: lowering (alone), port (for a hand-made version), translation

**Reference semantics**:
The executable description of what an intrinsic or library operation computes, such as the
body of an operation in the DX100 functional model. Lowerings and library operations are
tested against it.
_Avoid_: oracle (alone), golden model, spec (alone)

**Functional model**:
The DX100 authors' untimed model of DX100's programming interface, which completes every
operation at once. It shows what each operation computes, not how the device runs it (timing,
ready bits, order, memory traffic): a testing aid, never the semantics proofs trust.
_Avoid_: simulator (alone), emulator

**Strict layer**:
A drop-in replacement for the functional model's interface, with the same calls, that exposes
hazards the plain model hides: reads before a covering wait, tiles shared between threads,
truncation, and accesses outside registered memory regions.
_Avoid_: shim, mock

**Proof semantics**:
The description of an accelerator's programming interface that proofs trust: what each call
computes and which uses of its results are hazards. Each rule cites the device source or is marked
assumed with an owner. The strict layer is its executable counterpart for testing.
_Avoid_: proof edition, logical model, device model

**Certification**:
The certification command's test of a lowering or library operation against its reference
semantics, or of a candidate artifact against the checks of the rewrite contract it applies,
with every negative control run; it holds for one content hash. An intrinsic is certified when
its lowerings are, and a rewrite contract when a candidate artifact applying it is.
_Avoid_: verification, validation

**Certification level**:
How a candidate artifact ranks by certification in Extensa-mode selection: proven unbounded,
proven within bounds (its bounds recorded, thread count among them), certified, then
uncertified. A proven level applies only to a certified candidate artifact, and is the weakest
level among its proof units and the proven parts they depend on.
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
on a hardware target, applies the kernel's correctness check, and measures or estimates its speed
under a frozen protocol. Comparisons and selection take performance numbers only from it, in both modes.
_Avoid_: launcher, harness, benchmark runner

**Frozen protocol**:
A protocol record, fixed when frozen, that declares how the evaluator measures and compares runs
on one hardware target; comparisons cite it, and runs bound before its freeze are refused.
_Avoid_: config, benchmark setup

**Team protocol**:
A frozen protocol written in ArchEvolve mode; only comparisons under it count as team results.
_Avoid_: ArchEvolve-mode protocol (as a second name)

**Estimator**:
The evaluator stage that estimates how long code takes on a hardware target from its workload
characterization and the target's parameters, without running the code on that target.
_Avoid_: simulator, predictor, performance model (alone)

**Estimate**:
A time or speed ratio produced by the estimator, with basis estimated; never a measurement and
never a simulation result.
_Avoid_: prediction, projection, simulated result

**Workload characterization**:
The per-region description of what code does on one input that the estimator reads: access
patterns, operation counts, dynamic counts and accelerator calls.
_Avoid_: workload view (the retired HW format), feature report, profile (alone)

**Mechanism model**:
The estimator's model of one hardware behavior, such as reordering requests within a window or
fetching through a queue, reused by every hardware target that has that behavior.
_Avoid_: mechanism family (the hardware catalog's classification), component model

**Target description**:
The mechanism models and parameter values, each with its basis, that describe one hardware target
to the estimator.
_Avoid_: parameter sheet, hardware config

**Rewrite site**:
One or more changed spans of a candidate artifact's source diff against its baseline, merged when
one region overlaps several of them (possibly in several files), together with the baseline regions
it replaces and the candidate regions and calls that replace them.
_Avoid_: hunk (in prose), patch site

**Code origin**:
The label saying where a region's code came from, given to the regions of both estimates in a
comparison: untouched, agent-rewritten, library call, intrinsic, offload command, or unattributed.
_Avoid_: provenance (alone), modified/unmodified

**Resource floor**:
The lowest time a region's counted useful work could take on a target description's own rates,
ignoring latency and overheads. It is a limit, never an estimate of a real rewrite.
_Avoid_: roofline (alone), theoretical peak, ideal time

**Catalog bound**:
The lowest estimate a region could reach with a typed-library entry the site finder matches to it,
computed on the region's baseline counts.
_Avoid_: achievable speed, best known

**Headroom**:
A region's current estimate divided by its resource floor or catalog bound; the report always names
which limit.
_Avoid_: potential, slack

**Remaining gain bound**:
The most a region could still shorten a program's time if it reached its catalog bound; an upper
limit, never an expected value.
_Avoid_: expected gain, expected future gain, opportunity

**Attribution report**:
The record that splits two saved estimates, of a baseline and a candidate, by code origin, with
each region's headroom and a ranking for the next iteration. It is derived from estimates, never
a timing.
_Avoid_: breakdown (alone), attribution (alone)

**Split check**:
The comparison of an attribution report's estimated group shares with the shares measured by native
timing of the same pair, under a pass rule fixed before the timing. A report that fails it, or that
cannot be checked, is split-unverified, and nothing uses its ranking.
_Avoid_: validation (alone), agreement check

**Site-finder region**:
A region the site finder chose, named by implementation, function and lines of the full-source
revision, with the library entries that apply to it.
_Avoid_: candidate site, hotspot

**Measured scope**:
One function or loop of a timed translation unit with its measured exclusive thread-CPU time; the
split check gives it a code origin by its own lines.
_Avoid_: profile region, measured region (alone)

**Paired estimate**:
An estimate made for a candidate artifact or baseline in an Extensa campaign before its timing,
kept to measure how well estimates agree with timing. Only one that is followed by its timing
can enter an agreement report; an artifact that is refused or never timed keeps its estimate,
recorded as unknown.
_Avoid_: shadow estimate, ride-along estimate

**Numeric pairing check**:
The check D35 requires before any Extensa campaign starts: one real numeric paired estimate,
recorded before its timing, that the strict audit admits. The campaign file names it in
`paired_estimates.numeric_pairing_check`.
_Avoid_: smoke test (a companion case is not this check)

**Screening**:
Using estimates to choose which candidate artifacts of an Extensa iteration are timed; the others
are kept with their estimates but not timed.
_Avoid_: filtering, pruning (which means deleting raw output)

**Functional-target correctness**:
The kernel's correctness check passing on the strict layer of an accelerator's functional model,
used where the hardware target cannot run the code; it is never correctness on the hardware target.
_Avoid_: functional correctness (alone), simulated correctness

**Comparison baseline**:
The explicitly selected implementation and evaluation evidence against which a
candidate's performance is compared under a declared protocol.
_Avoid_: parent implementation (unless it is the selected comparator)

**Region of interest (ROI)**:
A declared computational region whose execution duration is the subject of a
performance comparison.
_Avoid_: whole-invocation time (unless the declared boundaries coincide)

**A/A pilot**:
A paired block that times a baseline implementation against itself under the full frozen protocol,
once per workload class before any candidate artifact is timed. Its ratio must be indistinguishable from
1 under the speed rule; a workload class whose gating A/A pilot fails is not timed.
_Avoid_: calibration run, dry run, warm-up

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
A deliberately broken copy of code that a test, or a formal verifier's proof setup, must reject.
A test or proof setup that misses its negative controls is not trusted. A control counts as rejected only when the check that fires is
attributable to the break itself, not to anything else the code under test does.
_Avoid_: mutant (alone), fault injection

**Seam witness**:
Evidence, recorded by evaluator code at a library seam, that every vertex in a frontier was claimed
and enqueued through the seams a rewrite contract requires. It shows structure, not correctness.
_Avoid_: ledger (alone), coverage

**Library fault**:
A negative control that acts inside a library seam the code under test calls (an intrinsic, the claim
or the queue push), built into evaluator code the candidate cannot see, so the candidate's own text
never changes.
_Avoid_: mutant, fault injection, harness fault

**Driver fault**:
A negative control of library-operation certification that evaluator code applies after the library
operation returns (one flipped input or output bit), run in the candidate's own binary under the same
run plan as the positive cases.
_Avoid_: mutant, perturbation (alone)

**Certification evaluator process**:
The trusted process that, in a certification run, holds the record channel, the run plan, the faults
and the seam-witness events, starts the candidate as its child, and writes every record the verdict is
computed from. The candidate reaches it only through shared memory requests.
_Avoid_: harness, supervisor, sandbox

**Certify command version**:
The label of one frozen certification procedure within one command family (candidate artifacts on
DX100, native-CPU contracts, library operations, lowerings and calibration). A behavior change gets a
new label; the same label in two families names two procedures.
_Avoid_: version (alone) when the family is not clear; certify level

**Formal verifier**:
A tool, such as CBMC or Z3, that proves or refutes a formal predicate about code, for all inputs
or within declared bounds.
_Avoid_: checker, prover (alone), verifier (alone, for this tool)

**Verifier lineup**:
The formal verifiers that fill the two roles, bounded verifier and unbounded verifier. The roles
are fixed; the tools that fill them may change.
_Avoid_: tier (names the typed library's tiers), verifier stack

**Bounded verifier**:
The formal-verifier role that gives proven-within-bounds verdicts and is the only source of
refutations and counterexamples.
_Avoid_: model checker (alone), bounded tier

**Unbounded verifier**:
The formal-verifier role that gives proven-unbounded verdicts. Its "not proven" never refutes; it
calls for more proof hints.
_Avoid_: deductive verifier (alone), unbounded tier

**Minimum bounds**:
A rewrite contract's smallest bounds at which the bounded verifier refutes every negative control a
formal check can see, set separately for single-thread and multi-thread runs. A bounded result below
them gives no proven level.
_Avoid_: bound floor, small scope (alone)

**Build constant**:
A value fixed when a candidate artifact is compiled, such as tile capacity, thread count or a knob.
A verdict records each build constant exactly; it is not an input bound.
_Avoid_: compile-time bound, parameter (alone)

**Proof unit**:
One call of the function that holds a rewrite site: the scope a formal verifier proves for a
candidate artifact, with every precondition it assumes either proven at each real call or listed
in the assumption set.
_Avoid_: harness (for this scope), proof scope

**Lifting lemma**:
A machine-checked lemma, proven once per rewrite contract and kernel, that a whole kernel run meets
the kernel's output relation when every call of the proof unit meets the contract's unit relation.
_Avoid_: composition proof, induction (alone)

**Contract proof**:
The proofs a rewrite contract carries, made once and reused by every candidate artifact that applies
it: its unit postcondition or relational template proven on its reference instance, its lifting lemma
per kernel, and its negative controls refuted. Its level is the weakest among these parts, and it
holds for one set of content hashes.
_Avoid_: proven contract (alone), contract verification

**Proof placement**:
Where a clause's proof comes from, named by the clause itself: proven once with a named library
entry, proven in each candidate artifact's proof unit, or assumed as an entry of the assumption set.
_Avoid_: proof scope (names the proof unit), discharge mode (how certification tests the clause)

**Reference instance**:
The code on which a contract proof is checked: the rewrite contract's own library code applied to
the baseline implementation or, when it has none, its first certified candidate artifact.
_Avoid_: reference implementation, golden candidate

**Summary**:
The proven clauses of a lowering or library operation, used in place of its code inside a candidate
artifact's proof. It is proven once with that library entry and reused by every rewrite contract
that calls it.
_Avoid_: stub, model (alone), abstraction (alone)

**Logic library**:
The formal definitions and lemmas that formal halves and proofs may use, either shared by several
rewrite contracts or owned by one; the only place recursive or inductive definitions may appear.
_Avoid_: axioms, theory (alone), prelude

**Assumption set**:
Everything a proven verdict depends on without proving it, each entry with its kind: an assumed
clause, the accelerator's proof semantics, a building-block summary, a reduction, or a trusted
tool.
_Avoid_: trusted base (alone), assumptions (alone)

**Shared action**:
One of a fixed set of kinds of step, such as claiming a write-once location or atomically adding to
one, through which the threads of a parallel region may change memory they share. A rewrite
contract lists the shared actions its code may use.
_Avoid_: atomic (alone), shared write, interference

**Sharing class**:
How the threads of a parallel region may touch one array between two barriers: read-only, owned by
one thread, changed only through shared actions, or guarded by a lock.
_Avoid_: data-sharing attribute (OpenMP's private and shared clauses), ownership (alone)

**History read**:
The proof meaning of a read that other threads may race with by design: it returns some value the
location already held, never older than the newest write the reading thread has already seen.
_Avoid_: stale read, relaxed read (for the proof meaning)

**Parallel composition theorem**:
The theorem, stated once for the method, that a parallel region whose threads are each proven alone,
touching shared memory only through shared actions and their sharing classes, ends as some serial
order of those shared actions would.
_Avoid_: reduction (alone), composition proof (names the lifting lemma), concurrency proof

**Proof hint**:
A ghost declaration or statement, loop invariant with its frame and variant, non-recursive
definition, lemma, tactic hint or intermediate assertion added to help a formal verifier reach a
verdict. Each hint must itself be proven; an assumption, a recursive definition, or a change to the
code under proof or to its rewrite contract, is never a proof hint.
_Avoid_: partial proof, auxiliary variable, annotation (alone)

**Proof-hint agent**:
A coding agent in the proof-hinting role that writes proof hints for one candidate artifact's proof
unit. It never edits code, and its provider kind is part of the record.
_Avoid_: proving agent, prover agent, hint LLM

**Counterexample-guided repair**:
The loop in which a bounded verifier's counterexample against a candidate artifact goes to the
rewriting role as correctness-repair feedback, and the repaired candidate artifact is certified and
proven again.
_Avoid_: refinement loop, counterexample-guided refinement, CEGAR

**Reverted repair**:
The outcome of counterexample-guided repair in which the repaired code no longer applies the rewrite
contract the refuted candidate artifact applied, for example because it dropped the offload or
equals the baseline implementation. It is reported apart and never counted as a repair.
_Avoid_: trivial repair, repair by copying

**Proof-hint loop**:
The loop, per proof unit of one candidate artifact, in which hint sets are tried, checked and
proven by the unbounded verifier until the unit is proven or the budget is spent. It never changes
the candidate artifact's code.
_Avoid_: proof loop (alone), proof search, refinement loop

**Hint set**:
The proof hints for one proof unit in one round, each placed at an anchor of the code under proof
and recorded with its provenance: proof-hint agent, seed, or human.
_Avoid_: hint overlay, annotations

**Proof setup check**:
The deterministic check, before every formal-verifier run, that a proof unit's inputs, summaries
and settings are the frozen ones, that every assumption in it comes from a summary, and that every
clause has a proof placement.
_Avoid_: preflight, harness check

**Proof hint check**:
The deterministic check that rejects a hint set using any kind outside the allowed proof hints, or
whose removal does not leave the code under proof unchanged.
_Avoid_: hint checker, cheat filter

**Method version**:
The versioned set of everything a candidate artifact's proofs use apart from the rewrite contract
and the candidate itself: the C-lowering subset and translators, the proof-hint vocabulary, the
proof setup check, the proof hint check and the verdict reading, the budgets, the prompts, the
catalog templates, the shared-action kinds and the bounded verifiers' settings. Changing any part
makes a new method version.
_Avoid_: toolchain version

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
model of the machine, read from code, reported by a person, inferred, analytically estimated, or unknown.
Unknown never means false.
_Avoid_: confidence, provenance (alone)

**Input density**:
How full the data fed to a kernel is (mostly zeros versus full; scattered versus
clustered indices), independent of the storage format.
_Avoid_: sparse format, dense format

### Databases

**Main database**:
LANL's kernel database, which fills ArchEvolve's Software Database role for the team.
_Avoid_: LANL DB (in prose), bootstrap database

**Research database**:
EvolveSWDB's own records, kept for Yan-Ru's research; its generated file takes the main
database's shape (a LANL core plus the SWDB extension).
_Avoid_: our database, local database, preliminary database

**LANL core**:
The part of the research database's generated file that has the main database's tables, with the
table and column names LANL has shown, and only those columns plus IDs and the links between them.
_Avoid_: main schema (LANL's full schema is unseen), LANL DB

**Guessed column**:
A LANL core column, or a whole table, that LANL has not shown but a link needs; it is listed as
guessed until LANL's own schema confirms or replaces it.
_Avoid_: assumed column, extra column

**SWDB extension**:
Everything in the research database's generated file that the main database lacks, kept in
tables prefixed `swdb_`. The LANL core never depends on it, so it can be merged in or dropped.
_Avoid_: separable extension (older wording), research tables

**Crosswalk**:
The 2026-10-06 draft that maps each main-database table and field to a research-database record
kind and field, or marks it as having no counterpart. Since ADR 0015 it is a historical record,
not the migration plan: the research database takes the main database's shape instead.
_Avoid_: schema mapping (alone), adapter (which is code)

### Legacy identifiers

Some stored names predate these terms and stay as written, because records, pins or other code read
them; prose uses the glossary terms. The native candidate profile keys `harness` and `harness_v14`
name evaluator files; `harness_scan` (check ID and campaign check), the `scan/harness` cell and the
words "harness scan" in refusals name the evaluator scan; `oracle_frontier_counts` holds reference
counts; persisted check and control IDs keep their spelling; "mutant" in ported Extensa synthesis code
means negative control; "hardware API" in pinned library operation headers means hardware interface.

