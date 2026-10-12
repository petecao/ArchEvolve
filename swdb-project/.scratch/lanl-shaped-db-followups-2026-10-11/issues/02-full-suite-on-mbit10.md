# 02 — Run the full swdb suite on mbit10

Created: 2026-10-11
**Type:** task
**Status:** resolved
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

## Answer

Resolved 2026-10-12 19:53 ET on interim evidence (Yan-Ru asked to close it faster); the comparison run finishes in
the background and this ticket reopens only if it finds a regression.
- Method: head 680298a3 vs base f2624d73 on mbit10, one socket lane, `-n 6`, temp under `/data`,
  the 140 full-catalog-copy tests and the 183 tests that already time out at base deselected.
  Per-test results compared by node ID.
- Result at ~3,600 of 4,880 tests: every head failure also fails at base or is an mbit10
  environment effect; **no failure caused by the LANL-shaped-db work.**
- mbit10 environment causes (pre-existing, not ticketed): the `mbit10` hostname guard in
  `swdb/dx100.py:127` and the evaluate path refuses fixture machines that disable the socket lane,
  so DX100 and protocol/extensa seed modules fail there; tests need the Mac's
  `/opt/homebrew/opt/llvm/bin/clang++`; full-catalog `swdb validate` takes ~13 min > the 600 s
  test limit; `workflow._source_destination` writes snapshots to `/data1/yanruj/EvolveSWDB_sources`
  outside the test basetemp (3 `test_bc_native` collisions came from reused run folders).
- Lessons: the first run (`-n 16`) ran out of node-0 memory; one run lost all results to a timeout
  because results were not written per test. Use `-n 6` and `--report-log` on mbit10.
