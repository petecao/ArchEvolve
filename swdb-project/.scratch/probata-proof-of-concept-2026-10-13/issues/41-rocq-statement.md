# 41 — Rocq: composition theorem statement and definitions

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 21:30 ET (`Reduction.v` revised under delegation: ticket 27 covers, see Later changes); 2026-10-14 14:40 ET (revised; approved by the main session under Yan-Ru's delegation; resolved); 2026-10-14 14:13 ET (Codex review: revise); 2026-10-14 14:07 ET (statements drafted); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
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

2026-10-14 14:40 ET. **Resolved.** Both statements and their definitions are written, revised
after four rounds of Codex adversarial review, type-checked, and approved by the main session
under Yan-Ru's delegation (record below). Ticket 42's box may start. Review guide, hypothesis
table, F1 candidate check and Codex dispositions:
[`library/rocq/probata/HYPOTHESES.md`](../../../library/rocq/probata/HYPOTHESES.md).

### Approval record

- **Approved by the main session under Yan-Ru's delegation, 2026-10-14 14:12 ET** (Yan-Ru,
  2026-10-14 14:12 ET: "use formal verification research thinking to make decision for me").
  Recorded 2026-10-14 14:40 ET. This is the main session's approval, not Yan-Ru's own reading.
- Approved content (sha256), in `swdb-project/library/rocq/probata/`:

  | File | sha256 |
  |---|---|
  | `Vocabulary.v` | `081b558de2d94a0b37200b094d39af38eddf51546686a575f97dac2e3a6a3a3d` |
  | `Composition.v` | `e30f62402164802aaf1bed224c6be0ac62fb787c43efe61190266e5a511dd01b` |
  | `Reduction.v` (current, revised 2026-10-14 21:30 ET, see Later changes) | `72f4a79fbf6005fc89990d5dcfed4b80118f9d02d8aac44b0bb9bc7b84968e53` |
  | `Reduction.v` (**superseded** 2026-10-14 21:30 ET) | `8a779482ff13c83a12d11fd15d34c0aadf1d8856052575e7ede38ab935188b7a` |

  Not part of the approval: `Sanity.v` (`8e73b9c3…`; now `8df1b4e7…`),
  `negative/HistoryReadIsLatest_FALSE.v` (`16aaf7db…`), `HYPOTHESES.md` (`a7b9759a…`; now
  `8da8a879…`). Any change to the three approved files needs a new approval; 42 and 43 check
  these hashes. `Vocabulary.v` and `Composition.v` are unchanged by the revision.

### What is stated

- `parallel_composition`: if the seven per-candidate obligations hold (`obl_class_fit`,
  `obl_owned_disjoint`, `obl_atomic_blocks`, `obl_chunk_cover`, `obl_uniform_control`,
  `obl_team_size`, `obl_dx100_quiet`) and the premises `memory_ok` (RC11 with fenced
  `__sync_*`), `omp_ok` (OpenMP 5.2) and `device_ok` (DX100 proof semantics) hold, every finished
  run of N threads has a serial twin: same events per thread, barrier intervals and critical
  sections one after another, every shared action and every read outside a shared-actions-only
  array (except dead DX100 reads, F1) reading the latest write, racing reads still history
  reads, same final memory, every worksharing iteration exactly once.
- `dx100_reduction`: if the command contracts are well formed (`contracts_ok`, proof semantics)
  and no at-issue run has a hazard (`obl_hazard_free_own`, `obl_hazard_free_cross`), every
  complete timed run gem5's rules allow has an at-issue twin with the same observations per core
  and the same final state.

### Decisions (each decided by the main session under Yan-Ru's delegation, 2026-10-14 14:12 ET)

- **F1, accepted in refined form.** `obl_dx100_quiet`: a command may stay uncovered past a
  barrier, or past the exit of a critical section it was issued in, only if it has outputs,
  writes tile elements only, and they are dead there; `reads_latest` excludes its reads.
  Deviation from the decision's wording: "dead" = not read before a later command's overwrite
  (not a *covered* overwrite), because gem5's WAW dispatch stall already finishes the old command
  first, and both candidates' overwriting commands are covered only later. Candidate check (line
  numbers in HYPOTHESES.md): **Peter's `TDStep` meets the rule** (`bfs_read_offload.inc:30-32`
  uncovered on the empty-chunk path, tile-only, dead); **the authors' `TDStepMAA` meets the
  rule** (`bfs.cc:163` uncovered on the break path, tile3 only, dead; the critical section's
  store `:179` is covered by `:180` before the exit). The first draft's rule failed both.
- **F2, accepted.** `in_region` is a relation; a DX100 memory access outside some registered
  region holding it, or in none, is a hazard. No disjointness is assumed.
- **F3, accepted.** Every definition stays explicit (Composition.v 365 lines, Reduction.v 272,
  about 5 + 4 printed pages); a one-page plain-language summary heads HYPOTHESES.md. The
  "about 2 printed pages" criterion is amended by this decision.
- **F4.** Provenance: drafted by Claude (`claude-opus-5-5`, Claude Code subagent); reviewed
  adversarially by Codex CLI 0.153.0 at the adapter pin `gpt-5.6-sol`, effort `xhigh`,
  read-only sandbox, in four rounds. The proofs (42, 43) stay Codex's.
- **M1-M10 accepted.** **Flag on M6, open obligation for ticket 43:** the reduction lemma orders
  CPU steps in one global sequence while the composition theorem uses RC11; 43 must show why the
  split is sound (issues and waits act as fences in the CPU model, or hazard freedom makes DX100
  timing unobservable under RC11).

### Findings added by this ticket

- **F5:** the proof semantics' coverage rule needs `cov_stall` (a covered command covers every
  earlier command that would have stalled its dispatch, `IF.cc:193-219`); without it
  `bfs.cc:147` never counts as covered and the tile0 read at `:191` is a false hazard.
- **F6:** DX100 commands write registers (the range loop's cursors); no cited gem5 rule orders
  them device against device, so a run overlapping a pending command on a register where either
  writes is a hazard. Both candidates wait on tile7 before the next range loop.
- **Open for ticket 45:** the `cover_sound` lowering obligation (specified in HYPOTHESES.md):
  command id = issue position, device events = the command's footprint, `DeviceCovered` only
  where `Reduction.covered` holds, DX100 read values reach the thread only through outputs,
  `Shared`'s fence flag and kind match the code. The formal bridge lemma is not written.

### Codex adversarial review (`gpt-5.6-sol`, `xhigh`, read-only)

Outputs in `/tmp/claude/probata-runs/t41/`. Every finding and its disposition is in
HYPOTHESES.md; rejected ones with reasons.

| Round | Output (sha256) | Result |
|---|---|---|
| 1 | `codex-review.md` (`4005d8dc…`) | 12 findings: reduction false (metadata), RC11 label, constructive TileReady, 7 major, 2 minor. Accepted 1, 3, 5, 6, 8, 9, 11, 12; partly 2, 7, 10; rejected 4 (commands need a covering wait: real code leaves `bfs.cc:163` uncovered). |
| 2 | `codex-review2.md` (`7e0e2708…`) | 8 findings: reduction still false (registers). Accepted 1, 4, 5, 7, 8; partly 2, 3 (cover_sound open for 45); rejected 6 (lifting lemma: the obligations already have the rely form of `obl_class_fit`). |
| 3 | `codex-review3.md` (`f630f68b…`) | Counterexample to `parallel_composition` (critical section touching a shared-actions-only location or holding a barrier). Accepted: both forbidden. |
| 4 | `codex-review4.md` (`7e47aba2…`) | **No counterexample found** for either statement. |

### Checks

Rocq 9.3.0 (switch `rocq-9`), every compile through `verifier_run.py`; outputs outside the repo
in `/tmp/claude/probata-runs/t41/` (final run after merging the integration tip: see the commit
message).
- `Vocabulary.v`, `Composition.v`, `Reduction.v`, `Sanity.v` compile (exit 0).
- `Print Assumptions` lists only the two theorems themselves (`Admitted`, marked "OPEN — ticket
  42/43"); no `Axiom` anywhere.
- Eight sanity lemmas, all `Qed`, "Closed under the global context": 5 kinds, 4 classes; a
  relaxed load may be stale inside the admitted program class (`stale_run_fits`,
  `stale_history_read_allowed`, `history_read_not_always_latest`); `read_own_write`;
  `failed_cas_reread_sees_winner` (15 item 12's must-prove control; the failed CAS writes
  nothing); `unready_read_is_hazard` (12 item 9).
- Negative check `negative/HistoryReadIsLatest_FALSE.v` is rejected at its unprovable branch
  (exit 1), as required.

### Assumptions

- Assumption: the development lives in `swdb-project/library/rocq/probata/` (library content,
  pinned by content hash in the method-version file, id `probata.rocq-development`; theorem names
  `parallel_composition`, `dx100_reduction` as in the method-version fixture).
- Assumption: Codex's adapter pin is taken from the ticket and design spec (`gpt-5.6-sol`,
  `xhigh`); the CLI ran with `-m gpt-5.6-sol -c model_reasoning_effort=xhigh -s read-only`.

### Later changes

- 2026-10-14 21:30 ET: `Reduction.v` revised by the main session under Yan-Ru's delegation
  (branch `probata-poc/t41b`). Source: ticket 27's Answer, "Disagreements with ticket 41's Rocq
  statement": `covered` only started at a wait, so `dx100_reduction` did not back proofs using
  proof semantics 0.1's issue-stall and register-write covers (fixtures `stall_condition`,
  `register_write`). Changes: constructors `cov_issue` (dispatch stall, `IF.cc:193-219`) and
  `cov_reg_write` (CPU register write held, `IF.cc:233-249`), both mirroring existing
  `timed_run` clauses; `pending` now excludes covers at its own step (`m <= j`), else a register
  write would still be a same-thread hazard against the commands it covers. New sha256
  `72f4a79f…` (approval record; `8a779482…` superseded). `Composition.v`, `Vocabulary.v`
  unchanged. Sanity lemmas `stall_covered`, `stall_not_pending`, `reg_write_covered`,
  `reg_write_not_pending` (Qed, no axiom). Codex round 5 (`gpt-5.6-sol`, `xhigh`, read-only,
  `/tmp/claude/probata-runs/t41b/codex-review.md`, sha256 `9dc000a6…`): no counterexample;
  4 findings, dispositions in HYPOTHESES.md ("Later change: ticket 27 covers"). Checks via
  `verifier_run.py` (`/tmp/claude/probata-runs/t41b/compile-5.log`, sha256 `83bab795…`): all four
  files compile; `Print Assumptions` lists only `parallel_composition` and `dx100_reduction`
  (Admitted); the negative check is still rejected (exit 1).
- **Note for ticket 43:** prove the text with sha256 `72f4a79f…`, not `8a779482…`. Proof
  shape: each base cover (`cov_direct`, `cov_issue`, `cov_reg_write`) removes n from `pending`
  only at a step where the matching `timed_run` clause forces n finished before that step, and
  the closure rules (`cov_producer`, `cov_stall`) preserve "finished before m"; inclusive
  `pending A n j` lines up with `unfinished T n j`. `cov_stall` is implied by `cov_issue` for
  `pending` (kept). Open from Codex round 5 finding 2: `contracts_ok` does not tie
  `regions_of`/`writes_memory` to gem5's assigned region and access class; this was already true
  of `timed_run`'s approved stall clause and is carried as descriptor faithfulness in the
  `cover_sound` lowering obligation (ticket 45) and ticket 28's region rules, not as a premise.
