# 03 — Prove a rewrite rule once, or validate each application?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

What does prior work say about proving a rewrite rule correct once and reusing the proof
everywhere it applies, versus validating each application (translation validation)?

Cover: Cobalt, Rhodium, PEC (parameterized equivalence checking), Alive/Alive2 peephole proofs,
CompCert verified passes versus translation validation (Pnueli; Necula; Tristan and Leroy),
relational verification and product programs (Barthe; regression verification by Godlin and
Strichman; REVE), loop-transformation validation (CoVaC, PolyCheck, equality saturation such as
HEC), MLIR translation validation.

Output:
- The candidate shapes for a "proven rewrite contract" and the per-instance check each implies.
- Which shapes handle data-dependent loops (BFS frontier), memory restructuring, and offload to
  an accelerator.
- How prior work handles legitimately different outputs (BFS may pick a different parent).

## Answer

Resolved 2026-10-09 14:16 ET. Full findings: [`../research/03-prove-once-rewrite-rules.md`](../research/03-prove-once-rewrite-rules.md).

- **Two camps:** prior work either proves a rule once and trusts every application (Cobalt,
  Rhodium, PEC, Alive, Lean-MLIR) or checks each application (Pnueli, Necula, Alive2, MLIR
  validators, HEC). PEC itself recommends a staged mix: prove once what you can, validate the
  rest per application.
- **Pure prove-once does not fit LLM candidates.** Its soundness rests on a trusted syntactic
  match to a template, and LLM code is not a template instance. A match check also cannot
  refute a bug such as the wrong-tile wait. Pure per-instance validation is the shape that did
  not scale in Extensa.
- **Recommended shape, a staged hybrid:**
  - **Proven once, per rewrite contract:** intrinsic and library-operation building blocks,
    proven against reference semantics and reused as summaries; contract lemmas such as L1;
    and a relational template (alignment plus a coupling invariant from `once_enqueue`).
  - **Per candidate artifact:** one small relational proof of a single `TDStep` call against
    the baseline, plus the existing runtime guards. LLM proof hints add only
    candidate-specific invariants.
  - **Verdict:** proven unbounded if the invariant is inductive, else proven within recorded
    bounds.
- **Different outputs:** prior work uses refinement (CompCert, Alive, Alive2), equality modulo
  a relation (bridge predicates, acceptability relations), or ∀∃ asymmetric products. For BFS,
  use equality modulo α (visited set and per-level frontier *sets*) plus parent validity.
  Under OpenMP this equals ∀∃ refinement of the baseline, and it is stronger than today's
  frontier-size check.
- **Sharpens ticket 01:**
  - Decision 2(a) should read "contract parts proven once, plus a small per-instance proof".
  - Proven verdicts are conditional on the assumed clauses L3 and L5 and on the reference
    semantics. Ticket 09 should list that assumption set.
