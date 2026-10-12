# The SQLite database

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-10-03 (Eastern Time): typed-library and statements tables (ticket 46).

Updated: 2026-10-04 (Eastern Time): statement facts and pattern-key tables for the query site finder (ticket 55).

Updated: 2026-10-06 (Eastern Time): one record/index access interface (analytic-evaluation ticket 02).

Updated: 2026-10-07 (Eastern Time): current evidence-basis interpretation.

Updated: 2026-10-11 (Eastern Time): every table name carries the `swdb_` prefix (LANL-shaped-db
ticket 01).

Updated: 2026-10-11 (Eastern Time): the LANL core starts with `kernels` and `kernel_variants`,
plus `swdb_row_origins` and `swdb_guessed_columns` (LANL-shaped-db ticket 02).

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
research query relations, either by translating queries or by exposing a
read-only projection through the crosswalk. The actual main schema is still
unverified; this refactor supplies the boundary without assuming that schema.
Contributions to the main database must use its ingest inputs, and
`create_index` must never open the main database for writing.

## LANL core

The database also holds LANL's tables, with LANL's names and only the columns LANL's
`DB_current_work` slide shows (transcribed in the
[LANL-shaped-db spec](../../.scratch/lanl-shaped-db-2026-10-09/spec.md) appendix).

- **Integer IDs.** Every LANL table has an `id` primary key, assigned at build time in record-ID
  order. IDs change between builds; the stable key is `slug` (or `swdb_row_origins`).
- **Unknown is NULL.** A value the records do not state is NULL, never a default.
- **Drop-ready.** LANL tables never reference a `swdb_` table. Delete every `swdb_` table and
  `PRAGMA foreign_key_check` is still clean.
- **Checked.** Foreign keys are declared, and every build fails if
  `PRAGMA foreign_key_check` reports a row.
- **Code.** Each table group is one module `swdb/lanl_<group>.py`; [`swdb/lanl.py`](../../swdb/lanl.py)
  runs them in order.

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

Updated: 2026-10-11 (Eastern Time), LANL-shaped-db ticket 03. Only what records name; no
column is guessed. Code: [`swdb/lanl_sources.py`](../../swdb/lanl_sources.py).

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

Added 2026-10-11 ET (LANL-shaped-db ticket 04). Code: [`swdb/lanl_performance.py`](../../swdb/lanl_performance.py).

**Only measurements on real machines.** Analytic estimates go to `swdb_estimates` (spec D4).
Simulated metrics (cachegrind) and inferred or unknown ones stay in `swdb_metrics`. Hardware
targets (a modeled DX100) are not machines.

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
| `parameters_json` | JSON: `input`, `input_arguments` (the input's generator arguments), `threads`, `trials`, `compiler`, `compiler_version`, `flags`, `omp_places`, `omp_proc_bind`, `binding`; null where the profile does not say |
| `git_commit` | the application's source revision (`build.application_commit`), or NULL |
| `kernel_variant_id` | guessed link: the profiled implementation (`kernel_variants.id`) |

#### `performance_runs`

One row per `timing[]` entry of a profile: one benchmark process at one thread count.

| Column | Meaning |
|---|---|
| `id` | integer ID (build-local) |
| `elapsed_seconds` | median time per trial (`median_s`); min, max and spread stay in the profile |
| `throughput_value` | NULL: no record states a throughput |
| `hardware_profile_id` | guessed link: the profile's machine (`hardware_profiles.id`) |
| `run_config_id` | guessed link: `run_configs.id` |
| `kernel_variant_id` | guessed link: the profiled implementation (`kernel_variants.id`) |

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

#### `swdb_estimates`

Extension table: one row per estimate record. Never copied into the LANL performance tables.

| Column | Meaning |
|---|---|
| `id` | estimate ID (`swdb_records.id`) |
| `kernel_variant_id` | the estimated implementation (`kernel_variants.id`): the subject itself, or for a candidate subject the implementation the candidate record names; NULL when neither resolves |
| `subject_kind` | `implementation` or `candidate` |
| `subject_id` | the subject's ID |
| `target` | the machine or hardware target estimated for |
| `input` | input ID |
| `threads` | thread count |
| `seconds` | estimated seconds, or NULL when unknown |
| `ratio` | estimated ratio to the baseline, or NULL |
| `verdict` | `estimated_gain`, `within_error` or `estimated_no_gain` |
| `estimator_version` | estimator version |

### Validation tables and the empty tables

Added 2026-10-11 ET (LANL-shaped-db ticket 05). Code:
[`swdb/lanl_validation.py`](../../swdb/lanl_validation.py). The two validation tables keep the
slide's capitalization.

**Which outcomes count.** A correctness outcome is a profile's `correctness` part or an
evaluation's `correctness.state`. It becomes a `Validation_results` row only when it names both
an implementation (the kernel variant) and an input record: a profile's `input`, or an
evaluation's `request.workload.id` when that is a `workload` record. Outcomes missing either
(for example the dx100 smoke evaluations, which name no implementation) have no row.

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

One row per counted correctness outcome. Origin: the profile (`parts.<n>.outcome`) or
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

### Contract link tables

Not built yet (LANL-shaped-db ticket 06).

### `swdb_row_origins`

The YAML record behind every LANL row. A row several records name has one origin per record.

| Column | Meaning |
|---|---|
| `table_name` | the LANL table, for example `kernel_variants` |
| `row_id` | the row's `id` in that table |
| `record_id` | the record it was read from (`swdb_records.id`) |
| `record_field` | the record field it was read from; `id` when the row stands for the whole record |

### `swdb_guessed_columns`

LANL-side tables and columns the slide does not show. Check these first against LANL's real
`schema.sql`.

| Column | Meaning |
|---|---|
| `table_name` | the LANL table |
| `column_name` | the guessed column (every column, for a guessed table such as `kernel_variants`) |
| `reason` | why it exists and what it links to |

## Tables

Every SWDB-only table is named `swdb_<name>`; unprefixed names belong to the
[LANL core](#lanl-core). Columns and contents are as listed; a file built before the prefix
(2026-10-11) has no `swdb_meta`, so every command treats it as stale and rebuilds it.

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
