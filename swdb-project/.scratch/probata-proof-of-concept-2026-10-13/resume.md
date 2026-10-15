# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Runtime checkpoint: integration `3f177e63` on `codex/probata-poc-integration`,
based on `yanrujhou_main` at `150930b4`, pushed and clean before the current acceptance handoffs.
Includes lowerer 9's integer result normalization, private-vector ownership,
mandatory `-wp-no-filter-init`, checked `at()` view, named DX100 initialization,
and conservative typed array-origin refusal. Explicit entry-domain declarations,
mathematical bindings and checked WP operation admission are integrated. Entry windows
are conditional typed input-contract premises; WP checks numerical bounds, target byte
capacity and operations. It does not establish complete typed-domain realizability.
Closed owner views independently check source origins, statement/access inventories,
guards and annotation admission; generic model fields remain unsupported.
Bounded domain planning and imported-domain stub refusal are integrated. The isolated
root branch has checked primitive CBMC execution at frozen `07a9a299`: five remote
controls pass in 189.77 seconds, including actual source C++ replay of both numerical
negatives. Its independently reviewed source-name fix and 40 component checks pass;
the corrected source has not yet been merged into integration. Crux fallback
initializedness/source admission is a separate active follow-up.
User approval covers scoped implementation, commits, pushes, remote source sync,
two mbit10 CPU lanes and BFS proof-workspace export through Codex/OpenAI.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Run 17 ended unproven at 08:25:15 ET, frozen `af9a61b6` | 53.48 counted minutes, 38 hints, 270 goals, 2 unit and 17 hint goals open; no final proof/smoke replay. All 13 preflight source pins match the clean worktree. Audit before choosing any later method. [Final evidence](evidence/t07-counted-17.json). |
| 24 | Focused model-result fix integrated | Four public positive callers and missing-input negative pass; remote native checkpoint passes 132 checks in 69.36 seconds at `aa7be61c`; combined-source full constructs await final origin policy. |
| 25 | Remote owner 16/16 audited; qualified `at()` actual pair passes | Original safe: 119 ordinary goals plus 11 smoke passes; stale's sole open goal is alias liveness. New pair at `3f177e63`: safe 121/121 ordinary plus 11 smoke; missing bounds 105/106 ordinary plus 11 smoke, sole open `owner_at_guard_1`. General model/member lifetime acceptance remains open. |
| 27 | Frozen DX batch 13 pass, 1 strict smoke failure | Stream/three-read positives and intended negatives/refusals pass. Offset-gather positive fails the introduced constant normalization branch smoke. Literal-only folding and stronger all-import/state-name bindings are under replay. Helper expansion has 53 component controls; adapter admission and nested ordinary reads remain pending. |
| 36 | WP entry 15/15 audited; primitive CBMC 5/5 at `07a9a299` | Typed windows remain conditional premises. Primitive CBMC checks exact original and lowered views, frozen extents and all mathematical intermediates; two negatives replay on C++. Other domain routes stay closed. Global snapshot binding regression repaired before integration; Crux source admission is being aligned. |
| 41 | Resolved | Approved reconstruction `e23f3715…`, protected/class/ownership lifetime premises and exact guard controls. |
| 42 | Resolved | Production Rocq composition theorem: 209 Qed, closed context, actual record validate/build; no DX100 reduction claim. |

Current count: **32 of 63 resolved**, five claimed. Drafts 1 and 2 are immutable;
reviewed combined identities will create draft 3. No current pointer source or
full construct acceptance is inferred from older checkpoints. Ticket43 remains
blocked by 29; 28 remains unclaimed until 27 closes. No held-out kernels or method
freeze before their dependencies resolve.

Next: finish conservative admission and actual acceptance, merge verified changes,
recompute the ticket frontier and use the two leased remote socket lanes.

## Host coordination

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
