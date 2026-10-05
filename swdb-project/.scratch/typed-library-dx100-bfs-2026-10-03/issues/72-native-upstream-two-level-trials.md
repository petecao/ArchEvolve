# 72 — Native upstream DO-BFS trials are two-level: options for Yan-Ru

Created: 2026-10-04 23:10 ET (by ticket 56, campaign `extensa-native-bfs-20261004-a6`)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: type task, Blocked by line); 2026-10-04 23:30 ET (resolved; implementation); 2026-10-04 23:19 ET (decided; rule pre-registered before any run, commit 3147b31)
**Type:** task
**Status:** resolved
**Blocked by:** None — can start immediately
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

## Decision and pre-registration (written before any run under the new rule)

**Decision 2026-10-04 23:15 ET**, agent-decided by the coordinating agent under Yan-Ru's delegation ("continue
working"; revisable): the recommendation, option 1 with option 3 as reporting.

**Version.** New speed rule `swdb.speed_rule.ci_width.v2`, chosen in the campaign file
(`protocol.speed_rule`). Rule v1 (ticket 66) and the range rule keep their meaning; **a6 is never re-judged**.

**What stays exactly as in v1 (ticket 66 pre-registration).** Every frozen protocol: 20 repetitions,
circular block bootstrap over repetitions in collection order (blocks of 4, 2000 resamples, seed 20260925),
95% percentile interval, per-comparison gate `relative_ci_width.v1` at most 0.05. Candidate verdicts per
comparison: `inconclusive` if the width exceeds 0.05, else `gain` only if the lower bound is strictly above
1.05, else `no_gain`. Selection uses the fork scalar TDStep comparison (Q61). Evaluator v3 (ticket 71).

**What changes in v2.**

1. **A/A pilot gates on the selection baseline only.** The pilot still times both roles per class. A class
   passes if and only if its `base_source` role (fork scalar TDStep) A/A block has relative CI width at most
   0.05 and its interval lies strictly inside (1/1.05, 1.05). The upstream DO-BFS A/A block is recorded with
   its interval and its pass/fail under the same test, as description only.
2. **Upstream comparisons stay beside each candidate** with their own verdict under the same per-comparison
   rule; under v2 they can be `inconclusive`. They never select.
3. **Level mix of upstream trials (reporting only).** For every upstream DO-BFS block (A/A pilot and each
   candidate comparison), each side's ROI times per source are sorted and split at the largest ratio between
   adjacent times. If that ratio is at least 1.08, the block side is `two_level`: the trials above the split are
   slow. Otherwise it is `one_level` with no slow trials. Reported per side and source: level count, number and
   share of slow trials, the medians of both levels and their ratio; plus each side's overall slow share. The
   classification never changes a verdict.

**Run a7 (pre-registered).**

- Campaign file `campaigns/extensa/extensa-native-bfs-20261004-a7.yaml`: the same as a6 except
  `speed_rule: swdb.speed_rule.ci_width.v2`. It keeps 20 repetitions, evaluator v3,
  `isolation: other_socket_free`, both workloads and the D5 default budgets (at most 8 iterations, plateau 4,
  24 lane-hours, 3 provider calls per iteration plus 1 setup call through the Codex session lock, 20 GB disk,
  1 lane).
- Host: mbit10 node 1 through MemAcc's `socket_lane.sh` from an up-to-date checkout, started only while the
  node 0, node 1 and legacy leases are all released; runs root by the 20 GB rule.
- One run: the pilot, then the campaign for passing classes, in one process.
- **The result is reported whatever it shows. No rerun is chosen by outcome.** One exception, as in a6: an
  `infrastructure_failure` before the first pilot block completes may be fixed and restarted once.
- A class with a `gain`: if its best candidate used a contract, it is re-certified on the Mac with the current
  certifier (`swdb certify` 1.2 or later). A best without a contract is reported as `uncertified`.

## Answer

Resolved 2026-10-04 23:30 ET by the agent, implementing the 23:15 ET decision (not pushed).

- `swdb/campaign.py`: `CI_WIDTH_RULE_V2` (`swdb.speed_rule.ci_width.v2`), `pilot_gating_roles` (v2: the
  `base_source` role only; v1 and the range rule: every role), `level_mix` / `level_mix_of` (split at the
  largest adjacent ratio, two levels when it is at least 1.08). The summary's `pilot` records `gating_roles`, a
  `gates` flag per role, and `level_mix_by_class_and_role`; each upstream comparison row carries `level_mix`.
  Frozen protocols under v2 are identical to v1's.
- `swdb/campaign_targets.py`: `NativeAdapter` adds the per-side level mix to every upstream DO-BFS block (pilot
  and candidate comparisons) under v2, read from the campaign store's evaluations; a read failure is recorded
  as `unavailable` and never stops the campaign.
- Campaign schema and `docs/reference/format-v0.4-extensa.md` admit v2.
- Tests: `tests/test_ci_width_gate.py` (level mix on two-level and one-level data; v2 files admitted like v1;
  fixture campaign where the upstream A/A fails but only the fork gates; v1 still gates on every role) and
  `tests/test_extensa_targets.py` (v2 through `NativeAdapter`: fork-only gating, level mix on both upstream
  blocks).
- Campaign file `campaigns/extensa/extensa-native-bfs-20261004-a7.yaml` follows the pre-registration.
