# The C lowering tool, the WP adapter and the verifier lock

Created: 2026-10-14 15:10 ET, Probata proof of concept ticket 21 (the A2 tracer). Updated: 2026-10-15 ET.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/21-c-lowering-wp-tracer.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Modules", "Verifier lineup and order", "Proof-hint loop"),
map 11 items 1, 3, 8, 9, 10; 13 items 4, 6, 7; 16 items 3, 6.
Code: `swdb/c_lowering.py`, `swdb/wp_adapter.py`, `swdb/verifier_lock.py`.
Tests: `tests/test_c_lowering.py`, `tests/test_wp_adapter.py`, `tests/test_formal_frame.py`.

**In one line:** `swdb lower` turns a core-subset C++ function into C with the same names and anchors;
`swdb prove --adapter wp` runs Frama-C/WP on that C under the machine-wide lock and writes one proof record.

## `swdb lower` (the C lowering tool)

Updated: 2026-10-15 ET (explicit initialization policy; historical manifests stay immutable).

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
| `new T[n]`, `delete[] p` | `swdb_alloc_new_array_<t>((size_t)(n))`, `swdb_alloc_delete_array_<t>(p)`: allocation models whose contracts are the assumption entry "allocation succeeds" |
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
  after the globals. Each is proven once by its own record (`swdb prove --model NAME --adapter wp`, below).
- **Outside the subset:** exit 1, `unsupported construct: <what> (<file> line N)`, and nothing written.
  Examples: inheritance, virtual functions, exceptions, lambdas, RTTI, standard containers (`std::vector`
  and `std::pair` come with ticket 25) and streams, `long double`, calls of functions with no body,
  overloads, other OpenMP directives and clauses, a `return`/`break`/`continue` out of a scope that
  destroys an object. C++ that does not parse: `parse error: ...`.
- **Declaration attributes (2026-10-15 ET).** Retained local variables, function definitions,
  parameters, and summarized function declarations admit only `UnusedAttr`, `DeprecatedAttr`,
  `WarnUnusedResultAttr`, `AlwaysInlineAttr`, and `NoInlineAttr` (diagnostic/inlining metadata).
  Other declaration attributes give `unsupported construct` with their Clang attribute name;
  a local `CleanupAttr` callback is never erased. This guard covers the retained declaration
  closure; it is not a full-TU startup-effect or class/global-attribute checker.
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

Updated 2026-10-15 ET: WP methods also require the canonical boolean switch
`-wp-no-filter-init`. WP33's default initialization filter can remove an entire defined
predicate containing initializedness, including its validity conjuncts, from a non-initialization
goal. Retaining the original hypotheses avoids that loss; it adds no input premise or runtime
assumption. Methods and prelaunch setup reject omission, the opposite switch, duplicate switches
and boolean `=value` spellings. This is a new method policy; existing method versions stay immutable.

WP methods must freeze `-rte-initialized @all`. The adapter first parses and inlines
the C input, then enables this function-set option against the existing AST and runs
WP in the same fresh process. Frama-C 33's `-wp-rte` alone omits initialization checks.
The normalized pre-proof input is retained as `wp_normalized`; every generated
initialization assertion remains a proof obligation. Input memory may require explicit
`\initialized` preconditions: `\valid` establishes access bounds, not initialization.
The adapter never invents those preconditions or assumes candidate locals initialized.
For bounded jobs, the ACSL translator accepts an explicit `requires \initialized` only for a pointer
parameter backed by the harness's completely filled input buffer. It emits the requested range check
against that buffer's actual capacity. Heap/global locations, summaries, runtime checks and postconditions
remain unsupported; this translation never asserts arbitrary storage initialized.
An older method without the explicit initialization flag cannot run this WP policy;
use a new method file rather than edit an existing pinned manifest.

The property reader accepts Frama-C 33's indented multiline property text as part of
the preceding TSV row. It refuses incomplete rows and keeps each property's function,
status and dependencies intact; a continuation never becomes a new unnamed property.


**Ticket 24: callees, summaries and C models.** One job proves one function, `<f>`, with everything it uses
accounted for once:

- Lowered callees (helpers, member functions, constructors, destructors, instantiated templates) are inlined
  (`-inline-calls=<every lowered callee>`), and WP proves only `<f>` (`-wp-fct=<f>`). A hint at a callee's
  anchor (for example `Bag_scale.loop1.head`) travels with the inlined copy. The verdict reader reads only
  `<f>`'s properties and goals.
- A callee that a library entry summarizes (its `proof_unit.function`, with `once: self` formal halves) stays a
  call: the lowering keeps a prototype, and WP's input puts the entry's `once: self` halves before it as the
  callee's contract. The entry's summary must have a proven record at its current content (`swdb prove --summary
  ENTRY --adapter wp`, subject `library_summary`, proven on the entry's own `proof_unit` code); the record pins
  it as `pins.summaries: [{id, sha256, proof_record}]` (ticket 22's shape) and lists it as a `summary`
  assumption entry.
- A C model (`std_min_int`, `swdb_atomic_load_n_int`, ...) must have a proven record of its own text:
  `swdb prove --model NAME --adapter wp` (no candidate) proves the model against its ACSL contract once,
  subject `{kind: c_model, id: NAME}`, code and contract pins the sha256 of the model's text. A unit pins it as
  `pins.models: [{id, sha256, proof_record}]` and lists it as a `summary` assumption entry. A missing record
  stops the job (no record): "run `swdb prove --model NAME --adapter wp` first".
- `new T[n]` and `delete[] p` call the allocation models `swdb_alloc_new_array_<t>` (n valid elements) and
  `swdb_alloc_delete_array_<t>`, whose contracts are the assumption entry "allocation succeeds" (map 16 item
  7): an `assumed_clause` entry each, no proof record. WP 33 has no deallocation (`\fresh`, `\freeable` and
  `frees` are unsupported): an index out of range reads not proven, but WP cannot see a read after
  `delete[]`; the bounded verifier (CBMC, ticket 22) models `free`.

**Hint file** (`--hint-file`): hint records `{hints: [{anchor, kind, text, provenance}]}`, merged at their
anchors only when the proof hint check accepts the set (ticket 35, updated 2026-10-14 ET:
[format-v0.4-proof-hints.md](format-v0.4-proof-hints.md)). Anchor lines stay in WP's input.

**Frozen settings** (the record's `settings`): the lineup's frama-c-wp flags (must hold `-wp-cache none`
and `-wp-model +real`), `-machdep x86_64`, `-wp-prover` in the method's exact pinned order (legacy methods without it use `alt-ergo,z3,cvc5`;
new fixture methods pin `z3,cvc5,alt-ergo`), `-wp-timeout` =
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
| `pins.summaries` | ticket 24: `{id, sha256, proof_record}` per summarized callee (library entry, content hash, its proven `library_summary` record) |
| `pins.models` | ticket 24: `{id, sha256, proof_record}` per C model the lowering calls (model name, sha256 of its text, its proven `c_model` record) |
| `pins.build_constants` | one `{name, value}` per `--define` |
| `evidence.reports` | `{name, path, sha256}` of `c_lowering`, `anchors`, `wp_input`, `hints`, `wp_log`, `wp_goals`, `wp_properties`, `handler`, all under `<runs-dir>/<record>/wp/` |
| `assumptions`, `tools` | one `trusted_tool` entry per tool, each with one plain sentence: `swdb-c-lowering-2`, `clang-22.1.8`, `frama-c-wp-33.0`, `alt-ergo-2.6.4`, `z3-5.1.0`, `cvc5-1.2.1` (IDs carry the installed versions; sha256 of each binary) |
| `assumptions` (ticket 24) | plus one `summary` entry per pinned summary and C model, and one `assumed_clause` entry ("allocation succeeds") per allocation model |
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
- Slots (2026-10-14, Yan-Ru approved two on the Mac): the policy file `<lock without .lock>.slots` (one
  integer, default 1) sets how many jobs may run at once; slot k > 1 is `<name>.slot<k>.lock`. The queue stays FIFO.
- Real WP jobs need Unix sockets (Why3's prover server in TMPDIR): inside the Claude Code Bash sandbox every
  prover call fails with a connection error, so run real-verifier tests with the sandbox off.

## The regression corpus

`tests/fixtures/proof/regression_corpus/<case>.yaml`: `{id, adapter, input, failure_class, cause}`. Each
diagnosed failure adds one case. `adapter: wp` cases rerun through `swdb prove` on the WP test seed;
`adapter: c_lowering` cases rerun through `swdb lower`. Each must give its recorded class again. One corpus
serves every adapter. Ticket 35 (2026-10-14 ET): a `wp` case whose hint the proof hint check now rejects before
WP names `hint_rule` (the check's rule) instead of `failure_class`, and reruns with the scripted WP stand-in.

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

## Checked terminal release (2026-10-15)

The C lowering version 4 records an ownership certificate for one restricted `new int[]` pattern.
Ordinary C and C++ artifacts retain `delete[]`. A separate WP view may omit the final delete only when
`swdb.terminal_release` checks all of these conditions:

- One fresh local owner, scalar `int` parameters, locals and return; no aliases, address escapes,
  reassignment, globals, calls, callbacks, extra releases or custom allocator definitions.
- A canonical complete fill loop immediately follows allocation, before any array read. Scalar locals
  initialize before use; self-initialization is rejected. This syntactic check restricts the ownership
  fragment in addition to the mandatory `-rte-initialized @all` proof obligations.
- The last two statements are exactly `delete[] owner; return scalar_expression;`, and the return does
  not read the owner. Formal halves mention only scalar parameters and result; only pre-release loop
  hints are admitted. Ghost declarations and statements are refused.

The view adds a proof obligation that the array count is nonnegative before conversion to `size_t`.
The existing allocation model requires a nonempty buffer, so zero-length arrays remain outside this
narrow path. WP must still prove all earlier accesses and scalar runtime checks; allocation success
never establishes freshness or initializedness by assumption.

The release argument is the unchanged allocation base, with no earlier release. After it, the unit
cannot observe heap lifetime or call an allocator hook. Eliding that terminal release therefore
preserves the scalar result and live caller memory under the existing ordinary allocator-model trust.
The path does not prove custom allocator side effects, resource exhaustion or general heap lifetimes.

Records pin `terminal_release_check` and `terminal_release_certificate`, keep the original lowering,
and separately report the WP view and its hash. The lowerer identity hashes both the lowering and
ownership-checker sources; the checker revalidates the exact view before hint checking and launch.
All uncertified releases and vector allocation/deallocation remain `not_proven / unsupported_construct`.
Ticket 25's WP vector-growth acceptance is still open.

## CPU effect inventory (2026-10-15)

Lowering version 5 adds generator-owned `cpu_effects` to `swdb lower` output and anchor metadata. It
lists ordinary reads, writes, calls and loop-containing functions across the entire lowered call tree.
Each source event names its function, source range and enclosing top-level statement ordinal; modeled
or unresolved effects keep unknown locations explicit. Matching tile probes cover their accesses;
ordinary arrays, dereferences, references, members, globals, atomics, escaped local storage and opaque
summaries remain visible. Pure local scalar operations need no ordinary-memory hazard probe.

This inventory supports conservative DX100 admission until ticket 28 models full cache-line hazards.
It does not prove a lack of interference. The admission policy rejects ordinary writes and permits
ordinary reads around device stores only when an acyclic unit-only prefix establishes strict statement
ordering. Same-expression order, callee order and loop iterations are not inferred from source offsets.

The lowerer identity hashes the lowering, ownership checker, effect collector and CPU admission policy
sources together. An absent policy has an explicit hash marker; adding or changing it changes the pin.
The final method draft must pin the integrated policy, not an intermediate lowerer-only checkout.


Terminal-release checker version 2 permits checked initialization loop invariants and gives the WP
view's valid, nonempty allocator result an equivalent `+ 0` pointer initializer. WP 33's modular call
rule binds return values without marking the receiving local initialized; ordinary expression
assignment tracks it. This preserves the pointer value under the existing nonempty allocation
contract, adds no heap initializedness or freshness premise, and leaves native artifacts unchanged.
An ignored unfilled-array read remains a failed initialization obligation.

Automatic storage admission (2026-10-15): CPU effects also list `local_storage` for local arrays and
aggregates, and for address-taken local or by-value parameter slots even when uninitialized. Pending
device reads can otherwise retain addresses after those objects cease to exist. Until a checked
ownership boundary models that lifetime, DX100 units with such storage are refused conservatively.
Passing a caller-owned buffer pointer by value does not give the callee ownership of its pointee;
taking the address of the pointer parameter itself exposes its callee-owned slot and is refused.


Checked memberwise copies (2026-10-15): lowerer7 emits a named `\valid_read` and `\initialized`
assertion on the exact source lvalue before ordinary implicit local/member copy construction. The
source must be a simple side-effect-free lvalue; self-initialization and copies in for initializers
are refused. Ordinary implicit/defaulted assignment is refused until its expression ordering has a
checked lowering. By-value copy expressions and returned copied objects remain outside the subset.
Modeled `std::pair` retains its separate initialized-source model contract. These are conservative
proof-subset restrictions: [CWG2264](https://www.open-std.org/jtc1/sc22/wg21/docs/cwg_active.html#2264)
still discusses the C++ treatment of copying indeterminate members; C struct assignment alone cannot
justify erasing that question. The generated assertion is a proof obligation, never an assumption.

Checked pointer formation (2026-10-15): lowerer9 records `pointer_bounds` in command output and
anchor metadata across the complete emitted function closure. WP33's RTE checks alone omit discarded
pointer addition. The WP view adds separately named assertions at the original statement's entry.
They are checked obligations, never assumptions; every failed or missing obligation stops proof.

Admission first certifies a typed array origin. The supported origins are concrete local/global
one-dimensional primitive arrays, immutable aliases to them, the existing checked nonescaping
terminal `new int[]` owner, and exact audited DX100 independent tile rows. Each semantic origin pins
the entry, model contents and generated geometry and is revalidated before launch. Rebinding,
address escapes and unknown calls invalidate pointer aliases. Embedded/multidimensional arrays,
untracked pointer casts and opaque returned pointers are refused. Ordinary indexing is inventoried
through the entire emitted callee closure too. Incoming primitive parameters can declare
`proof_unit.array_domains: {p: {extent: n}}`. This is an explicit typed-array-window input-contract
premise; concurrency-frame array lists and `valid` ranges do not supply it. The binding freezes every
extent parameter at entry, pins the formal half, and is independently regenerated from the source AST
before launch. Stable direct aliases preserve the window. Rebinding, shadowing, address escape and
unmodeled pointer calls refuse. Imported domain-bearing summaries also refuse without checked caller
discharge, including when the caller has no domain declaration.

WP checks named obligations for nonnegative extent, target byte capacity, null implying an empty
window, formation within the inclusive one-past range, and accesses within the strict element range.
These assertions add no preconditions. Existing RTE obligations still check memory access and
initializedness. The typed-window premise is advertised by the input contract; WP33 does not establish
the complete realizability of that premise together with arbitrary formal preconditions. Smoke checks
cover their projected ACSL preconditions. Opaque model and callee parameter origins remain unsupported.

C++17 permits null-pointer plus/minus zero. Supported side-effect-free expressions use
`offset == 0 ? base : original_expression`, preserving that result without executing C null
arithmetic. An exact AST integer literal zero reduces to the base; an exact nonzero literal retains
the original arithmetic. This avoids generating a dead conditional branch while retaining the same
checked bounds. An otherwise unknown origin receives a checked null-only obligation. Invalid nonnull
pointers receive no zero-offset exemption. Legal one-past formation of certified flat arrays remains
supported. Mutating arithmetic, pointer subtraction and conditional/effectful placement are refused
until their evaluation has a precise policy.

Generated C model proofs independently inventory every defined function with Clang. They receive no
blanket exemption from a content hash. Opaque model-parameter arithmetic/indexing is likewise refused
until a checked model domain exists; this currently leaves the copy model's desired positive
acceptance pending. Its C body handles empty/null ranges without C-only arithmetic and explicitly
requires its nonnegative distance to fit `ptrdiff_t`. Before launch the setup check regenerates the
complete model view or source assertions. The checker identity includes these policy/generator bytes.

Closed-vector origins (2026-10-15): the exact two-allocation owner view carries both a source
registry and an independently parsed C-view registry. The source registry binds the alias declaration
and every retained source observation by its AST range, model bytes and entry-frozen allocation
extent. The C-view registry inventories allocation, initialization loops, indexed accesses and alias
reads, checking the exact preceding range and liveness assertions. Source names are mapped to the
renamed view through this certificate; they are never emitted as unbound generic assertions. The
lowerer pins both checker modules and records `pointer_bounds.owner`. Admission and prelaunch
regenerate the original lowering and both registries and require equality. A registry alone grants
no permission to accept arbitrary `data()` results, field pointers, spare capacity or model calls.

The arithmetic boundary follows [C++17 N4659, additive operators](https://www.ece.uvic.ca/~frodo/cppdraft/n4659/html/expr.add).
[ACSL1.24's implementation manual for Frama-C33](https://frama-c.com/download/frama-c-acsl-implementation.pdf)
distinguishes allocation-block validity from same-array provenance. Actual uncached WP33 controls
confirm that `object_pointer` admits a target in an adjacent live subarray, while
`pointer_comparable` reports an undefined builtin even for a genuine flat one-past pointer. A validity
precondition on an imported summary can prove for a local/global two-dimensional row extending into
the next row; struct-member controls instead fail. Therefore block-validity checks apply only after
the conservative origin gate. These results do not establish general C++ undefined-behavior freedom.

Audited DX100 calls (2026-10-15): every imported command, query and tile-pointer producer must bind
to its exact global declaration, canonical pinned prototype and model/entry/geometry policy in a
fresh full translation-unit AST. Source definitions, namespaces, templates and unrecognized
code/linkage attributes refuse. Source declarations in the reserved `dx_`/`DX_` proof-state namespace
also refuse, preventing checked predicates from binding to caller-local state. These checks apply
even when the unit has no array-domain declaration.

The supported stream, gather and store host-pointer calls additionally need a stable explicit
primitive entry-window origin. Named assertions check each current command-state footprint against
the frozen entry extent and certified offset. Original initializedness, separation and RTE
obligations remain. Mutable-offset aliases, missing windows, pointer region/query calls without a
footprint policy, and unmodeled pointer helpers refuse. No helper premise is synthesized. Before
launch, setup reparses the complete source and rederives every call binding and live policy.

Checked contextual helpers (2026-10-15): a narrow DX100 source view expands annotation-free,
acyclic global void helpers with plain `int`/`int *` formals and bare binding/literal arguments.
Each context captures arguments once in fresh local declarations and retains every original
audited call in order. An independent full translation-unit AST comparison checks the original
body, captures, declaration bindings and expanded view. UTF-8 text is edited using Clang byte
offsets; unedited source bytes and include resolution are preserved.

This relation supplies no helper contract or entry window. The ordinary origin, call-footprint,
CPU-domain, initializedness and RTE checks still apply to the effective lowering. Source-anchored
hints are outside this initial slice. Records retain `helper_window_check`,
`helper_window_certificate`, `helper_original_source`, `helper_original_lowering` and
`helper_view_source` pins; `c_lowering` names the effective lowering. Both lowerings and the
original/view AST relation are freshly regenerated before WP. The source view persists beside
the proof evidence. A declaration alone grants no origin permission to other helpers or models.

The existing size fixture proves through this relation, while removing its original caller
initializedness leaves the stream-load precondition unproved. Original three-read source
`base[q[0]]` remains outside the supported scalar-offset grammar; helper certification does not
waive that separate nested-read obligation.
