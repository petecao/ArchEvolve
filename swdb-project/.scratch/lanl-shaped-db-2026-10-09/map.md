# Map: The research database takes LANL's shape

Created: 2026-10-09 14:19 ET
**Type:** ticket map
**Status:** ready-for-agent (implementation starts only on Yan-Ru's explicit go-ahead)
**Spec:** [spec.md](spec.md)

Each ticket is checkable on its own through `swdb build`, `swdb sql` and the existing query
commands. Order: 01 → 02 → (03, 04, 05 in parallel) → 06 after 03 → 07. Total about 16 h of agent
time (about 2 working days).

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 01 | [Rename every current table to swdb_ (no behavior change)](issues/01-rename-current-tables-to-swdb-prefix.md) | claimed | — | 2 h |
| 02 | [First LANL slice: kernels and kernel_variants](issues/02-first-lanl-slice-kernels-and-variants.md) | resolved | 01 | 3 h |
| 03 | [Source tables](issues/03-source-tables.md) | resolved | 02 | 3 h |
| 04 | [Hardware and performance tables, measured results only](issues/04-hardware-and-performance-tables.md) | resolved | 02 | 3 h |
| 05 | [Validation tables and the empty tables](issues/05-validation-and-empty-tables.md) | resolved | 02 | 2 h |
| 06 | [Contract link tables](issues/06-contract-link-tables.md) | claimed | 03 | 2 h |
| 07 | [ADR 0015, database reference, final shape check](issues/07-adr-reference-and-final-shape-check.md) | ready-for-agent | 03, 04, 05, 06 | 1.5 h |

## Context pointers

- 2026-10-11 19:15 ET: implementation started on integration branch `lanl-shaped-db` (from
  `yanrujhou_main` @ f2624d73). Yan-Ru's decisions: catalog-copying test fixtures may move to the
  record-closure helper (ticket 01 comment); build-speed criterion dropped (ticket 07 comment).
- 2026-10-11 21:20 ET: ticket 02 resolved — LANL group-module pattern (`swdb/lanl.py`,
  `swdb/lanl_<group>.py`, `tests/testkit/lanl.py`); see [02](issues/02-first-lanl-slice-kernels-and-variants.md#answer).
  Ticket 01 merged (42cff8c2) pending its full-suite report and five fixture fixes. ADR 0015
  (ticket 07 part 1) merged early (1b4f57cd).
- 2026-10-11 21:40 ET: tickets 04 and 05 resolved — measured-only performance tables and
  `swdb_estimates` ([04](issues/04-hardware-and-performance-tables.md#answer)); validation tables
  from outcomes that actually ran, four empty slide tables ([05](issues/05-validation-and-empty-tables.md#answer)).
- 2026-10-11 21:55 ET: ticket 03 resolved — source tables from stated code paths, snapshots,
  functions and arrays ([03](issues/03-source-tables.md#answer)). Ticket 06 claimed.
