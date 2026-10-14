# The SQLite database

Updated: 2026-10-14 ET: proof-record tables (Probata proof of concept ticket 04); skip records and `skip_reason` (ticket 11);
derived-implementation tables (ticket 19).
2026-10-14 02:57 ET: `swdb_proof_jobs`, `swdb_run_fields`, `swdb_repair_lineage` (ticket 12).
2026-10-12 00:36 ET: attribution final review fixes (headroom reasons point to one list,
split-check rule v2 and its estimated share). 2026-10-11 23:28 ET: measured native evaluation timings of an implementation feed
`performance_runs` (LANL-shaped-db follow-up ticket 03). 2026-10-11 23:24 ET: attribution tables
listed in the `swdb_` extension groups. 2026-10-11 22:07 ET: LANL-shaped-db review fixes (record-field path syntax, which
evaluations reach `Validation_results`, `swdb_estimates.base_kernel_variant_id`). 2026-10-11 21:50 ET:
rewritten for the LANL-shaped layout
([ADR 0015](../adr/0015-research-database-takes-the-main-database-shape.md), LANL-shaped-db
tickets 01–07). Earlier updates: 2026-09-28 navigation; 2026-10-03 typed library and statements;
2026-10-04 site-finder facts and pattern keys; 2026-10-06 access interface; 2026-10-07
evidence basis.

## At a glance

The generated file has two parts:

| Part | Tables | What it is |
|---|---|---|
| [LANL core](#lanl-core) | 16 unprefixed tables | LANL's tables, names and columns from the `DB_current_work` slide (15 tables), plus the guessed `kernel_variants` |
| [`swdb_` extension](#the-swdb_-extension) | every `swdb_` table | everything SWDB has that LANL lacks: full records, research tables, library, contracts, estimates, row origins |

Five rules hold for the whole file:

1. **YAML is the master copy** ([ADR 0002](../adr/0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md)).
   The file is regenerated; no record is rewritten for it.
2. **LANL tables hold only the slide's columns**, plus `id` and link columns. Columns the slide
   does not show are [guessed](#guessed-columns) and listed in `swdb_guessed_columns`.
3. **Measured only.** LANL's performance tables hold real-machine measurements. Estimates and
   simulated numbers stay in `swdb_` tables ([details](#measured-only)).
4. **Unknown is NULL**, never false or zero.
5. **Drop-ready.** No LANL table points at a `swdb_` table. [Delete every `swdb_`
   table](#dropping-the-extension) and you have a LANL-shaped database that passes
   `PRAGMA foreign_key_check`.

Raw SQL written before 2026-10-11 must use the new names (`profiles` → `swdb_profiles`, …).

## Building and reading the file

Updated: 2026-10-11 (Eastern Time): attribution catalog bounds and full ranking (fine-grained attribution ticket 08).
Updated: 2026-10-11 21:17 ET: attribution split-check tables (fine-grained attribution ticket 09).

Updated: 2026-10-11 21:31 ET: site-finder lookup tables (fine-grained attribution ticket 10).

Run commands inside `ArchEvolve/swdb-project/`. [The database builder](../../swdb/db.py)
writes `build/swdb.sqlite` beside `records/` by default (another records folder
`X` gets `build/swdb-X.sqlite`). It recreates every table in a temporary file,
then replaces the selected index. YAML remains authoritative (ADR 0002).
The `swdb_meta` table names the records folder and a fingerprint of its files (path,
size, and modification time of each); `swdb find`, `swdb implementations`, `swdb strategies`, and `swdb sql`
rebuild the file first unless the folder and the fingerprint match the folder being queried
and the file was built by the same `swdb` code (so a newer `swdb` never queries a file that
lacks its tables or fills them differently).

The BFS queries (`capabilities`, `bfs-hotspots`, `profile-strategies`,
`strategy-regions`, `bfs-coverage`, and `get`) use the selected `--db` path, or
its normal default. They validate the YAML records, refresh a stale index, then
load one SQLite record snapshot. `get --chain` resolves its root, ancestors and
descendants from that same snapshot. Changes made after the snapshot are visible
on the next query. Raw source, profile and evaluation artifacts are still checked
at query time; a fresh metadata index does not make changed or missing raw evidence
valid.

Record loading uses PyYAML's safe LibYAML parser when that optional extension is
installed, with the Python safe parser as a fallback. Both preserve dates as text
and reject repeated mapping keys; neither constructs Python objects from YAML.
[The access layer](../../swdb/access.py) caches unchanged files' JSON text within one
process, keyed by inode, size, modification time, and change time. Each load
returns fresh objects; records that change during parsing or cannot round-trip
through JSON are not cached. [Cache tests](../../tests/test_store_parse_cache.py)
check rereads and mutation isolation. Validation, write locks, and index
freshness checks still apply.

Run your own SQL with `swdb sql "<query>" [--format json]`, or open the file with the
`sqlite3` shell. Values that are JSON in the records (semantic values, property values)
are stored as JSON text, so `true`, `false`, and `null` stay distinct: compare with
`= 'true'`, `= 'false'`, or `= 'null'`, and check the matching `_basis` column
(`unknown` never means false).

## Record and query access interface

[`swdb.access`](../../swdb/access.py) is the I/O boundary shared by the
[record store](../../swdb/store.py), database queries, and the site finder. The
store keeps ID lookup and reference resolution; query modules keep their SQL and
result formatting. Record imports, candidate-record binding, and campaign export
also use this boundary.

| Function | Contract |
|---|---|
| `record_files(records_dir)` | Sorted `(absolute or caller-relative path, relative record path)` pairs for visible YAML files; hidden files and directories are skipped. |
| `read_record(path)` | Safe YAML data, or JSON data for a `.json` file, as a fresh object; unchanged files may use the process cache. A key repeated in one mapping refuses in both formats. YAML, JSON (`ValueError`) and I/O errors propagate to the caller's existing diagnostics. |
| `read_record_bytes(path)`, `record_hash(path)` | Exact source bytes and their SHA-256 for byte-preserving export; no YAML normalization. |
| `open_index(db_path)` | Read-only query session with dictionary-addressable rows; the caller closes it after the snapshot. A missing file is not created. Filenames are URI-encoded before opening. |
| `query(db_path, statement, parameters=())` | One SQL result as dictionaries, with positional or named bound parameters; the session always closes. |
| `create_index(db_path)` | Writable connection used only by the builder for its temporary generated research index. |

The existing `Store`, `db.sql`, `db.query_store`, and query-command signatures stay
available. `store.record_files` delegates to the same boundary, and `db.sqlite3`
remains available to callers that catch its errors. Validation, freshness checks,
and snapshot assembly keep their existing order. Only this access layer opens
the generated database.

A future main-database adapter belongs behind this interface (ADR 0014). It must
preserve record IDs, safe read behavior, snapshot lifetime, and the documented
research query relations. Since ADR 0015 the generated file already has the main
database's table shape (the [LANL core](#lanl-core)); the main database's full
schema is still unseen, so the guessed columns stay unverified. Contributions to
the main database must use its ingest inputs, and `create_index` must never open
the main database for writing.

## LANL core

LANL's tables, with LANL's names (capitalization kept: `Validation_definition`,
`Validation_results`) and only the columns LANL's `DB_current_work` slide shows. The slide is
transcribed in the [LANL-shaped-db spec](../../.scratch/lanl-shaped-db-2026-10-09/spec.md)
appendix.

- **Integer IDs.** Every LANL table has an `id` primary key, assigned at build time in record-ID
  order. IDs change between builds. The stable keys are `kernels.slug`, `kernel_variants.slug`,
  and `swdb_row_origins`.
- **Every row has an origin.** `swdb_row_origins` names the YAML record (and field) behind each
  LANL row.
- **Checked.** Foreign keys are declared, and every build fails if
  `PRAGMA foreign_key_check` reports a row.
- **Code.** Each table group is one module `swdb/lanl_<group>.py`; [`swdb/lanl.py`](../../swdb/lanl.py)
  runs them in order. Shape test: [`tests/test_lanl_shape.py`](../../tests/test_lanl_shape.py).

| Table | Slide group | Filled from | Code |
|---|---|---|---|
| `kernels` | source code | kernel records | `lanl_kernels.py` |
| `kernel_variants` | guessed (not on the slide) | implementation records | `lanl_kernels.py` |
| `source_files` | source code | implementation code, statement sources, source snapshot files | `lanl_sources.py` |
| `executables` | source code | implementation builds | `lanl_sources.py` |
| `definitions` | source code | functions records name | `lanl_sources.py` |
| `data_structures` | source code | arrays access-pattern steps name | `lanl_sources.py` |
| `hardware_profiles` | performance | machine records (never hardware targets) | `lanl_performance.py` |
| `run_configs` | performance | what measured profiles and evaluations ran with | `lanl_performance.py` |
| `performance_runs` | performance | measured profile timings and measured native evaluation timings | `lanl_performance.py` |
| `performance_metrics` | performance | profile metrics with basis `measured` | `lanl_performance.py` |
| `Validation_definition` | correctness | kernel check × input that an outcome ran | `lanl_validation.py` |
| `Validation_results` | correctness | correctness outcomes of profiles and evaluations | `lanl_validation.py` |
| `physics_assets`, `kernel_dependencies` | unlabeled | nothing yet: empty | `lanl_validation.py` |
| `code_chunks`, `embeddings` | semantic search | nothing yet: empty | `lanl_validation.py` |

### Measured only

LANL's performance tables (`performance_runs`, `performance_metrics`) hold only measurements
on real machines:

- **Analytic estimates** go to [`swdb_estimates`](#swdb_estimates) (spec D4, [ADR 0013](../adr/0013-archevolve-mode-estimates-speed.md)).
- **Simulated metrics** (cachegrind), inferred and unknown ones stay in `swdb_metrics`.
- **Simulated timings** (an evaluation's gem5 `timing[]` entries, basis `simulated`) and
  contract-fixture timings stay in the evaluation record ([ADR 0013](../adr/0013-archevolve-mode-estimates-speed.md)).
- **Hardware targets** (a modeled DX100) are not machines, so they never become
  `hardware_profiles` rows.

### Unknown is NULL

A value the records do not state, or whose basis is unknown, is NULL. It is never `0`,
`false`, or a default. Examples: `kernels.category` without a stated domain,
`executables.path`, `performance_runs.throughput_value`, `Validation_results.passed` for an
outcome whose correctness was not established.

### `kernels`

One row per kernel record.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `slug` | the SWDB kernel ID, for example `gapbs-bfs` |
| `name` | kernel name |
| `category` | the domain of the kernel's application (vocabulary `domains`), or NULL when not stated |

### `kernel_variants`

Guessed: not on the slide (spec D3). One row per implementation record; it fills the slot
that `Validation_results.kernel_variant_id` implies. All its columns are listed in
`swdb_guessed_columns`.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `kernel_id` | the implementation's kernel (`kernels.id`) |
| `slug` | the SWDB implementation ID, for example `gapbs-bfs-do` |

### Source tables

Only what records name; no column is guessed. Code:
[`swdb/lanl_sources.py`](../../swdb/lanl_sources.py).

#### `source_files`

One row per (kernel, path). A file several records name has one origin per mention.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `kernel_id` | the kernel (`kernels.id`) of the implementation that names the file |
| `path` | implementation code and statement sources: `<application source.local_path>/<path>` (for example `apps/gapbs/src/bfs.cc`), or `records/<path>` for code kept beside its record. Source snapshot files: `<artifact.path>/<path>`, the retained tree the snapshot record names |
| `language` | the application's `language`, only for files a record names as code (implementation `code`, statement sources, a snapshot's `context.code`); NULL for other retained files (LICENSE, Makefile, inputs) and when the application states none |

#### `executables`

One row per implementation build. The record names a program (`-o {binary}`) but no binary
file.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `kernel_id` | the implementation's kernel (`kernels.id`) |
| `name` | the implementation ID, the program's only stated name |
| `kind` | NULL: no record classifies its program |
| `path` | NULL: the binary's location depends on each run |

#### `definitions`

Functions records name: an implementation's `function` and `run.kernel_symbols`, its
statements' `function`, and each `kind: function` region of a source snapshot. One row per
(source file, name).

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `source_file_id` | the file (`source_files.id`) a record places it in: `code[0]` for the implementation's `function` (the format puts the kernel function there), the statements' source file, or the snapshot region's file. NULL when no record states the file (most other kernel symbols); such a row is kept per record |
| `name` | the function name |
| `kind` | always `function` |

#### `data_structures`

Arrays named by implementation access-pattern steps, one row per (kernel, array name).

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `kernel_id` | the implementation's kernel (`kernels.id`) |
| `name` | the array name, for example `g.in_index_` |
| `kind` | the stated `layout` (vocabulary `layouts`); NULL when it is `unknown` or records disagree |

### Hardware and performance tables

[Measured only](#measured-only). Code: [`swdb/lanl_performance.py`](../../swdb/lanl_performance.py).

#### `hardware_profiles`

One row per machine record.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `cpu_model` | `cpu.model` |
| `cores` | physical cores: `cpu.sockets` × `cpu.cores_per_socket` (not hyperthreads) |
| `memory_gb` | `memory_bytes` in GiB (2^30 bytes), unrounded |

#### `run_configs`

What a measured run ran with. Runs with identical parameters, commit and variant share one row,
with one origin per run.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `label` | `<implementation> on <input>, <threads> threads` (a name, not a key) |
| `parameters_json` | JSON. From a profile: `input`, `input_arguments` (the input's generator arguments), `threads`, `trials`, `compiler`, `compiler_version`, `flags`, `omp_places`, `omp_proc_bind`, `binding`. From an evaluation: `input` (the workload ID), `threads`, `trials` (measured trials), `sources`, `repetitions`, `roi`, `compiler`, `compiler_version`, `flags`, `omp_places`, `omp_proc_bind` (from `build.execution_environment`), `lane`. Null where the record does not say |
| `git_commit` | the application's source revision (a profile's `build.application_commit`, an evaluation's `context.source_revision`), or NULL |
| `kernel_variant_id` | guessed link: the profiled or evaluated implementation (`kernel_variants.id`) |

#### `performance_runs`

One row per `timing[]` entry of a profile: one benchmark process at one thread count.

Also one row per evaluation whose timings are a measured native run of an implementation.
Its origins name each trial (`timing[<i>]`) it summarizes. An evaluation counts only when all
of these hold:

- **What ran is an implementation**: the same rule as [`Validation_results`](#validation-tables-and-the-empty-tables)
  (unchanged `source_baseline` candidate, or no candidate). A rewrite candidate's timings never count.
- **Real machine**: its `machine` is a machine record (so a `hardware_profiles` row).
- **Measured native trials**: `timing[]` entries with basis `measured`, quantity
  `native_roi_wall_seconds` and evidence kind `execution`. gem5 (`simulated`) and
  contract-fixture entries never count.
- **Finished**: `outcome.state` is `complete`.
- **Not an aggregate**: an aggregate (`component_evaluations`) repeats its components' trials.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `elapsed_seconds` | median time per trial: a profile entry's `median_s`; for an evaluation, the median `duration_s` of its measured trials (all sources and repetitions; equals `summary.median_roi_seconds`). Min, max and spread stay in the record |
| `throughput_value` | NULL: no record states a throughput |
| `hardware_profile_id` | guessed link: the profile's or evaluation's machine (`hardware_profiles.id`) |
| `run_config_id` | guessed link: `run_configs.id` |
| `kernel_variant_id` | guessed link: the profiled or evaluated implementation (`kernel_variants.id`) |

#### `performance_metrics`

One row per profile metric with basis `measured`, a numeric value, and a thread count that
names exactly one run of the profile. Histograms and metrics without a thread count (host load,
index features of the input) stay in `swdb_metrics` only.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `metric_name` | metric name (vocabulary `metrics`) |
| `metric_value` | the measured value |
| `performance_run_id` | guessed link: the run at the metric's thread count (`performance_runs.id`) |

### Validation tables and the empty tables

Code: [`swdb/lanl_validation.py`](../../swdb/lanl_validation.py). The two validation tables
keep the slide's capitalization.

**Which outcomes count.** A correctness outcome is a profile's `correctness` part or an
evaluation's `correctness.state`. It becomes a `Validation_results` row only when what ran is an
implementation (the kernel variant) and it names an input record:

- **What ran.** A profile runs its `implementation`. An evaluation runs the candidate its
  `request.candidate` names (an aggregate, which has none, names it as `candidate`). That is an implementation only when the candidate is the
  implementation's unchanged source (`artifact_role: source_baseline`). An evaluation of a
  rewrite candidate gets no row, even though its record names the baseline as
  `implementation`: the rewrite's outcome is not the baseline's. It stays in the `swdb_` tables.
- **Input.** A profile's `input`, or the `workload` record an evaluation's `request.workload.id`
  names (`request.workload` when it is a bare ID).

Outcomes missing either (for example the dx100 smoke evaluations, which name no implementation)
have no row.

#### `Validation_definition`

One test case per (kernel, input) pair that at least one correctness outcome ran: the kernel's
`correctness_check` with that input. Pairs no outcome ran are not listed. Origins: the kernel
(`correctness_check`), the input (`generator` or `definition`), and each profile or evaluation
that ran the pair.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local), in `name` order |
| `kernel_id` | the kernel of the outcome's implementation (`kernels.id`) |
| `name` | `<kernel ID>/<input ID>`, for example `gapbs-bfs/kron-g16-k16` |
| `input_json` | an input record's `generator`, or a workload record's `definition`, as JSON; NULL when the record has none |
| `expected_output_json` | always NULL: no record states an expected output (checks are verifiers, not reference outputs) |

#### `Validation_results`

One row per counted correctness outcome. Origin: the profile (`parts[<n>].outcome`) or
evaluation (`correctness.state`).

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local), in record-ID order |
| `fixture_id` | guessed: the test case (`Validation_definition.id`); the slide shows no fixtures table |
| `kernel_variant_id` | the implementation that ran (`kernel_variants.id`) |
| `passed` | 1 for a profile check `complete` or an evaluation `passed`; 0 for an evaluation `failed`; NULL when correctness was not established (a profile check that timed out, an evaluation `unverified`). Never 0 for unknown |
| `max_abs_error` | always NULL: no record states one |

#### Tables with nothing to fill yet

Created empty with the slide's columns so the database has LANL's full shape. The slide gives
no column names for the search tables (`code_chunks`, `embeddings`); all their columns are
guessed and listed in `swdb_guessed_columns`.

| Table | Columns |
|---|---|
| `physics_assets` | `id`, `kernel_id` (`kernels.id`), `asset_type`, `name`, `format` |
| `kernel_dependencies` | `id`, `kernel_id` and `depends_on_kernel_id` (both `kernels.id`), `dependency_type` |
| `code_chunks` | `id`, `source_file_id` (`source_files.id`), `line_start`, `line_end`, `content` (text) |
| `embeddings` | `id`, `code_chunk_id` (`code_chunks.id`), `vector` (BLOB; the slide says 768 float32 dimensions) |

## Guessed columns

The slide shows table names and key columns only. Where a link needs a column the slide does
not show, or the slide gives no column names, the column is a guess. Each guess is a row of
[`swdb_guessed_columns`](#swdb_guessed_columns), with its reason. When LANL's `schema.sql`
arrives, check these first.

| Table | Guessed | Why |
|---|---|---|
| `kernel_variants` | the whole table: `id`, `kernel_id`, `slug` | not on the slide; fills the slot `Validation_results.kernel_variant_id` implies (spec D3) |
| `run_configs` | `kernel_variant_id` | link column, named by the slide's `<table singular>_id` pattern |
| `performance_runs` | `hardware_profile_id`, `run_config_id`, `kernel_variant_id` | link columns, same pattern |
| `performance_metrics` | `performance_run_id` | link column, same pattern |
| `Validation_results` | `fixture_id` (its target) | on the slide, but no fixtures table is shown; here it links to `Validation_definition.id` |
| `code_chunks` | every column | the slide gives only a data type (TEXT) and a size (line_start to line_end) |
| `embeddings` | every column | the slide gives only a data type (BLOB, 768 float32 dimensions) |

## The `swdb_` extension

Every table SWDB has and LANL lacks is named `swdb_<name>`. Extension tables may point at LANL
rows; no LANL table points back. A file built before the prefix (2026-10-11) has no
`swdb_meta`, so every command treats it as stale and rebuilds it.

| Group | Tables |
|---|---|
| Index bookkeeping | `swdb_meta`, `swdb_records` |
| Ties to the LANL core | `swdb_row_origins`, `swdb_guessed_columns` |
| Source and computation | `swdb_applications`, `swdb_kernels`, `swdb_implementations`, `swdb_implementation_contexts` |
| Memory access | `swdb_access_patterns`, `swdb_steps` |
| Inputs and machines | `swdb_inputs`, `swdb_input_properties`, `swdb_machines`, `swdb_machine_flags` |
| Strategies and intrinsics | `swdb_strategies`, `swdb_strategy_effects`, `swdb_strategy_intrinsics`, `swdb_applied_strategies`, `swdb_implementation_intrinsics`, `swdb_intrinsics`, `swdb_intrinsic_extensions` |
| Measurements and estimates | `swdb_profiles`, `swdb_metrics`, `swdb_estimates` |
| Typed library | `swdb_library_entries`, `swdb_library_dependencies`, `swdb_library_clauses`, `swdb_library_pattern_keys`, `swdb_library_pattern_key_steps` |
| Statement observations | `swdb_statements`, `swdb_statement_steps`, `swdb_statement_facts` |
| Contract links | `swdb_contract_definitions`, `swdb_contract_data_structures`, `swdb_contract_kernels`, `swdb_contract_kernel_variants` |
| Attribution reports | the `swdb_attribution*` tables ([Attribution tables](#attribution-tables)) |
| Derived implementations | `swdb_contract_lineage`, `swdb_rewrite_links` ([Derived-implementation tables](#derived-implementation-tables)) |
| Proof records | the `swdb_proof*` tables, `swdb_run_fields` and `swdb_repair_lineage` ([Proof tables](#proof-tables)) |

`swdb_kernels` and `kernels` describe the same kernel records: join them on
`swdb_kernels.id = kernels.slug`. Likewise `swdb_implementations.id = kernel_variants.slug`.

### `swdb_meta`

| Column | Meaning |
|---|---|
| `key` | `records_dir` (the absolute records folder the file was built from), `library_dir`, `fingerprint`, or `builder` |
| `value` | the folder; the typed library folder it uses (`library/` beside `records/`); the sha256 over every record file's and every library file's path, size, and modification time, so an edited library entry or pinned code file makes the index stale; or the sha256 of the `swdb` package's code, so any change to the tool rebuilds the file |

### `swdb_records`

One row per record, whatever its kind.

| Column | Meaning |
|---|---|
| `id` | record ID |
| `kind` | any supported [record kind](../../vocab/record_kinds.yaml), including workflow records |
| `status` | draft, reviewed, or deprecated |
| `path` | file path relative to the records folder |
| `json` | the whole record as JSON (query it with `json_extract`) |

### `swdb_row_origins`

The YAML record behind every LANL row. A row several records name has one origin per record.

| Column | Meaning |
|---|---|
| `table_name` | the LANL table, for example `kernel_variants` |
| `row_id` | the row's `id` in that table |
| `record_id` | the record it was read from (`swdb_records.id`) |
| `record_field` | the record field it was read from, as a dotted path with bracketed list indexes (`code[0]`, `timing[2]`, `parts[0].outcome`, `access_patterns[1].steps[2].array`); `id` when the row stands for the whole record |

### `swdb_guessed_columns`

LANL-side tables and columns the slide does not show; summary in
[Guessed columns](#guessed-columns). Check these first against LANL's real `schema.sql`.

| Column | Meaning |
|---|---|
| `table_name` | the LANL table |
| `column_name` | the guessed column (every column, for a guessed table such as `kernel_variants`) |
| `reason` | why it exists and what it links to |

### `swdb_applications`

| Column | Meaning |
|---|---|
| `id` | application ID |
| `name` | application name |
| `commit_hash` | pinned upstream commit |
| `language` | source language |
| `parallel_model` | parallel model (vocabulary `parallel_models`) |
| `domain` | domain (vocabulary `domains`) |
| `json` | the whole record |

### `swdb_kernels`

| Column | Meaning |
|---|---|
| `id` | kernel ID |
| `name` | kernel name |
| `application` | application ID |
| `baseline_implementation` | ID of the baseline implementation |
| `json` | the whole record, including the correctness check |

### `swdb_implementations`

| Column | Meaning |
|---|---|
| `id` | implementation ID |
| `name` | implementation name |
| `kernel` | kernel ID |
| `function` | function name in the code |
| `origin` | origin kind (vocabulary `implementation_origins`) |
| `is_baseline` | 1 if the kernel names it as its baseline |
| `json` | the whole record: code, build, run, loops, access patterns |

### `swdb_access_patterns`

The adjacent `swdb_implementation_contexts` table stores each implementation's resolved
`application`, `source_ancestor`, `source_baseline`, `comparison_baseline`, and full
context `json`. These are regenerated from authoritative source records. Its
`implementation` key identifies the same row in `swdb_implementations`; the older
`is_baseline` column retains its historical kernel-default meaning.

One row per access pattern of each implementation.

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `pattern` | access pattern ID (unique within its implementation) |
| `kernel` | kernel ID |
| `expression` | the memory-access expression |
| `loop` | ID of the loop the pattern runs in |
| `update_kind` | update kind (vocabulary `update_kinds`) |
| `pattern_class` | address shapes of the steps, then the update kind, e.g. `stream > ranged_indirect > single_valued_indirect : read` |
| `duplicate_target_indices`, `duplicate_target_indices_basis` | semantic value (JSON) and its basis |
| `index_modified_during_loop`, `index_modified_during_loop_basis` | semantic value and basis |
| `loop_carried_dependencies`, `loop_carried_dependencies_basis` | semantic value and basis |
| `shared_target_between_threads`, `shared_target_between_threads_basis` | semantic value and basis |
| `atomic_updates_required`, `atomic_updates_required_basis` | semantic value and basis |
| `ordering`, `ordering_basis` | semantic value (vocabulary `orderings`) and basis |
| `numerical_requirement`, `numerical_requirement_basis` | semantic value (vocabulary `numerical_requirements`) and basis |
| `semantics_json` | all semantic facts with notes and evidence |

### `swdb_steps`

One row per step of each access pattern's chain, in order.

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `pattern` | access pattern ID |
| `position` | 0 for the first step of the chain |
| `array_name` | the step's array |
| `role` | array role (vocabulary `array_roles`) |
| `element_type` | element type as written in the code |
| `element_bytes` | element size in bytes |
| `element_count` | element-count formula over input property symbols |
| `layout` | layout (vocabulary `layouts`) |
| `address_shape` | address shape (vocabulary `address_shapes`) |
| `stride` | stride in elements, for `stream` steps |
| `index_transform` | index transform, for `single_valued_indirect` steps |

### `swdb_inputs`

| Column | Meaning |
|---|---|
| `id` | input ID |
| `name` | input name |
| `generator_arguments` | generator arguments (null for a file input) |
| `file_path` | file path (null for a generated input) |
| `json` | the whole record |

### `swdb_input_properties`

| Column | Meaning |
|---|---|
| `input` | input ID |
| `name` | property name (vocabulary `input_properties`) |
| `value` | value as JSON text |
| `basis` | basis of the value |

### `swdb_machines`

| Column | Meaning |
|---|---|
| `id` | machine ID |
| `hostname` | host name |
| `cpu_model` | CPU model name |
| `sockets` | sockets |
| `cores_per_socket` | physical cores per socket |
| `llc_bytes` | size of one last-level cache instance |
| `counters_available` | 1 if hardware counters are available to the profiling user, 0 if not, NULL if unknown |
| `json` | the whole record |

### `swdb_machine_flags`

One row per ISA flag of each machine (`cpu.flags`; empty for a 0.2 machine without flags).

| Column | Meaning |
|---|---|
| `machine` | machine ID |
| `flag` | one `lscpu` flag name, e.g. `avx512f` |

### `swdb_strategies`

| Column | Meaning |
|---|---|
| `id` | strategy ID |
| `name` | human name |
| `target` | vocabulary `strategy_targets` |
| `json` | the whole record: effect, parameters, preconditions, benefits_when |

### `swdb_strategy_effects`

One row per effect item, in order.

| Column | Meaning |
|---|---|
| `strategy` | strategy ID |
| `position` | 0-based position in `effect` |
| `kind` | vocabulary `effect_kinds` |
| `json` | the effect item |

### `swdb_strategy_intrinsics`

| Column | Meaning |
|---|---|
| `strategy` | strategy ID |
| `intrinsic` | one ID from its `common_intrinsics` |

### `swdb_applied_strategies`

One row per `applies` item of each implementation.

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `position` | 0-based position in `applies` (the order applied) |
| `strategy` | strategy ID |
| `target` | loop or access-pattern ID, or `input` |
| `parameters_json` | the parameter values as JSON |

### `swdb_implementation_intrinsics`

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `intrinsic` | one ID from its `uses_intrinsics` |

### `swdb_intrinsics`

| Column | Meaning |
|---|---|
| `id` | intrinsic ID (the C name without leading underscores) |
| `name` | exact C name |
| `isa_family` | vocabulary `isa_families` |
| `isa_extensions` | JSON list of the extensions it needs (also one row each in `swdb_intrinsic_extensions`) |
| `header` | the header that declares it |
| `memory_kind` | vocabulary `intrinsic_memory_kinds` |
| `address_shape` | the address shape the instruction forms, or null |
| `element_bits`, `lanes` | element width and elements per call, or null |
| `json` | the whole record |

### `swdb_intrinsic_extensions`

| Column | Meaning |
|---|---|
| `intrinsic` | intrinsic ID |
| `extension` | one ISA extension it needs (vocabulary `isa_extensions`) |

### `swdb_profiles`

| Column | Meaning |
|---|---|
| `id` | profile ID (`<implementation>.<input>.<machine>.<UTC start>`) |
| `implementation` | implementation ID |
| `input` | input ID |
| `machine` | machine ID |
| `complete` | 1 if every part of the run completed (or was skipped on purpose) |
| `correctness` | `passed`, or `not_established` when the correctness check did not finish (`--allow-unverified`); null if the profile has no correctness part |
| `started` | UTC start time |
| `bottleneck` | inferred bottleneck class (vocabulary `bottleneck_classes`) |
| `bottleneck_basis` | its basis (inferred while counters are unavailable) |
| `memory_limit` | bandwidth or latency, for `memory_bound` |
| `json` | the whole record: build, environment, parts, timing, counts, metrics |

### `swdb_metrics`

One row per metric of each profile.

| Column | Meaning |
|---|---|
| `profile` | profile ID |
| `name` | metric name (vocabulary `metrics`) |
| `value` | numeric value, or null when the value is a histogram or unknown |
| `value_json` | the value as JSON (histograms live here) |
| `unit` | unit (fixed per metric name) |
| `basis` | Recorded basis from [`vocab/basis.yaml`](../../vocab/basis.yaml); ordinary profiling normally produces measured, simulated, inferred, or unknown facts. Estimated time belongs to estimate records. |
| `threads` | thread count, for per-thread metrics |
| `array_name` | the array, for per-array metrics |
| `scope` | count scope, where one applies |
| `tool` | the tool that produced it |

### `swdb_estimates`

One row per estimate record. Never copied into the LANL performance tables
([measured only](#measured-only)). Code: [`swdb/lanl_performance.py`](../../swdb/lanl_performance.py).

| Column | Meaning |
|---|---|
| `id` | estimate ID (`swdb_records.id`) |
| `kernel_variant_id` | the estimated implementation (`kernel_variants.id`), only when the subject is an implementation; NULL for a candidate subject, so an estimate of a candidate never reads as one of its baseline |
| `base_kernel_variant_id` | for a candidate subject, the implementation the candidate rewrites, as its record names it (`kernel_variants.id`); NULL for an implementation subject or when the candidate does not resolve |
| `subject_kind` | `implementation` or `candidate` |
| `subject_id` | the subject's ID |
| `target` | the machine or hardware target estimated for |
| `input` | input ID |
| `threads` | thread count |
| `seconds` | estimated seconds, or NULL when unknown |
| `ratio` | estimated ratio to the baseline, or NULL |
| `verdict` | `estimated_gain`, `within_error` or `estimated_no_gain` |
| `estimator_version` | estimator version |

### `swdb_library_entries`

One row per typed library entry (ADR 0007), read from the library folder's YAML
(`schemas/library/library_entry.schema.json` gives the entry shape). The YAML
stays authoritative; tier and status are derived from records, as `swdb promote`
and `swdb submit` derive them.

| Column | Meaning |
|---|---|
| `id` | entry ID (`intrinsic.`, `lowering.`, `operation.` or `contract.` prefix) |
| `kind` | intrinsic, lowering, library_operation, or rewrite_contract |
| `path` | YAML file path relative to the library folder |
| `content_sha256` | the normative content hash that certification and review records pin |
| `tier` | experimental or shared (shared only through Yan-Ru's current review), or null if underivable |
| `status` | draft, certified, inconclusive, refuted, or evaluated_on_target, or null if underivable |
| `derived_from` | for a derived rewrite contract, the contract it cites (`provenance.derived_from`), else null |
| `json` | the whole entry |

### `swdb_library_dependencies`

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `dependency` | an entry in its dependency closure (intrinsics, lowerings, operations, a cited contract) |
| `content_sha256` | that dependency's current content hash |

### `swdb_library_clauses`

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `clause` | clause ID (for example `L1` or `BC-L1`) |
| `role` | precondition, postcondition, frame, legality, or preservation |
| `discharge_mode` | how the clause is discharged (differential_test, assumed, ...) |
| `negative_control` | the named control that must be rejected, or `none` |
| `statement` | the natural-language statement |

### `swdb_statements`

The statements index: one row per statement annotation of an implementation
(`extensions.statements.annotations`, ticket 35).

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `statement` | statement ID |
| `function` | the function whose statements are annotated (for example `TDStep`) |
| `path` | source path of the statement |
| `first_line`, `last_line` | its pinned line range |
| `revision` | the pinned source revision |
| `code` | the statement's exact code |
| `basis` | basis of the annotation |
| `depends_on` | JSON list of statement IDs it depends on |
| `agent_claims` | number of retained agent claims (claims stay in `json`) |
| `json` | the whole annotation, with its claims and facts |

### `swdb_statement_steps`

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `statement` | statement ID |
| `pattern` | access-pattern ID the statement realizes |
| `step` | step position in that access pattern |

### `swdb_statement_facts`

Recorded facts on statements (`annotation_facts` of a statement annotation; agent claims are
never copied here). The query site finder (ticket 55, `swdb/site_finder.py`) reads legality
facts, whose field is `legality:<entry id>:<clause id>` and whose value is true or false.

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `statement` | statement ID |
| `position` | the fact's position in the statement's `annotation_facts` list |
| `field` | the fact's field |
| `value` | its value as JSON text (`true`, `false`, a list, ...) |
| `basis` | its basis (measured, simulated, reported, code_reading or inferred) |
| `evidence` | the evidence text the fact cites |

### `swdb_library_pattern_keys`

One row per pattern of a library entry's `pattern_key` (rewrite contracts and library
operations), in key order.

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `key_position` | the pattern's position in the key (0 first) |
| `update_kind` | the update kind it matches |
| `step_count` | the chain length it matches (the longer of its roles and address shapes) |

### `swdb_library_pattern_key_steps`

One row per step of a key pattern; a step missing its role or shape (a malformed key) has a
null there and never matches.

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `key_position` | the key pattern's position |
| `step` | step position in the chain (0 first) |
| `role` | the array role at that step (index, offsets or target) |
| `address_shape` | the address shape at that step |

### Contract link tables

Code: [`swdb/lanl_contracts.py`](../../swdb/lanl_contracts.py).

Four `swdb_` extension tables say which LANL rows a rewrite contract is tied to. They point at
LANL rows; no LANL table points back, so dropping them leaves the LANL core intact.

**Only links a record states.** Two kinds of record state one:

| Record | What it states | Links made |
|---|---|---|
| certification | `candidate.contract` was certified on `candidate.snapshot`, a source snapshot of one implementation | contract → that implementation (`kernel_variants`) and its kernel |
| implementation | a statement fact `legality:<contract>:<clause>` on one of its statements | contract and clause → the statement's function (`definitions`), the arrays of the access-pattern steps the statement names (`data_structures`), the implementation and its kernel |

- **A link is a tie, not a verdict.** A certification links whatever its verdict; a fact links
  whatever its value. Read the verdict or value through `record_id` and `record_field`, or in
  `swdb_statement_facts`.
- **The contract must be in the library** (`swdb_library_entries`, kind `rewrite_contract`).
  A record naming any other ID makes no link.
- **Not links:** the site finder's matches (recorded in campaign summaries) are inference, and a
  proposal's offered library is an offer. Lowerings, intrinsics and library operations never link.
- No `swdb_row_origins` entries: each link row names its own record.

All four tables have the same columns; only the LANL column differs.

| Column | Meaning |
|---|---|
| `contract` | the contract ID (`swdb_library_entries.id`) |
| `definition_id` / `data_structure_id` / `kernel_id` / `kernel_variant_id` | the linked LANL row (`definitions.id`, `data_structures.id`, `kernels.id`, `kernel_variants.id`) |
| `clause` | the clause a statement fact names; NULL for a certification |
| `record_id` | the record that states the link (`swdb_records.id`) |
| `record_field` | the field that states it: `candidate`, or `extensions.statements.annotations[<i>].annotation_facts[<j>]` |

| Table | Linked LANL row |
|---|---|
| `swdb_contract_definitions` | the function holding the statement: the `definitions` row the implementation's `extensions.statements.function` produced |
| `swdb_contract_data_structures` | each array (`data_structures` row of the implementation's kernel) that a step the statement names reads or writes; step numbers count from the statements' `step_index_base` (0 or 1) |
| `swdb_contract_kernels` | the kernel of the linked implementation |
| `swdb_contract_kernel_variants` | the implementation itself |

## Dropping the extension

To get a LANL-only database, delete every `swdb_` table from a copy:

```sh
cp build/swdb.sqlite lanl-only.sqlite
sqlite3 lanl-only.sqlite "select 'DROP TABLE \"' || name || '\";' from sqlite_master
  where type = 'table' and name like 'swdb\_%' escape '\'" | sqlite3 lanl-only.sqlite
sqlite3 lanl-only.sqlite "pragma foreign_key_check"   # prints nothing
```

- **Left:** the 16 LANL tables (15 slide tables + the guessed `kernel_variants`) and their rows. Every foreign key still resolves.
- **Lost:** full records, row origins, the guessed-column list, estimates, simulated metrics,
  library, contracts and contract links.
- **Use a copy.** `swdb` treats a file without `swdb_meta` as stale and rebuilds it.
- **Tested:** `assert_separable` in [`tests/testkit/lanl.py`](../../tests/testkit/lanl.py),
  called by each table group's test (`tests/test_lanl_<group>.py`).

## Queries

Every query prints YAML, or JSON with `--format json`, and rebuilds the database first when
it is stale.

- `swdb find [--shape S]... [--update U] [--semantic FIELD=VALUE]... [--kernel K]`: access
  patterns with their steps and semantics.
- `swdb find --strategy <id> [other filters]`: where an access-pattern strategy could apply.
  One entry per access pattern with `implementation`, `pattern`, `outcome` (`legal` or
  `undetermined`), and `unknown_fields`; illegal patterns are left out.
- `swdb implementations <kernel> [--require FIELD=VALUE]...`: a kernel's implementations
  whose every access pattern has each required value with a known basis.
- `swdb implementations <kernel> --applies <strategy> [--require FIELD=VALUE]...`: the
  kernel's implementations that apply the strategy. One entry per implementation with
  `implementation`, `applies` (its matching `applies` items, each with `strategy`, `target`,
  `parameters`, and `position`), `derived_from` (the baseline, or null), and `profiles`: one
  item per (input, machine) pair that either has a complete profile for, with `input`,
  `machine`, `profile` (the implementation's newest complete profile ID), and
  `baseline_profile` (the baseline's), each null when missing. Compare their metrics with
  `swdb sql` or `swdb view` to see whether the strategy helped.
- `swdb strategies --pattern <implementation>/<pattern>`: every access-pattern strategy,
  one entry each, with `strategy`, `outcome` (`legal`, `illegal`, or `undetermined`),
  `reasons` (why it is illegal), `unknown_fields` (the semantic fields whose basis is
  unknown, when undetermined), `check_by_hand` (the strategy's unchecked preconditions,
  always listed), and `benefits_when` (reported benefit conditions, shown and never used to
  filter). Legality rules: [format-v0.3.md](format-v0.3.md), section 12.
- `swdb strategies --loop <implementation>/<loop>`: every loop strategy, in the same entry
  shape, checked against every access pattern in the loop and its child loops. It is legal
  only when all of them pass, illegal when any known value contradicts (each reason starts
  with the pattern ID), and otherwise undetermined, with `unknown_fields` as
  `<pattern>.<field>`.
- `swdb strategies --input <implementation>`: every input strategy, in the same entry shape.
  Input preconditions are prose, so each entry is `undetermined` with its conditions in
  `check_by_hand`.

`find --strategy` takes only access-pattern strategies; `--pattern`, `--loop`, and `--input`
list only strategies of that target.

## Examples

```
# the kernels whose implementations include a ranged-indirect gather
swdb sql "select distinct kernel, implementation from swdb_steps join swdb_access_patterns using (implementation, pattern)
          where address_shape = 'ranged_indirect'"

# intrinsics a machine can run (every extension is among its flags)
swdb sql "select i.id from swdb_intrinsics i where not exists (select 1 from swdb_intrinsic_extensions e
          where e.intrinsic = i.id and e.extension not in (select flag from swdb_machine_flags where machine = 'mbit10'))"

# median time per thread count for one implementation on every input
swdb sql "select p.input, m.threads, m.value from swdb_metrics m join swdb_profiles p on p.id = m.profile
          where p.implementation = 'gapbs-pr-gs' and m.name = 'time_per_trial_median' order by 1, 2"
```

## Attribution tables

Added: 2026-10-11 (Eastern Time), fine-grained attribution ticket 02. One set of rows per
`attribution` record (`swdb attribute`; format in
[format-v0.4-attribution.md](format-v0.4-attribution.md)). These are SWDB-only tables, so
their names start with `swdb_`. Unknown values are NULL, never 0.

### `swdb_attributions`

One row per attribution report.

| Column | Meaning |
|---|---|
| `id` | report ID |
| `baseline_estimate` | baseline estimate ID |
| `candidate_estimate` | candidate estimate ID |
| `baseline_source` | source record (snapshot or candidate) the baseline counted |
| `candidate_source` | source record the candidate counted |
| `target_description` | shared target description ID |
| `target_description_sha256` | its content hash |
| `input` | shared input or workload ID |
| `threads` | shared thread count |
| `evidence_kind` | `execution` or `contract_fixture` |
| `baseline_seconds` | baseline estimate total (NULL if unknown) |
| `candidate_seconds` | candidate estimate total (NULL if unknown) |
| `total_speedup` | baseline total ÷ candidate total |
| `amdahl_ceiling` | baseline total ÷ untouched candidate seconds |
| `json` | the full record |
| `unattributed_flagged` | 1 when unattributed time is above 10% of either total, 0 when not, NULL when unknown (ticket 04) |

### `swdb_attribution_groups`

One row per code-origin group of a report (always three: untouched, agent_rewritten,
unattributed). Seconds are per-trial sums, then medians; groups need not add up to the total.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `origin` | code origin of the group |
| `baseline_seconds` | group seconds in the baseline |
| `candidate_seconds` | group seconds in the candidate |
| `baseline_share` | group ÷ baseline total |
| `candidate_share` | group ÷ candidate total |
| `realized_speedup` | baseline ÷ candidate group seconds |
| `drift` | untouched group only: candidate ÷ baseline seconds; NULL for other groups |
| `unknown_regions` | how many unknown regions make this group's numbers unknown |

### `swdb_attribution_regions`

One row per region of either estimate.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `origin` | its code origin |
| `reason` | why it got that origin |
| `path` | file path relative to its source tree (NULL outside the tree or without a location) |
| `first_line` | first line of its span |
| `last_line` | last line of its span |
| `seconds` | the estimate's per-region seconds (diagnostic) |
| `sites` | JSON list of the rewrite-site IDs it overlaps |
| `mixed` | 1 when it is rewritten but some of its lines are unchanged (added 2026-10-11 ET, ticket 04) |
| `matched_region` | the other side's region at the same untouched code, or NULL (ticket 04) |

### `swdb_attribution_origins`

Added: 2026-10-11 (Eastern Time), fine-grained attribution ticket 05. One row per origin inside
the `agent_rewritten` group of a report (always four: offload_command, intrinsic, library_call,
agent_rewritten). Same per-trial-sum-then-median rule as the groups.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `origin` | code origin of regions inside rewrite sites |
| `baseline_seconds` | that origin's seconds in the baseline |
| `candidate_seconds` | that origin's seconds in the candidate |
| `baseline_share` | origin ÷ baseline total |
| `candidate_share` | origin ÷ candidate total |
| `unknown_regions` | how many unknown regions make this origin's numbers unknown |

### `swdb_attribution_iterations`

Added 2026-10-11 ET (ticket 06). One row per report given a previous accepted candidate
(`this_iteration` in the record); none otherwise.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `iteration` | the candidate's iteration number (2 or more) |
| `previous_estimate` | previous accepted candidate's estimate ID |
| `previous_source` | source record the previous candidate counted |
| `earlier_sources` | JSON list of earlier accepted candidates' source IDs, oldest first |
| `previous_seconds` | previous candidate's estimate total (NULL if unknown) |
| `candidate_seconds` | candidate estimate total (NULL if unknown) |
| `total_speedup` | previous total ÷ candidate total (gain this iteration) |
| `amdahl_ceiling` | previous total ÷ candidate seconds untouched this iteration |

### `swdb_attribution_iteration_groups`

Same columns as `swdb_attribution_groups`, for the this-iteration comparison: `baseline_*`
means the previous accepted candidate. `swdb_attribution_groups` stays cumulative.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `origin` | code origin of the group (this iteration) |
| `baseline_seconds` | group seconds in the previous candidate |
| `candidate_seconds` | group seconds in the candidate |
| `baseline_share` | group ÷ previous total |
| `candidate_share` | group ÷ candidate total |
| `realized_speedup` | previous ÷ candidate group seconds |
| `drift` | untouched group only: candidate ÷ previous seconds |
| `unknown_regions` | how many unknown regions make this group's numbers unknown |

### `swdb_attribution_iteration_regions`

Same columns as `swdb_attribution_regions` for the this-iteration comparison (`side`
`baseline` = the previous candidate), plus the last-changed iteration.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` (previous candidate) or `candidate` |
| `region` | the estimate's region ID |
| `origin` | its code origin this iteration |
| `reason` | why it got that origin |
| `path` | file path relative to its source tree |
| `first_line` | first line of its span |
| `last_line` | last line of its span |
| `seconds` | the estimate's per-region seconds (diagnostic) |
| `sites` | JSON list of this iteration's rewrite-site IDs it overlaps |
| `last_changed_iteration` | iteration that last changed the region (0 = never; NULL = no source location) |

### `swdb_attribution_headroom`

Added: 2026-10-11 (Eastern Time), fine-grained attribution ticket 07. One row per region of
either estimate and named limit: `resource_floor` and, since ticket 08, `catalog_bound`.
Rows come from the cumulative `regions`; the `this_iteration` rows' limits stay in the
report JSON (`swdb_attributions.json`).

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `limit_name` | the named limit: `resource_floor` or `catalog_bound` |
| `limit_seconds` | the limit's seconds (NULL if unknown) |
| `limiting_term` | for the floor: `compute_throughput` or `streaming_bandwidth`; for the catalog bound: the entry that gives it (NULL if unknown) |
| `headroom` | region seconds ÷ limit seconds (NULL if it cannot be a number) |
| `reason` | why `headroom` is NULL: `unknown_estimate`, `zero_limit`, `unknown_limit` (floor), or the catalog bound's own reason (one list, in [format-v0.4-attribution.md § Catalog bound](format-v0.4-attribution.md#catalog-bound-ticket-08); the schema's `catalog_bound.reason` enum is the checked copy) |
| `missing` | JSON list of the missing counts and rates behind an unknown limit |

### `swdb_attribution_ranking`

Added: 2026-10-11 (Eastern Time), ticket 07. The candidate's regions in next-iteration order.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `position` | 1-based place in the order |
| `side` | always `candidate` |
| `region` | the candidate estimate's region ID |
| `tier` | `remaining_gain_bound` (ticket 08), then `floor_headroom`, then `unknown` (ranked after every known value); tiers are never compared |
| `limit_name` | the limit the value uses: `catalog_bound` or `resource_floor` |
| `value` | the ranking value: remaining gain bound (an upper limit, never an expected gain) or floor headroom; NULL in the `unknown` tier |
| `reason` | why the value is NULL |

### `swdb_attribution_catalog`

Added: 2026-10-11 (Eastern Time), ticket 08. One row per region of either estimate and
site-finder-matched entry: that entry's own estimate on the region, or why it has none. Rows
come from the cumulative `regions`.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `entry` | library entry ID |
| `kind` | `library_operation` or `rewrite_contract` (as the site finder recorded it) |
| `seconds` | the entry's estimate on the region's baseline counts (a candidate row reads its matched baseline region's; review fix 2026-10-11 ET) (NULL if unknown) |
| `reason` | why `seconds` is NULL: `needs_rewritten_counts`, `missing_inputs`, `no_offload_mechanism`, `entry_changed`, `entry_unhashed`, `not_in_library` or `no_baseline_counts` |
| `site_finder_regions` | JSON list of the joined site-finder region IDs that apply the entry |
| `mixed` | 1 when some line of the region lies outside every joined site-finder span (review fix 2026-10-11 ET: spans are the site-finder lines moved into the tree, or the whole function when they cannot be moved) |
| `missing` | JSON list of the entry's missing counts and rates |

### `swdb_attribution_split_checks`

Added: 2026-10-11 21:17 ET, ticket 09. One row per report that has a `split_check` (made with
`--baseline-profile` and `--candidate-profile`). No row = not checked.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `verdict` | `passed` or `split_unverified` |
| `rule_id` | `swdb.split_check.v2` (final review F40: estimated shares keep call time in the region's own group) |
| `max_abs_share_gap` | 0.1, the fixed pass threshold (10 percentage points) |
| `baseline_profile` | baseline region profile ID |
| `candidate_profile` | candidate region profile ID |
| `reasons` | JSON list of `{side, origin, reason}` why it is unverified; `[]` when passed |
| `baseline_load_average` | JSON host load recorded with the baseline profile run (NULL if none) |
| `candidate_load_average` | JSON host load recorded with the candidate profile run (NULL if none) |

### `swdb_attribution_split_gaps`

Added: 2026-10-11 21:17 ET, ticket 09. One row per side and group of a checked report (always
six). The measured scopes stay in the JSON column.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` or `candidate` |
| `origin` | `untouched`, `agent_rewritten` or `unattributed` |
| `estimated_share` | the split-check estimated share: each region's full seconds, calls included, under its own group (F40), not the `swdb_attribution_groups` share (NULL if unknown) |
| `measured_share` | measured exclusive thread-CPU share (NULL if nothing was measured) |
| `measured_seconds` | measured exclusive thread-CPU seconds of the group |
| `gap` | measured − estimated share (NULL if either is unknown) |
| `within_rule` | 1 when \|gap\| ≤ 0.1, 0 when not, NULL when unknown |

### `swdb_attribution_site_finder`

Added: 2026-10-11 21:31 ET, ticket 10. One row per report made with `--site-finder`: how the
site finder finds the latest report for its Extensa campaign's kernel and target. The verdict it acts on
is `swdb_attribution_split_checks.verdict` (no row = not checked: today's order).

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `campaign_summary` | the pinned Extensa campaign summary ID |
| `iteration` | the pinned iteration `index` |
| `kernel` | the site-finder `kernel` parameter that iteration ran under (NULL if not recorded) |
| `target` | the site-finder target binding (`native_cpu`, `dx100_gem5`; NULL if not recorded) |
| `created` | the report's `created` date, which is the latest `updated` date of its inputs (not the day it was made); the latest report is the greatest `created` (newest inputs), then the greatest ID |

### `swdb_attribution_site_finder_regions`

Added: 2026-10-11 21:31 ET, ticket 10. One row per cumulative region and joined site-finder
region (a region's `catalog_bound.site_finder_regions`), so a ranking row maps back to
site-finder region IDs.

| Column | Meaning |
|---|---|
| `attribution` | report ID |
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `site_finder_region` | a joined site-finder region ID |

## Proof tables

Added: 2026-10-14 (Eastern Time), Probata proof of concept ticket 04. One set of rows per `proof`
record (`swdb prove`; format in [format-v0.4-proof.md](format-v0.4-proof.md);
[ADR 0016](../adr/0016-proof-records-never-change-level-computed-on-read.md)). SWDB extension only:
no proof data enters a LANL core table. No level is stored here; `swdb candidate-level` computes it
on read.

### `swdb_proofs`

One row per proof record.

| Column | Meaning |
|---|---|
| `id` | proof record ID |
| `subject_kind` | subject kind (vocabulary `proof_subject_kinds`) |
| `subject_id` | the subject's `id` (NULL for a candidate proof unit) |
| `candidate` | candidate proof unit: the candidate artifact (else NULL) |
| `function` | candidate proof unit: the function that holds the rewrite site (else NULL) |
| `verdict` | `proven`, `refuted` or `not_proven`; NULL for a skip record (ticket 11) |
| `route` | `route_1`, `route_3`, `bounded_direct`, or NULL when the record names none |
| `failure_class` | a not-proven record's failure class (vocabulary `proof_failure_classes`, role `failure_class`; else NULL) |
| `skip_reason` | a skip record's skip reason (vocabulary `proof_failure_classes`, role `skip_reason`; else NULL) |
| `has_counterexample` | 1 when the record holds a counterexample inline (refuted), else 0 |
| `replay_label` | a refuted record's replay label (`reproduced`, `proof_semantics_only`, `not_reproduced`, `undefined_behavior`); NULL when absent (ticket 10, 2026-10-14 ET) |
| `evidence_kind` | `contract_fixture` (the scripted adapter) |
| `adapter` | the job block's adapter |
| `host` | the job block's host (`mac` on the Mac) |
| `log_path` | the adapter log's path on the run host; NULL for a skip record (no adapter ran) |
| `log_sha256` | the adapter log's sha256; NULL for a skip record |
| `json` | the full record |

### `swdb_proof_pins`

The content-hash set: one row per single pin, per summary used and per build constant.

| Column | Meaning |
|---|---|
| `proof` | proof record ID |
| `kind` | pin kind (`code`, `contract`, `baseline_function`, `reference_semantics`, `proof_semantics`, `method_version`, `minimum_bounds`, `predecessor_snapshot`, `summaries`, `build_constants`) |
| `position` | 0 for a single pin; the list index for a summary or build constant |
| `ref` | the pinned ID (a build constant's name); NULL when not applicable |
| `sha256` | the pinned hash; NULL when not applicable or a build constant |
| `function` | `baseline_function` pin: the function named in the pinned tree (else NULL) |
| `proof_record` | summary pin: the proof record that proved the summary (else NULL) |
| `value` | build constant: its value as JSON (else NULL) |
| `not_applicable` | the sentence saying why a pin does not apply yet (else NULL) |

### `swdb_proof_assumptions`

The assumption set: one row per entry.

| Column | Meaning |
|---|---|
| `proof` | proof record ID |
| `position` | the entry's index |
| `kind` | one of the seven kinds (vocabulary `proof_assumption_kinds`) |
| `ref` | the referenced ID |
| `sha256` | the referenced hash |
| `sentence` | the entry's plain sentence |

### `swdb_proof_bounds`

One row per bound dimension; `threads` is always present (a skip record has no rows here and none in
`swdb_proof_assumptions`).

| Column | Meaning |
|---|---|
| `proof` | proof record ID |
| `dimension` | bound dimension (for example `threads`, `vertices`) |
| `value` | the bound; NULL when unbounded |
| `unbounded` | 1 when the dimension is unbounded, else 0 |

### `swdb_proof_jobs`

Added 2026-10-14 ET (ticket 12): the job block, one row per proof record (skip records included), so
the evaluation's paired statistics can query cost per job. Proof time is a cost metric, never a speed
claim; never mix `host` values.

| Column | Meaning |
|---|---|
| `proof` | proof record ID |
| `adapter` | the verifier adapter (`scripted` for contract fixtures) |
| `host` | `mac` on the Mac, else the host's short name |
| `worker_core` | the pinned core number, or `unpinned`; NULL for a record written before ticket 12 |
| `wall_seconds` | the job's wall time |
| `cpu_seconds` | the job's CPU time |
| `batch_load_start` | the host's 1-minute load average when the job started |
| `batch_load_end` | the same when the job ended; NULL for a record written before ticket 12 |
| `peak_rss_bytes` | peak resident set size of the job's process tree (what the RSS watchdog reads) |
| `batch` | batch ID |
| `position` | position in the batch |

### `swdb_run_fields`

Added 2026-10-14 ET (ticket 12, S10): one row per proposal or proof record that carries a run index
or a provider pin.

| Column | Meaning |
|---|---|
| `record` | proposal or proof record ID |
| `record_kind` | `proposal` or `proof` |
| `run_index` | 1, 2 or 3; NULL when only a provider pin is given |
| `provider_kind` | `codex` or `claude`; NULL when no pin is given |
| `provider_model` | the pinned model |
| `provider_effort` | the pinned effort |

### `swdb_repair_lineage`

Added 2026-10-14 ET (ticket 12): one row per proposal with repair lineage.

| Column | Meaning |
|---|---|
| `proposal` | proposal ID (the repaired candidate artifact's proposal) |
| `refuted_candidate` | the refuted candidate artifact |
| `counterexample_record` | the refuted proof record holding the counterexample |
| `round` | the repair round (>= 1) |
| `reverted_repair` | 1 when the contract-match check flagged a reverted repair, else 0 |

## Derived-implementation tables

Added: 2026-10-14 (Eastern Time), Probata proof of concept ticket 19. Format in
[format-v0.4-derived.md](format-v0.4-derived.md). SWDB extension only. Whether a link still matches
and its proof route are computed on read by `swdb build` (ADR 0016); no record is rewritten.

### `swdb_contract_lineage`

One row per entry of a derived implementation's `contract_lineage`.

| Column | Meaning |
|---|---|
| `implementation` | derived implementation ID |
| `position` | the entry's index (0 = the first rewrite after the baseline implementation) |
| `contract` | rewrite contract ID |
| `version` | the contract's version (NULL while contracts carry none) |
| `content_sha256` | the contract's content hash the rewrite was certified with |

### `swdb_rewrite_links`

One row per rewrite link: each link of a derived implementation, and each certified certification
of a candidate artifact built on a derived implementation (its `predecessor`) that is not itself a
derived implementation's result.

| Column | Meaning |
|---|---|
| `subject_kind` | `derived_implementation` or `candidate` |
| `subject` | the derived implementation or candidate artifact ID |
| `position` | the link's index (one per contract of the rewrite) |
| `contract` | rewrite contract ID |
| `contract_sha256` | the contract content hash the certification holds for |
| `predecessor` | the implementation the rewrite was applied to |
| `predecessor_snapshot` | the predecessor's source snapshot ID |
| `predecessor_snapshot_sha256` | its tree hash when the rewrite was certified |
| `result_candidate` | the rewrite's result candidate artifact |
| `result_snapshot` | a derived implementation's own snapshot (NULL for a candidate subject) |
| `result_sha256` | the result's tree hash |
| `certification` | the certification record ID for this contract |
| `proof_route` | `route_1`, `route_3` or `bounded_direct` from the rewrite's proof record (its result candidate artifact and contract), or `none yet` |
| `matches` | 1 while the predecessor snapshot, the contract (when the library is known) and the result are unchanged and every earlier link of the chain matches; else 0 |
| `reason` | why it no longer matches (`; `-joined), else NULL |
