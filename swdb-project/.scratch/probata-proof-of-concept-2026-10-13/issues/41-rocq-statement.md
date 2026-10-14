# 41 — Rocq: composition theorem statement and definitions

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 14:13 ET (Codex review: revise before Yan-Ru's review); 2026-10-14 14:07 ET (statements drafted); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 09
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (composition theorem, shared-action kinds, memory model, OpenMP), "Formal-half language and the C++ subset" (sharing classes, YAML frame), "DX100 proof semantics" (reduction lemma, hazards), "Modules" (Rocq development), "What a proven verdict asserts" (assumption set, seven kinds), "Proof-of-concept plan" (Rocq side track), S9); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 4 days plus Yan-Ru's review

**What to build:** Codex writes, in Rocq, two statements and the definitions they need: the parallel
composition theorem and the DX100 reduction lemma. Yan-Ru then reviews and approves only these, in
one review before the shared Rocq box (S9), a human step recorded in this ticket. The theorem says:
if each thread of a parallel region is proven alone, and touches shared memory only through shared
actions within their sharing classes, then every run ends as some serial order of those shared
actions would. Shared-action kinds and sharing classes are closed constructors. Each hypothesis is
exactly one per-candidate WP obligation or one assumption entry. The lemma says: if the code is
hazard-free, every timing gem5 allows gives the same values as finish-at-issue (12 item 2). The
theorem fits on about 1-2 pages, so the review is short. The proofs are tickets 42 and 43.

## Acceptance

- [ ] Both statements and their definitions type-check under the Rocq version ticket 03 installed
      (version recorded). Both proofs are left open and visibly marked open. Nothing else is
      admitted, and no axiom is declared.
- [ ] Shared-action kinds are a closed enumeration with exactly five constructors: claim (write-once
      CAS), min-update, atomic add or OR, OpenMP reduction, queue reserve.
- [ ] Sharing classes are a closed enumeration with exactly four constructors: read-only,
      thread-owned, changed only through shared actions, lock-protected. A class is assigned per array
      per barrier interval.
- [ ] The definitions state 15 item 3's memory model: a history read returns a value the location
      already held, never older than the newest write the reading thread has seen (its own accesses,
      and writes ordered before it by a barrier, `critical` or a CAS); a CAS is a sequentially
      consistent read-modify-write; a plain access to a location changed only through shared actions
      is a race. Other threads' DX100 commands (15 item 7): their reads meet thread t as history
      reads; their writes are allowed only inside `critical` or into the issuing thread's own memory.
- [ ] The conclusion holds for a symbolic thread count N with distinct thread ids 0 to N-1: every run
      ends as some serial order of the shared actions would.
- [ ] A hypothesis table beside the Rocq files maps every hypothesis to exactly one per-candidate WP
      obligation or exactly one assumption entry (kind and plain sentence). No hypothesis maps to both
      or to neither. The table covers at least:
      - the per-candidate obligations of 15 items 2 and 4: accesses fit their sharing classes; each
        atomic block or `critical` section implements one shared action; owned ranges, tiles and
        registers are disjoint for t != t'; chunk splits cover the frontier exactly once; uniform
        control; team size = N;
      - the OpenMP runtime entry (trusted tool, citing OpenMP 5.2);
      - the RC11 entry (platform choice, per 26 item 4).
- [ ] Each hypothesis has a stable name, so each per-candidate WP obligation can be named after the
      hypothesis it discharges (16 item 4).
- [ ] **DX100 reduction lemma statement (S9).** The lemma is stated in the same development. Its
      definitions model what 12 item 2 names: one core's commands dispatch in program order but may finish out
      of order; the tile dispatch stall; the memory-region stall (across all cores of one instance,
      12 item 4); each command finishes at some point before its covering wait. Each definition
      cites the proof-semantics rule it models and that rule's gem5 citation.
- [ ] "Hazard-free" is the proof semantics' own hazard definition (12 items 3-5): no unready read,
      and no CPU write to a tile an unfinished command reads; no same-thread overlap with an
      unfinished command's footprint where either side writes; no other-thread overlap with an
      unfinished DX100 write; no use of a tile or register the thread does not own. Device against
      device is not a hazard: the region stall orders it, and the definitions model that stall.
- [ ] The theorem's statement plus definitions fit in about 2 printed pages.
- [ ] Yan-Ru's approval of both statements is recorded in this ticket's Answer: date and time ET, and
      the content hash of each statement's reviewed files. Codex's provider pin is recorded with the
      draft.

## Notes

- **Not in this ticket:** 42 — Rocq: composition theorem proof (the proof and its proof record);
  43 — Rocq: DX100 reduction lemma (the lemma's proof and proof record; its statement is written and
  reviewed here); 44 — Shared-action kinds and
  commutativity lemmas (the WP lemmas, and the script that checks the YAML kinds, sharing classes and
  Rocq constructors agree); 45 — Per-thread lowering (emits the obligations named after these
  hypotheses); 11 — Method-version file and failure classes.
- The commutativity lemmas are not hypotheses of this theorem. They feed each contract's
  order-independence lemma, which turns "some serial order" into the unit relation (15 item 2).
- Assumption (not decided in the map): the Rocq statement ends at "some serial order of the shared
  actions". It is joined with a contract's order-independence lemma (a WP proof) through the proof
  records' dependencies, not inside Rocq. Yan-Ru may ask for a Rocq corollary at review.
- The method-version file lists the Rocq development (S8). Assumption (not decided in the map): it is
  versioned library content, pinned there by content hash.
- Yan-Ru's one review, of both statements, comes before the box: one 2-week box then covers 42 and 43
  together (S9).
- Assumption (not decided in the map): any change to an approved statement or its definitions needs
  a new approval. Tickets 42 and 43 each check that they prove the approved hash.
- Assumption (not decided in the map): this ticket waits only on 09, so the lemma's statement is
  written from 12 items 2-5, not from a built proof-semantics version. 43's rule-coverage assumption
  checks it against the version 43 pins.
- Assumption (not decided in the map): 15 item 7 calls other threads' DX100 commands shared actions,
  but item 5's closed list has no DX100 kind. This ticket models them through history reads and the
  thread-owned and lock-protected classes, not as a sixth constructor. Yan-Ru confirms at review.
- Provider: Codex, pin `gpt-5.6-sol`, effort `xhigh` ([23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) item 7). Yan-Ru reviews only the statements and definitions,
  never the proofs (15 item 8; S9).
- The Rocq track starts after the spike verdict, so the spike's stop rule cannot waste it
  ([27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 4).
- Mac: Rocq runs as one job at a time under the ~8 GB RSS watchdog.

## Answer

2026-10-14 14:07 ET. **Status: ready-for-human.** Both statements and their definitions are
written and type-check. **Yan-Ru's review is the open step**, and 42 and 43 must not start before
it (S9). Review guide and hypothesis table: [`library/rocq/probata/HYPOTHESES.md`](../../../library/rocq/probata/HYPOTHESES.md).

**What Yan-Ru reviews** (in `swdb-project/library/rocq/probata/`):

| File | What | sha256 at this draft |
|---|---|---|
| `Vocabulary.v` | 5 shared-action kinds, 4 sharing classes (closed) | `081b558de2d94a0b37200b094d39af38eddf51546686a575f97dac2e3a6a3a3d` |
| `Composition.v` | `parallel_composition` and its definitions | `03c5337d74e63c0011b9521ddaadca955d5e2adee4889bef47c9b01ebc3432c6` |
| `Reduction.v` | `dx100_reduction` and its definitions | `83c1d97295bac65f11b52dfacd2394f7093b1b3cfc60b66dfd380c4bc7031d00` |

Not for review: `Sanity.v` (`2b918f89…`), `negative/HistoryReadIsLatest_FALSE.v` (`45e88e90…`).

**Approval record (to fill in):** date and time ET: ____; approved sha256 of the three files
above: ____. Any change to them needs a new approval; 42 and 43 check these hashes.

**Statements, one line each.**
- `parallel_composition`: if the seven per-candidate obligations hold (`obl_class_fit`,
  `obl_owned_disjoint`, `obl_atomic_blocks`, `obl_chunk_cover`, `obl_uniform_control`,
  `obl_team_size`, `obl_dx100_quiet`), then every finished run of N threads that meets the RC11,
  OpenMP and DX100-read premises has a serial twin: same events per thread, barrier intervals and
  critical sections one after another, every read outside a shared-actions-only array and every
  shared action reading the latest write, racing reads still history reads, same final memory,
  every worksharing iteration exactly once.
- `dx100_reduction`: if no at-issue run (each command runs at its issue; ghost "pending" until a
  covering wait) has a hazard, every complete timed run that gem5's rules allow (dispatch stall,
  region stall, out-of-order run with element readiness, finish order, wait rule) has an at-issue
  twin with the same observations per core and the same final state.

**Checks** (Rocq 9.3.0, switch `rocq-9`; all through `verifier_run.py`, output outside the repo
in `/tmp/claude/probata-runs/t41/`; final run `compile-8.log`, sha256
`b302f1a047d63311323436862621396fb99f3e791422ee7dd3887b23de72d257`, peak RSS 413 MB):
- `Vocabulary.v`, `Composition.v`, `Reduction.v`, `Sanity.v` compile (exit 0).
- `Print Assumptions` lists only the two theorems themselves: both proofs are `Admitted` with an
  "OPEN — ticket 42/43" comment. No `Axiom` anywhere; nothing else admitted.
- Seven sanity lemmas, all `Qed`, "Closed under the global context": enumerations have exactly 5
  and 4 members; a history read may be stale (the model is not SC); a plain read sees the
  thread's own write; 15 item 12's must-prove control (read, failed CAS, re-read sees the
  winner); a same-thread read during an unfinished DX100 store is a hazard (12 item 9).
- Negative check: `negative/HistoryReadIsLatest_FALSE.v` (history reads are SC) is rejected at
  its unprovable branch (exit 1), as required.

**Acceptance status.** Met: type-check, open proofs visibly marked, no axioms; 5 and 4 closed
constructors; class per array per barrier interval; 15 item 3 memory model and 15 item 7 DX100
rules; symbolic N with ids 0..N-1; hypothesis table with stable names; reduction lemma models
12 item 2 with gem5 citations; hazard-free per 12 items 3-5. **Not met:** length is about 4.5 +
3.5 printed pages, not about 2 (F3); Yan-Ru's approval (open); the draft is not by Codex (F4).

**Assumptions** (beyond the ticket's own):
- Assumption: the development lives in `swdb-project/library/rocq/probata/` (library content,
  pinned by content hash in the method-version file, id `probata.rocq-development`; theorem names
  match the fixture: `parallel_composition`, `dx100_reduction`).
- Assumption: modeling choices M1-M10 in HYPOTHESES.md (RC11 rendering with one global order; DX100
  effects at issue in the composition model; one-location critical sections; CAS loops as one
  shared action; worksharing constructs numbered dynamically; SC CPU steps inside the reduction
  lemma; 8-byte operands not modeled).

**Findings for Yan-Ru** (details in HYPOTHESES.md):
- **F1:** new per-candidate obligation `obl_dx100_quiet`: every DX100 command covered before the
  thread's next barrier and before it leaves `critical`. Without it, a DX100 read pending across
  a barrier can see next-interval writes (12 item 4 allows that overlap). Stricter than 12.
- **F2:** new hazard: a DX100 memory access outside its command's registered regions escapes the
  region stall. Registered regions are assumed disjoint.
- **F3:** length over target (every obligation spelled out so each maps to one table row).
- **F4:** provenance. The ticket names Codex (`gpt-5.6-sol`, `xhigh`) as drafter; this draft was
  written by Claude (`claude-opus-5-5`, Claude Code subagent). Codex `gpt-5.6-sol` `xhigh` was
  started read-only as an adversarial reviewer at 14:03 ET; it had not finished at commit time.
  Its output: `/tmp/claude/probata-runs/t41/codex-review.md` (event log `codex-review.jsonl`).
  Its first interim note claimed issued commands need not run; that is not so (`at_issue_run`
  requires a run step at `S n` for every issue; `complete_timed` requires a finish, which requires
  a run). Yan-Ru decides whether Codex should redraft.

### Codex adversarial review (2026-10-14 14:12 ET): revise before Yan-Ru reviews

Codex `gpt-5.6-sol`, effort `xhigh`, read-only. Output `/tmp/claude/probata-runs/t41/codex-review.md`
(sha256 `4005d8dcbc2767795858b682a72e75dd1ed49ce451188ae8eea57712ca7b6066`). **Verdict: do not
approve.** Status moves from ready-for-human back to **ready-for-agent**: the draft above must be
revised first, and its hashes will change. I (Claude) checked findings 1-3 and agree they are real.

- **Blocker 1 (`dx100_reduction` is false):** command metadata (`footprint`, tile roles,
  `regions_of`, `writes_memory`) are independent parameters. A command that writes memory but
  declares `writes_memory = false` escapes the region stall; Codex gives a two-core run whose
  final state no at-issue twin matches. Fix: a metadata-validity premise (memory outputs imply
  `writes_memory`; footprint agrees with tile/register/region declarations).
- **Blocker 2 (`memory_ok` is stronger than RC11):** `sync_shared` makes SC order between RMWs on
  different locations a happens-before edge, which forbids the RC11 store-buffering outcome with
  SC RMWs plus relaxed loads. This was intended (M1: `__sync_*` as full fences), but then the
  premise is not "RC11"; it must be named as the stronger `__sync` full-barrier platform
  assumption, or `hb` must keep SC order separate.
- **Blocker 3 (constructive):** timed `TileReady false` yields only `~ forall`, while at-issue
  needs an explicit pending witness. Fix: state the timed rule by cases with a witness for false.
- **Major 4-10:** commands need not have a covering wait (`complete_timed`); `DeviceQuiet` is an
  unchecked marker (needs a `quiet_sound` obligation or waits in the composition trace); `WaitReady`
  and `TileReady` skip the ownership check; premises do not map one-to-one (`hb` mixes RC11 and
  OpenMP edges; `device_ok` reuses it); `obl_hazard_free` is a whole-run property, not a one-thread
  WP obligation (split into local and pairwise parts plus a lifting lemma); a failed CAS is modeled
  as a write; `obl_atomic_blocks` cannot cover a DX100 write inside `critical`.
- **Minor 11-12:** the stale-read sanity example lies outside the admitted program class; the page
  budget is unmet.

Codex found no direct counterexample to `parallel_composition` over its own definitions and
judged `obl_class_fit` non-vacuous. **Next action:** revise `Composition.v` and `Reduction.v` for
findings 1-10 (Codex should do it, per F4), rerun the checks, then set ready-for-human.

