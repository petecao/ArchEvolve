# 11 — Which verifiers form the bounded and unbounded tiers?

Created: 2026-10-09
Updated: 2026-10-13 00:35 ET (resolved with Yan-Ru in four grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-12 22:50 ET)
**Blocked by:** 02, 08, 09
**Map:** `../map.md`

## Question

Which formal verifier (or verifiers) form the proven-within-bounds tier and the proven-unbounded
tier, and what is the fallback when the primary tool cannot read the code?

## Comments

- 2026-10-09: input from 02: only Clang/LLVM-based tools read our C++ unchanged; CBMC's C++
  support is "certainly spotty". Candidate tiers: bounded = ESBMC (then crux-llvm); unbounded =
  Frama-C/WP + RPP on a C port (then ESBMC k-induction). No single-thread tool models OpenMP:
  the concurrency phase needs VerCors, CIVL or a pthreads rewrite.
- 2026-10-11: input from 08: ESBMC 8.5 timed out on DX100 code: the strict layer as written
  (its `std::vector` model) and the array port (300–600 s, every size). crux-llvm 0.12 proved
  and refuted at one lane on the port, but cannot run libc++ 22 code, and no safe 2-lane run
  finished in 15 minutes. CBMC cannot parse libc++ 22 headers. Running 6 crux jobs at once
  exhausted the Mac's 36 GB of RAM: run one at a time, or on mbit10 under `ulimit -v`.
- 2026-10-12 22:25 ET: input from 09: the tiers must also cover (1) machine-checked lifting
  lemmas (induction over a kernel's driver loop, with the proof unit replaced by its claim);
  (2) equality over real arithmetic for floating-point kernels (PR, BC), rounding in the
  assumption set; (3) for proven unbounded, a proof for any thread count, since thread count is
  a bound. The evaluation covers other GAPBS kernels, not only BFS.
- 2026-10-12 22:52 ET: input from 10: the tiers must (1) use summaries, a library entry's proven clauses in
  place of its code, inside candidate proofs (function contracts that replace calls); (2) run
  two routes: a single-program proof of a unit postcondition (BFS; what 08 did with P2) and a
  paired-program proof under a relational template (PR, BC); (3) prove contract parts once,
  ideally for all graph sizes and knob values, else within recorded bounds. Hypothesis to test
  in the proof of concept: 08's safe 2-lane case proves in under 15 minutes on the Mac once
  summaries replace the inlined strict-layer port.
- 2026-10-12 23:24 ET: fact sweep for this grilling, [`../research/11-verifier-facts.md`](../research/11-verifier-facts.md).
  Exact-real floats: only crux-llvm `-f real` and WP `-wp-model +real` (crux's default float mode
  depends on the solver: always pass `-f`). Summaries: native in SAW, ESBMC, CBMC
  (`goto-instrument --dfcc`); crux needs hand stubs. SAW 1.6 has an arm64 asset and an LLVM 22
  bitcode parser (untested here). WP needs the `Wp.induction` tactic for induction lemmas (one
  subgoal not reached in tests); no Rocq in `framac-33`. RPP has no relational loop invariants.
  VerCors 2.4.0 rejects `#pragma omp parallel` blocks; only single `parallel for` loops with
  iteration contracts verify. Corrects 02 on VerCors (OpenMP support), SAW (cutpoint loop
  invariants exist) and crux (LLVM 3.6-21, as 07 said). WP runs fail inside the Bash sandbox
  (Why3 socket blocked).
- 2026-10-12 23:24 ET: grilling round 1 (Q1-Q9) posted to Yan-Ru; awaiting answers.
- 2026-10-12 23:33 ET: round 1 answers (checkpoint; not yet the answer). Accepted: Q1 (no "tier":
  bounded verifier, unbounded verifier, together the verifier lineup), Q3 (bounded verifier =
  Crucible family; ESBMC out; Yan-Ru is open to any verifier and the lineup may change later),
  Q4 (one summary source: call stubs for the bounded verifier, ACSL contracts for WP; only
  summary `assume`s allowed), Q5 (WP on a mechanical C lowering of a declared C++ subset; outside
  it, at most proven within bounds; bounded verifier runs on both forms), Q6 (our own product
  program; RPP out), Q8 (versions, solvers, front end and flags pinned per content-hash set; solver
  portfolio). Q2 re-asked: a timeout should trigger more proof hints, not be ignored. Q7 accepted
  with a requirement: every tool failure is root-caused, and the pipeline is made robust to it.
  Q9 accepted (no proven unbounded while threads = 1), but concurrency must be supported and
  proven; brainstorm it in the next rounds.
- 2026-10-12 23:44 ET: round 2 answers (checkpoint; not yet the answer). Accepted: Q10 (a WP timeout means
  "not proven yet" and triggers the proof-hint loop; never a bug, never a proof; bugs come only
  from bounded counterexamples), Q11 (the method fixes roles and an adapter interface, not tools;
  a swap reopens once-proven parts), Q12 (SAW 1.6 is the bounded verifier, specs generated from
  formal halves; crux-llvm fallback; first test: SAW reads clang 22 bitcode), Q13 (PR/BC bounded
  runs use crux `-f real` until SAW's float mode is confirmed; WP `-wp-model +real`; rounding in
  the assumption set), Q14 (lifting lemmas in WP with replayed `Wp.induction` scripts; Rocq in a
  separate switch as fallback), Q15 (failure classes with handlers; unclassified failure stops the
  batch; regression corpus), Q16 (concurrency claim for any thread count: race freedom, atomic
  critical sections, order independence, per-thread tile ownership and hazard freedom, exact chunk
  cover), Q18 (five concurrency negative controls), Q19 (concurrency in the first paper for BFS
  read offload; single thread first in the proof of concept; the fog becomes a ticket). Q17: Yan-Ru
  asks whether to do all three methods (reduction, permission logic, bounded interleaving); open,
  waits on the concurrency survey.
- 2026-10-12 23:49 ET: Q20 accepted (Q17 resolved: all three concurrency methods, each with its own job.
  Reduction is the proof for any thread count and the only one that sets the proven level;
  bounded interleaving at 2-3 threads is the concurrency refuter; permission logic is an
  independent cross-check and an evaluation comparison, setting no level unless it reads the real
  code or its rewrite is a proven reduction; dropped first if time runs short). Tools for the
  last two wait on the concurrency survey. Yan-Ru asked for a formal name for the tool, extending
  Extensa (round 3).
- 2026-10-12 23:51 ET: round 3 answers. Q21: the name covers the paper's system (Extensa's loop plus the proven
  levels), not only the verification component; "Extensa mode" stays the SWDB mode name. Q22: the
  name is **Extensa Probata** ("Extensa, proven"), short form Probata. Glossary: Extensa Probata,
  verifier lineup, bounded verifier, unbounded verifier added.
- 2026-10-13 00:05 ET: concurrency survey, [`../research/11-concurrency-verification.md`](../research/11-concurrency-verification.md).
  No tool proves this C++/OpenMP code for every thread count as written. Best fit: reduction to a
  thread-indexed sequential program proven in WP for symbolic N (Lipton; Conc2Seq did this for
  Frama-C but is archived). Cross-check: VerCors only on a hand PVL model. Bounded refuter: CIVL
  1.23 (C + OpenMP, tries team sizes 1..k; needs JDK 17+, not installed; pass
  `-ompLoopDecomp=ALL`); GenMC second (weak memory, pthreads rewrite). Two code findings, checked
  in this session: (1) the tile path is correct only when team size equals the compile-time
  `NUM_CORES` (`bfs.cc:62-63` arrays sized `NUM_CORES`, chunk stride `NUM_CORES * tile_size` at
  `:142,195`; `Makefile:58` builds `NUM_CORES=4`); (2) the fallback path's plain `parent[v]` read
  and write race with other threads' CAS (`bfs.cc:205-210`, `:243-248`), a data race under OpenMP
  5.2 section 1.4.1 (survey's reading). New obligation: the DX100 store issued inside `critical`
  completes and is visible to other cores before the lock is released (visibility unconfirmed).
- 2026-10-13 00:32 ET: round 4 answers. Accepted: Q23 (any thread count means every N, built with
  `NUM_CORES` = N and run with N threads; a contract precondition with a run-time guard), Q25
  (DX100 store complete and visible before `critical` ends: passed to ticket 12, an assumption-set
  entry until then), Q26 (reduction: the C lowering also emits a thread-indexed sequential
  program proven in WP for symbolic N; side obligations proven or in the assumption set), Q27
  (CIVL 1.23 refuter, GenMC second; JDK installed in the proof of concept), Q28 (VerCors on a hand
  PVL model for BFS read offload only, labeled hand-made, sets no level, dropped first). Q24
  provisional (Yan-Ru unsure; revisit with proof-of-concept data): undefined behavior is a proof
  obligation, a racy candidate artifact is refuted. Q29 accepted: undefined behavior is a proof
  obligation; implementation-defined or unspecified behavior is an assumption-set entry naming the
  pinned platform's choice; behavior outside the language is trusted accelerator semantics. Q30
  accepted (replaces a proposed repair step Yan-Ru found manual): the baseline's meaning is its
  single-thread run; every candidate artifact, at any thread count, is compared against it; the
  authors' `TDStepMAA` is a candidate like any other, so its inherited racy fallback path is
  refuted at threads > 1 and reported as a finding.
- 2026-10-13 00:35 ET: Q31 accepted (a proven candidate artifact vs. the authors' code is a
  hypothesis for the evaluation, with the framing below). Yan-Ru confirmed the shared
  understanding.

## Answer

2026-10-13 00:35 ET. Decided with Yan-Ru in a grilling session (rounds 1-4 in Comments). Facts:
[`../research/11-verifier-facts.md`](../research/11-verifier-facts.md) and
[`../research/11-concurrency-verification.md`](../research/11-concurrency-verification.md).

**Name.** The paper's system is **Extensa Probata** ("Extensa, proven"; Probata after first use):
Extensa's loop plus the proven levels. "Extensa mode" stays the SWDB mode name.

**Terms.** No "tier" (it names the typed library's tiers). The **verifier lineup** fills two roles,
the **bounded verifier** and the **unbounded verifier** (glossary).

1. **Roles, not tools.** The bounded verifier gives proven-within-bounds verdicts and is the only
   source of refutations and counterexamples. The unbounded verifier gives proven-unbounded
   verdicts; its timeout or "unknown" means "not proven yet" and triggers the proof-hint loop,
   never a bug claim, never a proof. Order per candidate artifact: certified, then bounded, then
   unbounded (only after bounded proves). Each tool plugs in through an adapter: input is the C++
   proof unit or its C lowering plus generated summaries; output is proven, refuted with a
   counterexample, or not proven with a failure class. Tools may be swapped later; a swap reopens
   once-proven parts (ticket 10, item 6). The paper claims the method; the proof of concept names
   the tools.
2. **Bounded verifier: SAW 1.6** (Crucible family; macOS arm64), with specs generated from the
   formal halves and summaries as native `llvm_verify` overrides. Fallbacks in order: crux-llvm
   0.12 on the C++ (hand stubs as summaries), crux-llvm on the C lowering, CBMC 6.11 on the C
   lowering (`goto-instrument --dfcc`). **ESBMC is out** (timeouts in ticket 08). First
   proof-of-concept test: does SAW read clang 22 bitcode (its README claims LLVM 20).
3. **Unbounded verifier: Frama-C/WP 33.0** (Weakest Precondition) on a **C lowering** made by our
   own deterministic tool, never an LLM, for a declared C++ subset (templates instantiated,
   `enum class` as `int`, no `std` containers in the proof unit). Outside the subset, a candidate
   reaches at most proven within bounds. The lowering tool is a trusted-tool entry; the bounded
   verifier runs on both the C++ and the lowering and the verdicts must agree. Frama-Clang is a
   proof-of-concept experiment only.
4. **One summary source.** Summaries are generated from a library entry's formal halves as
   SAWScript specs, C call stubs (assert precondition, havoc writes, assume postcondition) and
   ACSL contracts. Only `assume`s a summary generates are allowed, each listed as that summary;
   any other `assume` voids the verdict (ticket 09, item 10).
5. **Two proof routes** (ticket 10): a single-program proof of the unit postcondition C, or a
   paired-program proof on a **product program we build** from the relational template's
   alignment, proven as an ordinary single program. RPP is out (no relational loop invariants).
6. **Floating point (PR, BC):** bounded runs use crux-llvm `-f real` until SAW's float mode is
   confirmed; WP uses `-wp-model +real`. The flag is always explicit and frozen (crux's default
   depends on the solver). Rounding stays an assumption-set entry.
7. **Lifting lemmas:** WP on the C lowering of the driver loop, the proof unit replaced by its
   contract. Induction through the `Wp.induction` tactic, saved as a script replayed on every run;
   Rocq in a separate opam switch is the fallback.
8. **Pinned:** tool, solver and front-end versions (clang 22.1.8) and flags are part of each
   content-hash set. WP uses a solver portfolio (Alt-Ergo, Z3, CVC5); a goal proven by any one
   counts, with the solver recorded per goal.
9. **Failures are root-caused.** Every "not proven" carries a class: parse error, unsupported
   construct, unwinding bound too small, timeout, out of memory, solver error, tool crash,
   vacuous pass. Each class has a handler (extend the lowering or the subset; fix the adapter;
   hint loop; watchdog and rerun with more memory; minimal reproduction). An unclassified failure
   stops the batch until its cause is named. Diagnosed failures join a regression corpus for the
   adapters.
10. **Concurrency, for any thread count:**
    - **Claim:** for every thread count N: no data race outside atomics and critical sections;
      each critical section atomic, so a run equals some serial order of atomic blocks; every
      serial order meets the unit relation; each thread uses only its own tiles with no DX100
      hazard; the chunks cover the frontier exactly once.
    - **Thread count** means every N, built with `NUM_CORES` = N and run with N threads: the tile
      path is correct only then (`apps/dx100/benchmarks/gapbs/src/bfs.cc:62-63,142,195`). A
      contract precondition with a run-time guard.
    - **Three methods, three jobs:** (A) reduction: the C lowering also emits a thread-indexed
      sequential program for symbolic N, proven in WP with the same summaries; the only method
      that sets the level. (C) bounded interleaving with **CIVL 1.23** (C + OpenMP, team sizes
      1..k, `-ompLoopDecomp=ALL`; JDK installed in the proof of concept); GenMC second (weak
      memory). (B) VerCors on a hand-written PVL model of BFS read offload only: a labeled
      cross-check and an A-vs-B comparison, setting no level, dropped first if time runs short.
    - **Negative controls:** `wait_ready(tile3)` moved outside `critical`; `critical` dropped; one
      tile shared by all threads; two chunks overlapping by one; the barrier before the fallback
      path dropped.
    - **Baseline at one thread:** the baseline's meaning is its single-thread run; every
      candidate artifact, at any thread count, is compared against it. Baseline races never
      matter.
    - **Order:** single thread first in the proof of concept; concurrency is in the first paper
      for BFS read offload. Until concurrency proofs exist no candidate reaches proven unbounded
      ("unbounded in every data dimension, threads = 1" is proven within bounds).
11. **Undefined behavior rule (all kernels):** behavior the language standard leaves undefined
    (data races, signed overflow, out-of-bounds access, a violated `__restrict__`, type punning)
    is a proof obligation; a bounded counterexample is a refutation. Implementation-defined or
    unspecified behavior (rounding, integer widths) is an assumption-set entry naming the pinned
    platform's choice. Behavior outside the language (DX100 completion and visibility) is trusted
    accelerator semantics (ticket 12). **Provisional (Q24):** a racy candidate artifact is
    refuted; in Extensa mode the counterexample goes to the rewriting LLM, not the hint agent.
    Revisit with proof-of-concept data.
12. **The authors' `TDStepMAA` is a candidate like any other.** Its fallback path, copied from
    GAPBS, reads and writes `parent[v]` plainly beside other threads' CAS (`bfs.cc:205-210`), a
    data race. It is refuted at threads > 1 and reported as a finding; its single-thread proof
    stands. The same pattern is in `bc.cc:106-107` and `sssp.cc:157-160`.
13. **Generality:** roles, adapters, the summary source, the two routes, the failure classes, the
    undefined-behavior rule and the concurrency claim apply to every kernel and contract.

**Hypothesis for the evaluation (Q31):** Probata yields a candidate artifact proven at every
thread count where the authors' code is refuted at threads > 1, with performance compared. The
framing: "a machine-checked guarantee at every thread count; expert code that was tested and
published contained UB that only a proof exposes." The defect is inherited from GAPBS, outside
the DX100 offload, a one-line fix, and harmless with today's compilers; it motivates, it is not
the headline.

**Corrections to research 02** (details in `research/11-verifier-facts.md`): VerCors 2.4.0 rejects
`omp parallel` blocks; SAW has experimental cutpoint loop invariants for bitcode; crux-llvm 0.12
supports LLVM 3.6-21; CBMC's contract flags are in `goto-instrument`.

**Inputs passed on:** store completion and cross-core visibility before `critical` ends, and
summaries in three forms carrying hazard state → ticket 12; timeout trigger, failure classes,
per-tool hint vocabulary, the summary-only `assume` rule, and racy candidates going to the
rewriting LLM → ticket 13; the concurrency design → new ticket 15; the Q31 hypothesis, the
A-vs-B comparison and CIVL bounds → the map's "Evaluation plan" fog; failure class and lineup
versions per verdict → the "Records" fog.

