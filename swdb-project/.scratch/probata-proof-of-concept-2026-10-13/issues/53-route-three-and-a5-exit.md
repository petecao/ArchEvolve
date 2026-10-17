# 53 — Chained vs direct vs bundled; A5 exit

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 45, 49, 52
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes", "What a proven verdict asserts", "Proven once vs per candidate", "Concurrency", "Records and levels", "Evaluation design" (RQ3, ablations), "Proof-of-concept plan" (A5 exit, cut order); S5, S11); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 4, 7, 9 and later changes; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) items 3, 7; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 2, 5, 7; [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) items 1, 2; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 13
**Time estimate:** about 1-2 weeks
**Cut order:** 3

**What to build:** Three ways to prove Peter's read offload correct, and a fair timing of each.
**Chained:** the offload-only rewrite from 52, proven per thread against its proven predecessor
(route 3), with that predecessor proven once by route 1. **Direct:** the same final candidate artifact,
proven by route 1 against BFS's unit postcondition. **Bundled:** Peter's repaired bundled read offload
(49), proven by route 1. The ticket passes when all three reach the same certification level with
per-candidate proof times recorded. That is map ticket 17 item 9a passing, and it is the A5 exit.

## Acceptance

- [ ] **Route 1 on each derived implementation, once.** The three derived implementations from 52 are
  each proven against BFS's unit postcondition at every thread count, through `swdb prove` (per-thread
  proof for symbolic N, shared-action kinds, the parallel composition theorem). One proof record per
  derived implementation. Its time is recorded as a one-time cost, apart from per-candidate times.
- [ ] **Route 3.** The offload-only rewrite is proven per thread against the last derived
  implementation: a lockstep product of one thread of each shows that, given the same shared-memory
  answers, both perform the same shared actions with the same arguments in the same order. The result
  inherits its predecessor's verdict at every thread count.
- [ ] **Route 3 negative controls.** A seeded offload-only result that swaps two of its shared actions
  is not proven by route 3 (the lockstep relation fails; WP gives "not proven", never a refutation). A
  seeded result that changes a claim's argument is refuted by the bounded rung.
- [ ] **Offload-only contract proof** (design spec, "Proven once vs per candidate"). Each part has a
  counting proof record: the unit postcondition proven on the reference instance (52's final candidate
  artifact), with "the baseline meets it" and "two units that meet it satisfy the unit relation"; the
  order-independence lemma; the lifting lemma for BFS (machine-checked, or an assumption entry of kind
  "written proof" until it is); every formal-visible negative control refuted (a control that proves
  voids the contract proof); minimum bounds from the minimum-bounds script. Its drafted formal halves
  pass gates 2 and 3 here (52 runs gates 1 and 4).
- [ ] **Every arm runs the full path.** Each final candidate artifact runs certified, then the bounded
  rungs at the minimum bounds (SAW at threads = 1; CIVL at threads <= k, GenMC agreeing), then WP.
- [ ] **Levels on read.** `swdb candidate-level` reads the chained level as the weakest of the
  predecessor's route-1 record (with what it depends on) and the route-3 record; the direct and bundled
  levels from their route-1 records. Chained and direct prove the same final candidate artifact, so its
  level on read is the higher of the two (design S11: when one proof unit has counting records by two
  routes, any valid proof counts; weakest-of applies across proof units and dependencies). Control: on
  a fixture where only one of the two routes reaches proven unbounded, the final candidate artifact
  reads proven unbounded.
- [ ] **A5 exit (17 item 9a passes):** chained, direct and bundled reach the same certification level,
  with per-candidate proof times recorded. Each proof record holds wall and CPU time, hint rounds and
  provider calls. A short table compares the three arms, labeled host `mac`. If they differ: report it;
  route 1 still covers every candidate artifact (27 item 5).
- [ ] **Reopen rule** (17 item 7). On a fixture chain, changing one rewrite's contract hash makes that
  rewrite's proof records and every later rewrite's stop counting on read; earlier rewrites' records
  still count. With no direct route-1 record for it, the final candidate artifact reads as certified
  until re-proven. Control: with a counting direct record, it keeps that record's level.
- [ ] **Mac rules.** One real verifier job at a time under the ~8 GB RSS watchdog; at least 50 GB disk
  free; output to the Mac runs folder with its destination and size budget recorded first (LR-06); a
  30-minute heartbeat for any run past 30 minutes (LR-07).

## Notes

- **Not in this ticket:**
  - 52 — Split the bundled read offload: the contracts, the chain, its certification and records.
  - 49 — Peter's race repaired; A4 exit: the bundled arm's repaired code and its per-thread proof
    (reused here when its content-hash set still matches).
  - 45 — Per-thread lowering; 33 — Minimum-bounds script and A2 exit: the machinery this ticket runs.
  - 62 — Route choice and predecessor proofs in the campaign: choosing route 3 or route 1 per final
    candidate artifact automatically, and proving predecessors inside a campaign. Here each arm's
    route is fixed by the arm.
  - 10 — Level rule: the level computation itself, S11 included. This ticket only checks it on its
    arms.
  - 54 — Upstream-GAPBS demo: runs only after this ticket passes.
  - 58 — Mac verdicts reproduced on mbit10: these verdicts and times on mbit10.
  - evaluation 08 — RQ3: what a contract buys: the paper's route-3-vs-route-1 numbers.
- Assumption (not decided in the map): the chained arm's per-candidate time is the route-3 proof alone.
  The derived implementations' route-1 proofs are a one-time cost, like a contract proof, because
  every later candidate artifact built on the same predecessor reuses them. This matches RQ3's "route 3 vs
  route 1 time".
- Assumption (not decided in the map): the bundled arm is Peter's repaired code from 49, not the code
  as written, which races at N > 1 and would be refuted (15 item 11; S5).
- Assumption (not decided in the map): the offload-only contract reuses BFS's unit relation, so its
  lifting lemma has the same statement as `bfs_read_offload`'s. It still needs its own proof record,
  because its content-hash set differs.
- Assumption (not decided in the map): for the A5 exit's comparison, each arm's level is read from
  that arm's records alone, so S11's "higher of the two" on the shared final candidate artifact does not
  hide a gap between chained and direct.
- Mac times are calibration evidence only; paper numbers come from mbit10 (58). If A5 is cut (cut order
  3), RQ3 loses its chained arm and the "chained <= bundled" bar goes with it (27 item 7).
