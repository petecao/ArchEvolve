# 10 — What does a proven rewrite contract prove once?

Created: 2026-10-09
Updated: 2026-10-12 22:46 ET (resolved with Yan-Ru in two grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-12 22:27 ET)
**Blocked by:** 03, 09
**Map:** `../map.md`

## Question

What does a proven rewrite contract prove once, and what is left to check for each candidate
artifact? Options include:

- proven building blocks: intrinsic lowerings and library operations proven against reference
  semantics, then reused as summaries in candidate proofs;
- a rewrite contract proven sound for all code matching its pattern key;
- both.

Name the per-instance check and say why it stays small enough to scale where Extensa's gates did
not.

## Comments

- 2026-10-09: input from 03: pure prove-once needs code that is an exact template instance,
  which LLM candidates are not. 03 recommends a staged hybrid and suggests rewording decision 2(a)
  in 01 to "contract parts proven once, plus a small per-instance proof". Decide here.
- 2026-10-09: input from 06: LPG (2026) could not prove its generalized rules for all bitwidths
  and fell back to per-width checks; consider applying the two proven levels to contracts too.
- 2026-10-12 22:25 ET: input from 09: every rewrite contract must state (1) a unit relation (what
  one proof unit must preserve relative to the baseline, and what may differ), (2) its bound
  dimensions, thread count always among them, and (3) a machine-checked lifting lemma per kernel
  it applies to, linking the unit relation to the kernel's output relation. Decide here which of
  these the contract proves once. The method must be general across GAPBS kernels (map Notes).
- 2026-10-12 22:39 ET: grilling round 1 with Yan-Ru (checkpoint; not yet the answer). All eight
  recommendations accepted:
  1. Building-block proofs live with the library entry (lowering, library operation) and are
     reused by every contract that calls it. L1 in `bfs_read_offload` and `bc_read_offload`
     points at the same `range_loop` reference: one proof serves both.
  2. Clauses split by subject: intrinsic or library behavior (L1) proven once with that entry;
     the candidate's own code (L2, L4, `once_enqueue`, S2) checked per candidate in (A); assumed
     clauses (L3, L5) go to the assumption set. Knob ranges stay runtime guards or static
     assertions.
  3. For (B) the contract supplies either a unit postcondition C (proven once: the baseline meets
     C, and C on both sides gives the unit relation; per candidate: a single-program proof of C)
     or a relational template (per candidate: a paired-program proof). C wherever the kernel has
     a clean definition (BFS); the template otherwise (PR, BC).
  4. Each contract first proves its scaffold on a reference instance (its own library code;
     else its first certified candidate). 03's PEC-style fast path is dropped.
  5. Each once-proven part carries its own proven level and bounds; 09's cap rule applies; per
     dimension the verdict takes the smallest bound. Unproven parts are assumption-set entries.
  6. "Once" means once per set of content hashes (entry, reference semantics, baseline function,
     verifier version and flags). A change reopens the part; dependent candidates drop to
     certified until it is re-proven.
  7. Once-proven parts may be human-assisted, reviewed at promotion, under the same hint rules.
     Candidate proofs stay fully automatic.
  8. Scale is a hypothesis with a pass bar: 08's safe 2-lane case, with summaries instead of the
     inlined strict-layer port, proves in under 15 minutes on the Mac.
- 2026-10-12 22:43 ET: round 2 checkpoint. Accepted: Q9 (derivation records provenance,
  not proof reuse; reuse follows the content-hash rule), Q11 (each clause names its proof placement:
  once with a named entry, per candidate, or assumed; a clause without one blocks a proven
  verdict), Q12 (glossary: contract proof, reference instance, unit postcondition, relational
  template, summary). Q10 (negative controls in the contract proof) re-explained; open.
- 2026-10-12 22:46 ET: Q10 accepted after re-explanation (why negative controls apply to
  proofs: a narrow harness `assume`, an over-strong summary or a weak unit postcondition makes
  broken code prove too; 08's `parent[v] >= -1` assume would hide a candidate that tests
  `parent[v] == -1`).

## Answer

2026-10-12 22:46 ET. Decided with Yan-Ru in a grilling session (rounds 1–2 in Comments).

**Shape:** a staged hybrid. Some parts are proven once and reused; each candidate artifact gets
one small, automatic proof of its proof unit. Ticket 01 decision 2(a) now reads "contract parts
proven once, plus one small proof per candidate artifact".

1. **Proven once, with the library entry (not the contract):** each lowering and library
   operation is proven against its reference semantics. Its proven clauses become a **summary**
   that candidate proofs use in place of its code. Every contract that calls the entry reuses
   the proof. L1 in `bfs_read_offload` and `bc_read_offload` points at the same `range_loop`
   reference (`library/dx100/reference.hpp`): one proof of the `dxc_range_loop` lowering serves
   both.
2. **Proven once, with the contract (its contract proof):**
   - its **unit postcondition** C (where the kernel has a clean definition; BFS) with two
     lemmas: the baseline meets C, and two units that meet C satisfy the unit relation. Or, where
     no clean C exists (PR, BC), its **relational template**: alignment and coupling invariant;
   - that scaffold proven on the contract's **reference instance**: its own library code applied
     to the baseline (for BFS read offload, Peter's `bfs_read_offload.inc`); without library
     code, its first certified candidate artifact;
   - its lifting lemma per kernel (09);
   - every negative control a formal check can see, refuted on the reference instance with the
     same harness, summaries and scaffold. Each control is labeled single-thread, concurrency
     phase, or runtime only (such as the L3 race). A control that proves voids the contract
     proof: the setup cannot see that bug.

   03's PEC-style "fast path" (template matching) is dropped; the reference instance replaces it.
3. **Per candidate artifact:** one proof of its proof unit, with summaries in place of building
   blocks:
   - (A) the formal halves of clauses about the candidate's own code (BFS: L2, L4,
     `once_enqueue`; native staging: S2);
   - (B) via C (a single-program proof, as 08 did with P2) or via the template (a
     paired-program proof);
   - hazard freedom (09).

   Knob ranges stay runtime guards or static assertions, and the proof may rely on them.
   Assumed clauses (L3, L5) go to the assumption set.
4. **Proof placement per clause:** each clause names one: once (naming the entry that carries
   the proof), per candidate, or assumed. A checker confirms every clause is covered by a proof
   or by the assumption set; a clause without one blocks a proven verdict. ("Proof scope" is
   avoided: the glossary lists it under proof unit.)
5. **Levels:** each once-proven part carries its own level (proven unbounded, or proven within
   bounds with its bounds), as LPG's per-bitwidth fallback warns. 09's cap rule carries it into
   each candidate's verdict; per dimension, the verdict takes the smallest bound. An unproven
   part is an assumption-set entry and does not cap. A contract proof's level is the weakest of
   its parts.
6. **"Once" means once per set of content hashes:** the entry or contract, the reference
   semantics, the baseline function, and the verifier version and flags. A change reopens that
   part; candidates that depend on it drop to certified until it is re-proven.
7. **Derived contracts:** derivation records provenance, not proof reuse. Reuse follows item 6.
   `bc_read_offload` (derived from `bfs_read_offload`) inherits the building-block proofs and
   proves its own template, lifting lemma and BC-L1.
8. **Who proves:** once-proven parts may be human-assisted (Yan-Ru writes hints or proofs),
   reviewed at promotion, under the same hint rules (no `assume`). Candidate proofs stay fully
   automatic. The human cost is per contract, the automatic cost per candidate (the PEC and
   Alive split). That automatic per-candidate step is the paper's claim.
9. **Why the per-candidate check stays small where Extensa's gates did not:** it covers one
   call, not a benchmark; summaries remove the loops inside building blocks (in 08 the inlined
   strict-layer port made 2 lanes time out at 15 minutes); and the contract supplies C or the
   coupling invariant, so nothing searches for it. **This is a hypothesis with a pass bar:** in
   the proof of concept, 08's safe 2-lane case with summaries instead of the inlined port proves
   in under 15 minutes on the Mac. If it fails, the claim drops to "proven within bounds at
   1 lane".
10. **Generality:** building-block proofs serve every contract that calls the entry; the
    proof-placement field, the two routes, the reference instance and the negative-control check
    apply to every contract and kernel.

**Terms:** never "proven contract" alone. Say "contract proof at level X" or "candidate artifact
proven against its contract". Glossary: contract proof, reference instance, unit postcondition,
relational template, summary added; negative control and certification level sharpened.

**Inputs passed on:** summaries and the two proof routes → ticket 11; DX100 lowering summaries
with hazard state → ticket 12; human-assisted contract proofs, proof-placement check and
per-candidate vacuity → ticket 13. The map's "Vacuity guard" fog is settled by item 2.
