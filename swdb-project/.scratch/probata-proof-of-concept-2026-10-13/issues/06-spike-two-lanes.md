# 06 — Spike (b): 2 lanes under 15 minutes

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 12:45 ET (Continuation: pass via fallback (CBMC)); 2026-10-14 08:10 ET (Answer: fail after both levers); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 05
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (b); "Proven once vs per candidate", scale pass bar; "Bounds"; "DX100 proof semantics"; "What a proven verdict asserts", harness `assume`s; "Further Notes", risk table); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [08](../../formal-verification-2026-10-09/issues/08-wrong-tile-prototype.md), [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 4 days, inside the 2-week box

**What to build:** The spike's scale test: does Extensa's scaling failure repeat? In map 08, the
inlined strict-layer port made every safe 2-lane run time out. Here, throwaway agent-written
per-call summaries of the DX100 calls replace that port. With them, the bounded verifier chosen in
05 must prove two real proof units at threads = 1 in a build with `TILE_SIZE` = 2: one `TDStep` call
with Peter's read offload, and one call of the authors' `TDStepMAA`. Each proof must finish in under 15
minutes on the Mac. Every single-thread negative control must be refuted at map 19's hand-derived
minimum bounds. If lever 1 (per-call summaries) is not enough, lever 2 (shape splitting) is tried.
Failing after both levers is a stop condition for 09 — Spike verdict.

## Acceptance

- [x] One throwaway summary per DX100 call the two units make, used as overrides (SAW specs, or
      crux-llvm hand stubs if 05 chose crux-llvm). They follow map
      [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md)'s rules: values
      as if each command finished at issue; an unready read is an assertion failure; the gem5 wait
      rule. Neither proof inlines the strict-layer port.
- [x] Every run uses map [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md)'s
      hand-derived minimum: threads 1 (`NUM_CORES` = 1), lanes 2 (`TILE_SIZE` = 2), chunk 2, and
      inputs symbolic up to frontier 2, vertices 3, edges 3. Every build constant is recorded
      exactly.
- [x] Met via fallback (CBMC 6.11, Continuation: 3.4 s). SAW: not met (timeout at both levers; Answer). Peter's read offload: the unit is proven (BFS unit postcondition and hazard freedom) in under
      15 minutes wall time. Wall time, peak RSS and solver recorded.
- [x] Met via fallback (CBMC 6.11, Continuation: 5.6 s). SAW: not met (timeout at both levers). The authors' `TDStepMAA`: the unit is proven, same properties, same budget, same records.
- [x] Met via fallback (CBMC 6.11, Continuation: 7 of 7 refuted at the expected check). SAW: not met (no control refuted within the budget; Answer, Controls). Peter's read offload: each of the contract's seven single-thread controls (`dropped_wait`,
      `read_before_wait`, `index_wrap`, `forged_frontier`, `dropped_continuation`,
      `chunk_off_by_one`, `skipped_cas_recheck`) is refuted at these bounds, with the same harness
      and summaries, each with a counterexample. The check that fires is attributable to the break
      (glossary: negative control).
- [x] Met via fallback (CBMC 6.11, Continuation: 5 of 5 refuted at the expected check). SAW: not met (as above). `TDStepMAA`: each of its single-thread controls (see the assumption below) is refuted the
      same way.
- [x] The harness has no `assume` beyond summary-generated ones and proof-unit preconditions. Map
      08's `parent[v] >= -1` assume is widened to every value `InitParent` writes (map
      [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) item 10). Map
      08's relabeling (shape mode) is not used (map 19 item 4).
- [x] If a proof misses 15 minutes with lever 1, lever 2 runs: one job per graph shape, values
      symbolic, with a count check against a closed-form count of shapes. A missing or failed shape
      job leaves the whole verdict "not proven" (map 19 item 4). The 15-minute bar applies to each
      shape job (map 19 item 8: the budget is per bounded job); the total wall time is recorded too.
- [x] A timeout is recorded as "not proven, timeout" at these bounds. No run falls back to smaller
      bounds or to 1 lane (map 19 items 1 and 8).
- [x] The Answer has one table row per proof and control: subject, lever, verdict, wall time, peak
      RSS, bounds, evidence path and sha256. Its last line reads "pass", "pass with lever 2" or
      "fail after both levers".

## Notes

- **Not in this ticket:** 05 — Spike (a): SAW on clang 22 bitcode (picks the verifier); 09 — Spike
  verdict (the stop rule); 27 — Proof semantics for the BFS read-offload calls and 30 — Reference
  definitions, per-call summaries and new intrinsic versions (the real summaries); 31 — Five-gate
  drafting and the new bfs_read_offload version (formal halves L1-L4); 32 — BFS contract proof;
  33 — Minimum-bounds script and A2 exit (confirms the hand minimum by script; 2 lanes with generated
  summaries); 29 — Proof-semantics checks (the real semantics negative controls, per proof-semantics
  version); 46 — CIVL adapter, 47 — GenMC adapter and agreement and 48 — Concurrency negative
  controls (multi-thread controls such as `shared_context`).
- **Throwaway.** Nothing here becomes A2 code. A2's exit must reproduce these verdicts with
  generated summaries (33).
- Assumption (not decided in the map): "proven" here means the BFS unit postcondition (map 08's P2)
  plus hazard freedom (P1). Formal halves (A) do not exist until 31.
- Assumption (not decided in the map): `TDStepMAA`'s single-thread controls are the semantics
  negative controls that name it (its wait deleted; the authors' wait under the old wait rule; a
  same-thread read of `parent` while its DX100 store is unfinished; map 12 item 9), plus map 08's two
  wrong-tile bugs (a wait on a tile the store does not name; a wait on the compare's tile). The
  contract's seven controls are mutations of Peter's code, the contract's reference instance.
- Assumption (not decided in the map): `TDStepMAA` runs at the same bounds as Peter's code. Map 19
  derived the minimum for the read offload only.
- Reading of lever 2 (map 19 item 8, budget per bounded job): each shape job must finish in under 15
  minutes, and jobs run one at a time on the Mac. The total wall time is recorded too; 09 shows both.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs go to the Mac runs folder outside the
  repo, host `mac` (map 26 item 5), the one 05 records.
- **Risks:**
  - Map 08: crux-llvm on the port proved 1 lane, but no safe 2-lane run finished in 600-900 s. Up to
    six crux jobs at once exhausted the Mac's 36 GB and forced a restart.
  - The 1-lane fallback is withdrawn (map 19 item 1; map
    [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) Later changes):
    one lane cannot see `skipped_cas_recheck`. If both levers fail, candidate artifacts stay certified and
    Yan-Ru re-plans (design risk table).
  - If 05 chose crux-llvm: each loop's unwind limit is computed from the sizes, with unwinding
    assertions on (map 19 item 5).
  - Either verifier: SAW bundles no libc++ bitcode (map 11 research) and crux-llvm cannot run libc++
    22 code (map 07, 08), so throwaway overrides or stubs stand in for any standard-library member
    the unit calls (map 16 item 7 plans the real models; 25 — std::vector and std::pair models
    builds them).
- **Held-out code:** `TDStepMAA` is BFS calibration code. No held-out authors' function
  (`PBFSMAA`, `PageRankPullMAA`, `DeltaStepMAA`, and `BrandesMaa`, BC's DX100 driver, by design
  spec O2's default) is read.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog; a watchdog kill is
  "out of memory", never a pass. Keep at least 50 GB free. The full set (2 proofs plus about 12
  controls, one at a time) can pass 30 minutes, so schedule the 30-minute heartbeat first (LR-07).

## Answer

2026-10-14 08:10 ET. **Verdict: fail after both levers.** With per-call summaries (lever 1) and
with shape splitting (lever 2), neither proof unit is proven within 15 minutes at map 19's minimum
bounds on the Mac. Every job ended "not proven, timeout". No negative control was refuted within
the budget either. Extensa's scaling failure repeats with SAW 1.6 and summaries in place of the
port.

**What was not the cause.** With concrete inputs, the same harness, summaries and checks prove:
Peter's unit in 6.7 s and `TDStepMAA` in 8.2 s, both with P2 and hazard freedom at 2 lanes. The
summary tests pass, including with symbolic `parent` (`test_summaries.sh`, 21 s). So the
summaries are consistent with both units. The cost comes from symbolic values.

**Why it does not scale (profiles, `enable_crucible_profiling`).** SAW splits a path at every
value-dependent CPU branch: the claim `hint<0 && CAS` in Peter's code, the push
`tile4Ptr[i] && tile5Ptr[i] < 0` in `TDStepMAA`. Each `&&` is two branches, so each lane has
about three outcomes, and SAW explores the outcome combinations path by path. On each path, every
summary application costs 1-3 s once memory holds symbolic or merged values, against 0.18 s with
concrete inputs. Most of that time is SAW's override matching (`overrideBranches`, 50-75%) and
path-satisfiability queries. Even a shape with one edge (shape 84) did not finish in 30 minutes.
With the graph fully concrete and only `parent` symbolic, shape 95 did not finish in 25 minutes
(dev diag 3, 4).

**Prototype:** [`../prototype/06-two-lanes/`](../prototype/06-two-lanes/). `run_spike.sh` runs
the jobs one at a time through `/tmp/claude/probata-tools/verifier_run.py` (lock, 8 GB cap,
15-minute budget per bounded job) and checks each verdict against its table.
`test_summaries.sh` tests the summaries. `shapes.py count` checks the shape count.

| File | Role | sha256 |
|---|---|---|
| `ghost.cry` | proof semantics (Cryptol): hazard state, gem5 wait rule, value functions | `3257cb1839d492aed232f1a41d01f697b0fff7d0c4fc14a433331c4f5402a2dc` |
| `summaries.saw` | per-call summaries as `llvm_unsafe_assume_spec` overrides | `56fe1b746bcc96b5fb247019d2d65af6082a815f05f75ffb0383bca9aa12908e` |
| `units.saw` | harness specs: proof-unit preconditions, lever 1 and lever 2 inputs | `b864616390506640a5280c768f96e40aad5cc49841bf68b3de575244fac90776` |
| `spike_api.hpp` | declared-only `maa_*` calls, probes, GAPBS stand-ins | `6fceaef23edab051af447f4baef30bef2ae4497d71bd6939d928523b98ec9131` |
| `spike_lowering.hpp` | `__dxc_*` lowering, seams and faults (from `dxc_lowering.hpp`, `candidate_prelude.hpp`, `seams.cc`) | `e01077441475aedb71510e2e8a4f5bafccb2053bf103fc57d9cdd787c7b94e2b` |
| `unit_common.hpp` | inputs, P2 (BFS unit postcondition) | `03d98ac1048d1dc603ec911b2f2eceab614680adaa1020d2c859e78dd92e7a84` |
| `unit_peter.cpp` | unit 1: includes `library/dx100/bfs_read_offload.inc` unchanged (sha256 `3c5867a2b8919806…`) | `bbfd3da6e3ccc73f15153399668e8282e87e72701e79d54236c76022be9b936d` |
| `unit_maa.cpp` | unit 2: the authors' `TDStepMAA` (`bfs.cc:63-225`) with marked EDITs, PROBEs and controls | `319f355676678f66d095c188a37a608f246841181a76f657624e5e2b71fef46b` |
| `shapes.py` | lever 2 shape enumerator and closed-form count check (200 = 200) | `f3260421557f05ca01996b632cdaa4cb48fe6ca2c942988c7bdd68a1ce48884d` |
| `run_spike.sh` | runner and verdict check | `8bc0da9b54e9b0feaf28118d6be1a993877db9f4fb804a1d0073e5db56734554` |
| `test_summaries.{cpp,saw,sh}` | summary tests (range loop gives 2, 1, 0 lanes on shape 95) | `8fd1f14b…7c`, `1d29e6d9…2e`, `a46a0558…55` |

**Recorded setup.** SAW `1.6 (68eed5f release-1.6)`; goals by SAW's bundled Z3 4.8.14,
path-satisfiability queries by its bundled Yices 2.6.5 (`set_path_sat_solver "yices"`);
`enable_what4_hash_consing`; default memory model; `llvm_verify ... true` (path-sat on).
Homebrew clang++ 22.1.8, `-std=c++17 -c -emit-llvm -g -O0 [-I<swdb>/library/dx100] [fault flag]`.
Build constants: `TILE_SIZE` = 2, `NUM_CORES` = 1, `SWDB_CHUNK_SIZE` = 2, 8 tiles and 8 registers
per core. Knob: `SWDB_FRONTIER_THRESHOLD` symbolic, >= 1 (legality clause). Inputs: vertices 3,
edges 0-3 (CSR offsets), frontier 0-2 distinct visited vertices, `parent[v]` in [-3, 3)
(vertex IDs or a value `InitParent` writes at these bounds), `swdb_acceleration_enabled`
symbolic, tile memory symbolic. DX100 state at entry: nothing pending.

**Summaries** (one per call, map 12): `maa_const`, `maa_stream_load` (split into three
overrides so a refutation names its check: `stream_bounds`, `tile_truncation`, then the load and
its memory-region check), `maa_indirect_load` (one override per memory region; C code picks it by
concrete pointer), `maa_range_loop`, `maa_alu_scalar` (`LT_OP` only), `maa_indirect_store_vector`,
`wait_ready`, `get_tile_size`. Probes: `swdb_probe_tile_read` (before each CPU tile read; where
`dxc_lowering.hpp` checks `get_tile_ready`), `swdb_probe_cpu` (CPU access to a region, in the CAS
seam). Values as if each command finished at issue. An unready read, size read or overlapping CPU
access is a failed precondition. The gem5 rule: a wait covers every command that names the tile
and, transitively, their producers (not through a range loop that filled its tile); a dispatch
stall covers the users of an output tile; a register write covers its readers; a region stall.
No strict-layer code is compiled in.

**Results** (runs folder `/tmp/claude/probata-runs/t06/`, host `mac`; each log has a
`.summary.json`). Bounds for every row: threads 1, lanes 2, chunk 2, vertices 3, edges <= 3,
frontier <= 2. "s95" = shape 95 (`nf2_f01_o0133`: frontier {0,1}, edges 0->2, 1->2, 1->0), map 19's
hand-derived minimum scope.

| Subject | Lever | Verdict | Wall | Peak RSS | Evidence | sha256 |
|---|---|---|---|---|---|---|
| Peter's `TDStep` | 1 | not proven, timeout | 900 s | 1.20 GB | `peter_l1.log` | `d73eb3bc8bd1f10080c34be4cc7953e78769c0dda7ab4fd204ea74133da0cce2` |
| `TDStepMAA` | 1 | not proven, timeout | 900 s | 0.71 GB | `maa_l1.log` | `aa41b7fd9dfe422384dcbd3aef4e964f4154a0b7554a8ad4e4e14e10b35697f6` |
| Peter's `TDStep` | 2, s95 | not proven, timeout | 900 s | 1.19 GB | `peter_s95.log` | `bea7589908ee24c6639dea91be50073e099d52c8e323ebec7ecbd45391d61469` |
| Peter's `TDStep` | 2, shapes 84-85 (one and two edges; calibration) | not proven, timeout (shape 84 did not finish) | 1800 s | 1.58 GB | `peter_cal.log` | `88b3e300c82c2a82b0e3e8a8a9f270af6c939913e3a34e294bc684fce1d67297` |
| `TDStepMAA` | 2, s95 | not proven, timeout | 900 s | 0.71 GB | `maa_s95.log` | `0b977ce84bf6445336917149bb8cdd42922c06b6a27af282f345fefa4e0463ec` |
| `read_before_wait` (Peter) | 2, s95 | not refuted, timeout | 900 s | 1.18 GB | `peter_read_before_wait.log` | `0e631ff9b4d9864963c9fe8ddc81e53cfa1f623cae86a0dc1a4e63feb6e21bb8` |
| `TDStepMAA` wait deleted | 2, s95 | not refuted, timeout | 900 s | 0.74 GB | `maa_wait_deleted.log` | `00f446d1642d3ffb6c6fea1c265751db37f96f7023f658954573b3e1d574ee1d` |
| Summary tests (range loop 2, 1, 0 lanes; concrete and symbolic `parent`) | — | 3/3 pass | 21 s | 0.34 GB | `test_summaries.log` | `8232a5ecba1ff4910dc198e4dcdfcc369b2701cf7b0f1a6032a9463caabc0923` |
| `dropped_wait`, `index_wrap`, `chunk_off_by_one`, `forged_frontier`, `dropped_continuation`, `skipped_cas_recheck` (Peter) | 2, s95 | not run to a verdict (see below) | — | — | — | — |
| `TDStepMAA`: old wait rule, CPU read of `parent`, wait on tile6, wait on tile7 | 2, s95 | not run to a verdict (see below) | — | — | — | — |

Lever 2 verdict: shape 95 failed, so the whole lever-2 verdict is "not proven" for both units
(map 19 item 4). The other 199 shapes were not run: no result of theirs can change it. Total
lever-2 wall time: 900 s per unit (s95), plus 1800 s of calibration.

**Controls.** SAW reports a failed check only after the whole simulation ends, and a control has
the same simulation as the safe unit. Both controls run (one per unit) timed out with no verdict.
The remaining ten were not run: about 2.5 hours of the shared Mac lock to record ten more
timeouts. The first three Peter controls (`index_wrap`, `chunk_off_by_one`, `dropped_wait`) did
run once, but stopped at SAW setup: a missing symbol, now fixed. Those logs are in
`superseded/`. `run_spike.sh` lists all twelve control jobs with the check each must hit.

**Encoding attempts** (`dev/`, each one job of at most 15 minutes, all on Peter's unit; the
files of each attempt are copied next to its log):

| Attempt | Change | Result | Log sha256 (first 16) |
|---|---|---|---|
| lever 1, 1 | SAW ghost state (`declare_ghost_state`), record via `llvm_fresh_cryptol_var` | timeout, 3.7 GB | `e3a4990624f80184` |
| lever 1, 2 | hazard state in one harness global (What4 folds it) | timeout, 2.4 GB | `91c1f16a7ad19aeb` |
| lever 1, 3 | transitive producer masks computed at issue, hash-consing | timeout, 2.1 GB | `572716f3e5798b4a` |
| lever 2 s95, 1-2 | shape split; one global per state field | timeout | `b7f0c237835a3d04`, `b5440b6a7b7a99ad` |
| lever 2 s95, 3 | SMT-array memory model | timeout (solver 577 of 600 s) | `abc1825c1eab9fef` |
| lever 2 s95, 4 | SMT arrays, path-sat off | out of memory (8 GB watchdog, 443 s) | `2989aca444c57993` |
| lever 2 s95, 5 | default memory, path-sat off | timeout | `b3cb10b23efd3067` |
| diag 1 | all inputs concrete (Peter; attempt-1 encoding) | proven, 6.7 s (8.2 s wall) | `b6d41f4e299a1d01` |
| diag 2-4 | s95, neighbors concrete, `parent` symbolic | timeout at 600-1500 s | `64c267f901793f61`, `59e639c112984003`, `bb17da5df154c90c` |
| diag 6 | `TDStepMAA` all concrete / `parent` symbolic | proven, 8.2 s / timeout | `e600299d7a51239f` |

**Failed and unexpected runs, root-caused:**

1. **Every proof job: timeout.** Cause: path explosion over value-dependent CPU branches, with
   slow override application on symbolic memory (above). Class: timeout.
2. Lever 2 attempt 4: **out of memory** (watchdog kill at 8 GB). With the SMT-array memory model,
   memory reads stay symbolic, so concrete loop bounds look symbolic; with path-sat off, the
   loop unrolled until killed. Class: out of memory.
3. **SAW could not read one 81-word global back across slice writes** ("Error when loading
   through pointer", `llvm_points_to_untyped` slices). Fixed with one global per field. Class:
   unsupported construct.
4. **"Global symbol not allocated"** at setup: brace-initialized structs of global addresses
   become constant globals that SAW cannot allocate. Fixed with member-wise set-up. Override specs
   that name a global also need `llvm_alloc_global`. Class: unsupported construct.
5. **"Could not find definition for function"**: a control that never calls `wait_ready` has no
   such symbol to override. Fixed with a never-called function that keeps every summarized
   symbol. Class: tool crash (setup).
6. **Parse warnings:** about 380 lines of `METADATA_IMPORTED_ENTITY ... Invalid record size: 8,
   expected [6, 7]` from libc++ headers in clang 22 bitcode. Not fatal; ticket 05's fixture had
   no standard headers. Class: parse error (warning only).

Runs folder (LR-06): `/tmp/claude/probata-runs/t06/`, budget 300 MB, used 17 MB. Readers: this
ticket and 09. `README.txt` there records this. Verifier scratch was deleted after each job.
Notes for later tickets: `/tmp/claude/probata-poc-notes/saw-two-lanes.md`.

**For 09 (options, not tried here):** a larger machine does not help, because the budget is per
job. What might help, each a design change for Yan-Ru:

- split on values too, for example `parent` sign patterns and neighbor targets per shape. That is
  about 3,340 graphs times frontiers times patterns, so mbit10 work.
- summarize the CPU claim loop per lane, so that the proof no longer explores the CPU code.
- try crux-llvm on the same summaries as hand stubs.

Assumption: "proven" means P2 (map 08, plus "an unreached vertex keeps its parent") and hazard
freedom (P1, the probes and summary preconditions).
Assumption: the frontier window starts at queue index 0 (one chunk at these bounds). The queue
entries past the frontier stay symbolic.
Assumption: an unvisited vertex's `parent` is any value in [-3, -1], the values `InitParent`
writes at these bounds, not tied to the vertex's own degree. This is wider, so the proof would be
stronger.
Assumption: `TDStepMAA` EDIT 1: its tile-size ladder has no `TILE_SIZE` 2 rung (its `#else` is
`assert(false)`). The scaled ladder takes one full tile per core, and uses `>=` where the authors
use `>`, so that a frontier of 2 fills 2 lanes. EDIT 2 moves `__restrict__` after `*`, because
clang 22 rejects the authors' placement.
Assumption: hazard footprints are tracked per memory region, not per element (stricter than map 12
item 4). A store without a destination tile is not summarized: neither unit issues one.
Assumption: the old wait rule (`TDStepMAA` control 2) swaps only the wait summary (it covers the
writer and its producers); the other gem5 stalls stay.
Assumption: lever-2 jobs keep path-sat on and run one shape per `llvm_verify`. Each shape's own
wall time is SAW's `time`. A batch's peak RSS is per SAW process.
Assumption: verdicts go in this Answer, not in `proof` records (ticket Notes).

fail after both levers

## Continuation: CBMC box (2026-10-14 12:08 ET)

Yan-Ru chose ticket 09's proposed re-plan option 1 (2026-10-14 12:08 ET): a one-day box running CBMC 6.11
(SAT-based bounded model checking; the design's last bounded fallback, "CBMC on the C lowering") on this
spike's two units, hand-lowered to C with the same summaries as C stubs, at the same minimum bounds, plus all
12 single-thread controls. The pass bar is unchanged: both units proven and every control refuted, each job
under 15 minutes. Every SAW result above stays in the record. The box ends 2026-10-15 12:08 ET.

### Continuation Answer (2026-10-14 12:45 ET)

**Verdict: pass via fallback (CBMC).** CBMC 6.11 proves both units at map 19's minimum bounds:
Peter's `TDStep` in 3.4 s, `TDStepMAA` in 5.6 s. It uses lever 1 only: every input is symbolic,
with no shape splitting. All 12 single-thread controls are refuted, each at its expected check,
in 1.0-5.2 s. Peak RSS is at most 0.70 GB. Every number is a **Mac result** (host `mac`). No
mbit10 run was needed: every batch waited 0 s for the lock.

**Why CBMC scales where SAW did not.** CBMC puts every path into one SAT formula. A
value-dependent branch (the claim `hint<0 && CAS`, the push `tile4 && tile5<0`) becomes an
if-then-else term, not a separate path. The summaries are small bit-vector functions. SAW
explored the branch outcomes one path at a time and paid for override matching on each path.

**Prototype:** [`../prototype/06c-cbmc/`](../prototype/06c-cbmc/).

| File | Role | sha256 |
|---|---|---|
| `dx100_stubs.h` | ticket 06's per-call summaries (`summaries.saw` over `ghost.cry`) as C stubs. Each SAW precondition is a `CHECK`: a named `__CPROVER_assert`, then `__CPROVER_assume` | `6b7653dc4b317c57324b2efa20bc514883f72ce40d55dcce87d9e049e085b014` |
| `common.h` | inputs, queue buffer, P2 (from `unit_common.hpp`) | `bc79af83420e8a9428b56221775ef7173711fcf0e2ca81faaec69ead8e40c682` |
| `unit_peter.c` | unit 1, hand-lowered: `bfs_read_offload.inc` (sha256 `3c5867a2b8919806…`) through `spike_lowering.hpp`'s lowering, seams and faults | `e85123ad4d6faf5a79f18b6ec2a47aea4b326bb2ab85c189c70c167aa93844cc` |
| `unit_maa.c` | unit 2, hand-lowered: `unit_maa.cpp` (same EDIT 1, EDIT 2, PROBEs, controls) | `901316fb59326c66ebd874354d8dbe70089a9dfbe6f6b5570e3df44e823bca9c` |
| `harness.h` | CBMC harness (one `__CPROVER_assume` per `units.saw` precondition; sanity builds); native harness of the faithfulness tests | `0b260e6a76b4f32dcf382a664ee932cf610bea85d7d89b6a70d0dfc0fe9fef90` |
| `run_cbmc.py`, `cbmc_job.py` | job table, unwind bounds, one-at-a-time runner (900 s per job, per-job peak RSS), verdict check | `c609dcc03fe5a48533edab51f99460011d3dd65cf8c93266512e31dd2c14969e`, `5d2bbac4724d3f3b7741ebce77c877975a0b3e18762c8d32096fdf77a3eae59a` |
| `faith/run_faith.sh`, `faith/faith_cxx.cpp`, `faith/shim/cassert` | faithfulness test 1 (C lowering vs C++) | `7b16046343b7660787258836c4f6c10aa49ea08756d7437b47af2dd2b14f8391`, `4a3d13a8612b9f9683f2cacf08c2ef55a6dfe768642a825ef10803629af82215`, `3b4b1f67a7e66e3a0002eef73b5f4a9f8922aecb833cb72955e60a39a086a8d9` |
| `faith/stub_vectors.py`, `faith/stubcheck.cry` | faithfulness test 3 (C stubs vs `ghost.cry`) | `56c0e73e98485793c0c8c9a4665c14703beaefcb0225a723c2e614c77c2e83e8`, `5a697c73561e3a5f01c2c7cbcf6ae7032f8be7aa9f334de563d24a52fc6cbab9` |

The C++ sources and the proof semantics are the files the SAW runs used: `ghost.cry` `3257cb18…`,
`unit_peter.cpp` `bbfd3da6…` and `unit_maa.cpp` `319f3556…` (full values in the SAW table above).

**Recorded setup.**

- Tool: CBMC `6.11.0 (cbmc-6.11.0) 64-bit arm64 macos` (Homebrew).
- Invocation: `cbmc unit_<unit>.c -DSWDB_CBMC [control flags] --unwind 9 --unwindset <per loop>
  --unwinding-assertions --sat-solver cadical --slice-formula --trace`.
- CBMC's default checks stay on: array bounds, pointers, division by zero, signed overflow and
  undefined shifts. So SAW's memory-safety goals are kept.
- Build constants as for SAW: `TILE_SIZE` 2, `NUM_CORES` 1, `SWDB_CHUNK_SIZE` 2, 8 tiles and 8
  registers per core.
- Symbolic inputs as for SAW:
  - the frontier threshold, >= 1;
  - a graph of 3 vertices and 0-3 edges;
  - a frontier of 0-2 distinct visited vertices;
  - `parent[v]` in [-3, 3);
  - the acceleration flag;
  - the queue past the frontier, and tile memory.
- DX100 state at entry: g0 (nothing pending).

**Unwind bounds.** CBMC's bound K is the iteration count + 1. A check on a 3-iteration loop
confirmed this: K = 3 fails its unwinding assertion and K = 4 passes (`dev/unwind-semantics/`).
Every fixed loop gets `--unwind 9` (8 tiles, 8 registers, P2, the 5-step range fold). Each
data-dependent loop gets a bound derived from the sizes:

| Loop | Iterations from the bounds | K |
|---|---|---|
| chunk loop (Peter) | ceil(frontier 2 / chunk 2) = 1 | 2 |
| range loop (`for(;;)`, `do while`) | <= edges 3 non-empty calls + 1 empty call = 4 | 5 |
| lane loop | <= `TILE_SIZE` = 2 | 3 |
| CPU frontier loop / CPU edge loop | <= frontier 2 / <= out-degree 3 | 3 / 4 |
| `TDStepMAA` `while (idx < len)` | 1 (tile path adds 2 >= len; CPU path sets idx = len) | 2 |
| queue flush | <= pushes <= edges 3 + 1 forged duplicate = 4 | 5 |

Every unwinding assertion holds in every job, so each proof is complete at these bounds.

**Results.**

- Runs folder: `/tmp/claude/probata-runs/t06c/`, host `mac`. Batch log `final.log`, sha256
  `08b0da73298db9aa…`.
- Each job log has a `.log.json` with exit code, wall time, peak RSS and sha256.
- Bounds for every row: threads 1, lanes 2, chunk 2, vertices 3, edges <= 3, frontier <= 2,
  `parent` in [-3, 3). Every row uses lever 1.

| Subject | Verdict | Failed checks (counterexample for each) | Wall | Peak RSS | Evidence | sha256 |
|---|---|---|---|---|---|---|
| Peter's `TDStep` | **proven** (687 properties) | - | 3.42 s | 0.40 GB | `peter.log` | `f5c63f5ccae1bf8da12467431a3f4460e162f43fda5c4e78648e9594590525e0` |
| `TDStepMAA` | **proven** (725 properties) | - | 5.58 s | 0.67 GB | `maa.log` | `abdec31b684f2896cc6721367bf4568ba3c3e31cb88c9756904fd34e76981908` |
| `dropped_wait` (Peter) | refuted | `size_read_before_ready` | 1.04 s | 0.16 GB | `peter_dropped_wait.log` | `45414007fc02ce85efb2fdb871716e6e851247bedc30ae7ee685b8fcd71d52e9` |
| `read_before_wait` (Peter) | refuted | `tile_read_before_ready` | 2.99 s | 0.38 GB | `peter_read_before_wait.log` | `c7f798d18e8a22e74771f6124617459c332f0a53a07f9fb913b05d6d6f285d7c` |
| `index_wrap` (Peter) | refuted | `stream_bounds` | 2.89 s | 0.38 GB | `peter_index_wrap.log` | `9ee4c225f955d56f89474bb4112b4e04302e6f35773ecc7563c3daf4e115a2fe` |
| `forged_frontier` (Peter) | refuted | `P2_reached_pushed_exactly_once` | 3.67 s | 0.41 GB | `peter_forged_frontier.log` | `0f0ca25f1e4bc19116b5d36c08cbfe8f87e6c1ca8e3485a3dd3eca26ed1ccc93` |
| `dropped_continuation` (Peter) | refuted | `P2_reached_pushed_exactly_once`, `P2_parent_is_frontier_neighbor` | 3.38 s | 0.39 GB | `peter_dropped_continuation.log` | `0b8e785da25f247766b6b95891548018791c4b052ec81b80fafcd2c826765f64` |
| `chunk_off_by_one` (Peter) | refuted | `tile_truncation` | 3.04 s | 0.37 GB | `peter_chunk_off_by_one.log` | `37bc6f9c293bc6f1e94b38926fda296f784e7a425e2354252e4c6f347bf0226c` |
| `skipped_cas_recheck` (Peter) | refuted | `P2_reached_pushed_exactly_once` | 3.65 s | 0.39 GB | `peter_skipped_cas_recheck.log` | `8c87cbcbb56de1421bf21c31f32243836e191cedf4019fa672d78372c7f7ecec` |
| `TDStepMAA` wait deleted | refuted | `tile_read_before_ready` | 5.16 s | 0.64 GB | `maa_wait_deleted.log` | `1f6f7edb51308013171685f57f44e67c575d958ee9ec07700f41bd34f58edb78` |
| `TDStepMAA` old wait rule | refuted | `tile_read_before_ready` | 5.19 s | 0.67 GB | `maa_old_wait_rule.log` | `13d292c6188ecd96f1b6a67297302fa95676c2a78782392aa2084c384bbbc2af` |
| `TDStepMAA` CPU read of `parent` | refuted | `cpu_access_overlaps_unfinished` | 4.97 s | 0.65 GB | `maa_cpu_read_parent.log` | `6847980133a92e9852377faa1c2f3b7a41ab8100bb79e032a451b9bd14e6f327` |
| `TDStepMAA` wait on tile6 | refuted | `tile_read_before_ready` | 5.23 s | 0.64 GB | `maa_wait_tile6.log` | `b553b69bb39731ff64d07a00b56fce74ec8f5205bc50b5c7acbfd65696019afb` |
| `TDStepMAA` wait on tile7 | refuted | `tile_read_before_ready` | 5.22 s | 0.63 GB | `maa_wait_tile7.log` | `5b8558cd43d94af81b8a81b37eee6a1b5f51c5064afa3330a681611d4a5b5e2b` |

Each refutation is attributable:

- every failed property of the job is the control's expected check (the checks `run_spike.sh`
  names for SAW);
- no unwinding assertion fails.

Example counterexample (`TDStepMAA` wait deleted):

- inputs: frontier {0, 1}, offsets [0, 3, 3, 3], neighbors [2, 1, 1], `parent` [0, 0, 0];
- failure: the tile-0 probe passes, then the CPU reads tile 4 (the compare's result) before any
  wait covers it.

**Faithfulness checks.** All pass. Without them the verdict would not count.

1. **The C lowering agrees with the C++ on concrete inputs.** `faith/run_faith.sh` compiles two
   sides against the same stubs and the same native harness:
   - ticket 06's C++ units, unchanged (Peter's `.inc` included as is);
   - the C lowering.

   It runs **every input of the bounded domain** on both sides:
   - inputs: 334 CSR graphs x 216 `parent` vectors x every frontier; for Peter, also
     acceleration off/on x threshold 1-3. Tile memory is zero.
   - runs: 1,731,456 per Peter build and 288,576 per `TDStepMAA` build.
   - builds: the 2 safe builds and all 12 control builds.
   - each run prints the failed check, the failed P2 properties, a hash of the final state
     (queue, `parent`, tile memory, the whole hazard state) and a hash of the DX100 call trace
     (every call with its arguments, in order).

   Results:
   - **All 14 builds print identical output on both sides** (`faith/faith_summary.txt`
     `aa67e9b200e30e47…`).
   - The safe units fail nothing on any input.
   - Every control fails only its expected check, on 6,480-324,648 inputs.
   - Ticket 06's SAW concrete input (diagnostics 1 and 6: frontier {0, 1}, edges 0->2, 1->2,
     1->0, `parent` [0, 0, -1]) gives identical full traces (`faith/concrete_peter_*.txt`
     `409264dc1f71f946…`, `faith/concrete_maa_*.txt` `358d4593ec5bde6c…`).
   - CBMC proves both units on that input in 0.39 s / 0.49 s (`peter_concrete.log`
     `032fdce9bf72c0a5…`, `maa_concrete.log` `89cc90afb3494679…`).
2. **Sanity controls** (same harness and flags):
   - Non-vacuity: two reachability assertions are refuted in both units: the harness end, and
     an accelerated claim that changes `parent` (`peter_sanity_reach.log` `57025d3b14439dad…`,
     `maa_sanity_reach.log` `07e51e29c7e134de…`). So the preconditions are satisfiable and the
     DX100 path runs.
   - A precondition deleted, refutation expected: without "each real edge's target is a vertex",
     both units are refuted at exactly the checks that rely on it (`peter_drop_pre_neighbor.log`
     `4f043f05290d68f1…`, `maa_drop_pre_neighbor.log` `a8f20fa4997fb977…`):
     - the gather's memory region (DX100 path);
     - CBMC's bounds check on `parent[v]` (CPU path);
     - `P2_pushed_is_a_vertex`.
   - A precondition deleted, proof expected: without the lower bound -3 on `parent`, both units
     still prove (4.2 s / 5.9 s). This is expected: the code treats every negative value as
     unvisited (`peter_drop_pre_parent_lower.log` `a9ef88f41dcd248e…`,
     `maa_drop_pre_parent_lower.log` `e5da86b038ac5551…`).
3. **The C stubs agree with the SAW summaries** (added, not asked for).
   - Calls: `faith/stub_vectors.py` logs 16,193 summary calls, with the state before and after
     each. They come from the SAW concrete input plus a pseudo-random sample of the domain, over
     all 14 builds, and include every failed check.
   - Check: Cryptol (SAW 1.6's bundled `cryptol`) evaluates each call against `ghost.cry`'s
     function of the same name (`faith/stubcheck.cry`). A completed call needs its precondition
     true and an equal post-state; a failed call needs its precondition false.
   - Result: **all 16,193 hold.**
   - Checker sensitivity: we took one call of each summary kind and changed one tile-memory word
     of its post-state by 1. The checker rejects every one: 10 of 10 (Peter) and 12 of 12
     (`TDStepMAA`) (`faith/vectors/eval.log` `f887fadc1b7b05ea…`).

**Encoding attempts** (each a batch of jobs of at most 15 minutes, run one at a time):

| Attempt | Change | Result | Log sha256 (first 16) |
|---|---|---|---|
| unwind semantics | 3-iteration loop at K = 3 and K = 4 | K = 3 fails the unwinding assertion, so K = iterations + 1 | `259fbcb634979cfe` (`k3.log`) |
| 1 (`dev/a1`) | CaDiCaL, `--slice-formula`, all 22 jobs | units proven 3.5 s / 5.5 s; 12/12 controls refuted; sanity 7/8 (see failed run 1 below; table fixed, no code change) | `9593315bbc7a2bff`, `dde29b35b1741c10` |
| final | as attempt 1 (the verdict runs above) | 22/22 as expected | `08b0da73298db9aa` |
| 2 (`dev/a2`) | CBMC's default SAT solver, no `--slice-formula` | units proven 2.3 s / 4.0 s; 12/12 controls refuted at the same checks. The verdict depends on neither the solver nor slicing | `44560392e7c04700` (Peter), `5b42b6bc6297662b` (`TDStepMAA`) |

Neither lever 2 (shape splitting) nor value splitting was needed.

**Failed and unexpected runs, root-caused:**

1. Attempt 1, sanity control `*_drop_pre_neighbor`.
   - What happened: it was refuted as intended, but the checker rejected it. The failed set also
     held `P2_pushed_is_a_vertex`.
   - Cause: my expected-check table left that check out. An invalid edge target is pushed on the
     CPU path, so the check correctly fails.
   - Class: harness expectation error.
2. Unwind-semantics test, K = 4.
   - What happened: "VERIFICATION FAILED" on `no body for callee nondet`.
   - Cause: CBMC 6.11 flags any function without a body unless its name starts with `nondet_`.
     The test file's helper was named `nondet`. The harness uses `nondet_i32`, and no unit job
     shows this property.
   - Class: test-file artifact.

Runs folder (LR-06): `/tmp/claude/probata-runs/t06c/`, budget 500 MB, used 28 MB. Readers: this
ticket and 09. The heartbeat file `heartbeat.md` is in the same folder.

**What A2 should change.** These are proposals for Yan-Ru; the design spec is not edited here.

- **The bounded verifier becomes CBMC 6.11 on the C lowering** (map 11 item 2's last fallback).
  05's SAW decision stays as the record of spike (a).
- **21 (C lowering) comes before the bounded adapter.**
  - The hand lowering here is a stand-in, not 21's tool.
  - The lowering becomes a trust point. Each bounded job should carry faithfulness test 1: a
    differential run of the C lowering against the compiled C++ over the bounded domain.
- **22 becomes a CBMC adapter on 21's C lowering** (no SAW translator). It should:
  - emit the summaries as C stubs, with one named `assert` + `assume` per check, so a
    refutation names its check;
  - derive `--unwindset` from the sizes and keep `--unwinding-assertions` on;
  - add the reachability sanity asserts;
  - replay counterexamples on the C++ (Yan-Ru's `spurious_counterexample` class).
- **30 (summaries)** generates the C stubs from one proof-semantics source, with a vector check
  against that source like faithfulness test 3. Here, Cryptol `ghost.cry` was the source of truth.
- **33 (minimum-bounds script, A2 exit)** reproduces these 14 verdicts with generated stubs.
  Lever 2 is not needed at the minimum bounds.
- **61 (SAW whole-function equivalence)** loses its tool. Options: a CBMC equivalence harness on
  two C lowerings, or a re-plan.
- **Unchanged:** 46/47 (CIVL, GenMC) and the k-thread controls. This box proves threads = 1 only.

Assumption: the lowering replaces `__sync_bool_compare_and_swap` and `__atomic_*` with plain loads
and stores, and drops `__restrict__`. Both changes are exact at threads = 1, the spike's bound.
Assumption: CBMC's `nondet` inputs plus one `__CPROVER_assume` per `units.saw` precondition match
SAW's `llvm_fresh_var` + `llvm_precond`. The proofs are of the C lowering. Faithfulness tests 1 and 3
are the evidence that it is the same program with the same summaries.
Assumption: faithfulness test 1 fixes tile memory to zero, because every unit writes a tile before
it reads it. The CBMC proofs keep tile memory symbolic.
Assumption: a `CHECK` is an assertion and then an assumption, because SAW stops a path at a failed
precondition. A failed check is still reported. Later checks are judged only on paths where the
earlier ones held.

pass via fallback (CBMC)
