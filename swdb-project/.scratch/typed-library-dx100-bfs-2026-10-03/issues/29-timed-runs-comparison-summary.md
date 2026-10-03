# 29 — Timed gem5 runs, comparison and team summary

Created: 2026-10-03
**Type:** task
**Status:** claimed
**Blocked by:** 28
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The team gets its first gem5 result for Peter's rewrite, measured against a fresh scalar baseline. Runs only if ticket 28's Answer records L3 observed on target.

## Acceptance

- [ ] The pre-dispatch checks are recorded.
- [ ] Baseline and candidate-artifact timed runs finish on Kronecker 18 and uniform 18; all four pass the verifier, and the two candidate-artifact runs also pass the frontier check and the read-only execution case.
- [ ] A comparison is recorded whatever the speedup; gem5 results are reported as point ratios; the authors' T17 result is cited as context only.
- [ ] The contract and lowering entries' derived status becomes evaluated on target, or refuted.
- [ ] A one-page summary with basis labels is drafted for Yan-Ru to send.

## Comments

Implementation support added 2026-10-03 ET: `tools/typed_library_gem5_driver.py --stage timed` requires the completed prepare/companion receipts for the same `--id`, mandatory `--approval-reference`, an actually verified mbit10 socket lane and fresh stage resource admission. It reopens both companion identities and acceptance before dispatch, runs the fresh full-source scalar and certified candidate on each of the two frozen workloads, forms exact one-replay aggregates, records both comparisons whatever the qualified point ratio, and writes a one-page `first-result.md` operator draft with basis labels and a status table. Candidate samples require verifier/frontier and read-only/full/tail acceptance. Derived library states are included, with no self-promotion.

The command refuses inconclusive/refuted companion outcomes before any timed dispatch. Default gem5 memory remains 48 GiB and is never replaced by global free memory or a smaller prepare budget. The local driver tests pass; they are request/admission checks, not timing or target evidence. No timed gem5 run or summary of actual results has been produced yet; this ticket's actual acceptance remains pending.

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. Timed drivers/comparison support are ready. Real executions require ticket 28 completed observed L3 companion, current promotion/source pins and sufficient lane memory. No timing or gain result exists; ticket 31 remains conditional and untriggered. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

- Claimed 2026-10-03 11:10 ET: ticket28 is complete with actual observed L3 and published companion records. Root reviewed the bounded-completion classification fix on both axes; 200 affected tests pass. Current local replay yields 19 shared/evaluated-on-target entries and two unused ALU entries shared/certified. Publish/synchronize that source correction, revalidate actual remote states, exact binaries/protocol/companion acceptance and fresh socket capacity, then launch the four bounded timed executions. No actual timed result exists yet.

- Actual start2026-10-03 11:18 ET: timed driver runs on node0 at reviewed source982d19b with fresh38.684GiB conservative capacity against36GiB budget. First uniform18 scalar baseline public request started11:19:10 ET; root independent11:19:46 ET readback confirms running PIDs and lease. The remaining samples, comparisons and actual ratios are pending. [Start receipt](../evaluation/timed-start-1118-summary.json).

- 2026-10-03 12:13 ET: a1 first uniform18 baseline is incomplete (`missing_observation`, correctness unverified), because post-ROI continuation hit10**10 ticks without protected verdict/parent result/exit witness. Peak sampled RSS30.60GiB stays within36GiB. No candidate run, aggregate, ratio or assessment exists. Published failure8b68b2f and ten failed-checkpoint files remain preserved. Restore the established T17v2 post-seal ceiling10**14 uniformly; both review axes pass and168 affected cases pass, with4red regressions retained. All other request fields and wall/memory/storage/ROI/checker/guest constraints stay fixed. Fresh a2 preparation/protocol/actual binary pins, then companions and four timed samples are authorized after source publication/sync and fresh per-stage admission; actual acceptance remains pending. [Decision](../evaluation/post-roi-budget-decision.md).

- 2026-10-03 12:22 ET: actual fresh a2 preparation started12:20:12 ET at4c9bb01, node0generation442. Root independent12:21 ET confirms currentbaselineprimarycompile and healthyownedPIDs, fresh38.60GiBcapacity with4GiBprepare/36GiBfuture simulation separate, actual .lease node1/legacyfree. Newprotocol84229924369fc6b0 is actual; finalbuildpins, companions and fourqualifiedtimedsamples remainpending. Sourcefrozen; noGitpublicationwhileactive. [Start](../evaluation/a2-start-1220-summary.json).

- 2026-10-03 12:26 ET: fresh a2 all3builds complete12:22:57 ET; actual companions started12:24:56 ET at source4c9bb01. Independentrootreadback confirms live firstpubliccompanion-timed request, driver1590398, node0generation443 andotheractualleasesfree; freshcapacity38.58GiB admits36GiBbudget. Exact companionacceptance andtimedsamples/ratios remainpending. [Readback](../evaluation/a2-companion-start-1224-summary.json).

- 2026-10-03 13:02 ET: fresh a2 companion requalification passed after both actual executions completed at12:37 ET. The worker verified all nine retained artifacts per witness and exact public acceptance; L3 observed14,546 CAS failures with zero violations. The timed driver started12:39:05 ET under fresh38.67GiB capacity/36GiB budget, and the first uniform18 baseline at12:39:44 ET. Root's13:00 ET readback confirms simulator1592914 (`Rs`, about27.53GiB RSS) and driver1592364 alive, node0 generation444 held and other actual leases free. Source4c9 remains frozen. No completed timed verdict or ratio exists; all four samples, aggregates and comparisons remain required. [Readback](../evaluation/heartbeat-1258-summary.json).

- 2026-10-03 13:32 ET: actual uniform18 baseline complete/passed, pinfd42274d..., and exact one-replay aggregate complete, pin9b821fd4.... Root13:30 ET reads the completed zero-status exit witness after84billion post-ROI ticks, with no pending calls/events after exit. Full independent raw audit remains deferred until all measurements stop. Uniform18 candidate began13:21:45 ET and is running with gem5 PID1597474/RSS28.89GiB; source4c9 frozen/node0g444 held/other actual leases free. Kronecker18 pair and both comparisons remain pending; no ratio yet. [Readback](../evaluation/heartbeat-1328-summary.json).

- 2026-10-03 14:02 ET: candidate verification continues; root14:00 ET confirms active gem5 PID1597474, CPU00:34:49, RSS32.63GiB within36GiB and zero current pressure averages. Source4c9/node0generation444 unchanged; other actual leases free. The passed baseline/aggregate pins remain unchanged. Kronecker18 pair and comparisons are pending; no ratio or stall. [Readback](../evaluation/heartbeat-1358-summary.json).


- 2026-10-03 15:05 ET: both actual a2 uniform18 samples passed; baseline aggregate passed. Candidate aggregation timed out at300s and the driver failed14:30:25 ET; no candidate aggregate/comparison/ratio or Kronecker sample exists. All actual leases released and owned processes stopped before metadata5827f3f publication; root verifies all20records and exact failure manifest. A separate3600s public aggregation/comparison bound covers the observed1082s candidate trace validation while all physical/frozen constraints stay fixed. Reviewed exact r1 recovery reuses completed uniform evidence, publicly requalifies it before two missing Kronecker samples, and refuses extra history or hash/type/request/pin drift. Final35focused and138broader passes cover142distinct cases; both review axes pass. Fresh source sync and per-node admission precede dispatch; actual ticket acceptance remains pending. [Decision](../evaluation/postprocess-recovery-decision.md); [preserved failure](../evaluation/a2-aggregation-failure-summary.json).
