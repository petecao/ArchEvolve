# 23 — Read-only gem5 checks: execution case, frontier sizes, parent-gather race

Created: 2026-10-03
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The evaluator can qualify a read-only DX100 candidate artifact on gem5 and derive the L3 outcome.

## Acceptance

- [ ] A new read-only execution case uses per-opcode trace counts: stream, indirect and range at least 1; ALU 0; indirect stores 0; indirect equals three times range minus stream; full and tail tiles as today. The existing `executed` case and T17 records are unchanged; the baseline role has no accelerator cases.
- [ ] Per-level frontier sizes from the exact-text-checked `Starting TDStep` line are compared with the trusted oracle's per-depth counts.
- [ ] The parent-gather race case reads the diagnostic build's probe counters: compare-and-swap failures with a negative hint (must be above zero) and L3 violations (must be zero); the L3 outcome (observed, refuted, inconclusive) is derived from that evaluation record.
- [ ] Protocol freeze accepts the new cases, and companion acceptance is enforced inside compare-evaluations.
- [ ] Tests use fixture traces and outputs (prior art: the DX100 coverage tests); existing comparisons revalidate.

## Comments
