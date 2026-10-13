# 25 — How does the Extensa-mode loop budget proofs and rank candidate artifacts by certification level?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 19
**Map:** `../map.md`

## Question

ADR 0010: a campaign bounds iterations, lane-hours, provider calls and disk; selection ranks
certification first, performance second, per workload class. Proofs add cost and new levels.
Decide:

- **When proofs run:** for every certified final candidate artifact, for the top few by
  performance, or after the campaign; and the proof budget per campaign (mbit10 lane-hours, proof
  jobs inside a socket lane; 13 item 13).
- **Repair budget:** counterexample-guided repair rounds per refuted candidate artifact (13), and
  whether a repaired candidate re-enters selection.
- **Ranking:** proven unbounded > proven within bounds (verdicts with different bounds compared per
  ticket 19) > certified; a candidate whose proof is still running; a refuted candidate leaves
  selection (13 item 10).
- **Rewrite chains in the loop:** an iteration may start from a certified derived implementation;
  only final candidate artifacts are ranked and use lane-hours (17 item 8).
- **ArchEvolve mode:** whether and when proofs run there (one proposal attempt, ADR 0010).
- Whether ADR 0010 needs an amendment.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Extensa-mode loop" fog. The glossary's
  "Certification level" already ranks proven unbounded, proven within bounds, certified,
  uncertified in Extensa-mode selection.
- 2026-10-13 17:32 ET: input from 22 (resolved): a counterexample-guided repair may just revert to
  the baseline implementation (Orvalho et al. saw models copy the reference); decide whether such a
  repair re-enters selection.
- 2026-10-13 19:48 ET: input from 18 (resolved): RQ5 is BFS-only end to end: new campaigns if D35 has lifted, else a labeled
  retrospective; pass bars 5% of best certified speedup and <= 25% of lane-hours for proofs.
