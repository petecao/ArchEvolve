# 08 — Peter's feature reports as an input

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 05
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** A reader imports Peter's feature reports into a characterization as one input source, with basis `reported`. The characterization's field names match his where they overlap (D20). Where his values and SWDB's counts differ, both are kept and the difference is flagged.

## Acceptance

- [ ] His BFS sparse and fully connected reports (v1.2) import.
- [ ] A table of overlapping fields is documented.
- [ ] Conflicts are listed, never silently resolved.

Claimed: 2026-10-06 ET by Codex ticket 08 worker on `codex/lanl-ticket08`; base `8e2156a`. Public seams: import-feature-report, view and validate against a copied record store, extending the spec-confirmed characterization CLI seam. Report input is additional reported evidence; counted facts and receipts remain immutable.
