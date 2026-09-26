# Prospective author v2 completion observation

Updated: 2026-09-26 (Eastern Time). Preparation only; this document does not
authorize dispatch.

The new evaluation `bfs-dx100-witness-20260926-a1` tests the explicitly declared
`dx100.bfs.verifier.v2` contract on the unchanged author's `bfs_maa` binary. It
requires the sealed ROI, the protected author's ordered PASS, Verification Time,
and Average Time output, and one matching successful `exit_group(0)` call/return
pair in a separate post-seal simulator trace. Completion of these observations
does not assert normal guest termination. The record must state the actual event,
`stop_reason`, and `normal_exit_observed` independently. Existing v1 records and
their verdicts remain unchanged.

The fixed request is
`.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a1.yaml`.
Compared with the retained real a6 request, it changes only the evaluation ID,
the explicit checker to v2, the post-ROI allowance to `10000000000` ticks, and
the explicit `SyscallBase` trace option. The client validates this exact diff
against the retained evaluation before writing a new result directory. It
preserves the original simulator, model build, guest binary, source, a4 graph and
checkpoint manifest, four simulated cores, MAA configuration, 8 MiB/16-way LLC,
16 GB guest memory, and author traversal ROI. Checkpoint reuse requires every
existing identity check; no new checkpoint or graph is generated.

After the ROI statistics and seal are durable, the trusted driver redirects
simulator debug output to `post-roi-syscalls.log`, disables the named ROI debug
flags, disables `FmtTicksOff` and `FmtStackTrace`, and enables `FmtFlag` and
`SyscallBase`. The driver retains these settings and their enable tick. It uses
post-seal simulation chunks of at most `1000000000` ticks, with their sum bounded
by the request. It stops after the validated exit witness or an actual normal
terminal event; both successful branches still require the complete witness.
The trace parser, driver, output, protected source, seal, and trace hashes are
bound into the new evaluation. The parser's separate 32 MiB trace limit remains
inside the overall 2 GiB raw-storage limit.

The finite resource bounds are unchanged: 48 GiB process-group RSS, 750 seconds
for restoration/simulation, 1,100 seconds for the public adapter, 2 GiB raw
storage, and 1,200 seconds for the thin outer driver with its existing 30-second
cleanup reserve. There is one actual attempt and no automatic retry or cap
increase. Host/resource interruption, missing or reordered protected output,
incomplete witness, malformed trace, stale identity, or tick exhaustion remains
an unsuccessful evaluation. No gain, comparison, accelerator-coverage, or
artifact-reference conclusion follows from this tiny validation.

The coordinator must review and checkpoint code and the fixed request before
dispatch. The currently running native repeatability block must release its lane
before this job starts, so our own measurements do not interfere. Use an idle
checkout of the approved commit, never update an active checkout, and recheck
both socket leases, the legacy lease, live owners, current helper identity, load,
storage, and all exact input/checkpoint hashes. The unchanged capacity gate must
pass immediately before claim and again inside the selected lane: conservative
node availability at least 52 GiB, including the existing 1 GiB uncertainty
discount, and global MemAvailable at least 64 GiB. No forced reclamation or gate
relaxation is allowed.

Inside the freshly verified lane, run the fixed client through the normal lane
helper, named tmux session, and outer timeout:

```sh
python3 scripts/dx100_witness_probe.py \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 \
  --lane 1
```

Lane 0 is also eligible after the same coordinated fresh checks. Use a new outer
prefix `witness-a1-dispatch1` for capacity, lane, log, and exit receipts; each
preflight refusal requires a distinct later suffix. Never overwrite a6 or v1
probe evidence. Raw receipts and derived metadata stay on mbit10 while the
explicit metadata-export approval remains pending. Record successful or failed
observations through the public evaluator, then audit fresh public retrieval.
Any later candidate-wrapper or accelerated-profile validation needs its own
prospective reviewed plan.
