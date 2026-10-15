# 42 — Rocq: composition theorem proof

Created: 2026-10-13 22:17 ET
Updated: 2026-10-15 01:41 ET (ticket 41 repaired and approved under delegation; proof may resume); 2026-10-14 22:30 ET (blocker: the approved statement is false; needs a statement decision); 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
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

## Blocker (2026-10-14 22:25 ET): the approved statement is false

**Box.** Ticket 42 work started 2026-10-14 14:42 ET (from `date`). Used so far: about 7.7 h
of the 2-week box shared with 43. Proof writer: Codex CLI 0.153.0, `gpt-5.6-sol`, `xhigh`,
sandbox `workspace-write` on the proof folder; 3 Codex turns (1 new thread
`01a13bc9-6103-7ca3-bb7d-005cf6693d0e`, 2 resumes). Every Rocq compile ran through
`verifier_run.py`, one compile per lock hold (README rule of 2026-10-14).

**Counterexample (found by the orchestrator, confirmed by Codex).** Nothing in the statement
makes critical sections well bracketed, so a thread may perform an `Exit` with no open
`Enter`. Take N = team_size = 2, locations x = 0, l = 1, m = 2, class of m LockProtected and
of every other array SharedActionsOnly, init = 0, `sa_new _ _ v = Some (v+1)`, all
`fence = false`, no barriers or worksharing. Thread 0: `DeviceRead 7 l 1; Enter; Read m 0;
Write m 1; DeviceCovered 7; Exit; HistoryRead x 0`. Thread 1: `Shared x 0; Exit; Shared l 0`
(a stray `Exit`). Run X: `0 (1,Shared x) 1 (0,DeviceRead) 2 (0,Enter) 3 (0,Read m)
4 (1,Exit) 5 (0,Write m) 6 (1,Shared l) 7 (0,DeviceCovered 7) 8 (0,Exit) 9 (0,HistoryRead x 0)`,
rf 1 = Some 6, all other rf = None.
- All seven obligations hold (each thread fits its classes; the only critical block
  implements a shared action and holds no barrier; command 7 conflicts with no later own
  access and crosses no barrier or critical exit of a section it was issued in; the rest
  are vacuous), and so do `program_run`, `memory_ok`, `omp_ok`, `device_ok` and `complete`
  (the device read's later source at 6 is another thread's and precedes the cover at 7; no
  write reaches the final `HistoryRead x 0` through `hb`).
- No serial twin exists. The only value-1 source for the device read is `Shared l`. In any
  Y, `device_ok` forbids `DeviceCovered 7` between the read and a later source, and thread 0's
  critical section is contiguous, so `Shared l`, and thread 1's stray `Exit` before it, come
  before thread 0's `Enter`. `omp_sync_critical` (stray Exit -> Enter) then puts `Shared x`
  happens-before the final `HistoryRead x 0`, so `omp_ok Y` needs a source no older than it;
  the only value-0 source is the initial value, and `not_older None _` is False.

**Status of the Rocq refutation.** Codex was formalizing it as `NegStrayExit.v`
(`~ type of parallel_composition`); stopped unfinished at the first error on line 638 of 945
(the hypothesis side is checked through line 637). Draft:
`/tmp/claude/probata-runs/t42/work/NegStrayExit.v` (sha256 `bbfb8e82…`); write-up
`/tmp/claude/probata-runs/t42/work/COUNTEREXAMPLE.md` (`cb2dcc3e…`).

**Proposed fix (needs Yan-Ru's approval: it changes the approved text).** Add a
per-candidate obligation, or a clause of `obl_atomic_blocks`, that every program trace is
well bracketed: an `Exit` only while a critical section is open, an `Enter` only while none
is open. OpenMP structured blocks guarantee this; the C lowering discharges it
syntactically. With it, no other thread's `Exit` can lie inside a critical window, and the
window can be cleared by moving the other threads' events before the `Enter`, which also
avoids the device-source/cover reversal (Codex's `t42_device_safe` finding). Not yet
re-reviewed for other counterexamples.

**What is checked (kept for the fixed statement).** 122 lemmas Qed in the `t42 lemmas` block
of `library/rocq/probata/Composition.v` (commits `c2bbbc82`, `4db68f9b`): A1 threads below N,
A2 `all_fit` from `obl_class_fit`, A3 runs are already sorted by barrier interval, A4 shape of
critical windows, and the full adjacent-independent-swap preservation set (B). Open: A5
(`reads_latest X`), C (window clearing), D, the theorem. The approved statement is unchanged:
`library/rocq/probata/check/check_approved.py` rebuilds ticket 41's file from the marked blocks
and checks its sha256; `check/Checks.v` compares the elaborated statement (`Set Printing All`)
with `check/statement.expected` and prints `Print Assumptions`.

**Run record.** `/tmp/claude/probata-runs/t42/`: `heartbeat.md`, `logs/compile-index.tsv`
(147 rows; sha256 `42d68c4c…`), `codex/turn-{1,2,3}.{jsonl,final.md}`, `work/NOTES.md`
(`c52d489d…`). Peak RSS per Rocq job about 0.42 GB. Lock waits reached 20 min while other
tickets held the lock across whole pytest batches.

## Resumption — 2026-10-15 01:41 ET

Ticket 41's current answer supersedes the false statement: well-bracketed critical sections,
fix (a)'s protected-read lifetime rule, and read-class stability while commands remain
uncovered are approved by the main session under delegation after independent local review.
No personal human reading or external CLI review is claimed. Reconstructed statement hash:
`ffb5bda714b9fce5a13927a4860f6c85438821cdcdf3b4f1560f26a91eefd4f4`.
`check_approved.py` and `statement.expected` now guard that version. Existing 122 Qed
lemmas remain checked. This resumes the same shared box; it does not restart its clock or
claim any unchecked step complete. Candidate compatibility and lowering discharge of
`obl_dx100_quiet` remain ticket 45's responsibility.

### Active proof resumption — 2026-10-15 ET

Claimed by the ticket 42 implementer on `codex/probata-t42`, based on integration
`a65e8cb1`. The proof seam remains the approved statement guard plus Rocq kernel
checking; this reuses the existing acceptance harness. The shared box and its original
2026-10-14 14:42 ET start are unchanged. Provider: the local Codex agent; no external CLI
execution or human approval of proof steps is claimed.

### Checked proof progress — 2026-10-15 01:54 ET

A5 is proved: `t42_reads_latest` shows every nonracing, nonexempt original-run
read already observes the latest write. This includes DX100 reads: an uncovered
noncrossing command cannot source a future write from another barrier interval,
readonly data cannot be written, ownership excludes foreign writes, and a future
protected write would require an uncovered critical exit. The original run's
read-age and CPU/OpenMP ordering then establish latestness. Supporting results
also close the foreign-Exit window case introduced by the repaired bracketing premise.

Evidence: `/tmp/probata-t42-resume/logs/compile-10.log.summary.json` (Rocq 9.3.0,
exit 0, 3.43 s, peak RSS 443.3 MB, 8 GB watchdog, no kill/timeout). Eleven selected
new lemmas, including `t42_reads_latest`, each print `Closed under the global context`
in `assumptions-1.log` (sha256 `003974cb4fe114d51c7d2eed462e080514b2036c2028e95effd020fa8e9fb5fb`).
The exact reconstructed statement guard still accepts `ffb5bda7…`; no approved
definition or hypothesis changed. The theorem itself remains open, so this is
proof progress only and does not authorize a Rocq-checked method-part record.
Next: critical-window clearing, including the RF-sensitive coverage side condition,
then the global serialization and iteration-count assembly.

### Statement blocker: ownership handoff — 2026-10-15 ET

The approved statement admits a command reading a ThreadOwned location across an
ownership transfer while its class remains ThreadOwned. Two source/cover constraints
then force a foreign event inside a critical section. Ticket 41 is reopened for the
coordinator-delegated ownership-lifetime repair; its new hash requires review. The
checked A5 and window lemmas remain useful. The shared box is not restarted and no
fallback or method-part proof record is claimed.

### Resumed after ownership repair — 2026-10-15 ET

The main session independently reviewed and approved ticket 41's ownership
lifetime repair. The exact reconstruction is now `e23f3715…`; the changed-ownership
negative control is refused. Three sanity controls are Qed and closed: rejecting
the exact ownership-handoff witness, accepting prior-covered handoff, and accepting
a static owner's barrier crossing. The original shared box and all checked A5/window
proof progress remain intact; full composition proof work resumes.

The repair's first use is also Qed: `t42_future_owned_source_impossible` proves that
an outstanding ThreadOwned device read cannot source a future foreign owner's
write, even across a barrier, under `reads_owner_stable`. Global/thread-local
class-lifetime transport is Qed as `t42_read_class_stable_global`. Compile:
`/tmp/probata-t42-resume/logs/owner-proof-1.log.summary.json`, exit 0, 3.73 s,
peak 443.6 MB. These directly address the previously open RF-sensitive swap case.

### Critical-window swap safety — 2026-10-15 02:10 ET

Both conditions for clearing any foreign event leftward inside a critical window
are now Qed: `t42_window_adjacent_indep` proves nonconflict and absence of new or
old synchronization; `t42_window_device_safe` excludes the earlier RF-source/cover
reversal. `t42_future_source_in_critical_forbidden` combines class lifetime,
ownership lifetime, and protected-read quietness to close that case. The four
core results print `Closed under the global context` (log sha256
`f0532d0e8a885018e887fe9f2fc1415078fabe8f12825919a931ee3c625a3996`).
Rocq compile: `owner-proof-6.log.summary.json`, exit 0, 5.36 s, peak 451.7 MB,
8 GB watchdog. No approved statement edit. Remaining: finite constructive window
partition, global serialization, and iteration-count/conclusion assembly. The
main theorem is still open, so this remains checked progress only.

### Conclusion assembly checked — 2026-10-15 02:20 ET

`t42_iterations_once` is Qed: uniform worksharing reachability, per-thread chunk
coverage/disjointness/NoDup, and OpenMP scheduling give each global iteration
exactly once. `t42_serialization_suffices` is Qed and assembles every serial-outcome
conjunct from a valid observational reordering with contiguous critical sections.
`t42_reorder` has Qed reflexivity/transitivity and the checked critical-window
adjacent-swap interpretation. Compile `iterations-3.log.summary.json`: exit 0,
4.46 s, peak 476.6 MB, 8 GB watchdog. The outstanding mathematical step is now
constructive global critical-section serialization. No fallback or completed
method-part theorem record is claimed.
