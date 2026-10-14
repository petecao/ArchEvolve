# 59 — Method-version review and freeze

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 42, 43, 50, 58, 61, 62 (drop 62 if cut)
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Records and levels" (method-version file contents), "Proven once vs per candidate", "Evaluation design" (research questions, reading a bar, protocol), "Proof-of-concept plan" (A6 exit); S8, S9, O1); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) items 2, 7 and later changes; [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 2, 3, 9; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 1, 5, 6, 7; [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) items 1, 5; [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) item 2
**Time estimate:** about 2 days plus Yan-Ru's review

**What to build:** The destination of this effort. Assemble the method-version file with every frozen
value, and write the final research-question pass bars beside it. Yan-Ru reviews both and commits them,
a human step, before any held-out run. That commit is the freeze: it ends the proof of concept and
unblocks the evaluation. After it, "the method" in the paper is one frozen, citable thing.

## Acceptance

- [ ] **Every frozen value is in the file**, each part cited by ID and content hash:
  - the verifier lineup with versions and flags (SAW 1.6 with crux-llvm 0.12 and CBMC 6.11 as fallbacks;
    Frama-C/WP 33.0 with Alt-Ergo, Z3 and CVC5; clang 22.1.8; frozen flags such as `-wp-cache none`,
    `-wp-model +real` and the x86_64 machdep);
  - CIVL and GenMC settings; the OpenMP runtime;
  - the C-lowering subset, the translators and the naming rules; the ACSL language version;
  - the proof-hint vocabulary; the three checks (proof setup check, proof hint check, verdict reading);
  - the budgets, at the mbit10-recalibrated values from 58 (hint rounds, loop wall time, WP time per
    solver, bounded-job time, CIVL's k) plus the 5 repair rounds;
  - the prompts; the shared-action kinds; the sharing-class names;
  - the shared logic library, with the sum library; the `std::vector` and `std::pair` models; ghost
    capacity K;
  - the Rocq development (design S8).
- [ ] **What stays out of the file:** the proof semantics (its own version), the level rule (its own
  version, so a rule change recomputes levels without voiding proofs), rewrite contracts and candidate
  artifacts. A check confirms none of them is in it.
- [ ] **The file is usable.** `swdb validate` accepts it. A proof setup check run against it passes on
  a frozen run and fails on the same run with one flag changed (negative control).
- [ ] **Final pass bars written,** one per research question, starting from the design's values and
  changed only with a recorded reason from calibration. They state the reading rule: the pooled held-out
  estimate with its 95% Wilson interval, and "met, not significant" when the interval crosses the bar.
  RQ3's "chained <= bundled" bar is dropped if A5 was cut. RQ3 claims no proof-speed gain unless A3's BFS
  run showed one. The RQ1 and RQ4 bars state O1's rule: code that matches no contract is reported apart
  from RQ1's rates and in its own row outside RQ4's repair rate.
- [ ] **Once-per-method parts count under the frozen version.** Proof records pinned to the frozen
  method version exist for the parallel composition theorem (Rocq-checked, or the written fallback as an
  assumption entry of kind "written proof"), the DX100 reduction lemma (Rocq-checked, or 29's written
  proof and bounded check with its entry of kind reduction; its statement was reviewed in 41), the
  shared-action commutativity
  lemmas, the sum library and the concurrency negative controls. The replay also covers every
  counting library-summary record (all per-call intrinsic summaries from 30, the `std::min`,
  `std::max`, `std::copy` and `std::swap` models from 24, the `std::vector` and `std::pair` models
  from 25) and every method-part record, 23's SAW float-mode check included. `swdb candidate-level`
  on Peter's repaired BFS candidate artifact (49) reads the same level under the frozen version as
  before it.
- [ ] **A6 exit** (design spec, "Proof-of-concept plan"; 27 item 5): every Mac verdict reproduces on
  mbit10 and the budgets are recalibrated (58's answer, no unexplained difference left); the
  method-version file reviewed and committed (this ticket). If it fails: root-cause before the freeze.
- [ ] **Freeze preconditions hold:** 51 is done or cut; no record names BC, PR or SSSP as a proof,
  calibration or contract subject; the authors'-code guard test (01) still passes.
- [ ] **Yan-Ru's review packet:** the file; a diff from the design's starting values, each change with
  its reason and mbit10 evidence; the pass bars. Also in the packet, each cited by ID and content hash
  (some keep their own version, outside the file):
  - the proof semantics, with its agreement evidence (29);
  - the single- and multi-thread minimum bounds as re-derived on Peter's repaired code (49); 33's and
    48's records appear only as superseded evidence;
  - the float-routing outcome: 23's SAW float-mode check as replayed under the frozen version (passed:
    SAW serves real-valued units; else "not confirmed in this effort" and crux-llvm `-f real` stays);
  - the logic and sum libraries (26) and the `std::vector` and `std::pair` models (25);
  - the DX100 reduction lemma's statement, as approved in 41 before the Rocq box (design S9), with
    43's outcome;
  - the BFS contract proof, as completed on Peter's repaired code (49).

  The agent hands it over and stops. Yan-Ru reviews and commits; the commit hash is recorded as the
  frozen method version's citation.
- [ ] **After the commit:** evaluation 01 and evaluation 02 unblock (evaluation 10 also waits for
  55). No held-out proof run, contract draft or population proposal is dated before the commit.

## Notes

- **Not in this ticket:**
  - 11 — Method-version file and failure classes: the file's format and the failure-class list.
  - 58 — Mac verdicts reproduced on mbit10: the recalibrated budget values and the root-caused
    differences used here.
  - 42 — Rocq: composition theorem proof; 43 — Rocq: DX100 reduction lemma: the results this ticket
    pins.
  - 50 — ThreadSanitizer one-day box: its outcome (the baseline runs in RQ4, or "not run"), settled
    before the freeze.
  - 61 — SAW whole-function equivalence (bounded direct route): that route, built before the freeze.
  - 62 — Route choice and predecessor proofs in the campaign: the campaign's route choice, built
    before the freeze. If 62 is cut (with A5), its edge drops.
  - 10 — Level rule: versioned apart from the method.
  - evaluation 01 — Correctness checks and certification drivers for PR and SSSP; evaluation 02 — BC
    held-out contract and contract proof: the first tickets after the freeze. Provider pins live in the
    evaluation's run plan (23 item 5), not here.
- **After the freeze (decided, 18 item 7):** any method change makes a new method version, re-runs every
  held-out kernel, and both runs are reported. Per-candidate budgets can rise only that way (25 item 2).
- Assumption (not decided in the map): the pass bars are committed in the same commit as the
  method-version file, inside it or beside it. Proofs do not use them, so they stay out of the
  method version's content-hash set.
- Assumption (not decided in the map): every proof record pins the method version (26 item 2), so
  records made under a draft version stop counting once the frozen version exists (unless the
  committed file's hash equals the draft's). This ticket replays, under the frozen version on mbit10
  (final hint sets inline, no provider call), the once-per-method parts, every counting
  library-summary record (30, 24, 25), every method-part record (23's SAW float-mode check included)
  and the records Peter's repaired candidate artifact's level depends on (its proof unit and the
  `bfs_read_offload` contract proof), so they count for the evaluation; Rocq results that landed
  after 58 (43) are re-checked here too.
- Assumption (not decided in the map): "prompts" means the prompt of every agentic role the evaluation
  runs: rewriting, proof hinting, counterexample-guided repair and contract drafting.
- **Flag for Yan-Ru.** Assumption (not decided in the map): the Extensa campaign rewriting prompt
  (changed by 15, 17 and 63) is frozen only if 14-17 and 63 land before the freeze; otherwise Yan-Ru
  decides whether that prompt is scoped out of the frozen prompts.
- The status stays `ready-for-agent` for the assembly; the commit itself is Yan-Ru's.
