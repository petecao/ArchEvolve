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
