# 12 — Statistics and results report

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07, 08, 09, 10, 11 (drop 10, 11 if cut)
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": reading a bar, protocol, secondary results, method checks; "Records and levels": frozen research-database commit; "Providers and machines": Mac vs mbit10; S2, S3); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md)
**Time estimate:** about 4 days

**What to build:** The effort's destination: one results report that answers RQ1-RQ5 against the pass
bars committed at the freeze. Each bar shows the pooled held-out point estimate with its 95% Wilson
interval, and per-kernel rates beside it. An interval that crosses a bar reads "met, not significant".
Paired configurations get exact McNemar and Wilcoxon signed-rank tests. Secondary tables and the
method checks follow as evidence. Tickets 10 and 11 are included when they ran. Every number cites a
frozen research-database commit, so Yan-Ru or a reader can recompute it.

## Acceptance

- [ ] Each rate bar of RQ1 and RQ4: the pooled held-out point estimate against the frozen pass bar,
      its 95% Wilson interval, and per-kernel rates beside. RQ2's proof-rate difference is pooled
      the same way, with the interval named in Notes. Non-rate bars (RQ3's times and per-contract
      costs, RQ2's median-call cut, RQ4's noise band) are shown as values against the bar. RQ5,
      when 10 ran, is BFS only: per class against its 5% and 25% bars, never pooled with held-out
      kernels. Each bar reads met, "met, not significant" (the interval crosses the bar), or
      missed; a miss is reported as a refuted hypothesis.
- [ ] Paired configurations are tested per candidate artifact: exact McNemar for proven or not, and
      Wilcoxon signed-rank for provider calls and time. The pairs: hint loop vs WP alone; seeds on vs
      off; repair vs each mirror; with vs without a contract.
- [ ] LLM configurations report the mean over 3 runs as primary and "proven in any run" as
      secondary.
- [ ] The testing-only certification baseline's false acceptances (09) appear beside T-LLM
      Compiler's 33.8% false acceptance, labeled as its published counterpart (cited, not re-run).
- [ ] Secondary tables: C++ subset coverage, translator agreement, formal-half gate rejections,
      ghost-capacity failures and escape-hatch attempts by rule; plus 08's and 09's secondary results
      (small-scope curve, route used, alignment count, summaries vs inlined, threads > 1 refutation
      rate and repair calls, reverted repairs, patch size, the ThreadSanitizer baseline if 09 ran
      it). The authors' row comes from 09, with its direct-route verdicts. 07's BFS extras get their
      own table, never pooled with held-out kernels.
- [ ] The method checks appear as evidence, each citing its proof records: the semantics negative
      controls (reported once, not per kernel; 06's reading), the eight concurrency controls,
      CIVL–GenMC agreement and strict-layer agreement.
- [ ] Every bounded result states that it covers only the builds it ran (its build constants as recorded:
      tile capacity, thread count, knobs), not the deployed build (user story 10).
- [ ] 10 and 11 are included when they ran; 11 is labeled a sensitivity check and enters no bar. A
      cut ticket is named as cut.
- [ ] Every number cites a frozen research-database commit. A test recomputes a sample of levels with
      `swdb candidate-level` at that commit and gets the same values.
- [ ] Only mbit10 numbers count; any Mac result shown is labeled. Proof time appears as a cost, never
      a speed claim. A method change after the freeze appears as a new method version, with both runs
      reported.

## Notes

- **Not in this ticket:** 07 — RQ1 and RQ2 runs, 08 — RQ3: what a contract buys, 09 — RQ4: refutation
  and repair, 10 — RQ5: end-to-end BFS campaigns, 11 — Claude sensitivity check (the runs and their
  tables).
- Assumption (not decided in the map): a bar whose point estimate misses it reads "missed", with the
  interval shown, even when the interval crosses the bar. The map defines only "met, not
  significant".
- Assumption (not decided in the map): for a 3-run mean rate, the Wilson interval uses the mean as the
  point estimate and n = the number of candidate artifacts. The report says so.
- Assumption (not decided in the map): with 3 runs, McNemar runs per run index and on "proven in any
  run"; all are reported.
- Assumption (not decided in the map): RQ2's proof-rate difference is a difference of paired rates,
  which a Wilson interval does not cover. It is shown with its McNemar result and a paired
  interval, and the report names the method. The map names only Wilson intervals.
- Assumption (not decided in the map): the report is a document in this effort's folder; where it is
  shared is Yan-Ru's call.
- **Cut order:** if PR was cut, its rows are absent and the pooled estimates cover BC and SSSP. If
  10 or 11 is cut, its Blocked by edge drops, and the report names it as cut.
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.
