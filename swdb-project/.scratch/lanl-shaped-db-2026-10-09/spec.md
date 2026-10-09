# Spec: The research database takes LANL's shape

Created: 2026-10-09 14:15 ET
**Type:** spec
**Status:** ready-for-agent (implementation starts only on Yan-Ru's explicit go-ahead)
**Blocked by:** None
Owner: Yan-Ru Jhou
Supersedes: [lanl-crosswalk-v1 spec](../lanl-crosswalk-v1-2026-10-09/spec.md) (wontfix; it only
wrote a mapping document).
Decision records: amends [ADR 0014](../../docs/adr/0014-main-and-research-databases.md) (a new ADR
0015 is part of this work); keeps [ADR 0002](../../docs/adr/0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md)
and [ADR 0013](../../docs/adr/0013-archevolve-mode-estimates-speed.md).
Map and tickets: [map.md](map.md) (7 tickets, published 2026-10-09 14:19 ET)
Inputs: the `DB_current_work` slide LANL showed Yan-Ru (transcribed in the appendix); brainstorm
with Yan-Ru on 2026-10-09, where Yan-Ru approved decisions D1–D4 below.

## Summary (read this first)

1. **What changes:** the SQLite file that `swdb build` generates gets LANL's tables, with LANL's
   names and columns, as its core. Everything SWDB has that LANL lacks moves to tables prefixed
   `swdb_`.
2. **What does not change:** the YAML records in git stay the master copy and keep their format.
   No record is rewritten.
3. **LANL tables hold only the columns on the slide.** Anything extra lives in `swdb_` tables keyed
   by the LANL row.
4. **Drop-ready:** deleting every `swdb_` table leaves a database in LANL's shape that still passes
   SQLite's foreign-key check.
5. **Speed estimates never enter LANL's performance tables.** Only measured results do.
6. **Contracts and libraries** become `swdb_` tables that link to LANL's `definitions`,
   `data_structures`, `kernels` and `kernel_variants`.

## Problem Statement

LANL's SQLite database is ArchEvolve's main database. Yan-Ru's research database (SWDB) may later
merge into it. Today SWDB's generated SQLite file uses its own table names and layout (`kernels`
with text IDs, `implementations`, `profiles`, `metrics`, …), so a merge would mean a full
redesign at the worst possible time.

LANL has now shown its table names and key columns on a slide. Yan-Ru has no access to LANL's
database and will not contact LANL, but wants SWDB's database to already have LANL's shape, so
that a later merge is mostly copying rows.

Yan-Ru's research (contracts and libraries) has no place in LANL's schema. It must be added as an
extension that LANL's tables do not depend on, so it can be merged in or dropped.

## Solution

`swdb build` produces one SQLite file with two parts:

- **LANL core:** the 16 tables on the slide, with the slide's table and column names, integer
  `id`s, and declared foreign keys. They are filled from the YAML records where SWDB has matching
  data, and are left empty where it does not (for example `embeddings`).
- **SWDB extension:** every SWDB-only table, prefixed `swdb_`. This includes today's tables
  (renamed), the full JSON of each record, contracts, clauses, library entries, strategies,
  intrinsics, estimates, and a table that records which YAML record produced each LANL row.

Every existing `swdb` query command (`find`, `implementations`, `strategies`, `compare`, the site
finder, and record lookups) gives the same results as before. Raw SQL written for the old table
names must be updated; that is the one breaking change.

## User Stories

1. As Yan-Ru, I want my generated database to contain LANL's tables with LANL's names, so that a
   later merge is mostly copying rows.
2. As Yan-Ru, I want my YAML records left unchanged, so that the master copy and its history are
   not touched by this migration.
3. As Yan-Ru, I want LANL tables to hold only the slide's columns, so that I never add a column
   LANL might define differently.
4. As Yan-Ru, I want every SWDB-only table prefixed `swdb_`, so that I can tell at a glance what
   LANL has and what I added.
5. As Yan-Ru, I want to delete all `swdb_` tables and still have a valid LANL-shaped database, so
   that the extension is truly separable.
6. As Yan-Ru, I want my kernel IDs stored in `kernels.slug`, so that the stable name survives even
   though integer IDs are regenerated on every build.
7. As Yan-Ru, I want to look up which YAML record produced any LANL row, so that every row traces
   back to the master copy.
8. As Yan-Ru, I want each implementation to appear as a row in `kernel_variants`, so that
   `Validation_results.kernel_variant_id` has something real to point to.
9. As Yan-Ru, I want `kernel_variants` clearly marked as a guessed LANL table, so that nobody
   mistakes it for something LANL showed.
10. As Yan-Ru, I want only measured results in `performance_runs` and `performance_metrics`, so
    that analytic estimates never look like measurements.
11. As Yan-Ru, I want simulated metrics (for example cachegrind) kept out of LANL's performance
    tables, so that LANL's "hardware counters" table only holds real-machine numbers.
12. As Yan-Ru, I want estimates in a `swdb_estimates` table linked to the kernel variant, so that
    my analytic results stay queryable next to the LANL rows.
13. As Yan-Ru, I want machine records in `hardware_profiles`, so that the hosts I measured on
    appear in LANL's form.
14. As Yan-Ru, I want accelerator targets kept out of `hardware_profiles`, so that a modeled DX100
    is not presented as a system LANL can run on.
15. As Yan-Ru, I want `run_configs` filled from what my measured profiles ran with, so that each
    performance run names its parameters and git commit.
16. As Yan-Ru, I want source snapshot files and implementation code in `source_files`, so that
    LANL's source inventory includes my code.
17. As Yan-Ru, I want implementation builds in `executables`, so that my benchmark programs appear
    where LANL keeps theirs.
18. As Yan-Ru, I want the functions my records name in `definitions`, so that contracts can attach
    to them.
19. As Yan-Ru, I want the arrays my access patterns name in `data_structures`, so that contracts
    can attach to the data they constrain.
20. As Yan-Ru, I want correctness checks in `Validation_definition` and correctness outcomes in
    `Validation_results`, so that my correctness evidence appears in LANL's form.
21. As Yan-Ru, I want unknown values stored as NULL, never as false or zero, so that "unknown is
    not false" survives the migration.
22. As Yan-Ru, I want `physics_assets`, `kernel_dependencies`, `code_chunks` and `embeddings`
    created with the slide's columns even when empty, so that the database has LANL's full shape.
23. As Yan-Ru, I want contracts, clauses and library entries in `swdb_` tables, so that my
    research has a home outside LANL's schema.
24. As Yan-Ru, I want typed link tables from contracts to `definitions`, `data_structures`,
    `kernels` and `kernel_variants`, so that each contract says what it applies to.
25. As Yan-Ru, I want contract links filled only from links my records already state, so that the
    migration invents no new claims.
26. As Yan-Ru, I want every existing query command to give the same results as before, so that my
    current work and campaigns keep running.
27. As Yan-Ru, I want the site finder to keep finding the same sites, so that rewrite campaigns are
    unaffected.
28. As Yan-Ru, I want the database to pass SQLite's foreign-key check, so that links are known to
    be consistent.
29. As Yan-Ru, I want columns not on the slide but needed for links (for example the run-to-config
    link) listed as guessed, so that I know which names to check against LANL's real schema.
30. As Yan-Ru, I want the slide's exact capitalization kept (`Validation_definition`,
    `Validation_results`), so that names compare one-to-one with LANL's.
31. As Yan-Ru, I want the database reference document rewritten for the new layout, so that I can
    read the tables without opening code.
32. As Yan-Ru, I want an ADR recording that SWDB now takes LANL's shape, so that the reversal of
    ADR 0014's "crosswalk, not a shared schema" is on record.
33. As Yan-Ru, I want raw SQL in scripts and docs updated to the new names, so that nothing in the
    repo silently breaks.
34. As Yan-Ru, I want a build to stay about as fast as today (around a second), so that query
    commands stay responsive.
35. As a future agent merging into LANL's database, I want the slide-versus-guessed status of each
    column on record, so that I know what to check against LANL's `schema.sql` first.
36. As a future agent, I want the extension's join keys (`slug`, and the row-origin table) to be
    the only links between SWDB data and LANL rows, so that the extension can be moved or removed
    without editing LANL tables.
37. As Scott (advisor), I want the `swdb_` tables to show exactly what the research adds beyond
    LANL's schema, so that the paper's contribution is visible in the database itself.

## Implementation Decisions

### Approved by Yan-Ru on 2026-10-09

- **D1 — Migrate the generated SQLite only.** YAML stays the master copy (ADR 0002); record
  formats, record files and their validation do not change.
- **D2 — IDs.** Every LANL table gets an integer `id` primary key, assigned at build time in a
  deterministic order. `kernels.slug` holds the SWDB kernel ID. Integer IDs are build-local; the
  stable cross-database key is `slug`, plus the row-origin table for rows without a slug.
- **D3 — `kernel_variants`.** One row per implementation. Columns: `id`, `kernel_id`, `slug` (the
  implementation ID). It is unprefixed because it fills the slot `kernel_variant_id` implies, and
  is marked guessed. It is the only LANL-side table that is not on the slide.
- **D4 — Estimates stay out of LANL's performance tables.** They go to `swdb_estimates`, linked to
  `kernel_variants`.
- **D5 — ADR.** A new ADR 0015 (status proposed) records that the research database takes the main
  database's shape and amends ADR 0014's "crosswalk instead of a shared schema". ADR 0014's other
  rules stay: SWDB never writes LANL's file; the extension stays separable; paper results cite a
  frozen research-database commit.

### Layout rules

- **LANL tables use the slide's names exactly**, including capitalization, and contain only the
  slide's columns plus `id` and the link columns below.
- **Guessed link columns** follow the slide's naming pattern (`<table singular>_id`):
  `performance_runs.hardware_profile_id`, `performance_runs.run_config_id`,
  `performance_runs.kernel_variant_id`, `performance_metrics.performance_run_id`,
  `run_configs.kernel_variant_id`, and `Validation_results.fixture_id` linking to
  `Validation_definition.id`. The slide gives no column names for the search tables, so they are
  guessed too: `code_chunks` (`id`, `source_file_id`, `line_start`, `line_end`, `content`) and
  `embeddings` (`id`, `code_chunk_id`, `vector`). Each guessed column, and the `kernel_variants` table, is listed
  in a `swdb_guessed_columns` table (table, column, reason) and in the reference document.
- **Every SWDB-only table is prefixed `swdb_`**, including today's tables (`meta`, `records`,
  `kernels`, `implementations`, `profiles`, `metrics`, `access_patterns`, `steps`, `strategies`,
  `intrinsics`, `library_*`, `statements`, …). Their columns and contents do not change, only
  their names.
- **Row origins.** `swdb_row_origins` (table name, row id, record id, record field) names the YAML
  record behind every LANL row.
- **Foreign keys** are declared on every link and checked at the end of each build.
- **Unknown is NULL.** A value whose basis is unknown, or that SWDB does not record, is NULL.

### What fills each LANL table

| LANL table | Filled from | Rule |
|---|---|---|
| `kernels` | kernel records | `slug` = kernel ID; `category` = application domain when stated, else NULL |
| `kernel_variants` | implementation records | one row per implementation |
| `source_files` | source snapshot files; implementation code paths | `language` from the application when stated |
| `executables` | implementation build | one per built program the record names |
| `definitions` | functions named by implementations and statements | `kind` = `function`; only functions records name |
| `data_structures` | arrays named by access-pattern steps | only arrays records name |
| `hardware_profiles` | machine records | real machines only; hardware targets excluded |
| `run_configs` | measured profiles | `parameters_json` from the run and input; `git_commit` from the source revision |
| `performance_runs` | profiles with measured timing | measured only; estimated and simulated excluded |
| `performance_metrics` | profile metrics with basis `measured` | other bases stay in `swdb_metrics` |
| `Validation_definition` | kernel correctness check × input | `expected_output_json` NULL when not recorded |
| `Validation_results` | correctness outcomes of profiles and evaluations | `max_abs_error` NULL when not recorded |
| `physics_assets`, `kernel_dependencies`, `code_chunks`, `embeddings` | nothing yet | created empty with the slide's columns |

### Extension for contracts and libraries

- Library entries, dependencies, clauses and pattern keys move to `swdb_` tables unchanged.
- New typed link tables: `swdb_contract_definitions`, `swdb_contract_data_structures`,
  `swdb_contract_kernels`, `swdb_contract_kernel_variants`. They are filled only from links the
  records already state (for example a contract applied by an implementation, or a clause tied to
  a statement's function). No new inference.

### Interfaces

- `swdb build` and every query command keep their arguments and output.
- The builder version changes, so older database files are rebuilt automatically on first use
  (existing staleness rule).
- `swdb sql` is unchanged; queries written for the old names must use the new ones. Raw SQL in
  scripts, tools and docs inside `swdb-project/` is updated in the same work.

## Testing Decisions

- **A good test** builds a database from a small records folder through the CLI and checks what a
  user can see: the tables, their columns, query output, and SQLite checks. No test reads builder
  internals.
- **Seam:** `swdb build` followed by `swdb sql` and the existing query commands — the same seam the
  database tests already use. No new seam.
- **Prior art:** the existing database, query-index, library-index, strategy and site-finder tests,
  which build from fixture records and assert on command output.
- **Tests to add:**
  - shape: every slide table exists with exactly the slide's columns plus `id` and the listed
    guessed columns (the expected list is the appendix transcription);
  - separability: after deleting every `swdb_` table, `PRAGMA foreign_key_check` is clean;
  - integrity: a normal build passes `PRAGMA foreign_key_check`;
  - origins: every LANL row has a `swdb_row_origins` entry naming an existing record;
  - estimates: a records folder with an estimate and a measured profile puts only the measured one
    in `performance_runs`;
  - simulated metrics (cachegrind) never appear in `performance_metrics`;
  - unknown values are NULL;
  - `kernels.slug` equals the kernel ID; one `kernel_variants` row per implementation;
  - contract links appear only where records state the link.
- **Regression:** the full existing test suite passes. Query-command tests are updated only for
  table names inside raw SQL, never for their expected results.

## Out of Scope

- Changing YAML record formats or rewriting records.
- Importing from or exporting to LANL's real database; contacting LANL.
- Filling `code_chunks` and `embeddings` (LANL's search layer).
- Choosing LANL's real target for `kernel_variant_id`; D3 is the working guess.
- Crosswalk v1. The v0 crosswalk document stays as it is; this spec's appendix is the record of
  the slide.

## Further Notes

- **Estimate:** about 1–2 days of agent time after approval, split into tickets.
- **Suggested order:** (1) rename every current table to `swdb_` with no behavior change; (2) a
  thin end-to-end slice: `kernels` + `kernel_variants` + row origins + shape and separability
  tests; (3) source tables; (4) hardware and performance tables; (5) validation tables and the
  empty tables; (6) contract link tables; (7) ADR 0015 and the reference document.
- **Risk:** the slide shows only key columns. LANL's real tables likely have more. Because LANL
  tables here hold only slide columns, a later schema only adds columns; nothing needs removing.
- **When LANL's `schema.sql` arrives:** compare it against `swdb_guessed_columns` first.

## Appendix: slide transcription

Transcribed 2026-10-09 from Yan-Ru's screenshot of the PowerPoint slide show `DB_current_work`
(screenshot SHA-256 `34fe355a9654034b42354aab0cafc05405ab3b5365ee4c794af3060d45380fcc`; not copied
into the repo). Exact tokens as shown.

**Source code tables** (columns: table name, purpose, key columns, row count type)

| Table | Purpose | Key columns | Row count type |
|---|---|---|---|
| kernels | Kernel definitions | id, slug, name, category | Total # of kernels |
| source_files | Source code inventory | id, kernel_id, path, language | Multiple per kernel |
| executables | Benchmark programs | id, kernel_id, name, kind, path | Multiple per kernel |
| definitions | Code symbols (functions/classes) | id, source_file_id, name, kind | Multiple per file |
| data_structures | Kernel data structures | id, kernel_id, name, kind | Multiple per kernel |

**Performance and correctness tables** (columns: table name, purpose, key metrics, relationships)

| Table | Purpose | Key metrics | Relationships |
|---|---|---|---|
| hardware_profiles | System specifications | cpu_model, cores, memory_gb | → performance_runs |
| run_configs | Parameter combinations | label, parameters_json, git_commit | → performance_runs |
| performance_runs | Benchmark execution | elapsed_seconds, throughput_value | → performance_metrics |
| performance_metrics | Hardware counters | metric_name, metric_value | Linked to runs |
| Validation_definition | Test case definitions | kernel_id, name, input_json, expected_output_json | -> correctness_runs |
| Validation_results | Test execution results | fixture_id, kernel_variant_id, passed, max_abs_error | Links fixtures to variants |

**Unlabeled group** (same columns; relationships empty)

| Table | Purpose | Key metrics |
|---|---|---|
| physics_assets | Physics parameters & data | kernel_id, asset_type, name, format |
| kernel_dependencies | Kernel relationships | kernel_id, depends_on_kernel_id, dependency_type |

**Semantic search tables** (columns: table name, purpose, data type, size/format)

| Table | Purpose | Data type | Size/format |
|---|---|---|---|
| code_chunks | Code segments for embedding | TEXT | Variable (line_start to line_end) |
| embeddings | Vector representations | BLOB | 768 dimensions (float32) |

Slide inconsistencies kept as written: `Validation_definition` relates to `correctness_runs`, a
table not on the slide; `Validation_results` uses `fixture_id` with no `fixtures` table shown. In
this database, `fixture_id` links to `Validation_definition.id` and is listed as guessed.
