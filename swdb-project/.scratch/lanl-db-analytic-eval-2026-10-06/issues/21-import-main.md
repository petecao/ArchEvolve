# 21 — `swdb import-main`: read the main database, keep its IDs

Created: 2026-10-06
**Type:** slice
**Status:** needs-info
**Blocked by:** 20, 18, 19
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** A read-only import that turns main-database rows into research-database records through the crosswalk, keeping every main-database ID and tagging provenance.

## Acceptance

- [ ] Crosswalk rows used are re-marked `verified` against the real schema.
- [ ] Unmapped fields reported, never dropped silently.
- [ ] Imported records validate.
