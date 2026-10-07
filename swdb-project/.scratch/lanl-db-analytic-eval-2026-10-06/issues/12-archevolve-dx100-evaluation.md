# 12 — ArchEvolve-mode DX100 evaluation without gem5

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 06, 09
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** An ArchEvolve-mode DX100 candidate artifact is built on the functional model's strict layer and passes the kernel's correctness check and certification (functional-target correctness, D8), then gets an estimate, a three-state verdict (D25), an evaluation record and an evaluation-result handoff message whose new version carries the estimate, basis, verdict and band.

## Acceptance

- [ ] Functional-target correctness is labeled as such, never as correctness on the hardware target.
- [ ] The verdict is `within_error` until a band exists, with the ratio shown.
- [ ] The handoff format version is bumped and documented.
- [ ] A test shows that no gem5 job starts anywhere in the path.

## Implementation custody

Updated: 2026-10-06 21:23 ET. Parent `/root` owns `codex/lanl-ticket12`, based on integrated `4eaf95a`. Public seams: functional ArchEvolve evaluation, evaluation-result handoff and canonical validation. User authorized autonomous interface decisions; preserve functional-target correctness and outcome-free team lineage.

## Public local gate

Updated: 2026-10-06 22:06 ET. The functional evaluation, handoff 1.1 and canonical validation seams pass six distinct public cases across the recorded gates. Cached estimate/certificate integrity, stale certification, recursive team refusal, absence of child processes and historical 1.0 document pins are covered. See `../evidence/12-public-functional-evaluation-proof.json`. Remote exact-artifact acceptance is still pending; the ticket remains claimed.
