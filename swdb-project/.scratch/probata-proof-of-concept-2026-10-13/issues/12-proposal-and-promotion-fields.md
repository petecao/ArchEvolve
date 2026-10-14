# 12 — Proposal and promotion fields

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 10
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Loop, modes and guards", row "Proposals"; "Records and levels" (promotion review; where things live); "Refutation, repair and bugs"; "Evaluation design" (protocol: run index, pinned provider); "Providers and machines"; "Testing Decisions", seams 2 and 4; user stories 60, 62, 71; S10; O9); decisions: [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (items 3, 5, 6, 7), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 5, 6, 11)
**Time estimate:** about 1 day

**What to build:** Three record additions, so that repairs, repeated runs and approvals can be
audited later. Proposals carry repair lineage (the refuted candidate artifact, the proof record
that holds the counterexample, the round, the reverted-repair flag) and run fields (run index 1-3,
provider pin). Proof records carry the same run fields, because a proof-hint run has no proposal
(S10), and a job block (adapter, host, worker core, wall time, CPU time, batch load, peak RSS,
batch ID, position in the batch). This ticket is the one owner of the job-block field list. A
candidate artifact's promotion review cites its proof record IDs and the level snapshot at
promotion. When a pin later changes, `swdb candidate-level`
shows the current level beside the snapshot Yan-Ru approved, so the drop is visible against what
was approved.

## Acceptance

- [ ] **Repair lineage validates.** `swdb validate` accepts a proposal with repair lineage: the
      refuted candidate artifact, the ID of the proof record that holds the counterexample, the
      round (a positive integer) and the reverted-repair flag. It rejects, one at a time: a proof
      record that does not exist; one that is not a refutation with an inline counterexample; one
      whose subject is not the named refuted candidate artifact; a missing flag; round 0.
- [ ] **Run fields validate.** A proposal accepts run index 1, 2 or 3 and a provider pin (provider
      kind, model, effort; for example Codex, `gpt-5.6-sol`, `xhigh`). Run index 0 or 4, and a pin
      without its model or effort, fail validation.
- [ ] **Run fields on proof records (S10).** A proof record accepts the same run index and provider
      pin under the same rules. A proof-hint run, which has no proposal, carries both on its proof
      record. Controls: a proof record with run index 4, or a pin without its effort, fails
      validation.
- [ ] **Job block, one field list.** Every proof record `swdb prove` writes has a job block with
      adapter, host (`mac` on the Mac), worker core, wall time, CPU time, batch load, peak RSS,
      batch ID and position in the batch, each measured or read from the run (scripted adapter in
      tests). Peak RSS is what the 8 GB RSS
      watchdog per worker reads (O9). Validation rejects a record with a field missing, a negative
      time or a negative peak RSS. This list is
      the only one: 04 writes the block and 57 fills it on mbit10, and neither adds a field.
- [ ] **Build.** `swdb build` loads the new proposal and proof-record fields into SWDB extension
      tables, so the evaluation's paired statistics can query them. No new field appears in a LANL
      core table.
- [ ] **Promotion pins the level.** A new promotion review of a candidate artifact carries the proof
      record IDs that count at promotion and the level snapshot from 10 (level, date and time ET,
      level-rule version). The existing promotion command, `swdb promote`, fills both from the level
      rule. `swdb validate` rejects such a review whose snapshot has no level-rule version, or that
      cites a proof record about another candidate artifact.
- [ ] **A later drop shows.** Promote a fixture candidate artifact at proven within bounds,
      threads = 1. Then land a new proof-semantics version, so its proof records now pin an old one.
      `swdb candidate-level` reads certified and shows the promotion snapshot beside it (proven within
      bounds, threads = 1, its date, its level-rule version).
- [ ] **Records never change.** Running `swdb candidate-level`, `swdb build` or a promotion leaves
      every proof record and proposal byte-identical.
- [ ] **Old records stay valid.** Proposals and reviews of candidate artifacts written before this
      ticket, without the new fields, still pass `swdb validate` and `swdb build`. So does any proof
      record written before this ticket lands, by 04 or any other ticket, without run fields or any
      other field this ticket adds.

## Notes

- **Not in this ticket:** 10 — Level rule (computes the snapshot). 13 — Counterexample-guided repair
  (writes the repair lineage and runs the deterministic contract-match check that sets the
  reverted-repair flag). 15 — Two winners (campaign-summary winners with dated snapshots). 16 —
  Post-campaign WP phase and budgets (the `budgets.used` lines (name decided in map 26) for proof
  lane-hours, proof-hint calls and repair calls). 17 — Iteration ladder (`repair_of` (name decided
  in map 28) on ladder rows). 18 — ArchEvolve mode level
  and handoff block (the handoff's snapshot). 37 — The proof-hint loop (writes the run fields on
  its proof records). 57 — Proof workers in a socket lane (pinned cores and the 8 GB RSS watchdog
  per worker on mbit10, O9).
- **Owner of the job-block field list:** this ticket, and no other. 04 writes the block and 57
  fills it on mbit10; a new field is added here first. This ticket owns what each field means and
  how it is checked: measured from the run, validated, and loaded for the evaluation. What 04
  already does is kept and tested here as a regression.
- Assumption (not decided in the map): map 26 item 6 lists worker core, wall time, CPU time and
  batch load; peak RSS follows O9. The list also holds the adapter name, so a scripted record shows as
  such; the host, so Mac and mbit10 numbers never mix; and the batch ID and position in the batch.
  04 writes every field; 57 fills them on mbit10 and checks interleaving from the last two.
- Assumption (not decided in the map): peak RSS is the largest resident set size of the job's
  whole process tree (solver and JVM children included), the same measure the watchdog uses.
- Assumption (not decided in the map): on a proof record, the run fields are present when a
  provider call took part (proof hinting) or the job belongs to a repeated run; a bounded job with
  no provider call carries none.
- Assumption (not decided in the map): the drop shows in `swdb candidate-level`, which prints the
  promotion snapshot beside the current level. 26 item 11 says only that a later drop shows against
  what was approved.
- Assumption (not decided in the map): the new fields are optional on records written before this
  ticket. On new records: repair lineage is required on every proposal that counterexample-guided
  repair makes; the job block on every proof record; the snapshot on every promotion review of a
  candidate artifact (an empty proof record list is allowed for a candidate artifact with no
  proof).
- Assumption (not decided in the map): run index is optional. Absent means the proposal or proof
  record is not part of a repeated LLM configuration (23 item 5 repeats only those).
- Assumption (not decided in the map): macOS cannot pin a job to a core, so on the Mac worker core
  reads "unpinned". mbit10 records the pinned core (57).
- Assumption (not decided in the map): batch load is the host's 1-minute load average, sampled when
  the job starts and when it ends.
- Assumption (not decided in the map): the round cap (5) is not a schema rule. The repair loop (13)
  enforces it from the method version's budgets, so the schema checks only that a round is positive.
- Proof time is a cost metric, never a speed claim (23 item 6). Mac results carry host `mac` and are
  never mixed with mbit10 numbers.
- Tests use fixture records with `contract_fixture` evidence and the scripted adapter; no verifier
  runs. Full-suite runs on the Mac use at most 2 test workers.
