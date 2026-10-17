---
name: mbit10-runs
description: How to work ON the mbit10 lab host for EvolveSWDB — the connection check, host facts (CPU, disks, tools, what profiling is possible without counters), cloning and syncing the ArchEvolve monorepo (EvolveSWDB is its swdb-project/ folder), the two-lane socket dispatch procedure (MemAcc ADR 0010 leases), and the no-sudo measurement protocol. Load before SSHing to mbit10, capturing a machine record, or running any profile there. The always-on rules live in .claude/rules/remote_server.md.
---

# mbit10 — Procedures

Adapted 2026-09-22 from the owner's MemAcc `remote-mbit-runs` skill; MemAcc-only
recipes (LLVM bridge, Kokkos, LACT, mbit9) were left out. Updated 2026-09-29: EvolveSWDB
moved into the ArchEvolve monorepo (`swdb-project/`); the old EvolveSWDB repo is retired.

> Read `.claude/rules/remote_server.md` first. This file is the how-to. Facts below are
> dated; re-check anything a decision depends on.

## Connection check (run first, every time)

```
ssh mbit10 'uptime && df -h /data1 /data | tail -2 && who | wc -l && \
            grep -H "\"state\"" /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json'
```

From this Mac, ssh fails inside the command sandbox (DNS lookup is blocked); run it with
the sandbox disabled. Then, in the checkout you will use:
`git rev-parse --abbrev-ref HEAD && git rev-parse HEAD`.

## Host facts (checked 2026-09-22)

- Intel Xeon Gold 6326 (Ice Lake-SP), 2 sockets × 16 cores × 2 threads = 64 CPUs;
  2 NUMA nodes, **node 0 = even CPUs, node 1 = odd CPUs**. L1d 48 KiB and L2 1.25 MiB per
  core; L3 24 MiB per socket. 125 GB RAM. Ubuntu 24.04, kernel 6.8. Also has one NVIDIA
  RTX A6000 (not used by EvolveSWDB yet).
- Toolchain: gcc/g++ 13.3 on PATH; clang 18.1.8 only at `/data1/yanruj/llvm18/bin`;
  cmake 3.26; git 2.48; no ninja. System `python3` 3.12.3 already has PyYAML 6.0.1 and
  jsonschema 4.10.3, which is all `swdb` needs. No conda/uv.
- **Counters: unavailable.** `perf_event_paranoid` = 4 blocks every perf event, even
  `task-clock`. VTune 2025.1 is at `/opt/intel/oneapi/vtune/latest/bin64/vtune`, but
  hardware sampling needs the `vtune` group, which `yanruj` is not in. No likwid, PAPI,
  or pcm.
- **Counter-free tools that work:** valgrind 3.22 (`cachegrind --cache-sim=yes` uses the
  host's L3 as its last level; callgrind, lackey, dhat, massif also installed),
  `/usr/bin/time`, `strace`, `ltrace`. Not installed: DynamoRIO, Pin, SDE (DynamoRIO can
  be unpacked from its GitHub release into `/data1/yanruj/` without sudo).
- GitHub: the key `~/.ssh/github_memacc` authenticates as `ruchou` and can clone and
  fetch `petecao/ArchEvolve` over SSH (verified 2026-09-29). The ArchEvolve checkout is
  `/data1/yanruj/ArchEvolve` (cloned 2026-09-29).

## Disks

| Mount | Size | Rule |
|---|---|---|
| `/` (holds `$HOME`) | 439 G | runs near-full; write nothing here |
| `/data1` | 1.8 T | repos, builds, toolchains, and run output (24 G free on 2026-09-22) |
| `/data` | 1.8 T | overflow for run output when `/data1` has under 20 G free |

## Clone and sync ArchEvolve

```
cd /data1/yanruj && git clone git@github.com:petecao/ArchEvolve.git   # first time
cd /data1/yanruj/ArchEvolve && git fetch && git checkout <commit-or-yanrujhou_main>
cd swdb-project && python3 -m swdb validate
```

Code only arrives by git. Never edit records on the host and copy them back by hand;
commit on the host and push, or regenerate on the Mac.

## Two-lane dispatch (MemAcc ADR 0010)

At most two jobs at once, one per socket.

1. **Check both lanes and the legacy lease:**
   `grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json`.
   A held `mbit10-evaluation-node<N>` makes node N busy; a held legacy
   `mbit10-evaluation` occupies a socket without excluding a socket lease.
2. **Confirm the lane script** in an up-to-date Memacc checkout
   (`/data1/yanruj/Memacc`): after `git fetch`, compare
   `AgenticRefiner/scripts/host/socket_lane.sh` with the current branch's version.
3. **Dispatch** from that checkout's `AgenticRefiner/`:
   ```
   bash scripts/host/socket_lane.sh <node> <job-name> [--record <path.json>] -- \
        bash -c 'cd /data1/yanruj/ArchEvolve/swdb-project && <command>'
   ```
   It re-runs itself under `numactl --cpunodebind=<node> --membind=<node>`, takes the
   socket lease, records affinity, load, and policy, then runs the command. Options:
   `--record <path.json>`, `--no-align`, `--max-cell-age-s <s>` (default 900),
   `--load1-max <x>` (default 32), `--lease-timeout-s <s>` (default 600). Exit codes:
   the command's own; 2 bad arguments; 4 lease refused; 5 load gate refused.
4. **Alignment:** by default the script starts a job only within 15 min after a batch
   cell in the other lane starts, or when no batch runs. Use `--no-align` only when the
   other lane is idle.
5. Threads: at most 16 per job (one socket, no hyperthreads).

## Measurement protocol (no sudo)

Before every run, record into the run folder:
`uptime`, `who | awk '{print $1}' | sort -u`, `df -h /data1 /data`,
`cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`,
`cat /sys/devices/system/cpu/intel_pstate/no_turbo`, `lscpu`, `numactl --hardware`,
`uname -a`, `git rev-parse HEAD`, and start and end times.

- Run inside a named `tmux` session so a disconnect does not kill the job.
- Wrap every run in `timeout`.
- Raw output goes to `/data1/yanruj/EvolveSWDB_runs/<run-id>/` (or `/data/...`, see the
  rules), never into the repo, `$HOME`, `/tmp`, or `/var/tmp`.
