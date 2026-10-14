# 27 — In what order does the proof of concept build its pieces, and what closes each stage?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 18, 19, 24
**Map:** `../map.md`

## Question

The Destination says running the proof of concept is the next effort. Its pieces are decided
across tickets but not ordered or costed as a whole. Decide:

- **Stages and order.** Candidates: (1) one thread: C lowering, WP and SAW on Peter's read offload
  and the authors' `TDStepMAA`; (2) the proof-hint loop; (3) concurrency: CIVL and GenMC, WP's
  per-thread proof, the Rocq time-box (15 item 8); (4) rewrite chains: the catalog templates (17
  item 2) and chained vs bundled (17 item 9); (5) the strict layer catching up to the proof
  semantics as a new certify version (12 item 4, 16 item 11).
- **Each stage's pass bar and stop rule.** Already set: 2 lanes under 15 minutes with summaries,
  else the claim drops to 1 lane (10 item 9); SAW reads clang 22 bitcode, else crux-llvm (11 item
  2); Rocq in about 2 weeks, else a written proof (15 item 8); SAW ghost state on clang 22 (16 item
  10); every negative control refuted.
- **Cost:** the total against the cost rule (about one month per piece), and what is cut first if
  time runs short.
- **Split:** which pieces are build tickets of the next effort and which belong to the evaluation
  (ticket 23).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog (the proof-of-concept items).
  Build items already listed: 12 item 10 (new intrinsic and contract versions), 15's inputs (new
  `bfs_read_offload` and Peter's code versions; GenMC from source; a JDK for CIVL), 16's inputs
  (schema fields, translators, check mode, `std::vector` model, logic library), 17's inputs
  (contract lineage on implementation records; campaign start from a derived implementation;
  per-rewrite certification links).
- 2026-10-13 17:53 ET: input from 21 (resolved): no known product-program technique proves loop
  flattening as is, and unbounded reordering (fission-, tiling-like) defeats the data-driven
  aligner (`../research/21-relational-alignment.md`, Q4 failure modes 1-2). 17 item 2's catalog
  templates for flattening, phase split and chunking may need loop summaries; test one early.
- 2026-10-13 19:48 ET: input from 18 (resolved): first build item is the authors'-code guard fix (`swdb/provider_roles.py:26`); the
  method-version freeze gates held-out runs; held-out contract work comes after it; cut RQ5, then PR.
- 2026-10-13 20:10 ET: input from 19 (resolved): build item: the minimum-bounds derivation script, run on
  the reference instance to confirm 19's hand derivation (lanes 2, chunk 2, frontier 2, vertices 3,
  edges 3). Lever order: per-call summaries, then shape splitting. 10 item 9's pass bar has no 1-lane
  fallback.
- 2026-10-13 20:41 ET: input from 24 (resolved): (1) WP on real-valued sums is untested at our sizes;
  an early stage proves the sum library's lemmas and one PR unit; (2) SSSP's per-candidate proof needs
  delta-stepping's outer-loop invariant, from contract-proof seeds (risk); (3) build item: the sum
  library (method level, before the freeze); (4) 21's catalog-template risk is gone (no templates
  built); (5) SSSP contract: "delta <= least weight" precondition for the live `assert(false)`
  (`sssp.cc:384-388`).
- 2026-10-13 20:43 ET: input from 25 (resolved): build items: the bounded gate and counterexample
  repair before evaluation (`swdb/campaign.py:938-1003`); the WP phase after the campaign stops; the
  best-proven winner in selection, in the workspace and in the plateau test (`swdb/campaign.py:404-425,
  856-858,893-909`); `provider_calls_proof` in budget validation; iterations from a derived
  implementation (17 item 8). Measure how often campaign candidates are refuted at N > 1 and how many
  repair calls that uses.
