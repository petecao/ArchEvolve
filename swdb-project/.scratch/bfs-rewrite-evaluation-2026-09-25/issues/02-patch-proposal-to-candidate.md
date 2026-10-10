# 02 — Submit a patch and retrieve its candidate or rejection

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Provide the first public proposal-to-candidate path: accept a versioned patch proposal tied to an exact BFS source and profile-package reference, apply permissible edits to a separate candidate artifact, and make either the candidate or a rejection retrievable in a later process. Persist the proposal and outcome even when no candidate can be produced. Candidate creation is not correctness certification or performance evaluation.

## Scope and spec references

This slice contributes AC01, AC06–AC09, and AC20 through D02–D03, D06–D08, and D14–D15. It establishes patch submission, protected evaluation inputs, source identity, and durable outcomes. Early route tests may submit explicitly labeled fixture profile packages that satisfy the handoff contract; complete live package generation belongs to ticket 09 and is not a prerequisite.

## Acceptance criteria

- [x] A public patch submission records its format version, stable proposal identity, producer, source profile-package reference, exact source target, selected intent, constraints, and payload identity.
- [x] A valid patch produces an actual changed candidate and retrievable diff against the identified source, retaining supporting helper, data-structure, header, or build edits within the declared scope.
- [x] The starting artifact remains identifiable and unchanged; the candidate has its own content identity and is not presented as a verified implementation.
- [x] Stale or conflicting targets, an inapplicable patch, and unresolved required capabilities produce explicit rejected or unresolved outcomes without guessing a substitute source or capability.
- [x] Attempts to change protected correctness checks or evaluator-owned ROI instrumentation are refused and retained with the reason; candidate edits do not redefine the evaluation contract.
- [x] A rejection is queryable without a candidate or successful profile. A partially materialized candidate, if retained, is clearly incomplete and linked to its failed stage.
- [x] A fresh process can retrieve the proposal, payload, candidate when present, stage outcome, diff, and available raw-artifact references after the submitting process has ended.
- [x] Authoritative metadata and regenerated query results agree; persistence or indexing failure is reported rather than replaced by an apparent successful submission.

## Verification

Use the public workflow boundary with isolated source snapshots and records. Submit a valid source-changing patch, stale-target and patch-conflict cases, and a protected-input change; retrieve every outcome in a new process and regenerate the query index. Fixtures may provide profile-package or capability context but must be labeled. Do not mock away patch application or fabricate the candidate to satisfy the success case. No performance evidence is required by this slice.

## Dependencies and boundaries

Ticket 01 supplies source-specific resolution and explicit identity relationships. Native correctness and timing belong to ticket 03; instruction interpretation, repair, and annotated-source interpretation arrive in tickets 04–05. DX100 capability details arrive in ticket 10; unknown support must remain unresolved until an applicable contract exists. Those later tickets are not hidden prerequisites for this patch path or its failure retention.

## Implementation progress

2026-09-25: Source-identity interfaces from Ticket 01 are available. Candidate workflow preparation is proceeding in parallel with that ticket's validation; Ticket 02 will not resolve before Ticket 01. Root owns workflow persistence, source snapshots, patch application, CLI integration, and public contract tests.

## Answer

2026-09-25: Implemented public `source-snapshot`, `fixture-package`, `submit`, and `get --chain` commands. Source snapshots and real unified-patch candidates have independent content manifests; source/profile/region identity, allowed-file scope, evaluator verifier/harness/ROI controls, and required hardware capabilities are checked before candidate acceptance. Proposals and running/completed/failed stages are authoritative YAML records with regenerated SQLite retrieval. Patch creation never sets verified-implementation status. Original requests, payload identity, actual diff and partial external artifacts survive rejection or failure.

Verification: `python3 -m pytest -q tests/test_proposals.py -x` — **10 passed**. These public subprocess tests apply an actual BFS source patch, rebuild/query the index in later processes, and cover stale/conflicting source, protected verifier changes, patch conflict, unknown capabilities, scope violations, malformed producer, snapshot tampering, and duplicate YAML keys. This is contract evidence, not execution or performance evidence. Ticket 01 was resolved before this closure. Interfaces: `docs/format-v0.4.md` and `schemas/messages/rewrite-proposal.schema.json`.
