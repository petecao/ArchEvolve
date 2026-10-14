# 18 — ArchEvolve mode level and handoff block

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "ArchEvolve mode", "Records and levels", "What a proven verdict asserts" (assumption set, seven kinds), "Refutation, repair and bugs", "Verifier lineup and order", "Testing Decisions" seams 1, 2 and 4; choices S1, S2, S6; open point O1); decisions: [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) items 2-3, 5, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 2, 4, 7, 9, 10
**Time estimate:** about 2 days

**What to build:** In ArchEvolve mode, a rewrite proposal's one final candidate artifact gets the
same proof path as in Extensa mode, with the same budgets. Once certified, it runs the bounded gate.
A refutation calls 13's counterexample-guided repair loop, which counts as the mode's allowed
bounded correctness repair. Then the unbounded rung runs. The team sees the outcome in the handoff: the
`evaluation_result` envelope gains a `certification_level` block in plain words. It gives the
level, each bound as a value or "any", each assumption as one sentence, "says nothing about speed",
and the proof record IDs. When not proven, it gives the highest level reached and the failure class
in words. Every sentence comes from a fixed template; no LLM writes them. The level is reported,
never ranked. Built and tested with the scripted verifier adapter.

## Acceptance

- [ ] **Same gate.** A certified ArchEvolve-mode fixture candidate artifact runs the bounded rungs
  at its contract's minimum bounds through `swdb prove`, with the method version's per-candidate
  budgets (the same as Extensa mode's). An uncertified or rejected candidate artifact runs no proof
  step.
- [ ] **Refutation calls 13's repair loop.** This ticket tests only the call: a scripted refutation
  on this mode's gate invokes 13's counterexample-guided repair loop as the mode's allowed bounded
  correctness repair (25 item 5), and each repaired candidate artifact it returns comes back
  through this mode's gate. Control: a candidate artifact the gate does not refute opens no repair.
  The 5-round cap, the counterexample's destination and the reverted-repair flag are 13's and
  tested there.
- [ ] **Unbounded rung (S6).** A candidate artifact the bounded rung did not refute (proven, timed
  out, or no minimum bounds) goes on to the unbounded rung, which writes one proof record. A refuted
  candidate artifact never reaches it.
- [ ] **Block when proven.** Proven unbounded fixture: the block shows the level, every bound
  dimension as "any", each assumption as one sentence, "Says nothing about speed.", and the proof
  record IDs. Proven within bounds fixture: each bound dimension shows its value, thread count
  always among them.
- [ ] **Block when not proven.** The block gives the highest level reached and the failure class in
  words (for example "hint budget spent"), plus the proof record IDs of the attempts.
- [ ] **Template sentences only.** One fixed template per assumption kind (all seven: assumed
  clause, proof semantics, summary, reduction, trusted tool, written proof, platform choice), plus
  each assumed clause's own sentence. A test renders every kind. Negative controls: free text
  planted in a fixture proof record's assumption entry never reaches the block; an assumption kind
  with no template stops rendering with an error instead of producing text.
- [ ] **Dated snapshot.** The block is a snapshot that is dated and names the level-rule version.
  After a pin changes, `swdb candidate-level` reads a lower level, but an already rendered handoff
  keeps its dated snapshot.
- [ ] **Reported, never ranked, no speed claim.** The block has no rank or score. The level never
  changes the envelope's performance claim or result class. Control: a proven-unbounded candidate
  artifact with no gain still carries no performance claim.
- [ ] **Handoff envelope seam.** Every rendered `evaluation_result` envelope carries the block,
  with "Says nothing about speed." and, when proven, the counting proof record IDs. Negative
  controls: a proven level whose proof record IDs cannot be resolved, or a block missing the speed
  sentence, stops rendering with an error instead of emitting the envelope. The proof records behind
  the block pass `swdb validate` and `swdb build`.

## Notes

- **Not in this ticket:**
  - 14 — Bounded gate in the campaign: the gate inside the Extensa loop.
  - 13 — Counterexample-guided repair: the repair loop this ticket calls, with its 5-round cap,
    the counterexample's destination and the reverted-repair flag.
  - 63 — Experimental enabling contracts and the shared-contracts rule: refusing non-shared
    (experimental) contracts in ArchEvolve mode.
  - 16 — Post-campaign WP phase and budgets: WP scheduling in Extensa mode.
  - 10 — Level rule: computing the level and its snapshot.
  - 11 — Method-version file and failure classes: per-candidate budgets and the failure-class list.
  - 12 — Proposal and promotion fields: repair lineage on proposals; promotion review pins.
  - 19 — Derived implementations: rewrite chains, where each rewrite is one rewrite proposal.
  - 22 — SAW adapter and SAWScript translator, 37 — The proof-hint loop: the real verifiers behind
    the scripted adapter.
- Example block (design spec): "Proven for every graph and every thread count. Assumes: DX100
  follows its proof semantics v3, each rule cited to gem5 source; clang 22.1.8 compiles correctly;
  CPU caches hold no stale copy after a DX100 store (assumed; owner Eric). Says nothing about speed."
- Proven requires certified (O1): an uncertified candidate artifact's block shows the level
  certification gives.
- Assumption (not decided in the map): ArchEvolve mode's existing proposal commands (submit, then
  repair) drive the gate by calling `swdb prove`, and the tests drive those commands with the
  scripted adapter. The confirmed seams name only the proof command, `swdb candidate-level` and the
  handoff envelope for this mode.
- Assumption (not decided in the map): "same budgets" means the method version's per-candidate
  budgets (hint rounds, loop wall time, 15 minutes per bounded job, 5 repair rounds). ArchEvolve
  mode has no campaign, so `provider_calls_proof` and campaign lane-hours do not apply.
- Repair limits: ArchEvolve mode's existing build or correctness repair limit comes from the
  provider configuration (default 2, range 0-5), not D7's 2 (the campaign's certification repairs,
  25 item 3). Counterexample repair runs within the 5 rounds (25 item 5). How the two counts relate
  is 13's (its assumption: counted apart).
- Assumption (not decided in the map): the bounded gate runs after certification and before the
  evaluator's measurement; the unbounded rung runs after the measurement ends, never overlapping a
  timing step or a gem5 simulation, and runs whether or not the candidate artifact shows a gain.
- Assumption (not decided in the map): the plain words for each failure class live beside the
  failure-class list, and the envelope's format version rises with the new block.
- Assumption (not decided in the map): the handoff envelope is checked where it is rendered, not by
  `swdb validate` (it is a message, not a stored record).
- Generality: per contract, kernel and hardware target; nothing BFS- or DX100-specific. Contract
  fixtures only; no held-out kernel (BC, PR, SSSP).
- Tests use the scripted adapter; no real verifier job runs. Full-suite runs on the Mac use at most 2
  test workers.
