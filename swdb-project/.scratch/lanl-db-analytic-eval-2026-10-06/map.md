# Map: Analytic speed estimates and main-database compatibility

Created: 2026-10-06 ET
Updated: 2026-10-08 12:16 ET (tickets 21–23 wontfix: no LANL contact); 2026-10-08 12:00 ET (ticket 15 resolved: Scott approved counting); 2026-10-08 11:20 ET (14 of 15 assigned tickets resolved; 17 resumed)
**Type:** ticket map
**Status:** claimed (unfinished implementation/evaluation)
**Work state:** active; [resume guide](resume.md)
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
| 11 | [CPU error check and paired estimates in ArchEvolve mode](issues/11-cpu-error-check-and-paired-estimates.md) | resolved | 05, 06, 07 | 4–6 h |
| 12 | [ArchEvolve-mode DX100 evaluation without gem5](issues/12-archevolve-dx100-evaluation.md) | resolved | 06, 09 | 1 day |
| 13 | [DX100 sanity check against the paper](issues/13-dx100-sanity-check.md) | resolved | 10 | 2 h |

## D. Generality, Scott, Extensa

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 14 | [Generality: MAPLE and PageRank](issues/14-generality-maple-pagerank.md) | resolved | 05, 09, 10 | 1 day |
| 15 | [Show Scott the counting approach](issues/15-show-scott-counting.md) | resolved | 09 | about 15 min |
| 16 | [Extensa flow A: blind paired estimates](issues/16-extensa-blind-paired-estimates.md) | resolved | 06, 09 | 4–6 h |
| 17 | [Agreement report](issues/17-agreement-report.md) | claimed | 16 | 3–4 h plus campaign lane time (about 13 h of gem5 for 20 pairs) |
| 18 | [Decide on flow B](issues/18-decide-flow-b.md) | ready-for-human | 17 | about 15 min |

## E. Later or blocked

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 19 | [Flow B screening](issues/19-flow-b-screening.md) | needs-triage | 18 | 1 day |
| 20 | [XSBench as the bridge kernel](issues/20-xsbench-bridge-kernel.md) | needs-triage | 14 | 1–2 days |
| 21 | [Ask LANL for access](issues/21-ask-lanl-for-access.md) | wontfix | — | about 10 min, when Yan-Ru decides |
| 22 | [`swdb import-main`: read the main database](issues/22-import-main.md) | wontfix | 02, 03, 21 | 1 day |
| 23 | [Export and round-trip test](issues/23-export-and-round-trip.md) | wontfix | 22 | 1 day |

## Context pointers

- 2026-10-08 14:41 ET: [Normal terminal request readiness](evidence/17-normal-terminal-request-readiness-20261008-a5/README.md) retains the reviewed owned0664 terminal readerR1/bdf2 and local release request finalizerR3/47ec, plus exact14:29 native wrapper metadata10510B/00c269/0777. Generic private file pins would refuse writable native modes; preserve all modes and use selected reader/producer original byte checks. Fresh native/wrapper checks before32 and before/after b08 remain mandatory. Latest14:39 ET monitor observes4 iterations/8 candidate rows and public plateau summary, but no original helper stop/final exits and held511;0/4 normal completions remain admitted. Select terminal action draftR3/e647 and local finalizerR3 only after actualrelease_ready AND normal_exit_set_only and original matching stop/exits/normal state facts. All drafts/authors/terminal controls remain NOTRUN; no finalized request exists. Agents complete/responsive. Next required table/health check14:45 ET.

- 2026-10-08 14:15 ET: [P1 iteration progress and queued custody](evidence/17-p1-iteration-progress-and-queued-custody-20261008-a5/README.md) preserve the14:15 ET heartbeat. Fresh14:14 ET originals show p1 active node0/g511,3 completed iterations/6 completed candidate rows, no stopped receipt or reported infrastructure error. Owned helper/provider tree is live; R2 confirms held matching kernel lock/FD9 and release_ready=False. All agents completed responsive scoped work and source reviews; no stranded worker. P3/P4 BEFORE/dispatch and p2–p4 dispatch-state32 drafts are reviewed future inputs only; actual hashes/seals/generations/UTC/admission remain required. Raw output stays remote; no duplicate science/native mutation.0/4 normal trajectories; ticket17 stays claimed. Next scheduled table/agent check14:45 ET; report/audit/final Standards+Spec review/fixes still pending.

- 2026-10-08 14:03 ET: [First p1 iteration and release readiness](evidence/17-p1-first-iteration-and-release-readiness-20261008-a5/README.md) records1 completed iteration/active held511, 0/4 normal trajectories. Future release/AFTER drafts reviewed; actual staged observer confirms not-release-ready. Final campaign/report/review gates remain pending.

- 2026-10-08 13:13 ET: [Active p1 startup and queued p2 preparation](evidence/17-active-p1-startup-and-p2-preparation-20261008-a5/README.md) confirm public setup/advancing CPU, 0/4 normal trajectories. Source-only p2 commands reviewed; live admission and all final report/review gates remain pending.

- 2026-10-08 11:42 ET: [Fresh a5 preparation](evidence/17-fresh-a5-preparation-controls-20261008-a1/README.md) entered original guard; tracked53binding passed. Freeze/M2 and four campaigns pending. Test fixture closure repair active; canonical704validation and3math checks passed.

- 2026-10-08 11:29 ET: [Failed PREPARE and tracked-source fix](evidence/17-failed-prepare-and-tracked-manifest-fix-20261008-a1/README.md) preserves actual failure. Hook now admits only an exact tracked original53-file manifest; scientific source/budgets remain frozen. Fresh a5 preparation pending.

- 2026-10-08 11:20 ET: Yan-Ru resumed assigned work and authorized ongoing implementation/evaluation/sync. [Original retirement assessment](evidence/17-resumed-retirement-assessment-20261008-a1/README.md) confirms sixteen successful library-preserving retirements. Fresh host storage permits serial preparation; four campaigns/report remain pending. The 30-minute heartbeat now targets the resumed chat and is ACTIVE.

- 2026-10-08 11:11 ET: approved [local worktree cleanup](local-worktree-cleanup-20261008.md) archived and removed 17 completed checkouts and their merged local branches. Main, integration and ticket 17 remain; seven ignored originals are preserved. Writing-preference rule committed as `cb6f75ae`. Evaluation and heartbeat remain PAUSED; original retirement collection is still pending.
- 2026-10-08 10:53 ET: approved [remote branch cleanup](branch-cleanup-result-20261008.md) removed 37 merged refs, retained four mbit10 worktree-linked candidates, and preserved local/recovery/resume state. Branch-only host observation reports the retirement wrapper complete/exit 0; original receipt collection and assessment remain pending. Ticket 17 and all new evaluations stay paused.
- 2026-10-08 10:29 ET: Yan-Ru requested pause, ticket/status sync and commit.
  [Resume](resume.md), [latest exact custody](evidence/17-user-pause-custody-20261008-a1/README.md),
  [library-preserving controls](evidence/17-library-preserving-sparse-retirement-custody-20261008-a1/README.md)
  and [read-budget correction](evidence/17-sparse-read-budget-custody-correction-20261008-a1/README.md)
  preserve completed work. DEFAULT a3 original passed; RETIRE a4/plan a5 launched,
  result unassessed. Quiet until 10:48:28 ET; no closeout SSH. Ticket 17 remains
  incomplete, scientific campaigns 0/4, final review pending, heartbeat PAUSED.
  mbit10 checkout sync awaits original collection and explicit frozen-primary handling.
  Remote branch deletions await the separate user discussion.
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

- 2026-10-06 ET — Ticket 13 resolved: `issues/13-dx100-sanity-check.md#answer`; cited weak report `evidence/13-dx100-paper-sanity-20261006-a1/report.md`, sealed closeout `evidence/13-paper-sanity-closeout-20261006.json`. Actual BFS ratio unknown; BC/PR estimates absent pending 14; 9 public tests passed, generic source unchanged.

- 2026-10-06 ET — Ticket 14 claimed; actual Jacobi source count prerequisite tested, MAPLE FPGA data admitted with unknown services. Parent count commands and all-nine admission plan: `evidence/14-nine-pair-runbook-20261006.md`; prepared MAPLE requests remain unfrozen. Final reports await actual counts and generic 11/17 bundle.

- 2026-10-07 09:56 ET: [ticket 11](issues/11-cpu-error-check-and-paired-estimates.md#answer) resolved.
  Exact T1 native development/held-out validation and fresh verdict-reading reports
  retain BFS's broad validated envelope and BC's observed failed envelope with its
  original width. g17 forecast/native ratios are 53.9×/39.3×; both public
  `within_error` tokens are qualified by the separate validation state. Protected
  CPU evaluation carries a bound semantic estimate while timing still decides;
  timer/ROI transfer and historical mismatches remain unknown. No retuning or
  general accuracy claim. [Actual report admission and cleanup custody](evidence/11-report-admission-closeout-20261007-a4/README.md),
  [report receipt](evidence/11-cpu-band-report-mbit10-20261006-a3.json),
  [per-region explanation](evidence/11-holdout-admission-20261007-a3/README.md).
  Source C/F6 and all previous records are unchanged; actual report public
  validation passed 684 records, delivered integration retains 686.

- 2026-10-07 ET: [ticket 14](issues/14-generality-maple-pagerank.md#answer) resolved.
  The [actual per-region report](evidence/14-generality-final-final-20261007-a1-report.md)
  and [original reader custody](evidence/14-original-reader-actual-custody-20261008-a1/README.md)
  retain all nine pairs/five trials each, the fresh DX100 BFS reference, identical
  185-module F6 estimator/mechanism code, and exact target-specific counting policies.
  The data-only pure export adds nine protocols/nine estimates; public validation
  passed 704 records with all 686 prior canonical bytes unchanged. Only CPU BFS/BC
  have predicted whole-call totals; seven totals and all ratios/error bands remain
  null. MAPLE is estimate-only; PR inherits no BF/BC service or error-band admission.
  Ticket 11's broad/failed CPU envelopes remain separately qualified. No measured
  speedup or new accuracy claim. Final code-review and ticket 17 remain pending.

- 2026-10-08 ET: [ticket 15](issues/15-show-scott-counting.md#answer) resolved. Scott
  approved the strategies (reported by Yan-Ru). Address-stream counting stays; the
  D34 paper-parameter fallback is not triggered. Recorded in the [spec](spec.md) D34 row.
- 2026-10-08 ET: tickets [21](issues/21-ask-lanl-for-access.md#answer),
  [22](issues/22-import-main.md#answer) and [23](issues/23-export-and-round-trip.md#answer)
  closed as wontfix. We will not contact LANL and do not have their database; we wait
  passively for their response.
