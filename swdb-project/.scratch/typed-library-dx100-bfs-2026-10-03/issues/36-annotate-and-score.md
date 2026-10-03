# 36 — swdb annotate, scoring and the statement table for Josh

Created: 2026-10-03
**Type:** slice
**Status:** needs-info
**Blocked by:** 07, 34, 35
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The profiling agent annotates the seven TDStep statements, its agent claims are scored against per-line callgrind, and Josh's statement table is drafted.

## Acceptance

- [ ] `swdb annotate IMPLEMENTATION` runs the profiling agent through the provider launcher on mbit10 and writes pattern class, index provenance and expected cost rank per statement.
- [ ] Scoring reports the Spearman rank correlation and top-3 overlap against ticket 34's data, and applies the contradiction rule.
- [ ] A statement table for Josh is drafted for Yan-Ru to send.
- [x] Annotate and scoring are tested with fixtures.

## Comments

- 2026-10-03: Annotation, contradiction and scoring fixtures pass; the real guarded provider and Josh table await the admitted profile. No measured correlation or real provider result is claimed.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. The guarded annotation/scoring implementation and fixture CLI regressions pass. Actual annotation, correlation/top-three score and Josh result table require ticket 34 real profile and approved source synchronization. No real provider result or measured score is claimed. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.
