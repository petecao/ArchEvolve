# 52 — Extensa campaign skeleton

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 07, 48, 49, 24
**Spec:** `../spec.md`

**What to build:** `swdb campaign` runs one iteration of an Extensa campaign end to end on fixtures with a fixed region list.

## Acceptance

- [ ] One iteration runs: regions, rewrite provider, certification, evaluator, record writing.
- [ ] The Extensa campaign record store holds its records; only the summary, promoted candidate artifacts and team claims with evidence are copied to the team store; new library entries are committed to the library folder in the experimental tier.
- [ ] An Extensa campaign summary record (new kind, registered and documented) is written.

## Comments
