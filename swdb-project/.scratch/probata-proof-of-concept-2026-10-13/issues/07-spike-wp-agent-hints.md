# 07 — Spike (c): WP with agent hints

Created: 2026-10-13 22:17 ET
Updated: 2026-10-15 ET (run 16 not proven; 4 unit and 22 hint obligations remain; final offline audit recorded); 2026-10-14 22:50 ET (continuation 3: runs 10-12 fail, verdict fail so far, effort paused); 2026-10-14 17:10 ET (continuation 2: runs 7-9 fail, verdict fail so far); 2026-10-14 12:35 ET (continuation: runs 4-6 fail, verdict fail so far); 2026-10-14 08:45 ET (resolved: spike verdict fail); 2026-10-13 23:15 ET (review fixes)
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

### Continuation results (2026-10-14 12:35 ET, branch `probata-poc/t07c`)

**Verdict: fail so far.** Three more counted runs (4, 5, 6), all failed. The best one ended with 50
goals open. No hint set reached the fresh full replay, so no run met the pass bar. The bar and budget
did not change. The box is still open (about 2026-10-27 ET). All numbers are Mac results (host `mac`).

**Biggest finding: the stand-in could not be proven in runs 1-5.**

- WP 33 cannot prove any write into an infinite `assigns` range. Even a single direct write
  `q->shared[q->shared_in] = 1` under `assigns q->shared[q->shared_in ..]` times out with all three
  provers (`dev/assigns-probe/p.c`, variant D).
- TDStep's contract had `assigns ... queue->shared[queue->shared_in ..]`, so its function-assigns goals
  for the queue writes were unprovable whatever the hints.
- Stand-in fix before run 6: the range is now `[queue->shared_in .. 2^65 - 1]`. That bound lies above
  every index the queue can write (a `size_t` `shared_in` plus at most 16384 buffered entries), so the
  frame is unchanged for every index the code can reach.
- A probe with the same `push_back` contract proves every frame goal under the new bound
  (`dev/assigns-probe/q.c`, 22 of 24 goals). The 2 open goals are separation preconditions of the
  probe's own harness.

#### Every counted run (continuation)

Every run started with no hints in a fresh Codex session. All runs used Codex `gpt-5.6-sol` `xhigh`
(the `PINS["codex"]` pin), Codex CLI 0.153.0, shell off, `-s read-only`, workspace inline. None reached
the final replay.

| Run | Folder | Method | Rounds / Codex calls | Budget-min | Lock wait excluded | Best open goals (round mode, 10 s) | Outcome |
|---|---|---|---|---|---|---|---|
| 4 | `t07c/counted-4/` | (a)(b)(c) + one Codex session | 10 / 11 | 59.85 | 6.0 min | 11, but only under an unproven `assert !accelerate`; 95 in round 1 | **fail**: 10-round cap, 0 final replays |
| 5 | `t07c/counted-5/` | + (d) in-call tool, (e) context feedback | 8 / 8 (19 tool calls, 6 WP) | 60.99 | 0.2 min | 50 | **fail**: budget spent, 0 final replays |
| 6 | `t07c/counted-6/` | + stand-in fix, corrected loop-assigns example | 10 / 10 (17 tool calls, 7 WP) | 47.28 | 1.3 min | 51 | **fail**: 10-round cap, 0 final replays |

- Runs 4 and 5 reused run 1's no-hint run (same stand-in hashes; `goals.json` hash checked). Run 6
  had its own no-hint run on the fixed stand-in: 15.3 min, 3.6 GB. It left 105 goals open, all
  timeouts, and passed 139 of 139 smoke tests.
- Tokens:
  - Run 4: input 1,960,417 (1,745,664 cached), output 109,357.
  - Run 5: input 6,612,808 (5,831,808 cached), output 64,961.
  - Run 6: input 13,123,849 (12,812,160 cached), output 50,548.
- Peak WP RSS was 3.5 GB (round mode). The highest in-call WP run reached 3.2 GB. The 8 GB watchdog
  never fired.
- Hint rules held in every run:
  - The vocabulary check rejected 0 sets, so 0 escape-hatch attempts.
  - Every hint has Codex provenance (round, turn or tool call). The implementing agent wrote none.
  - Last sets: run 4, 47 hints; run 5, 45; run 6, 26.
- Not run: the negative control and the final-unit smoke tests. Both need a proven unit.
- Uncounted runs: `dev/tool-plumbing/` used effort `low` to test the harness and is not a hint run.
  The diagnostics in `dev/` re-ran recorded Codex sets on probes. None of them fed a counted run.

#### Method changes, each with its reason (they belong in the method version)

| # | Change | Since | Reason |
|---|---|---|---|
| a | Hint rounds run WP only on TDStep's goals and the lemmas, with no smoke tests, 10 s per prover and a run-local cache (`wp_run.sh round`). Only a set that proves everything there gets one fresh full replay (`wp-smoke`: all functions, 30 s, `-wp-cache none`), and only that replay is the verdict. | run 4 | One no-hint round takes 260 s instead of 905 s. |
| b | Prompt adds two files: `examples/acsl_examples.c`, a CSR frontier traversal (generic, not BFS) that WP proves in full with its smoke tests passing, and `examples/frama_c_errors.txt`, which lists the 6 Frama-C/WP errors runs 1-3 hit and their fixes. | run 4 | Frama-C rejected every first attempt in runs 1-3. In runs 4-6 the vocabulary check rejected no set. In run 4, round 1 still needed 1 repair turn for a syntax slip. |
| b' | Error 5's loop-assigns advice was corrected: use the function's own finite bound as the end of the range. | run 6 | The run 4-5 example (`a[0 .. 1073741823]`) led to frame goals that could not be proven. |
| c | Open goals are fed back with kind, merged-file line, source line and the hint that holds them. | run 4 | Codex could not tell which hint a goal belonged to. |
| — | One Codex session (`exec resume`) for the whole run; later rounds send only the feedback. | run 4 | Rounds 2+ no longer resend the roughly 75 KB workspace. |
| d | An in-call check tool (map 13 item 6), given to Codex as an MCP server, with the shell still off. `check_hints` runs the proof hint check. `prove_hints` runs the check, then round-mode WP. Codex is stopped 15 min before the budget ends, which keeps time for the final replay. | run 5 | Run-3 rounds were mostly round trips (Codex alone took 8-15 min per call). The tool sees only the stand-in, so confinement does not change. |
| e | A context note in the prompt, and REGRESSION marks on goals the no-hint run had proven. | run 5 | In run 4, Codex's hints made trivial goals time out (below). |
| — | A set identical to one already run reuses that round-mode run. | run 6 | In run 5, rounds 3-6 re-proved the same set (2.6 min each). |

On "seed hints for the CSR loop invariants": a counted run must have no hints from the implementing
agent. So the seeds went in only as prompt examples on a different function (change b). No hint was
placed in the stand-in.

#### What blocks a pass now (largest first)

1. **Codex does not converge on this unit within one budget.** With the tool, open goals per WP
   attempt went:
   - run 5: 58 → 50 → 71 → 87 → 74 → 56;
   - run 6: 51 → 55 → 69 → 70 → 95 → 74 → 67.

   Codex rewrites large parts of each set, and its first set is often its best. After the in-call
   budget ran out, Codex returned the same set every round. The 10-round cap ended runs 4 and 6.
2. **Hypothesis load.** Trivial goals time out once hints are added.
   - Example: the call precondition `dxc_reg_ok(c.reg[2])` is proven in 0.03 s with no hints. With
     run 4's hints it times out with all three provers.
   - The cause is two asserted predicate towers above that goal, not the lemmas: removing the 5 lemmas
     left the goal open (`dev/diag-nolemma/`).
   - The frame goals hit the same wall. In TDStep, the loop-assigns goals for the 2-D ghost ranges
     `dxc_dep[0..7][0..7]` and `dxc_tile_data[0..7][0..TILE_SIZE-1]` time out. The same ranges prove at
     once in a small probe (`dev/assigns-probe/r.c`, 25 of 25).
   - In run 6's best set, 34 of the 51 open goals are `assigns` or `loop assigns`. 9 are the
     postconditions.
3. **Cost per attempt.** A WP attempt takes 3-6.5 min in round mode, so about 7 attempts fit in one
   budget.

#### Other findings

- **Correction to ticket 09:** smoke tests do not "pass by timing out at 30 s". They use WP's
  `-wp-smoke-timeout`, which defaults to 2 s; `wp_run.sh` leaves it at that default. So they cost
  little. The cost of a pass is the real goals that time out: about 90 CPU-s each at 30 s, with
  3 provers.
- An unproven assertion still serves as a hypothesis for later goals. Run 4's rounds 4-10 got down to
  11 open goals only "under" `assert !accelerate` (Codex was testing whether the static
  `swdb_acceleration_enabled` is zero). Such a set can never pass the replay. Since run 5 the prompt
  says so.
- Codex calls MCP tools with the shell disabled: a probe could not read `/etc/hosts`. Its attempt to
  use MCP `resources/read` is refused by the server.

#### Assumptions (not decided in the map)

- Assumption: making the stand-in's infinite `assigns` range finite (bound 2^65 - 1) is a stand-in
  fix, which this ticket allows between runs, and not a change of the unit's contract. The frame is
  the same for every index a `size_t`-indexed queue can reach.
- Assumption: Codex's tool calls inside one provider call are not provider calls. Map 13 item 11
  counts 10 rounds of one provider call each. Item 6 lets the agent run the frozen wrapper inside a
  call.
- Assumption: the 15-minute reserve for the final replay is part of the 60-minute budget, not added
  to it.

#### Next levers (input to the re-plan; none was run)

- Let the vocabulary allow WP's `Wp.filter`/`Wp.clear` tactics through `\wp::strategy` hints, so a
  hint can prune hypotheses. The hint check now rejects the token `for`, which strategy attachment
  may need, so check that first.
- Keep the best set and require changes to it to be small (diff-limited rounds). That would stop the
  oscillation.
- Split the unit's proof into per-loop lemmas or functions. That needs ticket 21's lowering, not hints.
- Run on mbit10 inside a lane with more provers in parallel. That shortens each attempt but does not
  fix 1 or 2.

#### Evidence (Mac, `/tmp/claude/probata-runs/t07c/`, 61 MB; LR-06 record in `README.md`)

| File | sha256 |
|---|---|
| `counted-4/history.json` | `c51fd046059032e74f9169a6b6b0e2d601f66dba2abd783e1ced00fea6f3b152` |
| `counted-4/summary.json` | `a95a2b3406454307d01ef31552ad6d96468a216381e79f12c69473b2962c63d1` |
| `counted-5/history.json` | `268f6219b626897773d71197151fe2498476b9bb47f905ef362dfcef16ce9535` |
| `counted-5/summary.json` | `fe45abf66a9705e41854cca6a7f9a893eac404fd29c354a37c666ad39a623bfa` |
| `counted-6/history.json` | `7957e3a82a53982036ff3685315a9d41c14b0bccbb261f037b22444f8df90d2c` |
| `counted-6/summary.json` | `a8952cc2b536a639697f0068d441dcdab5b1d0923440e5f55d7aa1fdb5723105` |
| `counted-6/round-0/goals.json` (no-hint run, fixed stand-in) | `2ad8c9a9e518acea56a7892a24bb1a58f4a52858415af00b360b0770eea4b3be` |
| `counted-6/round-0/wp-smoke.log` | `a4cf174702cefb73e0c18274653a068d15ba113e68c35d54f21fe6112c2f5878` |
| `dev/assigns-probe/run.log` (infinite-range probe) | `f07a3feaca4d7621b9764aeffd62c3673ae3772e8e7ae9e947a075ef64a284cb` |
| `dev/assigns-probe/runq.log` (fixed-bound probe) | `fe2eb77abdc7a72d02affc9724ef10a48cc04e505fd1f6ffc95535863dad963d` |
| `dev/diag-nolemma/goals.json` (context diagnosis) | `a9ab0b8303923def01a91057ce3e651beb4ee7704f411b2adba0ab7866747d1c` |
| `dev/cal-nohint/goals.json` (round-mode calibration) | `c5eda81478f93384c24cdc1e8b8a8a369d15e75ba621f8f38c9ad6796bf86c6b` |

- Stand-in after the fix: `standin/tdstep_standin.c`, sha256
  `4228c0c19bf250ac6a20726ac35425c4b7e4a2a2c45dc6892d19d1094f44a0e8`. The headers are unchanged.
- Harness hashes per run are in each `meta.json`: `loop_sha256`, `tool_sha256`, `wp_run_sha256` and
  `examples_sha256`.
- Tests: `test_hints.py` and `test_loop_tool.py`, 15 passed. The heartbeat table is in
  `heartbeat.md`.

## Continuation 2 results (2026-10-14 17:10 ET, branch `probata-poc/t07d`)

**Verdict: fail so far.** Three more counted runs (7, 8, 9), all failed: no best set reached 0 open
goals in round mode, so no run reached the fresh full replay. The pass bar and the 60-minute budget did
not change. The box is still open (about 2026-10-27 ET). All numbers are Mac results (host `mac`).

**What changed, in one line each:**

- The three requested method changes work as mechanisms. Open goals now fall monotonically instead of
  oscillating (run 6: 51 → 95 → 67; runs 7-9: never worse than the best so far).
- The frame-goal wall is gone. It was mostly a WP encoding problem, not a hint problem (below).
- What still blocks a pass: closing the agent's own invariants and asserts (run 9 ends with 3 unit
  goals open but 26 hint goals open) and WP attempts per budget (7-18 per run).

### Biggest finding: the frame goals were a 2-D ghost array, not missing hints

- Dev diagnosis (`dev/goalprint/print.log`, `dev/goals_summary.py`): 23 of the open frame goals had
  the same shape. Each `dxc_dep[0 .. 7][0 .. 7]` range in an `assigns` or `loop assigns` became an
  existential goal (`exists i, j. i = a /\ j = b /\ 0 <= i <= 7 ...`). Qed does not close it, and the
  provers time out on it in TDStep's large context.
- Frama-C rejects the whole array as an `assigns` location ("not an assignable left value").
- **Stand-in fix** (allowed between runs; same frame and same semantics): the ghost array is now 1-D,
  `dxc_dep[DXC_NUM_TILES * DXC_NUM_TILES]`, read as `dxc_dep[x * DXC_NUM_TILES + y]` in
  `standin/dxc_summaries.h`. TDStep's `assigns` names `dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1]`.
- Effect, before any Codex call (round mode, 10 s, frame seeds in):

  | Stand-in | Open goals | Open frame goals |
  |---|---|---|
  | 2-D `dxc_dep` (`dev/dev-seeds-only`) | 63 of 216 | 34 |
  | 1-D `dxc_dep` (`dev/dev-seeds3-only`) | 39 of 209 | 12 |

  The 12 frame goals left need value ranges, such as `0 <= v < num_nodes` for `parent->start_[v]`.
  Those are invariants, so they are Codex's job.
- The no-hint run on the fixed stand-in (counted-7 round 0, frozen flags, 30 s): 103 goals open, all
  timeouts. 139 of 139 smoke tests passed. 14.8 min, 3.7 GB.

### Every counted run (continuation 2)

Common to all three runs:
- Each run started with no agent hints, in a fresh Codex session.
- Codex `gpt-5.6-sol` `xhigh` (`PINS["codex"]`), CLI 0.153.0. Shell off, `-s read-only`, workspace
  inline, and the in-call MCP tool only.
- The fixed stand-in and frozen flags. Round mode at 10 s.
- Runs 8 and 9 reused run 7's no-hint run (stand-in hashes checked).

| Run | Folder | Method | Codex calls / WP attempts | Budget-min | Lock wait excluded | Best set: open goals (unit + hint) | Outcome |
|---|---|---|---|---|---|---|---|
| 7 | `t07d/counted-7/` | (a) total-count acceptance, (b) seeds, (c) strategies | 2 / 18 | 44.65 | 10.6 min | 22 (15 + 7); 8 of 9 `ensures` open | **fail**: in-call budget spent, 0 final replays |
| 8 | `t07d/counted-8/` | + (a') unit-first acceptance, hint cap 15, 8-min replay reserve | 2 / 13 | 52.16 | 7.4 min | 17 (7 + 10); 4 `ensures` open | **fail**: in-call budget spent, 0 final replays |
| 9 | `t07d/counted-9/` | + hint cap 30 | 2 / 8 | 52.19 | 45.0 min | 29 (3 + 26); 0 `ensures` open | **fail**: in-call budget spent, 0 final replays |

- Trajectories of the best set's open goals (`attempts.py` on each run):
  - run 7: 38 → 38 → 29 → 29 → 24 → 24 → 23 → 22 (5 edits reverted);
  - run 8: 38 → 35 → 27 → 22 → 21 → 17 → 16 → 16 → 17 (3 reverted). Unit goals fell 38 → 7.
  - run 9: 38 → 34 → 27 → 27 → 29 → 29 → 29. Unit goals fell 38 → 3.
- Unit goals in run 9's best set: the frame goals `assigns_normal_part16` and `assigns_exit_part53`
  (the queue flush), and one gather precondition (`call___dxc_gather_5 requires_3`). Every `ensures`
  and every hazard check is proven in round mode, but only "under" 26 unproven hint goals. So run 9
  is no closer to a pass than run 8; it moved the open work into the agent's own hints.
- Tokens are lower bounds. When the in-call deadline stopped Codex (round 1 of every run), it emitted
  no `turn.completed` event. Recorded totals:
  - run 7: input 1,381,258 (1,292,032 cached), output 2,476;
  - run 8: input 1,000,100 (960,896 cached), output 1,218;
  - run 9: input 787,812 (725,376 cached), output 772.
- Peak WP RSS 3.7 GB (no-hint run). The 8 GB watchdog never fired.
- Hint rules held in every run:
  - 0 vocabulary rejections, so 0 escape-hatch attempts. 5 edits were rejected: 1 by the edit rules
    (a goal not open, run 7) and 4 by the Frama-C parse or goal-generation check (runs 8-9).
  - Every agent hint has Codex provenance (round and tool call). The frame seeds have provenance
    `seed: frame_seeds.py`. The implementing agent wrote no hint in a counted run.
- Not run: the negative control and the final-unit smoke tests. Both need a proven unit.
- **Run 9 confound:** the machine-wide verifier queue was crowded (up to 9 waiting jobs from other
  tickets). The excluded lock wait was 45 min.
  - `verifier_run.py` waits are excluded from the budget, but the Codex call deadline is wall-clock.
    So Codex was stopped at 43.6 budget-min with 8 in-call minutes still unused.
  - One `check_edit` waited 35 min in the queue, and Codex sat idle behind it.
  - Fix for the next run: give the Codex call a budget-clock deadline, extended by measured lock waits.

### Method changes, each with its reason (they belong in the method version)

| # | Change | Since | Reason |
|---|---|---|---|
| a | **Monotone, local editing.** The loop keeps one best set (`best.json`). Codex never returns a set, only edits: at most 8 operations (`add` / `delete` / `edit`) and 6,000 characters, each naming an open goal it targets. Through the in-call tool, `propose_edit` runs the check and round-mode WP on best set + edit. An edit that raises the open-goal count is reverted. The final JSON answer is one more edit. | run 7 | Run 6: Codex rewrote its whole set each attempt (51 → 95 → 67). |
| a' | **Unit-first acceptance.** Goals of the stand-in ("unit goals": postcondition, hazard checks, call preconditions, frames incl. seed frames, termination) count first. An edit is kept if it lowers the open unit goals, or keeps them and does not raise the total. Open goals inside the agent's own hints may rise, up to a cap (15 in run 8, 30 in run 9). | run 8 | In run 7, every one of the 5 reverted edits lowered the unit goals (for example 25 → 22, 18 → 16) but added more open invariant goals. The total count punished the necessary step of adding a not-yet-inductive invariant. |
| — | Final-replay reserve 15 → 8 min | run 8 | Run 7 never used its reserve. A set that proves everything at 10 s replays in a few minutes. |
| — | Hint cap 15 → 30 | run 9 | Run 8's edit #20 lowered the unit goals 8 → 7 but was reverted only because hint goals hit 21 > 15. |
| b | **Deterministic frame seeds** (`frame_seeds.py`). Before the first Codex call, a syntactic write-set pass writes every loop's `loop assigns`. It reads clang's JSON AST plus the callees' ACSL `assigns`, substitutes the actual arguments, resolves pure getters (`ensures \result == E`), drops block-scoped locals, applies alias facts from constructor `ensures`, and widens loop-varying indices to the function frame's range at `Pre`. Nothing is BFS-specific. WP checks the seeds in a seed round (2.6 min, counted in the budget). Codex may not edit them or add `loop assigns`. | run 7 | 34 of run 6's best set's 51 open goals were frame goals. |
| c | **Strategy hints.** New vocabulary: `\wp::strategy` plus its `\wp::proof` attachment. Tactics are limited to WP's own (Wp.filter, clear, split, unfold, instance, lemma, range, cut, separated, array, compound). `\prover` takes names only, with no time argument. No `\auto`; never on smoke tests. WP runs with the strategy engine (`wp_run.sh round-s` / `wp-smoke-s`: `-wp-prover tip,alt-ergo,z3,cvc5 -wp-script dry`, fresh session, no script saved or reused). | run 7 | Hints added hypotheses that made trivial goals time out (t07c finding 2). |

On (c)'s effect, measured:
- Codex used strategies in every run: run 7 issued 18 `strategy` and 10 `proof` operations, and the
  final sets hold 4-8 strategy hints (`Wp.filter`, `Wp.instance` on `@requires`/`@assert`/`@invariant`
  goals).
- In run 8's best set, WP reports 1 goal proven by a script (40 tactic steps).
- A generic `Wp.filter` seed on all `@assigns` goals (dev only) helped on the 2-D stand-in: 63 → 52
  open. On the fixed stand-in it changed nothing (39 vs 39 open) and cost 105 s more per WP run, so it
  was not used in counted runs.
- So (c) works as a mechanism, but it was not what limited these runs.

### Bug fixes (harness, not method)

- The merger orders loop clauses: invariants, then `loop assigns`, then `loop variant`. Frama-C
  rejects an invariant after a variant, and seeds come before agent hints.
- The verdict reader skips `strategy`/`proof` entries of `-report`. WP lists them with status `-`, so
  any set with a strategy hint could never have passed the replay. Found by reading run 8's log; no
  replay ran, so no verdict changed. Test: `test_verdict_reader_skips_strategy_directives...`.

### Uncounted (DEV) runs, all in `t07d/dev/`

- `dev-seeds-only`, `dev-seeds-filter`, `dev-seeds3-only`, `dev-seeds3-filter`: WP on seeds alone, with
  and without the filter seed, before and after the stand-in fix. No agent hints.
- `goalprint`: `-wp-print` of TDStep's frame goals, for the diagnosis above.
- `plumbing`: edit loop at Codex effort `low`, 22-minute budget, no no-hint run. Mechanics check only:
  accept 39 → 31, a revert 31 → 35, and the budget stop.
- No hint written by the implementing agent entered a counted run. The only hints written by the
  implementing agent were the dev filter-strategy probe (`seeds_strat.json`).

### Assumptions (not decided in the map)

- Assumption: frame seeds are part of the method (map 13 items 3 and 9: seeds before the first
  provider call). They are not agent hints, and the implementing agent did not write them: a
  deterministic program did. The seed round counts in the 60-minute budget.
- Assumption: a `\wp::strategy` hint needs its `\wp::proof` attachment to act, so the attachment is part
  of map 13 item 5's allowed "`\wp::strategy` tactic hints". `-wp-prover tip` with `-wp-script dry` and
  a fresh session reuses no script, so the verdict flags of item 7 still hold.
- Assumption: flattening the 2-D ghost array is a stand-in/summary fix, which this ticket allows
  between runs. Same state, same frame, same predicates.
- Assumption: as in t07c, in-call tool calls are not provider calls, and the replay reserve is inside
  the 60 minutes.

### What a pass would need now (input to ticket 09; none was run)

- **A budget-clock deadline for Codex**, extended by measured lock waits, or a dedicated verifier lane.
  Run 9 lost 8 in-call minutes to the wall clock.
- **More WP attempts per budget.** Each attempt costs 1-5 min (parse, goal generation, WP). Rerunning
  only goals whose context changed, or mbit10 in a lane with more provers in parallel, would give more
  than 7-18 attempts.
- **Close the agent's own hint goals.** Run 9 proves every `ensures` under 26 unproven invariants and
  asserts. A follow-up phase that lets only hint-goal edits through (unit goals fixed) is the natural
  next lever.

### What A3 (tickets 34-37) should adopt

- **34 (role/workspace):** an edit protocol, not whole sets: ops tied to open goals, a size limit, and
  the in-call tool (`check_edit` / `propose_edit` / `show_best`). Report open goals as unit vs hint.
- **35 (hint records, merger, check):**
  - add `proof` (attachment) to the strategy kind, with the narrow strategy vocabulary in
    `hints.strategy_problems`;
  - order loop clauses in the merger;
  - treat seed hints as fixed records with provenance `seed`.
- **36 (setup check / verdict reading):** skip `strategy`/`proof` directives in `-report` (status `-`).
  Flag 2-D ghost-array ranges in `assigns` as a known WP cost. Summaries (ticket 30) should keep ghost
  state 1-D.
- **37 (the loop):**
  - deterministic frame seeds before round 1 (the `frame_seeds.py` rules; ticket 21's lowering should
    emit them from its AST);
  - monotone best set with unit-first acceptance and a hint-goal cap;
  - a budget-clock deadline for provider calls;
  - a hint-goal-only closing phase.

### Evidence (Mac, `/tmp/claude/probata-runs/t07d/`, 52 MB; LR-06 record in `README.md`)

| File | sha256 |
|---|---|
| `counted-7/round-0/goals.json` (no-hint run, fixed stand-in) | `a437410a72ceb9ac3373182e93ba2e14766cc84911273391018a6e004b800709` |
| `counted-7/round-0/wp-smoke.log` | `9ddb842acb1eb6a5f94583d7c3b87fa0781fbb232fa6ad5b143b7f25a0cf7c61` |
| `counted-7/history.json` | `9564e5b7fd5626d71e300cd57c3a65ae0ef3aa1f417261deb1ebc1c3d71d9611` |
| `counted-7/summary.json` | `4160d40a67a2cbda26dd28d69fe1f2078d7a7ffcce77bc9fc8d1570b5240ea3a` |
| `counted-7/best.json` | `118206c84fc75044d8def1cc4714ca24454d6ba26e44e76fee21fc97d3caa1cd` |
| `counted-8/history.json` | `5d12ad389cddbff64c5aa950a68dad8f05f1096c7b13f56522ba80e98f239e07` |
| `counted-8/summary.json` | `60809d82e26f2c05719397b0466c3fbca03cb96e48c26687f3f92ded30a27eb6` |
| `counted-8/best.json` | `53559a4cfde19dc7cf2dd37c62de1e970f8b1e0c4dac18d3c4e13c0b881fefd5` |
| `counted-9/history.json` | `9b0bf828e9fd0b72e4f7df642fcc9969fba840af856d3a91a5ebe4037808e65c` |
| `counted-9/summary.json` | `a88fdec2f48084397044e6639ccdaebe4887cfc49fa2a445c10673c6d17fd1e3` |
| `counted-9/best.json` | `9308f1f967198519c299ddd229ca5ffa9dbfcaa82c88cd31c580647655da27d2` |
| `dev/dev-seeds-only/goals.json` (2-D, seeds) | `c3996ed2792de4327e1ac1397dcb3038d329d9818d7debffce59df35d4b3e38c` |
| `dev/dev-seeds-filter/goals.json` (2-D, seeds + filter) | `30df1b8a60964d8a1c4ac8be720f2caeaee1ac5dac603fe9a6be0bebe9f03c5c` |
| `dev/dev-seeds3-only/goals.json` (1-D, seeds) | `43e012918ac6d6fe17793560e14d19977d27c526e715b7b1a07490cd17e58dd4` |
| `dev/dev-seeds3-filter/goals.json` (1-D, seeds + filter) | `946dd3b3b6a0f2de4e61afe0db493028ae70656a81e91e024bd8ad976ccdf6f6` |
| `dev/goalprint/print.log` (frame-goal diagnosis) | `9fd2178354b823ea36a2e15cc0d5aab25cf48bac6872d5b6c813f98e8ca3dfe8` |
| `dev/plumbing/summary.json` | `b852289bae1d2569d6d97b8bd762ea5b529755eb40ba3d097ee553f4b03e78a5` |
| `heartbeat.md` (LR-07 table, 30-min cadence) | `f6e3c66ae15ad553222b4fdfb3cae782ccf805ad0aeff6a5b092212cbb6e324b` |

- Stand-in after the fix: `standin/tdstep_standin.c` `d5d599e4…40f8`, `standin/dxc_summaries.h`
  `d708c0ef…e0d2`. The other headers are unchanged.
- Harness hashes per run are in each `meta.json` (`harness_sha256`). Harness commits: `7af4b56a`
  (run 7), `0642d575` (run 8), `a1053ffb` (run 9).
- Tests: `test_edit_loop.py`, `test_hints.py` and `test_loop_tool.py`, 21 passed.
- Analysis scripts (not in the repo): `attempts.py` (unit/hint split per attempt), `strat_use.py`,
  `peek.py`.

## Continuation 3 results (2026-10-14 22:50 ET, branch `probata-poc/t07e`)

**Verdict: fail so far.** Three more counted runs (10, 11, 12), all failed. No best set reached 0 open
goals in round mode, so no run reached the fresh full replay. The pass bar and the 60-minute budget did
not change. Status stays `claimed`: the A1 box runs to about 2026-10-27 ET. Yan-Ru paused the effort
after run 12. All numbers are Mac results (host `mac`).

**In one line each:**

- Closest yet: runs 10 and 12 proved **every unit goal** (all 9 `ensures`, the hazard checks, frames,
  call preconditions, termination) in round mode. 9 and 17 goals of Codex's own hints stayed open.
- The budget-clock deadline worked. Codex used its full in-call budget in every run, despite 47-56
  minutes of excluded lock wait per run.
- What still blocks a pass: closing the agent's own hint goals. Phase 2 got only 4 WP attempts in
  run 10 and 1 in run 12 before the in-call budget ended.

### Every counted run (continuation 3)

Common to all three runs:
- Each run started with no agent hints, in a fresh Codex session: `gpt-5.6-sol` `xhigh`
  (`PINS["codex"]`), CLI 0.153.0. Shell off, `-s read-only`, workspace inline, in-call MCP tool only.
- Same stand-in as t07d (`tdstep_standin.c` `d5d599e4…40f8`, headers unchanged). Frozen flags.
  Round mode at 10 s. Frame seeds, strategies, unit-first acceptance, hint cap 30, 8-minute replay
  reserve.
- Each run reused run 7's no-hint run (stand-in hashes checked). The seed round left 38 of 209 goals
  open, at 2.6-2.7 budget-min.

| Run | Folder | Harness | Codex calls / WP attempts / show_goal | Budget-min | Lock wait excluded | Best set: open (unit + hint) | Phase at end | Outcome |
|---|---|---|---|---|---|---|---|---|
| 10 | `t07e/counted-10/` | (a)(b)(c1)(c2) | 1 / 12 / 11 (2 failed) | 51.75 | 56.0 min | **9 (0 + 9)** | 2 | **fail**: in-call budget spent, 0 final replays |
| 11 | `t07e/counted-11/` | + (c3), show_goal fix | 1 / 17 / 8 | 53.69 | 51.0 min | 20 (2 + 18) | 1 | **fail**: in-call budget spent, 0 final replays |
| 12 | `t07e/counted-12/` | same as run 11 | 1 / 10 / 6 | 54.07 | 46.7 min | 17 (0 + 17) | 2 | **fail**: budget-clock deadline, 0 final replays |

- Accepted-edit trajectories (open goals as unit + hint):
  - run 10: 38+0 → 26+7 → 16+9 → 6+11 → 3+13 → 2+11 → 0+11 (phase 2 at 30.7 budget-min) → 0+9.
    In phase 2, 3 edits were reverted: two closed hint goals but reopened unit goals (0 → 2 and 0 → 1);
    one raised the hint goals 11 → 12.
  - run 11: 38+0 → 33+3 → 16+8 → 11+15 → 7+17 → 4+19, then 9 neutral or near-neutral edits, and a
    final-answer edit to 2+18. It never reached phase 2.
  - run 12: 38+0 → 22+4 → 17+8 → 15+9 → 10+11 → 5+14 → 1+16 → 0+17 (phase 2 near 50 budget-min).
    The budget-clock deadline stopped Codex before a second phase-2 attempt.
- Run 10's 9 open hint goals: 5 loop invariants (2 established, 3 preserved; 3 with failure class
  `unknown`, which suggests not inductive as written), 3 asserts and 1 loop variant.
- Tokens:
  - run 10: input 10,334,878 (10,054,912 cached), output 24,653;
  - run 11: input 19,924,250 (19,565,952 cached), output 37,107;
  - run 12: not recorded. The deadline stopped Codex, so no `turn.completed` event was emitted.
- Peak WP RSS 4.0 GB (run 10). The 8 GB watchdog never fired.
- Hint rules:
  - Run 11's check rejected one attempt at a recursive definition (`recursive_definition`), so the
    escape-hatch count is 1. Runs 10 and 12 had 0.
  - Other rejections were Frama-C parse errors (runs 11 and 12) and one edit over the size limit
    (run 11). Every agent hint has Codex provenance; the frame seeds have provenance `seed`.
  - The implementing agent wrote no hint in a counted run.
- Not run: the negative control and the final-unit smoke tests. Both need a proven unit.

### Method changes, each with its reason (they belong in the method version)

| # | Change | Since | Reason |
|---|---|---|---|
| a | **Budget-clock Codex deadline.** The loop polls every 5 s and stops Codex once wall time minus every lock wait passes the in-call budget plus 2 minutes. That includes the in-call tool's wait in progress, which `loop.verifier` publishes live in `lockwait_live.json`. A 5-hour wall cap is only a guard. | run 10 | Run 9 lost about 8 in-call minutes: its deadline ran on the wall clock during 45 minutes of lock waits. |
| b | **Two-phase loop.** Phase 1 is run 9's method. Once the best set's unit goals reach 0, phase 2 accepts an edit only if every unit goal stays proven and the open hint goals do not rise. The tool, the open-goal list and the prompt announce the phase. The final fresh full replay stays reserved. | run 10 | The ticket asked for a hint-goal-only closing phase. Finding: at 0 unit goals, unit-first acceptance already is this monotone rule (tested). So what (b) adds is the phase signal to Codex, not a new acceptance rule. |
| c1 | **`show_goal(goal)` in-call tool.** It prints one open goal of the best set as WP generates it after Qed: hypotheses and conclusion, no prover, at most 14,000 characters (`goal_print.py`, `wp_run.sh print`). It reads only the merged stand-in. | run 10 | To close its own invariants, Codex must see why preservation fails. Until now it saw only the goal's name and line. Codex called it 6-11 times per run. |
| c2 | MCP tool timeout 3600 → 14400 s | run 10 | A tool call queued behind other tickets could exceed 60 minutes. Codex would then see an error while the tool kept running. |
| c3 | `propose_edit` reuses the folder of a `check_edit` that just passed for the same best set and ops. No second check runs. | run 11 | In run 10, 10 of 12 proposals repeated the check Codex had just run. Reuse fired 8 times in run 11. |

### Bug fixes (harness, not method)

- **Unit vs hint split.** A seed `loop assigns` merged into one block with agent invariants was counted
  as a hint goal. Seeds are method, so they now count as unit goals (`edit_core.is_hint_goal`).
  - Correction to continuation 2: run 9's best set was **5 unit + 24 hint**, not 3 + 26. Its 2 seed
    `loop assigns` goals were misclassified.
- **show_goal matching** (between runs 10 and 11):
  - call-site headers span two lines;
  - the normal and exit frame groups share headers;
  - `ensures` headers carry no line;
  - `@terminates` selects nothing in Frama-C 33.

  Run 10's 2 failed `show_goal` calls were of the last two kinds.

### Uncounted (DEV) runs, all in `t07e/dev/`

- `show-goal/`: `goal_print.show` on 4 goals of run 9's recorded best set, to check the goal matching.
- `mcp_smoke.py`: tool listing and phase text on a copy of run 9's best set.
- No hint entered a counted run from these.

### Assumptions (not decided in the map)

- Assumption: `show_goal` is part of map 13 item 6's in-call check wrapper. It reads only the merged
  stand-in and proves nothing, so confinement does not change. Its run time counts in the budget.
- Assumption: as in t07c/t07d, in-call tool calls are not provider calls, lock waits are excluded,
  and the replay reserve is inside the 60 minutes.

### What a pass would need now (input to ticket 09; none was run)

- **More WP attempts per budget.** Each attempt costs 2-6 minutes. Runs reach phase 2 only at
  30-50 budget-min, which leaves 1-4 phase-2 attempts. Options:
  - mbit10 in a lane with more provers in parallel;
  - rerunning only the goals whose context an edit changed.
- **Fewer, smaller agent invariants.** Phase 1 trades unit goals for hint goals: 0+9, 2+18, 0+17 at
  the end. Two run-10 edits closed hint goals but reopened unit goals. The unit goals depend on the
  hints, so the two counts cannot be minimized separately.
- **Note:** the shared verifier queue made one 60-minute budget take 1.7-1.8 hours of wall time.

**Next step:** when Yan-Ru resumes (box open to about 2026-10-27 ET), decide in ticket 09 whether (c)
gets a run with more WP attempts per budget (mbit10 lane, or goal-scoped reruns), or ends as fail.
Run 10 shows the unit postcondition can be proven under Codex hints in round mode. What is not shown is
closing the hints themselves within 60 minutes.

### Evidence (Mac, `/tmp/claude/probata-runs/t07e/`, 67 MB; LR-06 record in `README.md`)

| File | sha256 |
|---|---|
| `counted-10/history.json` | `b8bbe6085b6df5cf77768f9b27c6c7ffd8fa40e4152d50eb7dc1cd13c8c81f95` |
| `counted-10/summary.json` | `ef08abb23ab162cc5bf9d5963a8a7e481317ddbf7061878b45f2a032ad7682ae` |
| `counted-10/best.json` | `84cbc425cd4a9b4708b324ca025a3f59d39bccd8912aa5ce3a36f47603273394` |
| `counted-10/meta.json` | `53ef613ab81aed088dce86bafba27f2ffe780c71a4eabf17cea1e2707eefd209` |
| `counted-11/history.json` | `d557e66f08d0a90f609d65093bfb8320b59b1196abdcf1cd0a60bfa88aa5a891` |
| `counted-11/summary.json` | `1e327649d6cb3920e14a0c4e8c02fab1ec07f7337b170fe881fd39820452daef` |
| `counted-11/best.json` | `ca4934bd79f1b1d9871bb8332e34f4bdc5c27fdb549a7eb6499cf59407672eef` |
| `counted-11/meta.json` | `71ef44351bf38d301ac5c0d91a03c86e39e2af5e875091c8bf32e7f9fd47f430` |
| `counted-12/history.json` | `aff3207fbbafa3c0318a67dac8fbf9693079b6d41302a15f2a437ce7f82a451c` |
| `counted-12/summary.json` | `b6c48b07fbdbf57f7d399b54966ec0f9311d9310f3f7b8574b1198e10a580ad2` |
| `counted-12/best.json` | `466e766cc57f6d05d31287a3585d11bd4d7a40bc03d0db131035fa153ab5a2b9` |
| `counted-12/meta.json` | `70239f037584a899e247df7c7cb8222980bf7fd901e8e0ba5362326f7b2b0423` |
| `dev/show-goal/goal-d3/print.log` (call-site header probe) | `9c839ac4c91a4cb4aec64d073f9353f104dc2546c50de6fa58d3e77113099001` |
| `heartbeat.md` (LR-07 table, 30-min cadence) | `fd07e44493d2e2d71e745034d1825cc00f41e6a1150ec763ce60ae7fc46350dd` |

- Harness hashes per run are in each `meta.json` (`harness_sha256`). Harness commits: `c25a70f2`
  (run 10) and `06ea3ae6` (runs 11-12).
- Tests: `test_edit_loop.py`, `test_hints.py` and `test_loop_tool.py`, 26 passed.

### Counted run 13 — 2026-10-15 ET

**Fail; ticket remains claimed.** Same run-10 method, pinned Codex CLI 0.153.0,
`gpt-5.6-sol` / `xhigh`; fresh hints and the verified no-hint round-0 baseline.
Yan-Ru explicitly approved the scoped BFS proof-workspace export to Codex/OpenAI.
Run started 01:45:59 ET and ended 02:40:14 ET: 52.78 counted minutes, excluding
88.4 s waiting for shared verifier slots. No candidate proved before the in-call budget ended; the nominal 8-minute final
reserve was unused and no successful final replay ran.

Two Codex calls, 38 tool calls, 18 WP attempts. Best set: 44 hints, **19 open goals
of 239** (2 unit goals and 17 hint goals). A hint's own failing obligation cannot
be assumed to complete the unit. The original source, tool traces and reports
remain at `/private/tmp/probata-t07-20261015/counted-13`. Compact metadata and
artifact hashes: [counted-13 evidence](../evidence/t07-counted-13.json). The
shared box remains open to approximately 2026-10-27; this run does not exhaust it.

Before another counted run, audit the prototype's hint ghost-state ownership
boundary against ticket 36's newly fixed production check. Run 13 was not proven,
so no previously promoted result depends on that unaudited boundary.

### Guard review, goal diagnosis and counted run 14 — 2026-10-15 ET

The prototype now rejects model-state ghost writes, indirect calls, macro-based
mutations, shift assignments and trigraph introducers while retaining fresh scalar
snapshots. All **54 prototype controls pass** after integration (guard `09be3abf`,
merged `3db8002c`). See [guard review](../07-ghost-hint-safety-2026-10-15.md).

Read-only goal diagnosis found a concrete false hint in run 13: `best.json` index
25, `r1c18h1` at `loop:chunk_loop`. Its processed-prefix relation uses `begin`, which
may overshoot the frontier after a partial final chunk and include unprocessed
queue storage. A finite worked case falsifies that hint while preserving the unit
relation; clamping the prefix fixes that case only. This is not a contract bug or
universal proof. Compact artifact hashes: [goal audit](../evidence/t07-goal-audit-20261015.json).

**Counted run 14 started 03:33:40 ET and ended 04:33:12 ET unproven.** Frozen source branch
`codex/probata-t07-run14`, commit `05e81eac`. This method adds the checked ghost
ownership guard plus abstract partial-chunk boundary guidance, recorded in the
harness metadata. Same pinned provider and 60-minute counted budget (8-minute
replay reserve), fresh hints and hash-verified no-hint baseline. No previous hints,
worked-case workload inputs, tests or negative controls are supplied to Codex.
The user's explicit scoped Codex/OpenAI source-export approval applies. Original
source manifest, metadata and incremental output:
`/private/tmp/probata-t07-20261015-run14/`. Storage budget 2 GiB, 92 GiB free at
preflight; remaining readers are tickets 07/09 and the coordinator.

Run 14 used 53.32 counted minutes, excluding 373.2 s of verifier-queue wait. One Codex
call made 27 tool calls and 10 WP attempts. The best set has 39 hints and 14 open
hint obligations; zero open unit goals does not complete a proof resting on those
unproved cuts. No final proof/smoke replay or negative-control success occurred.
Compact metadata: [counted-14 evidence](../evidence/t07-counted-14.json).

The offline audit of accepted submission 25 finds one concretely false helper
assertion, `r1c15h4` at `stmt:after_flush`; its text is unchanged in the final best set. Its appended
queue-membership existential is outside the implication selecting newly discovered
vertices. An empty-frontier, previsited-vertex finite case satisfies the unit relation
and falsifies this stronger assertion. The executable logical evaluation and hashed
snapshots are retained at `/private/tmp/probata-t07-run14-audit/`; this is not a full C
replay or a counterexample to the unit contract. The audit never steered the active run.

### Counted run 15 — 2026-10-15 ET

Started **04:47:30 ET**, frozen `de78b7c6` in `/private/tmp/probata-t07-run15`.
This method adds abstract guidance to preserve quantifier and implication scope
when restating postconditions; it keeps run 14's partial-chunk guidance. All 54
prototype controls pass. Provider, effort, seeds and counted budgets are unchanged;
all hints are fresh. No previous hints, worked inputs, tests or negative controls
are exported. The existing scoped Codex/OpenAI approval applies.

Original output and source manifest: `/private/tmp/probata-t07-20261015-run15/`;
2 GiB budget, 83 GiB free at preflight, readers 07/09/coordinator. This functional
spike does not establish production RTE-initialization acceptance. Ticket 07 stays
claimed and the shared spike box remains open; no run-15 success is claimed yet.


**Run 15 ended 05:58:59 ET, not proven.** Two Codex calls, 41 tool calls and
12 WP attempts used **52.75 counted minutes**, excluding 1124.2 s of verifier-slot
wait. The best set has **57 hints and 25 open goals of 264: 1 unit frame goal plus
24 hint obligations**. `summary.final` is null; no complete proof/smoke replay or
negative-control success is claimed. Ticket 07 remains **claimed** and the shared
box remains open; this checkpoint does not close the spike or start run 16.

Compact metadata, source manifest and artifact hashes:
[counted-15 evidence](../evidence/t07-counted-15.json). The summary's
`best_sha256` is the SHA256 of the **entire final best.json file**
(`b0b754d8f5104fed3173e7ca0b6fdf51952be7af561560139d959644a198cfcb`),
not a hints-only digest. The evidence separately labels canonical hint-record and
logical-formula digests and their serialization.

**Offline audit boundary.** The audit copied round 1's best at `attempt-r1f`
(55 hints); final best is `attempt-r2c1` (57 hints). They are not byte-identical.
The final set retains every audited hint record and adds only `TDFrameUnfold` and
its `@assigns` attachment. All logical hint formulas, all three headers, and the
25 open goal names/failure classes are unchanged. The evidence pins both merged
source hashes and both full best-file hashes. No offline finding steered either
active provider call. Audit notes, finite scripts and reconciliation:
`/private/tmp/probata-t07-run15-audit/`. No concretely false hint was identified;
the remaining unknown/timeout outcomes stay unproved. Finite checks are not a
full C replay or a universal proof.

**Decision for the next experiment: repair the induction relationship before
retrying.** Current outer-loop invariants retain bookkeeping and safety, but do
not say that visitation equals reachability through the already processed
original-frontier prefix. An abstract exit state can satisfy those invariants
while omitting a reachable vertex; actual TDStep visits it, so this is missing
induction information, not a false-hint or contract counterexample. The finite
logical evaluation is `induction_gap.py` in the audit folder.

A justified follow-up would relate each initially negative vertex's current
visited state to the processed original-frontier prefix, clamped at the original
frontier end for the last partial chunk. Inner range and batch invariants must
refine that relation by their processed cursor/prefix and retain the equality
between each row's tile offsets and its original frontier vertex's CSR bounds.
`range_inputs` currently keeps bounds alone. This is a concrete induction
experiment within the remaining shared box; it is not a prediction of success.
No unchanged-method retry, new counted method, or new run was started here.

### Run16 preparation — 2026-10-15 ET

The next counted experiment uses fresh provider hints and adds only abstract
processed-frontier/CSR induction guidance to the reviewed prompt. It exports no
previous hint records, finite counterstates, tests or workload inputs. The unit,
contracts and headers remain unchanged. The provider must establish every proposed
base/preservation bridge; this guidance supplies no axiom or assumed invariant.

Harness regression:11 passed0.09s, `/private/tmp/probata-t07-run16-harness.jsonl`.
Frozen source worktree `/private/tmp/probata-t07-run16`; run output destination
`/private/tmp/probata-t07-20261015-run16/` on the Mac data volume, planned2GiB budget
and at least50GiB remaining. Readers:ticket07, ticket09 and implementation coordinator.
The existing30-minute heartbeat remains active. This preparation is no proof result.


**Run 16 ended 07:13:28 ET, not proven.** One Codex call, 21 tool calls and
11 WP attempts used **52.55 counted minutes**, excluding 694.6 seconds of verifier
slot waiting. Final best `attempt-r1f` has 42 hints, 257 goals and 26 open goals:
**4 unit and 22 hint obligations**. The four unit obligations are two seeded scalar
loop-frame goals and two gather call preconditions. All postconditions passing under
unproved cuts would not establish a proof. `summary.final` is null; no full proof,
smoke replay or negative-control success is claimed.

Compact evidence: [counted-16](../evidence/t07-counted-16.json). The full final
best-file SHA256 is `65d2df5df0de00c519ad65ed96d95f3a2774433816484537669444b0f098501d`;
the evidence separately labels the canonical hint-record digest. The frozen source
worktree is clean at `6acfbe4e7552d1763526e1da46dd2ef7d8041d28`, and its actual
harness/stand-in bytes match the launch metadata. This last observation was made
after completion; a separate preflight source-manifest file did not exist for run 16.

**Offline audit and next method.** Final-snapshot audit artifacts are retained in
`/private/tmp/probata-t07-run16-audit/`. No concretely false hint was found among
1,383 finite bookkeeping cases, 6,140 cutpoints, 524 partial chunks and 110 rank
states. These mathematical examples do not establish C execution, pointer safety,
device semantics or a universal theorem. An unreachable abstract exit state still
satisfies the actual chunk bounds, frontier preservation and bookkeeping predicates
while failing final reachability; actual processing visits the missing vertex.
The proof still lacks induction relating visitation to processed work.

A distinct follow-up must carry the clamped processed-frontier prefix and the
consumed CSR-pair prefix. Range issuance advances its continuation registers before
CPU consumption, so capture the pre-issue cursor and refine through completed
batches and positions already consumed. The scalar fallback needs the equivalent
row/edge prefix. No previous hints, finite counterstates, tests or evaluator code
may enter the provider workspace. No unchanged retry or run 17 has started.
Ticket 07 remains claimed within the shared two-week box.

### 2026-10-15: prospective consumed-prefix method

Prepared `consumed-prefix-cursor-snapshots-v4`: abstract guidance distinguishes range issuance from CPU consumption, captures pre-issue cursors, and carries processed row/edge prefixes through the range, batch and scalar loops. It contains no prior hints, worked formulas, counterstates, tests or workload inputs. All 54 pure prototype controls pass in 0.13 seconds (`/private/tmp/probata-consumed-prefix-guidance-controls.xml`). A future counted experiment will use fresh hints and total-open-goal acceptance, allowing it to revise the proof decomposition without rewarding a unit goal merely transferred into an open hint. No run 17 has started; implementation acceptance currently owns both local verifier slots. This is a prospective method change, not a proof result.
