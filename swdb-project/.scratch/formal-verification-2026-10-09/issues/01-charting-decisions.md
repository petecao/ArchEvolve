# 01 — Charting decisions

Created: 2026-10-09
**Type:** grilling
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

What is this map finding its way to, and which standing decisions frame every later ticket?

## Answer

Decided with Yan-Ru in the charting session, 2026-10-09 ET.

1. **Destination:** a research design spec for the "proven" certification level: claims, method,
   DX100 BFS proof of concept, evaluation plan, positioning. Ready to cut into build tickets.
   Running the proof of concept is the next effort.
2. **Headline claim:** the method is (a) rewrite contracts proven once, reused by every candidate
   artifact that applies them, plus (b) LLM proof hints when the formal verifier times out or
   returns unknown. (c) Bugs found in expert rewrites are the motivating evidence, not the claim.
3. **Modes:** both. Extensa mode is the core of the paper submission. ArchEvolve mode shows LANL
   the novelty through the team (no direct LANL contact).
4. **Deadline:** none; sooner is better.
5. **Terms:** what we verify is a candidate artifact's change against the rewrite contract it
   applies. The DX100 authors' accelerated BFS plays the role of a candidate artifact. "Proven
   contract" is split into two meanings in ticket 10.
6. **Two proven levels:** proven unbounded > proven within bounds > certified > uncertified.
   Every proven-within-bounds verdict records its bounds.
7. **Concurrency:** single-thread proofs first, then concurrency. Both are in scope.
8. **Proof hints:** the agent may add only ghost variables, loop invariants, lemmas and
   intermediate assertions, each itself proven. Never `assume`, never edits to the candidate's
   code or the contract. A checker rejects anything else.
9. **Proof-of-concept candidates (all three):**
   1. DX100 authors' `TDStepMAA`: should be proven under a gem5-matching wait rule (amended
      2026-10-09, see Comments; it was "must be refuted").
   2. Peter's §5 read offload with fixes E1–E5 (`library/dx100/bfs_read_offload.inc`): should be proven.
   3. Codex's native frontier-staging rewrite (`library/native/bfs-tdstep-frontier-staging.patch`): first rewrite actually produced by an LLM.

   Must be refuted (added 2026-10-09): seeded real bugs, namely the contract's negative controls
   and a deleted wait.
10. **Out of scope:** compiler correctness; DX100 hardware versus its functional model (the strict
    layer is the trusted semantics); speed; gem5.

## Comments

- 2026-10-09: ticket 14 found the authors' `wait_ready(tile3)` is safe on gem5; the "wrong-tile
  bug" exists only under our stricter strict-layer rule. Decision 9.1 ("must be refuted") no
  longer holds.
- 2026-10-09: Yan-Ru chose the replacement: the authors' version moves to "should prove" under a
  gem5-matching wait rule; seeded real bugs (negative controls, a deleted wait) must be refuted.
  The strict layer's false alarm on a correct expert rewrite is paper evidence that hardware
  semantics must be explicit and checked against the device model.
