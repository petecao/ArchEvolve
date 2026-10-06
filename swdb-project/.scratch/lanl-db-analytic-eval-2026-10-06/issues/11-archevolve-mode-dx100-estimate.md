# 11 — ArchEvolve-mode DX100 evaluation: functional-target correctness plus estimate

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 08, 10
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** For a DX100 candidate in ArchEvolve mode: native build on the strict layer, the kernel's correctness check and certification (D8), then an estimate and a verdict in three states (D25): `estimated_gain` only if the ratio stays above 1.05 after subtracting the error band, `within_error` if the band covers 1.05, otherwise `estimated_no_gain`. The evaluation record and the `evaluation_result` handoff message carry the estimate and its basis.

## Acceptance

- [ ] Functional-target correctness is labeled as such and never as hardware-target correctness.
- [ ] Before a band is validated (ticket 12 for CPU, ticket 13 for DX100), the verdict is `within_error`, with the ratio shown.
- [ ] Handoff message format bumped and documented.
