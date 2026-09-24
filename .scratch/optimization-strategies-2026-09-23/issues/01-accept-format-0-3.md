# 01 — Accept format 0.3 (prefactor)

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** the tool accepts records at format 0.3, and a v0.3 format document
exists that later tickets extend. No behavior changes for existing records.

- [x] Validation accepts `schema_version` "0.2" and "0.3"; every existing record still validates unchanged.
- [x] A v0.3 format document exists (the v0.2 content, a changelog section, and the versioning rule stating 0.3 is a minor release). The v0.2 document stays as it is.
- [x] The format-document coverage test checks the v0.3 document, and its "would catch a missing field" test still fails as intended.
- [x] A record at 0.3 passes, and a record at an unsupported version (for example "0.4") fails.
- [x] The full test suite passes.

## Comments

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- `schemas/envelope.schema.json` accepts `schema_version` "0.2" and "0.3". Every repo record
  validates unchanged (`tests/test_format_versions.py`).
- `docs/format-v0.3.md` is the v0.2 text plus a "Changes from 0.2" section and the versioning
  rule (0.3 is a minor release; a rule may require an addition only of records that say
  "0.3"). `docs/format-v0.2.md` is untouched.
- `tests/test_format_doc.py` now checks the v0.3 document; its negative control still fails as
  intended. A 0.3 record passes and a "0.4" record fails.
- Full suite: 193 passed, 3 skipped.
