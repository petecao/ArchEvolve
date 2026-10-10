# 41 — BC native evaluation on mbit10

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 08, 40
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** A real native BC evaluation passes BCVerifier on mbit10.

## Acceptance

- [x] The go-ahead and the run environment are recorded.
- [x] The BC workloads are registered and one native evaluation passes BCVerifier.
- [x] Records are committed after Yan-Ru approves.

## Comments

- 2026-10-03 ET (BC-track agent, ticket 40): code is ready. On mbit10 inside an owned lane:
  `scripts/prepare_dx100_bc_scalar_snapshot.py --runs-dir <runs> --register --check --lane <lane>`
  registers `bc-dx100-scalar-only-20261003-a1.source` (not yet in repository records; ticket 42's
  certification cites this ID and its deterministic tree sha256), then
  `scripts/register_bc_workloads.py --from-workload <registered BFS kronecker/uniform workload> --id <bc id> --work-dir <dir> --request-out <file>`
  registers BC workloads on the same graph files (sources need an outgoing edge; pass `--sources` if a BFS source has none).
- 2026-10-03 23:00 ET (BC-track agent, ticket 41): go-ahead recorded. Yan-Ru explicitly approved
  this mbit10 dispatch (Q62) on 2026-10-03, and committing the records, as relayed by the main
  session. Claimed.

## Answer

Resolved 2026-10-03 23:15 ET (agent, BC track). One native BC evaluation passes BCVerifier on
mbit10; both BC workloads are registered. No gain is claimed (unchanged scalar baseline only).

**Run environment.**
- Host mbit10, ArchEvolve checkout `/data1/yanruj/ArchEvolve`, branch `yanrujhou_main`, commit
  `ec50f7898b81cbf998171abef31ed7c50f6bfba7` (fast-forwarded from 58aff85 after checking that no
  measurement from it was running; all three leases were released).
- Lane: node 1, lease `mbit10-evaluation-node1` generation 507, entered through
  `/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh` (checked equal
  to `origin/yanrujhou_main` after `git fetch`); `numactl --cpunodebind=1 --membind=1`, aligned to
  `no_gapbs_batch_running`. Node 0 and the legacy lease were free throughout. Run in tmux session
  `swdb-bc-native-20261003-a1` under `timeout 7200`.
- Lane held 2026-10-03 23:03:42 to 23:09:30 ET (5 min 48 s); lane exit 0; lease released.
- Load: load1 1.00 at start, 2.07 at end (this job's 4 threads included); users logged in: yanruj.
- Disk: `/data1` 41 GB free, `/data` 74 GB free, before and after. Raw output (106 MB) is in
  `/data1/yanruj/EvolveSWDB_runs/bc-native-20261003-a1/`; it stays on mbit10. The dispatch
  preflight admitted the run (`/data1` 43,738,050,560 B free; node 1 MemFree 23,877,582,848 B
  against a 4 GiB budget).
- Governor and `intel_pstate/no_turbo` files are not exposed on this host (sysfs paths absent);
  recorded as unavailable. Environment files: `<run>/env/`.

**Steps (all inside the lane, one driver).**
1. `scripts/prepare_dx100_bc_scalar_snapshot.py --register --check --lane mbit10-evaluation-node1`
   registered `bc-dx100-scalar-only-20261003-a1.source` (tree sha256 `946d5398e335...`, 25 files);
   the scale-10 Kronecker and uniform FUNC smoke passed (4 threads), so its verification is `passed`.
2. `scripts/register_bc_workloads.py` registered, on the exact graph files of the BFS workloads the
   native BFS runs used (scale 18, edge factor 16, sources `[0, 1234, 7777]`, all with an outgoing
   edge):
   - `bc-20261003-kronecker18.f820ca0b525e1b48` from `bfs-20260925-kronecker18.48de8267ac2098d5`;
   - `bc-20261003-uniform18.d763d94cd31590b6` from `bfs-20260925-uniform18.cd2169a5c421baf7`.
   Choice: scale 18, matching the BFS native acceptance/pilot runs; the spec's scale-22 native graphs
   are for Extensa campaigns (D4), not this check.
3. `swdb baseline-candidate` made `bc-native-20261003-a1.baseline` (unchanged scalar source).
4. `swdb evaluate` ran `bc-native-20261003-a1.kronecker18.evaluation`: 4 threads, 3 repetitions x 3
   sources = 9 trials, ROI `bc.complete_call.v1`, build `g++ -std=c++11 -O3 -Wall -fopenmp -pthread
   -DFUNC`. Outcome complete; correctness passed: all 9 checks by `swdb.bc.brandes_scores.v1`
   pass with maximum absolute difference 0.0 and 173,900 reachable vertices per source. Median ROI
   0.0277 s (per source 0.0281 / 0.0278 / 0.0274 s). Evaluator wall 4 min 14 s (mostly the Python
   BCVerifier reproduction).

**Records** (copied from mbit10 by scp; sha256 match): `records/source_snapshots/bc-dx100-scalar-only-20261003-a1.source.yaml`,
`records/workloads/bc-20261003-kronecker18.f820ca0b525e1b48.yaml`,
`records/workloads/bc-20261003-uniform18.d763d94cd31590b6.yaml`,
`records/candidates/bc-native-20261003-a1.baseline.yaml`,
`records/evaluations/bc-native-20261003-a1.kronecker18.evaluation.yaml`. `swdb validate`: 488 valid
on mbit10.

**Left open.**
- The uniform BC workload is registered but not evaluated (one evaluation was the acceptance).
- mbit10's checkout holds these five records as untracked files; delete them there before the next
  `git pull` brings the committed copies, or the pull refuses to overwrite them.
- After the run no yanruj process referencing swdb, the run, or socket_lane remained; all three
  leases read `released`.
