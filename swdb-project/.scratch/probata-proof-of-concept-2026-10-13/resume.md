# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Updated: 2026-10-15 10:49 ET. Integration checkpoint `f389beb1` includes checked
helper and source-summary admission, based on `yanrujhou_main` at `150930b4`.
Declaration-attribute, qualified copy-body and nested-read changes are under
independent integration review. The standard-source gate branch is at `00b16733`,
with 20 focused offline and four prelaunch controls passing; its actual WP
current-owner/stale-alias pair passed at 10:53 ET (2 tests/243.20s, peak651MiB).
[Gate evidence](evidence/stdlib-source-provenance-20261015.json).

| Ticket | Current evidence | Next action |
|---|---|---|
| 07 | Run18 finished unproven at 10:43 ET; 20 open goals (13 unit/7 hint), 51.76 counted minutes, no final proof/smoke | Audit negative outcome and remaining induction goals; retain prototype/RTE scope boundary |
| 24 | Remote constructs stopped at opaque copy origin: 5 passed/1 failed; qualified copy body passes locally with 36 ordinary/7 smoke goals | Review repair and discharge caller typed range/capacity |
| 25 | Original-TU standard-source gate passes 24 focused controls; actual safe/stale pair passed | Integrate accepted gate and continue vector/pair pipeline |
| 27 | Remote entry/helper shard passes 17/17; original nested three-read actual proof passes | Integrate independently checked nested view, then combined acceptance |
| 36 | 43 remote records audited, all referenced hashes match; nested closure/capture hardening reviewed | Compose setup/source/checker unions and replay combined source |

**32 of 63 resolved; five claimed.** Drafts 1/2 remain immutable; draft 3 is not
created. Ticket 28 remains gated by 27; 43 remains blocked by 29. Held-out kernels
and method freeze remain gated by dependencies. Existing user authorization covers
implementation, commits/pushes, two remote lanes and scoped BFS source export.
Last 30-minute status table 10:35 ET; next due 11:05 ET.

## Host coordination

Live readback: 2026-10-15 10:49 ET. Both socket leases (node 0 generation 556,
node 1 generation 597) and legacy generation 77 are released. Load0.32/0.07/0.30;
21 GiB free on `/data1`, 97 GiB on `/data`. Evaluation checkout remains clean
detached `1ece49b8`. The completed 09:57 ET jobs produced 43 retained proof records
with matching artifact hashes: node 1 entry/helper **17 passed/1428.35s**; node 0
constructs **5 passed/1 failed/1268.59s**, stopped before WP on the opaque copy
model. Raw outputs remain remote for coordinator, ticket acceptance and independent
audit readers, each below its 2 GiB budget. Recheck all leases, activity and disks
before dispatching the next frozen combined checkpoint.
[Compact audit](evidence/helper-construct-mbit10-20261015.json).

Historical completed checkpoint:

Latest audited readback: 2026-10-15 09:51 ET. Both socket leases and legacy lease
released; load 0.02/0.25/0.52, 21 GiB free on `/data1`, 97 GiB on `/data`.
Evaluation checkout is clean detached `fddb1462`. Node 0 native job ended 09:35 ET;
node 1 bounded/source-summary job ended 09:42 ET, both exit 0. Their outputs use
14.2 MiB and 28.3 MiB, each below its 2 GiB budget. Raw output remains remote for
coordinator/ticket acceptance and independent audit readers. Recheck live leases,
load and disks before any dispatch; this is a timestamped observation.
[Compact audit](evidence/summary-source-binding-mbit10-20261015.json).

Historical host observations follow.

Latest live readback: 2026-10-15 09:00 ET. Node 0 generation 554, node 1 generation 595
and legacy generation 77 were released; load 0.00/0.02/0.14, 21 GiB free on `/data1`
and 97 GiB on `/data`. Evaluation checkout remained clean detached `07a9a299`.
No proof process appeared in the top CPU inventory. Recheck all leases and load
before either lane is used; this is a timestamped observation.

Latest readback at 2026-10-15 08:38 ET found both socket leases and the legacy lease
released, with load 0.38/0.68/0.61, 21 GiB free on `/data1` and 97 GiB on `/data`.
The frozen detached evaluation checkout is `07a9a299`. Corrected bounded controls
ran on node 0 generation 554 from 08:33:38 to 08:36:48 ET: five passed in 189.77
seconds, wrapper exit 0. Actual proof records show one positive, two intended
refutations replayed on source C++, and one prelaunch mathematical-intermediate
refusal; the fifth test covers source-name collision. All referenced artifact
hashes match. [Bounded evidence](evidence/bounded-entry-windows-mbit10-20261015.json).
Earlier `a3bd6c9a`/`ca6d7ae5` bounded checkpoints preceded the source-name fix;
the corrected-source replay is the acceptance checkpoint.

Earlier `b876dcb3` proof jobs started
at 07:49:32 ET: entry windows on node 0 generation 551 passed 15 tests in 616.97
seconds and released at 07:59:50 ET; owners on node 1 generation 595 passed 16 tests
in 429.57 seconds and released at 07:56:43 ET. Both wrappers exited 0. Compact entry
record audit: [entry-windows-mbit10-20261015.json](evidence/entry-windows-mbit10-20261015.json).
Raw output remains on mbit10; coordinator and ticket acceptance readers still need it.
This snapshot is not a promise of later lane availability; recheck before dispatch.

Earlier native preflight at 2026-10-15 07:14 ET found both socket leases and the legacy lease released,
load 0.11/0.29/0.19, 21 GiB free on `/data1` and 97 GiB on `/data`. The wrapper was fetched
and matched blob `261e7e04a64474020c6d2fd288bee9bab8dd1f5d`. Frozen native replay
`aa7be61c` then passed 132 checks in 69.36 seconds on node 0, generation 550, ending at 07:16 ET.
Its lease is released; node 1 generation 594 and legacy generation 77 remain released in that snapshot.
That native replay used a clean detached checkout at `aa7be61c`; it was subsequently
advanced to `b876dcb3` only after the job ended. The original replay used GNU headers and failed 21 of 133 checks;
matching libc++ 22.1.8 plus GCC 13 driver wrappers fixes configuration; the corrected
raw-endpoint expectation accounts for the remaining test. The corrected native shard
excludes the accidentally selected CBMC query. See ticket 24's native evidence;
this does not establish final proof acceptance. These are dispatch observations,
not permanent availability claims. New output
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

The 2026-10-15 08:35 ET report covered every active ticket and both lanes; next report
is due around 09:05 ET. Run 15 ended not proven after 52.75 counted minutes with 1 unit
and 24 hint obligations open; no final proof replay ran. Run 16 also ended unproven
with 4 unit and 22 hint goals; its final offline audit is recorded. Run 17 finished
at 08:25:15 ET with 2 unit and 17 hint obligations open; no final proof replay ran.
Both remote proof shards completed at `b876dcb3`; the next combined DX/helper/model
checkpoint and final method identities remain pending. The 132-case native checkpoint
passed separately.

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


Historical host snapshot 2026-10-15 03:25 ET: node 0 generation 548, node 1 generation 594
and legacy generation 77 all released; load 0.02/0.38/0.80, `/data1` 21 GiB free,
`/data` 97 GiB free. Root remote checkout is `yanrujhou_main` at `680298a3`;
it is not the frozen evaluation worktree. Both evaluation lanes await final source.
The frozen policy worktree's representative existing safe-fill and smoke-pair WP
regressions also passed: 2 tests, 139.41 s, `/private/tmp/probata-init-wp-regression.jsonl`.
