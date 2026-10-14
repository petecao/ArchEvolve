# 60 — Strict-layer replay and whole-kernel reproduction

Created: 2026-10-13 23:15 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 22, 29
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Refutation, repair and bugs" (evidence steps); "DX100 proof semantics" (agreement with the strict layer, the "stricter than the strict layer" list); "Concurrency" (memory model); "Records and levels" (subjects, where things live); "Verifier lineup and order" (failure classes); "Out of Scope" (gem5 runs); "Testing Decisions", seams 1 and 2; user stories 24, 25, 26; S1, S2; O6); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 10; [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 1, 5, 8; [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) items 1, 4, 8
**Time estimate:** about 4 days

**What to build:** Every refutation says how far its evidence reaches. When the bounded verifier
refutes a proof unit, the same `swdb prove` job replays the counterexample on the strict layer, under
the newest certify version that models the failing rule (51's version once it exists), whatever the
certification default, and gives the refutation exactly one label, in the replay-label field that
10 defines (optional there; this ticket makes it required on refuted records):

- **reproduced:** the strict layer flags the same violation;
- **proof semantics only:** the refutation rests on a rule the strict layer does not model yet (29's
  "stricter than the strict layer" list); the label cites that rule's gem5 source;
- **not reproduced:** the strict layer models the rule but does not flag the run, so the proof setup
  disagrees with testing; the batch stops until the cause is found;
- **undefined behavior (no strict-layer replay)** (O6): a data race or other undefined behavior,
  which no strict-layer rule covers; it counts as a refutation, and the batch goes on.

Unit refutation plus replay is one job, so one proof record (26 item 8). "Bug" is a separate step: a
whole-kernel reproduction job runs the whole kernel on a real input, plus a schedule for a race, and
writes its own proof record, subject `kernel_reproduction` (name decided in map 26), citing the
refutation. `swdb candidate-level` (10) reads "bug" while that record counts, else "unit-level
refutation".

## Acceptance

- [ ] **One record per refutation.** A refuting `swdb prove` job writes exactly one proof record. It
  holds the counterexample inline, the replay label in 10's replay-label field and the certify
  version it replayed against (the newest that models the failing rule, never just the
  certification default). No separate replay record exists.
- [ ] **Label required.** This ticket makes 10's replay-label field required on refuted records and
  adds no value to it. `swdb validate` refuses a refuted record with no replay label (negative
  control); existing refuted fixtures gain a label in this ticket.
- [ ] **Reproduced, hazard.** A fixture unit with a planted read before its covering wait (a rule both
  models) is refuted by the bounded verifier (22, with 27's proof semantics). The replay runs the
  unit's C++ under the strict layer on the counterexample's inputs and build constants. The strict
  layer flags the read: label reproduced.
- [ ] **Reproduced, value.** A fixture unit that breaks its unit postcondition, with no hazard, is
  refuted. The replay runs the check-mode form of the violated clause (23) on the counterexample, and
  the check fails: label reproduced.
- [ ] **Proof semantics only.** A fixture refutation that rests on a same-thread footprint overlap (on
  the "stricter" list until 51) is labeled proof semantics only. The record names the rule and its
  gem5 citation, read from the proof-semantics rule itself. Negative control: with a planted
  "stricter" list that leaves the rule out, the same replay is labeled not reproduced, and the batch
  stops.
- [ ] **Not reproduced stops the batch.** A planted setup fault (a hand-weakened summary that lets the
  bounded verifier refute a correct fixture unit) gives a counterexample the strict layer runs
  cleanly. The record is written with label not reproduced, no later job in the batch starts, and the
  stop names the record.
- [ ] **Undefined behavior (O6).** A scripted race refutation (a plain store to a shared-action
  location, with a two-thread trace as counterexample) and a scripted signed-overflow refutation are
  each labeled "undefined behavior (no strict-layer replay)". No strict-layer run happens, and the
  batch goes on. `swdb candidate-level` reads each candidate artifact as refuted, so it leaves
  selection. Control: a hazard refutation never gets this label.
- [ ] **Unmapped kinds stop.** A scripted refutation whose failing property has a kind with no label
  mapping stops the batch, like an unclassified failure.
- [ ] **Whole-kernel reproduction.** Given a refutation record, a real input and, for a race, a
  schedule, `swdb prove` runs the whole fixture kernel under its certify build and writes one proof
  record with subject `kernel_reproduction`. It cites the refutation, names the input and schedule by
  path and sha256, and records the outcome: the kernel fails its correctness check, executes the
  undefined behavior, or does neither. It never runs gem5.
- [ ] **"Bug" on read.** Before a reproduction, `swdb candidate-level` reads the refuted candidate
  artifact as "unit-level refutation"; after a reproduction that failed the check or executed the
  undefined behavior, "bug". The hazard fixture and the race fixture both reach "bug". Controls: a
  reproduction whose kernel run passes gives no "bug"; one that cites a different refutation gives
  none.
- [ ] **Records and Mac rules.** Every record passes `swdb validate` and `swdb build` and carries
  `contract_fixture` evidence. One real verifier job at a time under the ~8 GB RSS watchdog; tests
  that need SAW or LLVM 22 skip cleanly; full-suite runs use at most 2 test workers.

## Notes

- **Not in this ticket:**
  - 51 — Strict-layer catch-up: the memory-timing rule in a new certify version. Refutations that use
    the rule then replay against it, whatever the certification default, as reproduced instead of
    proof semantics only.
  - 46 — CIVL adapter; 47 — GenMC adapter and agreement: real race refutations. 46, 48 —
    Concurrency negative controls and 55 — End-to-end fixture campaign with real verifiers wait on
    this ticket for the undefined-behavior label.
  - 13 — Counterexample-guided repair: the counterexample goes to repair whatever its label.
  - 10 — Level rule (upstream): the replay-label field and its four values, the refuted flag, the
    label it shows and "bug" on read. A new label value is added in 10 first.
  - 58 — Mac verdicts reproduced on mbit10: re-runs these replays there.
  - Evaluation 01, 06 and 09: replays and reproductions for held-out subjects.
- Assumption (not decided in the map): the label follows the failing property's kind as the adapter
  reports it: a hazard probe (with its rule), a formal-half or unit-postcondition assertion, or an
  undefined-behavior check (race, overflow and the like).
- Assumption (not decided in the map): refuted records written before this ticket (for example by
  22) carry no label and still pass `swdb validate`, since records never change (ADR 0016); the
  field is required on records written from this ticket on.
- Assumption (not decided in the map): the replay uses the newest certify version that models the
  failing rule: 51's version once it exists, else 1.7. It names that version in the record. The
  design adds the new version "so refutations that use it can replay" ("Modules"). Whether new
  certify runs default to it is 51's open point and does not change the replay version. A rule no
  version models replays against the newest version, whose "stricter" list holds it: proof semantics
  only.
- Assumption (not decided in the map): a value refutation replays through check mode's runtime form of
  the violated clause. If a clause has no runtime form, raise it with Yan-Ru instead of picking a
  label.
- Assumption (not decided in the map): a "not reproduced" record still blocks a proven level for its
  content hash, since the unit was refuted. The fix (a new summary, harness, lowering or
  proof-semantics version) changes a pin, so the record stops counting. The diagnosed case joins the
  regression corpus (design, "Verifier lineup and order").
- Assumption (not decided in the map): a rule on the "stricter" list with no gem5 citation (assumed,
  with an owner) is labeled proof semantics only and cites its owner instead.
- Assumption (not decided in the map): the reproduction's input and schedule are inputs to the job;
  building them from the unit counterexample is not in this ticket. How the schedule is enforced and
  how "executes the undefined behavior" is observed are open: pick the smallest form the fixture
  tests can check, and name it in the reproduction record.
- Assumption (not decided in the map): a reproduction whose kernel run passes still writes its record
  (one record per proof job); it gives no "bug".
- Assumption (not decided in the map): the reproduction runs the kernel's certify build natively, with
  the strict layer for DX100 code, because proofs never run gem5 (design, "Out of Scope").
- O6 is a default awaiting Yan-Ru. If Yan-Ru rules otherwise, only the label set changes.
- Fixtures use contract-fixture code only; no held-out kernel (BC, PR, SSSP) before 59 —
  Method-version review and freeze. Before a batch of real replays, record its output destination,
  size budget and readers (LR-06); post the 30-minute heartbeat for a run past 30 minutes (LR-07).
- Assumption (not decided in the map): a multi-thread trace (CIVL or GenMC) replays with its interleaving enforced. Where the strict layer cannot follow a schedule, the label is "proof semantics only" with the reason named, never "not reproduced".
