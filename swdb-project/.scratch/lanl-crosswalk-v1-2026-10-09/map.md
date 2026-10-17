# Map: LANL crosswalk v1

Created: 2026-10-09 14:05 ET
**Type:** ticket map
**Status:** wontfix
Superseded 2026-10-09 ET by [the LANL-shaped database spec](../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
**Spec:** [spec.md](spec.md)

Each ticket is a vertical slice that is checkable on its own through
`python -m swdb validate --crosswalk`. Order: 01 → 02 → (03 and 04 in parallel) → 05.
Total about 2–3 hours of agent time.

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Validator picks the crosswalk format by version](issues/01-validator-picks-format-by-version.md) | wontfix | — |
| 02 | [First working v1: sources and the 5 source-code tables](issues/02-first-v1-sources-and-source-code-tables.md) | wontfix | 01 |
| 03 | [Unknown link targets and cardinality](issues/03-unknown-link-targets-and-cardinality.md) | wontfix | 02 |
| 04 | [Contract and library extension concepts](issues/04-contract-and-library-extension-concepts.md) | wontfix | 02 |
| 05 | [Remaining 9 tables, slide coverage check, README](issues/05-remaining-tables-coverage-and-readme.md) | wontfix | 03, 04 |

## Context pointers
