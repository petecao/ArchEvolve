# 18 — DX100 BFS: patch-route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
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
- [ ] Materialize changed CPU-runnable BFS code with recorded supporting edits, candidate/binary identities, diff, and any bounded repairs. Preserve evaluator-owned correctness and timing boundaries.
- [ ] Execute the candidate and its explicitly selected unaccelerated native baseline on both graph families using ticket 15's frozen graph/source, thread, target, ROI, and repetition rules.
- [ ] Retain structural BFS correctness evidence for the timed code and every workload supporting a timing claim. Verification remains outside the declared ROI, while required work inside that ROI remains charged.
- [ ] Retrieve actual native BFS ROI timing, selected-region timing, and refreshed dynamic memory evidence with the diagnostic collector's identity, attribution scope, and differences from the timed artifact.
- [ ] Confirm that a fresh public query retrieves the full proposal/candidate/evaluation chain and preserves native measurement identity; fixture timings and functional accelerator host runtimes do not satisfy this case.
- [ ] Preserve failures, incomplete evidence, and regressions with reasons and raw references. Run within explicit budgets and lab-host rules; a correct regression may complete the case, but missing correctness or required profiling cannot.

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
[review receipt](../../../docs/bfs-interim-review-20260926.md) for the retained
tool-result transcript and intermediate fixture-setup failure. No actual Ticket
18 candidate execution occurred, no frozen-protocol result was added, and this
ticket remains claimed behind Ticket 15 and current synchronization holds.
