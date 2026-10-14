# 55 — End-to-end fixture campaign with real verifiers

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16, 17, 39, 48, 60, 63
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Extensa mode", "Refutation, repair and bugs", "Records and levels" (campaign summary), "Verifier lineup and order", "Proof-of-concept plan" (Extensa track, cut order), "Testing Decisions" (seam 3); S1, S2, S6, O6); decisions: [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) items 1-4; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 4, 5, 7; [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md) items 1-5, 8
**Time estimate:** about 3 days
**Cut order:** 4

**What to build:** The Extensa track's exit. One `swdb campaign --fixture` campaign runs the whole
Probata loop with the real verifier adapters plugged in where tickets 13-17 used the scripted one: the
bounded gate, counterexample-guided repair, evaluation with fixture numbers, the WP phase after the
campaign stops, both winners and the iteration ladder. Yan-Ru sees, in one campaign summary, that the
loop logic built against scripted verdicts still holds when SAW, CIVL, GenMC and WP decide.

## Acceptance

- [ ] **Extensa track exit** (design spec, "Proof-of-concept plan"; 27 item 5): one `--fixture`
  campaign runs gate, repair, evaluation, WP phase and both winners end to end with real verifiers,
  plus the iteration ladder (28). Concretely: a contract-fixture campaign on the BFS read-offload
  contract runs through `swdb campaign --fixture` with the real SAW, CIVL, GenMC and WP adapters; every
  verifier run passes the proof setup check; every record carries `contract_fixture` evidence. The
  criteria below check each part.
- [ ] **Bounded gate before evaluation.** A certified candidate artifact that races at N > 1 is refuted
  by the gate (CIVL refutes, GenMC agrees). It gets no evaluation record and leaves selection. Its
  refutation's proof record carries the replay label 60's replay step gives it: "undefined behavior (no
  strict-layer replay)" (design O6), so the refutation counts and the batch goes on.
- [ ] **Counterexample-guided repair.** The refutation's counterexample goes to the repair call, never
  to the proof-hint agent: at most 5 rounds, counted apart from D7's 2 certification repairs. The
  repaired candidate artifact is new: certified, gated (proven within bounds, threads <= k), evaluated
  with fixture numbers and ranked. Its proposal carries repair lineage (refuted candidate artifact,
  counterexample proof record, round, reverted-repair flag).
- [ ] **Both winners.** Per workload class, the summary shows the fastest winner and the best-proven
  winner from real verdicts, each with a dated level snapshot naming the level-rule version. The fixture
  includes one certified candidate artifact the gate cannot prove (a skip reason or a timeout), faster
  than the proven one, so the two winners differ in at least one class.
- [ ] **WP phase.** It starts only after the campaign stops, on gain candidate artifacts, fastest first, and
  ends when one is proven unbounded or the budget ends. No proof job overlaps a timing step. The summary
  is rewritten once when the phase ends. Real WP sets the level reached. A WP proof at threads = 1
  gives at most proven within bounds (11 item 10); proven unbounded needs WP's per-thread proof for
  symbolic N (45's lowering, as 49 shows on Peter's repair).
- [ ] **Iteration ladder.** From iteration 2, `LADDER.json` has one row per earlier candidate artifact,
  with no gaps: the refuted one with reason `refuted`, the repaired one with `repair_of`, levels as known
  in the loop (never proven unbounded) and winner marks. Repair calls see it. State and summary record
  `rewrite_workspace: v2`. Negative control: the leakage check rejects a row that carries a counterexample
  or a raw timing.
- [ ] **Budgets.** Proof-hint calls count under `provider_calls_proof`, never in the rewriting total.
  `budgets.used` shows proof lane-hours, proof-hint calls and repair calls on their own lines.
- [ ] **Records hold.** `swdb validate` and `swdb build` accept every record. `swdb candidate-level`
  recomputes, on read, the same levels the summary snapshot shows.
- [ ] **Mac rules.** One real verifier job at a time under the ~8 GB RSS watchdog, so the gate's rungs
  run one after another here; at least 50 GB free; a 30-minute heartbeat if the run passes 30 minutes.

## Notes

- **Not in this ticket:**
  - 13 — Counterexample-guided repair; 14 — Bounded gate in the campaign; 15 — Two winners; 16 —
    Post-campaign WP phase and budgets; 17 — Iteration ladder: each piece and its scripted-adapter
    tests. This ticket only swaps in real adapters and runs them together.
  - 60 — Strict-layer replay and whole-kernel reproduction: the replay step and its labels, which
    this campaign's refutations carry.
  - 63 — Experimental enabling contracts and the shared-contracts rule: those rules themselves. This
    campaign runs with them in place.
  - 18 — ArchEvolve mode level and handoff block: ArchEvolve mode's one-candidate-artifact path.
  - 49 — Peter's race repaired; A4 exit: the per-thread proof that lets WP reach proven unbounded.
  - 57 — Proof workers in a socket lane: the gate's rungs in parallel, on mbit10.
  - evaluation 10 — RQ5: end-to-end BFS campaigns: real-target campaigns (D35 still refuses them).
- Assumption (not decided in the map): only the verifier adapters become real. The rewrite, repair and
  proof-hint providers replay recorded fixture outputs (for example, the hint set 39 proved with), so the
  run is repeatable and spends no provider calls. A run with the live Codex proof-hint agent is optional.
- Assumption (not decided in the map): how the campaign picks real or scripted adapters (a flag or a
  fixture setting) is open; choose the smallest change to the existing `--fixture` path.
- Assumption (not decided in the map): the fixture's candidate artifacts are Peter's read offload as
  written (certifies, races at N > 1) and its store-free repair as the recorded repair output, plus one
  certified candidate artifact the gate skips or times out on.
- **The race refutation's replay label (design O6, default until Yan-Ru rules):** a data race is
  undefined behavior, not a strict-layer rule, so it cannot replay on the strict layer. It gets the
  label "undefined behavior (no strict-layer replay)" instead of "not reproduced", and the batch goes
  on. Calling it a "bug" would still need a whole-kernel reproduction (60).
- **Design vs Mac:** the design runs the gate's rungs in parallel. The Mac's one-job rule makes them
  sequential here; this changes timing only, never a verdict.
- **Cut:** fourth in the proof of concept's cut order. If cut, this exit moves after the evaluation with
  RQ5 (27 item 7); the record and loop tickets still stand.
