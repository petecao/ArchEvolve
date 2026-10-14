# 13 — How does the proof-hint loop work?

Created: 2026-10-09
Updated: 2026-10-13 15:22 ET (resolved with Yan-Ru in three grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 14:22 ET)
**Blocked by:** 04, 09, 11
**Map:** `../map.md`

## Question

How does the proof-hint loop work?

- Who writes proof hints: a new proving agent role or the rewrite provider? (The DX100 authors'
  code has no rewrite provider.)
- What the agent sees: verifier output, counterexamples, the contract.
- The checker that enforces the hint rules in 01.
- The budget per candidate artifact.
- What each verdict does: proven sets the level; refuted is replayed as a concrete test before it
  counts as a bug; unknown after the budget leaves the candidate certified.

## Comments

- 2026-10-09: input from 06: Trivet already gates LLM proofs (no `sorry`/`admit`, statement
  unchanged); cite it, ours is the C/C++ form. Its gains came from a fixed proof scaffold with
  small holes for the LLM; a proven rewrite contract could supply that scaffold.
- 2026-10-09: input from 04: recommended loop and two-part soundness guard in
  `../research/04-llm-proof-hints.md`. Gaps in 01 decision 8 to settle here: CBMC loop
  invariants also need `assigns` and `decreases` clauses; CBMC has no ghost variables, so the
  checker must keep ghost state apart from real code; callee contracts and verifier flags are
  escape hatches; the trigger should be "anything below proven unbounded", not only timeout or
  unknown. Baselines: "verifier without hints" at equal wall time (Quokka: hints add 0–3 solves
  at 500 s; most gain is speed).
- 2026-10-09: input from 02: ESBMC and CBMC have no lemma construct and their ghost variables
  are ordinary variables; Frama-C/WP accepts `axiom` and `admit` without proof, so the checker
  must reject both.
- 2026-10-12 22:25 ET: input from 09: the checker must inventory every `assume` in a harness and
  map each one to a proof at the real call site or to a reduction listed in the assumption set;
  an unmapped `assume` voids the verdict. 08's harness already has one
  (`../prototype/08-wrong-tile/tdstep_harness.cpp:74` assumes `parent[v] >= -1`; real callers pass
  `-out_degree`).
- 2026-10-12 22:52 ET: input from 10: (1) contract proofs may be human-assisted (Yan-Ru writes hints or
  proofs, reviewed at promotion) under the same hint rules; candidate proofs stay fully
  automatic. (2) Each clause names its proof placement (once, per candidate, or assumed); the
  checker confirms every clause is covered by a proof or the assumption set. (3) Negative
  controls are refuted once per contract on its reference instance; vacuity checks per
  candidate stay here.
- 2026-10-13 00:35 ET: input from 11: (1) the trigger includes the unbounded verifier's timeout and
  "unknown": "not proven yet", never a bug or a proof. (2) Every "not proven" carries a failure
  class; only timeout (and proven-within-bounds verdicts) go to the hint loop; parse errors,
  unsupported constructs, memory and crashes have fixed handlers; an unclassified failure stops
  the batch. (3) Hint vocabulary per tool: WP (the unbounded verifier) has ghost code, lemmas,
  loop invariants, assertions and `Wp.induction` scripts; SAW (the bounded verifier) has only
  experimental cutpoint loop invariants, so hints mostly target WP. ESBMC and RPP are out.
  (4) The checker allows only `assume`s a summary generates. (5) A racy candidate artifact is
  refuted, and the counterexample goes to the rewriting LLM, not the hint agent (provisional).
- 2026-10-13 14:19 ET: input from 12: (1) a hazard is an assertion failure at an unready read, not
  a fixed or arbitrary value; on the C++ path the harness generator places a probe before each
  tile read loop, in the C lowering a check sits at each read. The checker must confirm these
  probes are present and generated, not hint-written. (2) A refutation replays on the strict
  layer before it counts as a bug, but rules only the proof semantics has (memory footprints,
  timing-dependent `get_tile_ready`, the other-thread read rule) cannot replay there until the
  strict layer catches up. Decide how such a refutation is reported.
- 2026-10-13 15:05 ET: grilling round 1 with Yan-Ru (checkpoint; not yet the answer).
  Facts gathered first: [`../research/13-wp-hint-facts.md`](../research/13-wp-hint-facts.md)
  (WP escape hatches; reproduced by `../prototype/13-wp-hint-facts/run.sh`).
  1. Q1 accepted: a new agent role, `proof_hinting`, writes proof hints and never edits code.
     **Default provider: Codex** (Yan-Ru). Provider kind recorded per hint set.
  2. Q2 questioned ("are you sure?"); re-checked in round 2.
  3. Q3 accepted: refutation evidence steps: unit refuted (SAW counterexample; blocks proven for
     that hash), replay on the strict layer (reproduced / proof semantics only, citing the gem5
     rule / not reproduced, which stops the batch), and "bug" only with a whole-kernel
     reproduction.
  4. Q4 accepted: a refuted candidate keeps its test record, leaves selection, and its
     counterexample goes to the rewriting role as correctness-repair feedback, never to the hint
     agent. Yan-Ru: this forms a counterexample-guided loop (term settled in round 2).
  5. Q5 accepted: before recording proven: smoke tests, one greedy minimization pass, full record.
  6. Q6 accepted with a change: 10 rounds / 60 min / 30 s per solver are starting values only;
     Yan-Ru wants them tuned by evaluation (rule settled in round 2).
- 2026-10-13 15:14 ET: grilling round 2 (checkpoint). Yan-Ru's "Q6 ok" read as accepting the Q2 re-check.
  1. Q2 accepted after re-check: hints go to WP only. SAW cutpoints need a call inserted in the
     loop condition and `llvm_unsafe_assume_spec` (`../research/11-verifier-facts.md:175-179`), both
     against 01 decision 8. The lowering subset must map `std::copy`/`std::swap` (GAPBS
     `QueueBuffer`, `pvector`); the proof of concept measures subset coverage on campaign
     candidates.
  2. Q7 accepted: budget values are run-plan parameters, calibrated on public C suites plus the
     BFS proof of concept, frozen, then evaluated on held-out kernels (bc, pr, sssp, bfs
     bottom-up); proof rate reported as a curve over the budget, with the no-hint baseline at
     equal wall time.
  3. Q8 accepted: "counterexample-guided repair" (glossary); avoid "refinement". Prior work
     (e.g., ESBMC-AI, Tihanyi et al. 2023; citation not yet checked): claim the combination.
  4. Q9 accepted: hints are `{anchor, kind, text}` records merged by a deterministic tool at
     lowering-generated anchors; erase-and-diff as second guard.
  5. Q10 accepted for now (Yan-Ru may change it later): allowed kinds are loop invariant /
     assigns / integer variant, assert, ghost declarations and statements, non-recursive
     definitions, lemmas proven in the same run, `\wp::strategy` tactics. Everything else rejected.
  6. Q11 accepted: workspace as proposed; the agent may run WP and the hint check through a frozen
     wrapper; verdicts only from the loop's own run (`-wp-cache none`, fresh session); hint
     records never enter a rewriting workspace.
  7. Q12 changed: proof of concept on the Mac; **final evaluation and experiments on mbit10**
     (Yan-Ru).
- 2026-10-13 15:22 ET: grilling round 3 (checkpoint). Q13-Q18 accepted. Yan-Ru on Q15: hint seeds are a
  feature to present and discuss in the paper submission. Yan-Ru asked whether there are two
  loops (Extensa's rewriting loop and the proof loop); there are three, named in the Answer.

## Answer

2026-10-13 15:22 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments). Facts:
[`../research/13-wp-hint-facts.md`](../research/13-wp-hint-facts.md), reproduced by
[`../prototype/13-wp-hint-facts/run.sh`](../prototype/13-wp-hint-facts/run.sh).

**Three loops, kept apart** (glossary):

| Loop | Scope | Changes code? | Driven by |
|---|---|---|---|
| Extensa mode | a campaign | yes: new rewrites | performance |
| Counterexample-guided repair | a refuted candidate artifact | yes: a repaired candidate | a bounded counterexample |
| Proof-hint loop | one proof unit of one candidate artifact | never | WP goals not proven |

1. **Who writes hints:** a new agent role, `proof_hinting`. Its proof-hint agent writes hints and
   never edits code. Default provider: **Codex**; the provider kind is recorded per hint set. The
   rewrite provider never writes hints (the authors' code has none).
2. **Where hints live:** ACSL on our C lowering, read only by the unbounded verifier (WP). The
   bounded verifier (SAW) never takes hints: its only mechanism, experimental cutpoints, needs a
   call inserted in the loop condition and `llvm_unsafe_assume_spec`
   (`../research/11-verifier-facts.md:175-179`), both against 01 decision 8. So no refutation
   depends on LLM text, and no compiled candidate contains hints. Outside the lowering's C++
   subset there is no hint loop (proven within bounds at most). The subset must map `std::copy`
   and `std::swap` (GAPBS `QueueBuffer`, `pvector`); the proof of concept measures subset coverage
   on Extensa-campaign candidates.
3. **Order per candidate artifact** (with ticket 11): certified, then bounded, then unbounded
   without hints, then seeds (round 0), then hint rounds. Trigger: WP goals not proven with
   failure class timeout or unknown.
4. **Hint form:** records `{anchor, kind, text}`. The lowering tool emits stable anchors (function
   entry, each loop head, before and after each statement, one ghost-globals slot); a
   deterministic merger inserts the hints. Erase-and-diff against the lowering is a second guard.
5. **Vocabulary** (versioned; Yan-Ru may revise it later). Allowed: `loop invariant`,
   `loop assigns`, `loop variant` with an integer measure; `assert`; ghost declarations and
   statements (Frama-C rejects interfering ghost code at its default `ghost:bad-use` level);
   non-recursive `predicate`/`logic` definitions; `lemma`s proven in the same run;
   `\wp::strategy` tactic hints. Rejected, among others: every `admit` form, `axiom`, recursive or
   `inductive` definitions (WP makes recursive ones unchecked axioms; `pbad(x) = !pbad(x)` proved a
   false postcondition), contracts (`requires`, `ensures`, `assumes`, `behavior`), ghost functions,
   body-less declarations, `loop variant … for R`, `import \wp::why3:`, `\from`,
   `global invariant`, `volatile` clauses, statement contracts. This widens 01 decision 8.
6. **Workspace:** read-only C lowering with anchors; the candidate's C++ proof unit (including the
   authors' `TDStepMAA` when it is the candidate, a narrow exception to the rule that hides it
   from every role); the contract's formal halves and unit postcondition or relational template;
   summaries as ACSL; the failing goals with kind and failure class; earlier rejected and blamed
   hints; seeds. Hidden: evaluator, workload inputs, tests, negative controls, other candidates.
   The agent may run WP and the hint check through a frozen wrapper inside one provider call.
   Verdicts come only from the loop's own run (`-wp-cache none`, fresh session): a hand-edited
   cache entry made a false goal `[ Valid ]`. Hint records never enter a rewriting workspace.
7. **Three checks**, each frozen in the run plan and versioned:
   - **proof setup check**, before every verifier run: only summary-generated `assume`s
     (09, 11); hazard probes present and generator-made (12); every clause has a proof placement
     (10); hashes of contract, summaries, lowering and run plan; frozen flags (`-wp-cache none`,
     fresh session, Frama-C warning levels at default, x86_64 machdep, no WP environment
     variables);
   - **proof hint check**, every round: anchors exist; kinds on the list; text parsed by
     Frama-C's ACSL parser and its syntax tree checked (not a regex); erase-and-diff;
   - **verdict reading:** WP's per-property report, never the consolidated `[ Valid ]`. Every
     goal, lemma, call-site precondition, termination goal and smoke goal Valid; no `Extern`.

   The seven fact files in `../prototype/13-wp-hint-facts/` are the first negative controls of
   these checks.
8. **Rejected hint sets** use up their round; reasons go back to the agent; every rejection is
   recorded by rule. The evaluation reports how often the agent tried an escape hatch.
9. **Hint seeds:** before the first provider call, the loop tries the contract proof's hints and
   those of earlier proven candidates of the same contract: placed where the anchor exists,
   dropped Houdini-style when they fail, otherwise shown as examples. Seeds alone may prove the
   unit with no provider call. Provenance per hint: seed (with source), agent, or human. Seeds
   from a human-assisted contract proof belong to the contract (reviewed at promotion); the
   per-candidate step stays automatic. **Paper feature (Yan-Ru):** present and discuss seeds in
   the submission; the evaluation reports with and without seeds.
10. **Verdicts:**
    - **Proven:** WP smoke tests on the final hinted unit (any reachable `\false` voids it), one
      greedy minimization pass (unminimized set kept if the budget ends mid-pass), then the
      record: per goal solver and time; per verdict hint-set hash, rounds, provider calls,
      tokens, wall time, provider kind, provenance.
    - **Refuted** (bounded verifier only), three evidence steps: *unit refuted* (no proven level
      for that content hash); *replay* on the strict layer, recorded as reproduced, proof
      semantics only (citing the rule's gem5 source; this answers 12's question), or not
      reproduced (setup disagrees with the strict layer: stops the batch until root-caused);
      *bug* only with a whole-kernel reproduction (a real input, plus a schedule for races, on
      which the kernel fails its correctness check or executes the undefined behavior);
      otherwise "unit-level refutation". The refuted candidate keeps its test record, leaves
      selection, and its counterexample goes to **counterexample-guided repair** (the rewriting
      role), never to the hint agent. The authors' code is reported only. A new proof-semantics
      version reopens the verdict.
    - **Not proven after the budget:** the candidate keeps its prior level (proven within bounds
      if SAW proved, else certified), with failure class "hint budget spent", the unproven goals
      and the last hint set; retried only when a content hash in its set changes.
11. **Budget:** run-plan parameters. Starting values: 10 rounds (one provider call each, counted
    in the campaign's provider-call budget), 60 min loop wall time including verifier time, WP
    30 s per solver; tokens recorded, not capped. Yan-Ru: tune them by evaluation. Calibrate on
    public C suites (Code2Inv, X509-parser, Frama-C-problems) plus the BFS proof of concept;
    freeze; evaluate on held-out kernels (bc, pr, sssp, bfs bottom-up). Report proof rate as a
    curve over the budget, with "verifier without hints" at equal wall time. A changed value is
    a new run plan.
12. **Other routes, same loop and checks:** relational route (PR, BC): the template's alignment
    and coupling invariant are fixed; hints go only at product-program anchors. Contract proofs:
    Yan-Ru's hints use the same records and checks, provenance "human"; only the contract's logic
    library may hold recursive or inductive definitions, reviewed at promotion and listed in the
    contract proof. Concurrency (ticket 15): the reduction program for symbolic N runs through
    this loop; CIVL counterexamples go to counterexample-guided repair.
13. **Machines:** proof of concept on the Mac (a scoped exception to ADR 0006, recorded when it
    starts; the role builds nothing; Frama-C machdep x86_64). **Final evaluation and experiments
    on mbit10** (Yan-Ru): the lineup installed under `/data1/yanruj/` without sudo at the pinned
    versions; the budget calibration re-run there; proof jobs inside a socket lane (ADR 0006
    holds); Mac results labeled and never mixed with mbit10 timings.
14. **Generality:** nothing here is BFS-specific. Role, records, vocabulary, checks, seeds and
    budget apply per contract and kernel; PR and BC use the relational route.

**Positioning:** LLM repair from bounded-model-checker counterexamples exists for C (e.g.,
ESBMC-AI, Tihanyi et al. 2023; citation not yet checked). Gates follow DafnyBench, Lynette and
Trivet (04, 06). Claim the combination (contract, proof, repair, seeds), not any one loop.

**Inputs passed on:** reduction program and CIVL counterexamples → ticket 15; hints as ACSL on
the C lowering and the contract's logic library for recursive or inductive definitions → ticket
16; budget curve, calibration split, seeds on/off, escape-hatch counts, subset coverage, mbit10
recalibration, the ESBMC-AI check → the map's "Evaluation plan" fog; hint sets with provenance,
rejections by rule, replay status, vocabulary and check versions → "Records"; lane-hours for
proofs and the repair budget per campaign → "Extensa-mode loop". Glossary: proof-hint agent,
counterexample-guided repair, proof-hint loop, hint set, proof setup check, proof hint check
added; proof hint sharpened.

## Later changes

- 2026-10-13 19:48 ET, from [18](18-evaluation-claims-and-subjects.md) (item 3): the held-out kernels
  are BC, PR and SSSP; BFS bottom-up is dropped (the authors' `bfs_bu.cc` is an unbuilt fragment).
