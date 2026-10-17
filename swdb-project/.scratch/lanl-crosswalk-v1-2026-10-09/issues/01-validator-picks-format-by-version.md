# 01 — Validator picks the crosswalk format by version

Created: 2026-10-09
**Type:** slice
**Status:** wontfix
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** `python -m swdb validate --crosswalk <file>` reads the document's
`crosswalk_version` and validates it against the matching format. Version 0 behaves exactly as
today. Any version without a format is refused with a clear problem at `crosswalk_version`.
This prefactor gives tickets 02–05 a place to add the v1 format without touching v0.

- [ ] The committed v0 crosswalk validates, with the same output as before
- [ ] All existing crosswalk tests pass unchanged
- [ ] A document with an unknown `crosswalk_version` is refused, and the error names `crosswalk_version`
- [ ] The v0 document and v0 format are byte-for-byte unchanged
- [ ] Validation without `--crosswalk` behaves as before

## Comments

Superseded 2026-10-09 ET by [the LANL-shaped database spec](../../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
