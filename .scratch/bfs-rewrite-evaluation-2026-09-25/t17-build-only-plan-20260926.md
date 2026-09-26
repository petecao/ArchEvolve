# T17 existing-candidate build-only plan

Created: 2026-09-26 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

This prepares one compilation of the retained initial instruction-route candidate.
It has not been dispatched. Run it only after the native study, a3 continuation,
and fixed-coverage work have ended and their owned-process cleanup has been
verified. Preserve their windows and other-node-idle admission gates. The single
native review readback has ended by timeout, with no retry. This plan neither freezes a
protocol nor completes [Ticket 17](issues/17-dx100-instruction-route-acceptance.md).

## Request and bindings

The [exact request](requests/t17-build-only-20260926-a1.json) is 551 bytes, SHA256
`de1b10536fa91f675bb3372f9104c10fbf160f952ac9016538c5d38cdb6fc211`.
Its new evaluation ID is `bfs-t17-build-only-20260926-a1`. It compiles
`bfs-campaign-preparation-20260925-a1.dx100-instructions.candidate-1`, selects
`DOBFS`, requests acceleration, and disables diagnostic instrumentation. The
public request retains ROI `bfs.complete_call.v1`; the pinned compiler adapter is
`dx100.complete_call.v2`, including the evaluator-owned original-adjacency oracle.
An acceleration request or a compiled verifier does not establish execution.

The [metadata-only observation](observations/t17-build-only-preflight-20260926.json)
records the actual proposal/candidate/source/model/compiler pins read on mbit10
at 13:05–13:07 ET. The candidate's 53-file artifact was reopened and verified as
`ca09d2f439a56f295c5ccdc5e18a5fd5a4c2c9726005365f8125cc1d8979740a`.
The model is the clean `e4fc4afdf894f295442cef3604667a469fab8e62`
checkout at `/data1/yanruj/DX100-bfs-e4fc4af`; completed model build
`bfs-dx100-build-20260925-a2` and its hashed receipt remain required.
The compiler is `/usr/bin/g++-13`, SHA256
`1353e9bdd29a7295c7226bf6c63abccce056d8cac31f112e5cdbecc3f28c2769`.

The existing provider checkout is
`/data1/yanruj/EvolveSWDB_provider_20260926_a1` at
`5f1b8028619976b36df5fa24b8aacb91bf488168`, whose code parent is
`6346189b55132f195b02544b729f34100d10ba92`. Its existing public
`dx100-compile` path accepts this candidate ID without resubmitting the proposal.
It invokes no provider. The original budget remains 1,800 provider seconds,
233.21830715797842 seconds consumed, zero repairs used of two; compilation must
not reset it. No retry or repair is included in this attempt.

## Bounds and admission

Compilation permits 180 seconds; the public API total is 240 seconds. The enclosing
attempt has a 270-second work deadline and at most 30 seconds for cleanup, with a
300-second hard outer stop. Preflight queries, public invocation, and post-build
retrieval share that original deadline; each stage is clipped to its remaining
allowance. A timeout or partial receipt is retained, without a second attempt.

Use one verified socket-0 lane through the current `socket_lane.sh`, in a named
tmux session, after fresh checks of both socket leases and the legacy lease.
Recheck host load, clean code/model pins, candidate/source protections, compiler
identity, unused evaluation/output IDs, and free-space reserves: 10 GiB on the
source/build volume and 30 GiB on the raw volume. Build outputs use `/data1`;
the distinct raw root is `/data/yanruj/EvolveSWDB_runs/bfs-t17-build-only-20260926`.
The request permits 16 GiB sampled compiler-process-group RSS and 1 GiB sampled
raw/build storage. These are sampled guards, not hard kernel quotas or true-peak
claims; any guard failure retains the unsuccessful attempt.

Inside that bounded lane job, the public invocation is:

```sh
python3 -m swdb dx100-compile REQUEST.json \
  --records /data1/yanruj/EvolveSWDB_provider_20260926_a1/records \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-t17-build-only-20260926 \
  --lane 0 --format json
```

## Required retained evidence

Before compilation, retain fresh public `swdb get` outputs for the exact proposal,
candidate, source snapshot, profile package, model-build evaluation, and hardware
target, with command/exit/file hashes. Reopen the pinned artifact manifests and
model receipt locally; record mismatches as refusals before compilation.

Retain the exact request and runtime pins, lane/host observations, public stdout
and stderr with hashes, exit code, elapsed times, compile command and logs,
sampled resource observations, generated-driver/binary hashes, and the durable
evaluation outcome. Retrieve that evaluation and its chain in a fresh public
process within the remaining bound. Keep all raw evidence on mbit10; no external
packet transfer is included here.

After the job, independently retain actual owned PID/start identities, observed
terminal states, direct-child reap results, descendant absence or explicit
survivors, and released lease generation. Signal only owned children. A zero exit
or ended tmux pane alone does not establish cleanup. Successful compilation leaves
correctness unverified, profiling incomplete, and gain false; timed execution,
actual full/tail/competing coverage, both graph families, and frozen-protocol
acceptance remain outstanding.

## Reviewed orchestration addendum — 2026-09-26

The local [T17 supervisor](../../scripts/bfs_t17_build_only.py) implements this
one attempt; its [focused tests](../../tests/test_bfs_t17_build_only.py) passed
47 cases locally, with two real Linux subreaper/pidfd cases skipped on macOS.
An independent reviewer reproduced that result and found no remaining issue after
the stage-boundary cleanup repair. This is local preparation, not a build result.
Dispatch remains contingent on the prerequisites and live host admission above,
a separately pinned idle orchestration checkout, and the Linux cleanup checks.
The existing provider and fixed-coverage checkouts remain unchanged.

Use the named tmux pane → `timeout --signal=TERM --kill-after=30s 270s` →
current socket-0 helper → supervisor topology. Capture the actual pane PID/start
identity and the original aware start/deadline immediately before the timeout;
the deadline is exactly 300 seconds after that start. Put the helper's lane,
outer exit, and preflight evidence in the new sibling
`/data/yanruj/EvolveSWDB_runs/bfs-t17-build-only-20260926.dispatch/` so the
supervisor can require its separate raw root to be unused. The command interface is:

```sh
python3 ORCHESTRATION_ROOT/scripts/bfs_t17_build_only.py \
  --expected-commit ORCHESTRATION_COMMIT \
  --outer-started ORIGINAL_START --outer-deadline ORIGINAL_START_PLUS_300_SECONDS \
  --pane-pid ACTUAL_PANE_PID --pane-start-ticks ACTUAL_PANE_START \
  --coverage-completion /data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926.dispatch/terminal-validation.json \
  --coverage-sha256 65969e8cae4ce113c289ba79c9b3aafd852f36724dcd8c060d8f37837c5c971a \
  --coverage-commit ACTUAL_PROSPECTIVELY_SELECTED_COVERAGE_COMMIT
```

Those uppercase values are required prospective inputs, not defaults or permission
to extend the original clock. The supervisor fixes the public checkout to
`5f1b8028619976b36df5fa24b8aacb91bf488168` and checks its code parent, all
tracked runtime sources and configuration, request bytes, Python executable, and
compiler/model identities. Its public sequence is six fresh preflight `get`
processes, one `dx100-compile`, then fresh evaluation and chain retrieval. Each
`get` has a maximum 15-second allowance, clipped to the common work deadline.
The child environment disables Python user-site and bytecode writes, uses the
existing `/data1/yanruj/tmp`, selects `/usr/bin:/bin`, and removes Python-path and
compiler search-path overrides; the exact controlled map is retained.

The supervisor uses the reviewed Linux subreaper/pidfd cleanup owner with the new
[RSS observer](../../scripts/bfs_owned_rss.py). Its basis is
`linux.proc_pid_stat.field24.v1`: PID, start time, state, and RSS pages come from
the same `/proc/PID/stat` read. RSS remains approximate. The helper was exported
separately at `a8b89115c9650173d516a50e3ed659036e614428`; the eventual client
checkout must bind its own complete runtime tree. The additional supervisor guard
covers itself and observed owned descendants across sessions, with the same
16 GiB ceiling, nominal five-second observations, and a maximum 30-second gap.
It does not claim a true peak or a kernel-enforced cap. Each public stage cleans
adopted detached descendants before the next stage starts. All direct shutdown,
reap, and adopted cleanup time spends one total 30-second allowance inside the
original 300 seconds; no stage receives a new cleanup budget.

The fixed coverage attempt ended **failed**, with outer/lane exit 1 and socket-0
generation 321 released. Its exact terminal audit above retains 14 observed
PID/start identities: 13 absent and only the captured tmux pane
`3053339/494729548` as a zero-RSS zombie. Its resource observer is still labeled
failed and sampling incomplete. The shared `coverage_cleanup` reader reopens
that failed driver, time/budget bindings, lane/exit/release artifacts, and the
full ancestry/known/sample identity union, then checks current process states.
It also preserves the passed a3 and completed native/provider cleanup barriers.
This admission establishes sequencing and terminal ownership only; it does not
establish full/tail/competing execution or promote failed correctness evidence.

The final independent terminal audit must include the supervisor's ancestry,
driver and pane identities, every resource-sample and known identity, every
public-stage identity, and all per-stage/final adopted-cleanup observations.
`driver.json` retains direct-child exit/reap results, source/Python/runtime hashes,
raw and binary bindings, elapsed time, resource observations, and final accounting.
Its `cleanup_verified` remains false because its own reaping and the later lease
release require the independent audit. No candidate performance or provider call
is added by this orchestration.
