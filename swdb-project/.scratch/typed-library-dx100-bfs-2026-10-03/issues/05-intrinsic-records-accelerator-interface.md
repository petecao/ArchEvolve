# 05 — Prefactor: intrinsic records accept a hardware interface

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Intrinsic records can describe accelerator commands as well as ISA instructions (Q60), without disturbing any existing record.

## Acceptance

- [ ] An intrinsic record may carry `interface: {id, version}` (the operation records' shape, for example `dx100-mmio` / `1.0-e4fc4af`) instead of ISA extensions; ISA family, extensions and header become optional only then.
- [ ] An accelerator intrinsic lists the operation record IDs it uses (possibly none, as for session begin and per-thread context), carries source-code provenance, and points to its library entry by path and content sha256; the vendor-reference rule applies only to ISA intrinsics.
- [ ] The database index, required-ISA derivation and profile-package intrinsic listing handle accelerator intrinsics (listed as not applicable to machine ISA support).
- [ ] The two existing ISA intrinsic records, every profile package and every existing test validate unchanged.
- [ ] New fields are documented in the format reference; the format-document and format-version tests stay green.

## Comments
