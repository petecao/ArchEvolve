# 03 — Crosswalk v0 from the slides

Created: 2026-10-06
Updated: 2026-10-09 23:10 ET (code review note); 2026-10-06 ET (implemented, source-audited and validated)
**Type:** task
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 1 h

**What to build:** A machine-readable crosswalk maps each main-database table and field to a research-database record kind and field, or marks it as having no counterpart. Every row is `unverified`; the source is the overview deck's slides 8–9. Research-database concepts with no counterpart are listed as the separable extension (ADR 0014).

## Acceptance

- [x] One versioned crosswalk that validates against a small schema.
- [x] The LANL notes (§4) point to it.
- [x] Every row is marked `unverified` with its slide as source.

## Answer

The versioned [crosswalk v0](../../../docs/compatibility/lanl-crosswalk-v0.yaml)
contains 25 mappings covering the ten table labels and visible field descriptions
in overview slides 8–9, plus 19 separable extension concepts. It validates against
[a standalone small schema](../../../schemas/compatibility/main_crosswalk.schema.json)
through `swdb validate --crosswalk`. The [LANL notes §4](../lanl-db-notes.md#4-draft-mapping-unverified-built-from-slide-pictures-only)
link to it and its [format instructions](../../../docs/compatibility/README.md).

Every mapping and extension is `unverified` with slide 8 or 9 as provenance.
Slide labels stay separate from SQL identifiers, and unseen identifiers stay null.
The source deck was inspected read-only and its PDF hash is retained. Proposed
research kinds and fields exist in current SWDB schemas; no LANL schema access,
import, verified compatibility or verified absence of extension concepts is claimed.

[Verification evidence](../crosswalk-v0-verification.md): 553 records and the
crosswalk validate; seven focused public CLI tests passed; the selected validation
and query regression run reported 139 passed and one data-dependent skip.

## Code review 2026-10-09

2026-10-09 23:10 ET. The crosswalk rows still validate and stay `unverified`. Fixed: the
schema's `record_kind` enum was a 2026-10-06 snapshot and could not name the 13 record
kinds added since (estimates, characterizations, CPU calibrations, agreement records).
It now lists every `swdb.store` kind, and `tests/test_crosswalk.py` checks that it stays in
sync and that every dotted field in the crosswalk exists in its record schema. The crosswalk
rows and extension list are unchanged (v0 is frozen from the slides); the new research-only
kinds are not classified in v0.
