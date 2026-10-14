# 40 — Bucketed-relaxation fixture

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 26, 37
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan": A3 row and exit check, two synthetic fixtures; "Further Notes": risk "SSSP needs delta-stepping's outer-loop invariant"; "Formal-half language and the C++ subset": logic-library rules; "Concurrency": shared-action kinds; "Proof-hint loop": Seeds; "Testing Decisions": fixture records; S13); decisions: [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (item 2, input 2), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) (items 3, 5, 10), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 9, seeds)
**Time estimate:** about 4 days

**What to build:** A synthetic bucket-worklist fixture with min-update CAS on distances, written for
this test and not taken from GAPBS SSSP. The loop proves its proof unit unbounded, with seeds from
a contract-proof-style seed set. This tests SSSP's riskiest proof, the outer-loop invariant of
bucketed relaxation, before the freeze and without touching the held-out kernel. If it fails,
Yan-Ru re-plans: SSSP is on the evaluation's floor.

## Acceptance

- [ ] **Fixture code.** A bucket worklist that relaxes edges with a min-update CAS on distances,
      inside the C++ subset, with integer weights. Its records carry `contract_fixture` evidence.
- [ ] **Unit postcondition.** A fixture contract states the shortest distances as its unit
      postcondition. The definition sits in the logic library, by primitive recursion on path
      length, and passes the logic library's primitive-recursion and `\false` checks.
- [ ] **Seed set.** A contract-proof-style proof of the fixture's reference version yields a hint
      set (the outer-loop invariant among them) that passes the proof hint check. Its record marks
      each hint's provenance, "human" where a person wrote it.
- [ ] **Proven by the loop.** `swdb prove` on the fixture unit under test (assumption below), with
      those seeds and no human step, gives WP's verdict proven: every goal Valid in the per-property
      report, smoke tests passed. Its hint provenance holds only "seed" (with source) and "agent".
      Hints a person wrote in the seed set's proof keep provenance "seed" here, and the step still
      counts as automatic (design S13).
- [ ] **Record and level.** The proof record names its bounds: threads = 1, every other dimension
      unbounded. It passes `swdb validate` and `swdb build`. With a fixture certification record
      for the unit, `swdb candidate-level` reads proven within bounds, threads = 1.
- [ ] **What the proof needed.** The minimized hint set shows which seeds the proof kept. The answer
      states whether the outer-loop invariant came from the seeds or from an agent round.
- [ ] **Fail path.** If the loop does not prove it within the budget, the record says "hint budget
      spent", and this ticket's answer records the re-plan with Yan-Ru.
- [ ] **No held-out code.** The fixture is written without reading GAPBS SSSP, the fork's
      `DeltaStep` or the authors' `DeltaStepMAA`.

## Notes

- **Not in this ticket:** 26 — Logic and sum libraries (the shared definitions this builds on); 37 —
  The proof-hint loop; 39 — BFS unit proven unbounded at one thread; A3 exit (reads this ticket's
  verdict for the A3 exit check); 44 — Shared-action kinds and commutativity lemmas (the min-update
  lemma); 45 — Per-thread lowering (symbolic N); evaluation 04 — SSSP held-out contract and contract
  proof.
- SSSP's distance definition is drafted after the freeze and counts in RQ3 (map 24 item 4).
  Assumption (not decided in the map): the fixture's definitions live in the fixture contract's own
  logic-library file, not the shared logic library, so they never become part of the method version
  and the held-out SSSP draft does not start from them.
- Assumption (not decided in the map): "proven unbounded" here means every bound dimension except
  thread count, at threads = 1, as for BFS in 39. The per-thread proof for symbolic N needs 45 (A4).
  At one thread the min-update CAS is a sequentially consistent read-modify-write (spec
  "Concurrency").
- Assumption (not decided in the map): the seed set comes from a proof of a reference version of the
  fixture, as a contract proof uses its reference instance. The unit under test is at least one
  differently written version, proven by the loop with those seeds, so seeds are tested as transfer,
  not replay. If Yan-Ru prefers one version, the reference-version proof alone shows less.
- Assumption (not decided in the map): the fixture contract states no SSSP-specific precondition
  (the "delta ≤ least weight" side finding belongs to the held-out SSSP contract).
- Mac: one real verifier job at a time under the ~8 GB RSS watchdog. Record the output destination
  and size budget before the first run (LR-06).
