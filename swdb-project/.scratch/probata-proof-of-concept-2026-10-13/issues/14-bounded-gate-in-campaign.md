# 14 — Bounded gate in the campaign

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 02, 11, 13
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Solution" (one candidate artifact's path, steps 1-3); "Bounds" (minimum bounds, Extensa mode proves at the minimum only, 15 minutes per bounded job); "Verifier lineup and order" (order per candidate; skip reasons); "Extensa mode" (bounded gate); "Testing Decisions", seam 3; user stories 22, 64, 65; S6; S8; O7); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (item 3), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) (item 9), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 1, 3, 6, 7, 8), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) (items 1, 3); [ADR 0010 proof note](../../../docs/adr/0010-extensa-mode-loop.md) ("Bounded gate")
**Time estimate:** about 2 days

**What to build:** In `swdb campaign`, refuted code never spends evaluation time. Right after
certification and before speed evaluation, each certified final candidate artifact runs the two
bounded rungs through `swdb prove`, at its contract's minimum bounds: one thread (SAW), and
threads ≤ k (CIVL, with GenMC as second refuter). The one exception to "minimum only" is k = 3, the
thread count CIVL runs at (19 item 6). The two rungs run in parallel, 15 minutes each; the budget
and k come from the method version (11). A refuted candidate artifact is never evaluated: it goes to
counterexample-guided repair (13), at most 5 rounds, counted apart from D7's 2 certification
repairs. A candidate artifact with no contract proof, no minimum bounds, or code outside the C++
subset skips only the steps that need the missing piece (O7), keeps its level and is evaluated as
today. Shown end to end by a contract-fixture campaign (`swdb campaign --fixture`) with a scripted
verifier adapter.

## Acceptance

- [ ] **Order.** In a `swdb campaign --fixture` run, each certified final candidate artifact's
      bounded jobs start after its certification records exist and before its evaluation step.
      Uncertified and rejected candidate artifacts get no bounded job.
- [ ] **Every contract.** A candidate artifact that applies two contracts runs the rungs for each
      contract's proof unit (one per contract, 10's assumption), at that contract's minimum bounds
      (this uses 02's every-record links). A refutation under either contract refutes the candidate
      artifact.
- [ ] **Minimum bounds only, and k = 3.** Each job runs at its rung's minimum bounds: the
      single-thread minimum for the one-thread rung, the multi-thread minimum for threads ≤ k. The
      one decided exception is the threads ≤ k rung's thread count: it runs at k = 3, the method
      version's k, above the multi-thread minimum of 2 threads (19 item 6; 15 item 9). Each proof
      record pins the minimum-bounds version. No campaign job runs any other dimension above the
      minimum.
- [ ] **Parallel, 15 minutes each.** Under the scripted adapter, a candidate artifact's two rungs run
      in parallel, each with a 15-minute wall budget. Both values (15 minutes and k) are read from
      the pinned method-version file's budgets (11's `contract_fixture` file in tests). A scripted job
      that runs out gives "not proven, timeout" for that rung only: no bounded level from it, no
      retry at smaller bounds, and the candidate artifact goes on to evaluation.
- [ ] **Refuted is never evaluated.** After a scripted refutation on either rung, the candidate
      artifact gets no evaluator call and spends no lane-hours on evaluation, so it cannot win. Its
      counterexample enters 13's loop. A repaired candidate artifact is certified, gated and, if not
      refuted, evaluated and ranked like any other. Control (seam 3's reverted-repair case): a
      scripted repair that returns the baseline is flagged as a reverted repair in campaign state,
      keeps the level certification gives it (it applies no contract, so it gets no bounded job),
      may still be evaluated and compete, and is never counted as a repair.
- [ ] **Two repair counters.** A refuted candidate artifact gets at most 5 counterexample repair
      rounds, on a counter apart from D7's 2 certification repairs. The 5-round cap and the
      reverted-repair flag come from 13's loop; the campaign only calls it. Fixture: a repaired
      candidate artifact that fails certification once uses one certification repair and no
      counterexample round. The campaign state shows both counters; both kinds of call count in the
      rewriting total.
- [ ] **Skips keep the level (O7).** A skip skips only the steps that need the missing piece. Fixture
      candidate artifacts with (a) no contract proof, (b) no minimum bounds, (c) code outside the
      C++ subset. (a) and (b) get no bounded rung, keep their level, and stay eligible for the WP
      phase later (16; route-1 WP needs only a unit postcondition; O7, S6). (c) runs the one-thread
      rung and skips threads ≤ k. Each skip records its skip reason, each candidate artifact keeps
      its level, and each is evaluated. Control: the same candidate artifact with a contract proof
      and minimum bounds runs both rungs.
- [ ] **Level read, never stored.** After the gate, `swdb candidate-level` reads each gated candidate
      artifact at the sub-rung its rungs proved (threads ≤ k above threads = 1), or certified. The
      campaign uses that computed level and stores none.
- [ ] **No change when nothing is gated.** A fixture campaign whose candidate artifacts all skip the
      gate runs the same evaluation steps and writes the same summary as before this ticket, apart
      from the recorded skips. D35's start gate is untouched.

## Notes

- **Not in this ticket:** 02 — Campaign adapter returns every certification record. 11 —
  Method-version file and failure classes (the budgets this gate reads, k among them; the skip
  reasons). 13 — Counterexample-guided repair (the loop itself, the 5-round cap and the
  reverted-repair check). 15 — Two winners (selection, the best-patch files, the plateau test; a
  refuted candidate artifact wins neither). 16 — Post-campaign WP phase and budgets (WP after the
  campaign stops; `provider_calls_proof` (name decided in map 13); the gate's proof jobs counted in
  lane-hours and reported apart). 17 — Iteration ladder (`refuted` and `proof_timeout` reason
  codes; names decided in map 28). 18 — ArchEvolve mode level and handoff block (the same gate on
  ArchEvolve mode's one candidate artifact). 19 — Derived implementations (records derived
  implementations). 22 —
  SAW adapter and SAWScript translator, 46 — CIVL adapter, 47 — GenMC adapter and agreement (the
  real rungs; a CIVL–GenMC contradiction stops the batch). 33 — Minimum-bounds script and A2 exit (real minimum
  bounds). 37 — The proof-hint loop (no contract seeds for a proof unit with no contract proof,
  O7). 55 — End-to-end fixture campaign with real verifiers. 57 — Proof workers in a socket lane.
  62 — Route choice and predecessor proofs in the campaign (route 3 or route 1 per final candidate
  artifact; builds intermediate-rewrite marking, after which an intermediate gets no bounded job).
- **Interim rule:** this ticket gates every certified candidate artifact the campaign would evaluate.
  62 builds intermediate-rewrite marking; until it lands, and for good if 62 is cut, this rule stays.
- **Why before evaluation** (25 item 1): in campaign a7, an iteration with a certified candidate
  artifact took 2.5-4 h of gem5 wall time; the gate takes about 15 minutes, and a refutation saves
  the whole evaluation.
- **Only a refutation blocks later proofs** (S6): a bounded timeout or missing minimum bounds does not
  stop the WP phase (16).
- **k = 3 is the one decided exception to "minimum only"** (19 item 6): the multi-thread minimum is 2
  threads, but CIVL runs keep k = 3 (15 item 9). k is a method-version budget (S8), calibrated like
  the others before the freeze.
- Decided: the 15-minute budget and k come from the pinned method-version file's budgets (25 item 2;
  S8). 11 builds that file and is a blocker, so the gate has no fallback default.
- Each job's wall time lands in its proof record's job block (12), so 16 can report proof lane-hours
  apart.
- Assumption (not decided in the map): on the Mac, real verifier jobs queue one at a time under the
  ~8 GB RSS watchdog (Mac RAM rule). "In parallel" holds for the scripted adapter and on mbit10
  lanes; each job keeps its own 15-minute budget.
- Assumption (not decided in the map): under O7's rule, code outside the C++ subset still runs the
  one-thread rung, because SAW reads the C++ bitcode, while CIVL and GenMC read the C lowering (15
  item 9). So only the threads ≤ k rung is skipped here, and the candidate artifact can reach proven
  within bounds, threads = 1 (11 item 3). WP, which also reads the C lowering, is skipped later for
  the same reason.
- Contract fixtures only; no held-out kernel (BC, PR, SSSP) before 59 — Method-version review and
  freeze. Tests use the scripted adapter; no real verifier runs. Full-suite runs on the Mac use at
  most 2 test workers.
