# Spec: Analytic speed estimates and main-database compatibility

Created: 2026-10-06 15:40 ET
Updated: 2026-10-06 17:45 ET (estimator workflow and tools; design confirmed); 2026-10-06 17:25 ET (grilling round 4: D31–D34; grilling complete); 2026-10-06 17:10 ET (grilling round 3: D26–D30); 2026-10-06 16:45 ET (grilling round 2: D21–D25; tickets 23–25); 2026-10-06 16:30 ET (grilling round 1: D16–D20); 2026-10-06 16:05 ET (D8–D15 confirmed by Yan-Ru)
**Type:** spec
**Status:** ready-for-agent (design confirmed 2026-10-06 17:45 ET; implementation starts only on Yan-Ru's explicit go-ahead)
**Blocked by:** None
Owner: Yan-Ru Jhou
Decision records: [ADR 0013](../../docs/adr/0013-archevolve-mode-estimates-speed.md) and
[ADR 0014](../../docs/adr/0014-main-and-research-databases.md) (both proposed); they narrow ADR 0002
and ADR 0008 and clarify ADR 0009.
Inputs: the ArchEvolve overview deck (LANL slides dated 10/6/2026); Yan-Ru's discussion with Scott
and the project manager (2026-10-06); [lanl-db-notes.md](lanl-db-notes.md);
[three-way-scan-analytic-evaluators.md](three-way-scan-analytic-evaluators.md).
Map: [map.md](map.md)

## Summary

1. **ArchEvolve mode:** correctness still executes; speed is **estimated**. No gem5 runs and no gem5
   numbers.
2. **Extensa mode** (Yan-Ru's research) keeps gem5 and the functional model. It adds **paired
   estimates** first (flow A), and **screening** only once estimates agree with gem5 (flow B).
3. **Research question for Extensa's evaluation:** can a cheap estimate pick the same rewrites gem5
   would?
4. **Databases:** LANL's database is the main database; SWDB is the research database. They stay
   compatible through a crosswalk, and either may later merge or go away.
5. **General, not DX100-specific:** the approach must hold for other hardware and other software (D17).
6. Formal verification is out of scope here.

## Problem statement

- The deck's Month 6 Evaluator ranks candidates with a "tiered performance model", and the team has
  no simulator. Scott asked for estimates from compiler analysis, LLM agents or a hybrid, not gem5.
- SWDB's evaluator times code natively on mbit10 and simulates DX100 code in gem5. One DX100 gem5 run
  takes about 35–41 minutes and 32–34 GB of memory. Under ADR 0008, DX100 code counts as correct
  only after a gem5 run, so without gem5 nothing can pass in ArchEvolve mode.
- Nobody owns the team evaluator yet. A good SWDB prototype may be adopted by LANL.
- The main database is LANL's, and we have no access to it. SWDB must read it later, and must
  survive a future merge or replacement.

## Decisions

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

Agent defaults (Claude, 2026-10-06), **confirmed by Yan-Ru on 2026-10-06** ("good." in reply to the
review request, which listed D8, D9, D10, D14 and the glossary retitle):

| # | Default | Why |
|---|---|---|
| D8 | ArchEvolve-mode DX100 correctness is **functional-target correctness**: native build on the strict layer of the functional model, the kernel's correctness check, and certification. It is never reported as correctness on the hardware target. Narrows ADR 0008. | Without it, no DX100 code can pass in ArchEvolve mode. The strict layer exposes the hazards the plain functional model hides (reads before a covering wait, shared tiles). |
| D9 | New evidence basis `estimated`, distinct from `inferred`. | Comparisons and selection must be able to filter estimates; `inferred` already marks rule-derived facts on records. |
| D10 | The estimator in team protocols is frozen without any gem5 data. Extensa's paired estimates may calibrate a separate research variant that never enters a team protocol. | Keeps D3 strict while letting the research learn from gem5. |
| D11 | The workload characterization is a new format, `swdb.workload-characterization.v1`, built from implementation access patterns (ADR 0003) and counts; the retired SPARTA workload view (`swdb view`) stays historical. | `swdb view` already joins the right records, but its format is retired. |
| D12 | Static analysis is an LLVM pass (Homebrew LLVM 22 on the Mac; a toolchain under `/data1/yanruj` on mbit10). Dynamic counts come from an IR-level instrumented native run, counted at source level so they do not depend on the machine; the host is recorded anyway. | LLVM 22 is installed on the Mac. Counts, unlike times, carry over between machines. |
| D13 | (Superseded by D25.) An ArchEvolve-mode verdict from estimates is a point ratio: `estimated_gain` when the ratio exceeds 1.05 (gem5's existing threshold), reported with the estimator's validated error band for that target. | Estimates have no run-to-run noise; their uncertainty is model error. |
| D14 | Validation in ArchEvolve mode: CPU estimates against existing native mbit10 timings; DX100 estimates only against the DX100 paper's reported numbers (basis reported), labeled a weak check. | D3 leaves no stronger DX100 reference in ArchEvolve mode. |
| D15 | First kernels: BFS, then BC (both have native and DX100 paths in SWDB). | Reuses existing records, baselines and evaluations. |

Decided in grilling (Yan-Ru, 2026-10-06; round 1):

| # | Decision |
|---|---|
| D16 | An estimate covers exactly what its paired timing covers: the whole timed call including accelerator setup, the target's thread count and the same graphs. It reports seconds per region and in total; ratios are derived. |
| D17 | Memory behavior of an accelerator is estimated by **counting over the real address stream** (for example, distinct DRAM rows per reorder window, giving a row-buffer hit rate), with paper-reported parameters as the fallback. **The approach must be general**: it must hold for other hardware and other software, not only DX100 and BFS. Show Scott once that counting is not simulation. |
| D18 | ArchEvolve mode may read a target's configuration from its pinned source (for example, tile count, DRAM channels, row size; basis `code_reading`). gem5 outputs are never read. |
| D19 | The LLM fills unknown parameters once per target-description version; the values are frozen into that description (sha256). An estimate that depends on a filled value lists it and reports how much the result moves if the value is halved or doubled. |
| D20 | The workload characterization is an SWDB format (refines D11) that reuses Peter's feature-report field names where they overlap, with a reader that imports his reports as one input source. |

Decided in grilling (Yan-Ru, 2026-10-06; round 2):

| # | Decision |
|---|---|
| D21 | The estimator is built from **mechanism models**, each modeling one hardware behavior (reorder-window row counting, cache fit, fetch queue, tile staging, offload setup, compute throughput, requests in flight). A **target description** lists a target's mechanisms and parameter values. Mechanisms are keyed to a design's operations and parameters, never to Eric's mechanism families alone. |
| D22 | Generality is shown on the mbit10 CPU, DX100 and MAPLE, and on BFS, BC and PageRank: adding MAPLE or PageRank needs only records and a description, no estimator code. gem5 agreement is measured on DX100 only. XSBench follows after Phase 2 as the bridge to the main database's kernels. |
| D23 | SWDB writes the first target descriptions from Eric's catalog, citing his claims, and offers the format to the HW team as the evaluator's hardware input. |
| D24 | The address stream is counted live in the instrumented native run, once per target description; no stream is stored. |
| D25 | An ArchEvolve-mode verdict has three states: `estimated_gain` only if the ratio stays above 1.05 after subtracting the error band; `within_error` if the band covers 1.05; otherwise `estimated_no_gain`. Until a band is validated the verdict is `within_error`, with the ratio shown. |

Decided in grilling (Yan-Ru, 2026-10-06; round 3):

| # | Decision |
|---|---|
| D26 | Extensa estimates are blind: each candidate is estimated before its timing exists, from inputs that never include timings, and the order is recorded. |
| D27 | In ArchEvolve mode, a CPU target's verdict comes from native measurement; the estimate is recorded beside it as a paired estimate. Targets without hardware get estimate-only verdicts (D25). This is the deck's tiered performance model. |
| D28 | The team estimator's CPU error check uses ArchEvolve-mode timings only, never Extensa's (ADR 0010). |
| D29 | Estimates may go beyond the graph sizes gem5 can run, labeled `beyond_paired_range` and never counted in agreement statistics. |
| D30 | The rule for switching Extensa to screening (flow B) is fixed now, before any data: after at least 20 DX100 candidates with both an estimate and a gem5 time, switch only if Kendall's tau is at least 0.6 (95% interval lower bound at least 0.3) and gem5's best candidate is inside the estimate's top 3 in every campaign. Otherwise stay in flow A and report. Yan-Ru makes the final call (ticket 16) but does not change the rule after seeing data. |

Decided in grilling (Yan-Ru, 2026-10-06; round 4):

| # | Decision |
|---|---|
| D31 | Ticket 30 of the typed-library map ("Send the first gem5 result and record the team claim") is closed as wontfix under ADR 0013. Its records stay as history, and Yan-Ru may use the result in research. |
| D32 | Version 1 estimates time only. Energy comes later as an extension of the mechanism models, with per-access energy values from published papers. |
| D33 | A region in an estimate is one of the function and loop regions SWDB already uses in profile packages and the site finder, with the same IDs. A loop the LLVM pass cannot map is listed, never dropped. |
| D34 | Scott sees the counting approach after the estimator works (ticket 24 after ticket 08). Accepted risk: if he calls counting simulation, the counting mechanism falls back to paper-reported parameters. |

## Solution

### Part B: the estimator (ArchEvolve mode)

The evaluator gains a speed stage that estimates instead of running. Per candidate artifact or
baseline, on one input and one hardware target:

1. **Workload characterization.** Per region (loop or function):
   - access patterns with address shape (`vocab/address_shapes.yaml`), stride, element bytes, and
     element counts as formulas of input properties: from implementation records, and from the static pass
     for new code;
   - operation counts by class from the static pass;
   - dynamic counts from one instrumented native run: trip counts, accesses per pattern, footprint;
   - accelerator calls (DX100 commands) with their sizes.
2. **Target description** (D21, D23): mechanism models plus parameter values, each with a basis:
   - mbit10: core count and clock from the machine record; effective bandwidth by access shape
     (stream, strided, indirect gather) from microbenchmarks on mbit10 (`measured`).
   - DX100: configuration from the hardware-target record (`code_reading`), mechanisms and numbers
     from Eric's catalog and the DX100 paper (`reported`), and the rest `unknown`.
   - MAPLE: from Eric's catalog (`maple-isca2022`) and its paper.
3. **Analytic bounds.** The target's mechanism models turn the characterization into bounds. Per
   region, estimated time is the largest of its compute bound, memory bound and accelerator bound,
   plus offload overhead (DX100 setup per call). The total is the sum
   over regions plus the serial remainder.
4. **Hybrid filling.** An estimation agent role (LLM, through the provider launcher, strict output
   schema) supplies values only for parameters that are `unknown`. It reads the characterization and
   the profile, never the candidate's timing. Each value it supplies carries basis `estimated` and a
   stated reason.
5. **Report.** Per region: the limiting bound (`vocab/bottleneck_classes.yaml`, extended with
   accelerator throughput and offload overhead), each bound's value
   and the parameters it used. In the scan, LLM agents that read such diagnostics or reason about
   bottlenecks needed fewer evaluations (Beacon, AgentDSE).
6. **Protocol.** An estimate protocol freezes the estimator version and the target description's
   sha256. A team protocol may name only an estimator frozen without gem5 data (D10).

#### Estimator workflow and tools (approved by Yan-Ru, 2026-10-06 17:45 ET)

```
candidate source ─► 1. clang -O3 -emit-llvm ─► 2. static LLVM pass ─► per-loop facts
                                              3. same pass inserts counters ─► one native run (counts only)
                                              ─► workload characterization
target ─► 4. target description ─► 5. LLM fills unknowns once (frozen)
characterization + description ─► 6. mechanism models: bounds per region ─► 7. report, ratio, verdict
```

| Need | Tool | Not chosen |
|---|---|---|
| Static facts | LLVM 22 IR pass (loop info, scalar evolution for address classification, debug info for region mapping) | Clang AST (misses inlining and vectorization); MLIR (our code enters through clang as C++) |
| Dynamic counts and live address-stream counting | Counters inserted by the same pass, with a small runtime | callgrind (slow; no live address counting); DynamoRIO or Pin (a second toolchain) |
| Compute bound | Operation counts × issue width | llvm-mca (models the pipeline cycle by cycle, too close to simulation under D3) |
| CPU memory parameters | Microbenchmarks on mbit10 (ticket 07) | Datasheet numbers |
| Unknown accelerator parameters | LLM, once per target-description version (D19) | — |

Known hard parts: OpenMP regions are outlined into separate IR functions (mapped back through debug
info); data-dependent trip counts need the counted run; row counting needs a DRAM address layout
(DX100's pinned configuration, D18; MAPLE's paper).

ArchEvolve mode for DX100 then runs: build → functional-target correctness (D8) → estimate →
verdict (D25) → evaluation record and handoff message carrying the estimate.

### Part C: Extensa mode

- **Flow A (paired estimates).** The campaign loop is unchanged (one candidate per workload class per
  iteration, at most 8 iterations). Each candidate also gets an estimate. Selection still uses gem5
  or native timing.
- **Agreement report** after one or two flow-A campaigns: rank agreement between estimate and gem5,
  and how often gem5's best candidate would have survived a top-k cut by estimate.
- **Flow B (screening), only if agreement is good** (Yan-Ru decides): one rewrite call yields N
  variants (knob values or sites, no extra provider call); all are certified and estimated; the
  top-k by estimate plus one random spot check are timed. Same gem5 hours, more candidates explored
  (the deck's "Search Efficiency" gate). Open: does certification cost depend on knob values? If
  it does, variants differ only in knobs, so one certification covers them all.

### Part A: two databases, one crosswalk

- **Crosswalk v0** from the slides, every row `unverified` (see lanl-db-notes.md §4).
- **One access layer**: tools read records through one interface (`swdb/store.py` today); the
  direct SQLite reads in `swdb/db.py` and `swdb/site_finder.py` move behind it, so a different
  database means a new adapter.
- **Blocked until LANL access:** an import (`swdb import-main`, read-only, keeps every
  main-database ID) and an export that writes the main database's own ingest inputs, with a
  round-trip test (import, export, their ingest, import again: same records).

## Testing and validation

- Static pass: its access-shape classification must match the hand-written access patterns of
  `gapbs-bfs-do` (13 patterns) and the BC implementation records; each mismatch is listed.
- Characterization: formulas evaluated on the class graphs must match the instrumented counts within
  a stated tolerance.
- Estimator: unit tests on synthetic regions with known bounds; CPU validation against existing
  native mbit10 evaluations (BFS, BC); DX100 sanity check against the DX100 paper's reported speedups.
- Extensa flow A: paired estimates appear in every campaign summary without changing selection.
- Guard: a team protocol that names a gem5 target or a gem5-calibrated estimator is refused.

## Out of scope

- Formal verification (a later conversation).
- Contacting LANL, Peter, Josh, Eric or Scott; drafts only, on request.
- Deleting gem5 code: ArchEvolve mode refuses it; Extensa keeps it.
- Energy in version 1 (D32); power, area and cost estimates later (the deck's Evaluator also covers them).
