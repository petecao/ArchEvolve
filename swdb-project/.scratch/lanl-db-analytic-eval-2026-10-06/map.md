# Map: Analytic speed estimates and main-database compatibility

Created: 2026-10-06 ET
Updated: 2026-10-06 ET (ticket 03 resolved with source and validation evidence); 2026-10-06 16:11 ET (tickets regenerated as 22 vertical slices, approved by Yan-Ru; ticket 01 kept); 2026-10-06 16:01 ET (ticket 01 resolved; design committed as `6c691e6`)
**Type:** ticket map
**Status:** ready-for-agent (implementation starts on Yan-Ru's go-ahead)
**Spec:** [spec.md](spec.md)

Each ticket is a vertical slice: it delivers something runnable and checkable on its own, from format to command to tests. Statuses: ready-for-agent; ready-for-human (Yan-Ru acts); needs-triage (Yan-Ru decides first); needs-info (waits on LANL access). Ticket 07 runs on mbit10 under the standing approval of 2026-10-05.

## A. Prefactor and groundwork

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 01 | [Yan-Ru reviews the design and approves the design-session commit](issues/01-review-and-commit-design.md) | resolved | — | about 20 min of reading |
| 02 | [Prefactor: one access layer for record reads](issues/02-one-access-layer.md) | resolved | 01 | 3–4 h |
| 03 | [Crosswalk v0 from the slides](issues/03-crosswalk-v0.md) | resolved | 01 | 1 h |

## B. The CPU path (first runnable version)

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 04 | [First runnable version: estimate a streaming loop on the mbit10 CPU](issues/04-first-runnable-estimate.md) | resolved | 01 | 1.5–2 days |
| 05 | [Indirect accesses and the BFS baseline on the CPU](issues/05-indirect-and-bfs-baseline.md) | resolved | 04 | 1.5–2 days |
| 06 | [Estimate protocols and the gem5 refusal](issues/06-estimate-protocols-and-gem5-refusal.md) | resolved | 04 | 3–4 h |
| 07 | [Measured mbit10 parameters](issues/07-measured-mbit10-parameters.md) | resolved | 04 | 2–3 h plus about 1 h of lane time (mbit10) |
| 08 | [Peter's feature reports as an input](issues/08-peter-feature-reports-input.md) | resolved | 05 | 3–4 h |

## C. DX100 and ArchEvolve mode

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 09 | [DX100 estimate](issues/09-dx100-estimate.md) | resolved | 05 | 1.5–2 days |
| 10 | [The estimation role fills unknowns](issues/10-estimation-role.md) | resolved | 09 | 4–6 h |
| 11 | [CPU error check and paired estimates in ArchEvolve mode](issues/11-cpu-error-check-and-paired-estimates.md) | ready-for-agent | 05, 06, 07 | 4–6 h |
| 12 | [ArchEvolve-mode DX100 evaluation without gem5](issues/12-archevolve-dx100-evaluation.md) | resolved | 06, 09 | 1 day |
| 13 | [DX100 sanity check against the paper](issues/13-dx100-sanity-check.md) | claimed | 10 | 2 h |

## D. Generality, Scott, Extensa

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 14 | [Generality: MAPLE and PageRank](issues/14-generality-maple-pagerank.md) | ready-for-agent | 05, 09, 10 | 1 day |
| 15 | [Show Scott the counting approach](issues/15-show-scott-counting.md) | ready-for-human | 09 | about 15 min |
| 16 | [Extensa flow A: blind paired estimates](issues/16-extensa-blind-paired-estimates.md) | resolved | 06, 09 | 4–6 h |
| 17 | [Agreement report](issues/17-agreement-report.md) | ready-for-agent | 16 | 3–4 h plus campaign lane time (about 13 h of gem5 for 20 pairs) |
| 18 | [Decide on flow B](issues/18-decide-flow-b.md) | ready-for-human | 17 | about 15 min |

## E. Later or blocked

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 19 | [Flow B screening](issues/19-flow-b-screening.md) | needs-triage | 18 | 1 day |
| 20 | [XSBench as the bridge kernel](issues/20-xsbench-bridge-kernel.md) | needs-triage | 14 | 1–2 days |
| 21 | [Ask LANL for access](issues/21-ask-lanl-for-access.md) | ready-for-human | — | about 10 min, when Yan-Ru decides |
| 22 | [`swdb import-main`: read the main database](issues/22-import-main.md) | needs-info | 02, 03, 21 | 1 day |
| 23 | [Export and round-trip test](issues/23-export-and-round-trip.md) | needs-info | 22 | 1 day |

## Context pointers

- 2026-10-06: design inputs are [lanl-db-notes.md](lanl-db-notes.md) and [three-way-scan-analytic-evaluators.md](three-way-scan-analytic-evaluators.md); decisions D1–D34 in the spec.
- 2026-10-06 16:01 ET: ticket 01 resolved; Yan-Ru confirmed D8–D34 and the estimator workflow and approved the design-session commit. [01](issues/01-review-and-commit-design.md), [spec](spec.md)
- 2026-10-06 16:11 ET: the 24 layer-by-layer tickets 02–25 were replaced by 22 vertical slices (02–23), approved by Yan-Ru; the first runnable version is [04](issues/04-first-runnable-estimate.md).

- 2026-10-06 ET: ticket [03](issues/03-crosswalk-v0.md) resolved: [crosswalk v0](../../docs/compatibility/lanl-crosswalk-v0.yaml), [format](../../docs/compatibility/README.md), and [source/test evidence](crosswalk-v0-verification.md). Every mapping remains unverified until LANL grants schema access.

- 2026-10-06 ET: [ticket 02](issues/02-one-access-layer.md#answer) resolved in `bb11cb1`:
  [`swdb.access`](../../swdb/access.py) owns record/index I/O; existing query APIs remain.
  [Interface contract](../../docs/reference/database.md#record-and-query-access-interface),
  [query regressions](../../tests/test_query_index.py), and the ticket Answer record the
  15 identical old/new outputs and the regression results: broad run 170 passed,
  one existing data-dependent skip, and one live-source fingerprint artifact; the
  exact affected case passed in a fresh process (1 passed).
- 2026-10-06 ET: ticket [04](issues/04-first-runnable-estimate.md) resolved: LLVM source counting and streaming estimates, [portable format and commands](../../docs/reference/format-v0.4-analytic.md); implementation `191fd8d`, 101-pass/1-skip regression batch plus the static-distribution test. Application/protocol binding remains explicit work for 05–06; measured mbit10 parameters for 07.

- 2026-10-06 ET: [ticket 06](issues/06-estimate-protocols-and-gem5-refusal.md#answer) resolved:
  portable implementation/target/dependency/input/source freezes, verified binding
  at estimate execution, and recursive ADR 0013 refusals. Source `c3633cf`, merged
  integration tip `9ccf710`; final 41-pass focused batch plus the public claim refusal,
  553 historical records valid, and Extensa/LLVM broad regression evidence in the ticket.


- 2026-10-06 ET: [ticket 05](issues/05-indirect-and-bfs-baseline.md#answer) resolved.
  Registered g16 BFS/BC counts and frozen estimates retain five trials each, 27/31
  observed per-region reports, all 129/165 unmapped loops, and explicit reasons for
  **0/13 and 0/20 direct handwritten matches**. Whole-call seconds/ratios remain
  unknown for unsupported runtime/memory/worker-rate costs; no CPU agreement is
  claimed. Sources `cda8f2d` (counts) / `b5acc909` (estimates), actual metadata
  `68df1dd`, final 584-record validation and 7-test combined compatibility evidence
  are linked from the Answer and [runbook](evidence/05-registered-counting-runbook.md).

- 2026-10-06 ET: [ticket 07](issues/07-measured-mbit10-parameters.md#answer) resolved:
  real socket-lane a1/a2 measurements, independently rebound v2 compute numerators,
  fresh per-T descriptions with typed calibration dependencies, and the actual
  [T1 frozen-hash fixture receipt](evidence/bound-calibration-fixture-mbit10-20261006-a1.json).
  All 584 records validate; old 10 measured target bytes/native trials are unchanged.
  [CPU calibration contract](../../docs/reference/cpu-calibration.md) records caps,
  units, plateau premises and cache/service limits. No CPU error-band claim.

- 2026-10-06 ET: [ticket 08](issues/08-peter-feature-reports-input.md#answer) resolved:
  both supplied BFS v1.2 filenames import with content schema 1.1 and basis
  `reported`; the [field table and command](../../docs/reference/feature-report-inputs.md)
  preserve native vocabulary and unresolved source/array/unit scope. Actual
  sparse/dense imports retain all five native BFS a2 trials/receipts, list 17/13
  conflicts, and validate with 579 records. The [compact receipt](evidence/08-reported-input-imports-20261006.json)
  separates original import and final-source hashes; final 15 public tests and
  canonical 584-record validation passed. No native unknown cost is promoted.


- 2026-10-06 21:15 ET: [ticket 09](issues/09-dx100-estimate.md#answer) resolved:
  generic live command/object/window counting and four DX mechanism compositions,
  source/config-only functional target, and the [actual five-trial T4 candidate report](evidence/09-functional-application-report-mbit10-20261006-a2.json).
  The [closeout proof](evidence/09-functional-estimate-closeout-20261006-a2.json) retains
  26 observed regions, all 284 static IDs/153 unmapped loops, exact setup and source
  hashes, nine ranked-by-dependency unknown references and honest null numerical
  impacts. Missing host memory/overlap/runtime costs keep total/ratio unknown;
  no hardware timing or gem5 agreement is claimed. Frozen bundle `3ad3ce75…`,
  final 22-case public gate, native static SHA support and 617-record validation
  passed; all 615 original canonical YAML bytes are preserved. Stable seams unblock
  10/12/16, with 16 prioritized for fresh blind campaign preparation.

- 2026-10-06 22:35 ET: [ticket 12](issues/12-archevolve-dx100-evaluation.md#answer) resolved. Retained strict functional certification, immutable estimated evaluation and handoff 1.1 passed exact-artifact mbit10 no-child acceptance; unknown totals/ratio/band remain null with `within_error`. Three final coexistence cases passed; 628 canonical records valid and all 888 prior protected blobs preserved. [Final proof](evidence/12-final-public-coexistence-proof-20261006.json).

- 2026-10-06 ET: [ticket 10](issues/10-estimation-role.md#answer) resolved. Closed
  three-file numerical fill uses existing guarded provider pins/audit and freezes
  one output per base version. Actual a2 completed once; separate postfill acceptance
  passed with seven estimated/two unknown values and honest null whole-call and
  sensitivity results. [Actual receipt](evidence/10-estimation-role-mbit10-20261006-a2-postfill-a1.json),
  [failure custody](evidence/10-estimation-role-postfill-custody-mbit10-20261006-a2.json),
  [public reference](../../docs/reference/estimation-role.md) and
  [integrated proof](evidence/10-integrated-closeout-proof-20261006.json): eight affected
  public paths passed, 631 records valid, 628 prior YAML/876 protected blobs unchanged.
  Historical bundle `b238c61b…` remains immutable; future execution must freeze the
  integrated bundle. No timing/accuracy claim; 13/14 can proceed after integration.
