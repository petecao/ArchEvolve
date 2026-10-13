# Map: Formally verified rewrites (the "proven" certification level)

Created: 2026-10-09 14:02 ET
Updated: 2026-10-13 19:48 ET (ticket 18 resolved: evaluation claims and subjects);
2026-10-13 17:53 ET (ticket 21 resolved: relational alignment research);
2026-10-13 17:32 ET (ticket 22 resolved: counterexample-guided LLM repair prior work);
2026-10-13 17:04 ET (all fog graduated into tickets 18–27; ticket 18 claimed);
2026-10-13 16:49 ET (ticket 16 resolved: ACSL formal halves in a YAML frame);
2026-10-13 16:47 ET (ticket 17 resolved: enabling rewrites and rewrite chains);
2026-10-13 16:09 ET (ticket 15 resolved: concurrency proofs for any thread count;
ticket 17 added; VerCors out of scope); 2026-10-13 15:22 ET (ticket 13 resolved: the proof-hint loop);
2026-10-13 14:19 ET (ticket 12 resolved: the proof semantics; ticket 16 added);
2026-10-13 00:35 ET (ticket 11 resolved: verifier lineup, concurrency, the name
Extensa Probata; ticket 15 added); 2026-10-12 22:52 ET (ticket 10 resolved: what a contract proves once);
2026-10-12 22:25 ET (ticket 09 resolved: what proven asserts; generality requirement added);
2026-10-11 18:58 ET (ticket 08 resolved: crux-llvm separates the bug at one lane)
**Type:** wayfinder map
**Status:** charted; research 02–06 and 14, task 07, prototype 08, grilling 09–13 and 15–17 resolved;
18–27 graduated from fog 2026-10-13 (18, 21, 22 resolved)

## Destination

A research design spec for the "proven" certification level: claims, method (what "proven"
asserts, verifier choice, the proof-hint loop), the DX100 BFS proof of concept, the evaluation
plan, and positioning against prior work. Ready to cut into build tickets. Running the proof of
concept is the next effort.

## Notes

- **Domain:** Yan-Ru's next paper (Extensa mode is its core) and ArchEvolve mode (shows LANL the
  novelty through the team; no direct LANL contact). No deadline; sooner is better.
- **Terms:** `../../GLOSSARY.md`. What we verify is a candidate artifact's change against the
  rewrite contract it applies. Avoid "transformation" and "optimization" alone.
- **Skills:** grilling tickets call `mattpocock-skills:grilling` and
  `mattpocock-skills:domain-modeling`. Research tickets call
  `academic-research-skills:deep-research` (lit-review discipline, every citation checked) and
  `mattpocock-skills:research`. Prototype tickets call `mattpocock-skills:prototype`.
- **Planning only.** Prototype code is throwaway and stays in `prototype/`. Nothing in `swdb/` or
  `library/` changes from this map.
- **Why this attempt differs:** Extensa's SMT, pet+ISL and libTooling legality gates did not
  scale on real benchmarks ("proofs don't construct or scale … pivot to TESTING",
  `MemAcc/AgenticRefiner/docs/superpowers/2026-06-23-session-handoff-legality-testing-gate.md:9`).
  Every method decision must say what changes that outcome.
- **Research output:** `research/NN-<slug>.md`, linked from each research ticket's answer.
- **Disk:** tool installs keep at least 50 GB free on the Mac.
- **Name (Yan-Ru, 2026-10-13):** the paper's system is **Extensa Probata** (Probata after first
  use): Extensa's loop plus the proven levels. "Extensa mode" stays the SWDB mode name.
- **Generality (Yan-Ru, 2026-10-12):** the method must be general, not BFS-specific. The
  evaluation covers other GAPBS kernels. Every claim and method decision must say how it applies
  beyond BFS.
- **Any input (Yan-Ru, 2026-10-13):** ArchEvolve must handle any input code, not only code an
  expert already reshaped for DX100. Peter's and Josh's code is preliminary and tentative: a
  proof-of-concept candidate, never ground truth.
- **Automation and cost (Yan-Ru, 2026-10-13):** minimize human effort and construct proofs as
  automatically as possible. Formal by default, but trade off: about one month of work per piece
  (not absolute), and do the chosen option well.

## Context pointers

- [01 — Charting decisions](issues/01-charting-decisions.md): headline method = contracts proven
  once + LLM proof hints (bugs are evidence); both modes; proven unbounded > proven within bounds >
  certified; single thread, then concurrency; hints never assume; three proof-of-concept
  candidates should be proven (authors' version under a gem5-matching wait rule, amended after
  14); seeded real bugs must be refuted.
- [03 — Prove a rewrite rule once, or validate each application?](issues/03-prove-once-rewrite-rules.md):
  staged hybrid. Proven once per contract: building blocks against reference semantics, contract
  lemmas, a relational template. Per candidate artifact: one small relational proof of one
  `TDStep` call. BFS outputs compared as visited and per-level frontier sets plus parent validity.
- [06 — Which papers are closest to ours?](issues/06-closest-prior-work.md): gap is real but
  narrow; claim the combination plus the DX100 offload, never "first". Closest: Trivet (LLM fills
  Lean proof holes when Alive2 times out), LLMLift, ProofWright.
- [05 — How do verifiers model an accelerator's command interface?](issues/05-accelerator-interface-verification.md):
  no prior work has "sentinel until covering wait"; closest is Cell DMA race checking. Split DX100
  proofs into hazards (proof edition of the strict layer) and function (instant completion),
  linked by a reduction lemma. Raised ticket 14: the wrong-tile bug may be our assumption.
- [04 — How do LLMs build proof hints for existing verifiers?](issues/04-llm-proof-hints.md):
  the LLM proposes, the verifier decides; unknown is never evidence. Loop: bounded run, hint
  overlay, deterministic checker (strip-and-diff, banned constructs, flags frozen), prove every
  hint, minimize, vacuity and negative-control checks, about 10 rounds.
- [02 — Which existing formal verifiers can check our C++ code as-is?](issues/02-verifier-landscape.md):
  none reads `bfs.cc` whole; all need a harness built without OpenMP. Bounded: ESBMC (reads the
  C++ as-is), crux-llvm/SAW, CBMC (C port only). Unbounded: Frama-C/WP + RPP (C port), ESBMC
  k-induction, VerCors (OpenMP, for the concurrency phase). Alive2 stays out.
- [14 — Does a DX100 wait on a store's source tile cover the store's result?](issues/14-dx100-wait-rule.md):
  yes. On gem5 the authors' `TDStepMAA` is SAFE; the "wrong-tile bug" exists only under our
  stricter strict-layer rule. The strict layer is looser than gem5 in two corners (range-loop
  early finish; memory effects applied at the call). Invalidates 01 decision 9.1.
  *2026-10-09 17:55 ET:* now implemented as candidate certify 1.7 and lowering certify 1.2, both
  defaults, including the dispatch stall on tiles (IF.cc:193-212). Calibration and Peter's and BC's
  read offloads certify. Memory timing stays open. See the
  [evidence note](evidence/strict-gem5-wait-rule-redeclaration-20261009.md).
- [Install the shortlisted verifiers on the Mac](issues/07-install-verifiers.md): all four run
  and pass a safe smoke program but not a seeded bug: ESBMC 8.5, CBMC 6.11, crux-llvm 0.12
  (only on prebuilt clang-22 bitcode with `--no-compile`), and Frama-C 33.0 + RPP 0.0.4 (opam
  switch `framac-33`; use `-then-last`). WP reports a bug as timeout, never as refuted. The
  install's z3 upgrade broke the LLVM 22 the analytic evaluator needs; repaired, but fragile.
- [Can an off-the-shelf verifier tell a real DX100 wait bug from a safe one?](issues/08-wrong-tile-prototype.md):
  yes at one lane, with crux-llvm on an array port of the strict layer (66-run differential
  match). The authors' wait is proven under the gem5 rule and refuted under the old one. Three
  seeded bugs are refuted. ESBMC timed out on the header and on the port. Two lanes do not
  finish in 15 minutes.
- [What does the "proven" level assert about a candidate artifact?](issues/09-what-proven-asserts.md):
  the rewrite is proven against its contract: formal halves hold, one proof unit (one `TDStep`
  call) refines the baseline modulo the contract's unit relation, and no accelerator hazards. A
  machine-checked lifting lemma per contract and kernel extends it to the kernel's output
  relation. Proven requires certified; every verdict lists its assumption set and per-dimension
  bounds (threads always a bound). Floating point compares over real arithmetic. 08's harness
  `assume` on `parent[]` misses real inputs.
- [What does a proven rewrite contract prove once?](issues/10-proven-rewrite-contract.md):
  staged hybrid. Building blocks are proven once with their library entry and used as summaries.
  The contract proof holds a unit postcondition (BFS) or relational template (PR, BC), proven on a
  reference instance, its lifting lemma per kernel, and its negative controls refuted. Per
  candidate: one automatic proof unit. Each clause names its proof placement; each part carries
  its own level, per content-hash set. Scale is a hypothesis: 2 lanes in under 15 minutes with
  summaries.
- [Which verifiers form the bounded and unbounded tiers?](issues/11-verifier-choice.md):
  roles, not tools: the bounded verifier (SAW 1.6; crux-llvm, CBMC fallbacks; ESBMC out) is the
  only refuter; the unbounded verifier (WP on our deterministic C lowering) proves, and its
  timeout triggers hints. One summary source, own product programs (RPP out), real-arithmetic
  floats, failures root-caused. Concurrency for any N (`NUM_CORES` = N): reduction in WP sets the
  level, CIVL refutes, VerCors cross-checks. Undefined behavior is a proof obligation; the
  baseline is its single-thread run; the authors' racy fallback path is refuted at N > 1. Name:
  Extensa Probata.
- [What semantics do DX100 proofs trust?](issues/12-dx100-proof-semantics.md):
  a separate **proof semantics**: one contract per `maa_*` call over ghost hazard state, each rule
  citing gem5 source or marked assumed. The functional model is a testing aid; the strict layer is
  the executable counterpart, kept in agreement by fixtures and semantics negative controls.
  Values as if finished at issue plus hazard assertions, joined by a reduction lemma. Unready
  reads and per-element memory-footprint overlaps are hazards, except another thread's write
  beside a DX100 read (Peter's pattern). Stops at the `maa_*` calls. L3, L5 become cited rules;
  stale CPU copies after a DX100 store stay assumed (owner Eric).
- [How does the proof-hint loop work?](issues/13-proof-hint-loop.md):
  three loops kept apart: Extensa mode (rewrites for speed), counterexample-guided repair
  (refutation → rewriting role) and the proof-hint loop (never changes code). A new
  `proof_hinting` role (default Codex) writes anchored ACSL records on the C lowering, for WP only;
  SAW stays hint-free. A versioned vocabulary, three checks (setup, hint, per-property verdict
  reading; WP's `[ Valid ]` and cache can mislead), hint seeds (a paper feature), and refutations
  called "bug" only with a whole-kernel reproduction. Budget starts at 10 rounds / 60 min,
  calibrated then frozen. Proof of concept on the Mac; final evaluation on mbit10.
- [How do proofs cover concurrency for any thread count?](issues/15-concurrency-proofs.md):
  WP proves one symbolic thread of N; other threads appear only through the contract's shared
  actions (a fixed set of kinds, each with a commutativity lemma). A parallel composition theorem,
  written by Codex in Rocq and checked there (time-boxed, written fallback), lifts it to every N.
  Reads that race on purpose are history reads (RC11); any other race refutes. CIVL gives proven
  within bounds for threads <= k, GenMC refutes, both must agree. All three proof-of-concept
  candidates race at N > 1 as written and go to repair. VerCors out; enabling rewrites to 17.
- [What language do formal halves and the proof semantics share?](issues/16-formal-half-language.md):
  ACSL inside a YAML frame: WP reads it as is; our translators make the SAWScript specs and C
  stubs; the Extensa grammar stays for runtime probes. First-order ACSL with bounded quantifiers
  and primitive recursion only; the C lowering keeps C++ names; relations are two-sided
  predicates. Every clause names its proof placement (BFS read offload: all per candidate except
  L5); sharing classes per barrier interval are per candidate. The C++ subset is defined by
  construct and includes a modeled `std::vector`. Ghost hazard state in fixed-size arrays (32
  command slots); new 8-byte tile-pair rule. An agent drafts missing formal halves behind five
  gates; our own check mode replaces E-ACSL, which drops `\old` under quantifiers.
- [How do enabling rewrites chain with offloading rewrites?](issues/17-enabling-rewrites.md):
  matching and splitting: a catalog of five recurring reshapes (chunking, fallback, phase split,
  buffers, edge-loop flattening), each with a template proven once; offloads become offload-only
  contracts that name the enabling contracts they need; bundled contracts stay legal. BFS proves
  the final candidate against the baseline directly; a rewrite that changes the thread split is
  proven against the baseline, one that keeps it per thread against its predecessor; a failed
  rewrite falls back to a bounded direct check. Certified enabling results become derived
  implementations; each rewrite is certified alone. The race fix stays repair. Proof of concept:
  Peter's read offload, chained vs bundled.
- [Which methods find a relational proof's alignment automatically, and can a wrong one make a proof unsound?](issues/21-relational-alignment-research.md):
  a wrong alignment only fails, provided guard agreement, adequacy and fairness are proven (WP can
  state all three with 13's kinds); assumed, proofs go vacuous. Aligners all guess and check; no
  LLM-proposed alignment found. Costly (45 CPU-hours per TSVC pair). Loop flattening and unbounded
  reordering are known blind spots, which questions 17's catalog estimate (risk to 27).
- [Which LLM repair loops driven by model-checker counterexamples exist, and how close are they to ours?](issues/22-cex-guided-llm-repair-research.md):
  ESBMC-AI is AST 2025 (cite that, not the preprint): safety-only repair, rechecked by ESBMC at
  unwind bound 1. Closest new work: T-LLM Compiler (bounded CBMC equivalence plus an LLM judge; 33.8% false
  acceptance). Relational loops exist, all per program; LLM race repair only for Java and Go; no
  accelerator-hazard repair. The term is already used (Orvalho et al.; AuthFix). Five mirror
  baselines go to 23.
- [What does the evaluation set out to show, and on which kernels and candidate artifacts?](issues/18-evaluation-claims-and-subjects.md):
  five research questions (automation, hints and seeds, once vs per candidate, refutation and
  repair, end to end for BFS), each with a pass bar fixed at the freeze. BFS calibrates; BC, PR and
  SSSP are held out (BFS bottom-up, CC, TC dropped), against the fork's baselines. Per contract, 20
  certified Codex candidates plus the authors' code, repairs and seeded faults; held-out contracts
  drafted blind to the authors' code. Freeze the method version first; fix the authors'-code guard
  first. Cut RQ5, then PR.

## Tickets

| # | Ticket | Type | Status | Blocked by |
|---|---|---|---|---|
| 01 | [Charting decisions](issues/01-charting-decisions.md) | grilling | resolved | — |
| 02 | [Which existing formal verifiers can check our C++ code as-is?](issues/02-verifier-landscape.md) | research | resolved | — |
| 03 | [Prove a rewrite rule once, or validate each application?](issues/03-prove-once-rewrite-rules.md) | research | resolved | — |
| 04 | [How do LLMs build proof hints for existing verifiers?](issues/04-llm-proof-hints.md) | research | resolved | — |
| 05 | [How do verifiers model an accelerator's command interface?](issues/05-accelerator-interface-verification.md) | research | resolved | — |
| 06 | [Which papers are closest to ours?](issues/06-closest-prior-work.md) | research | resolved | — |
| 07 | [Install the shortlisted verifiers on the Mac](issues/07-install-verifiers.md) | task | resolved | — |
| 08 | [Can an off-the-shelf verifier tell a real DX100 wait bug from a safe one?](issues/08-wrong-tile-prototype.md) | prototype | resolved | — |
| 09 | [What does the "proven" level assert about a candidate artifact?](issues/09-what-proven-asserts.md) | grilling | resolved | 03 |
| 10 | [What does a proven rewrite contract prove once?](issues/10-proven-rewrite-contract.md) | grilling | resolved | 03, 09 |
| 11 | [Which verifiers form the bounded and unbounded tiers?](issues/11-verifier-choice.md) | grilling | resolved | 02, 08, 09 |
| 12 | [What semantics do DX100 proofs trust?](issues/12-dx100-proof-semantics.md) | grilling | resolved | 05, 08, 14 |
| 13 | [How does the proof-hint loop work?](issues/13-proof-hint-loop.md) | grilling | resolved | 04, 09, 11 |
| 14 | [Does a DX100 wait on a store's source tile cover the store's result?](issues/14-dx100-wait-rule.md) | research | resolved | — |
| 15 | [How do proofs cover concurrency for any thread count?](issues/15-concurrency-proofs.md) | grilling | resolved | 11, 12 |
| 16 | [What language do formal halves and the proof semantics share?](issues/16-formal-half-language.md) | grilling | resolved | 11, 12 |
| 17 | [How do enabling rewrites chain with offloading rewrites?](issues/17-enabling-rewrites.md) | grilling | resolved | 15 |
| 18 | [What does the evaluation set out to show, and on which kernels and candidate artifacts?](issues/18-evaluation-claims-and-subjects.md) | grilling | resolved | — |
| 19 | [How are a bounded verdict's bounds chosen, and when are they enough?](issues/19-bounded-verdict-bounds.md) | grilling | claimed | — |
| 20 | [Does the authors' DX100 PageRank keep stale `incoming_totals` across iterations?](issues/20-dx100-pr-reset-check.md) | task | ready-for-agent | — |
| 21 | [Which methods find a relational proof's alignment automatically, and can a wrong one make a proof unsound?](issues/21-relational-alignment-research.md) | research | resolved | — |
| 22 | [Which LLM repair loops driven by model-checker counterexamples exist, and how close are they to ours?](issues/22-cex-guided-llm-repair-research.md) | research | resolved | — |
| 23 | [Which baselines, ablations and metrics answer each research question, and how are runs repeated?](issues/23-evaluation-baselines-and-metrics.md) | grilling | ready-for-human | 18, 22 |
| 24 | [Should the proof-hint loop gain an alignment hint kind for direct unbounded proofs?](issues/24-alignment-hint-kind.md) | grilling | ready-for-human | 21 |
| 25 | [How does the Extensa-mode loop budget proofs and rank candidate artifacts by certification level?](issues/25-extensa-loop-proofs-and-ranking.md) | grilling | ready-for-human | 19 |
| 26 | [How are proof verdicts and their evidence recorded, and what does ArchEvolve mode show?](issues/26-proof-records.md) | grilling | ready-for-human | 23, 25 |
| 27 | [In what order does the proof of concept build its pieces, and what closes each stage?](issues/27-proof-of-concept-stages.md) | grilling | ready-for-human | 18, 19, 24 |

## Not yet specified

Empty since 2026-10-13 17:04 ET. Each patch graduated into tickets:

- **Scaling past one lane** → 19 (bounds policy); 10 item 9's 2-lane pass bar → 27.
- **Where real DX100 bugs may hide** → 20 (the PR `incoming_totals` run check). The rest is decided:
  stale CPU copies and the two gem5 corners are assumption entries (12 item 7, owner Eric); the
  8-byte tile pair is a proof-semantics rule (16 item 11); Peter's plain store is a race (15).
- **Evaluation plan** → 18 (claims, kernels, candidates, split), 23 (baselines, ablations, metrics,
  protocol), 27 (proof-of-concept stages); the ESBMC-AI check → 22.
- **Records** → 26.
- **Extensa-mode loop** → 25.
- **Direct unbounded proofs without a template** → 21 (research), 24 (decision).

## Out of scope

Ruled at charting ([01](issues/01-charting-decisions.md)):

- Compiler correctness: gcc and clang are trusted.
- DX100 hardware versus its functional model: the strict layer is the trusted semantics.
- Speed: proofs say nothing about performance.
- gem5.

Ruled during the route:

- VerCors on a hand-written PVL model ([15](issues/15-concurrency-proofs.md), item 13): hand-made,
  BFS only, sets no level; against "any input" and the cost rule.
