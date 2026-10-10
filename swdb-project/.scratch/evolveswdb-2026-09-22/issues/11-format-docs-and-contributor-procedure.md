# 11 — Format documentation v0.2 and a contributor procedure

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 10
**Spec:** `../spec.md`

**What to build:** The written format matches what the tool enforces, and a collaborator
can add an application and its kernels by following one procedure.

- [x] The format document is rewritten as v0.2 from the enforced schemas, including the versioning rule (minor versus major changes, deprecation).
- [x] A test fails if any schema field is missing from the format document.
- [x] A step-by-step procedure for adding an application, its kernels, their implementations, and inputs, including what each basis value means.
- [x] The procedure is checked by using it to draft the application-level and kernel-level records for one gapbs kernel not yet recorded; `swdb validate` passes on the result.

## Comments

## Answer

Resolved 2026-09-22.

- `docs/format-v0.2.md`: the enforced format, the versioning rule (minor = additions only;
  major = anything that can invalidate a record, with a migration), and deprecation.
- `tests/test_format_doc.py` fails if any schema field or vocabulary is missing from the
  document (with a negative control).
- `docs/adding-an-application.md`: step-by-step procedure incl. what each basis means.
- Procedure check: two agents used it to write the kernel and implementation records of
  bfs, bc, sssp, cc, cc_sv, and tc (tickets 12-14); `swdb validate` passed. They reported
  26 gaps; the procedure and the tool were fixed for them (for example nullable
  data-dependent sizes, `sweep_count_regex`, `condition`, alias pairs, one-array-many-roles).
