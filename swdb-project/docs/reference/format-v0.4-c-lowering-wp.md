# The C lowering tool, the WP adapter and the verifier lock

Created: 2026-10-14 15:10 ET, Probata proof of concept ticket 21 (the A2 tracer).
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/21-c-lowering-wp-tracer.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Modules", "Verifier lineup and order", "Proof-hint loop"),
map 11 items 1, 3, 8, 9, 10; 13 items 4, 6, 7; 16 items 3, 6.
Code: `swdb/c_lowering.py`, `swdb/wp_adapter.py`, `swdb/verifier_lock.py`.
Tests: `tests/test_c_lowering.py`, `tests/test_wp_adapter.py`, `tests/test_formal_frame.py`.

**In one line:** `swdb lower` turns a core-subset C++ function into C with the same names and anchors;
`swdb prove --adapter wp` runs Frama-C/WP on that C under the machine-wide lock and writes one proof record.

## `swdb lower` (the C lowering tool)

Updated: 2026-10-14 ET (ticket 24: the declared C++ subset, naming rules `kept-names.2`, tool version 2).

```
swdb lower --source <file.cc> --function <name> --out <folder> [--include <dir>] [--define NAME[=VALUE]]
           [--summary NAME=SUMMARY]
```

- Writes `<name>.c` and `<name>.anchors.json`. Prints `{function, tool, c_lowering: {path, sha256},
  anchors: {path, sha256, count}}`, plus `summaries` and `models` when the C uses any.
- **Deterministic.** clang 22.1.8 parses the C++ (filtered `-ast-dump=json`, one dump per declaration name);
  Python prints the C. No LLM, no absolute path, no time in the output: the same input gives the same bytes.
- **Kept names** (naming rules `kept-names.2`, `swdb.c_lowering.RULES`): functions, parameters, locals,
  globals and fields keep their C++ names, so ACSL written over the C++ names type-checks against the C
  unchanged. The rules, in short:

| C++ | C |
|---|---|
| class or struct `C` | `struct C` (same fields, same order) plus `typedef struct C C;` |
| `C<int, 3>` (instantiated class template) | `struct C_int_3`; argument spelling: its C type, spaces to `_`, `*` to `ptr`, `-k` to `mk`, typedefs resolved |
| `f<long>` (instantiated function template) | `f_long` |
| member function `m` of `C` | `C_m(C *this, ...)`; `const C *this` for a const member; no `this` when static |
| `C::operator[]`, free `operator+` | `C_operator_index`, `operator_add` (table `OPERATOR_NAMES`) |
| constructor, destructor | `C_ctor(C *this, ...)` called right after the declaration; `C_dtor(C *this)` at scope end |
| `T &` | `T *`; the callee dereferences, the caller passes an address (a bound temporary: a compound literal) |
| `enum`, `enum class` | its underlying integer type (`int` if none); an enumerator prints as its value |
| `std::min`, `std::max`, `std::swap`, `std::copy` at `T` | calls of the C models `std_min_<t>`, ... (ACSL contract each) |
| `__atomic_<op>`, `__sync_<op>` at `T` | calls of the C models `swdb_atomic_<op>_<t>`, `swdb_sync_<op>_<t>` (one thread) |
| `new T[n]`, `delete[] p` | `(T *)malloc(sizeof(T) * (size_t)(n))`, `free(p)` |
| an OpenMP directive | a comment `/* omp <directive> (one thread) */`, then its statement |
| a call of a summarized function | the same (instantiated) name, a prototype only |
| an unnamed parameter | `swdb_unnamed_<n>` |

- **The subset** (map 16 item 6; ticket 21's core plus ticket 24): C plus references; classes without
  inheritance or virtual functions (fields, member functions, operators, constructors with member
  initializers, destructors); instantiated templates; `new[]`/`delete[]`; `enum class`, `constexpr`,
  `static_assert`; `std::min`/`max`/`swap`/`copy` through C models; OpenMP `parallel`, `for` (`schedule`
  static or dynamic, `nowait`), `critical`, `atomic`, `barrier`, `reduction` (`+ - * & | ^`, each use of the
  variable an `op=` update); `__sync_*` and `__atomic_*` through C models; calls named by `--summary` kept
  as calls.
- **Floating point** (asked by ticket 26): `float` and `double` types, literals and conversions print as the
  same C, so the C is faithful to IEEE semantics. A proof's meaning for them is the verifier's float model, a
  method-version choice: the frozen WP flags read `-wp-model +real` (floats as mathematical reals; the
  rounding gap is an assumption entry, map 11 item 6); `+float` would check IEEE rounding. `long double`
  stays outside.
- **One thread.** OpenMP and atomics get their meaning for one thread here: a parallel region runs as one
  thread, a CAS is a read, a compare and a write. The program for one symbolic thread of N is ticket 45.
- **Summaries.** `--summary NAME=SUMMARY` (Python: `lower(..., summaries={NAME: SUMMARY})`): every call of
  `NAME` stays a call with a prototype, and `<name>.anchors.json` lists `summaries: [{name, c_name,
  summary}]`. Every `__dxc_*` and `maa_*` call needs one; without one it is an unsupported construct.
- **C models** (`models` in `<name>.anchors.json`): static C functions with ACSL contracts, defined in the C
  after the globals. Proving each model's contract once (one proof record each) is not built yet.
- **Outside the subset:** exit 1, `unsupported construct: <what> (<file> line N)`, and nothing written.
  Examples: inheritance, virtual functions, exceptions, lambdas, RTTI, standard containers (`std::vector`
  and `std::pair` come with ticket 25) and streams, `long double`, calls of functions with no body,
  overloads, other OpenMP directives and clauses, a `return`/`break`/`continue` out of a scope that
  destroys an object. C++ that does not parse: `parse error: ...`.
- The tool's identity is `swdb-c-lowering-<TOOL_VERSION>` plus the sha256 of `swdb/c_lowering.py`;
  `swdb.c_lowering.naming_rules()` is `{id: kept-names.<n>, sha256}` of the rules text.

### Anchors

Each anchor is one comment line `/* swdb-anchor <id> */` in the C, listed in `<name>.anchors.json` as
`{id, kind, function, line}`. IDs are a deterministic function of the code's structure.

| Kind | ID | Where |
|---|---|---|
| `ghost_globals` | `ghost.globals` | one file-scope slot, after the headers |
| `contract` | `<f>.contract` | right before each function definition (the function contract goes here) |
| `entry` | `<f>.entry` | first line of each function body |
| `loop_head` | `<f>.loopN.head` | right before each loop (loop annotations go here) |
| `before`, `after` | `<f>.sN.before`, `<f>.sN.after` | around every statement, numbered in pre-order |

## `swdb prove --adapter wp`

```
swdb prove --candidate <c> --function <f> --contract <contract> --adapter wp --runs-dir <outside the repo> \
           [--hint-file <hints.yaml>] [--define NAME[=VALUE]] [--budget-minutes <n>]
```

1. Finds the one C++ file in the candidate artifact's tree that defines `<f>`, and lowers it.
2. Builds WP's input: the contract's per-candidate formal halves at `<f>.contract` (`requires` first),
   the logic-library files they use at `ghost.globals`, and fixture hints at their anchors.
3. Checks the installed tools against the pinned method version's `lineup` (Frama-C/WP, Alt-Ergo, Z3,
   CVC5, clang) and `c_lowering.translators` (the tool's ID and sha256). A mismatch runs nothing (exit 1).
4. Runs Frama-C/WP once, frozen settings, in a fresh process in the job's scratch folder (also `TMPDIR`),
   under the RSS watchdog and the wall budget.
5. Reads the verdict and runs the failure class's handler.

**Hint file** (`--hint-file`): `{hints: [{anchor, acsl}]}`. A `loop_head` anchor takes only `loop invariant`,
`loop assigns`, `loop variant`; `before`, `after` and `entry` take only `assert`. Ticket 35 replaces this
with hint records and the proof hint check.

**Frozen settings** (the record's `settings`): the lineup's frama-c-wp flags (must hold `-wp-cache none`
and `-wp-model +real`), `-machdep x86_64`, `-wp-prover alt-ergo,z3,cvc5`, `-wp-timeout` =
`budgets.wp_seconds_per_solver` (30), `-wp-par 1`, `-wp-prop=-@lemma` (ticket 26: logic-library lemmas
are proven once, with the method; see [format-v0.4-logic-library.md](format-v0.4-logic-library.md)), default
Frama-C warning levels (an annotation error aborts), a fresh session, every `FRAMAC_WP*` environment variable
removed.

**Minimal verdict reader:** proven only when every row of this run's per-property report (`-report-csv`)
is `Valid` and every goal of its per-goal report (`-wp-report-json`) passed. The consolidated summary line
is never read. Ticket 36 owns the full rule.

| Outcome | Failure class | Handler (writes `wp/handler.json`) |
|---|---|---|
| goals `timeout` or `stepout`; job over its wall budget | `timeout` | lists the goals for the hint loop (37) |
| goals `unknown` | `unknown` | lists the goals for the hint loop (37) |
| goals `failed` | `solver_error` | minimal reproduction (WP input, command) |
| Frama-C user error, annotation error | `parse_error` | minimal reproduction |
| crash, signal, internal error, other non-zero exit | `tool_crash` | minimal reproduction |
| the RSS watchdog killed the job | `out_of_memory` | keeps the class (the Mac cap stays 8 GiB) |
| the C lowering refuses the unit | `unsupported_construct` | minimal reproduction (no WP run) |
| no property and no goal | `vacuous_pass` | minimal reproduction |
| anything else | `unclassified_wp_outcome` (not a class) | none: `swdb prove` stops the batch |

WP never refutes: a not-proven record has no counterexample.

### What the record holds (on top of [format-v0.4-proof.md](format-v0.4-proof.md))

| Field | Meaning |
|---|---|
| `bounds` | `{threads: 1, input_size: unbounded}`: the C lowering is one thread; WP holds for every input size |
| `goals` | per goal: `goal`, `property`, `function`, `status` (`valid`, `timeout`, ...), `solver` (`qed`, `alt-ergo`, `z3` or `cvc5`; any one counts) and `seconds` |
| `unproven_properties` | not proven only: each per-property row that is not `Valid`: `property`, `kind`, `function`, `line`, `status` |
| `settings` | `tool`, `flags`, `session`, `warning_levels`, `machdep`, `wp_seconds_per_solver`, `environment_removed`, `rss_cap_bytes`, `hint_count`, `build_constants` |
| `pins.c_lowering` | `{id: <f>.c, sha256}` of the C lowering WP ran on |
| `pins.naming_rules` | `{id: kept-names.<n>, sha256}` of the lowering's naming rules (ticket 24); a new rules version gives a different pin |
| `pins.build_constants` | one `{name, value}` per `--define` |
| `evidence.reports` | `{name, path, sha256}` of `c_lowering`, `anchors`, `wp_input`, `hints`, `wp_log`, `wp_goals`, `wp_properties`, `handler`, all under `<runs-dir>/<record>/wp/` |
| `assumptions`, `tools` | one `trusted_tool` entry per tool, each with one plain sentence: `swdb-c-lowering-2`, `clang-22.1.8`, `frama-c-wp-33.0`, `alt-ergo-2.6.4`, `z3-5.1.0`, `cvc5-1.2.1` (IDs carry the installed versions; sha256 of each binary) |
| `evidence_kind` | `execution` under a method version whose `evidence_kind` is `execution`; `contract_fixture` under a fixture method version (and always for the scripted adapter) |

## The machine-wide verifier lock

- `swdb prove` holds it around every job of a real adapter (WP now; 22, 23, 46, 47 inherit it). The
  scripted adapter takes none.
- Same protocol as the Mac's `verifier_run.py`, so the two exclude each other: `mkdir` lock with an `owner`
  file, first-in first-out ticket files in the `.queue` folder beside it. A waiting job queues, never fails.
- Path: `SWDB_VERIFIER_LOCK`, else `/tmp/claude/swdb-verifier.lock` when `/tmp/claude` exists, else
  `/tmp/swdb-verifier-<uid>.lock`.
- Inside the holder's process tree (tests run under `verifier_run.py`) a job takes the nested lock
  `<lock>/nested` instead, so jobs there still never overlap.
- The RSS cap is `SWDB_VERIFIER_RSS_CAP_BYTES` (default 8 GiB).

## The regression corpus

`tests/fixtures/proof/regression_corpus/<case>.yaml`: `{id, adapter, input, failure_class, cause}`. Each
diagnosed failure adds one case. `adapter: wp` cases rerun through `swdb prove` on the WP test seed;
`adapter: c_lowering` cases rerun through `swdb lower`. Each must give its recorded class again. One corpus
serves every adapter.

## For later tickets

- 22/23 (CBMC): lower with `swdb.c_lowering.lower`; the bounded job adds the C-versus-C++ differential
  (pattern `tests/test_c_lowering.py::test_the_c_lowering_agrees_with_the_cpp_on_every_input_of_a_bounded_domain`
  and `prototype/06c-cbmc/faith/`). Take the lock through `swdb prove` (set `real = True` on the adapter).
- 24 (done 2026-10-14): the subset above; `TOOL_VERSION` 2, naming rules `kept-names.2`. The tool's lowering
  of spike (b)'s unit 1 agrees with the hand lowering `prototype/06c-cbmc/unit_peter.c` on every bounded input
  (`tests/test_c_lowering.py`, fixture `tests/fixtures/proof/lowering/spike_peter_unit.cc`).
- 25: `std::vector`/`std::pair` models go next to the `std::*` models (`_Printer._std`); add the types to
  `c_lowering.STD_CONTAINERS` handling. 45: replace the one-thread OpenMP and atomic models.
- 34/35/37: anchors from `<f>.anchors.json`; hints placed by `WpAdapter._input`; goals to retry from the
  record's `goals` and `unproven_properties`.
- 36: replace `read_outcome` with the full reading rule; keep the class table above.
