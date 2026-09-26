# T17 existing-candidate build-only plan

Created: 2026-09-26 (Eastern Time)

This prepares one compilation of the retained initial instruction-route candidate.
It has not been dispatched. Run it only after the native study, a3 continuation,
and fixed-coverage work have ended and their owned-process cleanup has been
verified. Preserve their windows and other-node-idle admission gates. The pending
native unpublishable-review readback takes priority. This plan neither freezes a
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
