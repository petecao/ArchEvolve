# 05 — Indirect accesses and the BFS baseline on the CPU

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** The pass classifies `single_valued_indirect` and `ranged_indirect` accesses (and `pointer_chase` or `data_dependent_merge` where it can, otherwise `unknown`); the counted run records executions and footprint per access; characterization regions are the existing profile-package and site-finder region IDs, including loops the compiler outlines for OpenMP (D33); the requests-in-flight (latency) and cache-fit mechanism models exist. The BFS and BC baselines get estimates on a small Kronecker graph, covering what their paired timing covers (D16).

## Acceptance

- [x] Classifications are compared with the 13 hand-written access patterns of `gapbs-bfs-do` and the BC implementation records; every mismatch is listed with a reason.
- [x] One fixture kernel per indirect address shape, with hand-computed answers.
- [x] Loops that map to no region are listed, never dropped.
- [ ] Estimates for `gapbs-bfs-do` and the BC baseline, each with a per-region report.

Claimed: 2026-10-06 ET by Codex ticket 05 worker, branch `codex/lanl-ticket05`; base `86b2a9a`.

Implementation status: 2026-10-06 ET — indirect hand fixtures, registered per-trial
BFS/BC binding and composable memory models implemented. Compact remote command
context: `../evidence/05-registered-counting-runbook.md`. Acceptance remains pending
the actual small-Kronecker mbit10 per-region estimates and pattern-comparison receipts.


Partial acceptance evidence: 2026-10-06 ET. The immutable actual mbit10 a1 records
(`5d0fbdb`, counted source `67f1b3b`) compare all 13 BFS and 20 BC handwritten patterns.
Direct matches are **0/13 and 0/20**; every mismatch has a nonempty explanation.
Individual lowered SSA sites do not prove the full handwritten multi-step chains or
shared-helper instances, and direct stream contracts differ from the observed
lowered address shapes. This establishes comparison, not classifier agreement.
All 129 BFS and 165 BC unmapped loop IDs are retained. The independent gather,
ranged-indirect, pointer-chase and data-dependent-merge fixtures have hand-computed
counts/footprints; atomic and sparse OpenMP fixtures retain memory and worker facts.

Corrected source `cda8f2d` excludes metadata/hint runtime costs while retaining
executed events, counts checked arithmetic explicitly, and preserves opaque runtime
costs as unknown. The final affected estimator/protocol batch passed 22 tests;
independent arithmetic/hint and metadata fixtures and the fake-verified binding
repair passed separately. All 555 records validate after importing immutable a1
receipts. Parent reported the corrected a2 BFS count passed on mbit10; BC is running.
The fourth acceptance item remains pending real frozen-protocol per-region reports.
