# Native speed rule: a bootstrap CI-width gate

Date: 2026-10-05 ET
Status: proposed (the v1 rule was decided by Yan-Ru on 2026-10-04; v2, the per-class gate and this
record are agent-decided under Yan-Ru's delegation, revisable, awaiting ratification)

Supersedes in part ADR 0010: its native gain condition "relative spread at most 0.1" holds only for
campaigns under the range rule. Records the two other departures from ADR 0010 that later tickets made.

A native Extensa campaign may name speed rule `swdb.speed_rule.ci_width.v1` or `.v2` in its campaign file
([ticket 66](../../.scratch/typed-library-dx100-bfs-2026-10-03/issues/66-native-protocol-after-isolation-test.md),
[ticket 72](../../.scratch/typed-library-dx100-bfs-2026-10-03/issues/72-native-upstream-two-level-trials.md)).
A file without it keeps `swdb.speed_rule.range.v1`: every per-source spread `(max - min) / median` at most 0.1.
Frozen protocols and recorded verdicts keep the rule they were made under; nothing is re-judged.

## The rule

- **Statistic.** The ratio is the spec's: the geometric mean over sources of the per-source median ratios
  (baseline over candidate) of one paired block of 20 repetitions.
- **Interval.** A 95% percentile bootstrap, 2000 resamples, seed 20260925. Each resample is a circular block
  bootstrap over the repetitions in collection order (blocks of 4); the same repetition indices apply to every
  source and both sides, so pairing and cross-source correlation are kept. Protocols freeze it as
  `sampling.analysis: paired_repetition_circular_block_bootstrap.v1` and `sampling.block_length: 4`.
- **Gate.** Statistic `relative_ci_width.v1`: `W = (upper - lower) / ratio`, at most 0.05 (frozen as
  `profitability.gate`, without `maximum_relative_spread`).
- **Verdict of a comparison.** `inconclusive` when `W > 0.05`; otherwise `gain` if and only if the lower bound
  of the same interval is strictly above 1.05; otherwise `no_gain`. `compare-evaluations` records
  `regression` when the upper bound is below 1, and the campaign counts it as `no_gain`.
- **A/A pilot.** Before iteration 1 each baseline role is timed against itself. A gating block passes only with
  `W <= 0.05` and its interval strictly inside `(1/1.05, 1.05)`. Under v1 every baseline role gates. Under v2
  only the campaign's selection baseline (`base_source`, the fork's scalar TDStep) gates; the other role
  (upstream DO-BFS) is timed, reported with its own verdict and a per-side level mix, and never gates or selects.
- **Upstream reported.** Selection uses the `base_source` comparison (Q61). The upstream comparison is
  reported beside it under the same rule.
- gem5 is unchanged: deterministic point ratios, gain when the ratio exceeds 1.05.

## Also recorded here

- **Per-class verdict** ([ticket 64](../../.scratch/typed-library-dx100-bfs-2026-10-03/issues/64-native-scale22-pilot-unstable.md)).
  The A/A gate applies per workload class. A failing class gets `baseline_unstable` and is not timed; the
  campaign stops with `baseline_unstable` only when every class fails. The threshold is never loosened
  inside a campaign. Applies under every speed rule.
- **Campaign summary in the team store** (decision D6 of the Extensa design). ADR 0010 keeps non-promoted
  records in the campaign's run folder. The one exception is the `campaign_summary` record, written once at
  stop and always copied to the team store with its `mode: extensa` and `campaign` tags.

## Why

The range gate failed the scale-22 A/A pilots a3, a4 and a5 (a5 with the other socket free): trial-to-trial
noise kept the per-source range above 0.1, while the 95% interval of the ratio the verdict uses had a width of
0.029–0.049 on every fork block of a5. The interval width measures the uncertainty of that number and narrows
with more repetitions; the range can only widen. Upstream DO-BFS trials sit on two levels about 15% apart,
which no legitimate control removes without counters or frequency control (tickets 64, 72); under v2 they are
reported, not gating, because selection never uses them.

## Scope and authority

Implemented in tickets 66, 71, 72 and 64 of the
[typed-library map](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md); the speed-rule code is
`swdb/campaign.py` and `swdb/bfs_protocol.py`. Ratification status is tracked in the spec's
"Awaiting ratification" section. This proposed record does not assert that Yan-Ru accepted it.

2026-10-06 00:25 ET: Yan-Ru ratified this rule (ci_width.v1/v2, the per-class A/A gate and `approval.gem5_other_socket`); it is no longer awaiting ratification.
