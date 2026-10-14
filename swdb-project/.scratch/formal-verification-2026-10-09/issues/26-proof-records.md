# 26 — How are proof verdicts and their evidence recorded, and what does ArchEvolve mode show?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** ready-for-human
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
