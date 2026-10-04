# Proposed fresh DX100 correctness continuation

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).

Status: prospectively coordinated on 2026-09-26 at 11:06 ET. This document is
outside the already completed four-commit code transfer. It records no new
simulator dispatch or result. The original proposed window remains below as
history; the selected window is the later coordinator decision.

## Preserved history

The actual `bfs-dx100-witness-20260926-a1` execution failed and remains failed,
with zero admitted timings. Its record SHA-256 is
`9a941cdff315e283b13563bf81ef2f45ba0712bbcf6d31b92f6232488efa3b42`.
The a2 window expired unused at 10:00 ET. Do not launch its client, reuse its ID,
extend its deadline, or promote either attempt through a new parser.

The next useful sequence is a read-only diagnosis of retained a1 bytes, followed
by one independently identified execution of the corrected mechanism. Neither
step establishes the remaining accelerated full/tail/competing-parent coverage.

## Read-only diagnosis

Use the reviewed parser from commit
`6346189b55132f195b02544b729f34100d10ba92`, after verifying that commit on the host.
Its `swdb/dx100_witness.py` SHA-256 is
`2d589162b6595fee0abf4f1db54aa5b1a0964dab3f51aa408ac06505b6014091`.
The unchanged driver and observer hashes are respectively
`371657977d56816a37f4885f19923f37175331d2d15b5d7f6e6049d3fa8c1395` and
`655c5804e26a0d1f8f7738f23ae62268cafe84562dbf8392af6c0169568146fd`.

Rehash the a1 record, seal, retained parser, and 2,761-byte trace against the
[a1 receipt](../evidence/bfs-dx100-witness-20260926-a1.yaml). Parse only that existing
trace with `parse_trace`, using these fixed diagnostic arguments:

```python
parse_trace(
    "/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/"
    "bfs-dx100-witness-20260926-a1/simulation/post-roi-syscalls.log",
    enabled_tick=2187360749,
    end_tick=3187360749,
    expected_cpu="system.switch_cpus0",
    expected_thread=0,
    allowed_cpus=CPUS,
    expected_sha256="f6ad616e622bdd0d538d7b377bfe9f14c15ebbe8030e635c40dbfa90f74603de",
)
```

`parse_trace` and `CPUS` come from `swdb.dx100_witness`. The interval ends at the
retained first continuation chunk boundary, not a newly inferred termination
time. Allow 30 seconds for this read-only parse. Retain its result as
`diagnostic_reparse`, with the old trace and new parser hashes. Do not write an
evaluation or replace the old verdict, runtime copies, audit, or seal. A parser
failure stops the proposed actual attempt for diagnosis; it does not invite
relaxing the grammar.

## One proposed new execution

The new ID is `bfs-dx100-witness-20260926-a3`. Derive its request from a1's exact
retained request by changing only `id`. Its canonical `artifacts.digest` must be
`ff0f415ba5e4fc3ac36b36bb32aa782ca875bcc3e5cc1d185b629a9f6e01ebbd`.
The unchanged input bindings are already spelled out in the
[a2 request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a2.yaml);
that file is an identity reference only, never this attempt's executable request.

Keep the unchanged author binary, pinned simulator/build, source-0 uniform64
graph, a4 checkpoint, four guest cores, MAA mode, 8 MiB/16-way LLC,
16,384-element tiles, 16 GB guest memory, author traversal ROI, v2 checker,
SyscallBase trace, and 10^10 post-ROI ticks. Do not build, regenerate a graph or
checkpoint, alter coverage flags, or assess a candidate in this attempt.

| Limit | Prospective value |
|---|---|
| Actual attempts | One; no automatic retry |
| Simulation/restoration | 750 seconds |
| Public adapter | 1,100 seconds |
| Outer execution | TERM at 1,170 seconds; KILL after at most 30 further seconds |
| Sampled process-group RSS | 48 GiB; not an instantaneous hard memory cap |
| Raw output | 2 GiB |
| Node/global admission | At least 52 GiB estimated node availability and 64 GiB global MemAvailable |
| Proposed absolute stop | 2026-09-26 11:55 ET |
| Proposed latest launch | 2026-09-26 11:35 ET, with the full 1,200 seconds available |

The proposed window permits the approved provider work to release lane 0 before
the proof and leaves the paired pilot's 11:58 ET latest start intact. It is not
a promise that the provider batch finishes early. Use actual completion times.
Run the proof before the paired calibration starts, with no other owned
measurement active. If lane availability, preparation, provider duration, or
capacity prevents this ordering, leave a3 unexecuted under this proposal. Do
not extend either plan or silently overlap the proof with calibration. The
coordinator may prospectively select a different fresh window before any a3
dispatch; record that decision separately instead of editing expired history.

Recheck both socket leases, the legacy lease, helper identity, live owners,
affinity/load, free disk, and every input/checkpoint hash. Apply the unchanged
capacity gate immediately before lane claim and again inside the selected
lane. Use the verified `socket_lane.sh`, a named tmux session, an inactive
checkout of the reviewed code, and new `witness-a3-dispatch1` receipts. Refuse
existing evaluation, output, or receipt paths. Historical DX5802a5a and
native41303ed7 checkouts remain pinned. All scratch/config/source writes use
`/data1/yanruj`; raw receipts stay on the authorized host run volume.

Within that outer envelope, the public operation is:

```sh
python3 -m swdb dx100-execute A3_REQUEST_JSON \
  --records REVIEWED_CHECKOUT/records \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 \
  --lane 0 --format json
```

Before that command, the coordinator's bounded wrapper must enforce the fixed
request digest, unchanged a1 failure digest, absent a2 execution paths, fresh a3
paths, runtime hashes, and the absolute clock cutoff. Do not invoke the old a2
wrapper with a changed file or monkeypatch its constants. Keep start/end times,
capacity and lane receipts, request and runtime identities, stdout/stderr hashes,
exit code, and cleanup observations for success or failure.

## What a successful result would establish

Audit a fresh public `get ID --chain` and the exact raw witness with
`validate_completed_witness(..., verify_artifacts=True)`. Require the actual new
execution's passed structural verifier, sealed ROI, protected completion output,
matching simulator-origin exit call/return, current retained runtime copies,
and clean simulator process. Preserve `normal_exit_observed` independently.
Keep `gain_claim: false` and do not publish a comparison or frozen protocol.

Passing a3 establishes the corrected completion mechanism on this finite tiny
author case. Its scalar fallback cannot close ticket 13. The next actual
coverage request must separately pin a case whose observed execution establishes
MAA work, full and tail tiles, and competing parent updates, with verification
against original adjacency and `verification.coverage: true`. Existing graph
topology or the prepared uniform22 graph does not itself prove those observations.
That larger case needs its own prospective identity and resource plan after a3;
it is not an automatic retry or an unbounded extension of this document.


## Coordinator decision — 2026-09-26 11:06 ET

The 11:35/11:55 proposal above is not selected for dispatch. Start the native
paired pilot first, with only provider source generation allowed concurrently.
Heavy simulator execution could perturb the measurement through shared host
resources even when pinned to the other socket, so the a3 proof waits until
all four paired cells and their owned processes have terminated and the driver
has a retained terminal receipt (success or failure).

The selected fresh a3 window ends **2026-09-26 15:40 ET**, with latest launch
**15:20 ET** and the same 1,200-second outer cap. It may start earlier once the
paired pilot and provider batch have both terminated, live capacity and all
three lease checks pass, and exact input/code/request identities are retained.
This timing is chosen before a3 execution or results. It changes no workload,
protocol, attempts, verification rules, memory/storage caps or historical
verdict. One actual a3 attempt is permitted. If admission cannot pass before
the latest launch, leave a3 unexecuted and retain that outcome; this document
does not authorize an automatic retry, deadline extension, or a4 attempt.

Read-only diagnosis and request/preflight preparation may proceed while the
paired pilot runs. They cannot start a simulator, alter historical records or
checkouts, consume a new measurement ID, or claim acceptance. A passing reparse
only explains the retained a1 failure; real acceptance requires the new actual
execution and its independent witness audit.

## Dedicated a3 admission driver — 2026-09-26

`scripts/dx100_witness_continuation.py` implements only the selected fresh window.
Its fixed [a3 request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a3.yaml)
has the canonical digest above. It refuses changed a1 bytes, any a2 evaluation
or execution path, and any existing a3 evaluation, output, or driver path,
including dangling symlinks. A driver directory created by a failed attempt is
retained and prevents an automatic retry. The public operation has a
1,150-second stage ceiling within the unchanged 1,170-second driver allowance
and 30-second outer cleanup reserve; the adapter and simulator retain their
1,100- and 750-second caps. Every preflight clock check requires the full
1,200 seconds before 15:40 ET. Neither old wrapper is modified or invoked.

The pinned read-only a1 diagnostic prerequisite is
`bfs-dx100-witness-20260926-a1-diagnostic-reparse-20260926.json`, SHA-256
`2d7d011e238f06954757fa426dc527bdec54504ffd6fd1890c542b4955f4a7b5`, under the
unchanged bring-up raw root. Its parse completed under the corrected parser;
its original evaluation remains failed. The driver only reads this receipt.

Each prior batch supplies a coordinator-reviewed completion JSON and its exact
SHA-256, passed separately on the command line. The JSON carries the exact batch
`id`, an aware `observed_at`, hashed `driver`, `lane`, and `outer_exit` references,
`lease_released: true`, and nonempty `owned_processes` with integer `pid` and
`start_ticks`. `process_observations` references a hashed JSON containing the
initial owned `ancestry` and optional additional `owned_processes` arrays. The
completion identity set must cover those arrays and every process from the
driver's hashed resource samples (`rss.samples` for paired collection,
`resource_artifact` for provider generation). Paired samples must contain the
recorded `driver_pid`. Missing observations fail admission. Receipt JSON reads
are capped at 2 MiB and resource sample reads at 16 MiB; these finite reader
limits fail closed if exceeded and do not change any collection resource cap.

For an all-absent batch, the completion state is `terminal_and_reaped` and
`owned_processes_absent: true`. A retained launcher zombie is the narrowly
permitted alternative for either batch: `terminal_no_live_owned_processes`,
`owned_processes_absent: false`, and `owned_processes_nonrunning: true`. In that
case exactly one retained process may have `state: Z`, `role: tmux_launcher`,
and `rss_bytes: 0`; every other entry has `state: absent`. That identity must
occur in the hashed initial ancestry and match the actual observed launcher:
provider PID/start-ticks `3033637/493713694`, or paired `3034758/493754291`.
The reader checks
current `/proc` PID/start identities, permits that recorded launcher only if it
is still a zero-RSS zombie or has disappeared, and rejects every other surviving
owned identity. It does not signal the shared tmux server or claim that the
launcher has been reaped. A reused PID with a different start time is not the
old process. These checks cover retained owned identities, not unknown jobs on
the shared host; the coordinator still checks all three leases and live load.

The reader reopens the actual `{socket_lane: {...}}` helper receipt and requires
mbit10 node 1/generation 400 for paired collection and node 0/generation 318 for
provider generation. Driver and outer exit records must be terminal, the lane
exit code must match, and their chronology must precede admission. The helper's
whole-second end timestamp denotes `[stamp, stamp + 1 second)`; the driver's
fractional finish must also precede the audit observation. Failed batches with
unattempted cells are allowed once their owned processes have terminated.
This barrier does not qualify their scientific or provider outcomes.

After the coordinator's fresh helper, lease, identity, disk, and capacity checks,
the command inside a newly claimed node-0 helper is:

```sh
timeout --signal=TERM --kill-after=30s 1170s \
  python3 scripts/dx100_witness_continuation.py \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 \
  --lane 0 \
  --paired-completion PAIRED_TERMINAL_JSON --paired-sha256 PAIRED_TERMINAL_SHA256 \
  --provider-completion PROVIDER_TERMINAL_JSON --provider-sha256 PROVIDER_TERMINAL_SHA256
```

The placeholders must be replaced with newly checked, exact receipt paths and
hashes; they are not permissions to create substitute evidence. The driver
rechecks current node-0 lane ancestry and capacity, and rechecks the retained
process identities just before public execution. It retains the request,
historical failure and diagnostic bindings, runtime hashes, repository commit,
both completion barriers, stage logs and hashes, elapsed time, and final result.
Only a fresh passed `validate_completed_witness(..., verify_artifacts=True)` can
mark a3 complete. `gain_claim` remains false, and no a4 or coverage job follows
automatically. Local driver tests use synthetic terminal/process fixtures and
are not simulator, cleanup, or correctness evidence for mbit10.
