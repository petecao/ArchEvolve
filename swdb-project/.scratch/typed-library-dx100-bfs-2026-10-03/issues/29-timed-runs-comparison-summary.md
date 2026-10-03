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
