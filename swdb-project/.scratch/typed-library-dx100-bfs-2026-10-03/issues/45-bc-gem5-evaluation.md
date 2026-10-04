# 45 — BC gem5 evaluation

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 26, 29, 41, 43, 44
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** One small BC gem5 run demonstrates contract reuse on hardware.

## Acceptance

- [x] The pre-dispatch checks are recorded.
- [x] One small gem5 BC run passes the BC completion witness and execution case.
- [x] Records are committed after Yan-Ru approves.

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

## Answer

Resolved 2026-10-04 00:52 ET (agent, BC track). The derived BC contract runs on the DX100 target
model. One small gem5 run passes the BC v2 completion witness for both roles, and the candidate
passes the read-only execution case and the frontier check. On this graph the candidate is slower.

**Environment.** mbit10, `/data1/yanruj/ArchEvolve` on `yanrujhou_main` at
`65a7c7b35f9acfb4c8d4b3a5fab375a6e2181770`, carrying the witness fix from b7f7798. Before the pull, the 10
untracked a1 records matched their origin blobs (`git hash-object`) and were deleted; the untracked
`records/.retention.lock` was left in place. Lane node 0, lease `mbit10-evaluation-node0` generation
449, entered through the same `socket_lane.sh` (sha256 `00c269b4...`, equal to origin); `numactl
--cpunodebind=0 --membind=0`, aligned to `no_gapbs_batch_running`; tmux `swdb-bc-gem5-20261003-r1`
under `timeout 14400`. Node 1 and the legacy lease were released at dispatch. Another agent's ticket-58
job held node 1 from 00:35 to 00:37 ET; it shares the OS and memory link. Lane held 2026-10-04 00:25:35 to
00:48:41 ET (23 min 6 s), lane exit 0, lease released. Load1 1.10 at start, 2.16 at end. `/data1` 41
GB and `/data` 74 GB free before and after. Raw output (114 MB for a1 and r1 together) stays in
`/data1/yanruj/EvolveSWDB_runs/bc-gem5-20261003-a1/`; it was not copied to the Mac.

**Preflight.** The timed stage admitted 36 GiB on node 0 (estimated capacity 41.16 GB = 38.3 GiB;
node 1 would have been refused at 27.4 GB) and 8 GiB of storage on `/data1` plus the 20 GiB reserve.

**Runs** (driver `tools/bc_gem5_driver.py --stage timed --attempt r1`, reusing the a1 prepare
receipts unchanged: protocol `bc-gem5-20261003-a1.protocol.e731422f9ab9f668`, candidate tree
`d6f86eb6...` equal to `certification.1e389a959ffb4ff9bfdcf4cea9eace06`).

| Workload | Role | Host time (checkpoint + simulation) | BC v2 witness | Read-only case / frontier | Peak RSS |
| --- | --- | --- | --- | --- | --- |
| BC Kronecker 14, source 0 | baseline (full-source scalar) | 80 s + 410 s | passed | not requested | 30.5 GiB |
| same | candidate (contract.bc_read_offload) | 80 s + 457 s | passed | observed (S=3, I=90, R=31, A=0, no indirect stores, I=3R-S); full tiles 25, tail tiles 3; frontier [1,6,2269,9757,509,1] equals the oracle | 32.2 GiB |

Both runs return the same 16,381 scores (FNV-1a `9ec6d9845db5d49c`), and BCVerifier prints PASS after
the ROI seal. Records: `bc-gem5-20261003-a1.timed-r1.{baseline,candidate}.evaluation`, one-replay
aggregates `...timed-r1.{baseline,candidate}.aggregate`, comparison `bc-gem5-20261003-a1.timed-r1.comparison`.

**Timing (simulated point ratio, single graph, single source).** Complete-call ROI: baseline 3.075 ms,
candidate 7.247 ms simulated; ratio 0.424 (decision `regression`). It covers one Kronecker-14 graph,
source 0 and one deterministic replay. Attribution is joint hardware/software (MAA enabled for the
candidate only), and the dependency pass stays scalar. This run was chosen to demonstrate reuse,
not speed. One plausible factor, not measured: scale-14 levels are small (largest 9,757 vertices), so
per-chunk accelerator setup may outweigh the read savings. No population or native claim.

**Library state.** Using this comparison, `contract.bc_read_offload` now derives as shared/evaluated_on_target.

**Pruning (ticket 26).** The successful r1 executions' checkpoint payloads were pruned
automatically after durable evaluation (`prune-intent-c0076820...`, `prune-intent-ce1e2d1c...`,
`retention-3db4bae3...`, `retention-f55291fe...`). The failed a1 baseline keeps its checkpoint. In
ArchEvolve mode the debug traces (candidate `roi-debug.trace.gz`, 43 MB) stay until a team claim
cites them or `swdb claim --release` records that none will; that decision is Yan-Ru's.

**After the run.** No yanruj process referencing swdb, gem5, socket_lane or the run remained; no
tmux session; all three leases read `released`. Nine new records were copied by scp (sha256 match);
`swdb validate`: 508 valid.

**Left open.** Trace release or claim (above). The failed a1 baseline record stays as
`missing_observation`; the witness bug that caused it is fixed in b7f7798. The uniform BC workload
was not run on gem5.

