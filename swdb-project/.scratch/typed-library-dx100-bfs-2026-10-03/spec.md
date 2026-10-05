# Spec: Typed library and DX100 BFS rewrites from intrinsic specifications, in ArchEvolve and Extensa modes

Created: 2026-10-03 00:50 ET
Updated: 2026-10-03 02:30 ET (spec reviews, ticket critiques and final audit applied; Q60–Q66)
Updated: 2026-10-05 14:40 ET (ticket 77: library-operation certification 1.1, record verdicts and blinded driver faults)
Updated: 2026-10-05 12:50 ET (ticket 76: certify 1.4, blinded controls and attributed rejections)
Updated: 2026-10-04 22:40 ET (ticket 70: certification isolation, certify 1.3)
Updated: 2026-10-03 ET (ticket 47: Extensa-mode decisions D1–D12, agent-decided under Yan-Ru's
2026-10-03 delegation and revisable; see [extensa-design-2026-10-03.md](extensa-design-2026-10-03.md))
Updated: 2026-10-04 21:05 ET (ticket 66: native CI-width speed rule, decided by Yan-Ru)
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** ticket 03 (ADRs 0007–0011 and the archevolve-handoff tracker updates), which
needs Yan-Ru's approval. The glossary, this spec, its map and its tickets were committed on
2026-10-03. The Extensa-mode design session (ticket 47) was resolved on 2026-10-03.
Owner: Yan-Ru Jhou
Decision records: ADR 0001–0006 (existing); ADR 0007–0011 (written by ticket 03, see "Decision
records" under Implementation Decisions)

## Problem Statement

In the team pipeline, Peter writes intrinsic specifications from Josh's interface packages and
Eric's hardware catalog. Yan-Ru turns each specification into working code, rewrites the targeted
region to call it, builds and runs the result, and hands the evidence back. The first
specification, Peter's v1.1 for the top-down step (`TDStep`) of the DX100-modified GAP BFS, cannot
be built as written:

- Every thread uses one shared set of DX100 tiles and registers.
- Stream-load bounds, strides and the range loop's continuation are passed as values, but the
  DX100 API takes register IDs, so the hardware cannot save where it stopped in a long neighbor
  list.
- The setup, allocation and memory-region calls are missing.
- Its tile table and its example rewrite disagree, and one specified intrinsic is never used.

Even with working code, there is nowhere to keep it. Strategy records hold no code (ADR 0004),
intrinsic records hold only ISA facts, and although records quote code, no record holds
buildable, tested library code such as a lowering, a reference-semantics pin or a contract.
Nothing records what an intrinsic computes, what a rewrite must preserve, or how either was
checked, in a form that agents can act on now and a formal verifier can check later. Every new
intrinsic specification would start from nothing, and nothing would carry over to the next kernel.

The available tests are not enough to trust a rewrite:

- The DX100 functional model completes every operation at once. It cannot expose a missing wait,
  a tile reused too early, or two threads sharing a tile. The DX100 authors' own accelerated BFS
  has exactly such a defect (a wait on the wrong tile), which the T17 rewrite had to fix.
- The BFS correctness check accepts output that does extra work, such as a vertex enqueued twice.
  The Extensa paper documented the same gap, where removed work passed output checks.
- Josh's DX100 package lists nine requirements, none discharged, with no reference semantics and
  no check that could discharge them.

The evaluator and the shared host add their own limits:

- The evaluator accepts only BFS, so no second kernel can be evaluated.
- The existing gem5 protocol's accelerator and companion cases assume the authors' design, in which
  DX100 also performs ALU and store operations. A read-only rewrite can never satisfy them.
- One gem5 DX100 run takes about 35–41 minutes of simulation and 32–34 GB of memory, and leaves
  about 1 GB of debug trace plus other raw output.
- On 2026-10-03 both run disks on mbit10 were more than 95 percent full.

Profiling has no statement-level evidence. Josh asked for statement placement, but existing
profiles hold only region totals, callgrind covers only the whole BFS call, and mbit10 gives no
hardware counters.

Finally, Yan-Ru's next paper extends Extensa toward formally verified rewrites. It needs a loop
like Extensa's that uses the team's evaluator and DX100, without changing Extensa's code and
without mixing research runs into team results.

## Solution

A **typed library** inside SWDB holds intrinsics with their reference semantics, lowerings,
library operations and rewrite contracts. Every clause has one ID, a natural-language statement,
and either a formal half or an explicit "natural-language only" mark. A formal predicate is
labeled stated until a formal verifier proves it. Entries live in two tiers: experimental entries,
usable only in Extensa mode, and shared entries, which Yan-Ru has reviewed.

The first entries come from Peter's v1.1 specification:

- DX100 intrinsics, lowered over DX100's real API with a per-thread context, register operands, a
  session lifecycle and a correct wait.
- A BFS rewrite contract that keeps Peter's data flow (DX100 performs the reads; the CPU keeps the
  compare-and-swap, the parent store and the queue push) and applies five fixes, E1–E5: per-thread
  context, register handles, session and memory-region lifecycle, chunk size bounded by the build's
  tile size, and wait plus barrier.

A new **certification command** runs on the Mac in minutes for hand-built entries. It tests
lowerings and library operations against their reference semantics, and candidate artifacts
against the kernel's correctness check, the contract's preservation obligations and its execution
witness. Every build runs through a strict layer over the DX100 functional API that exposes the
hazards the plain functional model hides, and every negative control must be rejected.

A new frozen gem5 protocol then gives the team a result against a freshly measured scalar
baseline. It starts with a new parent-gather race case, which tests the one assumption Eric owns:
that DX100 may read `parent` while CPU threads write it.

Two modes share one evaluator:

- **ArchEvolve mode** stays as it is. Each rewrite proposal runs once, the evaluator measures it,
  and the result goes to the team.
- **Extensa mode** is a new loop, seeded from Extensa inside SWDB, for Yan-Ru's research. It
  judges performance only on evaluator results, ranks certified candidate artifacts first, judges
  each workload class separately, works within lane-time, provider and disk budgets, and promotes
  candidate artifacts to the team only through Yan-Ru's review and a re-evaluation under the team
  protocol.

The evaluator also learns to handle more than one kernel (BC first) and to prune bulky raw output
automatically. Separately, the region profiler gains per-line callgrind data, and profiling-agent
statement annotations are scored against it.

## User Stories

### Typed library and contracts

1. As the SWDB maintainer (Yan-Ru), I want each intrinsic stored with its signature, its plain-English intent and a pinned reference semantics, so that every lowering is tested against one definition.
2. As the SWDB maintainer (Yan-Ru), I want every clause to carry one ID with a natural-language statement and, where expressible, a formal half, so that agents can act on the text now and a formal verifier can check the formal half later.
3. As the SWDB maintainer (Yan-Ru), I want a clause that no formal language can express marked natural-language only, with a one-line reason, so that gaps in the formal half are visible instead of silently missing.
4. As the SWDB maintainer (Yan-Ru), I want each clause to state its discharge mode, so that I know what evidence backs it.
5. As the SWDB maintainer (Yan-Ru), I want each clause that a test discharges to name the negative control (a copy of the code that violates it) that the test must reject, so that every test can be calibrated.
6. As a paper reader, I want a formal predicate labeled proven only after a formal verifier returned that verdict, and labeled stated otherwise, so that the library never claims more than it has earned.
7. As the SWDB maintainer (Yan-Ru), I want lowerings stored as their own entries, one per intrinsic and hardware interface version, so that the same intrinsic can later gain lowerings for other hardware.
8. As the SWDB maintainer (Yan-Ru), I want library operations stored in the same typed library as intrinsics, so that Extensa-style entries such as packing fit beside accelerator intrinsics.
9. As the SWDB maintainer (Yan-Ru), I want rewrite contracts keyed by the pattern classes of the access patterns they match, with arrays named by role, so that one contract can apply to several kernels.
10. As the SWDB maintainer (Yan-Ru), I want each rewrite contract to list the optimization strategies it realizes, the intrinsics and library operations it uses, its legality clauses, runtime guards, tunable knobs with allowed ranges, preservation obligations, expected execution witness and negative controls, so that applying it is mechanical and checkable.
11. As the SWDB maintainer (Yan-Ru), I want knob ranges enforced by legality clauses, so that a loop can tune knobs without ever weakening legality.
12. As the hardware-exploration owner (Josh), I want library entries keyed on my hardware-candidate ID, my intrinsic-level operation IDs and my requirement IDs, so that I can trace each of my nine requirements to how it was discharged.
13. As the hardware-catalog owner (Eric), I want library entries to cite the catalog design, revision and claim IDs they rely on, so that a catalog change shows which entries to revisit.
14. As the intrinsic-specification author (Peter), I want each entry to cite the exact specification version it came from, so that a revision of my specification shows which entries change.
15. As the SWDB maintainer (Yan-Ru), I want tier and status derived from separate records, so that review and evidence are recorded separately and promotion never invalidates a pin.
16. As the SWDB maintainer (Yan-Ru), I want an entry to become shared only when I record my review, so that one person is accountable for what both modes may use.
17. As a teammate who clones ArchEvolve without access to MemAcc, I want ArchEvolve mode and the shared tier to need no MemAcc code or data, beyond the lane scripts already required on mbit10, so that the team pipeline stays self-contained.
18. As the SWDB maintainer (Yan-Ru), I want buildable library code kept in one library folder and referenced from records by path and content sha256, so that buildable code is versioned and hashed in one place.
19. As the SWDB maintainer (Yan-Ru), I want an offload strategy effect and a DX100 read-offload strategy record, so that strategy queries can find DX100 options.
20. As the SWDB maintainer (Yan-Ru), I want an entry's content hash to cover only its normative content, so that recording a certification or an application never invalidates the records that pinned it.

### DX100 intrinsics and their lowering

21. As the author of a rewrite that calls these intrinsics, I want Peter's DX100 intrinsics lowered over DX100's real API, so that one source builds against the functional model on the Mac and against gem5 on mbit10.
22. As the author of a rewrite that calls these intrinsics, I want each thread's tiles and registers allocated once per BFS call into a per-thread context, so that threads never overwrite each other's scratchpad state.
23. As the author of a rewrite that calls these intrinsics, I want stream-load bounds, strides and the range loop's continuation passed through registers loaded by a constant-load intrinsic, so that the hardware can resume a long neighbor list across tiles.
24. As the author of a rewrite that calls these intrinsics, I want a session begin that reuses DOBFS's existing DX100 setup and runs inside the timed BFS call, followed by per-thread context allocation under mutual exclusion, so that DX100 is never set up twice or used before it is set up.
25. As the author of a rewrite that calls these intrinsics, I want memory-region registration to reuse the registration the scalar TDStep already performs, so that no memory region is registered twice.
26. As the author of a rewrite that calls these intrinsics, I want the wait intrinsic to be the held status read, a memory fence and a compiler barrier, so that tile contents read after a wait are fresh.
27. As the author of a rewrite that calls these intrinsics, I want a compile-time check that the tile size fits the 16-bit size field and a knob range that keeps chunk size within the tile size, so that chunks are never silently truncated.
28. As the SWDB maintainer (Yan-Ru), I want the lowering header's content sha256 recorded in the library and checked in every candidate artifact that ships it, so that gem5 is shown to have built the same header bytes that were certified, in its own build configuration.
29. As the SWDB maintainer (Yan-Ru), I want the setup intrinsics that Peter's v1.1 lacks (constant load, session begin, per-thread context) to get their own entries, so that every call the rewrite makes is in the library.

### Strict layer and certification

30. As the SWDB maintainer (Yan-Ru), I want a strict layer over the DX100 functional API that makes CPU reads see a sentinel until a covering wait, asserts per-thread ownership, the 32-bit byte-offset bound, tile-size truncation and memory-region membership, so that tests on the Mac catch the hazards the plain functional model hides.
31. As the SWDB maintainer (Yan-Ru), I want both my lowerings and the calibration code built through that strict layer, so that calibration exercises the same checks.
32. As the SWDB maintainer (Yan-Ru), I want a certification command that certifies lowerings and library operations against reference semantics and candidate artifacts against the correctness check, preservation obligations and execution witness, running every negative control, so that "certified" means the right code passes and broken code is rejected.
33. As the SWDB maintainer (Yan-Ru), I want hand-built entries certified on the Mac in minutes, so that ArchEvolve-mode lowerings and patches iterate locally before any gem5 time is spent.
34. As the SWDB maintainer (Yan-Ru), I want certification calibrated first on the T17-fixed authors' accelerated BFS, with the unmodified authors' BFS among the negative controls, so that I trust the command before using it on a new rewrite.
35. As the SWDB maintainer (Yan-Ru), I want a negative control to count as rejected only when it builds and then fails a named check, so that build failures and crashes cannot make certification vacuous.
36. As the SWDB maintainer (Yan-Ru), I want a BFS candidate artifact to pass only when the verifier prints PASS, every per-level frontier size equals the scalar TDStep's, and an accelerated-chunk counter is above zero on graphs whose scalar run reaches the frontier threshold, so that a guard fallback cannot pass vacuously and duplicated work is caught.
37. As the SWDB maintainer (Yan-Ru), I want the test graphs to include small Kronecker and uniform graphs and a two-level graph whose accelerated frontier contains a vertex of degree above 16,384, so that continuation across tiles runs on the accelerated path.
38. As the SWDB maintainer (Yan-Ru), I want each test run with tile sizes 16,384 and 1,024 and with four threads, so that the multi-chunk and continuation paths run cheaply.
39. As the SWDB maintainer (Yan-Ru), I want certification to write a record listing each negative control and why it was rejected, so that the evidence can be reviewed later.
40. As a paper reader, I want functional-model results labeled pre-check evidence, never performance and never the correctness check on the hardware target, so that functional-model evidence is not over-read.

### The BFS rewrite from Peter's specification

41. As the intrinsic-specification author (Peter), I want my data flow kept as the contract, so that my design is what gets tested.
42. As the intrinsic-specification author (Peter), I want my threshold, chunk size and schedule kept as default knob values, so that changing them later is tuning, not a contract change.
43. As the SWDB maintainer (Yan-Ru), I want the rewrite applied as a patch against the scalar-only source snapshot, so that the candidate artifact does not reuse the authors' accelerated code.
44. As the SWDB maintainer (Yan-Ru), I want runtime guards checked once per BFS call that send the whole call down the pre-rewrite path when the vertex count or the directed edge count exceeds the 32-bit byte-offset bound or the thread count exceeds the core count, so that the rewrite never runs where it is illegal.
45. As the hardware-catalog owner (Eric), I want the assumptions behind DX100 reading arrays that CPU threads write stated as named clauses, so that my coherence question is attached to the exact assumptions it tests.
46. As the hardware-catalog owner (Eric), I want a stale-parent failure recognized only when the parent-gather race case records a violation, so that an unrelated defect is not blamed on coherence.
47. As the SWDB maintainer (Yan-Ru), I want a ready fallback contract in which the CPU loads `parent` itself, so that a refuted parent-freshness assumption has an answer.
48. As the SWDB maintainer (Yan-Ru), I want the redundant parent store after a successful compare-and-swap kept and labeled redundant, so that the candidate artifact stays comparable to the fork baseline.
49. As the intrinsic-specification author (Peter), I want my markdown specifications accepted as they are and returned to me as contract YAML that an agent drafts and Yan-Ru reviews, so that I do not need to learn a new format.
50. As the hardware-exploration owner (Josh), I want each of my nine DX100 requirements mapped to how it is discharged, so that I can see which are tested, assumed, guarded or not applicable.
51. As the hardware-exploration owner (Josh), I want my handoff files left read-only, so that my generator's validator stays authoritative.

### First gem5 evaluation in ArchEvolve mode

52. As the SWDB maintainer (Yan-Ru), I want a real profile package built from the scalar-only snapshot, so that the first team-visible result rests on real profile evidence.
53. As the SWDB maintainer (Yan-Ru), I want a new frozen protocol, with its own ID, copied from T17 except where this rewrite differs, so that the result is comparable to earlier DX100 evidence and T17's comparisons stay valid.
54. As the hardware-catalog owner (Eric), I want the parent-gather race case run first, so that the cheapest runs test whether DX100 may read `parent` during CPU updates.
55. As a team member, I want the candidate artifact compared against a scalar baseline measured fresh under the new protocol, so that no evidence from another freeze is retrofitted.
56. As a team member, I want the authors' accelerated BFS result cited only as context, so that ratios measured under different protocols are never mixed.
57. As the SWDB maintainer (Yan-Ru), I want a read-only execution case with an exact instruction-mix rule, so that the record shows gem5 executed the rewrite's intended path (coverage, not correctness).
58. As a team member, I want a one-page summary that claims no more than the protocol supports, so that results are not over-read.

### Disk and raw output

59. As the SWDB maintainer (Yan-Ru), I want only debug traces and checkpoint payloads treated as bulky raw output, so that no file a record re-reads as evidence is ever pruned automatically.
60. As the SWDB maintainer (Yan-Ru), I want bulky raw output pruned only after every record that re-reads the run is written, so that aggregates, comparisons and packages never break.
61. As the hardware-catalog owner (Eric), I want each deletion recorded with the file's sha256 in a separate retention record, so that a deleted trace can still be identified and no pinned record changes.
62. As the SWDB maintainer (Yan-Ru), I want runs cited by a team claim to keep their bulky raw output, so that every claim sent to the team stays reproducible.
63. As the SWDB maintainer (Yan-Ru), I want a dry-run listing of every file under the run roots with its size, class and referencing records, so that I can approve a retroactive cleanup safely.
64. As the SWDB maintainer (Yan-Ru), I want input files such as registered graphs and source snapshots never proposed for deletion, so that future runs keep working.
65. As the SWDB maintainer (Yan-Ru), I want nothing deleted retroactively until I approve the listing, so that no evidence disappears by accident.
66. As the SWDB maintainer (Yan-Ru), I want free disk space and free memory on the lane's memory node checked before every dispatch, so that a run never fills a shared disk or starves a shared node.

### Evaluator support for more kernels

67. As the SWDB maintainer (Yan-Ru), I want the evaluator's kernel-specific parts made pluggable, so that kernels beyond BFS use the same workflow.
68. As the SWDB maintainer (Yan-Ru), I want BC as the second kernel, with a derived BFS rewrite contract applied to its forward-pass region, so that contract reuse is demonstrated.
69. As the SWDB maintainer (Yan-Ru), I want a gem5 completion witness for BC like BFS's, so that BC correctness on gem5 can be checked even though gem5 exits before the program's own verifier runs.
70. As the SWDB maintainer (Yan-Ru), I want BFS behavior unchanged by the generalization, so that existing records and protocols keep their meaning.

### Profiling agent

71. As the hardware-exploration owner (Josh), I want each BFS statement annotated with its pattern class, index provenance and expected cost rank, so that I get the statement placement I asked for.
72. As the SWDB maintainer (Yan-Ru), I want profiling-agent claims stored on the statement annotations and access patterns of the implementation record, with basis code_reading or inferred and the model, effort, prompt and inputs used, so that every claim is traceable.
73. As the SWDB maintainer (Yan-Ru), I want profiling-agent claims never to overwrite measured or simulated facts, so that disagreements stay visible.
74. As a paper reader, I want a cost-rank claim marked contradicted by a stated rule, and the agent's accuracy reported as a rank correlation, so that the agent's accuracy is reproducible.
75. As the SWDB maintainer (Yan-Ru), I want per-line callgrind data collected inside TDStep, so that agent annotations are scored against per-statement ground truth.
76. As the SWDB maintainer (Yan-Ru), I want the profiling agent available in both modes, so that one tool feeds Josh in ArchEvolve mode and the site finder in Extensa mode.

### Extensa mode

77. As the SWDB maintainer (Yan-Ru), I want Extensa mode built as a new system inside SWDB, seeded from Extensa, with Extensa's repository left unchanged, so that my published system stays reproducible.
78. As the SWDB maintainer (Yan-Ru), I want the license that ported files carry named before porting, with an SPDX header and a provenance header on each file, so that the terms of research code in the team repository are explicit.
79. As the SWDB maintainer (Yan-Ru), I want every agent role to run through SWDB's provider launcher and guarded workspace on mbit10, with one model and effort setting, so that the agent is never a hidden variable.
80. As the SWDB maintainer (Yan-Ru), I want Extensa mode to use the same evaluator as ArchEvolve mode, so that a number means the same thing in both modes.
81. As the SWDB maintainer (Yan-Ru), I want one frozen protocol per hardware target per Extensa campaign, with each gem5 baseline measured once per workload class, so that every candidate artifact faces the same gem5 baseline and gem5 cost per candidate roughly halves.
82. As the SWDB maintainer (Yan-Ru), I want the region of interest to be the whole BFS call including DX100 setup, so that moving work into setup cannot look like a speedup.
83. As the SWDB maintainer (Yan-Ru), I want a gain declared only when the evaluator's lower bound is above 1.05 with spread within 0.1, so that the rule is at least as strict as the threshold I published.
84. As a paper reader, I want deterministic gem5 results reported as point ratios, not confidence bounds, so that the statistics claim no more than the data supports.
85. As the SWDB maintainer (Yan-Ru), I want a separate verdict and a separate best candidate artifact per workload class, so that a rewrite that helps one graph family is not hidden by an average.
86. As a paper reader, I want per-class results labeled "single graph per class", so that the limitation is explicit.
87. As the SWDB maintainer (Yan-Ru), I want selection to rank certification level first and the evaluator's lower bound second, so that the loop prefers certified rewrites.
88. As the SWDB maintainer (Yan-Ru), I want faster uncertified candidate artifacts kept and reported, so that the headroom stays visible.
89. As the SWDB maintainer (Yan-Ru), I want the loop allowed to tune knobs within their ranges, choose regions and contracts, and synthesize experimental library entries, so that it can search the way Extensa does.
90. As the SWDB maintainer (Yan-Ru), I want edits that use no rewrite contract accepted but labeled uncertified, so that useful edits are not lost and are never counted as certified.
91. As the SWDB maintainer (Yan-Ru), I want each Extensa campaign bounded by iterations, a stop rule, lane-hours, provider calls and disk, so that a campaign cannot exhaust the shared host or the provider quota.
92. As the SWDB maintainer (Yan-Ru), I want Extensa mode to start with BFS on native CPU, compared separately against upstream direction-optimizing BFS and the fork's scalar TDStep, and with BFS on DX100 in gem5, so that the native number cannot be called inflated.
93. As the SWDB maintainer (Yan-Ru), I want the first site finder to be a query over indexed access patterns and contract pattern keys, so that region choice is cheap, repeatable and explainable.
94. As the SWDB maintainer (Yan-Ru), I want the experimental tier seeded with Extensa's packing, binning, relabeling, regrouping and gather-staging entries, each recertified before use, so that native-CPU campaigns have entries from the start.
95. As the SWDB maintainer (Yan-Ru), I want every record an Extensa campaign writes tagged with its mode and campaign, kept on mbit10, and only its summary, promoted candidate artifacts, team-claim evidence and new library entries committed, so that the team repository stays small and nothing is lost.
96. As a team member, I want team comparisons, handoffs and coverage reports to refuse unpromoted Extensa records, and ArchEvolve-mode submit to refuse experimental-tier entries, so that research runs never leak into team results.
97. As the hardware-exploration owner (Josh), I want loop failures kept out of my feedback channel, so that only promoted candidate artifacts and deliberate findings reach me.
98. As a team member, I want a promoted candidate artifact re-evaluated under a team protocol for its workload class, with its Extensa campaign recorded as its origin, so that promoted numbers are measured like every other team number.
99. As the intrinsic-specification author (Peter), I want the finding of the "is the specification enough?" experiment sent to me, so that I learn what a specification must contain.
100. As the SWDB maintainer (Yan-Ru), I want that experiment to compare three inputs with at least three samples each, scored by the certification command with the working rewrite hidden, so that the answer is not anecdotal.

### ArchEvolve mode and process

101. As a team member, I want ArchEvolve mode to keep running each proposal once, with bounded build or correctness repairs (two by default) and no tuning after a valid regression, so that team results keep their current meaning.
102. As the SWDB maintainer (Yan-Ru), I want ADR acceptance, commits, team messages, each mbit10 dispatch or Extensa-campaign launch, and every deletion outside automatic pruning to wait for my explicit approval, so that I control every outward or irreversible action.

## Implementation Decisions

### Decision records (design session)

The glossary, this spec, its map and its tickets were committed on 2026-10-03. Ticket 03 then
writes ADRs 0007–0011 as proposed (or accepted, if Yan-Ru's commit approval says so), updates the
record-kind vocabulary and the BFS kernel record's note per ADR 0008, and updates the
archevolve-handoff tracker: the spec-adapter ticket becomes wontfix (superseded by this spec), the
statement-crosswalk ticket is resolved with the mapping message sent to Josh, and the
pull-request-to-`main` ticket is blocked by the last ticket of every branch of this feature. The
offload strategy effect's code is its own ticket. Ticket 03 is one commit, after Yan-Ru approves.

- **ADR 0007, Typed library.**
  - Buildable library code and its clauses (reference semantics pins, lowerings, library
    operations, rewrite contracts) live in SWDB's library folder outside the record store,
    referenced from records by path and content sha256, the way source snapshots bind their
    artifacts. Proposal records keep carrying supplied patches.
  - **Amends ADR 0004 twice.** The intrinsic record kind widens from ISA-only to cover
    accelerator commands, and the strategy-effect list gains offload. ADR 0004 gets an "Updated"
    line pointing to ADR 0007.
  - **Narrows ADR 0002.** Library entries are git-tracked YAML checked by SWDB code until BC
    reuses them; then they get a JSON schema and SQLite tables. No query reads library YAML before
    then.
  - Two tiers, experimental and shared; tier and entry status are derived from records.
- **ADR 0008, What counts as correct.**
  - **Narrows ADR 0001** and the implementation phrase in ADR 0004. The kernel and its
    correctness check are unchanged. Code becomes an implementation only when that check passes on
    the hardware target it is written for, consistent with ADR 0005's target-bound check bindings,
    so DX100 candidate artifacts need a gem5 pass. The record-kind vocabulary and the kernel
    records' notes are updated to match.
  - Extra properties a rewrite must keep are preservation obligations of its rewrite contract.
    Evidence that the intended path ran is an execution witness, not correctness. A completion
    witness (such as the DX100 v2 witness) is part of the correctness check. Protocols keep
    accelerator cases (execution-witness requirements) under their correctness field despite its
    location.
  - A formal half is a predicate in the ported Extensa grammar (parse-checked) or a pinned
    reference into reference semantics (resolved by path and sha256). Its formal label is proven
    only once a formal verifier returns that verdict; otherwise it is stated.
  - Functional-model results are pre-check evidence with basis simulated: never performance
    evidence, and never the correctness check on the hardware target.
- **ADR 0009, Two modes, same evaluator.**
  - ArchEvolve mode and Extensa mode share records, the typed library, the provider launcher and
    the evaluator.
  - Extensa mode is a new system inside SWDB, seeded from Extensa (the AgenticRefiner folder of
    the MemAcc repository), and Extensa's repository stays frozen.
  - **Extends ADR 0006** from rewrite providers to every agent role. All roles use one model and
    effort setting, the same launcher and audit, and run only on mbit10 inside a socket lane. Each
    role's workspace comes from its own input. No role sees evaluator inputs, workload files,
    other candidate artifacts or the authors' accelerated code, and calibration runs outside every
    workspace. The provider launcher therefore gains roles: a role name, a role-specific workspace
    input and output schema, and a refusal to start real runs outside an mbit10 lane; the rewrite
    role behaves as today.
- **ADR 0010, Extensa-mode loop.**
  - Records the speed rule, workload classes, selection, budgets, promotion and records policy
    below.
  - **Narrows ADR 0002.** Records of non-promoted Extensa candidate artifacts live in an Extensa
    campaign record store in the Extensa campaign's run folder on mbit10, outside git, and are kept.
  - Lifts, for Extensa mode only, the rewrite worker's rule that a valid regression does not
    trigger tuning. The rule stays in force for ArchEvolve mode.
- **ADR 0011, Raw-output retention.** Compact evidence is always kept; bulky raw output is pruned
  automatically by the rules under "Raw-output retention and pruning".

### Typed library

- **Layout.** SWDB's `library/` folder has one subfolder per entry kind: intrinsics, lowerings,
  library operations, rewrite contracts. Lowerings are grouped by hardware interface and version
  (`dx100-mmio`, `1.0-e4fc4af`), the interface ID the operation and hardware-target records
  already use. Entry IDs follow the record ID rule, carry a kind prefix (for example
  `intrinsic.dxc_gather`, `lowering.dxc_gather.dx100-mmio.1.0-e4fc4af`, `contract.bfs_read_offload`)
  and never collide with record IDs.
- **Content hash.** An entry's content sha256 covers its normative content only: the code file for
  a lowering, reference body or differential-test driver, and every YAML field. Tier, status,
  certification results and applications are never stored in the entry; they are derived from the
  records that point at the entry ID and content sha256 (review, certification and evaluation
  records, and rewrite proposals). Promotion therefore never changes the content sha256. Lowering
  entries also store the sha256 of the code file that holds them, which submit compares with the
  shipped header.
- **Intrinsic records (Q60).** Each library intrinsic also has a code-free intrinsic record that
  points to its library entry by path and content sha256. The intrinsic schema widens: a record
  may carry a hardware interface (`interface: {id, version}`, the operation records' shape)
  instead of ISA extensions, and ISA family, ISA extensions and header become optional only then.
  An accelerator intrinsic lists the operation record IDs it uses (possibly none, for session
  begin and per-thread context) and carries source-code provenance; the vendor-reference rule
  applies only to ISA intrinsics. Required-ISA derivation accounts for hardware interfaces, and
  implementations keep naming intrinsic record IDs.
- **Intrinsic entry:**
  - ID and intrinsic record ID.
  - Provenance: Peter's intrinsic specification version; Josh's hardware-candidate package by
    path, sha256 and catalog sha256, with his intrinsic-level operation IDs (`dxc-*`) and
    requirement IDs; Eric's catalog design, revision and claim IDs.
  - Signature, natural-language intent and caveats.
  - Reference semantics: a pinned location and sha256, for example one operation body in the
    DX100 functional model.
  - Hardware operations: the operation record IDs it uses.
  - Clauses (shape below).
  - Memory footprint: descriptive lists of what it reads and writes over named memory regions,
    tiles and registers. It is not a formal clause.
  - Completion: asynchronous until a covering wait (rule under "Strict layer"), and host
    concurrency marked known or unknown with an owner.
  - Lowering IDs.
- **Lowering entry:** ID; intrinsic ID; hardware interface and version; location (file and
  symbol); code-file sha256; build defines (strict switch, tile size, core count); its
  differential-test driver (a C++ file in the library folder) and input set (sizes, index
  distributions, seeds). One header holds every DX100 lowering, so editing it re-opens every DX100
  lowering's certification.
- **Library operation entry:** like an intrinsic, but its body is plain C++ or calls intrinsics,
  its reference semantics is a plain C++ reference, and it names its differential-test driver and
  input set. It never calls a hardware interface directly.
- **Clause:**
  - ID and role: precondition, postcondition, frame, legality or preservation.
  - Natural-language statement.
  - Formal half: a predicate in the ported Extensa grammar, or a pinned reference into reference
    semantics. Otherwise the clause is marked natural-language only, with a one-line reason.
  - Discharge mode: runtime guard, static assertion, structural, differential test, observed on
    target, assumed (with evidence and owner), not applicable, or open.
  - References: Josh requirement IDs, Eric claim IDs, fix IDs E1–E5.
  - Negative control: required when the discharge mode is runtime guard, static assertion,
    structural or differential test, as the copy of the code violating the clause that a test must
    reject. For the other modes the field reads "none" with a one-line reason (for L3: the
    parent-gather race case is the target-side check).
  - Formal label: stated or proven, only for clauses with a formal half.
  - The ported grammar has a closed function alphabet, so legality clauses about time, memory
    order and ownership (L2–L5 and the completion clauses) start natural-language only.
- **Rewrite contract:**
  - ID.
  - Provenance: the intrinsic specification version and section it came from (Peter's v1.1 §5 for
    the BFS contract); Josh's hardware-candidate package by path and sha256; Eric's catalog design,
    revision and claim IDs. A derived contract also cites its parent; an Extensa-origin contract
    cites its Extensa campaign or its Extensa source commit and path.
  - Pattern key: the pattern class of each matched access pattern in chain order (address shape
    per step plus update kind), with arrays named by role from the array-role vocabulary, never by
    name.
  - The optimization strategies it realizes, in order.
  - The intrinsics and library operations it uses.
  - Legality clauses, runtime guards, and knobs with allowed ranges, defaults and origin.
  - Preservation obligations.
  - Correctness check: the target kernel's, resolved per application.
  - Expected execution witness.
  - Negative controls covering Extensa's three mandatory kinds: overlapping pointer (two threads
    share state), double claim (an element claimed twice) and dropped operand (part of the input
    skipped).
  - Requirement map: each of Josh's requirement IDs mapped to a discharge mode.
  - A contract applies only when its pattern key matches and every legality clause holds.
    Kernel-specific clauses go in a derived contract with its own ID that cites its parent.
- **Entry status** (derived): draft, then certified, then evaluated on target.
  - Certified: for a lowering or library operation, a passing certification record (its
    differential test) for the current content sha256; for an intrinsic, every one of its
    lowerings is certified; for a rewrite contract, a passing candidate-artifact certification
    record that carries the contract's ID and current content sha256.
  - Evaluated on target: a candidate artifact whose proposal cites the entry passed its
    correctness check and execution witness on the target.
  - Side states: refuted (a failed certification matrix cell, or a target correctness, witness or
    companion-case failure, including a recorded L3 violation) and inconclusive (an incomplete
    run). A surviving or invalid negative control blocks certification; the entry stays draft until
    the control set is repaired, and it is not refuted.
  - Only the certification command and the evaluator produce the records status is derived from.
- **Tier** (derived from review records): experimental entries are made in Extensa mode, seeded
  from Extensa, or hand-built from a teammate's intrinsic specification and not yet reviewed; all
  are usable only in Extensa mode, and each records its origin (Extensa campaign ID, Extensa source
  commit and path, or intrinsic specification version). An entry becomes shared when `swdb
  promote` writes a review record for its current content sha256; promotion requires the entry to
  be certified. ArchEvolve mode uses only shared entries whose status is certified or later.
- **Validation.** Until the JSON schema exists, a library validator inside `swdb validate`
  enforces required fields and the intrinsic, lowering, library-operation, rewrite-contract and
  clause shapes, and checks every formal half in its language (grammar predicates parse; pinned
  references resolve and match their sha256). The predicate grammar module is ported with this
  validator, ahead of Extensa mode (details under "Extensa mode").
- **Offload effect.** It has two fields: the access-pattern steps moved off the core, and the
  hardware-operation record IDs they move to. A new strategy record, DX100 read offload, uses it,
  and the BFS rewrite contract realizes it.

### DX100 lowering layer

- **One header, both builds.** One C++11 header realizes the DX100 intrinsics over DX100's
  `maa_*` API. Its canonical copy lives with the lowering entries in the library folder; candidate
  patches add a byte-identical copy beside the BFS source in the candidate's tree, under a name no
  pinned model header uses, so the gem5 build adapter finds it and does not reject it as shadowing
  a pinned interface. It is never placed in the vendored DX100 snapshot, which stays unmodified.
  The same source builds for the functional model (native, GCC with OpenMP) and for gem5.
- **New intrinsics (E1–E3).** A constant load (hardware operation `dx100.mmio.v1.const.i32`),
  session begin and per-thread context allocation are not in Peter's v1.1. Each gets its own
  intrinsic record, entry, reference semantics and lowering. ALU-scalar keeps its own entry but is
  not used by this rewrite.
- **Session begin.** Runs once per DOBFS call, inside the timed BFS call, after DOBFS's existing
  DX100 allocation and initialization (which it never repeats), and only after the runtime guards
  chose the accelerated path. **Per-thread context allocation** then runs once per thread in a
  critical section and takes the per-core budget of 8 tiles and 8 registers; six registers are used
  (minimum, maximum, one, zero, last row, last column) and two stay spare, as in the authors' code.
  It asserts that the thread count does not exceed the core count. The next DOBFS call's
  initialization resets the allocator.
- **Register operands.** Stream-load bounds, strides and the continuation pair go through the
  constant-load intrinsic into the thread's registers. The range loop's row bounds stay tile
  operands produced by the two offset gathers.
- **Memory regions.** The rewritten TDStep reuses the four memory-region registrations the scalar
  TDStep performs, so nothing is registered twice.
- **Wait.** The held ready-status read, then the memory fence, then a compiler barrier. Reading
  tile size does not wait.
- **Capacity.** A static assertion keeps the tile size within the 16-bit size field (at most
  65,535 elements). The chunk-size knob never exceeds the build's tile size.
- **Instrumentation interface.** The header defines two hooks the rewrite calls:
  - an accelerated-chunk hook, called once per accelerated chunk; the program prints
    `SWDB accelerated_chunks=<n>` after the BFS call;
  - a compare-and-swap probe, called after every compare-and-swap with the vertex, the DX100 hint
    and the outcome. It is empty unless the diagnostic define is set; in that labeled diagnostic
    build it counts compare-and-swap failures with a negative hint and L3 violations (a hint that
    is neither the vertex's initial value, minus its out-degree or minus one, nor a vertex ID, or a
    non-negative hint while the CPU's fresh load is still negative), and prints
    `SWDB cas_fail_negative_hint=<n> l3_violations=<n>`.

### Strict layer

- **What it is.** A strict drop-in implementation of the DX100 functional API, with the same
  `maa_*` names and signatures, selected at compile time by include path. The vendored files stay
  byte-identical. Every lowering's functional build and every calibration build use it.
- **Build recipe.** Strict builds define both the functional and the gem5 switches and put a strict
  include directory ahead of the vendored API folder and ahead of the vendored include folder. That
  directory holds a drop-in functional API, which also defines the two-argument memory-region
  registration and the region clear that the vendored functional API lacks, and a no-op m5 header
  that defines every m5 call the source makes (checkpoint, work begin and end, statistics reset and
  dump, exit). The source then selects the strict API; its gem5-guarded memory-region
  registrations compile and are checked, and its ROI calls compile as no-ops.
- **Semantics.**
  - A thread's DX100 operations take effect in program order, and each sees earlier results on
    the tiles and registers it reads.
  - CPU reads through a tile pointer, the tile size or a register see a sentinel until a covering
    wait.
  - A wait on a tile covers the last operation that wrote that tile and, transitively, the
    operations it depends on. It covers nothing else; in particular, waiting on a store's source
    tile does not cover the store.
  - A CPU constant load into a register that an uncovered operation reads is a hazard.
  - These rules are recorded in the wait entry's completion field as assumed, owner Eric, until
    gem5's ready-bit semantics are confirmed (Josh's `dxc-observer` and `dxc-reuse`).
- **Assertions.** Each thread uses only its own tiles and registers; every index keeps the 32-bit
  byte offset below 2^32; no tile is silently truncated; every DX100 memory access, from any
  thread, lies inside the memory regions registered for the current TDStep.

### BFS rewrite contract and candidate artifact

- **Data flow (Peter's §5).** DX100 stream-loads the frontier chunk, gathers the row bounds, runs
  the range loop with continuation, then gathers the neighbors, the parent vertices and the parent
  hint. The CPU then runs the compare-and-swap, the parent store (kept, labeled redundant) and the
  queue push.
- **Fixes to Peter's v1.1:** E1 per-thread context; E2 register handles; E3 session and
  memory-region lifecycle; E4 chunk size never exceeds the build's tile size; E5 wait plus barrier.
- **Knobs,** each range enforced by a legality clause:
  - frontier threshold: integer of at least 1, default 64 (accelerate when the frontier holds at
    least this many vertices, as in Peter's §5);
  - chunk size: 1 to the build's tile size, default the build's tile size;
  - OpenMP schedule: dynamic or static, granularity at least 1, default dynamic with granularity 1.
- **Runtime guards,** checked once per BFS call before session begin; each sends the whole call
  down the pre-rewrite path:
  - vertex count at most 1,073,741,823 and directed edge count (the length of the out-neighbor
    array) at most 1,073,741,823, per Josh's `dxc-byte-offset` and Peter's §4. Peter's §5 code
    falls back at 1,073,741,823 for both counts, one lower than these guards; the YAML returned to
    him says so;
  - OpenMP thread count at most the configured core count.

  The thread-count assertion in per-thread context allocation stays as a defensive check that the
  guard makes unreachable. The tile-size check is a static assertion, not a guard.
- **Legality clauses:**
  - L1: the range loop with continuation emits exactly the nested loop's vertex pairs.
  - L2: within TDStep, each parent value changes at most once, from negative to a vertex ID.
  - L3: a DX100 parent gather never returns memory older than parent's initialization. Assumed,
    owner Eric.
  - L4: the compare-and-swap on the parent entry with the frontier vertex as new value, the
    redundant parent store and the queue push stay on the CPU. The compare-and-swap's expected
    value is the DX100 parent hint, which may be stale; L2 and L3 make that safe. Both vertices
    come from the same chunk's tiles.
  - L5: every DX100 read of an array the CPU wrote earlier in the same BFS call (the frontier
    queue from the previous step's flush, the offset array built in DOBFS, and parent) returns
    values no older than the last CPU store that happens before the issuing thread's descriptor
    write. Assumed, owner Eric.
- **L3 outcome** (read from the diagnostic run's evaluation record):
  - observed on target for this run: race count above zero and no L3 violation. For the design,
    L3 stays assumed;
  - refuted: an L3 violation is recorded. The contract entry becomes refuted, L3's evidence cites
    the race-case record, and the fallback (the CPU loads the parent value itself; DX100 still
    gathers the neighbors and the frontier vertex) becomes a separate contract with its own ID,
    certification, proposal, companion runs and timed runs under the same protocol. Peter and Eric
    receive the finding;
  - inconclusive: the verifier failed without an L3 violation, or the race count was zero. This
    triggers diagnosis, not the fallback, and the timed runs wait.
- **Preservation obligation:** each discovered vertex is enqueued exactly once, checked by
  per-level frontier sizes. They come from DOBFS's existing `Starting TDStep: <n> elements` line,
  which the evaluator checks by exact text at build time like the verifier text, and are compared
  with the per-depth vertex counts the evaluator's trusted oracle computes from the registered
  graph and source. A negative control that double-enqueues while printing the expected sizes must
  be rejected.
- **Execution witness.**
  - Functional model: the accelerated-chunk count above zero, required on every graph whose scalar
    run has a level with a frontier at or above the threshold knob; the requirement is derived from
    the scalar run, never from the candidate artifact's own counter.
  - gem5: a new read-only execution case. The stream, indirect and range units each completed at
    least one operation; ALU operations are zero; indirect stores are zero, counted per opcode from
    the trace; and the indirect count equals three times the range count minus the stream count.
    That last rule follows Peter's §5 order: per chunk, one stream load, two row-bound gathers and
    one final empty range loop; per non-empty range tile, three gathers. Full and tail tiles are
    counted as today.
- **Delivery.** The candidate artifact is the scalar-only source snapshot with a patch applied
  that edits the BFS source and adds the lowering header as a new file. The patch also carries the
  instrumentation hooks' calls, so later gem5 runs use exactly the certified tree. The rewrite
  proposal (new message version) gains an optional library section: the contract (entry ID and
  content sha256), every cited intrinsic, lowering and library-operation entry with its content
  sha256, and every shipped file with its lowering entry IDs. Submit refuses the proposal unless
  every cited entry is shared and certified or later for that sha256 and every shipped file's
  sha256 equals its lowering entries' code-file sha256. The proposal's editable files list the BFS
  source and the header. The patch goes through `swdb submit`; no rewrite provider runs, and the
  producer names the authoring session (provenance kind agent_run).
- **Specification intake.** An agent drafts contract YAML from each markdown intrinsic
  specification, and Yan-Ru reviews it. Sending it to Peter is a team message that needs her
  approval. Josh's handoff files stay read-only.

### Certification command and other interfaces

- **`swdb certify ENTRY_ID [--candidate CANDIDATE_ID | --snapshot SNAPSHOT_ID --patch FILE] [--calibrate] [--tile-sizes 16384,1024] [--threads 4] [--sources 0] [--runs-dir DIR]`**
  - Without a candidate, it certifies a lowering or library operation by its differential-test
    driver against reference semantics. With `--candidate` or `--snapshot`/`--patch`, ENTRY_ID is
    the rewrite contract the code applies, and it certifies the candidate artifact by the kernel's
    correctness check, the contract's preservation obligations and its execution witness. Every
    build goes through the strict layer, and every negative control runs.
  - The Mac input form `--snapshot ID --patch FILE` exists because DX100 source snapshots and
    candidate artifacts live on mbit10. It rebuilds the snapshot's tree from the vendored DX100
    source (full source, or the scalar-only derivation), requires the tree's manifest digest to
    equal the snapshot record's artifact sha256, applies the patch, and records the resulting
    sha256. The candidate artifact later created on mbit10 must have the same sha256.
  - Builds, logs and control outputs go under the runs folder; the record names them.
  - Writes one record of the new certification kind: entry ID and content sha256 (and, for
    candidates, the contract ID, its content sha256 and the tree sha256), command version and the
    sha256 of its sources, host, matrix, each control's result and reason, and the verdict.
  - Exit codes: 0 certified; 1 a matrix cell failed or a control survived or was invalid; 2 usage
    error.
- **Negative controls.** A negative control is a patch on the lowering header, the differential-test
  driver or the candidate artifact, with a kind and the check expected to catch it. It counts as
  rejected only if it builds and then fails a named check: a differential mismatch against
  reference semantics (lowerings and library operations), the verifier, frontier-size equality, the
  accelerated-chunk count, or a strict-layer assertion. A build failure, timeout or crash without
  an assertion marks it invalid, and an invalid control blocks certification like a surviving one.
- **Isolation (certify 1.3; ticket 70, 2026-10-04 22:40 ET; agent-decided under Yan-Ru's
  2026-10-04 delegation, revisable).** For candidate artifacts, the pass rule above keeps its checks
  but not its inputs. No verdict is read from the candidate's stdout or stderr.
  - An evaluator-owned `main` calls the protected entry point (`DOBFS`, `Brandes`) and records the
    returned vector. The evaluator's own result check (`verify_parents`, `verify_scores`) stands in
    for the printed `PASS`.
  - The frontier inspection records each window. `duplicate_frontier` and the frontier sizes are
    judged out of process, as are the strict-layer check names and the witness counters.
  - Records go to a descriptor the harness opens for each run.
  - Faults live in a separately compiled seam object. The candidate's object is the same for the
    positive matrix and every library-fault control.
  - A harness scan refuses candidate-authored lines that name harness or fault symbols,
    `SWDB_STRICT` or `FUNC`, descriptor, environment, loader or process primitives, or text that
    imitates an evaluator line.
  - `forged_frontier` no longer forges the print. Calibration and lowering certification are
    unchanged.
- **Blinding and attribution (certify 1.4; ticket 76, 2026-10-05 ET; agent-decided under Yan-Ru's
  delegation, revisable).** The default for candidate artifacts; 1.3 stays selectable
  (`--command-version 1.3`) and older records keep their meaning.
  - Per tile size, the positive matrix and every library-fault control run one binary. The fault
    arrives at run time in a fixed-length plan on a pipe that trusted code drains before `main`.
    All runs of a tile size take a fresh random order.
  - A library-fault control is rejected only when its named check is attributable to the fault's
    own action, from trusted seam records: a duplicate behind a forged claim or the forged push
    copy; a strict failure inside the faulted stream load or on a thread the fault acted on; a
    missing frontier vertex behind an edge the dropped continuation removed.
  - Trusted code reads each window from the queue at its slide; nothing is inserted into the
    candidate's function.
  - Positive runs also need the **seam witness** (clause L4): one frontier queue; each window equals
    the pushes into it; every pushed vertex but the source is claimed by the pushing thread through
    `compare_and_swap` at one array's slot (for BFS, the returned parent array); and the execution
    witness needs a DX100 gather from that array.
  - Extensa feedback names a surviving control only as `negative_controls_not_rejected`.
  - Calibration and lowering certification still read printed lines; they run only pinned, trusted
    code, and calibration refuses candidate input.
- **Library operations (command 1.1; ticket 77, 2026-10-05 ET; agent-decided under Yan-Ru's
  delegation, revisable).** The default for `swdb certify ENTRY --profile P`; 1.0 stays selectable
  (`--command-version 1.0`) and its records keep their meaning.
  - A trusted driver, compiled apart from the candidate, calls the adapter's entry and records the
    frame check and the output on a pipe the harness reads. The output is compared with the plain
    C++ reference's out of process. A run without `end`, with a wrong nonce or a nonzero exit has
    no named check.
  - The reference is built and run on every case before any candidate or control is compiled;
    its binary and case folders are deleted first.
  - Two driver-fault controls (`input_write`, `output_perturb`) run in the candidate's own binary
    with a blinded 60-byte plan, in one random order with the positive cases and the mutation
    controls of that build.
  - A driver fault is rejected only when the only changed byte or element is the one it flipped;
    a mutation control only by its expected check from records, on a case whose positive run
    passed.
  - A scan refuses harness symbols and descriptor, environment, process, initializer, exit and
    printing primitives in the body, candidate template and control mutations.
- **Calibration** (`--calibrate`). Builds from the full DX100 source through the strict layer and
  runs the BFS matrix under its own pass rule: the verifier's PASS text; per-level frontier sizes,
  read from the authors' `Starting TDStepMAA: <n> elements` lines, equal to the trusted oracle's;
  no strict-layer assertion; and, in place of the accelerated-chunk rule, at least one DX100
  operation recorded by the strict layer on every graph whose scalar run has a level of more than
  four times 1,024 vertices (the authors' own acceleration switch).
  - Positive control: the T17-fixed authors' BFS (the authors' accelerated TDStep plus the wait on
    the store's result tile).
  - Negative controls: shared context; dropped continuation; a 16,384-element chunk in a
    1,024-element build; the unmodified authors' accelerated TDStep (wait on the wrong tile).
- **BFS matrix:**
  - Graphs: Kronecker at scales 10, 14 and 16; uniform at scale 14; a generated two-level graph
    whose accelerated frontier holds a vertex of degree above 16,384.
  - Tile sizes 16,384 and 1,024, four threads.
  - A candidate run passes only with the verifier's PASS text, per-level frontier sizes equal to
    the trusted oracle's, and the accelerated-chunk count rule above. Parent arrays are never
    compared byte for byte.
- **BFS-rewrite negative controls:** shared context (overlapping pointer); skipped
  compare-and-swap recheck (double claim); dropped continuation (dropped operand); chunk off by
  one; dropped wait; read before wait; 32-bit index wrap; forged frontier print (double-enqueues
  while printing the expected sizes).
- **Other new commands:**
  - `swdb promote ID` writes a review record (reviewer, date, target ID and content sha256) for a
    library entry, whose derived tier becomes shared, or for an Extensa candidate artifact.
    Promotion of library entries is needed before the first ArchEvolve-mode submit that cites
    them; promotion of candidate artifacts comes with Extensa mode.
  - `swdb claim RECORD_ID... --audience NAMES` records one team claim citing one or more records;
    `swdb claim --release EVALUATION_ID` records Yan-Ru's decision that no team claim will cite a
    run.
  - `swdb annotate IMPLEMENTATION` runs the profiling agent.
  - `swdb prune --dry-run` writes a cleanup listing; `swdb prune --approve LISTING` records
    Yan-Ru's approval of it; `swdb prune --apply LISTING` deletes only an approved listing.
  - `swdb campaign CAMPAIGN_FILE` runs an Extensa campaign.
  - Library validation runs inside `swdb validate`.
- **New record kinds:** certification; review; retention; team claim; Extensa campaign summary.
  Evaluation records are never edited after they are written, because aggregates, packages,
  comparisons and pair receipts pin their digest.

### First gem5 evaluation (ArchEvolve mode)

- **Profile package.** A real package built on mbit10 from the scalar-only snapshot: one native
  evaluation plus one region profile, about 17 minutes.
- **Protocol identity.** A new requested ID (for example
  `bfs-dx100-peter-v11-controlled-simulator-<date>`), version 1, no supersedes, so the T17
  comparisons stay valid.
- **Copied from T17 version 2:** targets, simulation identity, workloads (Kronecker 18 and
  uniform 18, source 0), sampling (one repetition, deterministic replay), profitability (minimum
  speedup 1.05 strictly exceeded by the lower bound, maximum relative spread 0.1, 95 percent
  interval from 2000 bootstrap resamples), region of interest, verifier v2, the baseline role,
  builds (compiler, compiler version, flags and adapter; the candidate keeps the accelerator
  define, so its compile request is accelerated), instrumentation (primary treatment, suppressed
  internal events, debug flags, verifier runtime, post-ROI trace, graph verification), and the
  accelerator and configuration differences.
- **Changed:**
  - no region pairs (Q64);
  - route: this candidate artifact and its builds;
  - the software-differences text;
  - candidate accelerator cases: the new read-only execution case, full tiles, tail tiles; the
    baseline role has none, as in T17;
  - companion case: the parent-gather race case below.
- **Parent-gather race case** (replaces T17's competing-parent case, which observes DX100 stores
  this rewrite never issues), on the coverage workload
  `bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e` (source 0, as in T17):
  1. The exact timed candidate binary passes the v2 verifier, and its per-level frontier sizes
     equal the trusted oracle's per-depth counts.
  2. The labeled diagnostic build of the same tree prints the probe counters: compare-and-swap
     failures with a negative hint must be above zero (the race happened), and L3 violations must
     be zero.

  Companion acceptance is checked inside the comparison command, not by a separate script.
- **Comparison baseline.** The comparison names the DX100 scalar implementation (ADR 0005), built
  from the full DX100 source, because the evaluator requires the baseline artifact to equal the
  vendored source; the scalar-only snapshot is only the candidate's patch base. The baseline is
  measured fresh, because the evaluator refuses runs bound before a protocol's freeze and T17's
  baseline runs predate this one.
- **Run order.** The two companion runs (about 5 minutes each), then, only if the L3 outcome is
  observed on target, the baseline and candidate timed runs on both workloads (about 35–41 minutes
  each): 6 runs, about 2.8 hours of lane time.
- **Context only.** The authors' accelerated BFS result from T17 is cited as context, never
  divided into these numbers.
- **Before dispatch:** the socket leases; the disk and memory preflight; the host load; the
  checkout's branch and commit. No rewrite provider runs for this patch, so provider logins are not
  checked.
- **Acceptance:** the companion case passes, or the L3 outcome rule applies. All four timed runs
  pass the verifier. The two candidate timed runs also pass the frontier check and the read-only
  execution case. A comparison result is recorded whatever the speedup. A one-page summary with
  basis labels is drafted, and Yan-Ru sends it.

### Raw-output retention and pruning

- **Bulky raw output** is only the compressed debug trace and checkpoint payloads. Every file a
  record names in its correctness output, witness chain, region raw report or companion acceptance
  is compact evidence and is never pruned automatically, whatever its size. Today the gem5
  simulation log holds the verifier output, so it stays.
- **Triggers.** The gem5 execute command prunes a run's checkpoints when the run completes with
  correctness passed; a failed or interrupted run keeps its checkpoint until it is retried or
  Yan-Ru releases it. The comparison command prunes debug traces right after recording a
  comparison, for each compared run whose re-reading records for its kind exist (gem5 timed run:
  aggregate and comparison; coverage run: coverage report; profile run: profile package).
- **Readers.** The witness validator, the coverage availability check and the region comparator
  report a file that has a retention record as "pruned, sha256 retained" instead of failing. A
  missing file without a retention record still fails.
- **Retention record.** One per prune event (a run may have several): evaluation ID, each deleted
  path, its sha256 (hashed before deletion when no record holds it), reason and time. Evaluations
  are never edited.
- **Team claims.** A team claim is a comparison result, finding or figure sent to a teammate or
  published; `swdb claim` records it when Yan-Ru approves sharing. Runs a team claim cites keep
  their bulky raw output. ArchEvolve-mode runs keep their debug traces until a team claim cites
  them or `swdb claim --release` records that none will.
- **Extensa-mode runs** have their bulky raw output pruned right after their comparison is
  recorded, unless a team claim cites them.
- **Retroactive cleanup.** The dry-run lists every file under the run roots with its size, class
  (bulky, compact or input) and every record that references its path in any field. Files
  referenced by a workload, source snapshot, build receipt or frozen protocol are inputs and are
  never proposed. Only bulky files are proposed. Apply refuses a listing without a recorded
  approval and any entry not classed as bulky.
- **Dispatch preflight.** The preflight checks the disk that holds the runs folder: at least 20 GB
  free plus the run's planned raw bytes (the stage's storage budget for DX100 stages, 2 GiB for
  native evaluations, pairs and profiles). It never switches folders itself; when the folder is on
  the primary run disk and the check fails, the refusal names the secondary run folder if that disk
  would pass. The lane's memory node must have the run's memory budget available (the stage's memory budget
  for DX100 stages; 4 GiB for native and profile dispatches). Literal node-local MemFree remains recorded.
  Admission may conservatively count half of that node's inactive file cache after subtracting mapped,
  shared, dirty, writeback and unevictable pages, then subtracting a reserve of at least4 GiB,1/16 of
  node RAM and the observed zone reserve. Active cache, slab and other-node/global memory supply no credit.
  Missing accounting falls back to MemFree-only admission; contradictory accounting refuses. The receipt
  distinguishes estimated admission capacity from literal free memory and records counters, reserve,
  formula version and time. This is an estimate, not reserved memory or guaranteed allocation.
  The measured36 GiB simulator budget and16GB guest/MMIO treatment remain unchanged. Ordinary kernel
  reclaim occurs under the existing strict socket memory binding. Disk, free bytes and memory node are
  recorded with the run. Clarification added2026-10-03 ET after the user's memory-admission question.

### Evaluator support for more kernels

- **Pluggable parts.** The parts tied to BFS become per-kernel plug-ins:
  - kernel-identity checks in workload registration and protocol validation;
  - native evaluation;
  - the gem5 and native build adapters (source path, protected verifier, trusted driver and its
    oracle);
  - the gem5 completion witness and the accelerator cases with their trace extractors;
  - region discovery and profiling.
- **BFS stays the same.** Its behavior and existing records are unchanged.
- **BC** (kernel `gapbs-bc`, correctness check BCVerifier) is the second kernel. It gets a
  scalar-only snapshot that removes the authors' accelerated BC code, Kronecker and uniform
  workloads, native evaluation, a gem5 completion witness like BFS's v2, and protocols.
- **Contract reuse.** A derived BC contract (new ID, citing the BFS contract) targets BC's
  forward-pass region. It adds BC-L1: the path-count test reads the depth on the CPU after the
  compare-and-swap, never the DX100 hint. BC's correctness check still covers the whole
  computation.
- **Library indexing.** Library entries get a JSON schema and SQLite tables once BC reuses them,
  together with a statements index; the database's staleness check then covers the library folder.

### Profiling agent

- **First version: a statement annotator** (`swdb annotate`). It reads the source and existing
  profiles and runs no tools. For each TDStep statement it records:
  - pattern class (glossary term);
  - index provenance: the statement IDs whose values form the index, in chain order;
  - expected cost rank: 1 to N within TDStep, 1 meaning the most last-level misses expected.
- **Storage.** Each statement annotation and access-pattern entry in the implementation record
  gains a claims list: value, basis (code_reading or inferred), model, effort, prompt sha256, input
  sha256s and contradicted-by. Claims never overwrite existing facts. Statement lines for the
  scalar-only snapshot are mapped through its source derivation.
- **Ground truth.** The region profiler gains a second callgrind execution, limited to TDStep and
  built with debug information, and a per-line parser. Its rows go in a separate per-line field of
  the region profile with its own validator, because the whole-ROI rows forbid repeated metrics.
  Last-level misses are summed per statement line range and stored as simulated facts.
- **Scoring.** The Spearman rank correlation between expected cost rank and callgrind misses, plus
  top-3 overlap. A cost-rank claim is contradicted when its rank differs from the callgrind rank by
  more than one position. Pattern-class and index-provenance claims are contradicted only by a
  measured, simulated or person-reported access-pattern fact.
- **Later version: a tool runner** that chooses tool runs in its guarded workspace; tool outputs
  keep their own basis.
- **Both modes.** In Extensa mode its claims stay in the Extensa campaign record store.

### Extensa mode

- **Ported from Extensa** (MemAcc's AgenticRefiner folder at a pinned commit):
  - the loop structure;
  - runtime-probe contract checks (contract predicates compiled as assertions into certification
    builds only);
  - certification against negative controls;
  - the predicate grammar module (MemAcc's L3 predicate-language grammar, not its runtime-probe
    grammar), already ported with the library validator; the Z3 and SMT modules are not ported
    while the formal-verification question is open;
  - synthesis with certification profiles (the matrix and control set a synthesized entry must
    pass).

  The grammar's parser library is vendored with its MIT license, so SWDB keeps its PyYAML and
  jsonschema install rule on mbit10. Each ported file gets an SPDX header with the license Peter
  confirms (Q66) and a provenance header (MemAcc commit and original path), and a provenance
  list names every ported file. Until Peter confirms, ported files carry Apache-2.0 WITH
  LLVM-exception under the accepted Q66 assumption, and ticket 02 blocks no ticket (D11).
  The exact module list, ported and not ported, is decision D1 of
  [extensa-design-2026-10-03.md](extensa-design-2026-10-03.md). Agent-decided under Yan-Ru's
  2026-10-03 delegation; revisable.
- **Not ported:** Extensa's agent runtime (its Codex support may be stale), its timing and launcher
  measurement, and its speed rule. Its benchmark adapters serve only as references. Also not
  ported: Extensa's A5 study gates, Z3/SMT and its K3/L4 evaluators, the clang `dyncheck` tool and
  non-CPU synthesis targets (D1).
- **Agent roles:** rewriting; independent test generation (an agent that sees the contract and the
  reference semantics, never the candidate artifact, and adds differential-test inputs); synthesis;
  profiling. Site finding is a query first; a coding-agent site finder comes with a second kernel.
  Every role runs on mbit10 in a lane with Codex `gpt-5.6-sol` at effort `xhigh` by default, or
  Claude `claude-sonnet-5-5` at effort `high`, and each invocation records its settings.
- **Extensa campaign** (`swdb campaign CAMPAIGN_FILE`). The file names one hardware target
  (D2), the workload classes with their graph, the allowed tier and contracts, and the budgets.
  Its format is `swdb.extensa-campaign.v1` YAML under `campaigns/extensa/` (D5). Each iteration
  makes one candidate artifact per workload class. One rewrite call returns one patch with
  per-class knob values, so per-class artifacts cost no extra provider call. Repairs, test
  generation and synthesis are each charged (D7). Each iteration runs these steps:
  1. the site finder chooses regions;
  2. a rewrite provider rewrites;
  3. certification runs (on mbit10);
  4. the evaluator measures;
  5. selection ranks;
  6. feedback goes into the next iteration.

  The Extensa campaign writes a summary record: inputs, candidate artifacts per
  iteration, verdicts, certification levels, sha256s, lane-hours, provider calls and disk used,
  and the stop reason. The record kind is `campaign_summary`; its shape is D6.
- **Speed rule.**
  - The region of interest is the whole BFS call (`bfs.complete_call.v1`), including DX100 setup.
  - One frozen protocol per hardware target per Extensa campaign, with no region pairs and an
    Extensa-campaign-level differences text.
  - Each comparison names its baseline implementation and measurement (ADR 0005). On gem5, the
    fork's scalar TDStep is measured once per workload class and serves every candidate artifact.
    On native CPU, each candidate artifact is collected in its own paired, interleaved block with
    its baseline, as pair receipts require; upstream direction-optimizing BFS and the fork's scalar
    TDStep are separate comparisons, and selection uses the baseline the candidate artifact
    rewrites (Q61).
  - A gain is the evaluator's rule: the lower bound (2.5th percentile of 2000 bootstrap draws) of
    the geometric mean of per-source median ratios strictly above 1.05, with spread within 0.1.
  - gem5 uses one run per source and one source per class graph (Q63). Its
    interval then equals the point ratio, so gem5 verdicts are reported as deterministic point
    ratios, not confidence bounds.
  - Native CPU uses paired repetition blocks of 10 repetitions, sources `[0, 1234, 7777]`, 1
    thread. An A/A baseline pilot first stops the campaign (`baseline_unstable`) if any spread
    exceeds 0.1 (D3).
  - Added 2026-10-04 ET (ticket 66, decided by Yan-Ru): a native campaign may instead name speed
    rule `swdb.speed_rule.ci_width.v1`. Its blocks have 20 repetitions and a circular block
    bootstrap over repetitions (blocks of 4). The A/A pilot and every candidate comparison are
    gated on the relative width of the same 95% interval, at most 0.05, instead of the spread; an
    A/A interval must also lie inside (1/1.05, 1.05). A gain still needs the lower bound strictly
    above 1.05. Protocols and campaigns without it keep the rule above.
- **Workload classes.** A class is a graph generator family: Kronecker and uniform for now, with a
  high-input-density family later, native only. Each class gets its own verdict and its own best
  candidate artifact; there is no cross-class average and no held-out graph. Results are labeled
  "single graph per class". Per-class bests stay separate; run-time selection among them is added
  only if needed. The graphs are:
  - native CPU: Kronecker scale 22 and `bfs-20260925-uniform22.f23b09bb0c0601b5`, both with edge
    factor 16;
  - gem5: `bfs-20260928-kronecker18-s0.cf4283236c5cb50c` and
    `bfs-20260928-uniform18-s0.8c7e69dfa516e53c`, source 0 (D4).
- **Selection.** Certification level first (certified, then uncertified), then the evaluator's
  lower bound. A proven level is added only after the formal-verification question is settled. An
  uncertified candidate artifact becomes best only if no certified one in its class passes the
  threshold; faster uncertified ones are kept and reported. A candidate artifact that fails
  certification is rejected, not uncertified. A class where nothing passes gets verdict no gain and
  no best.
- **What the loop may do:** tune knobs within their ranges; choose regions and existing
  contracts; synthesize experimental library entries. Edits that use no contract are kept; they
  have no certification record, so they derive as uncertified, and the summary lists them that
  way.
- **Budgets:**
  - at most 8 iterations, stopping after 4 iterations in which no class's best improved in the
    selection order (a higher certification level, or the same level with a higher lower bound);
  - a lane-hour cap, default 24, counting provider, certification and evaluator wall time;
  - a provider-call budget, default 3 calls per iteration across all agent roles; a usage-limit or
    login failure pauses the Extensa campaign, releases the lane and does not count as an
    iteration;
  - a disk cap, default 20 GB, plus the dispatch preflight;
  - one lane at a time unless Yan-Ru approves two; native timed repetitions never overlap a gem5
    job of any Extensa campaign (D2).
  - The provider-call cap is 3 per iteration plus 1 setup call (the profiling agent), so a
    campaign makes at most 25 counted calls (D7).
- **Targets.** BFS only for now: native CPU against both baselines, and DX100 in gem5 against the
  fork's scalar TDStep.
- **Site finder.** A query over the SQLite access-pattern and step tables, a new statements index,
  and the indexed contract pattern keys. It is built after library indexing exists, so it never
  reads library YAML directly.
- **Library seed.** Extensa's packing, binning, relabeling, regrouping and gather-staging entries
  enter the experimental tier with their Extensa source commit and path as origin and SPDX and
  provenance headers on their C++ bodies. Each gets a plain C++ reference semantics, a
  differential-test driver, negative controls and a matrix before it can be certified.
- **Records.** Every record an Extensa campaign writes carries `mode: extensa` and its Extensa
  campaign ID, set when the record is created; the field is optional (absent means ArchEvolve mode) and is
  never backfilled. Certification level is derived from certification records when queried, never
  stored on candidate-artifact records, which frozen protocols pin. These records go to the Extensa
  campaign record store on mbit10, where they are kept. Only the summary, promoted candidate
  artifacts, and team claims with their evidence are copied into the team record store, tags kept.
  New library entries are committed to the library folder in the experimental tier, with their
  Extensa campaign as origin.
- **Team boundary.** Team-protocol comparisons, handoffs and coverage reports refuse or skip
  Extensa records unless promoted. ArchEvolve-mode submit refuses experimental-tier entries. Loop
  failures stay local; promoted candidate artifacts and deliberate findings go to Josh through the
  rewrite-feedback template, whose candidate ID names his hardware candidate.
- **Promotion.** `swdb promote` records Yan-Ru's review; then a team protocol for the candidate
  artifact's workload class, derived from the current team protocol with only that class's
  workload, re-evaluates it. The Extensa campaign is recorded as its origin.
- **"Is the specification enough?" experiment.** Three inputs: the intrinsic specification only; plus
  Josh's draft; plus our contract. At least three samples per input (nine or more provider
  sessions, up to about 3 lane-hours), with the working rewrite hidden. For each sample, record
  whether it was certified and how many controls it rejected; compare the three inputs. Results
  stay local; the finding goes to Peter.

### ArchEvolve mode

Unchanged: one proposal, one candidate artifact, one evaluation, and the result goes to the team.
Bounded repair (the provider's repair limit, two by default and configurable from zero to five)
fixes only build or correctness failures, and a valid regression never triggers tuning.

## Testing Decisions

- **What makes a good test.** It drives the public `swdb` workflow against a temporary record
  store with contract fixtures (fake compiler, simulator, provider and agent), and asserts only on
  command outcomes and the records written, never on internal functions. Fixtures keep
  `evidence_kind: contract_fixture` and are never real evidence.
- **One seam.** All tests go through the `swdb` command line, including the new commands.
- **Repository gates.** Every new record kind is registered in the record-kind vocabulary and the
  store's kind list, and every new schema field is documented in the format reference, so the
  format-document and format-version tests stay green.
- **Behaviors to test:**
  - Library: required fields and the five entry shapes enforced; every formal half checked in its
    language; no proven label without a formal-verifier verdict; promotion and certification never
    change an entry's content sha256; derived tier and status follow the records; intrinsic records
    accept a hardware interface.
  - Certification: the T17-fixed authors' BFS certifies under the calibration pass rule; every
    calibration, lowering and rewrite control is rejected by a named check; an invalid control
    (build failure, crash) blocks certification; the strict layer rejects the unmodified authors'
    BFS; the Mac input form refuses a rebuilt tree whose manifest digest differs from the snapshot
    record and records the patched tree's sha256.
    These tests do real functional-model builds on tiny graphs and are marked slow.
  - Submit: a patch shipping the lowering header is accepted only when the header's sha256 matches
    the lowering entries' code-file sha256 and both files are editable; other files are rejected;
    ArchEvolve-mode submit refuses experimental entries and entries whose derived status is draft
    or refuted.
  - Protocols and comparisons: a new protocol has no supersedes and leaves T17 comparisons valid;
    it refuses baselines bound before its freeze; the read-only execution case and the
    parent-gather race case are enforced inside the comparison; the baseline role has no
    accelerator cases; per-class verdicts and certification-first selection in Extensa protocols;
    on gem5 one baseline measurement per class serves every candidate artifact, on native each has
    its own paired block; strict `>` against 1.05.
  - Pruning: bulky files are deleted only after re-reading records exist; readers report a pruned
    file with a retention record and still fail on a missing file without one; team-claim runs keep
    their raw output; a failed run's checkpoint is never pruned; the dry-run deletes nothing and
    never proposes inputs; apply refuses an unapproved listing.
  - Preflight: dispatch is refused when the runs disk or the lane's memory node lacks the budget,
    and both values are recorded with the run.
  - More kernels: BC workloads register; the right correctness check, completion witness and
    execution witness are chosen per kernel; BFS records revalidate unchanged.
  - Profiling agent: agent claims stored with basis and provenance; never overwriting;
    contradiction by the stated rule; the per-line callgrind field validates on its own and
    whole-ROI rows are unchanged.
  - Extensa campaigns: each budget stops the loop; a provider usage limit pauses without counting;
    uncertified edits are labeled; the summary is complete; team comparisons, handoffs and
    coverage refuse unpromoted Extensa records; promotion requires a team-protocol re-evaluation.
  - ArchEvolve mode: a valid regression still returns as an outcome without tuning.
- **Prior art:**
  - patch submission and edit scope: `test_proposals`; provider fixtures and repairs:
    `test_bfs_rewrite`;
  - freeze and compare: `test_bfs_protocol`, `test_bfs_shared_protocol`;
  - fixture simulator executions: the `test_bfs_simulator_*` modules;
  - coverage extraction from debug traces: `test_dx100_coverage`, `test_dx100_coverage_scan`,
    `test_dx100_gzip_trace` (driver fixtures: the `test_bfs_dx100_coverage_*` modules);
  - storage accounting and refusing dispatch when space is short (for pruning, disk caps and the
    preflight): `test_bfs_storage`, `test_bfs_simulator_storage`, `test_bfs_native_storage`. There
    is no prior art for deleting raw output; `test_bfs_campaign_cleanup` covers process reaping
    only;
  - region profiling: `test_bfs_profiling`.
- **Acceptance per phase** (recorded as evidence, not tests):
  - Certification: the calibration and the BFS candidate artifact certify on the Mac.
  - First gem5 evaluation: as listed under that section.
  - Pruning: one real run is pruned with sha256s kept, and nothing is deleted retroactively before
    an approved listing.
  - Profiling pilot: all seven TDStep statements annotated and scored against one mbit10 per-line
    callgrind run.
  - BC: workloads register, native evaluation passes BCVerifier, one small gem5 run passes the BC
    completion witness, and BFS records and protocols revalidate unchanged.
  - Extensa mode: one Extensa campaign finishes within its budgets and writes a complete summary.

## Out of Scope

- Deliberately open: what a formally verified rewrite proves first (rewrite equivalence, lowering
  correctness or legality conditions), and integrating any formal verifier. Until then every formal
  predicate is stated. The current recommendation, not a decision, is rewrite equivalence with
  legality conditions discharged by checks that return verdicts.
- MAPLE lowerings, until MAPLE has an ABI and a hardware target the evaluator can run.
- Terminus CAS offload, and DX100's store-based parent update as a rewrite target. The authors'
  version is used only for calibration.
- Kernels other than BFS in Extensa mode, on either target; SSSP and PR on DX100; a high-density
  workload class.
- Run-time selection among per-class bests, and held-out confirmation graphs.
- A head-to-head speedup comparison with Extensa.
- Any change to Extensa's repository (frozen) or to Josh's handoff files (read-only).
- Any change outside `swdb-project/` without Yan-Ru's approval.
- A new shared team exchange schema while LANL's official format is pending.
- Hardware performance counters on mbit10.
- A deadline. The pull request from `yanrujhou_main` to `main` comes after everything here is
  implemented.

## Further Notes

- **Approvals (Q62).** ADR acceptance, commits and team messages need Yan-Ru's approval. Approving
  an mbit10 dispatch (one evaluation batch, or one Extensa campaign within its budgets) also
  approves every run it makes and the automatic pruning of those runs' bulky raw output. Every
  other deletion, including retroactive cleanup, needs its own approval.
- **Evidence basis.** Functional-model and Mac results are pre-check evidence (simulated). gem5
  results are simulated; native mbit10 results are measured; callgrind results are simulated.
  Profiling-agent claims are code_reading or inferred. Peter's performance numbers are reported:
  they are not reproduced and never share a column with measured or simulated numbers.
- **Team communication.** After ticket 03's commit, each teammate hears separately: Peter
  gets the full picture, including Extensa mode and the paper; Josh and Eric get only what touches
  them. Every file named in a message carries its repository path, lines and branch or commit,
  because `swdb-project/` exists only on `yanrujhou_main`.
- **Waiting on teammates (non-blocking).** Eric: whether a DX100 read can return data older than
  CPU stores (L3, L5); whether memory-region registration is required; how instructions from
  several cores are assembled. Peter: his perf command and raw output. These questions belong to
  the Phase 0 decision note (the eight design decisions sent to Peter, Eric and Josh); record its
  send date when it goes out.
- **Confirmed 2026-10-03** (Q63–Q65): one source per class graph on gem5, reported as point
  ratios; no region pairs in the first gem5 protocol (6 runs, about 2.8 h of lane time; a
  follow-up protocol can add them); the parent-gather race case as the new companion case.
  **Decided, pending Peter (Q66):** ported Extensa files carry Apache-2.0 WITH LLVM-exception,
  matching MemAcc's LICENSE. Peter confirms it or names another license before any file is
  ported, since ArchEvolve has no license.
- **Pins.** Josh's package for the first entries:
  `runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/intrinsic-draft.yaml`, sha256
  `01f05bdc517922a082a10c9e28d8f1501c92892ba06a1e5298a60e7cc5d0bf30`, hardware candidate
  `gapbs_bfs_top_down_step--dx100-artifact-e4fc4af--read_execute`. Extensa: `MaizeHPC/MemAcc`,
  folder `AgenticRefiner/`; the port pins a commit (local checkout at `af3d6d7f7` on 2026-10-03).
  Peter's v1.1: `docs/bfs-intrinsics-spec-yanru.md` at the ArchEvolve root, commit `0b56895`,
  sha256 `3e54374ae43c841bad3f71d9210cb110742dfdb1bf688cde1953de9df64aabf9`; section 3 defines the
  intrinsics and section 5 is the example rewrite. `docs/peter-intrinsics-handoff.md` is Josh's
  upstream input, not the specification.
- **Estimated effort:**

  | Phase | Effort |
  |---|---|
  | Design session (glossary, spec, tickets done; ADRs in ticket 03) | ~4 h |
  | Library, strict layer, lowerings, certification and patch on the Mac | ~24 h |
  | First gem5 evaluation (incl. new accelerator and companion cases) | ~10 h of work and ~3 h of lane time |
  | Pruning and retroactive cleanup | ~8 h |
  | Profiling-agent pilot | ~6 h |
  | Evaluator for more kernels, with BC | ~30–40 h |
  | Extensa mode | ~59 h of work plus ~25 lane-hours (re-estimated by ticket 47, D12) |

- **Dated facts** (re-check before relying on them): one gem5 timed run takes about 35–41 minutes
  of simulation and 32–34 GB of peak memory; a companion run takes about 5 minutes; mbit10 has
  about 125 GiB of RAM in two memory nodes of about 62 GiB each, and two socket lanes.
