# 03: First real pair: t75 BFS attribution report

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F9, F16, F18; LR-01, LR-02)
**Time estimate:** about half a day of agent work on mbit10; 30 min if it ends on a negative report

**What to build:** Estimate the t75 native BFS candidate (`extensa-native-bfs-20261005-a8.it1.kronecker.a0`, contract `bfs_tdstep_frontier_staging`) and its baseline with the BFS g16/g17 CPU target description, on the exact input that ticket 09 will time. Save both estimates, with their order recorded, before any new timing. Run `swdb attribute` on the pair and save the real report. If an estimate comes out unknown, close on a negative report naming the missing pieces.

## Acceptance

- [ ] Both estimates saved before timing, order recorded, same input as the planned timing.
- [ ] A real attribution report saved and validated, or a negative report.
- [ ] Record shares of rewritten, untouched and unattributed time in the map's current state.
- [ ] Follow the mbit10 rules: lane lease, `df -h` before large runs, raw output outside git.

## Prospective plan (recorded before any estimate or timing)

Recorded: 2026-10-11 19:19 ET on branch `fga/03-real-pair`, before any command below ran.
Code under test: integration branch `yanrujhou/fine-grained-attribution` at `d0c80a8a`, checked
out on mbit10 as a separate worktree `/data1/yanruj/ArchEvolve-fga03` (the shared clone stays on
`yanrujhou_main`). Raw output: `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/`
(`/data1` had 23 GB free; the worktree takes about 2 GB of it).

**Pair (F9/F16, F26).** Baseline = the scalar-only source snapshot the candidate was cut from,
`bfs-dx100-scalar-only-20260929-a1.source` (implementation `dx100-bfs-scalar`). Candidate =
`extensa-native-bfs-20261005-a8.it1.kronecker.a0` (contract `bfs_tdstep_frontier_staging`).

**Target description (F9).** `mbit10.cpu.lanl20261006.t1.services.v1`
(sha256 `9fec46b1…ca76b`), the BFS/BC g16/g17 CPU description. Unchanged; T1.

**Input (F18).** `dx100-functional-kron-g16-k16`, run arguments `-g 16 -k 16 -n 5`, threads 1,
ROI `gapbs.functional_trial_lambda.v1`. **Planned ticket-09 timing input: the same ID,
`dx100-functional-kron-g16-k16`, T1, on mbit10.** Not the a8 campaign's scale-22 workloads
(`bfs-20261004-kronecker22.*`): those are a different input, so they cannot be used (risks B5).

**Order (LR-02).**

1. Freeze a fresh estimate protocol on `d0c80a8a` (F27).
2. Characterize, then estimate, the **baseline** (snapshot).
3. Characterize, then estimate, the **candidate**.
4. `swdb attribute` on the pair; `swdb validate` the records.
5. No timing in this ticket. Ticket 09 times afterwards.

**Stop rule (LR-01).** If either estimate's `seconds` is null, stop after step 3, keep the
estimates as evidence, and close on a negative report naming each missing piece. The target
description and the estimator are not changed to make the number appear.

### Plan amendment a2 (2026-10-11 19:34 ET, before any count or estimate)

Attempt a1 was stopped at 19:32 ET during step 1 (`freeze-protocol` was still validating the
copied store). No protocol, count or estimate was written. Three premises of the plan above were
wrong, found by reading the code and decisions F26 and risks B2/B5:

- **Baseline (F26):** a source-baseline *candidate* of the snapshot, not the implementation.
  `typed-library-bfs-scalar-profile-20261003-a1.baseline` has the snapshot's exact tree
  (`2bf9b1b8…c6af`), so it is reused.
- **Adapter (B2):** native candidates count only through `registered-cpu` with a prospective
  native evaluation request (evaluator v3, LLVM 22 `clang++`), one fresh-process slot.
- **Input (B5, F18):** the t75 re-evaluation workload `bfs-20261004-uniform22.2f83a134a6bef789`
  (scale 22, uniform). **Planned ticket-09 timing input: this same workload ID, T1, through the two
  prospective requests below.** The g16 input above is withdrawn.

Prospective requests (copied into this ticket's `evidence/` folder):
`fga03.t75-baseline.uniform22.t1.request.a1` and `fga03.t75-candidate.uniform22.t1.request.a1`
(sources `[0, 1234, 7777]`, 20 repetitions, counted slot = source position 0, repetition 0).

New order: (1) count baseline, (2) count candidate, (3) freeze the fresh protocol on `d0c80a8a`
(one per side only if the counted run arguments differ), (4) estimate baseline, (5) estimate
candidate, (6) `swdb attribute` only if both totals are known. Stop rule unchanged.
