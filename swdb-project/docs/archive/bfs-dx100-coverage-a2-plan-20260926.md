# Corrective fixed DX100 coverage attempt a2

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).
Status: corrected Linux admission fixtures passed at the reviewed prelaunch
revision. No a2 simulator build or execution has occurred as of 18:58 ET.

The active tested commit is `5a0b15fe666b2d094a2b2b9847ff5a30ef16fb4f`;
its canonical plan digest is
`d78c09751d9b56abddcce0a7217983fc1652ef6dc83c09fc55ecf8a9a4d4be5a`.
The [prelaunch correction](bfs-a2-interruption-prelaunch-revision-20260926.md)
preserves mandatory mbit10 lane checks and changes only the interruption
fixture and its plan bindings. Both fresh Linux selections passed; the
[actual receipts](../../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/a2-corrected-fixtures-actual-20260926.json)
remain contract evidence. The same unused measurement ID, 21:00 ET launch
cutoff and 3,600-second budget remain in force. Older preparation identities
below are retained as history, not the active admission pin.

This is one prospective corrective attempt for the failed
`bfs-dx100-coverage-20260926-a1` collection. It changes collection reliability,
interruption persistence, output identities, and the finite schedule. It keeps
the graph, unchanged author source, guest configuration, and correctness
obligations fixed. It does not choose a graph or implementation from observed
performance, perform a rewrite, or claim a gain.

The [a1 failure audit](../evidence/bfs-dx100-coverage-20260926-a1-failure.yaml)
remains failed: the resource monitor reported unavailable RSS, and the public
record retained an interrupted stage with a stale running top-level outcome.
Its exact offending process was not captured, so the identified cross-file
RSS exit race is a possible explanation, not a proven cause of that run.
Neither the old sealed guest continuation nor a new collector repairs the
old result. Its records, files, code pin, and terminal audit remain unchanged.

The relevant [spec](../../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md)
requires actual accelerated full/tail/competing-update checks (D10, lines
217–221), prospectively fixed configurations and corresponding comparisons
(D13, line 262), and retained completed evidence after failure or budget expiry
(D14, line 268). Success here supplies only this finite correctness case; it
does not supply both required graph families, the artifact reference, a frozen
performance protocol, profiling, or a candidate speedup.

## Fixed identity and public requests

Use `RUN_ID = bfs-dx100-coverage-20260926-a2`. The planned public IDs are
`RUN_ID.workload`, `RUN_ID.compile`, and `RUN_ID.execute`; workload registration
returns its normal immutable suffix. All must be unused. The planned new raw
root is `/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926-a2`, with driver
files in its `RUN_ID` child and wrapper artifacts in the sibling
`bfs-dx100-coverage-20260926-a2.dispatch` directory. The new compile directory is
`/data1/yanruj/EvolveSWDB_builds/RUN_ID.compile`. No overwrite or resume is allowed.

Retain the unchanged candidate
`bfs-author-maa-compile-20260925-a1.candidate`, canonical record digest
`1018e9002c86a2e0ef7850be0bc66dbec9849d388cced45542c61a18cd619fff`,
source artifact digest
`d5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d`,
and author `bfs.cc` digest
`6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465`.
The original author waits on tile 3. A different proposal's intended tile-5
change is outside this case.

Run the existing fixed generator into a new path. Require exactly 8,212
vertices, 147,492 directed adjacency entries, source 0, one isolate, the same
4,097-vertex frontier and sixteen shared successors. Reopen the SG32 bytes and
canonical adjacency. Their existing deterministic identities are:

- SG32 SHA-256: `d4697713f585b9670e1c44d26df94c72889f4c82fbd68b72e15627e6a0b39a56`;
  622,829 bytes.
- Canonical graph SHA-256:
  `e03a3905f9105b898b730387092d92a68b854cdd44280adb39b1bd9423a4a968`.
- Generator file SHA-256:
  `c4527c65266284f594709bfc7be1d829d40111f339198bd866d7a3348dfadb5f`.

The public sequence remains capacity admission, graph generation,
`register-workload`, fresh `dx100-compile`, `dx100-execute`, and fresh public
`get`. Compile `DOBFSMAA`, accelerated, with the trusted
`dx100.complete_call.v2` wrapper and semantic ROI `bfs.complete_call.v1`.
Execution uses the fresh exact binary, existing pinned model/build/simulator
from the a3 template, MAA mode, four guest cores, fixed guest memory `16GB`,
8 MiB L3 with associativity 16, and 16,384-element tiles. Keep
`dx100.bfs.verifier.v2`, coverage enabled, `max_ticks: 10000000000`, and
`post_roi_trace: SyscallBase`. The actual a2 binary hash is retained after
compilation; no binary hash is invented before that build.

## Window, sequencing, and resource bounds

The selected prospective window is **2026-09-26 16:00–22:00 ET**, with latest
outer-wrapper start **21:00 ET**. The complete 3,600-second allowance must remain.
The wrapper records its start before `timeout` and the lane helper. Pass that
same start and absolute end to the client; no inner clock may restart it.
TERM occurs at 3,570 seconds and KILL at 3,600 seconds. Final hashes, writes,
public retrieval, and owned cleanup all spend this one allowance.

The new one-thread native client must first have an independently sealed
terminal/cleanup audit for the entire client, including any diagnostics.
Its qualification outcome does not affect a2 eligibility: passing,
unqualified, or failed work can satisfy only this cleanup prerequisite.
Do not read mutable `driver.json` as a phase barrier. Waiting for the entire
client avoids adding a primary-phase publication interface and removes
avoidable simulator interference with its controls. If terminal admission is
unavailable by 21:00, a2 remains unused; the window is not extended.

Preserve the existing stage caps: generation plus registration 120 seconds,
compile 240, checkpoint 300, simulation 2,700, and public execution 3,100.
Capacity and final retrieval retain their 30-second caps. Every stage is also
clipped by the original shared work deadline; individual caps do not add time.
There is one compile and one execute, no retry or replacement ID.

Preserve 48 GiB sampled RSS for the client and all owned descendants, including
nested sessions, and 4 GiB aggregate retained artifacts, including failed
outputs, builds, requests, records, and receipts. RSS uses
`linux.proc_pid_stat.field24.v1`: identity, state, and RSS pages come from one
`/proc/PID/stat` read. Missing live telemetry fails closed; it is not replaced
by zero. Sample nominally every five seconds, with at most 30 seconds between
observations and per guard, including startup and final coverage. These are
sampled guards, not hard kernel limits or true-peak measurements.

Fresh admission requires at least 52 GiB estimated available on node 0 and
64 GiB global. Preserve 30 GiB raw and 10 GiB build-volume free-space reserves
throughout, with room for the prospective four-GiB artifact allowance before
starting. Account a shared filesystem once. Fresh host/helper/lease checks and
recorded load remain mandatory. Node 1 and the legacy lease must be idle;
entry is through the current verified socket-0 helper in a named tmux session.

## Implementation boundary

Optional `run_id` arguments, defaulting to the existing a1 constant, are added only
to `compile_request`, `registration_request`, `execution_request`, and
`validate_coverage` in `scripts/bfs_dx100_coverage_execution.py`. This lets a2
reuse the existing source, graph, request, exact-binary structural-verifier,
sealed-interval, full/tail-tile, and competing-parent checks. Leave the old
a1 `main`, constants, runtime inventory, and `validate_completed` behavior
unchanged; historical pinned checkouts are not modified.

The distinct `scripts/bfs_dx100_coverage_a2.py` has one focused test file.
Its small runner owns the new outer clock, immutable a2 plan, robust RSS
observer, complete runtime/Python identity, and one-attempt public stages.
Reuse the existing PID/start identity and ancestry reader,
`OwnedDescendants` subreaper/pidfd cleanup, and bounded `stop_owned` primitive.
Use the corrected observer from the first owned-process observation. Serialize
sampling with mutating cleanup, retain all seen PID/start pairs, and reap
adopted detached descendants before another public stage. Signals target
only verified owned children; never the shared tmux server. Cleanup spends
one cumulative 30-second reserve, including final reap and persistence.

Require the separately reviewed DX100 interruption-persistence correction in
the new code pin. A real public interruption fixture must show a terminal
interrupted/failed outcome and retained completed artifacts after SIGTERM,
even if a later correctness scan cannot finish. A forced KILL can still leave
partial evidence; the external terminal audit must preserve that outcome.

The new terminal reader takes an independently selected expected commit and
reopens all exact request/result/runtime/artifact references, actual stage
intervals, final accounting, and terminal ownership evidence. It must not
route a2 through a1's fixed `validate_completed` identity. Shared pure
coverage checks establish the same unchanged correctness obligations.

## Required pins and tests before dispatch

The new prospective admission packet must contain the reviewed client and
DX100 fix commit, complete runtime and Python hashes, exact a2 request hashes,
new paths and IDs, original a3 pass, historical paired/provider terminal
audits, the fixed a1 failed-cleanup audit, and the actual new native terminal
audit with its caller-selected code pin. The a1 audit SHA-256 remains
`65969e8cae4ce113c289ba79c9b3aafd852f36724dcd8c060d8f37837c5c971a`.
The selected native code is
`319645eab0a25c815fa03fe1c372d32b4ba45d10`; no attempt at its superseded
`d484afb` preparation is presumed. The future native terminal hash and new
a2 code pin must be sealed before launch.

The initial a2 plan at `67313d9` had canonical SHA-256
`f24375eca2fcfb304c92bd752c718f71f14e111ed40a2f1211c12172d3c558e7`.
It pinned the interruption correction from commit `76fd5b4`, the
stat-field-24 observer, and the historical shared batch/series/native helper
bytes from that reviewed base. The active [plan request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-coverage-a2-20260926.json)
changes only the required interruption-test hash, as recorded above.
The separately developing batch/series changes
are excluded from this a2 export. Runtime admission fails if they replace the
pinned shared files. The pure a1 helper changes are the only permitted edits
to the historical coverage module.

## Concrete interface for prospective admission

Run the new client from a new, independently selected checkout. Its required
arguments are `--expected-commit`, `--admission`, `--admission-sha256`,
`--outer-started`, `--outer-deadline`, `--pane-pid`, and `--pane-start-ticks`.
The surrounding named-tmux wrapper records the real outer start before
`timeout --signal=TERM --kill-after=30s 3570s` and the current verified
socket-0 helper. The client accepts entry at most five seconds after that
original start. It separately records actual driver entry, so helper/lane
start can occur after the outer start without resetting the charged clock.

The required-new admission JSON has format
`swdb.bfs.coverage-a2-admission.v1`, the exact `code_commit`, `plan_sha256`,
aware `prepared_at`, `runtime` from `runtime_identity(code_commit)`,
`fixed_prerequisites` copied exactly from the plan, `native_terminal` as a
path/SHA-256 reference, and `linux_proofs` with `owned_cleanup` and
`dx100_interruption` path/SHA-256 references. All terminal audits and fixture
proofs must predate admission preparation, which must predate the outer start.
No native phase or qualification boolean substitutes for its whole-client
terminal audit.

Each Linux proof has format `swdb.bfs.linux-fixture.v1`, `kind` equal to its
admission key, `host: mbit10`, `platform: linux`,
`evidence_kind: contract_fixture`, the selected `code_commit`, `state: passed`,
integer `returncode: 0`, aware `started`/`finished`, the exact same `runtime`,
actual pytest `command`, and hashed `stdout` and `junit` references. The
command uses the admitted Python and `--junitxml=ACTUAL_PATH`. JUnit must
contain the required cases with no failures, errors, or skips. Select:

```text
tests/test_bfs_dx100_coverage_a2.py::test_linux_a2_reaps_detached_child
tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem
```

The first selector runs success/failure detached-child cases; the second runs
the public SIGTERM raises/stalls cases. Runtime identity includes the complete
project runtime, test tree, project configuration, plan, and Python executable.
These Linux proofs establish collector contracts only.

The client materializes and hashes each public request before its command.
The compile request is fixed in the plan. The execution request binds the
fresh compile's actual binary digest and the new immutable workload record;
all remaining fields come from the unchanged fixed helpers. A failed execute
JSON is freshly queried when it exits within the remaining work allowance.
An interrupted or exhausted client retains its available records and raw
references without restarting a stage.

The driver receipt includes both outer and actual-driver intervals, exact
commands/requests/output/exit hashes, runtime/admission references, owned
PID/start identities, raw resource samples, final accounting, and cleanup
time consumed. Monitor shutdown and join, adopted cleanup, final hashes and
writes all spend the same cumulative 30-second cleanup reserve. The completed
reader is `validate_completed(ref, store, current, expected_commit, proc=...)`;
the caller's commit is mandatory. It reopens the actual complete trace and
checks both per-stage and final-cleanup identities against the terminal union.

Focused tests must cover unchanged a1 helper defaults; identical graph and
coverage requirements under a2 IDs; foreign/missing request and binary pins;
rejection after latest start or with a reset outer clock; native cleanup
acceptance independent of its qualification; omitted/reused owned identities;
direct failure and detached-child cleanup before the next stage; exhausted
shared cleanup; unavailable RSS; interrupted public outcome persistence;
and final hashing/writes crossing time or storage limits. Run the actual Linux
owned-process fixtures from the newly pinned idle checkout before admission.
Mac fixtures cannot establish Linux cleanup behavior or accelerator coverage.

An external terminal audit must bind the driver, actual outer exit, released
lane generation, and complete ancestry/direct-child/adopted-child/resource
identity union. Every owned identity must be absent or have a different start
time, except the exact original pane may be a zero-RSS zombie. The client
cannot certify its own process as reaped. A successful correctness claim
additionally requires the exact-binary original-adjacency PASS and reopened
full/tail/competing-update trace observations. Failures retain their partial
artifacts and never become accepted timing or coverage.

Dispatch remains contingent on these prerequisites and live host admission.
This document and local implementation create no new host job, provider call,
Git transfer, or change to the failed a1 evidence.

## Local verification — 2026-09-26

The combined command `python3 -m pytest tests/test_bfs_dx100_coverage_a2.py
tests/test_bfs_dx100_coverage_execution.py -q` passed 101 cases with two
Linux-only cases skipped in 25.97 seconds. The retained local log is
`/private/tmp/bfs-coverage-a2-stable-20260926/pytest.log`, SHA-256
`38b840539342b78a25f9ade99dea9114dc153a53d99ea65f4cfc0ce5c7205aab`.
Source and test hashes were unchanged across this run. Python compilation
and scoped whitespace checks passed. This is local contract verification;
actual Linux cleanup/interruption proofs and empirical coverage remain open.

A subsequent independent review reproduced a direct-child reap omission after
a shutdown error. The corrected stage always attempts its bounded direct-child
wait, retaining the original shutdown failure and the same cleanup deadline.
The affected subprocess, failure, cleanup, monitor, runtime-rehash, and
finalization group passed 12 cases (51 deselected) in 0.76 seconds. Log:
`/private/tmp/bfs-a2-direct-reap-fixed-20260926.log`, SHA-256
`52572ca279e21e2076e6e826bee7b0a5721dc508e565391ce0b36f7f40cb9498`.
The original independent failing probe remains retained; no host run occurred.
