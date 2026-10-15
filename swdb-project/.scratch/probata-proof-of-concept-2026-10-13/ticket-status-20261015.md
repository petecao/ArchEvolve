# Current Probata ticket status

Updated: 2026-10-15 15:05 ET.

32 resolved / 28 ready-for-agent / 3 claimed. Active frontier: **07, 24, 27**.
Derived from authoritative ticket frontmatter; unresolved dependencies still gate later work.
[Current resume](resume.md). Historical proof evidence retains its exact source pins.

| Ticket | Status | Unresolved blockers |
|---|---|---|
| [01 — Guard blocks the authors' held-out functions](issues/01-guard-authors-held-out-functions.md) | resolved | none |
| [02 — Campaign adapter returns every certification record](issues/02-adapter-every-certification-record.md) | resolved | none |
| [03 — New verifiers on the Mac](issues/03-install-new-verifiers-mac.md) | resolved | none |
| [04 — Proof record tracer](issues/04-proof-record-tracer.md) | resolved | none |
| [05 — Spike (a): SAW on clang 22 bitcode](issues/05-spike-saw-clang22.md) | resolved | none |
| [06 — Spike (b): 2 lanes under 15 minutes](issues/06-spike-two-lanes.md) | resolved | none |
| [07 — Spike (c): WP with agent hints](issues/07-spike-wp-agent-hints.md) | claimed | none |
| [08 — Spike (d): sums over reals](issues/08-spike-sums-over-reals.md) | resolved | none |
| [09 — Spike verdict](issues/09-spike-verdict.md) | resolved | 07 |
| [10 — Level rule](issues/10-level-rule.md) | resolved | none |
| [11 — Method-version file and failure classes](issues/11-method-version-and-failure-classes.md) | resolved | none |
| [12 — Proposal and promotion fields](issues/12-proposal-and-promotion-fields.md) | resolved | none |
| [13 — Counterexample-guided repair](issues/13-counterexample-guided-repair.md) | resolved | none |
| [14 — Bounded gate in the campaign](issues/14-bounded-gate-in-campaign.md) | resolved | none |
| [15 — Two winners](issues/15-two-winners.md) | resolved | none |
| [16 — Post-campaign WP phase and budgets](issues/16-post-campaign-wp-phase.md) | resolved | none |
| [17 — Iteration ladder](issues/17-iteration-ladder.md) | resolved | none |
| [18 — ArchEvolve mode level and handoff block](issues/18-archevolve-mode-level-and-handoff.md) | resolved | none |
| [19 — Derived implementations](issues/19-derived-implementations.md) | resolved | none |
| [20 — Formal-half frame](issues/20-formal-half-frame.md) | resolved | none |
| [21 — C lowering and WP adapter (A2 tracer)](issues/21-c-lowering-wp-tracer.md) | resolved | none |
| [22 — SAW adapter and SAWScript translator](issues/22-saw-adapter-and-translator.md) | resolved | none |
| [23 — C-stub translator, fallbacks and check mode](issues/23-stub-translator-fallbacks-check-mode.md) | resolved | none |
| [24 — C++ subset widening](issues/24-cpp-subset-widening.md) | claimed | none |
| [25 — std::vector and std::pair models](issues/25-vector-and-pair-models.md) | ready-for-agent | 24 |
| [26 — Logic and sum libraries](issues/26-logic-and-sum-libraries.md) | resolved | none |
| [27 — Proof semantics for the BFS read-offload calls](issues/27-proof-semantics-bfs-calls.md) | claimed | none |
| [28 — Proof semantics for the remaining maa_* calls](issues/28-proof-semantics-remaining-calls.md) | ready-for-agent | 27 |
| [29 — Proof-semantics checks](issues/29-proof-semantics-checks.md) | ready-for-agent | 28 |
| [30 — Reference definitions, per-call summaries and new intrinsic versions](issues/30-reference-definitions-and-summaries.md) | ready-for-agent | 25, 28 |
| [31 — Five-gate drafting and the new bfs_read_offload version](issues/31-five-gate-drafting-and-read-offload-version.md) | ready-for-agent | 30 |
| [32 — BFS contract proof](issues/32-bfs-contract-proof.md) | ready-for-agent | 31 |
| [33 — Minimum-bounds script and A2 exit](issues/33-minimum-bounds-and-a2-exit.md) | ready-for-agent | 29, 32 |
| [34 — proof_hinting role and workspace](issues/34-proof-hinting-role.md) | resolved | none |
| [35 — Hint records, merger and proof hint check](issues/35-hint-records-and-proof-hint-check.md) | resolved | none |
| [36 — Proof setup check and verdict reading](issues/36-proof-setup-check-and-verdict-reading.md) | ready-for-agent | 27 |
| [37 — The proof-hint loop](issues/37-proof-hint-loop.md) | ready-for-agent | 33, 36 |
| [38 — Calibration on the public C suites](issues/38-calibration-public-suites.md) | ready-for-agent | 37 |
| [39 — BFS unit proven unbounded at one thread; A3 exit](issues/39-bfs-unit-unbounded-and-a3-exit.md) | ready-for-agent | 33, 37, 38, 40 |
| [40 — Bucketed-relaxation fixture](issues/40-bucketed-relaxation-fixture.md) | ready-for-agent | 37 |
| [41 — Rocq: composition theorem statement and definitions](issues/41-rocq-statement.md) | resolved | none |
| [42 — Rocq: composition theorem proof](issues/42-rocq-composition-theorem.md) | resolved | none |
| [43 — Rocq: DX100 reduction lemma](issues/43-rocq-reduction-lemma.md) | ready-for-agent | 29 |
| [44 — Shared-action kinds and commutativity lemmas](issues/44-shared-action-kinds.md) | ready-for-agent | 31 |
| [45 — Per-thread lowering](issues/45-per-thread-lowering.md) | ready-for-agent | 24, 44 |
| [46 — CIVL adapter](issues/46-civl-adapter.md) | ready-for-agent | 25, 45, 60 |
| [47 — GenMC adapter and agreement](issues/47-genmc-adapter-and-agreement.md) | ready-for-agent | 46 |
| [48 — Concurrency negative controls](issues/48-concurrency-controls.md) | ready-for-agent | 33, 47, 60 |
| [49 — Peter's race repaired; A4 exit](issues/49-peter-race-repair-and-a4-exit.md) | ready-for-agent | 39, 48 |
| [50 — ThreadSanitizer one-day box](issues/50-threadsanitizer-box.md) | resolved | none |
| [51 — Strict-layer catch-up](issues/51-strict-layer-catch-up.md) | ready-for-agent | 29 |
| [52 — Split the bundled read offload](issues/52-split-bundled-read-offload.md) | ready-for-agent | 31 |
| [53 — Chained vs direct vs bundled; A5 exit](issues/53-route-three-and-a5-exit.md) | ready-for-agent | 45, 49, 52 |
| [54 — Upstream-GAPBS demo](issues/54-upstream-gapbs-demo.md) | ready-for-agent | 53 |
| [55 — End-to-end fixture campaign with real verifiers](issues/55-end-to-end-fixture-campaign.md) | ready-for-agent | 39, 48, 60 |
| [56 — Verifier lineup on mbit10](issues/56-lineup-on-mbit10.md) | resolved | none |
| [57 — Proof workers in a socket lane](issues/57-proof-workers-in-socket-lane.md) | resolved | none |
| [58 — Mac verdicts reproduced on mbit10](issues/58-reproduce-on-mbit10.md) | ready-for-agent | 38, 40, 49, 51, 53, 54 |
| [59 — Method-version review and freeze](issues/59-method-version-freeze.md) | ready-for-agent | 43, 58, 62 |
| [60 — Strict-layer replay and whole-kernel reproduction](issues/60-strict-layer-replay-and-kernel-reproduction.md) | ready-for-agent | 29 |
| [61 — SAW whole-function equivalence (bounded direct route)](issues/61-saw-whole-function-equivalence.md) | resolved | none |
| [62 — Route choice and predecessor proofs in the campaign](issues/62-route-choice-and-predecessor-proofs.md) | ready-for-agent | 53 |
| [63 — Experimental enabling contracts and the shared-contracts rule](issues/63-experimental-enabling-contracts.md) | resolved | none |
