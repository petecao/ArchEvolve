# 26 — How are proof verdicts and their evidence recorded, and what does ArchEvolve mode show?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 20:50 ET)
**Blocked by:** 23, 25
**Map:** `../map.md`

## Question

Every resolved ticket left fields a record must hold. Decide the record shapes, where they live and
what the team sees:

- **A proof verdict** per proof unit and per candidate artifact: level; per bound dimension a value
  or "unbounded"; the cap from proven dependencies; the assumption set with each entry's kind (09);
  the failure class of a "not proven" (11 item 9); verifier lineup versions, solvers and flags (11
  item 8); the proof-semantics version and its agreement evidence (12); hint sets with provenance,
  rejections by rule, rounds, provider calls, tokens, time, refutation replay status, vocabulary
  and check versions (13); CIVL and GenMC settings, the parallel composition theorem's version and
  status, the OpenMP runtime and RC11 entries (15); formal-half language and translator versions,
  the lowering's naming-rule version, logic-library hashes and `\false`-check results, the
  standard-library model version and its two entries, ghost capacity K, gate results per formal
  half (16); per rewrite in a rewrite chain, its contract hash, predecessor snapshot hash, result
  hash, certification record and proof route, and derived implementations' contract lineage (17).
- **Once-proven parts** (building blocks, contract proofs, the composition theorem): their records,
  levels and content-hash sets, and how a changed hash reopens dependents (10 item 6).
- **Where each lives:** research-database YAML (ADR 0002), the SWDB extension beside LANL's shape
  (ADRs 0014, 0015), raw output on mbit10 (ADR 0011); compact evidence vs bulky raw output.
- **What ArchEvolve mode shows** for a candidate artifact handed to the team: level, bounds and the
  assumption set in plain words.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Records" fog. Known defect to fix in the build:
  with several contracts per candidate, the campaign adapter returns only the first certification
  record ID (`swdb/campaign_targets.py:555-586`; 17's side findings).
- 2026-10-13 20:10 ET: input from 19 (resolved): each verdict records its build constants, the
  minimum-bounds version, the bounds used, the shape-split count check and the failure class.
- 2026-10-13 20:43 ET: input from 25 (resolved): per candidate artifact: the bounded gate's result per
  level, refutation and repair lineage (reverted-repair flag), the WP verdict; per class: the fastest
  winner and the best-proven winner, recomputed after WP; per campaign: proof lane-hours, proof-hint
  and repair call counts, and any approval entry that raised a budget. ArchEvolve mode reports its one
  final candidate's level, never a ranking.
- 2026-10-13 21:06 ET: claimed 20:50 ET. Facts re-checked in code this session: certification records
  have no level or proof field (`schemas/certification.schema.json`); library clauses allow only
  `formal_label: stated` (`swdb/library.py:394-401`); a changed hash reopens nothing, old receipts stop
  counting on read (`swdb/library.py:281-291`); the handoff envelope has no level or assumptions
  (`swdb/handoff.py:207-288`); LANL `Validation_results` is one pass/fail per kernel variant and input
  (`swdb/lanl_validation.py:33-36`); the adapter defect is confirmed (`swdb/campaign_targets.py:585`).
- 2026-10-13 21:06 ET: round 1, all seven recommendations accepted by Yan-Ru: Q1 a new `proof`
  record kind, one immutable record per proof job, with a subject; Q2 level computed on read from
  pins, dated snapshots only; Q3 one reviewed method-version file; Q4 seven assumption kinds (written
  proof, platform choice added; glossary updated); Q5 SWDB extension only, evidence by path and hash,
  scratch deleted; Q6 campaign, repair and run fields in existing kinds; Q7 a plain-words
  `certification_level` block in the handoff.
- 2026-10-13 21:09 ET: round 2: Q8-Q12 accepted by Yan-Ru (refutation evidence, level-rule version,
  failure-class list, promotion review pins the level, ADR 0016). Q13 (glossary terms "proof record" and
  "content-hash set") not yet answered.

## Answer

2026-10-13 21:09 ET. Decided with Yan-Ru in a grilling session (rounds 1-2 in Comments; every
recommendation accepted). Recorded in [ADR 0016](../../../docs/adr/0016-proof-records-never-change-level-computed-on-read.md)
(proposed).

1. **One new record kind, `proof`** (Q1). Each proof job writes one record in `records/proofs/` that
   never changes. A `subject` names what was proven: a candidate artifact's proof unit; a library
   entry's summary; a contract-proof part (unit postcondition on the reference instance, lifting
   lemma, negative controls, minimum-bounds derivation); a method part (the parallel composition
   theorem, the proof-semantics agreement checks of 12 item 8); or a whole-kernel reproduction
   (item 8). Drafted formal halves (16 item 5) need nothing new: gates 2-3 are proof records, gate 4
   certification records, gate 5 a review record. Rejected: a proof section in the certification
   record (WP runs after the campaign; evidence would be rewritten); one editable level record per
   candidate (once-proven parts have no candidate).
2. **The level is computed on read** (Q2). A proof record counts only while every pin in its
   content-hash set matches the current hash, as certifications work today
   (`swdb/library.py:281-291`). A candidate artifact's level is the weakest among its counting proof
   records and the proven parts they depend on (09's cap rule). A change reopens by making records
   stop counting; nothing is rewritten. Pins per record: the code proven (candidate tree hash, entry
   or contract hash), the contract, the baseline function, the reference semantics, the
   proof-semantics version, the method version, each summary used (entry hash plus its proof record
   ID), the minimum-bounds version, the predecessor snapshot (17), and every build constant's value.
   Campaign summaries, handoffs and reviews show dated snapshots only. Example: proof semantics v2
   lands, candidate X's records pin v1, X reads as certified; its campaign summary still shows its
   old level, dated.
3. **The method version is one reviewed file** (Q3), `library/methods/<version>.yaml`, cited by ID
   and hash. It lists the verifier lineup (tools, solvers, clang 22.1.8, flags), CIVL and GenMC
   settings, the OpenMP runtime, the C-lowering subset, translators and naming rules, the ACSL
   language version, the proof-hint vocabulary, the three checks, budgets, prompts, shared-action
   kinds, the shared logic library (with 24's sum library), the `std::vector` model and ghost
   capacity K. Frozen by Yan-Ru's review at the freeze (18). The proof setup check confirms each run
   matches it and records the result. The proof semantics keeps its own version (it belongs to the
   hardware target). Glossary "method version" sharpened; catalog templates dropped (24).
4. **Seven assumption kinds** (Q4): assumed clause, proof semantics, summary, reduction, trusted
   tool, plus **written proof** (09 item 6; 15 item 8) and **platform choice** (11 item 11; float
   rounding, 09 item 4; the RC11 memory model, 15). Each entry: kind, reference (ID and hash), one
   plain sentence. Glossary "assumption set" sharpened.
5. **Where it lives** (Q5).
   - SQLite: `swdb_proofs` plus child tables for pins, assumptions and bounds, in the SWDB extension.
     Nothing in the LANL core: `Validation_results` is one outcome per input
     (`swdb/lanl_validation.py:33-36`), and rewrite candidates already stay out (lines 10-13).
   - Inline in the YAML: the final hint set and any counterexample (small; needed for replay and
     repair).
   - Compact evidence on the run host, by path and sha256: verifier logs, per-goal reports, earlier
     rounds' hint sets.
   - Verifier scratch (WP and Why3 caches, generated bitcode, CIVL work folders) is never named by a
     record and is deleted when the job ends; ADR 0011 needs no new bulky class.
   - Mac proof-of-concept output goes to a Mac runs folder outside the repo, host `mac`; paper
     numbers come only from mbit10 (13 item 13).
6. **Campaign, repair and run fields in existing kinds** (Q6).
   - Campaign summary (`swdb/campaign.py:1315-1348`): per class, the fastest winner and the
     best-proven winner, each with a dated level snapshot; `budgets.used` adds proof lane-hours,
     proof-hint calls and repair calls. Written when the campaign stops, rewritten once when the WP
     phase ends.
   - Raised budgets stay in the campaign file's `approval` block
     (`schemas/extensa_campaign.schema.json:87-98`).
   - Repair lineage on the repaired candidate's proposal: the refuted candidate, the proof record
     with the counterexample, the round, and the reverted-repair flag from a deterministic check.
   - 23's run fields: worker core, wall and CPU time and batch load in each proof record's job block;
     run index (1-3) and provider pin on the proposal.
7. **ArchEvolve mode shows a plain-words block** (Q7). The `evaluation_result` envelope
   (`swdb/handoff.py:207-288`) gains `certification_level`: the level; each bound dimension's value or
   "any"; each assumption as its plain sentence; "says nothing about speed"; the proof record IDs.
   When not proven: the highest level reached and the failure class in words. Sentences come from a
   fixed template per assumption kind plus each assumed clause's own sentence; no LLM writes them.
   Example: "Proven for every graph and every thread count. Assumes: DX100 follows its proof semantics
   v3, each rule cited to gem5 source; clang 22.1.8 compiles correctly; CPU caches hold no stale copy
   after a DX100 store (assumed; owner Eric). Says nothing about speed."
8. **Refutation evidence** (Q8). 13 item 10's steps 1-2 (unit refuted, strict-layer replay) are one
   job, so one proof record. Step 3, a whole-kernel reproduction, is its own proof record (subject
   `kernel_reproduction`) citing the refutation. "Bug" is computed on read when a reproduction exists.
9. **Level-rule version** (Q9). Each snapshot names the version of the level rule (weakest-of, cap
   rule) that computed it. The rule is outside the method version: every proof record pins the
   method version, so a rule change would void every proof instead of recomputing levels.
10. **One failure-class list** (Q10), `vocab/proof_failure_classes.yaml`. Failure classes: 11 item 9's
    eight, plus "hint budget spent" (13) and "below minimum bounds" (19). Skip reasons: no contract
    proof, no minimum bounds, outside the C++ subset (25). A failure outside the list stops the batch
    (11).
11. **Promotion pins the level** (Q11). A candidate's promotion `review` cites its proof record IDs and
    the level snapshot at promotion, so a later drop shows against what was approved.
12. **Generality.** Nothing here is BFS- or DX100-specific: the record kind, subjects, pins, kinds and
    the handoff block apply per contract, kernel and hardware target.

**Build items** (to 27): the `proof` schema and `records/proofs/`; the `swdb_proof*` tables; the
level rule (versioned); `library/methods/<version>.yaml` and its review; `vocab/proof_failure_classes.yaml`;
the handoff block and its sentence templates; campaign-summary fields and the post-WP rewrite;
repair lineage and run fields on proposals; promotion review fields; the adapter returning every
certification record ID, one per contract (`swdb/campaign_targets.py:585`). The schema text still
says "candidate 1.3-1.6" (`schemas/certification.schema.json:55`) while the default is 1.7 (side
finding, not fixed here).

**Open:** Q13, the glossary terms "proof record" and "content-hash set", awaits Yan-Ru.
