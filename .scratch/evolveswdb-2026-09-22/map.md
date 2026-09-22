# Map: EvolveSWDB first milestone

Created: 2026-09-22
Updated: 2026-09-22
Spec: `spec.md` (ready-for-agent). Glossary and ADRs: SW Database `CONTEXT.md` and
`docs/adr/` (in `MemAcc/ArchEvolve/SW_Database/` until ticket 01 moves them).

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Bootstrap the repo and validate the first record | — | resolved |
| 02 | Kernel and baseline implementation for gapbs PageRank | 01 | resolved |
| 03 | Input and machine records | 01 | resolved |
| 04 | Workload view | 02, 03 | resolved |
| 05 | SQLite build and queries, plus the Jacobi implementation | 02 | resolved |
| 06 | Adding records (`swdb add`) | 05 | resolved |
| 07 | Profiling: timing and footprints | 03, 04, 06 | resolved |
| 08 | Index-stream features | 07 | resolved |
| 09 | Simulated cache misses (cachegrind) | 07 | resolved |
| 10 | Pilot on mbit10 | 05, 08, 09 | claimed |
| 11 | Format documentation v0.2 and a contributor procedure | 10 | resolved |
| 12 | gapbs bfs, bc, sssp | 11 | claimed |
| 13 | gapbs cc, cc_sv | 11 | claimed |
| 14 | gapbs tc | 11 | claimed |

Frontier now: 10, 12, 13, 14 (profiles running on mbit10 node1).

## Context pointers

(Append one line per resolved ticket: ticket number, date, where its result lives.)
- 01 (2026-09-22): repo bootstrapped; `swdb validate` + application schema; see issues/01 Answer.
- 02 (2026-09-22): gapbs in apps/gapbs; PageRank kernel + Gauss-Seidel baseline; validator rules (swdb/rules.py).
- 03 (2026-09-22): four pilot inputs (num_nodes measured/unknown, see Answer); mbit10 machine record via swdb capture-machine.
- 04 (2026-09-22): swdb view in Josh's format (swdb/view.py, tests/test_view.py).
- 05 (2026-09-22): swdb build/find/implementations/sql; Jacobi record; docs/database.md.
- 06 (2026-09-22): swdb add (swdb/writer.py), agent records draft + agent_run.
- 07 (2026-09-22): swdb profile (swdb/profile.py), lane scripts (scripts/mbit10), docs/mbit10-profiling.md.
- 08 (2026-09-22): tools/index_features (exact index-stream features) wired into swdb profile.
- 09 (2026-09-22): cachegrind in swdb profile, simulated basis, timeouts recorded as incomplete.
- 11 (2026-09-22): docs/format-v0.2.md (+ coverage test), docs/adding-an-application.md.
