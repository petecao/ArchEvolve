# 02 — Run the full swdb suite on mbit10

Created: 2026-10-11
**Type:** task
**Status:** claimed
**Blocked by:** None — can start immediately
**Spec:** `../../lanl-shaped-db-2026-10-09/map.md` (follow-up 2)

**What to do:** the full suite cannot finish on the Mac (about 125 catalog-copying tests take
about 10 min each; `swdb source-snapshot` hits its 600 s limit). Run it once on mbit10 at
`yanrujhou_main` 67269c86 or later, inside one socket lane (≤16 workers), with output under
`/data1/yanruj/EvolveSWDB_runs/`. Classify every failure as caused by the LANL-shaped-db work or
pre-existing (compare with the base commit f2624d73 for any failure that could touch the database).

- [ ] Run record: commit, host load, lane, workers, wall time, pass/fail/error counts
- [ ] Every failure classified, with the base-commit comparison for database-related ones
- [ ] Any failure caused by the LANL-shaped-db work fixed on `yanrujhou_main`
- [ ] Raw output deleted after its summary and hash are recorded
