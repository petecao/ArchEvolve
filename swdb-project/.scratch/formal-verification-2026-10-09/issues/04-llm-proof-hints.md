# 04 — How do LLMs build proof hints for existing verifiers?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

How do current systems use LLMs to construct proofs or proof hints (loop invariants, ghost state,
lemmas, intermediate assertions) for an existing formal verifier, and what do they do when the
verifier times out or returns unknown?

Cover: Lemur, AutoSpec, SpecGen, Laurel, Loopy and other LLM loop-invariant work, LLMLift (code
plus proof), LLM-Vectorizer (LLM rewrites checked by Alive2), AlphaVerus, AutoVerus, Clover,
SAFE, dafny-annotator, Baldur.

Output:
- Loop patterns: feedback signals, use of counterexamples, budgets.
- Soundness guards: how each prevents `assume` or weakening the specification.
- Reported success rates and the benchmarks usable as our baselines.

## Answer

Answered 2026-10-09 14:22 ET. Full findings: [`../research/04-llm-proof-hints.md`](../research/04-llm-proof-hints.md).

- **Gist:** every credible system works the same way. The LLM proposes hints, the existing
  formal verifier decides, and timeout or unknown means "not proven yet, try more hints," never
  evidence. Lemur, Loopy, Quokka and LORIS do this on C verifiers (ESBMC, UAutomizer, Frama-C).
  The one system that let an LLM predict soundness when Alive2 was inconclusive (Wang & Xie 2024)
  is the anti-pattern.
- **Soundness guard:** we need both kinds.
  - *Logic:* a hint is an assumption until it is proven (Lemur, Quokka).
  - *Text:* erase the hints, diff against the frozen code and contract, and scan for banned
    constructs (AutoVerus's Lynette, DafnyBench's rules). LLMs do cheat: Lynette rejected 12.4% of
    candidates, and AlphaVerus saw `assume(false)` snowball.
- **Recommended loop:** run bounded first (CBMC with unwinding assertions, no hints). On any
  verdict below proven unbounded, the proof-hint agent writes a hint overlay. A deterministic
  checker vets it, then the verifier proves every hint. Prune blamed hints (Houdini), minimize,
  and run vacuity and negative-control checks. Cap at about 10 rounds and record rounds, tokens
  and time.
- **Challenges to decision 8 (ticket 01):**
  - CBMC loop invariants need `assigns` and `decreases` clauses, which are not in the hint list.
  - CBMC has no ghost notion, so the checker must enforce ghost non-interference itself.
  - Callee and stub contracts and verifier flags are unlisted escape hatches.
  - The trigger should be "below proven unbounded," not only "timeout/unknown."
- **Baselines and evaluation:**
  - Copy DafnyBench's success rule: spec preserved, no escape hatch.
  - Calibrate on Code2Inv, the Loopy and LaM4Inv sets, InvBench (866 SV-COMP), X509-parser,
    TSVC, and Trivet's LLVM set.
  - Give "verifier without hints" the same wall time. Quokka found LLM invariants add only 0–3
    solves over UAutomizer at 500 s; most of the gain is speed.
  - Gap: no verified LLM work writes relational (two-program) hints for C.
