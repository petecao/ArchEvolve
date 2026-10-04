# Adding an application and its kernels

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-09-23

A step-by-step procedure for a collaborator who brings a new application (or a new kernel
of gapbs). You need the repo, Python 3.12 with PyYAML and jsonschema, and the source of
the application. The full field reference is [format-v0.3.md](format-v0.3.md); the words
used here are defined in [CONTEXT.md](../../CONTEXT.md). Model records to copy from:
`records/kernels/gapbs-pr.yaml`, `records/implementations/gapbs-pr-gs.yaml` (baseline),
`records/implementations/gapbs-pr-jacobi.yaml` (non-baseline, code stored next to it).

Run `python3 -m swdb validate` after every step (a kernel names its baseline
implementation, so write the kernel and its baseline implementation before validating
them together). It names the file, the field, and the reason for each error.

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

Every kernel and implementation record also needs its own `source_code` provenance entry
(what you read, which lines, the commit, the date), and every `evidence_refs` entry must
name a provenance `id` of the same record.

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
  (`value`, `measure`; `value: null` when there is no numeric tolerance, either because
  results must match exactly or because the check is structural and accepts many valid
  results, such as any valid BFS tree — say which in `measure`).
- `baseline_implementation`: the ID of the implementation you write next.

## 3. Each implementation

Write `records/implementations/<id>.yaml`. For the baseline, the code stays in the
application copy (`code[0].root: application`); for any other implementation, put its
code file in `records/implementations/<id>/` (`root: records`) with its `sha256`.

1. `kernel`, `name`, `function`, `origin` (`kind` from `implementation_origins`).
2. `code`: the function with `root`, `path`, `lines`, and `excerpt` copied exactly.
   `swdb validate` compares the excerpt with the file. If the kernel spans several
   functions, add one code entry per function; `code[0]` must be the file that is built.
3. `build`: `compiler`, `flags`, and `command`, a template with `{cxx}`, `{flags}`,
   `{source}` (the first code file), `{app}` (the application copy), `{binary}`. Code
   stored next to its record needs the application's headers on the include path:
   `"{cxx} {flags} -I {app}/src {source} -o {binary}"`.
4. `run`: `command` (template with `{binary}`, `{input_args}`, `{trials}`), `timer`
   (vocabulary `timer_formats`), `threads_env`, and optionally:
   - `sweep_log_flag`: only if that flag makes the benchmark print exactly one line of two
     fields, `<step number> <value>`, per outer iteration; sweeps are the largest step + 1.
   - `sweep_count_regex`: if the benchmark prints the count instead (for example
     `Shiloach-Vishkin took (\d+) iterations`), a regular expression whose one group
     captures it.
   - `kernel_symbols`: every function of the kernel. Cachegrind's kernel-only counts sum
     the functions whose names match, including their OpenMP outlined bodies; helpers
     inlined into them count, but library loops with their own outlined bodies (such as
     `pvector::fill`) do not — say so in `notes`.
   - `index_stream`: `order` is `in_neighbors_by_vertex` or `out_neighbors_by_vertex`
     (for u = 0 .. N−1 in order, every neighbor in stored order, as one thread would see
     it). Set it only when that is exactly the order the kernel reads the pattern's index
     array in each sweep; traversals that follow a frontier, sample neighbors, or relabel
     the graph first do not qualify.
5. `loops`: one entry per loop that matters, outermost first: `id`, `description`,
   `parent`, `trip_count` (a count: a `formula` over input properties or a `value`, a
   `scope` from `count_scopes`, a `basis`), `parallel` (`construct`, `schedule`,
   `reduction`), the loop's `code` lines, and a `condition` in words if it runs only
   sometimes (relabeling, directed-only code). A "sweep" (`per_sweep`) is one pass of the
   kernel's outer iterative loop; for a traversal say in the loop's `description` what
   one pass is (one BFS level, one bucket, one source). A loop in a helper called from
   several places names the caller loop it mostly runs under as `parent` and lists the
   others in its `description`. Counts that depend on run parameters (`-i`, `-d`) are a
   bare `value` for the default plus a `note`; counts that depend on the data are
   `basis: unknown` with a note.
6. `access_patterns`: one per memory-access expression in the loops, each with `id`,
   `expression`, `loop` (the loop it runs in), `steps`, `update_kind`, `update`
   (`pseudocode`, `side_effects`), `semantics`, `evidence_refs`, and optional `note` and
   `condition`. A second read of the same element in the same iteration (already in a
   register or cache line) needs no pattern of its own; say so in the first one's note.
   - `steps`: the chain from the first array touched to the array read or updated.
     Each step names its `array` (`name`, `role`, `element_type`, `element_bytes`,
     `element_count` as a formula over input property symbols, `layout`) and its
     `address_shape` with that shape's attribute: `stream` needs `stride` (whole elements
     per iteration; for a bit-per-vertex bitmap read through `v // 64`, use a
     `single_valued_indirect` step with `index_transform: divide`); `single_valued_indirect`
     needs `index_transform`; `ranged_indirect`, `pointer_chase`, and
     `data_dependent_merge` take neither.
     Formulas use `+ - * //`, parentheses, integers, and names from
     `vocab/input_properties.yaml` (no functions such as `min`). When an array's size
     depends on the data at run time (per-thread bins), set `element_count: null` and say
     why in the step's `note`; never put a guessed formula there.
     The chain starts with a `stream` or `pointer_chase`; the last step's array has role
     `target`, the others `index` or `offsets`; a ranged or merge step follows an
     `offsets` step, a single-valued indirect step follows an `index` step, and a
     `pointer_chase` may follow any step (it reads the address from its own array).
     One array may appear in several steps (for example `comp` as the index and then as
     the target of `comp[comp[n]]`): its type, size, and layout must be identical in every
     step, only its role changes. Accesses whose addresses come from a random-number
     generator (sampling) fit no address shape; leave them out and say so in `notes`.
   - `update_kind`: what the pattern does to its target (`read`, `write`, `add_update`,
     `min_max_update`, `compare_and_swap`, `arbitrary`). Record the mechanism the code
     uses, and the effect in the note: an atomic min built from a CAS retry loop is
     `compare_and_swap` with the note "a min-update implemented with CAS". A plain
     (non-atomic) check-then-store, pointer jumping, bitwise OR, or scaling is `arbitrary`
     with a note.
   - `semantics`: all seven facts, each with its basis and, for anything not obvious, a
     `note` that cites the lines. `duplicate_target_indices`: can two accesses in one
     execution of the loop hit the same target element. `index_modified_during_loop`: can
     the loop change the index arrays it reads. `loop_carried_dependencies`: can one
     iteration of the loop depend on another's result. `shared_target_between_threads`:
     do several threads touch the same target elements — read-only sharing counts, and
     the note says whether anyone writes. `atomic_updates_required`: must the updates be
     atomic for the result to pass the correctness check. `ordering` and
     `numerical_requirement`: values from their vocabularies.
   - Arrays that are the same memory on an undirected graph (gapbs `out_index_` and
     `in_index_`) say so with `undirected_alias` on either side (or both); footprints count
     the pair once.

If an array size depends on an input property that no vocabulary entry names yet, add the
property name to `vocab/input_properties.yaml` (with its meaning) and give it in every
input record the implementation is profiled on; a profile whose input lacks a symbol the
formulas use fails validation.

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
