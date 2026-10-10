# 19 — Flow B screening

Created: 2026-10-06
Updated: 2026-10-09 22:33 ET (wontfix: ticket 18 chose not to switch to flow B)
**Type:** slice
**Status:** wontfix
**Blocked by:** 18
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** One rewrite call yields N variants (knob values or sites, no extra provider call); all are certified and estimated; the top-k by estimate plus one random spot check are timed. If certification cost depends on knob values, variants differ only in knobs, so one certification covers them all.

## Acceptance

- [ ] gem5 hours per iteration are unchanged for the same k; candidates explored per iteration are reported.
- [ ] Spot-check results are recorded, so the rate of keeping the winner stays measured.
- [ ] Untimed variants are kept with their estimates and never ranked as timed.
