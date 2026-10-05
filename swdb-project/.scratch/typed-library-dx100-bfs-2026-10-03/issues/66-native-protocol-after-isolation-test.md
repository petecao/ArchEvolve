# 66 — Native protocol after the isolation test: options for Yan-Ru

Created: 2026-10-04 21:45 ET (by ticket 56, campaign `extensa-native-bfs-20261004-a5`)
**Type:** decision
**Status:** needs-info
**Blocked by:** —
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D3, D4; [56](56-native-campaign-target.md), [64](64-native-scale22-pilot-unstable.md)

**What to decide:** how the native Extensa BFS campaign gates timing noise. D3's range gate (every
`(max - min) / median` at most 0.1, 10 repetitions) was not met in three pilots, including a5 with the
other socket kept free. This ticket only proposes options. No threshold or protocol has changed, and no
rerun was made.

## Evidence

Compact evidence: [`evaluation/native-a5-isolation-2026-10-04.json`](../evaluation/native-a5-isolation-2026-10-04.json).
In the tables below, "range" means `(max - min) / median` per source, the frozen statistic.

**Pilots.** Maximum range for each pilot:

| Pilot | Isolation | Fork scalar TDStep, Kronecker / uniform | Upstream DO-BFS, Kronecker / uniform |
|---|---|---|---|
| a3 | partly beside gem5 | 0.161 / 0.057 | 0.012 / 0.134 |
| a4 | gem5 a7 on node 0 | 0.225 / 0.147 | 0.153 / 0.014 |
| a5 | node 0 free | **0.131** / 0.084 | 0.008 / 0.012 |

**a5 blocks.** All of these ran with node 0 free. The last three columns were computed afterwards from the
recorded trial times. They describe the data and are not verdicts.

| Block | Frozen range, max (baseline / candidate) | Ratio and 95% CI | CI width / ratio | Paired-ratio IQR / median, max | Baseline-side IQR / median, max |
|---|---|---|---|---|---|
| Kronecker pilot, fork | 0.131 / 0.098 | 0.991 [0.980, 1.009] | 0.029 | 0.085 | 0.073 |
| uniform pilot, fork | 0.064 / 0.084 | 0.999 [0.985, 1.016] | 0.030 | 0.075 | 0.043 |
| uniform it1, fork | 0.108 / 0.117 | 1.284 [1.270, 1.307] | 0.029 | 0.065 | 0.056 |
| uniform it3, fork | 0.133 / 0.159 | 1.318 [1.291, 1.355] | 0.049 | 0.126 | 0.085 |
| uniform it1, upstream | 0.136 / 0.149 | 0.127 [0.121, 0.130] | 0.070 | 0.145 | 0.134 |
| uniform it3, upstream | 0.136 / 0.111 | 0.133 [0.127, 0.134] | 0.055 | 0.132 | 0.128 |

What the data show:

- **Isolation helps but is not enough.** Keeping the other socket free lowers the spread, but the range
  stays above 0.1.
- **Upstream regimes persist.** Upstream DO-BFS still switches between its two regimes, about 15% apart
  and lasting minutes (ticket 64), with no gem5 job on the host.
- **Trials are already interleaved.** `native_paired.v1` alternates candidate and baseline trials for
  each source in a seeded random order, so the collection is already ABAB at trial level.
- **Paired ratios are not tighter.** Per-repetition paired ratios spread as much as either side, with
  ranges of 0.05–0.25 on the fork and candidate blocks. The noise is trial to trial, not only a slow drift that pairing would cancel.
- **IQR does not remove a regime switch.** When a block splits between the two regimes, the IQR is as wide
  as the range: up to 0.134 on the upstream blocks.
- **The bootstrap CI is narrow.** The CI the evaluator already reports (paired repetition-block bootstrap,
  2,000 resamples) has width / ratio 0.029–0.049 on every fork block and 0.055–0.070 on upstream.
- **Effects are large.** The effects of interest are 25–30%.

## Options (agent proposal; Yan-Ru decides)

Every option is a new frozen protocol version. Each must be pre-registered before its first run, with
one A/A pilot per class and no reruns chosen by outcome.

1. **Robust spread statistic, same blocks.**
   - (a) `IQR / median` per side and source, with a gate such as 0.05. This is cheap, but on this data it
     does not help with a regime switch inside a block: the uniform upstream blocks reach 0.134.
   - (b) **Bootstrap CI width.** Gate on the width of the existing 95% paired-bootstrap CI divided by the
     ratio, for example at most 0.05. The CI is reported today, so no evaluator code is needed. It
     reflects both sides, the pairing and the repetition count, and it narrows as repetitions grow.
2. **Explicit interleaved blocks with a ratio-spread gate.** Gate on the spread of per-repetition paired
   ratios instead of each side's times. Collection is already interleaved per trial, so this changes only
   the statistic. On a5 the paired ratios are not tighter than either side (range up to 0.25), so the
   agent does not expect this to help. Coarser ABAB sub-blocks (for example 5 trials per side, alternating)
   would need a new collection method in the evaluator.
3. **Longer blocks.** For example 20 or 30 repetitions instead of 10.
   - With the range statistic, more trials can only widen the range, so this helps only together with 1.
   - With 1(b), the CI narrows by about √2 to √3.
   - Lane time grows to about 0.5–0.75 h per fork block, so the plateau budget and the 24 lane-hour cap
     may end a campaign earlier.

**Agent recommendation:** 1(b), optionally with 3 at 20 repetitions.

- In the a5 data, a 0.05 CI-width gate would pass every fork block (maximum 0.049, a thin margin) and fail both uniform
  upstream candidate blocks (0.055 and 0.070).
- It needs no evaluator change, and it keeps the existing pass rule (lower bound strictly above 1.05).
- These numbers come from a5 itself. The gate value must therefore be fixed before a fresh pilot and
  never applied to a5 after the fact.

## What Yan-Ru needs to answer

- Which option or combination to use, and the gate value.
- The repetition count.
- Whether the upstream DO-BFS comparison, which is reported beside the selection, must also pass the
  gate. Today only the fork comparison selects (Q61).
