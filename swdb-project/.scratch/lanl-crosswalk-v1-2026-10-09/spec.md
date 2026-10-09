# Spec: LANL crosswalk v1 from the `DB_current_work` slide

Created: 2026-10-09 14:01 ET
**Type:** spec
**Status:** wontfix
Superseded 2026-10-09 ET by [the LANL-shaped database spec](../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
**Blocked by:** None
Owner: Yan-Ru Jhou
Decision records: [ADR 0014](../../docs/adr/0014-main-and-research-databases.md) (main and research
databases, crosswalk instead of a shared schema), [ADR 0001](../../docs/adr/0001-kernel-identity-is-its-correctness-check.md)
(kernel identity). Builds on crosswalk v0: [README](../../docs/compatibility/README.md),
[lanl-crosswalk-v0.yaml](../../docs/compatibility/lanl-crosswalk-v0.yaml).
Inputs: the `DB_current_work` slide LANL showed Yan-Ru (transcribed in the appendix); brainstorm
with Yan-Ru on 2026-10-09.
Map and tickets: [map.md](map.md) (5 tickets, published 2026-10-09 14:05 ET)

## Summary (read this first)

1. **What changes:** LANL showed real table names and key columns. Crosswalk v0 only had slide
   labels. v1 records the real names and maps each table to SWDB.
2. **Everything stays `unverified`.** A slide is not LANL's `schema.sql`.
3. **v0 stays frozen.** v1 is a new file with its own format version. Both keep validating.
4. **Two new ideas in the format:** a link column whose target is unknown lists its `candidates`
   (for example `kernel_variant_id`); a mapping states its `cardinality` (one SWDB kernel may be
   many LANL `kernels` rows).
5. **Contracts and libraries join the extension list.** v0 forgot them, and they are the core of
   Yan-Ru's research.

## Problem Statement

Yan-Ru must keep the research database compatible with LANL's main database, so a later merge or a
drop costs little (ADR 0014). Yan-Ru has no access to LANL's database and will not contact LANL.

The only compatibility record today, crosswalk v0, comes from slides 8–9 of the overview deck. It
holds table labels ("Kernel information", "Hardware details") and leaves every SQL name `null`.

LANL has now shown a slide with real table names and key columns. That information exists only in
a screenshot. If it is not recorded, it is lost, and later design work (the extension database for
contracts and libraries) has nothing concrete to link to.

The slide also raises questions the v0 format cannot express:

- `Validation_results.kernel_variant_id` points somewhere, but no table on the slide matches. It
  may point to a `kernels` row, an `executables` row, or a table not shown.
- If every code version is its own `kernels` row, one SWDB kernel corresponds to a group of LANL
  rows. v0 has no way to say "one-to-many".
- v0's extension list names strategies and intrinsics but omits rewrite contracts, library
  operations, lowerings and clauses.

## Solution

A new crosswalk document, v1, beside v0:

- It cites two sources: the overview deck (slides 8–9) and the `DB_current_work` slide.
- It has one mapping row per table on the new slide, and per key column where the mapping is
  meaningful, with the slide's exact SQL tokens as identifiers.
- Link columns with an unknown target list every candidate target; none is chosen.
- Each mapping states its cardinality.
- The extension list adds contracts and libraries, and names LANL's `definitions` and
  `data_structures` as the tables contracts would attach to.

`python -m swdb validate --crosswalk <file>` accepts both v0 and v1, choosing the format by the
document's `crosswalk_version`. Nothing imports, exports or writes LANL data.

## User Stories

1. As Yan-Ru, I want the slide's table names and key columns recorded in the repo, so that the
   information survives after the screenshot is gone.
2. As Yan-Ru, I want each LANL table mapped to SWDB record kinds and fields, so that I can see
   where our data would land in a merge.
3. As Yan-Ru, I want every mapping marked `unverified`, so that nobody reads a slide-based guess as
   a checked fact.
4. As Yan-Ru, I want v0 left unchanged, so that anything already citing v0 still points to the
   same content.
5. As Yan-Ru, I want v0 and v1 both to validate with one command, so that I do not need to
   remember which version needs which tool.
6. As Yan-Ru, I want `kernel_variant_id` recorded with its three candidate targets, so that the
   open question stays visible instead of being silently answered.
7. As Yan-Ru, I want `fixture_id` recorded with its candidate target (`Validation_definition`, or a
   table not shown), so that the same rule applies to every unknown link.
8. As Yan-Ru, I want the kernel mapping to say it may be one-to-many, so that a later import does
   not assume one LANL `kernels` row per SWDB kernel.
9. As Yan-Ru, I want our kernel ID matched to LANL's `slug`, not to their integer `id`, so that the
   link survives a rebuild of their database.
10. As Yan-Ru, I want `performance_runs` mapped only to measured profiles, so that analytic speed
    estimates (ADR 0013) never look like measurements in LANL's tables.
11. As Yan-Ru, I want the crosswalk to note that LANL's metrics carry no measured/estimated marker,
    so that the gap is on record before any export is designed.
12. As Yan-Ru, I want `definitions` and `data_structures` marked as having no SWDB counterpart but
    as the natural anchors for contracts, so that the extension design starts from them.
13. As Yan-Ru, I want rewrite contracts, contract clauses, library operations and lowerings listed
    as extension concepts, so that the contract-and-library research has a place outside LANL's
    schema.
14. As Yan-Ru, I want `code_chunks` and `embeddings` marked as having no counterpart, so that it is
    clear SWDB does not mirror LANL's search layer.
15. As Yan-Ru, I want `kernel_dependencies` and `physics_assets` mapped or marked explicitly, so
    that no slide table is left unmentioned.
16. As Yan-Ru, I want each row to name which source it came from, so that a reader can trace any
    identifier back to the deck or the new slide.
17. As Yan-Ru, I want the source's file name, date and SHA-256 recorded, so that the exact slide
    can be identified later without copying it into the repo.
18. As Yan-Ru, I want the validator to reject a row that cites an undeclared source, so that
    provenance cannot drift.
19. As Yan-Ru, I want the validator to reject `verified` status, so that v1 keeps v0's rule.
20. As Yan-Ru, I want the validator to reject an invented SWDB record kind, so that mappings only
    point to kinds that exist.
21. As Yan-Ru, I want the validator to reject a link column marked unknown with fewer than two
    candidates, so that "unknown" is only used when there is a real choice.
22. As Yan-Ru, I want the validator to reject an unknown cardinality value, so that the field
    stays meaningful.
23. As Yan-Ru, I want a check that v1 names every table on the slide, so that a dropped table is
    caught.
24. As Yan-Ru, I want the compatibility README to explain v1's new fields in plain language, so
    that I can read the crosswalk without opening the schema.
25. As Yan-Ru, I want the slide's inconsistencies (capitalized `Validation_*` names, `fixture_id`
    without a `fixtures` table) recorded as notes, so that they are not "corrected" by guesswork.
26. As a future agent doing the merge, I want the slide's exact tokens kept as written, so that I
    can compare them against LANL's real `schema.sql` line by line.
27. As a future agent designing the extension database, I want the crosswalk to name the LANL keys
    an extension row would join on (`slug`, the variant key), so that the extension can be attached
    or removed without touching LANL's tables.
28. As a future agent, I want the crosswalk to state that SWDB never writes LANL's SQLite file, so
    that ADR 0014's boundary stays explicit.
29. As Scott (advisor), I want the compatibility record to show which parts of the research are
    outside LANL's schema, so that the paper's contribution is clear.
30. As Yan-Ru, I want existing record validation and queries to behave exactly as before, so that
    this change carries no risk to current work.

## Implementation Decisions

- **Separate v1 document and v1 format.** v0's file and format stay byte-for-byte unchanged. v1
  gets its own JSON Schema (Draft 2020-12), with `crosswalk_version: 1` and its own `id`.
- **The validator dispatches on `crosswalk_version`.** Version 0 uses the v0 format, version 1 the
  v1 format; any other value is a validation problem. The public interface (`validate_crosswalk`
  and `python -m swdb validate --crosswalk`) does not change.
- **Sources become a list.** Each source has an `id`, `filename`, `date` and `sha256`, plus the
  slide or page it covers. Each row and each extension concept names one source `id`; the slide
  number moves under the source. This replaces v0's single `source_deck` and its fixed `8 | 9`
  slide enum.
- **The `DB_current_work` source.** Yan-Ru supplies the PowerPoint file's path; its SHA-256 is
  recorded and the file is not copied into the repo (same rule as v0). If Yan-Ru has no file, the
  source is the screenshot, SHA-256
  `34fe355a9654034b42354aab0cafc05405ab3b5365ee4c794af3060d45380fcc`, and the note says so. The
  slide's date is the date LANL showed it, as Yan-Ru states; unknown is recorded as `null`.
- **Identifiers are the slide's tokens, exactly as shown,** including capitalization
  (`Validation_definition`, `Validation_results`). Tokens not on the slide stay `null`.
- **Link targets.** A row for a column that points to another table carries a `link` object:
  either `known` with one target table, or `unknown` with two or more `candidates`. Candidates for
  `kernel_variant_id`: a `kernels` row, an `executables` row, a table not shown. Candidates for
  `fixture_id`: a `Validation_definition` row, a table not shown.
- **Cardinality.** Each `proposed` row states `one_to_one`, `one_to_many`, `many_to_one` or
  `unknown`, read as SWDB-to-LANL. The `kernels` row is `unknown` with a note naming the
  one-to-many possibility.
- **Disposition values stay `proposed` and `no_counterpart`.** `status` stays the constant
  `unverified`.
- **Research targets reuse v0's record-kind list.** Library entries (contracts, operations,
  lowerings) are not research records, so they appear only as extension concepts, not as mapping
  targets.
- **Proposed mapping (all unverified):**

  | LANL table | SWDB counterpart | Cardinality / note |
  |---|---|---|
  | `kernels` | kernel; `slug` ↔ kernel ID | unknown (one-to-many if each version is a row) |
  | `source_files` | source_snapshot files, implementation code | |
  | `executables` | implementation build and run | a `kernel_variant_id` candidate |
  | `definitions` | no counterpart | contract anchor |
  | `data_structures` | no counterpart (access patterns are closest) | contract anchor |
  | `hardware_profiles` | machine | |
  | `run_configs` | workload, input, implementation run; `git_commit` → source_snapshot | |
  | `performance_runs` | profile, measured runs only | estimates excluded |
  | `performance_metrics` | profile metrics | LANL has no measured/estimated marker |
  | `Validation_definition` | input, kernel correctness check | probable `fixture_id` target |
  | `Validation_results` | evaluation, correctness part | `kernel_variant_id` → implementation |
  | `physics_assets` | input (partial) | |
  | `kernel_dependencies` | no counterpart | |
  | `code_chunks`, `embeddings` | no counterpart | LANL's search layer |

- **Extension list.** v1 carries v0's 19 concepts and adds: rewrite contracts, contract clauses
  (with discharge mode and negative control), library operations, lowerings, and contract
  bindings to LANL `definitions`, `data_structures`, kernels and the variant target.
- **Documentation.** The compatibility README gains a v1 section: the two sources, `link`,
  `cardinality`, and the validation command for each version.

## Testing Decisions

- **One seam: the CLI command** `python -m swdb validate --records <dir> --crosswalk <file>`, the
  same seam v0's tests use. Tests write a document to a temp path and assert the exit code and the
  field path in the error output. No test reaches into validator internals.
- **Prior art:** the existing crosswalk tests (draft document → one mutation → expected error).
  v1 tests follow the same pattern.
- **Tests to add:**
  - the committed v1 document validates;
  - the committed v0 document still validates (existing test kept);
  - an unknown `crosswalk_version` is refused;
  - `verified` status is refused in v1;
  - a row citing an undeclared source is refused;
  - an `unknown` link with fewer than two candidates is refused;
  - an unknown cardinality value is refused;
  - an invented research record kind is refused;
  - every table identifier on the slide appears in the v1 document (the expected list is the
    appendix transcription).
- **Regression:** the full existing test suite passes unchanged.

## Out of Scope

- The extension database for contracts and libraries (separate SQLite file joined by `slug` and
  the variant key). It is the next design step and gets its own spec.
- Importing from or exporting to LANL's database (tickets 21–23 of the analytic-evaluator spec are
  wontfix).
- Contacting LANL or choosing a target for `kernel_variant_id` or `fixture_id`.
- Renaming SWDB tables or record fields to match LANL's names.
- Any change to the generated SWDB SQLite schema or to research records.

## Further Notes

- Estimate: about 2–3 hours of agent time, including the format, validator, tests and README.
- The only input needed from Yan-Ru before starting: the PowerPoint path, or "use the screenshot".
- When LANL's `schema.sql` becomes available, a v2 can replace `unverified` row by row; v1's exact
  tokens make that comparison mechanical.

## Appendix: slide transcription

Transcribed 2026-10-09 from Yan-Ru's screenshot of the PowerPoint slide show `DB_current_work`.
Exact tokens as shown.

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
table not on the slide; `Validation_results` uses `fixture_id` with no `fixtures` table shown.
