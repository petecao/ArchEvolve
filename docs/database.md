# The SQLite database

Updated: 2026-09-23

`swdb build` writes `build/swdb.sqlite` next to the repo's `records/` folder (another
records folder `X` gets `build/swdb-X.sqlite`; `build/` is ignored by git). It deletes and
recreates every table from the YAML records each time, so the file never drifts from them
(ADR 0002). The `meta` table names the records folder and a fingerprint of its files (path,
size, and modification time of each); `swdb find`, `swdb implementations`, `swdb strategies`, and `swdb sql`
rebuild the file first unless the folder and the fingerprint match the folder being queried
and the file was built by the same `swdb` code (so a newer `swdb` never queries a file that
lacks its tables or fills them differently).

Run your own SQL with `swdb sql "<query>" [--format json]`, or open the file with the
`sqlite3` shell. Values that are JSON in the records (semantic values, property values)
are stored as JSON text, so `true`, `false`, and `null` stay distinct: compare with
`= 'true'`, `= 'false'`, or `= 'null'`, and check the matching `_basis` column
(`unknown` never means false).

## Tables

### `meta`

| Column | Meaning |
|---|---|
| `key` | `records_dir` (the absolute records folder the file was built from), `fingerprint`, or `builder` |
| `value` | the folder; the sha256 over every record file's path, size, and modification time; or the sha256 of the `swdb` package's code, so any change to the tool rebuilds the file |

### `records`

One row per record, whatever its kind.

| Column | Meaning |
|---|---|
| `id` | record ID |
| `kind` | record kind (application, kernel, implementation, input, machine, profile, strategy, intrinsic) |
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
| `basis` | measured, simulated, inferred, or unknown |
| `threads` | thread count, for per-thread metrics |
| `array_name` | the array, for per-array metrics |
| `scope` | count scope, where one applies |
| `tool` | the tool that produced it |

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
