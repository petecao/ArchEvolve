# 10 — Rerun ticket 09: time source 0 and run the split check

Created: 2026-10-12 01:10 ET. Updated: 2026-10-13 01:55 ET (resolved: split_unverified); 2026-10-12 20:21 ET (claimed; run prepared; profiler gap fixed).
**Type:** task
**Status:** resolved
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

- [x] Split check verdict `passed` or `failed`, accepted by `swdb validate`. (The code's failing verdict is `split_unverified`.)
- [x] Checked attribution report committed; evidence in `evidence/10-rerun-09/`.
- [x] Kept binaries removed per LR-06 (identity, size/hash and no-use evidence recorded).

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

## Answer

Resolved: 2026-10-13 01:55 ET. Branch `cpud/10-split-check`. Runbook and evidence:
[`evidence/10-rerun-09/`](../evidence/10-rerun-09/README.md).

**Short version.** Verdict **`split_unverified`**: every rewritten/untouched gap is 35–42
percentage points, far above the 10-point rule. The main cause is the profiler, not the
estimate: region guards inflate tight per-vertex loops 5–6x, and most of those loops are untouched.

### Split check (`swdb.split_check.v2`, max |gap| 0.10)

| Side | Origin | Estimated share | Measured share | Gap |
|---|---|---|---|---|
| Baseline | untouched | 6.49% | 41.43% | **+34.94 pp** |
| Baseline | agent-rewritten | 93.51% | 58.57% | **−34.94 pp** |
| Baseline | unattributed | 0% | 0% | 0 |
| Candidate | untouched | 8.33% | 50.81% | **+42.48 pp** |
| Candidate | agent-rewritten | 91.67% | 49.19% | **−42.48 pp** |
| Candidate | unattributed | 0% | 0% | 0 |

- Record: `records/attributions/fga03.t75.uniform22.t1.attribution.a3.split-check.yaml`. Apart from
  `split_check`, it equals ticket 09's report (same shares, ranking and floor).
- Accepted by the whole-store check on mbit10: `OK: 733 record(s) valid`.

### Why the measured split is not a clean timing split

- Instrumented run per repetition: 9.20 s baseline and 7.49 s candidate, against native medians of
  1.686 s and 1.247 s. So the scope guards cost **5.5x / 6.0x** (the record says overhead is included).
- The overhead lands where scopes run per vertex: 4 194 304 entries per repetition each.
  - `InitParent` (untouched): 10.2 s baseline over 5 repetitions, more than a whole native call per repetition.
  - The `DOBFS` per-vertex loop (untouched): 4.2 s.
  - The rewritten `TDStep` loops carry the same per-vertex guards.
- So the gaps say little about the estimator's split. A useful split check needs lower-overhead
  timing (sampling, or guards only on function-level scopes). Not done here.

### Native timing (evaluator v3, LLVM 22, source 0, 20 repetitions, node0 lane)

| Side | Median | Min–max | `.a3` estimate | Estimate ÷ measured |
|---|---|---|---|---|
| Baseline | 1.686 s | 1.489–1.740 s | 26.643 s | 15.8x |
| Candidate | 1.247 s | 1.094–1.286 s | 20.770 s | 16.7x |

- Measured speedup 1.352x; estimated 1.283x.
- The estimates overstate absolute time about 16x. There is no error band for `services.v2` (C14),
  so no agreement claim is made.

### Resource floor

Unchanged from ticket 09 and numeric in all 286 + 289 regions: sum **0.197 s** (baseline) and
**0.206 s** (candidate), compute-throughput-limited. Both are far below the measured times.

### What ran, and code needed first

- Order: guard (F43: today 2026-10-13 > the estimates' 2026-10-12) → 2 evaluations → 2
  `bfs-profile` → checked `attribute` → whole-store validate. Lane node0, generation 523,
  2026-10-13 01:10–01:44 ET, commit `75036363`, load1 about 6–7 (another session's tests on node1).
- F44 holds: machine mbit10, sources `[0]`, same input seed. All 20 + 20 trials and 5 + 5
  profile runs passed the compiled verifier.
- Three blockers were found and fixed before any timing:
  1. `bfs-profile` could not read a v3 evaluation (`134e68fa`).
  2. Discovery failed on Clang's `omp.h`; caught by a static precheck, fixed with a parser-only
     shim (`574be6e2`).
  3. A full-store run was too slow. Attempt a1 was stopped before any trial, and the job now runs
     on reference-closed views (`75036363`).
- Not used for timing: the kept counted binaries. `swdb evaluate` always builds from source. Their
  only reader was the `.a3` protocols' run arguments, and validation does not open them.

### LR-06 (2026-10-13 01:47 ET, `lr06-identity.txt`, `lr06-remove.txt`)

- Removed `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/` (59 files, 65 738 321 bytes).
  Its four `a2/` manifests matched ticket 03's table under `en_US.UTF-8` order.
- Also removed this ticket's raw folders: `cpud10-20261013-a1` (1.24 GB, mostly a partial
  index), `cpud10-20261013-a2` (1.79 GB), `cpud10-precheck-20261012`, and the four
  `/data1/yanruj/EvolveSWDB_builds/cpud10.*` build folders.
- Before removal: no open files, no process naming any path, and my node0 lease released.
  Also removed: the mbit10 worktree `/data/yanruj/ArchEvolve-cpud10` and the tmux sessions.
- Records hold every hash a later check needs.
