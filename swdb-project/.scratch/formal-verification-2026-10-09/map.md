# Map: Formally verified rewrites (the "proven" certification level)

Created: 2026-10-09 14:02 ET
Updated: 2026-10-09 17:55 ET (ticket 14 pointer: gem5 wait rule implemented, with the dispatch stall)
**Type:** wayfinder map
**Status:** charted; research 02–06 and 14 resolved

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

## Tickets

| # | Ticket | Type | Status | Blocked by |
|---|---|---|---|---|
| 01 | [Charting decisions](issues/01-charting-decisions.md) | grilling | resolved | — |
| 02 | [Which existing formal verifiers can check our C++ code as-is?](issues/02-verifier-landscape.md) | research | resolved | — |
| 03 | [Prove a rewrite rule once, or validate each application?](issues/03-prove-once-rewrite-rules.md) | research | resolved | — |
| 04 | [How do LLMs build proof hints for existing verifiers?](issues/04-llm-proof-hints.md) | research | resolved | — |
| 05 | [How do verifiers model an accelerator's command interface?](issues/05-accelerator-interface-verification.md) | research | resolved | — |
| 06 | [Which papers are closest to ours?](issues/06-closest-prior-work.md) | research | resolved | — |
| 07 | [Install the shortlisted verifiers on the Mac](issues/07-install-verifiers.md) | task | ready-for-agent | 02 |
| 08 | [Can an off-the-shelf verifier tell a real DX100 wait bug from a safe one?](issues/08-wrong-tile-prototype.md) | prototype | ready-for-human | 07, 14 |
| 09 | [What does the "proven" level assert about a candidate artifact?](issues/09-what-proven-asserts.md) | grilling | ready-for-human | 03 |
| 10 | [What does a proven rewrite contract prove once?](issues/10-proven-rewrite-contract.md) | grilling | ready-for-human | 03, 09 |
| 11 | [Which verifiers form the bounded and unbounded tiers?](issues/11-verifier-choice.md) | grilling | ready-for-human | 02, 08, 09 |
| 12 | [What semantics do DX100 proofs trust?](issues/12-dx100-proof-semantics.md) | grilling | ready-for-human | 05, 08, 14 |
| 13 | [How does the proof-hint loop work?](issues/13-proof-hint-loop.md) | grilling | ready-for-human | 04, 09, 11 |
| 14 | [Does a DX100 wait on a store's source tile cover the store's result?](issues/14-dx100-wait-rule.md) | research | resolved | — |

## Not yet specified

- **Where real DX100 bugs may hide:** the two corners where the strict layer is looser than gem5
  (a range loop finishing early; memory effects applied at the call), and the same wait-on-source
  idiom in `apps/dx100/benchmarks/gapbs/src/pr.cc:242-245`.
- **Concurrency phase:** after single-thread proofs, the OpenMP hazards: parent compare-and-swap
  races, tiles shared between threads, the parent-gather race case. Which verifier handles threads.
- **Formal-half language:** what language clause formal halves use so the chosen verifier checks
  them, and how legality clauses L2–L5 (natural language only today) get formal halves. Waits on
  verifier choice.
- **Vacuity guard:** whether every negative control of a rewrite contract must also be refuted by
  the formal verifier, so a proof that also holds for broken code is caught.
- **Evaluation plan:** kernels beyond BFS (the authors' bc, pr and sssp rewrites; Extensa campaign
  artifacts), baselines (testing-only certification, verifier without hints, hints without
  contracts), metrics (proof rate, time, hint rounds, bugs found).
- **Records:** how proven verdicts, bounds, hints and counterexamples are stored in the research
  database and shown in ArchEvolve mode.
- **Extensa-mode loop:** the proving budget per iteration, and how ranking by proven level
  changes selection.

## Out of scope

Ruled at charting ([01](issues/01-charting-decisions.md)):

- Compiler correctness: gcc and clang are trusted.
- DX100 hardware versus its functional model: the strict layer is the trusted semantics.
- Speed: proofs say nothing about performance.
- gem5.
