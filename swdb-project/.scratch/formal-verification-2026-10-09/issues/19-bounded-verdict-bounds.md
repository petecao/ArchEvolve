# 19 — How are a bounded verdict's bounds chosen, and when are they enough?

Created: 2026-10-13 17:02 ET
Updated: 2026-10-13 20:10 ET (resolved with Yan-Ru in two grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 19:47 ET)
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

A proven-within-bounds verdict records a value per bound dimension (09 item 11). Nothing yet says
which values the bounded verifier tries, or when a verdict's bounds are large enough to mean
something. Decide:

- **How bounds are chosen per contract:** fixed per contract; grown one step at a time until the
  budget ends (the largest proven bounds recorded); or derived from the contract, for example the
  smallest bounds at which every negative control a formal check can see is refuted (10 item 2).
- **Minimum bounds:** whether a contract declares bounds below which a bounded verdict does not
  give "proven within bounds", and how they are justified (a small-scope argument: which hazards
  and races need two lanes, two chunks, two commands in flight, two threads).
- **Encoding levers** that reach larger bounds, and which one the proof of concept tries first:
  summaries in place of the inlined strict-layer port (10 item 9's 2-lane hypothesis), per-call
  proof-semantics summaries (12, 16 item 10), symbolic sizes.
- **CIVL's team-size bound k** (starts at 3, 15 item 9) and input bounds under the same rule.
- **Comparing verdicts with different bounds** (input to ticket 25's ranking).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Scaling past one lane" fog. Inputs: 08 (crux-llvm
  on the array port proves 1 lane; 2 lanes did not finish in 15 minutes on the Mac); 09 item 11
  (bound dimensions per contract, threads always one; BFS read offload lists threads, vertices,
  edges, tile lanes, knob values, frontier size, unroll depth); 10 item 9 (pass bar: 2 lanes under
  15 minutes with summaries, else the claim drops to 1 lane); 11 item 2 (SAW 1.6 is the bounded
  verifier, summaries as `llvm_verify` overrides; first test: does SAW read clang 22 bitcode).
  Mac rule: one verifier job at a time under an ~8 GB RSS watchdog; larger sweeps on mbit10.
- 2026-10-13 19:50 ET: claimed 19:47 ET. Facts re-checked in code:
  - **The contract's eight negative controls are runtime seam mutations**
    (`library/dx100/certification/seams.cc:45-119`); 10 item 2 asks for the formal-visible ones on
    the reference instance with the proof's own harness.
  - **Smallest scope per control, BFS read offload, one thread (hand derivation from Peter's
    code, `library/dx100/bfs_read_offload.inc:30-49`; to confirm by run):** `dropped_wait`,
    `read_before_wait`, `index_wrap`, `forged_frontier`: 1 lane, 1 edge. `dropped_continuation`:
    edges in one chunk > lanes. `chunk_off_by_one`: a chunk that fills the tile exactly.
    `skipped_cas_recheck`: two edges to one vertex **in one tile**, so lanes >= 2; at 1 lane the
    hint is re-gathered after the first claim (`:36,40`), the CAS never fails and the fault
    never fires. `shared_context`: threads >= 2. Together: lanes 2, chunk 2, frontier 2,
    vertices 3, edges 3 (frontier {0,1}, edges 0->2, 1->2, 1->x).
  - **Consequence:** 08's 1-lane verdict cannot see `skipped_cas_recheck`, so under 10 item 2 a
    1-lane setup voids the contract proof. 10 item 9's fallback ("else the claim drops to
    1 lane") conflicts with 10 item 2.
  - **`TILE_SIZE` is a build constant** (`apps/dx100/benchmarks/API/MAA.hpp:14-15`, default
    16384); lanes = 2 means a build with `TILE_SIZE` = 2. Knobs are compile-time constants too
    (`bfs_read_offload.inc:4-9`).
  Round 1 posted: Q1 minimum bounds from negative controls; Q2 build constants vs inputs; Q3 how
  bounds are chosen; Q4 encoding levers; Q5 CIVL and GenMC bounds; Q6 comparing verdicts;
  Q7 job budget; Q8 an empirical small-scope check.
- 2026-10-13 19:57 ET: round 1 answers (checkpoint; not yet the answer): Q1-Q8 accepted as recommended ("ok"
  each). Q1 minimum bounds per contract and per rung, derived automatically from the negative
  controls, approved at promotion; below them no level; replaces 10 item 9's 1-lane fallback.
  Q2 build constants (`TILE_SIZE`, `NUM_CORES`, knobs) recorded exactly; compared-only knobs
  symbolic within their legality clause; the deployed `TILE_SIZE` only through WP. Q3 Extensa
  mode runs at the minimum; larger bounds only in the evaluation or spare budget. Q4 levers:
  per-call summaries, then shape splitting, relabeling only as a reduction (not in the proof of
  concept); symbolic sizes are WP's job. Q5 CIVL minimum k = 2, runs at k = 3. Q6 one level, two
  sub-rungs (threads <= k above threads = 1); bounds above the minimum reported, never ranked.
  Q7 15 min per job, calibrated then frozen; a timeout never falls back to smaller bounds.
  Q8 the small-scope curve goes to 23. Round 2 posted: Q9 unroll depth; Q10 shape-split
  completeness; Q11 glossary terms; Q12 the change note on 10 item 9.
- 2026-10-13 20:07 ET: round 2 answers: Q9-Q12 accepted as recommended ("ok" each). Glossary: minimum bounds and
  build constant added. Shared-understanding confirmation posted.
- 2026-10-13 20:10 ET: Yan-Ru confirmed the shared understanding.

## Answer

2026-10-13 20:10 ET. Decided with Yan-Ru in a grilling session (rounds 1-2 in Comments). Facts: the
code re-checked in this session (the contract's negative controls in
`library/dx100/certification/seams.cc:45-119`, Peter's read offload in
`library/dx100/bfs_read_offload.inc`, `apps/dx100/benchmarks/API/MAA.hpp:14-15`).

**When bounds are enough:** never in the sense of a proof. A bounded verdict means something when its
bounds are at least the contract's **minimum bounds** (glossary): the setup then sees every negative
control a formal check can see. Whether that also catches real bugs is the small-scope hypothesis,
measured in the evaluation (item 9), never claimed.

1. **Minimum bounds, per contract** (Q1). The smallest bounds at which the bounded verifier refutes
   every negative control a formal check can see (10 item 2), set separately for single-thread runs
   (SAW and its fallbacks) and multi-thread runs (CIVL, GenMC), each from the controls labeled for it.
   - **Derived automatically:** a script grows the bounds one dimension at a time on the reference
     instance until every control is refuted, with the proof's own harness, summaries and scaffold.
     Yan-Ru approves the result at promotion. The minimum belongs to the contract proof's
     content-hash set (10 item 6): a changed control, harness or summary re-derives it.
   - **Below the minimum, no level:** the result is recorded as "bounded check below minimum" and the
     candidate stays certified.
   - **BFS read offload, one thread (hand derivation; the script must confirm it):** threads 1,
     lanes 2, chunk 2, frontier 2, vertices 3, edges 3 (frontier {0,1}, edges 0->2, 1->2, 1->x).
     `dropped_wait`, `read_before_wait`, `index_wrap` and `forged_frontier` need 1 lane and 1 edge;
     `dropped_continuation` needs more edges in one chunk than lanes; `chunk_off_by_one` needs a
     chunk that fills its tile; `skipped_cas_recheck` needs two edges to one vertex in one tile,
     because at 1 lane the hint is gathered again after the first claim (`bfs_read_offload.inc:36,40`)
     and the CAS never fails. `shared_context` needs threads >= 2.
   - **Replaces 10 item 9's fallback:** a 1-lane setup cannot see `skipped_cas_recheck`, so it voids
     the contract proof. If 2 lanes do not prove in the budget, candidates stay certified and the
     proof of concept tries the levers (item 4).
2. **Build constants** (glossary; Q2). Tile capacity (`TILE_SIZE`, default 16384), thread count
   (`NUM_CORES`) and knobs are fixed at compile time: "lanes = 2" is a build with `TILE_SIZE` = 2. A
   bounded verdict records every build constant exactly; inputs stay symbolic up to their size bounds.
   A knob that is only compared (the frontier threshold) becomes a symbolic constant limited by its
   legality clause. The deployed `TILE_SIZE` is covered only by WP, where it is a symbolic constant.
   The paper says a bounded verdict covers the builds it ran, not the deployed build.
3. **How bounds are chosen** (Q3). Extensa-mode campaigns run at the minimum bounds only. Larger bounds
   run only in the evaluation (a scaling curve) or for final candidate artifacts with spare budget.
   Rejected: growing until the budget ends (the largest bounds then measure the machine and the
   budget, not the candidate); fixed hand-picked bounds (no link to what the setup can see).
4. **Encoding levers, in order** (Q4, Q10).
   1. Per-call proof-semantics summaries (12, 16 item 10) in place of the inlined strict-layer port:
      10 item 9's 2-lane test.
   2. Shape splitting: one job per graph shape, values symbolic; jobs may run in parallel on mbit10
      under `ulimit -v`. The enumerator is a trusted-tool entry, and a count check compares the jobs
      with a closed-form count of shapes for the bounds; a missing or failed job leaves the whole
      verdict "not proven".
   3. Relabeling symmetry (08's shape mode) only as a reduction with its own proof obligation (09 item
      10); not in the proof of concept.

   Symbolic sizes are not a bounded lever: loops over a symbolic size need invariants, which is the
   unbounded verifier's job.
5. **Unroll depth is not a bound dimension** (Q9). With concrete sizes every loop ends, so the depth
   follows from the size bounds. A fallback that needs an unwind limit (CBMC `--unwind`, crux-llvm)
   gets one computed from the sizes, with unwinding assertions always on; off, a too-small limit
   passes silently.
6. **CIVL and GenMC under the same rule** (Q5). By our reading every concurrency control of 15 item 12
   needs only 2 threads, so the multi-thread minimum is k = 2; runs keep k = 3 (15 item 9). Their input
   bounds get their own minimum from the concurrency controls. The small-thread-count argument cites
   Lu et al., ASPLOS 2008 (citation not yet checked).
7. **Comparing verdicts with different bounds** (Q6; input to 25). Every proven-within-bounds verdict
   at or above the minimum is one level with two sub-rungs: threads <= k (CIVL) above threads = 1
   (SAW). Bounds above the minimum are reported, never ranked. Rejected: dominance per dimension
   (incomparable pairs; rewards compute).
8. **Budget per bounded job** (Q7). Starting value 15 minutes wall time; on the Mac one job at a time
   under the ~8 GB RSS watchdog; on mbit10 `ulimit -v` inside a socket lane. Calibrated, then frozen as
   part of the method version. A timeout at the minimum gives "not proven", failure class timeout
   (11 item 9); it never falls back to smaller bounds.
9. **Small-scope check in the evaluation** (Q8; to 23). How many seeded faults and LLM-proposed
   candidate artifacts (18) are refuted at the minimum, the minimum + 1 and the minimum + 2. The paper
   reports the curve, not a sufficiency claim.
10. **Generality.** Minimum bounds, build constants, the lever order, the sub-rungs and the budget rule
    apply per contract and kernel; each contract derives its own minimum from its own controls.

**Later changes made:** 09 item 11 (unroll depth leaves the dimension list), 10 item 9 (the 1-lane
fallback is withdrawn).

**Inputs passed on:**
- **Ticket 23:** the small-scope curve (item 9); the job budget calibrated then frozen (item 8).
- **Ticket 25:** one level with two sub-rungs, bounds above the minimum never ranked (item 7);
  Extensa mode proves at the minimum only (item 3); proof cost per candidate is one minimum-bound job
  per rung plus WP.
- **Ticket 27:** the minimum-derivation script on the reference instance as a build item, and its run
  confirming the hand derivation; lever order (item 4); 10 item 9's pass bar keeps 2 lanes with no
  1-lane fallback.
- **Ticket 26:** each verdict records build constants, minimum-bounds version, bounds used, shape-split
  count check and failure class.

Glossary: minimum bounds and build constant added.
