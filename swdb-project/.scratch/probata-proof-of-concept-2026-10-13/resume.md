# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Checkpoint: `codex/probata-poc-integration` starts at `150930b4` on `yanrujhou_main`;
ticket 25 is merged at `cd610c86` and ticket 41 at `a65e8cb1`.
The integration source is pushed through `cd610c86`. User approval covers scoped implementation, commits,
pushes, remote source synchronization and two mbit10 CPU lanes.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Coordinator; counted run 13 | Started 2026-10-15 01:45 ET, `/private/tmp/probata-t07-20261015`; unchanged run-10 method and pinned Codex, fresh hints, verified no-hint baseline reused. User explicitly approved this scoped BFS source export. |
| 24 | Coordinator; reproduce construct-group WP acceptance | Node 1 baseline `r4` is active after isolated C++ differential passes. Keep inheritance and `omp simd` excluded as the declared subset requires. |
| 25 | Model recovery merged; ticket remains claimed | 65 lowering tests, 6 bounded model tests, pair constructor WP proof, matching-library admission and mismatch refusal pass. WP lifetime modeling remains an acceptance gap. |
| 27 | `codex/probata-t27`; restore WP semantics and store cases | mbit10 node 0, tmux `probata-t27-frame`, output `/data/yanruj/EvolveSWDB_runs/probata-t27-20261015/frame-fix`; corrected missing ghost assignments before acceptance. |
| 36 | `codex/probata-t36`; proof setup checks | Implement independent check machinery while 27 acceptance is running; resolution still depends on 27. |
| 41 | Resolved; agent review and approval under delegation | Protected reads and read-class lifetime checks; four Rocq regression lemmas, exact statement guard and changed-hypothesis refusal pass. The theorem remains open. |
| 42 | `codex/probata-t42`; proof resumed | Approved reconstructed statement `ffb5bda714b9fce5a13927a4860f6c85438821cdcdf3b4f1560f26a91eefd4f4`; 122 existing lemmas retained, full theorem unchecked. |

Blockers: WP 33 does not implement deallocation, so the old read-after-delete expected
failure cannot support a completed ticket. Affected proofs must fail closed until a
validated lifetime model exists. Ticket 41's revised statement has no counterexample from
the final local review; Rocq type checking and sanity lemmas do not prove its theorem.

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

The baseline's isolated reruns diagnosed both the missing C++ header path and linker
path. `r4` supplies `SWDB_CLANG` with GCC 13, `CPLUS_INCLUDE_PATH` and `LIBRARY_PATH`;
the isolated native C++ versus C class fixture passes before the full WP module starts.
These generic subset fixtures use libstdc++; they are not vector-model evidence.
Vector-model admission now requires matching libc++ 22.1.8. The remote LLVM distribution
has matching headers and libraries, but its model jobs need an explicit libc++ compiler
and runtime-library configuration. No cross-library model agreement is inferred.

The 30-minute progress heartbeat is `probata-implementation-progress`; its reports do
not substitute for reading incremental run artifacts.
