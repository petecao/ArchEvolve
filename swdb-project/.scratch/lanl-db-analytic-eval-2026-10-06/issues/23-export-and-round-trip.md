# 23 — Export and round-trip test

Created: 2026-10-06
Updated: 2026-10-08 12:16 ET (wontfix: no LANL contact)
**Type:** slice
**Status:** wontfix
**Blocked by:** 22
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** Research-database kernels are written as the main database's own ingest inputs, never into its SQLite file, and import → export → their ingest → import gives identical records.

## Acceptance

- [ ] The round-trip test passes on a fixture.
- [ ] The separable extension is exported as extra tables or omitted, as LANL prefers.

## Answer

2026-10-08 12:16 ET, Yan-Ru: **wontfix.** We will not contact LANL, and we do not have their database.
Tickets 21–23 (ask for access, import, export and round-trip) are closed together. The
crosswalk v0 (ticket 03) and the access layer (ticket 02) stay as they are. Open a new
ticket if LANL later shares their database on their own.
