# The SQLite database

Updated: 2026-09-22

`swdb build` writes `build/swdb.sqlite` next to the records folder (the repo's `build/` is
ignored by git). It deletes and recreates every table from the YAML records each time, so
the file never drifts from them (ADR 0002). `swdb find`, `swdb implementations`, and
`swdb sql` rebuild it first if any record file is newer than the database.

Run your own SQL with `swdb sql "<query>" [--format json]`, or open the file with the
`sqlite3` shell. Values that are JSON in the records (semantic values, property values)
are stored as JSON text, so `true`, `false`, and `null` stay distinct: compare with
`= 'true'`, `= 'false'`, or `= 'null'`, and check the matching `_basis` column
(`unknown` never means false).

## Tables

### `records`

One row per record, whatever its kind.

| Column | Meaning |
|---|---|
| `id` | record ID |
| `kind` | record kind (application, kernel, implementation, input, machine, profile) |
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
| `counters_available` | 1 if hardware counters are available to the profiling user |
| `json` | the whole record |

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
| `basis` | measured, simulated, inferred, or unknown |
| `threads` | thread count, for per-thread metrics |
| `array_name` | the array, for per-array metrics |
| `scope` | count scope, where one applies |
| `tool` | the tool that produced it |

## Examples

```
# the kernels whose implementations include a ranged-indirect gather
swdb sql "select distinct kernel, implementation from steps join access_patterns using (implementation, pattern)
          where address_shape = 'ranged_indirect'"

# median time per thread count for one implementation on every input
swdb sql "select p.input, m.threads, m.value from metrics m join profiles p on p.id = m.profile
          where p.implementation = 'gapbs-pr-gs' and m.name = 'time_per_trial_median' order by 1, 2"
```
