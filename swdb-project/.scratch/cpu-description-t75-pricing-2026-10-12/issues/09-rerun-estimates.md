# 09 — Rerun ticket 03: estimate the t75 pair with services.v2

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 08
**Spec:** `../spec.md` (C13 (estimate half); user stories 1, 24, 25, 27, 28)
**Code map:** `../notes/ops.md`

**Time estimate:** about 2.5 hours (two freezes + two estimates).

## What to do

Reuse the saved `fga03.t75-{baseline,candidate}.uniform22.t1.request.a1.yaml` and the a2
characterizations (no recount). Freeze `.a3` protocols that pin `services.v2`, both at the same
commit (F47), estimate both sides (`.a3`), run `swdb attribute` (unchecked report). Log the order
(estimates before any timing).

## Acceptance

- [ ] Both estimates have non-null seconds, or `## Answer` closes negative with every remaining gap named (parameterized unknowns summary).
- [ ] Attribution report with numeric rewritten/untouched/unattributed shares saved as a record.
- [ ] Records committed and pushed; order log saved in `evidence/09-rerun-03/`.
