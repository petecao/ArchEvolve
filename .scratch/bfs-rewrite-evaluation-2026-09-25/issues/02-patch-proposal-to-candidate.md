# 02 — Submit a patch and retrieve its candidate or rejection

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Provide the first public proposal-to-candidate path: accept a versioned patch proposal tied to an exact BFS source and profile-package reference, apply permissible edits to a separate candidate artifact, and make either the candidate or a rejection retrievable in a later process. Persist the proposal and outcome even when no candidate can be produced. Candidate creation is not correctness certification or performance evaluation.

## Scope and spec references

This slice contributes AC01, AC06–AC09, and AC20 through D02–D03, D06–D08, and D14–D15. It establishes patch submission, protected evaluation inputs, source identity, and durable outcomes. Early route tests may submit explicitly labeled fixture profile packages that satisfy the handoff contract; complete live package generation belongs to ticket 09 and is not a prerequisite.

## Acceptance criteria

- [ ] A public patch submission records its format version, stable proposal identity, producer, source profile-package reference, exact source target, selected intent, constraints, and payload identity.
- [ ] A valid patch produces an actual changed candidate and retrievable diff against the identified source, retaining supporting helper, data-structure, header, or build edits within the declared scope.
- [ ] The starting artifact remains identifiable and unchanged; the candidate has its own content identity and is not presented as a verified implementation.
- [ ] Stale or conflicting targets, an inapplicable patch, and unresolved required capabilities produce explicit rejected or unresolved outcomes without guessing a substitute source or capability.
- [ ] Attempts to change protected correctness checks or evaluator-owned ROI instrumentation are refused and retained with the reason; candidate edits do not redefine the evaluation contract.
- [ ] A rejection is queryable without a candidate or successful profile. A partially materialized candidate, if retained, is clearly incomplete and linked to its failed stage.
- [ ] A fresh process can retrieve the proposal, payload, candidate when present, stage outcome, diff, and available raw-artifact references after the submitting process has ended.
- [ ] Authoritative metadata and regenerated query results agree; persistence or indexing failure is reported rather than replaced by an apparent successful submission.

## Verification

Use the public workflow boundary with isolated source snapshots and records. Submit a valid source-changing patch, stale-target and patch-conflict cases, and a protected-input change; retrieve every outcome in a new process and regenerate the query index. Fixtures may provide profile-package or capability context but must be labeled. Do not mock away patch application or fabricate the candidate to satisfy the success case. No performance evidence is required by this slice.

## Dependencies and boundaries

Ticket 01 supplies source-specific resolution and explicit identity relationships. Native correctness and timing belong to ticket 03; instruction interpretation, repair, and annotated-source interpretation arrive in tickets 04–05. DX100 capability details arrive in ticket 10; unknown support must remain unresolved until an applicable contract exists. Those later tickets are not hidden prerequisites for this patch path or its failure retention.
