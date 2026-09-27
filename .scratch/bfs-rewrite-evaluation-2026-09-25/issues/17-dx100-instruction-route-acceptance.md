# 17 — DX100 BFS: instruction-route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-27 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 04, 10, 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## Primary evidence durability — 2026-09-27 00:24 ET

The exact existing primary evaluation YAML is now Git-backed in commit
`efdadb8b1e7ff22562d07e9f63007198a6b6352d` and imported locally; see
[transfer receipt](../operator-recipes/t17-diagnostic/primary-evidence-transfer-20260927.json)
and [catalog validation](../observations/t17-primary-local-import-20260927.json).
This records the retained build without rerunning it. Diagnostic compilation
and empirical acceptance remain pending the fresh compatible Linux proof.

## What to build

Demonstrate the full public workflow for a representative SW Ensemble submission in natural language: query the DX100 scalar top-down BFS profile package, apply the specified optimization, and retrieve independently checked results for an accelerator-using candidate on both Kronecker and uniform-random graphs.

This is one starting implementation × proposal route, covering two graph-family cells and the DX100-source accelerator minimum. Use actual source changes, compilation, DX100 execution, and profiling. The producer is a labeled test client, not Peter's live agent.

## Scope and specification coverage

Covers AC06–AC11, AC13–AC14, AC16, AC18–AC20 and contributes evidence toward AC17. Applies D06–D14. A gain is not required in this individual ticket; correct accelerator execution on both graph families is required.

## Acceptance criteria

- [ ] Obtain the exact baseline source/context, ranked regions, and dynamic memory evidence through the public profile-package query. Record the package identity used by the test client.
- [ ] Submit natural-language instructions in the versioned proposal envelope, identifying the strategy, target regions, preserved semantics, ROI, and supported DX100 operation/interface requirements. Preserve test-client and SW-producer provenance.
- [ ] Produce real changed source from that proposal, including any necessary wrappers or supporting edits over existing operations. Record the source snapshot, resulting binary, diff, and bounded repairs; evaluator-owned correctness and ROI surfaces remain protected.
- [ ] Evaluate a qualifying candidate on both graph families under ticket 15's frozen protocol. Replay its actual graph/source workloads and retain the explicit unaccelerated DX100-source comparison baseline and declared target configuration.
- [ ] For both graph families, retain BFS structural correctness evidence covering the timed binary and affirmative evidence that the accelerator path actually executes. Cover relevant full/tail tiles and competing parent updates; scalar fallback alone does not qualify.
- [ ] Retrieve the BFS-level ROI duration, selected-region durations, and refreshed dynamic memory observations with scope, units, source correspondence, and attribution limits. Keep simulated target time and simulator host cost distinct.
- [ ] A fresh public query reconstructs the profile package, proposal, candidate, correctness, hardware/interface identities, protocol, comparator, timing/profiling evidence, and raw-artifact references.
- [ ] Retain every failed attempt and regression. Enforce the declared repair/run budgets and host resource rules. If no candidate meets correctness and actual acceleration on both families, leave this acceptance case incomplete and return evidence to the proposal owner rather than changing strategies autonomously.

## Verification and demonstration

Run the real query → proposal → rewrite → check → DX100 measurement/profile → retrieval sequence. Fast fixtures may check message or failure behavior, but cannot establish acceleration, correctness of the timed BFS binary, dynamic behavior, or performance.

## Dependencies and boundaries

Ticket 04 supplies instruction rewriting and bounded repair; 10 supplies operation contracts and capability checks; 15 supplies the frozen candidate protocol and verified evaluator/profiling prerequisites. Complete profile packages and the simulation backend are inherited through those dependencies.

Do not require every BFS phase to accelerate. Do not require a gain in this case or a win over the authors' accelerated version. No new hardware operation, live collaborator integration, or entire-paper campaign is included.

## Implementation progress

2026-09-25: Root owns dependent preparation of the representative proposal and public campaign driver. No candidate performance assessment begins before Ticket 15 freezes compatible protocols. Actual acceptance remains pending; preparation does not satisfy the listed blockers.


## Initial provider result — 2026-09-26 11:13 ET

The explicitly approved `dx100-instructions` source/profile payload was sent through
Claude Code in the bounded three-request socket-0 batch. This request created an unverified candidate.
The [initial batch summary](../observations/provider-initial-summary-20260926.json)
retains the actual outcome; no repair, retry, compile, performance evaluation or
final acceptance followed from this submission. The original annotations and
proposal context remain retained.

The six-file result packet was committed on mbit10 as `5f1b802`, but automatic
approval review rejected its new GitHub packet/branch. Exact approval is pending;
canonical proposal/candidate records have not been imported into this checkout.
See [the concrete inventory](../observations/provider-export-inventory-20260926.json).

## Prospective build-only preparation — 2026-09-26

The [bounded build-only plan](../t17-build-only-plan-20260926.md) retains an exact
public request for the existing initial candidate and metadata-only host binding
checks. It remains undispatched, follows native/a3/fixed-coverage cleanup, and
permits one compilation without a provider call, retry, or repair. Compilation
does not establish correctness, actual acceleration, or this ticket's acceptance.

## Actual fixed candidate compilation — 2026-09-26 14:47 ET

The existing initial instruction candidate compiled once through the public
DX100 path. All nine public calls, including fresh result and chain retrieval,
returned zero within 55.878 seconds (compilation 32.908 seconds). Independent
terminal inspection confirms all 15 owned PID/start identities absent and
socket-0 generation 324 released. The original proposal, source, candidate,
provider budget and measured public checkout remain unchanged; no provider call
or repair occurred. See the [terminal receipt](../observations/t17-build-only-terminal-20260926.json).

The actual binary hash is `852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527`.
Correctness remains unverified, profiling incomplete, and timings empty. This
proves compilation only. Both graph families, actual accelerated correctness,
reprofiling and frozen-protocol comparison still remain; the ticket stays claimed.


## Diagnostic preparation — 2026-09-26 21:40 ET

A [new bounded diagnostic build](../../../docs/bfs-t17-diagnostic-build-20260926.md)
retains the completed primary binary and candidate without rebuilding or
resubmitting them. Its [preparation receipt](../observations/t17-diagnostic-build-preparation-20260926.json)
records 24 passing focused tests and the distinction between real short-lived
subprocess checks and synthetic host/compiler fixtures. The fixed request adds
only a fresh ID and diagnostic-region instrumentation. Independent review,
same-host isolated record materialization, admission and actual compilation
remain pending; no new guest execution or acceptance is claimed.


2026-09-26 21:49 ET review: independent review reproduced an admission input
outside the counted dispatch directory. The [repair](../observations/t17-diagnostic-admission-fix-20260926.json)
requires the exact canonical admission path and rejects symlinks. All 27 author
checks pass; the [independent review](../observations/t17-diagnostic-standards-review-20260926.json)
retains the original red and passing follow-ups. Actual diagnostic compilation
and host admission remain pending; the existing primary is unchanged.


## Export checkpoint — 2026-09-26 22:03 ET

The [exact five-file diagnostic export](../observations/t17-diagnostic-export-20260926.json)
`46f3a264` passed independent blob/dependency review, but automatic approval review
rejected its push to the private repository because it falls outside the earlier
exact transfer list. Payload-specific approval is pending; no alternate transfer
or host build occurs. The future execution runtime must also contain the later
allocator repair before admission. Existing primary, provider budget and source
remain unchanged; both-family acceptance remains open.


## Current proof reader repaired — 2026-09-26

The combined-runtime review reproduced a four-versus-five-case Linux proof
mismatch before any transfer. The [repair](../observations/t17-five-case-proof-preparation-20260926.json)
requires the five exact passed cases and matching allocator identity for new
T17 admission, preserving historical scalar proof compatibility. Independent
[review](../observations/proof-cardinality-standards-recheck-20260926.json) passed
ten checks. The final exact packet's isolated test subset passed 553 checks with
ten Linux-only skips; actual Linux execution and diagnostic compilation remain
pending. The earlier five-file export remains unused.

The reviewed [controlled-simulator readiness note](../../../docs/bfs-t17-controlled-simulator-readiness-20260926.md)
identifies the exact retained builds, freeze derivation and finite four-series
recipe still needed after T15 and diagnostic prerequisites. It creates no
protocol, allowance or execution claim.


## Diagnostic setup failure and prospective allocation — 2026-09-27

The first diagnostic attempt failed at its initial public get because the record
view omitted two referenced implementation source attachments. No compiler,
provider, guest, or diagnostic evaluation ran. The exact failed driver and all
outputs remain retained. The [independent closure receipt](../observations/t17-diagnostic-failed-terminal-20260927.json)
verifies both process passes, no live owned work (the exact pane was a zero-RSS
zombie), socket-1 generation 438 released, and a settled four-event cleanup ledger
using 0.2261140875518322 seconds. Final allocated storage across all three roots
was 18,321,408 bytes.

The original 00:47:10.605637–00:57:10.605637 ET 600-second window has expired; it is
not reset. Conservative historical wall accounting retains 593 seconds from outer
start through the independent final observation (592.764382 seconds before
rounding), including the readback delay, not a claim of CPU time. Existing primary
binary/source/provider evidence remains unchanged.

Repair 3c09f3c admits exactly the two runtime-hash-bound `.cc` attachments; root's
actual-public-get regression and focused checks passed 29 tests. No retry followed.
The [prospective acceptance manifest](../operator-recipes/t17-acceptance/README.md)
includes one unused diagnostic request as a charged prerequisite of a future
route allocation derived from qualified T15 costs. Aggregate and series budgets,
workloads, protocol, and future clock remain unresolved, with dispatch explicitly
false. Eight planning-contract tests pass; no empirical acceptance is claimed.
This ticket remains claimed and all acceptance boxes remain open.

## Fixed client wiring checkpoint — 2026-09-27 02:46 ET

The [pure operator preparation](../observations/t17-operator-preparation-20260927.json)
now renders the four fixed series through the existing public client with both retained
build IDs, the complete-call frozen protocol, explicit stage/resource bounds, and shared
cleanup binding. All four synthetic commands parse with the actual client argument
definitions; 39 local planning/command controls passed. No subprocess or remote execution
was performed. The preview preserves null aggregate bounds, clock, and T15-dependent
workloads/protocol; dispatch remains false and acceptance criteria remain open.

## Stream C diagnostic a2 prepared, launch not performed — 2026-09-27 10:40 ET

Branch `codex/bfs-dx100-candidates-20260927-b1` (commit `b1fcf76`, root-reviewed under R9)
adds a bounded public-job launcher (`../operator-recipes/stream-c-20260927/`). Job
`t17-diagnostic-a2` runs exactly one public `dx100-compile` of the unused prospective request
`bfs-t17-diagnostic-build-only-20260927-a2` (repair 3c09f3c is in main) inside a node0 socket
lane, with a 270 s call cap in a 420 s outer cap, then a fresh chain `get`. No provider, repair,
guest or primary rebuild. Root assigned node0 at 10:35 ET. A clean host checkout exists at
`/data1/yanruj/EvolveSWDB_streamc_20260927_b1` (b1fcf76; `swdb validate` 253 records OK).
**This session's permission gate (shared-host mutation) blocked the launch, so it has not run;
it needs the user's permission.** The diagnostic binary and the region correspondence remain
pending. The a1 failure and its charges are unchanged.

Unaccelerated baseline: the four scalar v2 v2-adapter build records are now imported byte-exact
into Git ([import receipt](../observations/stream-c-scalar-v2-baseline-import-20260927.json)).
The `dx100.primary`/`dx100.diagnostic` pair is the T17 `dx100-bfs-scalar` comparison baseline.
Their enclosing preparation stays failed at finalization, and the import does not change that.
No acceptance box changes.
