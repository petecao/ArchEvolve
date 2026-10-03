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
- [x] Annotate and scoring are tested with fixtures.

## Comments

- 2026-10-03: Annotation, contradiction and scoring fixtures pass; the real guarded provider and Josh table await the admitted profile. No measured correlation or real provider result is claimed.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. The guarded annotation/scoring implementation and fixture CLI regressions pass. Actual annotation, correlation/top-three score and Josh result table require ticket 34 real profile and approved source synchronization. No real provider result or measured score is claimed. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

- 2026-10-03 08:43 ET: related source/dispatch authorization is complete; exact runtime f6972eb is synchronized and431 records validate. Claimed for the assigned real remote sequence. Node0 guarded annotation/scoring will start only after the actual complete a2 profile/package; root will review the resulting table before delegated sending.

- 2026-10-03 08:57 ET: actual annotation attempts1/2 both failed and are retained in [failure summary](../evaluation/annotation-a1-a2-failure-summary.json), published8506be7. Attempt1 failed before launch from tmux's missing standard Codex-home setting; attempt2 selected the existing regular protected login and reached the pinned real provider, with guard/audit pass and login-copy cleanup, but its output schema was rejected400 for unsupported uniqueItems. No claims, score or real table exist. A transport-only schema correction is being implemented; normative/local schema validation and duplicate-provenance rejection remain required.

- 2026-10-03 09:01 ET: both independent transport reviews pass. The correction copies the wire schema and omits unsupported uniqueness constraints only at schema nodes, while preserving normative local uniqueness validation and literal data. Three new regressions pass; complete affected-file tests and source publication are pending before fresh actual attempt3.

- 2026-10-03 09:03 ET: transport fix passes all45 complete affected-file cases, and both review axes pass. Full local identity coverage reconciles3,690 cases with zero unresolved failure/error; reviewed source is being published before fresh actual attempt3.
