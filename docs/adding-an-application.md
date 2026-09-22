# Adding an application and its kernels

Updated: 2026-09-22

A step-by-step procedure for a collaborator who brings a new application (or a new kernel
of gapbs). You need the repo, Python 3.12 with PyYAML and jsonschema, and the source of
the application. The full field reference is [format-v0.2.md](format-v0.2.md); the words
used here are defined in [CONTEXT.md](../CONTEXT.md). Model records to copy from:
`records/kernels/gapbs-pr.yaml`, `records/implementations/gapbs-pr-gs.yaml` (baseline),
`records/implementations/gapbs-pr-jacobi.yaml` (non-baseline, code stored next to it).

Run `python3 -m swdb validate` after every step. It names the file, the field, and the
reason for each error.

## What each basis means

Every fact you record states its basis. Pick the one that says where the value came from:

| Basis | Use it when | Example |
|---|---|---|
| `measured` | a run on a real machine produced the value | edge count printed by gapbs; trial times |
| `simulated` | a model of a machine produced it | cachegrind's D1 and LL misses |
| `code_reading` | you read it in the source at the pinned commit | `NodeID` is `int32_t`; the loop is `omp parallel for` |
| `reported` | a person said it, with no code or run attached | "sort() is memory bound" from a meeting |
| `inferred` | you derived it by a rule from other facts; say the rule in `note` | degree distribution of a Kronecker graph |
| `unknown` | nobody knows yet; the value must be `null` | edge count before any run |

Unknown is never false: a semantic field you have not established is
`{value: null, basis: unknown}`, not `false`. `swdb validate` rejects a value with
`basis: unknown` and a missing value with any other basis.

## 1. The application

1. Pin the source: note the upstream URL and the full 40-character commit.
2. Under about 10 MB: copy the source unchanged into `apps/<name>/` (every tracked file
   at that commit) and add `apps/<name>/PROVENANCE.md` with URL, commit, date, license,
   and how to check the copy. Larger: write a fetch script that checks out the pinned
   commit and verifies a checksum, and leave `source.local_path: null`.
3. Write `records/applications/<id>.yaml`: `name`, `source` (`origin`, `uri`, `commit`,
   `local_path`), `license`, `language`, `parallel_model`, `build` (`command`, `flags`),
   `domain`. Copy the envelope (`kind` … `provenance`) from an existing record and write
   one `provenance` entry of kind `source_code` saying what you read and when.

## 2. Each kernel

A kernel is what is computed plus how correctness is checked (ADR 0001), not a function.
Two pieces of code that pass the same correctness check are two implementations of one
kernel (gapbs `pr` and `pr_spmv` are one kernel).

Write `records/kernels/<id>.yaml`:

- `application`: the application ID; `name`; `computes`: one paragraph of what the result
  is, including defaults that change it (iterations, tolerance).
- `correctness_check`: `command` (a template: `{binary}` and `{input_args}` are filled in,
  e.g. `"{binary} {input_args} -n 1 -v"`), `verifier` (a description and a `code`
  reference to the verifier function, with `lines` and `excerpt` copied exactly),
  `pass_criterion` (in words), `pass_regex` (what the output must match), and `tolerance`
  (`value`, `measure`; `value: null` if the check is exact).
- `baseline_implementation`: the ID of the implementation you write next.

## 3. Each implementation

Write `records/implementations/<id>.yaml`. For the baseline, the code stays in the
application copy (`code[0].root: application`); for any other implementation, put its
code file in `records/implementations/<id>/` (`root: records`) with its `sha256`.

1. `kernel`, `name`, `function`, `origin` (`kind` from `implementation_origins`).
2. `code`: the function with `root`, `path`, `lines`, and `excerpt` copied exactly.
   `swdb validate` compares the excerpt with the file.
3. `build`: `compiler`, `flags`, and `command`, a template with `{cxx}`, `{flags}`,
   `{source}` (the first code file), `{app}` (the application copy), `{binary}`.
4. `run`: `command` (template with `{binary}`, `{input_args}`, `{trials}`), `timer`
   (vocabulary `timer_formats`), `threads_env`, and optionally `sweep_log_flag` (only if
   the log prints one `<step number> <value>` line per outer iteration), `kernel_symbols`
   (function names whose simulated misses count as the kernel), and `index_stream`
   (only when the extractor's visit order is exactly the kernel's order).
5. `loops`: one entry per loop that matters, outermost first: `id`, `description`,
   `parent`, `trip_count` (a count: a `formula` over input properties or a `value`, a
   `scope` from `count_scopes`, a `basis`), `parallel` (`construct`, `schedule`,
   `reduction`), and the loop's `code` lines.
6. `access_patterns`: one per memory-access expression in the loops.
   - `steps`: the chain from the first array touched to the array read or updated.
     Each step names its `array` (`name`, `role`, `element_type`, `element_bytes`,
     `element_count` as a formula over input property symbols, `layout`) and its
     `address_shape` with that shape's attribute: `stream` needs `stride`;
     `single_valued_indirect` needs `index_transform`; `ranged_indirect`,
     `pointer_chase`, and `data_dependent_merge` take neither.
     The chain starts with a `stream` or `pointer_chase`; the last step's array has role
     `target`, the others `index` or `offsets`; a ranged or merge step follows an
     `offsets` step, a single-valued indirect step follows an `index` step.
   - `update_kind`: what the pattern does to its target (`read`, `write`, `add_update`,
     `min_max_update`, `compare_and_swap`, `arbitrary`).
   - `semantics`: all seven facts (`duplicate_target_indices`,
     `index_modified_during_loop`, `loop_carried_dependencies`,
     `shared_target_between_threads`, `atomic_updates_required`, `ordering`,
     `numerical_requirement`), each with its basis and, for anything not obvious, a
     `note` that cites the lines.
   - Arrays that are the same memory on an undirected graph (gapbs `out_index_` and
     `in_index_`) say so with `undirected_alias`, so footprints count them once.

If an array size depends on something the input records do not state yet, add the
property name to `vocab/input_properties.yaml` (with its meaning) and to the inputs.

## 4. Inputs

Write `records/inputs/<id>.yaml` with exactly one of `generator` (`application`, `tool`,
`arguments`) or `file` (`path`, `format`, `sha256`, optional `arguments`). Under
`properties`, give every symbol your formulas use, each with a basis. A size you cannot
know without running (such as the edge count after duplicate removal) is
`{value: null, basis: unknown}`; `swdb profile` fills it in as `measured`.

## 5. Check and profile

1. `python3 -m swdb validate` must print `OK`.
2. `python3 -m swdb view <implementation> <input> <machine>` shows the workload view.
   Array sizes that depend on unknown input properties show `null` until profiled.
3. Profile on mbit10 as in [mbit10-profiling.md](mbit10-profiling.md). The profile record
   is written by the tool, never by hand.
4. Open a pull request, or commit to `main` if you own the repo. Records you or an agent
   add stay `status: draft` until a person reviews them and sets `reviewed`.

## Changing a record later

Never reuse or rename an ID. To replace a record, write the new one with a new ID and
set the old one's `status: deprecated` and `deprecated_by: <new id>`; it stays in place
so references to it still resolve.
