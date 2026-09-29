# Bounded simulator series for T15 and T16

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

This is prospective preparation, not dispatch or empirical acceptance. The
[remaining simulation sequence](bfs-remaining-simulation-sequence-20260926.md)
sets the scientific requirements. `scripts/bfs_simulator_batch.py` coordinates
existing public `scripts/bfs_simulator_series.py` calls; it does not introduce an
evaluator, publish a protocol, retry a run, select a graph, or decide a gain.
The expired pilot and unused a2 remain historical. The separately bounded a3
and new A2 fixed coverage case must finish successfully before either batch is admitted.

## Fixed scope and finite ceilings

| Batch | Fixed order | Shared elapsed / storage | Per series |
|---|---|---|---|
| `bfs-t15-simulator-batch-20260926-a1` | Author MAA uniform18, then kronecker18; sources 0, 1234, 7777 in each | New prospective 43,200 seconds / 40 GiB | 21,600 seconds |
| `bfs-t16-simulator-batch-20260926-a1` | Artifact scalar, artifact MAA, control scalar, control MAA; uniform22 source 2796003 | Existing reference/control 86,400 seconds / 60 GiB, less retained preparation below | 21,600 seconds |

The exact machine-readable plans are
[the T15 request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/bfs-t15-simulator-batch-20260926-a1.json)
and [the T16 request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/bfs-t16-simulator-batch-20260926-a1.json).
The coordinator pins their canonical hashes. Both retain zero warmups, two
replays per ordered source, the original author traversal-and-normalization ROI,
verifier v2, and the existing 1.05 minimum speedup, 0.10 spread limit,
95% confidence, 2,000 resamples and seed 20260925. Four reference series do not
establish confidence-interval coverage or power.

T15 collects six primary and six diagnostic evaluations per graph family, with
one actual profile/package for each primary/diagnostic pair. It passes no
`--protocol` flag: unchanged author calibration is an allowed public series
operation before freeze. Thus actual source-specific accelerator execution and
coverage observations can be collected without a circular native-freeze
prerequisite. The later shared gate still checks actual primary accelerator use,
correctness, actual profiles and per-source cases; collection alone does not
qualify or freeze anything.

T16 requires two actual independently frozen protocols that exactly match the
retained artifact/reference request files. Its four series yield eight primary
and eight diagnostic evaluations, eight profiles/packages, and four public
aggregates. The MAA executions under one protocol cannot be relabeled as the
other protocol. Two final comparisons and empirical review remain separate
public workflow steps; the coordinator does not publish or approve them.

Each T15 primary has at most 3,600 seconds for checkpoint and 3,600 for simulation;
T16 uses 3,600 and 14,400. Each diagnostic has the unchanged 600-second total
(300 checkpoint, 270 simulation, 30 reserve). Per execution the existing adapter
retains the 48-GiB memory ceiling, 10-GiB T15 or 15-GiB T16 storage ceiling and
10^14 post-ROI verification tick ceiling. These are maxima within the common
budget, not estimates that every case fits. A six-hour series allowance plus
30 seconds of cleanup must remain before dispatch. Later series are not started
with a shortened allowance or fresh clock. Every failure stops the batch;
no retries, new child IDs, partial resumes or automatic threshold changes.

The admission arithmetic is feasible when earlier work finishes below its
ceilings; the maxima are not additive reservations. T15 can start the second
full series only while coordinator elapsed is at most 21,570 seconds
(`43,200 - 21,600 - 30`). T16 can start the fourth only while prior preparation
charges plus coordinator elapsed through the first three series, their cleanup,
and preflight are at most 64,770 seconds (`86,400 - 21,600 - 30`). The absolute
deadline can impose a stricter limit. If earlier work consumes more, the next
series is not launched and the planned ordered collection remains incomplete.

Within a series, public primary execution totals are capped at 7,260 seconds
for T15 and 18,000 seconds for T16, with the diagnostic total capped at 600.
Every command also inherits the remaining common six-hour series deadline.
Thus six T15 or two T16 primaries cannot all consume their individual maxima
inside one series; the T16 3,600-second checkpoint and 14,400-second simulation
ceilings also cannot both be exhausted while leaving verification overhead.
These constraints are intentional finite stop conditions, not a claim of
runtime feasibility from measurements. A series budget expiry preserves its
partial or failed grid; it does not reduce repetitions or grant another window.

## Accounting and admission

The shared clock begins at the captured outer-wrapper entry, before helper startup or record/artifact validation,
and ends after owned-process cleanup and final storage accounting. Its remaining
time is the minimum of the monotonic allowance and a separately sealed absolute
ET deadline. Before dispatch the admission must state concrete aware timestamps
`not_before`, `latest_start`, and `absolute_end`; `latest_start` must equal
`absolute_end - remaining_batch_seconds`. Preparation must precede `not_before`.
The unused 19:56 ET admission selected a 20:00–20:30 ET start window on
2026-09-26. Its storage-accounting correction requires a new exact-code
admission and matching proofs before guest dispatch; the original latest start,
absolute ends, and allowances remain unchanged. The corrected admission plans
`not_before=2026-09-26T20:20:00-04:00` only if its preparation finishes before
that time, narrowing the start window without backdating. An unfilled template
is not admission.

The T16 plan fixes three prior preparation identities: uniform22 generation and
registration, author scalar diagnostic preparation, and author MAA diagnostic
preparation. The driver reopens their pinned original driver and lane receipts.
Elapsed charges are the ceiling of the larger of retained stage elapsed sum and
helper elapsed plus one second, accounting conservatively for whole-second
helper timestamps. `du -sk` rereads each explicitly listed graph, dispatch,
source/candidate, build and raw-output path. Missing paths or changed receipt
hashes reject admission. The operator cannot omit a preparation row or select a
smaller numeric credit. Admission must contain the exact recomputed
`preparation_charges` array. Retained logs, including failed outputs, count.
The current active batch adds its entire dedicated raw tree. The preexisting
charged paths are fixed inputs; no process may append to them during the batch.

The plan explicitly excludes common historical model/toolchain/author binaries
and the previously registered scale18 inputs from the new T15 allowance. The
native pilot, a1 failure/a2 nonexecution history, a3 correctness and fixed
coverage executions have separate finite budgets and are not charged again.
T16's graph and both source/diagnostic preparations are explicitly charged even
though their bytes can be reused. New source preparation, recompilation or an
extra attempt is outside these fixed plans and cannot be hidden behind a new ID.

An admission is a separately hashed JSON document with these required fields:

- `format: swdb.bfs.simulator-batch-admission.v1`, exact canonical
  `plan_sha256`, `prepared_at`, and the three `clock` timestamps above.
- `preparation_charges`: exact output of `preparation_charges(plan)` on the host.
- `code_commit`, `runtime_sha256`: the actual Git commit and exact output of
  `runtime_identity()`; `python: {path, sha256}` binds the resolved interpreter.
- `proofs`: `a3`, `coverage`, `paired`, and `provider`, each an absolute
  `{path, sha256}` terminal-audit reference. Actual a3/coverage must pass their
  shared readers; paired/provider may have failed but must be terminal with
  verified cleanup. The coverage evaluation is fixed to
  `bfs-dx100-coverage-20260926-a2.execute`, its exact graph/request and bounded
  completed driver. `coverage_commit` pins that actual reviewed code.
- `protocols`: empty for T15; for T16, `artifact` and `control`, each the actual
  immutable `{id, sha256}` of the matching independently frozen protocol.
- `linux_cleanup_tests`: two hashed actual host-test receipts described below.

Every prerequisite must exist before `prepared_at`. All fixed records and
source/build/graph/raw references are reopened and checked. Retained a1 failure
bytes must still match; the expired witness-a2 execution record rejects admission. The interrupted coverage-a1 public marker and its exact YAML bytes remain pinned separately and are not promoted. Existing batch
roots, child record prefixes or child build paths prevent retry/overwrite.
Unknown runtime, protocol or completion identities fail closed.

## Host resources and cleanup

Run sequentially under one current `socket_lane.sh` lease. The coordinator
verifies its own lane and the absence of a legacy lock, and records the other
socket's metadata and kernel lock consistently. A legitimate other-lane job is
allowed; this plan does not reserve both sockets for six hours. Actual paired,
provider and coverage terminal audits exclude unfinished dependent batches.
The helper's normal alignment/load checks still apply.

Every batch series command includes the new explicit `--require-capacity` flag.
The series reuses `dx100_capacity.capacity` immediately before each expensive
public `dx100-compile` or `dx100-execute` call and retains raw inputs and the
result in its driver receipt. It requires the existing discounted 52-GiB node /
64-GiB global availability gate. This is admission between sequential executions,
not a free-memory test while the owned simulator is already allocated. Existing
standalone series behavior is unchanged when the flag is absent. Capacity
estimates do not guarantee protection from other users' subsequent allocations.

Nominal five-second coordinator observations retain common elapsed/storage,
leases and PID/start-time descendant identities in `ledger.jsonl`, including
admission, record readback and finalization. The prospective coordinator and
explicitly opted-in series use `bfs_owned_rss`: PID, start time, state and RSS
come from one `/proc/PID/stat` record. The sampled coordinator subtree limit is
52 GiB, including its series/public evaluators and observed detached descendants;
the adapter's execution limit remains 48 GiB. This is a sampled guard, not a
kernel memory quota or a guarantee about unobserved short-lived processes.
Maximum inter-observation gap and guard duration are 30 seconds. Retained
samples are reopened to check arithmetic, ordering, memory bound and coverage
through finalization. Every guard also retains the existing 30-GiB raw and
10-GiB build free-space reserves.

Prospective execution uses `bfs_owned_execution`, independently of historical
`OwnedDescendants` APIs retained for older pinned clients. Linux child-subreaper
admission precedes dispatch. PIDfds and exact PID/start identity protect signals;
there is no signal to a reused numeric process group or the shared tmux server.
An exited public leader still requires adoption, termination and reaping of its
owned detached descendants before the next public stage.

One file-backed 30-second cleanup ledger is shared by the coordinator, each
series, and every public stage. Short atomic reservations and settlements hold
the file lock only for metadata; signaling, waiting and reaping occur outside
that lock. A dead supervisor's unsettled reservation remains charged. Graceful waiting cannot consume the final ten seconds reserved inside that same allowance for KILL, direct-child reap and final persistence. Concurrent
parent/child cleanup may conservatively double-charge overlapping time, but it
cannot reset the reserve. A bounded 50-ms settlement tail is charged and checked
after persistence. An overrun fails the batch. Monitor shutdown, post-stage log hashing, receipt persistence and final
resource readback are charged to the same reserve. All teardown, metadata and final
persistence also remain inside the original absolute and monotonic batch clocks.
The outer helper uses TERM at the remaining allowance minus 30 seconds and KILL
after the same 30 seconds. There is no per-series cleanup-clock extension.

## Required bounded Linux checks before dispatch

Mac fixtures do not establish Linux behavior. On the exact prospective runtime
pin, a free leased lane must run these two separately bounded fixture selections,
retaining actual commands, stdout hashes, JUnit hashes and terminal cleanup:

```sh
timeout --signal=TERM --kill-after=5s 85s \
  python3 -m pytest -q tests/test_bfs_owned_execution.py \
  -k linux --junitxml="$CLEANUP_JUNIT" --basetemp "$CLEANUP_TEST_RAW"
timeout --signal=TERM --kill-after=5s 85s \
  python3 -m pytest -q \
  tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem \
  --junitxml="$INTERRUPTION_JUNIT" --basetemp "$INTERRUPTION_TEST_RAW"
```

The first selection includes detached-child success, detached-child failure,
nested-parent/child interruption, and a TERM-resistant nested case sharing the
same reservation file. Actual direct-process regression also verifies reap even
when signaling fails, preservation of the first stage error, and the unchanged
work deadline after process startup. The second
reopens the public failed evaluation while optional postmortem work raises or
stalls. These are contract fixtures; no graph performance or coverage is inferred.
Both `swdb.bfs.linux-fixture.v1` receipts must identify mbit10/Linux, the exact
Git/runtime/test hashes and interpreter, successful unskipped required JUnit
cases, and at most 90 seconds. Historical Linux receipts do not satisfy these
new tests. The four ownership and two interruption cases passed on `d11dc04` with independent
terminal audits. Those receipts identify that exact revision. The dispatch-storage
correction requires fresh matching fixtures on the corrected revision; no empirical
batch had started as of 2026-09-26 20:03 ET.

## Prospective public invocation

After actual prerequisites and clock admission exist, the fixed coordinator
command is:

```sh
python3 scripts/bfs_simulator_batch.py t15 \
  --admission "$ADMISSION_JSON" --admission-sha256 "$ADMISSION_SHA256" \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-t15-simulator-batch-20260926-a1 \
  --lane 0 --outer-started "$OUTER_STARTED" --outer-deadline "$OUTER_END" \
  --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START_TICKS"
```

Use `t16` and its exact root name for T16. Lane 0 is an example; choose a currently
eligible socket under the helper and retain its actual receipt. The common outer
timeout is computed from the sealed remaining allowance, not copied as a fresh
24-hour allowance for each child. The driver records each exact child command
and complete/failure state before continuing. A completed receipt means the
fixed collection finished and its readback matched. It does not resolve tickets,
qualify a protocol, promote T14's unverified samples or assert a gain.

The A2 completed-reader import is intentionally lazy: the separately reviewed
A2 export still pins the historical batch/series dependency bytes. Its actual
successful code commit must be supplied in sealed admission and its full reader
must pass; mere existence of an A2 evaluation is insufficient. New batch code
must not leak into that separate measured runtime before independent review.

## Terminal accounting readback

After independent lease and PID/start-time closure, reopen the terminal driver
and final shared-ledger bytes with
`scripts.bfs_simulator_batch_terminal.validate_cleanup_ledger`. Supply the exact
hashed references and original run ID, outer start, absolute deadline and audit
time. The reader requires empty reservations, matching creator and immutable
header, settled charges totaling no more than 30 seconds, no exceeded grants,
and original-clock event ordering. Embedded cleanup snapshots are nonfinal;
they cannot replace the final ledger. This readback proves accounting
consistency, not process absence or empirical qualification.

Final shutdown and accounting errors remain visible separately from the first
stage failure. A new finalizer failure makes an otherwise successful coordinator
exit unsuccessfully; it cannot silently return success with a failed receipt.
The original stage exception remains authoritative if both fail.

## Dispatch storage correction — 2026-09-26 20:03 ET

The batch's storage boundary includes both the exact new run directory and its
canonical sibling `<runs>.dispatch`. The sibling retains admission, helper lane
records, launcher metadata, stdout, stderr, and exit status. Both directories
count against the same 40-GiB T15 or 60-GiB T16 allowance; no control-file
exemption or additional storage budget applies. T16's fixed historical
preparation charges still count as before. Missing, redirected, or duplicate
storage roots cannot substitute for these exact two directories.

During execution, sampling and driver finalization count both roots. The driver
snapshot precedes the helper's final writes and is therefore nonfinal for outer
storage. After independent process and lease closure, persist the terminal audit
inside the dispatch sibling, then call
`scripts.bfs_simulator_batch_terminal.validate_storage_accounting` with the exact
hashed driver and terminal-audit references and the current aware timestamp.
The reader verifies the fixed plan and preparation charges and recounts both
roots, including the already-persisted audit. If the caller persists this result,
repeat the read-only check after that final write. A failure stays a failure;
this check neither qualifies measurements nor proves process absence itself.

Preserve the unused original admission and launcher preparation. Corrected
admission uses a new file in the same counted dispatch directory; it does not
rename a consumed guest attempt or replenish the batch's time or storage.
