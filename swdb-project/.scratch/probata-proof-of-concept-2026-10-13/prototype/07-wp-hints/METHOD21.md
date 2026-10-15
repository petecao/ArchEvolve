# Method21: diagnostic baseline allocation

Created: 2026-10-15 ET. **Completed run24: unproven; no scientific success or ticket acceptance.**
Run23 remains frozen at `df19ff8a6342d24ca853624f1e97a6c6833cabcb`; its unproven
result and raw artifacts are not changed or reused. Implementation uses a separate
worktree. This plan changes scheduling only; it supplies no functional hint.

[Map13 item11](../../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md)
defines30seconds as a starting run-plan parameter and requires changed values to
form a new plan. [Ticket07 Notes](../../issues/07-spike-wp-agent-hints.md) expressly
adopt that30second default. The explicit `--diagnostic-baseline10` departure is
therefore named and recorded as `diagnostic-baseline10-v1`, on top of method20's
strict `--design-probes --staged-induction` foundation. Legacy defaults remain30s.

The fresh no-hint baseline uses `baseline-smoke10`:10seconds per solver, every
function and every smoke check, the unchanged Alt-Ergo/Z3/CVC5 portfolio,
`-wp-cache none`, fresh session, default warnings, x86_64 machdep, no-filter-init,
scrubbed environment and the same guarded resource scope. It does not select
functions/properties, suppress goals, accept partial inventory, waive smoke
failures or become a final verdict. All generated goals and timeout/unknown
statuses remain retained. Inventory cardinality is checked against the generated
scheduled report; a shorter solver timeout must not change the generated scope.

The baseline's observed passed set is freshly cleared and populated solely from
this new run's ordinary non-smoke observations. An obligation not proved in10s
may have proved at30s, so this can change regression markers as well as scheduling.
That is an explicit pass-set confound, not a matched proof-rate comparison.
Every original obligation remains mandatory at final acceptance regardless of
whether the baseline proved it. No old pass set, baseline, seed result, hint,
conversation, historical example, counterstate or control fragment is reused.

Everything else remains fixed: fresh clock before baseline,60counted minutes
including generation/proving/provider/cleanup,10round ceiling, five fresh
mechanical frame seeds,10second diagnostic hint rounds, sleep-inclusive clock,
55/35/10 search phases, eight-minute final reserve and zero provider grace.
Final positive replay is the unchanged fresh all-function `wp-smoke-s` at30s,
cache none, every ordinary/hint/property obligation and every smoke check passing.
The separately retained same-hints covering-wait negative also stays30s and must
leave the original hazard check not proven, never refuted. No production RTE or
initializedness guarantee is added by this throwaway C spike.

Run23 used14.97minutes for its baseline and2.53more for seeds, leaving about
34.5minutes of its52minute search window. A10second baseline might recover9–10
minutes, leaving about44minutes for provider search. This is an unmeasured
projection: portfolio scheduling, Qed, overhead and fresh pass-set differences
can change it. Final replay may also exceed its reserve; the60minute acceptance
clock stays strict. Any improvement needs a fresh prospective launch measurement.

Reporting preserves legacy fields and adds explicit retained-artifact counters:
recorded proposal requests; candidate WP attempts with a guarded report; complete
checked inventories; deadline-censored and other incomplete attempts. Baseline,
seed and final jobs are separate. Turns without usage are counted as unknown;
token sums are labeled lower bounds when any turn lacks usage. Exit0 alone is
not a completed check. Deterministic report controls include one complete run,
one deadline-censored run and one exit0 truncated report.

Before launch: RED/GREEN shell/driver/report controls, independent composed
review, a clean source/method/tool freeze, fresh resource preflight and coordinated
Mac actual slot. Controlled external executables in tests are not real proof or
provider evidence. No unchanged method20 retry is authorized by this document.


## Completed run24 — 2026-10-15 ET

Clean14c2a298 ran17:52:17–18:44:19EDT,52.03counted minutes. The baseline took
6.11minutes versus run23's14.97minutes: observed recovery8.86minutes, with the
stated scheduling/pass-set confounds. Best41records (five mechanical,36Codex)
left29/259round goals open (14unit/15hint); no final replay or negative control
was reached. The7.97minute final reserve was unused, not a60minute overrun.
[Run24 evidence](../../evidence/t07-counted-24-20261015.json) retains the frozen
source, reports and complete cleanup audit. Missing CLI completed-turn usage is
unknown; scoped partial counters cannot prove the interrupted tail complete.

The [independent provenance review](../../evidence/t07-seed-provenance-acceptance-review-20261015.md)
supersedes the earlier undecided seed-as-method interpretation for future ticket07
acceptance. Historical origins remain mechanical, never relabelled Codex. Any
future method22 must begin empty and trace Codex-authored frames like every other
hint. Run24 and its later uncounted diagnostic remain immutable and ineligible for
retrospective upgrade or future provider hint reuse.
