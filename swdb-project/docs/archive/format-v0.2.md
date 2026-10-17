# SW Database record format, version 0.2

Navigation updated: 2026-09-28 (Eastern Time).

- Version: 0.2, 2026-09-22
- Author: Yan-Ru Jhou
- Status: enforced. `swdb validate` checks every rule on this page; the schemas in
  `schemas/` and the vocabularies in `vocab/` are the machine-readable form. Supersedes
  [format proposal v0.1](format-proposal-v0.1.md).
- Words: [GLOSSARY.md](../../GLOSSARY.md). Decisions: [ADR 0001](../adr/0001-kernel-identity-is-its-correctness-check.md)
  (kernel identity), [ADR 0002](../adr/0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md)
  (YAML master copy), [ADR 0003](../adr/0003-access-pattern-is-a-chain-of-steps.md) (chains of steps).

## 1. Rules that hold everywhere

1. One record per YAML file under `records/`. Folders are for people; records refer to
   each other by ID only, so files can move.
2. IDs match `^[a-z0-9][a-z0-9._-]*$`, are unique across all records, and are never
   reused or renamed.
3. Unknown keys are errors, except under `extensions`, which takes anything; nothing under
   it is checked (not even `evidence_refs`). A new field starts there and moves into the
   schema once it is agreed.
4. Term lists live in `vocab/<name>.yaml`, one file per list, each value with a one-line
   `meaning` (and, for `metrics`, a `unit`). A field marked *vocab X* accepts exactly the
   values in that file; adding a value is a one-file change.
5. Every semantic fact states its `basis` (vocab `basis`). `basis: unknown` requires
   `value: null`; any other basis requires a value. Unknown never means false.
6. Every count states its `scope` (vocab `count_scopes`). Every metric has the `unit` its
   vocabulary entry gives.
7. Element counts are formulas over input property symbols; nothing is inferred from
   iteration counts.
8. Raw tool output stays outside git; records point to it (`runs_folder`, `raw_files`).
9. The YAML files are the master copy; SQLite is generated (see [database.md](../reference/database.md)).

Changes from 0.1: `option` became `implementation`; code, loops, access patterns, and
semantics moved from the kernel to the implementation; the `changes` field is gone (every
implementation carries its full semantics); access patterns are chains of steps; the
kernel is defined by its correctness check.

## 2. Versioning

`schema_version` is `"MAJOR.MINOR"`; the tool accepts `"0.2"`.

- **Minor** (0.2 → 0.3): only additions that every existing record still satisfies — a
  new optional field, a new vocabulary value, a new record kind, a new metric name
  (counter metrics will arrive this way). Old records need no edit; bump
  `schema_version` when a record starts using the addition.
- **Major** (0.x → 1.0): anything that can make an existing valid record invalid or change
  its meaning — renaming or removing a field, making a field required, narrowing a type,
  removing or redefining a vocabulary value. A major change ships with a migration script
  that rewrites every record, and the tool accepts only the new version afterwards.
- **Deprecation**: a record that should no longer be used keeps its file and ID, sets
  `status: deprecated`, and names its replacement in `deprecated_by`, which must be an
  existing record of the same kind. References to it keep resolving. A vocabulary value is
  deprecated by saying so in its `meaning`; removing it is a major change.

## 3. The envelope (every record)

| Field | Type | Rule |
|---|---|---|
| `kind` | vocab `record_kinds` | selects the schema |
| `schema_version` | `"0.2"` | required |
| `id` | ID | required, unique, stable |
| `status` | `draft`, `reviewed`, `deprecated` | agents' records stay `draft` until a person reviews them |
| `deprecated_by` | ID or null | required when `status: deprecated`; an existing record of the same kind |
| `created`, `updated` | `YYYY-MM-DD` (Eastern) | required |
| `provenance` | list, at least one | where the record's information came from (same shape as the HW side's workload provenance) |
| `notes` | list of text | free notes |
| `extensions` | mapping | anything; the only place unknown keys are allowed |

Each `provenance` entry: `id` (unique within the record; `evidence_refs` point here),
`kind` (vocab `provenance_kinds`: source_code, measurement, human_report, agent_run,
paper), `description`, `uri` (or null).

### Shared shapes

**Fact** — `{value, basis, evidence_refs, note}`. `evidence_refs` lists provenance IDs of
the same record. Typed facts restrict `value` (boolean, integer, or a vocabulary value)
but keep the basis rule.

**Count** — `{value, formula, scope, basis, evidence_refs, note}`: a number (`value`) or a
`formula` over input property symbols, a required `scope`, and a `basis`; with
`basis: unknown` both `value` and `formula` are null.

**Code reference** — `{root, path, lines, excerpt, sha256}`. `root` is `application` or `records`: `root: application` means
`path` is inside the application's local copy (`source.local_path`); `root: records`
means inside the records folder (code stored next to its record). `lines` is
`[first, last]`; `excerpt` must equal those lines of the file; `sha256`, if given, must
match the whole file.

**Formula** — an expression with `+ - * //`, parentheses, integers, and names from vocab
`input_properties` (for example `num_nodes + 1`). Evaluated on an input's properties; a
symbol the input does not define is an error, and a symbol whose value is unknown makes
the result unknown (null), never a guess.

## 4. `application`

| Field | Meaning |
|---|---|
| `name` | human name |
| `source` | `origin` (vocab `source_origins`), `uri`, `commit` (40 hex characters), `local_path` (the copy in this repo, or null) |
| `license` | SPDX identifier |
| `language` | source language and standard |
| `parallel_model` | vocab `parallel_models` |
| `build` | `command` and `flags` of the application's own build |
| `domain` | vocab `domains` |

## 5. `kernel`

A computation defined by what it computes and by its correctness check (ADR 0001).

| Field | Meaning |
|---|---|
| `name` | human name |
| `application` | ID of the application (the application does not list its kernels) |
| `computes` | what the result is, including defaults that change it |
| `correctness_check` | how to decide that code implements this kernel (below) |
| `baseline_implementation` | ID of the implementation found in the application; it must name this kernel |

`correctness_check`: `command` (template; `{binary}` and `{input_args}` are filled in),
`verifier` (`description` and `code`, a code reference to the verifier), `pass_criterion`
(in words), `pass_regex` (the check passes when the command exits 0 and its output
matches), `tolerance` (`value`, number or null if exact; `measure`, what is compared;
`note`).

## 6. `implementation`

Code that realizes a kernel, with everything about how it touches memory.

| Field | Meaning |
|---|---|
| `name` | human name |
| `kernel` | ID of the kernel it implements |
| `function` | function name in the code |
| `origin` | `kind` (vocab `implementation_origins`), `description`, `derived_from` (implementation ID or null) |
| `code` | list of code references; the first is the file that is built, with the kernel function's `lines` and `excerpt` |
| `build` | `compiler`, `flags`, `command` (template: `{cxx}`, `{flags}`, `{source}`, `{app}`, `{records}`, `{binary}`) |
| `run` | how `swdb profile` runs it (below) |
| `loops` | the loops, outermost first (below) |
| `access_patterns` | one per memory-access expression (below) |

`run`: `command` (template: `{binary}`, `{input_args}`, `{trials}`), `timer` (vocab
`timer_formats`), `threads_env` (the variable that sets the thread count),
`sweep_log_flag` (flag that makes the benchmark print one `<step> <value>` line per outer
iteration, or null), `sweep_count_regex` (a regular expression whose one group captures a
sweep count the benchmark prints, or null), `kernel_symbols` (function names whose simulated misses count as the
kernel's), `index_stream` (or null: `order`, `in_neighbors_by_vertex` or
`out_neighbors_by_vertex`; `pattern`, the access pattern whose index stream that is;
`note`).

Each loop: `id`, `description`, `parent` (loop ID or null), `trip_count` (a count),
`parallel` (`construct` from vocab `parallel_constructs`, `schedule`, `reduction`),
`code` (a code reference to its lines), and `condition` (in words, when the loop runs only
sometimes; absent or null means always).

Each access pattern: `id` (unique in the record), `expression`, `loop` (loop ID),
`steps` (the chain), `update_kind` (vocab `update_kinds`), `update` (`pseudocode`,
`side_effects`), `semantics`, `evidence_refs`, `note`, and `condition` (as for loops;
footprints still count its arrays and say so).

Each step: `array`, `address_shape` (vocab `address_shapes`), its shape's attribute,
and `note`. The attributes are exclusive: `stream` requires `stride` (in elements; 0
means the same element is reused); `single_valued_indirect` requires `index_transform`
(vocab `index_transforms`); `ranged_indirect`, `pointer_chase`, and
`data_dependent_merge` take neither. `array` holds `name`, `role` (vocab
`array_roles`), `element_type`, `element_bytes`, `element_count` (a formula, or null
when the size depends on the data at run time; footprints then report a lower bound),
`layout` (vocab `layouts`), and optionally `undirected_alias` (the array it is the same
memory as on an undirected graph; footprints count the pair once). An array named in
several steps is one array: its type, size, and layout must agree in every step; only its
role may differ.

Chain rules: the first step is a `stream` or a `pointer_chase`; the last step's array
has role `target` and no other step's does; a `ranged_indirect` or
`data_dependent_merge` step follows a step whose array role is `offsets`; a
`single_valued_indirect` step follows a step whose role is `index`. The pattern class is
the steps' address shapes plus the update kind, e.g.
`stream > ranged_indirect > single_valued_indirect : read`.

`semantics` holds seven facts, all required:

| Fact | Value |
|---|---|
| `duplicate_target_indices` | boolean: can two accesses in one loop execution hit the same target element |
| `index_modified_during_loop` | boolean: can the loop change the index arrays it reads |
| `loop_carried_dependencies` | boolean: can one iteration of the loop depend on another |
| `shared_target_between_threads` | boolean: do several threads touch the same target elements |
| `atomic_updates_required` | boolean: must the updates be atomic for correctness |
| `ordering` | vocab `orderings` |
| `numerical_requirement` | vocab `numerical_requirements` |

## 7. `input`

| Field | Meaning |
|---|---|
| `name` | human name |
| `generator` | `application`, `tool`, `arguments` (e.g. `-g 16 -k 16`) |
| `file` | `path`, `format` (vocab `input_formats`), `sha256`, `arguments` (added after `-f <path>`) |
| `properties` | facts keyed by names from vocab `input_properties` |

Exactly one of `generator` and `file`. Typed properties: `num_nodes`,
`num_edges_undirected`, `num_edges_directed`, `requested_degree`, `scale` (integers);
`directed`, `weighted` (booleans); `degree_distribution`, `index_locality`,
`input_density` (vocabs `degree_distributions`, `index_localities`, `input_densities`). Sizes known only after a run
start as `unknown`; `swdb profile` fills them in as `measured` and refuses to overwrite a
different measured value.

## 8. `machine`

Captured from the host by `swdb capture-machine`, read-only.

| Field | Meaning |
|---|---|
| `hostname` | short host name; `swdb profile` refuses to run elsewhere |
| `cpu` | `model`, `architecture`, `sockets`, `cores_per_socket`, `threads_per_core`, `logical_cpus`, `max_mhz` |
| `caches` | list of `level`, `type` (data, instruction, unified), `size_bytes` (one instance), `instances`, `shared_by` (core or socket) |
| `memory_bytes` | total memory |
| `numa_nodes` | list of `node`, `cpus`, `memory_bytes` |
| `os` | `kernel`, `distribution` |
| `counters` | `perf_event_paranoid`, `hardware_counters_available` (a boolean fact) |
| `capture` | `command` and `date` of the capture |
| `lane_required` | host policy: when true, `swdb profile` runs only inside a verified socket lane (see mbit10-profiling.md); absent means true on a machine with more than one NUMA node, and `swdb capture-machine` writes it |

## 9. `profile`

Written by `swdb profile`, never by hand: one implementation on one input and machine.

| Field | Meaning |
|---|---|
| `implementation`, `input`, `machine` | IDs |
| `complete` | true if every part completed or was skipped on purpose |
| `build` | `compiler`, `compiler_version`, `flags`, `command`, `application_commit`, `swdb_commit`, `swdb_dirty` |
| `environment` | `host`, `binding`, `omp_places`, `omp_proc_bind`, `numactl_show`, `lane`, `load_1min`, `users`, `governor`, `no_turbo`, `started`, `finished` (UTC) |
| `runs_folder` | `host`, `path`, `note`: where the raw output is |
| `parts` | each part of the run (below) |
| `timing` | per thread count: `threads`, `trials`, `times_s`, `median_s`, `min_s`, `max_s`, `spread` ((max − min) / median), `command` |
| `counts` | named counts (each a count with a scope) |
| `metrics` | list of metrics (below) |
| `bottleneck` | the inferred bottleneck (below) |

Each part: `part` (vocab `run_parts`), `outcome` (vocab `run_outcomes`: complete,
timed_out, failed, skipped), `command`, `started`, `finished`, `timeout_s`, `exit_code`,
`raw_files` (in the runs folder), `note`. A part that times out is recorded, and the
profile is marked incomplete; it is never dropped.

Each metric: `name` (vocab `metrics`), `value` (a number, or a structure such as a
histogram, or null with `basis: unknown`), `unit` (the vocabulary's), `basis`, and where
they apply `threads`, `array`, `scope`, `tool`, `evidence_refs`, `note`.

`bottleneck`: `value` (vocab `bottleneck_classes`, or null), `basis`, `memory_limit`
(vocab `memory_limits`, or null), `rests_on` (metric names it follows from),
`evidence_refs`, `note`. On a machine whose `hardware_counters_available` is not true,
the basis cannot be `measured` or `simulated`: it is `inferred` (or `unknown`).

## 10. The workload view

`swdb view <implementation> <input> <machine>` prints the HW side's workload format
(`archevolve/hw_ensemble/sparta-sort.input.yaml`): `workload_id` is
`<implementation>@<input>@<machine>`; every key of that format is present with the same
nesting; element counts are the formulas evaluated on the input (null when unknown);
semantic values appear as values, with their basis and evidence under the added key
`semantics_evidence`; counts, metrics, and bottleneck come from the newest complete
profile and are explicitly unknown when there is none. Added keys (`address_chain`,
`pattern_class`, `element_count_formula`, `semantics_evidence`, and the filled `code` and
`environment`) extend the format without renaming anything.
