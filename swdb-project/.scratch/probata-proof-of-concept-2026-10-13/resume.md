# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Updated: 2026-10-15 19:11 ET. **Implementation is active under the user's ongoing approval.**
Integration `codex/probata-resume-20261015` is based on `yanrujhou_main` at `d94d629b`.
Audited run23 documentation is published at `6dc94905`; reviewed method21 prototype
is published at `14c2a298`. Only `swdb/c_lowering.py`
differs in production from `71771f09`; its reviewed SHA256 remains
`0e185baaf5b0e926d2155a5c94cb61037e9d22bee2b5ee8d47424a2824fe4422`.
Every evaluation retains its own source identity.

**32 resolved / 28 ready-for-agent / 3 claimed**, derived from ticket frontmatter.
The active frontier is **07, 24, 27**. Ticket 25 waits on 24; ticket 36 waits on 27.
Drafts 1/2 remain immutable. No draft 3 or final production freeze exists.

| Ticket / owner | Verified checkpoint | Active work |
|---|---|---|
| 07 / `ticket07` | Run 24 remains unproven: 29 open, 52.03 counted minutes, 5 mechanical / 36 Codex records. Posthoc full-30-second replay timed out after 710.42s without a complete report; no verdict upgrade. | Temporary cleanup quarantine independently checked and released at 19:07 ET. Method 22 adds zero seeds, paged VC inspection and complete provider accounting; 33/36-minute search/return limits leave 24 minutes for final checks. TDD/review, no fresh actual. |
| 24 / `ticket24` | Current float pair, five std models, nine atomic models and atomic caller pair accepted. Remaining matrix stopped on a MAA summary with 3 ordinary Valid / 0 generated smoke goals; strict refusal preserved. Original std caller still unproven. | Node 0 generation 578 runs reviewed qualified std v2 at `bf7a404c`. Agent investigates a narrow no-op summary/caller nonvacuity witness without source/contract changes. Later original groups remain pending. |
| 27 / `ticket27` | Current bounded/native 35/35 and repaired capacity 3/3 accepted. Current negative 11/13 independently audited; historical safe 11/11 remains `717` only. | Node 1 generation 603 continues outside-footprint and short-store-frame negatives at `0e7`. Fresh safe 11 queued as disjoint 5 + 6 shards; historical weights about 50 minutes each, excluding setup/runtime drift. |
| 36 / dependency-gated | 122 compiler/scripted controls pass; 13 actual-WP cases excluded. | Waits on 27; runtime fallback research remains prospective. |

At17:43:14 ET node0 generation572 released after the standard caller safe timeout;
whole guard exit1,1805.69s,peak1,010,438,144B,noOOM/whole timeout. Its five standard
model proofs and float pair remain scoped results; no full-matrix acceptance.
The caller record SHA256 is
`e03a86746f27c7815aeb4b3765fb3d84da21e1079f8170b4f1a21ae881b6a194`;
exact open goal is `typed_real_swdb_std_unit_assert_swdb_pointer_formation_1`.
Original assertion/source must be preserved or repaired soundly; no premise may
be inserted solely to close the obligation.

Node0 capacity started17:46:58 ET at generation573 and released17:53:38 ET:
first32-command case failed naturally,45/47 ordinary+11/11 smoke Valid,5 init/4 RTE.
Open: `typed_real_dxf_capacity_loop_invariant_4_preserved` and
`typed_real_dxf_capacity_call_maa_stream_load_requires_memory_domain`.
Actual setup/launch passed; no OOM/whole timeout or source mutation. Record SHA256
`e358e61937fded3fd12f44b68f0e515580623a7d3c013e643b7ad58a4aa88bee`.
The later reviewed repair passes WP32 (49 ordinary + 11 smoke Valid);
new invariant establishment/preservation are Valid. Its code/contract/semantics/
method/build/naming pins match the old failed record exactly. No failed goal is filtered.
The33-command WP and CBMC cases were not reached.

Node 0 generation 574 bounded/native completed 35/35, exit 0 at 18:06:10 ET.
Inner guard: 528.402s, peak 369.8MB; outer: 530.426s, peak 421.1MB, no OOM/timeout.
Independent audit: 180 references / 204 files, zero mismatches. The 24 CBMC records
split into 12 proven and 12 refuted with source replay; these are bounded outcomes.
[Final bounded audit](evidence/t27-composed-bounded-completed-independent-20261015.json).

Node 0 generation 575 capacity rerun started 18:11:29 ET at clean detached
`b9a34bbbcaa1670a7e4653f78e220da94af01a08`, one worker, 8GiB tree cap and
1800s whole guard (outer 1920s). Source: `/data1/yanruj/probata-reviewed-b9a34bbb`;
raw: `/data/yanruj/EvolveSWDB_runs/probata-reviewed-b9a34bbb-t27-capacity`.
This profile completed 3/3 and released naturally at 18:21:42 ET.
WP32: 49/49 ordinary + 11/11 smoke; WP33: ghost-capacity nonproof,
47/49 ordinary + 11/11 smoke with both capacity-dependent timeouts retained.
CBMC32 proves; CBMC33 ends not_proven/ghost_capacity, no counterexample.
All four records pass 40-reference / 44-file audit; guard610.165s,
peak2,934,345,728B, no OOM/timeout. The new writer-kind invariant is Valid
in both WP32/WP33 establishment and preservation.
[Final capacity audit](evidence/t27-reviewed-capacity-completed-independent-20261015.json).
The one new ordinary writer-kind invariant itself is established/preserved;
all old hints, source, preconditions and assertions remain. Production/library
bytes and full runtime identity match `0e7f2327`; 197 physical/Git module checks pass.
[Repair launch audit](evidence/reviewed-t27-capacity-launch-b9a34bbb-20261015.json).

Node 1 generation 603 continues its original negative profile at clean detached
`0e7f232762e4555aa9435a3a3622923fad8ee928` in
`/data1/yanruj/probata-composed-0e7f2327`; raw remains
`/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative`.
Legacy 77 is released. Live 18:12 readback: 16GiB free on `/data1`, 95GiB on `/data`;
one additional full source worktree consumed about 2GiB. Raw stays on `/data`.
Planned raw budgets are coordinator-monitored, not filesystem quotas. Recheck
leases/processes/disks before dispatch; at most two jobs, one per socket.

Accepted evidence and preserved boundaries:

- [Fresh finite native agreement](evidence/t24-fresh-finite-agreement-0e7f2327-20261015.md):17 defined rows agree on112,589 comparisons; samples may repeat.47,164 precondition and2,207 known-UB exclusions stay separate; allocation seed has zero defined comparisons. Finite native evidence emits no proof verdict. All-observation/whole-source independent audit passes; clean producer and349MB raw remain retained.
- [Fresh float pair](evidence/t24-current-float-pair-0e7f2327-20261015.json): exact current source accepted with all init/RTE obligations retained. Seed stays not_proven, not a solver refutation. Historical three-init-timeout float record stays unchanged.
- [Atomic/enum review](evidence/t24-atomic-enum-independent-review-t27-20261015.json): effectful order/weak operands, weak CAS and ambiguous enum values/types now refuse;115 compiler/native/public/corpus controls passed. No actual WP false-proof claim.
- [Historical matrix](evidence/t24-historical-frontier-9b75-mbit10-20261015.json): Ring/allocation/DXC/class/OMP results retain their historical source; no upgrade to current0e7. [717 compiler provenance](evidence/t27-717-compiler-provenance-addendum-20261015.json) retains full frontend hashes and explicit link-DSO boundary.
- [Run23 audit](evidence/t07-counted-23-20261015.json): frozen df19 and raw `/private/tmp/probata-t07-20261015-run23` retained.55 guarded reports, no terminal resource/cleanup failure. Legacy12 proposal requests include one edit refusal;11 candidate proof attempts are10 complete+1censored. Interrupted second-call usage is unknown, totals lower bounds. No final-smoke/wait-negative success is claimed.

The coordinator owns merges, graph updates and remote dispatch. Node 0 generation
577 naturally released at 19:06:55 ET. Root preflight at 19:08:45 checked all three
leases (0 released / 1 held / legacy released), clean detached `0e7`, source/disk/load
and independent process state. Load 1.90; before the new checkout, 15 GiB was free
on `/data1` and 94 GiB on `/data`. No residual matrix verifier or third job.

Qualified std v2 started 19:09:05 ET on node 0 generation 578, exact clean detached
`bf7a404c65694a18d83635c4f6f56105b005fb59`; source:
`/data1/yanruj/probata-reviewed-bf7a404c`; raw:
`/data/yanruj/EvolveSWDB_runs/probata-reviewed-bf7a404c-t24-std-domain-v2`.
Whole cap 4200s / outer 4320s, public limits 1800s, one worker, 8 GiB process tree,
8 GiB planned raw storage (monitored, no quota). All 197 physical/Git module checks
pass; the full runtime dictionary equals the accepted `0e7` launch identity.
[Actual admission receipt](evidence/reviewed-t24-std-domain-v2-launch-bf7a404c-20261015.json).
This establishes source/runtime/admission, not ordinary model selection or proof success.

Run 24 source remains frozen at `14c` in `/private/tmp/probata-resume-t07-method21`;
raw `/private/tmp/probata-t07-20261015-run24`. Final evidence documentation is pending.
There were 63 guarded resource reports (62 exit 0, one normal search-deadline exit 137);
no terminal resource or owned-process cleanup failure. Its first provider turn
never returned `turn.completed`, so complete usage is unknown, not zero. Exact
owned-session telemetry retains 13,413,886 observed partial total tokens (including
13,386,648 input / 27,238 output; cached input and reasoning are subsets). The
last counter does not establish the unknown in-flight tail. The 259 ordinary entries
include 230 passed / 25 unknown / 4 timeouts; 6 of 9 postconditions remain open. Passing
individual goals under open hints is not a unit proof. The final 8-minute reserve
was unused because method 21 required zero diagnostic-open goals before replay.
The separate posthoc full-30-second diagnostic at
`/private/tmp/probata-t07-20261015-run24-posthoc-full30` timed out at 710.420516s,
peak 5616.22 MiB. It scheduled 497 goals and emitted 24 Unknown / 2 Timeout status
lines, but no complete JSON inventory. The 238-goal delta from the diagnostic
ordinary inventory cannot be partitioned reliably from retained files. No full
verdict or success is claimed. Its inspection error on exact owned PID 9354
remains recorded. Independent fresh absence scans supported exact-owner archival
and slot release at 19:07:14 ET; no process was signaled. These old concrete hints
and results cannot seed another fresh provider. Scheduling alone is not supported
as a remedy by this censored result.
Method 22 design/TDD/review proceeds separately; no blind method 21 rerun.
Independent literal acceptance review found the five mechanical frame hints cannot
satisfy ticket 07's every-hint-Codex criterion. The explicitly undecided seed
assumption does not override that criterion. Method 22 must start without mechanical
seeds and let the fresh scoped Codex session independently author allowed frames;
old concrete frame payloads are excluded. Existing provenance is not relabeled.
The next plan also adds bounded paging for previously truncated active-goal premises,
natural provider completion/accounting, and 33/36-minute search/return limits.
The remaining 24 minutes cover full-30-second positive and identical-hints negative
verification (at least 8 minutes reserved for the negative). This is an explicit
prospective allocation, not a measured sufficiency guarantee. No fresh run is launched.

Qualified std at6221 stopped before WP: public formal-half vocabulary excludes
valid_read/base_addr. Its zero-row failure and unchanged inputs remain retained;
no ordinary model eligibility/semantic result is claimed. V2 uses only allowed
null/valid/current-or-predecessor clauses, a disclosed narrower writable-object
domain;13controls now include actual public validation, and independent final
review passes at `bf7a`. Fresh WP/model eligibility/same-base assertion are active
on node 0; no result yet.

Node0 generation577 started the remaining original matrix at18:27 ET using
the existing0e7 checkout. Groups: atomics,maa_summary,dxc_summary,templates,
classes,omp,new_array, including all dependencies and lifetime controls.
Oneworker8GiB tree,21600s whole cap,1800s public limits,8GiB planned raw
(coordinator-monitored, no quota). Raw:
`/data/yanruj/EvolveSWDB_runs/probata-reviewed-0e7f2327-t24-remaining`.
[Launch audit](evidence/reviewed-t24-remaining-launch-0e7f2327-20261015.json):
197physical/Gitchecks,0errors, exact runtime matches prior0e7.
This run stopped at 19:06:55 ET after 12 rows: 9 atomic models + 2 callers accepted,
then a MAA summary with 3 ordinary Valid but no generated smoke goals refused by
the strict reader. Its original no-op body and frame-only contract are unchanged;
no general zero-smoke exception or artificial postcondition is adopted. Agent 24
is evaluating a narrow no-op/caller feasibility witness. Later groups did not run.

Next: finish the remaining matrix, reviewed v2 standard caller pair and
negative/fresh-safe profiles. The prospective two-shard safe plan covers all11
without overlap; historical weights project about50minutes each plus setup
if two lanes are available. No fresh-safe success or ETA guarantee is claimed. No full ticket
or final method success is claimed from these checkpoints. This chat's30-minute
heartbeat stays active; last full table 18:49 ET, next due 19:19 ET.
Research-only notes remain `/private/tmp/probata-ticket25-resume-exploration.md`,
`/private/tmp/probata-ticket25-lifetime-capabilities.md`,
`/private/tmp/probata-ticket25-heap-bridge-tcb-addendum.md`,
`/private/tmp/probata-ticket25-heap-import-entrypoints-20261015.md`,
`/private/tmp/probata-ticket25-lemma-dependency-safety-20261015.md`,
`/private/tmp/probata-ticket28-resume-exploration.md` and
`/private/tmp/probata-t36-runtime-fallback-review.md`.

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
