# 31 — Fallback contract: the CPU loads the parent value itself

Created: 2026-10-03
**Type:** slice
**Status:** wontfix
**Blocked by:** 28
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** Only if ticket 28 refutes L3: a separate contract in which the CPU loads the parent value itself while DX100 still gathers the neighbors and the frontier vertex.

## Acceptance

- [ ] A separate derived contract entry with its own ID cites the BFS read-offload contract and certifies on the Mac with the same negative controls.
- [ ] It gets its own proposal, companion runs and timed runs under the same protocol.
- [ ] The finding is drafted for Peter and Eric for Yan-Ru to send.
- [ ] It is triaged to ready only if ticket 28 records an L3 violation.

## Comments

## Answer

2026-10-03 11:10 ET: the conditional fallback is unnecessary for this evaluation. Ticket28 completed with observed L3, 14,546 exercised negative-hint CAS failures and zero L3 violations, published in `5d74de87bfe45023ab7193f36659c0f3f9999bfb`. The condition to create another contract was not triggered; keep the certified read-offload candidate and frozen protocol for ticket29. This finite observation does not discharge the global L3 assumption. [Actual companion evidence](../evaluation/companion-a1-summary.json).
