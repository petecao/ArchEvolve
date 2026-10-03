# 53 — Speed rule, per-class verdicts, selection and knob tuning

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 52
**Spec:** `../spec.md`

**What to build:** Extensa campaigns judge and select candidate artifacts by the spec's speed rule.

## Acceptance

- [ ] The region of interest is the whole BFS call (`bfs.complete_call.v1`); one protocol per target per Extensa campaign, no region pairs; gem5 baseline once per workload class; native candidate artifacts in their own paired blocks.
- [ ] A gain needs a lower bound strictly above 1.05 with spread within 0.1; gem5 results are reported as point ratios.
- [ ] Each workload class has its own verdict and best, labeled "single graph per class"; a class where nothing passes gets no gain and no best.
- [ ] Selection ranks certified before uncertified, then the lower bound; edits using no contract derive as uncertified; a candidate artifact that fails certification is rejected; faster uncertified candidate artifacts are reported.
- [ ] The loop tunes knobs only within their legality-enforced ranges; a test shows ArchEvolve mode still never tunes after a valid regression.

## Comments
