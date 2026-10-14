# Spec: Extensa Probata — proven certification levels

Created: 2026-10-13 21:46 ET
Updated: 2026-10-13 22:10 ET (Yan-Ru accepted the test seams and O1's default, with no objection to
choices S1–S6); 2026-10-13 22:08 ET (review pass against all 28 tickets: 8 corrections, 8 omissions
filled; the old open point O2 became choice S6, since tickets 13 and 25 already decide it)
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** None
Owner: Yan-Ru Jhou
Map and tickets: [map.md](map.md). This spec is the map's destination. Each decision lives in its ticket;
this spec gives the gist and links it. Where a later ticket changed an earlier one, the spec states the
latest decision (each ticket's "Later changes" names what changed it).
Builds on: ADR 0006, ADR 0009, ADR 0010 (proof note, proposed), ADR 0014, ADR 0015, ADR 0016 (proposed);
D8 (iteration-ladder note).
Next: the proof-of-concept effort gets its own folder, spec and the 18 build tickets in
[Proof-of-concept plan](#proof-of-concept-plan).

## Summary (read this first)

1. **Problem:** certification is testing. It cannot say a candidate artifact is correct for every input
   and thread count, and tests already missed real defects in expert DX100 code.
2. **Fix:** Extensa Probata adds two proven certification levels above certified. Contract parts are
   proven once; each candidate artifact gets one small, automatic proof; an LLM writes proof hints, and
   only for the unbounded verifier.
3. **Trust is written down:** DX100 proofs trust a proof semantics whose rules cite gem5 source. Every
   verdict lists its assumption set and its bounds. Proof records never change; the level is computed
   when read.
4. **Both modes:** Extensa mode refutes before it evaluates, proves after the campaign, and reports a
   fastest and a best-proven winner. ArchEvolve mode proves its one candidate and tells the team the
   level in plain words.
5. **Evaluation:** BFS calibrates; BC, PR and SSSP are held out. Five research questions, with pass bars
   fixed at the method-version freeze. Proofs make no speed claim.
6. **Plan:** two efforts split at the freeze. The proof of concept takes about 21 weeks (stages A0–A6,
   a 2-week kill-test spike first); the evaluation follows.
7. **Settled with Yan-Ru (2026-10-13 22:10 ET):** the [test seams](#seams-confirmed-by-yan-ru) and
   [open point O1](#open-point-o1-decided); the gaps the tickets left are filled by choices S1–S6.

## Problem Statement

Yan-Ru's next paper extends Extensa. In Extensa's loop an LLM rewrites memory-bound C++, DX100 offloads
included, and certification tests each candidate artifact against the rewrite contract it applies, with
negative controls. Certification is evidence from the runs it made: the inputs, builds and thread counts
it tried. It cannot say "correct for every input and every thread count".

That gap has already cost us. Three findings from this map:

| Finding | What happened | Ticket |
|---|---|---|
| **A false alarm** | Our strict layer flagged the DX100 authors' `wait_ready(tile3)` as a "wrong-tile bug". gem5 shows the wait is safe. The bug came from an unverified rule frozen into testing semantics. | [14] |
| **A latent defect** | The authors' DX100 PageRank never resets `incoming_totals`, so scores are wrong from iteration 2. Their default of 1 iteration hides it, and GAPBS's own verifier cannot tell right from wrong at that setting. | [20] |
| **Undefined behavior** | All three proof-of-concept candidates race at more than one thread as written: the authors' fallback path (inherited from GAPBS), Peter's plain store, Codex's plain read. No test exposed it. | [11], [15] |

Extensa tried formal gates before. Its SMT, pet+ISL and libTooling legality gates did not construct or
scale on real benchmarks, and Extensa pivoted to testing (map Notes). A new attempt must say what changes
that outcome.

Prior work leaves a real but narrow gap: no paper formally verifies LLM-written C/C++ performance
rewrites against reusable contracts proven once, and none formally verifies an LLM-written accelerator
offload ([06], [22]). Each piece has precedent, so the paper claims the combination, never "first".

Standing constraints (Yan-Ru, map Notes): the method is general (other GAPBS kernels, not only BFS); it
handles any input code, not only code an expert already reshaped; proofs are built as automatically as
possible; formal by default, but about one month of work per piece. Codex is the default provider for
every agentic task ([23]).

## Solution

**Levels.** Every candidate artifact has a certification level. From highest: proven unbounded; proven
within bounds (threads ≤ k ranks above threads = 1); certified; uncertified. A proven level applies only
to a certified candidate artifact. A refuted candidate artifact leaves selection whatever its level.

**What "proven" asserts** ([09]): the candidate artifact's change is proven against the rewrite contract
it applies.

- (A) every formal half about the candidate's own code holds;
- (B) one proof unit (one call of the function that holds the rewrite site, such as `TDStep`) refines
  the baseline implementation's unit modulo the contract's unit relation, shown by the contract's unit
  postcondition (route 1) or step for step against a proven predecessor (route 3);
- no accelerator hazard under the proof semantics.

A lifting lemma, machine-checked once per contract and kernel, carries this to the kernel's output
relation. Every verdict lists its assumption set and a value or "unbounded" per bound dimension. Thread
count is always a dimension, so a one-thread proof is at most proven within bounds.

**One candidate artifact's path:**

| # | Step | Tool | If it passes | Otherwise |
|---|---|---|---|---|
| 1 | Certify | the certification command (tests, negative controls) | certified | rejected |
| 2 | Bounded rung, one thread | SAW, at the contract's minimum bounds | proven within bounds, threads = 1 | refuted: counterexample-guided repair, never step 4; timeout: no bounded level, on to step 4 |
| 3 | Bounded rung, threads ≤ k | CIVL; GenMC also refutes | proven within bounds, threads ≤ k | as step 2 |
| 4 | Unbounded | WP on the C lowering, per thread for symbolic N: no hints, then seeds, then LLM hint rounds | proven unbounded | keeps its level, "hint budget spent" |

In Extensa mode steps 1–3 run inside the loop, before speed evaluation; step 4 runs after the campaign
stops, only for candidates with a gain.

**What is proven once and what per candidate** ([10], [15], [24]):

| Proven | How often | Contents |
|---|---|---|
| With each library entry | once per content-hash set | its summary (proven clauses used in place of its code) |
| With each rewrite contract | once per content-hash set | unit postcondition on the reference instance, with "the baseline meets it" and "two units that meet it satisfy the unit relation"; order-independence lemma; lifting lemma per kernel; negative controls refuted; minimum bounds |
| With the method | once per method version | parallel composition theorem; shared-action commutativity lemmas; sum library; the concurrency negative controls |
| With the proof semantics | once per proof-semantics version | agreement with the strict layer on fixture scenarios; the three summary forms agree; the semantics negative controls |
| Per candidate artifact | every candidate, no human step | one proof unit: formal halves about its own code, unit postcondition, hazard freedom, per-thread obligations |

**Why this can scale where Extensa's gates did not:** a candidate proof covers one call, not a benchmark;
summaries remove building blocks' loops; the contract supplies the unit postcondition, so nothing searches
for it; the bounded verifier runs at derived minimum bounds, not "as large as possible"; an LLM proposes
hints and the verifier decides. A 2-week kill-test spike tests exactly this before anything is built
([27]).

**What a proof never claims:** speed; compiler correctness; that DX100 hardware matches its proof
semantics; anything about gem5 runs.

## User Stories

**Levels and what they mean**

1. As Yan-Ru, I want every candidate artifact to carry one certification level (proven unbounded, proven
   within bounds, certified, uncertified), so that I see at a glance how far its correctness is
   established.
2. As Yan-Ru, I want a proven level only on a certified candidate artifact, so that proofs add to the
   testing evidence and never replace it.
3. As Yan-Ru, I want "proven" to mean the change is proven against its rewrite contract (formal halves,
   unit relation, hazard freedom), so that the claim is exactly the one Extensa could not make.
4. As Yan-Ru, I want a lifting lemma per contract and kernel, so that a proof about one call says
   something about the whole kernel run.
5. As Yan-Ru, I want every proven-within-bounds verdict to record a value per bound dimension, thread
   count always included, so that nobody mistakes a one-thread proof for a general one.
6. As Yan-Ru, I want threads ≤ k ranked above threads = 1, and bounds above the minimum never ranked, so
   that the ranking rewards what the setup can see, not machine time.
7. As Yan-Ru, I want every verdict to list its assumption set by kind, each entry with one plain sentence,
   so that I know exactly what a proof trusts.
8. As Yan-Ru, I want a dependency proven only within bounds to cap the level, and an unproven one listed
   in the assumption set without capping, so that the level is the weakest proven link.
9. As Yan-Ru, I want floating-point kernels compared over real arithmetic with rounding listed as a
   platform choice, so that PR and BC proofs are possible and honest.
10. As a reader of the paper, I want to be told that a bounded verdict covers the builds it ran, not the
    deployed build, so that tile capacity and thread count are never overstated.

**Proven once, proven per candidate**

11. As Yan-Ru, I want each lowering and library operation proven once against its reference semantics
    and used as a summary, so that no candidate proof re-proves a building block.
12. As Yan-Ru, I want each rewrite contract to carry a contract proof, so that per-candidate proofs stay
    small.
13. As Yan-Ru, I want every once-proven part to hold for one content-hash set, so that a changed entry,
    contract, semantics or method reopens exactly what depends on it.
14. As Yan-Ru, I want a contract proof voided when any formal-visible negative control proves, so that a
    harness or summary that hides bugs is caught.
15. As Yan-Ru, I want each clause to name its proof placement (once with an entry, per candidate, or
    assumed), so that a clause with no proof blocks a proven verdict.
16. As Yan-Ru, I want once-proven parts allowed to be human-assisted and reviewed at promotion, and
    per-candidate proofs fully automatic, so that human cost is per contract and the paper's claim is the
    automatic step.
17. As Yan-Ru, I want every evaluated kernel's contract to state a unit postcondition (sums over CSR
    ranges for PR and BC, shortest distances for SSSP), so that the direct route covers every candidate.

**Verifiers, bounds and refutation**

18. As Yan-Ru, I want the bounded verifier to be the only source of refutations and counterexamples, so
    that no bug claim rests on a timeout.
19. As Yan-Ru, I want the unbounded verifier's "not proven" to trigger proof hints, never a bug claim, so
    that a timeout is treated as unfinished work.
20. As Yan-Ru, I want verifiers plugged in by role through one adapter interface, so that a tool can be
    swapped later at the price of re-proving once-proven parts.
21. As Yan-Ru, I want every "not proven" to carry a failure class, and an unclassified failure to stop the
    batch, so that tool problems are root-caused.
22. As Yan-Ru, I want each contract's minimum bounds derived automatically from its negative controls, so
    that a bounded verdict below them gives no level.
23. As Yan-Ru, I want build constants (tile capacity, thread count, knobs) recorded exactly, so that
    "lanes = 2" reads as a build with tile capacity 2.
24. As Yan-Ru, I want a refutation called a "bug" only with a whole-kernel reproduction, so that a
    unit-level counterexample is never overstated.
25. As Yan-Ru, I want every refutation replayed on the strict layer and labeled reproduced, proof
    semantics only, or not reproduced (which stops the batch), so that setups that disagree with testing
    are found.
26. As Yan-Ru, I want undefined behavior treated as a proof obligation and a racy candidate artifact
    refuted, so that defects tests miss are exposed.

**Proof hints**

27. As the proof-hint agent (Codex by default), I want the C lowering with stable anchors, the formal
    halves, summaries, failing goals and seeds in my workspace, so that I can write hints without seeing
    what I must not.
28. As Yan-Ru, I want proof hints only as ACSL records for WP, never for the bounded verifier, so that no
    refutation and no compiled candidate depends on LLM text.
29. As Yan-Ru, I want a proof hint check that parses each hint with Frama-C's ACSL parser, allows only the
    versioned vocabulary and erases-and-diffs, so that no `admit`, axiom or code change slips in.
30. As Yan-Ru, I want a proof setup check before every verifier run, so that a proof cannot pass by
    changing its own setup.
31. As Yan-Ru, I want verdicts read per property from the loop's own fresh run, never from WP's
    consolidated `[ Valid ]` or a cache, so that a doctored cache cannot fake a proof.
32. As Yan-Ru, I want hint seeds (from the contract proof and earlier proven candidates) tried before any
    provider call, so that some units prove with no LLM call.
33. As Yan-Ru, I want WP smoke tests and one greedy minimization pass before a proven verdict is recorded,
    so that vacuous proofs are rejected and hint sets stay small.
34. As Yan-Ru, I want every rejected hint set recorded by rule, so that the paper can report how often the
    agent tried an escape hatch.
35. As Yan-Ru, I want hint budgets calibrated on public suites and BFS, then frozen, so that held-out
    results are not tuned.

**DX100 proof semantics**

36. As Yan-Ru, I want DX100 proofs to trust a proof semantics, one contract per `maa_*` call, each rule
    citing gem5 source or marked assumed with an owner, so that hardware assumptions are explicit.
37. As Yan-Ru, I want values computed as if each command finished at issue and hazards asserted
    separately, joined by a reduction lemma, so that value proofs stay simple without hiding timing
    hazards.
38. As Yan-Ru, I want a read of an unready tile to be an assertion failure, so that hazard freedom is part
    of every proven verdict.
39. As Yan-Ru, I want per-element memory footprints with an overlap rule split by thread and by what DX100
    does, so that Peter's tolerated read race proves and real write hazards refute.
40. As Yan-Ru, I want the strict layer and the proof semantics kept in agreement by fixture scenarios with
    0 differences, so that testing and proofs judge the same rules.
41. As Yan-Ru, I want semantics negative controls run per proof-semantics version, so that a wrong version
    is voided.
42. As Yan-Ru, I want library entries that contradict the proof semantics to get new versions before they
    yield summaries, so that no summary claims more than the semantics allows.

**Concurrency**

43. As Yan-Ru, I want proofs for every thread count N, built with `NUM_CORES` = N, so that "proven
    unbounded" covers threads too.
44. As Yan-Ru, I want WP to prove one symbolic thread of N against the contract's shared actions, with a
    parallel composition theorem made once, so that per-candidate concurrency proofs stay automatic.
45. As Yan-Ru, I want reads that race by design modeled as history reads under RC11, so that proofs stay
    sound when reads return stale values.
46. As Yan-Ru, I want the composition theorem written by Codex in Rocq and checked there within about 2
    weeks, with a written fallback, so that the most formal option fits the cost rule.
47. As Yan-Ru, I want CIVL to give proven within bounds for threads ≤ k and GenMC to refute, both agreeing
    on every run, so that concurrency bugs are found before WP runs.
48. As Yan-Ru, I want one general race fix in counterexample-guided repair (plain reads of shared-action
    locations become relaxed atomic loads; redundant plain stores removed), so that racy candidates are
    repaired systematically.

**Formal halves and the C lowering**

49. As a contract author (an agent or Yan-Ru), I want formal halves written in a first-order ACSL subset
    inside the library YAML, so that WP reads them as written.
50. As Yan-Ru, I want our two translators to generate SAWScript specs and C call stubs from the same text,
    agreeing on every fixture, so that one source feeds every verifier.
51. As Yan-Ru, I want our own deterministic tool, never an LLM, to make the C lowering of a declared C++
    subset (with a modeled `std::vector`), so that the lowering is versioned, trusted code.
52. As Yan-Ru, I want an agent to draft missing formal halves behind five gates, so that drafting costs me
    only a review.
53. As Yan-Ru, I want recursive and inductive definitions only in the logic library, checked for primitive
    recursion and for `\false`, so that WP's unchecked axioms cannot make false proofs.

**Rewrite chains and any input**

54. As Yan-Ru, I want enabling rewrites (reshape only) to let an offload-only contract match code no
    expert reshaped, so that ArchEvolve handles any input code.
55. As Yan-Ru, I want every final candidate provable directly (route 1) and an offload-only rewrite proven
    per thread against its proven predecessor (route 3), so that correctness never depends on a chain.
56. As Yan-Ru, I want a certified enabling result recorded as a derived implementation with its contract
    lineage, so that proposals and the site finder work on it unchanged.
57. As Yan-Ru, I want each rewrite in a chain certified alone and its verdict tied to its contract,
    predecessor and result hashes, so that a change reopens that rewrite and every one after it.

**Records and levels**

58. As Yan-Ru, I want one proof record per proof job that never changes, so that no job rewrites evidence.
59. As Yan-Ru, I want the level computed on read from proof records whose content-hash set still matches,
    so that a stale level cannot exist.
60. As Yan-Ru, I want campaign summaries, handoffs and promotion reviews to keep dated level snapshots
    naming the level-rule version, so that a later drop shows against what was approved.
61. As Yan-Ru, I want one reviewed method-version file, so that "the method" in the paper is one frozen,
    citable thing.
62. As Yan-Ru, I want proof data only in `swdb_` tables, never in the LANL core, so that the research
    database keeps the main database's shape.
63. As a reader of the paper, I want every paper number to cite a frozen research-database commit, so
    that levels can be recomputed exactly.

**Extensa mode**

64. As the Extensa loop, I want each certified final candidate artifact to pass the bounded gate before
    speed evaluation, so that refuted code never spends mbit10 lane-hours.
65. As the Extensa loop, I want a refuted candidate sent to counterexample-guided repair (at most 5 rounds,
    apart from D7's 2 certification repairs), so that a refutation becomes a better candidate.
66. As the Extensa loop, I want unbounded proofs only after the campaign stops, on gain candidates fastest
    first, never overlapping timing or gem5, so that proofs never disturb measurements.
67. As Yan-Ru, I want a fastest winner and a best-proven winner per workload class, both tracked inside the
    loop, so that the speed-versus-proof trade-off stays visible and I choose which to promote.
68. As Yan-Ru, I want proof-hint calls under their own cap (default 30) and proof lane-hours reported
    apart, so that proofs cannot starve rewriting and their cost is visible.
69. As the rewrite provider, I want an iteration ladder of every earlier candidate artifact with its level,
    verdict and winner mark (no patches, no counterexamples), so that I learn from the campaign's history
    without leakage.
70. As Yan-Ru, I want an iteration able to start from a certified derived implementation, so that enabling
    rewrites can be built on.
71. As Yan-Ru, I want a reverted repair flagged and never counted as a repair, so that copying the
    baseline is not mistaken for a repair.

**ArchEvolve mode and the team**

72. As a teammate receiving a handoff, I want a plain-words `certification_level` block (level, bounds as
    values or "any", each assumption as one sentence, "says nothing about speed"), so that I understand
    the guarantee without reading a proof.
73. As Yan-Ru, I want ArchEvolve mode to run the same gate and proofs on its one final candidate artifact
    and report the level, never rank it, so that both modes share one method (ADR 0009).
74. As Yan-Ru, I want the assumption sentences made from fixed templates, never by an LLM, so that the team
    never reads an invented claim.

**Evaluation and the paper**

75. As Yan-Ru, I want five research questions with pass bars committed before the first held-out run, so
    that a miss is reported as a refuted hypothesis.
76. As Yan-Ru, I want held-out contracts and output relations drafted after the freeze, blind to the
    authors' code, so that held-out results measure the method.
77. As Yan-Ru, I want the authors'-code guard to name every authors' DX100 function before any held-out
    proposal, so that no agent role sees held-out expert code.
78. As Yan-Ru, I want testing-only certification as a baseline, so that the paper shows what the bounded
    verifier catches that tests accept.
79. As Yan-Ru, I want RQ3's gap over the no-contract baseline reported in three parts (seeds, route 3 vs
    route 1, refutations only the bounded rung gives), so that the paper claims only what contracts buy.
80. As Yan-Ru, I want Codex as the one default provider and Claude only as a sensitivity check, so that the
    results are not a model comparison.
81. As a reviewer of the paper, I want the small-scope curve (refutations at the minimum bounds, +1, +2),
    so that bounded claims rest on data, not on a sufficiency claim.

**Building the proof of concept**

82. As an implementing agent, I want a 2-week kill-test spike before any building, with a stop rule, so
    that the effort stops early if Extensa's scaling failure repeats.
83. As an implementing agent, I want each stage to end only when its exit check passes, so that later
    stages build on proven ground.
84. As Yan-Ru, I want a stage that reaches 1.5× its estimate to stop for a re-plan, so that overruns are
    caught early.
85. As an implementing agent on the Mac, I want one verifier job at a time under an ~8 GB RSS watchdog, so
    that the Mac never runs out of memory again.

## Implementation Decisions

How to read this section: each block names its deciding tickets. The block is the gist; the ticket holds
the detail and the evidence.

### Modules

**Proof machinery (all new)**

| Module | Job | Decided in |
|---|---|---|
| Proof command (proposed name `swdb prove`) | Runs one proof job on one subject and writes one proof record. Extensa mode, ArchEvolve mode and the evaluation all call it. | S1 below; [26] |
| Verifier adapters | One interface per role. In: a C++ proof unit or its C lowering, plus generated summaries. Out: proven, refuted with a counterexample, or not proven with a failure class. Tools: SAW 1.6 (fallbacks crux-llvm 0.12, then CBMC 6.11), CIVL 1.23, GenMC, Frama-C/WP 33.0. | [11], [15] |
| C lowering tool | Deterministic lowering of the declared C++ subset, keeping C++ names; anchors for hints; the per-thread program for symbolic N; the history-read encoding CIVL needs and the pthreads harness GenMC runs; product programs for uniform control and the lockstep route. | [11], [13], [15], [16] |
| Formal-half frame and translators | ACSL inside the library YAML; translators to SAWScript specs and C call stubs; a check mode that gives each formal half a runtime form. | [16] |
| Proof-hint loop and `proof_hinting` role | Seeds, hint rounds, the three checks, minimization, smoke tests. | [13], [25] |
| Minimum-bounds script and shape-split enumerator | Derives each contract's minimum bounds from its negative controls; splits a bounded job by graph shape, with a count check. | [19] |
| Rocq development | The parallel composition theorem and the DX100 reduction lemma, written by Codex, checked by Rocq. | [15], [12] |

**Library content (new, or new versions)**

| Module | Job | Decided in |
|---|---|---|
| DX100 proof semantics | One ACSL contract per `maa_*` call over fixed-size ghost hazard state; each rule cites gem5 DX100 source at `e4fc4af` or is assumed with an owner; versioned. | [12], [16] |
| Logic library | Shared definitions (CSR graph model, sets, the sum library) plus one file per contract; an ACSL definition of each reference semantics, proven against the lowered reference code, which the per-call intrinsic summaries are written against. | [16], [24] |
| `std::vector` and `std::pair` models | A C struct plus one C function per member, each with an ACSL contract citing the standard's `[vector]` clauses; reused as SAW overrides. | [16] |
| New library versions | The 10 DX100 intrinsic entries' completion assumptions; `dxc_const_i32`'s result clauses; per-call intrinsic summaries; `bfs_read_offload` with formal halves for L1–L4 and `once_enqueue` and no redundant store (L4 no longer requires it); its `bc_read_offload` counterpart; L5 as a proof-semantics rule (L3 becomes per candidate). | [12], [15], [16] |
| Strict layer, new certify version | Adds the proof semantics' memory-timing rule, so refutations that use it can replay. The 8-byte tile-pair rule waits until after the evaluation. | [12], [27] |

**Records and levels**

| Module | Job | Decided in |
|---|---|---|
| `proof` record kind | One record per proof job, never edited, with a subject, a content-hash set, bounds, an assumption set and a job block. SQLite tables `swdb_proof*`. | [26], ADR 0016 |
| Level rule (versioned) | Computes the level on read. Lives outside the method version, so a rule change recomputes levels without voiding proofs. | [26] |
| Candidate-level command (changed) | Extended to compute the proven levels on read. | S2 below |
| Method-version file | One reviewed file listing everything the proofs use apart from the contract, the candidate and the proof semantics. | [26], [18] |
| Failure-class vocabulary | One list of failure classes and skip reasons; anything outside it stops the batch. | [26] |

**Loop, modes and guards (changed)**

| Module | Change | Decided in |
|---|---|---|
| Campaign loop | Bounded gate and counterexample repair before evaluation; WP phase after the campaign stops; two winners in selection, workspace and plateau test; `provider_calls_proof`; start from a derived implementation; iteration ladder (`LADDER.json`, `rewrite_workspace: v2`). | [25], [17], [28] |
| Campaign adapter | Returns every certification record ID, one per contract (today only the first). | [17], [26] |
| Handoff envelope | Gains the `certification_level` block. | [26] |
| Provider guard and workspaces | The guard names `PBFSMAA`, `PageRankPullMAA` and `DeltaStepMAA` and drops two names that exist nowhere (`TDStepMAA2`, `BCMAA`). The new `proof_hinting` workspace may show the authors' code only when it is the candidate; hint records never enter a rewriting workspace. | [18], [13] |
| Implementation records | Carry their contract lineage (today `applies` lists only strategies). | [17] |
| Proposals | Carry repair lineage (refuted candidate, counterexample record, round, reverted-repair flag), run index and provider pin. | [26], [23] |

### What a proven verdict asserts — [What "proven" asserts (09)][09]

- (A) + (B) + hazard freedom, as in the Solution. Every evaluated kernel's contract has a unit
  postcondition ([24] withdrew "PR and BC have no clean definition"), so (B) can always be shown directly.
- **Proof unit:** one call of the function that holds the rewrite site. A candidate's level is the weakest
  among its proof units and the proven parts they depend on.
- **Lifting lemma:** machine-checked once per contract and kernel (WP with replayed `Wp.induction` scripts;
  Rocq as fallback, [11]). Until checked, it is an assumption entry of kind "written proof".
- **Harness `assume`s:** each is proven at every real call or listed as a reduction; any other voids the
  verdict. Known violation to fix: the 08 prototype's harness assumes `parent[v] >= -1`, but `InitParent`
  writes `-out_degree`.
- **Bounds:** each contract lists its bound dimensions, thread count always among them. Unroll depth is
  not a dimension ([19]).
- **Assumption set, seven kinds** ([26]): assumed clause, proof semantics, summary, reduction, trusted
  tool, written proof, platform choice. Each entry: kind, reference (ID and hash), one plain sentence.
- **Cap rule:** a proven dependency caps the level; an unproven one is an assumption entry and does not.

### Proven once vs per candidate — [What a contract proves once (10)][10]

- **Summaries:** proven once with each lowering or library operation and reused by every contract that
  calls it. DX100 intrinsics get per-call summaries, written against ACSL definitions of their reference
  semantics, so one summary of a `dxc_*` call serves both the BFS and the BC read offload ([16] item 9;
  the whole-loop `range_loop` reference no longer serves as one).
- **Contract proof:** the unit postcondition proven on the reference instance (the contract's own library
  code applied to the baseline, or else its first certified candidate), its lifting lemma per kernel, and
  every formal-visible negative control refuted with the same harness and summaries. A control that proves
  voids the contract proof.
- **Drafting rule** ([24]): every contract states a unit postcondition; a relational template needs a
  recorded reason. Templates stay legal.
- **"Once" means once per content-hash set.** A changed hash makes dependent records stop counting;
  dependents read as certified until re-proven.
- **Who proves:** once-proven parts may be human-assisted under the same hint rules, reviewed at
  promotion; candidate proofs are fully automatic.
- **Scale pass bar:** the 08 prototype's safe 2-lane case, with summaries in place of the inlined
  strict-layer port, proves in under 15 minutes. The 1-lane fallback is withdrawn ([19]): one lane cannot
  see `skipped_cas_recheck`.

### Proof routes — [Enabling rewrites (17)][17] as revised by [No alignment hint kind (24)][24]

| Route | What is proven | Status |
|---|---|---|
| 1 Direct | the final candidate (and each derived implementation, once) against the kernel's unit postcondition | always available; the fallback |
| 2 Catalog template | an enabling rewrite through a kernel-independent relational template | not built in this effort |
| 3 Lockstep | an offload-only rewrite, per thread, against its proven predecessor | kept; used when the predecessor is proven |
| Bounded direct | the final candidate against the baseline, by the bounded verifier only | only for a kernel with no unit postcondition |

- Per final candidate: route 3 when its predecessor is proven, else route 1.
- Enabling rewrites and rewrite chains are about matching, not proofs. Catalog of recurring reshapes:
  chunking, small-remainder fallback, phase split, buffers, edge-loop flattening.
- An offload-only contract names its required enabling contracts in order (ID and version range),
  checked against the predecessor's lineage. Enabling contracts never list what they enable.
- The profiling agent annotates each derived implementation; a deterministic check confirms the pattern
  classes its enabling contract's strategy effects predict, and a mismatch blocks the chain.
- For any input with no fitting catalog entry, Extensa mode's rewriting role may write a new experimental
  enabling contract, usable only in Extensa mode until promotion; its results are proven by route 1 like
  any derived implementation ([24]).
- Each rewrite is certified alone against its predecessor's snapshot; the final candidate also runs the
  kernel's correctness check against the root baseline. The performance comparator stays the root
  baseline (ADR 0005).
- No alignment hint kind: an alignment changes the product program, so it is never a proof hint.

### Verifier lineup and order — [Verifier choice (11)][11], [Concurrency proofs (15)][15], [Bounds (19)][19]

- **Bounded verifier:** SAW 1.6 at threads = 1, specs generated from formal halves, summaries as
  overrides. Fallbacks in order: crux-llvm on the C++, crux-llvm on the C lowering, CBMC on the C lowering.
- **Threads > 1:** CIVL 1.23 gives proven within bounds for threads ≤ k (minimum k = 2, runs at k = 3);
  GenMC (RC11) is the second refuter. They must agree; a contradiction stops the batch and voids the
  method version.
- **Unbounded verifier:** Frama-C/WP 33.0 on our C lowering. Solver portfolio Alt-Ergo, Z3, CVC5 (a goal
  counts when any one proves it; the solver is recorded per goal). Floats as reals (`-wp-model +real`;
  crux-llvm `-f real` until SAW's float mode is confirmed).
- **Cross-check of the lowering:** the bounded verifier runs on both the C++ and the C lowering, and the
  verdicts must agree. It is the only check on the trusted lowering tool.
- **Pinned:** tool, solver and front-end versions (clang 22.1.8) and flags, all in each content-hash set.
- **Out:** ESBMC (timeouts), RPP (no relational loop invariants), VerCors. Frama-Clang is an experiment
  only.
- **Order per candidate:** certified, then bounded, then unbounded. A refuted candidate never reaches the
  unbounded verifier; a bounded timeout or missing minimum bounds does not block it (S6).
- **One summary source:** SAWScript specs, C call stubs and ACSL contracts generated from formal halves.
  Only summary-generated `assume`s are allowed.
- **Failure classes:** parse error, unsupported construct, unwinding bound too small, timeout, unknown
  (S3), out of memory, solver error, tool crash, vacuous pass, hint budget spent, below minimum bounds,
  ghost capacity (S3). Timeout and unknown send WP goals to the hint loop. Each has a handler; diagnosed failures join a regression corpus. Skip reasons (a step that cannot
  run, the level kept): no contract proof, no minimum bounds, outside the C++ subset.

### Bounds — [Bounded verdict bounds (19)][19]

- **Minimum bounds,** per contract and per rung: the smallest bounds at which the bounded verifier refutes
  every formal-visible negative control. A script derives them on the reference instance; Yan-Ru approves
  them at promotion; they belong to the contract proof's content-hash set.
- **Below the minimum, no level:** "bounded check below minimum", and the candidate stays certified.
- **BFS read offload, one thread** (hand derivation; the script must confirm it): threads 1, lanes 2,
  chunk 2, frontier 2, vertices 3, edges 3. PR's iteration count is a bound dimension expected to need at
  least 2 ([20]).
- **Build constants** are recorded exactly; inputs stay symbolic up to their size bounds; a knob that is
  only compared becomes a symbolic constant limited by its legality clause.
- **Extensa mode proves at the minimum only.** Larger bounds run only in the evaluation (a scaling curve)
  or for final candidate artifacts with spare budget.
- **15 minutes per bounded job,** calibrated, then frozen. A timeout never falls back to smaller bounds.
- **Levers, in order:** per-call summaries, then shape splitting. Relabeling symmetry only as a reduction
  with its own obligation, not in the proof of concept.

### DX100 proof semantics — [Proof semantics (12)][12], [Formal-half language (16)][16]

| Model | What it is | Used for |
|---|---|---|
| Functional model (the authors') | what each command computes, finished at once | a testing aid; never trusted by proofs |
| Strict layer (ours) | functional results plus hazard tracking, executable | certification |
| Proof semantics (new) | one contract per `maa_*` call over ghost hazard state | proofs |

- **Values and timing split:** values as if each command finished at issue; hazards asserted apart; a
  reduction lemma joins them (written proof, a bounded check on an asynchronous port, then Rocq).
- **Unready read = hazard** (assertion failure). "Unready" means the producer has not finished.
  `get_tile_ready` may answer either way while commands are pending.
- **Memory footprints,** per element:

  | A CPU access overlaps an unfinished DX100 command's footprint | Verdict |
  |---|---|
  | same thread, either side writes | hazard |
  | other thread, DX100 only reads | allowed; the read is a history read (Peter's pattern) |
  | other thread, DX100 writes | hazard |

- Device against device follows gem5's region stall. Tile ownership is a proof obligation. An 8-byte
  operand occupies tiles t and t+1.
- **Stops at the `maa_*` calls.** The MMIO code behind them is an assumption entry.
- **Visibility:** program accesses are proven; the store inside `critical` finishes before the lock is
  released (proven by the wait rule). Assumption entries: two gem5 corners for cross-core loads; "no stale
  CPU copy survives a DX100 store" (owner Eric); one DX100 instance.
- **Agreement with the strict layer,** per proof-semantics version: every rule both model runs as a
  fixture scenario on both, 0 differences; rules only the proof semantics has are listed; the three
  summary forms agree on every scenario.
- **Semantics negative controls,** per version. Must refute: `TDStepMAA` with its wait deleted; the
  authors' wait under the old rule; a same-thread read of `parent` during its DX100 store; another
  thread's read of a line a DX100 store has in flight. Must prove: the authors' wait under the gem5 rule;
  Peter's other-thread read pattern.
- **Encoding:** ACSL with fixed-size ghost arrays; K = 32 command slots per thread is an encoding bound,
  so more uncovered commands give "not proven, ghost capacity", never a refutation.
- **Sign-off:** cited rules need none; Yan-Ru approves the proof semantics at promotion; uncited rules stay
  "assumed, owner Eric". No message to Eric now.

### Formal-half language and the C++ subset — [Formal-half language (16)][16]

- **One source:** an ACSL subset inside the library YAML. WP reads it as written; our translators make the
  SAWScript specs and C stubs (trusted-tool entries). The ported Extensa grammar stays for runtime probes
  only.
- **Allowed ACSL:** `requires`, `ensures`, `assigns` with index ranges; first-order formulas with bounded
  quantifiers; `\old`, `\at(..., Pre)`; integer and real arithmetic; `\valid`, `\separated`, `\result`;
  logic-library calls (non-recursive, or primitive recursive, checked syntactically). Inductive
  definitions only in logic-library lemmas. No axioms anywhere.
- **Names:** ACSL over the C lowering's kept C++ names. A relation is a predicate with one parameter per
  side.
- **YAML frame:** per clause, `acsl` and a required proof placement (`once: <entry>@<version>`,
  `per_candidate`, or `assumed` with its kind); per contract, the shared-action kinds each interface array
  allows and whether its reads are history reads; per proof-semantics rule, its gem5 citation or owner; an
  offload-only contract's required enabling contracts.
- **`bfs_read_offload` placements:** every clause per candidate except L5, which is assumed (kind: proof
  semantics).
- **Sharing classes** per barrier interval are per candidate: the C lowering proposes them, WP proves them.
- **C++ subset,** by construct: C plus references; classes without inheritance or virtual functions;
  member functions and operators; constructors and destructors as explicit calls; templates
  (instantiated); `new[]`/`delete[]`; `enum class`, `constexpr`, `static_assert`; `std::min`, `std::max`,
  `std::copy`, `std::swap` through C models proven once; OpenMP `parallel`, `for` (static, dynamic,
  `nowait`), `critical`, `atomic`, `barrier`, `reduction`; `__sync_*`, `__atomic_*`; `__dxc_*` and
  `maa_*` through summaries; `std::vector<T>` (not `bool`) and `std::pair` as models. Out at first:
  inheritance, virtual functions, exceptions, lambdas, RTTI, other standard containers, streams; each
  "unsupported construct" failure extends the subset. Outside it a candidate reaches at most proven
  within bounds.
- **Standard-library model:** new assumption entries "the pinned standard library implements the modeled
  members as the standard says" (trusted tool) and "allocation succeeds". Growing a shared vector outside
  `critical` is refuted; `at` out of range is a proof obligation.
- **Runtime-check form:** our C-stub generator in check mode. E-ACSL is only a cross-check (it drops
  `\old` under a quantifier, the form BFS frame clauses need).
- **Five gates for a drafted formal half:** it parses and type-checks; the reference instance proves it;
  each formal-visible negative control is refuted by it; its runtime form passes every certify run of the
  reference instance; Yan-Ru approves it at promotion.

### Concurrency — [Concurrency proofs (15)][15]

- **One thread at a time:** WP proves one symbolic thread t of N. Other threads appear only through the
  contract's shared actions. The parallel composition theorem turns per-thread proofs into "every run ends
  as some serial order of the shared actions would".
- **Shared-action kinds,** each with a commutativity lemma proven once in WP: claim (write-once CAS),
  min-update, atomic add or OR, OpenMP reduction, queue reserve. A new kind bumps the method version.
- **Memory model:** a read that races by design is a history read; a CAS is a sequentially consistent
  read-modify-write; a plain access to a shared-action location is a race, so the candidate is refuted.
  Assumption entry: the pinned compiler and ISA implement RC11.
- **OpenMP:** one trusted-tool entry for the pinned runtime (OpenMP 5.2). Chunk splits, team size = N and
  uniform control (a two-copy product, GPUVerify-style) are proven, never trusted.
- **Composition theorem:** Codex writes it in Rocq, Rocq checks it; Yan-Ru reviews only its statement and
  definitions (1–2 pages). 2-week box; fallback a written proof with Codex adversarial review. Until Rocq
  checks it, it is an assumption entry of kind "written proof" ([26]).
- **Negative controls:** seven must refute (wait outside `critical`; `critical` dropped; one shared tile;
  overlapping chunks; barrier dropped; a plain store to a shared-action location; thread-dependent
  worksharing); one must prove (a re-read after a failed CAS sees the winner).
- **Repair, not hand fixes:** Peter's read offload proves at N = 1 and is refuted at N > 1; its next
  version comes from counterexample-guided repair on CIVL's race trace (a hand deletion only if the loop
  fails, labeled hand-made). The authors' `TDStepMAA` is a candidate like any other: refuted at N > 1,
  reported as a finding.

### Proof-hint loop — [Proof-hint loop (13)][13]

| Loop | Scope | Changes code? | Driven by |
|---|---|---|---|
| Extensa mode | a campaign | yes: new rewrites | performance |
| Counterexample-guided repair | one refuted candidate artifact | yes: a repaired candidate | a bounded counterexample |
| Proof-hint loop | one proof unit of one candidate artifact | never | WP goals not proven |

- **Hint form:** `{anchor, kind, text}` records at lowering-generated anchors, merged by a deterministic
  tool.
- **Vocabulary** (versioned). Allowed: `loop invariant`, `loop assigns`, integer `loop variant`; `assert`;
  ghost declarations and statements; non-recursive `predicate`/`logic` definitions; lemmas proven in the
  same run; `\wp::strategy` hints. Rejected: every `admit` form, `axiom`, recursive or inductive
  definitions, contracts, ghost functions, body-less declarations, `loop variant … for R`,
  `import \wp::why3:`, `\from`, global invariants, `volatile` clauses, statement contracts.
- **Three checks,** frozen and versioned:
  - *proof setup check* before every verifier run: only summary-generated `assume`s; generated hazard
    probes present; every clause has a proof placement; hashes of contract, summaries, lowering and run
    plan; frozen flags (`-wp-cache none`, fresh session, default Frama-C warning levels, x86_64 machdep, no
    WP environment variables);
  - *proof hint check* every round: anchors exist, kinds allowed, ACSL parsed and its syntax tree checked,
    erase-and-diff;
  - *verdict reading:* WP's per-property report; every goal Valid, no `Extern`.
- **Workspace:** the read-only C lowering with anchors; the candidate's C++ proof unit (the authors' code
  only when it is the candidate); the formal halves and unit postcondition; summaries as ACSL; failing
  goals with kind and failure class; earlier rejected hints; seeds. Hidden: the evaluator, workload inputs,
  tests, negative controls, other candidates. The agent may run WP and the hint check only through a
  frozen wrapper; verdicts come only from the loop's own run.
- **Seeds:** the contract proof's hints and earlier proven candidates' hints, tried before any provider
  call and dropped Houdini-style when they fail. A paper feature, reported with and without.
- **Budget** (starting values, calibrated on Code2Inv, X509-parser and Frama-C-problems plus BFS, then
  frozen): 10 rounds, 60 minutes, WP 30 s per solver; tokens recorded, not capped. Proof rate is reported
  as a curve over the budget, with WP alone at equal wall time.
- **Machines:** proof of concept on the Mac (a scoped ADR 0006 exception, recorded at A0); final evaluation
  on mbit10.

### Refutation, repair and bugs — [13], [23], [25]

- **Evidence steps:** unit refuted (blocks a proven level for that content hash); replay on the strict
  layer (reproduced, proof semantics only, or not reproduced, which stops the batch); "bug" only with a
  whole-kernel reproduction, computed on read when that record exists.
- **Repair:** the counterexample goes to the rewriting role, never to the proof-hint agent. At most 5
  rounds. A repaired candidate is a new candidate artifact: certified, gated, evaluated and ranked.
- **Reverted repair:** repaired code that no longer applies the refuted candidate's contract (drops the
  offload, or equals the baseline) is flagged, may compete, and never counts as a repair.
- **The authors' code** is reported only; it never competes in selection.

### Records and levels — [Proof records (26)][26], ADR 0016

- **Subjects:** a candidate's proof unit; a library entry's summary; a contract-proof part (unit
  postcondition, lifting lemma, negative controls, minimum-bounds derivation); a method part (composition
  theorem, proof-semantics checks); a whole-kernel reproduction.
- **Pins per record:** code proven; contract; baseline function; reference semantics; proof-semantics
  version; method version; each summary used (entry hash plus its proof record ID); minimum-bounds
  version; predecessor snapshot; every build constant.
- **Where things live:** SQLite `swdb_proof*` tables (SWDB extension only); the final hint set and any
  counterexample inline in the YAML; verifier logs and per-goal reports as compact evidence on the run
  host, by path and sha256; verifier scratch never named and deleted when the job ends. Mac output goes to
  a runs folder outside the repo (host `mac`); paper numbers come only from mbit10.
- **Method-version file contents:** verifier lineup with versions and flags; CIVL and GenMC settings; the
  OpenMP runtime; C-lowering subset, translators and naming rules; ACSL language version; proof-hint
  vocabulary; the three checks; budgets; prompts; shared-action kinds; shared logic library (with the sum
  library); `std::vector` model; ghost capacity K. Frozen by Yan-Ru's review at the freeze.
- **Campaign summary:** both winners per class with dated level snapshots; proof lane-hours, proof-hint
  calls and repair calls used. Written when the campaign stops, rewritten once when the WP phase ends.
- **Promotion review** cites the proof record IDs and the level snapshot at promotion.

### Extensa mode — [Loop proofs and ranking (25)][25], [Iteration ladder (28)][28]

- **Bounded gate** before evaluation, at minimum bounds, 15 minutes per rung, rungs in parallel. Refuted
  code is never evaluated.
- **WP phase** after the campaign stops: gain candidates, fastest first, until one is proven unbounded or
  the budget ends; never overlapping a timing step or a gem5 simulation.
- **Two winners per workload class:** the fastest winner (certified beats uncertified, as today) and the
  best-proven winner (highest proven level, then fastest). Both tracked in the loop; an iteration improves
  when either improves. Yan-Ru chooses which to promote.
- **Budgets:** `provider_calls_proof` (default 30) apart from the rewriting total; repair calls stay in the
  rewriting total; proof jobs share lane-hours (default 24), reported apart. Campaign caps rise only
  through the existing approval entry. Per-candidate budgets belong to the method version.
- **Iteration ladder:** on in every new campaign, no off switch. `LADDER.json`, rewritten whole each
  iteration from campaign state by the loop: one row per earlier candidate (rejected and repaired ones
  included, no gaps), with contracts, knobs, level known so far (never proven unbounded), verdict, ratio,
  lower bound, spread, reason codes (new: `refuted`, `proof_timeout`), public failed-check names and a
  winner mark. No patches, no counterexamples, no raw timings. `FEEDBACK.json` stays. Repair calls see it.
  The loop records `rewrite_workspace: v2`; earlier campaigns read as `v1`.
- **Start gate:** D35 still refuses every new real-target campaign; RQ5 waits for it.

### ArchEvolve mode — [25], [26], [17]

- Its one final candidate artifact runs the same gate and unbounded proofs with the same budgets.
  Counterexample-guided repair counts as its allowed bounded correctness repair.
- The level is reported in the handoff's `certification_level` block, never ranked. Example: "Proven for
  every graph and every thread count. Assumes: DX100 follows its proof semantics v3, each rule cited to
  gem5 source; clang 22.1.8 compiles correctly; CPU caches hold no stale copy after a DX100 store
  (assumed; owner Eric). Says nothing about speed."
- Shared contracts only; each rewrite of a chain is one rewrite proposal; a derived implementation enters
  the main database only through promotion.

### Providers and machines — [23], [13], [27]

- **Codex is the one default provider** for every agentic task (rewriting, proof hinting, repair, contract
  drafting, the Rocq theorem), pin `gpt-5.6-sol`, effort `xhigh`. **Claude** (`claude-sonnet-5-5`, effort
  `high`) appears only in a sensitivity check: proof hinting and repair on BFS and SSSP, one run each,
  never part of a pass bar.
- **Mac:** one verifier job at a time under an ~8 GB RSS watchdog; keep at least 50 GB of disk free; check
  that LLVM 22 still works for the analytic evaluator after any Homebrew change.
- **mbit10:** the lineup under `/data1/yanruj/` without sudo at the pinned versions; proof jobs inside a
  socket lane; up to 6 proof workers per lane job, each pinned to a core with an 8 GB RSS cap. Mac results
  are labeled and never mixed with mbit10 numbers.

### Evaluation design — [Claims and subjects (18)][18], [Baselines and metrics (23)][23]

**Kernels:** BFS top-down calibrates. BC, PR and SSSP are held out: every GAPBS kernel the DX100 authors
built accelerator code for. Together they cover all five shared-action kinds. BFS bottom-up (an unbuilt
fragment), CC and TC (no DX100 code) are dropped.

**Research questions** (starting pass bars, set finally at the freeze and committed before the first
held-out run):

| RQ | Question | Primary metric | Starting pass bar (held-out kernels) |
|---|---|---|---|
| RQ1 Automation | Of certified candidates that apply a contract, how many does the per-candidate step prove, at which level, with no human step? | proof rate per level | ≥ 50% proven unbounded and ≥ 80% at least proven within bounds, of non-refuted LLM candidates, inside the frozen budget |
| RQ2 Hints | What do LLM hints add over WP alone at equal wall time, and what do seeds add? | proof-rate difference; median provider calls per proven candidate, seeds on vs off | +20 points or more; seeds cut median calls by ≥ 30% |
| RQ3 Contracts | What does a contract proven once buy each candidate, and at what one-time cost? | median per-candidate proof time; per contract, agent time and Yan-Ru's review hours | median ≤ 30 min on mbit10; ≤ 3 weeks of agent time and ≤ 1 day of review per contract; chained ≤ bundled (dropped if A5 is cut); 2 lanes under 15 min |
| RQ4 Refutation and repair | Are seeded faults and N > 1 races refuted, and does repair yield candidates proven at every N? | refutation rate; repair rate | every formal-visible seeded fault and every racing as-written candidate refuted; ≥ 80% of refuted races repaired into candidates proven at every N within 5 rounds; repaired speed within the evaluator's noise band |
| RQ5 End to end (BFS) | Does ranking by proven level change which candidate wins, at what cost? | speedup gap between each class's two winners | best-proven within 5% of the best certified candidate's speedup; proofs ≤ 25% of lane-hours |

- **Reading a bar:** the pooled held-out point estimate (n about 60, about ±13 points), always shown with
  its 95% Wilson interval; an interval that crosses the bar is "met, not significant".
- **RQ3's gap** over the no-contract baseline is reported in three parts: seeds, route 3 vs route 1 time,
  and refutations only the bounded rung gives. No claim that contracts make proofs faster unless A3's BFS
  run shows it. RQ3 also counts the sum library's one-time cost.
- **RQ5** runs only on new campaigns, all with the iteration ladder. Campaign a7 becomes a labeled worked
  example ("no ladder (v1)"). The paper states that it does not measure whether the ladder or its level
  column changes the speed gap.

**Subjects per held-out kernel:**

- the authors' DX100 code as written, and its repairs (see [open point O1](#open-point-o1-decided));
- an LLM population: proposals from the ArchEvolve-mode rewriting role (Codex, pinned; not gated by D35;
  no ladder), deduplicated by normalized content hash, until 20 distinct candidates certify or 60
  proposals are made; the certification rate is reported;
- seeded faults: each contract's negative controls plus the semantics and concurrency controls.

BFS extras, outside held-out rates: Peter's read offload, Codex's frontier staging, the upstream-GAPBS
demo, the 32 BFS candidates in the team store. Reference instances never count in rates.

**Held-out contracts:** drafted after the freeze by an agent, from the baseline and the intrinsic
specification, the authors' code hidden; one offload-only contract per kernel; Yan-Ru approves at
promotion. Baselines are the fork's non-DX100 functions as found (`PBFS`, `PageRankPullGS`, `DeltaStep`).
PR's correctness check compares per vertex against a reference at a fixed iteration count of at least 2,
on inputs away from the fixed point ([20]).

**Baselines:** testing-only certification (its false acceptances; T-LLM Compiler's 33.8% is the published
counterpart); WP alone at equal wall time; no contract (route 1 for the unbounded half, SAW
whole-function equivalence for the bounded half); three repair mirrors at equal provider calls
(safety-only acceptance, verdict only, ask again). Cited, not run: LLOR, DR.FIX. A ThreadSanitizer repair
baseline runs only if it installs within one day.

**Ablations:** seeds on vs off (every kernel); chained (route 3) vs direct (route 1) vs bundled (BFS);
summaries vs inlined building blocks (BFS's 2-lane bar plus SSSP). No checker-off run.

**Protocol:** the candidate population is generated once and frozen by content hash. LLM configurations
run 3 times (primary = mean; "proven in any run" secondary); others run once. Paired tests: exact McNemar
for proven or not, Wilcoxon signed-rank for calls and time. Configurations are interleaved within a batch.
Proof time is a cost, never a speed claim. A method change after the freeze makes a new method version,
re-runs every held-out kernel, and both runs are reported ([18]).

**Secondary results:** the small-scope curve (refutations at the minimum, +1, +2); route used per
candidate; candidates that would have needed an alignment (expected 0); direct-route verdicts for the
authors' code; escape-hatch attempts by rule; subset coverage; translator agreement; formal-half gate
rejections; ghost-capacity failures; N > 1 refutation rate and repair calls per refuted candidate;
reverted repairs; patch size as tree edit distance. Method checks reported as evidence: the semantics
controls, the eight concurrency controls, CIVL–GenMC agreement, strict-layer agreement.

**Performance** appears only in RQ4 (repaired vs as written) and RQ5, measured with Extensa's evaluator on
mbit10, gem5 included for DX100.

**Cut order:** the Claude sensitivity check, then RQ5, then PR. BFS, BC and SSSP are the floor; BC is never
cut; if SSSP cannot finish, the submission waits.

**Cost (estimates):** 2–3 weeks of agent work per held-out kernel, in parallel; about 90 mbit10 lane-hours
of certification for the populations; at most about 760 proof worker-hours (about 3 days on 12 workers).

### Proof-of-concept plan

Decided in [Proof-of-concept stages (27)][27].

**Two efforts, split at the freeze.** The proof-of-concept effort builds the method, calibrates it on BFS
and the public suites (Mac, then mbit10) and ends when the method version is frozen and committed. The
evaluation effort then drafts the held-out contracts, generates the populations and runs RQ1–RQ5. Held-out
kernels are never touched before the freeze; two synthetic fixtures stand in for their riskiest proofs.

**Main track** (proof stages run one after another: one verifier job at a time on the Mac):

| Stage | Content | Weeks | Exit check |
|---|---|---|---|
| A0 Setup | Guard fix first; install SAW, CIVL with a JDK, GenMC from source, Rocq; record the ADR 0006 Mac exception | ~0.5 | the guard test blocks the three names; each new tool proves 07's safe smoke program and refutes its seeded bug (2 days, else its fallback: SAW to crux-llvm, GenMC to CIVL alone, Rocq to the written proof) |
| A1 Kill-test spike | (a) SAW reads clang 22 bitcode and keeps ghost state; (b) 2 lanes under 15 min with per-call summaries at threads = 1, on Peter's read offload and the authors' `TDStepMAA`, every single-thread control refuted at the hand-derived minimum; (c) WP proves one read-offload unit at threads = 1 with agent hints within 60 min; (d) WP proves the sum lemmas and one unit of a synthetic CSR pull-sum fixture over reals | 2 (box) | (a)–(d) pass; stop and re-plan with Yan-Ru if (b) fails after both levers or (c) fails in the box |
| A2 Foundations | YAML frame, translators, check mode; C lowering and `std::vector`; logic and sum libraries; proof semantics and new library versions; new `bfs_read_offload` version; minimum-bounds script | ~6 | generated artifacts reproduce every spike verdict; summary forms agree; the script reproduces the hand minimum; every formal-visible single-thread control refuted; 2 lanes under 15 min with generated summaries; every semantics control has its required verdict (S4) |
| A3 Proof-hint loop | Role, vocabulary, checks, seeds; calibration on public suites and BFS; the RQ3 both-ways BFS run; the synthetic bucketed-relaxation fixture | ~4 | the BFS read-offload unit proven unbounded at threads = 1 with no human step; the fixture proven with seeds; every planted bad hint rejected; budgets calibrated; RQ3 BFS numbers recorded |
| A4 Concurrency | Per-thread lowering, sharing classes, uniform control; CIVL and GenMC adapters; the eight controls; repair of Peter's race; the one-day ThreadSanitizer box | ~4 | seven controls refuted, one proven; CIVL and GenMC agree; Peter's race repaired; the repaired unit proven per thread for symbolic N; Rocq checked or the written fallback done |
| A5 Rewrite chains | Chained (route 3) vs direct (route 1) vs bundled on Peter's read offload; the upstream-GAPBS demo only if that passes | 2–3 | all three reach the same level, times recorded |
| A6 mbit10 and freeze | Lineup under `/data1/yanruj/`; the 6-worker lane job; budgets recalibrated; Yan-Ru reviews the method-version file; freeze | ~2 | every Mac verdict reproduces on mbit10; the method-version file reviewed and committed |

About 21 weeks (about 5 months). Only A2 exceeds the one-month rule, and it is several pieces.

**Side tracks:**

- **Rocq** (composition theorem and DX100 reduction lemma; 2-week box, written fallback) starts with A2.
  A4's exit needs its result.
- **Strict-layer catch-up** (the memory-timing rule as a new certify version) runs beside A3–A4 and ends
  before the freeze.
- **Extensa track,** from day 1 (Yan-Ru's choice): the record pieces first (A2 reuses them), then the loop
  items, campaign-summary and handoff fields, the adapter fix, start from a derived implementation, and the
  iteration ladder. Coded against a stub verifier adapter with scripted verdicts; the real gate plugs in
  after A2, the WP phase after A3. Exit: one `--fixture` campaign end to end with real verifiers.

**Overrun rule:** a stage at 1.5× its estimate stops for a re-plan with Yan-Ru. Time-boxed items (spike,
Rocq, ThreadSanitizer) end on their fallbacks.

**Cut order inside the proof of concept:** (1) the upstream-GAPBS demo; (2) the strict-layer catch-up;
(3) A5; (4) the Extensa track's end-to-end exit (moves after the evaluation, with RQ5). Never cut: A0–A4,
A6, the record pieces.

**Build tickets** for the proof-of-concept effort (P numbers, to avoid clashing with this map's tickets;
blocking follows the stage order and is final when the tickets are cut):

| # | Ticket | Stage or track | Blocked by (proposed) |
|---|---|---|---|
| P01 | Authors'-code guard fix | A0 | — |
| P02 | Tool installs and the ADR 0006 Mac exception | A0 | — |
| P03 | Kill-test spike | A1 | P02 |
| P04 | YAML frame, translators, check mode | A2 | P03 |
| P05 | C lowering and `std::vector` model | A2 | P03 |
| P06 | Logic library and sum library | A2 | P03 |
| P07 | Proof semantics, its checks (S4) and new library versions | A2 | P04, P16 |
| P08 | Minimum-bounds script | A2 | P04, P05, P07 |
| P09 | Proof-hint loop: role, vocabulary, three checks, seeds | A3 | P04–P08 |
| P10 | Calibration, the RQ3 BFS run, the bucketed-relaxation fixture | A3 | P09 |
| P11 | Concurrency | A4 | P10, P14 |
| P12 | Rewrite chains | A5 | P11 |
| P13 | mbit10 and freeze | A6 | P12 (P11 if A5 is cut), P15 (unless cut) |
| P14 | Rocq: composition theorem and reduction lemma | side | P03 |
| P15 | Strict-layer catch-up | side | P07 |
| P16 | Extensa records: `proof` kind, tables, level rule, method file, failure classes; repair-lineage and run fields on proposals; promotion-review level pins | Extensa track | — |
| P17 | Extensa loop items; campaign-summary fields; the handoff block and its sentence templates; the adapter fix with per-rewrite certification links; contract lineage on implementation records and the start from a derived implementation | Extensa track | P16 |
| P18 | Iteration ladder | Extensa track | P17 |

**Measured in the evaluation, not here:** how often campaign candidates are refuted at N > 1 and the repair
calls that uses.

### Positioning against prior work — [03], [04], [05], [06], [21], [22]

**Claim:** the combination (reusable contracts proven once, automatic per-candidate proofs, guarded LLM
proof hints, counterexample-guided repair, an explicit accelerator proof semantics) and the subject
(LLM-written DX100 offloads). Never "first".

| Work | What it does | What it lacks next to Probata |
|---|---|---|
| Trivet (arXiv 2026) | LLM fills Lean proof holes when Alive2 times out | integer IR only; validates given transformations, not LLM-written source |
| LLMLift (NeurIPS 2024) | LLM invariants checked by SMT, lifting to DSLs | side-effect-free code; one proof per program; no reusable rule |
| ProofWright (arXiv 2025/26) | LLM annotates LLM CUDA kernels for VerCors/Rocq | the LLM also writes the spec; full equivalence for 14% |
| T-LLM Compiler (arXiv 2026) | LLM loop rewrites, bounded CBMC equivalence plus an LLM judge | bounded, per pair; its filter accepted 33.8% of wrong rewrites |
| ESBMC-AI (AST 2025) | LLM repairs C safety violations from model-checker counterexamples | safety only, unwind 1; no functional spec |
| LLM-Vectorizer, CoV, LLM-VeriOpt (CGO 2025–26) | Alive2 checks LLM output at IR level | bounded, per instance; no hints, no reusable spec |
| Autocomp, KernelCraft, QiMeng-Xpiler | LLM accelerator kernels | tests only |

- **Prove once vs per application:** Probata takes the staged hybrid PEC recommends ([03]).
- **Accelerator interfaces:** no prior "unready until a covering wait" semantics; the closest is Cell DMA
  race checking ([05]).
- **Alignment:** automatic aligners guess and check; none uses an LLM ([21]).
- **Race repair with an LLM** exists only for Java and Go; none for accelerator hazards ([22]).
- **Cite where terms first appear:** Trivet's proof gate beside our proof hint check; Orvalho et al. (AAAI
  2025) and AuthFix (ASE 2025) beside "counterexample-guided repair"; ESBMC-AI as AST 2025, not the
  preprint.

### Choices made while writing this spec

These were not decided in a ticket. Each fills a gap the tickets left.

| # | Choice | Why |
|---|---|---|
| S1 | One proof command (proposed name `swdb prove`) runs every proof job and writes its proof record. | Tickets fixed the job, the adapter interface and the record, not the entry point. One command mirrors `swdb certify` and gives one test seam. |
| S2 | The proven levels are computed by extending `swdb candidate-level`. | It already derives certified, uncertified or rejected from records on read, which is ADR 0016's rule. |
| S3 | "Ghost capacity" and "unknown" join the failure-class list. | [16] item 10 defines "not proven, ghost capacity", and [13] item 3 sends WP goals with class "timeout or unknown" to the hint loop. [26] item 10's list has neither, and an unlisted class would stop the batch. |
| S4 | A2 carries the proof-semantics checks no stage listed: the strict-layer agreement fixtures and the semantics negative controls (both per proof-semantics version), and the reduction lemma's bounded check on an asynchronous port (once, in the proof of concept). | [12] items 2, 8 and 9 require them; [27]'s A2 exit lists only the summary-form agreement. |
| S5 | The `bfs_read_offload` contract proof is completed in A4, on the repaired library code. Parts proven earlier on Peter's code as written are re-proven then. | Its reference instance (Peter's library code) races at N > 1 as written ([15]), and the repair changes the contract's content hash ([10] item 6). |
| S6 | WP runs whenever the bounded rung did not refute: a bounded timeout or missing minimum bounds does not block it. | [11] item 1 says "only after bounded proves", but the later [13] item 10 ("proven within bounds if SAW proved, else certified") and [25] item 1 (the skip rule; WP for every gain candidate) run WP without a bounded proof. Sound: a proof for every bound covers each one. |

Bookkeeping, not a new decision: the map's out-of-scope line "the strict layer is the trusted semantics"
now names the proof semantics, as [12] item 1 decided; ticket [01] carries a matching "Later changes" note.

### Open point O1 (decided)

**O1 — Code that applies no rewrite contract, and "proven requires certified".** [24] item 5 lets the
authors' code that matches no contract "reach proven unbounded" by route 1. But [09] item 7 and the
glossary allow a proven level only on a certified candidate artifact, and a candidate whose change applies
no contract is uncertified. [23] item 3 also counts a repair only if it still matches the same contract.
[24]'s own list of changed tickets does not include 09, so the conflict was never settled.

- **Decision (Yan-Ru accepted this default, 2026-10-13 22:10 ET):** keep "proven requires certified". Such
  code's computed level stays what certification gives.
  Its proof records are reported beside it as "direct proof, no matching contract: <verdict>", apart from
  RQ1's rates (as [24] says). Its refutations and repairs stay RQ4 subjects (the authors' PageRank:
  refute, then repair; [20], [23] item 10) but appear as their own row, outside RQ4's repair rate.
- **Rejected alternative:** let a direct-route proof set a proven level for such code. Cost: the glossary rule gets
  an exception, and the authors' code would carry a level that no contract's checks tested.
- **Where it matters:** only when the authors' code fails to match its kernel's contract; a held-out
  contract is drafted blind, so this is known only after the freeze.

## Testing Decisions

**What a good test is:**

- It calls a public command, or the verifier adapter interface, on fixture inputs, and checks the written
  record or verdict against a hand-derived expectation. It never imports internal helpers.
- Every check is tested with its negative controls: the proof setup check, the proof hint check, the
  verdict reading, the guard and the ladder's leakage check. A check that misses one of its controls is
  not trusted.
- Fixture records carry `contract_fixture` evidence and are never evidence about real code.
- Tests that need a real verifier, or LLVM 22, skip cleanly when it is missing.
- On the Mac, tests never run more than one real verifier job at a time; full-suite runs follow the RAM
  rules (at most 2 test workers).

### Seams (confirmed by Yan-Ru)

Confirmed 2026-10-13 22:10 ET.

1. **The proof command (new; the main seam).** Fixture subject in, proof record out, then `swdb validate`
   and `swdb build`. Verifier adapters plug in here: a scripted adapter for loop logic, the real tools for
   adapter tests. Cases:
   - proven; refuted with a counterexample; not proven with each failure class; an unclassified failure
     stops the batch;
   - per bounded tool, 07's safe smoke program proves and its seeded bug refutes; WP proves the safe
     program and leaves the bug "not proven", never refuted;
   - the proof setup check rejects a non-summary `assume`, a missing hazard probe, a clause without proof
     placement, a changed flag and an enabled WP cache;
   - the seven WP fact files of [13] (ghost interference, logic definitions, `check`/`assert`/`admit`,
     report statuses, tactic scripts, smoke tests, other constructs) are the first negative controls of the
     three checks; the proof hint check also accepts every allowed kind;
   - verdict reading ignores the consolidated `[ Valid ]` and a doctored cache;
   - seeds alone prove a fixture unit with no provider call; a failing seed is dropped;
   - a smoke test voids a vacuous proof; minimization keeps a proving subset;
   - a bounded run below the minimum bounds gives no level;
   - replay labels: reproduced, proof semantics only, not reproduced (stops the batch);
   - method parts: the semantics controls, the concurrency controls, and translator agreement on the
     strict wait-rule fixture scenarios.
2. **`swdb candidate-level` (existing, extended).** Fixture certification and proof records in, level out.
   Cases: weakest-of across proof units; the cap rule; assumption entries never cap; a changed pin makes a
   record stop counting; proven requires certified; refuted leaves selection; the two sub-rungs; snapshots
   name the level-rule version; "bug" only with a reproduction record.
3. **`swdb campaign --fixture` (existing).** A contract-fixture campaign with the scripted adapter. Cases:
   a refuted candidate is never evaluated and gets at most 5 repair rounds, apart from D7's 2; a reverted
   repair is flagged; both winners are tracked and the plateau test uses both; the WP phase starts only
   after the campaign stops, fastest gain candidate first, and ends when one is proven unbounded;
   `provider_calls_proof` and the budget lines; ladder rows (no gaps, levels, winner marks, no
   counterexample, no raw timing); `rewrite_workspace: v2`; a start from a derived implementation.
4. **Existing record seams.** `swdb validate` and `swdb build` for the new kinds, fields and tables; the
   handoff envelope's `certification_level` block (template sentences only); the provider workspace and
   guard (the three authors' names blocked; the `proof_hinting` workspace shows the authors' code only when
   it is the candidate; hint records never reach a rewriting workspace).

**Not unit tests:** the kill-test spike, calibration, A3's RQ3 run and the mbit10 reproduction. Their
records and the stage exit checks judge them.

**Prior art:** the typed certification tests and their negative-control tests; the strict wait-rule
differential fixture (11 scenarios; the pattern [12] item 8 reuses); the contract-fixture campaign tests
(selection, budgets, candidate records); the candidate-level tests in the Extensa boundary tests; the
provider workspace and guard tests; the shared LLVM 22 skip fixture; the record-closure helper for
component fixtures (LR-03).

## Out of Scope

- **Compiler correctness.** gcc and clang are trusted (clang 22.1.8 is a trusted-tool entry).
- **DX100 hardware versus its proof semantics.** Proofs trust the proof semantics rule by rule, each rule
  cited to gem5 source or assumed with an owner.
- **Speed.** A proof says nothing about performance.
- **gem5 runs.** Proofs never run or trust gem5 simulation. gem5 source is cited only as evidence for
  proof-semantics rules; performance evaluation still uses gem5 for DX100 (ADR 0010).
- **VerCors** on a hand-written model ([15]): hand-made, BFS only, sets no level.
- **Alignment proposals** ([24]): no evaluated kernel needs one.
- **Not built in this effort:** catalog relational templates (route 2, [24]); the relabeling-symmetry lever
  ([19]).
- **Not run:** an iteration-ladder ablation; MemAcc's `lessons.md` and an evolving system prompt ([28]);
  LLOR and DR.FIX (cited only).
- **Deferred until after the evaluation:** the strict layer's 8-byte tile-pair rule ([27]).
- **Proof data in the LANL core** ([26]).
- **Messages** to the DX100 authors, Eric or the team about these findings ([12], [20]).
- **Running the proof of concept.** This spec is design; the build is the next effort.

## Further Notes

**Main risks, in the order the plan meets them:**

| Risk | Tested in | If it fails |
|---|---|---|
| SAW cannot read clang 22 bitcode or keep ghost state | A1 (a) | crux-llvm with hand stubs |
| 2 lanes do not prove in 15 minutes | A1 (b), A2 | shape splitting; else candidates stay certified and Yan-Ru re-plans |
| WP cannot handle real-valued sums at our sizes | A1 (d) | re-plan |
| SSSP needs delta-stepping's outer-loop invariant | A3, synthetic fixture | re-plan (SSSP is on the floor) |
| The Rocq theorem does not fit 2 weeks | Rocq track | the written proof, an assumption entry |
| D35 still blocks new campaigns | before RQ5 | RQ5 is cut; a7 stays a worked example |
| A Homebrew change breaks LLVM 22 | every install | check `clang --version` first; keep `llvm` pinned |

**Paper framing:**

- The motivation is the false alarm, the PageRank defect and the N > 1 races. For the races: inherited
  from GAPBS, outside the DX100 offload, a one-line fix, harmless with today's compilers. They motivate;
  they are not the headline ([11]).
- Before writing "Extensa's ladder", check that Extensa's published runs postdate MemAcc commit
  `bc92c2eec` (2026-08-25); the ladder was empty before it ([28]).
- Citations from grilling tickets, not research files, still need a check before use: Lu et al. (ASPLOS
  2008) ([19] marks it unchecked), Lahav et al. (PLDI 2017) and Betts et al. (2012) ([15]).

**Side findings left for later** (no ticket opened): the certification schema text still says "candidate
1.3–1.6" while the default is 1.7 ([26]); SSSP needs "delta ≤ least weight" as a proof-unit precondition,
or a proof that its `assert(false)` is unreachable ([24]); the fork's baselines are themselves
hand-reshaped from upstream GAPBS ([17], [18]).

**Glossary:** the terms this map added are in `GLOSSARY.md` (its Updated line lists them by ticket). This
spec adds none.

[01]: issues/01-charting-decisions.md
[03]: issues/03-prove-once-rewrite-rules.md
[04]: issues/04-llm-proof-hints.md
[05]: issues/05-accelerator-interface-verification.md
[06]: issues/06-closest-prior-work.md
[09]: issues/09-what-proven-asserts.md
[10]: issues/10-proven-rewrite-contract.md
[11]: issues/11-verifier-choice.md
[12]: issues/12-dx100-proof-semantics.md
[13]: issues/13-proof-hint-loop.md
[14]: issues/14-dx100-wait-rule.md
[15]: issues/15-concurrency-proofs.md
[16]: issues/16-formal-half-language.md
[17]: issues/17-enabling-rewrites.md
[18]: issues/18-evaluation-claims-and-subjects.md
[19]: issues/19-bounded-verdict-bounds.md
[20]: issues/20-dx100-pr-reset-check.md
[21]: issues/21-relational-alignment-research.md
[22]: issues/22-cex-guided-llm-repair-research.md
[23]: issues/23-evaluation-baselines-and-metrics.md
[24]: issues/24-alignment-hint-kind.md
[25]: issues/25-extensa-loop-proofs-and-ranking.md
[26]: issues/26-proof-records.md
[27]: issues/27-proof-of-concept-stages.md
[28]: issues/28-extensa-iteration-ladder.md
