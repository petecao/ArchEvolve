# 42 — Rocq: composition theorem proof

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 10, 11, 12, 41
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (composition theorem: 2-week box, written fallback), "Records and levels" (subjects), "What a proven verdict asserts" (assumption set, cap rule), "Modules" (level rule: level computed on read), "Further Notes" (risk: the Rocq theorem does not fit 2 weeks), "Proof-of-concept plan" (Rocq side track, overrun rule), S1, S2, S8, S9); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** one 2-week box, shared with 43 (S9)

**What to build:** Codex proves the composition theorem Yan-Ru approved in ticket 41, and Rocq checks
every step. One 2-week box covers this proof and then 43's reduction lemma, in that order (S9). The proof
command runs the Rocq check and writes a method-part proof record; 43 reuses this job and its
negative controls. If the box runs out, the fallback is a written proof: agent-written, reviewed adversarially by
Codex, approved by Yan-Ru at promotion. It keeps every lemma Rocq did check, and the theorem enters
assumption sets as an entry of kind written proof. Either way there is one method-part proof record,
and `swdb candidate-level` reads it correctly: a Rocq-checked theorem leaves the assumption set; a
written one stays listed and does not cap the level.

## Acceptance

- [ ] **One box for 42 and 43 (S9).** The box starts after Yan-Ru approves 41's statement. This ticket
      runs first, then 43. Its start date is recorded here and in 43. At 2 weeks of work, whatever is unchecked in either ticket
      switches to its fallback, with no extension. The time spent on each is recorded.
- [ ] The proof is of the approved text: the statement and definitions match, by content hash, those
      approved in ticket 41. A copy with one hypothesis changed is refused before any record is
      written.
- [ ] Rocq path: `swdb prove` on the composition theorem writes one method-part proof record, status
      Rocq-checked, pinning the method version, the development's content hash and the Rocq version.
      `swdb validate` and `swdb build` accept it.
- [ ] Rocq's own assumption listing for the theorem shows only its named hypotheses: no axiom, no
      admitted step. Negative controls: a copy with one admitted step, and a copy with one added
      axiom, each make `swdb prove` write no Rocq-checked record.
- [ ] Fallback path: the written proof cites every Rocq-checked lemma by name, and those lemmas still
      check. Codex's adversarial review is recorded, each finding answered. The method-part proof
      record has status written and enters assumption sets as kind written proof, with one plain
      sentence.
- [ ] `swdb candidate-level` drops the composition theorem's assumption entry on read once the
      Rocq-checked record counts (moved here from 45). Test on a fixture candidate artifact whose
      per-thread proof record comes from the scripted adapter and lists the theorem as kind written
      proof, as 45's records do: with the Rocq-checked record, its assumption set has no
      composition-theorem entry; with the written record, the entry is listed and the level is not
      capped (cap rule). Both are computed on read: the per-thread proof record is never rewritten
      (26 item 1).
- [ ] The outcome (Rocq-checked, or written with the steps left unchecked) and the record ID are in
      this ticket's Answer, for the A4 exit in ticket 49.
- [ ] Mac: Rocq runs one job at a time under the ~8 GB RSS watchdog. The record's job block holds the
      fields of ticket 12's list, peak RSS included.

## Notes

- **Not in this ticket:** 41 — Rocq: composition theorem statement and definitions; 43 — Rocq:
  DX100 reduction lemma (same box, after this ticket); 44 — Shared-action kinds and commutativity lemmas; 45 — Per-thread
  lowering (writes the per-thread records that list the theorem); 49 — Peter's race repaired; A4 exit
  (reads this outcome); 59 — Method-version review and freeze.
- Blockers: 10 — Level rule (the `swdb candidate-level` reading tested here), 11 — Method-version
  file and failure classes (the record pins the method version, which lists the Rocq development, S8)
  and 12 — Proposal and promotion fields (the job-block field list).
- Assumption (not decided in the map): how the box splits. About 1 week each, 43's earlier estimate;
  this ticket first, then 43 (43 is blocked by it). Time this ticket leaves unused goes to 43.
- Latest decision wins: 15 item 8 called the unchecked theorem an entry of kind "reduction"; 26 item 4
  later made it kind written proof.
- Rocq itself is a trusted-tool entry, like every verifier
  ([09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) item 8).
- Assumption (not decided in the map): the verifier adapter roles are bounded and unbounded, and Rocq
  fills neither. Under S1 ("one command runs every proof job"), `swdb prove` gets a Rocq check job for
  method-part subjects. 43 reuses it.
- Assumption (not decided in the map): "Yan-Ru approval at promotion" of a written fallback happens at
  the method-version review (ticket 59). This ticket ends when the written proof and Codex's review
  are recorded, which is what A4's exit calls "the written fallback done".
- Risk (design spec, "Further Notes"): the theorem does not fit 2 weeks. Fallback as above; candidate
  artifacts can still reach proven unbounded, with the written proof in their assumption sets.
- Provider: Codex, pin `gpt-5.6-sol`, effort `xhigh`. The proof needs no human step.
- Assumption (not decided in the map): the shared 2-week box clock starts when both 42 and 43 are unblocked apart from each other (41 approved and 29 resolved); 42 runs first inside it, then 43.
