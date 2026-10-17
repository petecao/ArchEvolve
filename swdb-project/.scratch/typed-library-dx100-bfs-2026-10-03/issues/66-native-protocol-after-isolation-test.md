# 66 — Native protocol after the isolation test: options for Yan-Ru

Created: 2026-10-04 21:45 ET (by ticket 56, campaign `extensa-native-bfs-20261004-a5`)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: type task, Blocked by line); 2026-10-04 20:55 ET (resolved as decided by Yan-Ru; gate pre-registered before any run). The
earlier "21:45 ET" stamps on this ticket and ticket 56 were ahead of the clock; mbit10 and the Mac read
20:47 ET when this update began.
**Type:** task
**Status:** resolved
**Blocked by:** None — can start immediately
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

## Answer

Resolved 2026-10-04 20:55 ET. **Decision by Yan-Ru Jhou, 2026-10-04: "go with the recommendation"**, that is
option 1(b), a bootstrap CI-width gate, with option 3 at 20 repetitions. The exact statistic and parameters
below were fixed by the agent under that decision (agent-decided; revisable). They are pre-registered here
and committed before any run under them.

### Pre-registration (written before any run under the new rule)

**Versions. Nothing frozen changes.**

- A campaign file opts in with `protocol.speed_rule: swdb.speed_rule.ci_width.v1`. Without it a campaign
  keeps `swdb.speed_rule.range.v1` (every `(max - min) / median` at most 0.1).
- Protocols frozen under the new rule carry `sampling.analysis:
  paired_repetition_circular_block_bootstrap.v1`, `sampling.block_length: 4` and `profitability.gate:
  {statistic: relative_ci_width.v1, maximum: 0.05}`, with no `maximum_relative_spread`. The per-source
  spreads are still computed and recorded, as description only.
- Every protocol and record frozen before keeps its rule and its verdict. **a5 is never re-judged** under
  this gate: its `baseline_unstable` (Kronecker) and `inconclusive` (uniform) verdicts stand.
- Candidates are timed with native evaluator `swdb.native.evaluator.scalable.v3` (ticket
  [71](71-native-evaluator-v3-parent-width.md)), which closes the review's open P3 (parent narrowing).

**Statistic (one number per paired block).** For each of the three registered sources s, let `Mb(s)` and
`Mc(s)` be the medians of the 20 baseline and 20 candidate ROI times. The ratio is
`R = geomean_s(Mb(s) / Mc(s))`, the spec's statistic, unchanged.

**Confidence interval.**

- 95% percentile bootstrap, B = 2000 resamples, `random.Random(20260925)`.
- Resampling unit: the **repetition**. In `native_paired.v1` one repetition is the six trials (both sides
  times three sources) collected back to back in a seeded interleaved order; repetitions are collected in
  index order.
- Each resample is a **circular block bootstrap** (Politis and Romano, 1992) over the 20 repetitions in
  collection order. It draws 5 start indices uniformly from 0..19, and each start contributes 4 consecutive
  repetitions (indices mod 20). The same 20 resampled repetition indices apply to every source and to both
  sides.
- `lower` is the 50th smallest of the 2000 draws and `upper` the 1950th (the index convention of the existing
  analysis).
- **Relative CI width** `W = (upper - lower) / R`.

**Why this resampling.**

- **Pairing.** Resampling whole repetitions keeps each baseline trial with the candidate trial taken
  seconds before or after it. A slow host state common to both sides then cancels in the ratio. a5 shows
  this: its upstream A/A blocks had width 0.001-0.002 while upstream's regimes persisted.
- **Cross-source correlation.** Using the same indices for all sources keeps the correlation that shared
  host state induces between sources at the same time.
- **Regime switching.** Regimes last minutes (ticket 64), and one repetition takes about 1.4 min (six trials
  of about 14 s each, including the graph map and the verifier). When a regime touches one side only, as in
  candidate blocks against upstream DO-BFS, consecutive repetitions are dependent, and resampling single
  repetitions would understate the variance. A block of 4 consecutive repetitions (about 6 min) keeps that
  dependence inside each resampled block. Circular wrapping gives every repetition equal weight.
- **Block length.** L = 4 is above the n^(1/3) = 2.7 rule of thumb on purpose. It is set by the observed
  regime time scale and still leaves 5 blocks per resample.
- **Known limit.** A regime longer than a whole block (about 28 min) cannot be seen by any resampling inside
  that block. The A/A pilot is the empirical check of the apparatus.
- **Interval shape.** A percentile interval respects the log scale of a ratio. The point estimate and the
  1.05 floor are the spec's.

**Repetitions.** 20 per source (option 3). Relative to 10, this narrows the interval by about the square
root of 2 and offsets the wider block-bootstrap interval. Everything else in D3 is unchanged: requested
sources [0, 1234, 7777] with ticket 64's recorded replacement, 1 thread, ROI `bfs.complete_call.v1`, `-O3`,
`native_paired.v1` with order seed 20260926, and the socket lane.

**A/A pilot gate (per class, before iteration 1).**

- Each baseline role is timed against itself with the full protocol.
- A role passes if and only if `W <= 0.05` **and** its CI lies strictly inside `(1/1.05, 1.05)`. The second
  condition says identical builds can show neither a gain nor a 5% loss under the same CI.
- A class passes only if both roles pass (fork scalar TDStep and upstream DO-BFS, as today). A failing class
  gets `baseline_unstable` and is not timed. The campaign stops with `baseline_unstable` only if every class
  fails.
- The gate is never loosened inside a campaign.

**Speed rule for candidate blocks, from the same CI.**

- `inconclusive` if `W > 0.05`;
- otherwise `gain` if and only if `lower > 1.05` strictly;
- otherwise `no_gain`. `compare-evaluations` records `regression` when `upper < 1`.
- Selection uses the lower bound of the fork scalar TDStep comparison (Q61). The upstream DO-BFS comparison
  gets its own verdict under the same rule and is reported beside it. It never selects.

**Run a6 (pre-registered).**

- Campaign file `campaigns/extensa/extensa-native-bfs-20261004-a6.yaml`: the same as a5 except
  `repetitions: 20`, `speed_rule: swdb.speed_rule.ci_width.v1` and `evaluator:
  swdb.native.evaluator.scalable.v3`. It keeps `isolation: other_socket_free` and the D5 default budgets
  (at most 8 iterations, plateau 4, 24 lane-hours, 3 provider calls per iteration plus 1 setup call through
  the Codex session lock, 20 GB disk, 1 lane).
- Host: mbit10 node 1, entered through MemAcc's `socket_lane.sh` from an up-to-date checkout. It starts
  only while the node 0, node 1 and legacy leases are all released. The runs root follows the 20 GB rule
  and is recorded.
- One run: the pilot first, then the campaign for the classes that pass, in the same process.
- **The result is reported whatever it shows. No rerun is chosen by outcome.** One exception: an
  `infrastructure_failure` before the first pilot block completes may be fixed and restarted once, because
  no timing has been seen.
- A class with a `gain`: if its best candidate used a contract, it is re-certified on the Mac with the
  current certifier. A best without a contract is reported as `uncertified`.
