# 23 — Export and round-trip test

Created: 2026-10-06
**Type:** slice
**Status:** needs-info
**Blocked by:** 22
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** Research-database kernels are written as the main database's own ingest inputs, never into its SQLite file, and import → export → their ingest → import gives identical records.

## Acceptance

- [ ] The round-trip test passes on a fixture.
- [ ] The separable extension is exported as extra tables or omitted, as LANL prefers.
