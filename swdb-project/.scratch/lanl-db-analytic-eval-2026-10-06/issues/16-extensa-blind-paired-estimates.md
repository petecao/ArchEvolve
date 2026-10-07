# 16 — Extensa flow A: blind paired estimates

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 06, 09
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** Extensa campaigns (gem5 and native) estimate every candidate artifact and baseline before timing it (D26), record both in the campaign summary, and still select on timing only (D5).

## Acceptance

- [ ] A fixture-target campaign test shows paired estimates in the summary.
- [ ] Each estimate's time precedes its candidate's timing.
- [ ] Selection is identical with and without paired estimates.
- [ ] Paired estimates are tagged with the campaign and Extensa mode, and team protocols refuse them.


Claimed: 2026-10-06 21:21 ET. Own `codex/lanl-ticket16` worktree is based exactly
on integrated09 `4eaf95a95ed581f3b258d881a719a33f24c80ab2`. Public campaign,
freeze-protocol, estimate and validate commands are the agreed test seams.
All timing routes, exact input/backend binding and recursive team refusal are
required; unknown premises remain explicit and selection/plateau stays unchanged.
