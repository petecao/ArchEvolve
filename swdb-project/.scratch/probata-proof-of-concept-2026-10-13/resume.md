# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Updated: 2026-10-15 16:22 ET. **Implementation is active under the user's ongoing approval.**
Integration: `codex/probata-resume-20261015`, based on `yanrujhou_main` at
`d94d629b`. One remote integration ref is published. Production `swdb/` bytes
still match `71771f09`; each evaluation retains its exact source identity below.

**32 resolved / 28 ready-for-agent / 3 claimed**, derived from ticket frontmatter.
The frontier is **07, 24, 27**. Ticket 25 waits on 24; ticket 36 waits on 27.
Drafts 1/2 remain immutable. Draft 3 and the final production freeze have not happened.

| Ticket / owner | Verified checkpoint | Active work |
|---|---|---|
| 07 / `ticket07` | Scoped CLI approval repair: 169 controls and neutral actual CLI probe pass. Runs 20/21 remain aborted. | Run 22 at `703ff3d7` aborted before provider work: baseline completed in 15.04 minutes, then process inspection raised AccessDenied during seed checking. Targeted guard diagnosis and representative pipeline checks precede another counted run. |
| 24 / `ticket24` | Original Ring and allocation safe/seeded pairs audited at `71771f09`; details below. Seven public unsupported-construct controls pass. | Node 0 generation 571 runs seven remaining pairs, fresh dependencies and ten allocation/lifetime controls at `9b75f4a2`. Completed pairs are skipped. Fresh DXC summary (4 ordinary + 1 smoke) and safe caller (9 ordinary + 3 smoke) are Valid; corrected seed is active. |
| 27 / `ticket27` | Seven of eleven safe cases pass at `71771f09`; stall-condition retains 111 ordinary + 35 smoke Valid, no open goals. | Node 1 generation 602 continues safe cases; remaining safe cases continue. Negative, capacity and bounded/native profiles remain. |
| 36 / dependency-gated | Mandatory RTE, complete-command and mutation checks integrated; 122 compiler/scripted controls pass, 13 actual-WP cases excluded. | Waits on 27; no full setup acceptance or production method freeze. |

Ticket 24 evidence: [Ring pair](evidence/t24-original-template-pair-mbit10-20261015.json)
has safe 89 ordinary + 1 smoke Valid and seeded 88 ordinary Valid + one ensures
timeout + 1 smoke Valid. [Allocation pair](evidence/t24-original-allocation-pair-mbit10-20261015.json)
has safe 42 ordinary + 7 smoke Valid; seeded 40 ordinary Valid, invariant/RTE
timeouts, 4 smoke Valid and 3 failed smoke. Both allocation records retain 11
initialization goals. Neither negative is a solver refutation.

The first remaining-groups run ended at 15:54:36 ET when the public test helper's
600-second limit interrupted the separate out-of-range case. It produced no
accepted record for that case. Generation 570 released normally; post-exit
inspection found no run-prefix survivors. The reviewed retry uses an explicit
1800-second public-command limit, unchanged 30-second solver limits, an 8 GiB
process-tree cap and a four-hour whole-profile limit.
[Launch, selection and prior cleanup metadata](evidence/resumed-t24-pending-launch-20261015.json).

Raw evidence stays outside Git:

- Mac: aborted `/private/tmp/probata-t07-20261015-run22` (driver 38318 stopped);
  aborted runs 20/21 retain their separate folders. No provider ran in run 22.
- Ticket 24: accepted Ring at `/data/yanruj/EvolveSWDB_runs/probata-resume-t24-templates-71771f09`;
  allocation and interrupted out-of-range at `probata-resume-t24-remaining-71771f09`
  under the same root; active retry at `probata-resume-t24-pending-9b75f4a2`.
- Ticket 27: active `/data/yanruj/EvolveSWDB_runs/probata-resume-t27-safe-71771f09`;
  old controlled-stop diagnostic remains `probata-resume-t27-diagnostic-20261015-1512`.

Keep the baseline archive and node 1 checkout at `71771f09`, active node 0 at
`9b75f4a2`, and retain Mac run 22 at `703ff3d7` while audit readers need it. Node 0
uses `/data1/yanruj/probata-t24-corrected-20261015`. Latest preflight: 19 GiB free
on `/data1`, 95 GiB on `/data`. Both lanes are held by this coordinator; raw output
stays on `/data`. Recheck live before dispatch. The lane wrapper matches freshly
fetched MemAcc `yanrujhou_main` at `76cca359`; its default `main` lacks that script.
GPU NVML has a driver/library mismatch; these jobs use CPUs.

A native audit found old DXC seed `+2` satisfies its stand-in contract. Its old WP
timeout is a modular-summary precision control. Corrected seed `+4` has a concrete
C++/C violation and is selected for fresh actual acceptance. OMP/float negative
readers accept attributable invariant failures. These changes never relabel old
records. The finite native agreement runner completed its independently admitted full
nine-group run: 17 rows agree on 112,589 defined input comparisons (samples may
repeat); the allocation seed is UB-only. Final independent review reconstructed
every defined observation and all exclusions with zero errors; 15,768 physical
references match. This reuses ticket 22's accepted native subcheck and emits no
proof verdict. [Accepted finite agreement and bounds](evidence/t24-finite-agreement-20261015.md).

The coordinator owns merges, graph updates and remote dispatch. The Mac's actual
verifier slot belongs to 07; remote jobs are serial within each leased socket.
This chat's 30-minute heartbeat is active; the old chat's remains paused.

Next: audit each selected original pair and the pending out-of-range record as
it completes. [Map](map.md), ticket acceptance text and compact evidence remain
authoritative. Research-only next-ticket notes remain in
`/private/tmp/probata-ticket25-resume-exploration.md`,
`/private/tmp/probata-ticket25-lifetime-capabilities.md` and
`/private/tmp/probata-ticket28-resume-exploration.md`.

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
