# 38 — Calibration on the public C suites

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 37
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Budget, Machines; "Proof-of-concept plan": A3; "Evaluation design": baselines, secondary results; "Records and levels": where things live; "Testing Decisions": not unit tests; user stories 34, 35, 85); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 8, 11, 13), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (item 7), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (item 2)
**Time estimate:** about 1 week

**What to build:** The proof-hint loop runs on the three public C suites (Code2Inv, X509-parser,
Frama-C-problems) on the Mac, with the real WP lineup and Codex. It delivers two things: the proof
rate as a curve over the budget, beside WP alone at equal wall time, and a report of escape-hatch
attempts by rule. Ticket 39 turns them, with the BFS results, into the calibrated Mac budget
proposal; ticket 59 freezes it. Output destination and size budget are recorded before the first
run. This is a calibration run, not a unit test: its records and the A3 exit judge it.

## Acceptance

- [ ] **Before the first run:** the output destination (a Mac runs folder outside the repo), its
      size budget and its readers are recorded (LR-06); `df` shows at least 50 GB free; each suite
      is pinned by version and hash, and the program list is fixed.
- [ ] **Every program runs through `swdb prove`** with the real loop: WP lineup from the method
      version, Codex at its pin, the starting budget (10 rounds, 60 minutes, 30 s per solver). Each
      job leaves one proof record with subject "calibration program", labeled host `mac`, that
      passes `swdb validate`.
- [ ] **WP alone at equal wall time** runs on the same programs: all solvers, the full wall-time
      budget, no hints (map 23 item 2). Each run leaves its own proof record.
- [ ] **Curve.** A report shows the proof rate over the budget, per suite and pooled: by rounds and
      by wall time for the loop, by wall time for WP alone (it has no rounds).
- [ ] **Escape hatches.** The report counts the proof hint check's rejections per rule, per suite.
- [ ] **Cost per program:** rounds, provider calls, tokens and wall time are in each record and
      summed in the report.
- [ ] **Handed to 39.** The curve and the escape-hatch report name the proof record IDs behind each
      point, for 39 to read. This ticket proposes no budget values.
- [ ] **Mac rules held:** one real verifier job at a time under the ~8 GB RSS watchdog; verifier
      scratch deleted after each job; at least 50 GB free at the end; LLVM 22 still works if Homebrew
      changed.
- [ ] **No held-out code.** No BC, PR or SSSP code, contract or definition is read or used.

## Notes

- **Not in this ticket:** 37 — The proof-hint loop (the loop itself); 39 — BFS unit proven
  unbounded at one thread; A3 exit (BFS calibration, the calibrated Mac budget proposal and the A3
  exit check); 40 — Bucketed-relaxation fixture; 58 — Mac verdicts reproduced on mbit10
  (recalibration on mbit10); 59 — Method-version review and freeze (freezes the values);
  evaluation 07 — RQ1 and RQ2 runs (the RQ2 numbers).
- Mac numbers are labeled and never paper numbers; those come only from mbit10 (map 13 item 13).
- **Long job:** expected to run well past 30 minutes. Schedule the 30-minute status heartbeat
  before starting (LR-07).
- Assumption (not decided in the map): each suite program enters `swdb prove` as a proof unit whose
  goal is the suite's own (its ACSL contract, or Code2Inv's final assertion), with the suite's proof
  hints (loop invariants, intermediate assertions) removed and the goal kept. Its record names no
  candidate artifact and counts toward no level.
- Subject: calibration runs use the "calibration program" subject, an assumption in 04 — Proof
  record tracer (map 26 item 1's five subjects have none for a suite program).
- Assumption (not decided in the map): seeds have no source here (no contract, no earlier proven
  candidate artifact), so calibration measures hint rounds alone.
- Assumption (not decided in the map): one run per program and configuration. The 3-run protocol
  (map 23 item 5) belongs to the evaluation.
- **Risk:** at up to 60 minutes per program, one verifier job at a time, plus WP alone at equal
  wall time, the full suites may not fit a week. Time a short pilot first. If the estimate exceeds
  the ticket's time, stop and ask Yan-Ru for a subset; do not pick one silently.

## Later changes
- 2026-10-14 17:02 EDT (main session): ticket 26's acceptance box "calibration suites" moves here: 26 could not run Code2Inv, X509-parser and Frama-C-problems because they are not on the Mac; this ticket installs them and runs 26's logic library against them too.
