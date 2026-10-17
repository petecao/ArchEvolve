# 57 — Proof workers in a socket lane

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 03:48 ET (resolved: Answer); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 04, 12, 56
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Providers and machines" (mbit10), "Records and levels" (job block, where things live), "Evaluation design" (protocol), "Bounds" (bounded-job budget), "Proof-of-concept plan" (A6); S1, O9); decisions: [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) item 6; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 2 (A6); [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 5, 6; [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 8
**Time estimate:** about 2 days

**What to build:** One mbit10 lane job that runs up to 6 proof workers inside one socket lane. The job
enters the lane only through the lane script, after checking both socket leases and the legacy lease.
Each worker is pinned to its own core, under an 8 GB RSS watchdog (design O9; `ulimit -v` is added
only for tools that start under it), and runs `swdb prove` jobs. Each proof record's job block gets
every field on 12's job-block field list, filled on mbit10: adapter, host, worker core (the pinned
core), wall time, CPU time, batch load, peak RSS, batch ID and position in the batch. Configurations
under comparison are
interleaved within a batch, so host load hits them alike. This is the machinery 58 and the
evaluation's proof runs use.

## Acceptance

- [x] **Lane entry.** Before dispatch, both socket leases and the legacy lease are checked and their
  states recorded. The job runs only through the lane script, from an up-to-date MemAcc checkout whose
  lane script was compared with the repository version first. Negative control: started without the lane
  script, the batch refuses to run.
- [x] **Up to 6 workers, each on its own core.** Each worker is pinned to a distinct physical core of
  the lane's socket (no two workers on hyperthread siblings; the lane procedure allows no
  hyperthreads). Negative control: a batch plan asking for 7 workers is refused, or capped at 6 with
  the cap recorded.
- [x] **8 GB RSS watchdog per worker** (design O9). Each lineup tool is tried once under an 8 GB
  `ulimit -v` and the result recorded; the cap is added only for tools that start under it, and the
  rest run under the watchdog alone. Negative control: a fixture job whose RSS passes 8 GB is ended by
  the watchdog with failure class "out of memory", and the other workers carry on.
- [x] **Job block fields.** Each proof record's job block holds every field on 12's job-block field
  list: adapter, host, worker core, wall time, CPU time, batch load, peak RSS, batch ID and position
  in the batch (12 owns the list; this ticket fills it on mbit10 and adds no field). Worker core is
  the pinned core; peak RSS is the value the worker's watchdog reads. `swdb validate` and
  `swdb build` accept them; a lane-job record missing any of 12's fields is rejected.
- [x] **Interleaving.** A batch with two configurations of the same subjects runs them interleaved, not
  grouped, and the records' batch ID and position in the batch show the order. Negative control: a
  batch plan that groups one configuration first is reordered or refused.
- [x] **A real batch.** At least 12 jobs that run real tools from the 56 lineup (07's smoke programs,
  two configurations) complete in one lane job. They go through `swdb prove` with whichever real
  adapters exist by then (21, 22, 46, 47); a tool with no adapter yet runs under the same worker wrapper.
  Each verdict matches the same job run alone. The batch mechanics are also tested with the scripted
  adapter.
- [x] **Output.** `df -h /data1 /data` is recorded before the batch. Raw output goes to
  `/data1/yanruj/EvolveSWDB_runs/<run-id>/` (or `/data/yanruj/EvolveSWDB_runs/` when `/data1` is low).
  Compact evidence is named by path and sha256. Verifier scratch is deleted when each job ends. Nothing
  goes under `$HOME`.
- [x] **Host record.** Each batch records the host load at start and end, free memory on the lane's
  node, and the ArchEvolve commit. A batch longer than 30 minutes gets the LR-07 heartbeat.

## Notes

- **Not in this ticket:**
  - 56 — Verifier lineup on mbit10: the installs.
  - 04 — Proof record tracer: the `proof` record kind; it writes the job block.
  - 12 — Proposal and promotion fields (upstream): the one job-block field list (peak RSS, batch ID
    and position in the batch included), what each field means and how it is validated.
  - 58 — Mac verdicts reproduced on mbit10: the reproduction and the budget recalibration that run on
    this machinery.
  - 11 — Method-version file and failure classes: budgets and the failure-class list.
- Assumption (not decided in the map): the lane job is one lane-script call whose command runs a batch
  of `swdb prove` jobs, up to 6 at a time. The batch's entry point and plan format are not decided.
- Assumption (not decided in the map): the batch checks it runs under the lane (for example, that the
  socket lease is held by its own lane-script call). This is the deterministic check behind the "refuses
  without the lane script" control (LR-04).
- Assumption (not decided in the map): interleaving is checked from each job's batch ID and position
  in the batch, two fields on 12's list.
- **Why a watchdog, not `ulimit -v` alone (design O9, default until Yan-Ru rules):** the map calls the
  cap an "RSS cap" (23 item 6) but sets it with `ulimit -v` (19 item 8), which caps virtual address
  space, not RSS. The JVM (CIVL) reserves its heap up front, by default a quarter of host memory, and
  fails to start under a low `ulimit -v` unless its heap flag is set below the cap. GHC-built SAW also
  reserves a large address range. So the RSS watchdog is the cap every worker gets.
- **Memory check:** 6 workers x 8 GB = 48 GB. The lane script binds memory to one node (about half of
  the host's 125 GB), so record that node's free memory before each batch.
- Counters were unavailable to `yanruj` when last checked (2026-09-22); re-check before relying on
  either answer. Wall and CPU time come from the operating system, not from hardware counters.

## Answer

2026-10-14 03:48 ET. **One mbit10 lane job now runs a batch of up to 6 pinned, watched proof workers,
and every check passed on mbit10 in lane node 1.** A real batch of 16 jobs (12 real-tool jobs, 4
`swdb prove` jobs) gave the same 16 verdicts with 6 workers as with each job alone. Two jobs that climbed
past 8 GB were ended `out_of_memory` while the other four finished.

**What was built** (branch `probata-poc/t57`; interface: `docs/reference/format-v0.4-proof.md`, "Proof
workers in a socket lane"):

| Piece | Where |
|---|---|
| Batch plan, interleaving, cores, lane check, host record, tool jobs, compare | `swdb/proof_lane.py` (`swdb prove-lane leases / run / compare`) |
| RSS watchdog (tree RSS from `/proc`, psutil on the Mac; kill above the cap) | `swdb/rss_watchdog.py` |
| Worker watchdog inside `swdb prove` (cap from `SWDB_WORKER_RSS_CAP_BYTES`; `peak_rss_bytes` = its reading; above the cap: `out_of_memory`) | `swdb/proof.py` `_run_job`, `_worker_watch` |
| Scripted adapter `run` key (a stand-in tool process for watchdog fixtures) | `swdb/proof.py` `ScriptedAdapter` |
| mbit10 entry: host, stale lane script, leases, disk, dirty checkout, then `socket_lane.sh` | `scripts/mbit10/prove_in_lane.sh` |
| The plans of this run (probe, batch, alone, oom) and the proof seed | `scripts/mbit10/probata_lane_batch.py`; `tests/test_proof_records.py` `build_proof_seed` |
| Tests (13; on the Mac the pinned-core test skips) | `tests/test_proof_lane.py` |

**mbit10 run** (2026-10-14 03:39–03:46 ET; ArchEvolve worktree `/data1/yanruj/ArchEvolve-probata-t57` at
`13654e8c`, clean; the main checkout `/data1/yanruj/ArchEvolve` stayed at `yanrujhou_main` `680298a3`).
Lane node 1 through `/data1/yanruj/Memacc-evolveswdb-lane` `socket_lane.sh` (Memacc `76cca359` = its
`origin/yanrujhou_main`), lease generations 581–590. Before every dispatch all three leases were
`released`; each check is in `lanes/*.leases.json`. Host load 0.15–1.83 (another user's light work).
Lane node 1 had 55.5 GB free at batch start. `/data1` had 17 GB free, under the 20 GB rule, so raw output
went to `/data/yanruj/EvolveSWDB_runs/probata-t57-20261014/` (under 10 MB). `df -h /data1 /data` is in
each `batch.json` (`host.df_before`). Nothing was written under `/home/yanruj` (`find -newermt` empty).

| Batch (folder under the run root) | What it shows |
|---|---|
| `batch.t57.20261014.probe` | the `ulimit -v` probe |
| `batch.t57.20261014b.batch` | 16 jobs, 6 workers on cores 1, 3, 5, 7, 9, 11; grouped plan reordered |
| `batch.t57.20261014b.alone` | the same 16 jobs, 1 worker |
| `batch.t57.20261014b.oom` | the watchdog negative control |

`batch.json` sha256: probe `d6c135986efb2a391045f9e0cd457677b87c7eedce1facc941e3029322e1a226`; batch
`81ec02804b9dfc15235b2027631ca1efda835f47e9c027306e8d8915c328c5f3`; alone
`983a511abab5052d4cc605dce8392070f1862cbe6976a240996a2be10029435d`; oom
`f38385a63c025ea178339c95623c891cde0dfddc10ba6c57d92fd62f5b424f05`.
(`batch.t57.20261014.batch` and `.alone` are a first pass whose crux-llvm counterexample pattern matched
parser warnings; same verdicts; superseded by the `…b` pair.)

- **Lane entry.** `prove_in_lane.sh` compared the lane script with `FETCH_HEAD`, recorded all three lease
  states, then entered the lane. Inside, `swdb prove-lane run` verified the lane from the kernel and the
  lease file (`mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 588)`).
  Negative control: run directly on mbit10 outside the lane, it refused with exit 1 (`not started through
  socket_lane.sh`) and created no batch folder. The same control is a test.
- **Workers and cores.** The 6 workers took cores 1, 3, 5, 7, 9 and 11: one logical CPU per physical
  core, never a sibling (the siblings are 33, 35, …). Every prove record's `worker_core` is its pinned
  core (6 distinct cores in `swdb_proof_jobs`). A plan asking for 7 workers is refused with exit 2 (test).
- **`ulimit -v` probe** (8 GiB cap, each tool's safe smoke program once): CBMC, crux-llvm, Frama-C/WP,
  SAW, CIVL (with its `-Xmx4g`), GenMC, Z3 and CVC5 start and give their expected verdicts. **Rocq does
  not:** `Fatal error: Not enough heap memory to reserve minor heaps` (OCaml 5 reserves address space up
  front; exit -6). So the cap is added for the first eight, and Rocq runs under the watchdog alone.
- **Watchdog control** (`oom` batch, 6 workers): a tool job and a `swdb prove` job (scripted, `run`
  allocating 9 GiB) were ended at 8,209 MiB and 8,250 MiB peak, both `not_proven` / `out_of_memory`. The
  four calm jobs (CBMC, WP, crux-llvm, a scripted prove) were proven. The prove job's record holds
  `peak_rss_bytes: 8651071488` from the worker watchdog and validates.
- **Job block.** All 18 proof records written on mbit10 carry the nine fields of 12's list with
  `host: mbit10`, the pinned core, `batch_load {start, end}` and the watchdog's peak. `swdb validate`
  (75 records valid) and `swdb build` accept them. A record missing a field is refused by 12's schema,
  which ticket 12's parametrized test covers; this ticket adds no field.
- **Interleaving.** `batch.yaml` was written grouped (all A, then all B). The batch recorded
  `interleaved_as_given: false` and ran A,B,A,B,…; each record's `batch` and `position` show that order.
  An interleaved plan keeps its order (test).
- **The real batch.** 12 real-tool jobs (07's `smoke.c`, `smoke_crux.cpp`, `smoke_wp.c`, safe and seeded
  bug; A = each tool's default solver path, B = CBMC `--z3`, crux-llvm `--force-offline-goal-solving`, WP
  `-wp-prover z3`) plus 4 scripted `swdb prove` jobs. Verdicts: CBMC safe proven, buggy refuted (`x=41`);
  crux-llvm safe proven, buggy refuted (`Found counterexample`); WP safe proven, buggy `not_proven`
  `timeout` (WP never refutes); scripted as scripted. `swdb prove-lane compare` of batch and alone:
  16 of 16 match.
- **Scratch.** Each job's scratch folder was deleted when it ended (none left). Logs stay, with their
  sha256 in each job's result.

**Tests.** Mac: `tests/test_proof_lane.py` 12 passed, 1 skipped (pinned cores need Linux); the proof
suites `test_proof_records.py`, `test_proof_run_fields.py`, `test_proof_method_version.py` 153 passed.
mbit10 (inside lane node 1, swdb test venv): `tests/test_proof_lane.py` 13 passed.

Assumption: no real adapter exists yet (21, 22, 46, 47 are open), so the 12 real-tool jobs run as `tool`
jobs under the same worker wrapper and write a result file with the same nine job-block fields (adapter
`none`), not a proof record. The ticket allows this.
Assumption: the batch's entry point is `swdb prove-lane run` with a YAML plan (`proof_lane_batch.1`);
`prove_in_lane.sh` is the supported way in on mbit10.
Assumption: a plan asking for more than 6 workers is refused (exit 2), not capped.
Assumption: "interleaved" means that in every prefix no configuration runs more than once ahead of
another; any other plan is reordered round-robin, and the order given is kept in the batch record.
Assumption: the two configurations of the real batch are solver paths of the same tool; 58 picks the
configurations its comparison needs.
Assumption: a tool job's verdict comes from the plan's exit-code and output rules, and its refutation is
the tool's own, not replayed (replay is 22/46/47 and 60).
Assumption: a prove job's worker watchdog lives inside `swdb prove` (the record is written there), and
the `ulimit -v` cap is applied to tool jobs only; a real adapter that starts a tool applies it itself.

**Side findings:**
- Rocq 9.3 (OCaml 5.3) does not start under an 8 GB `ulimit -v`; Frama-C on the same OCaml does.
- On the Mac, `ps` is refused inside the agent sandbox, so the watchdog reads RSS through psutil there.
  A watchdog that cannot read the process tree now stops the job instead of failing silently.
- The shared lane check (`swdb.profile._verified_lane`) names `profile_in_lane.sh` in its refusal; the
  live control above shows that text. `swdb prove-lane run` now names `prove_in_lane.sh` instead
  (after the mbit10 run; message only).
- No 30-minute heartbeat: the whole mbit10 session took about 8 minutes, the longest batch 16 seconds.
