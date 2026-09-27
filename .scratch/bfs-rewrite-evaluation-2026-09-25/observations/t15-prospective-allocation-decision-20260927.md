# T15 prospective recovery allocation decision

Created: 2026-09-27 ET. Updated: 2026-09-27 ET. **Historical proposal followed by approval and user stop; see the dated handoff below. No allocation clock, new execution plan, admission or dispatch was created.**

The original T15 window cannot admit further work: its last full-series start was
2026-09-27 03:13:39.851819 ET and its hard end is 09:14:09.851819 ET. These remain
unchanged. Completing the assigned grid needs an explicitly approved new empirical
allocation; existing implementation/transfer authorization does not extend this window.

## Evidence and preserved cost

| Retained observation | Actual value | What it supports |
|---|---:|---|
| First uniform18 checkpoint | 77.522 s | One checkpoint, not either family's full cost |
| First uniform18 simulation | 2,031.024 s | Simulator finished; public correctness/package did not pass |
| Failed first series | 3,990.450 s; zero accepted pairs | Includes preparation and expensive postprocessing; no accepted timing sample |
| Compressed ROI trace | 1,296,681,706 bytes | One trace, not a diagnostic-size bound |
| Failed attempt retained allocation | 1,432,768,512 bytes | One closed attempt including dispatch |
| Cumulative historical charge after closure | 14,433 s; 22,482,972,672 bytes | Retain in full, separately from any proposed increment |

Sources: [cost/trace observation](t15-budget-and-trace-analysis-summary-20260927.json),
[independent failed terminal](t15-lease-failed-terminal-independent-20260927.json),
and [seal diagnosis](t15-lease-witness-size-diagnosis-20260927.json).
The 72,432-byte ROI seal exceeded the old 65,536-byte reader cap. Repaired runtime
`2a64a188f08811baf09ab9c61e69633c3d45a7f2` includes the reviewed finite 32-MiB seal
ceiling and parser prefilters. It is a T16 continuation runtime, **not a T15
admission**. Its synthetic parser speedup supplies no actual-trace cost estimate.

## Minimum unchanged scientific scope

Retain the two registered families, uniform18
`bfs-20260925-uniform18.cd2169a5c421baf7` and kronecker18
`bfs-20260925-kronecker18.48de8267ac2098d5`, each with ordered sources
`[0, 1234, 7777]` and two configured replays. That is **12 primary/diagnostic pairs,
24 individual executions**. Keep the unchanged author MAA source/binaries,
four guest cores, traversal ROI, MAA configuration (8-MiB L3, associativity16,
tile16,384), complete structural verification and actual accelerator coverage.
Do not substitute T16 uniform22, tiny witnesses, partial traces, or fixture results.

Protocol publication requires both families' complete packages, six primary
executions per family, observed full/tail/competing-parent cases, repeatability,
and the existing native/reference qualification prerequisites. Keep calibration
separate from candidate assessment; freeze actual settings before the latter.

## Concrete proposal for approval discussion

**Concrete option requiring explicit approval: an incremental48-hour outer
envelope and96GiB of new retained raw output. No approval or allocation is recorded.**
The earlier30–48-hour /48–96-GiB ranges are planning scenarios, not a confidence
interval or a completion promise. Repeating the failed first-series cost across24 executions gives26.60hours;
repeating its trace and total retained footprint gives28.98GiB and32.02GiB.
Neither extrapolation measures Kronecker or diagnostic cost. The upper ceilings
provide headroom for those unknowns, package/readback, guards and finalization.
The proposed48-hour ceiling has this exact partition; none is allocated yet:

| Component | Maximum seconds | Included work |
|---|---:|---|
| Preparation | 3,600 | Source/model/compiler checks, record/dispatch setup, any fresh proof (at most600seconds), freezes and admission |
| Uniform family series | 82,800 | All six primary/diagnostic pairs, first-pair gate, collections and per-pair readbacks |
| Kronecker family series | 82,800 | All six primary/diagnostic pairs, collections and per-pair readbacks |
| Finalization | 3,570 | Final public retrieval, publication checks, retained accounting and independent closure observations |
| Scientific supervisor cleanup | 30 | One shared scientific-stage ledger; no per-child or per-stage replenishment |
| **Total** | **172,800** | **48hours including all overhead** |

The existing proof machinery retains its own fixture/auditor cleanup ledgers,
entirely contained within the600-second proof allowance inside preparation.
Those ledgers add no time beyond the3,600-second preparation ceiling or172,800-
second outer envelope. The separate30-second reserve applies to the scientific
supervisor; this proposal introduces no cross-proof ledger redesign.

The first-pair gate is the first of the unchanged12pairs, not a13th pair or a
retry. It consumes its family's allowance, not an extra allocation.
Before either family starts, its full82,800seconds plus remaining finalization
and shared cleanup must fit the single approved outer deadline. Preparation and
finalization overruns stop the attempt; they cannot borrow unapproved time.
The existing author-series ceiling of86,400seconds admits the proposed82,800,
but the new aggregate plan still requires reviewed implementation before export.

A storage adaptation is **known to be required**: retain an independently enforced
96-GiB incremental aggregate, reserving a4-GiB overhead subpool (up to2GiB for
a fresh proof and2GiB for preparation/finalization records, views and sidecars).
Pass each series `min(60 GiB, remaining aggregate GiB - unspent overhead reserve)`
(rounded down, rejecting a nonpositive remainder). The two series therefore share
at most92GiB; two60GiB caps are not independent120GiB grants. Never pass96GiB directly to the author-series CLI, whose ceiling is
60GiB. Both completed-family outputs remain counted when admitting the next.
All preparation/proof/view/cache/sidecar growth counts within the96GiB aggregate
and its assigned subpool; a subpool overrun stops the attempt. Per-series record
views and sidecars count against that series and the aggregate. Build outputs
remain separately counted under the existing build policy. A series may
fail its60GiB ceiling even with aggregate space remaining; no automatic widening
or retry is proposed.

**Serialize this proposed T15 work after T16's independent terminal closure.**
A driver exit alone is insufficient: require owned-process absence, settled cleanup,
lease release, and final stable storage recount. No T16 unconsumed allowance may
still grow while T15 occupies the proposed storage pool. Likewise, do not overlap
another BFS allocation that can consume this proposed headroom. Immediately before
admission, require at least126GiB physically free on the chosen output mount
(96GiB new retention plus the shared30GiB reserve), and the separate10GiB build-mount
reserve. Physical free bytes already exclude all retained historical artifacts;
do not subtract the historical20.939GiB again. Preserve those artifacts in full.
Fresh node/global memory and both socket/legacy lease checks remain mandatory.
Keep48GiB guest-process memory,52GiB sampled-tree ceiling, one shared30-second
cleanup reserve and at most two socket lanes across all work. Failures consume the
new allowance and remain retained. Host availability is unverified by this document.

Before committing the rest of the allocation, the first complete primary/diagnostic
pair must demonstrate that actual correctness parsing and package collection fit
their sealed bounds. In particular, the existing120-second profile collection
limit is unproven for this trace size. A failure is a retained stopping condition,
not permission to raise that limit or retry. No old trace is reparsed in this proposal.

## Outstanding admission dependencies

1. Explicit approval of an incremental numeric wall/storage allocation and its new
   absolute start/end; original charges and deadlines remain visible and untouched.
2. A new T15 plan with fresh IDs, complete unchanged grid, bounded accounting and
   prospective stop rules; immutable runtime export and matching Linux proof.
3. Live checks of both socket/legacy leases, helper version, disk/node capacity,
   retained source/compiler/model/binary hashes and required source attachments.
4. Actual first-pair collection feasibility, followed by the full grid and fresh
   public retrieval. Then source-specific native qualification and protocol freeze;
   no outcome is promoted merely because a process exited or a seal exists.

This document changes no ticket status, plan, budget, deadline, or authorization.

## Approval and stopped-work handoff — 2026-09-27 ET

After independent review, the user directly approved proceeding with the reviewed
48-hour /96-GiB incremental recovery and similar necessary bounded future work,
then explicitly instructed: stop here, synchronize everything including docs,
and resume later. The earlier proposal-only statements above describe preparation
before that approval; they do not negate the later authorization. The stop now
governs execution. Approval is retained for resumption, not consumed or treated
as an allocation start.

Implementation had reached design discussion only when stopped. **No T15
incremental request/plan, controller/helper, batch hook, runtime export, proof
ID, allocation timestamp, admission or scientific dispatch was created.** No
production Python file was edited for this new allocation. No implementation
tests or remote commands ran for it. The completed independent document review
remains [the revised review](t15-allocation-decision-revised-independent-review-20260927.json);
it does not validate an unimplemented controller. No syntax check is necessary
for this Markdown-only handoff.

The proposed controller design for later review was to retain the historical
14,433-second /22,482,972,672-byte charge separately; prospectively reserve all
3,600 preparation seconds including the600-second proof; clamp scientific time
to both the new allocation end and the remaining169,200-second partition;
reserve3,570 finalization plus30 shared scientific cleanup before each82,800-
second series; and monitor the96-GiB total,4-GiB overhead and92-GiB shared series
pools with each series capped at60GiB. These are **unimplemented design notes**,
not reviewed controller behavior. The exact typed identities, storage
roots and terminal evidence references still need a concrete plan and tests.

On resumption, first establish current T16 independent terminal closure and
storage state, then implement and independently review the approved partition,
fresh identities/runtime/proof and boundary tests. Retain the existing120-second
first-pair collection gate, unchanged12-pair scientific grid, all old failures,
and the original T15 deadlines. Do not restart the old attempt or infer a new
clock from the approval date. No action should occur while the user's stop is
in effect.
