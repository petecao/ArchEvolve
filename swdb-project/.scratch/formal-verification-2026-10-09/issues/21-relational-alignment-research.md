# 21 — Which methods find a relational proof's alignment automatically, and can a wrong one make a proof unsound?

Created: 2026-10-13 17:02 ET
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

17 item 4.4 found no unbounded route for a final candidate artifact whose rewrite chain fails to
prove: a direct relational proof against the baseline implementation needs an **alignment** (which
steps of the two programs run in lockstep), and only contract templates supply one. Find out:

- **Methods that find alignments automatically**, with what they handle (loops, different loop
  counts, reordered iterations): product programs (Barthe, Crespo and Kunz, FM 2011), regression
  verification (Godlin and Strichman; REVE, Felsing et al., ASE 2014), semantic program alignment
  (Churchill et al., PLDI 2019), property-directed self-composition (Shemer et al., CAV 2019),
  constraint-based relational verification (Unno et al., CAV 2021), and any 2023-2026 work where an
  LLM proposes the alignment or the relational invariant.
- **Soundness:** can a wrong or partial alignment make a product-program proof unsound, or only
  incomplete? Which side conditions (covering every pair of runs, fairness, termination) must a
  checker confirm, and can WP prove them?
- **Fit with our setup:** WP on product programs we build (11 item 5), which prove for-all-pairs
  properties; multi-threaded pairs need for-all-exists (17 item 4,
  `research/03-prove-once-rewrite-rules.md:23-28`); hints only as ACSL records under 13's checks.
- **Evidence of cost:** reported success rates and failure modes on loop-heavy C.

Output: `../research/21-relational-alignment.md`, every citation checked (map Notes). Facts only;
the decision is ticket 24.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Direct unbounded proofs without a template" fog.

## Answer

2026-10-13 17:53 ET. Resolved by a research subagent; findings in
[`../research/21-relational-alignment.md`](../research/21-relational-alignment.md) (about 45
sources, read scope per source). Spot-checked in the main session: Churchill et al. (PLDI 2019) in
Crossref and Charalambous et al. 2026 on arXiv match.

1. **A wrong alignment is unsound only through an unchecked side condition.** Three recur: guard
   agreement where steps are paired, adequacy (every pair of runs covered; no stuck product state)
   and fairness (no side starved, no one-sided divergence). Assumed, they make proofs vacuous (a
   scheduler that only runs copy 1 "proves" anything). Proven, a bad guess only fails.
2. **WP can state all three** with kinds 13 already allows (`assert`, loop invariants, integer
   `loop variant`). The scheduler cannot be ghost code (Frama-C rejects control-flow ghosts), so an
   alignment changes the product program itself. That each product step is a real step of the two
   programs is a theorem about the construction rules, proven once per generator.
3. **Automatic aligners all guess and check;** none uses an LLM to propose the alignment of an
   unbounded relational proof (2023-2026 search). Nearest: Trivet (LLM fills holes in a fixed
   alignment), Charalambous et al. 2026 (LLM one-sided contracts), LLMLift.
4. **Cost on loop-heavy C is high:** the strongest result (Churchill et al.) proves 55 of 56 TSVC
   pairs at a median 45 CPU-hours per pair and excludes memory indirection.
5. **Blind spots match our catalog:** no known product-program technique proves loop flattening as
   is (needs loop summaries plus termination); unbounded reordering (fission-, fusion- and
   tiling-like) is out of reach for the data-driven method. Research's reading: 17's edge-loop
   flattening, phase split and chunking fall in these classes.
6. **For-all-exists** needs a witness for the existential side; tools handle small programs only.
   Against a deterministic, terminating reference it reduces to for-all-pairs plus termination
   (research's reading), which fits proofs against the single-thread baseline (11 item 10; 17
   item 4.2).

**Inputs passed on:**
- **Ticket 24:** items 1-6, and research 21's "Inputs for ticket 24" list (no recommendation there).
- **Ticket 27 (risk):** item 5 questions 17 item 2's estimate of about one week per catalog
  template for flattening, phase split and chunking; their templates may need loop summaries
  rather than a plain product program. A proof-of-concept stage should test one early.
