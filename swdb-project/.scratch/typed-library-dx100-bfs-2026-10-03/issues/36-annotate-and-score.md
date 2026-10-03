# 36 — swdb annotate, scoring and the statement table for Josh

Created: 2026-10-03
**Type:** slice
**Status:** claimed
**Blocked by:** 07, 34, 35
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The profiling agent annotates the seven TDStep statements, its agent claims are scored against per-line callgrind, and Josh's statement table is drafted.

## Acceptance

- [ ] `swdb annotate IMPLEMENTATION` runs the profiling agent through the provider launcher on mbit10 and writes pattern class, index provenance and expected cost rank per statement.
- [ ] Scoring reports the Spearman rank correlation and top-3 overlap against ticket 34's data, and applies the contradiction rule.
- [ ] A statement table for Josh is drafted for Yan-Ru to send.
- [ ] Annotate and scoring are tested with fixtures.

## Comments
