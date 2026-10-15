# The level rule (`swdb candidate-level`)

Created: 2026-10-14 02:15 ET, Probata proof of concept ticket 10. Updated: 2026-10-14 ET, part names
pinned in vocabulary `proof_part_names`.
Updated: 2026-10-14 02:57 ET, ticket 12: `promotion` shows the approved level snapshot beside the level now.
Updated: 2026-10-14 17:25 ET, ticket 61: no-contract-baseline records are measurements (`baseline_measurements`),
a `bounded_direct` record above threads = 1 within bounds never counts, and a `baseline_function` pin may name a
candidate artifact. These make the rule `level-rule.2` (decided by the main session under Yan-Ru's delegation,
2026-10-14 20:48 ET: the versioning rule is strict even when no level changes). Snapshots stored earlier keep
`level-rule.1` (for example the handoff examples in `docs/bfs-handoff-examples/`); they are never recomputed.
Updated: 2026-10-15 ET, ticket 42: `level-rule.3` discharges a matching written-proof entry when a counting Rocq-checked method-part record exists. The original proof record stays unchanged.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/10-level-rule.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Records and levels", S11, S14, O1, O6, O7), map 26,
[ADR 0016](../adr/0016-proof-records-never-change-level-computed-on-read.md). Code: `swdb/level_rule.py`.
Records: [format-v0.4-proof.md](format-v0.4-proof.md).

**In one line:** `swdb candidate-level <candidate>` reads the certification and proof records and
returns one level with its reason. Nothing is stored; a changed pin changes the answer on the next read.

## The levels, ranked

| `rank` | `level` | Words |
|---|---|---|
| 4 | `proven_unbounded` | proven unbounded: every bound dimension, threads included, is `unbounded` |
| 3 | `proven_within_bounds_threads_k` | proven within bounds, threads ≤ k: some dimension bounded, threads not 1 |
| 2 | `proven_within_bounds_threads_1` | proven within bounds, threads = 1 |
| 1 | `certified` | certified, no counting proof |
| 0 | `uncertified` (and `rejected`, as certification gives it) | |

Bounds above the minimum are reported, never ranked.

## The rule (`level-rule.3`)

1. **A proof record counts** only while every pin in its content-hash set matches the current hash, no
   failed part voids what it pins, and every proof record it depends on still counts. A
   `not_applicable` pin always matches.
2. **Caps.** A counting proven record's bounds become, per dimension, the smallest of its own bounds and
   those of every proven part it depends on. Its level is read from those bounds. An unproven
   dependency never caps (it is an assumption entry). Assumption entries never cap.
3. **Within one proof unit**, the highest counting record sets the unit's level, whatever its route
   (S11). **Across proof units**, the weakest wins, and each bound dimension shows its smallest bound.
4. **Proven requires certified** (O1). A **counting refuted record** of the candidate artifact blocks
   every proven level and sets the refuted flag.

A proof unit is one per rewrite contract the candidate artifact applies, read from its counting
certifications that certify. A proof unit's records are the candidate's `candidate_proof_unit`
records whose `contract` pin names that contract.

### Current hash per pin kind

| Pin | Current value |
|---|---|
| `code` | a candidate artifact's `artifact.sha256`; otherwise a library entry's content sha256 |
| `contract` | the contract's library content sha256 |
| `baseline_function` | the pinned source snapshot record's `artifact.sha256` (ticket 61: or the pinned candidate artifact's, a whole-function baseline) |
| `reference_semantics` | the pinned library entry's content sha256 |
| `proof_semantics` | the file sha256 of the pinned version, only while it is the current version of its line in `library/proof_semantics/` (highest `sequence` per `target`) |
| `method_version` | the file sha256 of the current method version (`swdb.method_version.current`); an older version never matches |
| `summaries` | each entry's library content sha256; and its `proof_record` must count |
| `minimum_bounds` | the content digest (`swdb.artifacts.digest`) of the pinned minimum-bounds derivation record; that record must count |
| `predecessor_snapshot` | the predecessor candidate artifact's `artifact.sha256`; the predecessor must have a proven level |
| `build_constants` | the value each dependency record (summary, minimum-bounds derivation, contract-proof part) pins for the same name |

### Dependencies (what caps and what stops counting)

| Dependency | Which records | Caps with |
|---|---|---|
| Summary | the `proof_record` of each `summaries` pin | its level after its own caps |
| Contract-proof parts | `contract_proof_part` records of the same contract content (`contract` pin equal), any part but `minimum_bounds_derivation`; per part, the highest counting proven record | that record's level |
| Minimum-bounds derivation | the record the `minimum_bounds` pin names | its bounds |
| Predecessor (route 3) | the predecessor candidate artifact's proven level | its bounds |

A part with records of which none counts stops its dependents counting (10 item 6). A part whose
counting records are all unproven does not cap. With no contract-proof records at all (O7's skip), nothing caps.

### Voids

A counting refuted record of these subjects voids what it pins, even while it is current. The level
rule reads which part voids what from vocabulary `proof_part_names` (field `voids`), the one list of
part names; `swdb validate` refuses an unlisted part or one of another subject kind. Every other
record that pins the voided version or content stops counting, and the output names the failed record.

| Subject (`kind`, `part`) | Voids |
|---|---|
| `method_part`, `semantics_controls` | its `proof_semantics` pin (12 item 9) |
| `method_part`, `concurrency_controls` or `civl_genmc_agreement` | its `method_version` pin (15 items 9, 12) |
| `contract_proof_part`, `negative_controls` | its `contract` pin: the contract proof is void (10 item 2) |

A failed part is a refuted record: its claim ("every control has its required verdict", "CIVL and
GenMC agree") is refuted, and its counterexample names the control and the verdict it got.

### Below minimum bounds

A counting proven record whose bounds fall below its pinned minimum bounds in any dimension (a
dimension of the minimum it does not bound counts as below) gives no level. So does a not-proven record
with failure class `below_minimum_bounds`. Both are listed as "bounded check below minimum".

### Refuted and bug

The refuted flag lists each counting refuted `candidate_proof_unit` record of the candidate with its
`replay_label` (null when absent; 60 makes it required). It reads `"bug"` only while a counting
`kernel_reproduction` record with verdict `refuted` names that refutation in its subject `id`; else
`"unit-level refutation"`. A refutation labeled `undefined_behavior` counts like any other (O6).

## Output

The existing fields keep their meaning (`candidate`, `certifications`, `counted`, `stale`, `mode`,
`campaign`, `promotion`, `certification_level`, `proof_records`). New or changed:

| Field | Meaning |
|---|---|
| `level` | the level above; a proven level only on a certified, unrefuted candidate artifact |
| `rank` | the level's rank (table above) |
| `level_rule` | the level-rule version, `level-rule.3` (`level-rule.2` before ticket 42) |
| `proven` | null, or `{level, bounds, records}`: the level, per dimension the smallest bound across proof units, the records that set it |
| `proof_units` | per contract: `{contract, level, bounds, records: [{record, bounds, route, caps}]}`; `caps` lists each dependency that lowered that record's level (`kind`, `record` or `candidate`, `bounds`) |
| `assumptions` | the assumption set of the level: each entry (`kind`, `reference`, `sentence`) of the records that set it and of the proven parts they depend on, once, with `records` |
| `stale_proofs` | each proof record of the candidate that stopped counting: `{record, pins: [{pin, reason, dependency?, failed?}]}` |
| `below_minimum` | `{record, text: "bounded check below minimum", dimensions}` |
| `direct_proofs` | O1: counting records whose contract is not one the candidate is certified for: `{record, text: "direct proof, no matching contract: <verdict>"}` |
| `skipped` | skip records: `{record, skip_reason}`. A skip sets no level and blocks none (O7) |
| `baseline_measurements` | ticket 61: no-contract-baseline records (`route: bounded_direct`, contract pin not applicable): `{record, verdict, bounds}`. They set no level, never set the refuted flag, and are left out of every other list here. A `bounded_direct` record whose bounds read above proven within bounds, threads = 1 never counts (`stale_proofs`, pin `route`) |
| `refuted` | `{flag, records: [{record, replay_label}], evidence: null, "unit-level refutation" or "bug", reproductions}` |
| `snapshot` | `{level, at: "YYYY-MM-DD HH:MM ET", level_rule, records}`: the dated form campaign summaries, handoffs and promotion reviews store (`swdb.level_rule.snapshot`) |
| `promotion` | null, or the current promotion `{review, attribution}`; a review written by `swdb promote` since ticket 12 adds `level_snapshot` (what Yan-Ru approved, never recomputed), `proof_records` (those that counted at promotion) and `dropped` (true when `level` now ranks below the snapshot's level, for example after a pinned proof-semantics version is superseded) |

## Versioning rule

The level rule's version is `swdb.level_rule.VERSION`. It lives outside the method version (26 item 9):
a rule change recomputes levels and voids no proof. Proof records never hold a level or a level-rule
field (`swdb validate` refuses `level` and `level_rule`). Any change to the rule above is a new version.
