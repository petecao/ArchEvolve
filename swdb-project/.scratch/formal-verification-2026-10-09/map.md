# Map: Formally verified rewrites (the "proven" certification level)

Created: 2026-10-09 14:02 ET
Updated: 2026-10-13 16:47 ET (ticket 17 resolved: enabling rewrites and rewrite chains);
2026-10-13 16:09 ET (ticket 15 resolved: concurrency proofs for any thread count;
ticket 17 added; VerCors out of scope); 2026-10-13 15:22 ET (ticket 13 resolved: the proof-hint loop);
2026-10-13 14:19 ET (ticket 12 resolved: the proof semantics; ticket 16 added);
2026-10-13 00:35 ET (ticket 11 resolved: verifier lineup, concurrency, the name
Extensa Probata; ticket 15 added); 2026-10-12 22:52 ET (ticket 10 resolved: what a contract proves once);
2026-10-12 22:25 ET (ticket 09 resolved: what proven asserts; generality requirement added);
2026-10-11 18:58 ET (ticket 08 resolved: crux-llvm separates the bug at one lane)
**Type:** wayfinder map
**Status:** charted; research 02–06 and 14, task 07, prototype 08, grilling 09–13, 15 and 17 resolved

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
- [How do enabling rewrites chain with offloading rewrites?](issues/17-enabling-rewrites.md):
  matching and splitting: a catalog of five recurring reshapes (chunking, fallback, phase split,
  buffers, edge-loop flattening), each with a template proven once; offloads become offload-only
  contracts that name the enabling contracts they need; bundled contracts stay legal. BFS proves
  the final candidate against the baseline directly; a rewrite that changes the thread split is
  proven against the baseline, one that keeps it per thread against its predecessor; a failed
  rewrite falls back to a bounded direct check. Certified enabling results become derived
  implementations; each rewrite is certified alone. The race fix stays repair. Proof of concept:
  Peter's read offload, chained vs bundled.

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
| 16 | [What language do formal halves and the proof semantics share?](issues/16-formal-half-language.md) | grilling | ready-for-human | 11, 12 |
| 17 | [How do enabling rewrites chain with offloading rewrites?](issues/17-enabling-rewrites.md) | grilling | resolved | 15 |

## Not yet specified

- **Scaling past one lane:** what bound a proven-within-bounds verdict needs (2-lane tiles, more
  edges), and which engine or encoding reaches it. 08 showed crux-llvm cannot prove 2 lanes in
  15 minutes on the Mac. 09 settled how bounds are declared (per contract dimension, threads
  included); 11 chose SAW, whose summaries are native `llvm_verify` overrides, as the bounded
  verifier. 10's hypothesis: summaries in place of the inlined strict-layer port bring 2 lanes
  under 15 minutes.
- **Where real DX100 bugs may hide:** per 12, the strict layer's two looser corners are closed
  for proofs (the range-loop corner is in certify 1.7; memory timing is in the proof semantics),
  and the wait-on-source idiom in `apps/dx100/benchmarks/gapbs/src/pr.cc:242-245` is safe under
  the gem5 rule. Left: stale CPU copies after a DX100 store (assumed, owner Eric; research 12),
  and the two gem5 corners research 12 could not rule out. (Peter's plain store after the CAS is
  a data race, refuted at N > 1 per 15.) Per 17 (read from code, not run): DX100 PR never resets
  `incoming_totals` between iterations (`apps/dx100/benchmarks/gapbs/src/pr.cc:140-141,183,242`;
  the baseline resets, `:100`); scores look wrong from iteration 2. Needs a run check.
- **Evaluation plan:** kernels beyond BFS, required by the generality note (the DX100 authors'
  code covers bfs top-down and bottom-up (`bfs_bu.cc`), bc, pr and sssp; cc and tc have none;
  Extensa campaign artifacts), baselines (testing-only certification, verifier without hints,
  hints without contracts), metrics (proof rate, time, hint rounds, bugs found). Per 09, each
  evaluated kernel needs an output relation and, per contract, a unit relation and a lifting
  lemma. Per 10, each contract also needs a reference instance and a contract proof. Per 11: the
  hypothesis "a proven candidate artifact vs. the authors' code at every thread count, with
  performance compared" (the authors' fallback path races); CIVL team-size bounds. Per 15: the
  ladder per candidate (SAW threads = 1, CIVL threads <= k, WP every N); CIVL and GenMC agreement;
  eight concurrency controls (seven refuted, one proven); all three candidates as written vs
  repaired at every N; the outcome of the Rocq time-box for the parallel composition theorem. Per 12: the semantics negative controls, and the strict layer catching
  up to the proof semantics (memory footprints, the other-thread read rule) as a new certify
  version. Per 13: the proof rate as a curve over the budget (no-hint baseline at equal wall
  time); calibration on public C suites plus the BFS proof of concept, held-out kernels for the
  evaluation, recalibration on mbit10; seeds on and off (a paper feature, Yan-Ru); escape-hatch
  attempts by rule; C-lowering subset coverage on campaign candidates; check the ESBMC-AI
  citation (counterexample-guided LLM repair for C) for positioning. Per 17: Peter's read offload
  chained (catalog rewrites plus an offload-only read offload) vs bundled, comparing proof time
  and hint rounds; then, only if that passes, upstream GAPBS `TDStep` as an "any input" demo; the
  five catalog templates' proofs (about one month).
- **Records:** how proven verdicts, bounds, hints and counterexamples are stored in the research
  database and shown in ArchEvolve mode. Per 09, a verdict also carries its assumption set (each
  entry with its kind), a value or "unbounded" per bound dimension, and the cap from proven
  dependencies. Per 10, each once-proven part records its level and the content hashes it holds
  for; a changed hash reopens it. Per 11, every "not proven" records its failure class, and every
  verdict its verifier lineup versions, solvers and flags. Per 12, every verdict names the proof
  semantics version and its agreement evidence (fixture differences, semantics controls). Per
  13: hint sets with provenance, rejections by rule, rounds, provider calls, tokens and time,
  refutation replay status, and the hint vocabulary and check versions. Per 15: CIVL and GenMC
  settings (version, k or thread count, input and loop bounds, flags, memory-model encoding); the
  parallel composition theorem's version and status (Rocq-checked or written); the OpenMP runtime
  and RC11 entries. Per 17: per rewrite in a rewrite chain, its contract hash, predecessor snapshot
  hash, result hash, certification record and proof route; derived implementations' contract
  lineage (`applies` lists only strategies today).
- **Extensa-mode loop:** the proving budget per iteration, and how ranking by proven level
  changes selection. Per 13: lane-hours proofs may use on mbit10 per campaign (proof jobs run
  inside a socket lane), and the counterexample-guided repair budget per refuted candidate. Per
  17: an iteration may start from a certified derived implementation; only final candidate
  artifacts are ranked and use lane-hours.
- **Direct unbounded proofs without a template** (from 17): a final candidate artifact whose chain
  fails to prove reaches at most proven within bounds, because a direct relational proof needs an
  alignment nothing supplies. An "alignment" proof-hint kind would add an unbounded route (it
  widens 13's vocabulary).

## Out of scope

Ruled at charting ([01](issues/01-charting-decisions.md)):

- Compiler correctness: gcc and clang are trusted.
- DX100 hardware versus its functional model: the strict layer is the trusted semantics.
- Speed: proofs say nothing about performance.
- gem5.

Ruled during the route:

- VerCors on a hand-written PVL model ([15](issues/15-concurrency-proofs.md), item 13): hand-made,
  BFS only, sets no level; against "any input" and the cost rule.
