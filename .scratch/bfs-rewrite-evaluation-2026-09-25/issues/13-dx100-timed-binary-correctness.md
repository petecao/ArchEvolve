# 13 — DX100 timed-binary correctness

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 12
**Spec:** `../spec.md`

## Current checkpoint — 2026-09-26 18:28 ET

The [new A2 Linux admission checks](../observations/a2-linux-fixtures-20260926-a1.json)
ran against exact `67313d9` with separate supervisor `3f38a2b`. The two owned
cleanup cases pass, with independent proof and released generation 403. Both
interruption cases fail at validation because their synthetic machine record
disables the real host's required socket policy. They never enter simulation.
Their failure and verified generation-404 process/lease closure are retained;
no interruption proof or simulator admission is claimed. The fixture is being
corrected without weakening the production guard. Actual A2 remains unused,
with the same 21:00 ET cutoff and 3,600-second allowance. T13 remains claimed.

## Historical checkpoint — 2026-09-26 13:56 ET

The [fixed full/tail/competing-parent case](../observations/dx100-coverage-start-20260926.json)
started at 13:56:02 ET on socket 0 generation 321 from `53f2e768`. Both actual
Linux cleanup fixtures passed on that exact code first. Capacity, graph
generation and public registration passed; compilation is running at this
observation. No accelerated-coverage or ticket-completion claim is made before
actual execution and the independent terminal audit. The hard outer stop is
14:56:02 ET, with no retry.

## Historical checkpoint — 2026-09-26 13:38 ET

The single a3 execution passed its exact timed-guest structural verifier and
independent terminal audit. Driver, observer, supervisor and outer exits are
zero; socket 0 generation 319 is released. The retained author-traversal ROI
is 29.122772 microseconds. The explicit v2 exit witness completed; actual normal
termination remains false and is not inferred. See the
[a3 terminal receipt](../observations/dx100-witness-a3-terminal-20260926.json).

The tiny graph does not establish accelerated full/tail/competing-parent
coverage. Those actual observations remain required before resolving T13.
A1 remains failed and a2 expired unused.

## Historical checkpoint — 2026-09-26 11:42 ET

Exact code transfer is complete. The read-only corrected-parser diagnosis passed;
its evidence and limits are appended below. A1 remains failed, a2 expired unused,
and a3 is prospectively scheduled after paired calibration with latest launch
15:20 ET / hard end 15:40 ET. No new simulator correctness result is claimed.

The independently reviewed one-attempt continuation is synchronized as
`1018432` in the idle `/data1/yanruj/EvolveSWDB_dx100_continuation_20260926_a3`
checkout. Its 11:34:33 ET read-only preflight passed the exact request, runtime,
failed-a1 history, unused-a2/a3 paths, diagnostic receipt and actual provider
termination checks. The native paired job remains live, so its terminal barrier
is still required before dispatch. The isolated exported code passed 45 combined
continuation and graph-preparation tests; none is new accelerator execution.

## Historical checkpoint — 2026-09-26 10:04 ET

The a2 10:00 ET window ended unused after its 09:40 ET launch cutoff. No reparse,
dispatch, or new correctness result occurred. The read-only 10:04–10:05 ET audit
confirmed a2 output/record paths absent and the retained a1 record, trace, parser,
simulator, and audit hashes unchanged. The actual a1 failure stays failed with
zero admitted timings. Local correction and paired-calibration work now reaches
`6346189`; the updated exact four-commit code export is awaiting approval after
the earlier automatic rejection. This does not authorize retrying the expired
a2 plan. Accelerator correctness coverage remains incomplete.

## Prior checkpoint — 2026-09-26 09:34 ET

The one-attempt actual v2 proof ran at `0236631` on mbit10 lane 0, generation
315, and failed at 09:03 ET. The same guest emitted the protected PASS sequence
and successful exit syscall, but the parser rejected four unconditional CPU
progress messages. The retained result remains unverified with no admitted timing
or gain. Its evaluation SHA-256 is
`9a941cdff315e283b13563bf81ef2f45ba0712bbcf6d31b92f6232488efa3b42`;
local commit `1cc9557` imports that failure and its audit receipt.

Commit `b3a2cbe` accepts only the pinned CPU progress grammar, retaining those
observations separately from the syscall completion witness. Independent review
closed a progress/exit tick-ordering defect. The final parser/adapter/probe test
set passed **121 tests in 57.30 seconds**. Local catalog validation reports 186
valid records. These checks do not establish real execution of the correction.

The [one corrective a2 plan](../../../docs/bfs-dx100-witness-correction-20260926.md)
retains the 10:00 ET absolute end and requires at least 1,200 seconds at dispatch.
Automatic approval review rejected the new two-commit GitHub synchronization;
an exact payload/destination question remains pending. There is no a2 dispatch
or retrospective promotion of a1. Required accelerated full/tail/competing-parent
coverage is still outstanding, so this ticket remains claimed.

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Attach an explicit BFS correctness outcome to the exact binary and execution whose simulated ROI is retained. Preserve the sealed timing boundary while checking the produced BFS result, including a real accelerated path. Make verifier failure visible even when the guest or simulator exits successfully.

## Scope and spec references

Implements D08, D10, D14 and AC09–AC11. The inspected DX100 BFS path reaches a simulation exit before its enclosing verifier. Continuing that same simulation after sealing the ROI is one approach to evaluate, not a mandated design. The obligation is correctness evidence for the timed code/workload with verification excluded from the declared performance ROI.

## Acceptance criteria

- [ ] Every attached correctness result identifies the exact timed binary/source, graph representation and logical workload, actual BFS source vertex, target/configuration, execution, and verifier/check version. Evidence from a different functional build cannot silently certify that binary.
- [ ] The check enforces BFS structure: the source is its own parent, reachable vertices have valid predecessor edges at the preceding BFS depth, and unreachable vertices are represented correctly. Different valid parent trees pass.
- [ ] A real bounded accelerated BFS execution produces explicit structural-correctness evidence and evidence that acceleration actually executed. Presence of accelerator calls in source, successful compilation, or a scalar-fallback run alone is insufficient.
- [ ] The declared correctness cases exercise applicable full/tail tiles and competing parent updates, with graph/source identities and observed path coverage retained. A finite checked workload set is not presented as a proof for all graphs.
- [ ] The selected correctness mechanism preserves the intended ROI and seals the timing evidence before any excluded verification. Its runtime behavior is validated; source inspection alone does not establish that post-ROI continuation or another mechanism works.
- [ ] A printed verifier failure yields a failed correctness outcome even with a successful process exit. Missing, interrupted, or ambiguous verifier output remains incomplete/unverified and cannot promote a candidate to an implementation or support a successful gain claim.
- [ ] Public result retrieval exposes the explicit verdict, path coverage, raw verifier evidence, and sealed ROI association in a fresh process. Previously retained unverified execution evidence is not discarded when checking fails.
- [ ] Verification and retry attempts have predeclared limits and obey host/lane/resource procedures. Requested repetitions are reconciled with actual completed checks rather than inferred from a guest trial argument.

## Verification

Drive the public evaluation/result workflow with valid and invalid BFS-output cases, including a verifier failure paired with process exit zero and an absent verdict. Those cases establish outcome handling. Real acceptance additionally requires the pinned model executing the timed BFS binary with demonstrable acceleration and a structural check outside its sealed ROI. A mock simulator or separate functional API execution cannot satisfy that requirement. Full profiling and performance comparison are not needed to establish the correctness mechanism.

## Dependencies and boundaries

Ticket 12 supplies identified binaries, simulator execution, raw ROI artifacts, and durable unverified outcomes. This ticket does not depend on ticket 14's profile collector or ticket 11's full comparison protocols: it can retain direct path/check evidence for a bounded, explicitly identified execution. It does not move ROI boundaries, select a new strategy, run the full workload matrix, or prove profitability. Candidate-specific checks later reuse this mechanism for the workloads actually timed.

## Dependent preparation — 2026-09-25

Claimed for exact-binary continuation implementation while ticket 12 builds the pinned model. Acceptance remains blocked by the real bounded build and execution. The planned driver seals the guest-emitted ROI statistics before resuming the same simulator and guest binary for the enclosing structural verifier. Contract fixtures remain explicitly classified and cannot satisfy the real accelerated-path criteria.

## Implementation evidence — 2026-09-25

The continuation driver in `scripts/dx100_verify.py` seals the actual guest-dumped interval and resumes the same machine once. `swdb/dx100.py` binds explicit verifier results and observed MAA path evidence to exact execution identities while retaining incomplete/failing outcomes. `python3 -m pytest tests/test_dx100.py -q` passed 13 tests in 37.04 seconds, including direct driver execution with fake gem5 events for PASS, FAIL with exit zero, absent/ambiguous verdict, unexpected terminal cause, and post-seal timeout. These are contract fixtures; actual model continuation and applicable accelerated coverage remain unaccepted.

## Candidate and coverage preparation — 2026-09-25

The public candidate compiler now binds changed source artifacts to bounded
compilation receipts without rebuilding the model. Its trusted complete-call
wrapper preserves the actual returned parent array across the sealed exit and
validates its length and value range before the protected structural verifier.
An independent diagnostic-only wrapper preserves the unchanged author's
traversal ROI and forwards its internal reset/dump/exit events. The original
author primary binary is unchanged. Author function identity and accelerator
tile/core mismatches reject before simulation.

Actual MAA completion and tile sizes are parsed only inside the sealed ROI.
Competing-update evidence first binds the instruction's virtual parent base,
then detects distinct values for the same observed physical word; physical
trace addresses are never directly compared with a guest virtual pointer.
The combined adapter/driver/profile suite passed 42 tests in 166.32 seconds.
These source and contract tests do not satisfy the still-pending real
accelerated full/tail/competing-update acceptance.


## Actual continuation evidence — 2026-09-25

The real a6 model run sealed its ROI at tick 2,187,360,749, then the unchanged
same guest printed exactly one `Verification: PASS`, verification time, and
average time. It did not produce the required last-active-thread exit event;
continuation reached the declared 10^12-tick ceiling. The public record remains
unverified despite its PASS line and process exit zero, as required by the
contract. See [the audited finite receipt](../observations/dx100-smoke-a6.json).
The tiny graph's observed frontiers (1, 9, 37, 17) select the author's scalar
fallback and cannot establish accelerator execution/full-tile/tail/conflict
coverage. No acceptance criterion is resolved by this bring-up observation.

## Prospective v2 contract — 2026-09-26

Local checkpoint `8175ca1` retains exact verifier driver, parser, and host-memory
observer bytes per execution and binds their hashes into instrumentation. The
explicit v2 contract checks protected completion output and a separate
simulator-origin successful `exit_group(0)` call/return after the durable ROI
seal. It records actual normal termination separately; no previous v1 result is
promoted. The combined 89 runtime, public-adapter, and fixed-request tests passed.
These fixtures do not establish actual model acceptance.

The one-attempt unchanged-author proof is prepared in
`../requests/dx100-witness-a1.yaml` and repository-root
`docs/bfs-dx100-witness-probe-plan-20260926.md`. Automatic approval review rejected
the code push pending specific payload/destination approval, so the actual v2
attempt has not started. Accelerated full/tail/competing-update cases still
require their own actual observations. Ticket 13 remains claimed.

## Interim correctness repair — 2026-09-26

Independent Spec review reproduced a false PASS when a generated candidate
mutated the graph subsequently used by the protected verifier. The new
`dx100.complete_call.v2` wrapper checks the exact returned parent buffer against
independently loaded original adjacency. Its 2 GiB bounded allocation occurs
before checkpoint/ROI and is declared as a new treatment. Legacy wrappers stay
retrievable but cannot execute or qualify through comparisons/aggregates.

Compiled local regression cases reject the false PASS and accept valid alternative
parent trees; they are not actual DX100 acceptance. Unchanged author traversal
remains a distinct treatment. See [oracle contract](../../../docs/bfs-original-graph-oracle-20260926.md)
and [interim review](../../../docs/bfs-interim-review-20260926.md). The actual v2
proof, accelerated coverage, code synchronization, and evidence synchronization
remain pending. This ticket remains claimed.

## Corrective proof launch cutoff — 2026-09-26 09:40 ET

The a2 launch cutoff passed without the exact two-commit export approval.
The corrective attempt remains unused; no launch, reparse, or result is claimed.
Fewer than 1,200 seconds remain in its fixed 10:00 ET window, so dispatch is
prohibited under that plan. The rejected export is not retried and the deadline
is not extended. Local paired calibration implementation and fixed-commit
regression verification continue independently.


## Retained-trace diagnosis and next window — 2026-09-26 11:06 ET

After the exact code transfer was explicitly approved and completed, a bounded
read-only diagnosis used the approved `6346189` parser on the unchanged a1
trace. It completed in 0.062 seconds within a 30-second cap. The record, seal,
retained parser/driver/observer and 2,761-byte trace hashes matched their prior
pins. The corrected grammar accepted exactly 30 lines with four progress rows;
the exit call/return remained at lines 19/20, tick 2,222,725,680, within the
original interval [2,187,360,749, 3,187,360,749]. There were no pending or initial
partial calls. An earlier filename typo in the read-only precheck was corrected
before parsing; no execution was retried.

This is `diagnostic_reparse` only. A1 remains failed/unverified with zero admitted
timings and unchanged raw/record bytes. A2 remains expired and unexecuted.
The [new prospective a3 plan](../../../docs/bfs-dx100-witness-continuation-20260926.md)
waits for paired native calibration and provider generation to terminate,
retains one actual attempt and the same 1,200-second/resource caps, and has a
15:20 ET latest launch / 15:40 ET absolute end. No a3 simulation has run.

## Reviewed launch and coverage preparation — 2026-09-26 12:38 ET

The observer, fixed coverage case, completed-evidence readers, and bounded
simulator coordinator are prepared on the separate code branch
`codex/bfs-simulator-admission-20260926`. The final launcher tip is
`c5f70d77396af0e7562310375333f34791aac3a1`, independently verified on the remote
Git branch. The actual a3 client remains unchanged at `1018432`; the new launcher
runs that client and its read-only observer as separately identified children
inside the same original 1,170-second work plus 30-second cleanup allowance.
Separate child exits, exact pane ancestry and the independent terminal union
audit are mandatory. No existing deadline or failed result is replaced.

The [preparation test receipt](../observations/simulator-admission-tests-20260926.json)
retains 183 passing focused tests and two Linux-only skips in both root and
isolated checkouts. The [launcher review receipt](../observations/witness-launcher-tests-20260926.json)
retains 24 independently passing launcher tests and 43 passing launcher/observer
tests on the exact export. Review fixed deadline overrun, stale process-group
signaling and a real child-disappearance/reaping race. Earlier failed test
results remain available. These are local fixtures, not actual DX100 acceptance.

One a3 dispatch is authorized when the native/provider terminal barriers, free
socket lane, resource checks, exact runtime and original full launch window
all pass. The separate fixed 8,212-vertex coverage case can follow only a passed
actual a3 and its terminal audit; its 15:45 ET latest launch and 16:45 ET end
remain fixed. No coverage run, Linux cleanup test or simulator batch has been
dispatched at this checkpoint. Native pilot spread failure blocks T15's freeze
but does not itself block this independent correctness work or T16.

## Actual witness and failed coverage — 2026-09-26 14:25 ET

The actual tiny a3 continuation passed at 13:37 ET, with structural correctness
and an exit witness for the original timed binary. Its exact metadata is synced
in `aa6da989` (local `44180a0`); see the
[witness receipt](../observations/dx100-witness-a3-terminal-20260926.json).
This 64-vertex result does not establish full/tail/competing accelerator coverage.

The separate 8,212-vertex coverage a1 was actually dispatched and failed in its
resource monitor. No timing or correctness sample is accepted, despite a retained
guest seal. The [terminal/import receipt](../observations/dx100-coverage-terminal-20260926.json)
preserves the interrupted stage, stale public outcome, failed driver and verified
cleanup. A prospective observer correction is locally tested and independently
reviewed; Linux verification and a distinct corrective attempt remain outstanding.
This ticket stays claimed. No existing failure or acceptance requirement is waived.


## Reviewed corrective coverage client — 2026-09-26 15:44 ET

A distinct fixed a2 client is committed at `5e7eb62` and exported at
`67313d9b2a45d9f0fb23d935b56e755a3a19fa7f` on the private
`codex/bfs-dx100-coverage-20260926-a2` branch. Its 11-file tree preserves the
reviewed historical batch/series dependencies and adds the durable public
interruption correction. All six runtime dependency hashes match; 116 local
checks passed and three Linux-only checks remain pending. Independent review
reproduced and repaired a shutdown-error path that skipped direct-child reaping.
The [preparation/export receipt](../observations/dx100-coverage-a2-preparation-20260926.json)
retains tests, failures, exact inventory and verified remote ref.

This one new attempt retains the fixed 8,212-vertex graph, original author MAA
code, 3,600-second total/30-second shared cleanup, 48 GiB sampled RSS and 4 GiB
artifact limits. Its window is 16:00–22:00 ET with latest start 21:00 ET. Actual
Linux fixture proofs at that exact export and whole native-client terminal
cleanup remain mandatory. A native statistical failure can release this cleanup
barrier but cannot qualify a native protocol. No a2 dispatch, accepted coverage
sample or gain is claimed; all earlier failures remain unchanged.
