# 10 — Rerun ticket 09: time source 0 and run the split check

Created: 2026-10-12 01:10 ET. Updated: 2026-10-12 20:21 ET (claimed; run prepared; profiler gap fixed).
**Type:** task
**Status:** claimed
**Blocked by:** 09
**Spec:** `../spec.md` (C13 (timing half); user stories 26, 27)
**Code map:** `../notes/ops.md` (timing section, F43/F44)

**Time estimate:** about 3 hours of lane time.

## What to do

On a **later Eastern calendar day** than both `.a3` estimates (F43 compares the region profile's
`created` date to the estimates'), time workload `bfs-20261004-uniform22.2f83a134a6bef789` with the
kept counted binaries (`/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/`): LLVM 22
`clang++`, evaluator v3, 20 repetitions, `sources: [0]` (F44). Then `bfs-profile` per side, the checked
attribution report under `swdb.split_check.v2`, and `swdb validate`. Afterwards apply LR-06 to the
kept binaries (65.7 MB) and the raw run folders.

## Acceptance

- [ ] Split check verdict `passed` or `failed`, accepted by `swdb validate`.
- [ ] Checked attribution report committed; evidence in `evidence/10-rerun-09/`.
- [ ] Kept binaries removed per LR-06 (identity, size/hash and no-use evidence recorded).

## Progress

**2026-10-12 20:21 ET — prepared (branch `cpud/10-split-check`), no timing yet.**

- **Gap found and fixed: `bfs-profile` could not read a scalable evaluation.** It needed the v1
  text graph (`context.workload.canonical_path`), which an evaluator-v3 evaluation does not have,
  so step 2 would have crashed. `swdb/bfs_profiling.py` now profiles v2/v3 evaluations:
  - region binary from the v3 SG driver, with the evaluation's LLVM 22 toolchain flags and
    library paths;
  - each execution checked by the trial-record check and the compiled verifier;
  - `memory: false` required (Callgrind stays v1-only).
  Test: `tests/test_bfs_profiling.py::test_public_profile_of_a_scalable_v3_evaluation_times_regions_on_the_sg_input`.
  Doc: `docs/reference/bfs-profiling.md`. v1 profiles build and run exactly as before.
- **Not the kept binaries for timing.** `swdb evaluate` always builds from the candidate source
  (no option to time a prebuilt binary). The kept folders stay a reader only through the `.a3`
  protocols' run arguments; `run.sh` records their identity before use, and they are removed
  after the last reader (LR-06).
- **Files** (`evidence/10-rerun-09/`): two evaluation requests (the a1 requests with only `id`
  and `sources: [0]` changed), two profile requests (`repetitions: 5`, `memory: false`), and
  `run.sh` (guard → evaluate ×2 → bfs-profile ×2 → checked `attribute` → whole-store validate;
  ET order log).
- **Start conditions:** ticket 09 resolved with numeric `.a3` estimates; ET date strictly after
  both estimates' `created` (F43, also checked inside `run.sh`); code-review F1 fix (numeric
  floor-only bandwidth on services.v2) merged into `cpud/integration`.
