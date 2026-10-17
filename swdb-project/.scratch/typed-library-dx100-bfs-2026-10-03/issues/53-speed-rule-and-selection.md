# 53 — Speed rule, per-class verdicts, selection and knob tuning

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D7, D9)
**Type:** slice
**Status:** resolved
**Blocked by:** 52
**Spec:** `../spec.md`

**What to build:** Extensa campaigns judge and select candidate artifacts by the spec's speed rule.

## Acceptance

- [x] `swdb campaign` freezes one protocol per campaign from the campaign file. It uses ROI `bfs.complete_call.v1`, no region pairs, and a campaign-level differences text. Native uses 10 repetitions, sources `[0, 1234, 7777]` and 1 thread. gem5 uses 1 run and source 0.
- [x] On gem5, the fork's scalar TDStep is measured once per class and every candidate artifact's comparison cites that one evaluation. On native, each candidate artifact gets its own paired block against each baseline, with a per-candidate baseline block in its pair receipt.
- [x] A gain needs a lower bound strictly above 1.05 (a test at exactly 1.05 gives no gain) and every spread at most 0.1. gem5 verdicts are reported as point ratios, with no confidence wording.
- [x] The native A/A pilot (D3) runs before iteration 1. A fixture spread above 0.1 stops the campaign with `baseline_unstable` and spends no provider call.
- [x] Each class has its own verdict (`gain`, `no_gain`, `inconclusive`) and its own best, labeled "single graph per class". A class where nothing passes gets no best.
- [x] Selection ranks certified before uncertified, then by lower bound (point ratio on gem5), using the comparison against the campaign's `base_source` baseline (Q61, D9). The other native baseline's comparison is reported beside it. An edit that uses no contract derives as uncertified. A candidate artifact that fails certification is rejected. Faster uncertified artifacts are listed in `faster_uncertified`.
- [x] A knob value outside its contract's declared range rejects that class's artifact before certification, without a provider call.
- [x] A test shows that ArchEvolve mode still never tunes after a valid regression.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:49 ET by the agent under Yan-Ru's standing implementation approval.

The logic is in `swdb/campaign.py` (committed with ticket 52); this commit adds its tests.

- One protocol per campaign: `protocol_settings` takes ROI `bfs.complete_call.v1`, no region
  pairs, the campaign-level differences text, threads, repetitions and sources from the campaign
  file (native: 10 repetitions, sources `[0, 1234, 7777]`, 1 thread; gem5: 1 run, source 0) and the
  rule (minimum 1.05, spread at most 0.1). The adapter freezes it once, tagged, and every comparison
  cites it.
- gem5: the fork's scalar TDStep is measured once per class (cached baseline evaluation) and every
  candidate's comparison cites that evaluation; native: each candidate artifact gets its own paired
  block (its own baseline evaluation) against each baseline.
- `speed_verdict`: native gain needs lower > 1.05 strictly and every spread <= 0.1 (any spread above
  0.1 is inconclusive); gem5 verdicts are point ratios (lower = upper = ratio, spread 0, no interval
  wording).
- Native A/A pilot before iteration 1: a spread above 0.1 stops with `baseline_unstable` and no
  provider call.
- Per class: its own verdict and best, labeled "single graph per class"; nothing passing gives no best
  (`no_gain`, or `inconclusive` when every comparison was inconclusive).
- `select`: certified before uncertified, then the lower bound (point ratio on gem5) against
  `base_source`; the other native baseline is reported in `best_other_baseline`; an edit without a
  contract is uncertified; a failed certification (after its charged repairs) is rejected;
  faster uncertified artifacts are listed in `faster_uncertified`.
- A knob outside its contract's declared range (or choices) rejects that class's artifact before
  certification, with no provider call.

Tests: `tests/test_extensa_selection.py` (12 cases): frozen protocol, gem5 single baseline versus
native paired blocks, six speed-rule boundary cases (exactly 1.05 is no gain), pilot stop with zero
calls, certification-first selection with `faster_uncertified` and a rejected artifact, no best when
nothing passes, knob refusal without a call. ArchEvolve mode: `tests/test_bfs_rewrite.py::
test_successful_evaluation_cannot_trigger_performance_tuning` still passes (192-case regression
run in ticket 48 and the final full run).

Assumptions (agent-decided, revisable):

- A class verdict is `inconclusive` only when every evaluated artifact's selection comparison was
  inconclusive; otherwise a class with no passing artifact is `no_gain` (spec wording).
- With a native-mode fixture template, a gem5 fixture campaign keeps the template's repetitions in
  the frozen record; the campaign-level settings (1 run, source 0) are in the summary. The real gem5
  adapter (ticket 57) freezes a controlled-simulator protocol.
