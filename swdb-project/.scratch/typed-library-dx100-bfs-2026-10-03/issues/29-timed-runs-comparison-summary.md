# 29 — Timed gem5 runs, comparison and team summary

Created: 2026-10-03
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 28
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The team gets its first gem5 result for Peter's rewrite, measured against a fresh scalar baseline. Runs only if ticket 28's Answer records L3 observed on target.

## Acceptance

- [ ] The pre-dispatch checks are recorded.
- [ ] Baseline and candidate-artifact timed runs finish on Kronecker 18 and uniform 18; all four pass the verifier, and the two candidate-artifact runs also pass the frontier check and the read-only execution case.
- [ ] A comparison is recorded whatever the speedup; gem5 results are reported as point ratios; the authors' T17 result is cited as context only.
- [ ] The contract and lowering entries' derived status becomes evaluated on target, or refuted.
- [ ] A one-page summary with basis labels is drafted for Yan-Ru to send.

## Comments
