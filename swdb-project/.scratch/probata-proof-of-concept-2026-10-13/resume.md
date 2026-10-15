# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Checkpoint: reviewed integration source `6497f4f8` on `codex/probata-poc-integration`,
based on `yanrujhou_main` at `150930b4`. It includes lowerer 7's checked copies,
initialized WP fixtures, signed native footprint queries, distinct bounded tile objects,
mandatory CBMC pointer checks and the reader dependency hash closure.
User approval covers scoped implementation, commits, pushes, remote source sync and
two mbit10 CPU lanes; the specific BFS-to-Codex/OpenAI export approval also covers 07.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Counted run 15 active from 04:47:30 ET | Fresh hints plus abstract chunk and postcondition-scope guidance; frozen `de78b7c6`; output `/private/tmp/probata-t07-20261015-run15/`. Run 14 failed with 14 hint goals open; its finite false-assertion audit is retained. |
| 24 | Construct-group WP acceptance | Class positive/seeded-bug pair passes; positive has 153 valid recorded goals including 11 smoke checks. Template positive also proves on lowerer 7. Full 44-case combined-source replay awaits node 1 after unsafe semantics checks. |
| 25 | Lowerer 7 merged; bounded std restoration being combined | Original five bounded std jobs pass, including replayed stale-pointer refutations; 12 admission refusals pass. Lowerer 8's combined checks are running. General vector lifetime in WP remains unresolved. |
| 27 | Final source and two-lane acceptance | Local-storage and signed-query repairs are merged. Safe shard collects 133 cases, unsafe 12. Actual WP initialized-read and tile-extent diagnostics precede dispatch; older successful replays do not close current acceptance. |
| 36 | Pointer checks and reader closure merged | 80 focused tests and 14 post-merge controls pass. WP tile-boundary and discarded-pointer controls are being classified separately; an initialization failure must not mask a missing extent check. Draft 2 remains unchanged. |
| 41 | Resolved | Approved reconstruction `e23f3715…`, protected/class/ownership lifetime premises; exact guard and sanity controls pass. |
| 42 | Resolved: production Rocq-checked theorem | `proof.probata.composition.20261015-a1`, 209 Qed, closed global context, actual record validate/build pass; 9 final integrated tests passed. About 491.2 MiB peak. |

Current count: **32 of 63 resolved**, five claimed. Draft 2 is immutable after an
actual proof record pinned it; new lowerer or policy identities require draft 3.
Ticket 43 remains blocked by 29. Ticket 28 research is available in
`/private/tmp/probata-t28-research/PLAN.md`; it has not been claimed before 27 closes.
Research identifies source-inferred full-cache-line interference and ready-query
progress gaps, not a replayed gem5 counterexample. The adapter must refuse ordinary
memory cases it cannot check rather than assume their preservation.

Next: finish acceptance and conservative admission, merge verified changes, recompute
frontier. No held-out kernel work or method freeze before its dependencies resolve.

## Host coordination

Live preflight at 2026-10-15 04:56 ET found both socket leases and the legacy lease released,
load 0.00, no proof jobs, about 117 GiB available RAM, 21 GiB free on `/data1` and 97 GiB on
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

The 2026-10-15 05:00 ET report covered every active ticket and both lanes; next report is
due around 05:30 ET. Run 14 ended unproven after 53.32 counted minutes with 14 hint
obligations open; no final proof replay ran. Run 15 is active on fresh hints. Both
remote evaluation lanes await the final combined source and method checkpoint.

The early structural run disabled clang as well as WP/CBMC; four formal-frame assertions
therefore failed for the wrong tool configuration. One isolated failure passes with clang
restored, and the affected module gives 64 passed, 4 skipped (WP still disabled). A separate
checkout-integrity failure observed the coordinator's Rocq merge, not a test mutation.
That exact test passes in `/private/tmp/probata-validation-20261015` at frozen `3f559789`.
Future validation runs must use an unchanged source worktree. Logs and incremental reports:
`/private/tmp/probata-integration-20261015/`. No whole-catalog validation is claimed.

The early structural run completed: 424 passed, 31 skipped, 6 failed and 1 teardown error
in 1441.73 s. Four failures are the corrected clang configuration above; the two format
failures are covered by ticket 36's passing documentation checks. The teardown error is
the independently passing frozen-worktree replay above. This is diagnostic evidence,
not a clean final integrated-source suite.


Live host check 2026-10-15 03:25 ET: node 0 generation 548, node 1 generation 594
and legacy generation 77 all released; load 0.02/0.38/0.80, `/data1` 21 GiB free,
`/data` 97 GiB free. Root remote checkout is `yanrujhou_main` at `680298a3`;
it is not the frozen evaluation worktree. Both evaluation lanes await final source.
The frozen policy worktree's representative existing safe-fill and smoke-pair WP
regressions also passed: 2 tests, 139.41 s, `/private/tmp/probata-init-wp-regression.jsonl`.
