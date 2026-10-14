# 11 — Method-version file and failure classes

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Records and levels" (method-version file, failure-class vocabulary); "Records and levels" (method-version file contents); "Verifier lineup and order" (failure classes, skip reasons); "Extensa mode" (per-candidate budgets belong to the method version); "Testing Decisions", seams 1 and 4; user stories 21, 61; S3; S8; O7); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (items 8, 9), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 3, 5, 7, 10, 11), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) (items 4, 5, 9), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) (items 1, 3, 6, 7, 10), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (item 7), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 1, 8), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) (item 2), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 3, 10 and its Later changes)
**Time estimate:** about 1 day

**What to build:** Two fixed lists that every proof depends on. First, the method-version file
kind, `library/methods/<version>.yaml` (name decided in map 26): one reviewed file that lists
everything a candidate artifact's proofs use apart from the rewrite contract, the candidate
artifact and the proof semantics. `swdb validate` checks it, and every proof record pins it by ID
and hash. Second, the failure-class vocabulary, `vocab/proof_failure_classes.yaml` (name decided in
map 26): the one list of failure classes and skip reasons. When an adapter reports a class outside
the list, `swdb prove` stops the batch. Yan-Ru gets "the method" as one citable thing, and every
"not proven" names a known cause.

## Acceptance

- [ ] **Every section.** `swdb validate` accepts a `contract_fixture` method-version file with all
      sections: verifier lineup (each tool, solver and front end with an exact version and its
      flags, clang 22.1.8 among them); CIVL and GenMC settings; the OpenMP runtime; the C-lowering
      subset, translators and naming rules; the ACSL language version; the proof-hint vocabulary;
      the three checks (proof setup check, proof hint check, verdict reading), each with its
      version; budgets; prompts; shared-action kinds; sharing-class names (S8); the shared logic
      library, sum library included; the `std::vector` and `std::pair` models (S8); a reference to
      the Rocq development, which holds the composition theorem and the DX100 reduction lemma (S8);
      ghost capacity K. Negative controls: removing any one section fails validation and names that
      section.
- [ ] **Exact pins.** A lineup entry with a version range, "latest" or no flags field fails
      validation. An explicit empty flags list passes.
- [ ] **Budgets.** The budgets section holds the per-candidate budgets 25 item 2 gives the method
      version, at their starting values: hint rounds (10), hint-loop wall time (60 min), bounded job
      time (15 min), counterexample repair rounds (5); plus WP time per solver (30 s), a hint-loop
      run-plan parameter (13 item 11); plus CIVL's k (3, calibrated; 15 item 9, S8). Removing any
      one fails validation.
- [ ] **Pinned by every proof record.** `swdb prove` writes the method version's ID and sha256 into
      every proof record. `swdb validate` rejects a proof record with no method-version pin, one that
      names a missing file, and one whose hash does not match the file. This catches a version file
      edited in place: changing any part makes a new method version (glossary), so the fix is a new
      file, never an edited record.
- [ ] **The failure-class list.** The failure-class vocabulary holds exactly these failure
      classes: parse error, unsupported construct, unwinding bound too small, timeout, out of memory,
      solver error, tool crash, vacuous pass (11 item 9); unknown and ghost capacity (S3); hint budget
      spent (13); below minimum bounds (19). And exactly these skip reasons: no contract proof, no
      minimum bounds, outside the C++ subset (25). `swdb validate` rejects a proof record whose
      failure class or skip reason is not on the list.
- [ ] **Every listed class records.** With a scripted adapter, `swdb prove` writes one "not proven"
      record per listed failure class; each passes `swdb validate` and `swdb build`.
- [ ] **Skips record.** For each skip reason, `swdb prove` runs no verifier and records the skip
      with its reason; the result passes `swdb validate` and `swdb build`.
- [ ] **An unlisted class stops the batch.** A scripted adapter that reports a class outside the list
      makes `swdb prove` stop: no proof record for that job, a non-zero exit whose message names the
      class and the adapter's raw output by path, and no later job in the batch starts. Control:
      the same batch with a listed class runs to the end.

## Notes

- **Not in this ticket:** 04 — Proof record tracer (the record and its pins; the failure class is
  checked there only for presence). 10 — Level rule (how a changed method-version pin stops a record
  from counting). 14 — Bounded gate in the campaign (reads the bounded job time and k; applies the
  skip reasons). 16 — Post-campaign WP phase and budgets (reads the per-candidate budgets from this
  file). 21 — C lowering and WP adapter (A2 tracer), 22 — SAW adapter and SAWScript translator,
  46 — CIVL adapter and 47 — GenMC adapter and agreement (map each tool failure to a class; build
  each class's handler; the regression corpus of diagnosed failures). 25 — `std::vector` and
  `std::pair` models. 36 — Proof setup check and verdict reading (confirms each run matches this
  file and records the result). 37 — The proof-hint loop (sends WP goals with class timeout or
  unknown to hint rounds). 39 — BFS unit proven unbounded at one thread; A3 exit (the calibrated
  Mac budget proposal). 41–43 — the Rocq development this file names. 44 — Shared-action kinds and
  commutativity lemmas (the kinds and sharing classes). 58 — Mac verdicts reproduced on mbit10 (the
  mbit10-recalibrated budget values). 59 — Method-version review and freeze (Yan-Ru's review; the
  frozen version and its frozen budget values).
- **Skip reasons (O7):** a skip skips only the steps that need the missing piece. "No contract
  proof" means no contract seeds and no bounded rung; route-1 WP still runs when the proof unit has
  a unit postcondition.
- Kept out of this file, as decided: the proof semantics has its own version (it belongs to the
  hardware target), and the level rule is versioned apart, so a rule change never voids proofs (26
  items 3, 9).
- Before the freeze the method version may change freely (25 item 2); every change is a new version
  (glossary). After the freeze, a change is a new method version, re-runs every held-out kernel, and
  both runs are reported (18 item 7).
- Assumption (not decided in the map): old method-version files stay in the library, so old records'
  pins still resolve. The current method version is the newest file; 10 — Level rule reads a record
  that pins an older one as no longer counting.
- Assumption (not decided in the map): proof records written before this ticket carry 04's "not
  applicable" method pin. They still pass `swdb validate` (records never change, ADR 0016); from this
  ticket on, `swdb prove` writes a real pin.
- Assumption (not decided in the map): this ticket ships the file kind, its validation and a
  `contract_fixture` file for tests. The first real method-version file is written once the lineup
  is installed (03 — New verifiers on the Mac). It gets a new version as each part lands, until 59
  freezes one.
- Assumption (not decided in the map): a batch is the list of proof jobs given to one `swdb prove`
  call.
- Assumption (not decided in the map): a skip writes a proof record with no verdict and its skip
  reason, so campaign summaries and the evaluation can count skips; the level rule ignores it. The
  alternative, reporting the skip only in `swdb prove`'s output, keeps "one record per proof job"
  stricter. Yan-Ru may choose.
- Assumption (not decided in the map): each failure-class entry carries its handler from 11 item 9
  as text (extend the lowering or subset; fix the adapter; hint loop; watchdog and rerun with more
  memory; minimal reproduction). The handlers themselves are built by the adapter tickets.
- Tests use the scripted adapter; no real verifier runs. Full-suite runs on the Mac use at most 2
  test workers.
- Assumption (not decided in the map): a draft (non-frozen) method version may mark a section "not yet built"; `swdb validate` accepts the marker only on drafts, and 59 refuses it. The ticket that lands a section writes the next draft version; 21 writes the first real draft once the lineup is installed (03).
