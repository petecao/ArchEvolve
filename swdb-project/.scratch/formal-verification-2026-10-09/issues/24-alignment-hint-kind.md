# 24 — Should the proof-hint loop gain an alignment hint kind for direct unbounded proofs?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 20:04 ET)
**Blocked by:** 21
**Map:** `../map.md`

## Question

A final candidate artifact whose rewrite chain fails to prove reaches at most proven within bounds,
because a direct relational proof needs an alignment that nothing supplies (17 item 4.4). Using
research 21, decide:

- whether 13's hint vocabulary gains an **alignment** kind (the proof-hint agent proposes which
  loops of the two programs run in lockstep; our product-program generator builds the product; WP
  proves it), or the gap stays and the paper states it as a limit;
- which checks make an LLM-proposed alignment safe (side conditions the generator or WP must prove;
  13's three checks);
- how it meets concurrency (a per-thread lockstep only, 17 item 4.3; for-all-exists pairs at
  N > 1), the "any input" note and the cost rule;
- the vocabulary version bump and what the evaluation measures (ticket 23).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Direct unbounded proofs without a template" fog.
- 2026-10-13 20:08 ET: claimed 20:04 ET. Facts re-checked in code and earlier tickets:
  - **Who hits the gap.** BFS never: route 1 (unit postcondition) proves any candidate against the
    baseline directly (17 item 4.1). The gap is the relational-route kernels, PR and BC (10 item
    2.3), when a chain link fails (17 item 4.4) or a candidate matches no contract as written,
    above all the authors' held-out DX100 code, which today gets only the direct bounded check
    (18 item 5).
  - **"No clean definition (PR, BC)" is asserted, never argued** (09 item 3, 10 items 2.3 and 2).
    Over real arithmetic (09 item 4) both units have a functional summary as a sum over a CSR
    range: PR `next_contrib[u] = (base + kDamp * sum_{j in [off[u], off[u+1])} curr_contrib[in[j]]) / outdeg(u)`
    (`apps/dx100/benchmarks/gapbs/src/pr.cc:96-106`); BC adds `path_counts[u]` into
    `path_counts[v]` for every frontier edge with `depths[v] == depth`
    (`apps/dx100/benchmarks/gapbs/src/bc.cc:101-113`). 16 item 2 already allows primitive-recursive
    logic definitions such as this sum.
  - **The authors' PR is exactly research 21's flattening blind spot:** one flat edge loop over
    `maa_range_loop` with `maa_indirect_rmw_vector(..., ADD_OP)` into `incoming_total[tilei]`
    (`pr.cc:233-245`) against the baseline's nested per-vertex loop. No lockstep alignment fits;
    a one-sided loop summary (an invariant over partial range sums) does (research 21 Q4 item 2).
  - **An alignment is not a proof hint by the glossary:** the scheduler cannot be ghost code
    (research 21 Q2), so it changes the product program, the code under proof; 13's
    erase-and-diff would reject it.
  Round 1 posted: Q1 reopen "no clean definition" (unit postconditions over reals for PR and BC);
  Q2 an alignment is never a proof hint.
- 2026-10-13 20:21 ET: round 1 answers (checkpoint; not yet the answer): Q1 (a) and Q2 accepted
  as recommended ("ok" each). Q1: PR and BC get unit postconditions over real arithmetic (sums
  over CSR ranges), so route 1 covers every evaluated kernel; amends 09 item 3 and 10 item 2.3;
  relational templates stay legal for a kernel with no summary. Q2: an alignment is never a proof
  hint; any future form is an "alignment proposal", an input to the product generator outside
  13's vocabulary. Facts for round 2:
  - **SSSP's proof unit is the whole `DeltaStep` call** (09 item 5: the function holding the
    rewrite site; `apps/dx100/benchmarks/gapbs/src/sssp.cc:319-429`). Its output is deterministic
    at any N (shortest distances) though rounds are not. Weights are `int32_t`
    (`benchmark.h:30`), so no reals.
  - **SSSP precondition found:** both versions `assert(false)` when a thread's local bin for the
    current index is non-empty and under 1000 entries (`sssp.cc:269-273,384-388`); the fork
    builds without `NDEBUG` (`Makefile:5`). With the default delta 1 (`command_line.h:224`) and
    positive weights no relaxation lands in the current bin, so it never fires. A contract needs
    it as a proof-unit precondition (delta <= least weight) or proves the assert unreachable.
  Round 2 posted: Q3 SSSP fit and who writes held-out unit postconditions; Q4 alignment proposals
  built or stated as a limit; Q5 chain proofs and catalog templates on route-1 kernels; Q6 where
  the sum library lives; Q7 the authors' code that matches no contract; Q8 vocabulary and
  evaluation inputs.
- 2026-10-13 20:31 ET: round 2 answers (checkpoint; not yet the answer): Q3, Q4, Q6, Q7, Q8
  accepted as recommended ("ok" each). Yan-Ru asked what an alignment is (explained; glossary
  entry proposed in round 3). Q5: Yan-Ru asked "are you sure? enabling rewrites make the
  baseline compatible with the intrinsics; that seems orthogonal". Re-check against 17:
  - **Right: enabling rewrites and chains are about matching, not proofs** (17 item 1). Q5 kept
    them, but its wording ("drop chain proofs") blurred that.
  - **Q5 was wrong to drop route 3.** 17 item 4.3 proves an offload-only rewrite per thread
    against its predecessor, a lockstep proof that skips the reshaping. That is the per-candidate
    saving 17 item 9a set out to measure; route 1 alone would re-prove the reshaped loops for
    every candidate. Route 3 only needs a proven predecessor.
  - **What route 1 does replace is route 2 (catalog templates).** A derived implementation can be
    proven against the kernel's unit postcondition by route 1, once per derived implementation,
    instead of by a kernel-independent catalog template.
  Revised Q5 posted with Q9 (glossary) in round 3.
- 2026-10-13 20:38 ET: round 3 answers (checkpoint; not yet the answer): revised Q5 and Q9
  accepted ("ok" each). Glossary updated: alignment added; unit postcondition sharpened (may allow
  several outcomes). Shared-understanding check posted.
- 2026-10-13 20:41 ET: Yan-Ru confirmed the shared understanding ("ok").

## Answer

2026-10-13 20:41 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments; shared
understanding confirmed). Facts: research 21, the code re-checked in this session (paths in the
20:08 and 20:21 ET comments). The question's premise changed in round 1: the gap is a missing unit
postcondition, not a missing alignment.

1. **No alignment hint kind** (Q2, Q4). An alignment (glossary) changes the product program, which
   is the code under proof, because the scheduler cannot be ghost code (research 21 Q2); so it is
   never a proof hint, and 13's erase-and-diff would reject it. A future form would be an
   **alignment proposal**: an input to the product generator, with generator-emitted goals for
   guard agreement, adequacy and fairness, its own check and a once-proven construction theorem.
   It is not built in this effort: no evaluated kernel needs it (item 2), it would not prove the
   flattening and reordering reshapes we see (research 21 Q4), and the generator plus a Rocq
   construction theorem would cost more than a month. The paper states the limit: a kernel whose
   unit has no unit postcondition reaches at most proven within bounds on a direct route. "An LLM
   proposes the alignment" is future work (no prior work found, research 21 Q1).

2. **Every evaluated kernel gets a unit postcondition** (Q1 a, Q3). Amends 09 item 3 and 10 item
   2.3 ("no clean definition (PR, BC)" was asserted, never argued):
   - **PR:** over real arithmetic (09 item 4), `next_contrib[u] = (base + kDamp * sum_{j in [off[u], off[u+1])} curr_contrib[in[j]]) / outdeg(u)`,
     with `scores` and `error` likewise (`apps/dx100/benchmarks/gapbs/src/pr.cc:96-106`).
   - **BC:** per frontier edge with `depths[v] == depth`, `path_counts[v]` gains `path_counts[u]`;
     depths, successor bits and the next frontier as sets (`bc.cc:101-113`).
   - **SSSP:** the proof unit is the whole `DeltaStep` call (09 item 5; `sssp.cc:319-429`); its
     unit postcondition is the shortest distances (integer weights, `benchmark.h:30`), defined by
     primitive recursion on path length (16 item 2). Deterministic at any N though rounds are not.
   - These were checked only to show route 1 covers every kernel. Held-out unit postconditions are
     still drafted blind after the freeze (18 item 5), under one added drafting rule: every
     contract states a unit postcondition; a relational template needs a recorded reason.
     Relational templates stay legal.

3. **Proof routes** (Q5, revised after "are you sure?"; numbering from 17 item 4):
   - **Route 1** (direct, against the kernel's unit postcondition) proves every final candidate
     artifact on every evaluated kernel and is always the fallback; correctness never depends on
     a rewrite chain. It also proves each **derived implementation** once.
   - **Route 2** (a catalog relational template per enabling rewrite, 17 item 2) is **not built**
     in this effort: route 1 on the derived implementation replaces it. Saves about one month and
     removes research 21's flattening risk for 27.
   - **Route 3** (an offload-only rewrite proven per thread against its proven predecessor, 17
     item 4.3) **stays**: it skips re-proving the reshaped loops for every candidate. Its lockstep
     relation comes with the offload-only contract, not from an alignment proposal.
   - Per final candidate: route 3 when its predecessor is proven, else route 1.
   - **Enabling rewrites and rewrite chains are unchanged** (Yan-Ru: they make the baseline match
     the intrinsics, which is orthogonal to the proof route; 17 item 1).
   - 17 item 4.4's fallback (a failed rewrite gets only the direct bounded check) becomes route 1
     on every evaluated kernel; the bounded direct check remains for a kernel with no unit
     postcondition.

4. **Sum library at method level** (Q6). A logic-library part of the method version, written and
   proven before the freeze: a range sum, a filtered sum by an offsets array (the flattening case,
   `pr.cc:233-245`), and three lemmas: additivity, regrouping a flat edge range by owner vertex,
   permutation of a finite sum. Tested on the calibration suites plus a CSR fixture, never on PR or
   BC. Kernel-specific definitions (SSSP's distance, BC's path counts) are drafted after the freeze
   and count in RQ3. Rough cost: 1-2 weeks.

5. **The authors' code that matches no contract** (Q7) may reach proven unbounded by route 1
   (unit postcondition plus hazard freedom). Its record says "direct, no matching contract; formal
   halves not applicable"; it is reported apart from RQ1's rates. Amends 18 item 5 (was: direct
   bounded check only).

6. **Concurrency, any input, cost.** Route 1 at N > 1 uses 15's machinery unchanged (per-thread
   proof, shared-action kinds, parallel composition theorem); no for-all-exists pairing is needed.
   Route 1 works on any input code inside the C++ subset (13 item 2). Net cost: the sum library
   (1-2 weeks) against the catalog templates dropped (about one month).

7. **Vocabulary and evaluation** (Q8). 13's vocabulary is unchanged (no new kind; hints call
   logic-library definitions), so no version bump. To ticket 23: route used per candidate; the sum
   library's one-time cost (RQ3); the number of candidates that would have needed an alignment
   (expected 0); direct-route verdicts for the authors' code. 17 item 9a is re-scoped: per-candidate
   proof time of chained (route 3) vs direct (route 1) vs bundled.

**Changes to earlier tickets** (each noted under its "Later changes"): 09 item 3; 10 item 2.3;
17 items 2, 4.4 and 9a; 18 item 5 and RQ3; 23 items 2 and 8.

**Inputs passed on:**
- **Ticket 27:** (1) WP on real-valued sums at our sizes is untested: an early stage proves the
  sum library's lemmas and one PR unit; (2) SSSP's per-candidate proof needs delta-stepping's
  outer-loop invariant, supplied by seeds from the contract proof (13 item 9), a risk; (3) build
  item: the sum library; (4) 21's catalog-template risk is gone (no templates built).
- **SSSP contract drafting** (side finding): both versions `assert(false)` on a small non-empty
  current bin (`sssp.cc:269-273,384-388`), and the fork builds without `NDEBUG` (`Makefile:5`).
  It never fires with the default delta 1 (`command_line.h:224`) and positive weights; the
  contract needs "delta <= least weight" as a proof-unit precondition or proves the assert
  unreachable.

Glossary: alignment added; unit postcondition sharpened (may allow several outcomes).

## Later changes

- 2026-10-13 21:29 ET, from [27](27-proof-of-concept-stages.md) (item 3): input 1's early "one PR unit" becomes one unit of a
  synthetic CSR pull-sum fixture, because PR is held out (18 item 5; item 4 here: the sum library is
  never tested on PR or BC). Input 2's SSSP risk is tested the same way, on a synthetic
  bucketed-relaxation fixture, in stage A3.
