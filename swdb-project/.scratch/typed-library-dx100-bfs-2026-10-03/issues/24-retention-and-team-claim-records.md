# 24 — Retention and team-claim records; readers accept pruned files

Created: 2026-10-03
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Deleted raw files are recorded in retention records, team claims and releases are recorded, and readers report a pruned file instead of failing.

## Acceptance

- [ ] New record kinds retention (one per prune event) and team claim are registered and documented.
- [ ] `swdb claim RECORD_ID... --audience NAMES` records one team claim citing one or more records; `swdb claim --release EVALUATION_ID` records that no team claim will cite a run.
- [ ] The witness validator, coverage availability check and region comparator report a file with a retention record as "pruned, sha256 retained"; a missing file without one still fails.
- [ ] Evaluation records are never edited.
- [ ] Compare, aggregate and coverage still pass after a fixture prune, and fail without a retention record.

## Comments
