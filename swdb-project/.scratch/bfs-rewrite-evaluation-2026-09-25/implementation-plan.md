# BFS implementation and execution plan

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

The user authorized all 21 tickets, including builds, installations, remote execution,
Git synchronization, and Claude Code. Earlier publication-only holds are superseded.
The acceptance requirements and ticket dependencies remain unchanged.

## Decisions before implementation

- Preserve existing record formats and historical evidence. Source-specific records
  use the additive 0.4 format described in `docs/bfs-source-identity.md`.
- New workflow metadata remains YAML in the existing record store, with the existing
  generated SQLite index. Message versions are independent of record versions.
- Add public source-snapshot, proposal submission, evaluation, and retrieval commands.
  Candidate files, logs, and binaries live outside the records tree; metadata names
  their location, content hash, and producing stage. A candidate is not a verified
  implementation merely because patch application or compilation succeeds.
- Persist the submitted request before processing and each completed stage before
  starting another. A later process can distinguish interrupted work from completion.
- Derive protected verifier and ROI content from evaluator-owned source definitions.
  A proposal cannot authorize edits to its own correctness check or timing boundaries.
- Resolve exact source snapshots before applying edits. Reject stale identities,
  path escapes, symlink substitution, incompatible sources, and unknown capabilities.
- Keep pre-freeze execution diagnostic. Baseline/reference-only calibration determines
  workload sizes and repetition policy before any candidate profitability assessment.
- Native elapsed time, instrumented diagnostic time, simulated ticks, and simulation
  host cost are separate quantities. Real dynamic memory observations are mandatory
  for complete packages; unavailable native counters remain explicit.
- The native integration order is DX100 scalar top-down BFS, then upstream BFS.
  Both sources, both routes, both graph families, both-source acceleration, and the
  artifact/reference controls remain required for final acceptance.

## Ownership and sequence

The source-identity worker owns Ticket 01 and initial core schema/store/query changes.
The root worker owns proposal/candidate persistence and integration. A profiling
worker prepared the native discovery/collector design and will implement unblocked
profiling slices. The host worker inspects current resources and executable DX100
requirements; remote dispatch is coordinated through that worker and the root.
Shared-file ownership is reassigned explicitly to avoid concurrent rewrites.

Ticket completion requires its acceptance evidence and an Answer section. Fixture
tests establish contracts only. A later slice may be prepared while waiting for its
prerequisites, but it is not resolved before those prerequisites and its own checks.

## Resources and checkpoints

Only mbit10 is authorized as the lab host. Recheck both socket leases, the legacy
lease, processes, load, available memory, and disks immediately before dispatch.
Use the verified current `socket_lane.sh`, one job per socket, at most two jobs,
bounded timeouts, capped build parallelism, and named tmux sessions. Do not update a
checkout while a run uses it. Code moves through Git; raw output remains remote.

The initial 2026-09-25 preflight found both lanes released, approximately 111 GiB
available RAM, 22 GiB free on `/data1`, and 198 GiB on `/data`. These are observations,
not reservations. Plan large output under `/data/yanruj/EvolveSWDB_runs`; do not fill
the root filesystem or silently reuse a stale dispatch script.

The thread heartbeat checks progress, subagent health, leases, and logs every
30 minutes and posts the requested evaluation table. Recover dead workers without
discarding retained evidence. Stop the heartbeat after complete acceptance, review,
repairs, and tracker synchronization.

## Review boundary

Starting commit: `1bdb7d4037916dea782c40239a6415b61a47f3c1`.
After implementation, run independent Standards and Spec reviews using the
code-review skill, reproduce findings through the public boundary, and address them
before final closure. Preserve unrelated untracked `weeklogs/` content.
