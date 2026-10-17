# T16 reference b1 operator

Created: 2026-09-27 ET. Updated: 2026-09-28 ET.

This recipe prepares a fresh launch of Ticket 16 (the artifact reference pair and
the matched control on uniform22, source 2,796,003, 4 guest cores) on the repaired
runtime, under resume decisions R1–R3, R5, R9 and the root decisions R10–R12
(2026-09-27). Earlier T16 attempts stay closed and charged. That includes
`bfs-t16-protocol-recovery-simulator-batch-20260927-a1`, stopped at 09:43 ET,
and its 0.226 s dead-owner reservation, which R1 charges as consumed. No failed
ID is resumed.

## Scope changes, by decision

- **R10: one MAA execution set.** `artifact.maa` and `control.maa` use the same
  binary, configuration (MAA, 8 MiB/16-way, tile 16,384), graph, source and target.
  The `maa` series binds each primary to the artifact protocol and also names the
  control protocol in `shared_protocols`. `validate_protocol_for_simulation`
  accepts this only when every identity for the role matches: target,
  build, instrumentation, reference artifact, workload, ROI, threads, sampling,
  correctness and simulator. Each protocol then gets its own public aggregate
  (`<series>.aggregate` and `<series>.shared0.aggregate`).
- **R11: one replay.** A simulated protocol may set `repetitions: 1` only if it
  declares `sampling.determinism` = `deterministic_simulator_replay.v1` and names
  the retained T15 replay observation. `finalize.py requests --repetitions 1`
  refuses to run without that file.
- **R12: atomic verifier continuation.** This is opt-in with
  `verification.post_roi_cpu: AtomicSimpleCPU`. After the ROI statistics are
  sealed and the post-ROI trace is enabled, `dx100_verify.py` switches the four
  timed O3 CPUs to the same system's switched-out restore AtomicSimpleCPUs, in
  atomic memory mode. The switch is recorded in the seal. The witness validator
  accepts the restore-CPU names only when the switch was requested and recorded.
  Without the option nothing changes, so the running T15 pilot is untouched.

## Grid and allocation (1 replay, atomic verification)

The grid has three series: `artifact.scalar` (BASE, 10 MiB/20-way), `control.scalar`
(BASE, 8 MiB/16-way) and `maa`. That is 3 primary and 3 diagnostic executions,
3 packages, 4 aggregates and, later, 2 comparisons.

| Bound | Value | Basis |
|---|---|---|
| run_seconds | 43,200 | scalar ROI > 10,700 s measured, estimated 15,000–30,000 s |
| diagnostic_seconds | 79,200 | 7,200 checkpoint + 71,970 simulation + 30; T15 diagnostic ROI took 1.4–1.5x the primary host time |
| storage_gib (per execution) | 24 | MAA trace about 19.3 GiB (1.30 GB x 16) |
| profile_seconds / package_seconds | 36,000 / 36,000 | T15 b2 uniform18: 900 s / about 815 s, x16 for uniform22 |
| aggregate_seconds | 14,400 | aggregation re-validates each primary trace (T15: about 3.5 min per scale-18 primary) |
| series_seconds | 507,780 | all 6 execution envelopes behind one slot + own profile/package + 2 aggregates and 2 readbacks |
| allocation | 514,980 s (143.1 h) | 3,600 preparation + series + 3,600 finalization/cleanup |
| storage allocation | 64 GiB | 2 x 24 (MAA) + scalar/ledgers, per-series cap 50 |
| /data free at admission | >= 84 GiB | 64 + 20 reserve (root-approved 2026-09-28 11:15 ET: reserve 30 -> 20 GiB) |

The expected cost is lower than the bound: about 200,000–215,000 s (55–60 h),
assuming atomic verification cuts the roughly 30,000 s O3 verifier to a few
thousand seconds. The 2-replay fallback doubles the executions. Its series
bound exceeds the 864,000-s series cap and it needs 124 GiB of storage, which does not fit /data after
T15 unless traces are reduced.

## Low-storage variant (pinned 2026-09-28; replaces the table above for launch)

[Measurements](../../observations/t16-low-storage-measurements-20260928.json) on the
T15 b3 uniform18 trace show that 99.99% of its bytes come from `MAAIndirect` and
`MAARangeFuser`. The frozen required accelerator case (`executed`) needs only the
`MAATrace` unit Start/End lines (7.4e-5 of the stream). Scalar traces are empty.
Recompression would save at most about 40% (zstd -19). So the pinned plan sets
`trace_flags: MAATrace`, which makes accelerated executions request
`verification.coverage: false`. The protocols were re-frozen as version 2, changing
only the candidate debug flags: `author-reference-t16-b1-20260927.75c1f44c5f653f3a`
and `author-matched-control-t16-b1-20260927.7daeae1ccc961a49`, each with `supersedes`
set to the version-1 record. Tile-size and competing-parent observations become
unobserved by design.

| Bound | Low-storage value |
|---|---|
| storage per execution / per series / allocation | 4 / 8 / 16 GiB |
| raw reserve | 10 GiB (root-approved 2026-09-28) |
| /data free at admission | >= 26 GiB |
| profile / package / aggregate | 7,200 / 7,200 / 3,600 s |
| series_seconds / allocation | 406,980 s / 414,180 s (115.1 h) |

## Steps (all on mbit10, in the immutable runtime checkout)

```sh
OP=.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t16-reference-b1/t16_operator.py
HELPER=/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh
# 1. R12 proof (short lane job, needs a root lane assignment):
bash $HELPER <node> bfs-t16-r12-probe-20260927-b1 -- timeout 9000 /usr/bin/python3.12 -I -B $OP probe
# 2. On the Mac: import evidence, then
#    finalize.py requests --repetitions 1 --atomic --evidence <T15 replay observation>
#    swdb freeze-protocol <each request>; finalize.py plan; pin PLAN_HASHES['t16-reference']; commit; export runtime
# 3. In the new runtime checkout:
/usr/bin/python3.12 -I -B $OP setup
bash $HELPER <node> bfs-t16-reference-linux-tests-20260927-b1 -- \
  timeout 300 /data1/yanruj/venvs/evolveswdb-test/bin/python -I -B $OP tests --kind owned_cleanup
bash $HELPER <node> bfs-t16-reference-linux-tests-20260927-b1 -- \
  timeout 300 /data1/yanruj/venvs/evolveswdb-test/bin/python -I -B $OP tests --kind dx100_interruption
/usr/bin/python3.12 -I -B $OP prepare --node <node>     # the allocation clock starts here
tmux new -d -s t16ref "OPERATOR=$PWD/$OP OPERATOR_SHA=... ADMISSION_SHA=... bash $PWD/.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t16-reference-b1/launch.sh"
```

Run `launch` within 3,600 s of `prepare`. No step retries or overwrites. Raw traces
stay on mbit10, and no trace is deleted in flight.
