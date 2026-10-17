# 11 — Claude sensitivity check

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07, 09
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Providers and machines"; "Evaluation design": cut order); decisions: [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (item 7)
**Time estimate:** about 2 days
**Cut order:** 1

**What to build:** Claude (`claude-sonnet-5-5`, effort `high`) takes the proof-hinting and repair
roles on BFS and SSSP, one run each, with everything else held as in Codex's runs. The result is
reported as a sensitivity check beside Codex's numbers. It never enters a pass bar, and the report
states both provider pins. It is not a model comparison.

## Acceptance

- [ ] The run plan names both pins: Claude `claude-sonnet-5-5`, effort `high`; Codex `gpt-5.6-sol`,
      effort `xhigh`, as used in 07 and 09.
- [ ] Proof hinting: Claude in the `proof_hinting` role, one run on the BFS and SSSP subjects, with
      the same frozen budget, seeds, checks and mbit10 lanes as 07's Codex runs.
- [ ] Repair: Claude in the rewriting role for counterexample-guided repair, one run on BFS and SSSP
      refuted candidate artifacts, with the same counterexamples, 5 rounds and checks as 09's Codex
      runs.
- [ ] Every record carries provider kind and pin, and `swdb validate` accepts it. Provider
      workspaces follow the same guard: the authors' code appears only in a `proof_hinting` workspace
      where it is the candidate artifact.
- [ ] The proof setup check and the proof hint check apply unchanged. Rejected hint sets are recorded
      by rule.
- [ ] The report shows Claude beside Codex on the same subjects, labeled "sensitivity check, not a
      model comparison", states both pins, and uses Claude's numbers in no pass bar.

## Notes

- **Not in this ticket:** 07 — RQ1 and RQ2 runs and 09 — RQ4: refutation and repair (the Codex runs
  this mirrors); 12 — Statistics and results report.
- Codex is the one default provider; Claude appears only here (effort spec).
- Assumption (not decided in the map): the BFS subjects are the BFS candidate artifacts that have
  mbit10 Codex results, from 07 if the BFS extras ran there, else from
  [proof-of-concept 58 — Mac verdicts reproduced on mbit10](../../probata-proof-of-concept-2026-10-13/issues/58-reproduce-on-mbit10.md).
  The SSSP subjects are SSSP's population (07) and its refuted candidate artifacts (09).
- **Cut order:** first in the evaluation. Cutting it changes no pass bar.
