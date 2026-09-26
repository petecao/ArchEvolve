# One finite DX100 coverage execution

Created: 2026-09-26 (Eastern Time).
Status: prepared tooling with local contract tests; actual execution requires the retained prerequisites below.

This implements the separate correctness case in
[the coverage plan](bfs-dx100-coverage-plan-20260926.md). The public entry is
`python3 scripts/bfs_dx100_coverage_execution.py --runs-dir <raw-root> --expected-commit <exact-commit>
--pane-pid <captured-pid> --pane-start-ticks <captured-start-ticks>
--a3-audit <path> --a3-sha256 <hash> --paired-completion <path>
--paired-sha256 <hash> --provider-completion <path> --provider-sha256 <hash>`.
It runs only on mbit10 socket 0 through the current `socket_lane.sh`, in a new
named tmux session. The caller must apply TERM at 3,570 seconds and KILL after
30 seconds. Dispatch remains contingent on the prerequisites and live host
admission below.

The fixed ID is `bfs-dx100-coverage-20260926-a1`. The absolute end is
**2026-09-26 16:45 ET**; latest start is **15:45 ET**, with the complete
3,600-second allowance still available. Earlier launch is possible only after
the actual a3 proof and both batch cleanup prerequisites pass. The existing a3
latest start of 15:20 ET and end of 15:40 ET are unchanged.
The a3 prerequisite must retain repository commit
`1018432fdb3800522d723afb874f3bffa41dd0e5`, its fixed verifier runtime map, and
the reopened exact request. Its recorded start must satisfy the original full
1,200-second launch window; its aware timestamps and host wall duration must
agree within one second. The later coverage checkout has its own independent
prospective commit pin.

The driver first reopens the paired/provider completion receipts with the
existing a3 admission reader, including all observed process identities. Its
separate a3 audit input must contain `id`, `state: passed`, aware `observed_at`,
`evaluation`, `evaluation_sha256`, `driver`, `lane`, `outer_exit`,
`lease_snapshot`, `owned_processes`, and `process_observations`. Artifact
fields are absolute `{path, sha256}` references. The reader reopens the actual
public evaluation, exact a3 request, completed driver and successful socket-0
lane/outer result, then independently checks the v2 completion witness and raw
artifacts. Its `cleanup_state` is `terminal_and_reaped` with all identities
absent, or `terminal_no_live_owned_processes` with the one zero-RSS terminated
tmux launcher retained explicitly. Reopened process observations must identify
the driver and all observed descendants; the reader rechecks those PID/start
pairs and the released a3 lease snapshot. `process_observations` contains
`driver_pid`, `pane_pid`, the explicit `launcher_identity: {pid, start_ticks}`,
`ancestry`, `owned_processes`, and a hashed `resource_samples` JSONL reference.
Every sample lists its observed `processes` with PID/start identities. These
must be captured while a3 runs; absence of an observation cannot be filled in
afterward. Owned ancestry stops at the captured pane; any shared tmux server
is separate non-owned context. The allowed launcher is the captured pane. A declared audit verdict without
those bindings cannot admit work.
The a3 observer must have finished its bounded sampling with
`state: driver_terminated`, `sampling_complete: true`, and
`cleanup_verified: false`; its separate observer identity is included in the
terminal union. Hashed `driver_exit` and `observer_exit` files must each retain
exit code zero. That observation still requires the independent terminal audit;
coverage's in-process sampler does not create a separate observer exit file.

Only the unchanged identified author candidate
`bfs-author-maa-compile-20260925-a1.candidate` is compiled. Its source snapshot,
artifact manifest and pinned author BFS hash must agree before any generation
or compilation. Fresh generation and public `register-workload` share one
120-second deadline. The graph has 8,212 vertices and 147,492 adjacency entries,
source 0, and the generator's fixed canonical identity. Registration uses a
separate correctness-case family; it cannot replace a campaign workload.

Public `dx100-compile` has a 240-second total allowance and requests the trusted
complete-call ROI, producing `dx100.complete_call.v2`. Public `dx100-execute`
then binds that fresh build, registered SG32 graph and source, four guest cores,
16,384-element tiles, `verification.coverage: true`, and the v2 post-ROI syscall
witness. Checkpoint and simulation caps are 300 and 2,700 seconds; the enclosing
public execution cap is 3,100 seconds. No checkpoint is reused. Each actual
request and public stdout/stderr is retained with its identity.

All stages share the 3,570-second work deadline. A driver-owned process-tree
sampler includes descendants across sessions, with a nominal five-second
interval and 30-second stale/guard ceiling. It enforces a sampled 48 GiB RSS
guard, a combined 4 GiB raw/build artifact guard, 10 GiB build-volume and 30 GiB
raw-volume reserves. The existing capacity gate requires estimated node
availability of 52 GiB and global MemAvailable of 64 GiB. These sampled guards
are not hard kernel caps or true-peak measurements. Cleanup preserves a failed
receipt and never retries, resumes, overwrites, or changes the graph or gates.

Success requires a fresh public retrieval matching the actual execution record,
the original-adjacency structural oracle for its exact binary and graph, a
sealed ROI followed by the protected v2 witness, and independently reopened
trace/statistics showing accelerator execution, full and tail range tiles, and
different parent-store values at the same physical word bound to the returned
parent array. Merely obtaining a complete evaluation is insufficient. The
reader streams and hashes the actual binary and simulator again, reopens the
SG32 adjacency, and compares its canonical identity with the fixed generator
topology as well as the retained graph receipt. The
driver receipt records `gain_claim: false`, no profiling or performance
comparison, finite-case scope, all prerequisites, runtime/source identities,
resource observations, requests, outputs, and any failed admission reason.
Final sample/observation hashing and receipt persistence remain inside the same
time and storage limits. The receipt retains explicit `final_accounting` after
the work and checks again after each final write; a late deadline or storage
crossing changes the retained driver and sampling status to failed. Admission
reopens that final accounting and checks current retained output size as well
as the earlier sampled peaks.
The required prospective commit must equal HEAD, and every retained runtime
source must match that commit's tracked bytes before work starts. Dispatch
therefore requires the later reviewed code commit, not a self-declared live
source digest. Socket 1 and the legacy lease must also be released before
generation and again before simulation.

Later batches use `validate_completed(ref, store, current, expected_commit,
proc=Path('/proc'))`. The caller must supply the prospectively selected coverage
commit, independent of the receipt's own declaration. This reader reopens all
six ordered stage commands, successful outputs and errors, exact public requests,
runtime files, graph and evaluation, capacity inputs and sampled resource guards.
It also checks the full original start window and total/stage bounds. Its returned
mapping retains `audit`, `evaluation`, `evaluation_sha256`, `driver`,
`repository_commit`, and observed `coverage`; it conveys no gain claim.

The coverage terminal audit uses the same fields described above, with
`id: bfs-dx100-coverage-20260926-a1` and the coverage evaluation ID ending in
`.execute`. Coverage captures its own initial ancestry through the explicitly
supplied pane and samples throughout its existing run bound. Its retained
`process_observations` uses `observer_kind: in_process_driver`, the driver as
`observer_identity`, `state: driver_sampling_finished`, and
`sampling_complete: true` only after the driver work succeeds. Its
`cleanup_verified` remains false. The reader requires the independent terminal
audit to cover and recheck those ancestry identities and every sampled descendant.
This neither extends the separate a3 observer's 1,200-second cap nor lets a running
driver attest its own termination.

Local tests use synthetic receipts and temporary graphs. They establish contract
handling only; actual a3 and accelerated coverage remain unobserved here.
