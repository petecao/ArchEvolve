# 04 — Proof record tracer

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Records and levels"; "Records and levels" section; "What a proven verdict asserts" (bounds, assumption set); "Testing Decisions", seams 1, 2 and 4; "Choices made while writing this spec", S1 and S2); decisions: [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 1, 2, 4, 5, 6), [ADR 0016](../../../docs/adr/0016-proof-records-never-change-level-computed-on-read.md)
**Time estimate:** about 1-2 days

**What to build:** The narrowest complete path through proof records. `swdb prove` (proposed name,
S1) runs one proof job on one candidate artifact's proof unit through a scripted verifier adapter.
It writes one `proof` record (name decided in map 26) that never changes: subject, content-hash set
pins, bounds, assumption set and a minimal job block. The schema also gets an optional route field
for a candidate proof unit (route 1, route 3 or bounded direct); this ticket owns it, and later
tickets fill it. `swdb validate` checks the record. `swdb build` indexes it into `swdb_proof*`
tables (names decided in map 26) in the SWDB extension, never the LANL core. `swdb candidate-level` (extended, S2) reads it into a proven level for a
certified candidate artifact, computed on read and never stored. The scripted adapter uses the
interface the real tools will use: in, a proof unit plus summaries; out, proven, refuted with a
counterexample, or not proven with a failure class. Later tickets widen each layer.

## Acceptance

- [ ] **Write.** `swdb prove`, with the scripted adapter set to "proven" on a certified fixture
      candidate artifact's proof unit, writes exactly one `proof` record in `records/proofs/`
      (name decided in map 26). It holds: the subject (a candidate artifact's proof unit: the
      candidate artifact's ID and the function that holds the rewrite site); the content-hash set,
      one pin per kind map 26 lists (code proven, contract, baseline function, reference
      semantics, proof-semantics version, method version, each summary used with its proof record
      ID, minimum-bounds version, predecessor snapshot, every build constant); bounds, one value
      or "unbounded" per dimension, thread count always present; the assumption set, each entry
      with kind, reference (ID and hash) and one plain sentence; a minimal job block with exactly
      the fields on 12's list: adapter, host (`mac` on the Mac), worker core, wall time, CPU time,
      batch load, peak RSS, batch ID and position in the batch; and `contract_fixture` evidence. It
      has no route (optional; see below).
- [ ] **Other verdicts.** Scripted "refuted" writes the counterexample inline in the record.
      Scripted "not proven" writes its failure class. Each job writes one record.
- [ ] **Never changes.** Running `swdb prove` again on the same subject writes a second record with
      a new ID. The first record's file is byte-identical afterward.
- [ ] **Validate.** `swdb validate` accepts every record above and refuses each negative control: no
      thread-count bound; an assumption entry whose kind is not one of the seven, or that has no
      sentence; a missing pin kind; a refuted record without a counterexample; a not-proven record
      without a failure class.
- [ ] **Route field.** The schema has an optional route field on candidate proof-unit records, with
      three values: route 1, route 3 and bounded direct. `swdb validate` accepts a fixture record with
      no route and one with each value. Negative controls: any other value; a route on a record
      whose subject is not a candidate proof unit (assumption; see Notes). `swdb build` loads the
      route, when present, with the record. This ticket defines and checks the field only: 61 fills
      bounded direct; 62 fills route 1 and route 3 and makes the field required on candidate
      proof-unit records.
- [ ] **Build.** `swdb build` writes `swdb_proofs` (name decided in map 26) plus child tables for
      pins, assumptions and bounds, with row counts matching the records. Every LANL core table is
      identical before and after. Rebuilding from the YAML alone gives the same tables.
- [ ] **Level.** `swdb candidate-level` on the certified candidate artifact with the "proven" record
      at threads = 1 returns proven within bounds, lists the bounds and names the record ID. With
      every dimension "unbounded", thread count included, it returns proven unbounded. Nothing writes
      a level to the candidate artifact or the proof record.
- [ ] **Level, negative controls.** The proven record gives no proven level when the candidate
      artifact is uncertified or rejected (proven requires certified), when its code pin does not
      match the candidate artifact's tree hash, or when its contract pin does not match the
      contract's current content hash (the record stops counting). A refuted or not-proven record
      gives no proven level either. In each case the level is what certification gives.
- [ ] **Evidence.** The adapter's log sits in a runs folder outside the repo, and the record names it
      by path and sha256. The record names no verifier scratch, and the job's scratch folder is gone
      when the job ends.
- [ ] Tests call only public commands (`swdb prove`, `swdb validate`, `swdb build`,
      `swdb candidate-level`), build fixtures with the existing record-closure helper (LR-03), use no
      real verifier and run with at most 2 test workers.

## Notes

- **Not in this ticket:** 10 — Level rule (the versioned rule; weakest-of across proof units; the cap
  rule; assumption entries never cap; every other pin kind stopping a record from counting; the two
  sub-rungs; refuted leaves selection; dated snapshots naming the rule version; "bug" only with a
  reproduction). 11 — Method-version file and failure classes (the failure-class vocabulary; an
  unclassified failure stops the batch). 12 — Proposal and promotion fields (the single owner of
  the job-block field list: what each field means, how it is measured and how it is validated; this
  ticket only writes a minimal block and does not validate it). 18 — ArchEvolve mode level and
  handoff block. 19 — Derived implementations (reads the route field for its per-rewrite links).
  21 — C lowering and WP adapter (A2 tracer) and 22 — SAW adapter and SAWScript translator (the real
  adapters). 57 — Proof workers in a socket lane. 61 — SAW whole-function equivalence (bounded
  direct route) (fills route bounded direct). 62 — Route choice and predecessor proofs in the
  campaign (fills route 1 and route 3; makes the field required on candidate proof-unit records).
- **Owner of the route field:** this ticket, and no other. A new route value is added here first.
  Map 26 item 1 records a proof route per rewrite in a rewrite chain (17); the route names come from
  the map spec's "Proof routes" table (17 as revised by 24).
- The record pieces precede any proof stage whose results must count (map 26; map 27 item 4), and
  they are never cut. The scripted adapter is the stub the Extensa track codes against; its records are
  `contract_fixture` evidence, never evidence about real code.
- Assumption (not decided in the map): `swdb prove`'s arguments (subject, adapter choice, the
  scripted adapter's script file, runs folder). Keep them minimal; ticket 21 adds the real adapter.
- Assumption (not decided in the map): the job block also names the adapter, so a scripted record is
  visible as such; the host; and the batch ID and position in the batch (map 26 item 6 lists only
  worker core, wall time, CPU time and batch load; peak RSS follows O9). Ticket 12 owns the field
  list and lists them all; this ticket uses the same field names.
- Assumption (not decided in the map): the field's name and how its three values are spelled; the
  map names the routes but no field. Other subject kinds carry no route, so validation refuses one
  there.
- Assumption (not decided in the map): a pin that does not apply yet (no method-version file before
  ticket 11; no proof semantics for a subject without accelerator calls; no predecessor) is written
  explicitly as not applicable, never left out, so validation can require every pin kind.
- Assumption (not decided in the map): on read, the tracer checks only the code pin (the candidate
  artifact's tree hash) and the contract pin (content hash, as certifications already work).
  Ticket 10 adds the rest.
- Assumption (not decided in the map): the schema lists the five subject kinds from map 26 item 1
  (candidate proof unit, library entry's summary, contract-proof part, method part, whole-kernel
  reproduction) plus a sixth, calibration program, for the public-suite calibration runs of 38 —
  Calibration on the public C suites. Reference-definition proofs (30 — Reference definitions,
  per-call summaries and new intrinsic versions) use the library entry's summary subject. Only
  the candidate proof unit is exercised here.
- Assumption (not decided in the map): the failure class is checked only for presence here; ticket
  11 adds the vocabulary it must come from.
- Assumption (not decided in the map): the field names in `swdb candidate-level`'s output for the
  proven level, its bounds and the counted proof record IDs. The existing output keeps its fields.
