# 74 — The guard's thread cap bounds the model's work; a stop for the harness's own limit is uncounted

Created: 2026-10-05 10:15 ET (from campaign `extensa-native-bfs-20261005-a8`, ticket 56 a8 result)
Updated: 2026-10-05 12:00 ET (cpu_escape test fixed; mbit10 re-run pending); 2026-10-05 10:45 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D7; [07](07-role-based-provider-launcher.md),
[54](54-campaign-budgets.md), [56](56-native-campaign-target.md), [73](73-provider-capacity-and-protected-regions.md);
story 33 of `../../rewrite-provider-codex-2026-09-29/spec.md`

**What to build:** a harness fix, agent-decided under Yan-Ru's delegation (revisable), requested by the coordinating
agent on 2026-10-05.

## Findings (campaign a8)

1. **What stopped the calls.** Calls 1 (setup profiling) and 6 (iteration 5) ended about 0.5 s after launch with
   "provider resource limit exceeded: threads=17". The guard's `resource-overrun.json` shows two processes only:
   strace (1 thread) and Codex 0.153.0 (16 threads: `codex`, `codex-main`, 12 `tokio-rt-worker`, 2
   `notify-rs inotify`). No tool command had started (0 events, 0 commands). Calls 2-5 ran 195-413 s under the same
   cap, so this is a startup burst, not a steady state.
2. **Why Codex has 16 threads.** Codex is a native Rust binary on a tokio runtime. `TOKIO_WORKER_THREADS=1`
   bounds only the async workers. Tokio's blocking pool (file reads, DNS lookups) starts threads on demand
   (up to 512 by default) and keeps idle ones for about 10 s. Blocking-pool threads take the runtime's thread
   name, so the 12 `tokio-rt-worker` threads are most likely one worker plus blocking-pool threads from the
   startup reads of config, instructions and state (inferred from tokio's defaults; Codex's source was not read). The two inotify threads are file watchers. The Node-side settings
   (`UV_THREADPOOL_SIZE`, `--v8-pool-size`) do not apply to the native binary. The count is
   nondeterministic, so 16 or 17 total decided the outcome by chance. The same 17-thread shape stopped
   gem5 campaign `extensa-gem5-bfs-20261004-a7` call 18. The 2026-09-29 provider spikes stopped at 17-20
   (with sqlx pools or the code-mode host).
3. **What the cap protects.** Story 33 asks that each provider session be limited "so that it fits in one socket
   lane". On a shared host that means: (a) no task runs outside the lane's CPUs, and (b) runaway parallelism or
   process growth from the commands the model starts (`make -j64`, OpenMP binaries, fork loops) is stopped. Each
   thread of the provider's own runtime is pinned to one lane CPU already, so its count does not threaten the
   lane. Charging that count against the same 16 left the model's commands a budget that varied with Codex's
   startup I/O. Also, a CPU escape (a task widening its affinity with `taskset`, `numactl` or OpenMP binding) was
   not observed at all.
4. **Accounting.** The stop raised a plain `Failure` and the campaign counted it as `guard_refused`. Iteration
   5 became the fourth non-improving iteration, so the plateau was reached partly by the harness. D7 counts
   real attempts, and neither call was one.

## Decision

- **Two thread caps.** `limits.threads` (16, story 33) now covers the tool commands the model starts and all
  their descendants, including detached ones the tracer adopts. `limits.runtime_threads` (64) covers the provider
  runtime: the strace tracer, the original CLI and its exact persistent `codex-code-mode-host` service. The
  observed runtime maximum is 20, so 64 leaves more than 3x margin and still stops a runaway blocking pool.
  Memory stays one aggregate 32 GiB cap, charged to the tools when they push it over.
- **Lane CPUs observed.** Every thread of every owned process must stay inside the observer's verified lane
  affinity (`lane_cpus`), polled every 0.1 s. An escape stops the attempt as a guard violation.
- **Uncounted harness stops.** A stop for the runtime cap is written with `scope: runtime`
  (`swdb.guard-overrun.v2`). If the audit found nothing else, the role raises `GuardInfrastructure`. The
  campaign records it as `guard_infrastructure`, uncounted (D7), and retries after 30 s. After 2 retries
  the campaign stops `infrastructure_failure`. A synthesis call pauses, uncounted. A tool-scope overrun, a CPU
  escape, a command timeout or any other guard reason stays a counted `guard_refused`.
- **Calibration record.** `guard-audit.json` keeps `resource_peaks` (runtime threads, tool threads, resident
  bytes), so the runtime cap can be re-checked against real baselines.

## Acceptance

- [x] The raw a8 call 1 and call 6 receipts (byte copies, sha256 checked) split into runtime 17 threads and tools 0,
  which is within both new caps. Under the old aggregate cap they classify as harness limits.
- [x] A tool tree over 16 threads, or tools pushing memory over 32 GiB, is a tool overrun and takes precedence; a
  runtime over 64 threads is a harness limit. A CLI the handshake has not yet named is charged as a tool.
- [x] `harness_limit` returns nothing for a tool overrun, a passed audit, missing receipts or any non-resource
  guard reason.
- [x] A campaign replaying a8 calls 1 and 6 records both as `guard_infrastructure`, uncounted, retries them and
  produces the iteration's candidate. Persistent stops end the campaign `infrastructure_failure` after 3 stops.
- [x] The Linux guard tests cover a tool-thread overrun, a runtime overrun (harness limit) and a CPU escape
  (written; to be run on mbit10 inside `socket_lane.sh`).

## Answer

Resolved 2026-10-05 10:45 ET by the agent (worktree branch, not pushed; Mac only, no runs).

- `swdb/provider_guard.py`: `TOOL_THREADS` / `RUNTIME_THREADS`, `resource_scope()` (split, precedence, reason),
  `harness_limit(folder)` (v2 records, and legacy flat records re-split with the current caps), `_task_cpus()`
  lane check. The policy records `limits.runtime_threads`, `lane_cpus` and how each cap is enforced, and
  `guard-audit.json` records `resource_peaks`.
- `swdb/provider_adapters.py`: `GuardInfrastructure(Failure)` (not a `ProviderUnavailable`).
- `swdb/provider_roles.py`: a failed call whose only audit violations are resource limits and whose guard
  receipts show a harness limit raises `GuardInfrastructure`.
- `swdb/extensa/search.py`: `CallOutcome.GUARD_INFRASTRUCTURE` (SWDB addition), uncounted.
- `swdb/campaign.py`: `_call` retries a harness stop (`GUARD_RETRIES` = 2, `GUARD_RETRY_S` = 30;
  `SWDB_GUARD_RETRY_S` for tests), records `retry_after_s` and `guard_reason`, then stops
  `infrastructure_failure`; synthesis pauses uncounted. `schemas/campaign_summary.schema.json` allows the
  `provider_capacity` (ticket 73) and `guard_infrastructure` pause reasons.
- Tests: `tests/test_provider_guard_scope.py` (17 cases on the Mac, using a8 receipts in
  `tests/fixtures/provider_guard_a8/`), and `tests/test_provider_guard.py` updated for the split caps with new
  `runtime_threads` and `cpu_escape` modes. That file is Linux-only and skips on the Mac. It must pass on mbit10
  before the next real campaign.
- Not changed: `swdb submit` (`provider_workspace.run`) gets the new caps but keeps its own failure accounting.
- The a8 records are unedited; ticket 56's a8 result carries the erratum.

### Follow-up 2026-10-05 12:00 ET: the `cpu_escape` test, not the guard, was wrong

The coordinator's mbit10 run of `tests/test_provider_guard.py` in socket lane 0 (on `6b4372b`) gave 14 passed
and 1 failed. In `cpu_escape`, the fixture ran to its own completion and failed with "rewrite interpretation must
produce actual edits and explain them", so the guard never saw an escape. The fixture widened its affinity to
`range(os.cpu_count())`. Under Landlock the provider cannot read the host's CPU list, so `os.cpu_count()` most
likely fell back to the process's own one-CPU affinity (or failed), and the "escape" stayed on its lane CPU.
Outside the guard, a forked child under `numactl --cpunodebind=0` widens to all 64 CPUs (checked on mbit10), so a
real escape is possible and the guard's check is needed. The guard's order is unchanged: the lane check runs on
every poll, before the interpretation is read.

Fix (commit `227a61d`): the test names one CPU outside the observer's lane in the plan, and the child sets
exactly that CPU. The test now asserts that the guard's reason names that CPU, so a vacuous premise cannot pass
again. The re-run on mbit10 is pending Yan-Ru's approval for remote writes (clone, lane job).

- 2026-10-05 11:58 ET: verified on mbit10 at 434dc35 inside socket lane 0 (lease generation 461, record /data1/yanruj/EvolveSWDB_runs/guard-tests-t74b.lane.json): tests/test_provider_guard.py 15 passed. Scratch worktree tmp-guard-base and t74b.bundle removed with Yan-Ru's approval.
