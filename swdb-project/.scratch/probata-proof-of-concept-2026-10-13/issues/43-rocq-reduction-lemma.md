# 43 — Rocq: DX100 reduction lemma

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 29, 41, 42
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("DX100 proof semantics" (values and timing split, reduction lemma, memory footprints, region stall), "Modules" (Rocq development), "Records and levels", "Out of Scope" (hardware vs proof semantics), S4, S8, S9); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 1 week, inside the 2-week Rocq box shared with 42, after 42 (S9)

**What to build:** Codex proves the DX100 reduction lemma whose statement Yan-Ru approved in 41
before the box (S9), in the same Rocq development as the composition theorem, inside the one 2-week
box that covers 42 and 43, in that order. The lemma: if
the code is hazard-free, every timing gem5 allows gives the same values as finish-at-issue. It is what lets value proofs assume each command finished at issue. It
reuses 42's `swdb prove` Rocq job and negative controls (one admitted step, one added axiom). When
Rocq checks it, that job writes a proof record, and the lemma's reduction entry leaves the
assumption sets of the proofs that relied on it. If it is not checked when the box ends, the written
proof and bounded check from ticket 29 stay its evidence, and the entry stays, kind reduction.

## Acceptance

- [ ] **The proof is of the approved text.** The lemma's statement and definitions (12 items 2-5: the
      timing model and the hazard definition, as 41's criteria list them) match, by content hash,
      those Yan-Ru approved in 41. A copy with one side condition changed is refused before any
      record is written.
- [ ] Checked path: Rocq checks the lemma. Its assumption listing shows no axiom and no admitted
      step. Ticket 42's negative controls (one admitted step, one added axiom) are rerun on this
      development and refused.
- [ ] Checked path: `swdb prove` (42's Rocq job) writes one proof record for the lemma, status Rocq-checked, pinning
      the method version, the proof-semantics version, the development's content hash and the Rocq
      version.
      `swdb validate` and `swdb build` accept it.
- [ ] `swdb candidate-level` on a fixture DX100 candidate artifact: without the record, its assumption
      set lists the reduction entry; with it, the entry is gone. The level does not change (an unproven entry
      never capped it). This is computed on read: no earlier proof record is rewritten (26 item 1).
- [ ] A new proof-semantics version makes the record stop counting. The reduction entry then returns
      for candidate artifacts that pin the new version, until the lemma is checked again.
- [ ] Box: one box with 42 (S9), 42 first, then this lemma. The start date is 42's; the time spent on
      this lemma is recorded.
- [ ] Not checked when the shared box ends: no Rocq-checked record is written; ticket 29's written
      proof and bounded check stay the lemma's evidence; the unchecked entry keeps kind reduction and
      its sentence. The outcome (checked, or not checked with the reason) is in this ticket's Answer.

## Notes

- **Not in this ticket:** 29 — Proof-semantics checks (the written proof, the bounded check on an
  asynchronous port, the semantics negative controls, strict-layer agreement); 27 — Proof semantics
  for the BFS read-offload calls and 28 — Proof semantics for the remaining maa_* calls (the rules
  modeled here); 41 — Rocq: composition theorem statement and definitions (shared definitions, and
  this lemma's statement and definitions, reviewed there);
  42 — Rocq: composition theorem proof (same box, runs first; records its start; builds the
  `swdb prove` Rocq job and the negative controls reused here); 51 — Strict-layer catch-up.
- The unchecked lemma's entry keeps kind reduction (12 item 2). 26 item 4's kind "written proof"
  covers 09 item 6 and 15 item 8, not this lemma.
- The box: one 2-week box covers 42 and 43, in that order (S9; this ticket is blocked by 42). How the
  time splits is 42's assumption (about 1 week each; time 42 leaves unused goes to this lemma). It
  ends before the freeze (ticket 59 waits for it).
- Assumption (not decided in the map): the record's subject and pins. 26 item 1's subject list does not
  name this lemma. It is recorded as a method part that pins both the method version (which lists the
  Rocq development, S8) and the proof-semantics version (its side conditions are proof-semantics
  rules).
- Assumption (not decided in the map): rule coverage. The lemma covers every rule of the
  proof-semantics version it pins, the 8-byte tile-pair rule
  ([16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 11) included. If it
  covers less, its statement names the rules left out, and the reduction entry stays for proofs that
  use them.
- Review: the lemma's statement and definitions are reviewed in 41, with the composition theorem's,
  before the shared box (S9). Yan-Ru never reviews the proof (15 item 8).
- A checked lemma never claims that DX100 hardware matches its proof semantics (out of scope).
- Provider: Codex, pin `gpt-5.6-sol`, effort `xhigh`. Mac: one Rocq job at a time under the ~8 GB RSS
  watchdog.
- Assumption (not decided in the map): the shared 2-week box clock starts when both 42 and 43 are unblocked apart from each other (41 approved and 29 resolved); 42 runs first inside it, then 43.
