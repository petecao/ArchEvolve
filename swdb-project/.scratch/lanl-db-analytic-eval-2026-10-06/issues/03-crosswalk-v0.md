# 03 — Crosswalk v0 from the slides

Created: 2026-10-06
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 1 h

**What to build:** A machine-readable crosswalk maps each main-database table and field to a research-database record kind and field, or marks it as having no counterpart. Every row is `unverified`; the source is the overview deck's slides 8–9. Research-database concepts with no counterpart are listed as the separable extension (ADR 0014).

## Acceptance

- [ ] One versioned crosswalk that validates against a small schema.
- [ ] The LANL notes (§4) point to it.
- [ ] Every row is marked `unverified` with its slide as source.
