# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Runtime checkpoint: integration `b876dcb3` on `codex/probata-poc-integration`,
based on `yanrujhou_main` at `150930b4`, pushed and clean before the 07:49 ET remote dispatch.
Includes lowerer 9's integer result normalization, private-vector ownership,
mandatory `-wp-no-filter-init`, checked `at()` view, named DX100 initialization,
and conservative typed array-origin refusal. Explicit entry-domain declarations,
mathematical bindings and checked WP operation admission are integrated. Entry windows
are conditional typed input-contract premises; WP checks numerical bounds, target byte
capacity and operations. It does not establish complete typed-domain realizability.
Closed owner views independently check source origins, statement/access inventories,
guards and annotation admission; generic model fields remain unsupported.
Bounded domain planning is integrated with execution and imported-domain stub refusal.
Latest compact merged validation: 45 checks pass; report
`/private/tmp/probata-bounded-planner-merged-static-20261015.jsonl`.
User approval covers scoped implementation, commits, pushes, remote source sync,
two mbit10 CPU lanes and BFS proof-workspace export through Codex/OpenAI.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Run 17 active from 07:31:46 ET, frozen `af9a61b6` | Fresh hints, consumed-prefix/cursor guidance, total-open-goal acceptance and no phase lock. Run 16 ended unproven with 4 unit and 22 hint goals; its final audit is recorded. New output `/private/tmp/probata-t07-20261015-run17/`, with preflight manifest and launch metadata. |
| 24 | Focused model-result fix integrated | Four public positive callers and missing-input negative pass; remote native checkpoint passes 132 checks in 69.36 seconds at `aa7be61c`; combined-source full constructs await final origin policy. |
| 25 | Current-source remote owner suite: 16 controls pass | Source `b876dcb3`, node 1 generation 595, 429.57 seconds. Actual safe/stale records are under audit. General member/model and lifetime acceptance remains open; opaque model buffer arithmetic remains refused pending exact field/ownership domains. |
| 27 | Direct stream WP proof passes; remaining controls underway | First direct stream proof: 155.85 seconds, 44 scheduled goals. Exact callee/producer binding and mutation controls remain in progress. Annotation-free helper contextual cloning is the next narrow frontier; original helper and nested ordinary reads stay closed until checked. Older initializedness results remain checkpoint evidence. |
| 36 | Current-source remote entry-window suite: 15 controls pass | Source `b876dcb3`, node 0 generation 551, 616.97 seconds. Five positive proofs, five intended numerical negatives and five prelaunch refusals; all referenced evidence hashes match. Conditional typed-window and bounded planner-only boundaries remain explicit. Allocation-block bounds cannot establish 2D row provenance. |
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

Latest readback at 2026-10-15 08:03 ET found both socket leases and the legacy lease
released, with load 0.10/0.76/0.86, 21 GiB free on `/data1` and 97 GiB on `/data`.
The frozen detached evaluation checkout is `b876dcb3`. Its two proof jobs started
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

The 2026-10-15 08:05 ET report covered every active ticket and both lanes; next report
is due around 08:35 ET. Run 15 ended not proven after 52.75 counted minutes with 1 unit
and 24 hint obligations open; no final proof replay ran. Run 16 also ended unproven
with 4 unit and 22 hint goals; its final offline audit is recorded. Run 17 started
at 07:31:46 ET with a distinct consumed-prefix method and fresh hints.
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


Live host check 2026-10-15 03:25 ET: node 0 generation 548, node 1 generation 594
and legacy generation 77 all released; load 0.02/0.38/0.80, `/data1` 21 GiB free,
`/data` 97 GiB free. Root remote checkout is `yanrujhou_main` at `680298a3`;
it is not the frozen evaluation worktree. Both evaluation lanes await final source.
The frozen policy worktree's representative existing safe-fill and smoke-pair WP
regressions also passed: 2 tests, 139.41 s, `/private/tmp/probata-init-wp-regression.jsonl`.
