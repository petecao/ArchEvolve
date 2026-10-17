# 19 — Upstream BFS: instruction-route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-27 12:30 ET
**Type:** slice
**Status:** resolved
**Blocked by:** 04, 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Demonstrate a representative structured-instruction proposal for upstream GAPBS direction-optimizing BFS through the native public workflow on both Kronecker and uniform-random graphs. The worker resolves the specified source regions, applies the supplied optimization intent, and returns independently checked and reprofiled code.

This is the upstream starting implementation × instruction route, covering two graph-family cells and the structured-instruction payload example.

## Scope and specification coverage

Covers AC01, AC06–AC10, AC12–AC14, AC16, AC18, AC20 and contributes evidence toward AC17. Applies D01, D06–D08, and D10–D14.

## Acceptance criteria

- [x] Retrieve an actionable profile package for upstream direction-optimizing BFS and retain its actual source/build/evaluator context. Do not substitute DX100 top-down source merely because both implementations share one kernel.
- [x] Submit structured instructions with explicit strategy parameters, target identities, profile-package reference, semantic constraints, and ROI requirements. Label the submission as a representative test client.
- [x] Apply the instructions to produce real changed CPU-runnable code. Record how rules and preconditions were interpreted, the resulting source/binary identities, diff, supporting edits, and bounded repairs; the structured description is not treated as a proof of legality.
- [x] Evaluate the candidate and its explicit upstream unaccelerated comparison baseline on both graph families under ticket 15's frozen native protocol, replaying the recorded traversal sources.
- [x] Retain BFS structural correctness evidence covering the timed code and all timing-claim workloads. Keep protected checks and ROI boundaries intact, including initialization inside the selected BFS-call ROI.
- [x] Retrieve actual BFS ROI and selected-region timing plus refreshed dynamic memory observations and changed-region associations. Expose unsupported metrics, diagnostic differences, and attribution limits accurately.
- [x] A fresh public query reconstructs the structured proposal, candidate, native hardware configuration, protocol, comparison, correctness, timing/profiling, and raw evidence.
- [x] Retain all failures and regressions within declared budgets. If the selected strategy cannot produce a valid complete case, return its evidence without independently selecting another strategy or claiming that fixtures establish native performance.

## Verification and demonstration

Run the complete real structured-instruction → rewrite → native evaluation → reprofiling → retrieval workflow on both graph families. Supplement it with public-behavior tests for wrong-source targeting and unsatisfied preconditions.

## Dependencies and boundaries

Ticket 04 provides structured-instruction rewriting and bounded repairs. Ticket 15 provides the native evaluator, profile packaging, and frozen experiment protocol through its dependency chain. The case does not require tickets 17 or 18 to complete; scheduling must still respect the agreed DX100-first starting order and lab resource limits.

Ticket 20 owns the upstream-source accelerator minimum. A native gain in this case is useful but is not an individual completion condition.

## Implementation progress

2026-09-25: Root owns dependent preparation of the representative proposal and public campaign driver. No candidate performance assessment begins before Ticket 15 freezes compatible protocols. Actual acceptance remains pending; preparation does not satisfy the listed blockers.


## Initial provider result — 2026-09-26 11:13 ET

The explicitly approved `upstream-instructions` source/profile payload was sent through
Claude Code in the bounded three-request socket-0 batch. This request created an unverified candidate.
The [initial batch summary](../observations/provider-initial-summary-20260926.json)
retains the actual outcome; no repair, retry, compile, performance evaluation or
final acceptance followed from this submission. The original annotations and
proposal context remain retained.

The six-file result packet was committed on mbit10 as `5f1b802`, but automatic
approval review rejected its new GitHub packet/branch. Exact approval is pending;
canonical proposal/candidate records have not been imported into this checkout.
See [the concrete inventory](../observations/provider-export-inventory-20260926.json).

## Native launch preparation — 2026-09-27 ET

[Data-only preparation](../operator-recipes/native-acceptance/README.md) now binds
the actual original request, candidate, source/package identities, retained patch
and provider-budget history. All four historical package contexts explicitly use
four threads; the prospective one-thread reassessment preserves that history.
Protocol, fresh-package and host-admission fields remain unset pending T15 and
source-specific qualification/publication. The existing public campaign CLI is
sufficient; no provider, build, measurement, new allowance or acceptance is claimed.

## Native acceptance under the frozen one-thread protocol — 2026-09-27 12:30 ET

Stream B, branch `codex/bfs-native-routes-20260927-b1`. Evidence:
[native routes observation](../observations/native-routes-t18-t19-20260927.json).
Raw output stays on mbit10.

**Profile and proposal.** The retained actionable upstream packages were used,
not DX100 source: `bfs-native-pilot-20260925-upstream18-a2.{uniform-random,kronecker}`
(`gapbs-bfs-do`, upstream commit 2972aeb). The structured proposal
`bfs-campaign-preparation-20260925-a1.upstream-instructions` (test client,
payload `8a7f129a…`) targets region `function:bfs.cc:3477:…` with:

- strategy `remove-dead-initial-bitmap-clear`;
- two explicit preconditions, a preserve list and an unresolved-on-failure rule;
- editable file `src/bfs.cc`, preserving correctness and the ROI.

The retained provider interpretation checks both preconditions against the
source. The diff (`827466f8…`) removes exactly one `curr.reset();`. No repair
was used (0 of 1; 41.2 s of the 600 s provider budget consumed on
2026-09-26). The interpretation is not treated as proof: every timed trial
was checked independently.

**Protocol (R7).** Frozen protocol
`bfs-native-one-thread-upstream-do-20260927.9d4b53fd41e79297`, published
through the public prepare/publish route from the completed one-thread study.
Settings: 1 thread, 10 paired repetitions, 0.10 spread ceiling, 1.05 minimum
speedup, lane node1. Fresh baseline packages: upstream uniform
`…ffd9925db46a63a9` and Kronecker `…f613a3b01a24e380`. The 4→1 thread
reassessment preserves the original package identities and provider history.

**Run.** `bfs-native-acceptance-20260927-upstream-instructions-b2` ran on
node1 from 11:38:55 ET for 1,646 s of the 14,400 s cap (generation 456;
load1 at start 3.44). This was the candidate's first compile: binary
`0865b973…`; upstream unaccelerated baseline binary `741493a2…`. Recorded
sources 0, 1234 and 7777 were replayed in a 60-trial paired grid per family.
The T19 b1 run was admitted but never launched, because it was superseded by
the persist fix documented in Ticket 18; its admission is retained.

| Family | Baseline median ROI s | Candidate median ROI s | Speedup | 95% CI | Max spread (base / cand) | Decision |
|---|---|---|---|---|---|---|
| Uniform-random | 0.0073276 | 0.0072879 | 1.0019 | [0.9994, 1.0048] | 0.156 / 0.015 | inconclusive (spread veto) |
| Kronecker | 0.0059989 | 0.0059926 | 1.0013 | [0.9990, 1.0298] | 0.187 / 0.182 | inconclusive (spread veto) |

Structural correctness passed for 30/30 timed trials per role and family,
verified outside the ROI; initialization stays inside `bfs.complete_call.v1`.
Each family has a complete candidate diagnostic package (`…b8238c548d000951`,
`…151e5e95d47bac6c`). Each package holds per-region thread-CPU timing from a
separate instrumented binary, and 18 Callgrind 3.22 ROI memory rows with the
model limits stated (no hardware counters). It also holds changed-region
associations: 23 regions resolve identically to the fresh baseline profile,
and the changed `DOBFS` function (`function:bfs.cc:3477:…`) is reported as
unresolved, with "no timings or semantics are inherited". The region-profile records report `partial` (bounded source attribution, with explicit coverage and metric limits), the same state as every retained baseline profile; the packages themselves are `complete`.

A fresh process with a new SQLite database reconstructed the full chain
through `swdb get … --chain` for the proposal and both comparisons: the
structured proposal, candidate, evaluations, pair, package, region profile,
protocol, mbit10 machine/lane configuration and workload, with raw references.
Independent closure: 110 of 111 identities absent, the remaining one being
the exact zero-RSS tmux launcher pane. Lease released; storage within budget.
Records were imported through Git at `cc598bc`.

## Answer

2026-09-27 12:30 ET. T19 is complete. The representative structured-instruction
proposal for upstream DO-BFS produced real changed code, a single dead
`curr.reset()` removal with interpreted preconditions. The candidate compiled
and passed structural checks on every timed trial. It was timed natively
under the frozen one-thread paired protocol against the unaccelerated
`gapbs-bfs-do` baseline on Kronecker and uniform-random, then reprofiled and
retrieved in a fresh process. Both families are **inconclusive**: speedups are
1.0019 and 1.0013, the intervals include 1, and the spread veto triggered.
There is no gain and no regression, and no other strategy was selected. The
protocol was frozen under decision R7, independently of T15's simulator
packages. Map pointer: left to root (this stream does not edit `map.md`).

