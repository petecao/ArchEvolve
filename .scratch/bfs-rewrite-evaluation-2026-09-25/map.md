# Map: BFS profiling, rewrite proposals, and hardware-aware evaluation

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-27 (Eastern Time)
**Type:** ticket map
**Status:** claimed
**Blocked by:** Remaining empirical verification, calibration, artifact/control comparisons, final acceptance, and free host-lane availability. The user now grants standing authorization for current and future task-related transfers to private ruchou/EvolveSWDB codex/bfs-* branches, mbit10 through Git, and Anthropic through Claude Code. Earlier transfer holds are superseded; original budgets and evidence-preservation rules remain.
**Spec:** [Refined specification](spec.md)

The user authorized autonomous implementation of all 21 tickets and all necessary builds, installations, benchmark/simulator runs, external access, Git, and Claude Code on 2026-09-25. This supersedes the publication-only hold. The two-lane mbit10 rules and evidence requirements remain in force.

## Live checkpoint — 2026-09-27 00:56 ET

14 tickets are resolved and 7 remain claimed. No final campaign cell or gain is
qualified. The retained Linux recovery group passed 42 supplementary, 5 ownership,
and 2 interruption tests. Both pristine `6a493a0` simulator runtimes independently
reopened that immutable evidence with the full 600-second/2-GiB charge retained.
T15/T16 scientific recovery dispatch was pending reviewed admission and a free lane at this checkpoint.

T17 diagnostic attempt `bfs-t17-diagnostic-build-only-20260926-a1` exited before
compilation: its YAML-only view omitted two source attachments required by public
catalog validation. The failed attempt remains preserved; the source-attachment
inventory repair passes 29 focused tests, including an actual public lookup over
the full record view. This is no diagnostic build or acceptance result.

T20 context1 finished unresolved with no candidate and used 104.553762 seconds.
Its exact Git-backed result is imported locally; all 249 records validate.
[Terminal evidence](observations/provider-terminal-independent-20260927.json)
retains closure and accounting. A context2 clarification is prepared but uncalled;
its shared provider allowance is conservatively floored to 1,632 seconds.

The isolated full regression run at `c282c9f` is still running with two failure
markers; no full-suite pass is claimed. Independent final Standards and Spec
reviews remain required after acceptance and fixes.

## Approved tickets

The user approved this 21-ticket decomposition on 2026-09-25. Each link is one independently reviewable ticket. Blockers are ticket dependencies. Status and evidence are synchronized as work proceeds; acceptance is not inferred from fixture tests.

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | [Shared BFS identity and explicit baselines](issues/01-shared-bfs-identity-and-baselines.md) | None | resolved |
| 02 | [Patch proposal to durable candidate](issues/02-patch-proposal-to-candidate.md) | 01 | resolved |
| 03 | [Native BFS evaluation](issues/03-native-bfs-evaluation.md) | 02 | resolved |
| 04 | [Instruction-based rewriting and bounded repair](issues/04-instruction-rewriting-and-repair.md) | 03 | resolved |
| 05 | [Annotated-source rewriting](issues/05-annotated-source-rewriting.md) | 04 | resolved |
| 06 | [Automatic function hotspot discovery](issues/06-function-hotspot-discovery.md) | 03 | resolved |
| 07 | [Loop discovery and changed-region profiling](issues/07-loop-discovery-and-reprofiling.md) | 06 | resolved |
| 08 | [Dynamic memory observations](issues/08-dynamic-memory-observations.md) | 06 | resolved |
| 09 | [Complete profile packages and strategy lookup](issues/09-profile-packages-and-strategy-lookup.md) | 07, 08 | resolved |
| 10 | [Queryable DX100 operation contracts](issues/10-dx100-operation-contracts.md) | 02 | resolved |
| 11 | [Reproducible workloads and comparison protocols](issues/11-workloads-and-comparison-protocols.md) | 03 | resolved |
| 12 | [DX100 build and execution path](issues/12-dx100-build-and-execution.md) | 03 | resolved |
| 13 | [Correctness of the timed DX100 binary](issues/13-dx100-timed-binary-correctness.md) | 12 | resolved |
| 14 | [DX100 region timing and memory profiling](issues/14-dx100-region-and-memory-profiling.md) | 09, 12 | resolved |
| 15 | [Baseline pilot and protocol freeze](issues/15-baseline-pilot-and-protocol-freeze.md) | 11, 13, 14 | claimed |
| 16 | [Artifact reference and controlled comparisons](issues/16-artifact-reference-and-controls.md) | 11, 13, 14 | claimed |
| 17 | [DX100 BFS: instruction-route acceptance](issues/17-dx100-instruction-route-acceptance.md) | 04, 10, 15 | claimed |
| 18 | [DX100 BFS: patch-route acceptance](issues/18-dx100-patch-route-acceptance.md) | 15 | claimed |
| 19 | [Upstream BFS: instruction-route acceptance](issues/19-upstream-instruction-route-acceptance.md) | 04, 15 | claimed |
| 20 | [Upstream BFS: annotated-source route acceptance](issues/20-upstream-annotated-route-acceptance.md) | 05, 10, 15 | claimed |
| 21 | [Coverage, ROI gain, and collaborator handoff](issues/21-coverage-roi-gain-and-handoff.md) | 16, 17, 18, 19, 20 | claimed |

Tickets 01–14 are resolved (14/21). T13 closed after actual A2 full/tail/competing-update coverage and exact completed readback at 19:17 ET. Ticket 11 was resolved again at 14:00 ET after its native runtime-policy correction and independent review. The empirical frontier is now shared calibration, reference/control comparisons and candidate assessment. Later independent branches may proceed once their own blockers are resolved; list order alone is not an additional dependency. Runtime scheduling must also follow the lab's host and resource rules.

### Assigned acceptance cases

| Ticket | Starting implementation | Payload / producer | Execution requirement | Graph coverage |
|---|---|---|---|---|
| 17 | DX100 scalar top-down BFS | Natural-language instructions / SW test client | Correct candidate with proven DX100 accelerator execution | Kronecker and uniform-random |
| 18 | DX100 scalar top-down BFS | Supplied patch / test client | Real native CPU evaluation and reprofiling | Kronecker and uniform-random |
| 19 | Upstream direction-optimizing BFS | Structured instructions / test client | Real native CPU evaluation and reprofiling | Kronecker and uniform-random |
| 20 | Upstream direction-optimizing BFS | Annotated source / HW test client | Correct candidate with proven DX100 accelerator execution | Kronecker and uniform-random |

These four cases cover all eight source/route/graph cells, all four payload forms, and both source-specific accelerator minima. Ticket 16 separately supplies the actual artifact reference and controlled comparison evidence. A candidate or result may cover multiple obligations only when its source, workload, protocol, target, and required evidence match.

### Important dependency boundaries

- Ticket 14 may collect simulator profiling independently of ticket 13. Its output must remain explicitly unverified until correctness of the timed binary is established; ticket 15 joins those capabilities.
- Ticket 16 does not depend on the pilot-sized protocol in ticket 15. It owns and freezes its artifact/control protocol before the associated reference comparisons.
- Instruction and annotation development may use contract fixtures before complete profile-package generation is available. Such fixtures do not satisfy real BFS acceptance or performance criteria.
- Ticket 07 must demonstrate discovery on actual changed BFS/helper code, not only fabricated profiler output.
- Ticket 21 closes only when the spec's acceptance obligations, including at least one policy-qualified correct ROI gain, are evidenced. Otherwise it retains the incomplete report and returns the unmet requirement to the proposal owner; it does not launch an unbounded strategy search.

## Acceptance ownership

| Spec criterion | Principal tickets |
|---|---|
| AC01 — Shared kernel, correct source context | 01, 02, 19, 20 |
| AC02 — Automatic functions/loops and source attribution | 06, 07, 09 |
| AC03 — Newly introduced hot helper/loop | 07; candidate reprofiling in 17–20 |
| AC04 — Actual dynamic memory observations | 08, 09, 14; real evidence in 17–20 |
| AC05 — Forward/reverse strategy queries | 09 |
| AC06 — Both routes, sources, graphs; four payload forms | 04, 05, 17–20 |
| AC07 — Actual candidate and durable retrieval | 02–05, 17–20 |
| AC08 — Source/capability/protection rejection | 02–05, 10, 11 |
| AC09 — Retained failure, timeout, budget, missing data, regression | 03, 04, 12–14, 17–21 |
| AC10 — Structural correctness of timed code | 03, 13, 17–20 |
| AC11 — Acceleration from both source implementations | 13, 17, 20 |
| AC12 — Actual native evaluation | 03, 18, 19 |
| AC13 — Distinct BFS ROI, region, native/simulated/diagnostic quantities | 03, 07, 11, 14, 17–20 |
| AC14 — Explicit comparator and compatible evidence | 01, 11, 16–21 |
| AC15 — Artifact and controlled comparisons | 11, 16, 21 |
| AC16 — Frozen protocol and equivalent graph/source workloads | 11, 15, 16, 17–20 |
| AC17 — At least one correct ROI gain | Evidence from 17–20; final gate in 21 |
| AC18 — Full coverage including failed/regressing cases | 17–21 |
| AC19 — Executable capabilities and honest wrapper support | 10, 17, 20 |
| AC20 — Real workflow with labeled SW/HW test clients and handoff | 17–21 |

## Actual proof and provider checkpoint — 2026-09-27 00:38 ET

The [Linux proof group](observations/proofgroup-independent-closure-20260927.json)
passed all 49 cases without skips and independent operational closure. Its
26.359140 seconds / 3,223,552 bytes remain charged at the full reserved 600 seconds
/ 2 GiB for each task. Full batch admission separately exposed a venv-versus-resolved
Python path comparison defect; the reader repair preserves the original proof
runtime and requires unchanged tested primitives. No scientific batch has started.

The [bounded provider continuation](observations/provider-context1-launched-20260927.json)
started on node 1 at 00:37:05.675084 ET, with original end 00:49:35.675084 ET.
T17 diagnostic data-view preparation proceeds independently. Three workers are
active. The older exact-c282 full regression is past 67% and has two failure
markers; full diagnostics remain pending completion. No failure is discarded.
Tickets remain 14 resolved / 7 claimed, 0/8 final cells and no qualified gain.
Next scheduled host/worker/table check: 2026-09-27 01:03 ET.

## Recovery and evidence checkpoint — 2026-09-27 00:18 ET

Inactive workers were replaced; local recovery implementation and independent
review resumed. The [scoped review](observations/recovery-independent-review-20260927.json)
passed 154 tests, including earlier reproduced ancestry and lease-observation
failures. The new supplemental operator remains under development; no actual
Linux proof or guest execution follows from these local tests.

The [T17 primary metadata transfer](operator-recipes/t17-diagnostic/primary-evidence-transfer-20260927.json)
pushed one exact 17,230-byte YAML in commit `efdadb8b1e7ff22562d07e9f63007198a6b6352d`.
The exact Git blob is now imported locally, and `swdb validate` reports 248 valid
records. Binary and raw logs remain on mbit10. Diagnostic compilation still
requires the final corrected runtime and compatible fresh Linux proof.

The [helper comparison](observations/helper-upstream-comparison-20260927-0015.json)
verified the entire installed host subtree against fetched upstream `1ec1bc40`.
Node 0 was externally held at generation 333; node 1 and legacy were released
at 432 and 77. No checkout or active job was changed. Fresh kernel and metadata
checks remain mandatory before dispatch. The full local regression at `c282c9f`
is still running. Tickets remain 14 resolved / 7 claimed, with 0/8 final cells.

## Host and worker checkpoint — 2026-09-27 00:03 ET

The [scheduled checkpoint](observations/health-20260927-0003.json) observed host
state at 00:01:51 ET: both sockets and legacy released (332/430/77), no kernel
holders or live owned BFS jobs. All 944 retained T16 identities are now absent;
the failed run's 658,644,992 raw bytes and original failed budget verdict remain
unchanged. Free space is 16.055 GiB on `/data1` and 164.803 GiB on `/data`;
node0/node1/global available memory is 56.536/58.267/116.946 GiB. Load is
0.09/0.29/0.55. No lane is reserved by this observation. Three workers are active.

The prospective recovery implementation has 223 local tests passing and two
Linux skips; final review and actual Linux proof remain pending. T20 has made
no continuation call. T17 has operator templates, with exact retained-build Git
provenance being checked. The independently reviewed lifecycle identity repair
is committed and pushed at `c282c9f5c57f7756dc3b22e12952eb963683e6d3`.
A bounded full local regression at that immutable commit started 23:56:21 ET;
its running worktree must remain unchanged. Tests on that earlier commit may
retain the subsequently identified stale a4 test assertion; the new recovery
scope has its own corrected focused verification. There is no final suite result
or new empirical acceptance. Tickets remain 14 resolved / 7 claimed and 0/8
final cells. Next full check: 2026-09-27 00:33 ET.

## Host and worker checkpoint — 2026-09-26 23:33 ET

The [full host audit](observations/health-20260926-2333.json) found both socket
leases and the legacy lease released (332/429/77), no kernel holders, and no live
owned BFS work. T16 remains failed with zero completed samples; its exact retained
944-identity union is closed except the permitted zero-RSS launcher zombie.
All three current workers are active. Free space: 16.079 GiB on `/data1`, 164.972
GiB on `/data`; new raw output remains on `/data`. Available node0/node1/global
memory is 56.506/58.476/117.125 GiB; load is 0.44/0.58/1.71. Installed helper
bytes and working tree are unchanged. New upstream `15129f88` requires a host
subtree comparison before any admission. No lane is reserved by this observation.

The independently reviewed RSS and historical lease fixes are committed at
`a5a63f9223b684d9622d28914c704b175906da7a`; isolated exact runtime `0dc0d4fecfe2903ff0cc1ba9e6b738a8f5c1a4f1`
passed 158 tests with seven Linux-only skips and was pushed on the authorized
private runtime branch. Its seven changed blobs match independent review.
The [T16 cost-only review](observations/t16-failed-cleanup-accounting-review-20260926.json)
retains the outstanding five-second grant in full and preserves the failed
cleanup-budget verdict. It does not add that grant a second time to the full
11,121-second closed wall charge or reset the original hard end. Recovery remains
preparation. T20 has not called its provider. Next full check: 2026-09-27 00:03 ET.

## Execution failure and transfer checkpoint — 2026-09-26 23:27 ET

T16 stopped with `ProcessLookupError: [Errno 3] No such process` in the owned
RSS sampler at 23:20:51 ET. It completed zero samples and has no sealed ROI or
verified result. The independent retained union contains 944 PID/start identities:
943 absent and the exact zero-RSS tmux launcher zombie. Its cleanup ledger retains
20.94487111307685 settled seconds plus one unreturned five-second reservation;
that budget audit failed and remains failed. Final raw allocation is 658,644,992
bytes (1,789,632,512 including prior preparation), with 11,120.079151 seconds
from original outer start through final read-only recount. The public evaluation
still says running because its process was killed; this is stale interrupted
state, not live execution. See [failed terminal evidence](observations/t16-failed-terminal-20260926.json).

The T15 setup proof group failed its interruption audit when another user acquired
a successor socket lease. Five owned-cleanup and two interruption fixture tests
executed successfully, but only the owned proof sealed. The group remains failed,
with the entire 600-second/2-GiB reservation retained despite actual elapsed
297.915705 seconds and 1,548,288 allocated bytes. No rerun or retrospective proof
promotion is authorized by this checkpoint. See [failed group](observations/setup-recovery-proofgroup-failed-20260926.json).

Both prepared provider/native evidence packets were pushed and imported as exact
Git blobs in `c2c2dc6d87e73fdfd9db8e3b9eb1c2f856e0e5c9`. Fresh validation finds
247 valid records; representative public get/chain queries pass. Native
qualification remains pending. See [durability verification](observations/approved-evidence-durability-20260926.json).
Tickets remain 14 resolved / 7 claimed, final coverage 0/8, qualified gain false.
RSS and historical lease-closure repairs are under review; T20 has not started.

## Standing transfer authorization and resumed work — 2026-09-26 23:09 ET

The user's [standing authorization](observations/standing-transfer-authorization-20260926.json)
explicitly covers private project source and research evidence in all pending
and future task-related transfers to the named private repository/branches,
mbit10 through Git, and Anthropic through Claude Code. Changes of commit, file
inventory, size or task branch alone do not require another question. Credentials,
unrelated data, public publication and destructive operations remain excluded.
Original budgets, frozen settings and failed evidence are unchanged.

The reviewed runtime `eb2f51d` was pushed successfully to
`codex/bfs-recovery-runtime-20260926-a2`. The host worker may prepare the isolated
recovery checkout and fresh bounded a4 proof envelope; the evidence worker is
resuming the exact provider/native packet transfers, and the proposal worker
is resuming the already bounded context-supplemented Claude continuation.

The [23:03 full audit](observations/health-20260926-2303.json) retains T16 on
node 0 generation 332, with zero completed samples and no sealed ROI/stats.
Node 1 is again held, generation 423, and is unavailable for our new jobs.
The latest helper upstream tip requires a fresh bounded Git-object comparison
before dispatch; active checkout and T16 remain unchanged. Next full audit:
23:33 ET. No ticket or coverage cell is resolved by transfer alone.

## Heartbeat and lane coordination — 2026-09-26 22:42 ET

The [fresh bounded observation](observations/host-light-2242-20260926.json)
confirms T16 remains on node 0 generation 332 with the same gem5 PID/start
identity, zero completed samples, 30,953,414,656-byte sampled tree RSS and
1,762,017,280 charged bytes. ROI seal/stats remain absent; advancing tick output
is not a completion or ETA. The original stage and outer deadlines are unchanged.

Node 1 is now occupied: generation 418 was acquired at 22:40:03 ET by a separate
MemAcc upstream-reference measurement (`t16_upstream_ref_measure`, with an
observed RSBench descendant). Owner PID/start and kernel holder match the lease.
This is not this BFS campaign despite the other job's T16 label. No signal,
claim, command or lease change was made. Both socket lanes are currently occupied;
legacy generation 77 remains released. New BFS work must wait for a genuinely
free lane as well as the pending exact runtime transfer approval.

The [helper comparison](observations/helper-upstream-comparison-20260926.json)
closed the upstream-revision question: `socket_lane.sh` and the entire host-script
subtree are byte-identical at installed `42ce8dce` and upstream `8b572e8b`. The
object was already present; no fetch or active-checkout update occurred. The host
worker remains responsive, and both review workers completed normally. Next full
audit remains 23:03 ET; the heartbeat is active. No ticket or coverage cell is
newly resolved by these operational observations.

## Host and worker checkpoint — 2026-09-26 22:33 ET

The [full audit](observations/health-20260926-2233.json) confirms node 0 held at
generation 332 with the expected kernel holder; node 1 generation 416 and legacy
77 are released, with no corresponding kernel lock. The host worker is running
and responsive; both review workers completed their assigned reviews normally.
No dead worker or competing lane holder was found. Closed roots and historical
hashes remain unchanged. Free space is 16.18 GiB on `/data1` and 169.98 GiB on
`/data`; available memory is 58.47 GiB on node 1 and 88.92 GiB globally.

| Ticket or case | Status | Host / lane | Evidence | Next action |
|---|---|---|---|---|
| 01–14 | resolved | — | 14/21 tickets | Preserve accepted evidence |
| T15 recovery | reviewed, transfer pending | local; node 1 free | Fixed charges/hard end; Linux proof unrun | Exact transfer approval, then a4 proof/admission |
| T16 | running, zero completed samples | mbit10 / node 0, 332 | Same gem5 PID/start; 30,948,171,776-byte tree RSS; 1,756,381,184 charged bytes | Original stage bound, no retry |
| Full regression | passed | local / d5e2159 | 2,258 passed, 20 skipped | Retain exact revision evidence |
| New runtime | reviewed and locally tested | local / eb2f51d | 553 passed, ten Linux-only skips | Exact 26-file transfer question pending |
| Final acceptance | incomplete | — | 0/8 cells; no qualified gain | Seven tickets remain claimed |

The first T16 simulation stage started at 20:24:25.226146 ET with a 14,400-second
limit, corresponding to September 27 00:24:25.226146 ET; its existing monotonic
guard remains authoritative. A bounded prefix contains the author's ROI-start
marker, while the sealed ROI and ROI stats are absent. The latest bounded tail
shows tick 225,936,615,500. This is activity and entry evidence, not completion
or a remaining-time estimate. The marker prints `omp_get_num_threads()` from
serial scope (`apps/dx100/benchmarks/gapbs/src/bfs.cc:339`); its value of one does
not observe the later traversal team's size. Requested four-thread settings
and actual team observations remain distinct.

Remote Memacc upstream advanced to `8b572e8bbb20d60da32809746ca70fb9840cfc9e`.
Installed helper commit `42ce8dce` and script hash `00c269b4` remain unchanged.
A bounded Git-object comparison is in progress before any new lane dispatch;
no running helper checkout, job or lease is changed. Next full audit: 23:03 ET.
The 30-minute heartbeat is verified ACTIVE.

## Corrected exact runtime packet — 2026-09-26

The superseding local packet `eb2f51d0a02b7d3d1ca9cc02b022a18f1181a3e2` contains
26 files / 471,563 bytes, solely based on published `d5e2159`, for private branch
`codex/bfs-recovery-runtime-20260926-a2`. [Exact inventory](observations/recovery-runtime-export-a2-20260926.json),
[independent dependency review](observations/recovery-runtime-export-a2-standards-20260926.json),
and [isolated validation](observations/recovery-runtime-isolated-a2-20260926.json)
are retained. All 553 checks passed with ten Linux-only skips. The reviewer
verified the complete runtime/test trees, transitive local dependencies, old
plans, and exclusion of all held provider/native packet paths and ancestry.

This includes the previously rejected T17 code plus its proof-reader repair,
the SQLite allocator fix, fixed setup recovery, and reviewed native/primary-reuse
helpers. It remains unpushed and needs new exact payload approval; no attempt
is made to bypass the earlier automatic-review rejection. The older T17-only
`46f3a264` and dependency-blocked `37c02c55` packets remain unused. Fresh actual
Linux proofs, original-clock admission and guest execution remain required.

## Pinned regression and export integration review — 2026-09-26 22:26 ET

The complete isolated regression at published `d5e2159` finished at 22:25:58 ET:
**2,258 passed, 20 skipped in 3,431.29 seconds**, with the same final commit and
no tracked changes. The [receipt](observations/full-regression-d5e2159-complete-20260926.json)
pins the full log. Later allocator/recovery/T17 changes are outside that result.

The preliminary combined runtime `37c02c5` passed 489 isolated checks with ten
Linux-only skips, but [independent export review](observations/recovery-runtime-export-standards-blocker-20260926.json)
found the inherited T17 proof reader requires four cases while the changed
runtime supplies five. The exact packet remains local and is marked superseded
before transfer. The [reader repair](observations/t17-five-case-proof-preparation-20260926.json)
now requires the current five-case proof and exact allocator identity for T17,
while preserving historical scalar four-case reads. Ninety affected checks and
28 final focused checks passed; [independent review](observations/proof-cardinality-standards-recheck-20260926.json)
passed ten checks, including the actual T17 orchestration seam. A superseding
exact packet still needs isolated validation and payload-specific approval.

## Setup recovery reviewed — 2026-09-26

The [new fixed recovery plan](../../docs/bfs-t15-setup-recovery-20260926.md) has
266 passing affected tests, eight Linux-only skips, and 54 passing independent
review checks. The prior failed attempts remain failed. Flat charges, the actual
09:14:09.851819 ET hard end, and full-series admission remain enforced. A new
five-case owned Linux proof plus the two interruption cases is mandatory before
this attempt. Exact combined runtime preparation and transfer approval remain
pending; no new host job has started. See [preparation](observations/t15-setup-recovery-preparation-20260926.json)
and [independent review](observations/setup-recovery-standards-review-v2-20260926.json).

## Host and worker checkpoint — 2026-09-26 22:03 ET

The [full host audit](observations/health-20260926-2203.json) confirms node 0
held at generation 332 with the expected kernel holder, node 1 released at 416
with no kernel lock, and legacy 77 released. No other user claimed the free lane.
All three workers are running and responsive. Historical code, lease helper and
closed output hashes/counts are unchanged. Free disk is 16.18 GiB on `/data1`
and 170.00 GiB on `/data`; load is 1.32/1.28/1.26.

| Ticket or case | State | Host / lane | Evidence and next action |
|---|---|---|---|
| 01–14 | resolved | — | 14/21; preserve accepted evidence |
| T15 original and correction | failed, independently closed | mbit10 / node 1 released | No corrected guest execution; local recovery design only |
| T16 | running, zero samples | mbit10 / node 0, 332 | 30,946,598,912-byte tree RSS, 1,735,983,104 charged bytes; original 14,400-second simulation bound |
| Allocator repair | reviewed locally | local | 127 affected and 24 independent cases passed; fresh Linux admission remains |
| T17 diagnostic | prepared, transfer blocked | local | Five-file export question pending; eventual runtime also needs allocator repair |
| Native candidate preparation | reviewed locally | local | Exact dispatch accounting and retained primary reuse; protocol gates remain |
| Full regression | running | local / d5e2159 | About 63%; no final result |
| Final acceptance | 0/8 complete | — | Seven tickets claimed, no qualified gain |

A [bounded 22:05 metadata read](observations/t16-roi-progress-2205-20260926.json)
found current T16 simulation output at tick 175,936,615,500. The last 16 KiB had
no ROI-sealed marker or exit cause; sealed ROI/stats/post-ROI files were absent.
This is activity evidence, not a completed ROI or an estimate of remaining time.
Next full host/worker audit: 22:33 ET. The heartbeat remains active.

## Transient SQLite repair reviewed — 2026-09-26 22:01 ET

The [process-free allocator repair](../../docs/bfs-storage-transient-entries-20260926.md)
handles descriptor-relative confirmed nested `ENOENT` without treating a missing
charged root, permission error or unsafe replacement as zero bytes. Reappearing
entries are measured without following symlinks; root identity is checked again
at the end. Allocation semantics, guards and final quiescent recount stay fixed.
The [author's affected group](observations/storage-transient-entry-preparation-20260926.json)
passed 127 cases, and [independent review](observations/storage-sqlite-standards-review-20260926.json)
passed 24, including the unchanged real SQLite race reproducer and root/error/
deadline controls. Original source, red logs and both actual failed attempts are
retained. No new Linux proof, guest run or acceptance is inferred.

Assumption for prospective planning: a separately reviewed setup-failure recovery
may proceed under the user's autonomous bug-fix/evaluation authorization, while
the used correction remains consumed. It must charge every prior envelope and
all new preparation inside the original 43,200 seconds/40 GiB, keep the earlier
actual hard end of 2026-09-27 09:14:09.851819 ET, and require each complete series'
21,600 seconds plus cleanup before starting. This is design work only, not a
retry, new allowance, export approval or extension of the historical plan.

## Future candidate-run fixes reviewed — 2026-09-26 21:56 ET

[Primary reuse](../../docs/bfs-simulator-primary-reuse-20260926.md) adds a
frozen-complete-call-only `--primary-build` option. The exact retained source,
compiler, generated inputs and binary are reopened before and after the grid;
no primary compilation is issued. Defaults for current T15/T16 paths are
unchanged. [Author checks](observations/primary-reuse-preparation-20260926.json)
passed 130 cases; [independent review](observations/primary-reuse-standards-review-20260926.json)
passed 32 cases including post-grid binary and metadata corruption rejection.
These are local contracts, not a simulator measurement or a new campaign grant.

[Native storage preparation](observations/native-dispatch-storage-preparation-20260926.json)
now charges the exact wrapper `.dispatch` sibling inside the original 16 GiB
cap, with no double-counting of a nested record view. The original 4 GiB build
subset remains. A separate caller-pinned post-helper recount includes terminal
and late wrapper/record writes. [Independent review](observations/native-storage-root-review-20260926.json)
passed 26 cases including the original reproducer and new late-write checks;
65 author cases passed with two Linux-only skips. Actual Linux proof and native
admission remain pending. This accounting path preserves its existing byte
metric and is separate from the simulator allocator race now under repair.

## Corrected T15 failed before guest execution — 2026-09-26 21:56 ET

The [failed correction and terminal audit](observations/t15-correction-failed-terminal-20260926.json)
retain a real storage-monitor race: SQLite removed `.swdb.sqlite.3156540.tmp-journal`
between directory enumeration and metadata inspection. The driver failed at
21:52:07 ET; the public operation was interrupted at `execution_identity` before
any guest execution. There are zero completed samples or correctness checks.
The original failed attempt and this correction remain separate failed records.

The independent closure checked 105 PID/start identities twice: 104 absent and
only the exact launcher zombie with zero RSS. Node 1 generation 416 released and
its kernel lock cleared; node 0 generation 332 remains held for T16. The shared
cleanup ledger settled all 90 events in 13.349886 seconds without outstanding
reservations. Final retained raw plus dispatch bytes are 11,886,592. The entire
outer-start-to-final-recount envelope was 200.296152 seconds (ceil 201), distinct
from the driver's 82.02284-second interval. No retry is authorized by the used
fixed correction plan. The allocator's transient-child handling is under local
repair and independent review; old output roots remain frozen.

The [five-file T17 export](observations/t17-diagnostic-export-20260926.json)
`46f3a264` passed [independent exact-blob review](observations/t17-diagnostic-export-standards-20260926.json),
but automatic approval review rejected its push because the earlier exact
transfer list does not cover this new 41,823-byte internal code/metadata payload.
A payload-specific approval question is pending; no alternate transfer is used.
Local implementation and T16 monitoring continue. Counts remain 14 resolved,
seven claimed, zero of eight final cells, and no qualified gain.

## Corrected T15 started — 2026-09-26 21:52 ET

The separately bounded corrected batch started at 21:50:45.851819 ET on node 1,
generation 416, with exact code `d5e2159` and
[admission](observations/t15-correction-admission-20260926.json) `0c6ed8bc`.
[Independent admission review](observations/t15-correction-admission-standards-final-20260926.json)
checked the actual proof closures, 152 runtime hashes, original costs and wrapper
clock. Its hard end is 2026-09-27 09:14:09.851819 ET, exactly 41,004 seconds after
the actual outer start. The later prospective ceiling cannot extend that clock.
At the initial 21:51 readback the driver was performing charged preflight with
zero series or guest samples. T16 remains on node 0, generation 332. Both lanes
are occupied; there is no third evaluation job. The [actual launch receipt](observations/t15-correction-actual-launch-20260926.json)
binds original clocks, pane identity, generation, fresh capacity and all charged preparation.

## Actual correction proofs and fresh coverage — 2026-09-26 21:44 ET

The [new d5e Linux proof group](observations/t15-correction-linux-actual-20260926.json)
completed at 21:38:25 ET: four owned-cleanup cases and two public interruption
cases passed; helper, fixture, independent auditor and wrapper exits were zero.
Node-1 generations 414 and 415 released. The final five-root read-only count was
1,527,808 bytes after 184.252108 seconds. The full reserved 600 seconds and 2 GiB
remain charged, without refund. Both closed original-root pairs matched the new
allocator against Linux `du`. Final actual admission review is pending; no
corrected guest run has started.

The [fresh public coverage query](observations/acceptance-checkpoint-20260926-a3.json)
rebuilt its own temporary index from 218 valid local records. The result remains
0/8 completed cells, incomplete acceptance and no qualified gain. Published
T16 protocols do not imply completed comparisons; no candidate protocol or
reference comparison is selectable yet. Held remote provider/native evidence
and external raw-artifact availability remain outside this local report.

## Host and worker checkpoint — 2026-09-26 21:33 ET

The [full host audit](observations/health-20260926-2133.json) confirms node 0
held at generation 332 for T16, node 1 released at 413, and legacy 77 released.
T16's first scalar source/repetition remains running with zero completed samples,
30,931,394,560 bytes of tree RSS, and 1,715,388,416 charged bytes. Its unchanged
simulation limit is 14,400 seconds, not T15's one-hour limit. Free disk was
17,370,226,688 bytes on `/data1` and 182,565,216,256 on `/data`; load was
1.09/1.19/1.25. Active measured code and historical receipts remain unchanged.
All three workers are responsive; completed preparation/review workers are
reassigned to review the actual correction admission and T17 diagnostic build.

| Ticket or case | State | Host / lane | Evidence and next action |
|---|---|---|---|
| 01–14 | resolved | — | 14 of 21; no acceptance inferred from later fixtures |
| T15 original | failed, closed | mbit10 / released | Storage guard; retain all failures |
| T15 correction | preparing admission | mbit10 / node 1 | Exact d5e export and wrappers reviewed; new Linux proofs required |
| T16 | running; zero samples | mbit10 / node 0, 332 | First scalar execution; monitor original clock |
| Scalar v2 | four builds complete, outer preparation failed | mbit10 / released | Reopen individual builds before reuse; no rebuild |
| T17 diagnostic | prepared | local | 24 focused checks; independent review pending |
| Full regression | running | local / d5e2159 | Exact exported code; no result claimed |
| Final acceptance | 0/8 complete | — | Seven tickets claimed; no qualified ROI gain |

The [wrapper review](observations/t15-correction-wrapper-standards-20260926.json)
found no issue in the fixed 600-second proof-group scripts. The
[T17 preparation receipt](observations/t17-diagnostic-build-preparation-20260926.json)
separates actual subprocess tests from synthetic host/compiler outputs. Neither
is a completed BFS acceptance case. Next full host/worker audit: 22:03 ET.

## Corrective runtime exported — 2026-09-26 21:29 ET

The reviewed 21-file correction export `d5e215966a7d4d673050a78c6a6d77053aa62a85`
is pushed and its remote tip verified, directly parented by scalar preparation
`6732d53`; [exact inventory](observations/t15-gzip-correction-export-20260926.json).
It contains 533,439 bytes of code, tests, fixed plan and procedures, with no
held application source/profile packet. The new mbit10 checkout is pristine;
active T16 remains on `8c39ae0`.

The [combined targeted suite](observations/t15-correction-storage-preparation-20260926.json)
passed 351 tests with three Linux-only skips in 27.50 seconds.
[Independent storage review](observations/storage-standards-review-20260926.json)
passed real local `du` parity, actual cleanup-overlap and path-substitution checks.
A separate full regression started at this exact export in the reused clean
validation worktree at 21:28:47 ET; its result is pending. These local checks do
not replace the new actual Linux proofs or retained-host-root allocation parity.
The fixed 600-second proof group follows the 21:33 health check, then a new
sealed admission is required before the corrected T15 BFS run.

The apparent one-hour T16 timeout concern was rejected by reading its exact
retained request and stage: the simulation allowance is 14,400 seconds, with a
separate 3,600-second checkpoint allowance. The live stage started at 20:24:25 ET
and remains within that original limit. No setting or process was changed.

## Four scalar builds retained; supervisor failure preserved — 2026-09-26 21:21 ET

All four scalar v2 public compilations and their four result/chain checks returned
zero. The shared preparation supervisor then failed during final storage
accounting when ownership cleanup killed a monitor-spawned `du` process. Its
helper and outer exit were one; the whole preparation remains failed. The
[independent terminal audit](observations/scalar-v2-failed-terminal-20260926.json)
reopened all four completed build records and binary hashes, checked all 31
retained identities twice (30 absent and the exact zero-RSS pane zombie), and
verified node 1 generation 413 released. The final cleanup ledger has 37 settled
events totaling 2.084549 seconds. All output is retained: 17,801,216 bytes total,
including 4,337,664 build bytes. No build retry is authorized by this result.
The four binaries remain correctness-unverified, with empty timings and no gain.

The worker reproduced the same `du`/cleanup race locally with a real subprocess.
A shared process-free allocation reader is being reviewed for future batch,
series and scalar supervision. Active T16 remains on unchanged `8c39ae0`.
The successful build records may be revalidated by their future required
consumers; they do not turn the failed whole preparation into a pass.

The [new fixed corrective T15 plan](requests/bfs-t15-correction-simulator-batch-20260926-a1.json)
has digest `4bc526b7aa86ff09499a6478f7068319357789ca27fedb58a011d5b75937b7ea`.
It preserves the original science and 43,200-second/40-GiB aggregate, charges
1,124 seconds for the failed attempt through closure, 472 seconds for the
smoke preflight-to-final-recount envelope, and a full 600-second/2-GiB
reservation for two future Linux proofs and their complete audits. The
remaining allowance is 41,004 seconds and 29,787,017,216 bytes before new
batch work. Prior plans and IDs remain unchanged. The
[independent accounting review](observations/correction-reservation-standards-final-v2-20260926.json)
passed its focused checks after reproducing and fixing omitted auditor exit and
finish-time validation. This is preparation only; no corrective BFS run has begun.

## Progress check and actual gzip transport proof — 2026-09-26 21:03 ET

The [full host audit](observations/health-20260926-2103.json) confirms T16
remains on node 0 generation 332 with the same gem5 PID/start identity. Its first
artifact scalar primary is running with zero completed samples. Sampled tree RSS
is 30,857,994,240 bytes; charged output is 1,694,466,048 bytes. Node 1 generation
412 and legacy 77 are released. Disk headroom is 16.20 GiB on `/data1` and
170.06 GiB on `/data`; the lane helper matches current upstream. All three
workers are active. There are still 14 resolved and seven claimed tickets,
zero final candidate acceptances, and no qualified gain. Next full check: 21:33 ET.

The [actual no-guest gzip transport proof](observations/gem5-gzip-actual-20260926.json)
passed on the pinned gem5 binary: complete gzip EOF/CRC, first event in gzip,
second event after switching to plain output, and a separate stdout marker.
It ran from 20:58:40 to 20:58:43 ET and passed independent closure at 21:00 ET.
All five retained identities are terminal, the final cleanup ledger settled
within its original reserve, and retained output totals 200,704 bytes. The
short child fell between RSS samples; the sampled peak is not its measured
maximum. This is a no-guest transport contract, not BFS execution evidence.
The [exact two-file auxiliary export](observations/gem5-gzip-export-20260926.json)
is `179afc0`, directly parented by the unchanged borrowed runtime `8c39ae0`.

The four scalar builds are admitted but were not started at the full audit.
The gzip adapter is undergoing independent replay review, with reproduced
provenance defects retained and repaired before export. The separately bounded
[T15 correction preparation](../../../docs/bfs-t15-gzip-correction-20260926.md)
retains the original failed attempt and its costs. No corrected BFS attempt or
new scientific protocol has started.

## T15 retained storage failure and next prerequisites — 2026-09-26 20:46 ET

T15's first uniform18 primary ended as `budget_exhausted` during simulation:
`raw artifact storage budget exhausted`. Correctness is unverified because no
sealed ROI receipt was produced; no replay, diagnostic, or Kronecker sample
started. The [canonical failure and independent terminal readback](observations/t15-failed-terminal-20260926.json)
retain the exact outcome and closure. The outer attempt consumed 942.616 seconds.
All 181 retained PID/start identities were checked twice: 180 absent and the
exact pane a zero-RSS zombie. Socket 1 generation 411 released. The final shared
cleanup ledger has 23 settled events totaling 1.608397 seconds, with no outstanding
or exceeded grant. Final post-helper/audit storage is 11,014,971,392 bytes across
both retained roots, below the batch cap; this does not negate the sample's
10-GiB storage failure. Those roots remain unchanged.

The output is explicit per-element accelerator coverage tracing, dominated by
`MAAIndirect` messages unused by the coverage parser. The prospective correction
will preserve every trace byte through gem5's native gzip debug output and reopen
it consistently in collection and replay. No active settings, graph, model,
ROI, thresholds, or allowances have been changed. Any explicitly planned corrected
attempt must retain and charge the failed attempt rather than resume its ID or
reset its budget. T16's scalar measurement continues unchanged on node 0.

The exact eight-file scalar preparation export `6732d53` is now pushed and its
remote head verified; [inventory](observations/scalar-v2-export-20260926.json).
It contains only reviewed build preparation code/tests/docs and the four original
requests plus fixed manifest. No build has run. The next free-lane sequence is a
reviewed, bounded no-guest native gzip transport check, followed by the four
scalar builds with a fresh sealed admission and capacity checks. Neither step
may take a third lane or alter T16's active checkout.

## Regression result and scalar build preparation — 2026-09-26 20:40 ET

The full local suite finished on unchanged `d11dc04` at 20:34 ET:
**2,101 passed, 20 skipped** in 3,235.89 seconds, exit zero;
[complete receipt](observations/full-regression-d11dc04-complete-20260926.json).
This verifies that pinned local code. The later `8c39ae0` dispatch-storage
correction has its separate 201-pass targeted selection, independent 15-pass
selection and fresh actual Linux ownership/interruption proofs.

The [four-scalar-build recipe](../../../docs/bfs-scalar-v2-builds-20260926.md)
is prepared and locally tested: 49 cases passed, and the independent reviewer
passed 34 selected cases including a real public `get`. The review found a
concurrent clock-accounting race; it is reproduced, fixed with coherent locked
state, and retained in the [preparation evidence](observations/scalar-v2-build-preparation-20260926.json).
Loader overrides are rejected at startup and cleared for child processes;
[independent review](observations/scalar-v2-standards-review-20260926.json).
The exact four requests and 1,200-second envelope are unchanged. No build has
been dispatched, and no host success or guest result follows from these tests.

The 20:33 ET [full host audit](observations/health-20260926-2033.json) found both
owned socket leases held, the legacy lease free, all workers healthy and both
first samples in actual gem5. T15's raw volume was dominated by 6.905 GiB of
per-element debug text. The host subsequently reported its first sample failed
under the existing 10-GiB per-execution guard, with no completed sample; full
terminal readback is pending. T16 continues. This failure remains retained;
there is no automatic restart or increased allowance. A lossless trace transport
correction is under investigation, with explicit accounting of the consumed
attempt required before any prospective corrected run. Next full check: 21:03 ET.

## Both simulator batches launched — 2026-09-26 20:23 ET

Both fixed batches are actually running on the isolated, unchanged `8c39ae0`
checkout: [actual launch observation](observations/campaign-actual-launch-20260926.json).
The corrected [Linux proofs](observations/standard-fixtures-a2-actual-20260926.json)
passed all four ownership and two interruption cases, with independent audits
and released proof leases. The [new admissions](observations/campaign-admissions-a2-20260926.json)
were sealed at 20:15:15 ET, before the narrowed 20:20 ET earliest start;
[independent admission and launcher review](observations/campaign-admission-a2-standards-review-20260926.json)
passed. The original unused admissions remain retained.

| Batch | Actual start / host lane | Current observation | Same original allowance / actual clipped end | Next action |
|---|---|---|---|---|
| T15 | 2026-09-26 20:21:15 ET / mbit10 node 1, generation 411 | Charged input validation passed; first uniform18 series entered at 20:21:49 ET | 43,200 seconds; 2026-09-27 08:21:15 ET | Complete ordered pilot collection, then qualify evidence and freeze source-specific protocols |
| T16 | 2026-09-26 20:20:30 ET / mbit10 node 0, generation 332 | Charged input validation passed; first artifact-scalar series entered at 20:21:06 ET | 86,147 remaining seconds after 253 seconds prior preparation; 2026-09-27 20:16:17 ET | Complete ordered reference/control collection and two public comparisons |

These starts and series-entry events do not establish a completed guest result,
correctness, profiling success, or gain. Both keep the same storage limits and
one shared 30-second cleanup reserve each, including the corrected dispatch
accounting. No third lane is used. The next full host/worker check is 20:33 ET.
Ticket totals remain 14 resolved and seven claimed, with 0/8 final candidate
acceptance cells and no qualified gain.

## Dispatch storage repair verified locally — 2026-09-26 20:11 ET

The repair counts the exact canonical run root and sibling `.dispatch` in
sampling and driver finalization. A separate read-only terminal check reopens
the fixed plan and preparation charges and counts completed helper/audit output
against the unchanged ceiling. The host worker confirmed the required persisted
result followed by a final read-only recount after the last charged-root write.
[Preparation and tests](observations/simulator-dispatch-storage-preparation-20260926.json)
retain the reproduced failure and subsequent 201 passes / three Linux skips;
[independent review](observations/simulator-dispatch-storage-standards-review-20260926.json)
found no issue and independently passed 15 storage tests. These are local
contract tests, not empirical execution. The exact six-file export `8c39ae0` was pushed and its remote head verified;
[export inventory](observations/dispatch-storage-export-20260926.json) and
[independent Git-tree review](observations/dispatch-storage-export-standards-review-20260926.json). Fresh
matching Linux proofs are next. Only the two consumed
simulator proof IDs advance to fixed `a2` identities; guest batch IDs and
budgets remain unchanged.

## Progress check and prelaunch accounting correction — 2026-09-26 20:03 ET

Both socket leases and the legacy lease were released at the full 20:03 ET
[host audit](observations/health-20260926-2003.json), with no live retained owned processes. All three assigned workers
were responsive. Both capacity gates passed, with 17,433,550,848 bytes free
on `/data1` and 194,145,558,528 bytes on `/data`. No simulator batch had started;
both exact new batch roots were absent.

The [actual standard Linux proof summary](observations/standard-fixtures-actual-20260926.json)
records four ownership and two interruption cases passing on `d11dc04`, with
independent cleanup checks and released leases. Both [sealed admissions](observations/campaign-admissions-20260926.json)
passed real input validation, and [independent literal launch review](observations/campaign-admission-standards-review-20260926.json)
found their hashes, runtime, clocks, charges, and argv consistent. They remain
unused preflight evidence. Before launch, the host identified that the batch
sampled its run root but omitted the sibling `.dispatch` directory containing
helper and outer-process output. The repair will include both directories in
the existing storage allowance and recount terminal writes. No empirical
attempt or budget has been reset. New code requires fresh matching Linux
proofs; the original `d11dc04` proof evidence remains valid for that pin.

The exact-`d11dc04` full local regression remains running and has progressed
past 50% without a failure appearing in the log. This is local regression
progress, not native or DX100 acceptance. Ticket totals remain 14 resolved
and seven claimed; final candidate acceptance remains 0/8, with no qualified gain.

## Final-pin checks and future baseline builds — 2026-09-26 19:53 ET

The independently verified campaign export `d11dc04` is published and installed
in a pristine mbit10 checkout. A complete local regression started at 19:40 ET
on that exact pin, with a 7,200-second limit; [start receipt](observations/full-regression-d11dc04-start-20260926.json).
Its result is pending. Both actual standard Linux selections finished with
exit zero and have independent passed audits: four ownership cases and two
interruption cases. Both leases released before their original 90-second ends.
The subsequent 20:03 ET entry above records the prelaunch storage-accounting
correction discovered after these checks. The earlier wrapper newline concern was disproved by byte-level
and actual local render checks; [independent review](observations/standard-fixture-render-standards-review-20260926.json).
No change or attempt resulted from that rejected concern.

Four necessary unchanged-scalar v2 primary/diagnostic [build requests](requests/scalar-v2-20260926-a1.preparation.json)
are prepared for the DX100 and upstream baselines. They retain each historical
120-second build / 240-second API / 16-GiB RSS / 1-GiB artifact bound. A separately
proposed 1,200-second compile-only envelope accounts four calls and one shared
cleanup reserve; it does not replenish earlier attempts. Four real local
entrypoint probes stopped at host mismatch before any build, and 222 temporary
records validated; [receipt](observations/scalar-v2-request-validation-20260926.json).
These are prepared requests, not host compilation evidence. Their execution
clock and host/runtime gates remain unsealed, and they cannot take a third lane.

## Progress check and actual T16 freezes — 2026-09-26 19:33 ET

The [host audit](observations/health-20260926-1933.json) found both socket leases
and the legacy lease released (331/406/77), no kernel locks or live owned work,
and unchanged historical receipt/code identities. All three workers are responsive.
Available disk is 17,453,592,576 bytes on `/data1` and 194,147,344,384 bytes on
`/data`; both nodes meet current memory gates. Capacity must be rechecked at launch.
Ticket counts are 14 resolved, seven claimed, and 0/8 final acceptance. Next full
host/worker/ticket check: 20:03 ET.

The [actual T16 metadata operation](observations/t16-freeze-actual-20260926.json)
completed all four public freeze/get-chain commands with exit zero. It published
`bfs-author-reference-20260925.b4cbd3924b40e7df` and
`bfs-author-matched-control-20260925.d02e719e2d375764`, matching the exact prepared
settings and fresh retrieval. Both records were pushed in source-free `5db2bec`,
imported as `9cd2f82`, and independently checked locally for file/canonical/settings
hashes and immutable identity. These are the independent T16 policies; native
and candidate-specific simulator protocols remain pending.

The first launcher failed before any public command because pane-PID quoting
produced a literal dollar. Its failure remains retained with an incomplete
historical PID union; a current full-operation scan found no live survivors.
The corrected launcher spent the same original 19:30:05–19:40:05 ET operation
window, ending at 19:33:21 ET (196.471 seconds including the failed launch).
No public request was retried. The second launcher has an independently audited
eight-identity union, seven absent and only its exact zero-RSS pane zombie;
generation 331 is released. This metadata operation ran no guest measurement.

The prospective final campaign source is a separate child of the five-record
metadata chain. Its fresh standard Linux checks and absolute T15/T16 admissions
remain required before batch execution; no reference/control result is claimed.

## Accounted public databases — 2026-09-26 19:35 ET

The same real-CLI cache-placement defect was reproduced in simulator series
and protocol publication: their public queries created an unaccounted
checkout-root database. The series now owns SQLite inside its raw driver folder;
the publisher requires an explicit external `--db` and rejects paths overlapping
code, records, input or the not-yet-created output directory. Every public call
uses that path. Qualification logic, clocks and failed-prepare output ordering
remain unchanged. Callers account the selected database and its sidecars.

The [repair receipt](observations/public-client-database-fix-20260926.json)
retains original failures and 197 passing focused tests with two Linux-only
skips. The [independent review](observations/client-database-spec-review-20260926.json)
passes all 11 scoped cases, including actual public get/freeze/get. These are
contract fixtures, not empirical publication or measurements. The already
specified T16 public commands use an external database and are unaffected.

## Actual coverage and native runtime repair — 2026-09-26 19:20 ET

DX100 A2 completed all six public stages with correctness passed at 19:16 ET.
Its exact `5a0b15f` completed reader reopened the actual artifacts at 19:17 ET:
8 full tiles, 8 tail tiles, and 14,546 competing-parent updates inside the
selected ROI. The independent terminal audit checked all 14 retained PID/start
identities twice: 13 absent, with only the exact completed pane a zero-RSS zombie;
node 0 generation 329 is released. Peak sampled RSS was 34,732,048,384 bytes.
See [actual readback](observations/dx100-coverage-a2-completed-readback-20260926.json).
T13 is resolved against all eight ticket criteria; its [Answer](issues/13-dx100-timed-binary-correctness.md#answer) records the evidence and limits. This establishes finite coverage, not a candidate gain or final acceptance.
The three source-free canonical records (64,110 bytes) were pushed as `21d58c4`,
imported locally as `916043c`, and rehashed against the [exact inventory](observations/dx100-coverage-a2-record-inventory-20260926.json).

The future native campaign now routes every public CLI database into its
accounted raw driver directory, preventing a generated checkout-root `build/`
from invalidating the runtime guard. The real CLI regression reproduced the
failure before repair; 149 focused tests pass with two Linux-only skips, and
independent review is clean. [Fix receipt](observations/native-campaign-database-fix-20260926.json)
and [Spec review](observations/native-campaign-database-spec-review-20260926.json)
retain red and green evidence. This change does not alter measured checkouts.

[T16 preflight](../../docs/bfs-t16-freeze-preflight-20260926.md) and the
[post-A2 sequence](../../docs/bfs-post-a2-batch-sequence-20260926.md) now explicitly
place public SQLite caches outside the runtime checkout. Actual T15/T16 batches,
protocol publication and candidate acceptance remain pending.

## Evidence-integrity review correction — 2026-09-26

Independent Standards review reproduced a profile-package seal downgrade: a
missing version field bypassed identity checking. The [T09 repair](observations/profile-package-identity-repair-20260926.json)
now rejects that downgrade and removal of all seal fields under an assembly ID.
The public package suite passes 49 tests and all 213 catalog records validate;
all six explicit legacy fixtures remain retrievable. Independent recheck is
clean. T09 remains resolved. Independent Spec review separately found a paired
coverage statistics/provenance error. Its [repair](observations/paired-coverage-repair-20260926.json)
passes seven new/reproduction cases, 24 existing cases and three independent
edge checks, including refusal when raw paired evidence is missing. Both review
findings are closed; empirical acceptance remains incomplete.
The full local suite at isolated `c2f987b`, before these two fixes, finished
with 1,950 passes, 18 skips and three failures; see the 17:03 checkpoint below.

## Prospective supervision reviewed — 2026-09-26

The [simulator supervisor verification](observations/simulator-supervision-verification-20260926.json)
retains 182 passing local tests with six Linux-only skips and unchanged source
and runtime hashes throughout the final group. It covers shared process cleanup,
continuous resource accounting, original deadlines, aggregate/protocol admission,
terminal ledger readback, and preservation of original failures. The
[native supervision verification](observations/native-supervision-verification-20260926.json)
retains 124 integration passes, the final 41 repair-probe passes and independent
review. Actual existing-candidate campaigns now require exact runtime admission,
Linux owned-process proof and one four-hour clock with its shared cleanup reserve.
Historical pinned executions remain unchanged. These are implementation checks;
no new host fixture or candidate assessment has run. Broader isolated regression
and independent Standards/Spec readiness audits follow; final all-ticket review
still follows empirical acceptance.

## Finalizer review correction — 2026-09-26

The [prospective simulator finalizer correction](observations/simulator-finalizer-clipping-20260926.json)
keeps resource sampling active through owned cleanup, clips monitor shutdown to
the remaining reservation, and admits cleanup under the original outer clock
while preserving the work-phase reserve. A secondary persistence/accounting
failure retains the original public error and its own details. Independent
Standards and Spec reproductions are repaired and retained; both scoped
rechecks are clean. The combined local group passed 123 with two Linux skips
before the final exception-note delta; all six affected final-delta cases pass.
Actual Linux admission and final acceptance remain outstanding. The separate
A2 fixture route must bind its old tested runtime and new supervisor explicitly.

## Prospective supervision code synchronized — 2026-09-26

The [verified private code sync](observations/supervision-export-sync-20260926.json)
published `3f38a2b` on `codex/bfs-supervision-20260926-a1`: 56 explicit files,
857,716 bytes, with parent `67313d9`. The updated export changes only two
reviewed test fixtures and their receipt relative to the retained first export;
all production bytes are unchanged. The exact follow-up passes 61 tests and
validates 206 records. The initial 558-pass/nine-skip/two-failure result remains
retained, along with its local Git checkpoint. Independent inventory review
confirms required T15/T16 bindings and provider/raw-artifact exclusions.
A2 tests remain pinned to old `67313d9`; their supervisor and auditor use the
new separate checkout. Actual Linux fixtures and independent host closure
remain pending until whole native completion. This sync establishes no final
acceptance cell, empirical freeze or gain.

At 17:45 ET, [Git-only preparation](observations/supervision-checkout-preparation-20260926.json)
verified pristine detached `3f38a2b` in the separate mbit10 supervisor checkout.
The collector `319645e` and historical A2 tested checkout `67313d9` remain
unchanged. No Linux fixture, auditor, compilation or measurement ran during
this preparation. The original malformed preparation receipt is retained;
an additive valid JSON receipt preserves its reference and unchanged facts.

## Actual DX100 A2 started — 2026-09-26 19:09 ET

The [fixed empirical A2 attempt](observations/dx100-coverage-a2-start-20260926.json)
started at 19:09:05.775756 ET on node 0 generation 329, exact tested `5a0b15f`.
Its original 3,600-second clock ends at 20:09:05.775756 ET, including shared
30-second cleanup. Capacity, graph generation and registration completed;
compilation was running at the 19:09:49 observation. Node 1 and legacy were
idle. No simulator result, correctness coverage, protocol freeze or gain is
claimed from this start. The runtime checkout and sealed admission remain fixed.

## A2 admission prepared — 2026-09-26 19:07 ET

The [full prelaunch validation](observations/a2-admission-prepared-20260926.json)
passed at exact `5a0b15f` with both actual Linux proofs. The first metadata
check found three missing historical coverage-a1 records. Their
[exact published Git blobs](observations/a2-fixed-records-preparation-review-20260926.json)
were materialized without overwriting records or changing HEAD, runtime,
tests, plan or proof identities. All nine fixed record digests now agree.
This preparation check did not consume the simulator attempt. The same
unused A2 case is authorized after fresh host checks, within its original
21:00 ET launch cutoff and 3,600-second allowance.

The separate [native readback a2 failure](observations/native-readback-a2-failure-20260926.json)
retains zero reader events, the untouched pytest cache, both terminal process
checks and the released lease. Its four observed identities are complete
relative to retained telemetry; unobserved short-lived startup processes remain
an explicit sampling limitation. It supplies no qualification result.

## Progress check — 2026-09-26 19:03 ET

The [full host audit](observations/health-20260926-1903.json) reports released
socket/legacy generations 328/406/77, empty kernel locks, no live owned jobs,
and sufficient current memory/disk capacity. All three workers are responsive.
The exact local regression passed with 2,075 tests and 19 skips. The two corrected
A2 Linux proofs passed and have independent review; empirical A2 remains unused.
Counts remain 13 resolved/eight claimed and 0/8 final acceptance. Next full check:
19:33 ET.

Native standalone readback a2 failed before reader spawn because its checkout
contained `.pytest_cache`, created by the manual Linux test at 18:42:49 ET.
The entry and both failed attempts remain preserved. Independent closure found
no live retained process and released generation 328. No third standalone
invocation will occur. Spec and Standards independently confirmed that this
readback is not a prerequisite to A2 or T15 collection: native qualification
remains mandatory inside the separately bounded source-specific protocol
prepare/publish steps after actual simulator calibration. No guard is relaxed
and no cache or failure evidence is deleted.

## Full regression passed — 2026-09-26 18:55 ET

The isolated [exact `e4c4015` run](observations/full-regression-e4c4015-20260926.json)
completed in 3,324.53 seconds: **2,075 passed, 19 skipped, zero failures**.
The checkout was unchanged. Original failed broad-run receipts remain retained.
Subsequent native-reader and admission-fixture edits have their separately
recorded focused checks and real Linux proofs; this broad result covers its
exact earlier commit. No empirical acceptance or gain is inferred.

## Fresh Linux admission proofs — 2026-09-26 18:53 ET

Both [corrected A2 fixture selections](observations/a2-corrected-fixtures-actual-20260926.json)
passed against tested `5a0b15f` under supervisor `4c10943`. Owned cleanup took
6.058 seconds with two passed cases; public interruption took 9.331 seconds
with two passed cases. Both stayed within their original 90-second clocks,
had zero external and audit exits, and released node 1 generations 405/406.
Their complete retained identity unions were checked twice; only the exact
zero-RSS pane zombies remained. The old failed fixture stays preserved.
These are contract admission proofs; no A2 simulator execution has occurred.

The [actual native reader proof](observations/native-reader-fast-exit-actual-20260926.json)
also passed at `5e8b750`, retaining the real fast child's identity before reap.
The corrected [readback recipe](../../docs/bfs-native-readback-preflight-a2-20260926.md)
has independent review and a Git-only auxiliary export `5e4e895`. One bounded
invocation is scheduled after 19:00 ET, followed by A2 after fresh lane checks.
No empirical freeze, candidate acceptance, or gain is claimed.

## Progress check — 2026-09-26 18:33 ET

The [full host audit](observations/health-20260926-1833.json) found both socket
leases and legacy released (326/404/77), empty kernel locks, and no live owned
jobs. Native collection remains complete (240 checks, four packages); its failed
readback remains unqualified. The old A2 cleanup fixture passed while its
interruption fixture failed host-policy validation. All three workers responded;
the corrected regression suite remains running at exact `e4c4015`. Counts remain
13 resolved, eight claimed, and 0/8 final acceptance. Next full check: 19:03 ET.

The [reviewed fixture correction](observations/a2-prelaunch-revision-20260926.json)
preserves real host lane enforcement and the original A2 measurement window and
budget. Both selections require fresh actual Linux proofs at the new tested
revision. The [reader test delta](observations/native-reader-durable-fixture-delta-20260926.json)
retains fsynced real process events; its additive export `5e8b750` is synced, with
actual Linux proof still pending.

At 18:41 ET automatic approval review rejected the new 24-record native evidence
packet `c6f16004` (3,948,624 bytes, including 12 source-bearing records totaling
2,863,879 bytes) as outside the previously approved 14-file packet. Exact approval
was requested. The packet remains on mbit10; no push or substitute transfer
occurred. This does not block independent host-local qualification or A2 work.

## Actual A2 Linux admission outcomes — 2026-09-26 18:28 ET

The [actual Linux fixture packet](observations/a2-linux-fixtures-20260926-a1.json)
retains both fixed selections against `67313d9` under supervisor `3f38a2b`.
Owned cleanup passes two cases and its independent auditor; socket 1 generation
403 is released. Both public interruption cases fail before simulation because
the fixture disables mbit10's required lane policy. Production refusal is correct;
this is a fixture setup defect, not missing dependencies or simulator behavior.
The failed generation 404 is released, all six retained identities checked twice,
and only the exact zero-RSS pane remains. No pending/passed interruption proof
exists. A narrow fixture correction and fresh prelaunch code/proof bindings are
required. The actual A2 simulator remains undispatched with its original
21:00 ET launch cutoff, workload and 3,600-second limit unchanged.

## Native reader repaired — 2026-09-26 18:23 ET

The [launcher repair](observations/native-reader-repair-20260926.json) converts
the JSON records path to `Path` in the generated child. Its regression executes
the real historical Store API. An optional observer persists the actual Linux
PID/start identity before any poll/wait and reports direct reap under the same
cleanup deadline. Observer errors reject admission while preserving an earlier
reader failure; deterministic qualification output is unchanged. The full local
file passes 57 with one Linux-only skip; independent checks pass 10 with that
same Linux skip, including three boundary probes. Actual Linux fast-exit proof
remains required. The [separate corrected attempt](../../docs/bfs-native-readback-correction-20260926.md)
has one 990-second allowance and a fixed window; final code/recipe admission is
not sealed. The failed first attempt and completed measurements stay unchanged.

## Native readback failed before validation — 2026-09-26 18:13 ET

The [single readback attempt](observations/native-readback-failure-20260926.json)
started at 18:10:50 ET and exited one before validation. The generated launcher
passed a JSON string to the original collector's `Store`, which requires a
`Path`; `.rglob` raised `AttributeError`. No control/package admission or protocol
freeze resulted. Socket 0 generation 326 is released. The fast child's PID/start
identity was not captured, so the retained receipt explicitly declines a full
historical process-closure claim. A current exact-argv scan found no live reader;
only the recorded zero-RSS pane zombie remains. The native measurements and their
independent 131-identity closure remain unchanged. The failed attempt is consumed,
without retry; the launcher repair and child-identity retention are under review.
A separately retained 18:14 ET supplement scans every current own-user process
born in a conservatively expanded launch interval on two passes. It finds only
the exact zero-RSS pane zombie. Independent review accepts this current inactivity
for separate A2 fixture admission after fresh normal host gates; it does not
change the incomplete historical reader-identity record.

The [original full regression](observations/full-regression-7fe4c34-20260926.json)
finished at 18:11:32 ET: **2,004 passed, 18 skipped, 25 failed** in 3,329 seconds.
All failures are the three independently repaired package-fixture groups. Its
original log and pin are retained; the separate corrected `e4c4015` run continues.

## Native readback prepared and synchronized — 2026-09-26 18:09 ET

The [single-readback preparation](observations/native-readback-preparation-20260926.json)
retains six author and five independent accounting probes. The exact recipe,
selection and preflight were pushed to the private auxiliary branch at `39d330f`
and its remote ref verified. The three-file packet contains 15,105 bytes and has
sole parent `3f38a2b`; supervisor and collector HEADs remain unchanged. A prelaunch
reference-shape omission was corrected additively: V2 includes the sealed driver
reference's byte count. Historical refs and all four package IDs/order match.
The fixed bound is 990 seconds: one original 900+30 reader and 60 cumulative
seconds for other checks. No retry, measurement, protocol publication or gain
is authorized by this readback. Its actual result and external cleanup audit
remain outstanding at this checkpoint.

## Progress check — 2026-09-26 18:03 ET

The [full host audit](observations/health-20260926-1803.json) confirms the completed
native study and all 131 owned identities absent. Both socket leases and the
legacy lease are released (generations 325/402/77); all kernel locks and owners
are absent. Historical receipts and code pins are unchanged, and the separate
`3f38a2b` supervisor checkout is pristine. Free build/raw space is
16.35/181.10 GiB. All three workers are responsive; next full check is 18:33 ET.
The single bounded native readback is awaiting its final recipe review; no
Linux admission fixture or subsequent measurement has started at this audit.

All 25 identified failures in the retained `7fe4c34` full regression now have
independently checked test-fixture repairs. That original run continues unchanged.
A corrected full regression started at 17:59:51 ET on exact `e4c4015` in the
separate idle managed worktree, with a two-hour ceiling and its own retained log.
Neither full run is claimed green. Counts remain **13/21 resolved, 0/8 final
acceptance cells**, with no empirical protocol freeze or qualified candidate gain.

## One-thread native collection completed — 2026-09-26 17:58 ET

The [actual terminal audit](observations/native-one-thread-terminal-20260926.json)
records successful completion at 17:56:28 ET in 10,133 seconds. All 240 primary
structural checks, four fixed controls and 24 spread groups passed. All four
fresh diagnostic packages completed with 24 structural checks and 72 valid
memory rows. The separate terminal audit found all 131 retained PID/start
identities absent on both passes, socket 1 generation 402 released and its
kernel lock empty. Sampled peak tree RSS was 1.18 GiB; the original hard end
was unchanged. One bounded readback through the original collector remains
before publisher qualification. Shared simulator gates, protocol freeze and
all eight final acceptance cells remain open; passing unchanged-code controls
is not a candidate gain.

## All one-thread primary controls passed — 2026-09-26 17:38 ET

The [fourth retained control](observations/native-one-thread-fourth-cell-20260926.json)
passes. All 240/240 structural checks and 24/24 spread groups meet the fixed
policy; neither direction of any unchanged-code comparison triggers the gain
threshold. Upstream Kronecker's maximum spread is 3.25%; forward/reverse ratios
are 0.99854/1.00146 under the unchanged 1.05 numerical floor. The same driver
started DX100 uniform profiling at 17:36:22 ET. All four fresh diagnostic
packages and independent whole-client cleanup remain required; the original
20:11:35 ET hard stop and code pin remain unchanged. No empirical freeze or
candidate gain is claimed.

## Current package seals in contract fixtures — 2026-09-26

The [campaign and reassessment fixture correction](observations/profile-seal-fixture-repair-20260926.json)
uses current assembly seals and refreshes content-addressed fixture references
after deliberate mutations. Production validation is unchanged. All 16 campaign
and 45 reassessment cases pass; independent cross-reviews confirm the intended
semantic checks, unknown-origin fields and failed-build/no-repair behavior.
The original unpublished `c0df79e` check remains **558 passed, nine skipped,
two failed** with exact files unchanged. The superseding `3f38a2b` export includes
these two fixture corrections; its affected-module/catalog checks and private
branch synchronization are recorded above.

## T17 contract-fixture correction — 2026-09-26 17:57 ET

The running full regression exposed seven additional T17 build-only failures.
All seven reproduce because the synthetic origin package lacks its current
assembly seal. The [test-only repair](observations/t17-package-fixture-repair-20260926.json)
uses the real seal verifier and updates proposal/pin references. Targeted
negative assertions now require their intended failure reasons, and a changed
sealed package rejects before compilation. The full file passes 48 tests with
two Linux-only skips; independent Spec checks pass 11. Production validation
and the published supervisor are unchanged. The original failed run continues
at its exact pinned commit; no full-suite pass or actual T17 acceptance is claimed.

## Progress check — 2026-09-26 17:33 ET

The [full health audit](observations/health-20260926-1733.json) confirms native
progress at 237/240 checked trials, with three fixed controls passed and the
fourth still running. The pilot retains exact code `319645e`, socket 1 generation
402, empty stderr and the original 20:11:35 ET hard end. Recent sampled peak RSS
is 1.18 GiB. Socket 0 generation 325 and legacy generation 77 are released;
all historical receipt hashes, PID/start unions and runtime/helper pins pass.
Free build/raw space is 16.38/181.16 GiB. All three workers are responsive;
next full check is 18:03 ET. No additional host job or checkout change occurred.

The corrected broad suite at `7fe4c34` exposed 16 campaign fixture failures:
old synthetic execution-class packages lack the now-required assembly seal.
The repaired module passes all 16 cases while preserving semantic negative
checks. The separate exact export `c0df79e` has two related reassessment fixture
failures under repair. Both runs continue and their original failures remain
retained. The 54-file export inventory passed independent review but is not
pushed; its updated test fixtures will receive a fresh explicit export check.
Production package-seal enforcement is unchanged. Counts remain **13/21
resolved and 0/8 final cells**, with no empirical freeze or qualified gain.

## Independent fixture closure preparation — 2026-09-26

The [post-exit proof auditor](observations/linux-fixture-audit-preparation-20260926.json)
passes independent Standards and Spec rechecks after repairing final-hash
publication failure. Its combined local group passes 97 with one Linux-only
skip. It reopens the exact original fixture clocks, runtime, JUnit, output,
process identity union, released lane and settled cleanup ledger before sealing
a separate proof. Pending evidence remains unchanged. Actual Linux fixtures,
terminal audits and empirical acceptance are still outstanding. The corrected
full local suite runs separately at `7fe4c34`; no broad pass is inferred here.

## Local regression repair — 2026-09-26

The [three full-suite failures and clock follow-up](observations/c2-regression-repair-20260926.json)
are repaired. Smoke children use the work cutoff while cleanup retains the
original outer deadline; initial persistence now consumes the work allowance.
The witness fixture uses isolated prelaunch records. The focused repaired group
passed 47 tests; the final clock/cleanup group passed 66 with two Linux-only
skips. Independent review of the clock correction is clean. The failed broad
run remains retained, and a corrected isolated broad recheck is still required.
The [A2 wrapper and shared import guard](observations/a2-linux-fixture-preparation-20260926.json)
also pass scoped review. Neither result supplies actual Linux or empirical proof.

## Progress check — 2026-09-26 17:03 ET

The [full health audit](observations/health-20260926-1703.json) confirms native
progress at 183/240 checked trials. All three completed cells pass their fixed
controls; [DX100 Kronecker](observations/native-one-thread-third-cell-20260926.json)
completed 60/60 with maximum spread 4.38% and no numerical gain in either label
direction. Upstream Kronecker has 3/60 checked. Socket 1 generation 402 remains
healthy with empty stderr, recent peak RSS 1.13 GiB and unchanged 20:11:35 ET
hard stop. Socket 0 generation 325 and legacy generation 77 are released;
all historical identities, receipt hashes and runtime pins pass their checks.
Free build/raw space is 16.38/181.23 GiB. Three workers are responsive; the next
full audit is 17:33 ET.

The [isolated full regression](observations/full-regression-c2f987b-20260926.json)
finished with **1,950 passed, 18 skipped, three failed** at exact `c2f987b`.
Two failures concern legacy smoke cleanup reservation; one prelaunch fixture
conflicts with the newer durable a3 record. All failures are retained. Focused
repairs passed 47 tests, while independent review found a further initial
receipt-write clock gap that is being repaired before export. A2's separate
fixture wrapper and shared root import guard pass their scoped reviews; actual
Linux proof remains outstanding. Counts remain **13/21 resolved and 0/8 final
cells**, without empirical freeze or a qualified gain. Whole native cleanup
must precede A2 or any other measurement.

## Progress check — 2026-09-26 16:33 ET

The [full health audit](observations/health-20260926-1633.json) confirms the sole
native pilot is healthy at `319645e` on socket 1 generation 402. Both uniform
cells have 60/60 checked trials and passed fixed controls. The
[upstream cell](observations/native-one-thread-second-cell-20260926.json) has
maximum spread 2.44% and neither direction shows a numerical gain leg. DX100
Kronecker has 16/60 checked; upstream Kronecker has not started. Total progress
is 136/240, with empty stderr and recent tree RSS below 1.05 GiB. The hard stop
remains 20:11:35 ET. Socket 0 generation 325 and legacy generation 77 are
released with empty kernel locks and absent owners. All historical PID/start
unions, retained receipt hashes and runtime/helper pins pass their checks.
Free `/data1` and `/data` space is 16.38/181.48 GiB. All three workers are
active; next full audit is 17:03 ET.

The [Linux fixture runner](observations/linux-fixture-preparation-20260926.json)
is committed after independent Standards and Spec reviews: 20 focused cases
and two independent probes per axis pass. It emits only an unaccepted pending
proof; actual Linux execution and independent terminal closure remain required.
The prospective simulator finalizer is receiving a narrow cleanup-budget and
monitor-order correction before export. The isolated full suite at `c2f987b`
is still running; it predates the two evidence-integrity fixes and fixture runner.
A [fresh public coverage query](observations/acceptance-post-review-20260926.json)
after both evidence-integrity repairs retains the same incomplete report.
Counts remain **13/21 resolved and 0/8 final cells**, with no empirical freeze
or qualified candidate gain. Coverage A2 remains pinned separately to `67313d9`
and waits for whole-pilot terminal cleanup.

## Progress check — 2026-09-26 16:03 ET

The [full health audit](observations/health-20260926-1603.json) confirms the sole
native pilot is healthy on socket 1 generation 402: DX100 uniform is complete
60/60 with passed fixed controls, upstream uniform is running at 30/60 checked,
and both Kronecker cells have not started. The pilot has 90/240 checked trials,
empty stderr and recent tree RSS below 1.05 GiB. Its exact `319645e` runtime and
20:11 ET hard stop are unchanged. Socket 0 generation 325 and legacy generation
77 are released with empty kernel locks and absent owners. All historical
PID/start unions are absent; all 15 retained audit hashes and pinned checkouts
match. Free `/data1` and `/data` space is 16.38/181.73 GiB. All three workers are
active; next full audit is 16:33 ET.

Local independent result-admission/lifecycle checks passed 75 with four
Linux-only skips. The batch finalizer now preserves original failures and
rejects accounting failure through a nonzero exit. Native supervision review
also identified and is correcting a generic stage startup deadline edge.
These checks are preparation only; actual Linux admission remains required.
Counts remain **13/21 resolved and 0/8 final acceptance cells**, with no empirical
freeze or qualified gain. Coverage A2 waits for whole-pilot terminal cleanup.

## First one-thread pair complete — 2026-09-26 15:46 ET

The [DX100 uniform-random pair](observations/native-one-thread-first-cell-20260926.json)
completed 60/60 structural checks and passed all six fixed spread groups;
maximum spread is 5.08%. Its A/A ratio is 1.0015 with paired 95% interval
[0.9974, 1.0051], and neither label direction has a numerical gain leg.
Upstream uniform-random is now running under the same unchanged socket-1
lease and hard stop. This is one-cell repeatability evidence only; the full
study, fresh diagnostics and shared simulator gates remain unfinished.

## Progress check — 2026-09-26 15:33 ET

The [full health audit](observations/health-20260926-1533.json) confirms the
one-thread native pilot is the only active measurement, on socket 1 generation
402. Its first DX100 uniform-random pair has 43/60 timed structural checks
(22 baseline, 21 candidate); the other three pairs have not started. No failure
or retry is recorded, stderr is empty, and recent sampled tree RSS is below
1.05 GiB. Socket 0 generation 325 and legacy generation 77 are released with
empty kernel locks. All historical owned process identities are absent and all
15 retained audit hashes match. Free `/data1` and `/data` space is 16.38/182.01
GiB. All three workers are healthy; next full check is 16:03 ET.

The [prospective coverage a2 client](observations/dx100-coverage-a2-preparation-20260926.json)
is committed at `5e7eb62` after independent review repaired an unconditional
child-reap failure. Its isolated 11-file export is `67313d9` on native `319645e`;
exact-export tests passed 116 with three Linux-only skips, and the private branch
ref is verified. Actual Linux checks and native terminal cleanup are still
required before dispatch. The initial local export test invocation
used a Python without pytest and stopped before collection; the existing Python
3.12 test environment is now explicit. No coverage execution occurred. The [one-thread publisher](observations/one-thread-publisher-verification-20260926.json)
passed independent review after the same signal-failure/reap edge was repaired;
it still requires all fresh primary/diagnostic and shared accelerator gates.

Counts remain **13/21 resolved and 0/8 final acceptance cells**. No empirical
freeze or qualified gain is established. The publisher cleanup correction and
T15/T16 shared resource supervisor are still under review.

## One-thread pilot running — 2026-09-26 15:07 ET

The [sole native attempt](observations/native-one-thread-start-20260926.json)
started on mbit10 socket 1, generation 402, at exact `319645e`. Both actual Linux
cleanup tests, fresh historical/T17 terminal gates, 74 artifact references, and
20 unused record IDs passed admission. Its original hard stop is **20:11 ET**
(18,240 seconds); all primary/diagnostic sublimits remain fixed. The first
DX100 uniform-random pair is running. This start is not qualification or a
freeze. Coverage a2 must wait for whole-client independent terminal cleanup.

## Progress check — 2026-09-26 15:03 ET

The [full health audit](observations/health-20260926-1503.json) found both socket
leases and the legacy lease released, all kernel locks empty, and every retained
owned PID/start identity absent. The earlier coverage-pane zombie is gone.
Available node/global capacity is 57.29/58.54/117.73 GiB; free `/data1` and `/data`
space is 16.39/182.29 GiB. Historical checkouts and all 15 receipt hashes match.
All three delegated workers are healthy; next full check is 15:33 ET.

The [two actual Linux cleanup cases](observations/native-one-thread-linux-20260926.json)
passed at exact native client pin `319645eab0a25c815fa03fe1c372d32b4ba45d10`,
with zero skips/errors, outer exit zero, and independently absent child/parent
identities. This supersedes the unlaunched `d484afb` preparation; fresh admission
is still required before the sole native pilot starts. Counts remain **13/21
resolved and 0/8 final acceptance cells**, with no empirical freeze or gain.

| Case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| Four-thread pilot | Unqualified | mbit10 / 1 released | 240 correctness checks; 7/24 spread failures | Retain unchanged |
| One-thread pilot | Linux checks passed; admission pending | mbit10 / 1 planned | Exact319 cleanup proof; no pilot result | Fresh admission and one attempt |
| DX100 witness a3 | Passed, tiny scope | mbit10 / 0 released | Timed-binary witness; no full coverage | Larger coverage still required |
| DX100 coverage a1 | Failed and retained | mbit10 / 0 released | RSS monitor failure; zero admitted timings | Review fixed a2 client |
| T17 candidate | Build complete | mbit10 / 0 released | Fresh public build/result chain; cleanup verified | Correctness and performance pending |
| Candidate reassessment | Implemented and reviewed | Local | 88 author and 45 independent tests passed | Use only with fresh qualified packages/freeze |

## T17 build and native pilot export — 2026-09-26 14:47 ET

The [actual T17 build](observations/t17-build-only-terminal-20260926.json) completed
in 55.878 seconds, including nine successful public stages and fresh result/chain
readback. All 15 owned process identities are absent and node-0 generation 324
is released. No provider call or repair occurred. Correctness is unverified,
profiling incomplete and timings empty; T17 remains claimed.

The [reviewed one-thread pilot](observations/native-one-thread-preparation-20260926.json)
is committed at `cbfce757` and exported at `d484afb2` with only required runtime,
tests/plans and already-synced native history. Exact-export tests pass 127 with
five Linux-only skips. The new client still requires its two actual Linux
cleanup fixtures and fresh admission before launch. The sampler and T17 Linux
proofs already passed at their exact pins. Local catalog validation reports
213 valid records after the preserved coverage failure import.

## Progress check — 2026-09-26 14:33 ET

The [full health receipt](observations/health-20260926-1433.json) records all three
workers active, both socket leases and the legacy lease released, all kernel
locks empty, and no live owned evaluation job. The exact failed-coverage pane
remains a zero-RSS zombie. Available node/global capacity is 57.25/58.56/117.71
GiB; free `/data1` and `/data` space is 16.42/182.29 GiB. Historical pins and 11
receipt hashes remain unchanged. Next full check: 15:03 ET.

Counts remain 13 resolved and eight claimed; final acceptance is 0/8. The new
RSS/T17 minimal export `a53e619d` passes 59 local tests with three Linux skips.
The fixed T17 build awaits actual Linux cleanup tests. The one-thread pilot has
not launched; independent reviews are closing ownership, compiler readback and
monitor/cleanup synchronization findings. A separately reproduced simulator
fixture setup error is corrected with 25 regional/aggregation tests passing;
production runtime checks are unchanged. The full `d9b1340` suite continues with
its original setup failures retained.

## Failed coverage and reviewed monitor correction — 2026-09-26 14:25 ET

The actual fixed coverage a1 ended unsuccessfully at 14:01 ET after the resource
monitor reported unavailable owned-process RSS. It has zero admitted timings and
unverified correctness. The public interrupted-stage record retains its stale
`running` top-level outcome; an additive terminal audit records 14 observed
PID/start identities, 13 absent and the exact original pane zombie with zero RSS,
plus released node-0 generation 321. This is not accepted accelerator coverage.
The [terminal and Git import receipt](observations/dx100-coverage-terminal-20260926.json)
binds all four unchanged metadata files (46,426 bytes) imported from `238e5daa`.

The 14:03 ET health check found both socket and legacy metadata released, all
kernel locks empty, no live owned evaluation work, 16.42 GiB free on `/data1` and
182.29 GiB on `/data`. All three workers remain active. The next full check is
14:33 ET. Ticket counts remain 13 resolved and eight claimed; final coverage is
0/8 and no policy-qualified gain or empirical freeze exists.

A deterministic local reproduction exposes the old sampler's cross-file exit
race; it is a supported explanation for the actual failure, not a proved cause.
The [new observer](../../docs/bfs-owned-rss-20260926.md) reads one identity-bound
stat record and passes 12 local checks plus independent review, with one Linux
case still skipped. Its minimal export is `a8b89115` on
`codex/bfs-owned-rss-20260926`; actual Linux validation remains required before
new clients run. The one-thread native pilot and T17 build client are under
review and have not been dispatched. Historical measured checkouts stay pinned.

## Runtime contract restored — 2026-09-26 14:00 ET

T11 is resolved again after its requested runtime-input correction and two
independently reproduced admission fixes. The
[verification receipt](observations/native-runtime-fix-verification-20260926.json)
links the exact code and before/after checks. Counts are **13 resolved / 8 claimed**;
final acceptance remains **0/8**, with no empirical freeze or qualified gain.
The failed four-thread study and all earlier failures remain unchanged.

## Fixed accelerator coverage running — 2026-09-26 13:56 ET

The one [fixed correctness case](observations/dx100-coverage-start-20260926.json)
started at 13:56:02 ET on socket 0, generation 321, from clean `53f2e768`.
Both actual Linux cleanup cases passed on that exact code before dispatch.
Capacity, generation and registration passed; compilation was active at this
observation. The graph has 8,212 vertices and 147,492 adjacency entries, source 0.
Its own hard outer stop is 14:56:02 ET; no retry is permitted. Execution and
independent terminal coverage checks remain required before any T13 resolution.

## Progress check — 2026-09-26 13:33 ET

The [health receipt](observations/progress-20260926-1333.json) records released
socket and legacy metadata, no live native owned processes, 16.44 GiB free on
`/data1`, 182.57 GiB on `/data`, and sufficient memory. The separate 13:34 a3
prelaunch checked all three kernel locks; that later observation is explicitly
separate from the 13:33 metadata check. All workers were responsive or completed,
with no stranded worker. Next full check is 14:03 ET.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 15 native pilot | Complete; calibration failed | mbit10 / socket 1 released | 240 checks, 7/24 spreads over 0.10 | Retain failure and assess future design |
| Native prepare | Timed out | mbit10 / socket 1 released | Exit 124, no review/freeze request | No retry |
| 13 witness a3 | Ready at this observation | mbit10 / socket 0 free | Native/provider/readback terminal barriers passed | One authorized dispatch |
| 11 runtime policy | Fix under verification | Local | Tests and independent review pending | Resolve only after checks |
| Overall | 12 resolved / 9 claimed | — | 0/8 final cells; no gain or freeze | Continue independent work |

## DX100 witness and native readback — 2026-09-26 13:38 ET

The [single a3 witness](observations/dx100-witness-a3-terminal-20260926.json)
passed actual guest correctness and the independent terminal audit; all four
process exits are zero and socket 0 generation 319 is released. Its tiny graph
does not establish accelerated full/tail/competing-parent coverage or a gain.
T13 remains claimed while the fixed coverage case is prepared.

The one native prepare timed out after 175.028874 seconds, exit 124, with no
review or freeze request. Cleanup passed; no retry occurred. The exact 12
source-free paired metadata records were pushed to the private
`codex/bfs-native-paired-evidence-20260926-a1` branch at `b722d132`, with remote
SHA verified. Raw artifacts and the separately held provider packet are excluded.
Counts remain **12 resolved / 9 claimed**, **0/8 final acceptance cells**.

## Native pilot terminal — 2026-09-26 13:23 ET

The original paired study finished at **13:23:55 ET** with all **240/240**
structural checks passed and outer exit zero. Its independent 83-identity audit
found no live owned work, with only the exact original zero-RSS tmux pane zombie
remaining. Socket 1 generation 400 is released. The
[terminal receipt](observations/native-paired-terminal-20260926.json) retains
exact driver, cleanup, all four numerical analyses and same-host Git-view pins.

| Cell | Checks | Fixed spread gate | Next action |
|---|---:|---|---|
| DX100 uniform | 60/60 | Pass | Retain pilot evidence |
| Upstream uniform | 60/60 | Fail | Retain unchanged failure |
| DX100 Kronecker | 60/60 | Fail | Retain unchanged failure |
| Upstream Kronecker | 60/60 | Fail | Retain unchanged failure |

Seven of 24 role/source groups exceed the fixed 0.10 ceiling. All eight
label-direction checks have lower confidence bounds at most 1.05, so there is
no numerical A/A gain; this does not override the spread veto. Collection is
complete and calibration is unqualified. No samples or policy changed, and
no protocol is published. T15 remains claimed; the independent T13 sequence
continues after the separately bounded readback attempt. The new 12-record commit
`b722d132e0aba20a5b7fd524a3d2b31034e12a6e` remains host-local at this check.
Current tracker counts are **12 resolved / 9 claimed** because T11's local
runtime-policy correction is pending independent verification.

## Runtime-policy correction — 2026-09-26 13:15 ET

[Ticket 11](issues/11-workloads-and-comparison-protocols.md) is claimed again
following a public paired fixture that admitted changed inherited OpenMP/GOMP
settings. Current counts are **12 resolved / 9 claimed**; earlier tables retain
their observation-time counts. The fixture supplies no performance evidence.
A local correction will bind calibrated runtime settings to the actual child
environment and comparison. Active native and prepared simulator checkouts remain
unchanged. Independent review is required before the ticket is resolved again.

## Progress check — 2026-09-26 13:03 ET

The [host and kernel-lock observations](observations/progress-20260926-1303.json)
cover 13:03:36–13:04:30 ET. The host worker is active, Spec is responsive and
preparing the next build-only request, and Standards completed its read-only
native design audit. No dead or stranded worker was found. Status remains
**13 resolved / 8 claimed**, **0/8 final acceptance cells**, no empirical freeze
and no qualified gain.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 15 paired calibration | Running; qualification failed | mbit10 / socket 1, generation 400 | 201/240 observations; first three cells complete, upstream Kronecker 21/60; upstream uniform and DX100 Kronecker exceed fixed spread gate | Finish original final cell; retain all failures; no freeze |
| 13 correctness | Reviewed and prepared | mbit10 / socket 0 free | Exact a3 client `1018432`, acceptance launcher `c5f70d7`; 43 isolated focused tests passed | Native terminal barrier and one bounded readback, then one original-window a3 attempt |
| 16 artifact/control | Prepared independently of 15 | mbit10 / no dispatch | Both exact freeze requests and bounded batch plan retained | Actual a3/coverage, Linux cleanup test and sealed admission |
| 17/19 initial rewrites | Candidates created, unverified | mbit10 | Actual producer fields checked; T17 build-only request preparation | Build/correctness steps within fixed bounds; performance remains gated |
| New provider transfers | Held | mbit10 | Exact six-file result inventory and new context payload | Await pending exact approvals |

Socket 0/socket 1/legacy metadata and kernel locks agree: released 318 / held
400 / released 77. The active native driver/evaluator remain healthy on
`98b5f50`, with no outer exit and four recent empty stderr logs. Latest sampled
RSS is 1.051 GiB, peak 1.134 GiB; 1,308 samples retain maximum guard cost
3.651 seconds below 30. Load is 1.01/1.03/1.04, estimated node availability
57.28/57.40 GiB, global availability 116.58 GiB, and source/raw free space
16.44/182.64 GiB. Active, historical, idle acceptance and helper identities
and checked evidence hashes remain unchanged. A2 is unused/expired and a3 is
unused. Next full check: **13:33 ET**.

DX100 Kronecker completed all 60 checks at 12:50:51 ET. Its baseline/candidate
ratio is 1.01937589, 95% interval [0.99698372, 1.03831107]; the reverse ratio is
0.98099240, interval [0.96304593, 1.00302330]. Four of six role/source spreads
exceed 0.10, with maximum **0.5340568** for candidate-role source 1234.
All samples remain retained. The exact 6,824-byte third-cell analysis has
SHA-256 `1494b241394f87e06dffa29737f4f7d4133ee140ebfd54105779fe4b8804e272`.
Neither direction has a numerical gain leg; this does not override the spread
failure. Any later measurement design requires a separately reviewed prospective
version and fresh evidence. No new native plan or retry is authorized here.

## Progress check — 2026-09-26 12:33 ET

The [host and kernel-lock observations](observations/progress-20260926-1233.json)
cover 12:33:28–12:33:54 ET. All three workers are responsive; no dead or stranded
worker was found. Status remains **13 resolved / 8 claimed**, **0/8 final
acceptance cells**, no empirical freeze and no qualified gain.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 15 paired calibration | Running; qualification failed | mbit10 / socket 1, generation 400 | 146/240 checked observations; both uniform cells complete, DX100 Kronecker 26/60; upstream uniform spread 0.1591826 > 0.10 | Finish original remaining cells; retain all failures; no freeze |
| 13 correctness | Prepared | mbit10 / socket 0 free | Idle a3 client `1018432`; observer/coverage code `01e5fc1`; separate launcher race fix under review | Native terminal barrier, final launcher pin, actual bounded proof |
| 16 artifact/control | Prepared independently of 15 | mbit10 / no dispatch | Both exact freeze requests pass local settings/diagnostic admission | Actual a3/coverage, host Linux cleanup test, then sealed reference admission |
| Preparation tests | Passed locally | Root and isolated export checkout | 183 passed, two Linux-only skipped in each checkout | Real Linux cleanup checks remain required |
| New provider transfers | Held | mbit10 | Exact six-file result inventory and new context payload | Await pending exact approvals |

Socket 0/socket 1/legacy metadata and kernel locks agree: released 318 / held
400 / released 77. The active native driver/evaluator remain healthy on
`98b5f50`, with no outer exit or stderr failure. Latest sampled RSS is 0.949 GiB,
peak 1.049 GiB; 952 samples retain maximum guard cost 2.522 seconds below 30.
Load is 1.15/1.14/1.10, estimated node availability 57.30/57.51 GiB, global
availability 116.71 GiB, and source/raw free space 16.44/182.90 GiB. Historical
and helper pins and retained native/T14/a1/provider/cell-analysis hashes are
unchanged. A2 is unused/expired and a3 is unused. Next full check: **13:03 ET**.

The [focused test/export receipt](observations/simulator-admission-tests-20260926.json)
binds the 13-file preparation branch `codex/bfs-simulator-admission-20260926`
at `01e5fc13cf25b56549cdd285c6a2e197e2190bbf`. This contains code, tests,
prospective plans and documentation; it excludes the held provider packet and
raw artifacts. A separate witness launcher is still being fixed and reviewed.
An existing host Python 3.12.3/pytest 9.1.1 environment is available; no
installation or new host test has run. Original exact transfer branches stay
unchanged. These preparations establish no new empirical acceptance.

## New control result — 2026-09-26 12:18 ET

The first two paired cells completed 120/240 observations and all 120 correctness
checks passed. DX100 uniform passed its fixed control gates. Upstream uniform's
candidate-role source-0 relative spread is **0.1591826**, exceeding **0.10**;
both unchanged-code confidence intervals include 1. Its exact 6,902-byte host
analysis has SHA-256
`920189ff3c8abebafac60c00639497a90c4e07a3d70844b83cbe6302ab336a79`.
See [ticket 15](issues/15-baseline-pilot-and-protocol-freeze.md) for the full
reference and numerical results. Both Kronecker cells continue without altered
data, thresholds or attempts. This failure prevents current protocol
qualification. T15's prepared simulator collection stays undispatched;
independent T13 correctness and T16 comparisons continue toward their own
prerequisites. Ticket counts remain 13 resolved / 8 claimed, with 0/8 final
acceptance cells and no qualified gain.

## Progress check — 2026-09-26 12:03 ET

The [fresh host receipt](observations/progress-20260926-1203.json) was observed
at 12:03:49 ET. All three original exact transfers remain complete; the two
additional exact approval questions remain pending. Status is **13 resolved /
8 claimed**, **0/8 final acceptance cells**, no empirical freeze and no qualified
gain. All three workers are responsive; no dead or stranded worker was found.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 15 paired calibration | Running | mbit10 / socket 1, generation 400 | 93/240 observations; DX100 uniform complete; upstream uniform 33/60 | Finish both uniform and both Kronecker cells under fixed bounds |
| 13 correctness | A3 prepared; coverage/observer implementation reviewed in progress | mbit10 / socket 0 free | Idle a3 checkout `1018432`; no new simulator execution | Native terminal barrier, then one bounded actual proof |
| 17/19 initial rewrites | Candidates created, unverified | mbit10 / provider batch terminal | Two actual retained candidates | Compatible frozen-protocol assessment |
| 20 annotation | Original unresolved; supplement prepared | No provider running | Exact API/header/context and remaining budget retained | Pending exact new-payload approval |
| Regression | Complete, passed | Local isolated `83125b4` | 1,300 passed, three skipped; exit 0; 2,682.52 seconds | Focused checks and review for later code |
| Result sync | Six-file packet held | mbit10 | Exact `5f1b802` inventory | Pending exact packet/branch approval |

DX100 uniform's first 60 independent correctness checks passed. Its fixed-policy
unchanged-code ratio is 0.997256 with 95% interval [0.984188, 1.009630]; the
reverse ratio is 1.002752 with interval [0.990353, 1.016063]. Maximum relative
spread is 0.081338, below the prospective 0.10 ceiling. Neither direction has a
numerical gain leg. The exact host analysis is retained at
`bfs-native-paired-pilot-20260926-a1.dispatch/first-cell-fixed-policy-analysis.json`,
SHA-256 `86afd75a4cc7c44a89201053a5945190f13f4b45ab5d608ec81168ed3eb73171`.
This first cell does not qualify the four-cell study or publish a protocol.

Socket 0 and legacy leases remain released at 318/77; socket 1 has the live
owned driver/evaluator/trial at generation 400. Current sampled RSS is 1.01 GiB,
peak 1.04 GiB, with 600 samples and a 1.529-second maximum guard cost. Raw output
is 571 MiB. Load is 1.09/1.11/1.07, estimated node availability is 57.30/57.39 GiB,
global availability 116.59 GiB, and memory-pressure averages zero. Free source/raw
space is 16.46/183.16 GiB. Active, historical, helper and idle a3 checkout
identities remain unchanged, as do the checked native/T14/a1/provider receipts;
a2 is absent and a3 unused. Next full check is due by **12:33 ET**.

The [integrated regression receipt](observations/full-regression-83125b4-20260926.json)
records the exact green suite and excludes newer preparation code. The fresh
[public coverage checkpoint](observations/acceptance-checkpoint-20260926-a1.json)
reconstructs all eight incomplete cells from 197 valid local master records.
Local code preparation adds a fixed coverage case, a bounded read-only owned-
process observer, and shared simulator-batch budgets. These are not execution
or acceptance evidence, and the final post-acceptance reviews remain open.

## Progress check — 2026-09-26 11:33 ET

All three original exact transfers are complete. The new provider-results packet
is a separate held transfer, and the annotated context follow-up is a separate
prepared payload. Both concrete approval questions are pending. Native evaluation
and authorized code/test work continue. Status remains **13 resolved / 8 claimed**,
**0/8 final acceptance cells**, no qualified gain, and no empirical freeze.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 15 paired calibration | Running | mbit10 / socket 1, generation 400 | 37/240 observations; first cell 37/60; no stderr/failure | Complete the original four-cell finite plan |
| 17/19 initial rewrites | Candidates created, unverified | mbit10 / socket 0 released | Two retained actual provider candidates | Frozen-protocol evaluation after calibration |
| 20 annotation | Original unresolved; supplemental context prepared | No provider running | Exact API/header/capability bindings and retained prior spending | Exact new-payload approval before transfer |
| 13 correctness | A3 client prepared and independently reviewed | Waiting for native termination | Fixed history/request/runtime and cleanup barriers; diagnostic-only a1 reparse | Verify terminal receipts, then one actual bounded proof |
| Regression | Full suite running at pinned `83125b4` | Local isolated worktree | Past 44%; no failure reported at this check | Retain the final full result |
| Result synchronization | New six-file packet held | mbit10 | Commit `5f1b802`; 169,515 bytes including source/patch fields | Exact packet/branch approval |

The [fresh host health receipt](observations/progress-20260926-1133.json)
was observed at **11:33:07 ET**; its filename retains the scheduled 11:32 label.
Socket 0 and legacy leases are released at 318/77. Socket 1 is held by the
live paired job at 400. No dead or stranded worker was found. Paired sampled
RSS is 0.90 GiB, peak 0.99 GiB; 235 resource samples retain healthy five-second
sampling and a 0.0107-second maximum guard cost. Raw output is 272 MiB.
Load is 1.10/1.07/0.86, node availability is approximately 57.33/57.45 GiB,
and global availability is 116.68 GiB, with zero memory-pressure averages.
Free source/raw space is 16.47/183.45 GiB (the `df -h` display is 17/184 GiB).
Active code is `98b5f50`; helper `42ce8dc` and historical checkouts remain
unchanged. Native/T14/a1/provider receipt hashes are unchanged and a2 remains
absent. Next full health check is due by **12:03 ET**.

The provider batch ran 11:06:44–11:13:35 ET on socket 0. Two requests created
candidates; the annotation request returned unresolved context. Reported cost
is USD **2.7976184**. Its outer exit 0 means all three submissions reached
retained outcomes, not that every interpretation succeeded. No repair, retry
or candidate evaluation ran. The terminal audit records no live owned work;
one exact zero-RSS zombie launcher under shared tmux remains recorded and
untouched. See [the initial summary](observations/provider-initial-summary-20260926.json)
and [held export inventory](observations/provider-export-inventory-20260926.json).

Reviewed code-only acceptance preparation was synchronized separately as
`1018432fdb3800522d723afb874f3bffa41dd0e5` on
`codex/bfs-dx100-acceptance-prep-20260926`. Exactly seven new code/request/test/plan
files were based on `98b5f50`, excluding held provider records and unrelated
history. The isolated checkpoint passed **45 combined continuation/graph tests**
in 1.64 seconds; log `/private/tmp/bfs-dx100-acceptance-prep-20260926-1018432.log`,
SHA-256 `7755cb871a3efc7767f32af242a67d72b3afe5aec4a958dad0acc8f3a7a25fb1`.
No active checkout was changed. The graph remains preparation-only; a3 still
waits for the paired batch's terminal cleanup evidence before simulation.

## Progress and approved synchronization — 2026-09-26 11:03 ET

The user explicitly approved the exact four code commits through `6346189`,
the prepared 14-file evidence packet, and the three named Claude source/profile
payloads. The code branch now points to `6346189b55132f195b02544b729f34100d10ba92`;
the evidence branch points to `ee7af80a16eb92a42f4eef757cf1bdfa988d74d2`.
Both remote tips were verified. The evidence packet was imported at `332ec96`
and all 14 files / 1,118,269 bytes matched their preapproved hashes. Updated
[code](observations/code-export-20260926-1005.json) and
[evidence](observations/export-inventory-20260926.json) inventories preserve the
prior rejection history. Later local commits were excluded from the four-commit
code transfer.

Ticket [14](issues/14-dx100-region-and-memory-profiling.md#answer) is resolved by
the actual collection evidence, prior independent raw/source audit, exact import,
and fresh public query audit. Status is now **13 resolved / 8 claimed**,
**0/8 final cells**, no qualified gain, and no empirical freeze.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Failed a1 retained; a2 expired unused | mbit10 / released | Existing failure/trace hashes unchanged | Read-only parser diagnosis, then separately bounded future proof |
| 14 | Resolved: collection and retrieval | mbit10 evidence, local queries | 31 regions, 39 memory metrics, 17-record chain; correctness unverified | Preserve evidence boundary for downstream calibration |
| 15 | Paired preflight found compiler argv0 mismatch | mbit10 / socket 1 planned | Same executable, different version banner after symlink resolution; zero samples | Narrow tested fix, fresh preflight, dispatch by 11:58 ET, hard end 15:00 ET |
| 17/19/20 | Exact initial payload submissions authorized | mbit10 / socket 0 planned | Source/package/prompt hashes checked; finite $25 / 1,500 provider-second caps | Three initial submissions; no repair/retry/evaluation in this batch |
| 16–21 | Reference/control and matrix acceptance pending | Not running | No final cells or qualified gain | Complete remaining empirical gates |

Fresh health at **11:02:38 ET** found socket 0, socket 1, and legacy leases
released at generations **317/399/77**, with their recorded daemon PIDs absent.
No owned BFS/gem5/provider job was found. Two unrelated long-lived Claude tail
watchers were identified and left untouched. Load was 0.13/0.21/0.11; free
space was **17/184 GiB** on `/data1` and `/data`; estimated node availability
was 57.33/58.53 GiB and global availability 117.77 GiB, with zero pressure
averages. Historical DX `5802a5a`, native `41303ed7`, and witness `51df061`
checkouts remain pinned. Helper `42ce8dc` equals freshly fetched upstream and
its lane script hash remains `00c269b4…`. All owned workers are responsive;
completed workers finished normally, with no stranded agent found.

Native receipt `26ea5d69…`, profiling package receipt `a66864e…`, a1 audit
`4d228a78…`, simulator log `607b6f69…`, and trace `f6ad616e…` remain unchanged.
The same line-27 failure remains in a1; all a2 paths remain absent. Paired raw
and dispatch paths were absent at this observation. The native preflight failed
before creating run IDs or measurements. The next full health check is due by
**11:32 ET** (or the next heartbeat if earlier).

Provider generation may share the host on socket 0 during socket-1 native
calibration; its process presence will be recorded. The heavy a3 simulator
proof will be deferred until after calibration under a newly recorded finite
window. The unexecuted 11:35/11:55 a3 proposal does not extend the expired a2
window and is not selected for dispatch.

## Heartbeat check — 2026-09-26 10:29 ET

This heartbeat arrived before the previously anticipated 10:34 ET check; the
fresh host audit ran **10:30:03–10:32 ET**. All 21 ticket fields still agree with
the map: **12 resolved, 9 claimed**, **0/8 final cells**, no qualified gain, and
no empirical freeze. Local HEAD before this status update was `3b0fbac`.
Both review/implementation workers completed normally, and the host worker
completed this audit normally. No dead or stranded agent was found.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Actual a1 failure retained; a2 expired unused | mbit10 / socket 0 released | Record, simulator, trace, parser, and audit hashes unchanged; a2 paths absent | Exact code export approval before further execution; preserve expired window |
| 14 | Actual profiling collected; sync held | mbit10 / idle | Original failure retained; collection/package continuations complete and unchanged | Exact 14-file evidence export approval |
| 15 | Paired implementation reviewed; study unrun | Local; mbit10 socket 1 free at observation | Plan revalidated at 10:30 ET; 213 focused checks remain the existing evidence | Approved code sync, then dispatch only before 11:58 ET; hard end 15:00 ET |
| 18 | Existing candidate metadata fits initial-reuse shape | mbit10 / read-only | One completed patch attempt, candidate unverified, no provider/repair budget | Full artifact/package/replay validation and frozen-protocol evaluation |
| 16–21 | Empirical reference/control and matrix gates incomplete | Not running | 0/8 cells and no qualified gain | Clear exact export holds and complete prerequisites |

Socket 0, socket 1, and legacy leases remain released at generations **317,
399, 77**; their recorded daemon PIDs are absent. No matching owned EvolveSWDB or
gem5 job remains. Load is 0.00/0.00/0.00. Free disks remain **17 GiB on `/data1`
and 184 GiB on `/data`**. Conservative node availability is 57.34/58.52 GiB,
global availability 117.75 GiB, and pressure averages are zero. These observations
do not reserve resources for this task.

Historical DX `5802a5a`, native `41303ed7`, witness `51df061`, and helper `c40ad13`
are unchanged. Helper script `00c269b4…` matches its worktree, HEAD, and existing
origin copy; no fetch occurred. Native receipt `26ea5d69…` retains four complete
cells. T14's original failed driver `a4e67382…` retains the missing-`--runs-dir`
error; collection `45a0fb1d…` and package `a66864e…` remain complete. Recent native,
collection, and package stderr logs are empty. A1 record `9a941cdf…`, simulator
`607b6f69…`, trace `f6ad616e…`, parser `de6e008e…`, and audit `4d228a78…` are unchanged,
including the line-27 witness parsing failure. All a2 record/output/dispatch paths
remain absent. No remote mutation, export, provider call, or dispatch occurred.

The Ticket 18 metadata check confirmed its original proposal/candidate IDs,
source/package references, one completed initial rewrite, and retained artifact
SHA `10d4976f…`. It did not replay the patch, reopen source bytes or diagnostic
packages, admit reuse, or execute the candidate. Local full/focused test logs
also retain their prior hashes; no test was rerun during this heartbeat.

The exact four-commit code request through `6346189` and the separate evidence
and provider requests remain unanswered; this automated heartbeat is not a new
payload approval. Later local commits remain excluded from that code request.
The heartbeat remains active. With this early scheduler delivery, the next
30-minute check is expected around **10:59 ET**; perform it no later than
30 minutes after this audit. Final acceptance and post-acceptance review remain
open.

## Local verification and preparation — 2026-09-26 10:27 ET

The pinned `721fa72` full suite completed with **1,164 passed, 3 failed, and
3 skipped in 2,474.56 seconds**. Its original log and exact hash are retained in
[the review receipt](../../docs/bfs-interim-review-20260926.md). The failures were
the incomplete campaign fixture and two paired-field documentation checks.
The serial/paired fixture correction is in `6346189` and passed within the
213-case group; the documentation correction is in `d53c226` and all four format
checks pass. This is targeted repair evidence, not a full-suite pass at a newer
checkpoint.

A bounded audit of the remaining tickets identified one local preparation gap:
Ticket 18's proposal already created a candidate, while the native client always
resubmitted. Commit `35b0cff` adds explicit exact candidate reuse with public
retrieval, original provider/repair-budget preservation, and bounded patch replay
that binds source bytes to candidate bytes. Independent review reproduced and
closed a consistently rehashed candidate/diff mismatch; it found no remaining
actionable issue after repair. The focused group passed **40 tests with
23 deselected in 27.74 seconds**, including fresh submit, actual local patch
replay, public fixture evaluation, cleanup, and serial/paired flow. Paired receipt
bounds now report their existing 2,400-second allowance accurately. The
[campaign plan](campaign-plan.md) and [handoff](../../docs/bfs-handoff.md) describe
the interface and evidence limits.

All workers finished normally. The full-suite process has exited. All 21 ticket
states remain **12 resolved, 9 claimed**, with **0/8 final cells**, no qualified
gain, and no empirical freeze. No remote job, provider call, export, or new lease
was started. The most recent host observations remain the 10:04–10:05 ET audit
below; they are not relabeled as a new observation.

The pending four-commit code approval covers only the exact tip **`6346189`**
identified in [its inventory](observations/code-export-20260926-1005.json).
Later local tracker, documentation, and reuse commits are excluded; do not push
`HEAD` under that narrower approval. Separate evidence/provider questions remain
pending. The heartbeat is confirmed **ACTIVE, every 30 minutes**; next full
progress/host check is **10:34 ET**. Final post-acceptance Standards/Spec reviews
remain outstanding.

## Progress check — 2026-09-26 10:04 ET

Ticket states remain **12 resolved, 9 claimed**, with **0/8 final matrix cells**,
no qualified gain, and no empirical protocol freeze. Local HEAD is `6346189`.
Both implementation/review workers completed normally; the host worker completed
the scheduled health audit. No dead or stranded worker was found. Current catalog
validation reports **186 valid records**.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Actual a1 failed; a2 window expired unused | mbit10 / socket 0 released | Failure and raw trace hashes unchanged; reviewed parser correction passed 121 tests | Clear exact code-export hold before further execution; do not extend a2 |
| 14 | Actual profiling retained; synchronization held | mbit10 / idle | Final package receipt unchanged; timed-binary correctness remains unverified | Exact 14-file evidence export approval |
| 15 | Prospective paired driver and admission reader committed | Local / `6346189` | Independent reviews clean after repairs; 213 focused tests passed in 158.00 s; no paired execution | Exact code synchronization, then dispatch only before 11:58 ET under the fixed 15:00 ET end |
| 16–21 | Final reference/control and matrix acceptance incomplete | Not running | 0/8 final cells; no qualified gain | Clear export holds and empirical prerequisites |

Fresh read-only observations at **10:04:19–10:05:58 ET** found socket 0,
socket 1, and legacy leases released at generations **317, 399, 77**; recorded
lease daemons were absent. No matching owned EvolveSWDB/gem5 job remained. Load
was 0.00/0.03/0.10; free disks were 17 GiB on `/data1` and 184 GiB on `/data`.
Conservative available memory was 57.31/58.51 GiB per node and 117.72 GiB globally;
pressure averages were zero. These observations do not reserve a lane.

Historical DX `5802a5a`, native `41303ed7`, witness `51df061`, and helper
`c40ad13` remain unchanged. The helper script hash remains `00c269b4…` and matches
its HEAD and existing origin copy; no fetch occurred. Native driver `26ea5d69…`
still retains four complete cells. T14's original failed driver `a4e67382…` remains
failed, while its completed collection/package continuations, including final
package driver `a66864e…`, remain unchanged. Recent native/package stderr logs
were empty. A1 record `9a941cdf…`, simulator `607b6f69…`, trace `f6ad616e…`, parser
`de6e008e…`, and audit `4d228a78…` hashes were unchanged. Its line-27 trace-format
failure remains preserved. A2 evaluation, driver, audit, and dispatch paths were
absent; its 10:00 ET end passed unused. No host mutation or export occurred.

The code-export inventory now covers the concrete four-commit checkpoint
`1cc9557`, `b3a2cbe`, `721fa72`, `6346189`: **35 changed tip files, 592,945 bytes**,
targeting the same private GitHub repository/branch. The exact request supersedes
the earlier two-commit question; see
[the inventory](observations/code-export-20260926-1005.json). The 14-file evidence
packet and three Anthropic/Claude payload questions remain separately pending.
No rejected action was retried or routed elsewhere.

The full suite at pinned `721fa72` is still running. Its one observed failure is
an incomplete campaign fixture, reproduced and corrected in `6346189` for serial
and paired modes; both fixed cases are in the 213-test passing group. The original
full run and failure remain intact and are not reported as green. See
[interim review](../../docs/bfs-interim-review-20260926.md). Final post-acceptance
Standards/Spec reviews remain required. The heartbeat stays active; the next full
progress check is due **2026-09-26 10:34 ET**.

## Progress check — 2026-09-26 09:34 ET

All 21 map rows retain **12 resolved, 9 claimed**, with **0/8 final matrix
cells**, no qualified gain, and no empirical protocol freeze. Three active
workers responded; none was dead or stranded. Local HEAD is `b3a2cbe`.
The fresh local catalog check reports **186 valid records**.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Actual a1 failed; parser correction reviewed | mbit10 / socket 0 released | Failed v2 record imported at `1cc9557`; correction passed 121 tests in 57.30 s | Exact code-export approval; a2 only before 09:40 ET |
| 14 | Actual profiling retained; synchronization held | mbit10 / idle | 31 scopes and 39 memory rows; still unverified correctness | Exact 14-file evidence export approval |
| 15 | Original pilot expired; new paired plan in development | Local | Both old blocks preserved; paired parent-admission defect fixed and independently reproduced as rejected | Complete fixed 240-observation driver and publication review |
| 16–21 | Final reference/control and matrix acceptance incomplete | Not running | 0/8 final cells; no qualified gain | Clear export holds and empirical prerequisites |

Fresh read-only observations at **09:34:05–09:34:57 ET** found socket 0,
socket 1, and legacy leases released at generations **317, 399, 77**.
Intervening generations changed after the 09:04 observation; no ownership or
workload is inferred from those counters. No owned job remained. Load was
0.31/0.26/0.25; free disks were 17 GiB on `/data1` and 184 GiB on `/data`.
Conservative available memory was 57.21/58.51 GiB per node and 117.62 GiB globally.

Historical DX `5802a5a`, native `41303ed7`, witness `51df061`, and helper
`c40ad13` remain unchanged. The helper hash remains
`00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`.
The a1 evaluation (`9a941cd…`), trace (`f6ad616e…`), old parser (`de6e008e…`),
and audit (`4d228a78…`) hashes were rechecked unchanged. Its verdict remains
failed/unverified, with zero admitted timings and no gain. Native and T14
terminal receipts also remain unchanged. All a2 result, driver, launch, and
record paths were absent. This check made no remote mutation or transfer.

The user reaffirmed broad approval at 08:54 ET. Reviewed code was synchronized
through `0236631`, and the newly generated two-file failed-a1 metadata packet was
separately synchronized successfully. Automatic approval review rejected the
14-file source-excerpt packet and the later two-commit correction push
(`1cc9557`, `b3a2cbe`), requiring exact payload/destination approval. Specific
questions for those packets and the three Anthropic/Claude source/profile
payloads remain pending. No rejected action is retried or routed elsewhere.
The a2 corrective plan keeps its **10:00 ET** end and **09:40 ET** latest dispatch;
a missing approval does not extend it. The separately proposed paired native
study ends at **15:00 ET** with no retries or adaptive changes.

Local calibration fixture checks passed 88 tests. The new driver and publication
reader remain under development and independent review; those fixture results
are not actual paired calibration. The heartbeat stays active, with the next
full progress check due **2026-09-26 10:04 ET**.

## Progress check — 2026-09-26 08:34 ET

All 21 map rows match the ticket status fields: **12 resolved, 9 claimed**.
Acceptance remains **0/8 final matrix cells**, with no qualified gain or frozen
empirical protocol. Code remains at local checkpoint `5f4ffdf`. The two review
workers completed normally; the host worker completed this check normally. No
dead or stranded agent was found. The previous catalog validation reports 185
valid records; it was not rerun as a new test during this unchanged heartbeat.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Actual v2 proof pending | mbit10 / released | Reviewed implementation retained; no new execution | Specific code export approval, then bounded proof |
| 14 | Profiling collected; synchronization held | mbit10 / released | Existing complete package and unchanged terminal receipt | Approval for the exact 14-file evidence packet |
| 15 | Pilot expired; no freeze | mbit10 / released | Both native blocks retained; A/A instability unresolved | Preserve incomplete pilot; separately plan subsequent calibration |
| 16–21 | Final reference/control and matrix acceptance incomplete | Not running | 0/8 cells, no qualified gain | Clear export holds and empirical dependencies |

Fresh read-only observations at **08:34:40–08:35:30 ET** found socket 0, socket 1,
and legacy leases released at generations 314, 397, and 77. No owned jobs or prior
owned PIDs remained. Load was 0.00/0.00/0.00. Free disks were 17 GiB on `/data1`
and 184 GiB on `/data`; conservative node availability was 57.32/58.52 GiB and
global availability 117.75 GiB. Native and T14 driver receipts remain complete
with their previously recorded hashes unchanged; recent stderr files were empty.
DX `5802a5a`, native `41303ed7`, and helper `c40ad13` remain unchanged. The helper
hash remains `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`.
No new fetch, host write, export, lease change, or dispatch occurred.

The specific code/evidence/provider approvals are still unanswered. This
automated heartbeat does not grant those approvals or renew the expired pilot.
The automation remains active; the next scheduled check is **09:04 ET**.

## Recovery check — 2026-09-26 08:10 ET

Tickets remain **12/21 resolved**, final matrix acceptance **0/8**, with no
qualified gain or empirical protocol freeze. The usage limit prevented agent
work and observations from approximately 02:04 through 08:04 ET. Heartbeat
messages during that gap are not evidence of completed checks. Workers resumed
after usage recovered; all three responded and no dead worker was left running.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Original-graph checker implemented; actual v2 proof pending | Local / mbit10 released | Full suite at `0467c72`: 1,097 passed, 3 skipped; actual proof not run | Approved code sync, then separately bounded proof |
| 14 | Actual profiling retained; synchronization held | mbit10 / released | Complete 31-scope, 39-memory-row package remains unverified for correctness | Exact metadata export approval and master-record synchronization |
| 15 | Original pilot window expired; no freeze | mbit10 / released | Two native blocks retained; unchanged A/A crosses the gain threshold | Preserve incomplete outcome; separately plan any subsequent pilot |
| 16 | Reference/control prepared, unfrozen | Local preparation | Uniform22 and prospective author requests retained | v2 mechanism and independent protocol prerequisites |
| 17/19/20 | Exact provider payloads held | Not running | No new provider invocation | Specific payload approval and remaining freeze gates |
| 18 | Literal candidate retained; final evaluation pending | mbit10 / released | Existing compilation only | Frozen native evaluation and reprofiling |

Actual read-only host observations span **08:05:26–08:06:23 ET**. Both socket
leases are released (node 0 generation 314; node 1 generation 397), as is legacy
generation 77. No matching live EvolveSWDB/gem5 job or previously owned PID was
found. Load was 0.00/0.00/0.00. Free disks were 17 GiB on `/data1` and 184 GiB on
`/data`. Conservative available memory was 57.29/58.52 GiB per node and 117.72 GiB
globally; pressure averages were zero. Capacity does not supply export approval
or renew a run budget. Intervening lane use during the unobserved gap is unknown.

The historical DX checkout remains `5802a5a`; the native metadata checkout remains
`41303ed7`. The helper checkout is `c40ad13e`, matching its existing fetched origin,
with SHA-256 `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`.
No new fetch is claimed. The native driver receipt still hashes to
`26ea5d69db8a7b06f48e35876fa2308aa849a654c0cab351c6f70ae4777f4583`;
the profile continuation receipt still hashes to
`a66864e992b59eda7e3598bf083fb426ed94d845fe802338e053d4e452e53d53`.
No host job was dispatched, and no rejected export was retried or routed elsewhere.
The next periodic check is due **2026-09-26 08:34 ET**.

Local follow-up review found and repaired surviving-process cleanup, simulated
hotspot metric selection, and empty-operation executable-readiness enforcement.
Focused checks and the separately pinned 1,097-test suite are recorded in the
[interim review receipt](../../docs/bfs-interim-review-20260926.md). The final
post-acceptance review remains outstanding. The local
[export inventory](observations/export-inventory-20260926.json) identifies 14
remote evidence files and their proposed destination; preparation is not export
authorization. It excludes raw logs, binaries, and graph bytes. No ticket is
resolved from preparing that inventory.

2026-09-26 local checkpoint update: `5f4ffdf` commits the three latest reviewed
repairs after their focused tests and independent cross-reviews passed. Catalog
validation still reports 185 valid records. The pending code approval now names
all five local commits after `a6b2f61` (64 files, 3,598 additions, 323 deletions)
and the existing private repository/branch. A separate pending question names
the exact 14-file, 1,118,269-byte evidence packet and its proposed new branch.
Neither transfer has occurred; earlier provider-payload questions remain pending.
These local tracker updates and held host observations are excluded from the
code checkpoint. No new candidate or acceptance result follows from the commit.

The additional read-only handoff check at **08:23:39–08:24:53 ET** found both
socket leases still released at generations 314/397, legacy 77 released, and no
matching owned EvolveSWDB/gem5 process. Load was 0.03/0.02/0.00; free disks stayed
17/184 GiB. Conservative node availability was 57.30/58.53 GiB and global
availability 117.73 GiB. Checkout identities, helper bytes, and both terminal
receipt hashes were unchanged; recent driver stderr tails were empty and the
packages retained `gain_claim: false`. No host write, fetch, export, or job was
performed. This extra check does not fill the earlier monitoring gap or renew
the expired pilot. The scheduled 08:34 ET check remains due.

## Progress check — 2026-09-26 01:40 ET

Tickets remain 12/21 resolved; final acceptance remains 0/8, with no qualified
gain or empirical protocol freeze. All three workers are responsive. Interim
Standards/Spec review found four concrete defects: unsafe mutable-graph checking,
missing native package-backed region comparisons, incomplete descendant cleanup,
and YAML-only messages breaking durable JSON retrieval. Repairs and independent
cross-review are recorded in the [interim review receipt](../../docs/bfs-interim-review-20260926.md).
The final required review still follows acceptance.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Independent original-graph checker implemented; v2 proof pending | Mac / mbit10 queued | Compiled false-PASS regression now rejected; 114 candidate/author/witness cases passed | Finish downstream qualification guards and approved code sync |
| 14 | Actual profiling package complete; export held | mbit10 / released | 31 scopes and 39 memory rows; actual correctness still unverified | Authorized metadata sync before resolution |
| 15 | Native A/A veto implemented; simulator calibration pending | mbit10 / released | 121 calibration/repeatability contract cases passed; unchanged A/A crosses gain threshold | Preserve all samples; complete actual simulator gates |
| 16 | Prospective author/control policies refreshed, unfrozen | Local preparation | Updated v2 runtime parser identity; unchanged author traversal remains distinct | Bounded v2 proof and freeze prerequisites |
| 17/19/20 | Exact provider payload approvals pending | No provider invocation | No new generated candidate claimed | Resume only after approval and freeze |
| 18 | Literal candidate compiled; frozen native evaluation pending | mbit10 / queued | Existing compile evidence retained | Frozen evaluation and reprofiling |

Read-only host observations span 01:40:24–01:43:35 ET. Node 0 generation 277
is held by the live external workflow; node 1 generation 397 and legacy 77 are
released. No owned BFS/gem5/Callgrind job remains. Eight external Python workers
use both sockets without lane confinement; their processes and the external
Spatter process remain active. Load changed from 9.44/10.03/8.96 to
11.82/10.70/9.41. Disk availability remains 17 GiB on `/data1` and 196 GiB on
`/data`. Conservative node availability is 35.28/52.89 GiB and global availability
89.95 GiB; these estimates do not authorize or guarantee a dispatch.

Historical DX checkout `5802a5a` and native metadata checkout `41303ed7` remain
unchanged. The actual helper checkout remains clean at `c40ad13e`, matching its
existing fetched origin, and helper SHA-256 remains
`00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`.
No fetch, new host receipt, code export, or measurement was performed during
this check. The tool transcript retains the observations. Native driver receipt
SHA-256 remains `26ea5d69db8a7b06f48e35876fa2308aa849a654c0cab351c6f70ae4777f4583`;
profile continuation receipt remains
`a66864e992b59eda7e3598bf083fb426ed94d845fe802338e053d4e452e53d53`.
The next full check is due **2026-09-26 02:10 ET**. The pilot deadline remains
05:56:38 ET; idle/approval time does not extend it.

## Progress check — 2026-09-26 01:10 ET

Tickets 01–12 remain resolved (12/21); final matrix acceptance remains 0/8.
No empirical protocol or qualified gain is claimed. Local checkpoint `8175ca1`
retains verifier runtime bytes per execution and binds their hashes into frozen
instrumentation. Its 89 focused tests passed; the actual v2 attempt has not
started. Automatic approval review rejected this code push as well as the
previous evidence exports and Claude payloads. Exact payload/destination approval
questions remain pending. No alternate export or execution path was used.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Fixed v2 proof prepared; code synchronization held | Mac / mbit10 pending | 89 runtime, public execution, and fixed-request tests passed | Approved code sync, then one bounded author proof |
| 14 | Independent observation audit passed; synchronization held | mbit10 / released | Complete package, 31 source scopes and 39 memory rows; actual v1 remains unverified | Authorized metadata synchronization before ticket resolution |
| 15 | Second native block complete; profitability readiness unresolved | mbit10 / lane 1 released | All 60 trials checked; unchanged DX100 uniform nominal A/A ratio 1.176047, 95% interval [1.066142, 1.448303] | Retain instability and all samples; finish simulator gates |
| 16 | Reference/control prepared, not frozen | mbit10 / queued | Existing uniform22 graph and identified author builds | Validate v2 mechanism and prospective protocol |
| 17/19/20 | Exact provider payloads held | No provider invocation | Source/profile export approval pending | Resume only after explicit approval |
| 18 | Literal candidate and builds complete | mbit10 / queued | Existing primary/diagnostic compilation | Frozen native evaluation and profiling |

The native second block used `8c178a7` and completed in 1,662.222400 seconds.
Its four binary/wrapper/settings comparisons and all raw references passed the
remote audit. Remote-only evidence commit
`41303ed7fb02f9a5c515e2e951d27e20869c73e9` contains four evaluations and the audit;
189 remote records validate. It has not been exported or imported into the local
185-record catalog. The unchanged A/A interval is descriptive, not a qualified
gain. Every sample remains retained. The external Spatter workflow overlaps four
DX100 Kronecker execution-stage envelopes and all fifteen upstream Kronecker
trials; no causal explanation or sample exclusion is asserted.

The scheduled host snapshot was captured at 01:08:37 ET. Lane 0 generation 277
belongs to the live external workflow; lane 1 generation 397 and legacy lease 77
are released. No owned evaluator or gem5 process remains; the old outer wrapper
is an inert zombie. Load1 is 1.33, free disks are 17/196 GiB, conservative node
availability is 56.837/53.333 GiB, and global availability is 112.042 GiB. Helper
`c40ad13e` matches the last fetched origin and its retained hash; no fresh fetch
is claimed. The historical DX checkout stays pinned at `5802a5a`. The host receipt
`periodic-health-20260926-0110.json` has SHA-256
`3d76f1f7701ac597b45b0655cda525ced2d68592efe9ed1d4ec37999b305a0e4`
and remains remote. All three workers are active; no dead worker was found.
The next full check is due **2026-09-26 01:40 ET**.

Independent local work continues on explicit simulator source/replay identity
and separately labeled diagnostic case evidence. A diagnostic must retain its
own cell and cannot certify primary timing or primary accelerator execution.
Neither the 57 calibration fixture tests nor the prepared finite sequence
constitutes execution acceptance. The pilot deadline remains 05:56:38 ET.

## Progress check — 2026-09-26 00:40 ET

Tickets 01–12 remain resolved (12/21); final acceptance remains 0/8 and no
qualified gain is claimed. Core v2 implementation checkpoint `a6b2f61` is pushed;
its independent contract review and focused tests are documented in
[the local validation receipt](../../docs/evidence/bfs-v2-contract-review-20260926.md).
A real v2 attempt remains pending; no old execution has been promoted.

| Ticket/case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| 13 | Explicit v2 implemented and reviewed | Mac; model pending | 69 witness and 12 public adapter tests; exact checker binding | Review fixed request; run after native block |
| 14 | Complete package; independent audit pending | mbit10 / lane 0 released | 31 regions, 39 memory rows, fresh retrieval matches; v1 correctness remains unverified | Audit source/ROI attribution and preserve export hold |
| 15 | Second native block running | mbit10 / lane 1 generation 397 | DX100 uniform 15/15 checked with unchanged binary/wrapper; upstream uniform started | Finish three remaining fixed cells; analyze all trials |
| 16 | Reference/control prepared, not frozen | mbit10 / queued | Registered uniform22 graph and unchanged identified builds | Establish v2 correctness before freezing |
| 17/19/20 | Prepared provider payloads held | No provider invocation | Exact source/profile approval pending | Resume only after explicit payload authorization |
| 18 | Literal candidate/builds complete | mbit10 / queued | Identified primary and diagnostic compilation | Frozen native evaluation and profiling |

At 00:39:39 ET all three subagents were live. Lane 0 and the legacy lease were
released; lane 1 owner and driver were alive with the actual upstream evaluator.
No owned gem5 process remained. Load1 was 6.03; `/data1` and `/data` had 17 and
196 GiB free. Conservative per-node available memory was 53.438/53.061 GiB and
global availability 108.272 GiB. The lane helper still matched its current
`c40ad13e` source identity. No other user's job or active checkout was changed.
The next full check is due **2026-09-26 01:10 ET**.

The independent profile's original CLI failure occurred before collection:
`--runs-dir` was omitted. Both orchestration clients are fixed. The original
simulations and failure receipt remain unchanged; only the planned collection,
package, and fresh retrieval steps were completed in an additive continuation.
Unresolved compiler scopes remain explicit despite package completeness.

Automatic approval review still holds the three Claude payload submissions and
the exact Git evidence packet. New host evidence and this status update remain
local/remote as applicable and were excluded from code pushes. No alternate
agent, destination, or export path was used. Existing required approval questions
remain pending. Independent implementation and authorized execution continue.

## Progress check — 2026-09-26 00:10 ET

Tickets 01–12 remain resolved (12/21); final matrix acceptance remains 0/8 and no
qualified ROI gain is claimed. Commit `5802a5a` contains the reviewed post-seal
trace probe; `6234c6d` contains the independent source-bound profiling diagnostic.
The clean full-suite result remains 765 passed / 3 skipped at `d9c4c10`; it does
not cover later changes. A combined DX100/profile regression run is active.

| Case | Status | Host/lane | Evidence | Next action |
|---|---|---|---|---|
| Ticket 13 | Trace preflight passed; not yet dispatched at this check | mbit10 / lane 1 planned | Exact 14 input files and 10 checkpoint files rehashed; original a6 remains unverified | One bounded post-seal syscall probe |
| Ticket 14 | Observation driver reviewed | mbit10 / pending eligible lane | Existing scalar primary/diagnostic binaries; unsupported unused SIMD scope remains explicit | One bounded actual profile package |
| Ticket 15 | First native block complete; second block preparation | mbit10 / lane 1 planned | 60 primary observations; high unexplained timing spread | Remaining finite unchanged-baseline block |
| Ticket 16 | Graph/build identities prepared; not frozen | mbit10 | Actual uniform22 registration and concrete protocol requests | Validate correctness mechanism before comparisons |
| Tickets 17/19/20 | Envelopes prepared, provider calls held | No active provider | Three exact source/profile payloads await required approval | Resume only after payload authorization |
| Ticket 18 | Literal candidate and two build modes complete | mbit10 / released | Audited primary/diagnostic builds and 31 discovered regions | Frozen native correctness/timing/profiling |

At 00:09–00:10 ET both socket leases and the legacy lease were released, with no
owned probe PID. Lane 1 conservative capacity was 52.385 GiB, global available
memory 105.164 GiB, load1 11.36, and disks 17/196 GiB free on `/data1`/`/data`.
The lane helper was freshly verified against `c40ad13e`; no other user's job was
changed. Two workers were active and the independent review worker completed
normally; no dead worker was found. The next full progress check is due 00:40 ET.

Automatic approval review rejected the three Claude payloads and a separate
proposed Git metadata export. The latter remains held after fresh verification
that the existing remote is the user's private repository; it must not be routed
through another agent. Read-only host checks and authorized code/execution work
continue. This progress section is retained locally pending approval of the exact
new evidence export packet.

## Latest integration — 2026-09-25 23:54 ET

- Literal DX100 patch proposal and candidate now have actual primary and diagnostic
  compilation receipts, 31 discovered regions, and audited source/protection/binary
  hashes. [Preparation receipt](../../docs/evidence/bfs-campaign-preparation-20260925-a1.yaml)
  records that no candidate execution or performance timing occurred. Ticket 18
  remains claimed pending the frozen native evaluation.
- [Post-ROI diagnosis](../../docs/bfs-post-roi-termination-diagnosis.md) identifies a
  plausible lost clone-process association in serialized gem5 checkpoints. Runtime
  pointer aliasing is not yet observed. One bounded post-seal syscall trace is being
  prepared; no simulator modification or acceptance change has been applied.
- The independent diagnostic collector now retains exact sealed observations even
  when subsequent verification fails, preserving the original verdict and outcome.
  Configuration identity is captured before reporting that verdict. Twenty-eight
  focused continuation/collector/counter checks passed. The existing a6 record is
  unchanged and cannot acquire missing identities retrospectively.
- [Read-only a6 parser receipt](observations/dx100-a6-collector-preflight.json)
  records 7,253 counters and 39 actual ROI-wide memory rows, with a 29.122772 us
  sealed duration. This source-unbound bring-up observation is not a profile package
  or correctness acceptance. The local catalog validates all 185 records.

## Review navigation

| Review question | Spec destination |
|---|---|
| What is the deliverable, including every agreed coverage dimension? | Solution; Testing Decisions → Coverage accounting |
| What must Peter, Josh, the worker, and evaluator be able to do? | User Stories 1–60 |
| What are the source, proposal, hardware, and evaluation contracts? | Implementation Decisions D01–D15 |
| What proves completion? | Testing Decisions AC01–AC20 |
| What remains to be chosen, and when? | Further Notes → Decisions still to instantiate |

## Requirement traceability

| Requirement group | User stories | Decisions | Acceptance criteria |
|---|---|---|---|
| Shared kernel identity, exact application provenance, source context | 1–2, 9, 15, 19, 36, 48–49 | D01, D03–D04, D12–D13 | AC01, AC02, AC08, AC14, AC16 |
| Automatic discovery, new hot helpers/loops, dynamic memory evidence | 3–8, 10 | D03–D05 | AC02–AC05 |
| Four payload forms, two routes, worker ownership and bounded repair | 11–24 | D06–D08 | AC06–AC08 |
| Failure retention, independent correctness, durable retrieval | 25–31, 38, 40, 54 | D02, D08, D10, D14 | AC07–AC10, AC18 |
| Primary BFS ROI, region results, explicit comparator, protocol freeze | 32–39, 47–51 | D11–D13 | AC13–AC18 |
| DX100 operation contracts, both-source acceleration, future co-design | 41–46, 59 | D09–D10, D12, D15 | AC08, AC10–AC12, AC15, AC19 |
| Workload coverage, native execution, real gain, resource discipline | 29, 39–40, 46–52, 58 | D10–D14 | AC06, AC10–AC13, AC15–AC18 |
| Master records, collaborator fixtures, public workflow tests, authorization | 26–27, 53–60 | D02–D03, D14–D15 | AC07, AC09, AC18, AC20; publication gate |

## Context pointers

### Reviewed runtime fixes and verification — 2026-09-26 15:04 ET

- Native one-thread client phase accounting is serialized before any attempt. The
  superseding code export is `319645eab0a25c815fa03fe1c372d32b4ba45d10`; the prior
  `d484afb` export was not dispatched. Its phase regression passed 69 local cases
  with two Linux-only cases still required on the final host pin. See
  [phase fix](observations/native-one-thread-phase-fix-20260926.json) and
  [preparation/export](observations/native-one-thread-preparation-20260926.json).
- The simulator now persists its operational failure before optional postmortem
  scanning. The reviewed fix is `76fd5b4`; 42 focused checks and two independent
  public SIGTERM cases passed. [Receipt](observations/dx100-durable-interruption-verification-20260926.json).
  Historical failed coverage remains unchanged and unqualified.
- The exact `d9b1340` full suite completed with **1530 passed, 5 skipped, 11 setup
  errors**. All errors share the copied native-runtime metadata in an explicit
  simulator fixture. The separate fixture correction passed 25 targeted tests;
  this is not a green full-suite result. [Full result](observations/full-regression-d9b1340-20260926.json).
- Candidate reassessment and coverage a2 are local implementation work. Neither
  constitutes an empirical freeze, candidate acceptance, or qualified gain.


- 2026-09-25 23:46 ET: isolated fixed-commit validation at `d9c4c10` passed
  **765 tests with 3 skips and no failures**, in 1660.57 seconds. The checkout
  remained clean and unchanged throughout. The actual run was 23:15:16–23:42:57 ET;
  logs and the earlier Python-selection setup failure are preserved in
  `docs/evidence/bfs-validation-20260925-d9c4c10.yaml`. Later fixes are covered by
  separately recorded focused tests; this is not a full-suite claim for later HEAD.
- 2026-09-25 23:40 ET: twelve tickets are resolved. Ticket12 now meets its
  explicitly unverified checkpoint-to-ROI smoke scope: a6's simulator stage
  completed within wall/RSS bounds and sealed the actual ROI. Its overall
  `missing_observation` outcome and unverified correctness remain unchanged;
  Ticket13 still needs valid termination and actual accelerator coverage.
  Both native implementations have finished both scale18 families:60 primary
  checks,24 diagnostic executions and4 complete packages, imported through
  `f3b50df`. The fixed-checkpoint local suite at `d9c4c10` is still running;
  later focused checks pass, without a full-suite success claim. All workers
  are healthy; identity completed diagnosis normally. At23:39:29 both socket
  leases and legacy were released (generations274/395), with no owned active
  simulator/provider job. Free disks remain17GiB `/data1`,196GiB `/data`,42GiB
  locally. Node estimates are51.209/52.587GiB and global105.572GiB. The single
  a6 attempt is consumed; no retry is queued. Four fixed proposal envelopes
  are prepared. Automatic approval review rejected external Claude payload
  export before any submission; explicit approval for the three concrete
  instruction/annotation payloads is pending, while literal-patch work continues.
  Both concrete author/reference requests are prepared in `9c57862`, not frozen.
  No candidate matrix or policy-qualified gain exists yet.
- 2026-09-25 23:11 ET: eleven tickets remain resolved; 160 catalog records
  validate. Host and native-pilot workers are responsive; the identity worker
  completed normally with reviewed protocol and collector fixes ready to commit.
  Upstream native calibration remains complete. The DX100 native pilot holds
  lane 1 generation 394 at `2eda712`: uniform has 15/15 checked primary samples
  and a complete package; Kronecker has 11/15 checked samples at 23:11:53 ET.
  The upstream primary/diagnostic compile pair and both author traversal
  diagnostic builds passed at `81c0bc0`; lane 0 generation 273 released at
  23:11:29 ET. These are compilation results, not guest correctness or ROI
  acceptance. Uniform22 is registered with independently matching SG32/SG64
  adjacency hashes and author-selected source 2796003; see
  `observations/uniform22-preparation-a1.json`. At 23:09:31 ET the conservative
  available estimates were 51.356 GiB on node 0 and 51.525 GiB on node 1,
  both below the unchanged 52 GiB a6 admission gate; the actual 48 GiB attempt
  remains unused. The legacy lease is released; free disks are 17 GiB on
  `/data1` and 196 GiB on `/data`. A fixed-commit isolated full suite is being
  prepared. No empirical comparison protocol is frozen and no policy-qualified
  gain exists.
- 2026-09-25 22:41 ET: all three workers are responsive; 155 catalog records
  validate. Upstream native pilot a2 completed at 22:36 ET with 30/30 primary
  correctness checks, two complete packages, 12 checked diagnostic executions,
  and 36 memory observations; independently rehashed metadata is synchronized in
  `c91994c` and `docs/evidence/bfs-native-pilot-20260925-upstream18-a2.yaml`.
  Its noisy timing remains calibration evidence. Lane 1 generation 392 and the
  legacy lease are released; lane 0's external owner and child remain alive.
  The primary/diagnostic compile-only smoke is preparing at `2667f17`.
  Exact node-1 available estimate is 51.630 GiB, below a6's 52 GiB gate;
  a6 remains unused. Free space remains 17 GiB on `/data1`, 198 GiB on `/data`,
  and 42 GiB locally. The full local test run retained 653 passes, 3 skips, and
  12 failures, all addressed in separately passing focused checks; no clean
  full-suite result is claimed. Eleven tickets remain resolved; no empirical
  comparison protocol is frozen and no policy-qualified gain exists.
- 2026-09-25 22:11 ET: all three workers are responsive. Native upstream pilot
  a2 holds lane 1, generation 392, at exact commit `9fff245`; actual uniform-18
  materialization passed without changing the graph or reducing its scale. Lane 0
  remains held by its live external owner; the legacy lease is released. Free
  capacity is 17 GiB on `/data1`, 198 GiB on `/data`, and 42 GiB locally. The
  simulator a6 attempt remains unused. A real compile-only primary/diagnostic
  smoke is queued separately. All 124 catalog records validate. The full local
  suite is still running; known fixture timestamp and catalog-empty assertions
  were corrected and passed focused checks, without a full-suite success claim.
  The isolated public failure-contract demonstration completed 25 stages with
  synthetic timings explicitly excluded from empirical regression, matrix cells,
  and gain acceptance. No frozen candidate protocol or qualified gain exists yet.
- 2026-09-25 21:47 ET: all three workers are responsive. The live external
  lane-0 owner and Spatter child remain active; lane 1 and the legacy lease are
  released. Host free space is 17 GiB on `/data1` and 198 GiB on `/data`; raw
  output remains on `/data`. The a6 in-lane capacity refusal consumed no simulator
  attempt and its hashed receipts are preserved in
  `observations/dx100-a6-capacity-refusal.json`. The approved capacity estimator
  still holds dispatch below its exact threshold.
- 2026-09-25: Both actual scale-18 graphs and their corrected version-2 generator
  metadata are synchronized; see `docs/evidence/bfs-workloads18-20260925.yaml`
  and commit `05b936b`. Earlier incorrect generator declarations remain in the
  immutable version-1 records. Bytes, canonical adjacency, realized vertices,
  isolates, and ordered sources did not change. All 119 records validate;
  workload preparation does not establish calibration or a gain.

- 2026-09-25: Ticket 09 resolved from two complete real packages, fresh validated
  forward/reverse strategy queries, an exact-source patch handoff, and a fresh
  14-record chain. See `docs/evidence/bfs-package-handoff-20260925-a1.yaml` and
  the ticket Answer; metadata imported in `c4e94f6`. No performance gain is implied.

- 2026-09-25: Ticket 08 resolved from corrected a4 baseline/changed BFS profiles
  (12 checked diagnostic executions, 36 validated memory rows; metadata
  `5ea41132ac0f17b1ecb119cdaba4de3791c2dd0d`). The a3 memory audit remains
  invalid and preserved. Ticket 09 can now assemble packages from the new evidence.

- 2026-09-25: Tickets 06 and 07 resolved from independently checked a3 function/loop
  rediscovery: new helper ranked first and two nested loops executed; see their
  Answers for exact artifact hashes and metrics. The a3 memory family remains
  invalid under its retained audit; Tickets 08–09 remain unaccepted.

These entries retain historical milestones. The ticket table and each ticket's latest
evidence describe current acceptance; earlier publication-only or unexecuted notes
do not override the subsequent authorization and execution evidence.

- 2026-09-25 20:56 ET: all three workers remain responsive and the 30-minute
  heartbeat remains active. The 20:54 ET host check found the unrelated lane-0
  owner alive, lane 1 and the legacy lease released, 104 GiB available memory,
  17 GiB free on `/data1`, and 198 GiB free on `/data`. The real Callgrind control
  completed in seven seconds: STOP-before-DUMP reproduced unsigned wraparound
  with one and four threads; DUMP-before-STOP passed strict counter checks at
  both thread counts. Corrected BFS recollection still gates Tickets 08–09.
  Checkpoint `13fb89a` binds simulator checkpoint reuse to exact modeled settings;
  the six focused compatibility tests passed. The earlier full suite completed
  with 522 passed, three skipped, and three capability-fixture failures; those
  three assumptions were fixed in `dc12a01`, and all 14 capability tests passed
  separately. There is no full-suite rerun claim or qualified ROI gain.

- 2026-09-25 20:30 ET: all three workers responsive; mbit10 lane 0 remains held by
  another task, lane 1 is running the bounded simulator smoke, and the legacy lease
  is released. Live free capacity is 17 GiB on `/data1` and 198 GiB on `/data`.
  Profiling a3 completed its changed-helper demonstration (rank 1 and two new loops),
  but its final Callgrind value audit found unsigned-underflow counters. Those
  observations are retained as invalid; Tickets 08–09 remain unaccepted pending
  corrected collection. Local checkpoint `bccdd88` adds bounded simulator grids and
  separately instrumented author-traversal diagnostics; it is not execution evidence.

- 2026-09-25 20:20 ET: checkpoint `95909bc` separates the fixed author `DOBFSMAA`
  implementation from scalar `DOBFS`, binds evaluator entry points, preserves
  simulator source/repetition cells in complete profile packages, and exposes
  refreshed evidence through result chains. Targeted identity (29), aggregation
  (12), and package (28) checks passed. Native profiling attempt a3 is still running;
  no profiling or simulator ticket is resolved from this checkpoint alone.

- 2026-09-25: [Ticket 10](issues/10-dx100-operation-contracts.md) resolved: seven pinned source-backed operation contracts and 14 passing public capability/proposal tests. [Capability contract](../../docs/bfs-capabilities.md) separates model/interface support from executable readiness; no DX100 execution is yet claimed.

- 2026-09-25: [Ticket 02](issues/02-patch-proposal-to-candidate.md) resolved with 10 passing public subprocess tests: actual patch materialization, protected-source rejection, stable candidate identity, and fresh-process/index retrieval. [Workflow format](../../docs/format-v0.4.md) and `schemas/messages/rewrite-proposal.schema.json` define the provisional contract; no correctness or performance claim follows from candidate creation.

- 2026-09-25: [Ticket 01](issues/01-shared-bfs-identity-and-baselines.md) resolved: additive 0.4 source/evaluator ownership, scoped verification, and explicit comparison baselines. See [source contract](../../docs/bfs-source-identity.md), `tests/test_bfs_identity.py` (22 passing public workflow tests), and `apps/dx100/PROVENANCE.md` for the pinned unmodified import. DX100 source remains unchecked until real evaluation.

- 2026-09-25: Execution authorized; [implementation plan](implementation-plan.md) records assumptions and module ownership. Ticket 01 claimed. Review baseline: `1bdb7d4037916dea782c40239a6415b61a47f3c1`. A thread heartbeat checks progress, worker health, and evaluation state every 30 minutes.

- 2026-09-25: The user approved publication of 21 vertical-slice tickets. One file per ticket records exact blockers, externally observable acceptance, verification, and the execution hold. No ticket was started, claimed, or resolved.

- 2026-09-25: Requirements synthesized from the design discussion; both BFS starting implementations, both proposal routes, both graph families, native and DX100 evaluation, ROI priority, and future hardware/software co-design are retained.
- 2026-09-25: [Glossary](../../CONTEXT.md) distinguishes kernel, implementation, region, candidate artifact, rewrite proposal, hardware target, ROI, and comparison baseline.
- 2026-09-25: [ADR 0005](../../docs/adr/0005-kernel-identity-spans-sources-and-comparisons-name-their-baseline.md) records shared semantic kernel identity across source applications and explicit comparison baselines. It supersedes ADR 0004's implicit ancestry-based comparison rule; the code has not yet implemented this design.
- 2026-09-25: The user confirmed the full public SWDB workflow as the primary test boundary. Existing subprocess CLI tests supply the prior art; no new HTTP service or internal-module test boundary is mandated.
- 2026-09-25: Spec refinement completed with 60 user stories, 15 implementation decisions, 20 observable acceptance criteria, and explicit gates for pilot settings. This is documentation readiness, not completed functionality or performance evidence.

## Evidence pointers for future implementation design

These are navigation aids for the inspected checkout, not stable API requirements. SWDB HEAD inspected: a38dfac2e4849235158ec2cdfb2d2623ffe6b963. All sources below were inspected during the 2026-09-25 session; no new builds or experiments were run.

### Current SWDB behavior and testing prior art

| Evidence | Relevance |
|---|---|
| [Public command interface](../../swdb/cli.py) | Existing query, view, add, and profile entry points; no current full proposal/rewrite/evaluation workflow |
| [Subprocess test harness](../../tests/conftest.py) | Fresh processes, temporary records, isolated generated query database |
| [Profile tests](../../tests/test_profile.py) | Profile-to-later-view retrieval, incomplete metrics/timeouts, correctness failure, and gated real lab-host execution |
| [Record-add tests](../../tests/test_add.py) | Persist, validate, rebuild, and observe through a later public query |
| [Implementation/strategy comparison tests](../../tests/test_applies.py) | Current ancestry-based pairing and missing profile cases; relabeled fixtures are not performance evidence |
| [Benchmark fixture](../../tests/fixtures/profile/stub_bench.py) | Predetermined times used for contract behavior, not speedup claims |
| [Profiler](../../swdb/profile.py) | Current whole-call timing and configured-symbol Cachegrind aggregation; not the required automatic ranked-region workflow |
| [Application resolution](../../swdb/store.py) | Current inherited application context that must accommodate the accepted cross-source design |
| [BFS implementation record](../../records/implementations/gapbs-bfs-do.yaml) | Existing code/loop/access-pattern catalog and the limitation of static index-stream assumptions for BFS traversal |
| [CPU intrinsic schema](../../schemas/intrinsic.schema.json) | Existing ISA-wrapper semantics; accelerator resource/synchronization requirements need an appropriate contract |
| [Upstream GAPBS provenance](../../apps/gapbs/PROVENANCE.md) | Local upstream source is revision 2972aeb2703165bafd921222f4ed7196f542d3a8, not the DX100 source |

### DX100 artifact evidence

Pinned artifact revision: e4fc4afdf894f295442cef3604667a469fab8e62.

| Evidence | Relevance |
|---|---|
| [Artifact README](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/README.md) | Build/model description and artifact-wide resource estimates, not measured BFS-only costs |
| [BFS source](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc) | Actual top-down execution, conditional accelerator use, ROI boundaries, and simulator exit before enclosing verification |
| [Accelerator API](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/API/MAA_gem5.hpp) | Supported operations and memory-mapped API behavior to inspect for contracts |
| [Simulator runner](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py) | Artifact BASE/accelerated configuration differences and checkpoint automation requiring pilot validation |
| [Statistics parser](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/parse.py) | Existing statistics interpretation and hardcoded ticks-to-cycles conversion |
| [Benchmark harness](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/benchmark.h) | Source selection, trial loop, timer, and verifier result handling |
| [Graph generator](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/generator.h) | Available graph families and seeded generation |
| [Simulation exit implementation](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/pseudo_inst.cc) | Simulator-loop exit semantics; continuation is an untested correctness option |

### Extensa evaluation references

| Evidence | Relevance |
|---|---|
| [Primary measurement definitions](/Users/yanrujhou/CLionProjects/MemAcc/AgenticRefiner/refiner/measurement.py) | Primary target-operation quantity versus diagnostic timing |
| [GAPBS benchmark harness](/Users/yanrujhou/CLionProjects/MemAcc/DataLayoutAPI/benchmarks_vanilla/gapbs-master/src/benchmark.h) | Timer around the complete kernel call, with verification outside it |
| [BFS adapter](/Users/yanrujhou/CLionProjects/MemAcc/AgenticRefiner/adapters/gapbs-bfs.yaml) | Protected source surfaces and kernel timing scope |

The spec preserves these evidence boundaries. It does not import historical timings, fixed noise thresholds, or unverified current host capabilities as new results.

### Native evaluation acceptance — 2026-09-25

Ticket [03](issues/03-native-bfs-evaluation.md) is resolved: evaluator-owned native
ROI and structural correctness, durable failure stages, 17 contract cases, and a
real three-source mbit10 lane-1 DX100 scalar diagnostic. See
[native evaluator design](../../docs/bfs-native-evaluator-design.md) and metadata
commit `283467878fcce65a988f7dc28f151cc6d022d520`. This is pre-freeze diagnostic
evidence; automatic function/loop/memory collection remains tickets 06–09.

- 2026-09-25: [Ticket 11](issues/11-workloads-and-comparison-protocols.md) resolved with 27 protocol tests, 8 compiled streaming-SG tests, and 12 add/document checks. [Protocol contract](../../docs/bfs-protocol.md), `swdb/bfs_protocol.py`, `swdb/sg_stream.py`, and `tools/bfs_native/sg_identity.cc` define immutable workload identity and comparison enforcement. This is contract acceptance, not a candidate gain or empirical protocol freeze.

### Instruction and annotated-source acceptance — 2026-09-25

Tickets [04](issues/04-instruction-rewriting-and-repair.md) and [05](issues/05-annotated-source-rewriting.md) are resolved: real Claude source changes for natural-language, structured, and annotated inputs each have a three-source independently verified native diagnostic. The ten-test bounded rewrite suite passes, and earlier failed attempts remain linked. See [handoff](../../docs/bfs-handoff.md) for exact record IDs. Tickets 17–20 remain separate frozen-workload acceptance obligations.

- 2026-09-25: [Campaign plan](campaign-plan.md) records operator-selected strategies, provider/evaluation limits, and failure rules before candidate assessment. Native and proposal client drivers are preparatory; no frozen coverage or gain is claimed.

## Corrective proof launch cutoff — 2026-09-26 09:40 ET

The a2 launch cutoff passed without the exact two-commit export approval.
The corrective attempt remains unused; no launch, reparse, or result is claimed.
Fewer than 1,200 seconds remain in its fixed 10:00 ET window, so dispatch is
prohibited under that plan. The rejected export is not retried and the deadline
is not extended. Local paired calibration implementation and fixed-commit
regression verification continue independently.

## Execution checkpoint — 2026-09-27 01:00 ET

T15 recovery is now running on socket 1 generation 439 with unchanged 09:14 ET
hard end; the actual uniform-18 gem5 process is live. T16 remains prepared and
waits for external socket-0 generation 339 to release. All three delegated
workers are responsive, the prior failed T16 identity set is absent, and the
legacy lease is released. [Host evidence](observations/host-health-20260927-0100.json).
No final acceptance cell or gain has been qualified.

## Remaining client readiness — 2026-09-27 ET

The [T17/T20 audit](operator-recipes/t17-acceptance/README.md) identifies exact
T15, diagnostic-region, allocation and admission bindings for the remaining fixed
operator; 125 existing public API contract tests pass.
[T18/T19 templates](operator-recipes/native-acceptance/README.md) preserve actual
retained candidate/patch/provider provenance and leave empirical protocol and
package fields unresolved. No additional evaluation was launched or ticket resolved.

## Lease recovery checkpoint — 2026-09-27 02:25 ET

T15 supervision recovery failed before public correctness verification. Its
[independent closure](observations/failed-t15-supervision-closure-20260927.json)
retains the failed result and charges 4,551 seconds / 1,433,210,880 bytes.
Fresh T15/T16 plans retain original hard ends and require exact-runtime Linux
lease-transition proof. T20 context2 provider is running on node 1 generation 440;
node 0 remains externally occupied. No acceptance cell or gain is qualified.

## Provider and repair checkpoint — 2026-09-27 02:30 ET

The context2 provider attempt timed out after 600.315539094 seconds, returned no
candidate, and was independently closed; its subsequent wrapper JSON parsing
failure remains preserved. [Terminal observation](observations/provider-context2-terminal-independent-20260927.json).
No automatic retry was launched. The remaining floored provider allowance is
1,031 seconds. The reviewed lease repair is committed as `4743d52`; its minimal
runtime export is `07baead5` (806 files), pending fresh actual Linux proof.
The original simulator deadlines and all failed-attempt charges remain intact.

## Fresh Linux lease proof — 2026-09-27 02:36 ET

[Independent closure](observations/lease-proofgroup-independent-closure-20260927.json)
verified 51 supplemental, five ownership and two interruption cases, all passing
without skips on runtime `07baead5`. All three cleanup ledgers settled, retained
identities were checked twice, and node-1 generations 441–443 released. Actual
execution took 27.728543 seconds and retained 3,395,584 bytes across all five roots.
Both tasks retain the full 600-second/2-GiB reservation. This is contract proof;
T15/T16 scientific admission is being prepared and no acceptance cell is complete.

## Scientific recovery launch — 2026-09-27 02:41 ET

T15 launched at 02:39:53.162109 ET on node 1 generation 444 with unchanged
09:14:09.851819 ET hard end. The uniform-18 series is running; no accepted sample
is yet reported. [Independent startup](observations/t15-lease-startup-independent-20260927.json).
T16 admission independently passed and waits for external node 0 generation 347
to release; no T16 scientific job was launched. The legacy lease is free.
Tickets remain 14 resolved / seven claimed, with zero completed final acceptance
cells. The heartbeat remains active while evaluation and review work continue.

## Periodic host check — 2026-09-27 02:45 ET

T15 remains running on node 1 generation 444, with live batch, series and guest
processes and updating logs; no completed sample is reported. The guest RSS was
about 28.8 GiB, within unchanged bounds. Node 0 generation 347 is externally held;
the legacy lease is released. Free space was approximately 158.8 GiB on `/data`
and 15.8 GiB on `/data1`; raw output remains under `/data`.
All delegated workers are responsive. T20's opt-in prompt projection and bounded
continuation are under review; no additional provider call or allowance was used.

The [typed health observation](observations/host-health-20260927-0243.json)
retains process start identities and log freshness. The prompt projection passed
eight author and eight independent public contract tests; six independent default
prompt comparisons remained byte-identical. Full profile packages remain retained.
This local change does not establish provider completion or candidate acceptance.

## Periodic evaluation checkpoint — 2026-09-27 03:15 ET

[Live host observation](observations/host-health-20260927-0313.json), taken at
03:14:19 ET, confirms T15's unchanged gem5 process is making CPU progress, with
fresh telemetry and simulation logs. Its first primary ROI seal exists; verification
is still running and accepted samples remain zero. RSS is about 32.56 GiB, below
the unchanged limits. Node 1 generation 444 is ours; node 0 generation 348 remains
externally held, and legacy generation 77 is released. T16 remains admitted but
unlaunched. The context3 operator packet `4f57306c` is Git-delivered for readiness
inspection; no fourth provider call has run. Tickets remain 14 resolved / seven
claimed, with no final acceptance cell qualified.

## Evaluation limit checkpoint — 2026-09-27 03:44 ET

[Live health](observations/host-health-20260927-0343.json) confirms gem5 completed
but the first public evaluation remains in CPU-active result processing, with fresh
telemetry and zero accepted samples. Its original stage bound ends nominally at
04:43:01 ET; the batch hard end remains 09:14:09.851819 ET. Node 0 generation 349
is externally held, node 1 generation 444 belongs to T15, and legacy is free.

The [fixed scheduling gate](observations/t15-budget-and-trace-analysis-summary-20260927.json)
requires 21,630 seconds remaining to start each series. The second series can no
longer start after the elapsed 03:13:39.851819 ET cutoff. Therefore the current
plan cannot complete the two-series grid; continuing the first series does not
waive the missing family or qualify acceptance. No deadline or allowance was reset.
Context3 host rendering and immutable runtime verification passed, but both lanes
remain occupied and no provider call has started.

## Verified T15 failure and next work — 2026-09-27 04:16 ET

[Independent closure](observations/t15-lease-failed-terminal-independent-20260927.json)
verified all 246 retained identities absent twice and settled cleanup. The
[diagnosis](observations/t15-lease-witness-size-diagnosis-20260927.json) identifies
the actual rejection: a 72,432-byte ROI seal exceeded the reader's 65,536-byte
seal limit; the 39,877-byte syscall trace was within its own bound. T15 remains
failed with zero accepted samples. Charge 5,685 seconds through independent
closure, including 4,028 seconds of execution, and 1,432,768,512 retained bytes;
no historical charge was refunded.

The trace-parser optimization passed independent review and is committed as
`6f1e700`; it has not altered retained execution evidence. A separate bounded
seal-reader repair is now under development. T16 is held against this known
reader defect. Context3's reviewed one-call submission has started on node 0;
its existing provider allowance and original wrapper limits remain unchanged.

## Provider closure and T16 recovery preparation — 2026-09-27 04:46 ET

Context3 returned a provider timeout with no candidate. Its independent closure
and exact proposal/provider metadata are retained; actual consumption was
600.321021632 seconds, leaving 430.678978368 seconds after prior conservative
floors. No further provider call is admitted by that closed attempt.
The seal producer/reader repair passed 176 independent tests and is committed
as `1699d99`. Fresh T16 runtime proof and admission are being prepared with an
additional 600-second/2-GiB reservation deducted from the existing T16 allowance.
Its original deadlines and scientific grid remain unchanged. No T15 allowance
has been restored. [Live health](observations/host-health-20260927-0443.json)
confirmed node 0 free, node 1 externally held, legacy free, and no owned BFS jobs.

## Fresh Linux seal proof — 2026-09-27 04:56 ET

[Independent closure](observations/seal-proofgroup-independent-closure-20260927.json)
verified the exact `923cf33` runtime: 66 supplement, five owned-job, and two
interruption cases passed on mbit10 with zero skips. Strict cleanup and all
recorded process identities were checked twice. Actual wall time was 27.015572
seconds and retained storage was 5,246,976 bytes; the full 600-second/2-GiB
reservation remains charged to T16. This is infrastructure proof, not scientific
acceptance. The fresh T16 scientific checkout matches all 809 pinned files; its
operator and admission are being sealed before dispatch. Node 0 was released,
node 1 remained externally held, and the legacy lease was free at closure.
