# 04: Rewrite-site edge cases

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** claimed
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F1, F2, F14, F24; seam 1)
**Time estimate:** about 3–4 hours

**What to build:** `swdb attribute` handles the hard cases of mapping changed lines to regions: two sites sharing a region merge into one; a region only partly inside a site counts as rewritten and is flagged `mixed`; untouched functions are matched across inserted or deleted lines; a rewritten helper inlined into an untouched caller is labeled by its own file and line; unattributed time above 10% of the total sets a flag on the report.

## Acceptance

- [ ] One fixture per case, each with hand-checked labels.
- [ ] No region's time is counted in two sites.
- [ ] Unattributed above 10% is flagged and the report is still written.
