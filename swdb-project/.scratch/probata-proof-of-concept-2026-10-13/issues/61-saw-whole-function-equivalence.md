# 61 — SAW whole-function equivalence (bounded direct route)

Created: 2026-10-13 23:15 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
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
