# 68 — Native upstream DO-BFS trials are two-level: options for Yan-Ru

Created: 2026-10-04 23:10 ET (by ticket 56, campaign `extensa-native-bfs-20261004-a6`)
**Type:** decision
**Status:** needs-info
**Blocked by:** —
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D3; [56](56-native-campaign-target.md), [64](64-native-scale22-pilot-unstable.md), [66](66-native-protocol-after-isolation-test.md)

**What to decide:** how the native Extensa campaign handles the upstream DO-BFS baseline, whose single trials
take one of two levels about 15% apart. This ticket only proposes options. Nothing was changed and no rerun
was made.

## Evidence

Campaign a6 ran ticket 66's pre-registered CI-width gate (ticket 56 addendum, 2026-10-04 23:10 ET; compact
evidence [`evaluation/native-a6-ci-gate-2026-10-04.json`](../evaluation/native-a6-ci-gate-2026-10-04.json)):

| Class | Fork scalar TDStep A/A, CI width | Upstream DO-BFS A/A, CI width |
|---|---|---|
| Kronecker 22 | 0.040 (pass) | 0.125 (fail; upper bound 1.052) |
| Uniform 22 | 0.019 (pass) | 0.093 (fail) |

- In every upstream A/A block, each side's 20 ROI times per source sit on two levels about 15% apart
  (Kronecker 135/159 ms, uniform 124/143 ms), with 7-12 of 20 on the slow level. Levels switch every few
  repetitions, and the two sides of a pair land on different levels independently.
- A median of a near-even two-level mixture falls on either level, so a per-source A/A ratio of medians
  jumps by up to 15% (0.87-1.15 here). This is a property of the statistic on this data, not of the bootstrap.
- The fork baseline, the one that selects (Q61), passes in both classes.

## Options (agent proposal; Yan-Ru decides)

1. **Gate the pilot on the selection baseline only.** The upstream comparison stays reported beside each
   candidate with its own verdict (Q61), but its A/A no longer blocks a class. Smallest change; it answers
   ticket 66's open question "must upstream also pass the gate?" with no.
2. **A mean-based statistic for a new speed-rule version.** For example the geometric mean of per-source
   mean ROI ratios, which moves smoothly with the share of slow trials instead of jumping between levels.
   This changes the spec's "median ratio" statistic, so it needs a new pre-registration and A/A pilot.
3. **Report the level mix.** Classify each upstream trial by level and report the slow share per side
   beside the ratio, without gating on upstream. Pairs with option 1.

**Agent recommendation:** option 1 (with 3 as reporting), because the upstream comparison never selects and
the fork baseline passes the pre-registered gate in both classes. Any choice needs a fresh A/A pilot under a
newly pre-registered rule; a6 is never re-judged.
