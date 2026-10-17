# 18 — DX100 BFS: patch-route acceptance

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-27 12:25 ET
**Type:** slice
**Status:** resolved
**Blocked by:** 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Demonstrate a supplied CPU rewrite of DX100 scalar top-down BFS through the full public workflow on both Kronecker and uniform-random graphs. A representative test client submits a real patch; the evaluator independently builds, checks, times, profiles, and returns its results on the declared native target.

This is the DX100 starting implementation × supplied-code route, covering two graph-family cells and providing native execution evidence. Accelerator coverage for this source is assigned to ticket 17.

## Scope and specification coverage

Covers AC06–AC10, AC12–AC14, AC16, AC18, AC20 and contributes evidence toward AC17. Applies D06–D08 and D10–D14.

## Acceptance criteria

- [x] Retrieve the baseline profile package for the exact DX100 scalar source and declared native workload. Use the package's source, region, build, correctness, and ROI context in the proposal.
- [x] Submit an actual patch in the versioned proposal envelope, naming its optimization intent, exact source identity, required capabilities, and preservation constraints. Record test-client provenance.
- [x] Materialize changed CPU-runnable BFS code with recorded supporting edits, candidate/binary identities, diff, and any bounded repairs. Preserve evaluator-owned correctness and timing boundaries.
- [x] Execute the candidate and its explicitly selected unaccelerated native baseline on both graph families using ticket 15's frozen graph/source, thread, target, ROI, and repetition rules.
- [x] Retain structural BFS correctness evidence for the timed code and every workload supporting a timing claim. Verification remains outside the declared ROI, while required work inside that ROI remains charged.
- [x] Retrieve actual native BFS ROI timing, selected-region timing, and refreshed dynamic memory evidence with the diagnostic collector's identity, attribution scope, and differences from the timed artifact.
- [x] Confirm that a fresh public query retrieves the full proposal/candidate/evaluation chain and preserves native measurement identity; fixture timings and functional accelerator host runtimes do not satisfy this case.
- [x] Preserve failures, incomplete evidence, and regressions with reasons and raw references. Run within explicit budgets and lab-host rules; a correct regression may complete the case, but missing correctness or required profiling cannot.

## Verification and demonstration

Use the real patch-to-native-evaluation workflow for both graph families, including actual source changes and compilation. Public contract tests cover stale patches and protected-input rejection; they do not replace the real acceptance evidence.

## Dependencies and boundaries

Ticket 15 transitively supplies source resolution, patch handling, native evaluation, complete profile packages, and the frozen protocol. No instruction or annotation worker is required for a supplied patch, so tickets 04 and 05 are not additional blockers.

A performance gain is optional for this case. Ticket 17 owns the DX100-source accelerator minimum; this case need not run the patch under the accelerator.

## Implementation progress

2026-09-25: Root owns dependent preparation of the representative proposal and public campaign driver. No candidate performance assessment begins before Ticket 15 freezes compatible protocols. Actual acceptance remains pending; preparation does not satisfy the listed blockers.

## Actual proposal and compile preparation — 2026-09-25

The fixed literal patch was submitted as
`bfs-campaign-preparation-20260925-a1.dx100-patch` using both real native baseline
family packages. Its candidate `candidate-1` has artifact SHA
`10d4976f94783f7435b8d4faa6497f2693be4ce464b1b51eb6cd79cdc1f26028`.
Primary and diagnostic DX100 compilation succeeded and discovered 31 source
regions; exact patch output, protected inputs, all region bytes, and binary hashes
were independently audited. See [the retained receipt](../../../docs/evidence/bfs-campaign-preparation-20260925-a1.yaml).
These are materialization and compilation observations only. Native candidate
execution, correctness, timing, refreshed profiling, and the frozen comparison
remain pending; this ticket is not resolved.

## Exact candidate reuse preparation — 2026-09-26 10:27 ET

Commit `35b0cff` adds `--existing-candidate` to the native campaign client so the
already-created initial candidate can be evaluated without duplicate submission.
The client requires the exact original proposal JSON, reopens its public record
chain, verifies source/package/artifact/protection bindings, and replays the
authorized patch in a bounded temporary source snapshot. The replay rejects a
consistently rehashed candidate containing edits absent from the retained patch.
Reuse does not invoke a provider or reset repair history. Both default fresh
submission and existing-candidate fixture evaluation remain covered.

Independent scoped review reports no remaining actionable finding; 40 focused
tests passed, with 23 deselected, in 27.74 seconds. See the
[review receipt](../../../docs/archive/bfs-interim-review-20260926.md) for the retained
tool-result transcript and intermediate fixture-setup failure. No actual Ticket
18 candidate execution occurred, no frozen-protocol result was added, and this
ticket remains claimed behind Ticket 15 and current synchronization holds.

2026-09-26 10:30–10:32 ET read-only readiness check: the actual retained proposal
still has `candidate_created`, stage `rewriting`, exactly one completed attempt,
and its original `.candidate-1`. Neither proposal nor attempt contains provider
state, and no repair budget exists for this initial supplied patch. The candidate
remains unverified with artifact SHA `10d4976f…`; source and supporting package
IDs match the retained preparation. This checks metadata shape only, not source
replay, fresh package admission, or candidate execution.
The proposal and candidate YAML file hashes also match the current local master
copies: `ab3bd889417ab02e3a882d8a6cda86823fa42768e376456bbdaecc38ccbd9d43`
and `f426dd9eca7563b0cf66c161ca93f6d5fc4342160cc8bfca5a6a1da807ff9252`,
respectively. Matching record bytes do not verify their external artifact bytes.

## Explicit new-configuration reassessment — 2026-09-26

The reviewed `--reassessment` route in commit `e2e9c02` preserves the original
candidate, proposal payload, source snapshot, protected regions, and exact patch
replay while separately binding the two original and two fresh baseline packages
and a new frozen one-thread protocol. It cannot submit or invoke a provider or
repair. Unknown original runtime inputs remain unknown. The author group passed
88 tests and the independent group passed 45; see the
[reassessment receipt](../observations/native-reassessment-verification-20260926.json).
These are contract tests, not candidate assessment. The materialization checkbox
now reflects the already-retained actual primary/diagnostic compilation and
independent source audit; all frozen execution and profiling obligations remain
open. No new strategy or candidate was selected.

## Reviewed prospective supervision — 2026-09-26

Native candidate execution now has reviewed owned-process cleanup, original-clock resource
accounting and failure preservation; see the [verification receipt](../observations/native-supervision-verification-20260926.json).
The actual Linux fixtures, runtime admission and empirical execution remain
pending. This preparation does not satisfy or change any open acceptance item.

## Native launch preparation — 2026-09-27 ET

[Data-only preparation](../operator-recipes/native-acceptance/README.md) now binds
the actual original request, candidate, source/package identities, retained patch
and provider-budget history. All four historical package contexts explicitly use
four threads; the prospective one-thread reassessment preserves that history.
Protocol, fresh-package and host-admission fields remain unset pending T15 and
source-specific qualification/publication. The existing public campaign CLI is
sufficient; no provider, build, measurement, new allowance or acceptance is claimed.

## Native acceptance under the frozen one-thread protocol — 2026-09-27 12:25 ET

Stream B, branch `codex/bfs-native-routes-20260927-b1`. Evidence:
[native routes observation](../observations/native-routes-t18-t19-20260927.json).
Raw output stays on mbit10 under `/data/yanruj/EvolveSWDB_runs/`.

**Protocol (R7).** The one-thread study `bfs-native-one-thread-pilot-20260926-a1`
qualified through the public `bfs_freeze_pilot.py` prepare/publish route, with
the pinned 319645e reader in its original checkout. No gates were unmet. The
explicit R7 native-only size scope replaced the simulator size gate; it is
bound to the resume-plan hash, and controlled-simulator freezes keep that gate.
Frozen protocol: `bfs-native-one-thread-dx100-scalar-20260927.0d2d6da657751ff3`
(1 thread, 10 paired repetitions, `native_paired.v1`, 0.10 spread ceiling,
1.05 minimum speedup, lane node1). The fresh baseline packages are the study's
one-thread DX100 uniform `…b8f33855cc6c657e` and Kronecker `…122d39652ae0c326`.
The readback a1/a2 failures stay retained. The a2 cause (a stray
`.pytest_cache`) is fixed prospectively: project pytest runs no longer create
that cache.

**Run b1 (retained failure).** `bfs-native-acceptance-20260927-dx100-patch-b1`
started on node1 at 10:32 ET (generation 453). Reassessment, exact candidate
reacquisition and patch replay passed. Paired trials took about 70 s each,
against the pilot's 33 s, so the uniform pair could not fit its fixed 2,400 s
bound. The cost was harness persistence outside the ROI (every persist
reparsed and reindexed a 21 MB record view); the ~0.047 s BFS ROI was
unaffected. At root's direction one SIGTERM stopped the driver at 10:51 ET.
Its state is failed/interrupted, with six trials retained. Independent
closure: 44/44 identities absent and the lease released. The run ID is never
reused. The prospective fix (commits af100f1, 820f32b) adds a per-process
Store parse cache and a reference-closure record view. A trial-equivalent
persist fell from 8.7 s to 1.0 s. The unused T19 b1 admission is retained.

**Run b2 (evaluated).** `bfs-native-acceptance-20260927-dx100-patch-b2` ran on
node1 from 11:10:14 to 11:37:55 ET (1,661 s of the 14,400 s cap; generation
455; load1 at start 2.42). The run:

- reused candidate `bfs-campaign-preparation-20260925-a1.dx100-patch.candidate-1`
  (artifact `10d4976f…`) through `--existing-candidate --reassessment`, with no
  provider and no repair;
- compiled the candidate binary `e65d00dc…` and the unaccelerated
  `dx100-bfs-scalar` baseline binary `42546a5a…`;
- collected a 60-trial paired grid per family.

| Family | Baseline median ROI s | Candidate median ROI s | Speedup | 95% CI | Max spread (base / cand) | Decision |
|---|---|---|---|---|---|---|
| Uniform-random | 0.046034 | 0.045964 | 1.0015 | [0.9977, 1.0108] | 0.143 / 0.172 | inconclusive (spread veto) |
| Kronecker | 0.023259 | 0.023226 | 1.0004 | [0.9958, 1.0197] | 0.138 / 0.021 | inconclusive (spread veto) |

Structural correctness passed for all 30 timed trials per role per family,
verified outside the ROI; initialization stays charged inside
`bfs.complete_call.v1`. Each family has a complete candidate diagnostic
package (`…5df6a96f028565a1`, `…d612335972200df6`). Each package holds
per-region thread-CPU timing for 31 discovered regions from a separate
instrumented binary. It also holds Callgrind 3.22 ROI memory rows (18 each:
reads/writes, D1/LL misses, with the model limits stated) and region
correspondence to the fresh baseline profile. 26 regions resolve identically.
The five changed regions (TDStep, its two loops, DOBFS and its while loop) are
reported as unresolved, with the collector's stated limit: "no timings or
semantics are inherited". The comparison is software on a fixed target, so
there is no accelerator claim. The region-profile records report `partial` (bounded source attribution, with explicit coverage and metric limits), the same state as every retained baseline profile; the packages themselves are `complete`.

A fresh process with a new SQLite database retrieved the complete chain
through `swdb get … --chain` for the proposal and both comparisons: proposal,
candidate, evaluations, pair, package, region profile, protocol, machine and
workload. Independent closure: 94/94 identities absent, lease released,
storage within budget. Records were imported through Git at `cc598bc`.

This is no gain and no regression. The candidate differs from the baseline
by at most 0.15%, and the frozen spread veto fires on single-source outliers
(about 0.13–0.17 against 0.10). By the plan, no retry or tuning follows.

## Answer

2026-09-27 12:25 ET. T18 is complete. The supplied DX100 scalar patch
(64-vertex dynamic chunks, redundant CAS store removed, conditional printing)
went through the public workflow on both graph families. It was built,
structurally checked on every timed trial, and timed natively under the
frozen one-thread paired protocol against the unaccelerated `dx100-bfs-scalar`
baseline. It was reprofiled (region timing plus Callgrind memory) and
retrieved in a fresh process. Both families are **inconclusive**: speedups are
1.0015 and 1.0004, the intervals include 1, and the spread veto triggered. No
gain is claimed. The interrupted b1 run and its harness-overhead cause are
retained. The protocol was frozen under decision R7, independently of T15's
simulator packages. Map pointer: left to root (this stream does not edit
`map.md`).

