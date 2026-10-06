# 16 — Extensa flow A: blind paired estimates

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06, 09
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** Extensa campaigns (gem5 and native) estimate every candidate artifact and baseline before timing it (D26), record both in the campaign summary, and still select on timing only (D5).

## Acceptance

- [ ] A fixture-target campaign test shows paired estimates in the summary.
- [ ] Each estimate's time precedes its candidate's timing.
- [ ] Selection is identical with and without paired estimates.
- [ ] Paired estimates are tagged with the campaign and Extensa mode, and team protocols refuse them.
