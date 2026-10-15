# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Updated: 2026-10-15 ET. **Implementation, evaluation and provider work are paused
by user direction.** Closeout review, documentation, merge and cleanup are still
in progress. Root's bounded final controls at frozen `53471f7f` completed:313 passed,42
deselected in747.43s, no timeout/OOM. This is scoped closeout validation, not a
new evaluation campaign. No implementation agents or
verifier/provider campaigns are assigned. The progress heartbeat is **PAUSED**.
The reviewed docstring-only fix has identical executable AST; final merge and
recovery cleanup are still pending. [Cold-start handoff](HANDOFF.md) and
[all-ticket index](ticket-status-20261015.md) are authoritative resumption pointers.

All 63 ticket files now contain **32 resolved / 31 ready-for-agent / 0 claimed**.
The five unfinished claims (07/24/25/27/36) are released without closing any
acceptance criteria. The dependency frontier is **07, 24, 27**; 25 waits on 24,
36 on 27, and the other 26 open tickets retain their unresolved dependencies.
Drafts 1/2 remain immutable; draft 3 and the final method freeze do not exist.

| Ticket | Retained evidence | Remaining work after resumption |
|---|---|---|
| 07 | Method19 unproven: 27/237 open, 52.04 counted minutes; method20 unlaunched with 158 controls | Reviewed fresh counted run, every goal, final smoke and covering-wait negative; no qualifying BFS proof |
| 24 | Qualified copy and original class safe/negative records; pure condition slice 72 focused controls | Full current-policy construct/dependency acceptance, embedded template-array origins, conditional access placement and broader lifetime coverage |
| 25 | Bounded maximum and matching stale-data/iterator/at source replays accepted | Allocating member bodies, receiver domains and complete WP/bounded agreement; blocked by 24 |
| 27 | Qualified stall at 9940b155: 111 ordinary + 35 smoke checks; distinct query/transitive evidence retained | Full qualified safe/negative, values/register/range/footprint/capacity matrix and verifier agreement |
| 36 | Focused setup/source replay/verdict controls and two-axis review checkpoint | Independent RTE admission check before final freeze, remaining setup criteria; blocked by 27 |

The final review of `53471f7f` against `150930b4` found no new runtime must-fix.
The stale bounded-planner docstring is corrected; the inherited reliance on
method flags for `-wp-rte` is recorded in ticket 36. Current actual methods include
that flag; this is not evidence of a false proof. No flag-policy feature is added
during closeout. Historical actual results are not relabeled as proofs of the
current integrated runtime.

Durable pointers: [review decisions](evidence/final-review-closeout-20261015.md),
[method19 negative audit](evidence/t07-method19-negative-20261015.json),
[unlaunched method20](evidence/t07-method20-prospective-20261015.json),
[class lifetimes](evidence/t24-member-lifetimes-mac-20261015.json),
[condition slice](evidence/t24-condition-closeout-20261015.json),
[vector controls](evidence/t25-next-controls-accepted-20261015.json),
[deferred vector design](evidence/t25-vector-receiver-domain-deferred-20261015.json),
[qualified stall](evidence/t27-stall-qualified-accepted-20261015.json),
[footprint query](evidence/wp-footprint-query-20261015.json).

## Retained host and closeout observations

The observations below are historical, not current lease claims. No further
remote evaluation is scheduled. Root owns final validation, merges and cleanup;
retain raw proof artifacts and recovery inputs until their acceptance/audit readers
finish. Recheck actual host state before any later dispatch.

### Last accepted remote control readback

Both controls at frozen **94769312** completed with zero wrapper exits and no
watchdog/OOM failure. Iterator: 1 passed in 222.45 s, refuted with matching
source-C++ use-after-free. At pair: 1 passed in 302.84 s, unchecked refuted and
guarded proven. All three records, 26 report/log references, declared physical
pins, 203 source pins per lane and three certificate self-hashes match.
[Final audit](evidence/t25-next-controls-accepted-20261015.json),
[prospective launch](evidence/t25-next-controls-launch-20261015.json).

Read-only live check **2026-10-15 13:56 ET** found node 0 generation 568,
node 1 generation 600 and legacy generation 77 released, no owned evaluation
process, clean detached source `94769312`, load 0.40/0.85/0.76, and 21 GiB free
on `/data1` / 95 GiB on `/data`. These are timestamped observations.
Raw outputs remain at
`/data/yanruj/EvolveSWDB_runs/probata-t25-next-controls-20261015-1347-node0` and
`...-node1`; only compact metadata returned to the Mac. Coordinator, ticket25
acceptance and independent audit readers retain these outputs. No further remote
evaluation is scheduled during closeout. Local/remote effort refs and attached
checkouts have a [recovery-safe inventory](evidence/closeout-branch-inventory-20261015.json);
its exact tips require refreshing after final integration, and it authorizes no deletion. Root owns lane coordination and cleanup;
no remote path may be removed without checking current use and root authorization.

## Historical integration snapshots

The following checkpoints predate the current state above.

Integration `d3a5dd48` adds the reviewed typed-array ACSL spelling repair and
prospective WP launch metadata (two public stand-in controls pass). A focused
Linux replay started11:55:56ET at that frozen source: node0generation561 covers
native/header/metadata controls, node1generation599 covers original owner-data
safe/stale plus exact bindings and qualified copy callers. Snapshot11:57:52ET
has51 node0passes and node1firstactualactive; neither has a final result.
[Launch metadata](evidence/focused-parser-owner-launch-20261015.json). The remote
checkout must remain frozen until both jobs finish; later primary docs do not
upgrade that exact source. Mac caller acceptance at `0831b224` is separately
audited: four controls pass, with safe15ordinary/2smoke, empty13/2, model36/7;
uninitialized and short-capacity subjects remain not_proven.
[Caller evidence](evidence/t24-std-copy-callers-mac-20261015.json).


Updated: 2026-10-15 11:43 ET. Integration runtime checkpoint `77624eec` composes
nested initializers `268aaf19`, checked vector pipeline `5c8decdf`, exact original
standard-call bindings/caller ranges `c61af423`, and isolated parser fix `7e663aaf`.
The two pointer-call admission sets retain both checked owner handles and standard
range calls; checker/lowerer source unions remain complete. Fourteen compiler and
explicit verifier-stand-in composition controls pass (100.94s, peak450,658,304bytes
under8GiB), with no actual solver replay at this combined checkpoint.
[Parser diagnosis and composition evidence](evidence/stdlib-parser-context-20261015.json).

Linux's original frozen `5c2a` native outcome remains134passed/1failed. Its header
context failure is repaired by captured-search ordering plus an isolated libclang
worker: six focused Linux controls pass at `7e663aaf` (87.005s), including CPATH and
CPLUS_INCLUDE_PATH hook refusals. Historical actual WP results retain their exact
source/method pins: vector pipeline safe/wrong-comparison and nested initializer
safe/missing-window/missing-initialization evidence are accepted scoped slices.
Exact-call caller actual acceptance and the root entry-hint checkpoint remain
separate; no production method3 or whole-ticket completion is claimed.

| Ticket | Evidence at that checkpoint | Action recorded then |
|---|---|---|
| 07 | Run18 finished unproven at 10:43 ET; 20 open goals (13 unit/7 hint), 51.76 counted minutes, no final proof/smoke | Audit negative outcome and remaining induction goals; retain prototype/RTE scope boundary |
| 24 | Qualified copy body historical36ordinary/7smoke; exact original callee and typed caller range discharge integrated with compiler/stand-in controls | Run fresh qualified caller actual acceptance |
| 25 | Checked vector workflow integrated; historical safe77ordinary/12smoke and wrong-comparison76ordinary/1open/12smoke remain distinct from combined runtime | Continue wider vector/pair acceptance; no full-ticket claim |
| 27 | Checked automatic nested initializer integrated; historical safe14ordinary/1smoke, three independent negative obligations retained | Complete combined-policy, entry hints and remaining DX acceptance |
| 36 | Parser search reconstruction repaired: Mac13, Linux6, combined14 compiler/stand-in controls pass; source/checker unions preserved | Coordinate frozen combined-source replay and remaining setup acceptance |

**32 of 63 resolved; five claimed.** Drafts 1/2 remain immutable; draft 3 is not
created. Ticket 28 remains gated by 27; 43 remains blocked by 29. Held-out kernels
and method freeze remain gated by dependencies. Existing user authorization covers
implementation, commits/pushes, two remote lanes and scoped BFS source export.
The coordinator owns the full periodic status report and live lane dispatch; this
11:43 update records the scoped integration handoff.

## Historical host snapshots

Readback2026-10-15 11:46ET: node0generation560, node1generation598 and legacy77
are released; load0.02/0.57/1.04, `/data1`21GiB and `/data`95GiB free. Frozen
`5c2a` final outcomes remain native134passed/1failed and entry19passed/1failed.
The owner-safe failure has no WP launch/goals and shares the repaired parser
context refusal; stale-alias was not reached. All155 report references and2,852
declared absolute pins match.
[Final frozen audit](evidence/source-gate-final-frozen-5c-20261015.json).


Historical readback: 2026-10-15 10:49 ET. Both socket leases (node 0 generation 556,
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

The historical 30-minute progress heartbeat was `probata-implementation-progress`;
it is PAUSED for closeout. Its past reports do not replace incremental artifacts.

## Historical validation and progress reporting

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
