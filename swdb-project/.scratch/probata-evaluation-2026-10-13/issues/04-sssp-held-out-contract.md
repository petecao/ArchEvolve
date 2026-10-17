# 04 — SSSP held-out contract and contract proof

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": held-out contracts, RQ3; "Proven once vs per candidate"; "What a proven verdict asserts": proof unit, harness `assume`s; "Bounds"; "Formal-half language and the C++ subset": the five gates, primitive recursion; "Proof-hint loop": seeds; "Concurrency": shared-action kinds; "Further Notes": side findings, the SSSP risk; S1: the proof command); decisions: [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 9, seeds), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) (items 2, 4-5), [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) (offload-only contracts)
**Time estimate:** about 2-3 weeks of agent work

**What to build:** As for BC (02), but for SSSP. Once 01 gives SSSP a correctness check, an agent
(Codex) drafts SSSP's output relation and one offload-only rewrite contract, blind to the authors'
DX100 code, from the baseline `DeltaStep` and the intrinsic specification. The proof unit is the
whole `DeltaStep` call. The unit postcondition is the shortest distances (integer weights, no reals),
defined by primitive recursion on path length. The `assert(false)` on a small non-empty current bin
is handled one of two ways: "delta ≤ least weight" as a proof-unit precondition, or a proof that the
assert is unreachable. The contract proof carries hints for delta-stepping's outer-loop invariant, so
per-candidate proofs get them as seeds. Yan-Ru approves at promotion. Agent time and Yan-Ru's review
hours are recorded for RQ3.

## Acceptance

- [ ] **Blind drafting:** every drafting call's provider workspace hash list shows no authors' DX100
      function and no file outside 02's input list. The provider workspace and guard test refuses an
      input that names `DeltaStepMAA`.
- [ ] SSSP's output relation (the distances, the same at any thread count though rounds differ) is
      recorded beside 01's SSSP check. The contract and its formal halves pass `swdb validate` and
      `swdb build`.
- [ ] The contract is offload-only: it keeps its predecessor's thread split and loop order
      (`DeltaStep` itself, or the derived implementation the enabling contracts it names produce)
      and names any required enabling contracts in order (ID and version range). It states its unit
      relation, its bound dimensions (thread count among them) and, per interface array of the proof
      unit, its shared-action kinds and whether its reads are history reads. Every kind is in the
      method version's fixed set. Sharing classes stay per candidate (map ticket 16 item 4).
- [ ] The proof unit is one whole `DeltaStep` call. The unit postcondition states shortest distances
      over integer weights. Its distance definition lives in SSSP's own logic-library file and passes
      the library's primitive-recursion and `\false` checks.
- [ ] The contract records which form handles the `assert(false)`: (a) "delta ≤ least weight" as a
      proof-unit precondition, proven at every real call through the lifting lemma or listed as a
      reduction with its own proof obligation (map ticket 09 item 10); or (b) a proof that the
      assert is unreachable. Either way the proof setup check finds no `assume` other
      than summary-generated ones.
- [ ] Every drafted formal half passes the five gates. Gate 4 runs the runtime form on every certify
      run of the reference instance under 01's SSSP check. Each rejection is recorded with its gate.
- [ ] `swdb prove` writes one proof record per contract-proof part, each with its content-hash set:
      the unit postcondition on the reference instance with its two lemmas; the order-independence
      lemma; the lifting lemma for SSSP (machine-checked, else an assumption entry of kind "written
      proof"); each formal-visible negative control refuted; the minimum-bounds derivation per rung.
      No formal-visible control proves.
- [ ] The contract proof's final hint set includes the outer-loop invariant hints, recorded as seeds.
      A fresh `swdb prove` run of the reference instance's unit with those seeds and no provider call
      proves it.
- [ ] Yan-Ru approves the contract, the output relation, the formal halves, the `assert(false)` form
      and the minimum bounds at promotion; the review cites the proof record IDs. RQ3 inputs are
      recorded as in 02, including the time on SSSP's distance definition.
- [ ] The contract-proof records that count come from mbit10, inside a socket lane.

## Notes

- **Not in this ticket:** 01 — Correctness checks and certification drivers for PR and SSSP; 02 — BC
  held-out contract and contract proof; 03 — PR held-out contract and contract proof; 05 — LLM
  candidate populations; 06 — Authors' code and seeded faults; 08 — RQ3: what a contract buys.
- 02's notes on who proves, soundness, the reference instance, drafting inputs and machines apply
  here unchanged.
- Assumption (not decided in the map): which of the two `assert(false)` forms to use is the drafting
  agent's proposal, settled by Yan-Ru at promotion. Map ticket 24 allows either.
- **Risk (named in the design):** SSSP's per-candidate proofs need delta-stepping's outer-loop
  invariant. Before the freeze this was tested only on a synthetic fixture
  ([proof-of-concept 40 — Bucketed-relaxation fixture](../../probata-proof-of-concept-2026-10-13/issues/40-bucketed-relaxation-fixture.md)).
  If the contract proof cannot state it, re-plan with Yan-Ru. SSSP is on the floor: if it cannot
  finish, the submission waits.
- **Risk:** a needed shared-action kind outside the fixed five makes a new method version (02's
  risk). Stop and ask Yan-Ru.
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.
