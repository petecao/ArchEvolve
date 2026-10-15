# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Checkpoint: `codex/probata-poc-integration` starts at `150930b4` on `yanrujhou_main`;
ticket 25 is merged at `cd610c86`, WP semantics are staged at `a41bcd39`, and the latest
ownership-lifetime statement repair is merged at `3f559789`.
The integration source is pushed through `3f559789`. User approval covers scoped implementation, commits,
pushes, remote source synchronization and two mbit10 CPU lanes.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Coordinator; counted run 13 | Started 2026-10-15 01:45 ET, `/private/tmp/probata-t07-20261015`; unchanged run-10 method and pinned Codex, fresh hints, verified no-hint baseline reused. User explicitly approved this scoped BFS source export. |
| 24 | Coordinator; reproduce construct-group WP acceptance | Node 1 baseline `r4` completed: 17 passed, 1 xfailed in 1823.04 s, source `150930b4`. New lifetime safety controls: 3 passed; positive safe-deallocation acceptance is still expected-failing. Keep inheritance and `omp simd` excluded as the declared subset requires. |
| 25 | Model recovery merged; ticket remains claimed | 65 lowering tests, 6 bounded model tests, pair constructor WP proof, matching-library admission and mismatch refusal pass. WP lifetime modeling remains an acceptance gap. |
| 27 | `codex/probata-t27`; restore WP semantics and store cases | Node 0 replays source `d45a63d8` with an explicit checked ghost frame bound. The exact-index frame and a checked index assertion timed out. Capacity and insufficient-bound controls run with the safe cases. Output `/data/yanruj/EvolveSWDB_runs/probata-t27-20261015/`. |
| 36 | `codex/probata-t36`; proof setup checks | Review found solver-order pinning must be exact; dependency provenance is being added to classify partial properties without accepting them as proofs. Resolution still depends on 27. |
| 41 | Resolved; agent review and approval under delegation | Protected reads, read-class lifetime and ownership-handoff checks; regression lemmas and exact statement guard pass. The theorem remains open. |
| 42 | `codex/probata-t42`; proof resumed | Approved reconstructed statement `e23f37153fadb8c3307384b4ec074422e0af6ebc121ff673688b6d321485e513`; original 122 lemmas plus additional latest-read and swap-safety lemmas checked; full theorem unchecked. |

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
and runtime-library configuration. No cross-library model agreement is inferred. The final
baseline `r4` completed with 17 passed and the known use-after-delete expected failure;
the original report and logs occupy 9.7 MiB and remain on the host.

The 30-minute progress heartbeat is `probata-implementation-progress`; its reports do
not substitute for reading incremental run artifacts.

## Validation and progress reporting

The 2026-10-15 02:01 ET report covered every active ticket and both lanes; next report is
due around 02:31 ET. Counts are observations of incremental reports, not completed suites.

The early structural run disabled clang as well as WP/CBMC; four formal-frame assertions
therefore failed for the wrong tool configuration. One isolated failure passes with clang
restored, and the affected module gives 64 passed, 4 skipped (WP still disabled). A separate
checkout-integrity failure observed the coordinator's Rocq merge, not a test mutation.
That exact test passes in `/private/tmp/probata-validation-20261015` at frozen `3f559789`.
Future validation runs must use an unchanged source worktree. Logs and incremental reports:
`/private/tmp/probata-integration-20261015/`. No whole-catalog validation is claimed.
