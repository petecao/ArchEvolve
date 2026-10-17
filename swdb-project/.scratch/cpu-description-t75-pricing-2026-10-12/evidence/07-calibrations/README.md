# Ticket 07 runbook: services.v2 calibrations on mbit10

Updated: 2026-10-12 ET. Branch `cpud/07-calibrations`. Raw root (deleted after export, LR-06):
`/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1/`.

## For ticket 08: the new record IDs

Pass each of these to `bind-cpu-services` with `--calibration`, beside the `services.v1` list:

```
--calibration mbit10.cpu.lanl20261006.resource.memory-v2.a1
--calibration mbit10.cpu.lanl20261006.resource.allocator-v2.a1
--calibration mbit10.cpu.lanl20261006.service.openmp.a2
--calibration mbit10.cpu.lanl20261006.service.library-call.a1
--calibration mbit10.cpu.lanl20261006.resource.bulk-total.a3
```

- Keep `--bulk-copy-calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1`. Batch a3 also
  measures the memcpy8 cell (op 0), so the copy cell is duplicated (`notes/bulk.md`).
- Keep `service.openmp.a1` (classes 0–21); `service.openmp.a2` holds only class 22.
- The `service.memory-v2.a1`, `service.allocator-v2.a1` and `service.bulk-total.a3` records are
  the sources of their resource records. Bind the resource records, as `services.v1` does.

## What ran where

| Lane job | Lane | Lease gen | Steps | Source commit |
|---|---|---|---|---|
| `cpud07-calib-b` | node1 | 558 | OpenMP a2 count + elapsed (`--profile 22`) + receipt check; library-call count + elapsed (**failed**, see below) | `598232ca` |
| `cpud07-calib-a` | node1 | 559 | memory_v2, allocator v2, bulk a3 (count, then elapsed, each) | `598232ca` |
| `cpud07-calib-l` | node1 | 561 | library-call count + elapsed, attempt 2 | `f2d41156` |
| `cpud07-calib-t` (attempt 1) | node1 | 560 | the two native OpenMP tests (failed: no libstdc++ headers) | `598232ca` |
| tests attempt 2 | socket 0, `numactl`, no lease | — | same tests with the wrapper bin folder (failed: 240 s helper timeout) | `598232ca` |

- Node0 was held all day by another session's full test suite (`swdb-full-suite-20261012-a2`,
  `pytest -n 6`). So every measurement ran in the node1 lane, one job at a time. Host load1 was
  5.8–9.0 during the measurements (the other socket's pytest). Each receipt records its own
  start and end load.
- Imports are not measurements. They ran pinned to socket 0 with `numactl`, without a lease,
  into two copied stores in parallel (`records-b`, `records-c`). Each import commits through
  `writer.commit`, which runs the whole-store check, so each takes about 21 minutes and 7 GB RSS.
- Lane records: `lane-*.json`. Order log: `order.log`. Host snapshots: `env/`. Per-step wall time
  and peak RSS: `step-times.tsv`. Per-cell summary: `receipt-summary.json`.

## Exact commands

Scripts in this folder, run from `$RAW/scripts/` on mbit10. `common.sh` sets the checkout, the raw
root, LLVM 22, `OMP_*`, `LD_LIBRARY_PATH`, the `--lane mbit10-evaluation-node<N>` flag and the
`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13` toolchain flag.

1. Setup (on mbit10):
   ```sh
   cd /data1/yanruj/ArchEvolve && git fetch origin cpud/07-calibrations
   git worktree add --detach /data/yanruj/ArchEvolve-cpud07-598232ca 598232ca
   RAW=/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1; mkdir -p $RAW
   cp -a /data/yanruj/ArchEvolve-cpud07-598232ca/swdb-project/records $RAW/records
   ```
   The worktree went on `/data` because `/data1` had 22 GB free and a checkout is 2.2 GB.
2. Lane jobs, through the lane script (`chain.sh` / `when-free.sh` do this):
   ```sh
   cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner
   bash scripts/host/socket_lane.sh 1 cpud07-calib-b --record $RAW/lane-b.json -- bash $RAW/scripts/job-b.sh 1
   bash scripts/host/socket_lane.sh 1 cpud07-calib-a --record $RAW/lane-a.json -- bash $RAW/scripts/job-a.sh 1
   SRC=/data/yanruj/ArchEvolve-cpud07-f2d41156/swdb-project \
     bash scripts/host/socket_lane.sh 1 cpud07-calib-l --record $RAW/lane-l.json -- bash $RAW/scripts/job-l.sh 1
   ```
   The lane script copy matches `Memacc-evolveswdb-lane` `yanrujhou_main` (blob `261e7e04`).
3. Imports (`job-i.sh`, items `openmp memory allocator` into `records-b`, `bulk libcall` into
   `records-c`), then `job-v.sh`: merge `records-c` into `records-b`, run
   `targeted_validate.py` on the 8 new IDs, then `python3 -m swdb validate --records $RAW/records-b
   --library <checkout>/library`.

## Failures and fixes

- **Library-call attempt 1 failed** (`paired ordering/resolution differs`). The strlen pilot's
  driver took 0.052 s. Every warm trial then took 0.042–0.046 s, under `min_trial_s` 0.05, and the
  receipt validator refused it. Fix `f2d41156`: the pilot keeps 1.25x headroom, like the OpenMP
  and allocator runners (`pilot_batches` in `swdb/cpu_library_call_calibration.py`, test
  `test_pilot_keeps_headroom_so_warm_trials_still_resolve_min_trial`). Attempt 2 passed.
- **The two native OpenMP tests fail on mbit10 as written.** They pass no toolchain flag, so
  clang 22 picks GCC 14, which has no libstdc++ headers (`'cstddef' file not found`). `job-t.sh`
  runs them against a wrapper bin folder that adds the same `--gcc-install-dir` flag as every real run.
