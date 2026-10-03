# 23 — Read-only gem5 checks: execution case, frontier sizes, parent-gather race

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The evaluator can qualify a read-only DX100 candidate artifact on gem5 and derive the L3 outcome.

## Acceptance

- [x] A new read-only execution case uses per-opcode trace counts: stream, indirect and range at least 1; ALU 0; indirect stores 0; indirect equals three times range minus stream; full and tail tiles as today. The existing `executed` case and T17 records are unchanged; the baseline role has no accelerator cases.
- [x] Per-level frontier sizes from the exact-text-checked `Starting TDStep` line are compared with the trusted oracle's per-depth counts.
- [x] The parent-gather race case reads the diagnostic build's probe counters: compare-and-swap failures with a negative hint (must be above zero) and L3 violations (must be zero); the L3 outcome (observed, refuted, inconclusive) is derived from that evaluation record.
- [x] Protocol freeze accepts the new cases, and companion acceptance is enforced inside compare-evaluations.
- [x] Tests use fixture traces and outputs (prior art: the DX100 coverage tests); existing comparisons revalidate.

## Comments

Claimed and implemented by Codex retention/evaluator agent, 2026-10-03 ET.

## Answer

Implemented 2026-10-03 ET in `swdb/read_only_checks.py`, `swdb/dx100_coverage.py`, the candidate compiler and protocol evaluator. The new `read_only_executed` case counts completed opcodes inside the ROI, rejects ALU/stores/unmatched instruction pairs, and enforces I = 3R - S. Existing T17 `executed` shape and requirements remain unchanged. The evaluator pins the exact queue-size print and output bytes and compares every frontier with the trusted original graph oracle. The diagnostic adapter adds only `-DSWDB_DXC_DIAGNOSTIC`; exact `SWDB cas_fail_negative_hint=<n> l3_violations=<n>` output derives observed/refuted/inconclusive L3. A compact, hashed coverage report preserves the derived result.

Freeze binds the companion graph/source separately from the timed grid. `compare-evaluations` independently reopens and validates both explicit companion records, frozen binding, candidate tree, primary binary, diagnostic flags, frontiers and probe bytes before accepting timed evidence. L3 must be observed; a violation refutes it and zero races remain inconclusive. Tests cover fixture instruction mixes, original-adjacency frontier counts, probe outcomes, and changed companion output. The focused collector/custody/read-only suite passed 58 tests. These are fixture/pre-check results, not target coherence observations or timing evidence; tickets 28/29 still require real runs.
