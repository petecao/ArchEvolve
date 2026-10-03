# 29 — Timed gem5 runs, comparison and team summary

Created: 2026-10-03
**Type:** task
**Status:** needs-info
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
