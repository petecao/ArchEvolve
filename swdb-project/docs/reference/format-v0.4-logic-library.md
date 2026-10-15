# The logic library and the sum library

Created: 2026-10-14 16:15 ET, Probata proof of concept ticket 26.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/26-logic-and-sum-libraries.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Modules": logic library; "Records and levels"; "Proven once vs
per candidate"), map 16 items 2, 9, 12; 24 item 4; 27 item 3.
Code: `swdb/logic_library.py`, `swdb/formal_frame.py`, `swdb/level_rule.py`, `swdb/wp_adapter.py`.
Tests: `tests/test_logic_library.py`, `tests/test_formal_frame.py`.

**In one line:** formal halves call shared ACSL definitions from versioned files; every proof pins the files
it used, the files' lemmas are proven once (with the method), and WP must not prove `\false` from any file.

## Files

| File | ID | Who may use it |
|---|---|---|
| `library/logic/<name>.acsl` | `logic.<name>` | any entry (list it in `acsl.uses`) |
| `<entry file>.acsl` beside an entry's YAML | `logic.<entry ID>` | only that entry |

- **First line:** `// version: <dotted numbers>` (for example `// version: 1.0`). `swdb validate` refuses a
  file without it.
- **Content:** the allowed-ACSL rules of [format-v0.4-formal-frame.md](format-v0.4-formal-frame.md#logic-library-files)
  (non-recursive or primitive-recursive definitions, inductive definitions only in lemmas, no axiom).
- **Type check:** `swdb validate` parses and type-checks every file that passes those rules on its own with
  Frama-C 33.0 (`N logic file(s) type-checked`). Without Frama-C each file prints `UNCHECKED:` and counts as
  unchecked, never valid.
- **Proof hints:** a shared file's hints are in `library/logic/proofs/<name>/` (`hints.acsl`: WP strategy
  annotations; `script/*.json`: the scripts they generated). An entry's own file uses `<entry file>.proofs/`.

### The shipped files (version 1.0)

| ID | Holds | Lemmas |
|---|---|---|
| `logic.csr_graph` | CSR graph model: `csr_offsets`, `csr_ends_in`, `csr_graph`, `csr_edges`, `csr_degree`, `csr_edge_of`, `csr_adjacent` | none |
| `logic.sets` | set helpers over array prefixes and flag arrays: `in_prefix`, `distinct_prefix`, `prefix_subset`, `prefix_in_range`, `count_of`, `flag_set`, `flags_match_prefix` | none |
| `logic.access` | accessors over the C lowering's arrays: `at`, `at_real`, `unreached`, `same_prefix` | none |
| `logic.sum` | the sum library (below) | 17 |

## The sum library (`logic.sum`)

Over reals (`-wp-model +real`; float memory reads as reals).

| Name | Meaning |
|---|---|
| `sum_n(x, a, lo, n)` | sum of `x[a[j]]` for `j` in `[lo, lo + n)`; recurses on the count `n` under `n <= 0` |
| `range_sum(x, a, lo, hi)` | the **range sum** over `[lo, hi)` = `sum_n(x, a, lo, hi - lo)` (0 when `hi <= lo`) |
| `fsum_n`, `filtered_sum(x, a, off, v, lo, hi)` | the **filtered sum**: the part of the flat edge range `[lo, hi)` that vertex `v` owns under offsets `off` |
| `ADDITIVITY` | `range_sum(lo, hi) == range_sum(lo, mid) + range_sum(mid, hi)` for `lo <= mid <= hi` |
| `REGROUP_OWNER`, `REGROUP_TOTAL` | **regrouping** a flat edge range by owner vertex: per vertex, and summed over all vertices |
| `PERMUTATION` | **permutation** of a finite sum: `range_sum(x, b, 0, n) == range_sum(x, a, 0, n)` when `b[j] == a[p[j]]` for a bijection `p` |

The other 13 lemmas are steps toward these four. Library rule (ticket 08): a lemma statement reads `int`
memory only through non-recursive wrappers (`sum_term`, `col_val`, `perm_pick`, `clip_lo`, `clip_hi`), because
WP adds an `is_sint32` premise for each top-level read and that premise blocks reusing the lemma.

## `swdb prove-logic`

```
swdb prove-logic --runs-dir <outside repo> --lemmas <logic ID> [--file <version>] [--generate-scripts]
swdb prove-logic --runs-dir <outside repo> --false-check <logic ID> [--file <version>] [--timeout S]
swdb prove-logic --runs-dir <outside repo> --program <file.c> --uses <logic ID>... [--define NAME[=VALUE]]
```

- Each run: Frama-C/WP 33.0 with the method version's lineup (checked first; a mismatch runs nothing),
  `-wp-model +real`, a fresh session, `-wp-par 1`, the x86_64 machdep, inside the machine-wide verifier lock and
  the ~8 GB RSS watchdog. Logs and reports go to `--runs-dir/<record>/`, named in `evidence` by path and sha256.
- `--file` checks a proposed version (not yet the library's file) under the same ID.
- `--skip-subset-check`: negative controls only (runs a file that breaks the allowed-ACSL rules; the record's
  provenance says so).

| Run | Subject | Proven means | Not proven / refuted |
|---|---|---|---|
| `--lemmas` | `method_part` `logic_lemmas` (an entry's own file: `contract_proof_part` `contract_logic_lemmas`) | every lemma has a goal and every goal is valid, with the saved scripts replayed | not proven, with a failure class |
| `--false-check` | `method_part` `logic_false_check` (own file: `contract_logic_false_check`) | no solver proved `\false` within the budget (default 10 s per solver). **Evidence, not a consistency proof.** | **refuted**: WP proved `\false`; exit 1, "`<id> <version>` is refused" |
| `--program` | `calibration_program` (ID: the file name) | the program's own contract is proven, library lemmas excluded | not proven, with a failure class |

- **How the `\false` check reaches every definition:** WP sends a solver only the definitions a goal
  mentions (research 13, Q2). The generated lemma `SWDB_FALSE_CHECK` mentions every definition of the file,
  each inside an uninterpreted wrapper (`swdb_keep_integer`, `swdb_keep_real`), after all the file's lemmas.
  Its hypothesis is satisfiable unless the definitions and lemmas are inconsistent.
- **`--generate-scripts`:** a maintainer step. It runs the hint strategies with prover `tip`, replaces
  `script/` in the proofs folder and writes no record. Then run `--lemmas` again to replay.

## Pins and levels

- **`pins.logic`:** `[{id, version, sha256}]`, one per logic file. `swdb prove` writes it for the files the
  contract's per-candidate formal halves list (`acsl.uses`), whatever the adapter; `swdb prove-logic` for the
  file it checked or the files a program used. Written only when a file is used.
- **The level rule** (`swdb.level_rule`, rule 1) reads it:
  - the record stops counting when a pinned file's sha256 differs from the current file (an edit makes a new
    hash; a re-run records the new pin);
  - a record that pins a shared file with lemmas depends on a counting proven `logic_lemmas` record of that
    exact sha256; without one it stops counting ("no counting proof of the lemmas of ...");
  - a counting refuted `logic_false_check` (or `contract_logic_false_check`) record voids every record that
    pins the same file sha256 (vocabulary `proof_part_names`, `voids: logic`), even when that version is not
    the library's file.
- An entry's own file is a contract-proof part: its records pin the contract, so the level rule's existing
  contract-part dependency covers it.
- **WP adapter:** `swdb prove --adapter wp` passes `-wp-prop=-@lemma`, so a candidate's run takes the library
  lemmas as proven once and spends no solver time on them.
- **Database:** `swdb_proof_pins` holds one row per logic file (`kind` `logic`, `value` = version).
