# 13 — How does the proof-hint loop work?

Created: 2026-10-09
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 04, 09, 11
**Map:** `../map.md`

## Question

How does the proof-hint loop work?

- Who writes proof hints: a new proving agent role or the rewrite provider? (The DX100 authors'
  code has no rewrite provider.)
- What the agent sees: verifier output, counterexamples, the contract.
- The checker that enforces the hint rules in 01.
- The budget per candidate artifact.
- What each verdict does: proven sets the level; refuted is replayed as a concrete test before it
  counts as a bug; unknown after the budget leaves the candidate certified.

## Comments

- 2026-10-09: input from 06: Trivet already gates LLM proofs (no `sorry`/`admit`, statement
  unchanged); cite it, ours is the C/C++ form. Its gains came from a fixed proof scaffold with
  small holes for the LLM; a proven rewrite contract could supply that scaffold.
- 2026-10-09: input from 04: recommended loop and two-part soundness guard in
  `../research/04-llm-proof-hints.md`. Gaps in 01 decision 8 to settle here: CBMC loop
  invariants also need `assigns` and `decreases` clauses; CBMC has no ghost variables, so the
  checker must keep ghost state apart from real code; callee contracts and verifier flags are
  escape hatches; the trigger should be "anything below proven unbounded", not only timeout or
  unknown. Baselines: "verifier without hints" at equal wall time (Quokka: hints add 0–3 solves
  at 500 s; most gain is speed).
- 2026-10-09: input from 02: ESBMC and CBMC have no lemma construct and their ghost variables
  are ordinary variables; Frama-C/WP accepts `axiom` and `admit` without proof, so the checker
  must reject both.
- 2026-10-12 22:25 ET: input from 09: the checker must inventory every `assume` in a harness and
  map each one to a proof at the real call site or to a reduction listed in the assumption set;
  an unmapped `assume` voids the verdict. 08's harness already has one
  (`../prototype/08-wrong-tile/tdstep_harness.cpp:74` assumes `parent[v] >= -1`; real callers pass
  `-out_degree`).
- 2026-10-12 22:52 ET: input from 10: (1) contract proofs may be human-assisted (Yan-Ru writes hints or
  proofs, reviewed at promotion) under the same hint rules; candidate proofs stay fully
  automatic. (2) Each clause names its proof placement (once, per candidate, or assumed); the
  checker confirms every clause is covered by a proof or the assumption set. (3) Negative
  controls are refuted once per contract on its reference instance; vacuity checks per
  candidate stay here.
- 2026-10-13 00:35 ET: input from 11: (1) the trigger includes the unbounded verifier's timeout and
  "unknown": "not proven yet", never a bug or a proof. (2) Every "not proven" carries a failure
  class; only timeout (and proven-within-bounds verdicts) go to the hint loop; parse errors,
  unsupported constructs, memory and crashes have fixed handlers; an unclassified failure stops
  the batch. (3) Hint vocabulary per tool: WP (the unbounded verifier) has ghost code, lemmas,
  loop invariants, assertions and `Wp.induction` scripts; SAW (the bounded verifier) has only
  experimental cutpoint loop invariants, so hints mostly target WP. ESBMC and RPP are out.
  (4) The checker allows only `assume`s a summary generates. (5) A racy candidate artifact is
  refuted, and the counterexample goes to the rewriting LLM, not the hint agent (provisional).
- 2026-10-13 14:19 ET: input from 12: (1) a hazard is an assertion failure at an unready read, not
  a fixed or arbitrary value; on the C++ path the harness generator places a probe before each
  tile read loop, in the C lowering a check sits at each read. The checker must confirm these
  probes are present and generated, not hint-written. (2) A refutation replays on the strict
  layer before it counts as a bug, but rules only the proof semantics has (memory footprints,
  timing-dependent `get_tile_ready`, the other-thread read rule) cannot replay there until the
  strict layer catches up. Decide how such a refutation is reported.
