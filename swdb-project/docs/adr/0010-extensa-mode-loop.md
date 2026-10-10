# Extensa-mode loop

Date: 2026-10-03 ET
Updated: 2026-10-09 23:50 ET (D35 start gate note); 2026-10-05 ET (scope line, supersession note)
Status: proposed

Narrows ADR 0002 for non-promoted Extensa records, and relaxes ADR 0006’s no-performance-tuning rule only in Extensa mode.

An Extensa campaign bounds iterations, lane-hours, provider calls and disk. The evaluator supplies every performance number. Selection ranks certification first, performance second, separately per workload class. Native gain requires a lower bound strictly above 1.05 and relative spread at most 0.1 (the range rule; see the note below); deterministic gem5 results are point ratios. Non-promoted records stay in campaign run folders on mbit10; deliberate promotion re-evaluates under a team protocol. ArchEvolve mode retains one proposal attempt plus bounded build/correctness repair and no tuning after a valid regression.

## Supersession note (2026-10-05 ET)

Superseded in part by [ADR 0012](0012-native-speed-rule-ci-width.md):

- A native campaign under speed rule `swdb.speed_rule.ci_width.v1` or `.v2` (tickets 66, 72) replaces "relative
  spread at most 0.1" with a relative 95% CI width at most 0.05 from a circular block bootstrap, and gates its A/A
  pilot on that width plus an interval inside (1/1.05, 1.05). Campaigns without it keep the range rule.
- The A/A gate and the `baseline_unstable` verdict are per workload class (ticket 64).
- "Non-promoted records stay in campaign run folders" has one exception: the `campaign_summary` record is always
  copied to the team store (decision D6).

## Start gate note (2026-10-09 ET)

Yan-Ru's decision D35 ([spec](../../.scratch/lanl-db-analytic-eval-2026-10-06/spec.md), 2026-10-09 22:33 ET)
adds a precondition: no Extensa campaign starts until a *numeric pairing check* passes. That is one real numeric
paired estimate, recorded before its timing, that the strict audit admits.

- `swdb campaign` refuses a new campaign on a real target unless its file names the check's `paired_estimate`
  record in `paired_estimates.numeric_pairing_check`.
- **No check can pass yet.** The current paired-estimate schema keeps every application estimate unknown and
  ineligible, so every new real-target start is refused until that schema changes.
- The contract-fixture adapter and resumed campaigns are not affected.

## Scope and authority

Implementation follows the authorized tickets of the [typed-library map](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md): 01–37 at first, then 38–78 (updated 2026-10-05 ET; the map lists each ticket and its decision). This proposed record does not assert Yan-Ru accepted the ADR or sent the team note. Human review and communication receipts remain separate.
