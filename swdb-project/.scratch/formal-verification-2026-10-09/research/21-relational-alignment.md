# 21 — Automatic alignment for relational proofs, and when a wrong one is unsound

Created: 2026-10-13 17:43 ET
**Ticket:** [`../issues/21-relational-alignment-research.md`](../issues/21-relational-alignment-research.md) · **Map:** [`../map.md`](../map.md)
**Feeds:** ticket 24 (alignment hint kind). Facts only, no design decisions.
**Method:** scoped narrative literature review, not a systematic review
(`mattpocock-skills:research`, `academic-research-skills:deep-research` lit-review discipline).
Searched 2026-10-13 with web search, the arXiv API, Crossref and OpenAlex. Every source was opened
at its DOI record, arXiv, venue page or an author page; title, authors, venue and year were
checked against Crossref or arXiv. Read scope per source is under [Sources](#sources).
*Our reading* marks an inference no source states.

## TL;DR

- **A wrong or partial alignment only makes the proof fail, provided the checker proves the
  alignment's side conditions. If it assumes them, the proof can be vacuous.** A scheduler that
  only ever runs copy 1 "proves" every postcondition [PDSC19 §3.1]. Guessed alignments stay sound
  because every guess is checked: "insufficient data will cause the proof to fail" [DDEC13].
- **Three side conditions recur:** guard agreement wherever steps are paired (asserted, never
  assumed); **adequacy** (every pair of terminated runs is a run of the product; every reachable
  product state can move); **fairness** (no unfinished side is starved; no one-sided divergence).
  Termination is usually assumed or proven separately [REVE14; LLRÊVE18].
- **WP can state all three** as ACSL `assert`, loop invariants and integer `loop variant`, which
  become WP goals (research/13 Q3, Q7). Coverage of one given product can be per-instance VCs
  [LFCS13 §4; SPA19 §3.1]. That every product step is a real step of the two programs is a
  theorem about the construction rules, proven once [FM11 Prop. 1–5; LICS21 Thm 7].
  Frama-C precedent uses the Jessie plugin, not WP [FM11; LFCS13]; RPP runs on WP but has no
  relational loop invariants [RPP18 §7]. No paper found checks a proposed alignment with WP.
- **Automatic alignment exists, always as guess-and-check** (Horn solving, test traces,
  predicate abstraction, games). Most evaluations use small integer programs. The strongest
  loop-heavy C result, 55 of 56 TSVC pairs [SPA19], needs test inputs, a median 45 CPU-hours per
  pair, and excluded memory indirection.
- **Known blind spots hit our catalog** (17 item 2): [SPA19]'s authors know of no
  product-program technique that proves loop flattening as is, and their method cannot handle
  fusion, splitting, interchange or tiling over unbounded memory.
- **No 2023–2026 paper found in which an LLM proposes the alignment of an unbounded relational
  proof.** LLMs fill invariant holes inside a fixed alignment [Trivet26], write one-sided
  contracts [Contracts26], or write invariants against a functional summary [LLMLift24]. LLM
  equivalence *judgments* sit near chance on hard pairs [EquiBench25].
- **∀∃ needs a witness for the existential side** (leftness conditions, witness strategies plus
  prophecy, functional predicates); the tools handle small programs only. For a deterministic
  existential side, left and full products coincide [LFCS13 §5]. *Our reading:* ∀∃ against a
  deterministic, terminating reference is then ∀∀, which fits the single-thread baseline
  (11 item 10).

## Q1. Methods that find alignments automatically

An **alignment** says which steps of the two programs run together. A product program fixes one;
the coupling (relational) invariant is then proven on the product. Glossary: a contract's
**relational template** is a fixed alignment plus coupling invariant.

| Method | How the alignment is found | Different trip counts | Reordered or split iterations | Data-dependent control | Data |
|---|---|---|---|---|---|
| **Product programs** [FM11] | By hand, from construction rules plus refinements (unroll, peel, split a loop). Tools are "further work" (§6). | Yes, by unrolling or peeling; non-equivalent guards fall back to sequential loops | Interchange and fission shown by hand; 1 of 37 interchange goals needed Coq (Table 1) | Branches either assert guard agreement or are handled one-sided | Arrays (Why) |
| **Asymmetric products** [LFCS13] | A Frama-C plugin follows both flow graphs and picks a left, right or joint edge at each branch (§6) | Yes | Loop tiling (full product, Fig. 6) | Yes; nondeterminism allowed | Disjointness annotations by hand |
| **Regression verification** (RVT) [GS08; GS09; GS13; SS22] | Function mapping; loops become recursion; matched recursive calls become one uninterpreted function | Only "in sync"; out-of-sync fails [SS22 §2.1]. [SV16] needs the unrolling as input; [SS22] finds it automatically | No | Yes, inside loop-free checks (CBMC) | — |
| **REVE** [REVE14] | Greedy rule order matches loops as they occur; a Horn solver infers the coupling predicate | Loop rule lets one loop continue alone; a 4× unrolled loop needed a hand-made intermediate (§5.1) | No | Yes | Integers only, no arrays (§5.2) |
| **LLRêve** [LLRÊVE18] | Synchronization marks (`__mark`), placed by hand for libc; stuttering clauses for extra iterations | Yes (stutter) | No | Yes | Heap as SMT array |
| **Data-driven** [DDEC13; SPA19] | Guess alignment predicates from test traces, learn a product automaton, check with SMT | Yes, including data-dependent ratios (vectorized `strlen`) | **No**: reordering unbounded writes (splitting, fusion, interchange, tiling) and flattening are out (§5.6) | Yes | x86-64; heap equal except finitely many cells |
| **PDSC** [PDSC19] | Composition function inferred with the invariant over given predicates (mined, some manual) | Yes (state-dependent scheduling) | — | Yes | LRA and arrays (Spacer) |
| **PCSat** [PCSat21] | Scheduler as unknown predicates plus non-Horn fairness clauses, solved by CEGIS | Yes | — | Yes | Linear arithmetic; arrays not fully supported |
| **HyHorn** [HyHorn24] | Alignment, invariant and ∃-witness encoded as CHC, solved by Spacer | Yes | — | Yes | Arithmetic and arrays |
| **WhyRel** [WhyRel23] | User writes biprograms with alignment guards (left-only, right-only, lockstep); the tool checks adequacy | Yes | Loop tiling case study | Yes (guards on data) | Pointer programs (Why3) |
| Others, abstract-level | Weaver: CEGAR search for a reduction of the product [Weaver19]; Pequod: sync points and invariants searched together, JVM [Pequod19]; counterexample-guided correlation, IR vs assembly [Counter20]; synchronizing k-safety subtasks [Synonym18; CHL16]; procedure-modular products [MPP18] | | | | |

### LLM work, 2023–2026

**No paper found in which an LLM proposes the alignment (scheduler, synchronization points,
product) of an unbounded relational proof.** The nearest work:

| Work | What the LLM writes | Where the alignment comes from | Checker | Result |
|---|---|---|---|---|
| Trivet [Trivet26] | Lean loop invariant, inductive step, final assembly, other proof holes | Fixed scaffold: source is one self-loop block, target loop-free (§3.3) | Lean kernel; no `sorry`/`admit`, standard axioms, statements unchanged | 147 of 148 LLVM transformations; loop set 14 valid + 14 invalid |
| LLMLift [LLMLift24] | Target-DSL summary and loop invariants | None: the invariant relates the source loop to the summary (one-sided) | cvc5/Z3, all inputs | Side-effect-free code only |
| Charalambous et al. [Contracts26] | One-sided contracts for the old version | None: assume-guarantee replacement | ESBMC k-induction | EqBench-C: zero false equivalences |
| LLM-Vectorizer [LLMVec25] | The vectorized loop | None | Alive2, bounded | 38.2% of TSVC verified |
| Wang and Xie [WangXie24] | A soundness prediction when Alive2 is inconclusive | None | Fuzzing | No proof |
| EquiBench [EquiBench25] | An equivalent/inequivalent label | None | Ground-truth labels | Best 63.8% and 76.2% on the hardest categories (chance 50%) |
| ProofWright [ProofWright25]; self-play [SelfPlay26] | CUDA kernels in an agentic verification loop; Haskell variants with Liquid Haskell proofs | Not stated | Not named in the abstract; Liquid Haskell | Equivalence for element-wise kernels; training gains only |

Search terms (2026-10-13): LLM with relational verification, product program, coupling or
relational invariant, regression verification, translation validation, synchronization points,
trace or loop alignment, k-safety, hyperproperty, verified loop transformations, C-to-Rust
equivalence proofs.

## Q2. Soundness: what a checker must confirm

**Answer: unsound only through an unchecked side condition.** Each paper that proves soundness
states the conditions under which the product's proof transfers to the two programs.

| Side condition | What goes wrong if it is assumed | How papers discharge it | WP form (research/13) |
|---|---|---|---|
| **Guard agreement** where steps are paired (loop heads, branches) | Pairs where one loop exits first are silently dropped | `assert(b1 ⇔ b2)` inserted by the construction; validity includes "non-stuck" [FM11 §3.2, Def. 2]; lockstep loops need agreeing guards [WhyRel23] | `assert` gives a goal and a hypothesis; `admit` gives only a hypothesis (Q3) |
| **Adequacy (coverage):** every pair of terminated runs is a product run; every reachable product state can move | Uncovered pairs are never checked; "stuck" states make violations unreachable [HyHorn24 §2.2] | Path pairs absent from the product must be infeasible [SPA19 §3.1, obligation 2]; `Inv ⇒ ∨ C_M` [PDSC19 Def. 4]; R-adequacy [LICS21 Thm 7]; leftness VCs [LFCS13 §4]; biprogram check [WhyRel23] | First-order formula over product state: `assert` or loop invariant at the product loop head |
| **Fairness / progress:** an unfinished side is scheduled; no cycle in which one side never moves | The product never terminates, so partial correctness holds vacuously [PDSC19 §3.1] | Fairness condition [PDSC19 Def. 3–4]; clauses (4)–(5), on which soundness "crucially relies" [PCSat21 Thm 1]; no cycle with one side's paths empty [SPA19 obligation 3]; strong adequacy forbids one-sided divergence [LICS21 §III] | `assert` that the chosen step moves an unfinished side; integer `loop variant`. `loop variant … for R` is *assumed* well-founded (Q7) |
| **Termination** of each program | Only partial equivalence is shown | Assumed, checked by other tools [REVE14 §2; LLRÊVE18 §4.8]; for ∀∃, strong termination of the right program or no right-only loops [LFCS13 Lemmas 2–3] | WP termination goals. An infinite loop gave a `terminates` timeout while a false postcondition showed `[ Valid ]` (Q6) |
| **Construction:** each product step is a step of one or both programs | The proof is about another program | Proven once for the rules [FM11 Props. 1–5; LFCS13 Lemma 1, Thms 1–2; LICS21 Thm 7]; a relational VC generator proven sound in Coq [CertRel22] | Not a WP goal: a property of the generator |

**Unchecked alignments are unsound.**
- A non-fair composition that maps every state to copy 1 never terminates, so it satisfies every
  pre/post pair [PDSC19 §3.1].
- Scheduler predicates with no choice in some states give "stuck" states that make a violation
  unreachable [HyHorn24 §2.2].
- Treating guard agreement as an assumption is not adequacy; it must follow from the precondition
  [BiKAT23 §8.2]. Lockstep alone is not adequate in general [LICS21 §III].

**Checked guesses only lose completeness.**
- DDEC: a lack of test coverage can make the check fail but cannot yield a wrong equivalence
  [DDEC13 §1].
- REVE: correct for any order of rule application; counterexamples are genuine [REVE14 Thm 1].
- [SPA19] returns "unknown" when no guessed alignment passes (Fig. 7).
- Overlapping or partial scheduler conditions "do not damage soundness" when the invariant shows
  every reachable state is covered [PDSC19 Remark 1].
- [BiKAT23 abstract, §1] states the split: the product satisfies the property, and the product is
  adequate; alignments "discovered algorithmically or devised manually" both need the adequacy
  proof.

**Can WP prove the side conditions?**
- **In form, yes.** Guard agreement, coverage and fairness are first-order formulas over the
  product state; progress is an integer measure. WP turns `assert`, loop invariants and integer
  `loop variant` into goals (research/13 Q3, Q7). Ticket 13's vocabulary already allows these
  kinds (13 item 5).
- **The scheduler cannot be ghost code.** Frama-C rejects ghost code that changes control flow
  (research/13 Q1). An alignment therefore changes the product program itself.
- **Coverage of one product can be per-instance VCs**, checked by the same verifier: leftness
  VCs in Jessie/Why [LFCS13 §4], SMT obligations [SPA19 §3.1], a tool check of user biprograms
  [WhyRel23].
- **Correctness of the construction is outside the verifier** in every paper read: that each
  product step is a step of the programs is a theorem about the rules [FM11 Props. 1–5; LFCS13
  Lemma 1; LICS21 §III]. One relational VC generator is proven sound in Coq [CertRel22].
- **Frama-C precedent:** [FM11] verified hand-built products with Why and Frama-C/Jessie (most
  goals by SMT, Table 1). [LFCS13] built products in a Frama-C plugin that emits the leftness
  VCs. RPP runs on WP but only by sequential self-composition, and relational loop invariants
  are "not possible yet" [RPP18 §7].
- **WP pitfalls that apply** (research/13): `admit`, axioms and unproven lemmas can sit behind
  `[ Valid ]` (Q4); smoke tests catch dead code after a non-terminating loop but are best effort
  (Q6).

## Q3. For-all-exists (essentials)

- **Product programs prove ∀∀:** every pair of terminated runs from related states ends related
  [FM11 Def. 1; LICS21 §I]. PDSC, PCSat's k-safety encoding, REVE and [SPA19] are ∀∀.
- **∀∃ needs a witness** that resolves the existential program's choices:
  - *Left products:* the product must be able to move wherever the left program can, checked
    as VCs; the right program must strongly terminate or the product must have no right-only
    loops [LFCS13 Def. 4, Lemmas 2–3, Thm 1].
  - *Alignment witnesses:* the witness must be ∀∀-correct, cover every left run, and be a real
    right run; "not simply a reduction" to ∀∀ [BiKAT23 Thm 7.1].
  - *Games:* a witness strategy picks the existential program's steps, combined with a reduction;
    it fails when the witness needs future moves [HyPA22 §2.2]. Prophecy variables make the
    game approach complete for finite-state systems [Proph22; HyPA22 §8].
  - *Constraints:* functional predicates [PCSat21]; a CHC-encoded witness function [HyHorn24];
    ∀ᵏ∃ˡ by program logic and strongest postconditions [HyLive24].
  - *Deductive:* ghost-variable function specs [RHLE22]; a ∀∃ relational Hoare logic proven
    sound and alignment complete [LMCS25]; ghost monitors [Ghost20].
- **Refinement mappings** from implementation states to specification states may not exist;
  adding history and prophecy variables guarantees them under stated assumptions [Abadi91].
- **Concurrent pairs:** proof rules reduce partial equivalence of two multi-threaded programs to
  equivalence of sequential functions, without composing threads [Chaki12]; the journal version
  adds locks and dynamic thread creation [Chaki15].
- **Deterministic existential side:** for a deterministic right program, left products and full
  products coincide [LFCS13 §5], and the refinement judgment's existential names the right
  program's unique terminating run [LFCS13 §4]. *Our reading:* ∀∃ against a deterministic,
  terminating reference is ∀∀ plus that termination.
- **Cost:** ∀∃ tools are evaluated on very small programs with user predicates; witness synthesis
  is 2EXPTIME-hard even for finite-state systems, as [HyPA22 §7] cites.

## Q4. Evidence of cost

| Work | Programs | Outcome | Cost | Reported failure modes |
|---|---|---|---|---|
| [FM11] | 12 hand-built examples (loop optimizations, static caching) | Most goals by SMT; interchange 36/37, static caching 162/176, rest in Coq | — | Product built by hand |
| [REVE14] | 16–53 LOC integer pairs (both sides) | Eldarica proves most; `ackermann` not | Up to 28 s; timeout 600 s | 2:1 step ratio first unproven; 4× unrolling needs a manual intermediate; no arrays |
| [LLRÊVE18] | libc string functions (dietlibc, glibc, OpenBSD) | Most proven | Z3 mostly < 1 s; Eldarica up to 15 s; some 300-s timeouts | Sync marks placed by hand |
| [SPA19] | 28 TSVC functions, gcc -O1 vs gcc -O3 and clang -O3 (56 pairs); glibc `strlen` | 55/56; `strlen` proven | Median 45 CPU-h per pair (2.5–1166); `strlen` 3.3 min | Excluded 2-D arrays and memory indirection (11 functions) and interchange (6); search space 182–3318 predicates per pair, 3.1% viable on average (§5.5) |
| [PDSC19] | 5 non-lockstep examples; Java k-safety suites converted to C | All 5 (Synonym 0) | 2.8–58.2 s | Manual predicates for 3 examples |
| [PCSat21] | 20 problems | 15 automatic, 5 with hints | Limit 600 s | Linear arithmetic only; arrays not fully supported |
| [HyPA22] | Very small ∀∃ programs | All listed solved (lazy solver) | Up to 113 s | User predicates; no other tool solved them |
| [HyHorn24] | 112 k-safety examples plus HyPA's ∀∃ set | Compared with HyPA, PCSat, PDSC on their own suites | e.g., 0.56 s vs HyPA's 67 s on one example | No shared benchmark format; manual translations (§7) |
| [Contracts26] | EqBench-C, 272 pairs (loops, non-linear arithmetic, floats, strings) | 70 decided without contracts; 102–106 with LLM contracts | ESBMC under k-induction | 202 pairs time out or hit tool errors without contracts |
| [Trivet26] | 148 LLVM IR transformations, 28 with loops | 147 resolved | Loop proofs median 1471 s; mean $2.93 per loop proof | One self-loop source, loop-free target; integers only |
| [LLMVec25] | TSVC | 38.2% verified | — | Bounded only |
| [RoseBansal24] | C procedures up to 100+ SLOC vs 200+ instructions of assembly, with loop and vectorization transformations | Abstract only | — | — |

**Failure modes on loop-heavy C, across sources:**
1. Unbounded reordering (splitting, fusion, interchange, tiling): heap invariants that equate
   all but finitely many cells cannot express it [SPA19 §5.6]. Static-affine methods handle it,
   but only for compile-time control flow [REVE14 §6, on Verdoolaege et al.].
2. Loop flattening (m inner iterations ↔ 1 outer): the authors know of no product-program
   technique that proves it as is; it needs loop summaries plus a termination check [SPA19 §5.6,
   Fig. 12].
3. Memory indirection: excluded from [SPA19]'s benchmark set; arrays unsupported in [REVE14] and
   not fully supported in [PCSat21].
4. Out-of-sync recursion or unrolling factors: RVT fails unless the unrolling is supplied [SV16]
   or found [SS22].
5. Solver time dominates: 45 CPU-h median per TSVC pair [SPA19]; 202 of 272 EqBench-C pairs
   undecided without contracts [Contracts26].

## Inputs for ticket 24

Facts that bear on the decision; no recommendation.

1. No prior LLM work proposes the alignment of an unbounded relational proof (Q1). Prior LLM roles
   are invariants inside a fixed alignment, one-sided contracts, or bounded checks.
2. Every automatic aligner is guess-and-check, and its soundness never depends on the guess once
   the side conditions are proven (Q2). In [SPA19 §5.5], 182–3318 candidate predicates per pair
   gave viable products for 3.1% on average.
3. The side conditions are first-order and expressible with kinds 13 already allows (`assert`,
   loop invariant, integer `loop variant`). The scheduler cannot be ghost code (research/13 Q1).
4. Coverage of a given product is checkable per instance (leftness VCs, SMT obligations, a
   biprogram check). Correctness of the construction rules is a once-proven theorem in every
   paper read; one VC generator was proven sound in Coq [CertRel22].
5. A total fallback alignment always exists: sequential composition is adequate but needs
   functional invariants [FM11 §1–2; LICS21 §IV].
6. *Our reading:* the catalog's edge-loop flattening matches Q4 item 2; its phase split
   (fission-like) and chunking (tiling-like) match Q4 item 1.
7. ∀∃ tooling covers small programs only; ∀∃ against a deterministic, terminating reference is ∀∀
   (Q3; *our reading* for the single-thread baseline).
8. Cost data on loop-heavy C: median 45 CPU-h per TSVC pair [SPA19]; Trivet loop proofs median
   1471 s at a mean $2.93 [Trivet26].

## Open questions

- Can WP discharge [SPA19]-style coverage goals (infeasible path pairs) at our product sizes?
  Untested.
- Which language and loop features does the Coq-proven relational VC generator cover
  [CertRel22]? Read at abstract level only.
- Does an LLM proposal beat enumerative guessing of alignment predicates? No data found.
- Do [Chaki12]'s rules fit data-parallel loops with shared atomics? Abstract only.
- Counter's loop results [Counter20] and the 2016 product-program journal paper [JLAMP16] were
  not readable (paywall or 403).

## Sources

Checked: **Crossref** = DOI metadata matched title, authors, venue and year; **arXiv** = arXiv
record opened. Read scope: *full*, *partial* (named sections), *abstract*, *metadata*.
**Unverified** means the content could not be opened; the bibliographic data was still checked.

**Product programs and relational logic**
- [FM11] Barthe, G., Crespo, J. M., Kunz, C. (2011). *Relational Verification Using Product Programs*. FM 2011, LNCS, 200–214. https://doi.org/10.1007/978-3-642-21437-0_17. Crossref. Read: full (author PDF, https://software.imdea.org/~jmcrespo/docs/FM2011.pdf).
- [LFCS13] Barthe, G., Crespo, J. M., Kunz, C. (2013). *Beyond 2-Safety: Asymmetric Product Programs for Relational Program Verification*. LFCS 2013, LNCS, 29–43. https://doi.org/10.1007/978-3-642-35722-0_3. Crossref. Read: full (author PDF, https://software.imdea.org/~jmcrespo/docs/LFCS2013.pdf).
- [JLAMP16] Barthe, G., Crespo, J. M., Kunz, C. (2016). *Product programs and relational program logics*. JLAMP 85(5), 847–859. https://doi.org/10.1016/j.jlamp.2016.05.004. Crossref. Read: metadata; content **unverified** (publisher 403).
- [LICS21] Nagasamudram, R., Naumann, D. A. (2021). *Alignment Completeness for Relational Hoare Logics*. LICS 2021, 1–13. https://doi.org/10.1109/LICS52264.2021.9470690. Crossref; arXiv:2101.11730. Read: partial (§I–IV).
- [LMCS25] Nagasamudram, R., Banerjee, A., Naumann, D. A. (2025). *Alignment complete relational Hoare logics for some and all*. LMCS 21(4). arXiv:2307.10045 (journal reference on the record). Read: abstract.
- [BiKAT23] Antonopoulos, T., Koskinen, E., Le, T. C., Nagasamudram, R., Naumann, D. A., Ngo, M. (2023). *An Algebra of Alignment for Relational Verification*. PACMPL 7(POPL), 573–603. https://doi.org/10.1145/3571213. Crossref; arXiv:2202.04278v4. Read: partial (§1, §7.1–7.2, §8.2).
- [WhyRel23] Nagasamudram, R., Banerjee, A., Naumann, D. A. (2023). *The WhyRel Prototype for Modular Relational Verification of Pointer Programs*. TACAS 2023, LNCS, 133–151. https://doi.org/10.1007/978-3-031-30820-8_11. Crossref; arXiv:2303.14314 (titled "The WhyRel Prototype for Relational Verification"). Read: partial (§2–5).
- [MPP18] Eilers, M., Müller, P., Hitz, S. (2018). *Modular Product Programs*. ESOP 2018, LNCS, 502–529. https://doi.org/10.1007/978-3-319-89884-1_18. Crossref. Read: abstract (via OpenAlex).

**Regression verification and equivalence checking**
- [GS08] Godlin, B., Strichman, O. (2008). *Inference rules for proving the equivalence of recursive procedures*. Acta Informatica 45(6), 403–439. https://doi.org/10.1007/s00236-008-0075-2. Crossref. Read: metadata; rule as described in [SS22]; content **unverified**.
- [GS09] Godlin, B., Strichman, O. (2009). *Regression verification*. DAC 2009, 466–471. https://doi.org/10.1145/1629911.1630034. Crossref. Read: abstract (via OpenAlex).
- [GS13] Godlin, B., Strichman, O. (2013). *Regression verification: proving the equivalence of similar programs*. STVR 23(3), 241–258 (online 2012). https://doi.org/10.1002/stvr.1472. Crossref. Read: abstract (via OpenAlex).
- [SV16] Strichman, O., Veitsman, M. (2016). *Regression Verification for Unbalanced Recursive Functions*. FM 2016, LNCS, 645–658. https://doi.org/10.1007/978-3-319-48989-6_39. Crossref. Read: metadata; content as described in [SS22]; **unverified** directly.
- [SS22] Sayedoff, C. R. J., Strichman, O. (2022). *Regression verification of unbalanced recursive functions with multiple calls (long version)*. arXiv:2207.14364 (long version of a VSTTE 2022 submission). Read: partial (§1–2).
- [REVE14] Felsing, D., Grebing, S., Klebanov, V., Rümmer, P., Ulbrich, M. (2014). *Automating regression verification*. ASE 2014, 349–360. https://doi.org/10.1145/2642937.2642987. Crossref. Read: full (https://formal.kastel.kit.edu/improve/pubs/ase2014.pdf).
- [LLRÊVE18] Kiefer, M., Klebanov, V., Ulbrich, M. (2018). *Relational Program Reasoning Using Compiler IR*. JAR 60(3), 337–363 (online 2017). https://doi.org/10.1007/s10817-017-9433-5. Crossref. Read: partial, accepted manuscript (§4, §6; https://formal.kastel.kit.edu/~ulbrich/pdf/JAR2017.pdf).
- [DDEC13] Sharma, R., Schkufza, E., Churchill, B., Aiken, A. (2013). *Data-driven equivalence checking*. OOPSLA 2013, 391–406. https://doi.org/10.1145/2509136.2509509. Crossref. Read: partial (abstract, §1; https://theory.stanford.edu/~aiken/publications/papers/oopsla13b.pdf).
- [SPA19] Churchill, B., Padon, O., Sharma, R., Aiken, A. (2019). *Semantic program alignment for equivalence checking*. PLDI 2019, 1027–1040. https://doi.org/10.1145/3314221.3314596. Crossref. Read: full (https://theory.stanford.edu/~aiken/publications/papers/pldi19.pdf).
- [Pequod19] Zhou, Q., Heath, D., Harris, W. (2019). *Relational Verification via Invariant-Guided Synchronization*. HCVS/PERR 2019, EPTCS 296, 28–41. https://doi.org/10.4204/EPTCS.296.6. Crossref; arXiv:1907.03997. Read: abstract.
- [Counter20] Gupta, S., Rose, A., Bansal, S. (2020). *Counterexample-guided correlation algorithm for translation validation*. PACMPL 4(OOPSLA), 1–29. https://doi.org/10.1145/3428289. Crossref. Read: abstract (SPLASH 2020 page); results **unverified** (ACM 403).
- [RoseBansal24] Rose, A., Bansal, S. (2024). *Modeling Dynamic (De)Allocations of Local Memory for Translation Validation*. PACMPL 8(OOPSLA1), 1463–1492. https://doi.org/10.1145/3649863. Crossref; arXiv:2403.05302. Read: abstract.
- [EqBench21] Badihi, S., Li, Y., Rubin, J. (2021). *EqBench: A Dataset of Equivalent and Non-equivalent Program Pairs*. MSR 2021, 610–614. https://doi.org/10.1109/MSR52588.2021.00084. Crossref. Read: partial (author PDF). Dataset behind [Contracts26]: 147 equivalent, 125 non-equivalent pairs.

**Self-composition and scheduler inference (k-safety)**
- [PDSC19] Shemer, R., Gurfinkel, A., Shoham, S., Vizel, Y. (2019). *Property Directed Self Composition*. CAV 2019, LNCS, 161–179. https://doi.org/10.1007/978-3-030-25540-4_9. Crossref; arXiv:1905.07705v2. Read: partial (§3, §5).
- [PCSat21] Unno, H., Terauchi, T., Koskinen, E. (2021). *Constraint-Based Relational Verification*. CAV 2021, LNCS, 742–766. https://doi.org/10.1007/978-3-030-81685-8_35. Crossref; arXiv:2106.02628. Read: partial (§1–2, §4.1, §6).
- [Weaver19] Farzan, A., Vandikas, A. (2019). *Automated Hypersafety Verification*. CAV 2019, LNCS, 200–218. https://doi.org/10.1007/978-3-030-25540-4_11. Crossref; arXiv:1905.09242 (titled "Reductions for Automated Hypersafety Verification"). Read: abstract.
- [Synonym18] Pick, L., Fedyukovich, G., Gupta, A. (2018). *Exploiting Synchrony and Symmetry in Relational Verification*. CAV 2018, LNCS, 164–182. https://doi.org/10.1007/978-3-319-96145-3_9. Crossref. Read: abstract (via OpenAlex).
- [CHL16] Sousa, M., Dillig, I. (2016). *Cartesian Hoare Logic for Verifying k-Safety Properties*. PLDI 2016, 57–69. https://doi.org/10.1145/2908080.2908092. Crossref. Read: abstract (via OpenAlex).

**For-all-exists**
- [HyPA22] Beutner, R., Finkbeiner, B. (2022). *Software Verification of Hyperproperties Beyond k-Safety*. CAV 2022, LNCS, 341–362. https://doi.org/10.1007/978-3-031-13185-1_17. Crossref; arXiv:2206.03381v2. Read: partial (§1–2, §7–8).
- [Proph22] Beutner, R., Finkbeiner, B. (2022). *Prophecy Variables for Hyperproperty Verification*. CSF 2022, 471–485. https://doi.org/10.1109/CSF54842.2022.9919658. Crossref; arXiv:2206.01797. Read: abstract.
- [HyLive24] Beutner, R. (2024). *Automated Software Verification of Hyperliveness*. TACAS 2024, LNCS, 196–216. https://doi.org/10.1007/978-3-031-57249-4_10. Crossref (abstract deposited). Read: abstract.
- [HyHorn24] Itzhaky, S., Shoham, S., Vizel, Y. (2024). *Hyperproperty Verification as CHC Satisfiability*. ESOP 2024, LNCS, 212–241. https://doi.org/10.1007/978-3-031-57267-8_9. Crossref; arXiv:2304.12588v2. Read: partial (§1–2, §7).
- [RHLE22] Dickerson, R., Ye, Q., Zhang, M. K., Delaware, B. (2022). *RHLE: Modular Deductive Verification of Relational ∀∃ Properties*. APLAS 2022, LNCS, 67–87. https://doi.org/10.1007/978-3-031-21037-2_4. Crossref; arXiv:2002.02904. Read: abstract.
- [Ghost20] Clochard, M., Marché, C., Paskevich, A. (2020). *Deductive verification with ghost monitors*. PACMPL 4(POPL), 1–26. https://doi.org/10.1145/3371070. Crossref. Read: abstract (POPL 2020 page); its ∀∃ use in Why3 as described by [BiKAT23 §8].
- [Abadi91] Abadi, M., Lamport, L. (1991). *The existence of refinement mappings*. TCS 82(2), 253–284. https://doi.org/10.1016/0304-3975(91)90224-P. Crossref. Read: abstract and contents of the 1988 DEC SRC report version (https://lamport.azurewebsites.net/pubs/abadi-existence.pdf).
- [Chaki12] Chaki, S., Gurfinkel, A., Strichman, O. (2012). *Regression Verification for Multi-threaded Programs*. VMCAI 2012, LNCS 7148, 119–135. https://doi.org/10.1007/978-3-642-27940-9_9. Crossref. Read: abstract (https://cris.iucc.ac.il/en/publications/regression-verification-for-multi-threaded-programs/).
- [Chaki15] Chaki, S., Gurfinkel, A., Strichman, O. (2015). *Regression verification for multi-threaded programs (with extensions to locks and dynamic thread creation)*. FMSD. https://doi.org/10.1007/s10703-015-0237-0. Crossref. Read: metadata; content **unverified**.

**Frama-C relational tooling**
- [RPP17] Blatter, L., Kosmatov, N., Le Gall, P., Prevosto, V. (2017). *RPP: Automatic Proof of Relational Properties by Self-composition*. TACAS 2017, LNCS, 391–397. https://doi.org/10.1007/978-3-662-54577-5_22. Crossref; arXiv:1606.00678. Read: metadata.
- [RPP18] Blatter, L., Kosmatov, N., Le Gall, P., Prevosto, V., Petiot, G. (2018). *Static and Dynamic Verification of Relational Properties on Self-composed C Code*. TAP 2018, LNCS, 44–62. https://doi.org/10.1007/978-3-319-92994-1_3. Crossref; arXiv:1801.06876v2. Read: partial (§1, §7).
- [CertRel22] Blatter, L., Kosmatov, N., Prevosto, V., Le Gall, P. (2022). *Certified Verification of Relational Properties*. iFM 2022, LNCS, 86–105. https://doi.org/10.1007/978-3-031-07727-2_6. Crossref; arXiv:2202.10349v3. Read: abstract.

**LLM work (2024–2026)**
- [Trivet26] Liao, C., Xu, H., Zhou, X., Zhang, Y., Sun, C. (2026). *LLVM Translation Validation Automated with Large Language Models and Lean*. arXiv:2609.19583 (preprint). Read: partial (arXiv HTML to ~88%; §3.3, §4.1, §4.4–4.5).
- [LLMLift24] Bhatia, S., Qiu, J., Hasabnis, N., Seshia, S. A., Cheung, A. (2024). *Verified Code Transpilation with LLMs*. NeurIPS 2024. https://proceedings.neurips.cc/paper_files/paper/2024/file/48bb60a0c0aebb4142bf314bd1a5c6a0-Paper-Conference.pdf. Read: partial (§2–3).
- [Contracts26] Charalambous, Y., Menezes, R., Sun, Y., Cordeiro, L. C. (2026). *Partial Contracts Suffice: Sound, LLM-Inferred Regression Verification*. arXiv:2607.10291 (preprint). Read: partial (§I–II, §V).
- [LLMVec25] Taneja, J., Laird, A., Yan, C., Musuvathi, M., Lahiri, S. K. (2025). *LLM-Vectorizer: LLM-Based Verified Loop Vectorizer*. CGO 2025, 137–149. https://doi.org/10.1145/3696443.3708929. Crossref; arXiv:2406.04693. Read: abstract.
- [WangXie24] Wang, Y., Xie, F. (2024). *Enhancing Translation Validation of Compiler Transformations with Large Language Models*. IJSEKE (online 2024), 45–57. https://doi.org/10.1142/S0218194024500475. Crossref; arXiv:2401.16797. Read: abstract.
- [EquiBench25] Wei, A., Cao, J., Li, R., Chen, H., Zhang, Y., Wang, Z., Liu, Y., Teixeira, T. S. F. X., Yang, D., Wang, K., Aiken, A. (2025). *EquiBench: Benchmarking Large Language Models' Reasoning about Program Semantics via Equivalence Checking*. EMNLP 2025, 33856–33869. https://doi.org/10.18653/v1/2025.emnlp-main.1718. Crossref; arXiv:2502.12466v3. Read: abstract.
- [ProofWright25] Chatterjee, B., Zagieboylo, D., Damani, S., Hari, S., Kozyrakis, C. (2025, v2 2026). *ProofWright: Towards Agentic Formal Verification of CUDA*. arXiv:2511.12294 (preprint; venue unconfirmed). Read: abstract.
- [SelfPlay26] Miceli Barone, A. V., Poon, T. N. (2026). *Improving LLM Code Reasoning via Semantic Equivalence Self-Play with Formal Verification*. arXiv:2604.17010 (preprint). Read: abstract.

**Local sources:** [`13-wp-hint-facts.md`](13-wp-hint-facts.md) (Q1 ghost code, Q3 clause
kinds, Q4 statuses, Q6 smoke tests, Q7 variants);
[`../issues/13-proof-hint-loop.md`](../issues/13-proof-hint-loop.md) items 5, 7, 12;
[`../issues/11-verifier-choice.md`](../issues/11-verifier-choice.md) items 5, 10;
[`../issues/17-enabling-rewrites.md`](../issues/17-enabling-rewrites.md) items 2, 4;
[`03-prove-once-rewrite-rules.md`](03-prove-once-rewrite-rules.md) lines 23–28, 49–53, 185–201.
