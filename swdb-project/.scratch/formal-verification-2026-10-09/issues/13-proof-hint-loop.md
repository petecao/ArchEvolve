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
