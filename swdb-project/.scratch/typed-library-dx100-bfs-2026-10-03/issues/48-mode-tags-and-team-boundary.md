# 48 — Mode tags, team-boundary refusals and candidate-artifact promotion

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 11, 15, 47
**Spec:** `../spec.md`

**What to build:** Extensa records are tagged at creation and kept out of team results until promoted.

## Acceptance

- [ ] Records an Extensa campaign writes carry the mode and Extensa campaign ID, set at creation, optional (absent means ArchEvolve mode), never backfilled.
- [ ] Certification level is derived from certification records when queried, never stored on candidate-artifact records.
- [ ] compare-evaluations, handoff-message and the coverage report refuse or skip unpromoted Extensa records.
- [ ] `swdb promote` also covers candidate artifacts, followed by re-evaluation under a team protocol for the candidate artifact's workload class.

## Comments
