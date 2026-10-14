# 07 — Spike (c): WP with agent hints

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 08:45 ET (resolved: spike verdict fail); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (c); "Proof-hint loop"; "Verifier lineup and order", unbounded verifier; "Providers and machines"); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 3 days, inside the 2-week box

**What to build:** The spike's test of the unbounded half. WP must prove one read-offload proof
unit at threads = 1 against the BFS unit postcondition, with proof hints written by Codex, within 60
minutes. The unit is one `TDStep` call with Peter's read offload, the contract's reference instance.
The C lowering tool does not exist yet (21), so WP reads a hand-made C stand-in for it. Throwaway
ACSL contracts stand in for the DX100 calls' summaries. Failing within the box is a stop condition
for 09 — Spike verdict.

## Acceptance

- [ ] The hand-made C stand-in keeps the unit's C++ names (map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 3), has a
      hazard check at each tile-pointer read (map
      [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) item 3), and
      reaches the DX100 calls only through throwaway ACSL contracts. Scope: threads = 1; every data
      dimension symbolic; `TILE_SIZE` a symbolic constant (map
      [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 2).
- [ ] WP runs once with no hints; its unproven goals are recorded with their failure class
      (timeout or unknown).
- [ ] One counted run starts with no hints and ends with every goal proven within 60 minutes wall
      time, WP time and Codex calls included. Recorded: rounds, Codex calls, tokens, and solver and
      time per goal.
- [ ] Every hint is one of map [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md)
      item 5's allowed kinds. None of its rejected kinds appears (`admit` in any form, `axiom`,
      recursive or inductive definitions, contracts, ghost functions, ...). Erasing the hints leaves
      the stand-in unchanged, checked by diff. Provenance is recorded per hint: every hint in the
      counted run comes from Codex, none from the implementing agent.
- [ ] The verdict is read from WP's per-property report of a fresh run (`-wp-cache none`, fresh
      session, default warning levels, x86_64 machdep, no WP environment variables). Every goal,
      lemma, call-site precondition and termination goal is Valid. No `Extern` outside the
      contracts of summaries and `maa_*` calls (WP prints those body-less contracts as `Extern`);
      each such contract is an assumption entry (map 13 item 7; design S7). The consolidated
      `[ Valid ]` line is never used.
- [ ] Every smoke test passed on the final hinted unit: no reachable `\false`. A smoke goal WP
      proves Valid signals dead code, so it fails the test (design S7).
- [ ] Negative control: the same hints on a copy of the stand-in with its covering wait removed
      leave the hazard check not proven. WP reports "not proven", never "refuted" (map
      [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)).
- [ ] WP uses the solver portfolio Alt-Ergo, Z3 and CVC5. A goal counts when any one proves it; the
      solver is recorded per goal (map [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md)
      item 8).
- [ ] Codex sees map 13 item 6's workspace, minus what does not exist yet: the stand-in (read
      only), the unit's C++ code, the unit postcondition, the ACSL summaries, the failing goals with
      kind and failure class, and earlier rejected hints. It never sees tests, negative controls,
      the evaluator, workload inputs or other candidate artifacts. The provider pin is recorded.
- [ ] The Answer states "pass" or "fail", with evidence paths and sha256.

## Notes

- **Not in this ticket:** 21 — C lowering and WP adapter (A2 tracer) (the real lowering); 27 —
  Proof semantics for the BFS read-offload calls and 30 — Reference definitions, per-call summaries
  and new intrinsic versions (the real ACSL summaries); 31 —
  Five-gate drafting and the new bfs_read_offload version (formal halves); 34 — proof_hinting role
  and workspace; 35 — Hint records, merger and proof hint check; 36 — Proof setup check and verdict
  reading; 37 — The proof-hint loop (seeds, minimization, budgets); 39 — BFS unit proven unbounded at
  one thread; A3 exit; 45 — Per-thread lowering (symbolic thread count).
- **Throwaway.** Nothing here becomes A2 or A3 code.
- Assumption (not decided in the map): the 60 minutes count as map 13 item 11 counts its budget:
  loop wall time including verifier time, for one run that starts with no hints. Earlier runs may
  fix the stand-in and the summaries, never pre-seed hints. Map 13's other starting values (10
  rounds, WP 30 s per solver) apply and are recorded.
- Assumption (not decided in the map): "proven" here means the unit postcondition plus the hazard
  checks. Formal halves (A) do not exist until 31.
- Assumption (not decided in the map): Codex is called directly, with the design's pin
  (`gpt-5.6-sol`, effort `xhigh`), since the `proof_hinting` role arrives with 34.
- **Why 03 blocks this ticket:** Codex runs on the Mac under the scoped ADR 0006 exception that 03 —
  New verifiers on the Mac records. Confinement follows design O3's default until Yan-Ru rules:
  Codex's own sandbox over the frozen workspace; the role builds nothing (map 13 item 13). 03
  records that default in the exception.
- Assumption (not decided in the map): these direct Codex calls count as `proof_hinting` work under
  that exception, though the role itself arrives with 34.
- Assumption (not decided in the map): "the box" is A1's 2-week box. A counted run that has not
  passed when the box ends is a fail for 09.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs and per-goal reports go to a Mac runs
  folder outside the repo, host `mac` (map 26 item 5). If 05 has not yet recorded that folder, record
  its path, size budget and readers before the first run (LR-06).
- **Risks:**
  - WP must run outside the agent sandbox. Inside it, the Why3 server socket is blocked and WP
    reports `[Failure]` (map 11 and 13 research).
  - A hand-edited WP cache once made a false goal `[ Valid ]` (map 13). Never read a cache.
  - WP turns recursive definitions into unchecked axioms; one proved a false postcondition (map
    13). That is why the vocabulary bans them.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog. Keep at least 50 GB
  free. The counted run may take 60 minutes, so schedule the 30-minute heartbeat first (LR-07).

## Answer

2026-10-14 08:50 ET. **Spike verdict: fail.** No counted run ended with every goal proven within 60
minutes. These are Mac results (host `mac`), not comparable with mbit10 numbers.

**For ticket 09, two results:**

- **(a) First counted run (run 1): fail.** 10 rounds, 10 Codex calls, 58.97 budget-min. Frama-C's
  parser rejected all 10 hint sets, so WP never ran with hints. 8 of the 10 failed on the same error
  (a C local inside `\at(..., Pre)`). The loop could not tell Codex which hint held the failing line.
- **(b) Best run (run 3): fail.** 2 rounds, 6 Codex calls, 60.99 budget-min. One hint set reached
  WP: 543 of 642 goals proven, 99 timeouts. 8 of 9 postconditions and all 3 hazard checks were
  Valid, but only under hint assertions and invariants that WP did not prove. The budget stopped the
  second set's WP run.
- **Why both failed, largest cause first:**
  1. One WP pass takes 15–20 minutes (420–640 goals, 3 provers at 30 s each, `-wp-par 12`). With
     Codex calls added (2–14 min each at `xhigh`), 60 minutes hold about 2 WP passes.
  2. Frama-C accepted none of Codex's first-attempt hint sets (0 of 14 across all runs). In run 3,
     each round needed 2 repair turns: one for a parse error, one for a WP "Invalid infinite range"
     in a `loop assigns`.
  3. Waits for the verifier lock held by other tickets stretched each 60-minute budget to 2.4–2.9
     hours of wall time. These waits are excluded from the budget and recorded below.

### Every counted run

| Run | Folder | Harness | Rounds / Codex calls | Budget-min | Lock wait excluded | Outcome |
|---|---|---|---|---|---|---|
| aborted-1 | `aborted-1/` | v1 with bug A | 0 / 1, killed after 1 min | ~1 | 0 | aborted: bug A found before any hint set came back |
| 1 | `counted-1/` | v1 + fix A | 10 / 10 | 58.97 | 67.0 min | **fail**: parser rejected all 10 sets; 0 hinted WP runs |
| 2 | `aborted-2/` | v2 | 1 / 2 | 13.37 at abort | ~13 min | aborted: bug B (a WP abort read as "0 failing goals") would have misled round 2 |
| 3 | `counted-3/` | v3 | 2 / 6 | 60.99 | 114.2 min | **fail**: 99 goals left open after round 1; the budget killed round 2's WP run |

All runs used the same stand-in (sha256 below) and fresh Codex sessions. No hints carried over
between runs. Runs 2 and 3 reused run 1's no-hint WP run after a hash check.

**Harness changes between runs, classified:**

| Change | When | Kind | Why |
|---|---|---|---|
| A. The verdict reader attributes `Extern` lines to their function | before run 1 | **bug fix** | Summaries' `assigns \nothing` lines carry no file, so they were flagged as problems; a proven unit could never pass |
| Map each Frama-C error line to the hint that holds it, and show both | before run 2 | **method change** (feedback format) | Run 1 repeated one error 8 times; the error named a line of the merged file, which Codex never saw |
| Up to 3 repair turns per round, in the same Codex session (`codex exec resume`), after a failed hint check | before run 2 | **method change** (emulates map 13 item 6's in-call check wrapper) | Codex ran without tools here, so it could not run the check itself |
| Generic Frama-C syntax notes in the prompt (ghost locals need C types; no C locals inside `\at(..., Pre)`) | before run 2 | **method change** (prompt) | These two errors cost run 1 every round |
| B. A WP abort, or a WP run with 0 goals, counts as a failed round; the log tail goes back to Codex | before run 3 | **bug fix** | Run 2 read WP's abort as "0 failing goals" |
| WP goal generation (`-wp-prover none`) added to the hint check; its errors are traced to the hint | before run 3 | **method change** (hint check) | WP rejects some sets the parser accepts (infinite ranges in `loop assigns`) |
| Reuse run 1's no-hint run (same stand-in hashes) | runs 2, 3 | procedure | Saves 15 minutes; the no-hint run is outside the budget anyway |

The method changes belong in the method version (vocabulary, checks, prompts; see design "Records
and levels"). Here they changed only the spike harness.

### Acceptance, item by item

- **Stand-in:** `prototype/07-wp-hints/standin/tdstep_standin.c` (sha256 `a39c67ad…48c81`).
  - It keeps the unit's C++ names: `TDStep`, `g`, `VertexOffsets`, `parent`, `queue`, `lqueue`, `c`,
    `begin`, `end`, `count`, `vertices`, `frontier`, `hints`, `hint` and `claimed`; the struct fields
    `out_neighbors_`, `start_`, `shared`, `shared_in`, `shared_out_start` and `shared_out_end`; and
    members as named functions, such as `QueueBuffer_NodeID_push_back`.
  - Both branches are in: the DX100 path and the scalar fallback.
  - Hazard checks: a generated `check hazard_*` at each of the 3 tile-pointer reads, plus the
    `hazard_tile_size_ready` precondition of `__dxc_tile_size`.
  - The 10 DX100 calls are body-less ACSL summaries in `standin/dxc_summaries.h` (sha256
    `049659dc…a580a`). Each tile carries ghost pending and dependency state (map 16 item 10, reduced).
  - Scope: threads = 1, and every data dimension is symbolic. `TILE_SIZE` (1..65535),
    `SWDB_CHUNK_SIZE` (1..`TILE_SIZE`) and `SWDB_FRONTIER_THRESHOLD` (at least 1) are symbolic
    constants.
  - The unit postcondition has 9 `ensures`: 08's P2, plus queue framing and "DX100 idle at exit".
    Its definitions are in `standin/bfs_unit.h` (none recursive).
  - GAPBS members that have bodies are proven in the same run (`standin/gapbs_models.h`).
- **No-hint run** (`counted-1/round-0/`, 15.3 min, peak RSS 3.6 GB):
  - 422 goals. 317 proven: Qed 129, Alt-Ergo 158, Z3 2, CVC5 2, and 26 trivially terminating or
    unreachable.
  - **105 not proven, all with failure class timeout** (none unknown).
  - All 105 are in `TDStep`: 40 `assigns`, 5 `terminates`, the 9 postconditions, the 3 hazard checks
    and 47 call-site preconditions. Every goal of the models and summaries was proven.
- **Counted run within 60 minutes:** not achieved (see above).
  - Each run's `history.json` records rounds, Codex calls, tokens and wall time per round. Each WP
    run's `per_goal.tsv` (from WP's `-wp-report-json`) gives the solver and time per goal.
  - Run 1 tokens: input 704,221 (290,304 cached), output 221,188 (89,250 reasoning).
  - Run 3 tokens: input 377,771 (104,576 cached), output 121,500 (52,609 reasoning).
- **Hint vocabulary and provenance:**
  - The vocabulary check rejected 0 of the 26 hint sets (all runs, all turns). No `admit`, `axiom`,
    recursive or inductive definition, contract, ghost function or other banned kind was tried
    (escape-hatch count 0).
  - Every set that reached Frama-C passed erase-and-diff.
  - Run 3's WP-checked set (sha256 `7b603013…8ac1e`) has 155 hints: 85 `assert`, 37
    `loop invariant`, 16 `predicate`, 5 `loop assigns`, 5 `loop variant`, 4 `ghost`, 2 `lemma`,
    1 `logic`.
  - All 155 hints come from `codex gpt-5.6-sol xhigh`, with round and turn recorded per hint. The
    implementing agent wrote none.
- **Verdict reading:**
  - The frozen flags are in `wp_run.sh`: fresh run folder and session, `-wp-cache none`, default
    warning levels, x86_64 machdep, and `env -i`, so no WP environment variables reach WP.
  - The reader uses WP's per-property `-report` and `-wp-report-json`, never the consolidated line.
  - `Extern` is allowed only for the body-less functions in the two summary headers. Each is an
    assumption entry of kind summary: the DX100 calls, the region calls, the `__sync_*` and
    `__atomic_*` builtins, `std::copy`, and `operator new[]`/`delete[]`.
  - After run 3's round 1, 249 properties were not Valid (92 `-`, 157 `Partial`), so the verdict is
    "not proven".
- **Smoke tests:** 139 of 139 passed in the no-hint run and in run 3's hinted run, so no `\false` is
  reachable. The unit never proved, so there was no final hinted unit to smoke-test.
- **Negative control** (`negctl/`: the stand-in with `__dxc_wait(c.tile[5]);` removed, run 3's 155
  hints):
  - WP reported the hazard checks as `[ Partial ]`, that is, not proven. It never reported refuted
    (no `Invalid` status).
  - The control cannot tell the two variants apart yet. The positive run's hazard checks were also
    `Partial`, resting on the same unproven hint assertions. The control means something only once
    the positive unit proves.
- **Solver portfolio:**
  - Alt-Ergo, Z3 and CVC5 all ran on every goal Qed did not close. A probe showed 3 prover calls per
    failed goal; for timeouts, `-wp-report-json` records only the last prover.
  - In run 3's hinted run, Z3 alone closed 23 goals and CVC5 alone 14.
- **Workspace:**
  - Each Codex call got, inline in the prompt: the stand-in with anchors (read only); the three
    headers (summaries, models, postcondition definitions); the C++ unit
    `library/dx100/bfs_read_offload.inc`; the failing goals with kind and failure class; the last
    hint set; and every earlier rejected set with its reasons.
  - Codex never got tests, negative controls, the evaluator, workload inputs or other candidates.
  - Pin: `gpt-5.6-sol`, effort `xhigh`, from `PINS["codex"]` in `swdb/provider_adapters.py`. Codex CLI
    0.153.0.

### Assumptions (not decided in the map)

- Assumption: the 60-minute budget starts at the first Codex call. Map 13 item 3 runs WP without
  hints before the loop; that run (15.3 min) is recorded on its own.
- Assumption: time spent waiting for the machine-wide verifier lock (other tickets' jobs) is
  excluded from the budget and recorded per run.
- Assumption: ADR 0006's Mac exception is met by Codex's own sandbox (`-s read-only`) with **shell
  tools disabled** and the workspace inline.
  - Sessions: `--ephemeral` in run 1; kept sessions for repair turns in runs 2 and 3.
  - Why no shell: Codex's macOS sandbox does not restrict reads, so a shell tool could have read the
    negative controls in the repository.
  - Cost: Codex cannot run the hint check inside its call (map 13 item 6); the repair turns emulate
    that.
- Assumption: memory safety (`-wp-rte`, including the shared queue's capacity) is outside "proven"
  here. This matches the ticket's assumption that proven means the unit postcondition plus the
  hazard checks. Summary and model preconditions, such as `\valid_read` of gathered bases, are still
  goals.
- Assumption: the throwaway wait rule is the library's: a wait covers its producer and that
  producer's transitive dependencies. It is stricter than gem5's rule (research 14), so a hazard
  proven absent here is also absent under gem5. The range-loop summary follows the strict layer's
  continuation encoding and requires stride 1.
- Assumption: lowering choices for the hand stand-in (ticket 21 owns the real ones):
  - a `const T&` scalar is passed by value;
  - `operator new[]` for the `QueueBuffer` returns a per-thread storage block, because WP does not
    implement `\fresh` ("Allocation … not yet implemented");
  - `omp_get_thread_num()` is a model that returns 0.
- Assumption: verdicts live in this Answer, not in `proof` records. Spike code is in
  `prototype/07-wp-hints/`. Runs are in `/tmp/claude/probata-runs/t07/`; its `README.md` holds the
  LR-06 record (budget 2 GB, 8.5 MB used; readers: this Answer and ticket 09).

### Side findings

- **`verifier_run.py` has two defects.** Reported to the main session; not changed here.
  - On SIGTERM, the wrapper's `finally` frees the lock while the job tree keeps running. This
    happened once in t07's dev run: orphaned Frama-C and Why3 processes ran beside a t08 job until
    killed by hand.
  - The lock has no fairness. A waiter polls every 2 s with no queue. t07's 0.5-second parse job
    waited 75 minutes (06:52–08:07 ET) while t06 started SAW jobs back to back.
- WP prints "Memory model hypotheses" for summaries: separation assumptions it adds without a goal.
  The proof setup check (ticket 36) should list or check them (`-wp-check-memory-model`).
- WP accepts an infinite range (`a[i ..]`) in a function's `assigns`, but aborts on one in a
  `loop assigns` ("Invalid infinite range").
- One hinted WP run peaked at 6.4 GB RSS at `-wp-par 12`, close to the 8 GB watchdog.

### Evidence (Mac, `/tmp/claude/probata-runs/t07/`)

| File | sha256 |
|---|---|
| `counted-1/round-0/wp-smoke.log` (no-hint run) | `11b4c12c8b0519e312ffa2e8bb653cbe9f612b768c6147b9822e93bc538bc6f8` |
| `counted-1/round-0/goals.json` | `fb7a6ea5664bdc6351db0d81e9fe84b46fbbc0c0dbb87f2a0d7b4f2c8cce3721` |
| `counted-1/round-0/per_goal.tsv` | `425f1f11dd20cfebaaa7b9aacb2b63c929c585f6cee893cae397fae628f56997` |
| `counted-1/history.json` (run 1) | `912b0d24ea34cd246a79012052c56260b055118911fe1c17866e979bedc567a8` |
| `counted-1/summary.json` | `2428293344cca2b4dd3e22a25af935b20ebad93fdca9a09127c48a261d5acc61` |
| `counted-3/history.json` (run 3) | `0945d2b3f697b56d4332d3ff4a1cafb0d829ab104ef411149bad0c9466af7b24` |
| `counted-3/summary.json` | `42bc335cf7fe4052983bd704703bf10aba19e5a201498866ddeaa7eb11d1af82` |
| `counted-3/round-1-turn2/wp-smoke.log` (hinted run) | `9b1d7e9fa9bac04537d1468b97d5334d1fe10a589ca34e9436cf3375b6879a4a` |
| `counted-3/round-1-turn2/goals.json` | `244a77ea4047a7c6aa6c243553f540755bd21d0b21788f9949d49fbec2852224` |
| `negctl/hints_run3_round1.json` | `6d26f925578b272bbf6067ff69cbcb904ffa643a0bc4a32c7ea94b59f2c906ac` |
| `negctl/only-run/wp.log` | `55bc1b64e09dca78e698067a2ddcd9a638fd549355f0de82c639bfa7abe6aa2a` |
| `negctl/only-run/goals.json` | `8183ad7f6ce9a323f4f2c81e9b37302aedcf397ee0e948994abfaf84a48d2e29` |
| `heartbeat.md` (LR-07 status table) | `2be6a0d1424433b31c92e1614fa1a1351afbb9c751cbb9c3861695677029e8c5` |

Harness hashes: run 1's `loop.py` `4f4b8812…6cae` (snapshot `loop_run1_snapshot.py`); run 3's
`loop.py` `06ef99e3…6116` and `hints.py` `0e65d390…ed0e`. `test_hints.py`: 11 passed. Stand-in
headers: `gapbs_models.h` `401d8ccf…3eed3e`, `bfs_unit.h` `1bcbf4da…f7b235`.

**What a pass would need (input to 09, not a decision):** a budget that fits several WP passes, or
WP rerun on only the goals a round touched; or an agent that runs the parse and goal-generation
checks itself inside one call, as map 13 item 6 allows on mbit10 under Landlock. No uncounted
continuation was run, so it is not known whether run 3's 99 open goals can be closed at all.

## Continuation inside the box (2026-10-14 09:20 ET, main session)

Reopened. Ticket 09 found (c) is "fail so far": this ticket's own assumption says a counted run fails
only "when the box ends", and A1's 2-week box runs to about 2026-10-27 ET. So (c) continues inside the
box, with every earlier counted run kept in the record. Each method change made here is recorded as one
(it belongs in the method version), and each new counted run is reported, pass or fail.
