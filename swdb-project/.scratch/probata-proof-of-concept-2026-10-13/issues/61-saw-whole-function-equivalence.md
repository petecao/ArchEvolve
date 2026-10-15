# 61 — SAW whole-function equivalence (bounded direct route)

Created: 2026-10-13 23:15 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 22
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes" (bounded direct); "Verifier lineup and order" (bounded verifier, cross-check of the lowering, pinned versions, failure classes); "Bounds" (build constants, minimum bounds, 15 minutes per bounded job); "What a proven verdict asserts" (bounds, thread count always a dimension); "Evaluation design" (baselines: no contract); "Testing Decisions", seam 1; S1); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) item 4 and Later changes; [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) item 2 and Later changes; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) items 1, 3
**Time estimate:** about 3 days

**What to build:** A bounded check that needs no contract. SAW runs a final candidate artifact's
whole function and the baseline implementation's on the same symbolic inputs, at one thread, within
bounds, and compares every output. Equal: proven within bounds, threads = 1. Unequal: refuted, with a
counterexample. It serves two users:

- the evaluation's **no-contract baseline**, bounded half (23 item 2; evaluation 08);
- the **bounded direct route**, for a proof unit with no unit postcondition (24 item 3).

It never gives more than proven within bounds: an unbounded direct proof against the baseline needs
an alignment, and nothing supplies one (17 item 4; 24 item 1). Build constants are recorded exactly.
Tested on fixtures through `swdb prove`.

## Acceptance

- [ ] **Equal pair proves.** On a fixture pair (a baseline function and a rewrite with the same
  outputs, for example a split loop), `swdb prove` in whole-function mode writes one proof record:
  proven within bounds, route field (04) set to bounded direct, thread count 1, each size bound's
  value and each build constant's exact value for both builds. It pins both functions' code. Inputs
  stay symbolic up to their size bounds.
- [ ] **Unequal pair refutes.** A seeded rewrite that changes one output on some input is refuted. The
  record holds the counterexample inline: the concrete inputs, the first differing output location
  and both values.
- [ ] **Every output compared.** Every location either function may write, and the return value, is
  compared. Negative control: a rewrite that also writes one location the baseline never writes is
  refuted.
- [ ] **Capped at proven within bounds.** `swdb validate` refuses a record from this route with any
  dimension "unbounded" or a thread count above 1. `swdb candidate-level` never reads a level above
  proven within bounds, threads = 1, from such a record.
- [ ] **Route guard** (assumption; see Notes). `swdb prove` runs the bounded direct route only for a
  proof unit with no unit postcondition (its contract uses a relational template, with its recorded
  reason), or for the no-contract baseline. Asked for it on any other unit, it refuses and says why
  (negative control).
- [ ] **Bounds.** On the bounded direct route the job runs at its contract's minimum bounds; a run
  below them gives "below minimum bounds" and no level (10's rule, unchanged). For the no-contract
  baseline it runs at bound values passed to the job, labeled borrowed when they come from a contract.
- [ ] **A measurement, not a level** (assumption; see Notes). A record written for the no-contract
  baseline never counts toward a candidate artifact's level. Negative control: a certified fixture
  candidate artifact whose only proof record is such a record reads certified in
  `swdb candidate-level`. A bounded-direct-route record counts like any bounded record.
- [ ] **Both forms.** When both functions are inside the C++ subset, the job runs SAW on the C++ and on
  the C lowering, and the two verdicts must agree, as in 22. A planted disagreement stops the batch
  and records no proven verdict. Outside the subset it runs on the C++ only and records why.
- [ ] **Budget and failures.** A job over its time budget (starting value 15 minutes; small in the
  test) reads not proven, failure class timeout, and is never retried at smaller bounds. Every other
  SAW failure maps to the failure-class list; an outcome with no class stops the batch.
- [ ] **Pins and Mac rules.** SAW version, solver, flags and clang 22.1.8 are pinned in the
  content-hash set. One real verifier job at a time under the ~8 GB RSS watchdog; tests that need SAW
  or LLVM 22 skip cleanly. Records carry `contract_fixture` evidence and pass `swdb validate` and
  `swdb build`.

## Notes

- **Not in this ticket:**
  - 04 — Proof record tracer: the route field this ticket fills.
  - 22 — SAW adapter and SAWScript translator: the adapter and the C++-versus-C-lowering rule reused
    here.
  - 23 — C-stub translator, fallbacks and check mode: the crux-llvm and CBMC fallbacks.
  - 27 — Proof semantics for the BFS read-offload calls: the SAW form DX100 code needs here.
  - 60 — Strict-layer replay and whole-kernel reproduction: replays this route's refutations like any
    other bounded refutation.
  - 62 — Route choice and predecessor proofs in the campaign: the choice between routes 1 and 3.
  - 13 — Counterexample-guided repair: what a refutation feeds.
  - Threads ≤ k: CIVL's spec-vs-implementation compare mode (17 item 4.4) is unconfirmed and not built
    in this effort.
  - Evaluation 08 — RQ3: what a contract buys: runs the no-contract baseline on the populations.
- 59 — Method-version review and freeze waits on this ticket, so the evaluation's no-contract baseline
  runs on frozen tooling.
- Assumption (not decided in the map): "equivalence" means equal outputs, the T-LLM and VERT form.
  Risk: a correct candidate artifact with a different valid output (another valid BFS parent array)
  is refuted. In the no-contract baseline that is part of what the per-pair method measures. On the
  bounded direct route it would push a correct candidate artifact out of selection. Raise with Yan-Ru
  before the first real use; comparing modulo the kernel's output relation instead is not decided
  anywhere.
- Assumption (not decided in the map): the "whole function" is the function that holds the rewrite
  site, compared whole, with the same boundary on both sides (17 item 4.5).
- Assumption (not decided in the map): when a contract applies, its formal halves about the candidate
  artifact's own code are checked in the same job, as in 22. The no-contract baseline has none.
- Assumption (not decided in the map): on DX100 code the job uses 27's SAW form and hazard probes,
  because a proven verdict includes hazard freedom (map 09). An equal pair with a hazard is refuted.
  Fixtures here have no accelerator calls.
- Assumption (not decided in the map): a no-contract-baseline record must not change a level, because
  the design allows the bounded direct route only for a proof unit with no unit postcondition. How the
  record says so is open: pick the smallest form the level rule can read. The route guard follows from
  the same design line.
- Assumption (not decided in the map): the no-contract baseline's bound values are the contract's
  minimum bounds, labeled borrowed (evaluation 08's assumption), since without a contract there are no
  minimum bounds (map 19 item 1).
- Every record this ticket writes fills the route field defined by 04 with bounded direct. 04 owns the
  field; 62 makes it required for candidate proof units.
- Assumption (not decided in the map): if 09 — Spike verdict chose crux-llvm, this mode runs on
  crux-llvm under the same rules (22's assumption).
- Assumption (not decided in the map): a real-valued unit follows 23's float routing: crux-llvm
  `-f real` comparing outputs as reals, unless 23's SAW float-mode check passed; the record names the
  tool.
- Mac: keep at least 50 GB of disk free; if SAW needs a Homebrew change, check that LLVM 22 still works
  for the analytic evaluator. Contract fixtures only; no held-out kernel (BC, PR, SSSP).

## Later changes
- 2026-10-14 13:19 ET (Yan-Ru accepted ticket 09's A2 changes): SAW whole-function equivalence lost its role when CBMC replaced SAW as the bounded verifier. Before starting: pick another tool (e.g. CBMC on a product program of the two C lowerings) or propose the cut to Yan-Ru.

## Answer

2026-10-14 17:55 ET. **Resolved as CBMC whole-function equivalence on a product program.** Branch `probata-poc/t61`.
Format: [`format-v0.4-cbmc.md`, "Whole-function equivalence"](../../../docs/reference/format-v0.4-cbmc.md).

**Decision recorded (main session, under Yan-Ru's delegation, 2026-10-14):** SAW lost this role (Later changes).
The tool is CBMC 6.11 on a product program (self-composition) of the two functions' C lowerings, reusing 22's
harness and oracle, with the same bounded domain, unwinding assertions, reachability asserts and the C-vs-C++
differential on both sides. Loops whose trip counts differ get their own per-loop bound (`--unwindset`);
equality is asserted at the end; no alignment hints (map 24).

**What was built**

| Piece | Where |
|---|---|
| `swdb prove --adapter cbmc --whole-function bounded_direct\|no_contract_baseline` (`--baseline-candidate`, `--borrowed-bounds`, `--unwindset`) | `swdb/proof.py`, `swdb/cbmc_equivalence.py` |
| Product harness (one input draw, a copy of every array per call, one `swdb_equal.<location>` property per output) and baseline renaming | `swdb/cbmc_product.py`, its own trusted tool `swdb-cbmc-product-1` (the method version must list it; `swdb/cbmc_translator.py` is unchanged, so `method.probata-draft-1`'s translator pin still holds) |
| Route cap: schema (`route: bounded_direct` needs `threads: 1`, no `unbounded`); the level rule never counts one above | `schemas/proof.schema.json`, `swdb/level_rule.py` |
| No-contract baseline = measurement (`baseline_measurements`), never a level or the refuted flag | `swdb/level_rule.py` (`is_baseline_measurement`) |
| `relational_template: {reason}` on a contract (the route guard reads it); pin `baseline_c_lowering` | `schemas/library/library_entry.schema.json`, `schemas/proof.schema.json` |
| Tests (13) | `tests/test_cbmc_equivalence.py` |

**Acceptance, box by box (CBMC form)**

- Equal pair proves: split loop vs the baseline fill, `bounded_direct`: proven, `route: bounded_direct`, bounds
  `{threads: 1, n: 3}`, `pins.code` (candidate), `pins.baseline_function` and both C lowerings pinned, build
  constant `SWDB_FIXTURE_UNUSED=7` in `pins.build_constants` and in `settings.build_constants_by_build` for
  both builds; inputs drawn from the oracle (symbolic) up to the size bound; level
  `proven_within_bounds_threads_1`.
- Unequal pair refutes: the early-stop fill is refuted with `counterexample.inputs` and `first_difference
  {location: a[n-1], baseline: v, candidate: the old a[n-1]}`, replayed on the C++.
- Every output compared: the return value, every array element up to the array length, globals both versions
  use, and a global only one version uses (against its pre-call value). Negative controls: a write to `a[1]`
  the baseline never makes (n = 1) and a write to a global the baseline never names: both refuted at that
  location.
- Capped: `swdb validate` refuses a `bounded_direct` record with `threads: 2` or `n: unbounded`;
  `swdb candidate-level` refuses the invalid store; the level rule itself never counts such a record.
- Route guard: `bounded_direct` on a contract without `relational_template` is refused with the reason; no record.
- Bounds: `--minimum-bounds` runs at the derivation's bounds; below them the record reads below minimum and gives
  no level. The no-contract baseline runs at `--borrowed-bounds`, labeled `{kind: borrowed, record, contract}`.
- Measurement, not a level: a certified candidate whose only record is a no-contract-baseline record reads
  certified; a refuted measurement does not set the refuted flag. A `bounded_direct` record counts normally.
- Both forms: the product program is built from both C lowerings and from both C++ cuts and run over the bounded
  domain; a planted fault in the baseline's lowering stops the batch (`c_lowering_disagreement`, side named), no
  record. Outside the subset (GAPBS `InitParent`, default snapshot baseline): `unsupported_construct`, side named.
- Budget and failures: over budget reads `timeout` at unchanged bounds; an unclassified outcome stops the batch;
  every other class comes from 22's reader and handlers (shared code).
- Pins and Mac rules: CBMC, solver flag, clang 22.1.8 and the translator through 22's `_tools`; one CBMC job at
  a time through `swdb/verifier_lock.py`; tests skip without CBMC or clang 22.1.8; records are
  `contract_fixture` and pass `swdb validate`.

**Tests** (Mac; serial; no xdist; pytest outside the verifier lock, each CBMC job takes it through
`swdb/verifier_lock.py`). Equivalence results (CBMC wall per job): split vs base proven (0.10-0.17 s);
early-stop refuted (first difference `a[n-1]`); extra write refuted at `a[1]` (0.09 s); global write refuted at
`swdb_fixture_threshold`; slow loop unwinding_bound_too_small at K = 4 (0.10 s), proven with
`candidate:swdb_fixture_fill.0=7`. After merging integration `bedb57c7` and `12d44ea8`:
`test_cbmc_equivalence.py` (14), `test_cbmc_adapter.py`, `test_format_doc.py`, `test_level_rule.py`,
`test_proof_records.py`, `test_proof_method_version.py`: 262 passed, 1 failed by the lock-queue timeout (below),
which then passed alone (`pytest-final2.log` sha256 `21c58eefc59bba6f`..., `pytest-final3.log` `7851a891dc47799f`...).
After merging `2dff3f58` (ticket 24): `test_cbmc_equivalence.py`, `test_format_doc.py`, `test_level_rule.py`
**113 passed** (`pytest-final4.log` `b0d13e8986b14ab1`..., `report-final4.jsonl` `46a608990a43349b`...). Runs:
`/tmp/claude/probata-runs/t61/` (pytest temp folders deleted).

**SAW to CBMC translations** (each an Assumption; not decided in the map beyond the main session's decision):

- Assumption: "SAW runs both whole functions on the same symbolic inputs and compares every output" = CBMC on a
  product program: one oracle draw feeds both calls; one `swdb_equal.<location>` property per output location.
- Assumption: "SAW on the C++ and on the C lowering, verdicts agree" = 22's form on both sides: the native
  C-vs-C++ differential of the whole product program over the bounded domain, and replay of every
  counterexample on the product of the two C++ cuts. A disagreement stops the batch and names the side.
- Assumption: "outside the subset: SAW on the C++ only" = not proven, `unsupported_construct`, side named (as 22:
  CBMC never reads the C++).
- Assumption: "SAW version, solver, flags pinned" = CBMC, its bundled SAT solver and the lineup flags, as 22.
- Assumption: SAW's counterexample = the CBMC trace's oracle values replayed natively; the first differing
  location comes from that replay, in `settings.compared` order (equality failures are replayed first).

**Other assumptions**

- Assumption: the baseline is the candidate's source snapshot by default, or another candidate artifact
  (`--baseline-candidate`: a materialized baseline candidate, or a fixture); the level rule reads a candidate ID
  in `pins.baseline_function` by its `artifact.sha256`.
- Assumption: a contract "has no unit postcondition" exactly when it carries `relational_template: {reason}`
  (smallest form; every other contract is taken to state one, map 24's drafting rule).
- Assumption: a no-contract-baseline record says so by `route: bounded_direct` plus a `not_applicable`
  `pins.contract` (the smallest form the level rule reads); its `minimum_bounds` pin is not applicable too.
- Assumption: `--minimum-bounds` is optional on `bounded_direct` (as for 22's jobs); given without `--bounds`,
  the job runs at the derivation's bounds.
- Assumption: both builds use the same build constants (one `--define` list), recorded per build.
- Assumption: globals keep their static initializers on both sides (no symbolic global state); compared knobs
  and callee summaries are not used in the product program (callees inlined: the function is compared whole); a
  global array only one version names is listed in `settings.uncompared_globals`, not compared.
- Assumption: the two functions must have the same parameter and return types (17 item 4.5, same boundary); a
  lowering that defines a type is `unsupported_construct` (the product would define it twice).
- Assumption: a failing built-in check (overflow, bounds) in either copy is a refutation when it replays under the
  sanitizers; `counterexample.function` names the copy. Found while testing: a candidate loop bound `2 * n`
  overflows at `n = INT_MIN` and is refuted although its outputs agree elsewhere (fixture now guards `n > 0`).
- Assumption: the product-program generator is a separate trusted tool (`swdb/cbmc_product.py`,
  `swdb-cbmc-product-1`), not an extension of 22's translator: `method.probata-draft-1` pins the translator's
  sha256 and a method-version file is never edited in place. It reuses the translator's printers.
  **Needs the main session:** no committed method version lists `swdb-cbmc-product-1`, so a real whole-function
  job refuses to run until a new draft (next sequence) adds it (fixture method versions in the tests list it).
- Side finding: under a long verifier-lock queue (8 waiters), `test_a_job_over_its_budget_is_timeout_at_unchanged_bounds`
  failed once because `run_swdb`'s 600 s subprocess timeout counts the lock wait; alone it passes. 22's tests share
  this exposure.
- Open point for the main session: `level-rule.1` is kept. The changes (measurements left out, the
  `bounded_direct` cap, a candidate as baseline pin) change no level an earlier record gives, but the level-rule
  doc's versioning rule, read strictly, asks for `level-rule.2` (5 test files and 2 handoff examples name `.1`).
- Unchanged: this ticket's risk note (equal outputs refute a correct candidate with another valid output, such as
  another BFS parent array) still needs Yan-Ru before the first real use.
