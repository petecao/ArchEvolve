# 09 — What does the "proven" level assert about a candidate artifact?

Created: 2026-10-09
Updated: 2026-10-12 22:25 ET (resolved with Yan-Ru in two grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-12 19:52 ET)
**Blocked by:** 03
**Map:** `../map.md`

## Question

What exactly does a proven level assert about a candidate artifact? Choose or combine:

- each clause's formal half holds;
- the candidate refines the baseline implementation modulo the kernel's correctness check
  (BFS parents may legitimately differ);
- the candidate meets the kernel's postcondition directly.

Also decide the proof unit (one `TDStep` call per BFS level, or the whole BFS) and which bounds a
proven-within-bounds verdict must declare.

## Comments

- 2026-10-09: input from 03: compare BFS outputs as visited set and per-level frontier sets plus
  parent validity (∀∃ refinement under OpenMP); list the assumption set every proven verdict
  depends on (assumed clauses L3 and L5, reference semantics).
- 2026-10-12 22:00 ET: grilling round 1 with Yan-Ru (checkpoint; not yet the answer).
  - **Settled:** proven applies only to a certified candidate artifact (certification is
    testing; proof adds to it). Every proven verdict records an assumption set, each entry
    labeled by kind. Every `assume` in a harness is proven at each real call or listed as a
    reduction with its own obligation. Thread count is a bound: a single-thread proof is at most
    proven within bounds (threads = 1).
  - **Mostly settled:** the proof unit is one `TDStep` call, and whole BFS is proven once by
    induction over the `DOBFS` loop (a lifting lemma).
  - **Open:** what one proof unit claims (relational, postcondition, clause by clause, or all).
  - **New requirement:** the method must be general; evaluate on other GAPBS kernels.
  - **Found:** 08's harness assumes `parent[v] >= -1`
    (`../prototype/08-wrong-tile/tdstep_harness.cpp:74`), but `InitParent` writes
    `-out_degree` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:310`). 08's proof misses real inputs.
  - Glossary: proof unit, lifting lemma, assumption set added; certification level and formal
    verifier sharpened.
- 2026-10-12 22:20 ET: rounds 2–3. Yan-Ru accepted A + B + hazard freedom, plus C where a kernel
  has a clean definition; a machine-checked lifting lemma; real-number equality for floating
  point; per-contract bound dimensions; the cap rule. On "output relation", Yan-Ru asked for both
  levels: the rewrite is verified against its contract (unit relation), and the final output
  against the kernel (output relation).

## Answer

2026-10-12 22:25 ET. Decided with Yan-Ru in a grilling session (rounds 1–3 in Comments).

A proven verdict is a machine-checked claim about **the candidate artifact's change against the
rewrite contract it applies**. It adds to certification and never replaces it.

1. **Two relations, two homes.**
   - **Unit relation, in the rewrite contract:** what the candidate's proof unit must preserve
     relative to the baseline, and what may differ. BFS read offload: after one `TDStep` call,
     the same newly visited vertices, the same next-frontier *set* (queue order may differ),
     every new parent a valid frontier neighbor, every other vertex unchanged.
   - **Output relation, in the kernel** (beside its correctness check): which differences in the
     final output are acceptable. BFS: same reachable set and depths; parents may differ, each
     valid (what `BFSVerifier` checks).
2. **What one proof unit claims (all kernels):**
   - (A) every formal half of the contract that applies to the unit holds;
   - (B) the unit refines the baseline's unit modulo the contract's unit relation;
   - hazard freedom: the CPU never reads accelerator results before they are ready, under the
     semantics ticket 12 picks.

   (A) + (B) + hazard freedom is "the rewrite is proven against its contract": the claim Extensa
   could not make.
3. **Bonus where a kernel has a clean definition (C):** the unit also meets a stated
   postcondition (for BFS, 08's P2). Proving C for the candidate, plus once for the baseline,
   gives (B) when C fixes the compared state uniquely, as it does for BFS. Kernels without a
   clean definition (PR, BC) get (A) + (B) only.
4. **Floating point:** for PR and BC, "same" means equal over real arithmetic; rounding is an
   assumption-set entry. DX100 PR adds through `maa_indirect_rmw_vector(..., ADD_OP)`
   (`apps/dx100/benchmarks/gapbs/src/pr.cc:242`), so bitwise equality is not expected.
   Certification still checks the kernel's tolerance at run time.
5. **Proof unit:** one call of the function that holds the rewrite site (`TDStep` for BFS). A
   candidate artifact's level is the weakest level among its proof units.
6. **Lifting lemma:** machine-checked, proven once per rewrite contract and kernel (not per
   candidate): if every call meets the contract's unit relation, the final output meets the
   kernel's output relation. For this DX100 BFS it is induction over the `DOBFS` loop, which calls
   only `TDStep` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:343-352`). Until it is checked, the
   whole-kernel claim is an assumption-set entry ("written proof").
7. **Proven requires certified.** A proven level applies only to a candidate artifact already
   certified for the same content hash.
8. **Assumption set:** every proven verdict lists what it depends on without proving it, each
   entry with its kind: an assumed clause (BFS: L3, L5, owner Eric), the trusted accelerator
   semantics (today: the strict-layer port plus the gem5 wait rule, matched by differential test
   only), a building-block summary, a reduction (such as 08's relabeling), or a trusted tool
   (verifier, solver, clang).
9. **Cap rule:** proven dependencies cap the level (a summary proven only within bounds makes
   the unit at most proven within bounds). Unproven dependencies go in the assumption set and do
   not cap.
10. **Harness `assume`s:** each is either proven at every real call (via the lifting lemma) or
    listed as a reduction with its own proof obligation. Any other `assume` voids the verdict.
    **Known violation:** 08's harness assumes `parent[v] >= -1`
    (`../prototype/08-wrong-tile/tdstep_harness.cpp:74`), but `InitParent` writes
    `-out_degree` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:310`). The proof-of-concept harness
    must widen it.
11. **Bounds:** each rewrite contract lists its bound dimensions, thread count always among them.
    A verdict records a value or "unbounded" for each; proven unbounded means every dimension is
    unbounded, so single-thread proofs are at most proven within bounds (threads = 1). BFS read
    offload: threads, vertices, edges, tile lanes, knob values (chunk size, frontier threshold),
    frontier size, loop unroll depth. 08's verdict reads threads = 1, lanes = 1, edges = 1.
12. **Generality (new requirement):** the method is evaluated on other GAPBS kernels, not only
    BFS. Every item above applies per kernel and per contract.

**Inputs passed on:** unit relation and bound dimensions per contract → ticket 10; real
arithmetic, lifting-lemma tool and thread-parametric proofs → ticket 11; checker inventory of
`assume`s → ticket 13; assumption set, bound record and cap rule → the map's "Records" fog.
Glossary: proof unit, unit relation, output relation, lifting lemma, assumption set added;
certification level and formal verifier sharpened.
