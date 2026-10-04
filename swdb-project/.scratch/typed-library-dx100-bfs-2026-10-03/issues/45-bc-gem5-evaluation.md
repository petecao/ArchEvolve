# 45 — BC gem5 evaluation

Created: 2026-10-03
**Type:** task
**Status:** claimed
**Blocked by:** 26, 29, 41, 43, 44
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** One small BC gem5 run demonstrates contract reuse on hardware.

## Acceptance

- [x] The pre-dispatch checks are recorded.
- [ ] One small gem5 BC run passes the BC completion witness and execution case.
- [ ] Records are committed after Yan-Ru approves.

## Comments

- 2026-10-03 23:40 ET (BC-track agent): go-ahead recorded. Yan-Ru explicitly approved this mbit10
  dispatch (Q62) and committing the records on 2026-10-03, as relayed by the main session. Claimed.
- 2026-10-04 00:10 ET checkpoint (BC-track agent): attempt a1 ran; the baseline simulation and its
  in-guest BCVerifier passed, but the evaluator refused the record because of a ticket-44 witness
  bug. The bug is fixed locally; a fresh timed attempt needs the fix pushed and synced first.

  **Environment.** mbit10, `/data1/yanruj/ArchEvolve` on `yanrujhou_main` at
  `23128aa7eba2f88512dbe1c1dc6b7fe90a867eb1` (fast-forwarded from 8e41aae, no measurement running,
  tracked tree clean; untracked `records/.retention.lock` left). Lane node 0, lease
  `mbit10-evaluation-node0` generation 448, entered through
  `/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh` (sha256 equal to
  `origin/yanrujhou_main` after `git fetch`), `numactl --cpunodebind=0 --membind=0`, aligned to
  `no_gapbs_batch_running`; tmux `swdb-bc-gem5-20261003-a1` under `timeout 14400`. Node 1 and the
  legacy lease were released before and after. Lane held 2026-10-03 23:46:17 to 23:59:03 ET (12 min 46 s),
  lane exit 1, lease released. Load1 1.05 at start, 1.02 after. `/data1` 41 GB and `/data` 74 GB free
  before and after. Raw output (62 MB) stays in `/data1/yanruj/EvolveSWDB_runs/bc-gem5-20261003-a1/`
  (`env/start`, `env/end`, driver receipts). Governor/no_turbo sysfs files are absent on this host.

  **Preflight** (`swdb/dispatch_preflight.py`, inside each stage): prepare admitted 4 GiB, timed
  admitted 36 GiB on node 0 (MemFree 34.97 GB; estimated admission capacity 41.19 GB = 38.4 GiB;
  `/data1` 43.6 GB free against 8 GiB + 20 GiB reserve). Node 1 would have been refused (27.4 GB).

  **Graph choice.** Kronecker scale 14 (edge factor 16; 16,381 vertices, 425,860 directed edges),
  source 0 (out-degree 6), the exact bytes of `bfs-20260925-kronecker14.d03827828666f7dd`. It is a
  certified matrix size of the BC contract and its forward-pass levels exceed one 16,384-element
  tile, so full and tail tiles can occur. Simulator RSS does not shrink with the graph (the 16 GB
  guest dominates; even the tiny BFS coverage graph peaked at 32.2 GiB), so the 36 GiB budget stays;
  scale 14 cuts simulated time instead (baseline: 80 s checkpoint + 410 s simulation).

  **Driver.** `tools/bc_gem5_driver.py` (public SWDB commands only; shared mechanics from the
  ticket 28/29 driver), copied by scp into the run folder (sha256 `3461a8a1...` for a1) and run with
  `SWDB_PROJECT` set to the checkout.

  **Prepare (passed, 3.5 min).** Workload `bc-gem5-20261003-kronecker14-s0.bba5ce8b1f8b84b2`; full-source
  snapshot `bc-gem5-20261003-a1.full.source` and baseline candidate `bc-gem5-20261003-a1.baseline`
  (BFS precedent: unchanged full DX100 source, scalar path); contract-fixture package
  `bc-gem5-20261003-a1.contract-fixture-package` (explicitly labeled: no profile drove the
  choice); protocol `bc-gem5-20261003-a1.protocol.e731422f9ab9f668` (version 1, no supersedes, no region
  pairs, copied from the BFS a2 treatment with BC kernel, ROI `bc.complete_call.v1`, checker
  `dx100.bc.verifier.v2`, BC runtime pins, no race companion); proposal `bc-gem5-20261003-a1.proposal`
  submitted `library/dx100/bc-forward-pass.patch` and produced candidate tree `d6f86eb6...`, equal to
  certification `certification.1e389a959ffb4ff9bfdcf4cea9eace06`; builds
  `bc-gem5-20261003-a1.{baseline,candidate}.primary.build` match the frozen compiler and flags.

  **Timed a1 (failed record, run itself completed).** `bc-gem5-20261003-a1.timed.baseline.evaluation`:
  the guest printed one sealed `SWDB_BC_RESULT` (16,381 scores) and `Verification: PASS`, and the v2
  exit witness completed with status 0. Peak sampled RSS 30.5 GiB. The record is
  `missing_observation`, because `swdb/bc_witness.py` required `context.candidate_build is True`;
  real records store the compile record ID there (BFS's validator uses `bool(...)`), and ticket 44's
  fixture used `True`. With that one condition corrected, the full BC v2 witness validates on this
  exact retained baseline (checked read-only on mbit10). The candidate was not run. The failed
  attempt keeps its checkpoint, as required for failed runs (ticket 26).

  **Fix (local commit, not pushed).** `swdb/bc_witness.py` uses `bool(context.get("candidate_build"))`;
  `tests/test_bc_gem5_witness.py` now uses a build-ID string, which fails 9/18 before the fix and passes 18/18
  after it. `tools/bc_gem5_driver.py` gains `--attempt` so a fresh timed attempt reuses the
  completed prepare without touching a1.

  **Next.** Push; on mbit10 delete the 10 untracked `records/*/bc-gem5-20261003*` copies (committed now),
  `git pull --ff-only`, then in a node lane run
  `python3 tools/bc_gem5_driver.py --stage timed --attempt r1 --id bc-gem5-20261003-a1 --runs-dir /data1/yanruj/EvolveSWDB_runs/bc-gem5-20261003-a1 --approval-reference "<Q62>"`
  (about 25 min expected: two executions, aggregates and the comparison).
