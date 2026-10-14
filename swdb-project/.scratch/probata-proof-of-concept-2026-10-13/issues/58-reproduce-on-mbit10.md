# 58 — Mac verdicts reproduced on mbit10

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 38, 40, 49, 51, 53, 54, 57, 61 (drop 51, 53, 54 if cut)
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop" (budget, machines), "Bounds" (bounded-job budget), "Verifier lineup and order" (k), "Providers and machines", "Records and levels" (where things live), "Proof-of-concept plan" (A6 exit, cut order); S8); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) items 11, 13; [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) items 5, 6, 10; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 2, 5, 7; [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 8; [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) item 9
**Time estimate:** about 1 week

**What to build:** Part 1 of the A6 exit. Every Mac verdict of this effort (the spike excluded) is
re-run on mbit10 inside a socket lane and must come out the same. Every difference is root-caused
before the freeze. The budgets are then recalibrated on mbit10: hint rounds, loop wall time, WP solver
time, bounded-job time and CIVL's k. Mac results stay labeled and are never mixed with mbit10
numbers. Yan-Ru gets mbit10 evidence for every calibration result and the final budget values for
the method-version file (59).

## Acceptance

- [ ] **Inventory.** A list, read from the records, of every Mac verdict to reproduce: each proof record
  labeled host `mac` from A2 to A5 and the side tracks, spike and scripted-adapter records excluded. It
  includes the A3 RQ3 both-ways BFS run, the bucketed-relaxation fixture (40), the concurrency controls
  and Peter's repaired unit (49), the SAW whole-function equivalence verdicts (61), the strict-layer
  replays (51), the three A5 arms (53) and the upstream-GAPBS demo (54).
- [ ] **Re-run through `swdb prove`** in lane jobs (57), the configurations under comparison
  interleaved. Each new record is labeled host `mbit10`.
- [ ] **Same verdicts.** Proven stays proven, refuted stays refuted, and each refutation's counterexample
  replays with the same label. A "not proven" keeps its failure class.
- [ ] **Every difference root-caused before the freeze.** Each one has a named cause in a dated note,
  and is either fixed and re-run or taken to Yan-Ru. No difference is left unexplained when 59 starts.
- [ ] **Budgets recalibrated on mbit10.** The calibration on the public suites (Code2Inv, X509-parser,
  Frama-C-problems) plus BFS re-runs there. It yields values for hint rounds, loop wall time, WP time per
  solver, bounded-job time and CIVL's k (design S8: the budgets include k), each with its evidence,
  proposed for the method-version file. Proof rate is reported as a curve over the budget, with WP
  alone at equal wall time.
- [ ] **Stage bars re-checked on mbit10:** 2 lanes under 15 minutes with generated summaries; the BFS
  read-offload unit proven unbounded at threads = 1 with no human step; the RQ3 BFS numbers recomputed
  from mbit10 records only.
- [ ] **Mac and mbit10 kept apart.** Every record names its host. No table, summary or calibration value
  pools Mac and mbit10 numbers; Mac numbers appear only labeled "Mac".
- [ ] **Cut edges.** If 51, 53 or 54 is cut, its edge drops and its verdicts are simply absent from the
  inventory.
- [ ] **Host rules.** `df -h /data1 /data` before each large batch, its destination and size budget
  recorded (LR-06); a 30-minute heartbeat to Yan-Ru while batches run (LR-07); no pull into the checkout
  while a batch from it runs.
- [ ] **A6 exit, part 1** (design spec, "Proof-of-concept plan"; 27 item 5): every Mac verdict
  reproduces on mbit10, and the budgets are recalibrated. This ticket's answer cites the record IDs for
  both. If it fails: root-cause before the freeze. Part 2 (the method-version file reviewed and
  committed) is 59.

## Notes

- **Not in this ticket:**
  - 57 — Proof workers in a socket lane; 56 — Verifier lineup on mbit10: the machinery and installs.
  - 59 — Method-version review and freeze: writes the recalibrated budgets into the method-version file
    and freezes it.
  - 38 — Calibration on the public C suites: the Mac calibration this ticket repeats.
  - 61 — SAW whole-function equivalence (bounded direct route): the route whose verdicts join the
    inventory.
  - 55 — End-to-end fixture campaign with real verifiers: not a blocker here.
- Assumption (not decided in the map): a proven verdict from the proof-hint loop reproduces when WP
  proves the unit on mbit10 with the record's final hint set, with no provider call. The full loop,
  provider calls included, re-runs on mbit10 only inside the budget recalibration.
- Assumption (not decided in the map): Rocq results are machine-independent. Those present at this
  ticket's start are re-checked on mbit10 with the pinned Rocq; any that land later (43) are re-checked
  in 59.
- Assumption (not decided in the map): a timeout on one host and a verdict on the other counts as a
  difference to root-cause, not as a reproduction.
- Assumption (not decided in the map): records of 55 join the inventory only if they exist when this
  ticket starts; 55 does not block it.
- **Likely sources of difference:** host speed against fixed time budgets; the bitcode target (arm64 on
  the Mac, x86_64 on mbit10) for SAW on the C++; tool builds per platform. WP's machdep is x86_64 on both
  (13 item 7), so the C lowering's verdicts should not move.
- Paper numbers come only from mbit10.
