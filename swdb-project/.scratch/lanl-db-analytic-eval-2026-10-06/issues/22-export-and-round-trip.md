# 22 — Export through the main database's ingest inputs, with a round-trip test

Created: 2026-10-06
**Type:** slice
**Status:** needs-info
**Blocked by:** 21
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** Write research-database kernels in the main database's own ingest inputs (never its SQLite file), and test import → export → their ingest → import for identical records.

## Acceptance

- [ ] Round-trip test green on a fixture.
- [ ] The separable extension is exported as extra tables or omitted, as LANL prefers.
