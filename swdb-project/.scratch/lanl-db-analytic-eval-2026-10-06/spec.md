# Spec: Analytic speed estimates and main-database compatibility

Created: 2026-10-06 ET
Updated: 2026-10-06 16:11 ET (ticket number reference updated for the regenerated tickets); 2026-10-06 16:07 ET (rewritten to the full spec template: problem, solution, user stories,
implementation and testing decisions; decisions D1–D34 unchanged); 2026-10-06 ET, before the 16:01 ET
design-session commit `6c691e6` (D8–D15 confirmed; grilling rounds 1–4 added D16–D34; estimator
workflow approved)
**Type:** spec
**Status:** ready-for-agent (implementation starts only on Yan-Ru's explicit go-ahead)
**Blocked by:** None
Owner: Yan-Ru Jhou
Decision records: [ADR 0013](../../docs/adr/0013-archevolve-mode-estimates-speed.md) and
[ADR 0014](../../docs/adr/0014-main-and-research-databases.md) (both proposed). They narrow ADR 0002
and ADR 0008 and clarify ADR 0009.
Inputs: the ArchEvolve overview deck (LANL slides dated 10/6/2026); Yan-Ru's discussion with Scott
and the project manager (2026-10-06); [lanl-db-notes.md](lanl-db-notes.md);
[three-way-scan-analytic-evaluators.md](three-way-scan-analytic-evaluators.md).
Map and tickets: [map.md](map.md)

## Summary (read this first)

1. **ArchEvolve mode:** correctness still executes; speed is **estimated** wherever no real machine
   exists. No gem5 runs, no gem5 numbers.
2. **The estimator is general:** reusable mechanism models, combined per target description, with
   no code specific to one kernel or one target. Version 1 estimates time only.
3. **Extensa mode** (Yan-Ru's research) keeps gem5. Every candidate artifact gets a blind paired
   estimate (flow A); screening (flow B) starts only if a rule fixed in advance passes.
4. **Research question for Extensa's evaluation:** can a cheap estimate pick the same rewrites gem5
   would?
5. **Databases:** LANL's database is the main database; SWDB is the research database; a crosswalk
   keeps them compatible, and either may later merge or go away.

## Problem Statement

Yan-Ru owns ArchEvolve's software side. The project's direction changed on 2026-10-06:

- **The team evaluator is analytic.** The overview deck's Month 6 milestone ranks candidates with a
  "tiered performance model", and the team has no simulator. Scott asked SWDB to estimate
  performance with compiler analysis, LLM agents or a hybrid, not to run gem5.
- **SWDB's evaluator cannot do that today.** It times code natively on mbit10 and simulates DX100
  code in gem5; one DX100 gem5 run takes about 35–41 minutes and 32–34 GB of memory. Under
  ADR 0008, DX100 code counts as correct only after a gem5 run, so in ArchEvolve mode, without
  gem5, no DX100 candidate artifact could ever pass.
- **Nobody owns the team evaluator yet.** If SWDB builds a good prototype, LANL may adopt it, so it
  must be general and documented, not a DX100-only tool.
- **The main database is LANL's, and we have no access to it.** SWDB must read it later, contribute
  to it, and survive a future merge or replacement without breaking the paper's citations.
- **Yan-Ru's research still needs gem5.** Extensa mode evaluates rewrites on DX100 in gem5, and the
  paper needs a question that a cheap estimate can help answer.

## Solution

From Yan-Ru's side, after this feature:

- **In ArchEvolve mode,** a candidate artifact for a target without hardware (DX100, MAPLE) is built,
  checked for functional-target correctness, and estimated. The team receives an estimate with its
  basis, a per-region report of what limits the speed, and a verdict in three states. A CPU target
  is still timed natively, with the estimate recorded beside the timing.
- **The estimator** reads a workload characterization (what the code does on one input, per region)
  and a target description (the target's mechanism models and parameters, each with a basis). The
  characterization comes from an LLVM pass: one static analysis of the compiled code, and one native
  run with counters the pass inserts. Accelerator memory behavior comes from counting over the real
  address stream during that run. An LLM fills only parameters nobody knows, once per target
  description, and its values are frozen.
- **In Extensa mode,** every candidate artifact is estimated before it is timed. After enough
  campaigns, an agreement report applies the rule fixed in D30. Only then does Yan-Ru decide whether
  the loop switches to screening.
- **For the main database,** a crosswalk maps its tables to SWDB record kinds, and SWDB reads records
  through one access layer. An import and an export through LANL's own ingest follow when LANL grants
  access; until then, notes are ready and nobody contacts LANL.

## User Stories

### Direction and scope

1. As Yan-Ru, I want ArchEvolve mode to estimate speed instead of simulating it, so that SWDB follows Scott's direction and the deck's analytic evaluator.
2. As Yan-Ru, I want ArchEvolve mode to refuse gem5 runs and gem5 numbers, including for calibration and validation, so that no team result quietly depends on a simulator.
3. As Yan-Ru, I want Extensa mode to keep gem5 and the functional model, so that my research continues unchanged.
4. As Yan-Ru, I want the estimator built as a documented prototype, so that LANL can adopt it if it works.
5. As Scott, I want the estimate to rely on compiler analysis and counting, with an LLM only filling gaps, so that it matches the approach I asked for.
6. As the project manager, I want estimates to fit the deck's tiered performance model, so that Month 6's evaluator milestone has a software-side answer.

### Correctness without hardware

7. As Yan-Ru, I want DX100 code in ArchEvolve mode to pass functional-target correctness (the kernel's correctness check and certification on the functional model's strict layer), so that it can be evaluated without gem5.
8. As a teammate reading a result, I want functional-target correctness labeled as such, so that I never mistake it for correctness on the hardware target.
9. As Yan-Ru, I want the strict layer's hazard checks (reads before a covering wait, shared tiles, truncation, out-of-region accesses) kept in that check, so that the functional model's instant completion does not hide defects like the authors' wrong-tile wait.

### Workload characterization

10. As Yan-Ru, I want one workload characterization per candidate artifact (or baseline implementation) and input, so that every estimate starts from the same recorded facts.
11. As the estimator, I want each region's access patterns with address shape, stride, element bytes and element counts, so that I can compute bytes moved per access type.
12. As the estimator, I want operation counts by class (integer, floating point, branch, atomic) per region, so that I can compute a compute bound.
13. As the estimator, I want dynamic counts (loop trip counts, executions per access, footprint) from a real run on the real input, so that data-dependent loops such as neighbor lists are counted, not guessed.
14. As the estimator, I want accelerator calls listed with their sizes, so that I can charge offload work and setup cost.
15. As Yan-Ru, I want regions to be the same function and loop regions SWDB already uses in profile packages and the site finder, so that estimates attach to exactly the code rewrites target.
16. As Yan-Ru, I want loops the pass cannot map onto a region listed, never dropped, so that nothing disappears silently.
17. As Yan-Ru, I want the characterization's field names to match Peter's feature reports where they overlap, so that the team reads one vocabulary.
18. As Yan-Ru, I want a reader that imports Peter's feature reports as one input source, so that his facts feed the estimator without SWDB depending on his schema.
19. As a future adopter at LANL, I want the characterization format documented on its own, so that another evaluator can read it.
20. As Yan-Ru, I want unknown facts to stay null in the characterization, so that unknown never turns into zero or false.

### Static analysis and counting

21. As Yan-Ru, I want the static analysis to run on the compiled LLVM IR, so that it sees inlining and vectorization as the compiler produced them.
22. As Yan-Ru, I want the pass to classify every memory access by how its address is computed (stream, single-valued indirect, ranged indirect, pointer chase, data-dependent merge), so that classifications use the existing address-shape vocabulary.
23. As Yan-Ru, I want the pass's classifications compared with the hand-written access patterns of the BFS and BC implementation records, so that I can trust it on new code.
24. As Yan-Ru, I want OpenMP regions, which the compiler moves into separate functions, mapped back to their source regions, so that parallel loops are characterized like serial ones.
25. As Yan-Ru, I want the same pass to insert counters for one native run, so that static facts and dynamic counts come from one tool.
26. As Yan-Ru, I want counts taken at the source level, so that they do not depend on the machine that ran them, with the host recorded anyway.
27. As the estimator, I want the address stream counted live for each target's mechanisms (for example, distinct DRAM rows per reorder window), so that rewrites that change access order get different estimates.
28. As Yan-Ru, I want no address stream written to disk, so that a large graph's half-gigabyte neighbor stream never fills a run disk.
29. As Yan-Ru, I want small graphs characterized on the Mac and large ones on mbit10, so that development is fast and big inputs stay on the lab host.

### Target descriptions and mechanism models

30. As Yan-Ru, I want each hardware target described by its mechanism models and parameter values, each with a basis and a source, so that every number in an estimate can be traced.
31. As the estimator, I want mechanism models that each model one hardware behavior (reorder-window row counting, cache fit, fetch queue, tile staging, offload setup, compute throughput, requests in flight), so that new targets reuse them.
32. As Yan-Ru, I want mechanisms keyed to a design's operations and parameters, never to the hardware catalog's mechanism families alone, so that the model follows what the catalog says a design can do.
33. As Yan-Ru, I want mbit10's description built from its machine record plus microbenchmarks, so that its bandwidths are measured, not copied from a datasheet.
34. As Yan-Ru, I want DX100's description built from its hardware-target record, its pinned configuration and the DX100 paper, so that its values are `code_reading` or `reported`.
35. As Yan-Ru, I want MAPLE's description built from Eric's catalog and the MAPLE paper, so that a second accelerator tests generality.
36. As Yan-Ru, I want a ranked list of each target's unknown parameters, so that I know which unknown moves an estimate most.
37. As a hardware teammate, I want the target-description format written so the HW team could own it, so that the Hardware Database can supply it later.
38. As Yan-Ru, I want target descriptions versioned by content hash, so that every estimate names the exact description it used.

### Hybrid filling by an LLM

39. As Yan-Ru, I want an estimation agent role that fills only unknown parameters, so that the LLM never overrides known facts.
40. As Yan-Ru, I want the estimation role to read the characterization and the profile, never candidate timings, so that its values cannot be tuned to the answer.
41. As Yan-Ru, I want the role to run once per target-description version, with its values frozen into that version, so that estimates are reproducible.
42. As a teammate, I want every LLM-filled value labeled `estimated` with a stated reason, so that I can judge it.
43. As a teammate, I want an estimate that depends on an LLM-filled value to list it and show how much the result moves if that value is halved or doubled, so that I see how fragile it is.
44. As Yan-Ru, I want the role to use the same provider pins, workspace rules and audit as the other agent roles, so that it adds no new trust path.

### Estimation and reporting

45. As Yan-Ru, I want an estimate to cover exactly what its paired timing covers (the whole timed call including setup, the target's thread count, the same graphs), so that estimates and timings compare like for like.
46. As the estimator, I want each region's time to be its largest bound plus overhead, and the total the sum over regions plus the serial remainder, so that the model is simple enough to explain.
47. As a teammate, I want a per-region report naming the limiting bound, each bound's value and the parameters it used, so that I see why a rewrite is or is not faster.
48. As Yan-Ru, I want an unknown parameter to make the bound that needs it unknown, never zero, so that the estimator does not invent speed.
49. As Yan-Ru, I want every estimate to carry the basis `estimated`, so that comparisons and selection can tell it from measurements and simulations.
50. As Yan-Ru, I want estimate protocols that freeze the estimator version and the target description's hash, so that estimates are reproducible like other frozen protocols.
51. As Yan-Ru, I want estimates allowed beyond the graph sizes gem5 can run, labeled `beyond_paired_range`, so that ArchEvolve can explore realistic sizes honestly.

### Verdicts in ArchEvolve mode

52. As a teammate, I want a verdict in three states (`estimated_gain`, `within_error`, `estimated_no_gain`), so that I never act on a gain smaller than the estimator's error.
53. As Yan-Ru, I want the verdict to say `within_error` until the target's error band is validated, with the ratio still shown, so that early results are not overclaimed.
54. As Yan-Ru, I want a CPU target's verdict to come from native timing, with the estimate recorded beside it, so that real hardware decides wherever it exists.
55. As a teammate, I want the evaluation-result handoff message to carry the estimate, its basis and its verdict, so that I receive the same evidence SWDB records.

### Validation

56. As Yan-Ru, I want CPU estimates checked against existing ArchEvolve-mode native timings on mbit10, so that the CPU error band is measured.
57. As Yan-Ru, I want the CPU error check to use ArchEvolve-mode timings only, never Extensa's, so that research records stay out of team results.
58. As Yan-Ru, I want DX100 estimates compared with the DX100 paper's reported speedups and labeled a weak check, so that a gross error shows up without gem5.
59. As Yan-Ru, I want PageRank and MAPLE estimated with no estimator code change, so that generality is demonstrated, not claimed.
60. As Yan-Ru, I want the estimator to hold no kernel-specific or target-specific code, so that a new kernel or target needs only records and a description.
61. As Scott, I want to see once that counting over the address stream is not simulation, so that the approach stays inside my direction.

### ArchEvolve-mode guard

62. As Yan-Ru, I want team protocols to refuse a gem5 target, a gem5-derived record, or an estimator calibrated with gem5 data, so that the rule holds by construction.
63. As Yan-Ru, I want existing ArchEvolve-mode gem5 records kept as history, so that nothing already recorded is lost.
64. As Yan-Ru, I want refusals to name the rule and the offending record, so that a refused run is easy to fix.

### Extensa mode

65. As Yan-Ru, I want every Extensa candidate artifact and baseline to get a paired estimate, so that I collect estimate–timing pairs without changing the loop.
66. As Yan-Ru, I want selection unchanged by paired estimates, so that flow A cannot alter campaign results.
67. As Yan-Ru, I want each estimate made before its candidate's timing exists, with the order recorded, so that agreement cannot be inflated after the fact.
68. As Yan-Ru, I want paired estimates tagged with the campaign and Extensa mode, so that they never enter team protocols.
69. As Yan-Ru, I want an agreement report (rank agreement between estimate and timing, and whether gem5's best candidate survives a top-3 cut by estimate), so that I can answer the research question.
70. As Yan-Ru, I want the rule for switching to screening fixed now (at least 20 DX100 pairs; Kendall's tau at least 0.6 with its 95% interval's lower bound at least 0.3; gem5's best inside the estimate's top 3 in every campaign), so that a reviewer cannot say I moved the bar.
71. As Yan-Ru, I want to make the final switching decision myself after reading the report, so that the research direction stays mine.
72. As Yan-Ru, I want a research variant of the estimator, calibrated with Extensa's gem5 pairs, kept apart from the team estimator, so that I can study calibration without breaking the ArchEvolve rule.
73. As Yan-Ru, if screening is chosen, I want one rewrite call to yield N variants (knob values or sites), all certified and estimated, with only the top-k plus one random spot check timed, so that gem5 hours buy more explored candidates.
74. As Yan-Ru, I want untimed variants kept with their estimates but never ranked as timed, so that selection stays on timings.
75. As Yan-Ru, I want the spot check's results recorded, so that the rate at which screening keeps the winner stays measured.

### Databases

76. As Yan-Ru, I want LANL's database treated as the main database and SWDB as the research database, so that both roles are explicit.
77. As Yan-Ru, I want a crosswalk from main-database tables and fields to SWDB record kinds and fields, marked unverified until we see the schema, so that compatibility work starts without access.
78. As Yan-Ru, I want SWDB's tools to read records through one access layer, so that pointing them at another database later means writing one adapter.
79. As Yan-Ru, I want an import that keeps every main-database ID, so that records can be traced back after a merge.
80. As Yan-Ru, I want contributions to the main database to go only through its own ingest inputs, never by writing its SQLite file, so that LANL's pipeline stays authoritative.
81. As Yan-Ru, I want a round-trip test (import, export, their ingest, import again), so that compatibility is checked, not assumed.
82. As Yan-Ru, I want SWDB-only concepts (strategies, intrinsics, certifications, the evidence basis) kept as a separable extension, so that a merge can include or omit them.
83. As a paper reviewer, I want each paper result to cite a frozen SWDB commit, so that a later merge or replacement never breaks the citation.
84. As Yan-Ru, I want the LANL request drafted only when I decide to contact them, so that nothing goes out before I choose.
85. As a LANL database owner, I want SWDB's records to keep my IDs and use my ingest, so that SWDB contributions fit my pipeline.

### Later

86. As Yan-Ru, I want XSBench added after generality is shown, so that the estimator reaches the main database's fusion kernels.
87. As Yan-Ru, I want energy estimated later as an extension of the mechanism models, so that the deck's energy and performance-per-watt gates can follow without redesign.

## Implementation Decisions

### Decision register

Decided by Yan-Ru on 2026-10-06 (in conversation):

| # | Decision |
|---|---|
| D1 | LANL's database is the main database; SWDB is the research database; they stay compatible, and they may later merge or SWDB may be dropped (ADR 0014). |
| D2 | Do not contact LANL now; prepare notes only ([lanl-db-notes.md](lanl-db-notes.md)). |
| D3 | ArchEvolve mode runs no gem5 job and cites no gem5 number, including for validation (ADR 0013). |
| D4 | ArchEvolve-mode speed comes from the estimator: analytic bounds, with an LLM filling only parameters the model lacks. |
| D5 | Extensa mode keeps gem5 and the functional model; flow A (paired estimates) first, flow B (screening) only after agreement is measured. |
| D6 | Extensa's evaluation answers: "Can a cheap estimate pick the same rewrites gem5 would?" |
| D7 | No team evaluator owner is known; SWDB builds the estimator as an adoptable prototype with a documented input format. |

Proposed by Claude and confirmed by Yan-Ru on 2026-10-06:

| # | Decision |
|---|---|
| D8 | ArchEvolve-mode DX100 correctness is functional-target correctness: native build on the functional model's strict layer, the kernel's correctness check, and certification; never reported as correctness on the hardware target. Narrows ADR 0008. |
| D9 | New evidence basis `estimated`, distinct from `inferred`. |
| D10 | The estimator in team protocols is frozen without any gem5 data; Extensa's paired estimates may calibrate a separate research variant that never enters a team protocol. |
| D11 | The workload characterization is a new SWDB format, `swdb.workload-characterization.v1` (refined by D20); the retired SPARTA workload view stays historical. |
| D12 | Static analysis is an LLVM pass (LLVM 22 on the Mac; a toolchain under the lab work root on mbit10); dynamic counts come from an IR-level instrumented native run, counted at source level; the host is recorded. |
| D13 | Superseded by D25. |
| D14 | Validation in ArchEvolve mode: CPU estimates against existing native mbit10 timings; DX100 estimates only against the DX100 paper's reported numbers, labeled a weak check. |
| D15 | First kernels: BFS, then BC. |

Decided in the grilling (Yan-Ru, 2026-10-06):

| # | Decision |
|---|---|
| D16 | An estimate covers exactly what its paired timing covers: the whole timed call including accelerator setup, the target's thread count and the same graphs; seconds per region and total; ratios derived. |
| D17 | Accelerator memory behavior is estimated by counting over the real address stream, with paper-reported parameters as the fallback. The approach must be general, not DX100-specific. Scott sees the counting approach once. |
| D18 | ArchEvolve mode may read a target's configuration from its pinned source (basis `code_reading`); gem5 outputs are never read. |
| D19 | The LLM fills unknown parameters once per target-description version; the values are frozen into that version; dependent estimates list them with a halve/double sensitivity. |
| D20 | The characterization reuses Peter's feature-report field names where they overlap, with a reader that imports his reports as one input source. |
| D21 | The estimator is built from mechanism models (one hardware behavior each), combined per target description; mechanisms are keyed to a design's operations and parameters. |
| D22 | Generality is shown on the mbit10 CPU, DX100 and MAPLE, and on BFS, BC and PageRank, with no estimator code change; gem5 agreement is measured on DX100 only; XSBench follows after Phase 2. |
| D23 | SWDB writes the first target descriptions from Eric's catalog, citing his claims, and offers the format to the HW team. |
| D24 | The address stream is counted live in the instrumented run, once per target description; no stream is stored. |
| D25 | Verdicts have three states: `estimated_gain` only if the ratio stays above 1.05 after subtracting the error band; `within_error` if the band covers 1.05; otherwise `estimated_no_gain`. Until a band is validated, the verdict is `within_error`. |
| D26 | Extensa estimates are blind: made before the timing exists, from inputs without timings, with the order recorded. |
| D27 | In ArchEvolve mode, a CPU target's verdict comes from native timing, with a paired estimate beside it; targets without hardware get estimate-only verdicts. |
| D28 | The team estimator's CPU error check uses ArchEvolve-mode timings only. |
| D29 | Estimates may go beyond gem5's graph sizes, labeled `beyond_paired_range`, never counted in agreement statistics. |
| D30 | The switching rule for flow B is fixed now: at least 20 DX100 pairs; Kendall's tau at least 0.6 with its 95% interval's lower bound at least 0.3; gem5's best inside the estimate's top 3 in every campaign. Yan-Ru makes the final call but does not change the rule after seeing data. |
| D31 | Ticket 30 of the typed-library map (sending the first gem5 result as a team claim) is closed as wontfix under ADR 0013. |
| D32 | Version 1 estimates time only; energy later, as an extension of the mechanism models. |
| D33 | Regions are the existing profile-package and site-finder regions, with the same IDs; unmapped loops are listed. |
| D34 | Scott sees the counting approach after the estimator works; accepted risk: if he calls it simulation, counting falls back to paper-reported parameters. |

### Estimator workflow and tools

Approved by Yan-Ru on 2026-10-06:

```
candidate source ─► 1. clang -O3 -emit-llvm ─► 2. static LLVM pass ─► per-loop facts
                                              3. same pass inserts counters ─► one native run (counts only)
                                              ─► workload characterization
target ─► 4. target description ─► 5. LLM fills unknowns once (frozen)
characterization + description ─► 6. mechanism models: bounds per region ─► 7. report, ratio, verdict
```

| Need | Tool | Not chosen |
|---|---|---|
| Static facts | LLVM 22 IR pass: loop information, scalar evolution to classify addresses, debug information to map regions | Clang AST (misses inlining and vectorization); MLIR (our code enters through clang as C++) |
| Dynamic counts and live address-stream counting | Counters inserted by the same pass, with a small runtime | callgrind (slow; cannot count addresses live); DynamoRIO or Pin (a second toolchain) |
| Compute bound | Operation counts × issue width | llvm-mca (models the pipeline cycle by cycle, too close to simulation under D3) |
| CPU memory parameters | Microbenchmarks on mbit10 inside a socket lane | Datasheet numbers |
| Unknown accelerator parameters | The estimation agent role, once per target-description version | — |

Known hard parts: OpenMP regions are outlined into separate IR functions (mapped back through debug
information); data-dependent trip counts need the counted run; row counting needs a DRAM address
layout (DX100's pinned configuration; MAPLE's paper).

### Modules and their interfaces

- **Evidence vocabulary.** Gains the basis `estimated` (D9). Every place that accepts a basis
  accepts it; every existing record validates unchanged.
- **Estimate record.** An estimate names its estimator version, target-description hash,
  characterization hash, target, input and protocol; holds seconds per region and in total, the
  per-region report, the list of LLM-filled parameters with their sensitivity, and the verdict or
  the paired timing's reference. Whether it is a new record kind or a section of the evaluation
  record is chosen in ticket 04 by the smaller change; either way comparison and selection can tell
  it apart from measurements and simulations.
- **Workload characterization (format `swdb.workload-characterization.v1`).** One per (candidate
  artifact or implementation, input). Per region (existing region IDs): access patterns (address
  shape, stride, element bytes, element-count formula and evaluated value, basis), operation counts
  by class, dynamic counts, footprint, accelerator calls with sizes, and per-target address-stream
  counts keyed by target-description hash. Unknown stays null. Field names follow Peter's feature
  reports where they overlap; a reader imports his reports as one source.
- **Characterizer.** Interface: a buildable source (candidate artifact or baseline), its build flags,
  an input and optionally a target description → a characterization. Internally: compile to IR, run
  the static pass, build the instrumented binary, run it once, merge. The evaluator's build flags and
  protected-driver rules apply unchanged. The static pass knows accelerator commands by name from the
  intrinsic records, not from hard-coded lists.
- **Target description.** A versioned document per hardware target: its mechanism models, each
  mechanism's parameters with value, basis, source and unit, and the DRAM address layout when a
  mechanism counts rows. Unknown values stay null until the estimation role fills them in a new
  version.
- **Mechanism-model library.** Interface per mechanism: a region of the characterization plus the
  mechanism's parameters → one or more bounds in seconds, each with the formula's inputs. Composition
  per region: the largest bound plus overheads; total: sum of regions plus the serial remainder.
  Mechanisms for version 1: compute throughput, requests in flight (latency bound), cache fit,
  reorder-window row counting (row-buffer hit rate), fetch queue, tile staging and offload setup.
- **Estimator command.** Interface: a candidate artifact or implementation, an input, a target
  description and an estimate protocol → an estimate record. With a baseline, it also computes the
  ratio and, in ArchEvolve mode, the three-state verdict (D25).
- **Estimation agent role.** A role in the existing provider launcher with its own strict input and
  output schemas. Input: characterization, profile, the description's unknown entries. Output: value
  and reason per unknown. It never sees timings, evaluator code or other candidates. Its output
  becomes a new target-description version.
- **Estimate protocol.** Freezes the estimator version and the target-description hash like other
  frozen protocols. A team protocol may name only an estimator version frozen without gem5 data.
- **ArchEvolve-mode guard.** Team protocols and ArchEvolve-mode commands refuse a gem5 target, a
  gem5-derived record, or a gem5-calibrated estimator, naming ADR 0013 and the offending record.
  Extensa mode is untouched.
- **ArchEvolve-mode evaluation for targets without hardware.** Build → functional-target correctness
  (D8) → estimate → verdict (D25) → evaluation record → evaluation-result handoff message, whose
  format version is bumped to carry the estimate.
- **ArchEvolve-mode evaluation for CPU targets.** Unchanged native timing decides; a paired estimate
  is recorded beside it (D27).
- **Extensa campaign loop.** Each iteration estimates every candidate artifact and baseline before
  timing it (D26), records both in the campaign summary, and selects on timing only. A later agreement
  report applies D30. Flow B, if chosen, adds variants and screening without changing selection rules.
- **Microbenchmarks.** Effective bandwidth and requests in flight per access type on mbit10, run
  through the two-lane procedure, written into mbit10's target description with basis `measured`.
- **Crosswalk.** A versioned, machine-readable mapping from main-database tables and fields to SWDB
  record kinds and fields (or "no counterpart"), every row `unverified` until LANL's schema is seen.
- **Access layer.** One interface for every record read and query, beside the record store; the
  direct SQLite reads in the query and site-finder modules move behind it with no behavior change.
- **Import and export (blocked on access).** A read-only import that keeps every main-database ID
  and reports unmapped fields; an export that writes the main database's own ingest inputs.

### Schema changes

- Basis vocabulary: `estimated`.
- New formats: workload characterization v1, target description v1, estimate (record kind or
  evaluation section), crosswalk v0.
- Evaluation-result handoff message: new version carrying estimate, basis, verdict and band.
- Campaign summary: per-candidate paired estimate and the estimate-before-timing order.
- Bottleneck vocabulary: new values for limits it lacks (accelerator throughput, offload overhead).
- Records: a generic map of external IDs, added with the import.

## Testing Decisions

### What makes a good test here

- Tests check external behavior through the four seams below, never internal functions of the
  estimator or the pass.
- Numbers in tests are fixtures with hand-computed answers, never evidence (the repository's existing
  convention).
- A test that needs LLVM 22 skips cleanly when it is missing, like the existing compiler-dependent
  tests.
- No test depends on mbit10, gem5 or a live LLM provider.

### Seams (confirmed by Yan-Ru on 2026-10-06)

1. **New: the estimator commands (characterize and estimate) run against a copied record store.**
   - Tiny C++ fixture kernels, one per address shape, with hand-computed counts and bounds.
   - The pass's classifications against the 13 hand-written access patterns of `gapbs-bfs-do` and the
     BC records; mismatches listed.
   - Formulas against counts within a stated tolerance.
   - An unknown parameter yields an unknown bound, never zero.
   - Three-state verdicts for ratios on both sides of the band.
   - Generality: the PageRank and MAPLE estimates run with an unchanged estimator.
   - Prior art: the workload-view tests, which run a command over a copied repository and compare the
     output's shape.
2. **Existing: the campaign command with the fixture target adapter.**
   - Paired estimates appear in the campaign summary.
   - Each estimate's time precedes its candidate's timing.
   - Selection results are identical with and without paired estimates.
   - Prior art: the campaign-structure tests.
3. **Existing: the provider launcher with a stub provider.**
   - The estimation role's schemas; a value for a known parameter is rejected; output becomes a new
     target-description version; timings never appear in its workspace.
   - Prior art: the provider-role schema tests.
4. **Existing: validate and freeze-protocol.**
   - `estimated` validates; the new formats validate; every existing record still validates.
   - Team protocols refuse gem5 targets, gem5-derived records and gem5-calibrated estimators.
   - Prior art: the validation-rule tests.

The crosswalk and the access layer need no new seam: the existing query-command tests must give the
same output before and after.

## Out of Scope

- Formal verification (a later conversation).
- Contacting LANL, Peter, Josh, Eric or Scott; drafts only, on request.
- Deleting gem5 code: ArchEvolve mode refuses it; Extensa mode keeps it.
- Energy in version 1 (D32); power, area and cost later.
- Cycle-level or pipeline models, including llvm-mca (D3).
- The import and export before LANL grants access.
- XSBench before generality is shown (D22).

## Further Notes

- **Literature grounding** ([three-way scan](three-way-scan-analytic-evaluators.md)): the hybrid shape
  follows Concorde (analytic bounds plus a learned correction); empirical counts for irregular access
  follow MAPredict; feeding the LLM profiles follows Bolet et al. (64% from source alone, 100% with
  profiling data). No surveyed model estimates a shared, programmable indirect-access accelerator on
  graph kernels without a simulator; that gap is the research contribution.
- **Accepted risks:** Scott may call address-stream counting simulation (D34; fallback to
  paper-reported parameters); DX100's error band stays loose in ArchEvolve mode (D14); the agreement
  report needs about 13 h of gem5 lane time for 20 pairs.
- **Open item for flow B:** whether certification cost depends on knob values. If it does, variants
  differ only in knobs, so one certification covers them all.
- **Adoption:** the characterization and target-description formats are written for outside
  readers, so LANL or the HW team can take them over.
