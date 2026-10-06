# 17 — Extensa flow B: screening by estimate

Created: 2026-10-06
**Type:** slice
**Status:** needs-triage
**Blocked by:** 16
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** One rewrite call yields N variants (knob values or sites, no extra provider call); all are certified and estimated; the top-k by estimate plus one random spot check are timed. Open: if certification cost depends on knob values, variants differ only in knobs.

## Acceptance

- [ ] Gem5 hours per iteration unchanged for the same k; candidates explored per iteration reported.
- [ ] Spot-check results recorded so the winner-kept rate stays measured.
- [ ] Untimed variants kept with their estimates, never ranked as timed.
