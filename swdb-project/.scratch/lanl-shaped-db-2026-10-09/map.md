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
| 01 | [Rename every current table to swdb_ (no behavior change)](issues/01-rename-current-tables-to-swdb-prefix.md) | ready-for-agent | — | 2 h |
| 02 | [First LANL slice: kernels and kernel_variants](issues/02-first-lanl-slice-kernels-and-variants.md) | ready-for-agent | 01 | 3 h |
| 03 | [Source tables](issues/03-source-tables.md) | ready-for-agent | 02 | 3 h |
| 04 | [Hardware and performance tables, measured results only](issues/04-hardware-and-performance-tables.md) | ready-for-agent | 02 | 3 h |
| 05 | [Validation tables and the empty tables](issues/05-validation-and-empty-tables.md) | ready-for-agent | 02 | 2 h |
| 06 | [Contract link tables](issues/06-contract-link-tables.md) | ready-for-agent | 03 | 2 h |
| 07 | [ADR 0015, database reference, final shape check](issues/07-adr-reference-and-final-shape-check.md) | ready-for-agent | 03, 04, 05, 06 | 1.5 h |

## Context pointers
