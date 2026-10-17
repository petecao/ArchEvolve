# 05 — Prefactor: intrinsic records accept a hardware interface

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Intrinsic records can describe accelerator commands as well as ISA instructions (Q60), without disturbing any existing record.

## Acceptance

- [x] An intrinsic record may carry `interface: {id, version}` (the operation records' shape, for example `dx100-mmio` / `1.0-e4fc4af`) instead of ISA extensions; ISA family, extensions and header become optional only then.
- [x] An accelerator intrinsic lists the operation record IDs it uses (possibly none, as for session begin and per-thread context), carries source-code provenance, and points to its library entry by path and content sha256; the vendor-reference rule applies only to ISA intrinsics.
- [x] The database index, required-ISA derivation and profile-package intrinsic listing handle accelerator intrinsics (listed as not applicable to machine ISA support).
- [x] The two existing ISA intrinsic records, every profile package and every existing test validate unchanged.
- [x] New fields are documented in the format reference; the format-document and format-version tests stay green.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

Accelerator-interface intrinsic records retain ISA requirements for existing records and pin library content; build support stays distinct from ISA machine support. Schema, rules, derived database views and profile-package classification are implemented.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.
