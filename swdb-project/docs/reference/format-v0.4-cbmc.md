# The CBMC adapter and the CBMC translator (bounded verifier, threads = 1)

Created: 2026-10-14 16:10 ET, Probata proof of concept ticket 22 (Yan-Ru's 13:19 ET decision: CBMC 6.11 on
ticket 21's C lowering replaces SAW as the bounded verifier).
Updated: 2026-10-14 17:20 ET, ticket 61: [Whole-function equivalence](#whole-function-equivalence-ticket-61)
(the bounded direct route and the no-contract baseline, CBMC on a product program).
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/22-saw-adapter-and-translator.md` (Later changes);
design: `.scratch/formal-verification-2026-10-09/spec.md` ("Verifier lineup and order", "Bounds"), map 11
items 1-4, 8, 9; 16 items 1, 3; 19 items 2, 8. Reference: `prototype/06c-cbmc/` and the shared note
`cbmc-two-lanes.md`. Code: `swdb/cbmc_adapter.py`, `swdb/cbmc_translator.py`; `swdb prove --summary` in
`swdb/proof.py`; the gate hooks in `swdb/campaign_targets.py` and `swdb/bounded_gate.py`.
Tests: `tests/test_cbmc_adapter.py`.

**In one line:** `swdb prove --adapter cbmc --bounds '{"threads": 1, "n": 3}'` lowers the proof unit to C,
checks the C lowering against the C++ on the bounded domain, runs CBMC with unwinding assertions, and writes
one proof record: proven within the bounds, refuted with concrete inputs that replay on the C++, or not
proven with a failure class.

## `swdb prove --adapter cbmc`

```
swdb prove --candidate <c> --function <f> --contract <contract> --adapter cbmc --runs-dir <outside the repo> \
           --bounds '{"threads": 1, "<integer parameter>": <size bound>, ...}' [--define NAME[=VALUE]] \
           [--budget-minutes <n>]
swdb prove --summary <library entry> --adapter cbmc --runs-dir <outside the repo> --bounds '{"threads": 1}'
```

- **Bounds.** `threads` must be 1 (threads > 1 is CIVL's and GenMC's, tickets 46 and 47). Every other
  dimension names an integer parameter of the proof unit and bounds it from above (the contract's `requires`
  bound it from below). Every interface array is that many elements long (the largest size bound). A unit
  that takes arrays needs at least one size bound. The record's `bounds` are exactly the bounds asked for.
- **Initializedness admission (2026-10-15 ET).** CBMC's nondeterministic treatment of an uninitialized
  read does not prove that the C++ read is defined. Before either native agreement or CBMC, the lowering
  supplies a checked AST inventory of the entire retained function/callee closure. Primitive automatic
  locals require an explicit initializer checked before their binding (self-initialization is refused).
  Candidate heap storage, arrays, aggregates, references, address escapes, pointer reassignment and
  unknown pointer producers/effects currently return `not_proven/unsupported_construct`. These are
  conservative language restrictions, including some safe programs; they are not UB refutations.
  Whole-function jobs check candidate and baseline independently. WP's initializedness obligations are
  separate from this bounded admission rule.
  `settings.bounded_initialization` records the checker content hash, generated certificate, source and
  lowering hashes, admitted functions, input domain and actual harness capacity. The checker source is
  part of the C lowering tool identity. The final setup check validates the certificate and capacity
  again immediately before invocation. A zero-capacity pointer job is refused: its dummy allocation
  has no initialized elements.
  The bounded input domain consists of initialized scalar values and, for each pointer parameter, its
  own nonnull, distinct primitive buffer of exactly the largest size bound. A smaller logical size
  does not shorten that allocation. Null, shorter, uninitialized or aliased caller objects are outside
  this generated domain; a success makes no memory-safety claim for those excluded objects.
  DX100 model calls additionally require an audited exact-content policy for the ghost/state/C model
  files, a fresh entry pin and identical regenerated model bytes. Model globals have static initialization;
  the harness initializes bookkeeping and draws every tile element. Every source argument is checked,
  and only the audited tile-pointer producer may introduce a model buffer origin. Changed model bytes
  require a new audit and checker identity. This policy does not grant arbitrary opaque summaries an
  initializedness exemption.
- **Unwinding.** `--unwind K --unwinding-assertions`, with K = the largest size bound + 1 (CBMC's K is
  iterations + 1). A loop that runs longer fails its unwinding assertion: not proven,
  `unwinding_bound_too_small`, never proven.
- **Build constants** (`--define`) are recorded exactly in `pins.build_constants`; the C lowering is
  preprocessed with them and the C++ side of the differential run and of the replay is compiled with them.
- **Compared knobs.** A contract knob (`knobs: [{name, range: {min, max}, legality_clause}]`) that is a global
  of the C lowering and that the code only compares is drawn symbolically, assumed within its range, and its
  legality clause's `requires` is assumed too. It is never a build constant. A knob the code uses any other
  way is refused (give it with `--define`).
- **Budget.** The job's wall budget is `--budget-minutes` (the gate passes `budgets.bounded_job_minutes`),
  default 15 minutes. Over it: not proven, `timeout`; never retried at smaller bounds.
- **Summary proofs** (`--summary`): the subject is `{kind: library_summary, id: <entry>}`; the code proven is
  the entry's `proof_unit` function against its `proof_placement: {once: self}` formal halves. The record's
  `pins.code` and `pins.contract` are the entry's content hash.

### One job, step by step

1. Lower the unit (`swdb.c_lowering.lower`). Outside the core subset: not proven, `unsupported_construct`, and
   `settings.outside_cpp_subset` names the reason. CBMC never reads the C++ (it cannot parse libc++ 22).
2. Translate (`swdb.cbmc_translator`): the unit's harness from the contract's per-candidate formal halves
   (plus knob legality clauses); for each callee that a library entry summarizes (its `proof_unit.function`,
   with `once: self` clauses), that entry's stub replaces the callee's code in the C lowering. The callee's
   summary needs a proven `library_summary` record at the entry's current content (else no job runs); the
   unit's record pins it in `pins.summaries` as `{id, sha256, proof_record}`.
3. Differential run (the check on the trusted C lowering tool): the C lowering and the C++ text of the same
   functions (cut from the source by clang's source ranges), each with the same harness and the real callees,
   run every input of the bounded domain natively (`-O0 -fwrapv`). Domain: each size parameter from -1 to its
   bound, each knob over its range (at most 16 values, else 5), every other value and array element from
   {-2, -1, 0, 1, 2} (scalar values also INT_MIN and INT_MAX); at most 20 000 runs (a fixed-seed sample
   beyond). Any difference stops the batch: no record, the message names `c_lowering_disagreement` and the
   first differing input, and `cbmc/handler.json` plus `cbmc/reproduction/` hold both sources.
4. CBMC on `job.c` (`-DSWDB_CBMC --unwind K --unwinding-assertions` plus the lineup's `cbmc` flags,
   `--json-ui`) in the job's scratch folder, under the RSS watchdog and the wall budget, inside the
   machine-wide verifier lock.
5. Read every property and run the failure class's handler.

### The harness and the stubs (the CBMC translator)

One text compiles three ways: `-DSWDB_CBMC` (CBMC), `-DSWDB_NATIVE -DSWDB_DIFFERENTIAL` and
`-DSWDB_NATIVE -DSWDB_REPLAY`. Every nondeterministic value (inputs, knobs, havocked locations, a stub's
result) comes from one oracle, `swdb_next()`: under CBMC an unconstrained array; natively one line of stdin
per run. So a CBMC trace replays as the sequence of values `swdb_next()` returned along it.

| Formal half | Harness (the unit) | Stub (a summarized callee) |
|---|---|---|
| `requires` | assumed (after the size bounds) | one named CHECK: `__CPROVER_assert` then `__CPROVER_assume` |
| `assigns` | one named property: every interface array element and scalar global outside the locations keeps its value | the locations are havocked from the oracle (a summary must have one) |
| `ensures` | one named property each | assumed, each tagged with the entry and its sha256 |
| reachability | `swdb_reach.end` must FAIL | `swdb_reach.summary.<function>` must FAIL |

Property names are `<entry>#<clause id>`, plus `.<kind><n>` when one formal half holds several statements
(for example `contract.fixture_cbmc_fill#fill_post.ensures1`). Translated ACSL: integer arithmetic in
`long long`, chained comparisons, `!`, `&&`, `||`, `==>`, `<==>`, array reads, `\result`, `\true`, `\false`,
`\old`/`\at(e, Pre)` (in a stub only over parameters), `\valid` of a pointer parameter (`p`, `p + i`,
`p + (lo .. hi)`; in a stub `__CPROVER_w_ok`), and `\forall`/`\exists` over one integer variable with both
bounds in the guard (a loop). Anything else (logic-library calls, `\separated`, `\null`, ternaries,
bitwise operators) is not proven, `unsupported_construct` (`settings.untranslatable` says what).

### Reading the outcome

| Outcome | Verdict / failure class | Handler (writes `cbmc/handler.json`) |
|---|---|---|
| every property holds, every reachability assert fails | proven | none |
| a property fails and its trace replays on the C++ | refuted, `counterexample` inline | none (repair, ticket 13) |
| a property fails and no trace replays | `spurious_counterexample`, `unreplayed_counterexample` | minimal reproduction; never sent to repair |
| an unwinding assertion fails (or the oracle runs out) | `unwinding_bound_too_small` | names the loops and K |
| a reachability assert holds | `vacuous_pass` | minimal reproduction |
| job over its wall budget | `timeout` | recorded; never retried at smaller bounds |
| the RSS watchdog killed the job | `out_of_memory` | keeps the class (the Mac cap stays 8 GiB) |
| CBMC parsing or conversion error (exit 6) | `parse_error` | minimal reproduction (`job.c`, command) |
| a SAT solver error | `solver_error` | minimal reproduction |
| crash, signal, other exit with no result | `tool_crash` | minimal reproduction |
| the C lowering refuses the unit, or the translator a formal half | `unsupported_construct` | minimal reproduction |
| the C lowering and the C++ disagree on the bounded domain | `c_lowering_disagreement` (not a class) | the batch stops; no record |
| anything else | `unclassified_cbmc_outcome` (not a class) | none: `swdb prove` stops the batch |

**Replay** (stage 1 of ticket 11's two stages): the C++ cut with each summarized callee replaced by its stub
(the proof semantics), compiled with `-fsanitize=address,undefined -fno-sanitize-recover=all`, runs once on
the trace's oracle values. A named property replays when the native run reports the same name failing; a
CBMC built-in check (bounds, pointer, overflow, division) replays when a sanitizer stops the run. Ticket 60
replays a refutation further, on the strict layer (`replay_label`).

### What the record holds (on top of [format-v0.4-proof.md](format-v0.4-proof.md))

| Field | Meaning |
|---|---|
| `bounds` | the bounds asked for: `threads: 1` and each size bound |
| `counterexample` | refuted only: `property`, `check` (CBMC's property ID), `function`, `inputs` (`{name: value}`, arrays as lists, compared knobs by their global's name), `oracle` (the trace's values), `replay` (`form: cxx`, `replayed`, `failed`, `sanitizer`, `end`) |
| `unreplayed_counterexample` | `spurious_counterexample` only: the same shape, `replay.replayed: false` |
| `goals` | per CBMC property: `goal` (its ID), `property` (its description or name), `function`, `status` (`success`, `failure`), `solver` and `seconds` (null: CBMC reports neither per property) |
| `unproven_properties` | not proven only: each property that kept the job from proven: `property`, `kind` (`property`, `unwinding`, `reachability`), `function`, `line`, `status` |
| `settings` | `tool: cbmc`, `flags`, `translator`, `unwind`, `array_length`, `symbolic_knobs` (`{name, legality_clause, acsl, range}`), `summaries`, `agreement` (`runs`, `sampled`, `domain`, `c_output_sha256`, `cxx_output_sha256`, `verdict`), `forms` (`c_lowering` and `cxx` verdicts), `build_constants`, `rss_cap_bytes`, `wall_budget_seconds`; `outside_cpp_subset` or `untranslatable` when no CBMC ran |
| `pins.c_lowering` | `{id: <f>.c, sha256}` of the C lowering (after any scripted fault) |
| `pins.translator` | `{id: swdb-cbmc-translator-<version>, sha256 of swdb/cbmc_translator.py}` |
| `pins.summaries` | one `{id, sha256, proof_record}` per summarized callee |
| `evidence.reports` | `differential_c`, `differential_cxx` and their outputs, `cbmc_input` (`job.c`), `cbmc_output` (CBMC's JSON), `replay_cxx`, `handler`, all under `<runs-dir>/<record>/cbmc/` |
| `assumptions`, `tools` | one `trusted_tool` entry each: `swdb-c-lowering-2`, `clang-22.1.8`, `swdb-cbmc-translator-2` (ticket 23; was 1), `cbmc-6.11.0`, and the SAT solver inside CBMC (`cadical-in-cbmc-6.11.0`, from the lineup's `--sat-solver`) |

The method version must list both the C lowering tool and the CBMC translator (ID and sha256) in
`c_lowering.translators`, and pin `cbmc` (`6.11` matches 6.11.0) and `clang` in its `lineup`; a mismatch runs
nothing. Scripted faults for tests: `SWDB_CBMC` (a stand-in `cbmc` command line; `none` = missing) and
`SWDB_CBMC_LOWERING_FAULT` (a YAML file `replace: [[old, new], ...]` applied to the C lowering's text only).

## The bounded gate

- `TargetAdapter.bounded_job(candidate, contract, rung, bounds)` returns `{adapter: cbmc}` for `threads_1`
  (the gate then runs `swdb prove --adapter cbmc` with the rung's minimum bounds and
  `budgets.bounded_job_minutes`); `threads_k` still fails until tickets 46 and 47.
- `TargetAdapter.outside_cpp_subset(candidate)` is true when the proof function has no C lowering in the
  candidate artifact's tree. Code outside the subset now skips **both** rungs (`outside_cpp_subset`): CBMC,
  CIVL and GenMC all read the C lowering.
- The minimum-bounds record's bounds must use the proof unit's integer parameter names as size dimensions
  for the CBMC rung to run (ticket 33).

## For later tickets

- 23 (done 2026-10-14): stubs read `\old` over memory, logic calls, `\separated`; crux-llvm fallbacks, check mode
  and summary-form agreement: see [format-v0.4-stubs-check-mode.md](format-v0.4-stubs-check-mode.md).
- 25: vector and pair models become C stubs through this translator (`assigns` ranges on struct fields are
  not translated yet).
- 27: ghost hazard state goes into the stubs as globals; the harness already snapshots scalar globals.
- 33: per-loop unwinding bounds (`--unwindset`) from the minimum-bounds derivation; the A2 exit's 14 verdicts.
- 46/47: threads > 1; reuse `Code` (C lowering plus C++ cut) and the replay.
- 60: strict-layer replay of a `refuted` record starts from `counterexample.oracle` and `inputs`.
- 61: built, below.

## Whole-function equivalence (ticket 61)

**In one line:** `swdb prove --adapter cbmc --whole-function MODE` runs the candidate artifact's function and
the baseline's on the same symbolic inputs, at one thread and within bounds, and compares every output. Equal:
proven within bounds, threads = 1. Unequal: refuted, with the concrete inputs, the first differing location and
both values. Never more (no alignment exists: map 24 item 1). Code: `swdb/cbmc_equivalence.py`,
`swdb/cbmc_product.py` (the product-program generator); tests: `tests/test_cbmc_equivalence.py`.

**Method version.** The product-program generator is its own trusted tool, `swdb-cbmc-product-1` (ID plus the
sha256 of `swdb/cbmc_product.py`), kept out of `swdb/cbmc_translator.py` so the translator's sha256, which
`method.probata-draft-1` pins, did not change. A whole-function job runs only under a method version whose
`c_lowering.translators` lists it (else nothing runs); `method.probata-draft-1` does not, so a new draft must add
it. Records name it in `tools` and in the assumption set.

```
swdb prove --candidate <c> --function <f> --adapter cbmc --whole-function bounded_direct --contract <contract> \
           [--minimum-bounds <record> | --bounds <JSON>] [--baseline-candidate <b>] [--unwindset SIDE:LOOP=K ...] \
           [--define NAME[=VALUE]] [--budget-minutes <n>] --runs-dir <outside the repo>
swdb prove --candidate <c> --function <f> --adapter cbmc --whole-function no_contract_baseline \
           [--borrowed-bounds <record> | --bounds <JSON>] [--baseline-candidate <b>] ... --runs-dir <outside the repo>
```

| Mode | Who uses it | Contract | Level |
|---|---|---|---|
| `bounded_direct` | a proof unit with no unit postcondition (map 24 item 3) | required, and it must carry `relational_template: {reason}`; else refused, nothing written (the route guard) | counts like any bounded record (at most proven within bounds, threads = 1) |
| `no_contract_baseline` | the evaluation's no-contract baseline, bounded half (map 23 item 2) | none; `pins.contract` is not applicable | never: a measurement (`baseline_measurements` in `swdb candidate-level`), never the refuted flag |

Both modes write `route: bounded_direct`.

- **Equality only for a deterministic output** (decided by the main session under Yan-Ru's delegation,
  2026-10-14 20:48 ET). `bounded_direct` reads the contract's `output_determinism` (`deterministic` or
  `nondeterministic`); `no_contract_baseline` needs `--output-determinism`. Deterministic: outputs are compared by
  equality (`settings.comparison: {kind: equality, output_determinism: deterministic}`). Nondeterministic with no
  `output_relation`: refused with that reason (equality would refute a correct candidate with another valid output,
  such as another BFS parent array). Nondeterministic with an `output_relation`: the job should assert the relation
  on the candidate's output with the baseline's output as the witness; that form is ticket 62's work, so it is
  refused today and says so. Not stated: refused. Nothing is written on a refusal.

- **The baseline** is the candidate's source snapshot, or another candidate artifact (`--baseline-candidate`, for
  example a materialized baseline candidate or a fixture). `pins.baseline_function` pins it (`{id, function,
  sha256}`); the level rule reads a candidate ID there by its `artifact.sha256`.
- **The product program** (`job.c`): the candidate's C lowering as lowered; the baseline's C lowering with every
  function and global renamed to `swdb_base_<name>` by `#define`s around it; one harness. The harness draws
  every input once from the oracle (ticket 22's draws, size bounds and `requires`), gives each call its own copy
  of every array, calls the baseline then the candidate, checks the contract's per-candidate formal halves on the
  candidate's call (`bounded_direct` only), then asserts one property per output location, `swdb_equal.<location>`:
  the return value (`result`), every element of every array parameter (`a[0]` ... all `array_length` of them,
  so a write past what the baseline writes is caught), every scalar global both versions' code names, every
  global array both name (one property each), and every scalar global only one version's code names (compared
  with its value before the call, which the other version leaves alone).
- **Bounds.** `bounded_direct`: `--minimum-bounds` pins the contract's minimum-bounds derivation, and without
  `--bounds` the job runs at that record's bounds; a run below them is proven but reads "bounded check below
  minimum" and gives no level (the level rule, unchanged). `no_contract_baseline`: the bounds passed, or
  `--borrowed-bounds <minimum-bounds derivation record>`, whose bounds are used and labeled borrowed.
  `settings.bounds_origin` says which: `{kind: passed}`, `{kind: minimum_bounds, record}` or
  `{kind: borrowed, record, contract}`.
- **Unwinding.** `--unwind K` (K = the largest size bound + 1) for every loop, plus `--unwindset
  candidate:<function>.<n>=K` or `baseline:<function>.<n>=K` for a loop of one copy whose trip count differs
  (loop numbers from `cbmc --show-loops` on the function's own lowering). Unwinding assertions stay on: a copy
  whose loop runs longer than its bound is `unwinding_bound_too_small`, never proven. No alignment hints.
- **Both forms.** The differential run compiles the same product program twice, from both C lowerings and from
  both C++ cuts, and runs the bounded domain natively; any difference stops the batch (`c_lowering_disagreement`,
  the message names the side: `baseline`, `candidate` or `both`). A refutation replays on the product of the two
  C++ cuts with sanitizers on; equality failures are replayed first, in the order of `settings.compared`. Either
  function outside the C++ subset: not proven, `unsupported_construct`, `settings.outside_cpp_subset` names the
  side. A lowering that defines a type, or two functions whose parameter or return types differ, is also
  `unsupported_construct`.
- **Budget and failure classes:** as ticket 22's adapter (the same reader and handlers).

On top of the CBMC record above:

| Field | Meaning |
|---|---|
| `route` | `bounded_direct` (both modes); `swdb validate` refuses such a record with a thread count other than 1 or any dimension `unbounded`, and the level rule never counts one |
| `pins.baseline_function` | `{id, function, sha256}` of the baseline (source snapshot or candidate artifact) |
| `pins.baseline_c_lowering` | pin `baseline_c_lowering`: `{id: <f>.c, sha256}` of the baseline's C lowering |
| `pins.contract`, `pins.minimum_bounds` | `no_contract_baseline`: `not_applicable` |
| `pins.build_constants` | the build constants, the same for both builds |
| `counterexample.first_difference` | refuted: `{location, baseline, candidate}`, the first compared location whose values differ on the replay, with both values (null when a formal half failed and every output agrees) |
| `settings.whole_function` | the mode |
| `settings.baseline` | `{kind: source_snapshot or candidate, id, function}` |
| `settings.bounds_origin` | above |
| `settings.comparison` | `{kind: equality, output_determinism: deterministic}` (the only form today) |
| `settings.build_constants_by_build` | `{candidate, baseline}`: each build's `{name, value}` list |
| `settings.compared` | the compared locations, in property order |
| `settings.uncompared_globals` | globals not compared (a global array only one version names) |
| `settings.formal_halves` | the contract's formal halves checked in the same job (`bounded_direct`) |
| `settings.unwindset` | the per-loop bounds as CBMC got them (`<loop>:<K>`) |
| `settings.agreement.sides` | `[candidate, baseline]`: both sides' lowerings were checked |

A contract with no unit postcondition says so with `relational_template: {reason: <text>}` (a library entry
field, ticket 61's smallest form; map 24's drafting rule: a relational template needs a recorded reason).
