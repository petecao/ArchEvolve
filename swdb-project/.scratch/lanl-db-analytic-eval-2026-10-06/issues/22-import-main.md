# 22 — `swdb import-main`: read the main database

Created: 2026-10-06
Updated: 2026-10-08 12:16 ET (wontfix: no LANL contact)
**Type:** slice
**Status:** wontfix
**Blocked by:** 02, 03, 21
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** A read-only import turns main-database rows into research-database records through the crosswalk and the access layer, keeping every main-database ID and tagging provenance.

## Acceptance

- [ ] Crosswalk rows used are re-marked `verified` against the real schema.
- [ ] Unmapped fields are reported, never dropped.
- [ ] Imported records validate.

## Answer

2026-10-08 12:16 ET, Yan-Ru: **wontfix.** We will not contact LANL, and we do not have their database.
Tickets 21–23 (ask for access, import, export and round-trip) are closed together. The
crosswalk v0 (ticket 03) and the access layer (ticket 02) stay as they are. Open a new
ticket if LANL later shares their database on their own.
