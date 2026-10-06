# Map: Analytic speed estimates and main-database compatibility

Created: 2026-10-06 15:45 ET
Updated: 2026-10-06 17:45 ET (ticket 01 resolved; design committed); 2026-10-06 17:25 ET (grilling rounds 1–4: tickets 23–25 added; 01, 03–09, 11, 15, 16, 24 revised)
**Type:** ticket map
**Status:** ready-for-agent (implementation starts on Yan-Ru's go-ahead)
**Spec:** [spec.md](spec.md)

Statuses: ready-for-agent; ready-for-human (Yan-Ru acts); needs-triage (Yan-Ru decides first); needs-info (waits on LANL access). Every implementation ticket is blocked by 01. Ticket 07 runs on mbit10 under the standing approval of 2026-10-05.

## Phase 0: record the design

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 01 | [Yan-Ru reviews the design and approves the design-session commit](issues/01-review-and-commit-design.md) | resolved | — | about 20 min of reading |

## Phase 1: estimator foundations (Mac, except 07)

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 02 | [Prefactor: evidence basis `estimated` and the estimate record shape](issues/02-estimated-basis-and-estimate-records.md) | ready-for-agent | 01 | 1–2 h |
| 03 | [Workload characterization format v1 and `swdb characterize` from existing records](issues/03-workload-characterization-format.md) | ready-for-agent | 02 | 3–4 h |
| 04 | [LLVM static pass: operation counts and access-shape classification per loop](issues/04-llvm-static-pass.md) | ready-for-agent | 03 | 1–2 days |
| 05 | [Dynamic counts and live address-stream counting from an instrumented native run](issues/05-dynamic-counts.md) | ready-for-agent | 04 | 1 day |
| 06 | [Target descriptions for mbit10, DX100 and MAPLE](issues/06-target-descriptions.md) | ready-for-agent | 02 | 3–4 h |
| 07 | [mbit10 microbenchmarks: effective bandwidth by access shape](issues/07-mbit10-bandwidth-microbenchmarks.md) | ready-for-agent | 06 | 2–3 h plus about 1 h of lane time |
| 08 | [Estimator v1: mechanism models, per-region report and the estimate protocol](issues/08-estimator-v1.md) | ready-for-agent | 03, 06 | 1–2 days |
| 09 | [Estimation agent role: an LLM fills unknown parameters only](issues/09-estimation-agent-role.md) | ready-for-agent | 08 | 4–6 h |

## Phase 2: ArchEvolve-mode wiring and validation

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 10 | [ArchEvolve-mode guard: no gem5 runs, no gem5 numbers](issues/10-archevolve-mode-gem5-guard.md) | ready-for-agent | 02 | 2–3 h |
| 11 | [ArchEvolve-mode DX100 evaluation: functional-target correctness plus estimate](issues/11-archevolve-mode-dx100-estimate.md) | ready-for-agent | 08, 10 | 1 day |
| 12 | [CPU validation: estimates against existing native mbit10 timings](issues/12-cpu-validation.md) | ready-for-agent | 05, 07, 08 | 4–6 h |
| 13 | [DX100 sanity check against the DX100 paper's reported numbers](issues/13-dx100-reported-sanity-check.md) | ready-for-agent | 11 | 2 h |
| 23 | [Generality check: MAPLE and PageRank with no estimator code change](issues/23-generality-check-maple-pagerank.md) | ready-for-agent | 06, 08, 05 | 1 day |
| 24 | [Show Scott the address-stream counting approach](issues/24-show-scott-counting.md) | ready-for-human | 08 | about 15 min |
| 25 | [XSBench as the bridge kernel to the main database](issues/25-xsbench-bridge-kernel.md) | needs-triage | 23 | 1–2 days |

## Phase 3: Extensa mode

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 14 | [Extensa flow A: a paired estimate for every candidate](issues/14-extensa-paired-estimates.md) | ready-for-agent | 08 | 4–6 h |
| 15 | [Agreement report from flow-A campaigns](issues/15-agreement-report.md) | ready-for-agent | 14 | 3–4 h plus campaign lane time |
| 16 | [Yan-Ru decides whether Extensa switches to screening (flow B)](issues/16-decide-flow-b.md) | needs-triage | 15 | about 15 min |
| 17 | [Extensa flow B: screening by estimate](issues/17-extensa-screening.md) | needs-triage | 16 | 1 day |

## Phase 4: main-database compatibility

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 18 | [Crosswalk v0 from the slides, every row unverified](issues/18-crosswalk-v0.md) | ready-for-agent | 01 | 1 h |
| 19 | [Prefactor: one access layer for record reads](issues/19-one-access-layer.md) | ready-for-agent | 01 | 3–4 h |
| 20 | [Ask LANL for read access to the kernels repo](issues/20-ask-lanl-for-access.md) | ready-for-human | 01 | about 10 min, when Yan-Ru decides |
| 21 | [`swdb import-main`: read the main database, keep its IDs](issues/21-import-main.md) | needs-info | 20, 18, 19 | 1 day |
| 22 | [Export through the main database's ingest inputs, with a round-trip test](issues/22-export-and-round-trip.md) | needs-info | 21 | 1 day |

## Context pointers

- 2026-10-06: design inputs are [lanl-db-notes.md](lanl-db-notes.md) and [three-way-scan-analytic-evaluators.md](three-way-scan-analytic-evaluators.md); decisions D1–D15 in the spec.
- 2026-10-06 17:45 ET: ticket 01 resolved; Yan-Ru confirmed D8–D34 and the estimator workflow and approved the design-session commit. [01](issues/01-review-and-commit-design.md), [spec](spec.md)
