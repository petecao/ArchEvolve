# 11 — Format documentation v0.2 and a contributor procedure

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 10
**Spec:** `../spec.md`

**What to build:** The written format matches what the tool enforces, and a collaborator
can add an application and its kernels by following one procedure.

- [ ] The format document is rewritten as v0.2 from the enforced schemas, including the versioning rule (minor versus major changes, deprecation).
- [ ] A test fails if any schema field is missing from the format document.
- [ ] A step-by-step procedure for adding an application, its kernels, their implementations, and inputs, including what each basis value means.
- [ ] The procedure is checked by using it to draft the application-level and kernel-level records for one gapbs kernel not yet recorded; `swdb validate` passes on the result.

## Comments
