# 12 — What semantics do DX100 proofs trust?

Created: 2026-10-09
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 05, 08, 14
**Map:** `../map.md`

## Question

What semantics do DX100 proofs trust: the authors' functional model, our strict layer, or a
separate logical model? Who signs off on it (the strict layer is "assumed, owner Eric"), and how
is the gap between the authors' model and the strict layer handled?

## Comments

- 2026-10-09: input from 05: split each DX100 proof into hazards (over a "proof edition" of the
  strict layer: uncovered reads return arbitrary values, not a fixed sentinel) and function (over
  instant completion), linked by a reduction lemma proven once. Never use the functional model
  alone: it would prove `TDStepMAA`.
- 2026-10-09: 05 found two scope gaps in "the strict layer is the trusted semantics" (01, decision
  10): the strict layer does DX100 main-memory reads and writes at issue
  (`library/dx100/strict/MAA_functional.hpp:126,131,170`), so it never flags memory touched by an
  operation still in flight; and the wrong-tile refutation (01, decision 9.1) rests on an assumed
  wait rule that the authors' model may contradict. Ticket 14 checks gem5. Decide here what
  decision 9.1 becomes if gem5 says the wait covers the store.
- 2026-10-09: input from 02: no unbounded tool can trace the strict layer's growing op list and
  recursive `cover()`. Unbounded proofs will trust `maa_*` contracts, which need their own
  evidence against the strict layer.
- 2026-10-09: settled in 01 (amended): proofs use a gem5-matching wait rule (14). This ticket still
  decides the rest: the hazards/function split, evidence for `maa_*` contracts, and memory
  effects that land after the call.
