# The research database takes the main database's shape

Date: 2026-10-11 ET
Status: proposed (decided by Yan-Ru on 2026-10-09 after LANL showed the `DB_current_work` slide;
no access to the main database's schema file yet)

Amends [ADR 0014](0014-main-and-research-databases.md): its "crosswalk instead of a shared schema"
is replaced by a shared shape. Keeps [ADR 0002](0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md):
YAML in git stays the master copy; the SQLite file is generated.

The research database's generated SQLite takes the main (LANL) database's shape:

- **LANL core:** the slide's tables, with the slide's table and column names. Each holds only the
  slide's columns, plus `id` and the link columns the slide implies. Link columns and tables the
  slide does not show (for example `kernel_variants`) are guessed, and are listed as guessed.
- **`swdb_` extension:** every table the main database lacks (contracts, libraries, strategies,
  intrinsics, certifications, estimates, the evidence basis) takes the prefix `swdb_`.
- **Drop-ready:** deleting every `swdb_` table leaves a LANL-shaped database that still passes
  SQLite's foreign-key check.
- **Measured only:** LANL's performance tables hold measured results. Estimates and simulated
  numbers stay in `swdb_` tables ([ADR 0013](0013-archevolve-mode-estimates-speed.md)).
- **Unknown is NULL**, never false or zero.

## What stays from ADR 0014

- SWDB never writes LANL's SQLite file. It contributes only through that database's own ingest
  inputs.
- The extension stays separable: LANL tables never depend on a `swdb_` table.
- Each paper result cites a frozen research-database commit.

## What changes

ADR 0014 chose a crosswalk because the main database's schema was unseen. The slide now shows its
table names and key columns, so a shared shape is possible. A merge becomes mostly copying rows.
The crosswalk document stays as written and is no longer the migration plan.

## Considered Options

- **Keep the crosswalk (ADR 0014 as written):** a merge would still need a full redesign of the
  research database at the worst time.
- **Wait for LANL's `schema.sql`:** it may never arrive. The slide's names are enough to start, and
  guessed columns can be checked against the real schema when it does.
- **Rewrite the YAML records to LANL's shape:** breaks ADR 0002 and every record's history.
  Only the generated file changes.

## Consequences

- Raw SQL written for the old table names must use the new ones. This is the one breaking change.
- Integer IDs are regenerated on every build. The stable cross-database key is `kernels.slug`,
  plus a row-origin table that names the YAML record behind each LANL row.
- The slide shows only key columns, so LANL's real tables likely have more. LANL tables here hold
  only the slide's columns, so a later schema only adds columns.
- When LANL's `schema.sql` arrives, compare it with the guessed-column list first.
