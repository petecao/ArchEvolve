# 25 — swdb prune: dry run, approval and apply

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 24
**Spec:** `../spec.md`

**What to build:** Yan-Ru can see exactly what a cleanup would delete, and only an approved listing deletes anything.

## Acceptance

- [ ] `swdb prune --dry-run` lists every file under the run roots with its size, class (bulky, compact or input) and every record that references its path.
- [ ] Inputs (referenced by a workload, source snapshot, build receipt or frozen protocol) are never proposed; only bulky files are.
- [ ] `swdb prune --approve LISTING` records Yan-Ru's approval.
- [ ] `swdb prune --apply LISTING` refuses an unapproved listing and any entry not classed as bulky; it deletes only the listed files, hashing each first, and writes retention records.
- [ ] A dry run deletes nothing (test).

## Comments
