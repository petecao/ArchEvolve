# 50 — Tracer: certify one library operation (packing)

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 02, 11, 47
**Spec:** `../spec.md`

**What to build:** A library operation certifies end to end against a plain C++ reference.

## Acceptance

- [ ] The packing entry enters the experimental tier with its Extensa source commit and path as origin, and SPDX and provenance headers on its C++ body.
- [ ] It certifies against its plain C++ reference with a differential-test driver and negative controls.
- [ ] The validator rejects a library-operation body that calls a hardware interface.

## Comments
