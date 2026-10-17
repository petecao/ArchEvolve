# Profiling on mbit10

Updated: 2026-09-30 (Eastern Time).

[Guide](README.md) · [Setup and profiler details](reference/mbit10-profiling.md)

Use mbit10 for EvolveSWDB measurements. The Mac is ARM; mbit10 is x86_64, and their
measurements are not comparable. Before remote work, read the
[host rules](../../.claude/rules/remote_server.md) and
[mbit10 procedure](../../.claude/skills/mbit10-runs/SKILL.md).

## Run a profile

1. Sync through git and verify the remote commit. Keep repositories, builds, and
   caches under `/data1/yanruj/`. Never update a checkout while it is measuring.
2. Inspect both socket leases and the legacy lease, current load, and
   `df -h /data1 /data`. At most two measurement jobs may run: one per socket.
   A held legacy lease blocks admission. Use the current MemAcc lane scripts.
3. From `/data1/yanruj/ArchEvolve/swdb-project/` on `yanrujhou_main`,
   launch through the [lane wrapper](../scripts/mbit10/profile_in_lane.sh):

   ```sh
   cd /data1/yanruj/ArchEvolve/swdb-project
   bash scripts/mbit10/profile_in_lane.sh 1 gapbs-pr-gs kron-g16-k16 --cachegrind yes
   ```

4. Validate the resulting records and review their correctness, completeness,
   timing scope, and environment before publishing metadata through git.

The wrapper verifies host, lane-script freshness, leases, space, and checkout
state. The profiler verifies actual process ancestry, CPU/memory binding, and
lease ownership. Environment variables alone cannot establish admission.

## Interpret and retain results

Ordinary profiling defaults to five trials at each of 1, 2, 4, 8, and 16 threads
within one socket. Correctness is checked before timing. An explicitly allowed
unfinished check remains unverified and incomplete. Cachegrind is a separate
single-threaded diagnostic with a timeout; its counts are simulated. Kernel-only
counts use the recorded symbols, while whole-run counts include setup.
BFS comparisons use their own [frozen protocol](bfs-handoff.md).

Raw outputs stay outside git on mbit10: `/data1/yanruj/EvolveSWDB_runs/`, or
`/data/yanruj/EvolveSWDB_runs/` when required to preserve free space. The wrapper
reserves run space while keeping 20 GB free. Records name the actual location;
never copy remote raw output to the Mac.

The host is shared and has no sudo access. Record load and environment instead
of changing governor or system settings. Recheck hardware-counter availability;
when unavailable, inferred bottlenecks and simulated misses remain labeled as
such. The detailed procedure covers installation, batches, overrides, timeouts,
Cachegrind re-parsing, and process-group termination.
