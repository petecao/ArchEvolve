# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Checkpoint: integration `codex/probata-poc-integration`, based on `yanrujhou_main`
`150930b4`; production composition record at `3793deba`, prototype guard at `3db8002c`,
initialization policy/strict TSV reader merged at `d04193c1`, doc follow-up `f66bf568`.
User approval covers scoped implementation, commits, pushes, remote source sync and
two mbit10 CPU lanes; the specific BFS-to-Codex/OpenAI export approval also covers 07.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Counted run 14 active from 03:33:40 ET | Fresh hints, repaired guard and abstract partial-chunk guidance; frozen `05e81eac`; output `/private/tmp/probata-t07-20261015-run14/`. Run 13 remains failed. |
| 24 | Construct-group WP acceptance | Remote baseline 17 passed, 1 known UAF xfailed; three lifetime refusal controls pass. Positive safe deallocation remains expected-failing pending checked terminal-release integration. |
| 25 | Narrow checked terminal release; general lifetime still open | Worktree `/private/tmp/probata-lifetime-narrow`. Public WP acceptance pending. General aliases, moves and dangling-pointer semantics remain unresolved; WP initializedness support exists but requires an additional RTE selector. |
| 27 | Store/capacity acceptance and CPU-access admission | Node 0 frozen `dd975e72`: all six targeted cases passed in 3291.80 s. Add checked CPU/device memory interference and explicit initializedness before final two-lane acceptance. |
| 36 | Strict preflight and reader; waits for 27 | Shift/trigraph controls pass. New strict multiline TSV reader and initialization policy: 121 focused tests passed; current checker `48a828aa…`. Draft 2 keeps its historical pin. |
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

The 2026-10-15 03:30 ET report covered every active ticket and both lanes; next report is
due around 04:00 ET. Counted hint run 13 ended with 19 goals open and is not proven. Node 0 holds
the targeted semantics replay; node 1's generation 594 was released at 06:12:13 UTC.

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
