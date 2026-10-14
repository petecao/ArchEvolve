# 09 — Spike verdict

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 08:55 ET (Answer: A1 exit not passed, stop rule fires, re-plan note); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-human
**Blocked by:** 06, 07, 08
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan": A1 row, overrun rule; "Testing Decisions", not unit tests; "Further Notes", risk table); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (item 2, fallbacks), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 4 and 8, levers and job budget), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about half a day

**What to build:** The decision that closes stage A1. This ticket gathers the four spike results
(05-08) with their evidence and applies the stop rule. If (b) failed after both levers, or (c)
failed within the box, A2-A6 and the Rocq track stop (see the stop-rule reading in the Notes): the
re-plan goes to Yan-Ru before any A2 ticket starts.
Otherwise the ticket records which bounded verifier A2 uses (SAW or crux-llvm) and what the spike
taught each A2 ticket. No new verifier runs happen here.

## Acceptance

- [x] A1's exit check, restated from the design ("Proof-of-concept plan", A1 row; map
      [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 3 and 5)
      and answered item by item: "(a)-(d) pass; stop and re-plan with Yan-Ru if (b) fails after both
      levers or (c) fails in the box", where (a) SAW reads clang 22 bitcode and keeps ghost state;
      (b) 2 lanes under 15 min with per-call summaries at threads = 1, on Peter's read offload and
      the authors' `TDStepMAA`, every single-thread control refuted at the hand-derived minimum; (c)
      WP proves one read-offload unit at threads = 1 with agent hints within 60 min; (d) WP proves
      the sum lemmas and one unit of a synthetic CSR pull-sum fixture over reals.
- [x] One table row per spike, (a) to (d): verdict ("pass", "pass via fallback", "pass with lever
      2" or "fail"), the deciding numbers (wall times, peak RSS, rounds), tool versions, and evidence
      paths with sha256.
- [x] Each verdict is checked against its own ticket's acceptance list and evidence, not copied from
      its summary line. Any unmet criterion is named.
- [x] The stop rule is applied in writing. Both conditions are answered "yes" or "no" with the
      evidence: (b) failed after both levers; (c) failed within the box.
- [x] On a stop: a re-plan note for Yan-Ru names the failed spike, what was tried, and the responses
      the design's risk table gives, and flags the stop-rule reading in the Notes for Yan-Ru to
      confirm. This ticket's Status becomes `ready-for-human`, so 20 — Formal-half frame and 41 —
      Rocq: composition theorem statement and definitions stay blocked.
- [ ] Not applicable (stop). 05's decision stands: SAW 1.6. Otherwise: the bounded verifier for A2 is named (SAW 1.6, or crux-llvm 0.12 on the C++ with
      hand stubs), citing 05's recorded decision.
- [ ] Not applicable (stop); lessons pointer in the Answer. Otherwise: one line per A2 ticket (20 to 33, 60 — Strict-layer replay and whole-kernel
      reproduction, 61 — SAW whole-function equivalence (bounded direct route)), saying what the
      spike taught it, or "nothing". This includes whether lever 2 (shape splitting) was needed.
- [x] A list of every spike verdict in a form A2 can reproduce: subject, variant, verifier, bounds,
      build constants, verdict. A2's exit needs generated artifacts to reproduce every spike verdict
      (33 — Minimum-bounds script and A2 exit).
- [x] Results the stop rule does not cover follow the design's risk table: SAW failing (a) while
      crux-llvm passes is "pass via fallback" and needs no re-plan; (a) failing under crux-llvm too
      goes to Yan-Ru as an open question; a failed (d) goes to Yan-Ru for a re-plan.
- [x] Every number is labeled a Mac result. None is a paper number.

## Notes

- **Not in this ticket:** 05 — Spike (a): SAW on clang 22 bitcode, 06 — Spike (b): 2 lanes under 15
  minutes, 07 — Spike (c): WP with agent hints, 08 — Spike (d): sums over reals (the runs
  themselves); 20 — Formal-half frame (the first A2 ticket); 33 — Minimum-bounds script and A2 exit
  (reproduces the spike verdicts with generated artifacts); 41 — Rocq: composition theorem statement
  and definitions (the Rocq track starts with A2, so the stop rule cannot waste it).
- **The spike is not a unit test.** Its recorded verdicts and this exit check judge it (design,
  "Testing Decisions").
- **Time box:** A1 is a 2-week box, not an estimate, so the 1.5x overrun rule does not stretch it.
  Time-boxed items end on their fallbacks.
- Assumption (not decided in the map): on a stop, the Status is `ready-for-human`, not `resolved`.
  Yan-Ru resolves the ticket once the re-plan is decided, which unblocks 20 and 41.
- Assumption (not decided in the map): a spike unfinished when the 2-week box ends counts as failed
  within the box.
- Reading of lever 2 (map 19 item 8, budget per bounded job): (b) "pass with lever 2" needs each
  shape job under 15 minutes, every shape job proven and the count check passed. The total wall
  time from 06 is shown too.
- Assumption (not decided in the map): after a failed (d), whether A2 continues while the re-plan is
  open is Yan-Ru's call; this ticket asks and does not decide.
- Stop-rule reading (flag for Yan-Ru; map 27 item 3 says only "before building anything"): a stop
  pauses A2-A6 and the Rocq track (41-43). The Extensa track (02, 04, 10-19, 55, 63; scripted
  adapter) continues unless Yan-Ru's re-plan says otherwise. Note: 55 also waits on 39, 48 and 60,
  which sit in paused stages, so the Extensa track's exit cannot pass during a stop.
- Assumption (not decided in the map): this ticket writes its verdict into its own Answer only. It
  does not edit the spike tickets or the A2 tickets.

## Answer

2026-10-14 08:55 ET. **A1 exit: not passed. The stop rule fires on both conditions.** (b) failed
after both levers, and (c) failed in the box. Status is `ready-for-human`: 20 — Formal-half frame
and 41 — Rocq: composition theorem statement stay blocked until Yan-Ru decides the re-plan below.
Every number here is a **Mac result** (host `mac`), not a paper number. No verifier ran in this
ticket.

### A1 exit check, item by item

The design's check (A1 row; map 27 items 3 and 5): "(a)-(d) pass; stop and re-plan with Yan-Ru if
(b) fails after both levers or (c) fails in the box".

| Spike | Verdict | Deciding numbers (Mac) | Tools | Evidence, `/tmp/claude/probata-runs/` (sha256, first 16) |
|---|---|---|---|---|
| (a) SAW reads clang 22 bitcode, keeps ghost state | **pass** (SAW, no fallback) | Safe variant proven in 0.47 s, 157 MB. Seeded bug refuted in 0.47 s at the read's ghost check (counterexample `a: 6, b: 1`). Control (ghost check removed) proves, so that check is the one that fails. | SAW 1.6 (68eed5f), bundled Z3 4.8.14; clang++ 22.1.8 `-g -O0` | `t05/saw_safe.log` `2ee3b5a17af3e13f`; `t05/saw_buggy.log` `5e7f66eaf94fb428`; `t05/saw_control.log` `2d6f072f4280bb51` |
| (b) 2 lanes under 15 min, per-call summaries, threads 1 | **fail** (after both levers) | Lever 1: Peter's `TDStep` timeout at 900 s (1.20 GB), `TDStepMAA` timeout at 900 s (0.71 GB). Lever 2, shape 95: both time out at 900 s (1.19 / 0.71 GB). Shape 84 (one edge) unfinished at 1800 s (1.58 GB). Controls: 2 of 12 run, both "not refuted, timeout"; 10 not run. With concrete inputs the same harness proves in 6.7 s / 8.2 s. | SAW 1.6; goals Z3 4.8.14, path-sat Yices 2.6.5; clang++ 22.1.8 | `t06/peter_l1.log` `d73eb3bc8bd1f100`; `t06/maa_l1.log` `aa41b7fd9dfe4223`; `t06/peter_s95.log` `bea7589908ee24c6`; `t06/maa_s95.log` `0b977ce84bf64453`; `t06/peter_cal.log` `88b3e300c82c2a82` |
| (c) WP proves one read-offload unit with agent hints in 60 min | **fail** | Run 1: 10 rounds, 10 Codex calls, 58.97 budget-min; Frama-C rejected all 10 hint sets. Run 3: 2 rounds, 6 calls, 60.99 budget-min; one set reached WP, 99 goals timed out. One WP pass: 905 s without hints (3.6 GB), 1209 s hinted (6.4 GB). Lock waits excluded: 67.0 and 114.2 min. | Frama-C/WP 33.0; Alt-Ergo 2.6.4, Z3 5.1.0, CVC5 1.2.1 (30 s each, `-wp-par 12`); Codex CLI 0.153.0, `gpt-5.6-sol` `xhigh` | `t07/counted-1/summary.json` `2428293344cca2b4`; `t07/counted-3/summary.json` `42bc335cf7fe4052`; `t07/counted-3/round-1-turn2/goals.json` `244a77ea4047a7c6` |
| (d) WP proves the sum lemmas and a CSR pull-sum unit over reals | **pass** | Lemmas 17/17 Valid on a fresh replay of 11 saved scripts; slowest `REGROUP_TOTAL` 13 s. Unit: 63/63 goals, 50/50 properties completely validated, 6/6 smoke tests passed; 31 s, 1.2 GB. Seeded bug not proven. `\false` not proven (Alt-Ergo timeout 30 s, CVC5 unknown 0.8 s, Z3 timeout 8 s). | Frama-C/WP 33.0 `-wp-model +real`; Why3 1.8.2; Alt-Ergo 2.6.4, Z3 5.1.0, CVC5 1.2.1 | `t08/lemmas/wp_report.json` `27fa02966c6ede81`; `t08/unit/wp_report.json` `3555f8ea1e3ba9a5`; `t08/bug/wp_report.json` `b668179b87fc3266`; `t08/SHA256SUMS` `cafa5caa0c471f8d` |

**Evidence check (2026-10-14, this ticket).**

- Every full sha256 quoted in the Answers of 05-08, re-hashed: 58 of 58 match (logs, bitcode,
  prototype files).
- `t08/SHA256SUMS`: 110 of 110 entries match. 08's 11 scripts, concatenated in name order: match.
- 07's run-3 hint set (`7b603013…`): matches as the sha256 of `t07/negctl/hints_run3_round1.json`
  in sorted-key JSON form. It holds 155 hints, all with provenance `codex gpt-5.6-sol xhigh round 1
  turn 2`, in the kinds 07 lists.
- Three abbreviated hashes in 07's Answer have wrong tails (typos): `dxc_summaries.h` ends
  `…6580a` (written `…a580a`), `loop.py` ends `…4116` (written `…6116`), `hints.py` ends `…d19d7e`
  (written `…ed0e`). The full values in `t07/counted-3/meta.json` match the committed files, so
  these are the files the runs used.

### Each verdict against its own ticket's acceptance list

- **(a), ticket 05: pass.** All 7 applicable items met. The crux-llvm fallback item does not
  apply. Minor: 05's table gives 0.47 s wall for the safe run; the watchdog summary says 0.81 s
  (wrapper start-up included). No effect.
- **(b), ticket 06: fail after both levers.**
  - Unmet: Peter's unit proven; `TDStepMAA` proven (timeouts at lever 1 and lever 2); Peter's 7
    controls refuted (1 run, timeout; 6 never reached a verdict); `TDStepMAA`'s 5 controls refuted
    (1 run, timeout; 4 not run).
  - Met: summaries per map 12, no port inlined; map 19's bounds, every build constant recorded;
    harness assumes only from summaries and preconditions; lever 2 with the count check (200 =
    200); timeouts recorded as "not proven, timeout"; table and last line.
  - Lever 2 ran on shape 95 only. By map 19 item 4, one failed shape makes the whole verdict "not
    proven", so the other 199 shapes cannot change it.
- **(c), ticket 07: fail.**
  - Unmet: a counted run with every goal proven within 60 minutes (neither counted run, 1 or 3); a
    fresh-run verdict with every property Valid (249 not Valid after run 3's round 1); smoke tests
    on the final hinted unit (no final unit exists; 139/139 passed on the no-hint and the hinted
    run).
  - Met in letter only: the negative control. Its hazard checks are `Partial`, never `Invalid`, but
    the positive run's are `Partial` too, so it does not yet separate the variants.
  - Met: stand-in (names, hazard checks, ACSL summaries, symbolic `TILE_SIZE`); no-hint run (105
    timeouts, 0 unknown); hint vocabulary and per-hint provenance (verified above); solver
    portfolio; workspace and provider pin; verdict stated.
  - Note: 07 changed its method 4 times between counted runs (feedback format, repair turns, prompt
    notes, goal generation in the hint check). The runs do not test one fixed method. 07 classified
    each change.
- **(d), ticket 08: pass.** All 10 items met. Hints came from the implementing agent, which 08's
  Notes allow ((d) does not test agent hints). Its "61 goals" is WP's scheduled count; the log
  says 63/63, with 2 trivial goals.

### Stop rule

- **(b) failed after both levers: yes.** Lever 1 (3 encodings) and lever 2 (5 encodings, shape 95,
  plus shapes 84-85) all ended "not proven, timeout" at map 19's minimum. Cause (06's profiles): SAW
  explores the value-dependent CPU branches path by path (`hint<0 && CAS` in Peter's code,
  `tile4Ptr[i] && tile5Ptr[i] < 0` in `TDStepMAA`), and each summary application costs 1-3 s on
  symbolic memory.
- **(c) failed within the box: yes, provisionally.** Neither of 07's counted runs (1, 3) proved the unit
  within 60 budget-minutes. Flag: 07's own assumption reads "the box" as A1's 2-week box and counts
  a run as failed "when the box ends". The box opened 2026-10-13 (tickets created 22:17 ET), so it
  runs to about 2026-10-27 ET. Read strictly, (c) is "no pass yet, box still open", and a re-run of
  (c) (below) still falls inside the box. This does not change the outcome: (b) alone fires the
  stop.
- **Results the stop rule does not cover:** (a) passed with SAW, no fallback; (d) passed. Nothing
  goes to Yan-Ru from them.

### Re-plan note for Yan-Ru

**To decide:** (1) the stop-rule reading below; (2) a response for (b); (3) a response for (c).
Until then A2-A6 and the Rocq track (41-43) wait; tickets 20 and 41 stay blocked.

**Stop-rule reading to confirm** (ticket Notes; map 27 item 3 says only "before building
anything"): a stop pauses A2-A6 and the Rocq track. The Extensa track (02, 04, 10-19, 55, 63)
continues. 55 also waits on 39, 48 and 60, so the Extensa track's exit cannot pass during the stop.
The main session has applied this reading since about 07:50 ET on 2026-10-14.

#### (b) Two lanes in 15 minutes: failed after both levers

- **What was tried (06):** lever 1, per-call summaries, 3 encodings (SAW ghost state; harness
  globals; producer masks with hash-consing). Lever 2, shape splitting, 5 encodings (one global per
  field; SMT-array memory; path-sat off). Every job timed out; one ran out of memory. Concrete
  inputs prove in 6.7-8.2 s, so the summaries are consistent; the cost comes from symbolic values.
- **The design's responses:**
  - Risk table, "2 lanes do not prove in 15 minutes": "shape splitting; else candidates stay
    certified and Yan-Ru re-plans". Shape splitting is spent.
  - Map 11 item 2, the remaining bounded fallbacks in order: crux-llvm 0.12 on the C++ (hand
    stubs); crux-llvm on the C lowering; CBMC 6.11 on the C lowering (`goto-instrument --dfcc`).
  - Map 19 item 1: no fallback to 1 lane (one lane cannot see `skipped_cas_recheck`). Item 8: the
    budget is per job, so a larger machine does not help one job.
- **06's options:** value splitting (`parent` sign patterns, neighbor targets; about 3,340 graphs
  times frontiers times patterns, mbit10 work); a per-lane summary of the CPU claim loop; crux-llvm
  on the same summaries.
- **Main session's recommendation — proposed, not decided:**
  - Skip both crux-llvm fallbacks. Path explosion is the weakness of symbolic execution that SAW and
    crux-llvm share (both are Crucible). Map 08 already saw no safe 2-lane crux-llvm run finish in
    15 minutes.
  - A 1-day box with CBMC 6.11, the design's last bounded fallback ("CBMC on the C lowering"). CBMC
    is SAT-based bounded model checking: all paths go into one formula, not path by path. Input:
    06's two units hand-lowered to C, the same summaries as C stubs, the same bounds, plus the 12
    controls. Pass bar unchanged: both units proven and every control refuted, each job under 15
    minutes.
  - Risk: map 08's ESBMC (also a bounded model checker) timed out on a similar port (300-600 s at
    every size).
  - Alternatives: a per-lane summary of the CPU claim/push loop; value splitting on mbit10; accept
    the stop.
- **This ticket's notes on that proposal** (also not decided):
  - CBMC 6.11.0 is already installed on both hosts (`/opt/homebrew/bin/cbmc` on the Mac; mbit10 per
    the shared note `verifiers-mbit10.md`).
  - Map 11: CBMC cannot parse libc++ 22 headers, so the hand-lowered C must include no C++ header.
  - CBMC can also take the summaries natively as contracts (`goto-instrument --dfcc
    --replace-call-with-contract`) instead of C stubs. Either way, give each hazard check its own
    `__CPROVER_assert`, so a refutation names its check (as 06 split `maa_stream_load`).
  - Keep unwinding assertions on and derive each unwind limit from the sizes (map 19 item 5's rule
    for crux-llvm holds for CBMC for the same reason).
  - If CBMC passes, A2's plan changes, not only a tool name. The bounded verifier would read the C
    lowering, so 21 (C lowering) comes before the bounded adapter; 22 (SAW adapter and translator)
    becomes a CBMC adapter; 61 (SAW whole-function equivalence) loses its tool. The hand lowering
    is a spike stand-in, not 21's trusted tool.

#### (c) WP with agent hints in 60 minutes: failed

- **What was tried (07):** 2 counted runs (1, 3) and 2 aborted ones (aborted-1, run 2) on one stand-in, with 4 method changes
  between runs (Frama-C errors mapped to hints; up to 3 repair turns per round via `codex exec
  resume`; syntax notes in the prompt; WP goal generation in the hint check). Best run (3): one
  hint set reached WP, 99 goals timed out, and the budget stopped round 2's WP run.
- **The design's responses:** none. The risk table has no row for (c); map 27 item 3 says only
  "stop and re-plan". 07's own input: a budget that fits several WP passes, WP rerun only on the
  goals a round touched, or an agent that runs the parse and goal-generation checks inside one call
  (map 13 item 6, on mbit10 under Landlock).
- **Main session's recommendation — proposed, not decided:**
  - The 60-minute budget holds only about 2 WP passes (15-20 min each), and Frama-C accepted 0 of
    14 of Codex's first-attempt hint sets.
  - Make the hint loop incremental: re-prove only the goals whose hints changed (`-wp-prop` /
    `-wp-fct`), with one fresh full replay at the end, since the WP cache can mislead (research 13).
  - Add syntax-checked hint seeds and ACSL examples to the prompt.
  - Re-run (c) once inside an mbit10 lane with parallel provers.
  - Put the 4 method changes 07 introduced into the method version.
  - The question is the 99 open goals: one hint set already reached 543/642 goals, and 8 of 9
    postconditions and 3 of 3 hazard checks were Valid given hint assertions WP had not proven.
- **This ticket's notes on that proposal** (also not decided):
  - **Correction:** the Mac WP runs used `-wp-par 12`, not `-wp-par 1`
    (`prototype/07-wp-hints/wp_run.sh`, line 25). So an mbit10 lane adds cores and removes lock
    waits; the Mac runs were already parallel. Ticket 57 caps a lane at 6 proof workers: check how
    that cap counts `-wp-par` before sizing the run. The hinted Mac run peaked at 6.4 GB, near the
    8 GB watchdog.
  - **543/642 includes 139 smoke tests that passed and 26 trivial goals.** Real goals: 404 of 503
    Valid with hints, 178 of 283 without (from the two `goals.json` files).
  - **Smoke tests pass by timing out** (139 goals, up to 30 s per prover), so they likely take a
    large share of each 15-20 minute pass (an estimate, not measured). Design S7 needs smoke tests
    on the final hinted unit, so hint rounds could skip `-wp-smoke-tests` and keep them for the
    final replay.
  - **`-wp-fct` gains little:** all 99 open goals are in `TDStep`. With `-wp-prop`, a changed
    invariant can change goals that were Valid before. So the final fresh full replay is required,
    and it must fit inside the 60 minutes (one 15-20 minute pass).
  - **The A1 box is still open** (to about 2026-10-27 ET), so this re-run counts as within the box.

### Verdicts in a form A2 can reproduce (for 33 — Minimum-bounds script and A2 exit)

All Mac results. Paths are under this effort's `prototype/` folder.

| # | Subject | Variant | Verifier | Bounds | Build constants | Verdict |
|---|---|---|---|---|---|---|
| a1 | `05-saw-ghost/fixture.cpp` (8-tile ghost array) | safe | SAW 1.6, Z3 4.8.14 | 32-bit `a`, `b`, `base`; `a, b < 8`, `a != b`; any start ghost; 4-iteration read loop | clang++ 22.1.8 `-std=c++17 -g -O0` | proven |
| a2 | same | `-DBUGGY` (covering wait removed) | same | same | same | refuted at the read's ghost check |
| a3 | same | `-DBUGGY`, read check replaced by `True` (control) | same | same | same | proven |
| b1 | Peter's `TDStep` (`06-two-lanes/unit_peter.cpp`; `bfs_read_offload.inc` `3c5867a2b8919806`) | lever 1 | SAW 1.6; Z3 4.8.14 goals, Yices 2.6.5 path-sat | threads 1, lanes 2, chunk 2, vertices 3, edges <= 3, frontier <= 2, `parent[v]` in [-3, 3) | `TILE_SIZE`=2, `NUM_CORES`=1, `SWDB_CHUNK_SIZE`=2, 8 tiles and 8 registers per core, `SWDB_FRONTIER_THRESHOLD` symbolic >= 1; clang++ 22.1.8 `-g -O0` | not proven, timeout (900 s) |
| b2 | `TDStepMAA` (`06-two-lanes/unit_maa.cpp`) | lever 1 | same | same | same | not proven, timeout (900 s) |
| b3 | Peter's `TDStep` | lever 2, shape 95 | same | same, shape 95 | same | not proven, timeout (900 s) |
| b4 | `TDStepMAA` | lever 2, shape 95 | same | same, shape 95 | same | not proven, timeout (900 s) |
| b5 | Peter's `TDStep` | control `read_before_wait`, shape 95 | same | same, shape 95 | same | not refuted, timeout (900 s) |
| b6 | `TDStepMAA` | control "wait deleted", shape 95 | same | same, shape 95 | same | not refuted, timeout (900 s) |
| b7 | both units | the other 10 controls | same | same | same | no verdict (not run) |
| c1 | `07-wp-hints/standin/tdstep_standin.c` (`a39c67adc531f547`) | no hints | Frama-C/WP 33.0; Alt-Ergo, Z3, CVC5 at 30 s each; `-wp-par 12` | threads 1; every data dimension symbolic | `TILE_SIZE` 1..65535, `SWDB_CHUNK_SIZE` 1..`TILE_SIZE`, `SWDB_FRONTIER_THRESHOLD` >= 1, all symbolic; machdep x86_64 | not proven (105 goals timeout) |
| c2 | same | run 3's 155 Codex hints | same | same | same | not proven (99 goals timeout) |
| c3 | same, `__dxc_wait(c.tile[5])` removed | run 3's hints (control) | same | same | same | not proven (hazard checks `Partial`) |
| d1 | `08-sums-over-reals/sum_logic.h` lemmas | 11 saved scripts | Frama-C/WP 33.0 `-wp-model +real` | none (unbounded) | — | proven (17/17) |
| d2 | `08-sums-over-reals/csr_pull_sum.c` | safe | same, `-wp-rte -wp-smoke-tests` | sizes symbolic, threads 1 | `float` read as real | proven (63/63; 6/6 smoke tests passed) |
| d3 | same | `-DSEEDED_BUG` | same | same | same | not proven |
| d4 | `08-sums-over-reals/false_check.c` | `\false` from definitions and lemmas | same, one prover per job | — | — | not proven |

### Not applicable on a stop

- **Bounded verifier for A2:** not named here. 05's decision stands for now ("SAW 1.6 is the
  bounded verifier"); a CBMC result from the re-plan could change it (see (b)).
- **One line per A2 ticket:** not written. Lever 2 was needed and failed. The lessons A2 needs are
  in the Answers of 05-08 and in the shared notes' hand-off list: 22 (ghost precondition order,
  `llvm_elem` for namespaced structs, `llvm_return`), 26 (induction base -1, wrappers for `int`
  reads, `Wp.lemma` hints, permutation with its inverse), 34/37 (`Wp.lemma` hints, repair turns,
  checks inside the call), 36 (`Extern` attribution, memory-model hypotheses), 21 (no `\fresh`, no
  infinite range in `loop assigns`).

### Assumptions and records

- Assumption (not decided in the map): the A1 box starts at ticket creation (2026-10-13 22:17 ET)
  and ends about 2026-10-27 ET.
- Assumption: verdicts rest on each spike ticket's recorded evidence, re-hashed here; no run was
  repeated.
- Runs folders (LR-06): `/tmp/claude/probata-runs/t05` to `t08` (about 30 MB) stay until Yan-Ru
  decides the re-plan. Readers now: this re-plan and the main session. Nothing was deleted.
