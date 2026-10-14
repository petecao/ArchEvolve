# 57 — Proof workers in a socket lane

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
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

- [ ] **Lane entry.** Before dispatch, both socket leases and the legacy lease are checked and their
  states recorded. The job runs only through the lane script, from an up-to-date MemAcc checkout whose
  lane script was compared with the repository version first. Negative control: started without the lane
  script, the batch refuses to run.
- [ ] **Up to 6 workers, each on its own core.** Each worker is pinned to a distinct physical core of
  the lane's socket (no two workers on hyperthread siblings; the lane procedure allows no
  hyperthreads). Negative control: a batch plan asking for 7 workers is refused, or capped at 6 with
  the cap recorded.
- [ ] **8 GB RSS watchdog per worker** (design O9). Each lineup tool is tried once under an 8 GB
  `ulimit -v` and the result recorded; the cap is added only for tools that start under it, and the
  rest run under the watchdog alone. Negative control: a fixture job whose RSS passes 8 GB is ended by
  the watchdog with failure class "out of memory", and the other workers carry on.
- [ ] **Job block fields.** Each proof record's job block holds every field on 12's job-block field
  list: adapter, host, worker core, wall time, CPU time, batch load, peak RSS, batch ID and position
  in the batch (12 owns the list; this ticket fills it on mbit10 and adds no field). Worker core is
  the pinned core; peak RSS is the value the worker's watchdog reads. `swdb validate` and
  `swdb build` accept them; a lane-job record missing any of 12's fields is rejected.
- [ ] **Interleaving.** A batch with two configurations of the same subjects runs them interleaved, not
  grouped, and the records' batch ID and position in the batch show the order. Negative control: a
  batch plan that groups one configuration first is reordered or refused.
- [ ] **A real batch.** At least 12 jobs that run real tools from the 56 lineup (07's smoke programs,
  two configurations) complete in one lane job. They go through `swdb prove` with whichever real
  adapters exist by then (21, 22, 46, 47); a tool with no adapter yet runs under the same worker wrapper.
  Each verdict matches the same job run alone. The batch mechanics are also tested with the scripted
  adapter.
- [ ] **Output.** `df -h /data1 /data` is recorded before the batch. Raw output goes to
  `/data1/yanruj/EvolveSWDB_runs/<run-id>/` (or `/data/yanruj/EvolveSWDB_runs/` when `/data1` is low).
  Compact evidence is named by path and sha256. Verifier scratch is deleted when each job ends. Nothing
  goes under `$HOME`.
- [ ] **Host record.** Each batch records the host load at start and end, free memory on the lane's
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
