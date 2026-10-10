# 04 — Mark the SPARTA v0.1 Workload view as replaced

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

## What to do

- Add a one-line note to `swdb/view.py` and `archevolve/hw_ensemble/` that Josh has retired
  this format. Delete no code. (The glossary term was removed on 2026-09-29.)
- Add a dated note to `../bfs-rewrite-evaluation-2026-09-25/spec.md` near line 18 that the
  2026-09-24 meeting replaced the ensemble roles with the linear pipeline.

## Answer

2026-09-29: Added dated retirement notes to `swdb/view.py` and
`archevolve/hw_ensemble/README.md`; all copied drafts and their checksums remain intact.
The BFS rewrite specification now states Yan-Ru → Peter → Josh/Eric → Peter → Yan-Ru,
the annotated-source handoff, and Peter's ownership of per-statement memory features.
Older roles remain historical requirements, with no code deleted.

Validation: `test_repo.py` and `test_view.py` — 13 passed, 1 skipped; public record
validation — 312 valid records.
