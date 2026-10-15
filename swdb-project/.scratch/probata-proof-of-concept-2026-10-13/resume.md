# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Checkpoint: `codex/probata-poc-integration` starts at `150930b4` on `yanrujhou_main`.
The integration source is pushed. User approval covers scoped implementation, commits,
pushes, remote source synchronization and two mbit10 CPU lanes.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 24 | Coordinator; reproduce construct-group WP acceptance | Baseline node 1 stopped at seed: LLVM 22 needs its GCC 13 C++ header path. Diagnose one failure before rerunning. Keep inheritance and `omp simd` excluded as the declared subset requires. |
| 25 | `codex/probata-t25`; recover models without changing the old worktree | Preserve `--model` / `c_model` / `pins.models`; test real CBMC stale-pointer refutations. WP lifetime modeling remains an acceptance gap. |
| 27 | `codex/probata-t27`; restore WP semantics and store cases | mbit10 node 0, tmux `probata-t27`, output `/data/yanruj/EvolveSWDB_runs/probata-t27-20261015/initial`. |
| 41 | `codex/probata-t41`; apply recorded fix (a), independently review | Initial fix compiles; review is testing a residual class-change counterexample. Do not approve a known-false statement or unblock 42. |

Blockers: WP 33 does not implement deallocation, so the old read-after-delete expected
failure cannot support a completed ticket. Affected proofs must fail closed until a
validated lifetime model exists. Ticket 41's theorem remains open to counterexamples;
Rocq type checking and sanity lemmas do not prove it.

Next action: finish the active acceptance runs and review, merge each verified change,
then recompute the ready frontier from the ticket files. No held-out kernel work or
method freeze is authorized by an incomplete acceptance run.

## Host coordination

Live preflight on 2026-10-15 ET found both socket leases and the legacy lease released,
low CPU activity, about 118 GiB available RAM, 18 GiB free on `/data1` and 97 GiB on
`/data`. These are dispatch observations, not permanent availability claims. New output
uses `/data/yanruj/EvolveSWDB_runs/`; source uses Git worktrees under `/data1/yanruj/`.
The current lane wrapper is in `/data1/yanruj/Memacc-evolveswdb-lane`, verified against
`origin/yanrujhou_main`. The older `/data1/yanruj/Memacc` checkout lacks it and has unrelated
changes; leave that checkout untouched. GPU NVML reports a driver/library mismatch;
CPU proofs do not require the GPU.

Node 1 baseline run: `/data/yanruj/EvolveSWDB_runs/probata-t24-baseline-20261015`, source
`150930b4`, lease generation 591. It exited after fixture setup errors, before proving
the construct groups. The first error is missing `<cstddef>`, not a proof failure.
Output budget was 6 GiB; measured output was 2.4 MiB. Retain original logs and reports
until the diagnosis and acceptance readers finish.

The 30-minute progress heartbeat is `probata-implementation-progress`; its reports do
not substitute for reading incremental run artifacts.
