# 22 — `swdb import-main`: read the main database

Created: 2026-10-06
**Type:** slice
**Status:** needs-info
**Blocked by:** 02, 03, 21
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** A read-only import turns main-database rows into research-database records through the crosswalk and the access layer, keeping every main-database ID and tagging provenance.

## Acceptance

- [ ] Crosswalk rows used are re-marked `verified` against the real schema.
- [ ] Unmapped fields are reported, never dropped.
- [ ] Imported records validate.
