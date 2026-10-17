# 62 — Route choice and predecessor proofs in the campaign

Created: 2026-10-13 23:15 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16, 19, 53
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes"; "Extensa mode" (WP phase, budgets); "What a proven verdict asserts" (proof unit, level); "Records and levels" (pins: predecessor snapshot); "Evaluation design" (secondary results: route used per candidate); "Proof-of-concept plan" (cut order); "Testing Decisions", seams 1, 2 and 3; S1, S6, S11); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 4, 7, 8 and Later changes; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 3; [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) item 1
**Time estimate:** about 3 days
**Cut order:** 3

**What to build:** Rewrite chains inside a running campaign. Two pieces:

1. **Route choice in `swdb prove`.** Per final candidate artifact: route 3 when its predecessor is
   proven, else route 1 (24 item 3). The proof record's route field (defined by 04) names the
   route; this ticket makes the field required for candidate proof units.
2. **Predecessor proofs in the WP phase** (25 item 1). When a final candidate artifact reaches WP, the
   route-1 proof of the derived implementation it depends on runs first, once per content hash. Final
   candidate artifacts that share a predecessor share its proof record.

Intermediate rewrites are marked as such (this ticket builds the marking), recorded as derived
implementations (19), and never gated, evaluated or ranked (17 item 8). Tested with the scripted
adapter through `swdb prove` and `swdb campaign --fixture`. Cut together with A5 (52, 53): then
every final candidate artifact is proven by route 1.

## Acceptance

- [ ] **Route 3 when the predecessor is proven.** `swdb prove` on a fixture final candidate artifact
  that applies an offload-only contract to a derived implementation with a counting proven record
  picks route 3. The record names route 3, pins the predecessor snapshot and cites the predecessor's
  proof record ID.
- [ ] **Else route 1.** The same candidate artifact gets route 1 when the predecessor has (a) no proof
  record, (b) only a not-proven one, or (c) one that stopped counting after a pin changed. A final
  candidate artifact built on the baseline implementation, or applying a bundled contract, also gets
  route 1. Each record names its route.
- [ ] **Route on every record.** Every candidate proof-unit record `swdb prove` writes fills the route
  field defined by 04 (route 1, route 3, or bounded direct once 61 lands). This ticket makes the field
  required for candidate proof units: `swdb validate` refuses a candidate proof-unit record with no
  route, and a route-3 record that cites no predecessor proof record (negative controls).
- [ ] **Predecessor first, once.** Fixture campaign: an intermediate rewrite, then two `gain` final
  candidate artifacts built on its derived implementation. In the WP phase, fastest first, the
  predecessor's route-1 job runs before the fastest candidate artifact's job; the second reuses that
  record, so one predecessor job runs in all. Control: when the second builds on a predecessor with a
  different content hash, a second predecessor job runs.
- [ ] **Never earlier.** No predecessor job runs during the loop, overlaps a timing step or a gem5
  simulation, or runs for a derived implementation that no scheduled `gain` final candidate artifact
  depends on.
- [ ] **Unproven predecessor, route 1.** When the scripted predecessor job ends "not proven, hint
  budget spent", the final candidate artifact runs route 1.
- [ ] **Budgets.** Predecessor jobs count in the campaign's lane-hours and in its proof lane-hours
  line; their hint calls draw on `provider_calls_proof` (name decided in map 25). The rewritten
  summary's budget lines include them.
- [ ] **Intermediates never evaluated or ranked.** An intermediate is recorded as a derived
  implementation and stays in campaign state, but gets no bounded gate job, no evaluator call and no
  evaluation lane-hours, and is never a winner. Control: the same code proposed as final is gated,
  evaluated and ranked.
- [ ] **Levels on read.** After the phase, `swdb candidate-level` reads a route-3 final candidate
  artifact as the weakest of its route-3 record and the predecessor's record (with what that record
  depends on). With route-1 and route-3 records both counting, it reads the higher (S11). The
  rewritten summary's best-proven winner uses these levels.
- [ ] Fixture records carry `contract_fixture` evidence and pass `swdb validate` and `swdb build`.
  Tests use the scripted adapter; full-suite runs on the Mac use at most 2 test workers.

## Notes

- **Not in this ticket:**
  - 04 — Proof record tracer: owns the route field (its values and checks); this ticket fills and
    requires it.
  - 53 — Chained vs direct vs bundled; A5 exit: route 1 on derived implementations and route 3
    themselves. This ticket wires them into `swdb prove`'s choice and the campaign.
  - 52 — Split the bundled read offload: chain contracts, the lineage check and the pattern-class
    check.
  - 16 — Post-campaign WP phase and budgets: the phase this ticket extends.
  - 19 — Derived implementations: records, lineage, per-rewrite links, iteration start.
  - 61 — SAW whole-function equivalence (bounded direct route): the route for a proof unit with no unit
    postcondition.
  - 63 — Experimental enabling contracts and the shared-contracts rule: their derived implementations
    get their route-1 proofs here, like any other.
  - 18 — ArchEvolve mode level and handoff block: ArchEvolve mode's one final candidate artifact.
  - Evaluation 08 — RQ3: what a contract buys: reports the route used per candidate artifact.
- Assumption (not decided in the map): "its predecessor is proven" means a counting proof record at
  proven unbounded. Route 3's result inherits its predecessor's verdict, so a predecessor proven only
  within bounds would cap it there, while route 1 might reach proven unbounded. If Yan-Ru prefers "any
  proven level", route 3 runs more often; S11 still keeps the higher of two counting records.
- Assumption (not decided in the map): only the immediate predecessor needs a proof. Route 1 proves it
  against the kernel's unit postcondition directly, so earlier rewrites need none (24 item 3).
- Assumption (not decided in the map): route 3 applies only to an offload-only contract, whose
  lockstep relation comes with it (24 item 3), applied to a derived implementation. A final candidate
  artifact on the baseline implementation gets route 1.
- Assumption (not decided in the map): when route 3 ends not proven, route 1 runs next as its own job,
  because the design calls route 1 "the fallback". Both draw on the same campaign budgets. Ask Yan-Ru
  if the extra WP time is unwanted.
- Assumption (not decided in the map): the predecessor job is its own `swdb prove` job with the method
  version's per-candidate budget.
- Assumption (not decided in the map; this ticket builds the marking, and 19 and 14 point here): the
  rewrite response marks its result as intermediate or final, the way it names its contracts and its
  start; an unmarked result is final. Confirm with Yan-Ru before coding.
- Assumption (not decided in the map): the route requirement holds for records written after this
  ticket lands. Earlier candidate proof-unit records with no route still pass, because records never
  change (ADR 0016); 19's links read them as "none yet".
- Assumption (not decided in the map): an intermediate gets an iteration-ladder row (map 28: no gaps)
  with its level, and no ratio or winner mark.
- Assumption (not decided in the map): ArchEvolve mode schedules predecessor proofs the same way:
  before its final candidate artifact's unbounded rung, once per content hash.
- **Cut:** third in the cut order, with 52 and 53. If cut, every final candidate artifact is proven by
  route 1, 14's interim rule (gate every certified candidate artifact the campaign would evaluate)
  stays, the route field stays optional (04), and 59's edge to this ticket drops.
- Contract fixtures only; no held-out kernel (BC, PR, SSSP).
