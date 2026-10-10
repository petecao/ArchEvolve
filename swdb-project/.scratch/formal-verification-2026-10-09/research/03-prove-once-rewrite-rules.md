# 03 — Prove a rewrite contract once, or validate each application?

Created: 2026-10-09 14:16 ET
**Ticket:** [`../issues/03-prove-once-rewrite-rules.md`](../issues/03-prove-once-rewrite-rules.md) · **Map:** [`../map.md`](../map.md)
**Feeds:** ticket 09 (what "proven" asserts) and ticket 10 (what a proven rewrite contract proves once).

---

## TL;DR

- **Prior work has two camps:** prove a rewrite rule once and trust every application (Cobalt,
  Rhodium, PEC, Alive, Lean-MLIR), or check each application separately (translation
  validation: Pnueli, Necula, Alive2, MLIR validators, HEC). PEC itself recommends a **staged
  mix**: prove once whatever you can, and validate the rest per application.
- **A pure prove-once rule does not fit LLM-written candidates.** It is sound only when the code
  is a literal instance of the rule's template. PEC trusts its pattern matcher, and Alive's
  generated C++ fires only after a syntactic match. Free-form code from an LLM is not a template
  instance, and a bug like the wrong-tile wait would only fail to match, not be refuted.
- **Pure per-application validation does not scale.** It is the shape of Extensa's
  whole-benchmark gates. Alive2 stays practical only by working per function and unrolling
  loops to a bound. LLM-Vectorizer ran Alive2 on each LLM-written loop and verified 38.2% of
  TSVC vectorizations.
- **Different outputs are a solved pattern.** Prior work replaces equality with **refinement**:
  the new code may show only behaviors the old code could show (CompCert, Alive, Alive2), or
  equality **modulo a relation or abstraction** (bridge predicates, acceptability relations).
  When the baseline is itself nondeterministic, the right form is ∀∃ (asymmetric product
  programs). For BFS the abstraction is deterministic: the visited set and the per-level
  frontier *sets* are unique. Only the parent choice and the queue order vary.

## Recommendation for our case

**Shape: a staged hybrid. Prove once the parts of a rewrite contract that every candidate
shares. For each candidate artifact, run one small relational proof that reuses those parts.**

| | What | Prior-work model |
|---|---|---|
| **Proven once, per contract** | (1) **Building blocks:** each intrinsic lowering and library operation refines its reference semantics (DX100 functional model). Each becomes a summary. | Godlin–Strichman: callees already proven are abstracted as uninterpreted functions |
| | (2) **Contract lemmas:** formal halves that mention only the contract's own machinery, e.g. L1 (the range-loop continuation emits exactly the nested CSR vertex pairs), for all graphs and all knob values in range. | PEC parameterized rules with symbolic parameters |
| | (3) **Relational template:** the product-program skeleton, the alignment (baseline frontier position *i* ↔ candidate chunk *k*, slot *j*, with *i = k·chunk_size + j*), and a coupling invariant built from `once_enqueue` and the output relation below. | Product programs (Barthe); coupling predicates (REVE) |
| **Per candidate artifact** | (a) **Proof unit:** one `TDStep` call. Product of baseline and candidate `TDStep`. Building blocks replaced by their summaries. | Alive2 and Necula work per function or per pass, never whole-program |
| | (b) **Relation:** candidate refines baseline modulo α. α = equal visited set and equal next-frontier set, every newly claimed `parent[v]` is a valid parent (in-neighbor at depth d−1), and each vertex is enqueued once. | Refinement modulo an abstraction |
| | (c) **Side conditions:** knob ranges and count guards stay runtime guards with fallback, or static assertions (already in `bfs_read_offload.yaml`). | Zuck et al. run-time validation; Alive preconditions |
| | (d) **Proof hints:** the LLM agent adds only candidate-specific invariants on top of the contract's coupling invariant. | Crellvm and PCC: the producer emits a certificate, a checker checks it |
| | (e) **Verdict:** proven unbounded if the coupling invariant is inductive for a symbolic graph. Otherwise proven within bounds, recording \|V\|, \|E\|, chunk_size and the unroll depth. | Alive (≤64-bit widths), Alive2 (loop unroll bound) |

**Why this stays small where Extensa's gates did not:**

1. The unit is one changed region, not a whole benchmark.
2. Loops inside intrinsics and library operations disappear behind proven summaries. Godlin and
   Strichman's tool gets loop-free, recursion-free verification conditions this way.
3. The hardest part of a relational proof is finding the alignment and the coupling invariant.
   REVE infers it with Horn solvers; Churchill et al. infer the alignment from concrete runs.
   We write it **once in the contract** instead of searching for it for each candidate. This
   is our synthesis, not a claim from any one paper.
4. When the unbounded proof stalls, a bounded verdict with recorded bounds is still a result.

**Fast path (optional):** candidates that use the contract's library code verbatim
(Peter's `bfs_read_offload.inc`) could get a PEC-style check: match the template, then check the
side conditions. Candidates that deviate, such as Codex's frontier staging, take the relational
path. This is PEC's staged paradigm (PEC §2.3).

---

## Approaches at a glance

| Shape | Proven once | Per-instance check | Data-dependent loops (BFS frontier) | Memory restructuring (tiles, staging) | Accelerator offload | Legitimately different outputs | Examples |
|---|---|---|---|---|---|---|---|
| **A. Proven parameterized rewrite** | The rule: template + side conditions | Trusted syntactic match + side-condition check | Only with opaque loop bodies and "commute" facts. A CAS race breaks state equality. | Index shifts (`S[I+1]`) yes; staging buffers not shown | Intrinsics would need axioms; not shown in these papers | PEC: state equality. Alive: refinement. | Cobalt, Rhodium, PEC, Alive, Lean-MLIR |
| **B. Per-instance translation validation** | Nothing; the validator is trusted | Full equivalence or refinement proof of the (old, new) pair | Bounded unrolling (Alive2) or an inferred simulation relation (Necula) | Yes for affine code (HEC tiling, fusion) | Yes, given a semantics: mlir-tv, Melchert et al., Kundu et al. (HLS) | Refinement (Alive2, MLIR validators) | Pnueli, Necula, Alive2, mlir-tv, HEC, LLM-Vectorizer |
| **C. Proven checker** | The checker (validator) itself, in Coq | Run the checker, optionally on a producer-emitted proof | Per validator (Tristan–Leroy software pipelining) | Not covered by these sources | Not covered by these sources | Behavior inclusion (CompCert) | Tristan–Leroy, CompCert, Crellvm, PCC |
| **D. Relational proof with proven-once parts** | Equivalence of callees, as summaries | Product-program or coupling proof of the changed region | Yes, *if* a coupling invariant is found or supplied | Yes, via array coupling invariants | Building blocks as summaries | Equality modulo a relation; ∀∃ for nondeterministic baselines | Godlin–Strichman, REVE, Barthe products, CoVaC, DDEC, Churchill et al. |
| **E. Spec-direct** | Nothing relational | Prove the candidate meets the kernel's postcondition | Needs full functional loop invariants (hard) | n/a | n/a | Natural: any valid output passes | CompCert "spec preservation" framing, certifying algorithms, Graph500 / `BFSVerifier` |
| **F. Static + run-time validation** | Static legality rules | Run-time test, with recovery on failure | Yes: data-dependent legality is checked at run time | PolyCheck: affine only | Not covered by these sources | Not covered by these sources | Zuck et al. 2005, PolyCheck |

**Our recommendation = D, with A's fast path and F's runtime guards.** The kernel spec (E) stays
the testing-level correctness check (`BFSVerifier`) and can become a proof target later.

---

## Detail

### 1. Prove the rule once (shape A)

- **Cobalt** (PLDI 2003) writes optimizations as guarded rewrite rules over a C-like IR. The
  Simplify prover discharges a few small obligations per rule, automatically. The rules cover
  constant propagation, redundancy elimination, dead assignment elimination and simple
  points-to. The checker caught "many subtle bugs" during development.
- **Rhodium** (POPL 2005) recasts rules as dataflow facts with local propagation and rewrite
  rules. It proves Cobalt's rules plus Andersen points-to and redundant array load elimination.
  Both systems handle only single-statement rewrites (PEC §1).
- **PEC** (PLDI 2009) is the closest model for a rewrite contract (full text read):
  - Rules are `P1 ⇒ P2 where φ`. P1 and P2 are *parameterized programs* with meta-variables for
    statements (S), expressions (E) and variables (I). φ is a side condition built from facts
    such as `DoesNotModify(S, I)` and `Commute(S1, S2)`, each with a semantic meaning (§2.1).
  - Many-to-many rewrites cover software pipelining, loop unswitching, unrolling, peeling,
    splitting, interchange, reversal, skewing, fusion and distribution. Reordering rules go
    through a *Permute* module adapted from Zuck et al. (§6).
  - **The relation is state equality:** `π1(σ) = π2(σ)` for every start state (Def. 1), proven
    with a bisimulation. It has no slack for a different parent.
  - **The trusted base at application time:** "the syntactic pattern matching … is always
    trusted". Side-condition analyses are either trusted or implemented in a provably safe
    system such as Rhodium (§7).
  - **Cost:** 1–16 s and 3–94 prover calls per rule (Fig. 11).
  - **Staged paradigm:** "use PEC to check as many of the optimizations as possible before they
    are run. For those … we can't prove correct once and for all, we can use PEC again … to
    perform translation validation on the concrete input/output pairs" (§2.3).
- **Alive** (PLDI 2015; CACM 2018 version read):
  - A rule is `source template ⇒ target template` with a precondition. It is checked for every
    feasible type assignment, with "an upper bound of 64 bits" for implicit integer widths. So a
    rule proof is itself *bounded* (§2.2).
  - Precondition predicates come from LLVM dataflow analyses that are "trusted by Alive:
    verifying their correctness is not within Alive's scope" (§2.3).
  - Templates may not jump backward, so there are no loops.
  - Correctness is refinement, with ∀∃ quantifiers over `undef` values (§3.2).
  - At application time, the generated C++ does a pattern match plus a precondition check (§4).
- **Lean-MLIR** (ITP 2024) proves rewrites in Lean over a generic SSA calculus. Its framework
  proves that "lifting a peephole rewrite to a rewrite on the entire program preserves
  semantics" (§1, contributions). This is the cleanest statement of "prove the rule once,
  apply it anywhere".

**Lesson for us:** shape A's per-application cost is near zero, but only because applying a
rule is a trusted syntactic match. An LLM candidate is not produced by the matcher, so shape A
applies to us only on the fast path.

### 2. Validate each application (shape B)

- **Pnueli, Siegel, Singerman** (TACAS 1998) coined translation validation. After each compiler
  run, check that the target code correctly implements the source, with "correct
  implementation" defined as a refinement relation. Their motivation: a once-and-for-all
  compiler proof must be redone after every compiler change.
- **Necula** (PLDI 2000) validated GCC pass by pass. It inferred a simulation relation from
  constraints, with heuristics instead of help from the compiler.
- **Alive2** (PLDI 2021) does bounded translation validation of LLVM functions. It "unroll[s]
  loops up to a given bound" and limits time and memory, so it can miss bugs but avoids false
  alarms. It found 47 new bugs, 28 of them fixed. On nondeterminism: "Refinement allows a
  transformation to remove non-determinism, but not to add it."
- **MLIR validators:**
  - mlir-tv (CAV 2022) over-approximates FP arithmetic and refines that abstraction when a
    check fails.
  - Wang et al. (IJSEKE 2024) check refinement between MLIR programs with Z3.
  - Fehr et al. (PLDI 2025) give dialects their semantics as a lowering into SMT dialects.
    They found 5 miscompilations and verified one canonicalization pass.
- **HEC** (USENIX ATC 2025) checks each program pair with e-graphs over MLIR (affine dialect):
  - Static datapath rules are *assumed* correct. Per-program dynamic rules for unrolling,
    tiling and fusion have their conditions checked by Z3.
  - It processes 100k+ lines of MLIR in 40 minutes and found 2 mlir-opt bugs.
  - No support for indirect indexing is described.
- **LLM-Vectorizer** (CGO 2025) is the nearest LLM case. LLM agents vectorize loops, and Alive2
  checks each result. Even with domain-specific scalability techniques, 38.2% of TSVC
  vectorizations were verified.

**Lesson for us:** per-instance validation is what Extensa tried. It works per function, with
bounds, and on IR. It does not scale to a whole benchmark.

### 3. Prove the checker once (shape C)

- **Leroy's framing** (CACM 2009, read §2):
  - A verified validator with the property `Validate(S,C)=true ⇒ S≈C`, run after an unverified
    pass, gives guarantees "as strong as those provided by a verified compiler".
  - Validators "are necessarily incomplete and should reply false if they cannot establish
    S≈C".
  - CompCert chooses per pass between a proven pass and an unproven pass plus a verified
    validator; lazy code motion uses the validator route.
- **Tristan and Leroy** proved validators for list and trace scheduling (POPL 2008), lazy code
  motion (PLDI 2009) and software pipelining (POPL 2010).
- **Crellvm** (PLDI 2018): each LLVM pass emits a proof for each translation, and a
  Coq-verified checker checks it. It found 4 bugs in mem2reg and gvn.
- **Proof-carrying code** (POPL 1997): the producer ships a certificate, and only the
  client-side checker is trusted.

**Lesson for us:** this is the right model for **proof hints**. The LLM agent is the
untrusted producer, its hints are the certificate, and the formal verifier is the checker.
It is not a model for what a contract proves once.

### 4. Relational proof with proven-once parts (shape D)

- **Regression verification** (Godlin and Strichman, DAC 2009; STVR 2013):
  - It proves partial equivalence of two similar programs function pair by function pair.
  - Callees already proven equivalent become uninterpreted functions, and loops become
    recursion. This yields loop-free, recursion-free verification conditions.
  - It works well when the two sides run in lockstep and tends to fail otherwise (per
    Strichman's later work on unbalanced recursion).
  - Chaki, Gurfinkel and Strichman (VMCAI 2012) extend it to multi-threaded programs. This is
    relevant to our concurrency phase; read at title level only.
- **REVE** (Felsing et al., ASE 2014) turns equivalence into Horn constraints with placeholder
  coupling predicates. A Horn solver *infers* the coupling predicate, so the user writes no
  invariants. Kiefer et al. (JAR 2018) bring this to compiler IR.
- **Product programs** (Barthe, Crespo, Kunz):
  - FM 2011 reduces a relational property to an ordinary Hoare proof of one combined program.
    Its examples include loop optimizations.
  - LFCS 2013 *asymmetric* products handle nondeterministic programs and ∀∃ refinement. They
    also cover loop optimizations the 2011 version could not.
- **CoVaC** (Zaks and Pnueli, FM 2008) analyzes the cross-product of source and target with
  standard program analysis. It targets "consonant" (structurally similar) programs.
- **Data-driven alignment:** DDEC (OOPSLA 2013) and Churchill et al. (PLDI 2019) learn an
  alignment from concrete runs and build a product program from it. They verified glibc's
  vectorized `strlen` and vectorization of 56 TSVC benchmarks.

**Lesson for us:** shape D handles data-dependent loops, but someone must supply the alignment
and the coupling invariant. Tools either infer them, which is where they stall, or require them
from the user. **A rewrite contract is the natural place to write them once.**

### 5. Loop-restructuring validators

- **Zuck et al.** (FMSD 2005) validate distribution, fusion, tiling and interchange with
  permutation rules. They add **run-time validation** for loop rewrites whose legality cannot
  be decided at compile time, including recovery without aborting the program. This is the
  prior-work model for our `runtime_guard` discharge mode with its whole-call fallback.
- **PolyCheck** (POPL 2016) generates lightweight checker code at compile time that runs inside
  the transformed program. It covers iteration reordering on affine programs only.
- **HEC** (above) and Courant and Leroy (POPL 2021, verified polyhedral code generation) are
  likewise affine.

**Lesson for us:** the polyhedral and affine methods cannot express a BFS frontier, whose loop
bounds come from `offsets[queue[i]]`. Only shapes B (bounded), D and F reach it.

### 6. Accelerator offload

- No source found proves a rule once for offload to an accelerator. The prior work is
  per-instance validation against a hardware semantics:
  - Kundu, Lerner, Gupta (CAV 2008) validate each translation of the SPARK high-level
    synthesis tool against the input C.
  - Melchert et al. (FMCAD 2025) validate a compiler for statically scheduled accelerators
    using symbolic models of each stage and of the hardware.
  - Vericert (OOPSLA 2021) is the prove-once counterpart for high-level synthesis.
- The MLIR validators show the general recipe: give each operation a semantics, as an SMT
  encoding (mlir-tv) or a lowering to an SMT dialect (Fehr et al.), then validate against it.

**Lesson for us:** any shape needs the DX100 strict layer as the semantics of each intrinsic
(ticket 01, decision 10). Proving each intrinsic lowering against `dx100/reference.hpp` **once**
and reusing it as a summary is a genuine prove-once win. The protocol side (L5, `dropped_wait`,
`read_before_wait`) needs that semantics to make a read before its wait return an arbitrary
value, so that a missing wait is refuted. That is ticket 05/12 territory.

### 7. Legitimately different outputs

| Technique | What it says | Source |
|---|---|---|
| **Refinement (behavior inclusion)** | All observable behaviors of the new code are acceptable behaviors of the old. Needs the *old* code to be nondeterministic. | CompCert property (2) (Leroy CACM §2.1); Alive §3; Alive2 §1 |
| **Spec preservation** | If the old code meets spec, so does the new. Proving refinement once "spares us from establishing [this] for every specification". | Leroy CACM §2.1, property (4) |
| **Equality modulo a relation** | Determinism or equivalence judged by a programmer-given *bridge predicate* on output states, or a relational *acceptability* property between the original and relaxed program. | Burnim and Sen (FSE 2009); Carbin et al. (PLDI 2012) |
| **∀∃ relational** | For every run of the new program there exists a run of the old one with the same observation. | Barthe et al. asymmetric products (LFCS 2013); Antonopoulos et al. (POPL 2023, title-level) |
| **Output checker** | Check the result itself, not its relation to a baseline. | Certifying algorithms (McConnell et al. 2011); Graph500 BFS validation |

**For BFS:**

- `BFSVerifier` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:463`) checks the following:
  - `parent[source] = source`;
  - each `parent[v]` is an in-neighbor at depth d−1;
  - reachability matches a serial BFS.
- Graph500 checks the same kind of properties. It accepts any algorithm "as long as it produces
  a correct BFS tree as output".
- **Proposed α:** visited set, per-vertex depth (equivalently, the per-level frontier *sets*),
  and validity of each new parent.
- **Our reasoning, not a cited result:**
  - Under OpenMP, every in-neighbor at depth d−1 is in frontier d−1 and attempts the CAS on v,
    so each of them can win under some interleaving.
  - So "same α + valid parent" equals ∀∃ refinement of the multi-threaded baseline. We get it
    without modeling the baseline's interleavings.
- **Stronger than today's check:** the formal relation can compare frontier *sets*. The
  runtime correctness check compares only frontier *sizes*.
- **Extensa comparison:** Extensa's output-equivalence lattice has no element for "valid but
  different". Its `order_dependent_observation_only` appears to cover order-sensitive
  accumulated values (our reading of MemAcc registry uses). The relation above would be a new
  element: **equality modulo α plus a validity predicate**.

---

## Findings that challenge or sharpen ticket 01

1. **Decision 2(a), "contracts proven once, reused by every candidate":** in its pure form this
   needs candidates that are template instances, with a trusted matcher (PEC §7; Alive §4). LLM
   candidates are not. **Sharpen the claim:** the contract's building blocks, lemmas and
   relational template are proven once; each candidate gets a small relational proof that
   reuses them. PEC's own staged paradigm supports this reading. It is a refinement of the
   decision, not a reversal.
2. **Decision 9.1, the wrong-tile wait must be refuted:** a match-based check can only say "not
   an instance". Refutation needs a semantic per-instance check. This is a second argument for
   shape D over shape A.
3. **Decision 8, "never assume":** this decision is about proof hints, and it stands. But every
   prove-once system trusts something when a rule is applied: Alive trusts its analysis
   predicates, and PEC trusts its matcher and possibly its side-condition analyses. Our
   contract has L3 and L5 with `discharge_mode: assumed`. **A proven verdict is therefore
   conditional on the assumed clauses plus the reference semantics.** Ticket 09 should make the
   proven level list that assumption set.
4. **Decision 6, bounded vs unbounded:** the most deployed systems are bounded. Alive checks
   widths up to 64 bits, and Alive2 unrolls loops. This supports keeping "proven within
   bounds" as a first-class level. It also means a contract lemma proven by bounded model
   checking is "proven within bounds" too, and must record its bounds.
5. **Proof unit (ticket 09):** every scalable system works per function, per pass or per
   function pair, never on the whole program. This supports one `TDStep` call as the unit.

## Open questions

- **Codex's frontier staging:** does it reorder frontier work? If so, a lockstep alignment
  breaks, and the coupling must be order-insensitive (set-based). Test this in the ticket 08
  prototype.
- **Fast-path matcher:** is a PEC-style template proof of Peter's `.inc` worth building, or does
  the relational path alone suffice for the proof of concept?
- **Formal halves of L2–L5:** which language lets the chosen verifier check them (map: "Not yet
  specified")? Ticket 02/11 must confirm the verifier can encode a product program with
  arrays and summaries.
- **Vacuity guard:** should each negative control be refuted by the relational check? PEC and
  Alive report bugs caught during rule development, which is the analog.
- **Concurrency phase:** regression verification for multi-threaded programs (Chaki et al.
  2012) and determinism checking (Vechev et al. 2010) were found only at title level. Read them
  before the concurrency tickets.

---

## Sources (annotated)

DOIs were resolved through doi.org (registered metadata matched title, authors, venue and
year). **Read scope** says how much of each source was read: *full* (full text), *partial*
(named sections), *abstract* (abstract, author page or index summary), or *title* (metadata
only; no claim beyond the title is made). Nothing below is unverified.

**Prove once**
- Lerner, S., Millstein, T., & Chambers, C. (2003). Automatically proving the correctness of compiler optimizations. *PLDI '03*, 220–231. https://doi.org/10.1145/781131.781156. Cobalt; guarded rewrite rules auto-proven with Simplify. *abstract*
- Lerner, S., Millstein, T., Rice, E., & Chambers, C. (2005). Automated soundness proofs for dataflow analyses and transformations via local rules. *POPL '05*, 364–377. https://doi.org/10.1145/1040305.1040335. Rhodium. *abstract*
- Kundu, S., Tatlock, Z., & Lerner, S. (2009). Proving optimizations correct using parameterized program equivalence. *PLDI '09*, 327–337. https://doi.org/10.1145/1542476.1542513. PEC; staged paradigm; trusted matcher; state equality. *full* (author PDF, cs.cornell.edu/~lerner/papers/pldi09-pec.pdf)
- Lopes, N. P., Menendez, D., Nagarakatte, S., & Regehr, J. (2015). Provably correct peephole optimizations with Alive. *PLDI '15*, 22–32. https://doi.org/10.1145/2737924.2737965. Facts taken from the CACM 2018 version (https://doi.org/10.1145/3166064). *partial* (CACM pp. 84–88)
- Bhat, S., Keizer, A., Hughes, C., Goens, A., & Grosser, T. (2024). Verifying peephole rewriting in SSA compiler IRs. *ITP 2024*, LIPIcs 309, 9:1–9:20. https://doi.org/10.4230/LIPIcs.ITP.2024.9. Lean-MLIR; whole-program lifting theorem. *partial* (abstract, §1)
- Mullen, E., Zuniga, D., Tatlock, Z., & Grossman, D. (2016). Verified peephole optimizations for CompCert. *PLDI '16*, 448–461. https://doi.org/10.1145/2908080.2908109. *title*
- Courant, N., & Leroy, X. (2021). Verified code generation for the polyhedral model. *PACMPL 5(POPL)*, 1–24. https://doi.org/10.1145/3434321. *title*

**Validate each application**
- Pnueli, A., Siegel, M., & Singerman, E. (1998). Translation validation. *TACAS '98*, LNCS 1384, 151–166. https://doi.org/10.1007/BFb0054170. *abstract*
- Necula, G. C. (2000). Translation validation for an optimizing compiler. *PLDI '00*, 83–94. https://doi.org/10.1145/349299.349314. *abstract*
- Lopes, N. P., Lee, J., Hur, C.-K., Liu, Z., & Regehr, J. (2021). Alive2: Bounded translation validation for LLVM. *PLDI '21*, 65–79. https://doi.org/10.1145/3453483.3454030. *partial* (pp. 1–2)
- Bang, S., Nam, S., Chun, I., Jhoo, H. Y., & Lee, J. (2022). SMT-based translation validation for machine learning compiler. *CAV 2022*, 386–407. https://doi.org/10.1007/978-3-031-13188-2_19. *abstract*
- Wang, Y., Xie, F., Yang, Z., Cocchini, P., & Yang, J. (2024). A systematic translation validation framework for MLIR-based compilers. *IJSEKE 34(10)*, 1621–1640. https://doi.org/10.1142/S021819402450030X. *abstract*
- Fehr, M., Fan, Y., Pompougnac, H., Regehr, J., & Grosser, T. (2025). First-class verification dialects for MLIR. *PACMPL 9(PLDI)*, 1466–1490. https://doi.org/10.1145/3729309. *abstract*
- Yin, J., Song, Z., Bohm Agostini, N., Tumeo, A., & Yu, C. (2025). HEC: Equivalence verification checking for code transformation via equality saturation. *USENIX ATC '25*, 1181–1196. https://www.usenix.org/conference/atc25/presentation/yin (arXiv 2506.02290). *partial* (arXiv HTML, first ~100k chars)
- Tate, R., Stepp, M., Tatlock, Z., & Lerner, S. (2009). Equality saturation: A new approach to optimization. *POPL '09*, 264–276. https://doi.org/10.1145/1480881.1480915. *title*
- Stepp, M., Tate, R., & Lerner, S. (2011). Equality-based translation validator for LLVM. *CAV 2011*, 737–742. https://doi.org/10.1007/978-3-642-22110-1_59. *title*
- Taneja, J., Laird, A., Yan, C., Musuvathi, M., & Lahiri, S. K. (2025). LLM-Vectorizer: LLM-based verified loop vectorizer. *CGO '25*, 137–149. https://doi.org/10.1145/3696443.3708929. *abstract*

**Prove the checker once**
- Leroy, X. (2009). Formal verification of a realistic compiler. *CACM 52(7)*, 107–115. https://doi.org/10.1145/1538788.1538814. Behavior inclusion; spec preservation; verified validators. *partial* (§2–3.2)
- Leroy, X. (2006). Formal certification of a compiler back-end or: Programming a compiler with a proof assistant. *POPL '06*, 42–54. https://doi.org/10.1145/1111037.1111042. *title*
- Tristan, J.-B., & Leroy, X. (2008). Formal verification of translation validators: A case study on instruction scheduling optimizations. *POPL '08*, 17–27. https://doi.org/10.1145/1328438.1328444. *abstract*
- Tristan, J.-B., & Leroy, X. (2009). Verified validation of lazy code motion. *PLDI '09*, 316–326. https://doi.org/10.1145/1542476.1542512. *title*
- Tristan, J.-B., & Leroy, X. (2010). A simple, verified validator for software pipelining. *POPL '10*, 83–92. https://doi.org/10.1145/1706299.1706311. *title*
- Kang, J., Kim, Y., Song, Y., Lee, J., Park, S., Shin, M. D., Kim, Y., Cho, S., Choi, J., Hur, C.-K., & Yi, K. (2018). Crellvm: Verified credible compilation for LLVM. *PLDI '18*, 631–645. https://doi.org/10.1145/3192366.3192377. *abstract*
- Necula, G. C. (1997). Proof-carrying code. *POPL '97*, 106–119. https://doi.org/10.1145/263699.263712. Described via Leroy CACM §2.2. *title*

**Relational verification**
- Godlin, B., & Strichman, O. (2009). Regression verification. *DAC '09*, 466–471. https://doi.org/10.1145/1629911.1630034. *abstract*
- Godlin, B., & Strichman, O. (2013). Regression verification: Proving the equivalence of similar programs. *STVR 23(3)*, 241–258. https://doi.org/10.1002/stvr.1472. *abstract*
- Chaki, S., Gurfinkel, A., & Strichman, O. (2012). Regression verification for multi-threaded programs. *VMCAI 2012*, 119–135. https://doi.org/10.1007/978-3-642-27940-9_9. *title*
- Felsing, D., Grebing, S., Klebanov, V., Rümmer, P., & Ulbrich, M. (2014). Automating regression verification. *ASE '14*, 349–360. https://doi.org/10.1145/2642937.2642987. *abstract*
- Kiefer, M., Klebanov, V., & Ulbrich, M. (2018). Relational program reasoning using compiler IR. *JAR 60(3)*, 337–363. https://doi.org/10.1007/s10817-017-9433-5. *title*
- Barthe, G., Crespo, J. M., & Kunz, C. (2011). Relational verification using product programs. *FM 2011*, 200–214. https://doi.org/10.1007/978-3-642-21437-0_17. *abstract*
- Barthe, G., Crespo, J. M., & Kunz, C. (2013). Beyond 2-safety: Asymmetric product programs for relational program verification. *LFCS 2013*, 29–43. https://doi.org/10.1007/978-3-642-35722-0_3. *abstract*
- Zaks, A., & Pnueli, A. (2008). CoVaC: Compiler validation by program analysis of the cross-product. *FM 2008*, 35–51. https://doi.org/10.1007/978-3-540-68237-0_5. *abstract*
- Sharma, R., Schkufza, E., Churchill, B., & Aiken, A. (2013). Data-driven equivalence checking. *OOPSLA '13*, 391–406. https://doi.org/10.1145/2509136.2509509. *title*
- Churchill, B., Padon, O., Sharma, R., & Aiken, A. (2019). Semantic program alignment for equivalence checking. *PLDI '19*, 1027–1040. https://doi.org/10.1145/3314221.3314596. *abstract*
- Antonopoulos, T., Koskinen, E., Le, T. C., Nagasamudram, R., Naumann, D. A., & Ngo, M. (2023). An algebra of alignment for relational verification. *PACMPL 7(POPL)*, 573–603. https://doi.org/10.1145/3571213. *title*

**Loop restructuring and run-time validation**
- Zuck, L., Pnueli, A., Goldberg, B., Barrett, C., Fang, Y., & Hu, Y. (2005). Translation and run-time validation of loop transformations. *FMSD 27(3)*, 335–360. https://doi.org/10.1007/s10703-005-3402-z. *abstract*
- Bao, W., Krishnamoorthy, S., Pouchet, L.-N., Rastello, F., & Sadayappan, P. (2016). PolyCheck: Dynamic verification of iteration space transformations on affine programs. *POPL '16*, 539–554. https://doi.org/10.1145/2837614.2837656. *abstract*

**Accelerator and hardware**
- Kundu, S., Lerner, S., & Gupta, R. (2008). Validating high-level synthesis. *CAV 2008*, 459–472. https://doi.org/10.1007/978-3-540-70545-1_44. *abstract*
- Herklotz, Y., Pollard, J. D., Ramanathan, N., & Wickerson, J. (2021). Formal verification of high-level synthesis. *PACMPL 5(OOPSLA)*, 1–30. https://doi.org/10.1145/3485494. *title*
- Melchert, J., Terrill, C., Perez-Lopez, A. R., Barrett, C., & Raina, P. (2025). Automated translation validation of a compiler for statically scheduled accelerators. *FMCAD '25*, 198–208. https://doi.org/10.34727/2025/isbn.978-3-85448-084-6_26. *abstract*

**Different outputs**
- Burnim, J., & Sen, K. (2009). Asserting and checking determinism for multithreaded programs. *ESEC/FSE '09*, 3–12. https://doi.org/10.1145/1595696.1595700. *abstract* (via CACM 2010 version and Burnim's thesis)
- Carbin, M., Kim, D., Misailovic, S., & Rinard, M. C. (2012). Proving acceptability properties of relaxed nondeterministic approximate programs. *PLDI '12*, 169–180. https://doi.org/10.1145/2254064.2254086. *abstract*
- Vechev, M., Yahav, E., Raman, R., & Sarkar, V. (2010). Automatic verification of determinism for structured parallel programs. *SAS 2010*, 455–471. https://doi.org/10.1007/978-3-642-15769-1_28. *title*
- McConnell, R. M., Mehlhorn, K., Näher, S., & Schweitzer, P. (2011). Certifying algorithms. *Computer Science Review 5(2)*, 119–161. https://doi.org/10.1016/j.cosrev.2010.09.009. *title*
- Graph 500 Steering Committee. Graph 500 benchmarks 1 ("Search") and 2 ("Shortest Path"), §Validation. https://graph500.org/?page_id=12. Industry specification (gray literature). *partial* (validation section)

**Local sources**
- `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml` (clauses L1–L5, `once_enqueue`, knobs, runtime guards).
- `swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc:458-509` (`BFSVerifier` and its comment block).
- `MemAcc/CONTEXT.md:78-83` (Extensa output-equivalence lattice), read-only.

## Method note

Lit-review discipline from `academic-research-skills:deep-research`: every citation was checked
against doi.org metadata or the publisher or author page, and read scope is recorded per source.
The skill's multi-agent pipeline and sub-agents were not used, as instructed, and its
review-form note was skipped because the caller had fixed the form (scoped lit-review). Claims
marked "our reasoning" or "our synthesis" are not taken from a source.
