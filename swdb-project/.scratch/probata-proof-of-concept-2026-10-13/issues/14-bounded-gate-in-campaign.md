# 14 — Bounded gate in the campaign

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
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

- [x] **Order.** In a `swdb campaign --fixture` run, each certified final candidate artifact's
      bounded jobs start after its certification records exist and before its evaluation step.
      Uncertified and rejected candidate artifacts get no bounded job.
- [x] **Every contract.** A candidate artifact that applies two contracts runs the rungs for each
      contract's proof unit (one per contract, 10's assumption), at that contract's minimum bounds
      (this uses 02's every-record links). A refutation under either contract refutes the candidate
      artifact.
- [x] **Minimum bounds only, and k = 3.** Each job runs at its rung's minimum bounds: the
      single-thread minimum for the one-thread rung, the multi-thread minimum for threads ≤ k. The
      one decided exception is the threads ≤ k rung's thread count: it runs at k = 3, the method
      version's k, above the multi-thread minimum of 2 threads (19 item 6; 15 item 9). Each proof
      record pins the minimum-bounds version. No campaign job runs any other dimension above the
      minimum.
- [x] **Parallel, 15 minutes each.** Under the scripted adapter, a candidate artifact's two rungs run
      in parallel, each with a 15-minute wall budget. Both values (15 minutes and k) are read from
      the pinned method-version file's budgets (11's `contract_fixture` file in tests). A scripted job
      that runs out gives "not proven, timeout" for that rung only: no bounded level from it, no
      retry at smaller bounds, and the candidate artifact goes on to evaluation.
- [x] **Refuted is never evaluated.** After a scripted refutation on either rung, the candidate
      artifact gets no evaluator call and spends no lane-hours on evaluation, so it cannot win. Its
      counterexample enters 13's loop. A repaired candidate artifact is certified, gated and, if not
      refuted, evaluated and ranked like any other. Control (seam 3's reverted-repair case): a
      scripted repair that returns the baseline is flagged as a reverted repair in campaign state,
      keeps the level certification gives it (it applies no contract, so it gets no bounded job),
      may still be evaluated and compete, and is never counted as a repair.
- [x] **Two repair counters.** A refuted candidate artifact gets at most 5 counterexample repair
      rounds, on a counter apart from D7's 2 certification repairs. The 5-round cap and the
      reverted-repair flag come from 13's loop; the campaign only calls it. Fixture: a repaired
      candidate artifact that fails certification once uses one certification repair and no
      counterexample round. The campaign state shows both counters; both kinds of call count in the
      rewriting total.
- [x] **Skips keep the level (O7).** A skip skips only the steps that need the missing piece. Fixture
      candidate artifacts with (a) no contract proof, (b) no minimum bounds, (c) code outside the
      C++ subset. (a) and (b) get no bounded rung, keep their level, and stay eligible for the WP
      phase later (16; route-1 WP needs only a unit postcondition; O7, S6). (c) runs the one-thread
      rung and skips threads ≤ k. Each skip records its skip reason, each candidate artifact keeps
      its level, and each is evaluated. Control: the same candidate artifact with a contract proof
      and minimum bounds runs both rungs.
- [x] **Level read, never stored.** After the gate, `swdb candidate-level` reads each gated candidate
      artifact at the sub-rung its rungs proved (threads ≤ k above threads = 1), or certified. The
      campaign uses that computed level and stores none.
- [x] **No change when nothing is gated.** A fixture campaign whose candidate artifacts all skip the
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

## Answer

2026-10-14 05:30 ET. Built test-first; every acceptance box is met. Branch `probata-poc/t14`.
Interface: [`format-v0.4-extensa.md`](../../../docs/reference/format-v0.4-extensa.md) "The bounded gate";
`swdb prove` options in [`format-v0.4-proof.md`](../../../docs/reference/format-v0.4-proof.md); the loop's
`charge` in [`format-v0.4-repair.md`](../../../docs/reference/format-v0.4-repair.md). Code `swdb/bounded_gate.py`.

**What exists now:**

- **The gate** (`swdb.bounded_gate.Gate`): on when the campaign's library holds a method version at setup
  (state and summary `bounded_gate`: method-version pin, `budget_minutes` = `bounded_job_minutes`, `k` =
  `civl_k`). Each certified candidate artifact, after certification and before evaluation, runs per contract
  `threads_1` at the single-thread minimum and `threads_k` at the multi-thread minimum with threads = k, in
  parallel (two threads, in-process `swdb prove`), each with the method version's wall budget. Each record
  pins its minimum-bounds derivation. Skips (O7): `no_contract_proof` (both rungs), `outside_cpp_subset`
  (`threads_k` only), `no_minimum_bounds` (that rung). Refuted is read by the level rule, never stored.
- **Campaign** (`swdb/campaign.py`): a refuted candidate artifact is never evaluated; its first refutation
  enters 13's `loop(setting="campaign")`. Each repair follows its refuted entry (`repaired_from`), is
  certified, gated and, when it ends the loop unrefuted (repaired, or a flagged reverted repair with no
  bounded job), evaluated and ranked. A repair that fails certification uses D7's certification repairs.
  Every counterexample repair call is charged to the D7 ledger before it opens (role
  `counterexample_repair`); `state.json` and the summary hold `repair_counters` (`certification_repairs`,
  `counterexample_repair_rounds`, `repairs`, `reverted_repairs`). The D7 certification loop moved into
  `Campaign._certification` unchanged in behavior. D35's start gate is untouched.
- **13's loop:** optional `charge` hook (cap checked first, so a spent budget charges nothing); new outcome
  `calls_refused`. **`swdb prove`:** `--bounds`, `--minimum-bounds`, `--budget-minutes`; `Job.bounds`,
  `Job.budget_seconds`; the scripted adapter kills a `run` command past the budget (not proven, timeout).
- **Fixture adapter:** `contract_proofs` (fixture contract-proof and minimum-bounds records written at
  setup), per class/attempt scripted verdicts (`proven`, `refuted`, `timeout`, `spurious`, or a mapping),
  `cpp_subset: false`; with `base_snapshot` a candidate artifact retains its own patch (`diff`). Real adapters:
  copy team-store contract proofs (none exist yet), proof function `TDStep`, no bounded verifier yet.

**Tests:** `tests/test_bounded_gate_campaign.py`, 11 tests (seam 3 `swdb campaign --fixture`, seam 2
`swdb candidate-level`, seam 1 scripted adapter budget). Serial, no xdist; 11 passed in 8 min 24 s; report log
`/tmp/claude/probata-runs/t14/gate-tests.jsonl`, sha256
`fa2fa2dae6adc692572aefd4c148506b95eab94a338b9f92b224fb75804c9669`. Regression run (`test_proof_records`,
`test_proof_method_version`, `test_format_doc`, `test_derived_implementations`,
`test_campaign_certification_links`, `test_extensa_campaign`, `test_campaign_budget_fixes`,
`test_campaign_candidate_records`, `test_campaign_structure`, `test_extensa_targets`,
`test_counterexample_repair`): 269 passed, 2 failed in 23 min, one worker
(`/tmp/claude/probata-runs/t14/regression.jsonl`, sha256
`e0f84f7f340571c8ee7208e5218642c25683b6831300bfdd9d021a4e90259f86`). The 2 failures were
`test_format_doc` (two new summary fields not yet named in the format docs); fixed in
`format-v0.4-extensa.md`, and `test_format_doc.py` then passed (4 of 4).

**Assumptions** (the ticket's own assumptions are implemented as written):

- Assumption: without a method version in the campaign's library the gate is off and the campaign runs as
  before (no summary block). The repository library has no `methods/` yet (ticket 21), so every existing
  campaign is ungated until then. A resumed campaign refuses a changed method version.
- Assumption: "contract proof" = at least one counting proven contract-proof part (other than the
  minimum-bounds derivation) of the contract's current content; the single-thread minimum is the counting
  derivation record with threads 1, the multi-thread minimum one with more threads.
- Assumption: the `threads_k` rung is one job (the scripted adapter stands in for CIVL with GenMC); 46/47
  split it into the CIVL job and the GenMC agreement.
- Assumption: the repair loop starts from the first refutation in job order (contract order, `threads_1`
  first); the repair call shows that one counterexample.
- Assumption: a counterexample repair that fails certification gets D7's certification repairs (its own 2,
  like any candidate artifact). Its certified result has no repair lineage, so if it is refuted the chain ends
  there (13's cap could not count a further round); it is not repaired again.
- Assumption: the campaign folder gets `library/` beside its store as a symlink to the campaign's library,
  and the records the library names are copied from the team store, because `swdb prove`, the repair loop
  and `swdb candidate-level` validate and read the store with the library beside it.
- Assumption: proof-job wall time is recorded (`bounded_gate.proof_job_hours`) but not charged to
  `lane_hours`; ticket 16 reports proof lane-hours apart.

**For other tickets:** 15 reads `bounded_gate.refuted` (a refuted entry has no `selection`) and the level
rule for the best-proven winner. 16 counts ledger role `counterexample_repair` in the rewriting total and
reads `bounded_gate.proof_job_hours` and each record's job block. 17 reads `bounded_gate` jobs
(`refuted`, `failure_class: timeout`) and `repaired_from` for ladder rows. 18 can reuse `Gate.run`
(`swdb.bounded_gate`) with `setting="archevolve"`. 22/46/47 implement `TargetAdapter.bounded_job` (and 24
`outside_cpp_subset`); 29/32/33 write the team-store contract proofs `prepare_proofs` copies. 55: the real
adapters' proposals have no `profile_package` or `constraints.editable_files`, so a real-target repair records
`counterexample_repair.state: not_started` until they do.

**Side finding (for Yan-Ru):** the spec default `provider_calls_per_iteration` is 3, and repair calls stay
in the rewriting total, so without an approval entry raising it a refuted candidate artifact gets at most 2
counterexample rounds per iteration (fewer with two classes), not 5; the loop then ends `calls_refused`.
The fixture tests raise the cap through the approval entry.
