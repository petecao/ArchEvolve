# The SQLite database

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-10-03 (Eastern Time): typed-library and statements tables (ticket 46).

Updated: 2026-10-04 (Eastern Time): statement facts and pattern-key tables for the query site finder (ticket 55).

Updated: 2026-10-06 (Eastern Time): one record/index access interface (analytic-evaluation ticket 02).

Updated: 2026-10-07 (Eastern Time): current evidence-basis interpretation.

Updated: 2026-10-11 (Eastern Time): attribution catalog bounds and full ranking (fine-grained attribution ticket 08).

Run commands inside `ArchEvolve/swdb-project/`. [The database builder](../../swdb/db.py)
writes `build/swdb.sqlite` beside `records/` by default (another records folder
`X` gets `build/swdb-X.sqlite`). It recreates every table in a temporary file,
then replaces the selected index. YAML remains authoritative (ADR 0002).
The `meta` table names the records folder and a fingerprint of its files (path,
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

## Tables

### `meta`

| Column | Meaning |
|---|---|
| `key` | `records_dir` (the absolute records folder the file was built from), `library_dir`, `fingerprint`, or `builder` |
| `value` | the folder; the typed library folder it uses (`library/` beside `records/`); the sha256 over every record file's and every library file's path, size, and modification time, so an edited library entry or pinned code file makes the index stale; or the sha256 of the `swdb` package's code, so any change to the tool rebuilds the file |

### `records`

One row per record, whatever its kind.

| Column | Meaning |
|---|---|
| `id` | record ID |
| `kind` | any supported [record kind](../../vocab/record_kinds.yaml), including workflow records |
| `status` | draft, reviewed, or deprecated |
| `path` | file path relative to the records folder |
| `json` | the whole record as JSON (query it with `json_extract`) |

### `applications`

| Column | Meaning |
|---|---|
| `id` | application ID |
| `name` | application name |
| `commit_hash` | pinned upstream commit |
| `language` | source language |
| `parallel_model` | parallel model (vocabulary `parallel_models`) |
| `domain` | domain (vocabulary `domains`) |
| `json` | the whole record |

### `kernels`

| Column | Meaning |
|---|---|
| `id` | kernel ID |
| `name` | kernel name |
| `application` | application ID |
| `baseline_implementation` | ID of the baseline implementation |
| `json` | the whole record, including the correctness check |

### `implementations`

| Column | Meaning |
|---|---|
| `id` | implementation ID |
| `name` | implementation name |
| `kernel` | kernel ID |
| `function` | function name in the code |
| `origin` | origin kind (vocabulary `implementation_origins`) |
| `is_baseline` | 1 if the kernel names it as its baseline |
| `json` | the whole record: code, build, run, loops, access patterns |

### `access_patterns`

The adjacent `implementation_contexts` table stores each implementation's resolved
`application`, `source_ancestor`, `source_baseline`, `comparison_baseline`, and full
context `json`. These are regenerated from authoritative source records. Its
`implementation` key identifies the same row in `implementations`; the older
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

### `steps`

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

### `inputs`

| Column | Meaning |
|---|---|
| `id` | input ID |
| `name` | input name |
| `generator_arguments` | generator arguments (null for a file input) |
| `file_path` | file path (null for a generated input) |
| `json` | the whole record |

### `input_properties`

| Column | Meaning |
|---|---|
| `input` | input ID |
| `name` | property name (vocabulary `input_properties`) |
| `value` | value as JSON text |
| `basis` | basis of the value |

### `machines`

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

### `machine_flags`

One row per ISA flag of each machine (`cpu.flags`; empty for a 0.2 machine without flags).

| Column | Meaning |
|---|---|
| `machine` | machine ID |
| `flag` | one `lscpu` flag name, e.g. `avx512f` |

### `strategies`

| Column | Meaning |
|---|---|
| `id` | strategy ID |
| `name` | human name |
| `target` | vocabulary `strategy_targets` |
| `json` | the whole record: effect, parameters, preconditions, benefits_when |

### `strategy_effects`

One row per effect item, in order.

| Column | Meaning |
|---|---|
| `strategy` | strategy ID |
| `position` | 0-based position in `effect` |
| `kind` | vocabulary `effect_kinds` |
| `json` | the effect item |

### `strategy_intrinsics`

| Column | Meaning |
|---|---|
| `strategy` | strategy ID |
| `intrinsic` | one ID from its `common_intrinsics` |

### `applied_strategies`

One row per `applies` item of each implementation.

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `position` | 0-based position in `applies` (the order applied) |
| `strategy` | strategy ID |
| `target` | loop or access-pattern ID, or `input` |
| `parameters_json` | the parameter values as JSON |

### `implementation_intrinsics`

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `intrinsic` | one ID from its `uses_intrinsics` |

### `intrinsics`

| Column | Meaning |
|---|---|
| `id` | intrinsic ID (the C name without leading underscores) |
| `name` | exact C name |
| `isa_family` | vocabulary `isa_families` |
| `isa_extensions` | JSON list of the extensions it needs (also one row each in `intrinsic_extensions`) |
| `header` | the header that declares it |
| `memory_kind` | vocabulary `intrinsic_memory_kinds` |
| `address_shape` | the address shape the instruction forms, or null |
| `element_bits`, `lanes` | element width and elements per call, or null |
| `json` | the whole record |

### `intrinsic_extensions`

| Column | Meaning |
|---|---|
| `intrinsic` | intrinsic ID |
| `extension` | one ISA extension it needs (vocabulary `isa_extensions`) |

### `profiles`

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

### `metrics`

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

### `library_entries`

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

### `library_dependencies`

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `dependency` | an entry in its dependency closure (intrinsics, lowerings, operations, a cited contract) |
| `content_sha256` | that dependency's current content hash |

### `library_clauses`

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `clause` | clause ID (for example `L1` or `BC-L1`) |
| `role` | precondition, postcondition, frame, legality, or preservation |
| `discharge_mode` | how the clause is discharged (differential_test, assumed, ...) |
| `negative_control` | the named control that must be rejected, or `none` |
| `statement` | the natural-language statement |

### `statements`

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

### `statement_steps`

| Column | Meaning |
|---|---|
| `implementation` | implementation ID |
| `statement` | statement ID |
| `pattern` | access-pattern ID the statement realizes |
| `step` | step position in that access pattern |

### `statement_facts`

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

### `library_pattern_keys`

One row per pattern of a library entry's `pattern_key` (rewrite contracts and library
operations), in key order.

| Column | Meaning |
|---|---|
| `entry` | library entry ID |
| `key_position` | the pattern's position in the key (0 first) |
| `update_kind` | the update kind it matches |
| `step_count` | the chain length it matches (the longer of its roles and address shapes) |

### `library_pattern_key_steps`

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
swdb sql "select distinct kernel, implementation from steps join access_patterns using (implementation, pattern)
          where address_shape = 'ranged_indirect'"

# intrinsics a machine can run (every extension is among its flags)
swdb sql "select i.id from intrinsics i where not exists (select 1 from intrinsic_extensions e
          where e.intrinsic = i.id and e.extension not in (select flag from machine_flags where machine = 'mbit10'))"

# median time per thread count for one implementation on every input
swdb sql "select p.input, m.threads, m.value from metrics m join profiles p on p.id = m.profile
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
| `reason` | why `headroom` is NULL: `unknown_estimate`, `zero_limit`, `unknown_limit` (floor), or the catalog bound's reason (`needs_rewritten_counts`, `unknown_catalog_entry`, `no_catalog_match`, `no_site_finder`) |
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
| `seconds` | the entry's estimate on the region's own counts (NULL if unknown) |
| `reason` | why `seconds` is NULL: `needs_rewritten_counts`, `missing_inputs`, `no_offload_mechanism`, `entry_changed` or `not_in_library` |
| `site_finder_regions` | JSON list of the joined site-finder region IDs that apply the entry |
| `mixed` | 1 when some joined site-finder region only partly covers the region |
| `missing` | JSON list of the entry's missing counts and rates |
