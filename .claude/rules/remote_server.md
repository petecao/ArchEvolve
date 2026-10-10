# Lab Hosts (mbit10) — Rules

Adapted 2026-09-22 from the owner's MemAcc rules for EvolveSWDB. Updated 2026-09-29:
EvolveSWDB now lives in the ArchEvolve monorepo as `swdb-project/`.

> **Scope: durable rules only.** Volatile state (free space, leases, load, which branch
> a checkout holds) is read from the host, never recorded here.
>
> **Procedures:** the `mbit10-runs` skill (`.claude/skills/mbit10-runs/SKILL.md`). Load
> it before any work on mbit10.

## Hosts

| | mbit10 | mbit9 |
|---|---|---|
| Role | **the only lab host for EvolveSWDB** | frozen for another project; do not use |
| SSH | alias `mbit10` (`mbit10.eecs.umich.edu`), user `yanruj` | — |
| Work root | `/data1/yanruj/` — **never `$HOME`** | — |
| ArchEvolve clone | `/data1/yanruj/ArchEvolve` (work in `swdb-project/`, branch `yanrujhou_main`) | — |

The two hosts are separate machines with separate disks; nothing crosses except by git.

## mbit10 two lanes (MemAcc ADR 0010)

**At most two measurement jobs at once, one per socket. Never a third.**

- A lane is one socket plus its lease `mbit10-evaluation-node<N>`. The lease is the only
  mutual exclusion. Before dispatch, check BOTH socket leases and the LEGACY
  `mbit10-evaluation` lease (it occupies a socket without excluding a socket lease).
- Enter a lane ONLY through MemAcc's `AgenticRefiner/scripts/host/socket_lane.sh`, in an
  up-to-date Memacc checkout on mbit10. An old checkout can hold a stale copy; compare
  it with the repository version first. Never run a multi-threaded job unconfined.
- Other users' jobs (and a LACT batch in the other lane) share the OS, the memory link
  between sockets, and anything left unconfined. Record the load with every run.

## Disks and output

- `/` holds `$HOME` and runs near-full. Write nothing there (no caches, no builds).
- Repos, builds, and toolchains live under `/data1/yanruj/`. Raw run output goes to
  `/data1/yanruj/EvolveSWDB_runs/`, or to `/data/yanruj/EvolveSWDB_runs/` when `/data1`
  has under 20 GB free or the planned run would push it there. The profile record names
  the folder actually used.
- **Run `df -h /data1 /data` before any large run.** Identify disks by mount point,
  never by `sdX` letter (letters change across reboots).
- Raw run output never goes into the git repo and is never copied to the Mac.

## Constraints

- Shared lab host (UMich EECS, Mahlke group) with many accounts; others' jobs perturb
  measurements. **No sudo:** no governor, turbo, `drop_caches`, frequency pinning, or
  system packages. Reproducibility comes from recording the environment per run.
- Hardware counters are unavailable to `yanruj` (checked 2026-09-22:
  `perf_event_paranoid` = 4, not in the `vtune` group). Profiling is counter-free until
  that changes; re-check before assuming either way.
- The Mac is aarch64 and mbit10 is x86_64. Never compare measurements across them.

## Code sync

- git only. Push from the Mac, then `git fetch && git checkout` on mbit10. Never rsync
  builds or binaries.
- Never assume which commit a checkout holds: run `git rev-parse --abbrev-ref HEAD` and
  `git rev-parse HEAD` after every connection, and record the commit in each profile.
- Never pull into a checkout while a measurement from it is running.
- Never build with `-j$(nproc)` on the shared host; cap parallel jobs (for example `-j8`).
