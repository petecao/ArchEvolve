# 22 — LLM repair loops driven by verifier counterexamples

Created: 2026-10-13 17:26 ET
**Ticket:** [`../issues/22-cex-guided-llm-repair-research.md`](../issues/22-cex-guided-llm-repair-research.md)
**Method:** scoped narrative literature review (not systematic), facts only. Searched 2023–2026 on
2026-10-13 (web search, arXiv, Crossref; DBLP blocked automated access). Every cited work was
opened at its arXiv, DOI, venue or project page; title, authors, venue and year were checked there
or in Crossref. Read scope is under [Sources](#sources). Extends research
[04](04-llm-proof-hints.md) and [06](06-closest-prior-work.md) without repeating them.

## TL;DR

- **The ESBMC-AI citation, checked.** Right as a 2023 preprint (arXiv:2305.14752; v1 lists
  Charalambous first), but cite the published version: Tihanyi, Charalambous, Jain, Ferrag,
  Cordeiro, *A New Era in Software Security: Towards Self-Healing Software via Large Language Models
  and Formal Verification*, AST 2025, pp. 136–147, DOI 10.1109/AST66626.2025.00020. It repairs C
  safety violations (bounds, overflow, NULL, division by zero, leaks): ESBMC finds one, the LLM gets
  the code, counterexample, stack trace and line, and ESBMC checks the patch again.
- **Few direct successors.** The same group's 2024 report on neural-network C code reached 18%
  single-shot and 25% iterative repair. Other groups kept the loop but swapped the safety property
  for an equivalence check: T-LLM Compiler (C performance rewrites, CBMC, arXiv 2026), VERT
  (translation to Rust, Kani, ASE 2025), LPO (LLVM IR, Alive2, ASPLOS 2026).
- **A repair usually counts when the same checker passes again, within small bounds.** ESBMC-AI
  ran ESBMC with `--unwind 1`, unwinding assertions off and a 10 s timeout; behavior was checked
  by hand on 1,337 patches. T-LLM's CBMC equivalence check (`--unwind 20`) let 33.8% of wrong
  rewrites through, so its authors added an LLM judge. Few loops also run tests (DR.FIX, Orvalho
  et al., VERT's property-based tests before Kani).
- **Does the counterexample help? The evidence is mixed.** ESBMC-AI: 80–90% with it, 31–37%
  without. The 2024 ESBMC report and FLOURINE found no gain or a loss. In Orvalho et al., adding
  the failing test changed per-model counts by −18 to +26 programs out of 1,431.
- **Races and accelerators: none found for C/C++ with a formal counterexample and an LLM.** Closest:
  ConFixAgent (Java, Java PathFinder reports, arXiv 2026) and DR.FIX (Go, ThreadSanitizer, PLDI
  2025). Verifier-guided race repair without an LLM exists: LLOR (OpenMP, VMCAI 2025), GPURepair
  (CUDA/OpenCL, VMCAI 2021). No accelerator or DMA hazard repair was found. A 2026 ESBMC survey
  credits ESBMC-AI with deadlock and data-race results that neither arXiv version contains.
- **Functional and relational specs: yes, several.** Relational: T-LLM, VERT, LPO and a 2023 Kani
  blog demo. Functional: VeCoGen (ACSL contracts, Frama-C WP, loop-free C), Orvalho et al. (test
  suites), AuthFix (Java, Petri-net checker). Each checks a candidate against its own per-program
  spec. None checks against a reusable contract proven once.
- **Where ours differs (facts):** our counterexample comes from the bounded verifier on one proof
  unit, checked against the unit relation of a rewrite contract with the baseline implementation,
  plus hazard assertions. It is replayed on the strict layer before it counts as a bug. A repaired
  candidate artifact must certify and be proven again. Proof hints live in a separate loop that
  never edits code. No LLM judges correctness.
- **The term is already in use.** Orvalho et al. (AAAI 2025; the counterexample is a failing test)
  and AuthFix (ASE 2025; a model-checker counterexample) both name their loops
  counterexample-guided repair. Cite them with the glossary term.

## Positioning table

Closest to ours first. "Accepted when" is what a repair must pass inside the loop. Results are
the authors' own, on their own benchmarks, and are not comparable across rows.

| Work | Year, venue | Code; what breaks | Checker → what the LLM sees | Spec | Accepted when | Reported result |
|---|---|---|---|---|---|---|
| **T-LLM Compiler** (Fazel et al.) | 2026, arXiv | C (PolyBench/C); LLM performance rewrites | CBMC equivalence harness → "verifier's feedback", original and failed code | Relational: rewrite ≡ original function, bounded | Compiles; CBMC (`--unwind 20`) finds no difference; an LLM judge agrees. No tests | Up to 83.3% "optimization accuracy"; CBMC check: 33.8% false acceptance, 8.4% false rejection (400 cases) |
| **VERT** (Yang et al.) | 2025, ASE | C, C++, Go → Rust; translation bugs | Property-based tests, then Kani → failing inputs from earlier rounds as few-shot examples | Relational: ≡ an oracle compiled via Wasm | Tests, then bounded Kani (bound k, unwind checks off) pass | Claude-2: bounded-verified 1% → 42%, tests 31% → 54% (1,394 programs) |
| **LPO** (Xu et al.) | 2026, ASPLOS | LLVM IR; LLM-proposed peephole rewrites | Alive2 → its counterexample; at most 2 attempts | Relational: refinement | Alive2 proves refinement | 22 of 25 known missed optimizations (Souper 15, Minotaur 3) |
| **ESBMC-AI** (Tihanyi et al.) | 2025, AST (arXiv 2023) | C (FormAI); bounds, overflow, NULL, division by zero, leaks | ESBMC → counterexample, stack trace, line, error type, code; expert prompt per bug type | Safety (built-in checks) | ESBMC passes again (evaluation also reviewed 1,337 by hand) | GPT-4o, one round: 41.0–95.6% by bug class |
| **ConFixAgent** (Li et al.) | 2026, arXiv | Java; races, atomicity and order violations, deadlocks | Java PathFinder report + code slices; at most 5 attempts | Safety: no assertion failure or deadlock over explored schedules | JPF passes (evaluation reviewed final patches by hand) | 29 non-deadlock bugs (PFIX 22, HIPPODROME 21), plus 4 deadlocks |
| **ESBMC on NN code** (Charalambous et al.) | 2024, arXiv report | C neural-network code (~81k mutants); memory safety | ESBMC → bug report or full counterexample, plus a code window | Safety | ESBMC passes again | GPT-3.5: 18% single-shot, 25% iterative |
| **VeCoGen** (Sevenhuijsen et al.) | 2025, FormaliSE | C functions without loops; generated, then improved | Frama-C WP + RTE → failed goals and compiler errors (no counterexamples) | Functional: expert-written ACSL contract | WP proves the contract | 13 of 15 Codeforces problems |
| **Orvalho et al.** | 2025, AAAI | C student programs; wrong output | MaxSAT fault localization → sketch without the buggy lines, plus a failing test | Functional: I/O test suite | All tests pass | 1,013 of 1,431 (70.8%) over six ~7B models and prompt variants; Clara 34.6%, Verifix 6.3% |
| **Kani blog demo** (Kani team) | 2023, project blog | Rust toy; ChatGPT bit-trick "optimization" | Kani equivalence harness → concrete counterexample | Relational: ≡ original for every `u32` | Kani passes | Verified after two counterexample rounds (one function) |
| **FLOURINE** (Eniser et al.) | 2024, arXiv | C, Go → Rust | Differential fuzzer → counterexample inputs (three prompt styles) | Relational: I/O equivalence | Fuzzer finds no difference before timeout | Best LLM 47%; asking again beat counterexample prompts |
| **DR.FIX** (Behrang et al.) | 2025, PLDI | Go (Uber); data races | ThreadSanitizer report, code skeleton, retrieved past fixes; failure text on retry | Safety: race freedom, observed dynamically | Builds; each test runs 1,000 times without the race; code review | 224 of 404 races patched; 193 merged |
| **AuthFix** (Rahat et al.) | 2025, ASE | Java OpenID Connect; protocol bugs | Petri-net model checker against the protocol spec → counterexample-guided refinement | Functional: protocol spec | Model check passes | 17 of 23 bugs |
| **LLM4PLC** (Fakih et al.) | 2024, ICSE-SEIP | Structured Text (PLC); generated code | nuXmv and compiler errors, plus user feedback | Functional and safety properties (SMV) | nuXmv passes | Success 47% → 72% |
| **LLOR** (Bora et al.), *no LLM* | 2025, VMCAI | OpenMP C/C++/Fortran; data races | LLOV race traces → constraints on where to enable barriers or ordered regions | Safety: race freedom | LLOV reports no race | Over 80% of programs with a real race (415 programs) |
| **GPURepair** (Joshi, Muduganti), *no LLM* | 2021, VMCAI | CUDA/OpenCL kernels; races, barrier divergence | GPUVerify → barrier insertion or removal | Safety | GPUVerify passes | About 750 kernels evaluated |

## Detail by cluster

### A. ESBMC-AI, checked

- **Versions differ; cite the published one.**
  - arXiv v1 (2023-05-24), Charalambous first: gpt-3.5-turbo; 1,000 generated C programs of 20–50
    lines; unwind bound 50, 10 s; "up to 80%" repaired (buffer overflow, pointer dereference).
  - arXiv v2 (2024-06-27), Tihanyi first: GPT-4o; 50,000 FormAI programs. Details below are v2.
  - AST 2025 (Crossref, program page): five authors; Sun is not listed. Its PDF was not opened.
- **What the LLM sees:** the code, ESBMC's counterexample, stack trace, line number and error
  type. Experts wrote one prompt per vulnerability type; the authors report that a generic "fix
  the code" prompt lowers accuracy. One issue is fixed per round.
- **Checker settings in the loop:** `--overflow --memory-leak-check --show-stacktrace --timeout 10
  --unwind 1 --multi-property --no-unwinding-assertions`. A pass means no violation found on paths
  with one loop unrolling, within 10 s. (Labeling used unlimited k-steps and a 500 s timeout.)
- **Validation:** ESBMC again. Behavior preservation is not checked automatically; the authors call
  that infeasible because program equivalence is undecidable. They reviewed 1,337 patches by hand
  and used lines of code and cyclomatic complexity as proxies. No tests.
- **Results (Table III, one round):** array lower bound 95.60% (n = 182), `fscanf` overflow 91.29%
  (241), `scanf` overflow 90.40% (175), division by zero 86.47% (133), NULL dereference 80.35%
  (229), add overflow 70.27% (73), forgotten memory 48.66% (187), array upper bound 41.03% (117).
- **Failure modes (authors):** a fix can expose a new violation (two rounds then reached 88%);
  upper-bound fixes often just add 1; leak fixes need files outside the prompt.
- **No concurrency.** Neither arXiv version evaluates data races or deadlocks (v1 PDF and v2 HTML
  text searched). The 2026 ESBMC survey (Dantas et al.) cites ESBMC-AI for lower rates on deadlock
  and data-race categories, yet a note in the same survey says concurrency defects are not reported
  in the cited source. Do not repeat the survey's claim.

### B. The same group's follow-up: ESBMC on neural-network C code (2024)

- Charalambous, Manino, Cordeiro; an arXiv technical report; no venue found. NeuroCodeBench grown
  to about 81k programs by mutation; ESBMC checks memory safety (NULL, out-of-bounds, double free,
  leaks) with incremental BMC and a 300 s timeout.
- The LLM (GPT-3.5-Turbo) sees a code window around the reported line and either the short bug
  report or the full counterexample: "no significant difference". In single-shot prompts, verifier
  feedback made results worse. Best single-shot 18%; iterative 25%, peaking at three attempts with
  earlier patches in the prompt. A repair counts when it compiles and ESBMC passes.

### C. Relational loops: the candidate is checked against a reference

- **T-LLM Compiler** (arXiv 2026, venue unknown). Closest in subject: LLM performance rewrites of
  C loops (Qwen2.5-32B-Instruct, PolyBench/C), checked against the original function.
  - Harness: both functions run on the same nondeterministic input, then an assertion that outputs
    match. Flags: `--cvc5 --no-standard-checks --function main --unwind 20`, so memory-safety
    checks are off.
  - Feedback prompt: original code, failed code and a `{FEEDBACK}` slot. The paper does not say
    whether CBMC's trace fills it.
  - Acceptance: compiler, then CBMC, then an LLM "semantic verifier". Tests are avoided on purpose.
  - CBMC as a filter (400 cases): 87% accuracy, 8.4% false rejection, 33.8% false acceptance,
    which the authors attribute to the bound. Alive2 often timed out on these C-level rewrites.
- **VERT** (ASE 2025; arXiv title ends "as Few-Shot Learners"). The reference is an oracle Rust
  program compiled mechanically through Wasm (rWasm). Checks: property-based tests, then Kani with
  bound k and unwind checks off (120 s), then optional full verification. A timeout counts as a
  failure. On failure the LLM translates again, with failing inputs from earlier rounds as
  few-shot examples. Repair is regeneration, not editing.
- **LPO** (ASPLOS 2026). Relational at IR level (Alive2 refinement). When Alive2 refutes a
  candidate, its counterexample goes back to the LLM; each instruction sequence gets at most two
  attempts. Research 06 covers LPO as a checker; the feedback loop is the new fact here.
- **Kani blog demo** (2023, gray literature). ChatGPT rewrote a 32-iteration loop as a bit trick;
  a Kani harness compared it with the original for every `u32`. Two counterexamples went back to
  ChatGPT and the third version verified. Toy scale, run by hand.
- **FLOURINE** (arXiv 2024; the TU Wien repository lists it as a preprint). C and Go to Rust,
  checked by a cross-language differential fuzzer. Three of four feedback strategies used
  counterexamples. The fourth simply repeated the prompt and did best (a 7–21% gain); the authors
  conclude LLMs do not always understand counterexamples. Best LLM: 47% of benchmarks translated.
- **Test-based relatives (no formal checker).** LLM-Vectorizer (CGO 2025, research 06) repairs
  from checksum tests and runs Alive2 afterwards. SmartC2Rust (ICSE 2026) and Weiss et al. (SANER
  2026) repair C-to-Rust output from test or fuzzing mismatches; feedback narrowed LLM gaps (Weiss).

### D. Functional-spec loops

- **VeCoGen** (FormaliSE 2025). Inputs: an expert-written ACSL contract (up to 3 hours each),
  English text and tests. Frama-C WP and RTE check each candidate; failed goals and compiler errors
  go back (GPT-3.5-turbo by default). Single loop-free functions only, so WP needs no invariants.
  It generates code rather than repairing an artifact, and WP gives no counterexamples.
- **Orvalho et al.** (AAAI 2025). Student C programs. CFaults (MaxSAT fault localization over the
  failing tests) removes suspect lines; the LLM fills the holes; tests check the result; a failing
  test is the counterexample. Six open ~7B models. With the reference implementation in the
  prompt the portfolio rises to 1,190 (83.2%), but the authors report models often replaced the
  student program with the reference instead of fixing it.
- **AuthFix** (ASE 2025). Java OpenID Connect libraries. An LLM (GPT-3.5) localizes faults and
  writes repair expressions; a Petri-net model checker checks the patch against a protocol spec;
  counterexamples refine the search. It calls itself a "counterexample-guided repair engine".
- **LLM4PLC** (ICSE-SEIP 2024). PLC Structured Text, checked by nuXmv against SMV properties
  derived from a plant specification. Errors go back to the LLM, with a human in the loop.

### E. Concurrency, races and accelerators (ticket question 2)

- **LLM plus model checker, Java: ConFixAgent** (arXiv 2026). Java PathFinder explores thread
  interleavings and reports the bug. A static happens-before graph picks the code the LLM sees.
  JPF re-checks each patch, up to five attempts. Covers races, atomicity and order violations, and
  deadlocks. The evaluation reviewed final patches by hand for unchanged behavior.
- **LLM plus dynamic detector, Go: DR.FIX** (PLDI 2025). ThreadSanitizer reports from Uber's test
  runs. The LLM sees race information, a code skeleton and retrieved past fixes (GPT-4 Turbo,
  GPT-4o, o1-preview). A patch must build, run each affected test 1,000 times without the race,
  then pass code review.
- **Verifier-guided race repair without an LLM.** LLOR (VMCAI 2025) turns LLOV race traces into
  constraints over candidate synchronization points in OpenMP code. GPURepair (VMCAI 2021) uses
  GPUVerify to insert or remove barriers in CUDA and OpenCL kernels. Both repair only by placing
  synchronization.
- **MPI.** Piersall et al. (JPDC 2026) raise LLM detection of MPI errors from 44% to 77% with
  few-shot, chain-of-thought and retrieval prompting. Read: abstract only; it names no checker.
- **Accelerators.** No LLM repair from a formal counterexample was found for offload code, DMA or
  command-interface hazards. Nearest: LLM repair of C/C++ for high-level synthesis (MLCAD 2024),
  validated by C-RTL co-simulation on the original tests; and counterexample-guided LLM repair of
  RTL designs with open-source formal tools (Tran, arXiv 2026), where one of six designs was
  repaired reliably. Neither concerns software that drives an accelerator.
- **Scope of these absence claims.** Web searches on 2026-10-13 pairing LLM repair with ESBMC,
  CBMC, Kani, SAW, Frama-C, CIVL, GPUVerify, KLEE or model checking, and with races, deadlock,
  OpenMP, MPI, CUDA, DMA or accelerators. Also read: the 2026 ESBMC survey (§8) and a 2025
  vulnerability-repair SoK; both name ESBMC-AI as their example of LLM plus formal-tool repair.

## How ours differs

Facts from our tickets beside what the prior loops do. No claim of novelty.

| Aspect | Prior loops (examples) | Ours |
|---|---|---|
| Counterexample source | ESBMC, CBMC, Kani, Alive2, JPF, fuzzers, failing tests | The bounded verifier: SAW at one thread; CIVL for threads ≤ k, with GenMC as a second refuter ([11](../issues/11-verifier-choice.md); [15](../issues/15-concurrency-proofs.md) item 9) |
| Scope of a check | Whole program (ESBMC-AI), whole function (T-LLM, VERT), IR snippet (LPO) | One proof unit: one call of the function that holds a rewrite site ([09](../issues/09-what-proven-asserts.md)) |
| Checked against | Built-in safety checks; equivalence with the original or an oracle; a per-problem contract or test suite | The unit relation or relational template of the rewrite contract the candidate applies, against the baseline implementation, plus no accelerator hazards ([09](../issues/09-what-proven-asserts.md), [10](../issues/10-proven-rewrite-contract.md), [12](../issues/12-dx100-proof-semantics.md)) |
| When a counterexample counts | Taken as found | Replayed on the strict layer; "bug" only with a whole-kernel reproduction ([13](../issues/13-proof-hint-loop.md) item 10) |
| What a repair must pass | The same checker again, usually at the same small bound; sometimes tests, a human, or an LLM judge | Certification again (tests, negative controls), then the bounded and unbounded proofs again (glossary: counterexample-guided repair) |
| Who judges | Verifiers; T-LLM adds an LLM judge | Verifiers and certification only; the LLM proposes, the verifier decides ([04](04-llm-proof-hints.md) TL;DR 1; [13](../issues/13-proof-hint-loop.md) item 7) |
| When the check cannot decide | Failure (VERT) or the bounded pass is accepted (ESBMC-AI, T-LLM); none of the loops found adds proof help | A separate proof-hint loop adds hints for WP and never edits code; SAW takes no hints ([13](../issues/13-proof-hint-loop.md) items 1–2) |
| Races | JPF (Java) or ThreadSanitizer (Go) with an LLM; LLOV or GPUVerify without one | CIVL and GenMC refute; repair applies one general fix: relaxed atomic load, redundant plain store removed ([15](../issues/15-concurrency-proofs.md) item 10) |
| Accelerators | None found | DX100 hazards are proof obligations in the proof semantics ([12](../issues/12-dx100-proof-semantics.md)) |
| Spec reuse | Per program or per pair | One rewrite contract serves many candidates; a contract change is a new contract version ([10](../issues/10-proven-rewrite-contract.md); [15](../issues/15-concurrency-proofs.md) item 11) |

## Suggested baselines that mirror the closest work

Input for ticket [23](../issues/23-evaluation-baselines-and-metrics.md). Each mirrors one published
loop; none is a design decision.

- **Safety-only repair (ESBMC-AI):** counterexample plus code to the rewriting role; accept when
  the bounded verifier finds no safety violation at the same bounds. No unit relation, no
  re-certification. It shows what the contract check and re-certification catch.
- **Per-pair bounded equivalence (T-LLM, VERT):** CBMC- or Kani-style bounded equivalence of the
  whole rewritten function against the baseline implementation, with counterexamples fed back.
  No contract, no unbounded proof. T-LLM's 33.8% false acceptance is the figure to compare with.
- **No counterexample, or simply ask again (ESBMC-AI's ablation, FLOURINE):** the same number of
  provider calls with (a) only the verdict and (b) the original prompt repeated. Published results
  disagree on whether the counterexample helps, so either outcome is informative.
- **Races without an LLM (LLOR, GPURepair):** synchronization placement from race traces, solved
  as constraints. Our race fix is also one fixed rule ([15](../issues/15-concurrency-proofs.md)
  item 10), so this baseline isolates what the LLM adds.
- **Races with a dynamic detector (DR.FIX):** ThreadSanitizer-driven repair accepted after repeated
  test runs, on the same racy candidates as our CIVL- and GenMC-driven repair.
- **Metrics this literature reports:** repair rate after one round and after k rounds (ESBMC-AI
  one round; the 2024 report peaks at 3 attempts; LPO caps at 2, ConFixAgent at 5); false
  acceptance found by an independent check (T-LLM; hand review in ESBMC-AI and ConFixAgent); patch
  size (lines and cyclomatic complexity in ESBMC-AI; tree edit distance in Orvalho et al.); and
  how often a "repair" copies the reference (Orvalho et al.).

## Open questions

- **Revert-to-baseline repairs.** Orvalho et al. saw models replace a buggy program with the
  reference they were shown. Our rewriting role works from the baseline implementation. Does a
  repair that removes the rewrite count, and how often does it happen? (Tickets 23, 25.)
- **T-LLM's feedback content.** Its prompt has a `{FEEDBACK}` slot; whether CBMC's trace fills it
  is not stated.
- **ESBMC-AI numbers.** The v2 text swaps the two array-bounds rates against Table III. Two table
  cells differ slightly from their own counts: `scanf` 160/175 = 91.4% (printed 90.40%) and add
  52/73 = 71.2% (printed 70.27%). Cite Table III; the AST version was not opened.
- **The survey's concurrency claim** about ESBMC-AI has no source we could find.
- **Venues unknown** as of 2026-10-13: T-LLM Compiler, ConFixAgent, FLOURINE and the 2024 ESBMC
  report (arXiv only).
- **Not covered:** LLMs writing proofs or hints instead of code (research 04, including ExVerus),
  Dafny, Verus and Lean code generation, RTL repair beyond one example, unpublished tools.

## Sources

Status key, as in research 06: **VERIFIED** = DOI resolved in Crossref and title, authors and
venue matched; **PLAUSIBLE** = arXiv, venue or repository page opened and matched, no DOI check;
**GRAY** = project blog. "Read" is what was actually read.

**Seed and its line**

- Tihanyi, N., Charalambous, Y., Jain, R., Ferrag, M. A., Cordeiro, L. C. (2025). *A New Era in
  Software Security: Towards Self-Healing Software via Large Language Models and Formal
  Verification.* 2025 IEEE/ACM International Conference on Automation of Software Test (AST),
  136–147. https://doi.org/10.1109/AST66626.2025.00020. VERIFIED (Crossref and the AST 2025
  program page agree). Preprint https://arxiv.org/abs/2305.14752: v1 2023-05-24 (Charalambous,
  Tihanyi, Jain, Sun, Ferrag, Cordeiro); v2 2024-06-27 (Tihanyi, Jain, Charalambous, Ferrag, Sun,
  Cordeiro). Read: v1 PDF text; v2 HTML (method, setup, Table III, limitations). AST PDF not opened.
- Charalambous, Y., Manino, E., Cordeiro, L. C. (2024). *Automated Repair of AI Code with Large
  Language Models and Formal Verification.* arXiv:2405.08848 (technical report).
  https://arxiv.org/abs/2405.08848. PLAUSIBLE; no venue found in Crossref. Read: arXiv HTML
  (§4–5).
- Dantas, P., Cordeiro, L., Junior, W. (2026). *ESBMC: A Survey of Its Evolution, Integration, and
  Future Directions in Formal Software Verification.* arXiv:2605.26169.
  https://arxiv.org/abs/2605.26169. PLAUSIBLE. Read: §8 (AI and LLM integration).
- Li, Y., Shezan, F. H., Wei, B., Wang, G., Tian, Y. (2025). *SoK: Towards Effective Automated
  Vulnerability Repair.* arXiv:2501.18820. https://arxiv.org/abs/2501.18820. PLAUSIBLE; venue not
  checked. Read: passages on LLM and external-tool repair.

**Relational loops**

- Fazel, Z., Gamage, S., Bagi, S. S. G., Ashouri, A. H., Czajkowski, T. S., Chan, B., Azimi, R.,
  Gao, Y. (2026). *T-LLM Compiler: Trusted LLM-based Code Optimization and Verification
  Framework.* arXiv:2608.14953. https://arxiv.org/abs/2608.14953. PLAUSIBLE; venue unknown. Read:
  arXiv HTML (§3, §4.2–4.5, appendix prompts).
- Yang, A. Z. H., Takashima, Y., Paulsen, B., Dodds, J., Kroening, D. (2025). *VERT: Polyglot
  Verified Equivalent Rust Transpilation with Large Language Models.* ASE 2025.
  https://conf.researchr.org/details/ase-2025/ase-2025-papers/57/VERT-Polyglot-Verified-Equivalent-Rust-Transpilation-with-Large-Language-Models ;
  arXiv:2404.18852 (*…with Large Language Models as Few-Shot Learners*). PLAUSIBLE (program page
  lists no DOI). Read: arXiv HTML v2 (§3.5–3.6, results).
- Xu, Z., Xu, H., Tian, Y., Zhou, X., Sun, C. (2026). *LPO: Discovering Missed Peephole
  Optimizations with Large Language Models.* ASPLOS 2026, Vol. 2, 1136–1150.
  https://doi.org/10.1145/3779212.3790184. VERIFIED. Read: arXiv HTML (§3).
- Kani team (2023-05-01). *Writing Code with ChatGPT? Improve it with Kani.* Kani Rust Verifier
  Blog. https://model-checking.github.io/kani-verifier-blog/2023/05/01/writing-code-with-chatgpt-improve-it-with-kani.html.
  GRAY; no author named on the page. Read: full post.
- Eniser, H. F., Zhang, H., David, C., Wang, M., Christakis, M., Paulsen, B., Dodds, J.,
  Kroening, D. (2024). *Towards Translating Real-World Code with LLMs: A Study of Translating to
  Rust* (FLOURINE). https://arxiv.org/abs/2405.11514. PLAUSIBLE; the TU Wien repository lists it
  as a preprint. Read: arXiv HTML (§1, §3–5, §6.3).
- Taneja, J., Laird, A., Yan, C., Musuvathi, M., Lahiri, S. K. (2025). *LLM-Vectorizer: LLM-Based
  Verified Loop Vectorizer.* CGO 2025, 137–149. https://doi.org/10.1145/3696443.3708929. VERIFIED.
  Read: arXiv HTML (§2.2, §4.4).
- Shiraishi, M., Cao, Y., Shinagawa, T. (2026). *SmartC2Rust: Iterative, Feedback-Driven C-to-Rust
  Translation via Large Language Models for Safety and Equivalence.* ICSE 2026, 980–991.
  https://doi.org/10.1145/3744916.3773259. VERIFIED. Read: arXiv HTML (repair, equivalence).
- Weiss, M., Hecking-Harbusch, J., Quante, J., Woehrle, M. (2026). *Feedback Loops and Code
  Perturbations in LLM-Based Software Engineering: A Case Study on a C-to-Rust Translation
  System.* SANER 2026, 367–376. https://doi.org/10.1109/SANER67736.2026.00047. VERIFIED. Read:
  abstract and system section.

**Functional-spec loops**

- Sevenhuijsen, M., Etemadi, K., Nyberg, M. (2025). *VeCoGen: Automating Generation of Formally
  Verified C Code With Large Language Models.* FormaliSE 2025, 101–112.
  https://doi.org/10.1109/FormaliSE66629.2025.00017. VERIFIED. Read: arXiv HTML (§III–IV).
- Orvalho, P., Janota, M., Manquinho, V. M. (2025). *Counterexample Guided Program Repair Using
  Zero-Shot Learning and MaxSAT-based Fault Localization.* AAAI 2025, 39(1), 649–657.
  https://doi.org/10.1609/aaai.v39i1.32046. VERIFIED. Read: arXiv HTML v1 (method, Tables 6–9).
- Ahmed, U. Z., Fan, Z., Yi, J., Al-Bataineh, O. I., Roychoudhury, A. (2022). *Verifix: Verified
  Repair of Programming Assignments.* ACM TOSEM. https://doi.org/10.1145/3510418. VERIFIED. Read:
  Crossref metadata and Orvalho et al.'s description only.
- Rahat, T. A., Chen, Y., Feng, Y., Tian, Y. (2025). *Automated Repair of OpenID Connect
  Programs* (AuthFix). ASE 2025, 2261–2273. https://doi.org/10.1109/ASE63991.2025.00187. VERIFIED.
  Read: arXiv extended version 2510.02773 (abstract, §V–VI).
- Fakih, M., Dharmaji, R., Moghaddas, Y., Quiros, G., Ogundare, O., Al Faruque, M. A. (2024).
  *LLM4PLC: Harnessing Large Language Models for Verifiable Programming of PLCs in Industrial
  Control Systems.* ICSE-SEIP 2024, 192–203. https://doi.org/10.1145/3639477.3639743. VERIFIED.
  Read: arXiv HTML (abstract, §4).

**Concurrency and accelerators**

- Li, Z., Yi, Q., Xiao, K., Ji, Z., Liang, H. (2026). *An End-to-End Approach for Fixing
  Concurrency Bugs via SHB-Based Context Extractor* (ConFixAgent). arXiv:2604.05753.
  https://arxiv.org/abs/2604.05753. PLAUSIBLE; venue unknown. Read: arXiv HTML (§III, §IV-B).
- Behrang, F., Zhang, Z., Saioc, G.-V., Liu, P., Chabbi, M. (2025). *DR.FIX: Automatically Fixing
  Data Races at Industry Scale.* PACMPL 9 (PLDI), 475–502. https://doi.org/10.1145/3729265.
  VERIFIED. Read: arXiv HTML (§4.4, §5.1).
- Bora, U., Joshi, S., Muduganti, G., Upadrasta, R. (2025). *LLOR: Automated Repair of OpenMP
  Programs.* VMCAI 2025, LNCS, 121–136. https://doi.org/10.1007/978-3-031-82703-7_6. VERIFIED.
  Read: arXiv HTML (§2, results summary).
- Joshi, S., Muduganti, G. (2021). *GPURepair: Automated Repair of GPU Kernels.* VMCAI 2021, LNCS,
  401–414. https://doi.org/10.1007/978-3-030-67067-2_18. VERIFIED. Read: arXiv 2011.08373 abstract.
- Piersall, S., Gao, Y., Liu, S., Wang, L. (2026). *Improving MPI Error Detection and Repair with
  Large Language Models and Bug References.* Journal of Parallel and Distributed Computing, 105255.
  https://doi.org/10.1016/j.jpdc.2026.105255. VERIFIED. Read: abstract only.
- Xu, K., Zhang, G. L., Yin, X., Zhuo, C., Schlichtmann, U., Li, B. (2024). *Automated C/C++
  Program Repair for High-Level Synthesis via Large Language Models.* MLCAD 2024, 1–9.
  https://doi.org/10.1145/3670474.3685953. VERIFIED. Read: arXiv HTML (§III, Table II).
- Tran, H. T. (2026). *Open-Source LLM-Driven Formal Verification: A Multi-Agent Pipeline for RTL
  Repair.* arXiv:2607.28877. https://arxiv.org/abs/2607.28877. PLAUSIBLE. Read: abstract only.

**Searched but not included:** Galois's 2023 post on GPT-4 writing SAW proof scripts (404; not
opened). CiL-Agent (C repair from GCC, Clang Static Analyzer and Valgrind feedback; snippet only).
PathFix (arXiv 2510.14341; KLEE-based C repair where counterexamples refine a synthesizer, not the
LLM). Agentic Model Checking (BMC-Agent; finds bugs, no repair; research 04). SpecLoop (RTL
specification generation). Agents4PLC (abstract only).

*AI disclosure: an AI agent (Claude) ran the searches and drafted this note; every citation above
was opened at its source page during this session unless marked otherwise.*
