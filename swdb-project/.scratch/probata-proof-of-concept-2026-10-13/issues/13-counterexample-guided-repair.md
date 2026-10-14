# 13 — Counterexample-guided repair

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 12
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Refutation, repair and bugs"; "Proof-hint loop" (the three loops, kept apart); "Concurrency" (repair, not hand fixes); "Extensa mode" (budgets: repair calls stay in the rewriting total); "ArchEvolve mode"; "Testing Decisions", seams 1 and 4 (seam 3's repair cases run in 14); user stories 18, 26, 48, 65, 71; S6; O1; O5); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 6, 10), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) (items 10, 11), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (item 6), [20](../../formal-verification-2026-10-09/issues/20-dx100-pr-reset-check.md) (inputs to 18: fail certification or be refuted), [22](../../formal-verification-2026-10-09/issues/22-cex-guided-llm-repair-research.md) (items 5, 6), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (items 3, 4), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) (items 2, 3, 5)
**Time estimate:** about 2 days

**What to build:** A refutation becomes a better candidate artifact instead of a dead end. When the
bounded verifier refutes a certified candidate artifact, the counterexample in the refuted proof
record goes to the rewriting role as correctness-repair feedback, never to the proof-hint agent.
The loop runs at most 5 rounds, one provider call each. Each repaired candidate artifact is a new
candidate artifact: its own record, a proposal with repair lineage (12), certified again and gated
again by the bounded rungs. A deterministic contract-match check flags a reverted repair, one that
drops the offload or equals the baseline implementation. A flagged repair may compete but never
counts as a repair. The same loop serves both settings: outside campaigns (ArchEvolve mode's one
candidate artifact, the evaluation's RQ4 subjects) and inside them (14 wires it into
`swdb campaign`). This ticket is the one owner of the 5-round cap and the reverted-repair flag in
every mode; 14 and 18 only call the loop. In the evaluation only, the repair workspace may show the
authors' code when it is the refuted candidate artifact under repair (O5), and the loop also accepts
a refuted proof record for a candidate artifact that failed certification (the authors' code; O1:
refute, then repair; O5). Tested with a scripted bounded verifier and a scripted provider.

## Acceptance

- [ ] **Feedback goes to the rewriting role.** `swdb repair`, given a refuted proof record (scripted
      bounded verifier, inline counterexample) for a certified fixture candidate artifact, opens a
      repair call in the rewriting role. Its provider workspace holds the refuted candidate
      artifact's patch and the counterexample, and its workspace manifest hashes both.
- [ ] **Never to the proof-hint agent.** The provider guard refuses a counterexample in every
      workspace except a rewriting-role repair workspace. Negative controls, one per workspace: a
      counterexample placed in a profiling, estimation, independent test generation or synthesis
      workspace, or in an ordinary (non-repair) rewriting workspace, is refused before a provider call
      opens.
- [ ] **At most 5 rounds, one call each.** When the scripted verifier refutes every repaired
      candidate artifact, the loop makes exactly 5 provider calls and stops, recording that the
      repair budget is spent (a loop outcome, not a proof failure class); no sixth call opens. Each
      round's proposal records its round. Control: a repair that the scripted rungs do not refute in
      round 2 ends the loop after 2 calls. The cap and the flag live only here, for every caller
      (campaigns through 14, ArchEvolve mode through 18, the evaluation).
- [ ] **A repaired candidate artifact is new.** Each one gets its own candidate record and content
      hash. Its proposal carries repair lineage (refuted candidate artifact, proof record with the
      counterexample, round, reverted-repair flag) and its provider pin (12). It is certified by the
      certification command and gated by `swdb prove`'s bounded rungs before anything else uses it.
- [ ] **The refuted candidate artifact stays as it was.** Its records are byte-identical afterward.
      It keeps its test record and its refuted flag, and `swdb candidate-level` still reads it as
      refuted. When the scripted rungs prove a repaired candidate artifact, `swdb candidate-level`
      reads that repair at the proven sub-rung they gave.
- [ ] **Reverted repair flagged.** The contract-match check is deterministic (no LLM) and runs on
      every repaired candidate artifact. It sets the reverted-repair flag when the repair no longer
      applies the refuted candidate artifact's rewrite contract. Negative controls: a scripted
      provider that returns the baseline implementation (normalized content hash equal to the
      baseline's) is flagged; one that drops the offload is flagged; a genuine repair that still
      applies the contract is not.
- [ ] **Flagged repairs compete but never count.** A flagged repair stays a candidate artifact,
      eligible for selection at its own level. The loop's outcome counts it as a reverted repair,
      never as a repair.
- [ ] **Repair calls are rewriting calls.** Every call the loop makes is recorded as a rewriting-role
      repair call, never as a proof-hint call. (So it never draws on `provider_calls_proof` (name
      decided in map 13), which 16 adds; repair calls stay in the rewriting total, 25 item 2.)
- [ ] **Works outside campaigns.** `swdb repair`, ArchEvolve mode's existing repair command, which
      today admits only build or correctness failures, also admits a refuted proof record as its
      trigger and runs this loop as the mode's allowed bounded correctness repair (25 item 5).
      Control: a regression still admits no repair. The resulting records pass `swdb validate` and
      `swdb build`.
- [ ] **The authors' code under repair (O5).** In an evaluation repair run, the provider guard lets
      the rewriting-role repair workspace show a guarded authors' function only when it is the
      refuted candidate artifact under repair. Negative controls, each refused before a provider call
      opens: the same function in a `swdb campaign` repair workspace; in ArchEvolve mode's repair;
      in an ordinary rewriting workspace; in an evaluation repair workspace whose refuted candidate
      artifact is a different one. Fixtures stand in with a guarded name in contract-fixture code,
      never the authors' code.
- [ ] **Refuted but uncertified (O1, O5).** In an evaluation repair run, `swdb repair` accepts a
      refuted proof record for a candidate artifact that failed certification (the authors' code)
      and runs this loop: same rounds, cap and reverted-repair flag. Fixture: a guarded-name
      candidate artifact with a failing certification record and a scripted refuted record. Control:
      the same pair outside an evaluation repair run (a `swdb campaign` repair, ArchEvolve mode's
      repair) is refused before a provider call opens.

## Notes

- **Not in this ticket:** 14 — Bounded gate in the campaign (calls this loop from `swdb campaign`;
  tests the count apart from D7's 2 certification repairs). 15 — Two winners (repaired candidate
  artifacts in selection). 16 — Post-campaign WP phase and budgets (the repair-call line in
  `budgets.used` (name decided in map 26)). 17 — Iteration ladder (repair workspaces get
  `LADDER.json`; `refuted` reason code; `repair_of` rows; names decided in map 28). 18 — ArchEvolve
  mode level and handoff block (the gate on ArchEvolve mode's one candidate artifact; it calls this
  loop). 22 — SAW adapter and SAWScript translator and 46 — CIVL adapter (real counterexamples).
  34 — proof_hinting role and workspace (its workspace inherits this guard rule; the `proof_hinting`
  (name decided in map 13) negative control, the case the design names, can only run there; 34 tests
  it (hidden-material controls)). 37 — The proof-hint loop (a refuted candidate artifact
  never reaches WP, S6). 49 — Peter's race repaired; A4 exit (the general race fix on CIVL's race
  trace). Evaluation 06 — Authors' code and seeded faults (runs the authors' PageRank repair under
  O5). Evaluation 09 — RQ4: refutation and repair (repair rate after round 1 and after round 5; the
  three repair mirrors; patch size as tree edit distance).
- **One owner, every mode:** the 5-round cap and the reverted-repair flag live here. 14 (campaigns)
  and 18 (ArchEvolve mode) only call this loop; neither re-implements the cap or the check.
- **Three loops stay apart** (13): Extensa mode changes code for speed; this loop changes code for
  one refuted candidate artifact; the proof-hint loop never changes code. Hint records never enter a
  rewriting workspace (34 tests that side).
- Assumption (not decided in the map): round r repairs the candidate artifact round r-1 produced,
  citing its refutation. The 5-round cap covers the whole chain from the first refuted candidate
  artifact.
- Assumption (not decided in the map): outside campaigns the loop's entry is `swdb repair`, extended
  to take a refuted proof record as its trigger; the evaluation's RQ4 runs drive the same command.
- Assumption (not decided in the map): outside campaigns too, the 5 counterexample rounds are counted
  apart from `swdb repair`'s existing build or correctness repair cap (the provider configuration's
  repair limit, default 2), as 25 item 3 counts them apart from D7's 2 inside campaigns. A repaired
  candidate artifact that fails certification may use that cap.
- Assumption (not decided in the map): a reverted repair ends the loop, because the result no longer
  applies the contract the counterexample was checked against.
- Decided: the 5-round cap is a per-candidate budget of the method version (25 item 2). The loop reads it from the pinned
  method-version file's budgets (11 is upstream; tests use the `contract_fixture` file).
- Assumption (not decided in the map): the rule "counterexamples only in rewriting-role repair
  workspaces" is enforced in the provider guard.
- Assumption (not decided in the map): how 15 item 10's general race fix (plain reads of
  shared-action locations become relaxed atomic loads; redundant plain stores removed) reaches the
  rewriting role, a prompt sentence for race counterexamples or a deterministic rewrite, is settled
  in 49. This loop passes any bounded counterexample on unchanged.
- **The authors' code (O5; default applied until Yan-Ru rules):** RQ4 repairs the authors' DX100
  code (18 item 6; 23 item 10; spec O1: the authors' PageRank, refute then repair). The rewriting
  role may see the authors' code only when it is the refuted candidate artifact under repair, in
  the evaluation, never in a campaign. The authors' PageRank counts as caught when it fails
  certification or is refuted (20). The bounded verifier runs on it whatever certification says
  (O1), so a refuted record can exist for a candidate artifact that failed certification; this loop
  takes it. `swdb repair`'s existing certification-repair path applies only when no refuted record
  exists, and evaluation 06 then stops for Yan-Ru before any repair call. The proof of concept
  repairs only Peter's code (49); the authors' `TDStepMAA` is reported only.
- Assumption (not decided in the map): outside an evaluation repair run, a refuted record for a
  candidate artifact that failed certification is refused, since campaigns and ArchEvolve mode run
  the bounded rungs only after certification.
- Assumption (not decided in the map): an evaluation repair run is marked as such when
  `swdb repair` starts it, and the mark is recorded in the workspace manifest. `swdb campaign` and
  ArchEvolve mode never set it. The guard reads the mark.
- Risks: evidence that counterexamples help LLM repair is mixed (22 item 5). Models may copy the
  reference (Orvalho et al.); the reverted-repair check catches that. Cite Orvalho et al. (AAAI 2025)
  and AuthFix (ASE 2025) where the term first appears in the paper (22 item 6).
- Fixtures use contract-fixture code only. No held-out kernel code (BC, PR, SSSP) before 59 —
  Method-version review and freeze. Tests use the scripted verifier and provider; no real verifier
  runs. Full-suite runs on the Mac use at most 2 test workers.
