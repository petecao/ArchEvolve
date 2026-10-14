# 10 — Level rule

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 02:24 ET (resolved, ticket 10 answer); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 04, 11
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Solution" (levels); "What a proven verdict asserts" (proof unit, assumption set, cap rule); "Proven once vs per candidate" ("once" means once per content-hash set; a control that proves voids the contract proof); "Bounds" (below the minimum, no level); "Refutation, repair and bugs" (evidence steps); "Records and levels"; "Testing Decisions", seam 2; user stories 1, 2, 5, 6, 7, 8, 13, 14, 22, 24, 59, 60; S2; S6; S11; S14; O1; O6; O7); decisions: [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) (items 5, 7, 8, 9, 11), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) (items 2, 5, 6), [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) (item 4.3, route 3 inherits its predecessor's verdict), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) (items 2, 9), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) (items 9, 12), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 1, 7), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (item 5 and its Later changes), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 2, 4, 8, 9); [ADR 0016](../../../docs/adr/0016-proof-records-never-change-level-computed-on-read.md)
**Time estimate:** about 2 days

**What to build:** `swdb candidate-level` computes a candidate artifact's full certification level
each time it is read, from its certification records and proof records, under a versioned level
rule (ADR 0016). Yan-Ru runs it on any candidate artifact and gets one level: proven unbounded;
proven within bounds, threads ≤ k; proven within bounds, threads = 1; certified; uncertified
(rejected stays as today). Within one proof unit, the highest counting record sets the level,
whatever its route; across proof units and dependencies, the weakest wins (S11). Beside the level
comes the reason: the proof records that count, the ones that stopped counting and the pin that
changed, the dependency that capped the level, the bounds per dimension, the assumption set, a
refuted flag with its replay label, "bug" only when a reproduction earns it, and the level-rule
version. Nothing is stored and nothing is rewritten; a changed pin changes the answer on the next
read. Code that applies no contract keeps its certification level, with its direct proof shown
beside it (O1). The same computation yields the dated snapshot that campaign summaries, handoffs and
promotion reviews keep. This ticket also owns the optional replay-label field on refuted proof
records, with O6's four values; 60 fills it and makes it required.

## Acceptance

- [x] **Order.** On fixture certification and proof records, `swdb candidate-level` returns each
      level, ranked: proven unbounded > proven within bounds, threads ≤ k > proven within bounds,
      threads = 1 > certified > uncertified. A candidate artifact with counting records at both
      bounded sub-rungs reads threads ≤ k. A record unbounded in every data dimension but at
      threads = 1 reads proven within bounds, threads = 1, never proven unbounded. Bounds above the
      minimum are reported, never ranked: two threads = 1 records with different bounds above the
      minimum read the same level.
- [x] **Pins.** A proof record counts only while every pin in its content-hash set matches the
      current hash. Negative controls, one per pin kind: change the code proven, the contract, the
      baseline function, the reference semantics, the proof-semantics version, the method version,
      one summary (entry hash or its proof record ID), the minimum-bounds version, the predecessor
      snapshot, or one build constant. Each time, the record stops counting, the output lists it as
      stale with the pin that changed, and the candidate artifact reads the level its remaining
      records give (certified when none remain). Every record file is byte-identical before and
      after.
- [x] **Two routes, one proof unit (S11).** A proof unit with counting records by two routes reads
      the higher level: any valid proof counts. Each record's level is taken after its caps.
      Fixture: a route-3 record capped at proven within bounds, threads = 1 by its predecessor's
      proof, plus a route-1 record proven unbounded, reads proven unbounded. Control: without the
      route-1 record, the unit reads proven within bounds, threads = 1.
- [x] **Weakest of, across proof units and dependencies (S11).** A candidate artifact with two proof
      units, one proven unbounded and one proven within bounds at threads = 1, reads proven within
      bounds, threads = 1. Per bound dimension the output shows the smallest bound.
- [x] **Cap rule.** A proven dependency caps the level. A per-candidate record proven unbounded that
      uses a summary proven only within bounds reads proven within bounds, and the output names the
      summary as the cap. The same holds for a contract-proof part (unit postcondition, lifting
      lemma, negative controls, minimum-bounds derivation) and, on route 3, for the predecessor's
      proof (17 item 4.3). When a dependency's record stops counting, every record that depends on
      it stops counting too (10 item 6). A contract proof whose negative-control part shows a
      control proven is void, and its dependents read certified (10 item 2).
- [x] **Failed method parts void their version.** A failed method-part record voids the version it
      tests: a semantics control with the wrong verdict voids its proof-semantics version (12 item
      9); a concurrency control with the wrong verdict, or a CIVL–GenMC contradiction, voids its
      method version (15 items 9, 12). Every record that pins the voided version stops counting, even
      though that version is still the current one; the output lists each as stale and names the
      failed record. Fixtures: one failed record of each of the three kinds. Control: a record that
      pins a different version keeps counting. Every record file is byte-identical before and after.
- [x] **Assumption entries never cap.** A record proven unbounded whose assumption set holds one
      entry of each of the seven kinds (assumed clause, proof semantics, summary, reduction, trusted
      tool, written proof, platform choice) still reads proven unbounded. The fixture includes the
      once-proven parts not yet machine-checked, each with its kind: the DX100 reduction lemma as
      "reduction" (12 item 2); the composition theorem and a lifting lemma as "written proof" (26
      item 4). The output lists each entry with its kind, reference (ID and hash) and plain
      sentence.
- [x] **Verifiers and solvers are entries (S14).** Every assumption set the output lists holds each
      verifier and solver the counting records used as a trusted-tool entry. Control: a fixture proof
      record whose assumption set omits its verifier fails `swdb validate`, naming the tool.
- [x] **Proven requires certified (O1).** Code that applies no rewrite contract, with a counting
      direct-route proof record proven unbounded, reads what certification gives (uncertified). The
      output shows the proof beside it as "direct proof, no matching contract: <verdict>". Controls: a
      proven record for a candidate artifact certified only at another content hash gives no proven
      level (09 item 7); a candidate artifact that applies a contract, certified at the same content
      hash, with the same proven record reads proven unbounded.
- [x] **Below minimum bounds.** A bounded record with failure class "below minimum bounds", or whose
      bounds fall below its pinned minimum bounds in any dimension, gives no proven level. The
      candidate artifact stays certified, and the output says "bounded check below minimum".
      Control: the same record at exactly the minimum reads proven within bounds at its sub-rung.
- [x] **Skips (O7).** A skip sets no level and blocks none; it skips only the steps that need the
      missing piece. Fixture: a proof unit with a "no contract proof" skip record (11) and a counting
      route-1 WP record proven unbounded reads proven unbounded. Control: the skip record alone
      leaves the proof unit certified.
- [x] **Replay-label field (owned here).** The proof-record schema has an optional replay-label
      field on refuted records, with O6's four values: "reproduced", "proof semantics only", "not
      reproduced" and "undefined behavior (no strict-layer replay)". `swdb validate` accepts a
      refuted record with no label and one with each value. Negative controls: any other value; a
      label on a record that is not refuted (assumption; see Notes). `swdb build` loads the label,
      when present, with the record. This ticket defines and checks the field only: 60 fills it and
      makes it required on refuted records.
- [x] **Refuted.** A counting refuted record for the candidate artifact's content hash blocks every
      proven level for that hash. It sets a refuted flag, with the refuting record IDs and the replay
      label from the field above. Fixture: one refuted record per label, each setting the flag, and
      one with no label, which sets it too (assumption; see Notes). The flag tells selection the
      candidate artifact leaves it whatever its level. A refutation with the undefined-behavior
      label counts like any other (O6). Control: when the refuted record stops counting (a new
      proof-semantics version lands, 13 item 10), the flag clears.
- [x] **Bug.** A refuted candidate artifact reads "unit-level refutation". It reads "bug" only while
      a counting proof record with subject `kernel_reproduction` (name decided in map 26) cites that
      refutation. 60 builds that record; fixture records stand in here. Controls: a reproduction
      that cites a different refutation, or one that stopped counting, gives no "bug"; a refutation
      with the undefined-behavior label and no reproduction reads "unit-level refutation" (O6).
- [x] **Snapshots and the rule version.** The output names the level-rule version. A snapshot form
      (level, date and time ET, level-rule version, counting proof record IDs) is available for
      campaign summaries, handoffs and promotion reviews to store. Proof records do not pin the level
      rule (26 item 9): no proof record holds a level-rule field, and `swdb validate` refuses one
      that does.

## Notes

- **Not in this ticket:** 04 — Proof record tracer (the `proof` kind (name decided in map 26), its
  tables, `swdb prove` with a scripted adapter, the code and contract pins on read, "proven requires
  certified" for the tracer's one record). 11 — Method-version file and failure classes (the file
  the method-version pin names; the failure-class list that holds "below minimum bounds"; the skip
  reasons). 12 — Proposal and promotion fields (the promotion review that stores a snapshot). 14 —
  Bounded gate in the campaign. 15 — Two winners (selection reads the level and the refuted flag;
  campaign-summary snapshots). 16 — Post-campaign WP phase and budgets (the summary rewrite after
  WP). 17 — Iteration ladder (rows show the level known so far). 18 — ArchEvolve mode level and
  handoff block (the plain-words `certification_level` block (name decided in map 26) and its
  sentence templates). 33 — Minimum-bounds script and A2 exit (real minimum bounds). 60 —
  Strict-layer replay and whole-kernel reproduction (fills the replay-label field this ticket
  defines and makes it required on refuted records; the `kernel_reproduction` record that "bug"
  reads). 62 — Route choice and predecessor proofs in the campaign (the route-3 records and
  predecessor pins this rule reads).
- **Owner of the replay-label field:** this ticket, and no other. A new label value is added here
  first. 60 fills the field and makes it required on refuted records.
- **"Current" hash:** the version now in the library. When proof semantics v2 lands, records that
  pin v1 stop counting and the candidate artifact reads certified, while old snapshots keep the old
  level, dated (26 item 2's example).
- **Where the rule lives:** outside the method version (26 item 9). A rule change recomputes levels
  and never voids a proof.
- Assumption (not decided in the map): a candidate artifact's proof units are one per rewrite
  contract it applies, read from its counting certification records. A proof unit with no counting
  proof record reads certified, so the candidate artifact reads certified.
- Decided (S11): within one proof unit, the highest counting record sets that unit's level, by any
  route (any valid proof counts; a proof for every bound covers each bound, S6). Across proof units
  and dependencies, the weakest wins. Order: cap each record, take the highest per proof unit, then
  the weakest across proof units.
- Assumption (not decided in the map): the contract-proof parts a per-candidate proof record depends
  on are the counting contract-proof records for the contract hash that record pins. With no
  contract proof (O7's skip), no contract-proof part caps the record; an unproven dependency is an
  assumption entry and never caps (design "Cap rule").
- Assumption (not decided in the map): `swdb validate` enforces S14 on each proof record; the level
  rule adds no entry on read.
- Assumption (not decided in the map): "refuted" is a flag beside the level, not a sixth level. The
  candidate artifact keeps the level its test record gives. The iteration ladder (17) shows
  "refuted" in its level column by reading this flag.
- Assumption (not decided in the map): the replay-label field's name. A label on a record that is
  not refuted fails validation. Until 60 makes the field required, a refuted record with no label
  still sets the refuted flag, and the output shows the label as absent.
- Decided: a semantics control with the wrong verdict voids that proof-semantics version (12 item 9);
  a concurrency control with the wrong verdict, or a CIVL–GenMC contradiction, voids the method
  version (15 items 9, 12). Assumption (not decided in the map): the level rule reads the failed
  method-part record on read and stops counting every record that pins the voided version, the
  same way a void contract proof works; a CIVL–GenMC contradiction is written as a failed
  method-part record.
- Assumption (not decided in the map): the output's field names. The existing fields keep their
  meaning.
- Generality: nothing here is BFS- or DX100-specific (26 item 12).
- Tests use fixture records with `contract_fixture` evidence, built with the existing record-closure
  helper (LR-03); no verifier runs. Prior art: the candidate-level tests in the Extensa boundary
  tests. Full-suite runs on the Mac use at most 2 test workers.

## Answer

2026-10-14 02:24 ET. Built test-first; every acceptance box is met. Branch `probata-poc/t10`.

**What exists now** (interface: [`format-v0.4-level-rule.md`](../../../docs/reference/format-v0.4-level-rule.md)):

- **`swdb.level_rule`** (`VERSION = "level-rule.1"`): `Rule(store)` reads every proof record once;
  `Rule.status(id)` says whether a record counts, why not (each pin, `dependency`, `failed`), its
  bounds after caps and the caps; `candidate_level(store, id)` is `swdb candidate-level`'s answer;
  `snapshot(level, records)` is the dated form. `swdb/extensa_boundary.level_cli` calls it. The tracer
  rule (`swdb.proof.proven_level`, `counts`, `bounded_level`, `unit_records`) is removed.
- **Level names:** `proven_unbounded`, `proven_within_bounds_threads_k`, `proven_within_bounds_threads_1`,
  `certified`, `uncertified` (`rejected` as before), with `rank` 4..0. Ticket 04's tests now read the
  sub-rung name.
- **Output fields** (existing ones keep their meaning): `rank`, `level_rule`, `proven`, `proof_units`,
  `assumptions`, `stale_proofs`, `below_minimum`, `direct_proofs`, `skipped`, `refuted`, `snapshot`.
- **Proof-record schema:** `replay_label` (refuted only, optional; `reproduced`, `proof_semantics_only`,
  `not_reproduced`, `undefined_behavior`); `tools` (S14; `swdb validate` names a tool with no
  trusted-tool entry; `Verdict.tools`, scripted script key `tools`); `level` and `level_rule` are refused
  with a reason. `swdb_proofs.replay_label` column (`docs/reference/database.md`).

**Tests:** `tests/test_level_rule.py` (85 tests, seam 2 and seam 4, fixture records with
`contract_fixture` evidence on ticket 04's seed). Also green: `test_proof_records.py`,
`test_proof_method_version.py`, `test_extensa_boundary.py`, `test_validate_rules.py`,
`test_crosswalk.py`, `test_format_doc.py`, `test_db.py`. Serial, no xdist, no verifier ran (nothing
through `verifier_run.py`). Test scratch only: `/tmp/claude/probata-runs/t10/pytest/`.

**Assumptions** (the map leaves these open), besides the ticket's own Notes:

- Assumption: level value names and `rank` above. A record whose threads are `unbounded` but some data
  dimension is bounded reads threads ≤ k (the highest within-bounds sub-rung).
- Assumption: a `not_applicable` pin always matches (the record states the kind does not apply).
- Assumption: where the "current" hash lives for kinds whose owning ticket is not built: reference
  semantics = a library entry's content sha256 (30); proof semantics = a version file
  `library/proof_semantics/<name>.yaml` with `id`, `target`, `sequence`, current = highest `sequence`
  per `target` (27 writes the real files and their schema); minimum bounds = a
  `minimum_bounds_derivation` contract-proof part record named by ID, pinned by its content digest
  (`swdb.artifacts.digest`), whose `bounds` are the minimum (33); predecessor snapshot = the
  predecessor candidate artifact's tree sha256 (62); build constants = the value each dependency record
  pins for the same name (no global "current" constant exists).
- Assumption: the minimum-bounds derivation caps only the records that pin it, not every record of the
  contract. Otherwise its bounded level would cap every route-1 WP proof of that contract at proven
  within bounds, which contradicts the design (route-1 WP reaches proven unbounded).
- Assumption: contract-proof parts are grouped by `subject.part`; within a part the highest counting
  record counts; a part whose records all stopped counting stops its dependents (10 item 6); a part
  with only unproven counting records does not cap.
- Assumption: a failed part is a `refuted` record whose counterexample names the control and the verdict
  it got. Part names: `semantics_controls` (voids its proof-semantics pin), `concurrency_controls` and
  `civl_genmc_agreement` (void its method-version pin), `negative_controls` on a contract-proof part
  (voids its contract pin). A failed record voids only while its own pins match.
- Assumption: below minimum: a dimension of the minimum that the record does not bound counts as below.
- Assumption: a `kernel_reproduction` record cites its refutation in `subject.id` and earns "bug" only
  with verdict `refuted` (it reproduced) while it counts. 60 may refine the outcome encoding.
- Assumption: the assumption set listed is that of the records that set the level and of the proven
  parts they depend on (summaries, contract-proof parts, minimum-bounds derivation, predecessor's records).
- Assumption: `tools` stays optional until the real adapters (21, 22) write it; a record that omits
  `tools` is not checked for S14.

**Side findings** (for the main session; nothing changed outside this ticket's scope):

- Design gap: decision 10 item 5 makes every contract-proof part cap, and 33 makes the minimum-bounds
  derivation a contract-proof part whose bounds are bounded by nature. Read literally, no proof of a
  contract with a minimum-bounds record could read proven unbounded. Handled by the assumption above
  (it caps only what pins it); Yan-Ru may want to confirm.
- The part names (`semantics_controls`, `concurrency_controls`, `civl_genmc_agreement`,
  `negative_controls`, `minimum_bounds_derivation`, `unit_postcondition`, `lifting_lemma`) are free
  text in the schema; 29, 32, 33 and 48 must write exactly these, or a vocabulary should pin them.
