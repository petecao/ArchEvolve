# 01 — Accept format 0.3 (prefactor)

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** the tool accepts records at format 0.3, and a v0.3 format document
exists that later tickets extend. No behavior changes for existing records.

- [ ] Validation accepts `schema_version` "0.2" and "0.3"; every existing record still validates unchanged.
- [ ] A v0.3 format document exists (the v0.2 content, a changelog section, and the versioning rule stating 0.3 is a minor release). The v0.2 document stays as it is.
- [ ] The format-document coverage test checks the v0.3 document, and its "would catch a missing field" test still fails as intended.
- [ ] A record at 0.3 passes, and a record at an unsupported version (for example "0.4") fails.
- [ ] The full test suite passes.

## Comments
