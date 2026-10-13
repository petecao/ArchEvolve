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
- 2026-10-11: input from 08: no verifier ran on the strict layer as written; proofs ran on
  `prototype/08-wrong-tile/port/strict_port.hpp`, an array port with both wait rules. The only
  evidence that it matches today is differential: 11 fixture scenarios x 2 rules x 3 tile sizes,
  0 diffs. In 08's harness, P1 (hazard) depends only on the control-flow shape, not on data.
  That supports the hazards/function split from 05.
- 2026-10-12 22:52 ET: input from 10: each DX100 lowering is proven once against the semantics this ticket
  picks, and its proven clauses become a summary used in every candidate proof. The summary must
  carry hazard state (which tiles are ready after which wait), so hazard freedom can be proven
  without the inlined port. 10's scale hypothesis depends on such summaries. Who signs off on
  the semantics also signs off on what the summaries may claim.
- 2026-10-13 00:35 ET: input from 11: (1) the concurrency proof needs the DX100 store issued inside
  `critical` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:170-187`) to be complete **and visible to
  other cores** before the lock is released. Research 14 confirmed completion on gem5, not
  cross-core visibility. Until this ticket decides, it is an assumption-set entry (trusted
  accelerator semantics). (2) Summaries come in three generated forms (SAWScript specs, C call
  stubs, ACSL contracts) from one source, the formal halves; the DX100 summaries must carry hazard
  state in all three, and per-thread tile ownership for concurrency (ticket 15). (3) Behavior
  outside the language standard is trusted accelerator semantics; undefined behavior is a proof
  obligation (11, item 11).
