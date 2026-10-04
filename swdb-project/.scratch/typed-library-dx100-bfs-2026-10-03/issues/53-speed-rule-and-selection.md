# 53 — Speed rule, per-class verdicts, selection and knob tuning

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D7, D9)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 52
**Spec:** `../spec.md`

**What to build:** Extensa campaigns judge and select candidate artifacts by the spec's speed rule.

## Acceptance

- [ ] `swdb campaign` freezes one protocol per campaign from the campaign file. It uses ROI `bfs.complete_call.v1`, no region pairs, and a campaign-level differences text. Native uses 10 repetitions, sources `[0, 1234, 7777]` and 1 thread. gem5 uses 1 run and source 0.
- [ ] On gem5, the fork's scalar TDStep is measured once per class and every candidate artifact's comparison cites that one evaluation. On native, each candidate artifact gets its own paired block against each baseline, with a per-candidate baseline block in its pair receipt.
- [ ] A gain needs a lower bound strictly above 1.05 (a test at exactly 1.05 gives no gain) and every spread at most 0.1. gem5 verdicts are reported as point ratios, with no confidence wording.
- [ ] The native A/A pilot (D3) runs before iteration 1. A fixture spread above 0.1 stops the campaign with `baseline_unstable` and spends no provider call.
- [ ] Each class has its own verdict (`gain`, `no_gain`, `inconclusive`) and its own best, labeled "single graph per class". A class where nothing passes gets no best.
- [ ] Selection ranks certified before uncertified, then by lower bound (point ratio on gem5), using the comparison against the campaign's `base_source` baseline (Q61, D9). The other native baseline's comparison is reported beside it. An edit that uses no contract derives as uncertified. A candidate artifact that fails certification is rejected. Faster uncertified artifacts are listed in `faster_uncertified`.
- [ ] A knob value outside its contract's declared range rejects that class's artifact before certification, without a provider call.
- [ ] A test shows that ArchEvolve mode still never tunes after a valid regression.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
