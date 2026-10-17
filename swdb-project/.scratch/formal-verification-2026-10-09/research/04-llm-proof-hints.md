# 04 — How LLMs build proof hints for existing verifiers

Created: 2026-10-09 14:20 ET
**Ticket:** [`../issues/04-llm-proof-hints.md`](../issues/04-llm-proof-hints.md)
**Method:** narrative literature review. Every paper below was opened at its arXiv,
publisher, or conference page during this session; venue notes say where a venue could not be
confirmed. Numbers are quoted with their benchmark and source. No number is extrapolated.

---

## TL;DR

1. **One skeleton everywhere: the LLM proposes, the existing formal verifier decides.** Only
   output the verifier accepts counts. The single system that let an LLM *predict* soundness when
   Alive2 was inconclusive (Wang & Xie 2024) is the anti-pattern to cite, not copy.
2. **Two guards, and the strong systems use both.**
   - *Logic guard:* an LLM hint enters as an assumption and must itself be proven before it counts
     (Lemur's proven-sound calculus; Quokka's two-query rule; in ACSL, `assert` = `check` + `admit`).
   - *Text guard:* erase the hints, diff against the original code and specification, and scan for
     escape hatches. AutoVerus's Lynette rejected **326 of 2,637 candidates (12.4%) as unsafe**;
     AlphaVerus saw `assume(false)` "snowball" with no filter. So LLMs do cheat, and the checker in
     decision 8 is required, not optional.
3. **Timeout or unknown always means "not proven yet, try more hints," never evidence.** Systems
   respond in four ways: propose a sub-goal (Lemur), split the failed obligation into smaller checked
   steps (LORIS, Trivet), insert a hint at the failure location (Laurel), or switch verification
   strategy (LLM-Vectorizer). When the budget runs out, the candidate keeps its lower level
   (LLM-Vectorizer's "plausible," our "certified").
4. **Headline rates are high, but the fair baseline is the verifier alone with the same time.**
   On 866 SV-COMP programs, every LLM method added only **0–3 solved instances over UAutomizer at
   500 s** (best: 3). Most of the gain was speed (Quokka). If "proven" means equivalence to the
   original kernel (ticket 09), the agent must also write *relational* hints for C: coupling
   invariants that link the original kernel to the candidate artifact. No verified LLM work does
   this yet. That gap is open, and it is a novelty point for us.
5. **Recommendation:** run bounded first, use hints to reach unbounded, and keep hints in their own
   checked overlay. The design is in the next section.

---

## Recommended loop for our case (DX100 BFS, C++11, single thread)

```
 frozen inputs ─► [1] verifier, no hints ─┬─► proven unbounded ............ done
 (candidate src hash,                     ├─► refuted, counterexample ...... done (bug evidence)
  contract formal halves hash,            └─► timeout / unknown / bounded-only
  verifier + flags from run plan)                    │
                                                     ▼
                         [2] proof-hint agent role writes a hint overlay
                                                     │
                         [3] deterministic hint checker (rejects ⇒ feedback)
                                                     │
                         [4] verifier with hints: every hint is an obligation
                              ├─ all proven ─► [5] minimize hints, vacuity checks, record
                              ├─ hint blamed ─► drop it (Houdini), feed back, go to [2]
                              └─ budget spent ─► keep lower level (within bounds / certified)
```

**[1] Start bounded.** A bounded model checker with unwinding assertions on gives a "proven within
bounds" verdict and real counterexamples with no hints at all. BMC-Agent works this way (CBMC,
default unwind 4, 120 s per function, clean runs labeled "bounded, spec-relative"). This answers
Extensa's failure ("proofs don't construct or scale"): every candidate still gets a formal label
from a tool that needs no invariant.

**[2] Hints lift bounded to unbounded.** Pirzada et al. (ASE 2024) replace each loop with a node
asserting LLM invariants, which a prover checks, so BMC no longer unrolls. CBMC loop contracts do
the same natively (`--apply-loop-contracts`). The hint agent's provider workspace should hold:

- the candidate artifact source (read-only);
- the contract's clauses (read-only);
- the failed obligation, labeled timeout, unknown, or refuted;
- the counterexample trace, when the tool gives one;
- the rejected hints from earlier rounds, with reasons.

On BFS, the hint targets are the chunk loop, the `for(;;)` tile loop and the inner `k` loop in
`library/dx100/bfs_read_offload.inc:27-45`. A ghost counter or set fits the preservation
obligation "enqueue each discovered vertex once."

**[3] Hint checker (deterministic, runs before the verifier).** Build this from the guards in the
literature:

| Check | Source pattern |
|---|---|
| Erase hints; the rest must equal the frozen source exactly | Lynette erases ghost code and diffs (AutoVerus) |
| Contract formal halves unchanged (hash) | Lynette compares pre/post; DafnyBench fails any `requires`/`ensures` edit |
| Banned constructs: `__CPROVER_assume`; ACSL `admit`, `axiom`, any `requires`/`ensures`/`assumes`/`behavior` | Lynette's `admit()`/`assume()` scan; AlphaVerus's string filter; vericoding's ban list |
| Ghost state never written or read by real code | Verus has this by construction; **CBMC has no ghost notion**, so we must enforce it |
| Verifier flags unchanged (unwinding assertions on, checks on, same bounds) | Gap: AutoVerus's fallback *changes* a verifier setting (`loop_isolation(false)`) |

**[4] Every hint is a proof obligation.** Loop invariants are checked for base case and inductive
step, assertions are checked, and lemmas are proven. Accept only when every obligation, hints
included, is fully proven. Use Houdini-style pruning (Loopy): drop the hints the verifier blames
and keep the rest. Feedback should name the obligation kind: established, preserved, or assertion
(Loopy, LORIS). Pass on counterexamples when the tool has them (ExVerus, LaM4Inv, BMC-Agent).

**[5] Before recording "proven unbounded":**
- *Minimize:* drop hints the proof does not need (AutoSpec's simplification step). Records then
  keep only the hints that matter.
- *Vacuity:* hints without `assume` cannot make a proof vacuous. Contradictory preconditions or
  stub contracts can. Run reachability/smoke checks (Frama-C/WP smoke tests, Blanchard et al.
  TAP 2024). Also confirm the proof fails on each negative control of the rewrite contract, such
  as the wrong-tile wait.

**Budget.** The literature flattens after a few feedback rounds:
- DafnyBench: 10 attempts.
- vericoding: 5 attempts.
- AutoSpec: 5 rounds.
- Loopy: 15 completions in total.
- AutoVerus: 8.8 LLM calls per task on average.
- SAFE: extra self-debugging rounds gave "<1%."
- LORIS: capped at 600 s and 150k tokens.

Start at ≤10 rounds. Record rounds, tokens and wall time for every verdict.

---

## Table A — closest to us: C or LLVM-IR verifiers

| System (year, venue) | Verifier | What the LLM writes | Feedback used | On timeout / unknown | Soundness guard | Reported result (benchmark) |
|---|---|---|---|---|---|---|
| **Lemur** (ICLR 2024) | ESBMC, UAutomizer (30 s/call) | Candidate invariants at program points | Verifier verdict T/F/Unknown | Unknown ⇒ Propose new sub-goal or Repair (strengthen) | Proposals are assumptions until proven; calculus proven sound (Thm 3.1) | Code2Inv 133: 107 vs ESBMC 68; 47 hard SV-COMP: 25 vs 1 each (GPT-4) |
| **Loopy** (FMCAD 2024) | Frama-C/WP, 3 s prover timeout | Loop invariants (ACSL) | Frama-C "established/preserved" labels + blamed invariants | Unproven ⇒ Houdini drops it; LLM repair | Houdini returns only inductive subsets | 398/469 vs Ultimate Automizer 430/469; 31 unique solves |
| **LaM4Inv** (ASE 2024) | BMC filter + SMT | Candidate predicates | BMC filters predicates; checks fed into next prompt | Reassemble predicates, re-query | SMT checks final invariant | 309/316 vs best baseline 218 |
| **Pirzada et al.** (ASE 2024) | Modified BMC + first-order prover (tool not named on page; compared with ESBMC) | Loop invariants replacing loops | Prover result | — | Prover checks each invariant before the loop is replaced | Page gives no counts |
| **AutoSpec** (CAV 2024) | Frama-C/WP | ACSL specs incl. function contracts and loop invariants | Legality + satisfiability per round | Unverifiable spec removed; ≤5 rounds | Verifier only; optional removal of unneeded specs | 199/251 (79%); X509-parser 6/6 |
| **Quokka** (arXiv 2025) | UAutomizer (ESBMC in appendix) | One invariant at a time | Two parallel queries: is q valid; does goal hold under q | U = inconclusive, no claim; pick by speedup | Decision-soundness theorem | 866 SV-COMP: +41/+25/+3 over UAutomizer at 30/60/500 s |
| **LORIS** (TOPLAS 2026) | Frama-C 27.1 (5 s/VC) + Z3 | Invariant + natural-language proof of the failing VC | Z3 checks each proof step; names the false step | Failed VC ⇒ localized step feedback | Frama-C decides; Z3 only shapes feedback | 445/460 (93.1%) vs LaM4Inv 414, Clause2Inv 409 |
| **VerIbmc** (arXiv 2026) | ESBMC | Invariant refinements (local models) | Structured verifier feedback | Iterate | Verifier decides | 431/499 (86.4%); symbolic alone 75 |
| **ConVer** (arXiv 2026) | BMC (ESBMC-LF) | Function contracts | CEGAR-CEGIS, ICE learning | Refine on failure | Contracts checked at both levels | Frama-C set 82–96%; X.509 33–50% |
| **BMC-Agent** (arXiv 2026) | CBMC (C), Kani (Rust) | Specs in a DSL ⇒ assume/assert; refinements | Counterexample triage, replay, realism audit | Retries ⇒ "inconclusive" | Guard rejects refinements that "could mask real bugs" | 62 confirmed bugs; bounded clean runs |
| **AutoACSL** (arXiv 2026) | Frama-C/WP | ACSL specs | Verifier loop | Stop at limit | Verifier | 96% full proof (Gemini-3, 604 programs) |
| **LLM-Vectorizer** (CGO 2025) | Alive2, bounded | Vectorized code only (no hints) | Checksum test values | Inconclusive ⇒ next strategy, else stays "plausible" | Alive2; tool authors add trip-count `assume` | TSVC 149: 57 equivalent, 61 not, 31 inconclusive |
| **Trivet** (arXiv 2026) | Lean kernel | Lean proofs of rewrite-specific obligations | Proof checker | Covers 10 cases where Alive2 times out | Lean kernel checks every verdict | 147/148 LLVM IR rewrites verified or refuted |
| **Wang & Xie** (arXiv 2024) | Alive2 | Soundness *prediction* | — | **LLM predicts soundness, then fuzzes** | None for "sound" verdicts | Anti-pattern |

## Table B — other verifiers (useful for loop patterns and guards)

| System (year, venue) | Verifier | What the LLM writes | Feedback / timeout handling | Soundness guard | Reported result (benchmark) |
|---|---|---|---|---|---|
| **Laurel** (OOPSLA 2025) | Dafny 4.3 | One helper assertion at a placeholder | Error message localizes the placeholder; k=10 | Placeholder limits edit location; no explicit diff check | 56.6% of DafnyGym (baseline 6.2%) |
| **dafny-annotator** (Dafny @ POPL 2025) | Dafny | One invariant/assert/decreases per step | Greedy, ≤5 iterations; tool picks location | Model outputs only the annotation; tool inserts it (no explicit diff check in paper) | 15.7% ⇒ 50.6% after fine-tuning (83 methods) |
| **DafnyBench** (TMLR 2025) | Dafny | All hints for a program | Error message, ≤10 attempts | **Fail if any requires/ensures changed, or `assume false` / `{:verify false}`** | Claude 3 Opus 67.8%; no LLM 26.9% |
| **vericoding** (arXiv 2025) | Dafny, Verus, Lean | Code + proof | ≤5 attempts with errors | Ban `assume`/`{:axiom}`/`sorry`; LLM judge for spec translation | DafnyBench now 89% (Opus-4.1), 96.8% union |
| **Clover** (SAIV 2024) | Dafny + LLM | Code, docstring, annotations | ≤3 tries | Six consistency checks catch weak annotations | 87% accept, 0 false positives (CloverBench 60) |
| **AutoVerus** (OOPSLA 2025) | Verus | Invariants, assertions, proof blocks | Generate ⇒ refine ⇒ debug on 8 error types | **Lynette: ghost-erased code equal, pre/post equal, no `admit`/`assume`** | 137/150 vs GPT-4o 67/150 |
| **SAFE** (ICLR 2025) | Verus | Proofs (fine-tuned model) | Self-debug from errors | Verifier only (no diff check on page) | VerusBench 70.5% @100 vs GPT-4o 43.9% @100 |
| **AlphaVerus** (arXiv 2024; ICML 2025 unconfirmed) | Verus | Code + proof | Tree search on errors: breadth 32, depth 8 | String filter, LLM comparison, exploit model | MBPP 65.7%, HumanEval 32.9% (pass@256) |
| **ExVerus** (ICML 2026) | Verus | Invariants | Generalizes validated counterexamples | Verifier | No numbers on abstract page |
| **SpecGen** (ICSE 2025) | OpenJML | Specs (mutated on failure) | Mutation + selection | Verifier | 279/385 |
| **LLMLift** (NeurIPS 2024) | SMT | Program summary + invariants (Python IR) | 50 summary × 10 invariant queries | Accept only verified summary + invariant | 4 DSLs: 44/45, 10/10, 60/60, 23/23 |
| **Baldur** (ESEC/FSE 2023) | Isabelle/HOL | Whole proof, then repair | Error message + failed proof | Proof checker | +8.7% over Thor; 65.7% combined (6,336 theorems) |

---

## Detail

### Loop patterns

- **Guess and check** is universal. The variations are in what gets checked between guesses.
  - *Filter and recombine:* Houdini drops blamed candidates (Loopy). BMC filters single
    predicates, then recombines them (LaM4Inv).
  - *Assume and discharge:* the proposal is treated as an assumption, and the goal is checked
    under it. The proposal then becomes the next goal (Lemur, Quokka).
  - *Phase agents:* draft, refine with tips, debug by error type (AutoVerus). Error types are
    fixed in a set order: type errors, then bounds, then invariant-before-loop.
  - *Search:* tree search scored by the fraction of functions verified (AlphaVerus), or greedy
    one-annotation steps (dafny-annotator).
- **Feedback signals**, from weakest to strongest:
  1. pass/fail only;
  2. the verifier's error message;
  3. a localized location (Laurel's placeholder; the obligation kind in Loopy and LORIS);
  4. the false step in an LLM-written proof (LORIS);
  5. a concrete counterexample.
- **Counterexamples** come from bounded model checkers (LaM4Inv, BMC-Agent, ConVer) or are
  generated and validated separately (ExVerus). Deductive tools such as Frama-C/WP mostly report
  "not proven," with no trace. LORIS's checked natural-language proof is one way to get sharp
  feedback without a counterexample.
- **Budgets** are small. See the budget list in the recommended loop above.

### What systems do on timeout or unknown

- **Lemur** separates `Unknown` (propose or strengthen a sub-goal) from `False` (fail or
  backtrack). It is the clearest model for our "times out or returns unknown" trigger.
- **Quokka** makes no claim on `U`. It judges a hint by whether it *speeds up* the proof, measured
  against 1.2× the original solve time.
- **Laurel** targets proofs the verifier "rejects … or … times out on," because the reasoning
  chain is too long. A single localized assertion is enough for 56.6% of its tasks.
- **LLM-Vectorizer** tries three Alive2 strategies in turn. Inconclusive results keep their
  testing-only "plausible" status, which is the same fallback as our certified level.
- **Trivet** sends the obligations Alive2 cannot handle (timeouts, symbolic bit widths, loops) to
  LLM-written Lean proofs, checked by the kernel.
- **AutoVerus** falls back to a different verifier setting. Our checker must forbid this unless
  the run plan allows it.
- **Wang & Xie** let a fine-tuned LLM *predict* soundness. Do not do this.

### Soundness guards, as a taxonomy

1. **Verifier as oracle** (all systems). Necessary, but not enough on its own: `assume(false)`
   passes any verifier.
2. **Assume, then discharge** (Lemur, Quokka): soundness theorems conditional on the verifier.
3. **Text diff after erasing hints** (Lynette): the only enforced, published "code and spec
   unchanged" check found. It caught 12.4% of candidates.
4. **Banned-construct rules** (DafnyBench, vericoding, AlphaVerus). A list is brittle by itself.
   AlphaVerus adds an *exploit model* that tries trivial solutions against a spec to catch weak
   specs.
5. **Restricted edit surface:** the placeholder (Laurel), or the tool chooses the location
   (dafny-annotator).
6. **Weak-spec detection:** Clover's consistency checks; vericoding's manual audit found about
   9% of specs too weak among the successes. This matters for our "proven contract" work
   (ticket 10), not for hints.
7. **Proof-kernel check** (Trivet, Baldur): the strongest guard, but it requires an
   interactive prover.

### Success rates and benchmarks usable as baselines

- **The hint-loop protocol to copy:** DafnyBench's success rule (spec preserved, no escape hatch,
  ≤10 attempts), enforced by a Lynette-style diff.
- **C invariant suites** for checking that our loop reproduces published numbers:
  - Code2Inv (133): Lemur.
  - The MSR 469-positive set: Loopy.
  - LaM4Inv's 316.
  - InvBench, 866 SV-COMP programs: Quokka.
  - The LORIS 460.
  - Frama-C-problems (51) and X509-parser (6 functions): AutoSpec, ConVer.
- **Equivalence suites:** TSVC (LLM-Vectorizer with Alive2), Trivet's 148 LLVM IR rewrites,
  LLMLift's four DSL suites.
- **Baselines to run:**
  - (a) the verifier alone, with the *same total time*. Lemur also ran the baselines for 12 h;
    they gained only 1–3 solves.
  - (b) symbolic invariant synthesis. UAutomizer beat Loopy 430 vs 398 of 469, and VerIbmc's
    symbolic stage alone solved 75.
  - (c) an LLM without the hint checker, to measure how often cheating occurs.
- **None of these suites has accelerator calls or two-program (relational) obligations.** Our
  DX100 kernels are new ground, so use the public suites only to calibrate.

---

## Findings that bear on ticket 01

- **Decision 8's hint list is too narrow for the CBMC tier.** CBMC loop contracts are declared
  as *assigns, invariant, decreases*, and "each loop should have one assigns clause." ACSL has
  `loop assigns` and `loop variant` too. These are proven obligations, so they fit the spirit of
  decision 8, but they are not in its list. **Suggest:** "loop invariants together with their
  frame (assigns) and variant (decreases)."
- **"Ghost variable" means nothing to CBMC.** A ghost local is ordinary C there, so the checker
  must enforce non-interference itself (Verus and ACSL give it by construction).
- **Callee contracts are a gray zone.** AutoSpec, ConVer and BMC-Agent all have the LLM write
  function contracts. A contract on an internal helper is sound when both sides are proven. A
  contract on a stub (a DX100 intrinsic) is an assumption and belongs to the trusted semantics
  (ticket 12), never to the agent.
- **Verifier configuration is an unlisted escape hatch.** Examples: unwind bounds without
  unwinding assertions, disabled checks, AutoVerus's setting flip. Decision 8 should add: "the run
  plan fixes verifier flags."
- **The trigger should be "below proven unbounded," not only "timeout/unknown."** A bounded tier
  returns "proven within bounds," not unknown. Hints are exactly how literature lifts that to
  unbounded (Pirzada ASE 2024; CBMC loop contracts).
- **Evaluation caution, not a decision change:** Quokka shows that LLM hints mostly buy time on
  small loops. "Verifier without hints" must get equal wall time, or the proof-rate gain will be
  overstated.

## Open questions (for tickets 11 and 13)

1. Relational hints: how does the agent write a coupling invariant between the original
   `TDStep` and the candidate artifact? No verified LLM work found. Prior non-LLM tools
   (PEQUOD, llrêve) exist but were not reviewed here.
2. Should proof hints be a new agent role? The glossary lists rewriting, test generation,
   synthesis and profiling roles. Hints need their own workspace and output schema.
3. Can the hint overlay stay out of the compiled candidate? One idea: macros that expand to nothing
   outside verification, so the compiled IR stays byte-identical. This is our proposal, not from
   the literature.
4. Which consolidated status counts as proven: fully valid only, or also "valid under hypotheses"?
   Confirm in each tool's report format during ticket 07.

---

## Sources

Status key: **confirmed** means the page was opened this session and the venue was confirmed
there or at the publisher or conference site. **venue unconfirmed** means the paper exists but
the venue could not be confirmed.

**Listed in the ticket**

- Wu, H., Barrett, C., Narodytska, N. *Lemur: Integrating Large Language Models in Automated
  Program Verification.* ICLR 2024. https://arxiv.org/abs/2310.04870 — confirmed (arXiv comment
  "Accepted at ICLR 2024"). Numbers from the HTML version: Code2Inv and SV-COMP tables.
- Wen, C., Cao, J., Su, J., Xu, Z., Qin, S., He, M., Li, H., Cheung, S.-C., Tian, C. *Enchanting
  Program Specification Synthesis by Large Language Models using Static Analysis and Program
  Verification* (AutoSpec). CAV 2024, LNCS, doi:10.1007/978-3-031-65630-9_16.
  https://arxiv.org/abs/2404.00762 — venue and DOI taken from a citing paper's bibliography;
  Springer page behind a login.
- Ma, L., Liu, S., Li, Y., Xie, X., Bu, L. *SpecGen: Automated Generation of Formal Program
  Specifications via Large Language Models.* ICSE 2025, doi:10.1109/ICSE55347.2025.00129.
  https://arxiv.org/abs/2401.08807 — confirmed (ICSE 2025 program page).
- Mugnier, E., Anaya Gonzalez, E., Jhala, R., Polikarpova, N., Zhou, Y. *Laurel: Unblocking
  Automated Verification with Large Language Models.* OOPSLA 2025.
  https://arxiv.org/abs/2405.16792 — confirmed (arXiv comment; SPLASH 2025 listing).
- Kamath, A., Senthilnathan, A., Chakraborty, S., Deligiannis, P., Lahiri, S. K., Lal, A.,
  Rastogi, A., Roy, S., Sharma, R. *Finding Inductive Loop Invariants using Large Language
  Models* (Loopy), arXiv 2023, https://arxiv.org/abs/2311.07948; published as *Leveraging LLMs
  for Program Verification*, FMCAD 2024 (FMCAD author list not opened; the PDF link returned 404),
  https://www.microsoft.com/en-us/research/publication/finding-inductive-loop-invariants-using-large-language-models/
  — numbers from arXiv v1.
- Bhatia, S., Qiu, J., Hasabnis, N., Seshia, S. A., Cheung, A. *Verified Code Transpilation with
  LLMs* (LLMLift). NeurIPS 2024. https://arxiv.org/abs/2406.03003 ;
  https://neurips.cc/virtual/2024/poster/93370 — confirmed.
- Taneja, J., Laird, A., Yan, C., Musuvathi, M., Lahiri, S. K. *LLM-Vectorizer: LLM-based
  Verified Loop Vectorizer.* CGO 2025, doi:10.1145/3696443.3708929.
  https://arxiv.org/abs/2406.04693 — CGO 2025 confirmed from author profiles; DOI from an
  aggregator, not opened at doi.org. Note: the paper's "38.2%" is 57/149.
- Aggarwal, P., Parno, B., Welleck, S. *AlphaVerus: Bootstrapping Formally Verified Code
  Generation through Self-Improving Translation and Treefinement.* arXiv 2024.
  https://arxiv.org/abs/2412.06176 — **venue unconfirmed** (one search snippet says ICML 2025; the
  project page lists only arXiv).
- Yang, C., Li, X., Misu, M. R. H., Yao, J., Cui, W., Gong, Y., Hawblitzel, C., Lahiri, S.,
  Lorch, J. R., Lu, S., Yang, F., Zhou, Z., Lu, S. *AutoVerus: Automated Proof Generation for
  Rust Code.* OOPSLA 2025, doi:10.1145/3763174. https://arxiv.org/abs/2409.13082 — confirmed.
- Sun, C., Sheng, Y., Padon, O., Barrett, C. *Clover: Closed-Loop Verifiable Code Generation.*
  SAIV 2024, LNCS 14846, doi:10.1007/978-3-031-65112-0_7. https://arxiv.org/abs/2310.17807 —
  confirmed (author page).
- Chen, T., Lu, S., Lu, S., Gong, Y., Yang, C., Li, X., Misu, M. R. H., Yu, H., Duan, N., Cheng,
  P., Yang, F., Lahiri, S. K., Xie, T., Zhou, L. *Automated Proof Generation for Rust Code via
  Self-Evolution* (SAFE). ICLR 2025. https://arxiv.org/abs/2410.15756 ;
  https://proceedings.iclr.cc/paper_files/paper/2025/hash/b2e20d7402c9985eae4ba924c65370a8-Abstract-Conference.html
  — confirmed. Note: the introduction's 79.14% matches no table; 70.50% is the highest table value.
- Poesia, G., Loughridge, C., Amin, N. *dafny-annotator: AI-Assisted Verification of Dafny
  Programs.* Dafny workshop @ POPL 2025. https://arxiv.org/abs/2411.15143 — confirmed (POPL 2025
  Dafny track).
- First, E., Rabe, M. N., Ringer, T., Brun, Y. *Baldur: Whole-Proof Generation and Repair with
  Large Language Models.* ESEC/FSE 2023, doi:10.1145/3611643.3616243.
  https://arxiv.org/abs/2303.04910 — confirmed (ESEC/FSE 2023 program page).

**Benchmarks and protocols**

- Loughridge, C., Sun, Q., Ahrenbach, S., Cassano, F., Sun, C., Sheng, Y., Mudide, A., Misu,
  M. R. H., Amin, N., Tegmark, M. *DafnyBench: A Benchmark for Formal Software Verification.*
  TMLR 2025. https://arxiv.org/abs/2406.08467 — TMLR per mlanthology/DBLP search results; also
  POPL 2025 Dafny track (confirmed).
- Bursuc, S., Ehrenborg, T., Lin, S., et al. (13 authors), *A benchmark for vericoding: formally
  verified program synthesis.* arXiv 2025 (talk at Dafny @ POPL 2026).
  https://arxiv.org/abs/2509.22908 — confirmed as arXiv.

**2025–2026 work beyond the ticket list**

- Wei, A., Sun, T., Suresh, T., Wu, H., Wang, K., Aiken, A. *Quokka: Accelerating Program
  Verification with LLMs via Invariant Synthesis.* arXiv 2025 (v4 2026).
  https://arxiv.org/abs/2509.21629 — confirmed as arXiv. Note: the authors re-ran all baselines
  with gpt-5.2.
- Li, T., Yan, Z., Liu, J., Di, P., Zhang, X. *Guiding LLM-based Loop Invariant Synthesis via
  Feedback on Local Reasoning Errors* (LORIS). ACM TOPLAS 48(2), Article 8, 2026.
  https://arxiv.org/abs/2605.17914 — confirmed (journal ref on arXiv).
- Wu, G., Cao, W., Yao, Y., Wei, H., Chen, T., Ma, X. *LLM Meets Bounded Model Checking:
  Neuro-symbolic Loop Invariant Inference* (LaM4Inv). ASE 2024.
  https://conf.researchr.org/details/ase-2024/ase-2024-research/33/LLM-Meets-Bounded-Model-Checking-Neuro-symbolic-Loop-Invariant-Inference
  — confirmed (program page; DOI not listed).
- Pirzada, M. A. A., Reger, G., Bhayat, A., Cordeiro, L. C. *LLM-Generated Invariants for Bounded
  Model Checking Without Loop Unrolling.* ASE 2024, doi:10.1145/3691620.3695512 — confirmed
  (program page; no numbers there).
- Pirzada, M. A. A., Parsert, J., Wang, W., Korovin, K., Cordeiro, L. C. *Neuro-Symbolic Software
  Verification: Hyper-charging Local Language Models with Symbolic Reasoning at Scale*
  (VerIbmc). arXiv 2026. https://arxiv.org/abs/2606.16886 — confirmed as arXiv.
- Pirzada, M. A. A., Wang, W., Charalambous, Y., Korovin, K., Cordeiro, L. C. *ConVer: Using
  Contracts and Loop Invariant Synthesis for Scalable Formal Software Verification.* arXiv 2026.
  https://arxiv.org/abs/2605.27051 — confirmed as arXiv.
- Sun, Y., Liu, J., Kroening, D., Xue, J. *Agentic Model Checking* (BMC-Agent). arXiv 2026.
  https://arxiv.org/abs/2605.21434 — confirmed as arXiv; numbers from the HTML version.
- Zhou, H., Luo, Y., Xu, D. *AutoACSL: Synthesizing ACSL Specifications by Integrating LLMs with
  CPG-Based Static Analysis.* arXiv 2026. https://arxiv.org/abs/2606.20969 — confirmed as arXiv.
- Beg, A., O'Donoghue, D., Monahan, R. *Evaluating LLM-Generated ACSL Annotations for Formal
  Verification.* FTfJP 2026 (conditionally accepted). https://arxiv.org/abs/2602.13851 —
  confirmed as arXiv. Finding: rule-based ACSL generation was more reliable than LLMs.
- Yang, J., Sun, Y., Wu, Y., Caridad, R., Yuan, Y., Yao, J., Lu, S., Pei, K. *ExVerus: Verus
  Proof Repair via Counterexample Reasoning.* ICML 2026. https://arxiv.org/abs/2603.25810 ;
  https://icml.cc/virtual/2026/poster/65247 — confirmed.
- Liao, C., Xu, H., Zhou, X., Zhang, Y., Sun, C. *LLVM Translation Validation Automated with
  Large Language Models and Lean* (Trivet). arXiv 2026. https://arxiv.org/abs/2609.19583 —
  confirmed as arXiv.
- Wang, Y., Xie, F. *Enhancing Translation Validation of Compiler Transformations with Large
  Language Models.* arXiv 2024. https://arxiv.org/abs/2401.16797 — confirmed as arXiv (cited as
  the anti-pattern).

**Tool documentation (primary sources for the checker design)**

- CBMC loop contracts: https://diffblue.github.io/cbmc/contracts-loops.html and the index at
  https://diffblue.github.io/cbmc/contracts-user.html (clause order assigns, invariant, decreases;
  `--apply-loop-contracts`).
- Frama-C, *Admit and check annotations in ACSL* (2021):
  https://frama-c.com/2021/06/10/acsl-admit-check.html (`assert P` ≡ `check P; admit P`).
- Blanchard, A., Correnson, L., Djoudi, A., Kosmatov, N. *No Smoke without Fire: Detecting
  Specification Inconsistencies with Frama-C/WP.* TAP 2024. https://allan-blanchard.fr/2024-tap.html
  — confirmed via author page (WP smoke tests catch inconsistent hypotheses).

**Searched but not included:** SpecSyn, KVerus, VeriStruct, RagVerus, VeruSAGE, ATLAS, LimICE,
miniF2F-Dafny and EquiBench. They turned up in searches but were not opened or not needed;
excluded rather than cited unread. Not run: the deep-research multi-agent pipeline and the
review-form step (single-agent scope set by the caller).

*AI disclosure: compiled by an AI research agent (Claude) using web search and page fetches;
every citation above was opened during this session unless marked otherwise.*
