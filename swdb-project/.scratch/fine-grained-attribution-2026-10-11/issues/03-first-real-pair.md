# 03: First real pair: t75 BFS attribution report

Created: 2026-10-11 15:14 ET. Updated: 2026-10-12 00:40 ET (final review fixes: every missing piece,
boxes ticked, retention and HEAD validation recorded); 2026-10-11 23:17 ET (resolved, negative);
2026-10-11 19:34 ET (plan amendment a2); 2026-10-11 19:19 ET (prospective plan).
**Type:** task
**Status:** resolved
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F9, F16, F18; LR-01, LR-02)
**Time estimate:** about half a day of agent work on mbit10; 30 min if it ends on a negative report

**What to build:** Estimate the t75 native BFS candidate (`extensa-native-bfs-20261005-a8.it1.kronecker.a0`, contract `bfs_tdstep_frontier_staging`) and its baseline with the BFS g16/g17 CPU target description, on the exact input that ticket 09 will time. Save both estimates, with their order recorded, before any new timing. Run `swdb attribute` on the pair and save the real report. If an estimate comes out unknown, close on a negative report naming the missing pieces.

## Acceptance

- [x] Both estimates saved before timing, order recorded, same input as the planned timing.
  ([`order.log`](../evidence/03-first-real-pair/order.log): estimates end 22:50 and 23:16 ET; no
  timing ran; workload `bfs-20261004-uniform22.2f83a134a6bef789` in both requests. A timing must now
  also time source 0 only, the counted source, F44.)
- [x] A real attribution report saved and validated, or a negative report. (Negative; see Answer.)
- [x] Record shares of rewritten, untouched and unattributed time in the map's current state.
  ([map](../map.md#current-state): unknown.)
- [x] Follow the mbit10 rules: lane lease, `df -h` before large runs, raw output outside git.
  ([`lane-a2.json`](../evidence/03-first-real-pair/lane-a2.json), node 1, generation 552;
  [`env-start-a2.txt`](../evidence/03-first-real-pair/env-start-a2.txt); raw output on `/data`.)

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

## Answer

Resolved 2026-10-11 23:17 ET on branch `fga/03-real-pair`. **Negative result (LR-01): both
estimates are unknown, so no attribution report was made.** No timing was run.

**What ran** (mbit10, lane 1 `mbit10-evaluation-node1` generation 552, 19:35–23:16 ET, load ≈1–2,
code `d0c80a8a` in `/data1/yanruj/ArchEvolve-fga03`). Order, from
[`order.log`](../evidence/03-first-real-pair/order.log):

1. 19:35–20:07 count baseline `typed-library-bfs-scalar-profile-20261003-a1.baseline` (F26).
2. 20:07–20:39 count candidate `extensa-native-bfs-20261005-a8.it1.kronecker.a0`.
3. 20:39–22:25 freeze two fresh protocols (F27; the counted run arguments name each side's own
   wrapper folder, so one protocol per side). Each freeze took about 50 min (whole-store check).
4. 22:25–22:50 estimate baseline; 22:50–23:16 estimate candidate.

Both counts: `registered-cpu-sg`, binding `verified`, evidence `execution`, ROI
`bfs.complete_call.v1`, T1, workload `bfs-20261004-uniform22.2f83a134a6bef789`, slot = source 0,
repetition 0, counted correctness passed.

**Result.** Both estimates have `seconds: null`. Every region that ran is unknown: 16 of 286
regions (baseline) and 19 of 289 (candidate); the other regions are 0 s. So there is no share to
split, and rewritten/untouched/unattributed shares are **unknown**.

**Missing pieces** (corrected 2026-10-12, final review H2, F41). Five groups, the same on both sides.
Every item, with its region count per side, is in
[`unknowns-summary.json`](../evidence/03-first-real-pair/unknowns-summary.json), made by the
deterministic script [`unknowns_summary.py`](../evidence/03-first-real-pair/unknowns_summary.py)
from the two saved estimates (it checks every trial and the estimates' own
`parameter_report.structural_missing`; 35 items per side).

| # | Group (regions, baseline / candidate) | What is missing |
|---|---|---|
| 1 | Characterization allowlist (16 / 19, every unknown region) | `native_service_costs` and `memory_service_scenario` in `mbit10.cpu.lanl20261006.t1.services.v1` accept only the four gapbs g16/g17 counts (risk B1) |
| 2 | Call costs (7 / 7; 17 calls) | no service rate for OpenMP runtime (`__kmpc_*`), allocator (`_Znam`, `_ZdaPv`, `malloc`), `llvm.memcpy`/`llvm.memmove`, `system_clock::now`, iostream and `ctype`, `strlen`, one `indirect-call` |
| 3 | OpenMP projection (5 / 5) | `openmp.exact_characterization_projection`: no exact OpenMP characterization/static-site projection for these counts; the estimates mark it `required_for_total` |
| 4 | Call-shape size bins (2 / 2; 10 bins) | `_Znam`/`_ZdaPv` at 16 777 216 and 16 777 220 bytes, and six `llvm.memmove` bins (140, 4388, 7300, 9044, 14496, 30164 bytes) |
| 5 | Memory-scenario cells (2 / 2; 5 items) | write cells 1 and 2, access primitives 107, 109 and 113 |

Fixing them needs a new target description, frozen before any timing; not done here (the ticket
forbids changing the description). Not an estimate gap: the description has no `bytes_per_s`
(risk B3), so the resource floor would stay unknown too.

**Records added** (master copies, under `records/`):
- `protocols/fga03.t75-baseline.uniform22.t1.estimate.protocol.a2.6ac95ee72d9e4798`
- `protocols/fga03.t75-candidate.uniform22.t1.estimate.protocol.a2.d305b51d59a092bc`
- `workload_characterizations/fga03.t75-{baseline,candidate}.uniform22.t1.characterization.a2`
- `estimates/fga03.t75-{baseline,candidate}.uniform22.t1.estimate.a2`

Validated on mbit10 at `d0c80a8a` against the copied store: `OK: 711 record(s) valid`
([`validate-mbit10-a2.txt`](../evidence/03-first-real-pair/validate-mbit10-a2.txt)). Copied byte
for byte to the Mac (SHA-256 checked); not re-validated on the Mac (a whole-store check needs about
7 GB of RAM for about 50 min).

**For ticket 09.** Its F19 check has no estimated shares to compare, so it closes on the same
missing pieces with verdict `split_unverified`. No rerun is planned: Yan-Ru declined the optional
follow-up ticket on 2026-10-11. For the record, a rerun would have to time source 0 only (the
counted source, F44), not the requests' `[0, 1234, 7777]`, on a later day than the estimates (F43).

**Plan changes, for the record.** Attempt a1 (g16 input, implementation baseline) was stopped
before it wrote anything; see the a2 amendment above. `attribute` stays out of
`archevolve.EVIDENCE_COMMANDS` (not decided here; nothing to attribute).

**Final review fix (2026-10-12 00:40 ET, branch `fga/final-fixes`).**
- H2 (F41): the missing-piece list above was incomplete; it now has the OpenMP projection and the
  six `llvm.memmove` size bins, from a deterministic script.
- L15: the fga03 records validate at `yanrujhou_main` HEAD too: whole-store `swdb validate` at
  `528eadb6` on mbit10, `OK: 713 record(s) valid`
  ([`validate-mbit10-head-528eadb6.txt`](../evidence/03-first-real-pair/validate-mbit10-head-528eadb6.txt)).
- L9 (LR-06), checked on mbit10 2026-10-12 00:09 ET. Kept in
  `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/` (65.7 MB in all; `/data` had 57 GB
  free), manifest SHA-256 = sha256 of `sha256sum` over the folder's sorted files:

  | Folder (`a2/`) | Files | Bytes | Manifest SHA-256 |
  |---|---|---|---|
  | `baseline-counted` | 13 | 15 978 104 | `6a73000552ddb612b1b02aa3de3ab91b40d70872ddb105e46ca8f626daabe133` |
  | `candidate-counted` | 13 | 16 103 834 | `5e3789357eedd9595c45190f90d43d68c629f44937364360a07f8664257d1201` |
  | `swdb-protected-cpu-wrapper-8yok3jhh` | 4 | 16 815 389 | `7a16e1d3534de88ec110f21eedc79c4b752e0372b1ad8720f9a668e8ac00ca69` |
  | `swdb-protected-cpu-wrapper-bjvc5lh_` | 4 | 16 815 409 | `6dc0b113b8ba4a285475efb35a4588f61da5e312a1925dd1b967dd780bb51029` |

  Their only planned reader, the ticket 09 rerun, is gone (follow-up declined), so they are
  disposable; they stay until Yan-Ru authorizes removal (LR-06: remove only authorized output).
  The `/data1/yanruj/ArchEvolve-fga03` worktree no longer exists (already removed).
