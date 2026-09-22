# Map: EvolveSWDB first milestone

Created: 2026-09-22
Spec: `spec.md` (ready-for-agent). Glossary and ADRs: SW Database `CONTEXT.md` and
`docs/adr/` (in `MemAcc/ArchEvolve/SW_Database/` until ticket 01 moves them).

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Bootstrap the repo and validate the first record | — | resolved |
| 02 | Kernel and baseline implementation for gapbs PageRank | 01 | ready-for-agent |
| 03 | Input and machine records | 01 | ready-for-agent |
| 04 | Workload view | 02, 03 | ready-for-agent |
| 05 | SQLite build and queries, plus the Jacobi implementation | 02 | ready-for-agent |
| 06 | Adding records (`swdb add`) | 05 | ready-for-agent |
| 07 | Profiling: timing and footprints | 03, 04, 06 | ready-for-agent |
| 08 | Index-stream features | 07 | ready-for-agent |
| 09 | Simulated cache misses (cachegrind) | 07 | ready-for-agent |
| 10 | Pilot on mbit10 | 05, 08, 09 | ready-for-agent |
| 11 | Format documentation v0.2 and a contributor procedure | 10 | ready-for-agent |
| 12 | gapbs bfs, bc, sssp | 11 | ready-for-agent |
| 13 | gapbs cc, cc_sv | 11 | ready-for-agent |
| 14 | gapbs tc | 11 | ready-for-agent |

Frontier now: 02, 03.

## Context pointers

(Append one line per resolved ticket: ticket number, date, where its result lives.)
- 01 (2026-09-22): repo bootstrapped; `swdb validate` + application schema; see issues/01 Answer.
