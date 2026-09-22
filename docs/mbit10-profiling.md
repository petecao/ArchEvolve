# Profiling on mbit10

Updated: 2026-09-22

How `swdb profile` runs on the lab host. The always-on rules are in
`.claude/rules/remote_server.md`; the host facts and the lane mechanism are in the
`mbit10-runs` skill. This page is the EvolveSWDB procedure built on them.

## One-time setup

```
ssh mbit10
cd /data1/yanruj && git clone git@github.com:ruchou/EvolveSWDB.git
# the lane script: a small sparse clone of MemAcc on the owner's main branch
git clone --depth 1 --branch yanrujhou_main --filter=blob:none --sparse \
    git@github.com:MaizeHPC/MemAcc.git Memacc-evolveswdb-lane
cd Memacc-evolveswdb-lane && git sparse-checkout set AgenticRefiner/scripts/host
```

The other MemAcc checkouts on the host belong to other work; EvolveSWDB never pulls into
them. `profile_in_lane.sh` refuses to run if this clone's `socket_lane.sh` or
`hostlock.sh` differs from the branch on GitHub.

## Every session

1. Sync code by git only: push from the Mac, then on mbit10
   `cd /data1/yanruj/EvolveSWDB && git fetch && git checkout <commit>` and note
   `git rev-parse --abbrev-ref HEAD` and `git rev-parse HEAD`. Never pull while a profile
   from this checkout is running.
2. Check the lanes: `grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json`.
   A held `mbit10-evaluation-node<N>` means socket N is busy. Tell other sessions which
   lane you take (session board or a direct message) before you start.
3. Check the disks: `df -h /data1 /data`.
4. Start a named tmux session and run one profile, or a batch:
   ```
   tmux new -s evolveswdb-pilot
   bash scripts/mbit10/profile_in_lane.sh 1 gapbs-pr-gs kron-g16-k16 --cachegrind yes
   bash scripts/mbit10/profile_batch.sh 1 scripts/mbit10/pilot.list
   ```
5. When the batch ends, `python3 -m swdb validate`, then commit the new profile records
   and the updated input records on mbit10 and push, or pull them to the Mac. Raw output
   stays on mbit10.

## What `profile_in_lane.sh` does

It refuses to start (exit 3) unless: the host is mbit10; the lane script equals the
repository version; the chosen socket's lease is free; `/data1` and the runs disk each
have at least 20 GB free; and no tracked file outside `records/` is modified. It prints
all three leases and `df -h`, then runs

```
socket_lane.sh <node> evolveswdb-<impl>-<input> --record <runs>/lanes/<job>.<stamp>.json -- \
  timeout 14400 python3 -m swdb profile <impl> <input> mbit10 --runs-dir <runs> --lane ... "$@"
```

`socket_lane.sh` re-executes itself under `numactl --cpunodebind=<node> --membind=<node>`,
takes the lease, applies the load gate, records affinity, memory policy, load, and lease
generation in the lane JSON, and then runs the command. Every build, run, extractor, and
cachegrind process of the profile inherits that binding. Inside it, threads are placed
with `OMP_PLACES=cores OMP_PROC_BIND=close`, at most 16 threads (one per core of the
socket), so hyperthreads stay idle.

## Where output goes

Raw output (build logs, timer output, `index_features.json`, `cachegrind.out`, the host
state) goes to `<runs>/<profile id>/`. The default runs folder is
`/data/yanruj/EvolveSWDB_runs`: `/data1` had 24 GB free on 2026-09-22, just above its
20 GB floor, and the GPU campaign holding node 0 asked for EvolveSWDB output on `/data`.
Set `EVOLVESWDB_RUNS` to change it; the profile record names the folder it used. Raw
output never goes into git and is never copied to the Mac.

## Measurement protocol

- Trials: `--trials 5` per thread count by default; each thread count is its own process
  (the graph is built once per process, outside the timed region).
- Threads: 1, 2, 4, 8, 16 inside one socket.
- Correctness: the kernel's correctness check runs once at the largest thread count
  before timing; a failure stops the profile and writes no record.
- Cachegrind: single-threaded, one trial, with `--cachegrind-timeout` (default 3600 s).
  A timeout is recorded as a `timed_out` part and the profile is marked incomplete.
  Cachegrind's last-level cache is the host's L3 (24 MiB, 12-way). Kernel-only counts
  sum the functions named in the implementation's `run.kernel_symbols`, including the
  OpenMP outlined bodies; whole-run counts include graph generation and building.
- The host is shared and there is no sudo: the profile records the load, the logged-in
  users, the governor, and turbo state instead of controlling them.
- No hardware counters (`perf_event_paranoid` = 4): the bottleneck is inferred from
  footprints, thread scaling, and simulated misses, never measured.
